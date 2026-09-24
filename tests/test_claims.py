"""Jede Zahl, die App-Text, Preset-Hilfen und README nennen, wird hier über die echten Auswertungsfunktionen (ev.analyse / ev.run_config / ev.sweep / ev.ew_quality / ev.capacity_curve) belegt - nie über ein
Ad-hoc-Skript. Kosten sind Gleitkommazahlen, Kennzahlen daher auf Rundungsstellen verglichen; Zweigzahlen, Bedarfe und Anteile sind ganzzahlig."""

from dataclasses import replace
from functools import lru_cache

import pytest

import cmst_algorithm as A
import cmst_constants as C
import cmst_evaluation as ev

BASE = ev.Settings(seed=0)


@lru_cache(maxsize=None)
def _ana(**kw):
    return ev.analyse(ev.Settings(**kw))


@lru_cache(maxsize=None)
def _cfg(**kw):
    return ev.run_config(replace(BASE, **kw))


@lru_cache(maxsize=None)
def _sweep(param, values=None, **kw):
    return ev.sweep(param, replace(BASE, **kw), values=values)


@lru_cache(maxsize=None)
def _quality(**kw):
    return ev.ew_quality(replace(BASE, **kw))


def _col(rows, key, digits=2):
    return [None if r[key] != r[key] else round(r[key], digits) for r in rows]


def r2(x):
    return round(x, 2)


def _sizes(a, sol):
    return [A.branch_demand(b, a.demand) for b in sol.branches]


# --- Preset-Hilfen (jeweils die Einzelinstanz des Presets) ------------------------------------------------------------------------------------------


def test_preset_standard_case():
    a = _ana()
    assert r2(a.mst.cost) == 215.65 and [A.branch_demand(b, a.demand) for b in a.mst.branches] == [2, 10] and not a.mst_free
    for k in ("kruskal", "ew", "ls", "exact"):
        assert r2(a.sols[k].cost) == 262.60 and _sizes(a, a.sols[k]) == [2, 4, 3, 3]
    assert r2(a.price("exact")) == 21.77 and r2(a.star.cost) == 555.17 and round(a.star_saving, 1) == 52.7


def test_preset_capacity_two_star_and_free():
    a = _ana(cap=2)
    assert r2(a.sols["exact"].cost) == 358.88 and r2(a.sols["ew"].cost) == 358.88 and r2(a.sols["ls"].cost) == 358.88 and r2(a.sols["kruskal"].cost) == 375.75
    assert a.sols["exact"].n_branches == 7 and r2(a.price("exact")) == 66.42 and r2(a.excess("kruskal")) == 4.70
    s = _ana(cap=1)
    assert r2(s.best.cost) == 555.17 and s.best.n_branches == 12 and r2(s.price("exact")) == 157.44 and all(r2(s.sols[k].cost) == 555.17 for k in ("kruskal", "ew", "ls", "exact"))
    f = _ana(cap=10)
    assert f.mst_free and r2(f.price("exact")) == 0.0 and r2(f.best.cost) == 215.65


def test_preset_depot_in_the_middle():
    a = _ana(depot="center")
    assert r2(a.mst.cost) == 225.43 and a.mst.n_branches == 1 and A.branch_demand(a.mst.branches[0], a.demand) == 12
    assert r2(a.sols["exact"].cost) == 264.51 and a.sols["exact"].n_branches == 3 and _sizes(a, a.sols["exact"]) == [4, 4, 4] and r2(a.price("exact")) == 17.34
    assert r2(a.sols["ew"].cost) == 277.77 and r2(a.sols["ls"].cost) == 277.77 and r2(a.excess("ew")) == 5.01 and r2(a.sols["kruskal"].cost) == 280.15 and r2(a.excess("kruskal")) == 5.91
    assert a.best_name == "exact"


def test_preset_kruskal_beats_esau_williams():
    a = _ana(seed=11)
    assert r2(a.sols["ew"].cost) == 310.64 and r2(a.excess("ew")) == 9.59 and r2(a.sols["kruskal"].cost) == 289.02 and r2(a.excess("kruskal")) == 1.96
    assert r2(a.sols["ls"].cost) == 283.45 and r2(a.sols["exact"].cost) == 283.45


def test_preset_villages():
    a = _ana(kind="hubs", n=14, cap=5)
    assert r2(a.mst.cost) == 155.13 and [A.branch_demand(b, a.demand) for b in a.mst.branches] == [7, 7]
    assert r2(a.best.cost) == 238.88 and r2(a.price(a.best_name)) == 53.98 and a.best.n_branches == 4 and _sizes(a, a.sols["exact"]) == [5, 2, 5, 2] and r2(a.excess("kruskal")) == 0.93


