"""Orakel-Test jenseits der Brute-Force-Grenze (<= 5 Kunden): die exakte Mengenpartition gegen ein
unabhängiges CP-SAT-Modell (Elternbogen je Kunde + Ein-Gut-Fluss mit Kapazität Q auf jedem Bogen, also
ohne den Zweigsatz) bei 7 bis 9 Kunden mit ganzzahligen Kosten (viele Gleichstände); die Heuristiken
müssen gültige Bäume mit korrekter Kostenbuchführung liefern und dürfen nie unter dem Optimum liegen."""
import pytest

import cmst_algorithm as A
from brute import random_instance

cp_model = pytest.importorskip("ortools.sat.python.cp_model")


def _cpsat(D, demand, cap):
    n = D.shape[0]
    q = cap if cap is not None else sum(demand)
    m = cp_model.CpModel()
    x, f = {}, {}
    for u in range(1, n):
        for v in range(n):
            if u != v:
                x[u, v] = m.NewBoolVar(f"x{u}_{v}")
                f[u, v] = m.NewIntVar(0, q, f"f{u}_{v}")
                m.Add(f[u, v] <= q * x[u, v])
    for u in range(1, n):
        m.Add(sum(x[u, v] for v in range(n) if v != u) == 1)
        m.Add(sum(f[u, w] for w in range(n) if w != u) - sum(f[w, u] for w in range(1, n) if w != u) == demand[u])
    m.Minimize(sum(int(D[u, v]) * x[u, v] for (u, v) in x))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.Solve(m) == cp_model.OPTIMAL
    return solver.ObjectiveValue()


@pytest.mark.parametrize("seed", range(10))
def test_exact_partition_matches_cpsat_and_heuristics_are_valid_and_not_below_it(seed):
    nc = 7 + seed % 3
    D, demand = random_instance(nc, 500 + seed, mixed=seed % 2 == 1, integer=True)
    cap = (3, 4, 5, 6, 8, None)[seed % 6]
    if cap is not None:
        cap = max(cap, max(demand))
    exact = A.exact_partition(D, demand, cap)
    assert exact.feasible and exact.solution.cost == pytest.approx(_cpsat(D, demand, cap))
    n = D.shape[0]
    for sol in (A.capacitated_kruskal(D, demand, cap), A.esau_williams(D, demand, cap)):
        assert A.is_valid_tree(n, sol.edges, demand, cap)
        assert sol.cost == pytest.approx(sum(D[u, v] for u, v in sol.edges))
        assert sol.cost >= exact.solution.cost - 1e-9
        local = A.local_search(sol.branches, D, demand, cap)
        assert exact.solution.cost - 1e-9 <= local.cost <= A.reoptimize(sol, D).cost + 1e-9
