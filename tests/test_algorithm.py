"""Die Korrektheitskette der Verfahren (zuerst, vor jeder Messung): Zweigsatz, Exaktheit der Mengenpartition gegen Brute-Force über alle Bäume, Gültigkeit, Schrankenkette, Sonderfälle, Buchführung von
Esau-Williams, Lokalsuche, schwierige Fixtures."""

import math
from itertools import combinations

import numpy as np
import pytest

import cmst_algorithm as A
import cmst_scenario as S
from brute import all_trees, brute_cmst, random_instance
from fixtures import fixture


def _cases(count=90):
    for seed in range(count):
        nc = 3 + seed % 3
        D, dem = random_instance(nc, seed, mixed=seed % 2 == 1, integer=seed % 3 == 0)
        for cap in (None, 1, 2, 3, 4, 5, 8):
            yield seed, D, dem, cap


# --- 1. Zweigsatz -----------------------------------------------------------------------------------------------------------------------------


def test_branch_cost_is_the_cheapest_tree_with_the_depot_as_a_leaf():
    for seed in range(60):
        nc = 2 + seed % 4
        D, _dem = random_instance(nc, seed, integer=seed % 3 == 0)
        n = nc + 1
        for size in range(1, nc + 1):
            for S_ in combinations(range(1, n), size):
                best = math.inf
                nodes = (0,) + S_
                idx = {v: i for i, v in enumerate(nodes)}
                for edges in all_trees(len(nodes)):
                    if sum(1 for e in edges if 0 in e) == 1:
                        best = min(best, sum(D[nodes[u], nodes[v]] for u, v in edges))
                assert A.branch_cost(S_, D) == pytest.approx(best), (seed, S_)
                assert A.edges_cost(A.branch_edges(S_, D), D) == pytest.approx(best)
                assert len(A.branch_edges(S_, D)) == size


def test_mst_cost_matches_brute_force_and_handles_tiny_sets():
    D, _ = random_instance(5, 3)
    assert A.mst_cost((), D) == 0.0 and A.mst_cost((2,), D) == 0.0
    for S_ in ((1, 2), (1, 3, 5), (1, 2, 3, 4, 5)):
        nodes = tuple(S_)
        best = min(sum(D[nodes[u], nodes[v]] for u, v in edges) for edges in all_trees(len(nodes))) if len(nodes) > 1 else 0.0
        assert A.mst_cost(S_, D) == pytest.approx(best)


# --- 2. Exaktheit -----------------------------------------------------------------------------------------------------------------------------


def test_exact_partition_matches_brute_force_over_all_trees():
    for seed, D, dem, cap in _cases():
        feasible = cap is None or cap >= max(dem)
        ref = brute_cmst(D, dem, cap) if feasible else None
        ex = A.exact_partition(D, dem, cap)
        if ref is None:
            assert not ex.feasible and ex.solution is None
        else:
            assert ex.feasible and ex.solution.cost == pytest.approx(ref), (seed, cap)
            assert A.is_valid_tree(D.shape[0], ex.solution.edges, dem, cap)


def test_exact_partition_matches_an_independent_partition_enumeration():
    def partitions(items):
        if not items:
            yield []
            return
        first, rest = items[0], items[1:]
        for r in range(len(rest) + 1):
            for comb in combinations(rest, r):
                block = (first,) + comb
                remaining = [x for x in rest if x not in comb]
                for tail in partitions(remaining):
                    yield [block] + tail

    for seed in range(25):
        nc = 6 + seed % 3
        D, dem = random_instance(nc, 200 + seed, mixed=seed % 2 == 0)
        for cap in (4, 5, 7, None):
            best = min((sum(A.branch_cost(b, D) for b in part) for part in partitions(list(range(1, nc + 1))) if cap is None or all(sum(dem[v] for v in b) <= cap for b in part)), default=None)
            ex = A.exact_partition(D, dem, cap)
            assert ex.solution.cost == pytest.approx(best)


