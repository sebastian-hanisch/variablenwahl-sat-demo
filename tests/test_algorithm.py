"""Einheiten der Variablenwahl gegen Handrechnung: Handbeispiel F3 (Zerfall 1/2), Wahlregeln, Phasenspeicher, Schritt-Aufbereitung.

Die Sollwerte des Handbeispiels sind von Hand hergeleitet (Plan, Abschnitt „Handbeispiel“; unabhängig mit Brüchen nachgerechnet): drei Konflikte, gelernte
Klauseln (x5 ∨ x2 ∨ x1), (x2 ∨ x1), (¬x3 ∨ x7 ∨ ¬x5), Sprünge auf Stufe 2, 1, 3, Aktivitäten nach jedem Konflikt und die Entscheidungsfolge."""

from fractions import Fraction as Fr

import pytest
from hilfen import modell_erfuellt

import vsd_algorithm as A
import vsd_constants as C
import vsd_scenario as S
from vsd_cdcl import Loeser

AKT1 = {1: Fr(1), 2: Fr(1), 3: Fr(0), 4: Fr(1), 5: Fr(1), 6: Fr(0), 7: Fr(1)}
AKT2 = {1: Fr(3), 2: Fr(3), 3: Fr(2), 4: Fr(1), 5: Fr(3), 6: Fr(2), 7: Fr(3)}
AKT3 = {1: Fr(3), 2: Fr(3), 3: Fr(6), 4: Fr(5), 5: Fr(7), 6: Fr(2), 7: Fr(7)}


def _lauf(f3, **kw):
    return A.loese(f3, zerfall=0.5, trace=True, **kw)


def test_f3_drei_konflikte_klauseln_und_spruenge(f3):
    erg = _lauf(f3)
    assert erg.antwort is True and erg.stat["konflikte"] == 3
    gelernt = [(e[1], e[2]) for e in erg.spur if e[0] == "lerne"]
    assert gelernt == [([5, 2, 1], 2), ([2, 1], 1), ([-3, 7, -5], 3)]
    konflikt_klauseln = [e[1] for e in erg.spur if e[0] == "konflikt"]
    assert sorted(konflikt_klauseln[0], key=abs) == [1, -4, -7]        # Konflikt 1 in K2 (¬x7 ∨ ¬x4 ∨ x1)
    assert sorted(konflikt_klauseln[1], key=abs) == [-3, 6, 7]         # Konflikt 2 in K7 (x6 ∨ x7 ∨ ¬x3)
    assert sorted(konflikt_klauseln[2], key=abs) == [-3, -4, 7]        # Konflikt 3 in K9 (¬x3 ∨ x7 ∨ ¬x4)


def test_f3_beteiligte_und_aktivitaeten_nach_jedem_konflikt(f3):
    erg = _lauf(f3)
    beteiligt = [e[1] for e in erg.spur if e[0] == "beteiligt"]
    assert [sorted(v for v, _ in b) for b in beteiligt] == [[1, 2, 4, 5, 7], [1, 2, 3, 5, 6, 7], [3, 4, 5, 7]]
    akt = {v: Fr(0) for v in range(1, 8)}
    nach = []
    for b in beteiligt:
        for v, a in b:
            akt[v] = Fr(a)                    # bei Zerfall 1/2 sind alle Werte exakt darstellbar
        nach.append(dict(akt))
    assert nach == [AKT1, AKT2, AKT3]


def test_f3_aktivitaet_durch_zuwachs_ist_die_abgezinste_summe(f3):
    """Äquivalenz des Zuwachs-Tricks von Hand: x5 war an Konflikt 1, 2, 3 beteiligt: 7 / 8 = (1/2)^3 + (1/2)^2 + (1/2)^1."""
    zuwachs = Fr(8)                                              # nach drei Konflikten: 2^3
    beteiligt_je_konflikt = [{1, 2, 4, 5, 7}, {1, 2, 3, 5, 6, 7}, {3, 4, 5, 7}]
    for v in range(1, 8):
        alter_summe = sum(Fr(1, 2) ** (4 - k) for k, b in enumerate(beteiligt_je_konflikt, start=1) if v in b)
        assert AKT3[v] / zuwachs == alter_summe, v
    assert AKT3[5] / zuwachs == Fr(7, 8)


