"""Kapazitierter minimaler Spannbaum (CMST): ein Depot (Knoten 0), n Kunden mit Bedarf, jeder Zweig - jeder Teilbaum unter einer Depotkante - darf höchstens Q Bedarfseinheiten tragen.
Q = unbegrenzt ist der MST, Q = 1 (bei Einheitsbedarf) der Stern; dazwischen ist das Problem NP-schwer (Papadimitriou 1978).

**Zweigsatz:** Das Depot ist in einem Zweig ein Blatt. Entfernt man es, bleibt ein Baum auf den Kunden S des Zweigs; der billigste ist der MST von S, dazu kommt die billigste Depotkante zu einem Kunden von S:
`branch_cost(S) = MST(S) + min_{v in S} c(0, v)`. Damit ist der CMST eine **Mengenpartition** der Kunden in Zweige mit Bedarf <= Q und minimalen Summenkosten - der exakte Weg (`exact_partition`, dynamische
Programmierung über Teilmengen) braucht keinen Löser.

Verfahren: Kruskal mit Kapazität (naive Antwort), **Esau-Williams** (1966: beginne mit dem Stern; verschmelze die zwei Zweige mit der größten Ersparnis "teurere Depotkante minus neue Kante", solange der
vereinigte Bedarf passt), Neu-Optimierung je Zweig und eine Lokalsuche über Umhängen, Tauschen und Zusammenlegen von Zweigen. Alle deterministisch (Schlüssel: Kosten bzw. Ersparnis, dann Knotenindizes)."""

import math
from dataclasses import dataclass, field

import numpy as np

from cmst_unionfind import UnionFind

EPS = 1e-9


# --- Kosten und Bäume auf Kundenmengen ------------------------------------------------------------------------------------------------------------


def mst_edges(idx, D):
    """Kanten (a, b) mit a < b eines MST auf den Knoten `idx` (Prim, numpy); leer für weniger als zwei Knoten."""
    idx = list(idx)
    k = len(idx)
    if k <= 1:
        return []
    sub = D[np.ix_(idx, idx)]
    dist = sub[0].copy()
    src = np.zeros(k, dtype=int)
    used = np.zeros(k, dtype=bool)
    used[0] = True
    out = []
    for _ in range(k - 1):
        masked = np.where(used, np.inf, dist)
        j = int(np.argmin(masked))
        a, b = idx[int(src[j])], idx[j]
        out.append((min(a, b), max(a, b)))
        used[j] = True
        better = sub[j] < dist
        dist = np.where(better, sub[j], dist)
        src = np.where(better, j, src)
    return out


def mst_cost(idx, D):
    return math.fsum(D[a, b] for a, b in mst_edges(idx, D))


def gate_of(S, D):
    """Der Kunde in S mit der billigsten Depotkante (Gleichstand: kleinster Index)."""
    return min(S, key=lambda v: (D[0, v], v))


def branch_cost(S, D):
    """Kosten des billigsten Zweigs über der Kundenmenge S: MST(S) plus billigste Depotkante (Zweigsatz)."""
    S = tuple(S)
    return mst_cost(S, D) + float(D[0, gate_of(S, D)])


def branch_edges(S, D):
    S = tuple(S)
    return mst_edges(S, D) + [(0, gate_of(S, D))]


def edges_cost(edges, D):
    return math.fsum(D[u, v] for u, v in edges)


def branches_of(n_nodes, edges):
    """Zweige einer Kantenmenge: die Zusammenhangskomponenten der Kunden ohne das Depot, jeder als sortiertes Tupel, sortiert nach kleinstem Kunden."""
    uf = UnionFind(n_nodes, "full")
    for u, v in edges:
        if u != 0 and v != 0:
            uf.union(u, v)
    groups = {}
    for v in range(1, n_nodes):
        groups.setdefault(uf.find(v), []).append(v)
    return sorted(tuple(g) for g in groups.values())


def branch_demand(branch, demand):
    return int(sum(demand[v] for v in branch))


