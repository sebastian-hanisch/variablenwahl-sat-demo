"""Verdikte an von Hand gesetzten Kennzahlen (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Kennzahlen, nicht Seeds. Die Schwelle für „deutlich“ ist der Faktor 1,5 (Constants.SCHWELLE_KLAR),
inklusive; Abbrüche zählen mit dem Budget (untere Schranke) und werden im Text genannt."""

import vsd_evaluation as E
from vsd_evaluation import Kennzahlen


def kz(median, maximum=None, abbrueche=0, n=12, minimum=1):
    return Kennzahlen(n, float(median), int(maximum if maximum is not None else median), minimum, abbrueche, n - abbrueche, 0, None)


# --- Zahlen ----------------------------------------------------------------------------------------------------------------------------------

def test_zahl_deutsche_schreibweise():
    assert E.zahl(1853) == "1.853" and E.zahl(544.5) == "544,5" and E.zahl(20000.0) == "20.000" and E.zahl(0) == "0" and E.zahl(1234567.5) == "1.234.567,5"
    assert E.zerfall_text(0.95) == "0,95" and E.zerfall_text(1.0) == "1,0"


# --- Aktivität gegen feste Reihenfolge -------------------------------------------------------------------------------------------------------

def test_verdict_aktivitaet_abbrueche_der_festen_reihenfolge():
    kind, text = E.verdict_aktivitaet("Zufalls-3-SAT n = 150", kz(1853, 4410), kz(20000, 20000, abbrueche=7), 20000)
    assert kind == "success"
    assert "**7 von 12** Läufen das Budget von 20.000 Konflikten" in text and "bei Aktivität **0**" in text
    assert "Median der Konflikte 20.000 gegen 1.853 (Maximum 20.000 gegen 4.410)" in text
    assert text.startswith("Zufalls-3-SAT n = 150:")
    assert text.endswith("Mindestens die Hälfte der Läufe eines Verfahrens bricht ab: sein Median ist nur eine untere Schranke.")


def test_verdict_aktivitaet_schwelle_faktor_eineinhalb_inklusive():
    assert E.verdict_aktivitaet("x", kz(100), kz(150), 1000)[0] == "success"      # genau 1,5: deutlich
    kind, text = E.verdict_aktivitaet("x", kz(100), kz(149), 1000)                 # knapp darunter
    assert kind == "info" and "Kein klarer Unterschied" in text and "Abbrüche" not in text
    assert E.verdict_aktivitaet("x", kz(150), kz(100), 1000)[0] == "warning"      # umgekehrt: Aktivität braucht mehr


def test_verdict_aktivitaet_median_null_und_gleichstand():
    assert E.verdict_aktivitaet("x", kz(0), kz(0), 1000)[0] == "info"             # beide 0: kein Unterschied, kein Nullteiler
    assert E.verdict_aktivitaet("x", kz(0), kz(3), 1000)[0] == "success"          # fest 3 gegen 0: jedes positive x über 0
    kind, text = E.verdict_aktivitaet("x", kz(100, abbrueche=1), kz(100, abbrueche=3), 1000)       # gleicher Median, mehr Abbrüche
    assert kind == "success" and text.endswith("Abbrüche zählen mit dem Budget; der Median bleibt davon unberührt, das Maximum ist eine untere Schranke.")


# --- Phasenspeicher --------------------------------------------------------------------------------------------------------------------------

def test_verdict_phase_hilft_mit_abbruechen_wie_schur_44():
    kind, text = E.verdict_phase("Schur n = 44", kz(6313.5, 20000, abbrueche=2, n=20), kz(19879, 20000, abbrueche=10, n=20), 20000)
    assert kind == "success" and "Hier hilft der Phasenspeicher." in text
    assert "Mit Phasenspeicher Median 6.313,5 (Maximum 20.000, 2 von 20 Abbrüchen)" in text
    assert "ohne 19.879 (Maximum 20.000, 10 von 20 Abbrüchen; Budget 20.000)" in text