# --- 3. Gültigkeit ----------------------------------------------------------------------------------------------------------------------------


def test_every_solution_is_a_valid_tree_with_correct_bookkeeping():
    for seed, D, dem, cap in _cases():
        if cap is not None and cap < max(dem):
            with pytest.raises(ValueError):
                A.esau_williams(D, dem, cap)
            with pytest.raises(ValueError):
                A.capacitated_kruskal(D, dem, cap)
            continue
        sols = [A.esau_williams(D, dem, cap), A.capacitated_kruskal(D, dem, cap)]
        sols.append(A.reoptimize(sols[0], D))
        sols.append(A.local_search(sols[0].branches, D, dem, cap))
        sols.append(A.exact_partition(D, dem, cap).solution)
        for s in sols:
            n = D.shape[0]
            assert A.is_valid_tree(n, s.edges, dem, cap), (s.method, seed, cap)
            assert s.cost == pytest.approx(sum(D[u, v] for u, v in s.edges))
            assert sorted(v for b in s.branches for v in b) == list(range(1, n)) and len(s.edges) == n - 1
            assert all(sum(1 for e in s.edges if e[0] == 0 and e[1] in b) == 1 for b in s.branches)


# --- 4. Schrankenkette ------------------------------------------------------------------------------------------------------------------------


def test_bound_chain_mst_le_exact_le_local_search_le_reoptimized_ew_le_ew_le_star():
    for seed, D, dem, cap in _cases():
        if cap is not None and cap < max(dem):
            continue
        mst, star = A.mst_solution(D), A.star_solution(D)
        ex = A.exact_partition(D, dem, cap).solution
        ew, ck = A.esau_williams(D, dem, cap), A.capacitated_kruskal(D, dem, cap)
        re = A.reoptimize(ew, D)
        ls = A.local_search(ew.branches, D, dem, cap)
        assert mst.cost - 1e-9 <= ex.cost <= ls.cost + 1e-9 <= re.cost + 2e-9 <= ew.cost + 3e-9
        assert ew.cost <= star.cost + 1e-9 and ex.cost <= ck.cost + 1e-9 and ex.cost <= star.cost + 1e-9


def test_local_search_is_a_local_optimum_of_its_neighbourhood():
    for seed in range(40):
        D, dem = random_instance(6, 500 + seed, mixed=seed % 2 == 1)
        for cap in (4, 5, 7):
            ew = A.esau_williams(D, dem, cap)
            ls = A.local_search(ew.branches, D, dem, cap)
            base = ls.cost
            branches = [tuple(b) for b in ls.branches]
            bc = lambda b: A.branch_cost(b, D) if b else 0.0  # noqa: E731
            for i, b in enumerate(branches):
                for v in b:
                    rest = tuple(x for x in b if x != v)
                    for j in range(len(branches) + 1):
                        if j == i:
                            continue
                        tgt = branches[j] if j < len(branches) else ()
                        if sum(dem[x] for x in tgt) + dem[v] > cap:
                            continue
                        delta = bc(rest) + bc(tgt + (v,)) - bc(b) - (bc(tgt) if tgt else 0.0)
                        assert delta >= -1e-8
            for i, j in combinations(range(len(branches)), 2):
                if sum(dem[x] for x in branches[i] + branches[j]) <= cap:
                    assert bc(branches[i] + branches[j]) - bc(branches[i]) - bc(branches[j]) >= -1e-8
                for v in branches[i]:
                    for w in branches[j]:
                        ni = tuple(x for x in branches[i] if x != v) + (w,)
                        nj = tuple(x for x in branches[j] if x != w) + (v,)
                        if sum(dem[x] for x in ni) <= cap and sum(dem[x] for x in nj) <= cap:
                            assert bc(ni) + bc(nj) - bc(branches[i]) - bc(branches[j]) >= -1e-8
            assert base >= A.exact_partition(D, dem, cap).solution.cost - 1e-9


# --- 5. Sonderfälle ---------------------------------------------------------------------------------------------------------------------------


