"""Auswertung: was ist die Kapazität am Depot wert, und wie gut sind die Verfahren?

Verfahren auf derselben Instanz: Stern (alle direkt ans Depot), MST (ohne Kapazität; nur zulässig, wenn seine Zweige passen), Kruskal mit Kapazität, Esau-Williams, Lokalsuche (auf den Zweigen von
Esau-Williams bzw. Kruskal, das bessere Ergebnis) und - für kleine Instanzen - exakt (Mengenpartition). Kosten sind die Summe der Kantenkosten des Baums. Alles ist deterministisch: Kennzahlen laufen über
5 feste Instanzen (Seeds 100000-100004), Median mit 10./90. Perzentil.

- **Preis der Kapazität** (`price_*`) = Kosten / MST-Kosten - 1 in Prozent: was die Kapazität gegenüber dem unbeschränkten MST kostet.
- **Aufschlag** (`excess_*`) = Kosten des Verfahrens / Kosten des besten gefundenen Baums - 1: die Lücke der Heuristik (bei kleinen Instanzen ist der beste Baum der exakte).
- **Ersparnis gegen den Stern** (`star_saving`) = 1 - Kosten des besten Baums / Sternkosten.
- **Zweige** = Teilbäume unter den Depotkanten (= Grad des Depots); **größter Zweig** in Bedarfseinheiten.
Die Kapazität `cap` ist in Bedarfseinheiten; 0 heißt unbegrenzt."""

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import cmst_algorithm as A
import cmst_constants as C
import cmst_scenario as S

INF = float("inf")


@dataclass(frozen=True)
class Settings:
    kind: str = "depot"
    n: int = C.DEFAULT_N
    demand_mode: str = "unit"
    depot: str = "edge"
    cap: int = C.DEFAULT_CAP
    terrain: float = C.DEFAULT_TERRAIN
    sats: int = C.DEFAULT_SATS
    seed: int = C.DEFAULT_SEED


@lru_cache(maxsize=256)
def instance_of(settings):
    if settings.kind == "textbook":
        return S.textbook_instance()
    return S.generate(settings.n, settings.terrain, settings.seed, settings.kind, settings.sats, settings.depot, settings.demand_mode)


def cap_value(settings):
    """Kapazität als Zahl oder None (unbegrenzt)."""
    return None if settings.cap == C.UNLIMITED else int(settings.cap)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    cap: object                        # int oder None
    star: object                       # Solution
    mst: object                        # Solution (ohne Kapazität)
    sols: dict                         # Name -> Solution oder None (Kruskal, EW, LS, exakt)
    infeasible: bool = False           # ein Kunde hat mehr Bedarf als die Kapazität
    exact_offered: bool = False
    exact_subsets: int = 0

    @property
    def D(self):
        return self.inst.D

    @property
    def demand(self):
        return self.inst.demand

    @property
    def mst_max_branch(self):
        return max((A.branch_demand(b, self.demand) for b in self.mst.branches), default=0)

    @property
    def mst_free(self):
        """Der MST erfüllt die Kapazität schon: dann kostet sie nichts."""
        return self.cap is None or self.mst_max_branch <= self.cap

    def solution(self, name):
        if name == "star":
            return None if self.infeasible else self.star
        if name == "mst":
            return self.mst if self.mst_free else None
        return self.sols.get(name)

    @property
    def best_name(self):
        if self.infeasible:
            return None
        cands = [(s.cost, n) for n in ("star", "mst", "kruskal", "ew", "ls", "exact") if (s := self.solution(n)) is not None]
        return min(cands, key=lambda t: (t[0], t[1]))[1] if cands else None

    @property
    def best(self):
        n = self.best_name
        return self.solution(n) if n else None

    @property
    def proved(self):
        return self.sols.get("exact") is not None

    def price(self, name):
        """Kosten des Verfahrens gegen den unbeschränkten MST in Prozent (None ohne Baum)."""
        s = self.solution(name)
        return None if s is None else 100.0 * (s.cost / self.mst.cost - 1.0)

    def excess(self, name):
        """Aufschlag gegen den besten gefundenen Baum in Prozent."""
        s, b = self.solution(name), self.best
        return None if s is None or b is None else 100.0 * (s.cost / b.cost - 1.0)

    @property
    def star_saving(self):
        b = self.best
        return None if b is None else 100.0 * (1.0 - b.cost / self.star.cost)

    def max_branch(self, name):
        s = self.solution(name)
        return None if s is None else max((A.branch_demand(b, self.demand) for b in s.branches), default=0)


