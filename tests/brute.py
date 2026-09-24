"""Referenzen nur für die Tests: alle Bäume über Prüfer-Folgen aufzählen, Zufalls-Instanzen erzeugen."""

import heapq
from itertools import product

import numpy as np

import cmst_algorithm as A


def prufer_to_edges(seq, n):
    """Kanten (u < v) des beschrifteten Baums auf den Knoten 0..n-1 zur Prüfer-Folge `seq` (Länge n - 2)."""
    degree = [1] * n
    for x in seq:
        degree[x] += 1
    leaves = [i for i in range(n) if degree[i] == 1]
    heapq.heapify(leaves)
    edges = []
    for x in seq:
        leaf = heapq.heappop(leaves)
        edges.append((min(leaf, x), max(leaf, x)))
        degree[x] -= 1
        if degree[x] == 1:
            heapq.heappush(leaves, x)
    a, b = heapq.heappop(leaves), heapq.heappop(leaves)
    edges.append((min(a, b), max(a, b)))
    return edges


def all_trees(n):
    """Alle n^(n-2) beschrifteten Bäume auf 0..n-1 (nur für n <= 7)."""
    if n == 2:
        yield [(0, 1)]
        return
    for seq in product(range(n), repeat=n - 2):
        yield prufer_to_edges(seq, n)


def random_instance(n_customers, seed, mixed=False, integer=False):
    """Zufallsinstanz mit vollständiger Kostenmatrix (Knoten 0 = Depot); ganzzahlige Kosten 1..6 erzeugen Gleichstände."""
    rng = np.random.default_rng([seed, 31337])
    n = n_customers + 1
    upper = rng.integers(1, 7, size=(n, n)).astype(float) if integer else np.round(rng.uniform(1, 10, size=(n, n)), 3)
    D = np.triu(upper, 1)
    D = D + D.T
    demand = (0,) + tuple(int(x) for x in (rng.integers(1, 5, size=n_customers) if mixed else np.ones(n_customers, dtype=int)))
    return D, demand


def brute_cmst(D, demand, cap):
    """Kleinste Kosten über ALLE Spannbäume mit Zweigbedarf <= cap (None, wenn keiner)."""
    n = D.shape[0]
    best = None
    for edges in all_trees(n):
        if A.is_valid_tree(n, edges, demand, cap):
            c = A.edges_cost(edges, D)
            if best is None or c < best - 1e-9:
                best = c
    return best
