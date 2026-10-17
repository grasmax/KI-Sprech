# KI-Sprech

Hier werden Code-Fragmente gesammelt, die beim Entwickeln von python-Programmen mit google gemini entstanden sind.
Dabei geht man am besten so vor:
- In einem Prompt für die KI beschreiben, was der python-Code können soll; dazu google chrome verwenden. Beispiel siehe fibonacci.py
- Ein python-Script für die Auswahl des KI-Modells, die Ausführung des Prompts und die Sicherung des Ergebnis-Codes schreiben. Beispiel siehe piccat redesign.py
- Dieses Script in Visual Studio oder auf der Kommandozeile ausführen. Bei der Ausführung von piccat redesign.py entstehen dann z.B. die Dateien piccat2_*.py.
- Für die Fehlerbehebung und Weiterentwicklung von piccat2_*.py braucht es dann einen weiteren Prompt. Beispiel siehe modify_piccat2_thumbs.py


Wenn man nicht wie oben beschrieben mit prompt-Scripts arbeitet, sondern nur in einem Browser-Fenster, dann kommt der Ergebnis-Code oftmals unvollständig an, wenn man nicht mit genauesten Vorgaben wie diesen arbeitet (außerdem kann man nicht das KI-Modell festlegen):
## Der KI eine Rolle zuweisen
<img width="658" height="132" alt="image" src="https://github.com/user-attachments/assets/d39c9639-20bb-4dc2-9308-3f5ebce5e9cd" />

Mit der Formulierung („Du bist ein...“) in der ersten Zeile im Prompt wird in der KI eine feste Rolle oder Identität zuzuweisen (das sogenannte Role-Prompting).

## Vermeiden, dass das Ergebnis einer Abfrage in mehrere Blöcke zerissen wird:

„Schreibe das gesamte Skript in einen einzigen, zusammenhängenden Code-Block. Unterbrich den Code unter keinen Umständen für Erklärungen oder Zwischenüberschriften. Teile den Code nicht in mehrere Blöcke auf, selbst wenn er sehr lang ist. Erklärungen sind nicht gewünscht – gib ausschließlich den reinen, ausführbaren Code in diesem einen Block aus.“

## Etwas abgeschwächt:
„Gib das komplette Skript in einem einzigen, ununterbrochenen Code-Block aus. Teile den Code nicht auf. Wenn du Erklärungen oder Hinweise hast, füge diese ausschließlich als standardisierte Kommentare direkt in den Code-Block ein, sodass ich den gesamten Block am Stück kopieren kann.“
