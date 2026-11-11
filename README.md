# Variablenwahl nach Aktivität – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-variablenwahl-sat-demo.streamlit.app/)** -->

Demo der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie baut auf dem Konfliktlernen auf (die Frage: was eine feste Reihenfolge der Variablen kostet) und zeigt **eine Frage an einem wachsenden Beispiel**: Ein Löser, der aus Konflikten lernt, muss bei jeder Entscheidung eine Variable und einen Wert wählen. Wie viele Konflikte er braucht, hängt stark von dieser Wahl ab. Vehikel sind Zufalls-3-SAT als Wachstumsmaß, die Färbung eines Konfliktgraphen (Aufträge auf Rampen, Zeitfenster im Konflikt) und Schur-Partitionen an der Grenze der Lösbarkeit.

## Warum dieses Problem

Die Aktivität merkt sich, welche Variablen an den letzten Konflikten beteiligt waren, und entscheidet sie zuerst; alte Konflikte werden langsam vergessen. Eine feste Reihenfolge kennt die Formel nicht. Dazu wählt der **Phasenspeicher** den Wert, den die Variable zuletzt hatte. Die Demo zeigt die Wahl an einer Formel mit sieben Variablen Schritt für Schritt (Aktivitätsbalken, Begründung jeder Entscheidung, Vergleich mit der festen Reihenfolge) und misst in **Konflikten** (nie in Sekunden), was Wahl, Phasenspeicher und Zerfall ausmachen: **auf manchen Aufgaben viel, auf anderen kein klarer Unterschied, und auf dem Schubfach-Prinzip (h = 5 und 6, Nummerierung Taube für Taube) ist die Aktivität schlechter als die feste Reihenfolge.**

## Modell

- **Löser.** CDCL mit 1-UIP-Konfliktanalyse und Luby-Neustarts (Einheit 32), ohne Löschen gelernter Klauseln. Die Neustarts laufen in jeder Messung mit; ihr Einfluss ist nicht von der Wahl getrennt.
- **Aktivität (VSIDS-Variante wie in MiniSat).** Eine Aktivität je Variable. Bei jedem Konflikt erhält jede Variable der Herleitung (Konfliktklausel und aufgelöste Gründe, nur oberhalb von Stufe 0) den Zuwachs *g*; danach wird *g* durch den Zerfall δ geteilt. Entschieden wird die offene Variable mit der höchsten Aktivität, bei Gleichstand die kleinste Nummer. Übersteigt eine Aktivität 10^100, werden alle Aktivitäten und *g* mit 10^−100 multipliziert.
- **Feste Reihenfolge.** Die kleinste offene Variable (Nummer). Das ist die einfachste feste Regel, keine ausgeklügelte statische Heuristik.
- **Phasenspeicher.** Der Wert einer Entscheidung ist der zuletzt zurückgenommene Wert der Variablen (anfangs falsch); ausgeschaltet ist er immer falsch.
- **Aufwand.** Gezählt werden **Konflikte**. Ein Lauf, der das Konfliktbudget (20.000 in der Referenz) erreicht, gilt als Abbruch, zählt mit dem Budget und macht den Median zur unteren Schranke. Bei erreichtem Budget lautet die Antwort „unbekannt“, nicht „unerfüllbar“. Bei „unerfüllbar“ zählt die Konfliktzahl auch den letzten Konflikt auf Stufe 0, der nicht mehr analysiert wird.
- **Formelfamilien.** Zufalls-3-SAT mit 4,26 Klauseln je Variable, Rampen (3-Färbung eines Zufallsgraphen mit mittlerem Grad 4,5), Schur-Partitionen auf vier Mengen (n = 43, 44), alle über den ganzzahligen SplitMix64-Generator (unabhängig von Python-Version und Plattform; die CI rechnet billige Läufe der Referenz nach); Schubfach h = 5, 6 als Randbemerkung.
- Mathematik und Symboltabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL mit Aktivität, Phasenspeicher, Zerfall, Spur | `vsd_cdcl.py` | **wörtliche Kopie** des Kern-Moduls `cdcl.py` der Linie (Kern-Version 832b2c10dfdea62d); nur der Import ist auf `vsd_rng` umgestellt (`tests/test_kern_kopien.py`) |
| SplitMix64 | `vsd_rng.py` | Kopie des Kern-Moduls `rng.py` (5d5d8f45d0e1eddf); Regressionstest auf veröffentlichte Referenzwerte |
| Instanzerzeuger (Zufall, Schubfach, Schur, Färbung, Rampen) | `vsd_instanzen.py` | Kopie des Kern-Moduls `instanzen.py` (6795de796b66fff8) |
| Schalter des Lösers, Wahlregeln, Schritt-Aufbereitung der Spur | `vsd_algorithm.py` | eigene Einheiten: `optionen`, `loese`, `waehle_aktivitaet`, `waehle_fest`, `schritte` (eigener Buchstand über Belegung, gemerkte Phasen, Aktivitäten) |
| Handbeispiel F3, kleine Zufallsformeln, Läufe der Messreihen | `vsd_scenario.py` | je Aufgabe feste Formeln bzw. Zufalls-Seeds des Lösers |
| Messreihen, Kennzahlen, Verdikte | `vsd_evaluation.py` | Verdikte sind reine Funktionen; jede Zahl im Text stammt aus den Kennzahlen |
| Vorgerechnete Messreihen | `vsd_messungen.json` | geschrieben von `tools/messungen.py` (dieselben Funktionen wie die Live-Messreihen) |

