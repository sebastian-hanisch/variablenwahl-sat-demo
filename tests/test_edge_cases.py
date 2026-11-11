"""Randfälle der Variablenwahl (DEMO-PLAYBOOK §12): alle Aktivitäten 0, ein einziger Konflikt, Überlauf, Zerfall 1,0, Zerfall unter der Grenze, Budget."""

from fractions import Fraction

import pytest
from hilfen import modell_erfuellt, nachvollzug

import vsd_algorithm as A
import vsd_scenario as S
from vsd_cdcl import Loeser
from vsd_instanzen import Instanz, pigeonhole, rand3


def test_alle_aktivitaeten_null_wahl_entspricht_dem_tiebreak():
    """Ohne Konflikt bleibt jede Aktivität 0: die Wahl nach Aktivität ist dann die kleinste Nummer, also dieselbe Entscheidungsfolge wie die feste Reihenfolge."""
    inst = Instanz(4, [(1, 2, 3), (-1, 2, 4)], {})
    akt = A.loese(inst, trace=True)
    fest = A.loese(inst, A.WAHL_FEST, trace=True)
    assert akt.stat["konflikte"] == 0 == fest.stat["konflikte"]
    def folge(e):
        return [(x[1], x[2]) for x in e.spur if x[0] == "entscheide"]

    assert folge(akt) == folge(fest) == [(-1, 1), (-2, 2), (-4, 3)]        # x3 wird von (x1 ∨ x2 ∨ x3) erzwungen


def test_ein_einziger_konflikt():
    """(x1 ∨ x2)(x1 ∨ ¬x2): ein Konflikt, x1 und x2 erhalten je +1, das Modell setzt x1 wahr."""
    inst = Instanz(2, [(1, 2), (1, -2)], {})
    erg = A.loese(inst, trace=True)
    assert erg.antwort is True and erg.stat["konflikte"] == 1 and erg.modell[1] is True
    beteiligt = [e[1] for e in erg.spur if e[0] == "beteiligt"]
    assert len(beteiligt) == 1 and sorted(beteiligt[0]) == [(1, 1.0), (2, 1.0)]
    assert modell_erfuellt(inst.klauseln, erg.modell)


def test_unerfuellbare_formel_ohne_entscheidung_und_mit_einheiten():
    """Die Formel (x1)(¬x1) ist schon beim Aufnehmen widersprüchlich: Antwort unerfüllbar, kein Konflikt, keine Entscheidung."""
    erg = A.loese(Instanz(1, [(1,), (-1,)], {}), trace=True)
    assert erg.antwort is False and erg.stat["konflikte"] == 0 and erg.stat["entscheidungen"] == 0 and erg.spur == []
    assert A.schritte(erg.spur, 1, 0.95) == []


def test_zerfall_eins_vergisst_nichts():
    """Zerfall 1,0: der Zuwachs bleibt 1, die Aktivität zählt die Konflikte mit Beteiligung (ohne Abzinsen)."""
    inst = pigeonhole(4)
    s = Loeser(inst.n, inst.klauseln, decay=1.0, trace=True)
    erg = s.loese()
    beteiligt = [{v for v, _ in e[1]} for e in erg.spur if e[0] == "beteiligt"]
    assert s.zuwachs == 1.0 and beteiligt
    for v in range(1, inst.n + 1):
        assert s.aktivitaet[v] == sum(v in b for b in beteiligt)


def test_zerfall_grenze_halb_inklusive_und_darunter_abgelehnt():
    assert A.optionen(zerfall=0.5)["decay"] == 0.5 and A.optionen(zerfall=1.0)["decay"] == 1.0
    with pytest.raises(ValueError):
        A.optionen(zerfall=0.499)
    with pytest.raises(ValueError):
        A.optionen(zerfall=0.0)