def test_preset_cross_fixture():
    for cap, cost, price in ((3, 88.28, 10.36), (2, 96.57, 20.71), (1, 116.57, 45.71)):
        a = _ana(kind="textbook", cap=cap)
        assert r2(a.sols["exact"].cost) == cost and r2(a.price("exact")) == price and a.proved
    a = _ana(kind="textbook", cap=3)
    assert r2(a.mst.cost) == 80.0 and a.mst.n_branches == 1 and _sizes(a, a.sols["exact"]) in ([3, 1], [1, 3])


# --- Wert der Kapazität -----------------------------------------------------------------------------------------------------------------------


def test_capacity_curve_of_the_standard_instance():
    rows = ev.capacity_curve(ev.Settings())
    assert [r["cap"] for r in rows] == list(range(1, 13)) + [C.UNLIMITED] and all(r["proved"] for r in rows)
    assert _col(rows, "cost") == [555.17, 358.88, 308.84, 262.6, 253.26, 244.78, 233.47, 233.47, 224.14, 215.65, 215.65, 215.65, 215.65]
    assert _col(rows, "price") == [157.44, 66.42, 43.21, 21.77, 17.44, 13.51, 8.26, 8.26, 3.93, 0.0, 0.0, 0.0, 0.0]
    assert [r["branches"] for r in rows] == [12, 7, 5, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2]
    assert [r["mst_free"] for r in rows] == [False] * 9 + [True] * 4


def test_price_of_capacity_over_q_with_the_depot_at_the_edge():
    rows = _sweep("cap", values=(1, 2, 3, 4, 5, 6, 8, 10, 0))
    assert _col(rows, "price_best") == [133.6, 47.23, 25.78, 13.49, 8.52, 3.29, 0.88, 0.0, 0.0]
    assert _col(rows, "star_saving") == [0.0, 35.92, 46.16, 50.97, 52.9, 56.23, 56.82, 57.19, 57.19]
    assert [r["mst_free_share"] for r in rows] == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0, 80.0, 100.0]
    assert _col(rows, "branches", 0) == [12.0, 6.0, 4.0, 4.0, 3.0, 3.0, 2.0, 2.0, 2.0]


def test_depot_in_the_middle_makes_the_capacity_cheaper_not_dearer():
    rows = _sweep("cap", values=(2, 4, 6, 8, 0), depot="center")
    assert _col(rows, "price_best") == [35.78, 6.98, 2.47, 0.0, 0.0] and [r["mst_free_share"] for r in rows] == [0.0, 0.0, 40.0, 60.0, 100.0]
    d = _sweep("depot")
    assert [r["value"] for r in d] == ["edge", "center"] and _col(d, "price_best") == [13.49, 6.98] and _col(d, "star_saving") == [50.97, 47.01]


def test_mixed_demand_needs_a_capacity_of_at_least_four_and_costs_more():
    rows = _sweep("cap", values=(2, 3, 4, 6, 8, 0), demand_mode="mixed")
    assert [r["infeasible_share"] for r in rows] == [100.0, 80.0, 0.0, 0.0, 0.0, 0.0]
    assert _col(rows, "price_best") == [None, 85.5, 78.33, 52.31, 27.17, 0.0]
    d = _sweep("demand_mode")
    assert _col(d, "price_best") == [13.49, 78.33] and _col(d, "star_saving") == [50.97, 17.75] and _col(d, "branches", 0) == [4.0, 9.0]


def test_the_price_grows_with_n_at_fixed_capacity_and_the_star_saving_too():
    rows = _sweep("n", values=(8, 12, 14, 20, 30, 60))
    assert [r["value"] for r in rows] == [8, 12, 14, 20, 30, 60]
    assert _col(rows, "price_best") == [6.29, 13.49, 19.99, 25.81, 38.17, 85.58] and _col(rows, "star_saving") == [44.45, 50.97, 53.89, 56.68, 60.18, 65.11]
    assert _col(rows, "branches", 0) == [3.0, 4.0, 4.0, 6.0, 9.0, 16.0] and [r["mst_branches"] for r in rows] == [2.0] * 6


def test_terrain_does_not_change_the_story():
    rows = _sweep("terrain")
    assert [r["value"] for r in rows] == [0.0, 0.3, 0.6, 1.0] and _col(rows, "price_best") == [13.49, 10.28, 10.47, 8.77]


# --- Güte der Verfahren -----------------------------------------------------------------------------------------------------------------------