def is_valid_tree(n_nodes, edges, demand, cap):
    """n - 1 verschiedene Kanten, die alle Knoten zusammenhängend verbinden, und jeder Zweig hat Bedarf <= cap (cap = None: unbegrenzt)."""
    if len(edges) != max(n_nodes - 1, 0) or len(set(edges)) != len(edges):
        return False
    uf = UnionFind(n_nodes, "full")
    if not all(uf.union(u, v) for u, v in edges):
        return False
    if cap is None:
        return True
    return all(branch_demand(b, demand) <= cap for b in branches_of(n_nodes, edges))


@dataclass
class Solution:
    method: str
    edges: list                                    # (u, v) mit u < v, n - 1 Kanten inklusive Depotkanten
    cost: float
    branches: list                                 # sortierte Tupel von Kunden
    history: list = field(default_factory=list)    # nur Esau-Williams: ein Eintrag je Verschmelzung
    blocked_end: object = None                     # nur Esau-Williams: beste am Ende wegen der Kapazität unzulässige Verschmelzung (u, v, Ersparnis) oder None

    @property
    def n_branches(self):
        return len(self.branches)


def make_solution(method, edges, D, history=None):
    edges = sorted((min(u, v), max(u, v)) for u, v in edges)
    return Solution(method, edges, edges_cost(edges, D), branches_of(D.shape[0], edges), list(history or []))


def solution_from_branches(method, branches, D, history=None):
    edges = []
    for b in branches:
        edges += branch_edges(b, D)
    return make_solution(method, edges, D, history)


def _check_capacity(demand, cap):
    if cap is not None and any(d > cap for d in demand[1:]):
        raise ValueError("ein Kunde hat mehr Bedarf als die Kapazität")


# --- Referenzen: Stern und MST --------------------------------------------------------------------------------------------------------------------


def star_solution(D):
    return make_solution("star", [(0, v) for v in range(1, D.shape[0])], D)


def mst_solution(D):
    """MST über Depot und alle Kunden ohne Kapazität (Kruskal, Schlüssel (Kosten, Index)); Untergrenze der Kosten jeder Kapazität."""
    n = D.shape[0]
    pairs = [(D[u, v], u, v) for u in range(n) for v in range(u + 1, n)]
    pairs.sort(key=lambda t: (t[0], t[1], t[2]))
    uf = UnionFind(n, "full")
    edges = [(u, v) for _w, u, v in pairs if uf.union(u, v)]
    return make_solution("mst", edges, D)


# --- Kruskal mit Kapazität ------------------------------------------------------------------------------------------------------------------------


def capacitated_kruskal(D, demand, cap):
    """Alle Kanten (auch Depotkanten) nach (Kosten, Index): eine Kundenkante wird genommen, wenn sie zwei Komponenten verbindet und der vereinigte Bedarf <= cap ist und nicht beide bereits
    am Depot hängen; eine Depotkante, wenn die Komponente noch nicht am Depot hängt. Findet immer einen Baum (jeder Kunde passt allein)."""
    n = D.shape[0]
    _check_capacity(demand, cap)
    pairs = [(D[u, v], u, v) for u in range(n) for v in range(u + 1, n)]
    pairs.sort(key=lambda t: (t[0], t[1], t[2]))
    uf = UnionFind(n, "full")
    dem = {v: demand[v] for v in range(1, n)}
    gated = {v: False for v in range(1, n)}
    edges = []
    for _w, u, v in pairs:
        if u == 0:
            r = uf.find(v)
            if not gated[r]:
                gated[r] = True
                edges.append((0, v))
            continue
        ru, rv = uf.find(u), uf.find(v)
        if ru == rv or (gated[ru] and gated[rv]):
            continue
        if cap is not None and dem[ru] + dem[rv] > cap:
            continue
        uf.union(u, v)
        r = uf.find(u)
        dem[r] = dem[ru] + dem[rv]
        gated[r] = gated[ru] or gated[rv]
        edges.append((u, v))
    return make_solution("kruskal", edges, D)


# --- Esau-Williams --------------------------------------------------------------------------------------------------------------------------------


