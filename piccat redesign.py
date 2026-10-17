import os
from google import genai
from google.genai import types

# 1. API-Client initialisieren
# Der API-Key wird automatisch aus der Windows-Umgebungsvariable GEMINI_API_KEY geladen.
client = genai.Client()

# Pfade zu Ihren bestehenden Skripten im Visual Studio Projektordner
client_script_path = "piccat_client_x2x4x16.py"
server_script_path = "piccat_server_x16.py"
output_script_path = "piccat_server_neu.py"

# Modell-Auswahl für Oktober 2026: 'gemini-3.7-flash' ist im Free-Tier kostenlos, 
# extrem schnell und hochpräzise bei der Code-Generierung.
sModel = "gemini-3.7-flash"

print("Lese bestehende Quelldateien ein...")

# 2. Inhalt der alten Skripte einlesen
try:
    with open(client_script_path, "r", encoding="utf-8") as f:
        client_code = f.read()
except FileNotFoundError:
    print(f"Fehler: {client_script_path} wurde nicht gefunden. Bitte Pfad prüfen.")
    exit(1)

try:
    with open(server_script_path, "r", encoding="utf-8") as f:
        server_code = f.read()
except FileNotFoundError:
    print(f"Fehler: {server_script_path} wurde nicht gefunden. Bitte Pfad prüfen.")
    exit(1)

# 3. Den optimierten Architektur-Prompt mit den Code-Inhalten zusammenbauen
prompt_text = f"""Du bist ein erfahrener Software-Architekt für Python, Computer Vision und High-Performance Deep Learning. 
Deine Spezialgebiete sind Bildverarbeitung und Bild-Kategorisierung unter Verwendung von PyTorch (torch, torchvision), OpenCV und CUDA-basiertem GPU-Computing. 

Ich arbeite in Visual Studio Community und plane ein Refactoring meines Bildanalyse-Projekts "piccat". 

Hier sind die neuen Rahmenbedingungen für das Zielsystem:
1. Die Bilddateien liegen lokal auf einer externen USB-3.0-Festplatte (HDD), die direkt an den schnellen Gaming-PC angeschlossen ist. Es findet KEINE Bildübertragung über das Netzwerk statt.
2. Das Einlesen der Bilder und die gesamte Verarbeitung sollen komplett auf diesem PC (AMD Ryzen 7 7800X3D und NVIDIA RTX 5060 Ti) stattfinden.
3. Nur die finalen Analyse-Ergebnisse (Metadaten/Ergebnisdaten) sollen am Ende in eine externe MariaDB auf einem Raspberry Pi geschrieben werden.
4. Die alte Server-Netzwerk-Hülle (FastAPI, Uvicorn, Sockets, Request-Handler, Netzwerk-Listener) wird nicht mehr benötigt und soll komplett entfernt werden.

DEINE AUFGABE:
Schreibe mir ein einziges, konsolidiertes und optimiertes Python-Skript (piccat_server_neu.py) für den Gaming-PC.
- Übernehme die Logik für das Einlesen und Vorverarbeiten (Skalieren auf 224x224 bzw. 336x336 via Pillow) der Bilddateien aus der Client-Datei.
- Integriere die CLIP-Analyse-Logik aus der Server-Datei und optimiere sie für CUDA und FP16 (Half Precision).
- Da die Bilder von einer mechanischen USB-HDD gelesen werden, implementiere ein asynchrones Producer-Consumer-Muster mit einer Queue. Ein Hintergrund-Thread muss die Bilder von der USB-Platte vorladen, während die GPU parallel die Batches verarbeitet, damit die GPU niemals auf den I/O-Unterbau warten muss.
- Entferne die gesamte Netzwerk-Server-Hülle (FastAPI) sowie die binäre Serialisierung (struct.pack/unpack). Die Bilder werden direkt im RAM als PyTorch-Tensoren übergeben.
- Passe das Speichern so an, dass die Ergebnisse via Bulk-Insert direkt in die externe MariaDB auf dem Raspberry Pi geschrieben werden (nutze dafür das native Modul 'mariadb'). Schreibe die Daten in Paketen (z. B. nach jedem Ordner oder nach 1000 Bildern), um den Netzwerk-Overhead zum Raspi zu minimieren.

Hier ist der Code der beiden Dateien:

=== START DATEI: piccat_client_x2x4x16.py ===
{client_code}
=== ENDE DATEI: piccat_client_x2x4x16.py ===

=== START DATEI: piccat_server_x16.py ===
{server_code}
=== ENDE DATEI: piccat_server_x16.py ===

Fasse alle notwendigen Codefragmente in einer einzigen Datei zusammen und gib mir als Ausgabe NUR den finalen, einsatzbereiten Python-Code aus, damit ich ihn direkt in ein lokales Git-Repository committen kann. Antworte ohne umschließende Markdown-Code-Blöcke (keine ```python-Tags), sondern liefere ausschließlich den reinen Skriptinhalt."""

