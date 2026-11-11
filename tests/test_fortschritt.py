"""Live-Messreihen mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os

from streamlit.testing.v1 import AppTest

import vsd_evaluation as E
import vsd_fortschritt as F

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))

FAELLE = (("rampen", 60, 3, 3000, ["aktivitaet", "fest"]), ("zufall", 50, 2, 2000, ["aktivitaet", "ohne_phase"]), ("schur", 36, 2, 1000, ["aktivitaet", "ohne_phase"]))


def test_zwischengespeicherte_messreihe_ist_gleich_der_ungepufferten():
    for art, groesse, anzahl, budget, verfahren in FAELLE:
        F.lauf_messung.clear()
        direkt = E.messe_live(art, groesse, anzahl, budget, verfahren)
        assert F.messreihe(art, groesse, anzahl, budget, verfahren) == direkt, (art, groesse)
        assert F.messreihe(art, groesse, anzahl, budget, verfahren) == direkt, (art, groesse, "zweiter Aufruf aus dem Zwischenspeicher")


def test_zweiter_aufruf_rechnet_nichts_neu_ein_anderer_parameter_schon():
    F.lauf_messung.clear()
    v0 = F.gerechnet()
    erste = F.messreihe("rampen", 60, 3, 2000, ["aktivitaet", "fest"])
    v1 = F.gerechnet()
    assert v1 - v0 == 6
    assert F.messreihe("rampen", 60, 3, 2000, ["aktivitaet", "fest"]) == erste and F.gerechnet() == v1
    # mehr Formeln: nur die neuen Läufe werden gerechnet, die ersten kommen aus dem Speicher, und das Ergebnis stimmt
    mehr = F.messreihe("rampen", 60, 4, 2000, ["aktivitaet", "fest"])
    assert F.gerechnet() - v1 == 2 and mehr == E.messe_live("rampen", 60, 4, 2000, ["aktivitaet", "fest"])
    v2 = F.gerechnet()
    anderes_budget = F.messreihe("rampen", 60, 3, 500, ["aktivitaet", "fest"])
    assert F.gerechnet() - v2 == 6, "ein anderes Budget darf nicht aus dem Zwischenspeicher kommen"
    assert anderes_budget == E.messe_live("rampen", 60, 3, 500, ["aktivitaet", "fest"])
    v3 = F.gerechnet()
    andere_groesse = F.messreihe("rampen", 70, 3, 2000, ["aktivitaet", "fest"])
    assert F.gerechnet() - v3 == 6 and andere_groesse == E.messe_live("rampen", 70, 3, 2000, ["aktivitaet", "fest"])
    assert andere_groesse["verfahren"] != erste["verfahren"]
    v4 = F.gerechnet()
    F.messreihe("rampen", 60, 3, 2000, ["aktivitaet", "ohne_phase"])
    assert F.gerechnet() - v4 == 3, "ein anderes Verfahren rechnet nur die Läufe dieses Verfahrens"


def test_fortschritt_meldet_jeden_lauf_in_ordnung():
    F.lauf_messung.clear()
    meldungen = []
    F.messreihe("rampen", 60, 3, 1000, ["aktivitaet", "fest"], lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(i, 6) for i in range(1, 7)]


def test_app_zweiter_start_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    F.lauf_messung.clear()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.button(key="live_go_phase").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    erste = [(d.value.to_dict("records")) for d in at.dataframe if "Abbrüche am Budget" in d.value.columns]
    assert erste
    v = F.gerechnet()
    assert v > 0
    at.button(key="live_go_phase").click().run(timeout=TIMEOUT)
    assert not at.exception and F.gerechnet() == v
    zweite = [(d.value.to_dict("records")) for d in at.dataframe if "Abbrüche am Budget" in d.value.columns]
    assert zweite[-1] == erste[-1]