Experimente in der App: **Eine Formel Schritt für Schritt** (Handbeispiel F3 oder eine kleine Zufallsformel mit 8 bis 12 Variablen), **Kernfrage** (Aktivität gegen feste Reihenfolge), **Hilft der Phasenspeicher?**, **Wie viel Gewicht haben alte Konflikte?** (Zerfall 0,5 / 0,8 / 0,95 / 0,99 / 1,0). Die großen Messreihen sind **vorgerechnet, nicht live**; je Experiment rechnet ein Knopf eine kleinere Messreihe derselben Familie live nach (Größe, Zahl der Läufe und Budget einstellbar, Zerfall 0,95).

## Befunde (gemessen, keine Behauptungen)

Die Zahlen dieser Tabelle stehen in `tests/test_claims.py` (Messung: `vsd_messungen.json`, Skript `tools/messungen.py`, Budget 20.000 Konflikte, Zerfall 0,95, Luby-Neustarts). Zufallsformeln: 12 feste Formeln (n = 100 mit 426, n = 150 mit 639 Klauseln), Rampen: 10 feste Konfliktgraphen (160 Aufträge, 3 Rampen), Schur: **eine** Instanz und 20 Zufalls-Seeds des Lösers. Median (Maximum) der Konflikte; Abbrüche zählen mit dem Budget.

