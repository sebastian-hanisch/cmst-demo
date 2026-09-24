"""Die Instanz dieser Demo: ein Depot (Konzentrator, Werk) und n Kunden als Punkte auf einer Karte; gesucht wird ein Leitungsnetz, das alle verbindet - mit einer **Kapazität am Depot**: jeder
Zweig (Teilbaum unter einer Depotkante) darf höchstens Q Bedarfseinheiten tragen. Kantenkosten = Trassenlänge = euklidischer Abstand mal Geländefaktor u in [1, 1 + Zuschlag] (je Knotenpaar,
symmetrisch). Der Kandidatengraph ist **vollständig**: der exakte Weg braucht die billigsten Bäume auf beliebigen Kundenmengen.

Knoten 0 ist das Depot, die Kunden sind 1..n. Bedarf: einheitlich 1 oder gemischt (zufällig 1 bis 4, eigener Zufallsstrom je Seed). Layouts: gleichverteilt ("depot"), "Ortschaften" ("hubs": Verteiler mit
`sats` Anschlussnehmern im Kreis - dort liegt ein Zweig je Ortschaft nahe), und ein handgebautes Lehrbuchbeispiel (Kreuz aus vier Kunden, Depot links)."""

import math
from dataclasses import dataclass

import numpy as np

import cmst_constants as C

INSTANCE_KINDS = C.KINDS


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (N, 2), Knoten 0 = Depot
    D: np.ndarray                  # (N, N) symmetrische Kostenmatrix, Diagonale 0
    demand: tuple                  # Länge N, demand[0] = 0
    kind: str = "depot"
    terrain: float = 0.0
    seed: int = 0
    sats: int = 0
    depot: str = "edge"
    demand_mode: str = "unit"
    labels: object = None          # Knotennamen der Fixtures

    @property
    def n(self):
        """Zahl der Knoten inklusive Depot."""
        return len(self.xy)

    @property
    def customers(self):
        return self.n - 1

    @property
    def total_demand(self):
        return int(sum(self.demand))

    @property
    def max_demand(self):
        return int(max(self.demand[1:], default=0))


def _hub_points(n_customers, sats, seed):
    """Verteiler mit `sats` Anschlussnehmern im Kreis (Radius ~6); Verteiler mit Mindestabstand zufällig auf der Fläche. Genau `n_customers` Punkte (der letzte Verteiler ggf. mit weniger)."""
    rng = np.random.default_rng([int(seed), 910])
    n_hubs = max(1, -(-int(n_customers) // (sats + 1)))
    centers = []
    min_d = 24.0
    tries = 0
    while len(centers) < n_hubs:
        c = rng.uniform(12.0, C.AREA - 12.0, size=2)
        tries += 1
        if all(np.hypot(*(c - o)) >= min_d for o in centers) or tries > 500:
            centers.append(c)
        if tries > 500:
            min_d = 0.0
    pts = []
    for c in centers:
        pts.append(c)
        phase = rng.uniform(0.0, 2.0 * math.pi)
        for j in range(sats):
            ang = phase + 2.0 * math.pi * j / sats + rng.uniform(-0.15, 0.15)
            r = 6.0 * rng.uniform(0.9, 1.1)
            pts.append(c + r * np.array([math.cos(ang), math.sin(ang)]))
    return np.array(pts[: int(n_customers)])


def _cost_matrix(xy, terrain, rng):
    n = len(xy)
    factor = rng.uniform(1.0, 1.0 + float(terrain), size=(n, n))
    factor = np.triu(factor, 1) + np.triu(factor, 1).T
    diff = xy[:, None, :] - xy[None, :, :]
    dist = np.hypot(diff[:, :, 0], diff[:, :, 1])
    D = dist * np.where(factor > 0, factor, 1.0)
    np.fill_diagonal(D, 0.0)
    return D


def generate(n_customers=C.DEFAULT_N, terrain=C.DEFAULT_TERRAIN, seed=C.DEFAULT_SEED, kind="depot", sats=C.DEFAULT_SATS, depot="edge", demand_mode="unit"):
    """Depot + `n_customers` Kunden; Knoten 0 ist das Depot."""
    if kind not in ("depot", "hubs"):
        raise ValueError(f"unbekanntes Layout {kind}")
    if depot not in C.DEPOT_POS:
        raise ValueError(f"unbekannte Depotlage {depot}")
    if demand_mode not in C.DEMAND_MODES:
        raise ValueError(f"unbekannter Bedarf {demand_mode}")
    n_c = int(n_customers)
    rng = np.random.default_rng([int(seed), 909])
    if kind == "depot":
        pts = rng.uniform(0.0, C.AREA, size=(n_c, 2))
    else:
        pts = _hub_points(n_c, int(sats), seed)
    xy = np.vstack([np.array([C.DEPOT_POS[depot]]), pts])
    D = _cost_matrix(xy, terrain, rng)
    if demand_mode == "unit":
        demand = (0,) + (1,) * n_c
    else:
        dem_rng = np.random.default_rng([int(seed), 707])
        demand = (0,) + tuple(int(x) for x in dem_rng.integers(1, C.DEMAND_MAX + 1, size=n_c))
    return Instance(xy, D, demand, kind, float(terrain), int(seed), int(sats) if kind == "hubs" else 0, depot, demand_mode)


# --- Handgebautes Lehrbuchbeispiel ----------------------------------------------------------------------------------------------------------------

TEXTBOOK_XY = [(20.0, 50.0), (40.0, 50.0), (60.0, 50.0), (40.0, 70.0), (40.0, 30.0)]


def textbook_instance():
    """Kreuz aus vier Kunden, Depot W links, Bedarf je 1: C (Mitte), E, N, S. Ohne Kapazität ist der MST der Stern um C (Kosten 80, ein Zweig mit 4 Kunden). Q = 3: S hängt stattdessen direkt am Depot (88.28);
    Q = 2: zwei Zweige zu je zwei Kunden (96.57); Q = 1: Stern ab Depot (116.57)."""
    xy = np.array(TEXTBOOK_XY)
    diff = xy[:, None, :] - xy[None, :, :]
    D = np.hypot(diff[:, :, 0], diff[:, :, 1])
    return Instance(xy, D, (0, 1, 1, 1, 1), "textbook", labels=("W", "C", "E", "N", "S"))
