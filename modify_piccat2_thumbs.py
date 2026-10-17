import os
import subprocess
from google import genai
from google.genai import types

# 1. API-Client initialisieren
client = genai.Client()

# Pfade definieren
target_script_path = "piccat2_thumbs.py"
sModel = "gemini-3.7-flash"

print(f"Lese aktuelle Version von {target_script_path} ein...")

# 2. Bestehenden Code einlesen
try:
    with open(target_script_path, "r", encoding="utf-8") as f:
        existing_code = f.read()
except FileNotFoundError:
    print(f"Fehler: {target_script_path} wurde nicht gefunden. Bitte Pfad prüfen.")
    exit(1)

# 3. Den präzisen Update-Prompt formulieren
prompt_text = f"""Du bist ein erfahrener Python-Entwickler und Performance-Architekt. 
Deine Aufgabe ist es, das bestehende Skript 'piccat2_thumbs.py' gezielt um drei Features zu erweitern, ohne die bestehende Kern-Logik (os.walk, Pillow-Skalierung, Cache-Ordner-Struktur) zu zerstören.

HIER SIND DIE DREI NEUEN AUFGABEN:

1. EXIF-WARNUNGEN ABFANGEN & DATEINAMEN ANZEIGEN:
   - Modifiziere die Fortschrittsschleife oder den Fehler-Block so, dass bei einer 'UserWarning' von Pillow (z.B. 'Corrupt EXIF data') abgefangen wird, welches Bild exakt betroffen ist. 
   - Das Programm soll bei einer solchen Warnung den Pfad oder Namen des aktuellen Bildes in der Konsole ausgeben, anstatt die Warnung unformatiert in die Fortschrittszeile zu schreiben.

2. START-, ENDE- UND LAUFZEIT-LOGGING:
   - Erweitere die finale, maximal 10 Zeilen lange Zusammenfassung am Ende so, dass sie neben der Gesamtlaufzeit auch den exakten Start-Zeitpunkt und den Ende-Zeitpunkt im Format 'HH:MM:SS' anzeigt.

3. PROGNOSE-ENDZEIT (ETA) IM 2-SEKUNDEN-TAKT:
   - Erweitere die bestehende Fortschrittszeile, die alle 2 Sekunden ausgegeben wird, um eine mathematisch korrekte Endzeit-Prognose (ETA).
   - WICHTIG FÜR DIE BERECHNUNG: Die bereits übersprungenen (bereits gecachten) Bilder dürfen NICHT in die Berechnung der verbleibenden Zeit einfließen! 
   - Berechne die Geschwindigkeit (Bilder/Sek) ausschließlich auf Basis der TATSÄCHLICH NEU verarbeiteten Bilder seit dem Start des Skripts und der dafür vergangenen Zeit.
   - Die verbleibende Restzeit berechnet sich dann wie folgt: (Tatsächlich noch zu verarbeitende Bilder) geteilt durch (Tatsächliche Bilder/Sek). 
   - Addiere diese Restzeit auf die aktuelle Uhrzeit auf und zeige das Ergebnis im Format 'ETA: HH:MM:SS' an.



Hier ist der aktuelle Code der Datei:
=== START DATEI: piccat2_thumbs.py ===
{existing_code}
=== ENDE DATEI: piccat2_thumbs.py ===

Liefere als Ausgabe NUR den modifizierten, einsatzbereiten Python-Code für das Skript. Antworte ohne umschließende Markdown-Code-Blöcke (keine ```python-Tags)."""

print(f"Sende Code an Gemini ({sModel}) für die Erweiterungen...")

# 4. API-Aufruf an das Modell abfeuern
response = client.models.generate_content(
    model=sModel,
    contents=prompt_text,
    config=types.GenerateContentConfig(
        temperature=0.1,  # Sehr niedrig für exakte Code-Modifikation
    )
)

# 5. Modifizierten Code zurückschreiben
print(f"Schreibe aktualisierten Code zurück in {target_script_path}...")
with open(target_script_path, "w", encoding="utf-8") as f:
    f.write(response.text)

# 6. Automatisiertes Git Commit und Push
print("\nStarte Git-Automatisierung...")
try:
    # Git Add
    subprocess.run(["git", "add", target_script_path], check=True)
    
    # Git Commit mit einer präzisen Nachricht
    commit_message = "Feat: Add ETA prognosis, detailed EXIF warning logs, and start/end time to piccat2_thumbs"
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    
    # Git Push (lädt es direkt auf GitHub hoch)
    print("Pushe Änderungen zu GitHub...")
    subprocess.run(["git", "push"], check=True)
    
    print("\n[SUCCESS] Skript erfolgreich aktualisiert und auf GitHub gesichert!")

except subprocess.CalledProcessError as git_err:
    print(f"\n[WARNUNG] Git-Befehl fehlgeschlagen. Der Code wurde lokal gespeichert, aber nicht übertragen: {git_err}")
except FileNotFoundError:
    print("\n[WARNUNG] 'git' Befehl nicht gefunden. Stellen Sie sicher, dass Git installiert und im System-Pfad (PATH) hinterlegt ist.")

