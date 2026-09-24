"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt, alle Instanztypen und Bäume, Randwerte, Würfel-Knopf, Permalink-Grenzen, Instanzwechsel, Experimente und Sweeps auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import cmst_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if step != 1:
        at.select_slider(key="cmst_step").set_value(step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m for m in at.metric if m.label.startswith(label))


def test_default_run_has_no_exception_and_shows_the_four_metrics():
    at = _run()
    _ok(at)
    assert {"Preis der Kapazität", "Zweige", "Esau-Williams", "Kruskal mit Kap."} <= {m.label for m in at.metric}
    assert _metric(at, "Preis").value == "+21.77 %" and _metric(at, "Zweige").value == "4" and _metric(at, "Esau-Williams").value == "optimal" and _metric(at, "Kruskal mit").value == "optimal"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    ss = at.session_state
    assert (ss["kind_select"], ss["cap_select"], ss["demand_select"], ss["depot_select"], ss["n_slider"], ss["seed_input"]) == (p["kind"], p["cap"], p["demand_mode"], p["depot"], p["n"], p["seed"])
    assert at.metric and at.get("plotly_chart")


@pytest.mark.parametrize("step", [1, 2, 3])
def test_every_step_runs_for_every_kind(step):
    for kind in C.KINDS:
        for cap in (2, 0):
            at = _run(kind_select=kind, cap_select=cap, n_slider=10, cmst_step=step)
            _ok(at)
            assert at.get("plotly_chart") and at.session_state["cmst_step"] == step


def test_every_tree_view_runs():
    for tree in C.TREE_OPTIONS:
        at = _run(step=3, tree_select=tree)
        _ok(at)
        assert at.get("plotly_chart") and any("Kosten" in m.value for m in at.markdown)
    at = _run(step=3, tree_select="exact", n_slider=20)
    _ok(at)
    assert any("nur bis n = 14" in w.value for w in at.warning)
    at = _run(step=3, tree_select="mst")
    _ok(at)
    assert any("verletzt die Kapazität" in w.value for w in at.warning)


def test_infeasible_capacity_shows_a_warning_and_an_info():
    at = _run(step=3, demand_select="mixed", cap_select=2)
    _ok(at)
    assert any("kleiner als der größte Einzelbedarf" in w.value for w in at.warning) and any("keinen gültigen Baum" in i.value for i in at.info)
    at2 = _run(step=2, demand_select="mixed", cap_select=2)
    _ok(at2)
    assert any("kleiner als der größte Einzelbedarf" in w.value for w in at2.warning)


def test_esau_williams_slider_walks_through_all_merges():
    at = _run(step=2)
    _ok(at)
    kmax = int(at.slider(key="cmst_k").max)
    assert kmax == 8
    for k in (0, 3, kmax):
        at.slider(key="cmst_k").set_value(k).run()
        _ok(at)
        assert any(x.value.startswith(f"**Schritt {k} von {kmax}:**") for x in at.markdown)
    assert any("Ende:" in x.value for x in at.markdown) and any("passt nicht in die Kapazität" in x.value for x in at.markdown)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    assert at.session_state["cmst_k"] <= int(at.slider(key="cmst_k").max) == 3


@pytest.mark.parametrize("kw", [
    dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX), dict(n_slider=C.N_MAX, cap_select=C.CAP_OPTIONS[0]), dict(cap_select=C.CAP_OPTIONS[0]), dict(cap_select=C.UNLIMITED), dict(terrain_select=C.TERRAIN_OPTIONS[-1]),
    dict(demand_select="mixed", cap_select=4, n_slider=C.N_MAX), dict(depot_select="center", n_slider=14), dict(kind_select="hubs", sats_select=C.SATS_MAX), dict(kind_select="hubs", sats_select=C.SATS_MIN, cap_select=3),
    dict(kind_select="textbook", cap_select=1), dict(n_slider=C.N_MIN, cap_select=1, demand_select="mixed"),
])
def test_extreme_settings_run(kw):
    for step in (1, 2, 3):
        _ok(_run(step=step, **kw))


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(n="9999", cap="7", demand="big", depot="corner", terrain="0.35", sats="99", tree="nope", kind="nope").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["n_slider"], ss["cap_select"], ss["demand_select"], ss["depot_select"], ss["terrain_select"], ss["sats_select"]) == (C.N_MAX, C.DEFAULT_CAP, "unit", "edge", C.DEFAULT_TERRAIN, C.SATS_MAX)
    assert (ss["tree_select"], ss["kind_select"]) == (C.DEFAULT_TREE, "depot")