| Frage | Befund |
|---|---|
| **Aktivität gegen feste Reihenfolge** | Zufalls-3-SAT n = 100: 257,5 (607) gegen 1.319 (2.195), kein Abbruch, Faktor 5,1. Zufalls-3-SAT n = 150: Aktivität 2.888 (5.949), kein Abbruch; die feste Reihenfolge erreicht das Budget bei **8 von 12** Formeln (Median 20.000, untere Schranke; Faktor mindestens 6,9). Rampen n = 160: 118,5 (337) gegen 1.161,5 (4.491), Faktor 9,8 (`test_claim_aktivitaet_gegen_feste_reihenfolge`). Die vier Formeln, die die feste Reihenfolge entscheidet, brauchen 3.461 / 7.104 / 19.227 / 19.647 Konflikte; die Aktivität entscheidet bei n = 150 neun der zwölf Formeln als unerfüllbar und drei als erfüllbar (`test_claim_entschiedene_laeufe_der_festen_reihenfolge_bei_zufall_150`). |
| **Länge gelernter Klauseln** | Mittlere Länge (Literale), feste Reihenfolge gegen Aktivität: Zufall n = 100 10,1 gegen 8,2; n = 150 16,4 gegen 11,4; Rampen 18,9 gegen 11,9 (`test_claim_laenge_der_gelernten_klauseln`). Das gilt für die gemessenen Läufe, nicht bei gleicher Konfliktzahl: die feste Reihenfolge braucht dabei viel mehr Konflikte (bei Zufall n = 150 bricht sie bei 8 von 12 Formeln am Budget ab), und mit der Lauflänge wachsen die Klauseln. |
| **Phasenspeicher** | Mit gegen ohne, Median (Maximum): Zufall n = 150 2.888 (5.949) gegen 2.618 (5.493), Rampen 118,5 (337) gegen 126 (402): jeweils unter dem Faktor 1,5, **kein klarer Unterschied**; in drei von vier Formelmengen (diese und die Gegenprobe unten) liegt der Median ohne Phasenspeicher niedriger. Schur n = 43 (20 Zufalls-Seeds): 255 (5.306) gegen 564,5 (2.356), Faktor 2,2 beim Median, **das Maximum ist mit Phasenspeicher größer**. Schur n = 44: 3.307 (3 von 20 Abbrüchen) gegen 19.031,5 (**9** von 20 Abbrüchen), Faktor 5,8 (`test_claim_phasenspeicher`); beide Mediane sind exakt, weil weniger als die Hälfte der 20 Läufe abbricht, nur die Maxima (20.000) sind untere Schranken. |
| **Zerfall** | Median bei Zerfall 0,5 / 0,8 / 0,95 / 0,99 / 1,0: Zufall n = 150 6.023,5 / 4.273 / 2.888 / 2.772 / 3.566 (bester Wert 0,99, schlechtester 0,5, Faktor 2,2; **0,5 und 0,8** liegen um den Faktor 1,5 oder mehr über dem besten); Rampen n = 160 200,5 / 75,5 / 118,5 / 143 / 113 (bester Wert 0,8, schlechtester 0,5, Faktor 2,7; 0,5, 0,95 und 0,99 liegen um den Faktor 1,5 oder mehr über dem besten). Kein Abbruch. In diesen Referenzmengen ist der beste Wert in beiden Familien verschieden und 0,5 jeweils der schlechteste (`test_claim_zerfall`); die Gegenprobe (unten) bestätigt das für 0,5 nur bei den Rampen. |
| **Schubfach (Randbemerkung)** | h = 5 / 6 (unerfüllbar, eine Instanz, ein Lauf je Verfahren): Aktivität 159 / 1.004 Konflikte, feste Reihenfolge 50 / 130, also bei h = 6 das 7,7-Fache für die Aktivität (`test_claim_schubfach_umgekehrt_zur_kernfrage`). |
| **Handbeispiel F3** | Sieben Variablen, 14 Klauseln, Zerfall 0,5: drei Konflikte, gelernte Klauseln (x5 ∨ x2 ∨ x1), (x2 ∨ x1), (¬x3 ∨ x7 ∨ ¬x5), Sprünge auf Stufe 2, 1, 3; Aktivitäten nach dem dritten Konflikt 3 / 3 / 6 / 5 / 7 / 2 / 7 für x1 … x7; die Entscheidungen x5, ¬x7 und x3 nach dem zweiten Konflikt, von denen die ersten beiden von der festen Reihenfolge abweichen (`tests/test_algorithm.py`, von Hand nachgerechnet). |

### Stabilität (Gegenprobe, nicht Teil der Tests)

Die Gegenprobe mit **anderen festen Formelmengen** (Skript `tools/gegenprobe.py`: Zufall n = 150 mit den Seeds 3000 bis 3011, Rampen n = 160 mit den Seeds 700 bis 709; sonst gleiche Verfahren und Budget) ergab, jeweils Median (Maximum, Abbrüche):

| Frage | Zufall n = 150 (andere 12 Formeln) | Rampen n = 160 (andere 10 Graphen) |
|---|---|---|
| Aktivität | 2.410,5 (5.180, 0) | 165 (653, 0) |
| feste Reihenfolge | 20.000 (20.000, **9** von 12) | 3.788 (20.000, 1 von 10) |
| Aktivität ohne Phasenspeicher | 1.873,5 (4.608, 0) | 141,5 (691, 0) |
| Zerfall 0,5 / 0,8 / 0,95 / 0,99 / 1,0 | 3.345 / 2.456 / 2.410,5 / 2.900,5 / 4.672,5 | 170 / 114,5 / 165 / 110 / 127,5 |

Die **Richtung und Größenordnung der Kernfrage** reproduzieren sich (feste Reihenfolge: 9 statt 8 von 12 Abbrüchen bei Zufall, Faktor 23 statt 9,8 bei Rampen). Beim **Phasenspeicher** bleibt es bei „kein klarer Unterschied“ (Faktor 1,29 und 1,17, in beiden Mengen ohne Phasenspeicher etwas besser; in der Referenzmenge war es bei den Rampen umgekehrt, Faktor 1,06). Der **beste Zerfall hängt von der Formelmenge ab**: Zufall 0,95 statt 0,99, Rampen 0,99 statt 0,8; der schlechteste ist bei Zufall 1,0 statt 0,5 (nur bei den Rampen weiter 0,5), der Faktor zwischen bestem und schlechtestem Wert 1,9 statt 2,2 bzw. 1,5 statt 2,7. Aus den Zerfall-Messungen folgt also nur, dass der Wert eine Rolle spielt, nicht welcher der beste ist.

