import os
from google import genai  # Neues Google GenAI SDK
from git import Repo      # GitPython Bibliothek

# --- KONFIGURATION ---
client = genai.Client() 

LOCAL_REPO_PATH = r"E:\dev_priv\git\KI-Sprech"
FILE_NAME = "creasockel.py"
sModel = "gemini-3.5-flash"  # Ihr funktionierendes Modell

# ERWEITERTER PROMPT
PROMPT = (
"Du bist ein erfahrener Software-Architekt für Python und ein Experte für 2D Bin Packing, Nesting und erstellst optimale Lösungen für das Cutting Stock Problem.\n"
"Deine Spezialgebiete sind das Lösen von Zweidimensionalen Behälterproblemen, das automatisierte Anordnen von Teilen und 2D-Verschnittoptimierung.\n"
"Ich arbeite in Visual Studio Community und plane ein Optimierungs-Script in Python, das berechnet, wie Fliesenreste in eine Fläche mit Breite B und Höhe H eingefügt werden können, dass ein für das menschliche Auge harmonisches Bild entsteht.\n\n"
"Hier sind die neuen Rahmenbedingungen für das Zielsystem:\n"
"1. Die Ziel-Fläche mit Breite B=6,2 m (620 cm) und Höhe H=0,3 m (30 cm)\n"
"2. Die Fliesenreste, jeweils mit Breite B (5 <= B <= 100 cm) und Höhe H (5 <= H <= 100 cm) liegen in einer json-Datei vor.\n"
"3. Für den Test soll eine Datei fliesenreste.json mit 40 Einträgen erzeugt werden. Jeder Eintrag soll eine random-Breite TB (5 <= TB <= 100 cm) und random-Höhe TH haben: (5 <= TB <= 100 cm) (5 <= TH <= 100 cm)\n"
"4. Die json-Datei fliesenreste.json soll nur dann erzeugt werden, wenn sie noch nicht existiert\n"
"5. fliesenreste.json soll komplett eingelesen werden\n"
"6. Das zu erstellende Script soll für das Ergebnis der Berechnung eine Datei im HTML-Format speichern, die in google chrome angezeigt werden kann.\n"
"7. Für das Generieren des HTML-Codes bitte die Logik von https://github.com analysieren, nachnutzen und für den Sockelverband (Flächenhöhe 30cm) adaptieren.\n\n"
"WICHTIGE SYNTAX-REGEL FÜR RECHTSCHREIB-STILE & F-STRINGS:\n"
"Achte penibel darauf, dass innerhalb von f-Strings (formatierten Strings) keine doppelten Anführungszeichen verschachtelt werden! "
"Wenn ein f-String mit doppelten Anführungszeichen beginnt (z.B. f\"... \"), müssen alle inneren Strings, wie HTML-Klassennamen oder Dictionary-Keys, zwingend einfache Anführungszeichen verwenden (z.B. 'badge-red' oder tile['cuts']). Vermeide Syntax-Fehler durch doppelte Anführungszeichen im Inneren von f-Strings.\n\n"
"DEINE AUFGABE:\n"
"Schreibe mir ein einziges, konsolidiertes und optimiertes Python-Skript (creasockel.py). Gib den Code formatiert in einem standardmäßigen Markdown-Codeblock (mit ```python) aus."
)

try:
    # --- 1. PROMPT AN GEMINI SENDEN ---
    print(f"Generiere Code mit {sModel}...")
    response = client.models.generate_content(
        model=sModel,
        contents=PROMPT,
    )
    generated_code = response.text

    # --- 2. AUTOMATISCHE MARKDOWN-ENTFERNUNG (KORRIGIERT) ---
    # Wir spalten den Text sauber auf und isolieren den Inhalt zwischen den Backticks
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    # --- 3. DATEI IM REPO SPEICHERN ---
    file_path = os.path.join(LOCAL_REPO_PATH, FILE_NAME)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(generated_code)
    print(f"Datei erfolgreich gespeichert unter: {file_path}")

    # --- 4. GIT COMMIT & PUSH ---
    print("Starte Git-Vorgang...")
    repo = Repo(LOCAL_REPO_PATH)
    
    repo.index.add([FILE_NAME])
    
    commit_message = f"Feat: Script automatisch durch {sModel} erstellt"
    new_commit = repo.index.commit(commit_message)
    print(f"Erfolgreich lokal committet! Commit-SHA: {new_commit.hexsha}")
    
    print("Pushe Änderungen zu GitHub (grasmax/KI-Sprech)...")
    origin = repo.remote(name='origin')
    origin.push()
    print("Erfolgreich in das GitHub-Repository hochgeladen!")

except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")
