"""Messskript der vorgerechneten Messreihen: schreibt `vsd_messungen.json` (Konflikte je Lauf, Antwort, Länge der gelernten Klauseln).

Aufruf (aus dem Repo-Ordner, mit dem Test- oder Runtime-venv):
    python tools/messungen.py --zellen zufall100 zufall150 --out teil_a.json       # eine Teilmenge der Zellen messen
    python tools/messungen.py --zusammenfuegen teil_a.json teil_b.json             # Teile zu vsd_messungen.json vereinen
    python tools/messungen.py --alle                                               # alle Zellen, direkt nach vsd_messungen.json

Die Zellen und ihre Verfahren stehen in `vsd_constants.py` (ZELLEN_AKTIVITAET, ZELLEN_PHASE, ZELLEN_ZERFALL); gemessen wird mit
denselben Funktionen wie in den Live-Messreihen der App (`vsd_evaluation.messe_zelle`). Aufwand wird in Konflikten gezählt, nie in Sekunden;
die Laufzeit des Skripts (für Schur n = 44 mehrere Minuten) ist kein Messwert.
"""

import argparse
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import vsd_constants as C  # noqa: E402
import vsd_evaluation as E  # noqa: E402

ALLE = tuple(dict.fromkeys(C.ZELLEN_AKTIVITAET + C.ZELLEN_PHASE + C.ZELLEN_ZERFALL))


def schreibe(daten: dict, ziel: Path) -> None:
    """Eine Zelle je Zeile (gut zu vergleichen), Zählwerte kompakt."""
    zeilen = ['{', f'"version": 1, "kern": "832b2c10dfdea62d", "budget": {C.BUDGET_REFERENZ},', '"zellen": {']
    schluessel = [k for k in ALLE if k in daten["zellen"]]
    for i, k in enumerate(schluessel):
        zeilen.append(f'{json.dumps(k)}: {json.dumps(daten["zellen"][k], ensure_ascii=False, separators=(",", ":"))}' + ("," if i < len(schluessel) - 1 else ""))
    zeilen += ["}", "}"]
    ziel.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--zellen", nargs="+", choices=ALLE, help="diese Zellen messen")
    p.add_argument("--alle", action="store_true", help="alle Zellen messen")
    p.add_argument("--out", type=Path, help="Zieldatei (Standard bei --alle: vsd_messungen.json)")
    p.add_argument("--zusammenfuegen", nargs="+", type=Path, help="Teildateien zu vsd_messungen.json vereinen")
    a = p.parse_args()
    if a.zusammenfuegen:
        daten = {"zellen": {}}
        for pfad in a.zusammenfuegen:
            daten["zellen"].update(json.loads(pfad.read_text(encoding="utf-8"))["zellen"])
        schreibe(daten, HIER / "vsd_messungen.json")
        print("zusammengefügt:", ", ".join(daten["zellen"]))
        return
    zellen = ALLE if a.alle else (a.zellen or [])
    if not zellen:
        p.error("--zellen, --alle oder --zusammenfuegen angeben")
    ziel = a.out or HIER / "vsd_messungen.json"
    daten = {"zellen": {}}
    for k in zellen:
        z = E.messe_zelle(k, E.verfahren_der_zelle(k))
        daten["zellen"][k] = z
        schreibe(daten, ziel)
        zusammen = {v: E.kennzahlen(m) for v, m in z["verfahren"].items()}
        print(k, {v: (kz.median, kz.maximum, kz.abbrueche) for v, kz in zusammen.items()}, flush=True)


if __name__ == "__main__":
    main()
