import os
from google import genai  # Neues Google GenAI SDK
from git import Repo      # GitPython Bibliothek

# --- KONFIGURATION ---
# Das SDK liest Ihre Windows-Umgebungsvariable GEMINI_API_KEY automatisch aus
client = genai.Client() 

# Ihr lokaler Repository-Pfad
LOCAL_REPO_PATH = r"E:\dev_priv\git\KI-Sprech"
FILE_NAME = "fibonacci.py"
sModel = "gemini-3.5-flash" #gemini-2.5-pro" #"gemini-3.1-pro-preview" # gemini-1.5-pro"#"gemini-3.7-flash"

# Optimierter System-Prompt nach Ihren Repository-Regeln:
PROMPT = (
    "Schreibe ein sauberes Python-Skript, das die Fibonacci-Folge berechnet. "
    "Gib das komplette Skript in einem einzigen, ununterbrochenen Code-Block aus. "
    "Teile den Code nicht auf. Wenn du Erklärungen oder Hinweise hast, füge diese "
    "ausschließlich als standardisierte Kommentare direkt in den Code-Block ein. "
    "Gib keinen Markdown-Container wie ```python aus."
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
    print(f"Ein Fehler ist aufgetreten: {e}")