def test_f3_entscheidungsfolge(f3):
    erg = _lauf(f3)
    ents = [(e[1], e[2], e[3]) for e in erg.spur if e[0] == "entscheide"]
    # vor dem ersten Konflikt: alle Aktivitäten 0, kleinste Nummer, Wert falsch
    assert [(l, s) for l, s, _ in ents[:3]] == [(-1, 1), (-2, 2), (-3, 3)]
    assert [i["gleichstand"] for _, _, i in ents[:3]] == [7, 6, 5]
    # nach Konflikt 2: x5 (Aktivität 3, Gleichstand mit x7, kleinere Nummer, zuletzt wahr), dann x7 (3, zuletzt falsch), dann x3 (2, Gleichstand mit x6, zuletzt wahr)
    (l4, s4, i4), (l5, s5, i5), (l6, s6, i6) = ents[3:6]
    assert (l4, s4) == (5, 2) and i4["aktivitaet"] == 3.0 and i4["gleichstand"] == 2 and i4["phase_gespeichert"] is True
    assert (l5, s5) == (-7, 3) and i5["aktivitaet"] == 3.0 and i5["gleichstand"] == 1 and i5["phase_gespeichert"] is False
    assert (l6, s6) == (3, 4) and i6["aktivitaet"] == 2.0 and i6["gleichstand"] == 2 and i6["phase_gespeichert"] is True
    # nach Konflikt 3: x4 (Aktivität 5, zuletzt wahr), dann x6 (Aktivität 2); x6 hatte zuletzt den Wert falsch, weil es in diesem Lauf
    # auf Stufe 2 durch K13 falsch erzwungen und beim Sprung zurückgenommen wurde (die Belegung von x6 auf Stufe 4 kommt nicht mehr zustande)
    assert [(l, i["aktivitaet"]) for l, _, i in ents[6:]] == [(4, 5.0), (-6, 2.0)]
    assert len(ents) == 8 == erg.stat["entscheidungen"]


def test_f3_modell_erfuellt_alle_klauseln(f3):
    erg = _lauf(f3)
    assert modell_erfuellt(f3.klauseln, erg.modell)
    assert erg.modell == {1: False, 2: True, 3: False, 4: True, 5: True, 6: False, 7: False}


def test_f3_feste_reihenfolge_waehlt_anders(f3):
    """Die feste Reihenfolge hätte nach Konflikt 2 als Nächstes x3 gewählt (nicht x5), mit dem gespeicherten Wert wahr."""
    erg = _lauf(f3)
    folge = A.schritte(erg.spur, f3.n, 0.5)
    vierte = folge[-1].entscheidungen[3]
    assert vierte["variable"] == 5 and vierte["fest_variable"] == 3 and vierte["fest_lit"] == 3 and vierte["abweichung"]
    fuenfte = folge[-1].entscheidungen[4]
    assert fuenfte["variable"] == 7 and fuenfte["fest_variable"] == 3 and fuenfte["abweichung"]
    sechste = folge[-1].entscheidungen[5]
    assert sechste["variable"] == 3 and sechste["fest_variable"] == 3 and not sechste["abweichung"]
    # vor dem ersten Konflikt stimmen beide Regeln überein (alle Aktivitäten 0, kleinste Nummer)
    assert not any(d["abweichung"] for d in folge[-1].entscheidungen[:3])


def test_f3_feste_reihenfolge_laeuft_und_antwortet_gleich(f3):
    fest = A.loese(f3, wahl=A.WAHL_FEST, zerfall=0.5, trace=True)
    assert fest.antwort is True and modell_erfuellt(f3.klauseln, fest.modell)
    ents = [e for e in fest.spur if e[0] == "entscheide"]
    assert all(e[3]["art"] == "reihenfolge" for e in ents)
    assert [abs(e[1]) for e in ents[:3]] == [1, 2, 3]                  # kleinste offene Variable


# --- Wahlregeln einzeln --------------------------------------------------------------------------------------------------------------------

def test_waehle_aktivitaet_gleichstand_kleinste_nummer():
    akt = {1: 1.0, 2: 5.0, 3: 1.0, 4: 0.5}
    assert A.waehle_aktivitaet(4, {2}, akt) == 1                          # x2 ist belegt; x1 und x3 gleichauf, kleinste Nummer
    assert A.waehle_aktivitaet(4, set(), akt) == 2
    assert A.waehle_aktivitaet(4, {1, 2, 3, 4}, akt) is None
    assert A.waehle_aktivitaet(3, set(), {1: 0.0, 2: 0.0, 3: 0.0}) == 1   # alle 0: kleinste Nummer


def test_waehle_fest_kleinste_offene():
    assert A.waehle_fest(4, {1, 2}) == 3
    assert A.waehle_fest(3, set()) == 1
    assert A.waehle_fest(3, {1, 2, 3}) is None


def test_optionen_grenzen_und_namen():
    o = A.optionen()
    assert o == {"vsids": True, "phase_saving": True, "decay": 0.95, "restarts": "luby", "restart_unit": 32}
    assert A.optionen(A.WAHL_FEST, False, 0.5) == {"vsids": False, "phase_saving": False, "decay": 0.5, "restarts": "luby", "restart_unit": 32}
    assert A.optionen(zerfall=1.0)["decay"] == 1.0                          # Grenzen inklusive
    for schlecht in (0.49, 0.0, 1.01, -1.0):
        with pytest.raises(ValueError):
            A.optionen(zerfall=schlecht)
    with pytest.raises(ValueError):
        A.optionen(wahl="zufall")


