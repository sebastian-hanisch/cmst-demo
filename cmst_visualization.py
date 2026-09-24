"""Plotly-Abbildungen: Karte mit Zweigen (Farbe je Zweig, Punktgröße = Bedarf), Esau-Williams Schritt für Schritt, Kosten-Balken, Kapazitätskurve, Sweeps.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import cmst_algorithm as A

BAD_COLOR = "#d62728"
DIFF_COLOR = "#ff7f0e"
MISS_COLOR = "rgba(120,120,120,0.6)"
METHOD_COLORS = {"star": "#8c8c8c", "mst": "#7b3fbf", "kruskal": "#4c78a8", "ew": "#e8a13a", "ls": "#d95f9b", "exact": "#2F6B65"}
METHOD_LABELS = {"star": "Stern", "mst": "MST (ohne Kapazität)", "kruskal": "Kruskal mit Kapazität", "ew": "Esau-Williams", "ls": "Lokalsuche", "exact": "Exakt"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.1):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_axes(fig, height=460):
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height)


def _height(inst):
    return 340 if inst.kind == "textbook" else 460


def _branch_color(i):
    return f"hsl({(i * 137 + 20) % 360},58%,42%)"


def _lines(fig, inst, pairs, color, width=2.6, dash="solid", name="", showlegend=False):
    pairs = list(pairs)
    if not pairs:
        return
    xs, ys = [], []
    for u, v in pairs:
        xs += [inst.xy[u][0], inst.xy[v][0], None]
        ys += [inst.xy[u][1], inst.xy[v][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), name=name, hoverinfo="skip", showlegend=showlegend))


def _points(fig, inst, colors, texts=None):
    labels = texts if texts is not None else (list(inst.labels) if inst.labels is not None else None)
    sizes = [8 + 3 * d for d in inst.demand]
    fig.add_trace(go.Scatter(x=inst.xy[1:, 0], y=inst.xy[1:, 1], mode="markers+text" if labels is not None else "markers", text=labels[1:] if labels is not None else None, textposition="top center",
                             marker=dict(size=sizes[1:], color=colors[1:], line=dict(width=1, color="white")), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers+text" if inst.labels is not None else "markers", text=[inst.labels[0]] if inst.labels is not None else None, textposition="top center",
                             marker=dict(size=18, symbol="star", color="#2ca02c", line=dict(width=1, color="white")), name="Depot", hoverinfo="skip", showlegend=False))


def _branch_colors(inst, edges, cap=None):
    """Punktfarbe je Knoten nach Zweig; Zweige über der Kapazität rot."""
    colors = ["#2ca02c"] * inst.n
    branches = A.branches_of(inst.n, edges)
    for i, b in enumerate(branches):
        bad = cap is not None and A.branch_demand(b, inst.demand) > cap
        for v in b:
            colors[v] = BAD_COLOR if bad else _branch_color(i)
    return colors, branches


def build_solution(inst, edges, cap=None, mst_edges=None):
    """Der Baum: Kanten je Zweig in der Zweigfarbe (Zweig über der Kapazität rot), Depotkanten dicker. Optional der MST als grau gestrichelte Kanten, die dem Baum fehlen."""
    fig = go.Figure()
    colors, branches = _branch_colors(inst, edges, cap)
    if mst_edges is not None:
        have = set(edges)
        _lines(fig, inst, [e for e in mst_edges if e not in have], MISS_COLOR, 1.8, "dash", "MST-Kante fehlt", True)
    for i, b in enumerate(branches):
        bad = cap is not None and A.branch_demand(b, inst.demand) > cap
        col = BAD_COLOR if bad else _branch_color(i)
        members = set(b)
        inner = [e for e in edges if e[0] != 0 and e[0] in members]
        gate = [e for e in edges if e[0] == 0 and e[1] in members]
        _lines(fig, inst, inner, col, 2.8)
        _lines(fig, inst, gate, col, 4.6)
    _points(fig, inst, colors)
    return _map_axes(fig, _height(inst))


def edges_after(inst, history, k):
    """Kantenmenge nach den ersten `k` Verschmelzungen von Esau-Williams (Start: Stern)."""
    edges = {(0, v) for v in range(1, inst.n)}
    for h in history[:k]:
        edges.discard(h["dropped"])
        edges.add((min(h["u"], h["v"]), max(h["u"], h["v"])))
    return sorted(edges)


def build_ew_step(inst, history, k, blocked_end=None):
    """Zustand nach `k` Verschmelzungen: Zweigfarben; die zuletzt gewählte Kante orange, die dabei weggefallene Depotkante grau gestrichelt und - falls vorhanden - die bessere, aber wegen der Kapazität
    unzulässige Verschmelzung des nächsten Schritts rot gestrichelt."""
    fig = go.Figure()
    edges = edges_after(inst, history, k)
    colors, branches = _branch_colors(inst, edges)
    for i, b in enumerate(branches):
        col = _branch_color(i)
        members = set(b)
        _lines(fig, inst, [e for e in edges if e[0] != 0 and e[0] in members], col, 2.8)
        _lines(fig, inst, [e for e in edges if e[0] == 0 and e[1] in members], col, 4.0)
    if k >= 1:
        h = history[k - 1]
        _lines(fig, inst, [h["dropped"]], MISS_COLOR, 2.0, "dash", "entfallene Depotkante", True)
        _lines(fig, inst, [(min(h["u"], h["v"]), max(h["u"], h["v"]))], DIFF_COLOR, 5.0, name="gewählte Verschmelzung", showlegend=True)
    nxt = history[k]["blocked"] if k < len(history) else blocked_end
    if nxt is not None:
        u, v, _s = nxt
        _lines(fig, inst, [(min(u, v), max(u, v))], BAD_COLOR, 2.4, "dot", "besser, passt aber nicht (Kapazität)", True)
    _points(fig, inst, colors)
    return _map_axes(fig, _height(inst))


def build_cost_bars(costs, mst_cost, order):
    """Kosten je Verfahren als Aufschlag gegen den MST (%); Verfahren ohne Baum als Text."""
    fig = go.Figure()
    ys = [None if costs.get(k) is None else 100.0 * (costs[k] / mst_cost - 1.0) for k in order]
    fig.add_trace(go.Bar(x=[METHOD_LABELS[k] for k in order], y=[0 if y is None else y for y in ys], marker_color=[METHOD_COLORS[k] for k in order],
                         text=["kein Baum" if y is None else f"{y:+.2f} %" for y in ys], textposition="outside"))
    fig.update_yaxes(title_text="Mehrkosten gegen den MST (%)", rangemode="tozero")
    return _base(fig, 320)


def build_capacity_curve(rows):
    """Kosten des besten Baums über die Kapazität (Linie), Stern und MST als Referenzen, Zahl der Zweige als Balken."""
    xs = ["∞" if r["cap"] == 0 else str(r["cap"]) for r in rows]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=xs, y=[r["branches"] for r in rows], marker_color="rgba(76,120,168,0.22)", name="Zweige"), secondary_y=True)
    fig.add_trace(go.Scatter(x=xs, y=[r["cost"] for r in rows], mode="lines+markers", line=dict(color="#2F6B65", width=2.8), name="bester Baum"), secondary_y=False)
    fig.add_hline(y=rows[0]["star"], line=dict(color="#8c8c8c", dash="dash", width=1.5), annotation_text="Stern", annotation_position="top right", secondary_y=False)
    fig.add_hline(y=rows[0]["mst"], line=dict(color="#7b3fbf", dash="dash", width=1.5), annotation_text="MST", annotation_position="bottom right", secondary_y=False)
    fig.update_xaxes(title_text="Kapazität Q", type="category")
    fig.update_yaxes(title_text="Kosten", secondary_y=False)
    fig.update_yaxes(title_text="Zweige", secondary_y=True, showgrid=False)
    return _base(fig, 360, legend_y=-0.3)


def build_sweep(rows, param_label, series, y_label, tick=None, log_y=False, ref_line=None, ref_label=None):
    """`series` = [(key, Name, Farbe)]: Median als Linie, 10. bis 90. Perzentil als Band (`<key>_lo`/`<key>_hi`)."""
    xs = [tick(r["value"]) if tick else str(r["value"]) for r in rows]
    fig = go.Figure()
    for key, name, color in series:
        ys = [None if r[key] != r[key] else r[key] for r in rows]
        lo = [None if r.get(f"{key}_lo", r[key]) != r.get(f"{key}_lo", r[key]) else r.get(f"{key}_lo", r[key]) for r in rows]
        hi = [None if r.get(f"{key}_hi", r[key]) != r.get(f"{key}_hi", r[key]) else r.get(f"{key}_hi", r[key]) for r in rows]
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        if all(v is not None for v in lo + hi):
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.13)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=2.5), name=name, connectgaps=False))
    if ref_line is not None:
        fig.add_hline(y=ref_line, line=dict(color="#888", dash="dash", width=1.5), annotation_text=ref_label, annotation_position="top left")
    fig.update_xaxes(title_text=param_label, type="category")
    fig.update_yaxes(title_text=y_label, type="log" if log_y else "linear")
    return _base(fig, 360, legend_y=-0.3)