def exact_offered(settings, inst):
    return inst.customers <= C.N_EXACT


def analyse(settings):
    inst = instance_of(settings)
    D, dem = inst.D, inst.demand
    cap = cap_value(settings)
    star, mst = A.star_solution(D), A.mst_solution(D)
    a = Analysis(settings, inst, cap, star, mst, {}, exact_offered=exact_offered(settings, inst))
    if cap is not None and inst.max_demand > cap:
        a.infeasible = True
        return a
    ck = A.capacitated_kruskal(D, dem, cap)
    ew = A.esau_williams(D, dem, cap)
    ls_a = A.local_search(ew.branches, D, dem, cap, "ls")
    ls_b = A.local_search(ck.branches, D, dem, cap, "ls")
    ls = min((ls_a, ls_b), key=lambda s: s.cost)
    a.sols = {"kruskal": ck, "ew": ew, "ls": ls}
    if a.exact_offered:
        ex = A.exact_partition(D, dem, cap)
        a.exact_subsets = ex.subsets
        a.sols["exact"] = ex.solution
    return a


# --- Kennzahlen über feste Instanzen ------------------------------------------------------------------------------------------------------------


def _stats(values):
    values = [v for v in values if v is not None and not np.isnan(v) and v != INF]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.percentile(values, 10)), float(np.percentile(values, 90))


def run_config(base, seeds=C.SWEEP_SEEDS, **changes):
    s0 = replace(base, **changes)
    rows = [analyse(replace(s0, seed=seed)) for seed in seeds]
    out = {"n_runs": len(rows), "infeasible_share": 100.0 * sum(r.infeasible for r in rows) / len(rows), "mst_free_share": 100.0 * sum((not r.infeasible) and r.mst_free for r in rows) / len(rows),
           "offered_share": 100.0 * sum(r.exact_offered for r in rows) / len(rows)}
    ok = [r for r in rows if not r.infeasible]
    out["ew_optimal_share"] = 100.0 * sum(1 for r in ok if r.excess("ew") is not None and r.excess("ew") <= 1e-9) / max(1, len(rows))
    out["kruskal_optimal_share"] = 100.0 * sum(1 for r in ok if r.excess("kruskal") is not None and r.excess("kruskal") <= 1e-9) / max(1, len(rows))
    out["ls_optimal_share"] = 100.0 * sum(1 for r in ok if r.excess("ls") is not None and r.excess("ls") <= 1e-9) / max(1, len(rows))
    cols = [("cost", [r.best.cost if r.best else None for r in rows]), ("mst_cost", [r.mst.cost for r in rows]), ("star_cost", [r.star.cost for r in rows]),
            ("price_best", [100.0 * (r.best.cost / r.mst.cost - 1.0) if r.best else None for r in rows]), ("star_saving", [r.star_saving for r in rows]),
            ("branches", [float(r.best.n_branches) if r.best else None for r in rows]), ("max_branch", [float(A.branch_demand(max(r.best.branches, key=lambda b: A.branch_demand(b, r.demand)), r.demand)) if r.best else None for r in rows]),
            ("mst_branches", [float(r.mst.n_branches) for r in rows]), ("mst_max_branch", [float(r.mst_max_branch) for r in rows])]
    for nm in ("kruskal", "ew", "ls"):
        cols.append((f"excess_{nm}", [r.excess(nm) for r in rows]))
        cols.append((f"price_{nm}", [r.price(nm) for r in rows]))
    cols.append(("price_exact", [r.price("exact") for r in rows]))
    cols.append(("gap_ew_exact", [100.0 * (r.sols["ew"].cost / r.sols["exact"].cost - 1.0) if r.proved else None for r in rows]))
    cols.append(("gap_kruskal_exact", [100.0 * (r.sols["kruskal"].cost / r.sols["exact"].cost - 1.0) if r.proved else None for r in rows]))
    cols.append(("gap_ls_exact", [100.0 * (r.sols["ls"].cost / r.sols["exact"].cost - 1.0) if r.proved else None for r in rows]))
    for key, values in cols:
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = _stats(values)
    return out


