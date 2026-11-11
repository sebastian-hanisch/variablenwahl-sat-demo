"""Presets: Vollständigkeit, gültige Werte, erstes Preset = Standardeinstellungen, Permalink (Einrasten)."""

import vsd_constants as C
import vsd_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_allowed_options():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            assert preset[key] in P.SETTING_SPECS[state_key].options, (name, key)


def test_default_preset_equals_the_default_settings():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    assert {P.PRESET_KEYS[k]: v for k, v in erstes.items()} == {k: s.default for k, s in P.SETTING_SPECS.items()}


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_differ_in_at_least_one_setting():
    werte = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(werte)) == len(werte)


def test_preset_names_follow_the_tasks():
    """Jedes Preset außer dem Handbeispiel trägt den Namen seiner Aufgabe und stellt genau diese ein."""
    for name, preset in C.PRESETS.items():
        if name != "Handbeispiel F3":
            assert preset["aufgabe"] == name


def test_permalink_rastet_auf_erlaubte_werte_ein():
    spec = P.SETTING_SPECS["zerfall"]
    assert P.einrasten(spec, "0.96") == 0.95 and P.einrasten(spec, "7") == 1.0 and P.einrasten(spec, "-3") == 0.5
    assert P.einrasten(spec, "abc") is None
    text = P.SETTING_SPECS["aufgabe"]
    assert P.einrasten(text, "Schur n = 44, k = 4") == "Schur n = 44, k = 4" and P.einrasten(text, "gibt es nicht") is None
    assert P.einrasten(P.SETTING_SPECS["formel"], P.FORMEL_KLEIN) == P.FORMEL_KLEIN


def test_alle_aufgaben_haben_label_und_schluessel():
    assert len(C.AUFGABEN_LABELS) == len(set(C.AUFGABEN_LABELS)) == len(C.AUFGABEN)
    for k, a in C.AUFGABEN.items():
        assert C.SCHLUESSEL_VON_LABEL[a["label"]] == k
    for gruppe in (C.ZELLEN_AKTIVITAET, C.ZELLEN_PHASE, C.ZELLEN_ZERFALL):
        assert set(gruppe) <= set(C.AUFGABEN)
