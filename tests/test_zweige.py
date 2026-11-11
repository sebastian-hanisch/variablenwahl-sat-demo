"""Zweig-Tests (DEMO-PLAYBOOK §0): jede Variante der Messreihen läuft wirklich und weicht auf mindestens einer Instanz von jeder anderen ab.

Eine Spalte mit lauter Nullen oder gleiche Spalten hießen: die Variante wird nie ausgeführt (toter Zweig)."""

import itertools

import vsd_algorithm as A
import vsd_constants as C
import vsd_evaluation as E
import vsd_scenario as S


def test_jede_variante_der_referenz_weicht_von_jeder_anderen_ab_und_ist_nicht_null():
    d = E.lade_messungen()["zellen"]
    for zelle, z in d.items():
        for v, m in z["verfahren"].items():
            assert any(c > 0 for c in m["konflikte"]), (zelle, v)
        for (a, ma), (b, mb) in itertools.combinations(z["verfahren"].items(), 2):
            assert ma["konflikte"] != mb["konflikte"], (zelle, a, b)


def test_schalter_wahl_phase_zerfall_wirken_auf_einer_kleinen_formel():
    """Auf Zufalls-3-SAT n = 60 (4 Formeln) ändert jeder Schalter die Konfliktzahlen mindestens einer Formel."""
    laeufe = S.laeufe("zufall", 60, 4)

    def konflikte(wahl=A.WAHL_AKTIVITAET, phase=True, zerfall=C.DEFAULT_ZERFALL):
        return [A.loese(l.inst, wahl, phase, zerfall, budget=20000).stat["konflikte"] for l in laeufe]

    basis = konflikte()
    assert konflikte(wahl=A.WAHL_FEST) != basis
    assert konflikte(phase=False) != basis
    assert konflikte(zerfall=0.5) != basis and konflikte(zerfall=1.0) != basis and konflikte(zerfall=0.5) != konflikte(zerfall=1.0)


def test_noise_seed_wirkt_nur_mit_aktivitaet():
    inst = S.laeufe("zufall", 60, 1)[0].inst
    akt = {A.loese(inst, seed=s, budget=20000).stat["konflikte"] for s in range(6)}
    fest = {A.loese(inst, A.WAHL_FEST, seed=s, budget=20000).stat["konflikte"] for s in range(6)}
    assert len(akt) >= 2 and len(fest) == 1
