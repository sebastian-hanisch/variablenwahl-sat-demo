"""Messreihen, Kennzahlen und Verdikte.

Gemessen werden Konflikte (nie Sekunden). Ein Lauf, der das Budget erreicht, zählt mit dem Budget (untere Schranke) und wird als
Abbruch ausgewiesen. Die vorgerechneten Messreihen der Referenz stehen in `vsd_messungen.json` (Messskript `tools/messungen.py`, das
dieselben Funktionen aufruft wie die Live-Messreihen der App); alle Verdikte sind reine Funktionen `verdict_*(...) -> (Art, Text)`,
jede Zahl im Text stammt aus den übergebenen Kennzahlen.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import vsd_algorithm as A
import vsd_constants as C
import vsd_scenario as S
from vsd_instanzen import pigeonhole

MESSDATEI = Path(__file__).with_name("vsd_messungen.json")

# Verfahren der Messreihen -> (Wahl, Phasenspeicher, Zerfall)
def zerfall_name(z: float) -> str:
    return f"zerfall_{z:g}"


VERFAHREN = {
    "aktivitaet": (A.WAHL_AKTIVITAET, True, C.DEFAULT_ZERFALL),
    "fest": (A.WAHL_FEST, True, C.DEFAULT_ZERFALL),
    "ohne_phase": (A.WAHL_AKTIVITAET, False, C.DEFAULT_ZERFALL),
}
for _z in C.ZERFAELLE:
    if _z != C.DEFAULT_ZERFALL:
        VERFAHREN[zerfall_name(_z)] = (A.WAHL_AKTIVITAET, True, _z)
VERFAHREN_LABEL = dict(C.VERFAHREN_LABEL)
for _z in C.ZERFAELLE:
    if _z != C.DEFAULT_ZERFALL:
        VERFAHREN_LABEL[zerfall_name(_z)] = f"Zerfall {str(_z).replace('.', ',')}"


# --------------------------------------------------------------------------------------------------------------------------------- Zahlen
def zahl(x: float) -> str:
    """Deutsche Schreibweise: Tausenderpunkt, Dezimalkomma; ganze Werte ohne, halbe mit einer Nachkommastelle."""
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def zerfall_text(z: float) -> str:
    return str(z).replace(".", ",")


def live_label(art: str, groesse: int) -> str:
    """Beschriftung einer Live-Messreihe."""
    return {"zufall": f"Zufalls-3-SAT n = {groesse}", "rampen": f"Rampen (Färbung, n = {groesse})",
            "schur": f"Schur n = {groesse}, k = {C.SCHUR_K}"}[art]


# --------------------------------------------------------------------------------------------------------------------------------- Messen
def messe(laeufe: list[S.Lauf], budget: int, verfahren: str) -> dict:
    """Ein Verfahren über alle Läufe: Konflikte je Lauf, Antwort (True / False / None bei Abbruch) und Länge der gelernten Klauseln."""
    wahl, phase, zerfall = VERFAHREN[verfahren]
    konflikte, antworten, gelernt, literale = [], [], 0, 0
    for lauf in laeufe:
        erg = A.loese(lauf.inst, wahl, phase, zerfall, budget=budget, seed=lauf.seed)
        konflikte.append(erg.stat["konflikte"])
        antworten.append(erg.antwort)
        gelernt += erg.stat["gelernt"]
        literale += erg.stat["gelernte_literale"]
    return {"konflikte": konflikte, "antwort": antworten, "gelernt": gelernt, "gelernte_literale": literale}


@dataclass(frozen=True)
class Kennzahlen:
    n: int
    median: float
    maximum: int
    minimum: int
    abbrueche: int
    erfuellbar: int
    unerfuellbar: int
    laenge: float | None     # mittlere Länge der gelernten Klauseln (Literale)

    @property
    def median_untere_schranke(self) -> bool:
        """Der Median ist nur eine untere Schranke, wenn er einen abgebrochenen Lauf enthält: die Abbrüche sind die größten Werte,
        der Median (Mittel der beiden mittleren Werte) berührt sie ab n − n // 2 Abbrüchen (12 Läufe: ab 6, 20 Läufe: ab 10)."""
        return self.abbrueche >= self.n - self.n // 2 and self.abbrueche > 0


def kennzahlen(m: dict) -> Kennzahlen:
    """Median, Maximum, Abbrüche usw. einer Messung; Abbrüche zählen mit dem erreichten Budget (untere Schranke)."""
    k = m["konflikte"]
    ant = m["antwort"]
    laenge = m["gelernte_literale"] / m["gelernt"] if m.get("gelernt") else None
    return Kennzahlen(len(k), float(median(k)), max(k), min(k), sum(a is None for a in ant), sum(a is True for a in ant),
                      sum(a is False for a in ant), laenge)


