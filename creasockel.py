# ==============================================================================
# Fibonacci-Folge in Python
# ==============================================================================
# Dieses Skript bietet zwei Implementierungen zur Berechnung der Fibonacci-Folge:
# 1. Eine iterative Methode (gibt eine Liste der ersten N Zahlen zurück)
# 2. Eine Generator-Methode (speicherschonend für sehr große Sequenzen)
# ==============================================================================

def fibonacci_iterativ(n: int) -> list:
    """
    Berechnet die ersten n Fibonacci-Zahlen und gibt sie als Liste zurück.
    
    Parameter:
    n (int): Die Anzahl der zu berechnenden Fibonacci-Zahlen.
    
    Rückgabe:
    list: Liste mit den ersten n Fibonacci-Zahlen.
    """
    # Validierung der Eingabe: Nur positive Ganzzahlen sind erlaubt
    if not isinstance(n, int) or n <= 0:
        return []
    
    # Spezialfall für n = 1
    if n == 1:
        return [0]
    
    # Startwerte der Fibonacci-Folge (F(0) = 0, F(1) = 1)
    folge = [0, 1]
    
    # Iterative Berechnung der restlichen Zahlen
    # Jedes neue Element ist die Summe der beiden vorherigen Elemente
    for _ in range(2, n):
        naechste_zahl = folge[-1] + folge[-2]
        folge.append(naechste_zahl)
        
    return folge


def fibonacci_generator():
    """
    Ein Python-Generator, der unendlich viele Fibonacci-Zahlen nacheinander erzeugt.
    Vorteil: Benötigt nahezu keinen Arbeitsspeicher, da Werte 'on the fly'
    berechnet und nicht im Speicher gehalten werden.
    """
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


# Hauptprogramm zur Demonstration der Funktionsweise
if __name__ == "__main__":
    # Definition der Anzahl der zu berechnenden Zahlen
    anzahl = 12
    
    print(f"--- Demonstration 1: Iterativer Ansatz (erste {anzahl} Zahlen) ---")
    liste_ergebnis = fibonacci_iterativ(anzahl)
    print(f"Ergebnis-Liste: {liste_ergebnis}")
    print()
    
    print(f"--- Demonstration 2: Generator-Ansatz (erste {anzahl} Zahlen) ---")
    # Instanziierung des Generators
    fib_gen = fibonacci_generator()
    
    # Abrufen der Werte über eine Schleife mittels next()
    generator_ergebnis = []
    for _ in range(anzahl):
        generator_ergebnis.append(next(fib_gen))
        
    print(f"Ergebnis-Generator: {generator_ergebnis}")