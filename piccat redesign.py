import os
from google import genai
from google.genai import types

# 1. API-Client initialisieren
client = genai.Client()

# Pfade zu Ihren bestehenden Skripten im Visual Studio Projektordner
client_script_path = "piccat_client_x2x4x16.py"
server_script_path = "piccat_server_x16.py"

# Die beiden neuen Zielpfade
output_thumbs_path = "piccat2_thumbs.py"
output_cat_path = "piccat2_cat.py"

sModel = "gemini-3.7-flash"

print("Lese bestehende Quelldateien ein...")

try:
    with open(client_script_path, "r", encoding="utf-8") as f:
        client_code = f.read()
except FileNotFoundError:
    print(f"Fehler: {client_script_path} wurde nicht gefunden.")
    exit(1)

try:
    with open(server_script_path, "r", encoding="utf-8") as f:
        server_code = f.read()
except FileNotFoundError:
    print(f"Fehler: {server_script_path} wurde nicht gefunden.")
    exit(1)

# ==============================================================================
# PROMPT 1: Für das Vorbereitungsskript (Thumbs)
# ==============================================================================
prompt_thumbs = f"""Du bist ein erfahrener Software-Architekt für Python und Computer Vision.
Ich plane ein Refactoring meines Bildanalyse-Projekts "piccat".

DEINE AUFGABE:
Schreibe mir ein eigenständiges Python-Skript namens "piccat2_thumbs.py". Dieses Programm ist rein für das Einlesen, Rotieren, Herunterskalieren der Originalbilder und das Speichern der herunterskalierten Thumbs zuständig.

RAHMENBEDINGUNGEN & LOGIK:
1. Das Skript piccat2_thumbs.py soll alle Originalbilder aus dem Verzeichnis F:\\bilder einlesen.
2. Nutze die Einlese- und Ordnerstruktur-Logik aus der unten bereitgestellten Client-Datei (os.walk, EXIF-Rotation via Pillow).
3. Jedes Bild soll auf exakt 336x336 Pixel mit dem LANCZOS-Filter skaliert und in einen dedizierten Cache-Ordner auf der externen Festplatte (z. B. 'F:\\bilder\\.piccat_cache\\') gespeichert werden. Die originale Unterordner-Struktur muss im Cache-Ordner exakt gespiegelt werden.
4. Falls ein Bild im Cache-Ordner bereits existiert, soll es übersprungen werden (inkrementelles Arbeiten).
5. Das Skript benötigt KEINE KI-Module (kein torch, kein clip) und KEINE Datenbankverbindung. Es läuft rein auf der CPU.

FORTSCHRITTSANZEIGE & KONSOLEN-LOGGING (WICHTIG):
- Das Skript darf den Fortschritt (z. B. "Verarbeitet: X/Y Bildern | Z% | Geschwindigkeit: A Bilder/Sek") strikt NUR alle 2 Sekunden auf der Kommandozeile ausgeben, um die Konsole nicht zu überfluten. Nutze dafür eine Abfrage wie 'if time.time() - last_print >= 2:'.
- Am Ende des Programms MUSS eine saubere, übersichtliche und MAXIMAL 10 Zeilen lange Zusammenfassung ausgegeben werden. Diese muss mindestens enthalten: Gesamtlaufzeit, Anzahl der neu verarbeiteten Bilder, Anzahl der übersprungenen (bereits gecachten) Bilder sowie eventuelle Fehler.

Hier ist der Code der Client-Datei als Basis:
=== START DATEI: piccat_client_x2x4x16.py ===
{client_code}
=== ENDE DATEI: piccat_client_x2x4x16.py ===

Gib mir als Ausgabe NUR den finalen, einsatzbereiten Python-Code für "piccat2_thumbs.py" aus. Antworte ohne umschließende Markdown-Code-Blöcke (keine ```python-Tags)."""

