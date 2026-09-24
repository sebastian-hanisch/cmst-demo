"""Instanzen: Erzeugung, Determinismus, Kostenmatrix, Bedarf, Depotlage, Geländefaktor, Ortschaften, Kreuz-Fixture."""

import numpy as np
import pytest

import cmst_algorithm as A
import cmst_constants as C
import cmst_scenario as S


@pytest.mark.parametrize("kind", ["depot", "hubs"])
def test_generate_is_deterministic_and_well_formed(kind):
    a = S.generate(15, 0.3, 7, kind, 5, "edge", "mixed")
    b = S.generate(15, 0.3, 7, kind, 5, "edge", "mixed")
    assert np.array_equal(a.D, b.D) and np.array_equal(a.xy, b.xy) and a.demand == b.demand
    assert a.n == 16 and a.customers == 15 and a.kind == kind
    assert a.D.shape == (16, 16) and np.allclose(a.D, a.D.T) and np.all(np.diag(a.D) == 0) and np.all(a.D[~np.eye(16, dtype=bool)] > 0)
    assert len(a.demand) == 16 and a.demand[0] == 0
    assert not np.array_equal(S.generate(15, 0.3, 8, kind, 5).D, a.D)


def test_depot_position_and_demand_modes():
    assert tuple(S.generate(10, 0.0, 1, depot="edge").xy[0]) == C.DEPOT_POS["edge"]
    assert tuple(S.generate(10, 0.0, 1, depot="center").xy[0]) == C.DEPOT_POS["center"]
    unit = S.generate(10, 0.0, 1)
    assert unit.demand == (0,) + (1,) * 10 and unit.total_demand == 10 and unit.max_demand == 1
    mixed = S.generate(30, 0.0, 1, demand_mode="mixed")
    assert set(mixed.demand[1:]) <= {1, 2, 3, 4} and len(set(mixed.demand[1:])) > 1 and mixed.max_demand <= C.DEMAND_MAX


def test_demand_stream_depends_only_on_seed_and_count():
    a = S.generate(12, 0.0, 5, demand_mode="mixed", depot="edge")
    b = S.generate(12, 0.9, 5, kind="hubs", sats=6, depot="center", demand_mode="mixed")
    assert a.demand == b.demand
    assert S.generate(12, 0.0, 6, demand_mode="mixed").demand != a.demand


def test_terrain_factor():
    plain = S.generate(12, 0.0, 3)
    xy = plain.xy
    for u in range(plain.n):
        for v in range(u + 1, plain.n):
            assert plain.D[u, v] == pytest.approx(float(np.hypot(*(xy[u] - xy[v]))))
    hilly = S.generate(12, 0.5, 3)
    assert np.all(hilly.D >= plain.D - 1e-9) and np.all(hilly.D <= 1.5 * plain.D + 1e-9) and not np.allclose(hilly.D, plain.D)


def test_invalid_arguments_raise():
    for kw in (dict(kind="grid"), dict(depot="corner"), dict(demand_mode="big")):
        with pytest.raises(ValueError):
            S.generate(5, 0.0, 1, **kw)


def test_hub_layout_has_rings_of_satellites_and_truncates():
    for sats in (3, 5, 8):
        inst = S.generate(sats * 2 + 2, 0.0, 4, "hubs", sats)
        pts = inst.xy[1:]
        assert inst.sats == sats and len(pts) == sats * 2 + 2
        ring = pts[1:sats + 1]
        d = np.hypot(ring[:, 0] - pts[0][0], ring[:, 1] - pts[0][1])
        assert d.min() >= 5.39 and d.max() <= 6.61
    for n in (5, 7, 11, 16):
        assert S.generate(n, 0.0, 2, "hubs", 5).customers == n
    assert S.generate(10, 0.0, 2).sats == 0


def test_cross_fixture():
    t = S.textbook_instance()
    assert t.kind == "textbook" and t.n == 5 and t.demand == (0, 1, 1, 1, 1) and t.labels == ("W", "C", "E", "N", "S")
    assert np.allclose(t.xy[0], (20.0, 50.0)) and np.allclose(t.xy[1], (40.0, 50.0))
    assert A.mst_solution(t.D).cost == pytest.approx(80.0)
    assert t.D[0, 2] == pytest.approx(40.0) and t.D[3, 4] == pytest.approx(40.0) and t.D[0, 3] == pytest.approx(20.0 * 2 ** 0.5)