def esau_williams(D, demand, cap):
    """Esau-Williams (1966). Start: Stern, jeder Kunde eine Komponente mit Depotkante c(0, g). Ersparnis der Verschmelzung zweier Komponenten A, B über die billigste Kante (u, v) zwischen ihnen:
    max(w_A, w_B) - c(u, v), wobei w die Kosten der Depotkante der Komponente sind (die teurere entfällt, die billigere bleibt). Wiederholt die Verschmelzung mit der größten positiven Ersparnis, deren
    vereinigter Bedarf <= cap ist (Gleichstand: kleinste Knotenindizes), bis keine mehr übrig ist.
    `history`: je Schritt (u, v, Ersparnis, Kosten danach, weggefallene Depotkante, "blockiert": die beste Verschmelzung mit größerer Ersparnis, die wegen der Kapazität nicht passte, oder None)."""
    n = D.shape[0]
    _check_capacity(demand, cap)
    members = {v: [v] for v in range(1, n)}
    gate = {v: v for v in range(1, n)}
    dem = {v: demand[v] for v in range(1, n)}
    link = {a: {b: (float(D[a, b]), a, b) for b in range(1, n) if b != a} for a in range(1, n)}
    edges = [(0, v) for v in range(1, n)]
    cost = edges_cost(edges, D)
    history = []
    while True:
        best, blocked = None, None
        ids = sorted(members)
        for i, a in enumerate(ids):
            wa = D[0, gate[a]]
            for b in ids[i + 1:]:
                dmin, u, v = link[a][b]
                saving = max(wa, D[0, gate[b]]) - dmin
                if saving <= EPS:
                    continue
                key = (-saving, u, v)
                if cap is not None and dem[a] + dem[b] > cap:
                    if blocked is None or key < blocked[0]:
                        blocked = (key, u, v, saving)
                elif best is None or key < best[0]:
                    best = (key, a, b, u, v, saving)
        if best is None:
            break
        _key, a, b, u, v, saving = best
        drop = b if D[0, gate[b]] >= D[0, gate[a]] else a
        keep = a if drop == b else b
        edges.remove((0, gate[drop]))
        edges.append((min(u, v), max(u, v)))
        cost = cost - saving
        hist_block = None if blocked is None or blocked[3] <= saving + EPS else (blocked[1], blocked[2], blocked[3])
        history.append({"u": u, "v": v, "saving": float(saving), "cost": float(cost), "dropped": (0, gate[drop]), "blocked": hist_block})
        gate[a] = gate[keep]
        members[a] = members[a] + members.pop(b)
        dem[a] += dem.pop(b)
        gate.pop(b)
        del link[a][b]
        del link[b][a]
        for c in list(link[b]):
            other = link[b].pop(c)
            del link[c][b]
            cur = link[a].get(c)
            if cur is None or (other[0], other[1], other[2]) < cur:
                link[a][c] = other
                link[c][a] = other
        del link[b]
    sol = make_solution("ew", edges, D, history)
    sol.blocked_end = None if blocked is None else (blocked[1], blocked[2], float(blocked[3]))
    return sol


# --- Neu-Optimierung und Lokalsuche ---------------------------------------------------------------------------------------------------------------


def reoptimize(solution, D):
    """Jeden Zweig neu bauen: MST(S) plus billigste Depotkante. Nie schlechter (Zweigsatz)."""
    return solution_from_branches(solution.method + "+reopt", solution.branches, D)