def messe_zelle(schluessel: str, verfahren: list[str], budget: int = C.BUDGET_REFERENZ) -> dict:
    """Eine Zelle der Referenz: feste Läufe der Aufgabe, jedes genannte Verfahren."""
    a = C.AUFGABEN[schluessel]
    laeufe = S.laeufe_der_aufgabe(schluessel)
    return {"label": a["label"], "art": a["art"], "groesse": a["groesse"], "anzahl": len(laeufe), "budget": budget,
            "laeufe": [l.label for l in laeufe], "verfahren": {v: messe(laeufe, budget, v) for v in verfahren}}


def messe_live(art: str, groesse: int, anzahl: int, budget: int, verfahren: list[str]) -> dict:
    """Live-Messreihe (kleiner als die Referenz): erste `anzahl` feste Formeln bzw. Löser-Seeds in der gewählten Größe."""
    laeufe = S.laeufe(art, groesse, anzahl)
    return {"art": art, "groesse": groesse, "anzahl": len(laeufe), "budget": budget, "laeufe": [l.label for l in laeufe],
            "verfahren": {v: messe(laeufe, budget, v) for v in verfahren}}


def verfahren_der_zelle(schluessel: str) -> list[str]:
    """Welche Verfahren die Referenz in dieser Aufgabe misst (Vereinigung aus den drei Experimenten)."""
    v = []
    if schluessel in C.ZELLEN_AKTIVITAET or schluessel in C.ZELLEN_PHASE or schluessel in C.ZELLEN_ZERFALL:
        v.append("aktivitaet")
    if schluessel in C.ZELLEN_AKTIVITAET:
        v.append("fest")
    if schluessel in C.ZELLEN_PHASE:
        v.append("ohne_phase")
    if schluessel in C.ZELLEN_ZERFALL:
        v += [zerfall_name(z) for z in C.ZERFAELLE if z != C.DEFAULT_ZERFALL]
    return v


_CACHE: dict = {}


