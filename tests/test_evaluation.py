"""Messung, Kennzahlen, Zellen und die Läufe der Aufgaben: kleine, schnelle Fälle."""

import json

import pytest

import vsd_constants as C
import vsd_evaluation as E
import vsd_scenario as S


def test_laeufe_der_familien_sind_fest_und_deterministisch():
    a, b = S.laeufe("zufall", 40, 3), S.laeufe("zufall", 40, 3)
    assert [l.inst.klauseln for l in a] == [l.inst.klauseln for l in b]
    assert [l.label for l in a] == ["Formel 1", "Formel 2", "Formel 3"] and all(l.seed is None for l in a)
    assert all(len(l.inst.klauseln) == S.klauselzahl(40) == 170 for l in a)
    assert len({tuple(l.inst.klauseln) for l in a}) == 3                                  # drei verschiedene Formeln
    r = S.laeufe("rampen", 60, 2)
    assert r[0].inst.meta["einkleidung"] == "rampen" and r[0].inst.meta["grad"] == C.RAMPEN_GRAD and r[0].inst.klauseln != r[1].inst.klauseln
    s = S.laeufe("schur", 30, 4)
    assert [l.seed for l in s] == [0, 1, 2, 3] and len({id(l.inst) for l in s}) == 1      # eine Instanz, vier Löser-Seeds
    with pytest.raises(ValueError):
        S.laeufe("kugel", 3, 3)


def test_aufgaben_der_referenz_haben_die_groessen_des_plans():
    z = S.laeufe_der_aufgabe("zufall150")
    assert len(z) == 12 and z[0].inst.n == 150 and len(z[0].inst.klauseln) == 639
    assert len(S.laeufe_der_aufgabe("zufall100")[0].inst.klauseln) == 426
    r = S.laeufe_der_aufgabe("rampen160")
    assert len(r) == 10 and r[0].inst.n == 160 * 3 and r[0].inst.meta["auftraege"] == 160
    sch = S.laeufe_der_aufgabe("schur44")
    assert len(sch) == 20 and sch[0].inst.n == 44 * 4 and [l.seed for l in sch] == list(range(20))


def test_kleine_formel_begrenzt_n_und_bleibt_unter_60_klauseln():
    for n in range(C.KLEIN_N[0], C.KLEIN_N[1] + 1):
        inst = S.kleine_formel(n, 3)
        assert inst.n == n and len(inst.klauseln) <= C.MAX_SCHRITT_KLAUSELN
    assert S.kleine_formel(99, 1).n == 12 and S.kleine_formel(1, 1).n == 8                # außerhalb: auf die Grenzen gesetzt
    assert S.kleine_formel(10, 5).klauseln == S.kleine_formel(10, 5).klauseln
    assert S.kleine_formel(10, 5).klauseln != S.kleine_formel(10, 6).klauseln


def test_kennzahlen_median_maximum_abbrueche_und_laenge():
    m = {"konflikte": [10, 20, 40, 5], "antwort": [True, None, False, True], "gelernt": 4, "gelernte_literale": 46}
    k = E.kennzahlen(m)
    assert (k.n, k.median, k.maximum, k.minimum, k.abbrueche, k.erfuellbar, k.unerfuellbar) == (4, 15.0, 40, 5, 1, 2, 1)
    assert k.laenge == pytest.approx(11.5)
    assert E.kennzahlen({"konflikte": [0], "antwort": [True], "gelernt": 0, "gelernte_literale": 0}).laenge is None


def test_messe_zaehlt_abbrueche_mit_dem_budget():
    laeufe = S.laeufe("zufall", 60, 3)
    voll = E.messe(laeufe, 5000, "aktivitaet")
    knapp = E.messe(laeufe, 5, "aktivitaet")
    assert all(a is not None for a in voll["antwort"])
    assert any(a is None for a in knapp["antwort"])                                       # bei Budget 5 bricht mindestens ein Lauf ab
    assert all(c == 5 for c, a in zip(knapp["konflikte"], knapp["antwort"]) if a is None)
    assert E.kennzahlen(knapp).abbrueche == sum(a is None for a in knapp["antwort"])


def test_messe_live_nimmt_die_ersten_laeufe_der_groesseren_messung():
    z = E.messe_live("rampen", 60, 3, 3000, ["aktivitaet", "fest"])
    assert list(z["verfahren"]) == ["aktivitaet", "fest"] and z["anzahl"] == 3 and z["budget"] == 3000
    kleiner = E.messe_live("rampen", 60, 2, 3000, ["aktivitaet"])
    assert kleiner["verfahren"]["aktivitaet"]["konflikte"] == z["verfahren"]["aktivitaet"]["konflikte"][:2]


def test_verfahren_der_zellen_gemaess_experimenten():
    assert E.verfahren_der_zelle("zufall100") == ["aktivitaet", "fest"]
    assert E.verfahren_der_zelle("schur44") == ["aktivitaet", "ohne_phase"]
    assert E.verfahren_der_zelle("zufall150") == ["aktivitaet", "fest", "ohne_phase", "zerfall_0.5", "zerfall_0.8", "zerfall_0.99", "zerfall_1"]
    assert E.zerfall_name(1.0) == "zerfall_1" and E.zerfall_name(0.5) == "zerfall_0.5"
    for v in E.verfahren_der_zelle("zufall150"):
        assert v in E.VERFAHREN and v in E.VERFAHREN_LABEL


def test_referenz_zelle_liest_nur_gemessene_verfahren(tmp_path):
    daten = {"zellen": {"zufall100": {"label": "Z", "art": "zufall", "groesse": 100, "anzahl": 2, "budget": 20000,
                                      "verfahren": {"aktivitaet": {"konflikte": [3, 5], "antwort": [True, False], "gelernt": 2, "gelernte_literale": 20}}}}}
    r = E.referenz_zelle("zufall100", ["aktivitaet"], daten)
    assert r["kennzahlen"]["aktivitaet"].median == 4.0 and r["n"] == 2 and r["budget"] == 20000
    assert E.referenz_zelle("zufall100", ["aktivitaet", "fest"], daten) is None
    assert E.referenz_zelle("zufall150", ["aktivitaet"], daten) is None
    assert E.lade_messungen(tmp_path / "gibt_es_nicht.json") == {"zellen": {}}            # fehlende Datei: leer
    datei = tmp_path / "m.json"
    datei.write_text(json.dumps(daten), encoding="utf-8")
    assert list(E.lade_messungen(datei)["zellen"]) == ["zufall100"]


def test_live_label_und_zahl_formate():
    assert E.live_label("zufall", 80) == "Zufalls-3-SAT n = 80" and E.live_label("schur", 40) == "Schur n = 40, k = 4"
    assert E.live_label("rampen", 100) == "Rampen (Färbung, n = 100)"