def test_zerfall_gegen_null_zaehlt_nur_der_letzte_konflikt():
    """Begründung der Mindestgrenze: bei kleinem Zerfall wächst der Zuwachs so schnell, dass der letzte Konflikt alle früheren zusammen übertrifft
    (Zuwachs 1/δ^(k-1) gegen die Summe der früheren Zuwächse). Bei δ = 0,5 ist die Summe aller früheren Zuwächse 2^(k-1) − 1, noch kleiner als der letzte."""
    d = Fraction(1, 2)
    for k in range(2, 12):
        assert sum(d ** -(i - 1) for i in range(1, k)) < d ** -(k - 1)
    d = Fraction(1, 20)
    assert sum(d ** -(i - 1) for i in range(1, 6)) < d ** -5          # bei 0,05 erst recht
    d = Fraction(95, 100)
    assert sum(d ** -(i - 1) for i in range(1, 6)) > d ** -5          # bei 0,95 zählen frühere Konflikte zusammen mehr als der letzte


def test_budget_erreicht_liefert_unbekannt_nie_unerfuellbar():
    inst = pigeonhole(6)
    erg = A.loese(inst, budget=50)
    assert erg.antwort is None and erg.stat["konflikte"] == 50 and erg.modell is None
    voll = A.loese(pigeonhole(3))
    assert voll.antwort is False


def test_budget_gleich_der_noetigen_konfliktzahl_ist_untere_schranke():
    """Ein Lauf, der genau beim Budget beendet wird, wird als Abbruch gemeldet (untere Schranke): mit Budget = Konfliktzahl − 1 sieht man es."""
    inst = rand3(30, S.klauselzahl(30), 305)
    voll = A.loese(inst)
    assert voll.antwort is not None and voll.stat["konflikte"] > 3
    knapp = A.loese(inst, budget=voll.stat["konflikte"] - 1)
    assert knapp.antwort is None and knapp.stat["konflikte"] == voll.stat["konflikte"] - 1


def test_zufalls_seed_des_loesers_aendert_nur_den_start_der_aktivitaeten():
    inst = rand3(40, S.klauselzahl(40), 31)
    a, b = A.loese(inst, seed=1, budget=5000), A.loese(inst, seed=2, budget=5000)
    ohne = A.loese(inst, budget=5000)
    assert a.antwort is b.antwort is ohne.antwort
    assert len({a.stat["konflikte"], b.stat["konflikte"], ohne.stat["konflikte"]}) >= 2                               # nicht alle Läufe gleich
    assert A.loese(inst, seed=1, budget=5000).stat == a.stat                                                         # gleicher Seed, gleicher Lauf


def test_feste_reihenfolge_ignoriert_den_seed():
    inst = rand3(40, S.klauselzahl(40), 31)
    assert A.loese(inst, A.WAHL_FEST, seed=1, budget=3000).stat == A.loese(inst, A.WAHL_FEST, seed=2, budget=3000).stat


def test_schritte_leere_spur_und_unbekannte_ereignisse():
    assert A.schritte([], 3, 0.95) == []
    folge = A.schritte([("neustart",), ("loesche", 4)], 3, 0.95)
    assert [s.text for s in folge] == ["Neustart", "4 gelernte Klauseln gelöscht"]


def test_nachvollzug_findet_eine_falsche_wahl():
    """Der Nachvollzug ist scharf: eine absichtlich verfälschte Entscheidung (kleinste Nummer statt höchster Aktivität) fällt auf."""
    inst = rand3(30, S.klauselzahl(30), 300)
    erg = A.loese(inst, zerfall=0.5, budget=45, trace=True)
    spur = list(erg.spur)
    for i, e in enumerate(spur):
        if e[0] == "entscheide" and e[2] > 1:
            andere = next(v for v in range(1, inst.n + 1) if v != abs(e[1]))
            spur[i] = ("entscheide", -andere, e[2], e[3])
            break
    with pytest.raises(AssertionError):
        nachvollzug(spur, inst.n, Fraction(1, 2), exakt=True)
