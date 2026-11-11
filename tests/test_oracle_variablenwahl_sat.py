"""Orakel-Tests der Variablenwahl nach Aktivität (ORACLE-PLAYBOOK §5): unabhängige Rechenwege.

* Erfüllbarkeit: OR-Tools CP-SAT (nur Test) auf 40 Zufallsformeln und Schur n = 14 (k = 3, unerfüllbar), jede Wahl-Variante; jedes Modell mit eigener Prüfung.
* Aktivitäten, Herleitungen und Entscheidungen: `hilfen.nachvollzug` rechnet die Spur des Lösers mit eigenem Code und exakten Brüchen nach (1-UIP-Auflösung,
  Zuwachs, gemerkte Phasen) und prüft jede Entscheidung gegen die Regel „höchste Aktivität, bei Gleichstand kleinste Nummer“.
* Eigenschaften: Äquivalenz des Zuwachs-Tricks, Neuskalierung, Antwort unabhängig von der Wahlregel, Umbenennen der Variablen ändert die Antwort nie.
"""

from fractions import Fraction

import pytest
from hilfen import cpsat_antwort, modell_erfuellt, nachvollzug

import vsd_algorithm as A
import vsd_scenario as S
from vsd_cdcl import Loeser
from vsd_instanzen import Instanz, pigeonhole, rand3, schur
from vsd_rng import SplitMix64

VARIANTEN = [(A.WAHL_AKTIVITAET, True), (A.WAHL_AKTIVITAET, False), (A.WAHL_FEST, True), (A.WAHL_FEST, False)]


def test_erfuellbarkeit_gegen_cpsat_auf_40_zufallsformeln_alle_varianten():
    sat = unsat = 0
    for seed in range(40):
        n = 25 + (seed % 3) * 5
        inst = rand3(n, S.klauselzahl(n), 9000 + seed)
        referenz = cpsat_antwort(inst.n, inst.klauseln)
        sat += referenz
        unsat += not referenz
        for wahl, phase in VARIANTEN:
            erg = A.loese(inst, wahl, phase, 0.95, budget=20000)
            assert erg.antwort is referenz, (seed, wahl, phase)
            if erg.antwort:
                assert modell_erfuellt(inst.klauseln, erg.modell), (seed, wahl, phase)
    assert sat >= 8 and unsat >= 8          # beide Antworten kommen vor


@pytest.mark.parametrize("zerfall", [0.5, 0.8, 1.0])
def test_antwort_haengt_weder_von_wahl_noch_zerfall_ab_schur(zerfall):
    for n_zahlen, erwartet in ((13, True), (14, False)):                # Schur-Zahl S(3) = 13
        inst = schur(n_zahlen, 3)
        assert cpsat_antwort(inst.n, inst.klauseln) is erwartet
        for wahl, phase in VARIANTEN:
            erg = A.loese(inst, wahl, phase, zerfall, budget=50000)
            assert erg.antwort is erwartet
            if erwartet:
                assert modell_erfuellt(inst.klauseln, erg.modell)


# --- Aktivitäten und Entscheidungen aus der Spur nachgerechnet -----------------------------------------------------------------------------

def analysierte_konflikte(erg) -> int:
    """Konflikte mit Analyse: bei „unerfüllbar“ endet die Suche mit einem Konflikt auf Stufe 0, der nur gezählt, aber nicht analysiert wird."""
    return erg.stat["konflikte"] - (1 if erg.antwort is False else 0)


def _pruefe_beteiligte(erg, konflikte):
    """Die Beteiligten und Aktivitäten, die der Löser meldet, entsprechen der eigenen Herleitung."""
    gemeldet = [e[1] for e in erg.spur if e[0] == "beteiligt"]
    assert len(gemeldet) == len(konflikte)
    for meldung, (beteiligt, akt) in zip(gemeldet, konflikte):
        assert {v for v, _ in meldung} == beteiligt
        for v, a in meldung:
            assert a == float(akt[v]), v


@pytest.mark.parametrize("seed", range(12))
def test_nachvollzug_zufallsformeln_zerfall_halb_exakt(seed):
    inst = rand3(30, S.klauselzahl(30), 300 + seed)
    erg = A.loese(inst, zerfall=0.5, budget=45, trace=True)                # höchstens 45 Konflikte: die Zuwächse 2^k bleiben exakt darstellbar
    konflikte, geprueft = nachvollzug(erg.spur, inst.n, Fraction(1, 2), exakt=True)
    assert geprueft == erg.stat["entscheidungen"] > 0
    assert len(konflikte) == analysierte_konflikte(erg)
    _pruefe_beteiligte(erg, konflikte)


