"""Jede Zahl der README (Abschnitt „Befunde“) wird hier nachgerechnet (DEMO-PLAYBOOK §4, §11a).

Die großen Messreihen stehen vorgerechnet in `vsd_messungen.json` (Messskript `tools/messungen.py`); dieser Test liest sie mit denselben Auswertungsfunktionen wie die App
und prüft einen kleinen Teil davon durch eine Neumessung (Reproduzierbarkeit auf jeder Plattform). Die Zahlen der README sind Mediane und Maxima über die festen Läufe
der Messreihe (Zufallsformeln: 12 feste Formeln, Rampen: 10 feste Konfliktgraphen, Schur: eine Instanz mit 20 Zufalls-Seeds des Lösers); Abbrüche am Budget zählen mit
dem Budget und machen Mediane zu unteren Schranken. Die Gegenprobe mit anderen Formelmengen (README, Abschnitt „Stabilität“) steht nicht in den Tests.
"""

import pytest

import vsd_constants as C
import vsd_evaluation as E


@pytest.fixture(scope="module")
def daten():
    d = E.lade_messungen()
    assert set(d["zellen"]) == {"zufall100", "zufall150", "rampen160", "schur43", "schur44"}
    return d


def kz(daten, zelle, verfahren):
    return E.kennzahlen(daten["zellen"][zelle]["verfahren"][verfahren])


def test_daten_aufbau_budget_und_zahl_der_laeufe(daten):
    assert daten["budget"] == C.BUDGET_REFERENZ == 20000 and daten["kern"] == "832b2c10dfdea62d"
    soll = {"zufall100": 12, "zufall150": 12, "rampen160": 10, "schur43": 20, "schur44": 20}
    for zelle, n in soll.items():
        z = daten["zellen"][zelle]
        assert z["budget"] == 20000 and z["anzahl"] == n
        for v, m in z["verfahren"].items():
            assert len(m["konflikte"]) == len(m["antwort"]) == n, (zelle, v)
        assert set(z["verfahren"]) == set(E.verfahren_der_zelle(zelle)), zelle


def test_claim_aktivitaet_gegen_feste_reihenfolge(daten):
    """Kernfrage: Zufall n = 100 / n = 150 und Rampen n = 160 (Median, Maximum, Abbrüche)."""
    z100a, z100f = kz(daten, "zufall100", "aktivitaet"), kz(daten, "zufall100", "fest")
    assert (z100a.median, z100a.maximum, z100a.abbrueche) == (257.5, 607, 0)
    assert (z100f.median, z100f.maximum, z100f.abbrueche) == (1319.0, 2195, 0)
    z150a, z150f = kz(daten, "zufall150", "aktivitaet"), kz(daten, "zufall150", "fest")
    assert (z150a.median, z150a.maximum, z150a.abbrueche) == (2888.0, 5949, 0)
    assert (z150f.median, z150f.maximum, z150f.abbrueche) == (20000.0, 20000, 8)
    ra, rf = kz(daten, "rampen160", "aktivitaet"), kz(daten, "rampen160", "fest")
    assert (ra.median, ra.maximum, ra.abbrueche) == (118.5, 337, 0)
    assert (rf.median, rf.maximum, rf.abbrueche) == (1161.5, 4491, 0)
    # Faktoren der Mediane (feste Reihenfolge durch Aktivität): bei Zufall 150 untere Schranke, weil 8 von 12 Läufen am Budget abbrechen
    assert round(z100f.median / z100a.median, 1) == 5.1 and round(rf.median / ra.median, 1) == 9.8 and round(z150f.median / z150a.median, 1) == 6.9


def test_claim_entschiedene_laeufe_der_festen_reihenfolge_bei_zufall_150(daten):
    m = daten["zellen"]["zufall150"]["verfahren"]["fest"]
    entschieden = [(c, a) for c, a in zip(m["konflikte"], m["antwort"]) if a is not None]
    assert len(entschieden) == 4 and sorted(c for c, _ in entschieden) == [3461, 7104, 19227, 19647]
    assert sorted(a for _, a in entschieden) == [False, False, True, True]
    a = kz(daten, "zufall150", "aktivitaet")
    assert (a.erfuellbar, a.unerfuellbar) == (3, 9)                           # die Antworten von Aktivität: 3 erfüllbar, 9 unerfüllbar


def test_claim_erfuellbarkeit_der_formelmengen(daten):
    assert (kz(daten, "zufall100", "aktivitaet").erfuellbar, kz(daten, "zufall100", "aktivitaet").unerfuellbar) == (6, 6)
    assert (kz(daten, "rampen160", "aktivitaet").erfuellbar, kz(daten, "rampen160", "aktivitaet").unerfuellbar) == (6, 4)
    s = kz(daten, "schur43", "aktivitaet")
    assert (s.erfuellbar, s.unerfuellbar, s.abbrueche) == (20, 0, 0)


def test_claim_laenge_der_gelernten_klauseln(daten):
    """Mittlere Länge gelernter Klauseln (Literale), fest gegen Aktivität."""
    werte = {z: (round(kz(daten, z, "fest").laenge, 1), round(kz(daten, z, "aktivitaet").laenge, 1)) for z in ("zufall100", "zufall150", "rampen160")}
    assert werte == {"zufall100": (10.1, 8.2), "zufall150": (16.4, 11.4), "rampen160": (18.9, 11.9)}