def local_search(branches, D, demand, cap, method="ls"):
    """Lokalsuche auf der Zweigpartition: einen Kunden in einen anderen (oder einen neuen) Zweig umhängen, zwei Kunden aus verschiedenen Zweigen tauschen, zwei Zweige zusammenlegen; jede Änderung mit den
    exakten Zweigkosten (Zweigsatz) bewertet, beste Verbesserung je Runde, streng fallende Kosten. Gibt eine `Solution` zurück (Zweige neu gebaut)."""
    cache = {}

    def bc(S):
        key = tuple(sorted(S))
        if not key:
            return 0.0
        if key not in cache:
            cache[key] = branch_cost(key, D)
        return cache[key]

    cur = [tuple(sorted(b)) for b in branches]
    while True:
        costs = [bc(b) for b in cur]
        dem = [branch_demand(b, demand) for b in cur]
        m = len(cur)
        best = None
        for i in range(m):
            for v in cur[i]:
                rest = tuple(x for x in cur[i] if x != v)
                rest_cost = bc(rest)
                for j in range(m + 1):
                    if j == i:
                        continue
                    target = cur[j] if j < m else ()
                    if (dem[j] if j < m else 0) + demand[v] > (cap if cap is not None else math.inf):
                        continue
                    delta = rest_cost + bc(target + (v,)) - costs[i] - (costs[j] if j < m else 0.0)
                    if delta < -EPS and (best is None or delta < best[0] - EPS):
                        best = (delta, ("move", i, v, j))
        for i in range(m):
            for j in range(i + 1, m):
                if dem[i] + dem[j] <= (cap if cap is not None else math.inf):
                    delta = bc(cur[i] + cur[j]) - costs[i] - costs[j]
                    if delta < -EPS and (best is None or delta < best[0] - EPS):
                        best = (delta, ("merge", i, j))
                for v in cur[i]:
                    for w in cur[j]:
                        if dem[i] - demand[v] + demand[w] > (cap if cap is not None else math.inf) or dem[j] - demand[w] + demand[v] > (cap if cap is not None else math.inf):
                            continue
                        ni = tuple(x for x in cur[i] if x != v) + (w,)
                        nj = tuple(x for x in cur[j] if x != w) + (v,)
                        delta = bc(ni) + bc(nj) - costs[i] - costs[j]
                        if delta < -EPS and (best is None or delta < best[0] - EPS):
                            best = (delta, ("swap", i, v, j, w))
        if best is None:
            return solution_from_branches(method, cur, D)
        move = best[1]
        if move[0] == "move":
            _k, i, v, j = move
            new = [tuple(sorted(x for x in b if not (k == i and x == v))) for k, b in enumerate(cur)]
            if j == m:
                new.append((v,))
            else:
                new[j] = tuple(sorted(new[j] + (v,)))
        elif move[0] == "merge":
            _k, i, j = move
            new = [b for k, b in enumerate(cur) if k not in (i, j)] + [tuple(sorted(cur[i] + cur[j]))]
        else:
            _k, i, v, j, w = move
            new = list(cur)
            new[i] = tuple(sorted([x for x in cur[i] if x != v] + [w]))
            new[j] = tuple(sorted([x for x in cur[j] if x != w] + [v]))
        cur = sorted(b for b in new if b)


# --- Exakt: Mengenpartition -----------------------------------------------------------------------------------------------------------------------


@dataclass
class ExactResult:
    solution: object                               # Solution oder None
    feasible: bool
    subsets: int = 0                               # zulässige Zweig-Kandidaten (Bedarf <= cap)


def exact_partition(D, demand, cap):
    """Exakter CMST über die Mengenpartition: cost[S] = Zweigkosten (Zweigsatz) für jede Kundenmenge S mit Bedarf <= cap; f[M] = kleinste Kosten, M in Zweige zu zerlegen (S enthält das niedrigste
    Bit von M). O(3^n) - nur für kleine n. Gibt eine `ExactResult`; nicht lösbar, wenn ein Kunde mehr Bedarf als cap hat."""
    n = D.shape[0] - 1
    if n == 0:
        return ExactResult(make_solution("exact", [], D), True, 0)
    if cap is not None and any(d > cap for d in demand[1:]):
        return ExactResult(None, False, 0)
    full = (1 << n) - 1
    dsum = [0] * (full + 1)
    cost = [math.inf] * (full + 1)
    count = 0
    for m in range(1, full + 1):
        low = (m & -m).bit_length() - 1
        dsum[m] = dsum[m & (m - 1)] + demand[low + 1]
        if cap is None or dsum[m] <= cap:
            cost[m] = branch_cost([i + 1 for i in range(n) if m >> i & 1], D)
            count += 1
    f = [math.inf] * (full + 1)
    choice = [0] * (full + 1)
    f[0] = 0.0
    for m in range(1, full + 1):
        low = m & -m
        rest = m ^ low
        s = rest
        best, pick = math.inf, 0
        while True:
            S = s | low
            c = cost[S]
            if c < math.inf:
                val = c + f[m ^ S]
                if val < best - 1e-12:
                    best, pick = val, S
            if s == 0:
                break
            s = (s - 1) & rest
        f[m], choice[m] = best, pick
    branches, m = [], full
    while m:
        S = choice[m]
        branches.append(tuple(i + 1 for i in range(n) if S >> i & 1))
        m ^= S
    return ExactResult(solution_from_branches("exact", sorted(branches), D), True, count)