def test_nachvollzug_hat_konflikte_geprueft():
    """Die Zufallsformeln erzeugen genug Konflikte, damit der Nachvollzug nicht nur leere Läufe sieht."""
    zahlen = [A.loese(rand3(30, S.klauselzahl(30), 300 + s), zerfall=0.5, budget=45).stat["konflikte"] for s in range(12)]
    assert sum(zahlen) >= 100 and max(zahlen) >= 20


def test_nachvollzug_ohne_phasenspeicher_und_feste_reihenfolge():
    inst = rand3(30, S.klauselzahl(30), 305)
    ohne = A.loese(inst, phase=False, zerfall=0.5, budget=45, trace=True)
    nachvollzug(ohne.spur, inst.n, Fraction(1, 2), phase=False, exakt=True)
    fest = A.loese(inst, A.WAHL_FEST, True, 0.5, budget=45, trace=True)
    nachvollzug(fest.spur, inst.n, Fraction(1, 2), exakt=True)


@pytest.mark.parametrize("zerfall", [0.8, 0.95, 0.99, 1.0])
def test_nachvollzug_gleitkomma_mit_toleranz(zerfall):
    for seed in range(4):
        inst = rand3(40, S.klauselzahl(40), 500 + seed)
        erg = A.loese(inst, zerfall=zerfall, trace=True)
        konflikte, geprueft = nachvollzug(erg.spur, inst.n, zerfall, exakt=False)
        assert geprueft == erg.stat["entscheidungen"]
        gemeldet = [e[1] for e in erg.spur if e[0] == "beteiligt"]
        for meldung, (beteiligt, akt) in zip(gemeldet, konflikte):
            assert {v for v, _ in meldung} == beteiligt
            for v, a in meldung:
                assert a == pytest.approx(float(akt[v]), rel=1e-9)


def test_nachvollzug_schubfach_und_schur_mit_neustarts():
    """Strukturaufgaben mit mehr als 32 Konflikten: Neustarts (Luby) laufen mit, der Nachvollzug folgt den Rücksprüngen auf Stufe 0."""
    for inst in (pigeonhole(5), schur(14, 3)):
        erg = A.loese(inst, zerfall=0.95, trace=True)
        assert erg.stat["konflikte"] > 32 and erg.stat["neustarts"] >= 1
        konflikte, geprueft = nachvollzug(erg.spur, inst.n, 0.95, exakt=False)
        assert len(konflikte) == analysierte_konflikte(erg) and geprueft == erg.stat["entscheidungen"]


# --- Eigenschaften -------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("zerfall", [0.5, 0.8, 0.95])
def test_aequivalenz_zuwachs_trick_ueber_zufaellige_konfliktfolgen(zerfall):
    """Aktivität / Zuwachs = Summe über die Konflikte mit Beteiligung, je Konflikt mit Zerfall^(Alter) abgezinst (unabhängig aus den Beteiligten gerechnet)."""
    for seed in range(8):
        inst = rand3(30, S.klauselzahl(30), 700 + seed)
        s = Loeser(inst.n, inst.klauseln, decay=zerfall, trace=True)
        erg = s.loese(conflict_budget=60)
        beteiligt = [{v for v, _ in e[1]} for e in erg.spur if e[0] == "beteiligt"]
        k = len(beteiligt)
        assert k == analysierte_konflikte(erg)
        for v in range(1, inst.n + 1):
            soll = sum(zerfall ** (k + 1 - i) for i, b in enumerate(beteiligt, start=1) if v in b)
            assert s.aktivitaet[v] / s.zuwachs == pytest.approx(soll, rel=1e-9, abs=1e-12), (seed, v)


def test_neuskalierung_aendert_die_reihenfolge_nie():
    """Eine Aktivität über 1e100 löst die Neuskalierung aus: alle Aktivitäten und der Zuwachs werden mit 1e-100 multipliziert, die Rangfolge bleibt.
    Von Hand (Einheiten 1e99): x1 = 4, x2 = 7, x3 = 7, x4 = 2, x5 = 3, Zuwachs 6. Vor der Erhöhung: x2, x3, x1, x5, x4. Erste Erhöhung von x5: 9 (keine
    Neuskalierung), Reihenfolge x5, x2, x3, x1, x4. Zweite Erhöhung: 15 > 10, Neuskalierung: x5 = 1,5, x2 = x3 = 0,7, x1 = 0,4, x4 = 0,2, Zuwachs 0,6."""
    s = Loeser(5, [(1, 2, 3)], decay=0.5)
    s.aktivitaet = [0.0, 4e99, 7e99, 7e99, 2e99, 3e99]
    s.zuwachs = 6e99

    def rang():
        return sorted(range(1, 6), key=lambda v: (-s.aktivitaet[v], v))

    assert rang() == [2, 3, 1, 5, 4]
    s._erhoehe(5)
    assert s.aktivitaet[5] == 9e99 and s.zuwachs == 6e99 and rang() == [5, 2, 3, 1, 4]
    s._erhoehe(5)
    assert s.zuwachs == pytest.approx(0.6) and s.aktivitaet[5] == pytest.approx(1.5)
    assert [round(s.aktivitaet[v], 6) for v in range(1, 6)] == [0.4, 0.7, 0.7, 0.2, 1.5]
    assert rang() == [5, 2, 3, 1, 4]                 # exakte Reihenfolge der Brüche 15, 7, 7, 4, 2
    assert s.waehle() == 5                          # die Halde wurde mitgezogen


