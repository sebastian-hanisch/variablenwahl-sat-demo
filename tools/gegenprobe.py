"""Gegenprobe der Referenz mit anderen festen Formelmengen (README, Abschnitt „Stabilität“; nicht Teil der Tests).

Zufall n = 150: Seeds 3000 bis 3011 statt 2000 bis 2011, Rampen n = 160: Seeds 700 bis 709 statt 500 bis 509; sonst dieselben Verfahren, dasselbe
Budget und dieselben Funktionen wie `tools/messungen.py`. Ausgabe: Median, Maximum und Abbrüche je Verfahren. Aufruf aus dem Repo-Ordner:
    python tools/gegenprobe.py
Die Rechnung dauert mehrere Minuten (die feste Reihenfolge erreicht bei Zufall n = 150 oft das Budget).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vsd_constants as C  # noqa: E402
import vsd_evaluation as E  # noqa: E402

C.ZUFALL_SEEDS = tuple(range(3000, 3012))
C.RAMPEN_SEEDS = tuple(range(700, 710))

for zelle in ("rampen160", "zufall150"):
    z = E.messe_zelle(zelle, E.verfahren_der_zelle(zelle))
    print(zelle, {v: (k.median, k.maximum, k.abbrueche) for v, k in ((v, E.kennzahlen(m)) for v, m in z["verfahren"].items())}, flush=True)