def test_unlimited_capacity_is_the_mst_and_unit_capacity_one_is_the_star():
    for seed in range(40):
        D, dem = random_instance(5, seed, integer=seed % 3 == 0)
        mst, star = A.mst_solution(D), A.star_solution(D)
        assert A.exact_partition(D, dem, None).solution.cost == pytest.approx(mst.cost)
        assert A.exact_partition(D, dem, sum(dem)).solution.cost == pytest.approx(mst.cost)
        assert A.exact_partition(D, dem, 1).solution.cost == pytest.approx(star.cost)
        assert A.esau_williams(D, dem, 1).cost == pytest.approx(star.cost) and A.capacitated_kruskal(D, dem, 1).cost == pytest.approx(star.cost)
        assert A.esau_williams(D, dem, None).cost >= mst.cost - 1e-9


def test_capacity_two_branches_have_at_most_two_customers_and_match_brute_force():
    for seed in range(40):
        D, dem = random_instance(5, 700 + seed, integer=seed % 2 == 0)
        ex = A.exact_partition(D, dem, 2).solution
        assert all(len(b) <= 2 for b in ex.branches)
        assert ex.cost == pytest.approx(brute_cmst(D, dem, 2))


def test_mst_free_capacity_gives_the_mst_cost():
    for seed in range(30):
        D, dem = random_instance(5, 900 + seed)
        mst = A.mst_solution(D)
        top = max(A.branch_demand(b, dem) for b in mst.branches)
        assert A.exact_partition(D, dem, top).solution.cost == pytest.approx(mst.cost)


def test_tiny_instances():
    D0 = np.zeros((1, 1))
    assert A.exact_partition(D0, (0,), 3).solution.edges == [] and A.mst_solution(D0).edges == []
    D1 = np.array([[0.0, 4.0], [4.0, 0.0]])
    for cap in (1, 5, None):
        assert A.exact_partition(D1, (0, 1), cap).solution.cost == 4.0 and A.esau_williams(D1, (0, 1), cap).cost == 4.0 and A.capacitated_kruskal(D1, (0, 1), cap).cost == 4.0
    assert not A.exact_partition(D1, (0, 3), 2).feasible


def test_equal_costs_everywhere_and_demand_equal_to_capacity():
    n = 6
    D = np.ones((n, n)) - np.eye(n)
    dem = (0,) + (2,) * 5
    ex = A.exact_partition(D, dem, 2).solution
    assert ex.cost == 5.0 and ex.n_branches == 5
    ex3 = A.exact_partition(D, (0,) + (1,) * 5, 3).solution
    assert ex3.cost == 5.0 and all(A.branch_demand(b, (0,) + (1,) * 5) <= 3 for b in ex3.branches)


def test_collinear_customers_form_a_chain_branch():
    xy = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0]])
    D = np.abs(xy[:, None, 0] - xy[None, :, 0])
    dem = (0, 1, 1, 1, 1)
    for cap, cost in ((4, 4.0), (2, 1.0 + 1.0 + 3.0 + 1.0), (1, 1 + 2 + 3 + 4)):
        assert A.exact_partition(D, dem, cap).solution.cost == pytest.approx(cost)


# --- 6. Buchführung von Esau-Williams ---------------------------------------------------------------------------------------------------------


def test_esau_williams_savings_equal_cost_decreases_and_savings_are_positive():
    for seed in range(60):
        D, dem = random_instance(6, 1000 + seed, mixed=seed % 2 == 0)
        cap = 5 + seed % 3
        ew = A.esau_williams(D, dem, cap)
        cost = A.star_solution(D).cost
        for h in ew.history:
            assert h["saving"] > 0
            cost -= h["saving"]
            assert h["cost"] == pytest.approx(cost)
        assert ew.cost == pytest.approx(cost)
        assert len(ew.history) == D.shape[0] - 1 - ew.n_branches
        for h in ew.history:
            if h["blocked"] is not None:
                assert h["blocked"][2] > h["saving"]