def lade_messungen(pfad: Path = MESSDATEI) -> dict:
    """Die vorgerechneten Messreihen; fehlt die Datei, ist das Ergebnis leer (die App weist dann darauf hin)."""
    schluessel = str(pfad)
    if schluessel not in _CACHE:
        try:
            _CACHE[schluessel] = json.loads(pfad.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _CACHE[schluessel] = {"zellen": {}}
    return _CACHE[schluessel]


def referenz_zelle(schluessel: str, verfahren: list[str], daten: dict | None = None) -> dict | None:
    """Kennzahlen der vorgerechneten Zelle für die genannten Verfahren, oder None, wenn sie nicht gemessen wurde."""
    daten = daten if daten is not None else lade_messungen()
    z = daten.get("zellen", {}).get(schluessel)
    if not z or any(v not in z["verfahren"] for v in verfahren):
        return None
    return {"label": z["label"], "budget": z["budget"], "n": z["anzahl"], "art": z["art"],
            "kennzahlen": {v: kennzahlen(z["verfahren"][v]) for v in verfahren}, "roh": {v: z["verfahren"][v] for v in verfahren}}


# --------------------------------------------------------------------------------------------------------------------------------- Verdikte
def deutlich_mehr(x: float, y: float) -> bool:
    """x liegt um mindestens den Faktor SCHWELLE_KLAR über y (bei y = 0: jedes positive x)."""
    return x > y and x >= C.SCHWELLE_KLAR * y


def _abbruch_satz(*kennz: Kennzahlen) -> str:
    """Hinweis zu Abbrüchen: ein Median ist exakt, solange weniger als die Hälfte der Läufe abbricht; sonst nur eine untere Schranke."""
    if any(k.median_untere_schranke for k in kennz):
        return " Mindestens die Hälfte der Läufe eines Verfahrens bricht ab: sein Median ist nur eine untere Schranke."
    if any(k.abbrueche for k in kennz):
        return " Abbrüche zählen mit dem Budget; der Median bleibt davon unberührt, das Maximum ist eine untere Schranke."
    return ""


def verdict_aktivitaet(label: str, akt: Kennzahlen, fest: Kennzahlen, budget: int) -> tuple[str, str]:
    """Aktivität gegen feste Reihenfolge: Abbrüche und Median, beides aus der Messung."""
    kopf = (f"{label}: Bei fester Reihenfolge erreichen **{fest.abbrueche} von {fest.n}** Läufen das Budget von {zahl(budget)} Konflikten, "
            f"bei Aktivität **{akt.abbrueche}**. Median der Konflikte {zahl(fest.median)} gegen {zahl(akt.median)} "
            f"(Maximum {zahl(fest.maximum)} gegen {zahl(akt.maximum)}).")
    nachsatz = _abbruch_satz(akt, fest)
    if fest.abbrueche > akt.abbrueche or deutlich_mehr(fest.median, akt.median):
        return "success", kopf + " Die feste Reihenfolge braucht in dieser Messung deutlich mehr." + nachsatz
    if akt.abbrueche > fest.abbrueche or deutlich_mehr(akt.median, fest.median):
        return "warning", kopf + " In dieser Messung braucht die Aktivität mehr als die feste Reihenfolge." + nachsatz
    return "info", kopf + " Kein klarer Unterschied in dieser Messung." + nachsatz


def verdict_phase(label: str, mit: Kennzahlen, ohne: Kennzahlen, budget: int) -> tuple[str, str]:
    """Phasenspeicher: Median, Maximum und Abbrüche mit und ohne."""
    kopf = (f"{label}: Mit Phasenspeicher Median {zahl(mit.median)} (Maximum {zahl(mit.maximum)}, {mit.abbrueche} von {mit.n} Abbrüchen), "
            f"ohne {zahl(ohne.median)} (Maximum {zahl(ohne.maximum)}, {ohne.abbrueche} von {ohne.n} Abbrüchen; Budget {zahl(budget)}).")
    nachsatz = _abbruch_satz(mit, ohne)
    if ohne.abbrueche > mit.abbrueche or deutlich_mehr(ohne.median, mit.median):
        return "success", kopf + " Hier hilft der Phasenspeicher." + nachsatz
    if mit.abbrueche > ohne.abbrueche or deutlich_mehr(mit.median, ohne.median):
        return "warning", kopf + " Hier ist es mit Phasenspeicher nicht besser, sondern schlechter." + nachsatz
    return "info", kopf + " Kein klarer Unterschied." + nachsatz


def verdict_zerfall(label: str, kennz: dict[float, Kennzahlen]) -> tuple[str, str]:
    """Zerfall: Median je Wert, bester und schlechtester Wert, Werte mit Faktor SCHWELLE_KLAR über dem besten."""
    werte = sorted(kennz)
    med = {z: kennz[z].median for z in werte}
    bester = min(werte, key=lambda z: (med[z], z))
    schlechtester = max(werte, key=lambda z: (med[z], -z))
    reihe = " / ".join(zahl(med[z]) for z in werte)
    zs = " / ".join(zerfall_text(z) for z in werte)
    text = f"{label}: Median der Konflikte bei Zerfall {zs}: {reihe}. Bester Wert {zerfall_text(bester)} ({zahl(med[bester])}), schlechtester {zerfall_text(schlechtester)} ({zahl(med[schlechtester])})."
    schlecht = [z for z in werte if deutlich_mehr(med[z], med[bester])]
    if schlecht:
        text += f" Um mindestens den Faktor 1,5 über dem besten liegt: {', '.join(zerfall_text(z) for z in schlecht)}."
    else:
        text += " Kein Wert liegt um den Faktor 1,5 oder mehr über dem besten."
    text += _abbruch_satz(*(kennz[z] for z in werte))
    return "info", text


def verdict_zerfall_familien(beste: dict[str, float]) -> tuple[str, str]:
    """Ein Wert für alle Familien? `beste`: Beschriftung der Familie -> bester Zerfall in der Messung."""
    if len(beste) < 2:
        return "info", "Für den Vergleich der Familien braucht es mindestens zwei gemessene Aufgaben."
    liste = "; ".join(f"{k}: {zerfall_text(v)}" for k, v in beste.items())
    if len(set(beste.values())) == 1:
        return "info", f"Bester Zerfall je Aufgabe: {liste}. In diesen Messungen ist es in allen gemessenen Aufgaben derselbe Wert."
    return "info", f"Bester Zerfall je Aufgabe: {liste}. Ein Wert, der in allen gemessenen Aufgaben der beste ist, existiert in diesen Messungen nicht."


# --------------------------------------------------------------------------------------------------------------------------------- Schubfach
def messe_schubfach(hs=C.SCHUBFACH_H, budget: int = C.BUDGET_REFERENZ) -> dict:
    """Schubfach-Prinzip (h + 1 Tauben, h Fächer; unerfüllbar): Konflikte bei Aktivität und bei fester Reihenfolge, je ein Lauf (deterministische Instanz)."""
    erg = {}
    for h in hs:
        inst = pigeonhole(h)
        a = A.loese(inst, A.WAHL_AKTIVITAET, True, C.DEFAULT_ZERFALL, budget=budget)
        f = A.loese(inst, A.WAHL_FEST, True, C.DEFAULT_ZERFALL, budget=budget)
        erg[h] = {"aktivitaet": a.stat["konflikte"], "fest": f.stat["konflikte"], "antwort": (a.antwort, f.antwort)}
    return erg


def schubfach_satz(m: dict) -> str:
    """Satz zur Schubfach-Messung, aus den Zahlen abgeleitet (Richtung nur, wenn sie für alle gemessenen h gleich ist)."""
    hs = sorted(m)
    akt = " / ".join(zahl(m[h]["aktivitaet"]) for h in hs)
    fest = " / ".join(zahl(m[h]["fest"]) for h in hs)
    h_text = " / ".join(str(h) for h in hs)
    kopf = f"Schubfach-Prinzip mit h = {h_text}: Aktivität {akt} Konflikte, feste Reihenfolge {fest}"
    if all(m[h]["fest"] < m[h]["aktivitaet"] for h in hs):
        return kopf + ". Hier braucht die Aktivität mehr als die feste Reihenfolge."
    if all(m[h]["aktivitaet"] < m[h]["fest"] for h in hs):
        return kopf + ". Hier braucht die feste Reihenfolge mehr als die Aktivität."
    return kopf + ". Keine einheitliche Richtung."
