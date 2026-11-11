"""Figuren: Sortierung der Balken, Farben je Zustand, Streifendiagramm (Punkte, Abbruchkreuze, Median, feste Achsen)."""

import vsd_constants as C
import vsd_visualization as V


def test_sortierung_absteigend_bei_gleichstand_kleinere_nummer_zuerst():
    akt = {1: 3.0, 2: 3.0, 3: 2.0, 4: 1.0, 5: 3.0, 6: 2.0, 7: 3.0}
    assert V.sortierte_variablen(akt) == [1, 2, 5, 7, 3, 6, 4]


def test_aktivitaetsbalken_farben_belegt_hervorgehoben_offen():
    akt = {1: 3.0, 2: 1.0, 3: 0.0}
    fig = V.build_aktivitaet(akt, belegt={2, 3}, hervorgehoben=(1, 2), titel="t")
    balken = fig.data[0]
    assert list(balken.x) == ["x1", "x2", "x3"] and list(balken.y) == [3.0, 1.0, 0.0]
    assert list(balken.marker.color) == [C.COLOR_WAHL, C.COLOR_BETEILIGT, C.COLOR_BELEGT]       # offen+hervorgehoben, belegt+hervorgehoben, belegt
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_aktivitaetsbalken_alle_null_hat_endliche_achse():
    fig = V.build_aktivitaet({1: 0.0, 2: 0.0}, set(), (), "t")
    assert fig.layout.yaxis.range[1] == 1.0
    assert list(fig.data[0].marker.color) == [C.COLOR_AKTIV, C.COLOR_AKTIV]


def test_streifen_punkte_kreuze_und_median():
    reihen = {"a": {"konflikte": [10, 100, 20000], "antwort": [True, False, None]},
              "b": {"konflikte": [0, 50], "antwort": [True, True]}}
    fig = V.build_streifen(reihen, 20000, {"a": "Verfahren A + x", "b": "Verfahren B"}, {"a": "#111111", "b": "#222222"}, "Titel")
    assert [t.name for t in fig.data] == ["Verfahren A + x", "Verfahren B"]
    a, b = fig.data
    assert list(a.marker.symbol) == ["circle", "circle", "x"]                    # der Abbruch ist ein Kreuz
    assert list(b.y) == [0.7, 50]                                               # 0 Konflikte auf der logarithmischen Achse bei 0,7
    medianstriche = [s for s in fig.layout.shapes if s.type == "line" and s.xref != "x domain"]       # ohne die Budgetlinie (x domain)
    assert [s.y0 for s in medianstriche] == [100, 25.0]                          # Median 100 bzw. (0 + 50) / 2
    assert fig.layout.yaxis.type == "log" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert "<br>" in fig.layout.xaxis.ticktext[0]                               # lange Beschriftungen brechen um