# ==============================================================================
# PROMPT 2: Für das KI-Analyseskript (Kategorisierung)
# ==============================================================================
prompt_cat = f"""Du bist ein erfahrener Software-Architect für High-Performance Deep Learning mit PyTorch, CUDA und CLIP.
Ich plane ein Refactoring meines Bildanalyse-Projekts "piccat".

DEINE AUFGABE:
Schreibe mir ein eigenständiges Python-Skript namens "piccat2_cat.py". Dieses Programm führt die KI-Kategorisierung durch und speichert die Ergebnisse.

RAHMENBEDINGUNGEN & LOGIK:
1. Das Skript liest KEINE Originalbilder mehr ein, sondern arbeitet ausschließlich mit den bereits vorbereiteten 336x336-Bildern aus dem Cache-Ordner 'F:\\bilder\\.piccat_cache\\'.
2. Implementiere ein performantes Producer-Consumer-Muster mit 'threading.Queue'. Ein Hintergrund-Thread lädt die 336x336-Bilder blitzschnell aus dem Cache vor, während der Haupt-Thread die Batches (Größe 16) auf der GPU/CPU verarbeitet.
3. Integriere die CLIP-Analyse-Logik aus der Server-Datei.
4. Schalte die Hardware automatisch: 'device = "cuda" if torch.cuda.is_available() else "cpu"'. Wenn CUDA verfügbar ist (Gaming-PC), aktiviere FP16 (Half Precision).
5. Entferne die gesamte alte Netzwerk-Server-Hülle (FastAPI, Uvicorn, Sockets) und die struct.pack-Serialisierung vollständig.
6. Schreibe die finalen Analyse-Ergebnisse via Bulk-Insert mit dem nativen Modul 'mariadb' direkt in die externe MariaDB auf dem Raspberry Pi (in Paketen von z. B. 1000 Bildern), um den Netzwerk-Overhead zu minimieren. Nutze das bestehende Tabellenschema aus der Client-Datei.

FORTSCHRITTSANZEIGE & KONSOLEN-LOGGING (WICHTIG):
- Das Skript darf den Status (fortlaufende I/O-Time und Inference-Time in Millisekunden sowie den Gesamtfortschritt) strikt NUR alle 2 Sekunden auf der Kommandozeile ausgeben ('if time.time() - last_print >= 2:').
- Am Ende des Programms MUSS eine saubere, übersichtliche und MAXIMAL 10 Zeilen lange Zusammenfassung ausgegeben werden. Diese muss mindestens enthalten: Gesamtlaufzeit des KI-Prozesses, Anzahl der erfolgreich kategorisierten Bilder, durchschnittliche Zeit pro Batch sowie Status der Datenbankübertragung.

Hier sind die Quellcodes:
=== START DATEI: piccat_client_x2x4x16.py ===
{client_code}
=== ENDE DATEI: piccat_client_x2x4x16.py ===

=== START DATEI: piccat_server_x16.py ===
{server_code}
=== ENDE DATEI: piccat_server_x16.py ===

Gib mir als Ausgabe NUR den finalen, einsatzbereiten Python-Code für "piccat2_cat.py" aus. Antworte ohne umschließende Markdown-Code-Blöcke (keine ```python-Tags)."""

# 4. API-Aufrufe nacheinander starten
print(f"Generiere Stufe 1: {output_thumbs_path}...")
response_thumbs = client.models.generate_content(
    model=sModel, contents=prompt_thumbs, config=types.GenerateContentConfig(temperature=0.1)
)
with open(output_thumbs_path, "w", encoding="utf-8") as f:
    f.write(response_thumbs.text)

print(f"Generiere Stufe 2: {output_cat_path}...")
response_cat = client.models.generate_content(
    model=sModel, contents=prompt_cat, config=types.GenerateContentConfig(temperature=0.1)
)
with open(output_cat_path, "w", encoding="utf-8") as f:
    f.write(response_cat.text)

print("\nFertig! Beide Programme wurden erfolgreich getrennt voneinander erzeugt:")
print(f"1. [{output_thumbs_path}] -> Für CPU/E570 (Bildvorbereitung & 2s-Takt-Log)")
print(f"2. [{output_cat_path}] -> Für GPU/Ryzen (KI-Analyse, Bulk-DB & 2s-Takt-Log)")
