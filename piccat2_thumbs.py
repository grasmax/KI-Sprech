import os
import sys
import time
import warnings
from collections import deque
from pathlib import Path
from PIL import Image, ImageOps

SOURCE_DIR = r"F:\bilder"
CACHE_DIR = r"F:\bilder\.piccat_cache"
TARGET_SIZE = (336, 336)
VALID_EXTENSIONS = (".jpg", ".jpeg")
WINDOW_SECONDS = 20.0  # Zeitfenster für dynamische Momentangeschwindigkeit


def main():
    print(f"Starte Thumbnail-Generierung...")
    print(f"Quellverzeichnis: {SOURCE_DIR}")
    print(f"Cache-Verzeichnis: {CACHE_DIR}")

    if not os.path.exists(SOURCE_DIR):
        print(f"FEHLER: Quellverzeichnis '{SOURCE_DIR}' existiert nicht.")
        sys.exit(1)

    t_start = time.time()
    start_str = time.strftime("%H:%M:%S", time.localtime(t_start))

    # 1. Bilddateien ermitteln
    print("Scanne Dateisystem nach Bildern...")
    file_list = []
    cache_dirname = os.path.basename(CACHE_DIR).lower()

    for root, dirs, files in os.walk(SOURCE_DIR):
        # Ordner ignorieren, die mit '000' beginnen oder der Cache-Ordner selbst sind
        dirs[:] = [
            d for d in dirs
            if not d.startswith("000") and d.lower() != cache_dirname
        ]

        for file_name in files:
            if file_name.lower().endswith(VALID_EXTENSIONS):
                file_list.append(os.path.join(root, file_name))

    count_total = len(file_list)
    print(f"{count_total} relevante Bilddateien gefunden.")

    count_processed = 0
    count_skipped = 0
    count_errors = 0
    last_print = 0.0

    # Verlaufsspeicher für gleitende Momentangeschwindigkeit: (timestamp, count_processed)
    speed_history = deque([(t_start, 0)])

    # 2. Bildverarbeitung
    for idx, src_file in enumerate(file_list, start=1):
        try:
            rel_path = os.path.relpath(src_file, SOURCE_DIR)
            dest_file = os.path.join(CACHE_DIR, rel_path)

            if os.path.exists(dest_file):
                count_skipped += 1
            else:
                dest_dir = os.path.dirname(dest_file)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

                # EXIF-Warnungen fangen und dem Bild zuordnen
                with warnings.catch_warnings(record=True) as caught_warnings:
                    warnings.simplefilter("always", UserWarning)

                    with Image.open(src_file) as img_raw:
                        img_trans = ImageOps.exif_transpose(img_raw)
                        img_rgb = img_trans.convert("RGB")
                        if img_trans is not img_raw:
                            img_trans.close()

                    img_final = ImageOps.fit(
                        img_rgb, TARGET_SIZE, method=Image.Resampling.LANCZOS
                    )
                    img_rgb.close()

                    img_final.save(dest_file, format="JPEG", quality=85)
                    img_final.close()

                    if caught_warnings:
                        for w in caught_warnings:
                            # Zeile bereinigen und Warnung formatiert ausgeben
                            print(f"\r{' ' * 120}\r[EXIF-WARNUNG] {src_file}: {w.message}", flush=True)

                count_processed += 1

        except Exception:
            count_errors += 1

        # Fortschritt strikt alle 2 Sekunden ausgeben
        now = time.time()
        if now - last_print >= 2.0:
            pct = (idx / count_total * 100.0) if count_total > 0 else 0.0

            # Dynamische Momentangeschwindigkeit über gleitendes Zeitfenster
            speed_history.append((now, count_processed))
            while len(speed_history) > 1 and speed_history[0][0] < now - WINDOW_SECONDS:
                speed_history.popleft()

            t_old, count_old = speed_history[0]
            dt = now - t_old
            dp = count_processed - count_old
            speed = (dp / dt) if dt > 0 else 0.0

            # Restbilder ohne bereits erledigte/gecachte Dateien
            remaining_to_process = count_total - idx

            if speed > 0 and remaining_to_process > 0:
                remaining_sec = remaining_to_process / speed
                eta_str = time.strftime("%H:%M:%S", time.localtime(now + remaining_sec))
            elif remaining_to_process == 0:
                eta_str = time.strftime("%H:%M:%S", time.localtime(now))
            else:
                eta_str = "--:--:--"

            print(
                f"\rVerarbeitet: {idx}/{count_total} | {pct:5.1f}% | Geschwindigkeit: {speed:5.1f} Bilder/Sek | ETA: {eta_str}",
                end="",
                flush=True
            )
            last_print = now

    # Zeilenumbruch nach dem interaktiven Fortschritt
    print()

    # 3. Abschluss-Zusammenfassung (exakt 10 Zeilen)
    t_end = time.time()
    end_str = time.strftime("%H:%M:%S", time.localtime(t_end))
    total_sec = t_end - t_start
    m, s = divmod(int(total_sec), 60)
    h, m = divmod(m, 60)
    dauer_str = f"{h:02d}:{m:02d}:{s:02d}"

    print("=" * 60)
    print("ZUSAMMENFASSUNG: THUMBNAIL-CACHING")
    print(f"Startzeit:            {start_str}")
    print(f"Ende-Zeitpunkt:       {end_str}")
    print(f"Gesamtlaufzeit:       {dauer_str} ({total_sec:.2f} s)")
    print(f"Dateien gesamt:       {count_total}")
    print(f"Neu verarbeitet:      {count_processed}")
    print(f"Übersprungen (Cache): {count_skipped}")
    print(f"Fehlerhafte Dateien:  {count_errors}")
    print("=" * 60)


if __name__ == "__main__":
    main()