def test_claim_phasenspeicher(daten):
    """Mit und ohne Phasenspeicher: Zufall 150, Rampen 160, Schur 43 und 44."""
    z = kz(daten, "zufall150", "aktivitaet"), kz(daten, "zufall150", "ohne_phase")
    assert [(k.median, k.maximum, k.abbrueche) for k in z] == [(2888.0, 5949, 0), (2618.0, 5493, 0)]
    r = kz(daten, "rampen160", "aktivitaet"), kz(daten, "rampen160", "ohne_phase")
    assert [(k.median, k.maximum, k.abbrueche) for k in r] == [(118.5, 337, 0), (126.0, 402, 0)]
    s43 = kz(daten, "schur43", "aktivitaet"), kz(daten, "schur43", "ohne_phase")
    assert [(k.median, k.maximum, k.abbrueche) for k in s43] == [(255.0, 5306, 0), (564.5, 2356, 0)]
    s44 = kz(daten, "schur44", "aktivitaet"), kz(daten, "schur44", "ohne_phase")
    assert [(k.median, k.maximum, k.abbrueche, k.n) for k in s44] == [(3307.0, 20000, 3, 20), (19031.5, 20000, 9, 20)]
    # Faktoren der README (ohne gegen mit): Zufall 1,10, Schur n = 43 2,2, Schur n = 44 5,8; Rampen umgekehrt (mit besser): 1,06
    assert round(z[1].median / z[0].median, 2) == 0.91 and round(z[0].median / z[1].median, 2) == 1.10
    assert round(r[1].median / r[0].median, 2) == 1.06
    assert round(s43[1].median / s43[0].median, 1) == 2.2 and round(s44[1].median / s44[0].median, 1) == 5.8
    assert s43[0].maximum > s43[1].maximum                                  # Schur n = 43: das Maximum ist mit Phasenspeicher größer
    # Median und Abbrüche: bei Schur n = 44 liegt der Median trotz 9 Abbrüchen fest (weniger als die Hälfte von 20), bei Zufall n = 150 (fest) nicht
    assert not s44[0].median_untere_schranke and not s44[1].median_untere_schranke
    assert kz(daten, "zufall150", "fest").median_untere_schranke
    # Verdikte der App für diese vier Zellen (die Richtung steht in der README)
    arten = [E.verdict_phase(zelle, kz(daten, zelle, "aktivitaet"), kz(daten, zelle, "ohne_phase"), 20000)[0] for zelle in ("zufall150", "rampen160", "schur43", "schur44")]
    assert arten == ["info", "info", "success", "success"]


def test_claim_zerfall(daten):
    zs = C.ZERFAELLE
    namen = ["zerfall_0.5", "zerfall_0.8", "aktivitaet", "zerfall_0.99", "zerfall_1"]
    zufall = [daten["zellen"]["zufall150"]["verfahren"][n] for n in namen]
    rampen = [daten["zellen"]["rampen160"]["verfahren"][n] for n in namen]
    assert [E.kennzahlen(m).median for m in zufall] == [6023.5, 4273.0, 2888.0, 2772.0, 3566.0]
    assert [E.kennzahlen(m).median for m in rampen] == [200.5, 75.5, 118.5, 143.0, 113.0]
    assert [E.kennzahlen(m).abbrueche for m in zufall + rampen] == [0] * 10
    assert zs == (0.5, 0.8, 0.95, 0.99, 1.0)
    # bester Wert je Familie und Faktor zwischen schlechtestem und bestem
    mz = [E.kennzahlen(m).median for m in zufall]
    mr = [E.kennzahlen(m).median for m in rampen]
    assert zs[mz.index(min(mz))] == 0.99 and zs[mr.index(min(mr))] == 0.8
    assert round(max(mz) / min(mz), 1) == 2.2 and round(max(mr) / min(mr), 1) == 2.7
    assert zs[mz.index(max(mz))] == 0.5 and zs[mr.index(max(mr))] == 0.5
    # Anzahl der Werte, die um den Faktor 1,5 oder mehr über dem besten liegen
    assert sum(E.deutlich_mehr(x, min(mz)) for x in mz) == 2 and sum(E.deutlich_mehr(x, min(mr)) for x in mr) == 3


def test_claim_zerfall_verdikte_der_app(daten):
    kennz = {z: kz(daten, "zufall150", "aktivitaet" if z == 0.95 else E.zerfall_name(z)) for z in C.ZERFAELLE}
    text = E.verdict_zerfall("Zufall", kennz)[1]
    assert "Bester Wert 0,99 (2.772), schlechtester 0,5 (6.023,5)" in text and "0,5, 0,8." in text


def test_claim_schubfach_umgekehrt_zur_kernfrage():
    m = E.messe_schubfach()
    assert {h: (v["aktivitaet"], v["fest"]) for h, v in m.items()} == {5: (159, 50), 6: (1004, 130)}
    assert all(v["antwort"] == (False, False) for v in m.values())                  # unerfüllbar, kein Abbruch
    assert "Hier braucht die Aktivität mehr als die feste Reihenfolge." in E.schubfach_satz(m)
    assert round(m[6]["aktivitaet"] / m[6]["fest"], 1) == 7.7


def test_json_ist_reproduzierbar_auf_dieser_plattform(daten):
    """Neumessung der billigsten Läufe: dieselben Konfliktzahlen wie in der Datei (SplitMix64 und Löser sind plattformunabhängig)."""
    z = daten["zellen"]
    neu = E.messe_live("rampen", 160, 3, 20000, ["aktivitaet"])
    assert neu["verfahren"]["aktivitaet"]["konflikte"] == z["rampen160"]["verfahren"]["aktivitaet"]["konflikte"][:3]
    neu = E.messe_live("zufall", 100, 2, 20000, ["aktivitaet", "fest"])
    for v in ("aktivitaet", "fest"):
        assert neu["verfahren"][v]["konflikte"] == z["zufall100"]["verfahren"][v]["konflikte"][:2]
    assert neu["verfahren"]["aktivitaet"]["antwort"] == z["zufall100"]["verfahren"]["aktivitaet"]["antwort"][:2]