def test_phasenspeicher_schalter_aendert_den_wert():
    """Ohne Phasenspeicher ist jede Entscheidung falsch; mit ihm kehrt eine Variable zu ihrem zuletzt zurückgenommenen Wert zurück."""
    inst = S.hand_formel()
    mit = A.loese(inst, zerfall=0.5, trace=True)
    ohne = A.loese(inst, phase=False, zerfall=0.5, trace=True)
    assert all(e[1] < 0 for e in ohne.spur if e[0] == "entscheide")
    assert any(e[1] > 0 for e in mit.spur if e[0] == "entscheide")
    assert all(e[3]["phase_gespeichert"] is None for e in ohne.spur if e[0] == "entscheide")


def test_waehle_literal_des_loesers_folgt_dem_gemerkten_wert():
    s = Loeser(3, [(1, 2, 3)], phase_saving=True)
    s.gemerkt[2] = True
    assert s.waehle_literal(2) == 2 and s.waehle_literal(1) == -1
    t = Loeser(3, [(1, 2, 3)], phase_saving=False)
    t.gemerkt[2] = True
    assert t.waehle_literal(2) == -2


# --- Schritt-Aufbereitung ------------------------------------------------------------------------------------------------------------------

def test_schritte_ein_schritt_je_ereignis_und_endstand(f3):
    erg = _lauf(f3)
    folge = A.schritte(erg.spur, f3.n, 0.5)
    assert len(folge) == len(erg.spur) and [s.nr for s in folge] == list(range(1, len(folge) + 1))
    assert folge[-1].aktivitaet == {v: float(a) for v, a in AKT3.items()}
    assert folge[-1].konflikte == 3 and folge[-1].zuwachs == 8.0
    assert [k for k, _ in folge[-1].gelernt] == [[5, 2, 1], [2, 1], [-3, 7, -5]]
    # nach dem ersten Konflikt: x1, x2, x4, x5, x7 haben Aktivität 1, der nächste Zuwachs ist 2
    nach_k1 = next(s for s in folge if s.art == "beteiligt")
    assert nach_k1.aktivitaet == {v: float(a) for v, a in AKT1.items()} and nach_k1.zuwachs == 2.0
    assert nach_k1.hervorgehoben == (1, 2, 4, 5, 7)
    assert "x1, x2, x4, x5, x7" in nach_k1.text and "+1 Aktivität" in nach_k1.text


def test_schritte_phasen_stimmen_mit_dem_loeser_ueberein(f3):
    """Die selbst geführte Phasenerinnerung der Aufbereitung entspricht dem gespeicherten Wert, den der Löser in jede Entscheidung schreibt."""
    erg = _lauf(f3)
    folge = A.schritte(erg.spur, f3.n, 0.5)
    ents = [e for e in erg.spur if e[0] == "entscheide"]
    for d, e in zip(folge[-1].entscheidungen, ents):
        gespeichert = e[3]["phase_gespeichert"]
        assert (d["lit"] > 0) == gespeichert
    assert "Anfangswert" in folge[-1].entscheidungen[0]["wert"] and "zuletzt wahr" in folge[-1].entscheidungen[3]["wert"]


def test_schritte_belegung_nach_sprung_und_gelernter_einheit():
    """(x1 ∨ x2)(x1 ∨ ¬x2): Entscheidung ¬x1 erzwingt x2 und ¬x2, Konflikt, gelernt wird die Einheit (x1), Sprung auf Stufe 0.
    Die Einheit hat keinen Schluss-Eintrag in der Spur; die Aufbereitung führt sie als Belegung auf Stufe 0."""
    from vsd_instanzen import Instanz
    inst = Instanz(2, [(1, 2), (1, -2)], {})
    erg = A.loese(inst, trace=True)
    assert erg.antwort is True and erg.stat["konflikte"] == 1
    folge = A.schritte(erg.spur, inst.n, 0.95)
    assert [k for k, _ in folge[-1].gelernt] == [[1]]
    assert (1, 0, None) in folge[-1].belegung
    nach_sprung = next(s for s in folge if s.art == "springe")
    assert nach_sprung.belegung == [(1, 0, None)] and nach_sprung.stufe == 0


def test_zahl_text_und_literal_text():
    assert A.zahl_text(3.0) == "3" and A.zahl_text(0.5) == "0,50" and A.zahl_text(1.0000000001) == "1"
    assert A.literal_text(3) == "x3" and A.literal_text(-12) == "¬x12"
    assert A.klausel_text((5, -2, 1)) == "(x5 ∨ ¬x2 ∨ x1)"
    assert C.HAND_ZERFALL == 0.5 and S.F3_N == 7 and len(S.F3_KLAUSELN) == 14
