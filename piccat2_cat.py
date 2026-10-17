import os
import sys
import time
import queue
import threading
from pathlib import Path
from PIL import Image

import torch
from torchvision import transforms
import clip
import mariadb

# Konfiguration
CACHE_DIR = Path(r"F:\bilder\.piccat_cache")
BATCH_SIZE = 16
BULK_FLUSH_SIZE = 1000
MIN_CONFIDENCE_PERCENT = 15
TOP_K_COUNT = 5

DB_CONFIG = {
    "host": "raspiSolarMariaDb",
    "port": 3306,
    "user": "root",
    "password": "YOUR_DB_PASSWORD",
    "database": "piccat"
}


def producer_file_loader(file_paths, image_queue, stop_event):
    """
    Hintergrund-Thread: Lädt die vorbereiteten 336x336-Bilder parallel zur GPU-Inferenz.
    """
    batch_tensors = []
    batch_meta = []
    load_start = time.perf_counter()

    for path in file_paths:
        if stop_event.is_set():
            break

        try:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                batch_tensors.append(transforms.functional.to_tensor(img_rgb))
                batch_meta.append(path.name)
        except Exception:
            continue

        if len(batch_tensors) == BATCH_SIZE:
            io_duration_ms = (time.perf_counter() - load_start) * 1000.0
            image_queue.put((torch.stack(batch_tensors), batch_meta, io_duration_ms))
            batch_tensors = []
            batch_meta = []
            load_start = time.perf_counter()

    if batch_tensors and not stop_event.is_set():
        io_duration_ms = (time.perf_counter() - load_start) * 1000.0
        image_queue.put((torch.stack(batch_tensors), batch_meta, io_duration_ms))

    image_queue.put(None)


def get_current_run_seq(conn):
    cur = conn.cursor()
    cur.execute("SELECT NEXT VALUE FOR piccat_seq_run")
    seq_run = cur.fetchone()[0]
    cur.execute("INSERT INTO piccat_tab_run (seqRun, tBeg) VALUES (?, NOW(6))", (seq_run,))
    conn.commit()
    cur.close()
    return seq_run


def load_categories(conn):
    cur = conn.cursor()
    cur.execute("SELECT seqCat, sAiText FROM piccat_tab_category")
    rows = cur.fetchall()
    cur.close()
    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    return ids, texts


def get_next_sequence_values(conn, count):
    cur = conn.cursor()
    ids = []
    cur.execute(f"SELECT NEXT VALUE FOR piccat_seq_file FROM seq_1_to_16 LIMIT {count}")
    for row in cur.fetchall():
        ids.append(row[0])
    cur.close()
    return ids


def flush_database_buffers(conn, file_buffer, conf_buffer):
    if not file_buffer and not conf_buffer:
        return
    cur = conn.cursor()
    if file_buffer:
        cur.executemany(
            "INSERT INTO piccat_tab_file (seqFile, sName, seqFolder, seqRun, dtExif) VALUES (?, ?, ?, ?, ?)",
            file_buffer
        )
    if conf_buffer:
        cur.executemany(
            "INSERT INTO piccat_tab_confidence (seqRun, seqFile, seqFolder, seqCategory, iConfidence) VALUES (?, ?, ?, ?, ?)",
            conf_buffer
        )
    conn.commit()
    cur.close()
    file_buffer.clear()
    conf_buffer.clear()


