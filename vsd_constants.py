"""Konstanten: Regler-Grenzen, feste Annahmen, Aufgaben der Messreihen, Farben und Presets."""

# --- Löser ----------------------------------------------------------------------------------------------------------------------------------
ZERFAELLE = (0.5, 0.8, 0.95, 0.99, 1.0)     # Messraster des Zerfalls; 0,5 ist die untere Grenze (Grenzwert 0 wird nicht zugelassen, siehe README)
DEFAULT_ZERFALL = 0.95                       # Voreinstellung der Messreihen (wie MiniSat)
HAND_ZERFALL = 0.5                           # Handbeispiel: der Zuwachs verdoppelt sich je Konflikt, damit man von Hand rechnen kann
NEUSTART_EINHEIT = 32                        # Luby-Neustarts bleiben in allen Läufen eingeschaltet (eigenes Stück 4)
BUDGET_REFERENZ = 20000                      # Konfliktbudget der vorgerechneten Messreihen
BUDGET_LIVE = (500, 5000)                    # Regler „Budget“ der Live-Messreihen
DEFAULT_BUDGET_LIVE = 2000

# --- Formeln --------------------------------------------------------------------------------------------------------------------------------
VERHAELTNIS = 4.26                           # Klauseln je Variable der Zufallsformeln (Übergangsbereich, Stück „SAT in der Praxis“)
RAMPEN_GRAD = 4.5                            # mittlerer Grad des Konfliktgraphen (Aufträge im Zeitkonflikt)
RAMPEN_K = 3                                 # Rampen (Farben)
SCHUR_K = 4                                  # Mengen
ZUFALL_SEEDS = tuple(range(2000, 2012))      # 12 feste Formeln je Zufallsfamilie: nie ein einzelner Seed als Befund
RAMPEN_SEEDS = tuple(range(500, 510))        # 10 feste Konfliktgraphen
LOESER_SEEDS = tuple(range(20))              # 20 Zufalls-Seeds der Löser (zufälliger Start der Aktivitäten) bei der einen Schur-Instanz
KLEIN_N = (8, 12)                            # Schritt-für-Schritt-Ansicht: Zufallsformel mit 8 bis 12 Variablen (höchstens 60 Klauseln)
DEFAULT_KLEIN_N, DEFAULT_KLEIN_SEED = 10, 0           # n = 10, Zufalls-Seed 0: sechs Konflikte, erfüllbar
SEED_MAX = 999999
SCHUBFACH_H = (5, 6)                         # Schubfach-Instanzen der Randbemerkung (deterministisch, ein Lauf je Verfahren)
MAX_SCHRITT_VARIABLEN = 12
MAX_SCHRITT_KLAUSELN = 60

# --- Aufgaben der Messreihen (Schlüssel -> Beschreibung) -------------------------------------------------------------------------------------
AUFGABEN = {
    "zufall100": {"label": "Zufalls-3-SAT n = 100", "art": "zufall", "groesse": 100, "anzahl": 12},
    "zufall150": {"label": "Zufalls-3-SAT n = 150", "art": "zufall", "groesse": 150, "anzahl": 12},
    "rampen160": {"label": "Rampen (Färbung, n = 160)", "art": "rampen", "groesse": 160, "anzahl": 10},
    "schur43": {"label": "Schur n = 43, k = 4", "art": "schur", "groesse": 43, "anzahl": 20},
    "schur44": {"label": "Schur n = 44, k = 4", "art": "schur", "groesse": 44, "anzahl": 20},
}
AUFGABEN_LABELS = tuple(a["label"] for a in AUFGABEN.values())
SCHLUESSEL_VON_LABEL = {a["label"]: k for k, a in AUFGABEN.items()}
# Vorgerechnete Zellen je Experiment (tools/messungen.py schreibt sie nach vsd_messungen.json)
ZELLEN_AKTIVITAET = ("zufall100", "zufall150", "rampen160")
ZELLEN_PHASE = ("zufall150", "rampen160", "schur43", "schur44")
ZELLEN_ZERFALL = ("zufall150", "rampen160")
# Live-Messreihen: Größenbereich je Art (Regler im Hauptbereich), Zahl der Formeln bzw. Läufe
LIVE_GROESSE = {"zufall": (50, 110, 80, 10), "rampen": (60, 140, 100, 10), "schur": (36, 44, 40, 1)}   # (min, max, Voreinstellung, Schritt)
LIVE_ANZAHL = (2, 8, 4)                      # (min, max, Voreinstellung): feste Formeln bzw. Zufalls-Seeds des Lösers

# --- Verfahren (Namen der Messreihen) --------------------------------------------------------------------------------------------------------
VERFAHREN_LABEL = {
    "aktivitaet": "Aktivität + Phasenspeicher",
    "fest": "feste Reihenfolge + Phasenspeicher",
    "ohne_phase": "Aktivität ohne Phasenspeicher",
}
SCHWELLE_KLAR = 1.5     # Medianverhältnis, ab dem ein Unterschied im Verdikt als Richtung gelesen wird; darunter „kein klarer Unterschied“

# --- Darstellung ----------------------------------------------------------------------------------------------------------------------------
COLOR_AKTIV = "#2F6B65"
COLOR_FEST = "#B5651D"
COLOR_OHNE = "#7A6FA8"
COLOR_BELEGT = "rgba(150,150,150,0.55)"
COLOR_WAHL = "#C0392B"
COLOR_BETEILIGT = "#E3A92B"

# --- Presets ---------------------------------------------------------------------------------------------------------------------------------
PRESETS = {
    "Handbeispiel F3": {"aufgabe": "Zufalls-3-SAT n = 150", "formel": "Handbeispiel F3", "zerfall": HAND_ZERFALL},
    "Rampen (Färbung, n = 160)": {"aufgabe": "Rampen (Färbung, n = 160)", "formel": "Handbeispiel F3", "zerfall": DEFAULT_ZERFALL},
    "Zufalls-3-SAT n = 150": {"aufgabe": "Zufalls-3-SAT n = 150", "formel": "Handbeispiel F3", "zerfall": DEFAULT_ZERFALL},
    "Schur n = 44, k = 4": {"aufgabe": "Schur n = 44, k = 4", "formel": "Handbeispiel F3", "zerfall": DEFAULT_ZERFALL},
}
PRESET_HELP = {
    "Handbeispiel F3": "Sieben Variablen, 14 Klauseln, Zerfall 0,5: drei Konflikte, die man von Hand nachrechnen kann. Die Messreihen darunter zeigen Zufalls-3-SAT n = 150.",
    "Rampen (Färbung, n = 160)": "Aufträge auf drei Rampen, Konfliktgraph mit mittlerem Grad 4,5; Messreihen auf zehn festen Graphen, Zerfall 0,95.",
    "Zufalls-3-SAT n = 150": "Zufallsformeln mit 4,26 Klauseln je Variable; Messreihen auf zwölf festen Formeln, Zerfall 0,95.",
    "Schur n = 44, k = 4": "Zahlen 1 bis 44 auf vier Mengen ohne a + b = c in einer Menge; eine Instanz, 20 Zufalls-Seeds der Löser, an der Grenze der Lösbarkeit.",
}