def test_verdict_phase_kein_klarer_unterschied_und_umgekehrt():
    kind, text = E.verdict_phase("Zufall", kz(1853, 4410), kz(1436, 3874), 20000)      # 1,29: unter der Schwelle
    assert kind == "info" and "Kein klarer Unterschied." in text
    kind, text = E.verdict_phase("Zufall", kz(300), kz(100), 20000)
    assert kind == "warning" and "nicht besser, sondern schlechter" in text
    assert E.verdict_phase("Zufall", kz(150), kz(100), 20000)[0] == "warning"          # genau 1,5, mit schlechter
    assert E.verdict_phase("Zufall", kz(100), kz(150), 20000)[0] == "success"


# --- Zerfall ---------------------------------------------------------------------------------------------------------------------------------

def test_verdict_zerfall_nennt_alle_werte_bester_schlechtester_und_ausreisser():
    werte = {0.5: kz(3424.5), 0.8: kz(2330), 0.95: kz(1853), 0.99: kz(2844.5), 1.0: kz(2208.5)}
    kind, text = E.verdict_zerfall("Zufall n = 150", werte)
    assert kind == "info"
    assert "Zerfall 0,5 / 0,8 / 0,95 / 0,99 / 1,0: 3.424,5 / 2.330 / 1.853 / 2.844,5 / 2.208,5" in text
    assert "Bester Wert 0,95 (1.853), schlechtester 0,5 (3.424,5)" in text
    assert "Um mindestens den Faktor 1,5 über dem besten liegt: 0,5, 0,99." in text      # 3424,5 / 1853 = 1,85 und 2844,5 / 1853 = 1,535


def test_verdict_zerfall_ohne_ausreisser_und_mit_abbruechen():
    werte = {z: kz(100 + i) for i, z in enumerate((0.5, 0.8, 0.95, 0.99, 1.0))}
    kind, text = E.verdict_zerfall("F", werte)
    assert "Kein Wert liegt um den Faktor 1,5 oder mehr über dem besten." in text and "Abbrüche" not in text
    werte[1.0] = kz(104, abbrueche=2)
    assert E.verdict_zerfall("F", werte)[1].endswith("der Median bleibt davon unberührt, das Maximum ist eine untere Schranke.")
    werte[1.0] = kz(104, abbrueche=6)                                           # 6 von 12: der Median enthält einen Abbruch
    assert E.verdict_zerfall("F", werte)[1].endswith("sein Median ist nur eine untere Schranke.")


def test_verdict_zerfall_gleichstand_bester_ist_der_kleinere_wert():
    werte = {0.5: kz(50), 0.8: kz(50), 0.95: kz(60), 0.99: kz(60), 1.0: kz(60)}
    assert "Bester Wert 0,5 (50)" in E.verdict_zerfall("F", werte)[1]


def test_verdict_zerfall_familien():
    kind, text = E.verdict_zerfall_familien({"Zufall": 0.95, "Rampen": 0.8})
    assert kind == "info" and "Zufall: 0,95; Rampen: 0,8" in text and "existiert in diesen Messungen nicht" in text
    assert "derselbe Wert" in E.verdict_zerfall_familien({"Zufall": 0.95, "Rampen": 0.95})[1]
    assert "mindestens zwei" in E.verdict_zerfall_familien({"Zufall": 0.95})[1]


def test_median_untere_schranke_ab_der_haelfte_der_abbrueche():
    assert not kz(5, abbrueche=0).median_untere_schranke
    assert not kz(5, abbrueche=5, n=12).median_untere_schranke and kz(5, abbrueche=6, n=12).median_untere_schranke       # 12 Läufe: ab 6
    assert not kz(5, abbrueche=9, n=20).median_untere_schranke and kz(5, abbrueche=10, n=20).median_untere_schranke     # 20 Läufe: ab 10
    assert not kz(5, abbrueche=2, n=5).median_untere_schranke and kz(5, abbrueche=3, n=5).median_untere_schranke         # ungerade: ab 3 von 5
    # Gegenprobe an Zahlen: 20 Läufe, 9 Abbrüche: die beiden mittleren Werte (10. und 11. kleinster) sind beendete Läufe
    laeufe = sorted([10] * 11 + [20000] * 9)
    assert laeufe[9] == laeufe[10] == 10