## Ehrliche Grenzen

- **Wenige Formeln.** Je Familie 12 bzw. 10 feste Formeln, bei Schur eine Instanz; die Mediane streuen von Formelmenge zu Formelmenge (siehe Stabilität). Vor allem der **beste Zerfall** ist eine Messung je Formelmenge und kein Wert.
- **Die feste Reihenfolge ist die Nummer der Variablen**, und die Nummerierung hängt von der Kodierung ab: Beim Schubfach (Taube für Taube) schlägt sie die Aktivität, bei den Rampen (Auftrag für Auftrag) verliert sie in der Referenz um den Faktor 9,8. Der Vorsprung der festen Reihenfolge am Schubfach hängt an der Nummerierung Taube für Taube: Mit zufällig umnummerierten Variablen schrumpft er (Nachprüfung, nicht Teil der Tests, 6 Umnummerierungen je h; h = 6: 580 bis 695 gegen 130 Konflikte, Aktivität 740 bis 1.166). Der Rückstand der festen Reihenfolge bei den Rampen bleibt bei zufälliger Nummerierung bestehen (10 Graphen, je eine Umnummerierung: Median fest 1.090, Aktivität 92,5). Der Vergleich sagt nichts über statische Regeln wie Jeroslow–Wang und nichts über andere Kodierungen derselben Aufgabe.
- **Der Phasenspeicher ist keine allgemeine Empfehlung.** Gemessen sind Zufallsformeln, Färbung und eine Schur-Instanz an der Grenze der Lösbarkeit (k = 4, n = 43 und 44); für andere k, andere Instanzen oder Löser mit anderen Neustarts sagt die Demo nichts.
- **Median mischt erfüllbare und unerfüllbare Formeln**, deren Anteil schwankt (Zufall n = 150: 3 erfüllbar und 9 unerfüllbar nach Aktivität).
- **Abbrüche sind untere Schranken.** Ein Median ist exakt, solange weniger als die Hälfte der Läufe abbricht; sonst ist er nur eine untere Schranke: das gilt für die feste Reihenfolge bei Zufall n = 150 (8 von 12), dort ist der Faktor „mindestens“; bei Schur n = 44 liegen die Mediane trotz 3 bzw. 9 Abbrüchen fest, die Maxima nicht.
- **Konflikte sind keine Laufzeit.** Die Verwaltung der Aktivitäten (Halde, Zuwächse) kostet selbst Zeit; sie ist nicht gemessen.
- **Die Variante ist die aus MiniSat**, nicht das Chaff-Original (dort ein Zähler je Variable und Polarität, periodisch geteilt); die MiniSat-Quelle ist nicht gelesen, deshalb ohne Zitat. Moderne Löser mischen mehrere Heuristiken (stabiler und fokussierter Modus); davon zeigt die Demo nichts.
- **Python-CDCL, lesbar statt schnell.** Live laufen nur kleine Messreihen (Zufall bis n = 110, Rampen bis n = 140, Schur bis n = 44 mit wenigen Zufalls-Seeds); die Referenz ist vorgerechnet.
- **Deutungen sind als solche gekennzeichnet.** Die Demo misst, ob die Wahl etwas ausmacht, nicht warum.

## Befunde und Korrekturen gegenüber dem Plan

