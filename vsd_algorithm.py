"""Variablenwahl: der Löser mit seinen drei Schaltern (Wahl, Phasenspeicher, Zerfall) und die Schritt-für-Schritt-Aufbereitung.

Der CDCL steht in `vsd_cdcl` (wörtliche Kopie des Kern-Moduls). Dieses Modul ruft ihn mit den Schaltern der Demo auf und liest seine
`spur` (Ereignisse `entscheide`, `schliesse`, `konflikt`, `beteiligt`, `lerne`, `springe`) in Schritte um. Die Aufbereitung (`schritte`)
führt ihren eigenen Buchstand über Belegungen, Aktivitäten und gemerkte Phasen und vergleicht jede Entscheidung des Lösers mit der Wahl
der festen Reihenfolge (kleinste offene Variable).

Einheiten, einzeln getestet: `optionen`, `loese`, `literal_text`, `waehle_fest`, `waehle_aktivitaet` und `schritte`.
"""

from dataclasses import dataclass, field

import vsd_constants as C
from vsd_cdcl import Ergebnis, solve
from vsd_instanzen import Instanz

WAHL_AKTIVITAET, WAHL_FEST = "aktivitaet", "fest"


def optionen(wahl: str = WAHL_AKTIVITAET, phase: bool = True, zerfall: float = C.DEFAULT_ZERFALL) -> dict:
    """Optionen für `cdcl.solve`: Wahl nach Aktivität (VSIDS-Variante wie in MiniSat) oder feste Reihenfolge, Phasenspeicher an/aus,
    Zerfall der Aktivität. Neustarts (Luby) bleiben eingeschaltet. Der Zerfall liegt in [0,5; 1]: gegen 0 zählt nur der letzte Konflikt,
    das lässt die Demo nicht zu."""
    if wahl not in (WAHL_AKTIVITAET, WAHL_FEST):
        raise ValueError("Wahl muss WAHL_AKTIVITAET oder WAHL_FEST sein")
    if not (C.ZERFAELLE[0] <= zerfall <= 1.0):
        raise ValueError("Zerfall muss zwischen 0,5 und 1 liegen")
    return {"vsids": wahl == WAHL_AKTIVITAET, "phase_saving": bool(phase), "decay": float(zerfall),
            "restarts": "luby", "restart_unit": C.NEUSTART_EINHEIT}


def loese(inst: Instanz, wahl: str = WAHL_AKTIVITAET, phase: bool = True, zerfall: float = C.DEFAULT_ZERFALL,
          budget: int | None = None, seed: int | None = None, trace: bool = False) -> Ergebnis:
    """Löst die Formel. `seed` (Zufalls-Seed des Lösers) schaltet den zufälligen Start der Aktivitäten ein; ohne ihn starten alle bei 0."""
    return solve(inst.n, inst.klauseln, conflict_budget=budget, trace=trace, noise=seed is not None, seed=seed or 0,
                 **optionen(wahl, phase, zerfall))


# --------------------------------------------------------------------------------------------------------------------------------- Texte
def literal_text(lit: int) -> str:
    return f"x{lit}" if lit > 0 else f"¬x{-lit}"


def klausel_text(klausel) -> str:
    return "(" + " ∨ ".join(literal_text(l) for l in klausel) + ")"


def wert_text(lit: int) -> str:
    return "wahr" if lit > 0 else "falsch"


def zahl_text(x: float) -> str:
    """Aktivität bzw. Zuwachs: ganze Werte ohne Nachkommastelle, sonst mit Komma (zwei Stellen)."""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.2f}".replace(".", ",")


# --------------------------------------------------------------------------------------------------------------------------------- Wahl
def waehle_fest(n: int, belegt) -> int | None:
    """Wahl der festen Reihenfolge: die kleinste offene Variable (None, wenn alle belegt sind)."""
    return next((v for v in range(1, n + 1) if v not in belegt), None)


def waehle_aktivitaet(n: int, belegt, aktivitaet: dict) -> int | None:
    """Wahl nach Aktivität: die offene Variable mit der höchsten Aktivität, bei Gleichstand die kleinste Nummer."""
    offen = [v for v in range(1, n + 1) if v not in belegt]
    return min(offen, key=lambda v: (-aktivitaet[v], v)) if offen else None


# --------------------------------------------------------------------------------------------------------------------------------- Schritte
@dataclass
class Schritt:
    """Zustand der Suche nach einem Ereignis der Spur."""
    nr: int
    art: str                      # entscheide, schliesse, konflikt, beteiligt, lerne, springe, neustart, loesche
    text: str
    stufe: int
    belegung: list = field(default_factory=list)        # [(Literal, Stufe, Grund als „K5“ oder None)] in Reihenfolge der Belegung
    aktivitaet: dict = field(default_factory=dict)      # Variable -> Aktivität
    zuwachs: float = 1.0                                # Zuwachs, den der nächste Konflikt vergibt
    konflikte: int = 0
    entscheidungen: list = field(default_factory=list)  # alle Entscheidungen bis hier (Dictionaries)
    gelernt: list = field(default_factory=list)         # [(Klausel, Sprungstufe)]
    hervorgehoben: tuple = ()                           # Variablen, die dieses Ereignis betrifft (Entscheidung, Beteiligte)