def test_permalink_accepts_valid_values():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(kind="hubs", n="14", cap="5", demand="mixed", depot="center", terrain="0.4", sats="6", seed="7", tree="kruskal").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["n_slider"], ss["cap_select"], ss["demand_select"], ss["depot_select"], ss["terrain_select"], ss["sats_select"], ss["seed_input"], ss["tree_select"]) == ("hubs", 14, 5, "mixed", "center", 0.4, 6, 7, "kruskal")


def test_sidebar_shows_only_the_controls_that_matter():
    plain = _run()
    assert any(w.key == "cap_widget" for w in plain.select_slider) and any(w.key == "n_widget" for w in plain.slider) and not any(w.key == "sats_widget" for w in plain.slider)
    assert any(r.key == "demand_widget" for r in plain.radio) and any(r.key == "depot_widget" for r in plain.radio) and any(n.key == "seed_widget" for n in plain.number_input)
    hubs = _run(kind_select="hubs")
    assert any(w.key == "sats_widget" for w in hubs.slider)
    tb = _run(kind_select="textbook")
    assert not any(w.key == "n_widget" for w in tb.slider) and not any(n.key == "seed_widget" for n in tb.number_input) and not any(r.key == "depot_widget" for r in tb.radio) and any(w.key == "cap_widget" for w in tb.select_slider)


def test_changing_the_instance_while_on_step_three_does_not_crash():
    at = _run(step=3, tree_select="exact")
    _ok(at)
    for kw in (dict(kind_select="hubs"), dict(kind_select="textbook"), dict(kind_select="depot", n_slider=30), dict(demand_select="mixed", cap_select=1)):
        for k, v in kw.items():
            at.session_state[k] = v
        at.run()
        _ok(at)


def test_metrics_for_the_unlimited_and_infeasible_cases():
    at = _run(cap_select=0)
    _ok(at)
    assert _metric(at, "Preis").value == "+0.00 %" and _metric(at, "Zweige").value == "2"
    at2 = _run(demand_select="mixed", cap_select=1)
    _ok(at2)
    assert not at2.metric and any("keinen gültigen Baum" in i.value for i in at2.info)


def test_large_instance_offers_no_exact_method_but_states_it():
    at = _run(n_slider=40)
    _ok(at)
    assert any("Kein exaktes Verfahren bei n = 40 > 14" in c.value for c in at.caption)


def test_capacity_curve_runs_on_demand():
    at = _run(n_slider=9)
    next(b for b in at.button if b.key == "curve_start").click().run()
    _ok(at)
    assert any("Kapazität ab der der MST schon passt" in c.value for c in at.caption)


def test_quality_experiment_runs_on_demand():
    at = _run(n_slider=8, cap_select=3)
    next(b for b in at.button if b.key == "quality_start").click().run()
    _ok(at)
    assert {"Esau-Williams optimal", "Größte Lücke", "Kruskal schlechter", "Lokalsuche optimal"} <= {m.label for m in at.metric}
    at2 = _run(n_slider=8, demand_select="mixed", cap_select=2)
    next(b for b in at2.button if b.key == "quality_start").click().run()
    _ok(at2)
    assert any("keine gültigen Bäume" in i.value for i in at2.info)


@pytest.mark.parametrize("param", ["cap", "n", "depot", "demand_mode", "terrain"])
@pytest.mark.parametrize("metric", ["price", "excess", "branches"])
def test_sweeps_run_on_demand_for_every_metric(param, metric):
    at = _run(n_slider=8, sweep_metric=metric)
    at.selectbox(key="sweep_select").set_value(param).run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_villages_offer_the_sats_sweep_and_the_textbook_has_no_experiments():
    at = _run(kind_select="hubs", n_slider=8)
    assert "Anschlüsse je Verteiler" in list(at.selectbox(key="sweep_select").options)
    tb = _run(kind_select="textbook")
    assert not any(b.key in ("curve_start", "quality_start", "sweep_start") for b in tb.button)


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Esau, L. R., & Williams, K. C. (1966)" in m.value and "Papadimitriou, C. H. (1978)" in m.value and "Uchoa, E." in m.value for m in at.markdown)
