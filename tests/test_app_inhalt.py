"""Inhaltsprüfungen der App über AppTest (der Smoke-Test steht in test_app.py): Startansicht, jede Aufgabe, Schalter, Live-Messreihen, Permalink."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import vsd_constants as C
import vsd_presets as P

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    return " ".join([m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info]
                    + [s.value for s in at.success] + [w.value for w in at.warning])


def test_startansicht_ist_das_handbeispiel():
    at = _fresh_app()
    metriken = {m.label: m.value for m in at.metric}
    assert metriken["Antwort"] == "erfüllbar" and metriken["Konflikte"] == "3" and metriken["Entscheidungen"] == "8"
    assert metriken["Abweichungen"] == "2"        # Handbeispiel F3: x5 und x7 statt der kleinsten offenen Variablen
    assert sum(1 for b in at.button if b.label == "Messreihe live starten") == 3


@pytest.mark.parametrize("label", C.AUFGABEN_LABELS)
def test_jede_aufgabe_rendert_und_zeigt_ein_verdikt_oder_einen_hinweis(label):
    at = _fresh_app()
    at.sidebar.selectbox(key="aufgabe").set_value(label).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    text = _texte(at)
    assert "Vorgerechnet sind:" in text or "Vorgerechnet, nicht live" in text or "vsd_messungen.json) fehlen" in text


def test_jede_aufgabe_hat_die_vorgerechneten_zellen_der_experimente():
    """Je Experiment zeigen genau die Aufgaben der Zellenliste ein Verdikt, die übrigen den Hinweis „nicht vorgerechnet“."""
    for key, a in C.AUFGABEN.items():
        at = _fresh_app()
        at.sidebar.selectbox(key="aufgabe").set_value(a["label"]).run(timeout=TIMEOUT)
        text = _texte(at)
        zeigt = text.count("Vorgerechnet, nicht live")
        erwartet = sum(key in z for z in (C.ZELLEN_AKTIVITAET, C.ZELLEN_PHASE, C.ZELLEN_ZERFALL))
        assert zeigt == erwartet, (key, zeigt, erwartet)
        assert text.count("nicht vorgerechnet") == 3 - erwartet, key


def test_formel_zufall_klein_und_alle_schalter():
    at = _fresh_app()
    at.sidebar.selectbox(key="formel").set_value(P.FORMEL_KLEIN).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    for n in (C.KLEIN_N[0], C.KLEIN_N[1]):
        at.slider(key="klein_n").set_value(n).run(timeout=TIMEOUT)
        assert not at.exception, [str(e) for e in at.exception]
    at.radio(key="wahl_radio").set_value("Feste Reihenfolge").run(timeout=TIMEOUT)
    assert not at.exception and [m.value for m in at.metric if m.label == "Abweichungen"] == ["–"]
    at.toggle(key="phase_toggle").set_value(False).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    at.button(key="preset_Schur n = 44, k = 4").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]


def test_zerfall_wirkt_auf_die_schritt_ansicht():
    at = _fresh_app()
    vorher = {m.label: m.value for m in at.metric}
    at.sidebar.select_slider(key="zerfall").set_value(0.99).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Der Zerfall steht hier auf 0,99" in c.value for c in at.caption)
    at.sidebar.select_slider(key="zerfall").set_value(0.5).run(timeout=TIMEOUT)
    assert {m.label: m.value for m in at.metric} == vorher


def test_live_messreihe_zeigt_verdikt_und_tabelle():
    at = _fresh_app()
    at.button(key="live_go_phase").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    text = _texte(at)
    assert "Live gemessen, nicht vorgerechnet" in text and "Zufalls-3-SAT n = 80" in text
    assert [d for d in at.dataframe if "Abbrüche am Budget" in d.value.columns]


def test_permalink_uebernimmt_gueltige_werte_und_ignoriert_ungueltige():
    at = AppTest.from_file(APP_PATH)
    at.query_params["aufgabe"] = "Schur n = 43, k = 4"
    at.query_params["zerfall"] = "0.99"
    at.query_params["formel"] = "gibt es nicht"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.selectbox(key="aufgabe").value == "Schur n = 43, k = 4"
    assert at.sidebar.select_slider(key="zerfall").value == 0.99
    assert at.sidebar.selectbox(key="formel").value == P.FORMEL_HAND            # ungültig: Standard