def schritte(spur: list, n: int, zerfall: float, phasenspeicher: bool = True, vsids: bool = True) -> list[Schritt]:
    """Liest eine Spur (`Ergebnis.spur`, nur mit trace=True) in eine Folge von Schritten um, einen je Ereignis.

    Der Buchstand ist eigener Code: Belegungen (aus `entscheide`/`schliesse`; ein Rücksprung schneidet sie ab), gemerkte Phasen (zuletzt
    zurückgenommener Wert), Aktivitäten (aus den Werten des Ereignisses `beteiligt`) und der Zuwachs (1/Zerfall je Konflikt). Die
    gelernte Einheitsklausel gilt nach dem Sprung auf Stufe 0 und hat keinen eigenen Schluss-Eintrag in der Spur.
    """
    belegung: list[tuple[int, int, int | None]] = []     # (Literal, Stufe, Klauselindex)
    gemerkt = {v: False for v in range(1, n + 1)}
    schon_zurueck = set()                                # Variablen, die schon einmal zurückgenommen wurden (sonst „Anfangswert“)
    akt = {v: 0.0 for v in range(1, n + 1)}
    konflikte, stufe = 0, 0
    entscheidungen: list[dict] = []
    gelernt: list[tuple] = []
    einheit = None
    ergebnis: list[Schritt] = []

    for e in spur:
        art, hervor = e[0], ()
        if art == "entscheide":
            _, lit, s, info = e
            stufe = s
            if info.get("art") == "annahme":
                text = f"Stufe {s}: Annahme {literal_text(lit)}"
            else:
                v = abs(lit)
                bel = {abs(l) for l, _, _ in belegung}
                offen = [u for u in range(1, n + 1) if u not in bel]
                fest = waehle_fest(n, bel)
                fest_lit = None if fest is None else (fest if (phasenspeicher and gemerkt[fest]) else -fest)
                if info["art"] == "aktivitaet":
                    gleich = [u for u in offen if akt[u] == akt[v]]
                    grund = f"höchste Aktivität {zahl_text(akt[v])}"
                    if len(gleich) > 1:
                        grund += f", Gleichstand zwischen {', '.join('x%d' % u for u in gleich)}: kleinste Nummer"
                else:
                    grund = "feste Reihenfolge: kleinste offene Variable"
                if not phasenspeicher:
                    wert = "Wert falsch (Phasenspeicher aus)"
                elif v in schon_zurueck:
                    wert = f"Wert {wert_text(lit)}, weil zuletzt {wert_text(lit)} (gespeichert)"
                else:
                    wert = f"Wert {wert_text(lit)} (Anfangswert, noch nie zurückgenommen)"
                entscheidungen.append({
                    "nr": len(entscheidungen) + 1, "stufe": s, "lit": lit, "variable": v, "aktivitaet": akt[v], "grund": grund,
                    "wert": wert, "fest_variable": fest, "fest_lit": fest_lit, "nach_konflikten": konflikte,
                    "abweichung": fest is not None and fest != v})
                text = f"Stufe {s}: Entscheidung {literal_text(lit)}: {grund}; {wert}"
                hervor = (v,)
            belegung.append((lit, s, None))
        elif art == "schliesse":
            _, lit, klausel, s, ci = e
            belegung.append((lit, s, ci))
            text = f"Stufe {s}: K{ci + 1} {klausel_text(klausel)} erzwingt {literal_text(lit)}"
            hervor = (abs(lit),)
        elif art == "konflikt":
            _, klausel, s, ci = e
            text = f"Konflikt auf Stufe {s} in K{ci + 1} {klausel_text(klausel)}: alle Literale sind falsch"
        elif art == "beteiligt":
            liste = e[1]
            zuwachs = (1.0 / zerfall) ** konflikte
            konflikte += 1
            for v, a in liste:
                akt[v] = a
            hervor = tuple(sorted(v for v, _ in liste))
            namen = ", ".join("x%d" % v for v in hervor)
            text = (f"Beteiligt an der Herleitung: {namen}; jede erhält +{zahl_text(zuwachs)} Aktivität" if vsids
                    else f"Beteiligt an der Herleitung: {namen}; die feste Reihenfolge nutzt keine Aktivität")
        elif art == "lerne":
            _, klausel, rueck, _lbd = e
            gelernt.append((list(klausel), rueck))
            einheit = klausel[0] if len(klausel) == 1 else None
            text = f"Gelernte Klausel {klausel_text(klausel)}, Sprung zurück auf Stufe {rueck}"
        elif art == "springe":
            s = e[1]
            rest = []
            for l, ls, ci in belegung:
                if ls > s:
                    schon_zurueck.add(abs(l))
                    if phasenspeicher:
                        gemerkt[abs(l)] = l > 0
                else:
                    rest.append((l, ls, ci))
            belegung, stufe = rest, s
            if einheit is not None:
                belegung.append((einheit, 0, None))
                einheit = None
            text = f"Zurück auf Stufe {s}"
        elif art == "neustart":
            text = "Neustart"
        elif art == "loesche":
            text = f"{e[1]} gelernte Klauseln gelöscht"
        else:
            text = str(art)
        ergebnis.append(Schritt(
            nr=len(ergebnis) + 1, art=art, text=text, stufe=stufe,
            belegung=[(l, s, None if ci is None else f"K{ci + 1}") for l, s, ci in belegung], aktivitaet=dict(akt),
            zuwachs=(1.0 / zerfall) ** konflikte, konflikte=konflikte, entscheidungen=list(entscheidungen),
            gelernt=list(gelernt), hervorgehoben=hervor))
    return ergebnis