def test_neuskalierung_in_langem_lauf_aendert_die_antwort_nicht():
    """Bei Zerfall 0,5 wächst der Zuwachs wie 2^k: nach etwa 333 Konflikten greift die Neuskalierung. Antwort und Modell bleiben richtig."""
    inst = pigeonhole(6)
    s = Loeser(inst.n, inst.klauseln, decay=0.5)
    erg = s.loese()
    assert erg.stat["konflikte"] > 400 and erg.antwort is False
    assert s.zuwachs < 1e100 and max(s.aktivitaet) < 1e101          # die Neuskalierung hat gegriffen (ohne sie läge der Zuwachs über 2^400)


def test_antwort_unabhaengig_von_der_wahlregel_auf_zufallsformeln():
    for seed in range(15):
        inst = rand3(30, S.klauselzahl(30), 1100 + seed)
        antworten = {(w, p): A.loese(inst, w, p, 0.8, budget=20000) for w, p in VARIANTEN}
        assert len({e.antwort for e in antworten.values()}) == 1
        for e in antworten.values():
            assert e.antwort is not None
            if e.antwort:
                assert modell_erfuellt(inst.klauseln, e.modell)


def test_umbenennen_der_variablen_aendert_die_antwort_nie():
    for seed in range(15):
        inst = rand3(30, S.klauselzahl(30), 1300 + seed)
        perm = list(range(1, inst.n + 1))
        SplitMix64(seed).shuffle(perm)
        neu = [tuple((perm[abs(l) - 1]) * (1 if l > 0 else -1) for l in k) for k in inst.klauseln]
        a = A.loese(inst, budget=20000)
        b = A.loese(Instanz(inst.n, neu, {}), budget=20000)
        assert a.antwort is b.antwort and a.antwort is not None
        if b.antwort:
            assert modell_erfuellt(neu, b.modell)
        # das Modell der umbenannten Formel, zurückübersetzt, erfüllt auch die Originalformel
        if b.antwort:
            zurueck = {v: b.modell[perm[v - 1]] for v in range(1, inst.n + 1)}
            assert modell_erfuellt(inst.klauseln, zurueck)


def test_mini_instanz_mit_gleichstand_der_aktivitaeten():
    """Von Hand: (x1 ∨ x2)(x1 ∨ ¬x2)(¬x1 ∨ x3 ∨ x4)(¬x1 ∨ x3 ∨ ¬x4)(¬x1 ∨ ¬x3 ∨ x4)(¬x1 ∨ ¬x3 ∨ ¬x4) ist unerfüllbar.
    Alle Aktivitäten 0: Entscheidung ¬x1 (kleinste Nummer, Wert falsch) erzwingt x2 und ¬x2, Konflikt 1 beteiligt x1 und x2 (je +1), gelernt (x1), Sprung auf
    Stufe 0. Offen sind x2 (Aktivität 1), x3 und x4 (je 0): Entscheidung x2 (höchste Aktivität, eindeutig, zuletzt wahr). Danach x3 und x4 mit
    Gleichstand 0: kleinste Nummer (x3), Wert falsch; das erzwingt x4 und verletzt (x1-frei vereinfacht) (x3 ∨ ¬x4): Konflikt 2 beteiligt x3 und x4."""
    inst = Instanz(4, [(1, 2), (1, -2), (-1, 3, 4), (-1, 3, -4), (-1, -3, 4), (-1, -3, -4)], {})
    erg = A.loese(inst, trace=True)
    assert erg.antwort is False
    ents = [e for e in erg.spur if e[0] == "entscheide"]
    assert [e[1] for e in ents[:3]] == [-1, 2, -3]
    assert ents[0][3]["gleichstand"] == 4 and ents[0][3]["aktivitaet"] == 0.0
    assert ents[1][3]["aktivitaet"] == 1.0 and ents[1][3]["gleichstand"] == 1 and ents[1][3]["phase_gespeichert"] is True
    assert ents[2][3]["aktivitaet"] == 0.0 and ents[2][3]["gleichstand"] == 2        # x3 und x4 gleichauf: kleinste Nummer
    konflikte, _ = nachvollzug(erg.spur, inst.n, 0.95, exakt=False)
    assert konflikte[0][0] == {1, 2} and konflikte[1][0] == {3, 4}
