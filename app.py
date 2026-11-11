"""Variablenwahl nach Aktivität - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein CDCL-Löser entscheidet bei jedem Schritt, welche Variable er als nächste belegt und mit welchem Wert. Die Demo zeigt an einer
kleinen Formel Schritt für Schritt, wie die Aktivität (VSIDS-Variante wie in MiniSat) die Wahl bestimmt, und misst in Konflikten, was
diese Wahl, der Phasenspeicher und der Zerfall der Aktivität ausmachen. Die großen Messreihen sind vorgerechnet (nicht live).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import vsd_algorithm as A
import vsd_constants as C
import vsd_evaluation as E
import vsd_presets as P
import vsd_scenario as S
import vsd_visualization as V
from vsd_layout import dunkles_design, kopf_css
from vsd_presets import (
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Variablenwahl nach Aktivität – Sebastian Hanisch", layout="wide")

WAHL_LABELS = {"Aktivität": A.WAHL_AKTIVITAET, "Feste Reihenfolge": A.WAHL_FEST}
SCHRITT_BUDGET = 500          # Konflikte, die die Schritt-für-Schritt-Ansicht höchstens zulässt (die Formeln sind klein)


@st.cache_data(show_spinner=False)
def _schrittlauf(formel, klein_n, klein_seed, wahl, phase, zerfall):
    inst = S.hand_formel() if formel == P.FORMEL_HAND else S.kleine_formel(klein_n, klein_seed)
    res = A.loese(inst, wahl, phase, zerfall, budget=SCHRITT_BUDGET, trace=True)
    folge = A.schritte(res.spur, inst.n, zerfall, phasenspeicher=phase, vsids=(wahl == A.WAHL_AKTIVITAET))
    return {"n": inst.n, "klauseln": [tuple(k) for k in inst.klauseln], "antwort": res.antwort, "modell": res.modell,
            "stat": res.stat, "schritte": folge, "gekuerzt": res.spur_gekuerzt}


@st.cache_data(show_spinner=False)
def _live(art, groesse, anzahl, budget, verfahren):
    return E.messe_live(art, groesse, anzahl, budget, list(verfahren))


def _klausel_zeile(i, k):
    return f"K{i + 1} {A.klausel_text(k)}"


# --- Kopf, Einleitung ----------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Variablenwahl nach Aktivität")
st.markdown(
    """
Ein Löser, der aus Konflikten lernt, muss bei jeder Entscheidung eine **Variable** und einen **Wert** wählen. Eine **feste Reihenfolge** kennt die
Formel nicht; die **Aktivität** merkt sich, welche Variablen an den letzten Konflikten beteiligt waren, und vergisst alte Konflikte langsam.
Der **Phasenspeicher** wählt dazu den Wert, den die Variable zuletzt hatte. Die Demo zeigt die Wahl an einer kleinen Formel Schritt für Schritt
und misst in **Konflikten** (nie in Sekunden), was Wahl, Phasenspeicher und Zerfall ausmachen: auf manchen Aufgaben viel, auf anderen kein klarer Unterschied.

