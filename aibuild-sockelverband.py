import os
from google import genai  # Neues Google GenAI SDK
from git import Repo      # GitPython Bibliothek

# --- KONFIGURATION ---
# Das SDK liest Ihre Windows-Umgebungsvariable GEMINI_API_KEY automatisch aus
client = genai.Client() 

# Ihr lokaler Repository-Pfad
LOCAL_REPO_PATH = r"E:\dev_priv\git\KI-Sprech"
FILE_NAME = "creasockel.py"
sModel = "gemini-3.5-flash" #gemini-2.5-pro" #"gemini-3.1-pro-preview" # gemini-1.5-pro"#"gemini-3.7-flash"

# Optimierter System-Prompt nach Ihren Repository-Regeln:
PROMPT = (
"Du bist ein erfahrener Software-Architekt für Python und ein Experte für 2D Bin Packing, Nesting und erstellst optimale Lösungen für das Cutting Stock Problem. "
"Deine Spezialgebiete sind das Lösen von Zweidimensionales Behälterproblemen, das automatisierte Anordnen von Teilen und 2D-Verschnittoptimierung."
"Ich arbeite in Visual Studio Community und plane ein Optimierungs-Script in python, das berechnet, wie Fliesenreste in eine Fläche mit Breite B und Höhe H eingefügt werden können, dass ein für das menschliche Auge harmonisches Bild entsteht. "
"Hier sind die neuen Rahmenbedingungen für das Zielsystem:"
"1. Die Ziel-Fläche mit Breite B=6,2 m und Höhe H=0,3 m"
"2. Die Fliesenreste, jeweils mit Breite B (5 <= B <= 100 cm) und Höhe H (5 <= H <= 100cm) liegen in einer json-Datei vor."
"3. Für den Test soll eine Datei fliesenreste.json mit 40 Einträgen erzeugt werden. Jeder Eintrag soll eine random-Breite TB (5 <= TB <= 100 cm)und random-Höhe TH haben: (5 <= TB <= 100 cm) (5 <= TH <= 100cm)"
"4. die json-Datei fliesenreste.json soll nur dann erzeugt werden, wenn sie noch nicht existiert"
"5. fliesenreste.json soll komplett eingelesen werden"
"6. Das zu erstellende Script soll für das Ergebnis der Berechnung eine Datei im HTML-Format speichern, die in google chrome angezeigt werden kann."
"7. Für das Generieren des HTML-Codes bitte  https://github.com/grasmax/wildverband/blob/main/plan4.py analysieren und nachnutzen"
"DEINE AUFGABE:"
"Schreibe mir ein einziges, konsolidiertes und optimiertes Python-Skript (creasock.py)"
"Schreibe das gesamte Skript in einen einzigen, zusammenhängenden Code-Block. Unterbrich den Code unter keinen Umständen für Erklärungen oder Zwischenüberschriften. Teile den Code nicht in mehrere Blöcke auf, selbst wenn er sehr lang ist. Erklärungen sind nicht gewünscht – gib ausschließlich den reinen, ausführbaren Code in diesem einen Block aus."
)

try:
    # --- 1. PROMPT AN GEMINI 3.7 FLASH SENDEN ---
    print(f"Generiere Code mit {sModel}...")
    response = client.models.generate_content(
        model=sModel,
        contents=PROMPT,
    )
    generated_code = response.text

    # --- 2. DATEI IM REPO SPEICHERN ---
    file_path = os.path.join(LOCAL_REPO_PATH, FILE_NAME)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(generated_code)
    print(f"Datei erfolgreich gespeichert unter: {file_path}")

    # --- 3. GIT COMMIT & PUSH ---
    print("Starte Git-Vorgang...")
    repo = Repo(LOCAL_REPO_PATH)
    
    # Entspricht: git add fibonacci.py
    repo.index.add([FILE_NAME])
    
    # Entspricht: git commit -m "..."
    commit_message = f"Feat: Script automatisch durch {sModel} erstellt"
    new_commit = repo.index.commit(commit_message)
    print(f"Erfolgreich lokal committet! Commit-SHA: {new_commit.hexsha}")
    
    # Entspricht: git push origin main (bzw. aktiver Branch)
    print("Pushe Änderungen zu GitHub (grasmax/KI-Sprech)...")
    origin = repo.remote(name='origin')
    origin.push()
    print("Erfolgreich in das GitHub-Repository hochgeladen!")

except Exception as e:
    print(f"Ein Fehler ist in aubuild.py aufgetreten: {e}")