- **Neue Formeln, neue Zahlen.** Der Plan nennt Werte der Vormessung mit Python-`random`; die Demo misst mit SplitMix64 neu. Zufall n = 150: Aktivität 2.888 statt 1.853, feste Reihenfolge Abbruch bei 8 statt 7 von 12; Rampen 118,5 gegen 1.161,5 statt 91,5 gegen 1.025,5; Schur n = 43: 255 gegen 564,5 statt 544,5 gegen 908, n = 44: 3.307 (3 Abbrüche) gegen 19.031,5 (9 Abbrüche) statt 6.313,5 (2) gegen 19.879 (10). Die Aussagen der Kernbotschaft (Aktivität gegen feste Reihenfolge, Phasenspeicher hilft auf Schur) haben sich reproduziert, die Zahlen des Plans gelten als überholt.
- **Phasenspeicher auf Zufall und Färbung.** Im Plan „ohne Phasenspeicher etwas besser (1.436 gegen 1.853; 67 gegen 91,5)“; hier 2.618 gegen 2.888 und 126 gegen 118,5, also in der Rampen-Messung mit Phasenspeicher etwas besser. Beide Unterschiede liegen unter dem Faktor 1,5; die App sagt „kein klarer Unterschied“.
- **Zerfall: „schwacher Einfluss“ nicht übernommen.** Der Plan nennt den Einfluss schwach und nur 0,5 deutlich schlechter. Hier liegt der Faktor zwischen bestem und schlechtestem Wert bei 2,2 (Zufall) bzw. 2,7 (Rampen); 0,5 ist in beiden Referenzmengen der schlechteste (in der Gegenprobe nur bei den Rampen), auf Zufall liegt in der Referenz auch 0,8 um mehr als den Faktor 1,5 über dem besten. Das Verdikt zählt statt zu bewerten (Faktor 1,5 als Schwelle für „deutlich“).
- **Schubfach: „keine Wahlregel hilft“ gilt in der Nummerierung Taube für Taube nicht.** Dort braucht die feste Reihenfolge deutlich weniger Konflikte als die Aktivität (h = 5: 50 gegen 159, h = 6: 130 gegen 1.004); mit zufällig umnummerierten Variablen schrumpft der Abstand (Nachprüfung, nicht Teil der Tests). Die Randbemerkung der App nennt das.
- **Handbeispiel F3, Endmodell.** Konflikte, gelernte Klauseln, Sprünge, Aktivitäten und die ersten sechs Entscheidungen stimmen mit der Handrechnung des Plans überein. Das Endmodell weicht in x6 ab: im Plan x6 = wahr (dort belegt die Propagation x6 auf Stufe 4), im Löser x6 = falsch, weil dessen Propagation (zwei beobachtete Literale) den dritten Konflikt findet, bevor x6 auf Stufe 4 belegt wird; der zuletzt zurückgenommene Wert von x6 ist dann falsch. Beide Modelle erfüllen die Formel (`test_f3_modell_erfuellt_alle_klauseln`).
- **Messdesign.** Bei den Formelfamilien (Zufall, Rampen) gibt es je feste Formel einen Lauf ohne Zufall im Löser, bei Schur 20 Zufalls-Seeds des Lösers (zufälliger Start der Aktivitäten), so wie die Ergebnistabelle des Plans es misst; der Plan-Text für das Phasenspeicher-Experiment nennt 20 Zufalls-Seeds für alle Familien.
- **Zerfall als Messreihe, nicht als Regler.** Das Experiment zeigt alle fünf Werte nebeneinander; der Regler „Zerfall“ der Seitenleiste wirkt nur auf die Schritt-für-Schritt-Ansicht.
- **Grad der Rampen fest.** Der mittlere Grad des Konfliktgraphen ist 4,5 (Referenz und Live); regelbar ist nur die Größe.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung (`tests/test_algorithm.py`): Handbeispiel F3 mit Brüchen (Konflikte, gelernte Klauseln, Sprungstufen, Aktivitäten nach jedem Konflikt, Entscheidungsfolge, Äquivalenz „Aktivität durch Zuwachs = abgezinste Summe“ von Hand: x5 mit 7/8), Wahlregeln, Gleichstand, Phasenspeicher, Schritt-Aufbereitung. Die kopierten Kern-Module: Regression und Einheiten (`tests/test_kern_kopien.py`).
- **Orakel** (`tests/test_oracle_variablenwahl_sat.py`): Erfüllbarkeit gegen OR-Tools CP-SAT auf 40 Zufallsformeln in allen vier Varianten (Wahl × Phasenspeicher) und auf Schur n = 13 / 14 (k = 3) bei drei Zerfallswerten; Modelle mit eigener Prüfung; **die Spur wird mit eigenem Code und exakten Brüchen nachgerechnet** (1-UIP-Herleitung, Aktivitäten, gemerkte Phasen, jede Entscheidung gegen „höchste Aktivität, kleinste Nummer“) auf zwölf Zufallsformeln bei Zerfall 1/2, bei Zerfall 0,8 bis 1,0 mit Toleranz, auf Schubfach h = 5 und Schur n = 14 mit Neustarts; Eigenschaften: Neuskalierung ändert die Rangfolge nicht, Antwort unabhängig von der Wahlregel, Umbenennen der Variablen ändert die Antwort nie.
- **Randfälle** (`tests/test_edge_cases.py`): alle Aktivitäten 0, ein einziger Konflikt, Zerfall 1,0, Zerfallsgrenze 0,5 (darunter abgelehnt), Budget erreicht, Zufalls-Seed des Lösers, leere Spur; der Nachvollzug fällt bei einer absichtlich verfälschten Entscheidung auf.
- **Zweige** (`tests/test_zweige.py`): jede Variante der Referenz weicht von jeder anderen ab und ist keine Nullspalte.
- **Verdikte** als reine Funktionen, jede Schwelle (Faktor 1,5 inklusive) und jede Zahl im Text an handgesetzten Kennzahlen (`tests/test_verdicts.py`); **Claims:** die Zahlen der Tabelle „Befunde“ (`tests/test_claims.py`), dazu eine Neumessung billiger Läufe gegen die JSON-Datei. Nicht in den Tests stehen die Zahlen der Gegenprobe (Skript `tools/gegenprobe.py`) und die zitierten Werte des Plans.
- **Schnellstart-Szenarien (Presets) und Layout:** vollständig, erlaubte Werte, Standard-Preset gleich Standardeinstellung; Schnellstart in der Seitenleiste, jede Änderung eines Reglers hebt die Hervorhebung auf (`tests/test_presets.py`, `tests/test_layout.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der drei Live-Messreihen, jeder Slider am Minimum und Maximum, `tests/test_app.py`) und Inhaltsprüfungen (jede Aufgabe, jeder Schalter, Permalink, `tests/test_app_inhalt.py`), Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Schritt-für-Schritt-Ansicht, Kernfrage, Experimente, Grenzen, Mathematik |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur als Gegenprobe in den Tests) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/messungen.py` | Messskript der vorgerechneten Messreihen |
| `vsd_algorithm.py` | Schalter des Lösers, Wahlregeln, Schritt-Aufbereitung |
| `vsd_cdcl.py`, `vsd_instanzen.py`, `vsd_rng.py` | wörtliche Kopien der Kern-Module (Herkunft und Kern-Version im Kopf) |
| `vsd_constants.py` | Aufgaben, Regler-Grenzen, Farben, Presets |
| `vsd_evaluation.py` | Messreihen, Kennzahlen, Verdikte |
| `vsd_layout.py` | Fester Kopf (Stylesheet) |
| `vsd_messungen.json` | vorgerechnete Messreihen (Konflikte je Lauf) |
| `vsd_presets.py` | Permalink (Einrasten), Presets, Zufalls-Seed-Button |
| `vsd_scenario.py` | Handbeispiel F3, kleine Zufallsformeln, Läufe der Aufgaben |
| `vsd_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Zweige, Verdikte, Claims, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Neustarts und Löschen gelernter Klauseln:** eigene Demos der Linie; hier laufen die Neustarts mit und das Löschen ist aus. Ein Schalter „Neustarts aus“ fehlt, damit die Aufgaben der Referenz nur eine Variable ändern.
- **Klausel-Minimierung:** in der Vormessung gemessen, in der Demo nicht gezeigt.
- **Andere Heuristiken** (VMTF, stabiler und fokussierter Modus, Jeroslow–Wang im CDCL): nicht gemessen, nicht gezeigt.
- **Zeitmessung:** nur Konflikte.
- **PDF-Export:** nicht nötig, die Messreihen stehen in `vsd_messungen.json`.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Die vorgerechneten Messreihen neu schreiben: `python tools/messungen.py --alle` (mehrere Minuten).

## Einordnung und Quellen

- Die Aktivität im Original (ein Zähler je Variable und Polarität, bei jeder neu hinzugefügten Klausel erhöht, periodisch geteilt, Gleichstand zufällig): Moskewicz, Madigan, Zhao, Zhang, Malik, Chaff, DAC 2001 (Volltext gelesen). Die hier gezeigte Variante (Aktivität je Variable, erhöht für alle an der Konfliktanalyse beteiligten Variablen, Zerfall über einen wachsenden Zuwachs) ist die von MiniSat; diese Quelle ist nicht gelesen. Die Konfliktanalyse: Marques-Silva und Sakallah, GRASP, IEEE Transactions on Computers 1999 (gelesen). Die Herkunft des Phasenspeichers ist hier nicht belegt.
- Verzweigungsregeln im DPLL (erste, häufigste Variable, Jeroslow–Wang): [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo).

Gebaut mit Streamlit, Pandas und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