def test_kruskal_with_capacity_is_worse_at_small_and_medium_q_esau_williams_is_exact_in_the_median():
    rows = _sweep("cap", values=(1, 2, 3, 4, 5, 6, 8, 10, 0))
    assert _col(rows, "excess_kruskal") == [0.0, 4.28, 7.24, 5.19, 6.33, 0.0, 0.0, 0.0, 0.0] and _col(rows, "excess_ew") == [0.0] * 9
    assert [r["ew_optimal_share"] for r in rows] == [100.0, 60.0, 60.0, 80.0, 80.0, 80.0, 80.0, 100.0, 100.0]
    assert [r["kruskal_optimal_share"] for r in rows] == [100.0, 20.0, 20.0, 40.0, 20.0, 60.0, 80.0, 80.0, 100.0]
    assert [r["ls_optimal_share"] for r in rows] == [100.0, 100.0, 60.0, 80.0, 80.0, 100.0, 100.0, 100.0, 100.0]
    assert all(r["gap_ew_exact"] == 0.0 for r in rows)


def test_esau_williams_quality_over_fifty_instances():
    for kw, ew_opt, mean, mx, ck_worse, ck_better, ls_opt, ls_imp, ck_opt in (
        (dict(n=12, cap=3), 60.0, 1.59, 10.8, 70.0, 6.0, 90.0, 38.0, 26.0),
        (dict(n=12, cap=4), 52.0, 1.37, 9.4, 62.0, 14.0, 84.0, 38.0, 20.0),
        (dict(n=12, cap=6), 56.0, 0.78, 5.7, 48.0, 12.0, 74.0, 22.0, 40.0),
        (dict(n=12, cap=4, depot="center"), 78.0, 0.49, 6.8, 62.0, 4.0, 90.0, 12.0, 34.0),
        (dict(kind="hubs", n=14, cap=5), 6.0, 3.53, 11.8, 80.0, 12.0, 52.0, 76.0, 2.0),
    ):
        q = _quality(**kw)
        assert q["n_runs"] == 50 and q["exact_used"]
        assert (q["ew_optimal"], round(q["ew_gap_mean"], 2), round(q["ew_gap_max"], 1), q["kruskal_worse"], q["kruskal_better"], q["ls_optimal"], q["ls_improves"], q["kruskal_optimal"]) == (ew_opt, mean, mx, ck_worse, ck_better, ls_opt, ls_imp, ck_opt), kw
    assert _quality(n=12, cap=4)["mst_free"] == 0.0 and _quality(n=12, cap=6)["mst_free"] == 6.0


def test_villages_make_esau_williams_worse():
    rows = _sweep("cap", values=(2, 3, 4, 5, 6, 8, 0), kind="hubs", n=14)
    assert _col(rows, "price_best") == [169.76, 98.97, 66.21, 59.89, 32.68, 21.4, 0.0]
    assert _col(rows, "excess_ew") == [0.0, 2.68, 2.27, 3.91, 0.0, 0.0, 0.0] and _col(rows, "excess_kruskal") == [2.53, 3.65, 3.97, 6.52, 0.0, 0.0, 0.0]
    assert [r["ew_optimal_share"] for r in rows] == [60.0, 0.0, 0.0, 0.0, 60.0, 80.0, 100.0]


def test_capacity_matching_the_village_size_is_cheap():
    rows = _sweep("sats", values=(3, 4, 5, 6, 8), kind="hubs", n=14, cap=5)
    assert _col(rows, "price_best") == [33.27, 28.55, 59.89, 69.42, 62.06] and [r["ew_optimal_share"] for r in rows] == [40.0, 80.0, 0.0, 0.0, 20.0]
    assert _col(rows, "excess_ew") == [1.05, 0.0, 3.91, 3.01, 0.48]


def test_larger_instances_without_exact_compare_the_heuristics_only():
    for n, price, ck, ew in ((20, 25.81, 7.85, 0.74), (30, 38.17, 4.93, 0.75), (60, 85.58, 7.99, 1.47)):
        r = _cfg(n=n)
        assert r["offered_share"] == 0.0 and r2(r["price_best"]) == price and r2(r["excess_kruskal"]) == ck and r2(r["excess_ew"]) == ew and r["ls_optimal_share"] == 100.0


def test_the_lower_bound_property_the_mst_is_never_dearer_than_any_capacitated_tree():
    for seed in C.SWEEP_SEEDS:
        for cap in (2, 4, 8):
            a = ev.analyse(ev.Settings(n=12, cap=cap, seed=seed))
            assert a.mst.cost <= a.best.cost + 1e-9
