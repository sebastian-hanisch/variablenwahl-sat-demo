"""Permalink (Begrenzen/Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Alle Regler der Seitenleiste sind Auswahlen mit festen Werten (`options`): ein Wert aus der Adresszeile rastet auf den nächsten
erlaubten Wert ein (Zahlen) bzw. wird verworfen (Text, der nicht zur Auswahl gehört).
"""

import random
from dataclasses import dataclass

import streamlit as st

import vsd_constants as C

FORMEL_HAND = "Handbeispiel F3"
FORMEL_KLEIN = "Kleine Zufallsformel"
FORMELN = (FORMEL_HAND, FORMEL_KLEIN)


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    options: tuple = ()


SETTING_SPECS = {
    "aufgabe": SettingSpec("aufgabe", str, C.AUFGABEN["zufall150"]["label"], C.AUFGABEN_LABELS),
    "formel": SettingSpec("formel", str, FORMEL_HAND, FORMELN),
    "zerfall": SettingSpec("zerfall", float, C.HAND_ZERFALL, C.ZERFAELLE),
}
PRESET_KEYS = {"aufgabe": "aufgabe", "formel": "formel", "zerfall": "zerfall"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def einrasten(spec: SettingSpec, roh):
    """Wert aus der Adresszeile auf eine erlaubte Option bringen, sonst None."""
    try:
        wert = spec.caster(roh)
    except (ValueError, TypeError):
        return None
    if spec.caster is float:
        return min(spec.options, key=lambda o: abs(o - wert))
    return wert if wert in spec.options else None


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf erlaubte Werte begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            wert = einrasten(spec, qp[spec.url_param])
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS mit dem Session State (ein Preset ohne Eintrag für einen Regler
    meint dessen Standardwert). Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["klein_seed"] = random.randint(0, C.SEED_MAX)
