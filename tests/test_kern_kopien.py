"""Die kopierten Kern-Module (`vsd_rng`, `vsd_instanzen`, `vsd_cdcl`): wörtliche Kopie, Regressionswerte und Einheiten mit Handrechnung.

Die Kopien stammen aus `sat-cp-planung/kern/` (Kern-Version im Modulkopf). Die Vergleichsprüfung mit dem Kern läuft nur, solange der Ordner
neben dem Repo liegt; die übrigen Tests bleiben als Regression bei der Kopie (SplitMix64-Werte, Instanzerzeuger, CDCL-Einheiten).
"""

import re
from pathlib import Path

import pytest

import vsd_instanzen as I
from vsd_cdcl import Loeser, luby, solve
from vsd_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
VERSION = {"rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8", "cdcl": "832b2c10dfdea62d"}


def _lies(pfad: Path) -> str:
    return pfad.read_bytes().decode("utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("modul", ["rng", "instanzen", "cdcl"])
def test_kopie_gleicht_dem_kern_bis_auf_kopf_und_importe(modul):
    quelle = KERN / f"{modul}.py"
    if not quelle.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    kopie = _lies(ROOT / f"vsd_{modul}.py")
    kopf = kopie.split("\n", 2)
    assert VERSION[modul] in kopf[0] and f"kern/{modul}.py" in kopf[0]
    rest = kopie.split("\n", 2)[2]
    rest = re.sub(r"^from vsd_rng import", "from rng import", rest, flags=re.M)
    assert rest == _lies(quelle)


def test_kern_version_stimmt_mit_hashes_txt():
    hashes = KERN / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    eintraege = {zeile.split()[1]: zeile.split()[0] for zeile in hashes.read_text(encoding="utf-8").splitlines() if zeile.strip()}
    for modul, version in VERSION.items():
        assert eintraege[f"{modul}.py"] == version


# --- SplitMix64 und Instanzen -------------------------------------------------------------------------------------------------------------

def test_splitmix_bekannte_werte():
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    h = SplitMix64(12345)
    assert [h.next() for _ in range(3)] == [2454886589211414944, 3778200017661327597, 2205171434679333405]


def test_splitmix_hilfsmethoden():
    g = SplitMix64(5)
    xs = [g.random() for _ in range(1000)]
    assert all(0 <= x < 1 for x in xs) and 0.45 < sum(xs) / 1000 < 0.55
    liste = list(range(20))
    SplitMix64(3).shuffle(liste)
    assert sorted(liste) == list(range(20)) and liste != list(range(20))
    probe = SplitMix64(3).sample(range(50), 7)
    assert len(set(probe)) == 7 and SplitMix64(3).sample(range(50), 7) == probe


def test_rand3_referenzwerte_und_praefix():
    # Referenzwerte aus red_scenario.random_formula (Komplexitätsklassen, Stück 3): n = 5, m = 3, Seed 7
    assert I.rand3(5, 3, 7).klauseln == [(3, -2, -1), (-4, -1, 5), (1, 2, -3)]
    kurz, lang = I.rand3(20, 30, 1).klauseln, I.rand3(20, 40, 1).klauseln
    assert lang[:30] == kurz and all(len({abs(l) for l in c}) == 3 for c in lang)


def test_schubfach_schur_faerbung_handwerte():
    inst = I.pigeonhole(2)                      # 3 Tauben, 2 Löcher
    assert inst.n == 6 and len(inst.klauseln) == 3 + 2 * 3
    assert solve(inst.n, inst.klauseln).antwort is False
    assert solve(*I.schur(13, 3)[:2]).antwort is True and solve(*I.schur(14, 3)[:2]).antwort is False      # S(3) = 13
    dreieck = I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 2)
    assert solve(dreieck.n, dreieck.klauseln).antwort is False
    a, b = I.flat_graph(40, 4.0, 3), I.flat_graph(40, 4.0, 3)
    assert a.klauseln == b.klauseln and len(a.meta["kanten"]) == 80
    r = I.rampen_instanz(30, 3.0, 2, 4)
    assert r.meta["einkleidung"] == "rampen" and r.meta["rampen"] == 4


# --- CDCL-Einheiten -----------------------------------------------------------------------------------------------------------------------

def test_luby_folge():
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]
    with pytest.raises(ValueError):
        luby(0)


def _lehrbeispiel(**kw):
    # Von Hand: c1 = (¬1 ∨ 2), c2 = (¬1 ∨ 3 ∨ 5), c3 = (¬2 ∨ 4), c4 = (¬3 ∨ ¬4)
    return Loeser(5, [(-1, 2), (-1, 3, 5), (-2, 4), (-3, -4)], **kw)


@pytest.mark.parametrize("watch", [True, False])
def test_konfliktanalyse_1uip_handrechnung(watch):
    """Entscheidung ¬5 (Stufe 1), dann 1 (Stufe 2): 1 → 2 (c1), 1 ∧ ¬5 → 3 (c2), 2 → 4 (c3), c4 ist verletzt. 1-UIP ist die Entscheidung 1 selbst.
    Gelernt wird (¬1 ∨ 5), Rücksprung auf Stufe 1, LBD 2."""
    s = _lehrbeispiel(watch=watch)
    s.entscheide(-5)
    assert s.propagiere() is None
    s.entscheide(1)
    k = s.propagiere()
    assert k is not None
    klausel, rueck, lbd = s.analysiere(k)
    assert sorted(klausel) == [-1, 5] and klausel[0] == -1 and rueck == 1 and lbd == 2
    assert set(s.beteiligte) == {1, 2, 3, 4, 5}


def test_rueckspringen_und_phasenspeicher():
    s = _lehrbeispiel()
    s.entscheide(-5)
    s.propagiere()
    s.entscheide(1)
    s.propagiere()
    s.springe_zurueck(1)
    assert len(s.grenzen) == 1 and s.spur_lit == [-5] and [s.wert[v] for v in (1, 2, 3, 4)] == [0, 0, 0, 0]
    s.springe_zurueck(0)
    assert s.spur_lit == [] and s.gemerkt[5] is False and s.gemerkt[1] is True       # Phasenspeicher: 1 war zuletzt wahr


def test_spur_entscheidung_mit_begruendung_und_decay():
    erg = solve(3, [(1, 2, 3), (-1, 2), (-2, 3)], trace=True)
    art, lit, stufe, info = erg.spur[0]
    assert (art, lit, stufe) == ("entscheide", -1, 1)
    assert info == {"art": "aktivitaet", "aktivitaet": 0.0, "gleichstand": 3, "phase_gespeichert": False, "wahl": "falsch"}
    inst = I.pigeonhole(3)
    for decay in (0.5, 0.95):
        s = Loeser(inst.n, inst.klauseln, decay=decay)
        erg = s.loese()
        assert erg.antwort is False
        assert s.zuwachs == pytest.approx((1 / decay) ** erg.stat["gelernt"])


def test_statische_wahl_und_startphase():
    s = Loeser(3, [(1, 2, 3)], vsids=False)
    assert s.waehle() == 1
    s.entscheide(-1)
    assert s.waehle() == 2 and s.waehle_literal(2) == -2
    assert solve(3, [(1, 2, 3)], vsids=False, startphase=True).modell == {1: True, 2: True, 3: True}
