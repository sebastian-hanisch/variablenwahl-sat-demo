"""Hilfen der Tests: unabhängiger Nachvollzug einer Spur (eigener Code, kein Aufruf des Lösers, keine Funktion aus `vsd_algorithm`).

`nachvollzug(spur, n, zerfall, ...)` liest nur die Ereignisse `entscheide`, `schliesse`, `konflikt`, `springe`, `lerne` einer Spur und rechnet
daraus selbst: Belegung, gemerkte Phasen, die Herleitung jedes Konflikts nach dem 1-UIP-Schema (Auflösen entlang der Belegung), die
Aktivitäten in exakter Bruchrechnung und prüft jede Entscheidung gegen die Regel „höchste Aktivität, bei Gleichstand kleinste Nummer“.
"""

from fractions import Fraction


def literal_falsch(trail, lit) -> bool:
    return any(l == -lit for l, _, _ in trail)


def herleitung(trail, konflikt, stufe):
    """Variablen der Herleitung (alle gesehenen Variablen oberhalb von Stufe 0) beim Konflikt: 1-UIP-Auflösung von hinten."""
    level = {abs(l): lv for l, lv, _ in trail}
    gesehen, beteiligt, zaehler = set(), set(), 0

    def aufnehmen(klausel, ausser=None):
        nonlocal zaehler
        for q in klausel:
            v = abs(q)
            if v == ausser or level.get(v, 0) == 0:
                continue
            beteiligt.add(v)
            if v not in gesehen:
                gesehen.add(v)
                zaehler += level[v] == stufe

    aufnehmen(konflikt)
    i = len(trail) - 1
    while True:
        lit, lv, grund = trail[i]
        i -= 1
        v = abs(lit)
        if v not in gesehen or lv != stufe:
            continue
        if zaehler == 1:
            return beteiligt          # v ist der erste eindeutige Implikationspunkt
        zaehler -= 1
        gesehen.discard(v)
        aufnehmen(grund, ausser=v)


def nachvollzug(spur, n, zerfall, phase=True, exakt=True, toleranz=1e-9):
    """Rechnet die Spur nach. Rückgabe: Liste der Konflikte als (Variablenmenge, Aktivitäten danach) und Zahl der geprüften Entscheidungen.

    `exakt=True`: Aktivitäten als Brüche, jede Entscheidung genau nach Regel (nur für Zerfall mit exakt darstellbaren Zuwächsen, z. B. 1/2,
    und höchstens etwa 50 Konflikte). Sonst Gleitkomma mit Toleranz: die gewählte Variable muss unter den fast gleichauf Höchsten sein."""
    zerfall = Fraction(zerfall) if exakt else float(zerfall)
    eins = Fraction(1) if exakt else 1.0
    akt = {v: eins * 0 for v in range(1, n + 1)}
    zuwachs = eins
    gemerkt = {v: False for v in range(1, n + 1)}
    trail = []                      # [Literal, Stufe, Grundklausel oder None]
    konflikte, geprueft, einheit = [], 0, None
    for e in spur:
        art = e[0]
        if art == "entscheide":
            _, lit, stufe, info = e
            if info["art"] != "annahme":
                belegt = {abs(l) for l, _, _ in trail}
                offen = [v for v in range(1, n + 1) if v not in belegt]
                v = abs(lit)
                assert v in offen, "entschieden wurde eine belegte Variable"
                if info["art"] == "aktivitaet":
                    hoechste = max(akt[u] for u in offen)
                    if exakt:
                        assert akt[v] == hoechste and v == min(u for u in offen if akt[u] == hoechste)
                    else:
                        nah = [u for u in offen if akt[u] >= hoechste - toleranz * max(1.0, hoechste)]
                        assert v in nah
                else:
                    assert v == offen[0]
                erwartet = gemerkt[v] if phase else False
                assert (lit > 0) == erwartet, "Wert weicht vom Phasenspeicher ab"
                assert info["phase_gespeichert"] == (gemerkt[v] if phase else None)
                geprueft += 1
            trail.append([lit, stufe, None])
        elif art == "schliesse":
            _, lit, klausel, stufe, _ci = e
            assert all(literal_falsch(trail, q) for q in klausel if q != lit), "Schluss ohne falsche übrige Literale"
            trail.append([lit, stufe, list(klausel)])
        elif art == "konflikt":
            _, klausel, stufe, _ci = e
            assert all(literal_falsch(trail, q) for q in klausel), "Konfliktklausel nicht ganz falsch"
            if stufe > 0:
                beteiligt = herleitung(trail, klausel, stufe)
                for v in beteiligt:
                    akt[v] += zuwachs
                zuwachs = zuwachs / zerfall
                konflikte.append((beteiligt, dict(akt)))
        elif art == "lerne":
            klausel = e[1]
            einheit = klausel[0] if len(klausel) == 1 else None
        elif art == "springe":
            stufe = e[1]
            bleibt = []
            for eintrag in trail:
                if eintrag[1] > stufe:
                    if phase:
                        gemerkt[abs(eintrag[0])] = eintrag[0] > 0
                else:
                    bleibt.append(eintrag)
            trail = bleibt
            if einheit is not None:
                trail.append([einheit, 0, None])
                einheit = None
    return konflikte, geprueft


def modell_erfuellt(klauseln, modell) -> bool:
    """Eigene Modellprüfung (unabhängig von `vsd_instanzen.pruefe_modell`)."""
    return all(any(modell[abs(l)] == (l > 0) for l in k) for k in klauseln)


def cpsat_antwort(n, klauseln):
    """OR-Tools CP-SAT als Orakel der Erfüllbarkeit (nur Test)."""
    import pytest
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    m = cp_model.CpModel()
    x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
    for k in klauseln:
        m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in k])
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 60
    r = s.Solve(m)
    assert r in (cp_model.OPTIMAL, cp_model.INFEASIBLE), "CP-SAT ohne Antwort"
    return r == cp_model.OPTIMAL
