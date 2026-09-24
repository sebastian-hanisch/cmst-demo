"""Per Skriptsuche gefundene kleine Instanzen (fest verdrahtet): Kostenmatrix als obere Dreiecke (Knoten 0 = Depot), Bedarf, Kapazität. Gegen Brute-Force über alle Bäume bestätigt."""

import numpy as np


def _matrix(upper, n):
    D = np.zeros((n, n))
    it = iter(upper)
    for u in range(n):
        for v in range(u + 1, n):
            D[u, v] = D[v, u] = next(it)
    return D


FIXTURES = {
    "ck_worse_than_ew": dict(cap=2, demand=(0, 1, 1, 1, 1, 1), upper=[7.621, 8.725, 6.299, 4.973, 7.796, 9.027, 2.551, 2.464, 2.204, 9.958, 8.431, 2.544, 2.796, 6.857, 9.422]),
    "ew_worse": dict(cap=2, demand=(0, 1, 1, 1, 1, 1, 1), upper=[7.777, 5.76, 5.323, 4.329, 2.78, 1.584, 1.639, 1.986, 5.771, 3.702, 2.33, 5.819, 8.774, 4.685, 5.245, 8.11, 9.889, 6.235, 4.129, 9.178, 6.34]),
    "ls_stuck": dict(cap=2, demand=(0, 1, 1, 1, 1, 1, 1), upper=[7.777, 5.76, 5.323, 4.329, 2.78, 1.584, 1.639, 1.986, 5.771, 3.702, 2.33, 5.819, 8.774, 4.685, 5.245, 8.11, 9.889, 6.235, 4.129, 9.178, 6.34]),
    "ck_better_than_ew": dict(cap=4, demand=(0, 2, 2, 2, 1, 3, 3), upper=[2.531, 7.459, 3.869, 4.334, 5.104, 4.475, 7.856, 8.919, 3.706, 7.067, 3.294, 6.81, 6.284, 8.105, 6.024, 4.046, 7.066, 5.847, 7.496, 8.402, 6.874]),
    "ls_improves_ew": dict(cap=5, demand=(0, 2, 2, 2, 1, 3, 3), upper=[2.531, 7.459, 3.869, 4.334, 5.104, 4.475, 7.856, 8.919, 3.706, 7.067, 3.294, 6.81, 6.284, 8.105, 6.024, 4.046, 7.066, 5.847, 7.496, 8.402, 6.874]),
}


def fixture(name):
    f = FIXTURES[name]
    n = len(f["demand"])
    return _matrix(f["upper"], n), f["demand"], f["cap"]