def main():
    t_process_start = time.perf_counter()

    if not CACHE_DIR.exists():
        print(f"Fehler: Cache-Verzeichnis '{CACHE_DIR}' nicht gefunden.")
        sys.exit(1)

    cached_files = [p for p in CACHE_DIR.glob("*.jp*") if p.is_file()]
    total_files = len(cached_files)
    if total_files == 0:
        print(f"Keine Bilddateien in '{CACHE_DIR}' gefunden.")
        sys.exit(0)

    try:
        conn = mariadb.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Fehler bei Verbindung zur MariaDB: {e}")
        sys.exit(1)

    seq_run = get_current_run_seq(conn)
    category_ids, category_texts = load_categories(conn)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_half = (device == "cuda")

    model, _ = clip.load("ViT-L/14@336px", device=device)
    if use_half:
        model.float()
        clip.model.convert_weights(model)
    model.eval()

    text_tokens = clip.tokenize(category_texts).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_tokens)
        if use_half:
            text_features = text_features.half()
        text_features /= text_features.norm(dim=-1, keepdim=True)

    normalize_transform = transforms.Normalize(
        mean=(0.48145466, 0.4578275, 0.40821073),
        std=(0.26862954, 0.26130258, 0.27577711)
    )

    image_queue = queue.Queue(maxsize=16)
    stop_event = threading.Event()
    loader_thread = threading.Thread(
        target=producer_file_loader,
        args=(cached_files, image_queue, stop_event),
        daemon=True
    )
    loader_thread.start()

    db_file_buffer = []
    db_conf_buffer = []
    total_processed = 0
    total_batches = 0
    total_inference_time = 0.0
    last_print = time.time()
    db_error = False

    try:
        while True:
            item = image_queue.get()
            if item is None:
                image_queue.task_done()
                break

            batch_tensors, batch_filenames, io_time_ms = item
            batch_size = batch_tensors.size(0)

            t_inf_start = time.perf_counter()
            batch_norm = torch.stack([normalize_transform(t) for t in batch_tensors]).to(device)
            if use_half:
                batch_norm = batch_norm.half()

            with torch.no_grad():
                image_features = model.encode_image(batch_norm)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                top_values, top_indices = similarity.topk(min(TOP_K_COUNT, len(category_ids)), dim=-1)

            if device == "cuda":
                torch.cuda.synchronize()

            inf_time_ms = (time.perf_counter() - t_inf_start) * 1000.0
            total_inference_time += (inf_time_ms / 1000.0)
            total_batches += 1
            total_processed += batch_size

            seq_file_ids = get_next_sequence_values(conn, batch_size)

            top_values_list = top_values.cpu().tolist()
            top_indices_list = top_indices.cpu().tolist()

            for i in range(batch_size):
                seq_file = seq_file_ids[i]
                file_name = batch_filenames[i]
                db_file_buffer.append((seq_file, file_name, 0, seq_run, None))

                for rank, (idx, val) in enumerate(zip(top_indices_list[i], top_values_list[i])):
                    conf = int(val * 100 + 0.5)
                    if conf >= MIN_CONFIDENCE_PERCENT or rank == 0:
                        cat_id = category_ids[idx]
                        db_conf_buffer.append((seq_run, seq_file, 0, cat_id, conf))

            if len(db_file_buffer) >= BULK_FLUSH_SIZE:
                flush_database_buffers(conn, db_file_buffer, db_conf_buffer)

            image_queue.task_done()

            current_time = time.time()
            if current_time - last_print >= 2.0:
                progress_pct = (total_processed / total_files) * 100.0
                print(f"Fortschritt: {total_processed}/{total_files} ({progress_pct:.1f}%) | "
                      f"I/O: {io_time_ms:.1f}ms | Inferenz: {inf_time_ms:.1f}ms")
                last_print = current_time

    except KeyboardInterrupt:
        stop_event.set()
        print("\nAbbruch durch Benutzer...")
    except Exception as e:
        stop_event.set()
        db_error = True
        print(f"\nUnerwarteter Fehler: {e}")
    finally:
        loader_thread.join()
        try:
            flush_database_buffers(conn, db_file_buffer, db_conf_buffer)
            cur = conn.cursor()
            cur.execute("UPDATE piccat_tab_run SET tEnd = NOW(6) WHERE seqRun = ?", (seq_run,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            db_error = True

    total_duration_sec = time.perf_counter() - t_process_start
    avg_batch_ms = (total_inference_time / total_batches * 1000.0) if total_batches > 0 else 0.0
    db_status = "Erfolgreich abgeschlossen" if not db_error else "Fehlgeschlagen / Unvollständig"

    print("=" * 60)
    print(" PICCAT2 KI-ANALYSE ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f" Gesamtlaufzeit         : {total_duration_sec:.2f} Sekunden")
    print(f" Verarbeitete Bilder    : {total_processed} von {total_files}")
    print(f" Verwendetes Device     : {device.upper()} (FP16: {'Ja' if use_half else 'Nein'})")
    print(f" Verarbeitete Batches   : {total_batches} (Batch-Größe: {BATCH_SIZE})")
    print(f" Ø Inferenz-Zeit / Batch: {avg_batch_ms:.2f} ms")
    print(f" Datenbank-Status       : {db_status}")
    print("=" * 60)


if __name__ == "__main__":
    main()