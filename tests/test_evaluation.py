"""Auswertung: Analysis-Felder, Kennzahlen über feste Instanzen, Sweeps, Qualitäts-Experiment, Kapazitätskurve, Determinismus."""

import math
from dataclasses import replace

import pytest

import cmst_algorithm as A
import cmst_constants as C
import cmst_evaluation as ev

BASE = ev.Settings(seed=0)


def test_analyse_fields_are_consistent():
    a = ev.analyse(ev.Settings())
    assert a.cap == 4 and a.exact_offered and a.proved and not a.infeasible and not a.mst_free
    assert set(a.sols) == {"kruskal", "ew", "ls", "exact"}
    for name, s in a.sols.items():
        assert A.is_valid_tree(a.inst.n, s.edges, a.demand, a.cap), name
        assert s.cost == pytest.approx(A.edges_cost(s.edges, a.D))
    assert a.best_name is not None and a.best.cost == pytest.approx(a.sols["exact"].cost)
    assert a.solution("mst") is None and a.solution("star") is a.star and a.solution("nope") is None
    assert a.price(a.best_name) >= 0 and a.excess(a.best_name) == pytest.approx(0.0, abs=1e-9)
    assert a.star_saving == pytest.approx(100.0 * (1.0 - a.best.cost / a.star.cost))
    assert a.max_branch(a.best_name) <= a.cap


def test_unlimited_capacity_makes_the_mst_free_and_best():
    a = ev.analyse(ev.Settings(cap=C.UNLIMITED))
    assert a.cap is None and a.mst_free and a.solution("mst") is a.mst
    assert a.price("exact") == pytest.approx(0.0, abs=1e-9) and a.best.cost == pytest.approx(a.mst.cost)


def test_capacity_below_the_largest_demand_is_infeasible_and_offers_no_tree():
    a = ev.analyse(ev.Settings(demand_mode="mixed", cap=3))
    assert a.infeasible and a.best_name is None and a.best is None and a.solution("star") is None and a.sols == {}
    assert a.price("ew") is None and a.excess("ew") is None and a.star_saving is None
    assert ev.run_config(replace(BASE, demand_mode="mixed", cap=2))["infeasible_share"] == 100.0


def test_exact_is_only_offered_for_small_instances():
    small, big = ev.analyse(ev.Settings(n=C.N_EXACT)), ev.analyse(ev.Settings(n=C.N_EXACT + 1))
    assert small.exact_offered and small.proved and not big.exact_offered and "exact" not in big.sols and not big.proved and big.solution("exact") is None
    assert big.best_name in ("star", "mst", "kruskal", "ew", "ls")


def test_best_name_never_reports_an_invalid_mst():
    for seed in range(30):
        a = ev.analyse(ev.Settings(n=10, cap=5, seed=seed))
        if not a.mst_free:
            assert a.best_name != "mst"
        assert a.best.cost <= min(s.cost for s in a.sols.values()) + 1e-9


def test_analyse_is_deterministic():
    for kw in (dict(), dict(kind="hubs", n=14), dict(kind="textbook", cap=2), dict(n=30, demand_mode="mixed", cap=8)):
        a, b = ev.analyse(ev.Settings(**kw)), ev.analyse(ev.Settings(**kw))
        assert {k: (s.cost, s.edges) for k, s in a.sols.items()} == {k: (s.cost, s.edges) for k, s in b.sols.items()}


def test_run_config_uses_five_fixed_instances_and_ignores_the_seed():
    a = ev.run_config(replace(BASE, seed=1))
    b = ev.run_config(replace(BASE, seed=999))
    assert a["n_runs"] == 5 and a["price_best"] == b["price_best"] and a["cost"] == b["cost"]
    assert C.SWEEP_SEEDS == tuple(range(100000, 100005)) and C.FEAS_SEEDS == tuple(range(200000, 200050))


def test_run_config_percentile_bands_enclose_the_median():
    r = ev.run_config(replace(BASE, n=10))
    for key in ("price_best", "price_ew", "excess_kruskal", "branches", "cost"):
        assert r[f"{key}_lo"] - 1e-9 <= r[key] <= r[f"{key}_hi"] + 1e-9


def test_run_config_ew_gap_to_exact_is_nonnegative_and_shares_are_percentages():
    r = ev.run_config(replace(BASE, n=10, cap=3))
    assert r["gap_ew_exact"] >= -1e-9 and r["gap_kruskal_exact"] >= -1e-9 and r["gap_ls_exact"] >= -1e-9
    for k in ("ew_optimal_share", "kruskal_optimal_share", "ls_optimal_share", "mst_free_share", "infeasible_share", "offered_share"):
        assert 0.0 <= r[k] <= 100.0
    assert r["offered_share"] == 100.0


def test_price_of_capacity_falls_with_the_capacity():
    rows = ev.sweep("cap", replace(BASE, n=10), values=(1, 2, 4, 8, C.UNLIMITED))
    prices = [r["price_best"] for r in rows]
    assert prices == sorted(prices, reverse=True) and prices[-1] == pytest.approx(0.0, abs=1e-9)


def test_sweeps_have_one_row_per_value_and_only_valid_parameters():
    assert ev.sweep_params("depot") == ["cap", "n", "depot", "demand_mode", "terrain"]
    assert ev.sweep_params("hubs")[-1] == "sats" and all(p in ev.SWEEP_LABELS for p in ev.sweep_params("hubs"))
    rows = ev.sweep("depot", replace(BASE, n=8))
    assert [r["value"] for r in rows] == ["edge", "center"]
    rows = ev.sweep("n", replace(BASE, cap=3), values=(6, 9))
    assert [r["value"] for r in rows] == [6, 9]
    assert ev.SWEEP_TICKS["cap"](C.UNLIMITED) == "∞" and ev.SWEEP_TICKS["cap"](4) == "4" and ev.SWEEP_TICKS["depot"]("center") == C.DEPOT_LABELS["center"]


def test_ew_quality_reports_consistent_shares():
    q = ev.ew_quality(replace(BASE, n=9, cap=3), seeds=range(200000, 200012))
    assert q["n_runs"] == 12 and q["exact_used"]
    assert 0 <= q["ew_optimal"] <= 100 and q["ew_gap_mean"] >= -1e-9 and q["ew_gap_max"] >= q["ew_gap_mean"] - 1e-9
    assert q["kruskal_worse"] + q["kruskal_better"] <= 100.0 + 1e-9 and q["ls_optimal"] >= 0
    inf = ev.ew_quality(replace(BASE, demand_mode="mixed", cap=2), seeds=range(200000, 200004))
    assert inf["n_runs"] == 0 and math.isnan(inf["ew_gap_mean"])


def test_capacity_curve_is_monotone_and_ends_at_the_mst():
    rows = ev.capacity_curve(replace(BASE, n=9))
    assert rows[0]["cap"] == 1 and rows[-1]["cap"] == C.UNLIMITED
    costs = [r["cost"] for r in rows]
    assert all(a >= b - 1e-9 for a, b in zip(costs, costs[1:])) and rows[-1]["cost"] == pytest.approx(rows[-1]["mst"]) and rows[0]["cost"] == pytest.approx(rows[0]["star"])
    assert all(r["proved"] for r in rows) and rows[-1]["mst_free"]
    mixed = ev.capacity_curve(replace(BASE, n=9, demand_mode="mixed"))
    assert mixed[0]["cap"] == 4