Weiter unten: die **Kernfrage**, zwei Experimente (**Phasenspeicher**, **Zerfall**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Variablenwahl nach Aktivität", expanded=True):
    st.markdown(
        """
1. **Beteiligte zählen.** Bei jedem Konflikt erhält jede Variable, die in der Herleitung der gelernten Klausel vorkommt (Konfliktklausel und aufgelöste
   Gründe, nur oberhalb von Stufe 0), den aktuellen **Zuwachs** auf ihre Aktivität.
2. **Alte Konflikte verblassen.** Nach jedem Konflikt wird der Zuwachs durch den **Zerfall** geteilt (Zerfall 0,95: der Zuwachs wächst um den Faktor 1/0,95).
   So zählen neuere Konflikte mehr, ohne dass alle Aktivitäten umgerechnet werden müssen; Aktivität geteilt durch den Zuwachs ist die mit dem Zerfall abgezinste Summe.
3. **Wählen.** Entschieden wird die offene Variable mit der **höchsten Aktivität**, bei Gleichstand die mit der kleinsten Nummer. Der Wert ist der **gespeicherte**
   (zuletzt zurückgenommene, anfangs falsch), mit abgeschaltetem Phasenspeicher immer falsch.
4. **Die Vergleichsregel:** die **feste Reihenfolge** wählt immer die kleinste offene Variable. Sie ist hier die einfachste feste Regel, keine ausgeklügelte statische Heuristik.

Die Variante ist die aus MiniSat (eine Aktivität je Variable, Zuwachs mit Zerfall); das Chaff-Original zählt je Variable und Polarität und teilt die Zähler periodisch.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Messreihen**")
    aufgabe_label = st.selectbox("Aufgabe", C.AUFGABEN_LABELS, key="aufgabe",
                                 help="Familie der Messreihen unter der Kernfrage und in den Experimenten (vorgerechnet; die Live-Messreihen nutzen dieselbe Familie in kleinerer Größe).")
    st.markdown("**Schritt für Schritt**")
    formel = st.selectbox("Formel", P.FORMELN, key="formel",
                          help="Handbeispiel F3: sieben Variablen, 14 Klauseln, von Hand nachrechenbar. Oder eine kleine Zufallsformel (8 bis 12 Variablen) mit eigenem Zufalls-Seed.")
    zerfall = st.select_slider("Zerfall der Aktivität", C.ZERFAELLE, key="zerfall", format_func=E.zerfall_text,
                               help="Wirkt nur auf die Schritt-für-Schritt-Ansicht. Die Messreihen stehen auf 0,95 (Kernfrage, Phasenspeicher) bzw. zeigen alle fünf Werte (Zerfall). "
                                    "Kleinere Werte als 0,5 lässt die Demo nicht zu: gegen 0 zählt nur noch der letzte Konflikt.")

sync_query_params({"aufgabe": aufgabe_label, "formel": formel, "zerfall": zerfall})
aufgabe = C.SCHLUESSEL_VON_LABEL[aufgabe_label]
art = C.AUFGABEN[aufgabe]["art"]

# --- Primäransicht: eine Formel Schritt für Schritt ---------------------------------------------------------------------------------------------

st.markdown("## 🎯 Eine Formel Schritt für Schritt")
c_wahl, c_phase = st.columns([2, 1])
wahl_label = c_wahl.radio("Wahl der nächsten Variablen", list(WAHL_LABELS), horizontal=True, key="wahl_radio",
                          help="Aktivität: höchste Aktivität unter den offenen Variablen. Feste Reihenfolge: kleinste offene Variable.")
phase = c_phase.toggle("Phasenspeicher", value=True, key="phase_toggle",
                       help="An: der Wert, den die Variable zuletzt hatte (anfangs falsch). Aus: immer falsch.")
wahl = WAHL_LABELS[wahl_label]

if formel == P.FORMEL_KLEIN:
    c1, c2, c3 = st.columns([1, 1, 1])
    klein_n = c1.slider("Variablen n", *C.KLEIN_N, value=C.DEFAULT_KLEIN_N, key="klein_n",
                        help=f"Zufalls-3-SAT mit {C.VERHAELTNIS} Klauseln je Variable, gerundet (n = 12: {S.klauselzahl(12)} Klauseln).")
    klein_seed = c2.number_input("Zufalls-Seed der Formel", 0, C.SEED_MAX, value=C.DEFAULT_KLEIN_SEED, step=1, key="klein_seed")
    c3.write("")
    c3.button("🎲 Neue Formel", on_click=randomize_seed, width="stretch")
    klein_n, klein_seed = int(klein_n), int(klein_seed)
else:
    klein_n, klein_seed = C.DEFAULT_KLEIN_N, C.DEFAULT_KLEIN_SEED

lauf = _schrittlauf(formel, klein_n, klein_seed, wahl, phase, float(zerfall))
folge = lauf["schritte"]
signatur = (formel, klein_n, klein_seed, wahl, phase, float(zerfall))
if st.session_state.get("schritt_signatur") != signatur or not (1 <= st.session_state.get("schritt", 0) <= len(folge)):
    # beim Wechsel der Formel oder der Schalter: auf den ersten Schritt nach dem ersten gelernten Konflikt springen
    erster = next((s.nr for s in folge if s.art == "springe"), len(folge))
    st.session_state["schritt"] = min(max(erster, 1), len(folge))
    st.session_state["schritt_signatur"] = signatur

abweichungen = sum(1 for d in (folge[-1].entscheidungen if folge else []) if d["abweichung"])
m1, m2, m3, m4 = st.columns([3, 2, 2, 2])
m1.metric("Antwort", {True: "erfüllbar", False: "unerfüllbar", None: "Budget erreicht"}[lauf["antwort"]])
m2.metric("Konflikte", lauf["stat"]["konflikte"])
m3.metric("Entscheidungen", lauf["stat"]["entscheidungen"])
m4.metric("Abweichungen", abweichungen if wahl == A.WAHL_AKTIVITAET else "–",
          help="Entscheidungen, bei denen die Aktivität eine andere Variable gewählt hat als die feste Reihenfolge (die kleinste offene Variable).")
if lauf["gekuerzt"]:
    st.warning("Die Spur ist auf 5.000 Ereignisse begrenzt; der Rest der Suche wird hier nicht gezeigt.")
if float(zerfall) != C.DEFAULT_ZERFALL:
    st.caption(f"Der Zerfall steht hier auf {E.zerfall_text(float(zerfall))}; die Voreinstellung der Messreihen ist {E.zerfall_text(C.DEFAULT_ZERFALL)}.")

if folge:
    nr = st.slider("Schritt", 1, len(folge), key="schritt",
                   help="Ein Schritt je Ereignis des Lösers: Entscheidung, erzwungener Schluss, Konflikt, Beteiligte, gelernte Klausel, Rücksprung.")
    s = folge[nr - 1]
    st.info(f"**Schritt {s.nr} von {len(folge)}.** {s.text}")
    belegt = {abs(l) for l, _, _ in s.belegung}
    links, rechts = st.columns([5, 6])
    with links:
        titel = f"Aktivität nach {s.konflikte} Konflikt{'en' if s.konflikte != 1 else ''}" if wahl == A.WAHL_AKTIVITAET else "Aktivität (nicht benutzt)"
        st.plotly_chart(V.build_aktivitaet(s.aktivitaet, belegt, s.hervorgehoben, titel), width="stretch", key="chart_aktivitaet")
        zuwachs = f" Der nächste Konflikt vergibt den Zuwachs {A.zahl_text(s.zuwachs)}." if wahl == A.WAHL_AKTIVITAET else ""
        st.caption("Absteigend nach Aktivität, bei Gleichstand die kleinere Nummer zuerst. Grau: belegt; rot: die gerade entschiedene Variable; "
                   "gelb: an diesem Konflikt beteiligt." + zuwachs)
    with rechts:
        st.markdown("**Entscheidungen bis hier** (mit Begründung und dem Vergleich mit der festen Reihenfolge)")
        if s.entscheidungen:
            zeilen = []
            for d in s.entscheidungen:
                fest = "–" if d["fest_variable"] is None else A.literal_text(d["fest_lit"])
                zeilen.append({"Nr": d["nr"], "Stufe": d["stufe"], "Entscheidung": A.literal_text(d["lit"]),
                               "Begründung": f"{d['grund']}; {d['wert']}", "Feste Reihenfolge hätte": fest,
                               "Vergleich": "🔴 andere Variable" if (d["abweichung"] and wahl == A.WAHL_AKTIVITAET) else "gleich"})
            st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")
        else:
            st.caption("Noch keine Entscheidung.")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**Belegung** (Stufe: Literal, Grund)")
        if s.belegung:
            je_stufe: dict[int, list[str]] = {}
            for lit, stufe, grund in s.belegung:
                je_stufe.setdefault(stufe, []).append(A.literal_text(lit) + (f" ({grund})" if grund else " (Entscheidung)" if stufe > 0 else ""))
            st.markdown("  \n".join(f"Stufe {st_}: " + ", ".join(v) for st_, v in sorted(je_stufe.items())))
        else:
            st.caption("Nichts belegt.")
    with b2:
        st.markdown("**Gelernte Klauseln und Sprünge** (Zusammenfassung)")
        if s.gelernt:
            st.markdown("  \n".join(f"{A.klausel_text(k)}, Sprung auf Stufe {r}" for k, r in s.gelernt))
        else:
            st.caption("Noch nichts gelernt.")
    with st.expander("Die Klauseln der Formel"):
        st.markdown("  \n".join(_klausel_zeile(i, k) for i, k in enumerate(lauf["klauseln"])))
    if lauf["antwort"] is True and nr == len(folge) and lauf["modell"]:
        st.success("Modell: " + ", ".join(f"x{v} = {'wahr' if b else 'falsch'}" for v, b in sorted(lauf["modell"].items())))
else:
    st.info("Diese Formel wird ohne Entscheidung gelöst; es gibt nichts zu zeigen.")

st.markdown("---")

# --- Messreihen: Darstellung ---------------------------------------------------------------------------------------------------------------


def _tabelle(kennz: dict, beschriftung: dict) -> pd.DataFrame:
    zeilen = []
    for name, k in kennz.items():
        zeilen.append({"Verfahren": beschriftung[name], "Läufe": k.n, "Median": E.zahl(k.median), "Maximum": E.zahl(k.maximum),
                       "Abbrüche am Budget": k.abbrueche,
                       "mittlere Länge gelernter Klauseln": "–" if k.laenge is None else f"{k.laenge:.1f}".replace(".", ",")})
    return pd.DataFrame(zeilen)


def _zeige(exp: str, kennz: dict, roh: dict, budget: int, beschriftung: dict, farben: dict, titel: str, verdikt, kopfnote: str):
    st.caption(kopfnote)
    kind, text = verdikt
    getattr(st, kind)(text)
    st.plotly_chart(V.build_streifen(roh, budget, beschriftung, farben, titel), width="stretch", key=f"streifen_{exp}")
    st.dataframe(_tabelle(kennz, beschriftung), hide_index=True, width="stretch")


def _live_panel(exp: str, verfahren: list[str], beschriftung: dict, farben: dict, verdikt_fn, titel: str):
    """Kleinere Messreihe live: Größe, Zahl der Läufe und Budget einstellbar, Ergebnis wie die Referenz."""
    lo, hi, vor, schritt = C.LIVE_GROESSE[art]
    with st.expander("🔁 Live nachrechnen (kleiner als die Referenz)"):
        st.caption("Dieselben Verfahren in kleinerer Größe: die ersten festen Formeln bzw. Zufalls-Seeds des Lösers der Referenz, Zerfall 0,95 (im Experiment Zerfall alle fünf Werte). "
                   "Abbrüche am (kleineren) Budget zählen mit dem Budget. Mit wenigen Läufen streuen die Mediane stark: die Richtung des Verdikts ist dann unsicher.")
        c1, c2, c3 = st.columns(3)
        groesse = c1.slider("Größe n" if art != "schur" else "Zahlen n (Schur)", lo, hi, vor, step=schritt, key=f"live_groesse_{exp}_{art}")
        anzahl = c2.slider("Zahl der Formeln" if art != "schur" else "Zahl der Zufalls-Seeds des Lösers", *C.LIVE_ANZAHL[:2], value=C.LIVE_ANZAHL[2],
                           key=f"live_anzahl_{exp}_{art}")
        budget = c3.slider("Budget (Konflikte)", *C.BUDGET_LIVE, value=C.DEFAULT_BUDGET_LIVE, step=500, key=f"live_budget_{exp}")
        signatur = (art, groesse, anzahl, budget)
        if st.button("Messreihe live starten", key=f"live_go_{exp}", help="Je nach Größe und Budget bis zu etwa einer Minute."):
            with st.spinner("Die Messreihe läuft (bis zu etwa einer Minute) …"):
                st.session_state[f"live_{exp}"] = {"sig": signatur, "daten": _live(art, groesse, anzahl, budget, tuple(verfahren))}
        gespeichert = st.session_state.get(f"live_{exp}")
        if gespeichert and gespeichert["sig"] == signatur:
            d = gespeichert["daten"]
            kennz = {v: E.kennzahlen(d["verfahren"][v]) for v in verfahren}
            roh = {v: d["verfahren"][v] for v in verfahren}
            label = E.live_label(art, groesse)
            _zeige(f"{exp}_live", kennz, roh, budget, beschriftung, farben, f"{titel} (live)", verdikt_fn(label, kennz, budget),
                   f"Live gemessen, nicht vorgerechnet: {d['anzahl']} {'Läufe (Zufalls-Seeds des Lösers)' if art == 'schur' else 'feste Formeln'}, "
                   f"Budget {E.zahl(budget)} Konflikte, Zerfall 0,95, Neustarts Luby.")
        elif gespeichert:
            st.caption("Die Einstellungen haben sich geändert: Messreihe erneut starten.")


def _nicht_gemessen(frage: str, zellen: tuple):
    namen = ", ".join(C.AUFGABEN[z]["label"] for z in zellen)
    st.info(f"Für diese Aufgabe ist {frage} nicht vorgerechnet. Vorgerechnet sind: {namen}. Eine kleinere Live-Messreihe der gewählten Familie steht darunter zur Verfügung.")


def _fehlt_datei():
    st.warning("Die vorgerechneten Messreihen (vsd_messungen.json) fehlen; nur die Live-Messreihen stehen zur Verfügung.")


def _roh_kopf(z) -> str:
    wo = "Läufe (Zufalls-Seeds des Lösers, eine Instanz)" if z["art"] == "schur" else "feste Formeln"
    return (f"Vorgerechnet, nicht live (Messskript tools/messungen.py, Datei vsd_messungen.json): {z['n']} {wo}, Budget {E.zahl(z['budget'])} Konflikte, "
            f"Neustarts Luby. Aufgabe: {z['label']}.")


# --- Kernfrage: Aktivität gegen feste Reihenfolge -------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Konflikte braucht eine feste Reihenfolge, wie viele die Aktivität?")
farben_ae = {"aktivitaet": C.COLOR_AKTIV, "fest": C.COLOR_FEST}
ref = E.referenz_zelle(aufgabe, ["aktivitaet", "fest"]) if aufgabe in C.ZELLEN_AKTIVITAET else None
if not E.lade_messungen().get("zellen"):
    _fehlt_datei()
elif ref is None:
    _nicht_gemessen("diese Frage", C.ZELLEN_AKTIVITAET)
else:
    k = ref["kennzahlen"]
    _zeige("aktivitaet", k, ref["roh"], ref["budget"], E.VERFAHREN_LABEL, farben_ae, f"Konflikte je Lauf: {ref['label']}",
           E.verdict_aktivitaet(ref["label"], k["aktivitaet"], k["fest"], ref["budget"]), _roh_kopf(ref))
_live_panel("aktivitaet", ["aktivitaet", "fest"], E.VERFAHREN_LABEL, farben_ae,
            lambda label, kz, budget: E.verdict_aktivitaet(label, kz["aktivitaet"], kz["fest"], budget), "Konflikte je Lauf")

st.markdown("---")

# --- Experiment: Phasenspeicher --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Hilft der Phasenspeicher?")
st.caption("Aktivität mit und ohne Phasenspeicher. Bei den Formelfamilien je eine Messung je feste Formel; bei Schur eine Instanz und 20 Zufalls-Seeds des Lösers (zufälliger Start der Aktivitäten).")
farben_p = {"aktivitaet": C.COLOR_AKTIV, "ohne_phase": C.COLOR_OHNE}
ref = E.referenz_zelle(aufgabe, ["aktivitaet", "ohne_phase"]) if aufgabe in C.ZELLEN_PHASE else None
if not E.lade_messungen().get("zellen"):
    _fehlt_datei()
elif ref is None:
    _nicht_gemessen("diese Frage", C.ZELLEN_PHASE)
else:
    k = ref["kennzahlen"]
    _zeige("phase", k, ref["roh"], ref["budget"], E.VERFAHREN_LABEL, farben_p, f"Konflikte je Lauf: {ref['label']}",
           E.verdict_phase(ref["label"], k["aktivitaet"], k["ohne_phase"], ref["budget"]), _roh_kopf(ref))
_live_panel("phase", ["aktivitaet", "ohne_phase"], E.VERFAHREN_LABEL, farben_p,
            lambda label, kz, budget: E.verdict_phase(label, kz["aktivitaet"], kz["ohne_phase"], budget), "Konflikte je Lauf")

st.markdown("---")

# --- Experiment: Zerfall ---------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie viel Gewicht haben alte Konflikte?")
st.caption("Fünf Werte des Zerfalls (0,5 bis 1,0; bei 1,0 wird nichts vergessen), jeweils mit Phasenspeicher. Das Verdikt vergleicht die Werte und danach die gemessenen Familien.")
zerfall_verfahren = ["aktivitaet" if z == C.DEFAULT_ZERFALL else E.zerfall_name(z) for z in C.ZERFAELLE]
zerfall_beschriftung = {("aktivitaet" if z == C.DEFAULT_ZERFALL else E.zerfall_name(z)): f"Zerfall {E.zerfall_text(z)}" for z in C.ZERFAELLE}
farben_z = {v: C.COLOR_AKTIV for v in zerfall_verfahren}


def _zerfall_kennz(kz: dict) -> dict:
    return {z: kz["aktivitaet" if z == C.DEFAULT_ZERFALL else E.zerfall_name(z)] for z in C.ZERFAELLE}


ref = E.referenz_zelle(aufgabe, zerfall_verfahren) if aufgabe in C.ZELLEN_ZERFALL else None
if not E.lade_messungen().get("zellen"):
    _fehlt_datei()
elif ref is None:
    _nicht_gemessen("diese Frage", C.ZELLEN_ZERFALL)
else:
    k = ref["kennzahlen"]
    _zeige("zerfall", k, ref["roh"], ref["budget"], zerfall_beschriftung, farben_z, f"Konflikte je Lauf: {ref['label']}",
           E.verdict_zerfall(ref["label"], _zerfall_kennz(k)), _roh_kopf(ref))
beste = {}
for z in C.ZELLEN_ZERFALL:
    r = E.referenz_zelle(z, zerfall_verfahren)
    if r:
        kz = _zerfall_kennz(r["kennzahlen"])
        beste[r["label"]] = min(C.ZERFAELLE, key=lambda w: (kz[w].median, w))
if beste:
    kind, text = E.verdict_zerfall_familien(beste)
    getattr(st, kind)(text)
_live_panel("zerfall", zerfall_verfahren, zerfall_beschriftung, farben_z,
            lambda label, kz, budget: E.verdict_zerfall(label, _zerfall_kennz(kz)), "Konflikte je Lauf")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")


@st.cache_data(show_spinner=False)
def _schubfach():
    return E.messe_schubfach()


st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Konflikte verraten, welche Variablen wichtig sind** | Auf dem Schubfach-Prinzip ist es umgekehrt zur Kernfrage: {E.schubfach_satz(_schubfach())} Gemessen mit einer Instanz je h, einem Lauf je Verfahren und Zerfall 0,95. Der Vorsprung der festen Reihenfolge hängt an der Nummerierung Taube für Taube: In einer Nachprüfung (nicht Teil der Tests) mit zufällig umnummerierten Variablen schrumpft er (h = 6: 580 bis 695 gegen 130 Konflikte; Aktivität 740 bis 1.166). Bei beiden Regeln wachsen die Konflikte von h = 5 auf h = 6. | Symmetriebrechung (eigene Demo der Linie) |
| **Der Phasenspeicher hilft** | Er hilft nicht überall: auf Zufallsformeln und Färbung zeigt die Messung oben keinen klaren Vorteil, auf Schur an der Grenze der Lösbarkeit einen deutlichen. Er ist keine allgemeine Empfehlung. | – |
| **Die feste Reihenfolge ist die Vergleichsregel** | Sie wählt nur nach der Nummer, nicht nach einer statischen Heuristik wie Jeroslow–Wang; der Vergleich sagt nichts über solche Regeln. Moderne Löser mischen mehrere Heuristiken; die Demo zeigt nur die eine belegte Variante. | Verzweigungsregeln im DPLL: [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo) |
| **Konflikte sind das Maß** | Die Verwaltung der Aktivitäten kostet selbst Zeit; sie ist nicht gemessen. Die Neustarts (Luby) laufen in allen Messungen mit und sind hier nicht erklärt. | Neustarts, Löschen gelernter Klauseln (eigene Demos der Linie) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel in konjunktiver Normalform über den Variablen $x_1, \dots, x_n$; ein CDCL-Löser belegt sie nach und nach und lernt bei jedem Konflikt eine Klausel. Gesucht ist hier nicht die Antwort (die hängt nicht von der Wahl ab), sondern wie viele Konflikte der Löser dafür braucht.

| Symbol | Bedeutung |
|---|---|
| $a_v$ | Aktivität der Variablen $x_v$ (anfangs 0) |
| $\delta$ | Zerfall, in dieser Demo $0{,}5 \le \delta \le 1$ (Voreinstellung der Messreihen $0{,}95$) |
| $B_k$ | Variablen der Herleitung beim $k$-ten Konflikt (Konfliktklausel und aufgelöste Gründe, nur oberhalb von Stufe 0) |
| $g_k$ | Zuwachs beim $k$-ten Konflikt |
| $\sigma_v$ | gemerkter Wert der Variablen (zuletzt zurückgenommen, anfangs falsch) |

**Aktivität und Zuwachs.** Beim $k$-ten Konflikt erhalten alle Variablen der Herleitung den Zuwachs, danach wächst er:
$$a_v \leftarrow a_v + g_k \quad (v \in B_k), \qquad g_k = \delta^{-(k-1)}$$
Nach $K$ Konflikten ist die Aktivität die Summe der Zuwächse der Konflikte, an denen die Variable beteiligt war:
$$a_v^{(K)} = \sum_{k \le K,\; v \in B_k} \delta^{-(k-1)}$$
Geteilt durch den Zuwachs $g_{K+1} = \delta^{-K}$ ergibt das die mit dem Alter abgezinste Summe, deshalb muss nie eine Aktivität einzeln verkleinert werden:
$$\frac{a_v^{(K)}}{g_{K+1}} = \sum_{k \le K,\; v \in B_k} \delta^{\,K+1-k}$$
**Neuskalierung.** Überschreitet eine Aktivität $10^{100}$, werden alle Aktivitäten und der Zuwachs mit $10^{-100}$ multipliziert; die Reihenfolge der Aktivitäten ändert sich dadurch nicht.

**Wahl.** Unter den offenen Variablen $O$ wird entschieden:
$$v^{*} = \min \operatorname{arg\,max}_{v \in O} \; a_v$$
(bei Gleichstand die kleinste Nummer), und zwar mit dem Wert
$$\ell = \begin{cases} x_{v^{*}} & \text{falls } \sigma_{v^{*}} = \text{wahr} \\ \neg x_{v^{*}} & \text{sonst.} \end{cases}$$
Die feste Reihenfolge wählt stattdessen $v^{*} = \min O$.

**Literatur.** Die Aktivität im Original (ein Zähler je Variable und Polarität, bei jeder neuen Klausel erhöht und periodisch geteilt, Gleichstand zufällig): Moskewicz, Madigan, Zhao, Zhang, Malik, Chaff, DAC 2001 (Volltext gelesen). Die hier gezeigte Variante (Aktivität je Variable, Zuwachs mit Zerfall) ist die von MiniSat; diese Quelle ist nicht gelesen, deshalb steht sie ohne Zitat. Die Konfliktanalyse nach Marques-Silva und Sakallah (GRASP, IEEE Trans. Computers 1999, gelesen) ist Thema einer anderen Demo der Linie.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
