# -*- coding: utf-8 -*-
"""
Dieses Skript berechnet die Fibonacci-Folge.
Es enthält eine robuste Funktion zur Generierung der Folge bis zu einer 
bestimmten Anzahl von Gliedern sowie ein kurzes Anwendungsbeispiel.
"""

from typing import List

def generiere_fibonacci(n: int) -> List[int]:
    """
    Generiert die ersten n Zahlen der Fibonacci-Folge.

    Parameter:
    n (int): Die Anzahl der zu generierenden Fibonacci-Zahlen.

    Rückgabe:
    List[int]: Eine Liste mit den ersten n Fibonacci-Zahlen.
    """
    # Validierung der Eingabe: Die Anzahl muss eine ganze Zahl sein.
    if not isinstance(n, int):
        raise TypeError("Die Anzahl der Glieder muss eine ganze Zahl sein.")
    
    # Wenn n kleiner oder gleich 0 ist, wird eine leere Liste zurückgegeben.
    if n <= 0:
        return []

    # Spezialfall für das erste Element: F(0) = 0
    if n == 1:
        return [0]

    # Initialisierung der Folge mit den ersten beiden Werten: F(0) = 0, F(1) = 1
    fib_folge = [0, 1]

    # Iterative Berechnung der weiteren Folgenglieder.
    # Jedes neue Glied ist die Summe der beiden vorhergehenden Glieder: F(i) = F(i-1) + F(i-2)
    for _ in range(2, n):
        naechste_zahl = fib_folge[-1] + fib_folge[-2]
        fib_folge.append(naechste_zahl)

    return fib_folge

# Hauptprogramm zur Demonstration der Funktion
if __name__ == "__main__":
    # Definition der Anzahl der gewünschten Fibonacci-Zahlen
    anzahl_glieder = 15

    print(f"Berechnung der ersten {anzahl_glieder} Fibonacci-Zahlen:")
    try:
        # Aufruf der Funktion und Ausgabe des Ergebnisses
        ergebnis = generiere_fibonacci(anzahl_glieder)
        print(ergebnis)
    except TypeError as fehler:
        print(f"Fehler bei der Berechnung: {fehler}")