SWEEP_VALUES = {"cap": C.CAP_OPTIONS, "n": (8, 12, 14, 20, 30, 60), "depot": ("edge", "center"), "demand_mode": ("unit", "mixed"), "terrain": (0.0, 0.3, 0.6, 1.0), "sats": (3, 4, 5, 6, 8)}
SWEEP_LABELS = {"cap": "Kapazität Q", "n": "Kunden n", "depot": "Depotlage", "demand_mode": "Bedarf", "terrain": "Geländezuschlag", "sats": "Anschlüsse je Verteiler"}
SWEEP_TICKS = {"cap": lambda v: "∞" if v == C.UNLIMITED else str(v), "depot": lambda v: C.DEPOT_LABELS[v], "demand_mode": lambda v: C.DEMAND_LABELS[v]}


def sweep_params(kind):
    params = ["cap", "n", "depot", "demand_mode", "terrain"]
    if kind == "hubs":
        params.append("sats")
    return params


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def ew_quality(base, seeds=C.FEAS_SEEDS):
    """Wie gut ist Esau-Williams? Über `seeds` Instanzen mit den Einstellungen von `base` (nur der Seed wechselt): Anteil der Instanzen, in denen die Verfahren den besten Baum treffen, mittlere und größte Lücke von
    Esau-Williams, Anteil, in dem Kruskal mit Kapazität schlechter bzw. besser ist als Esau-Williams, Anteil, in dem die Lokalsuche Esau-Williams verbessert."""
    an = [analyse(replace(base, seed=seed)) for seed in seeds]
    an = [a for a in an if not a.infeasible]
    m = max(1, len(an))
    ex_ew = [a.excess("ew") for a in an]
    return {"n_runs": len(an), "exact_used": all(a.proved for a in an) and bool(an), "ew_optimal": 100.0 * sum(e <= 1e-9 for e in ex_ew) / m, "ew_gap_mean": float(np.mean(ex_ew)) if an else float("nan"),
            "ew_gap_max": float(max(ex_ew)) if an else float("nan"), "kruskal_worse": 100.0 * sum(a.sols["kruskal"].cost > a.sols["ew"].cost + 1e-9 for a in an) / m,
            "kruskal_better": 100.0 * sum(a.sols["kruskal"].cost < a.sols["ew"].cost - 1e-9 for a in an) / m, "ls_optimal": 100.0 * sum(a.excess("ls") <= 1e-9 for a in an) / m,
            "ls_improves": 100.0 * sum(a.sols["ls"].cost < a.sols["ew"].cost - 1e-9 for a in an) / m, "kruskal_optimal": 100.0 * sum(a.excess("kruskal") <= 1e-9 for a in an) / m,
            "mst_free": 100.0 * sum(a.mst_free for a in an) / m}


def capacity_curve(base, caps=None):
    """Kosten des besten Baums über die Kapazität für EINE Instanz (Seed und Einstellungen von `base`): je Kapazität Kosten, Zweige, Preis gegen den MST. Kapazitäten unter dem größten Einzelbedarf entfallen."""
    inst = instance_of(base)
    top = inst.total_demand
    caps = caps if caps is not None else sorted({c for c in range(inst.max_demand, min(top, 30) + 1)}) + [C.UNLIMITED]
    rows = []
    for c in caps:
        a = analyse(replace(base, cap=c))
        if a.infeasible or a.best is None:
            continue
        rows.append({"cap": c, "cost": a.best.cost, "branches": a.best.n_branches, "price": a.price(a.best_name), "mst_free": a.mst_free, "star": a.star.cost, "mst": a.mst.cost, "proved": a.proved})
    return rows