def test_esau_williams_stops_only_when_no_feasible_positive_merge_is_left():
    for seed in range(50):
        D, dem = random_instance(6, 1500 + seed, mixed=seed % 2 == 1)
        cap = 5
        ew = A.esau_williams(D, dem, cap)
        gates = {}
        for b in ew.branches:
            g = [e[1] for e in ew.edges if e[0] == 0 and e[1] in b][0]
            gates[b] = D[0, g]
        for b1, b2 in combinations(ew.branches, 2):
            if A.branch_demand(b1, dem) + A.branch_demand(b2, dem) > cap:
                continue
            best = min(D[u, v] for u in b1 for v in b2)
            assert max(gates[b1], gates[b2]) - best <= 1e-9


def test_esau_williams_blocked_end_reports_a_real_capacity_conflict():
    D, dem = random_instance(6, 1, mixed=False)
    ew = A.esau_williams(D, dem, 2)
    if ew.blocked_end is not None:
        u, v, saving = ew.blocked_end
        bu = next(b for b in ew.branches if u in b)
        bv = next(b for b in ew.branches if v in b)
        assert bu != bv and A.branch_demand(bu, dem) + A.branch_demand(bv, dem) > 2 and saving > 0


# --- 7. Schwierige Fixtures (gegen Brute-Force bestätigt) -------------------------------------------------------------------------------------


def test_esau_williams_can_be_strictly_worse_than_exact():
    D, dem, cap = fixture("ew_worse")
    ref = brute_cmst(D, dem, cap)
    ex = A.exact_partition(D, dem, cap).solution
    ew = A.esau_williams(D, dem, cap)
    assert ref == pytest.approx(20.687) and ex.cost == pytest.approx(20.687) and ew.cost == pytest.approx(21.215)


def test_local_search_can_get_stuck_above_the_optimum():
    D, dem, cap = fixture("ls_stuck")
    ex = A.exact_partition(D, dem, cap).solution
    ew, ck = A.esau_williams(D, dem, cap), A.capacitated_kruskal(D, dem, cap)
    for start in (ew, ck):
        ls = A.local_search(start.branches, D, dem, cap)
        assert ls.cost == pytest.approx(21.215) and ls.cost > ex.cost + 0.5


def test_kruskal_can_be_strictly_worse_than_esau_williams():
    D, dem, cap = fixture("ck_worse_than_ew")
    ref = brute_cmst(D, dem, cap)
    ew, ck = A.esau_williams(D, dem, cap), A.capacitated_kruskal(D, dem, cap)
    assert ref == pytest.approx(24.076) and ew.cost == pytest.approx(24.076) and ck.cost == pytest.approx(26.319)


def test_kruskal_can_be_strictly_better_than_esau_williams():
    D, dem, cap = fixture("ck_better_than_ew")
    ex = A.exact_partition(D, dem, cap).solution
    ew, ck = A.esau_williams(D, dem, cap), A.capacitated_kruskal(D, dem, cap)
    assert ex.cost == pytest.approx(26.495) and ck.cost == pytest.approx(26.495) and ew.cost == pytest.approx(26.597)


def test_local_search_can_improve_esau_williams():
    D, dem, cap = fixture("ls_improves_ew")
    ew = A.esau_williams(D, dem, cap)
    ls = A.local_search(ew.branches, D, dem, cap)
    assert ew.cost == pytest.approx(25.709) and ls.cost == pytest.approx(25.128) and A.exact_partition(D, dem, cap).solution.cost == pytest.approx(25.128)


def test_cross_fixture_by_hand():
    t = S.textbook_instance()
    D, dem = t.D, t.demand
    assert A.mst_solution(D).cost == pytest.approx(80.0) and A.mst_solution(D).n_branches == 1
    r = 20.0 * math.sqrt(2)
    for cap, cost in ((1, 60 + 2 * r), (2, 40 + 2 * r), (3, 60 + r), (4, 80.0)):
        assert A.exact_partition(D, dem, cap).solution.cost == pytest.approx(cost)