print(f"Sende Code und Architektur-Prompt an Gemini ({sModel})...")

# 4. API-Aufruf an das ausgewählte Modell
# Temperature 0.1 sorgt für strikt logische Einhaltung der Programmiervorgaben.
response = client.models.generate_content(
    model=sModel,
    contents=prompt_text,
    config=types.GenerateContentConfig(
        temperature=0.1,
    )
)

# 5. Das generierte Skript direkt abspeichern
print(f"Refactoring abgeschlossen. Schreibe Ergebnis in {output_script_path}...")
with open(output_script_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print("Fertig! Die Datei kann jetzt in Visual Studio geöffnet und auf dem E570 getestet werden.")





Du bist ein erfahrener Software-Architekt für Python, Computer Vision und High-Performance Deep Learning. 
Deine Spezialgebiete sind Bildverarbeitung und Bild-Kategorisierung unter Verwendung von PyTorch (torch, torchvision), OpenCV und CUDA-basiertem GPU-Computing. 


Ich arbeite in Visual Studio Community und plane ein Refactoring meines Bildanalyse-Projekts "piccat". 

Hier sind die neuen Rahmenbedingungen für das Zielsystem:
1. Die Bilddateien liegen lokal auf einer externen USB-3.0-Festplatte, die direkt an den schnellen Gaming-PC (Server) angeschlossen ist. Es findet KEINE Bildübertragung über das Netzwerk statt.
2. Das Einlesen der Bilder und die gesamte Verarbeitung sollen komplett auf diesem Server stattfinden.
3. Nur die finalen Analyse-Ergebnisse (Metadaten/Ergebnisdaten) sollen am Ende in eine externe MariaDB auf einem Raspberry Pi geschrieben werden.
4. Die alte Server-Netzwerk-Hülle (z. B. Sockets, Request-Handler, Netzwerk-Listener) wird nicht mehr benötigt und soll komplett entfernt werden.

Ich stelle dir unten den Code der beiden bisherigen Dateien zur Verfügung:
- "piccat_client_x2x4x16.py" (enthält aktuell die Logik für das Einlesen und Speichern)
- "piccat_server_x16.py" (enthält die Analyse-Logik und die alte Server-Netzwerk-Infrastruktur)

DEINE AUFGABE:
Schreibe mir ein einziges, konsolidiertes und optimiertes Python-Skript (piccat_server_neu.py) für den Gaming-PC mit diesen Komponenten ########. 
- Übernehme die Logik für das Einlesen der Bilddateien aus der Client-Datei.
- Integriere die Analyse-Logik aus der Server-Datei.
- Entferne die gesamte Netzwerk-Server-Hülle aus der Server-Datei.
- Passe das Speichern so an, dass die Ergebnisse direkt in die externe MariaDB auf dem Raspberry Pi geschrieben werden (nutze dafür eine saubere SQL-Verbindung, z.B. via mysql-connector-python oder PyMySQL).
- Optimiere den Code für die Ausführung auf einem schnellen Gaming-PC (z. B. effizientes I/O-Handling beim Einlesen von der USB-Festplatte).

Hier ist der Code der beiden Dateien:

=== START DATEI: https://github.com/grasmax/piccat/blob/main/piccat_client_x2x4x16.py ===
[Diese Datei soll nicht geändert werden. Es sollen nur die Code-Teile für das Einlesen der Bilddateien und für das Speichern der Ergebnisse in die piccat_server_neu.py zu übertragen.]
=== ENDE DATEI: piccat_client_x2x4x16.py ===

=== START DATEI: https://github.com/grasmax/piccat/blob/main/piccat_server_x16.py ===
[Diese Datei soll nicht geändert werden. Es sollen nur die Code-Teile für das Kategorisieren und Speichern der Ergebnisse übernommen werden.]
=== ENDE DATEI: piccat_server_x16.py ===

Fasse alle notwendigen Codefragement in einer Datei zusammen und gib mir als Ausgabe NUR den finalen, einsatzbereiten Python-Code aus, damit ich ihn direkt in ein lokales Git-Repository committen kann.
