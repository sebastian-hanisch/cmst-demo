"""Konstanten der Demo zum kapazitierten Spannbaum: Instanz-Geometrie, Regler, gemessene Werte, Presets."""
AREA = 100.0
DEPOT_POS = {"edge": (15.0, 50.0), "center": (50.0, 50.0)}
DEPOT_LABELS = {"edge": "am Rand", "center": "in der Mitte"}
N_MIN, N_MAX, DEFAULT_N, N_STEP = 5, 60, 12, 1
TERRAIN_MIN, TERRAIN_MAX, DEFAULT_TERRAIN = 0.0, 1.0, 0.0
TERRAIN_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0)
SEED_MAX = 999999
DEFAULT_SEED = 35
SATS_MIN, SATS_MAX, DEFAULT_SATS = 3, 8, 5
KINDS = ("depot", "hubs", "textbook")
KIND_LABELS = {"depot": "Depot und Kunden (Karte)", "hubs": "Ortschaften (Verteiler mit Anschlüssen)", "textbook": "Lehrbuchbeispiel (Kreuz, 4 Kunden)"}
DEMAND_MODES = ("unit", "mixed")
DEMAND_LABELS = {"unit": "einheitlich (1)", "mixed": "gemischt (1 bis 4)"}
DEMAND_MAX = 4
UNLIMITED = 0
CAP_OPTIONS = (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, UNLIMITED)
DEFAULT_CAP = 4
SWEEP_SEEDS = tuple(range(100000, 100005))
FEAS_SEEDS = tuple(range(200000, 200050))
N_EXACT = 14
TREE_OPTIONS = ("best", "ew", "kruskal", "ls", "exact", "star", "mst")
ALL_TREES = TREE_OPTIONS
TREE_LABELS = {"best": "Bester Fund", "ew": "Esau-Williams", "kruskal": "Kruskal mit Kapazität", "ls": "Lokalsuche", "exact": "Exakt", "star": "Stern", "mst": "MST (ohne Kapazität)"}
DEFAULT_TREE = "best"

_BASE = {"kind": "depot", "n": 12, "cap": 4, "demand_mode": "unit", "depot": "edge", "terrain": 0.0, "sats": 5, "seed": 35, "tree": "best"}
PRESETS = {
    "Standardfall (Voreinstellung)": dict(_BASE),
    "Kapazität 2": {**_BASE, "cap": 2},
    "Stern (Kapazität 1)": {**_BASE, "cap": 1},
    "Kapazität kostenlos (Q = 10)": {**_BASE, "cap": 10, "tree": "mst"},
    "Depot in der Mitte": {**_BASE, "depot": "center", "tree": "ls"},
    "Kruskal schlägt Esau-Williams": {**_BASE, "seed": 11, "tree": "ew"},
    "Ortschaften (Q = 5)": {**_BASE, "kind": "hubs", "n": 14, "cap": 5},
    "Lehrbuchbeispiel (Q = 3)": {**_BASE, "kind": "textbook", "cap": 3},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "12 Kunden, Depot am Rand, Bedarf 1, Q = 4, Seed 35: der MST (215.65) hat zwei Zweige mit 2 und 10 Kunden - der große verletzt Q. Der beste kapazitierte Baum kostet 262.60 (+21.77 %) mit 4 Zweigen (Bedarf 2/4/3/3); Kruskal mit Kapazität, Esau-Williams, Lokalsuche und exakt finden hier denselben. Gegen den Stern (555.17) spart er 52.7 %.",
    "Kapazität 2": "Q = 2 (polynomiell lösbar, ein Matching): 7 Zweige, Kosten 358.88 (+66.42 %). Esau-Williams, Lokalsuche und exakt finden dasselbe, Kruskal mit Kapazität liegt 4.70 % darüber (375.75).",
    "Stern (Kapazität 1)": "Q = 1: jeder Kunde einzeln am Depot, Kosten 555.17 = Stern (+157.44 % gegen den MST), 12 Zweige. Alle Verfahren finden dasselbe - ohne Spielraum gibt es keinen Unterschied.",
    "Kapazität kostenlos (Q = 10)": "Der MST (215.65) hat zwei Zweige mit 2 und 10 Kunden - Q = 10 kostet nichts (+0.00 %). Schon Q = 9 kostet +3.93 %, Q = 8 +8.26 %.",
    "Depot in der Mitte": "Depot in der Mitte: der MST (225.43) ist ein einziger Zweig mit 12 Kunden. Das exakte Optimum kostet 264.51 (3 Zweige zu je 4 Kunden, +17.34 %); Esau-Williams und die Lokalsuche stecken bei 277.77 (+5.01 % über dem Optimum), Kruskal mit Kapazität bei 280.15 (+5.91 %).",
    "Kruskal schlägt Esau-Williams": "Seed 11: Esau-Williams 310.64 (+9.59 % über dem Optimum 283.45), Kruskal mit Kapazität nur 289.02 (+1.96 %); die Lokalsuche findet das Optimum 283.45. Esau-Williams ist nicht in jedem Fall die bessere Heuristik.",
    "Ortschaften (Q = 5)": "14 Kunden in Ortschaften, Q = 5: MST 155.13 (zwei Zweige mit Bedarf 7), bester Baum 238.88 (+53.98 %) mit 4 Zweigen (Bedarf 5/2/5/2); Kruskal mit Kapazität liegt 0.93 % darüber. Über 50 Instanzen trifft Esau-Williams in Ortschaften nur in 6 % der Fälle den besten Baum.",
    "Lehrbuchbeispiel (Q = 3)": "Vier Kunden im Kreuz: der MST (80) ist ein einziger Zweig mit 4 Kunden. Q = 3 kostet 88.28 (+10.36 %), Q = 2 kostet 96.57 (+20.71 %), Q = 1 kostet 116.57 (+45.71 %).",
}
# Beobachtete Spannweite der Kennzahl (MEDIAN über die 5 festen Instanzen Seeds 100000-100004) je Preset, mit Sicherheitsabstand: (Kennzahl, untere, obere Grenze).
PRESET_EXPECTED_BANDS = {
    "Standardfall (Voreinstellung)": ("price_best", 10.0, 17.0),
    "Kapazität 2": ("price_best", 40.0, 55.0),
    "Stern (Kapazität 1)": ("price_best", 110.0, 160.0),
    "Kapazität kostenlos (Q = 10)": ("price_best", -0.01, 0.5),
    "Depot in der Mitte": ("price_best", 4.0, 10.0),
    "Kruskal schlägt Esau-Williams": ("price_best", 10.0, 17.0),
    "Ortschaften (Q = 5)": ("price_best", 50.0, 70.0),
}
