"""Formeln der Demo: das Handbeispiel F3, kleine Zufallsformeln für die Schritt-für-Schritt-Ansicht und die Aufgaben der Messreihen.

Alle Zufallsformeln laufen über SplitMix64 (`vsd_rng`), nie über Python-`random`: gleiche Eingabe, gleiche Formel auf jeder Plattform.
Ein Lauf einer Messreihe ist ein Tripel (Beschriftung, Instanz, Zufalls-Seed des Lösers oder None). Bei Formelfamilien (Zufall, Rampen)
gibt es je Formel einen Lauf ohne Zufall im Löser; bei Schur gibt es eine feste Instanz und je Zufalls-Seed des Lösers einen Lauf
(zufälliger Start der Aktivitäten).
"""

from typing import NamedTuple

import vsd_constants as C
from vsd_instanzen import Instanz, rampen_instanz, rand3, schur

# Handbeispiel F3 aus dem Plan: 7 Variablen, 14 Klauseln (Literale als Ganzzahlen, -3 = „nicht x3“)
F3_KLAUSELN = (
    (4, -1, 3), (-7, -4, 1), (-1, 4, -3), (5, 6, 1), (2, 7, 5), (-5, 4, -6), (6, 7, -3),
    (4, -3, -5), (-3, 7, -4), (1, 4, 5), (2, 3, 6), (6, -7, 1), (2, -5, -6), (-6, -7, 4),
)
F3_N = 7


class Lauf(NamedTuple):
    label: str
    inst: Instanz
    seed: int | None      # Zufalls-Seed des Lösers (zufälliger Start der Aktivitäten) oder None


def hand_formel() -> Instanz:
    return Instanz(F3_N, [tuple(k) for k in F3_KLAUSELN], {"art": "handbeispiel"})


def klauselzahl(n: int) -> int:
    """Klauseln der Zufallsformel: 4,26 je Variable, gerundet."""
    return int(round(C.VERHAELTNIS * n))


def kleine_formel(n: int, seed: int) -> Instanz:
    """Zufalls-3-SAT für die Schritt-für-Schritt-Ansicht (n = 8 bis 12, höchstens 60 Klauseln)."""
    n = max(C.KLEIN_N[0], min(C.KLEIN_N[1], int(n)))
    return rand3(n, klauselzahl(n), int(seed))


def laeufe(art: str, groesse: int, anzahl: int) -> list[Lauf]:
    """Die festen Läufe einer Aufgabe: die ersten `anzahl` festen Formeln bzw. Zufalls-Seeds des Lösers."""
    if art == "zufall":
        m = klauselzahl(groesse)
        seeds = C.ZUFALL_SEEDS[:anzahl]
        return [Lauf(f"Formel {i + 1}", rand3(groesse, m, s), None) for i, s in enumerate(seeds)]
    if art == "rampen":
        seeds = C.RAMPEN_SEEDS[:anzahl]
        return [Lauf(f"Graph {i + 1}", rampen_instanz(groesse, C.RAMPEN_GRAD, s, C.RAMPEN_K), None) for i, s in enumerate(seeds)]
    if art == "schur":
        inst = schur(groesse, C.SCHUR_K)
        return [Lauf(f"Löser-Seed {s}", inst, s) for s in C.LOESER_SEEDS[:anzahl]]
    raise ValueError(f"unbekannte Art {art!r}")


def laeufe_der_aufgabe(schluessel: str) -> list[Lauf]:
    a = C.AUFGABEN[schluessel]
    return laeufe(a["art"], a["groesse"], a["anzahl"])
