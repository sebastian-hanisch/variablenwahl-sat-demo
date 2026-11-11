"""Live-Messreihen mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Jeder Lauf eines Verfahrens auf einer festen Formel (bzw. mit einem festen Zufalls-Seed des Lösers) ist eine Aufgabe: `lauf_messung` rechnet sie mit
`vsd_evaluation.messe` und wird einzeln zwischengespeichert (`st.cache_data`, höchstens 200 Einträge). Der Fortschrittsbalken zählt die fertigen Läufe;
ändert jemand nur die Zahl der Formeln oder wechselt das Budget zurück, kommen die schon gerechneten Läufe aus dem Zwischenspeicher. Das Ergebnis ist
gleich dem von `vsd_evaluation.messe_live` (`tests/test_fortschritt.py`)."""

from contextlib import contextmanager

import streamlit as st

import vsd_evaluation as E
import vsd_scenario as S

_ZAEHLER = {"gerechnet": 0}


def gerechnet() -> int:
    """Wie viele Läufe in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient der Anzeige und dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=200)
def lauf_messung(art: str, groesse: int, nr: int, budget: int, verfahren: str) -> dict:
    """Messung eines Verfahrens an Lauf Nr. `nr` (ab 0) der Aufgabe; eine Liste der Länge 1 je Feld wie bei `E.messe`."""
    _ZAEHLER["gerechnet"] += 1
    return E.messe([S.laeufe(art, groesse, nr + 1)[nr]], budget, verfahren)


def messreihe(art: str, groesse: int, anzahl: int, budget: int, verfahren, melde=None) -> dict:
    """Die Messreihe wie `E.messe_live(art, groesse, anzahl, budget, verfahren)`; `melde(fertig, gesamt)` wird nach jedem Lauf aufgerufen."""
    laeufe = S.laeufe(art, groesse, anzahl)
    gesamt = len(laeufe) * len(verfahren)
    teile = {v: [] for v in verfahren}
    fertig = 0
    for nr in range(len(laeufe)):
        for v in verfahren:
            teile[v].append(lauf_messung(art, groesse, nr, budget, v))
            fertig += 1
            if melde:
                melde(fertig, gesamt)
    zusammen = {v: {"konflikte": [k for t in ts for k in t["konflikte"]], "antwort": [a for t in ts for a in t["antwort"]],
                    "gelernt": sum(t["gelernt"] for t in ts), "gelernte_literale": sum(t["gelernte_literale"] for t in ts)} for v, ts in teile.items()}
    return {"art": art, "groesse": groesse, "anzahl": len(laeufe), "budget": budget, "laeufe": [l.label for l in laeufe], "verfahren": zusammen}


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()
