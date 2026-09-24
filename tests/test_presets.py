"""Presets: gültige Einstellungen, Kennzahl-Bänder über die 5 festen Instanzen, Permalink-Spezifikation."""

import pytest

import cmst_constants as C
import cmst_evaluation as ev
import cmst_presets as P

KEYS = {"kind", "n", "cap", "demand_mode", "depot", "terrain", "sats", "seed", "tree"}


def _settings(p):
    return ev.Settings(p["kind"], p["n"], p["demand_mode"], p["depot"], p["cap"], p["terrain"], p["sats"], p["seed"])


def test_presets_have_help_and_full_settings():
    assert len(C.PRESETS) == 8 and set(C.PRESET_HELP) == set(C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name
        assert p["kind"] in C.KINDS and p["tree"] in C.TREE_OPTIONS and p["demand_mode"] in C.DEMAND_MODES and p["depot"] in C.DEPOT_POS
        assert C.N_MIN <= p["n"] <= C.N_MAX and p["cap"] in C.CAP_OPTIONS and p["terrain"] in C.TERRAIN_OPTIONS and C.SATS_MIN <= p["sats"] <= C.SATS_MAX and p["seed"] <= C.SEED_MAX
        assert len(C.PRESET_HELP[name]) > 40


def test_default_preset_is_the_default_setting():
    assert _settings(C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    for key, state_key in P.PRESET_KEYS.items():
        assert P.SETTING_SPECS[state_key].default == C.PRESETS["Standardfall (Voreinstellung)"][key]


@pytest.mark.parametrize("name", list(C.PRESET_EXPECTED_BANDS))
def test_preset_key_metric_lies_in_its_band(name):
    metric, lo, hi = C.PRESET_EXPECTED_BANDS[name]
    r = ev.run_config(_settings(C.PRESETS[name]))
    assert lo <= r[metric] <= hi, (name, metric, r[metric])


def test_every_preset_analyses_and_finds_a_tree():
    for name, p in C.PRESETS.items():
        a = ev.analyse(_settings(p))
        assert not a.infeasible and a.best_name is not None, name


def test_setting_specs_cover_all_widget_keys_and_permalink_names_are_unique():
    assert set(P.WIDGET_KEYS) <= set(P.SETTING_SPECS)
    urls = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(urls) == len(set(urls))
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


@pytest.mark.parametrize("state_key,bad", [("kind_select", "grid"), ("cap_select", "7"), ("demand_select", "big"), ("depot_select", "corner"), ("terrain_select", "0.35"), ("tree_select", "nope")])
def test_permalink_casters_reject_invalid_choices(state_key, bad):
    with pytest.raises(ValueError):
        P.SETTING_SPECS[state_key].caster(bad)
    default = P.SETTING_SPECS[state_key].default
    assert P.SETTING_SPECS[state_key].caster(str(default)) == default


def test_permalink_casters_accept_valid_values():
    assert P.SETTING_SPECS["cap_select"].caster("0") == C.UNLIMITED and P.SETTING_SPECS["cap_select"].caster("30") == 30
    assert P.SETTING_SPECS["depot_select"].caster("center") == "center" and P.SETTING_SPECS["demand_select"].caster("mixed") == "mixed"
    assert P.SETTING_SPECS["n_slider"].lo == C.N_MIN and P.SETTING_SPECS["sats_select"].hi == C.SATS_MAX
