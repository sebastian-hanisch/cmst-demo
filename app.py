"""Kapazitierter Spannbaum – Esau-Williams, Kruskal, Lokalsuche, exakt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Spannbaum-Reihe der "Konzepte"-Reihe: ein Depot versorgt Kunden über ein Leitungsnetz, aber jeder Zweig unter einer Depotkante darf nur Q Bedarfseinheiten tragen. Q = unbegrenzt ist der MST,
Q = 1 der Stern, dazwischen ist das Problem NP-schwer. Gemessen werden der Wert der Kapazität, die Güte von Esau-Williams (1966) und Kruskal mit Kapazität gegen das exakte Optimum (Mengenpartition über die
Zweige), die Lokalsuche und die Wirkung von Depotlage, Bedarf und Ortschaften.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import cmst_algorithm as A
import cmst_constants as C
from cmst_evaluation import SWEEP_LABELS, SWEEP_TICKS, Settings, analyse, capacity_curve, ew_quality, sweep, sweep_params
from cmst_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from cmst_visualization import (
    build_capacity_curve,
    build_cost_bars,
    build_ew_step,
    build_solution,
    edges_after,
    build_sweep,
)

st.set_page_config(page_title="Kapazitierter Spannbaum – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _quality(base):
    return ew_quality(base)


@st.cache_data(show_spinner=False)
def _curve(base):
    return capacity_curve(base)


def pct(x):
    return "kein Baum" if x is None else f"{x:+.2f} %"


def num(x):
    return f"{x:.2f}"


def cap_txt(cap):
    return "∞" if cap in (None, C.UNLIMITED) else str(cap)


st.title("🌳 Kapazitierter Spannbaum – Zweige mit Kapazität")
st.markdown(
    """
**Siebtes Stück der Spannbaum-Reihe.** Ein Depot (Konzentrator, Werk) versorgt Kunden über ein Leitungsnetz, aber **jeder Zweig unter einer Depotkante darf nur Q Bedarfseinheiten tragen** - eine Leitung, ein Port, ein
Verteilerkabel hat nur begrenzte Kapazität. Ohne Grenze ist der Baum der **MST**; bei Q = 1 hängt jeder Kunde einzeln am Depot (**Stern**). Dazwischen ist das Problem **NP-schwer** (Papadimitriou 1978, schon bei Einheitsbedarf).

Die Standard-Heuristik ist **Esau-Williams** (1966): Start mit dem Stern, dann immer die Verschmelzung zweier Zweige, die am meisten spart ("teurere Depotkante minus neue Kante"), solange der Bedarf noch passt.
Hier wird gemessen, **was die Kapazität kostet**, wie nah Esau-Williams, **Kruskal mit Kapazität** und eine **Lokalsuche** am **exakten Optimum** liegen (das für kleine Instanzen eine Mengenpartition über die Zweige liefert) und wie
**Depotlage, Bedarf und Ortschaften** wirken.
"""
)
st.caption(
    "Setzt auf [kruskal-demo](https://github.com/sebastian-hanisch/kruskal-demo) und [constrained-mst-demo](https://github.com/sebastian-hanisch/constrained-mst-demo) auf; Esau-Williams ist die Baum-Schwester der "
    "Savings-Heuristik aus [vrp-nachbarschaften-demo](https://github.com/sebastian-hanisch/vrp-nachbarschaften-demo). Geplante Nachfolger (nicht gebaut): Steiner-Baum, Prize-Collecting Steiner-Baum, Sensitivität, zufällige Spannbäume."
)

with st.expander("So funktionieren die Verfahren", expanded=True):
    st.markdown(
        """
1. **Zweigsatz:** das Depot ist in jedem Zweig ein Blatt. Ein Zweig über der Kundenmenge S kostet mindestens **MST(S) + billigste Depotkante zu einem Kunden von S** - und genau das ist erreichbar. Der Baum ist also eine **Partition
   der Kunden in Zweige** mit Bedarf ≤ Q; der exakte Weg probiert alle Teilmengen (nur für kleine Instanzen).
2. **Kruskal mit Kapazität:** alle Kanten (auch die zum Depot) nach Länge; eine Kante wird genommen, wenn sie zwei Komponenten verbindet, der vereinigte Bedarf ≤ Q ist und nicht beide schon am Depot hängen.
3. **Esau-Williams:** Start Stern; je Schritt die Verschmelzung mit der größten Ersparnis (die **teurere** der beiden Depotkanten entfällt, die neue Kante kommt dazu), sofern der Bedarf passt.
4. **Lokalsuche:** Kunden umhängen, tauschen, Zweige zusammenlegen - jede Änderung mit den exakten Zweigkosten bewertet; startet von Esau-Williams und Kruskal, das bessere Ergebnis zählt.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ss = st.session_state
with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Ortschaften: Verteiler mit Anschlussnehmern im Kreis (ein Zweig je Ortschaft liegt nahe). Lehrbuchbeispiel: vier Kunden im Kreuz, von Hand nachzurechnen.")
    cap = st.select_slider("Kapazität Q (Bedarfseinheiten je Zweig)", options=list(C.CAP_OPTIONS), value=int(ss["cap_select"]), key="cap_widget", on_change=store_from_widget, args=("cap_select",),
                           format_func=cap_txt, help="Höchster Bedarf, den ein Zweig unter einer Depotkante tragen darf. Kleiner als der größte Einzelbedarf gibt es keinen Baum. ∞ = der unbeschränkte MST.")
    if kind != "textbook":
        n = st.slider("Kunden n", *bounds("n_slider"), value=int(ss["n_slider"]), key="n_widget", on_change=store_from_widget, args=("n_slider",),
                      help=f"Das exakte Optimum wird bis n = {C.N_EXACT} Kunden angeboten; darüber zeigt die Demo die Heuristiken und vergleicht sie untereinander.")
        demand_mode = st.radio("Bedarf der Kunden", options=list(C.DEMAND_MODES), format_func=lambda v: C.DEMAND_LABELS[v], key="demand_widget", on_change=store_from_widget, args=("demand_select",),
                               index=list(C.DEMAND_MODES).index(ss["demand_select"]), help="Einheitlich: jeder Kunde 1. Gemischt: zufällig 1 bis 4 (die Kapazität muss dann mindestens 4 sein, sonst passt der größte Kunde nicht).")
        depot = st.radio("Depotlage", options=list(C.DEPOT_POS), format_func=lambda v: C.DEPOT_LABELS[v], key="depot_widget", on_change=store_from_widget, args=("depot_select",),
                         index=list(C.DEPOT_POS).index(ss["depot_select"]), help="Das Depot am Rand oder in der Mitte der Fläche.")
        terrain = st.select_slider("Geländezuschlag", options=list(C.TERRAIN_OPTIONS), value=float(ss["terrain_select"]), key="terrain_widget", on_change=store_from_widget, args=("terrain_select",),
                                   format_func=lambda v: "0 (euklidisch)" if v == 0 else f"{v:g}", help="Kosten = Länge x Geländefaktor in [1, 1 + Zuschlag] je Knotenpaar.")
        if kind == "hubs":
            sats = st.slider("Anschlüsse je Verteiler", *bounds("sats_select"), value=int(ss["sats_select"]), key="sats_widget", on_change=store_from_widget, args=("sats_select",),
                             help="Anschlussnehmer im Kreis um jeden Verteiler (Radius etwa 6).")
        else:
            sats = C.DEFAULT_SATS
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        n, demand_mode, depot, terrain, sats, seed = C.DEFAULT_N, "unit", "edge", C.DEFAULT_TERRAIN, C.DEFAULT_SATS, C.DEFAULT_SEED

sync_query_params({"kind_select": kind, "n_slider": int(ss["n_slider"]), "cap_select": int(ss["cap_select"]), "demand_select": ss["demand_select"], "depot_select": ss["depot_select"],
                   "terrain_select": float(ss["terrain_select"]), "sats_select": int(ss["sats_select"]), "seed_input": int(ss["seed_input"]), "tree_select": ss["tree_select"]})

settings = Settings(kind, int(n), demand_mode, depot, int(cap), float(terrain), int(sats), int(seed))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst = a.inst
capv = a.cap
names = inst.labels

# --- In Aktion ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Der kapazitierte Baum in Aktion")
STEP_LABELS = {1: "1 · Instanz und MST", 2: "2 · Esau-Williams", 3: "3 · Der kapazitierte Baum"}
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="cmst_step", format_func=lambda s: STEP_LABELS[s])

if step == 1:
    over = [b for b in a.mst.branches if capv is not None and A.branch_demand(b, inst.demand) > capv]
    line = (f"**Depot ⭐ und {inst.customers} Kunden** (Gesamtbedarf {inst.total_demand}, Punktgröße = Bedarf). Der MST ohne Kapazität kostet **{num(a.mst.cost)}**, hat **{a.mst.n_branches} Zweig(e)** mit Bedarf "
            + ", ".join(str(A.branch_demand(b, inst.demand)) for b in a.mst.branches) + ".")
    if capv is None:
        line += " Ohne Kapazitätsgrenze ist der MST der beste Baum."
    elif over:
        line += f" **{len(over)} Zweig(e) verletzen die Kapazität Q = {capv}** (rot) - der Baum muss zerlegt werden."
    else:
        line += f" Alle Zweige passen in Q = {capv}: **die Kapazität kostet hier nichts.**"
    st.markdown(line)
    st.plotly_chart(build_solution(inst, a.mst.edges, capv), width="stretch", key="s1_map")
    st.caption("Farbe = Zweig unter einer Depotkante (dick); ein Zweig über der Kapazität ist rot.")
elif step == 2:
    if a.infeasible:
        st.warning(f"Die Kapazität Q = {capv} ist kleiner als der größte Einzelbedarf ({inst.max_demand}): kein Kunde dieser Größe passt in einen Zweig, es gibt keinen Baum.")
    else:
        ew = a.sols["ew"]
        hist = ew.history
        kmax = len(hist)
        if "cmst_k" in ss:
            ss["cmst_k"] = min(max(0, int(ss["cmst_k"])), kmax)
        k = st.slider("Verschmelzungen", 0, kmax, key="cmst_k", help="Schritt 0 = Stern; jede Verschmelzung ersetzt zwei Depotkanten-Zweige durch einen.") if kmax > 0 else 0
        cost_now = A.edges_cost(edges_after(inst, hist, k), inst.D)
        if k == 0:
            st.markdown(f"**Schritt 0 von {kmax}:** der Stern - jeder Kunde direkt am Depot, Kosten **{num(cost_now)}**.")
        else:
            h = hist[k - 1]
            st.markdown(f"**Schritt {k} von {kmax}:** Kante {h['u']}–{h['v']} verschmilzt zwei Zweige; die teurere Depotkante entfällt, das **spart {num(h['saving'])}** - Kosten jetzt **{num(cost_now)}**.")
        nxt = hist[k]["blocked"] if k < kmax else ew.blocked_end
        if nxt is not None:
            lead = "Im nächsten Schritt wäre" if k < kmax else "Zum Schluss wäre noch"
            st.markdown(f"{lead} die Verschmelzung {nxt[0]}–{nxt[1]} (spart {num(nxt[2])}) besser als die gewählte, sie **passt nicht in die Kapazität** Q = {capv} (rot gepunktet)." if k < kmax
                        else f"{lead} die Verschmelzung {nxt[0]}–{nxt[1]} sinnvoll (spart {num(nxt[2])}), sie **passt nicht in die Kapazität** Q = {capv} (rot gepunktet).")
        if k == kmax:
            st.markdown(f"**Ende:** keine zulässige Verschmelzung mit positiver Ersparnis mehr. Esau-Williams: **{num(ew.cost)}** mit {ew.n_branches} Zweigen.")
        st.plotly_chart(build_ew_step(inst, hist, k, ew.blocked_end), width="stretch", key=f"s2_map_{k}")
        st.caption("Farbe = Zweig; orange = zuletzt gewählte Kante, grau gestrichelt = dabei entfallene Depotkante, rot gepunktet = bessere Verschmelzung, die wegen der Kapazität nicht passt.")
else:
    options = [t for t in C.TREE_OPTIONS]
    if ss.get("tree_widget") not in options:
        ss.pop("tree_widget", None)
    cur = ss["tree_select"] if ss["tree_select"] in options else options[0]
    tree_key = st.radio("Baum zeigen", options=options, format_func=lambda v: C.TREE_LABELS[v], key="tree_widget", horizontal=True, index=options.index(cur), on_change=store_from_widget, args=("tree_select",),
                        help="Bester Fund = billigster gültiger Baum unter Stern, Kruskal, Esau-Williams, Lokalsuche und (falls angeboten) exakt. Der MST ist nur zulässig, wenn seine Zweige in Q passen.")
    name = a.best_name if tree_key == "best" else tree_key
    sol = a.solution(name) if name else None
    if a.infeasible:
        st.warning(f"Die Kapazität Q = {capv} ist kleiner als der größte Einzelbedarf ({inst.max_demand}): es gibt keinen Baum.")
    elif sol is None:
        why = {"exact": f"Das exakte Verfahren wird nur bis n = {C.N_EXACT} Kunden angeboten.", "mst": "Der MST verletzt die Kapazität (seine Zweige sind zu groß)."}.get(name, "Hier gibt es keinen Baum.")
        st.warning(f"{C.TREE_LABELS.get(tree_key, tree_key)}: {why}")
        st.plotly_chart(build_solution(inst, a.star.edges, capv), width="stretch", key="s3_none")
    else:
        st.plotly_chart(build_solution(inst, sol.edges, capv, a.mst.edges if name != "mst" else None), width="stretch", key=f"s3_map_{name}")
        st.markdown(f"**{C.TREE_LABELS[name]}:** Kosten **{num(sol.cost)}**, **{pct(a.price(name))}** gegen den MST ({num(a.mst.cost)}), **{sol.n_branches} Zweig(e)** mit Bedarf "
                    + ", ".join(str(A.branch_demand(b, inst.demand)) for b in sol.branches) + (f" (Kapazität {capv})." if capv is not None else "."))
    if not a.infeasible:
        order = ("star", "mst", "kruskal", "ew", "ls", "exact")
        costs = {k: (a.solution(k).cost if a.solution(k) is not None else None) for k in order if k != "exact" or a.exact_offered}
        st.plotly_chart(build_cost_bars(costs, a.mst.cost, [k for k in order if k in costs]), width="stretch", key="cost_bars")
        st.caption("Mehrkosten gegen den MST. Ein fehlender Balken heißt: kein gültiger Baum (der MST verletzt die Kapazität) bzw. das Verfahren wird bei dieser Größe nicht angeboten.")

st.markdown("---")

# --- Kennzahlen --------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ⚙️ Was ist die Kapazität wert?")
if a.infeasible:
    st.info("Bei dieser Kapazität gibt es keinen gültigen Baum - erhöhen Sie Q mindestens auf den größten Einzelbedarf.")
else:
    best = a.best
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Preis der Kapazität", pct(a.price(a.best_name)), delta=f"Fund: {C.TREE_LABELS[a.best_name]}", delta_color="off")
    m2.metric("Zweige", str(best.n_branches), delta=f"größter {a.max_branch(a.best_name)} von Q = {cap_txt(capv)}", delta_color="off")
    m3.metric("Esau-Williams", "optimal" if a.excess("ew") <= 1e-9 else pct(a.excess("ew")), delta="gegen besten Fund", delta_color="off")
    m4.metric("Kruskal mit Kap.", "optimal" if a.excess("kruskal") <= 1e-9 else pct(a.excess("kruskal")), delta="gegen besten Fund", delta_color="off")
    ex_txt = f"Exakt bewiesen: das Optimum ist der beste Fund ({a.exact_subsets} zulässige Zweig-Kandidaten)." if a.proved else f"Kein exaktes Verfahren bei n = {inst.customers} > {C.N_EXACT}: 'bester Fund' ist die beste Heuristik."
    st.caption(f"Preis = Kosten des besten gültigen Baums gegen den unbeschränkten MST ({num(a.mst.cost)}); Ersparnis gegen den Stern ({num(a.star.cost)}): {a.star_saving:.1f} %. {ex_txt}")

st.markdown("---")

# --- Experimente auf Abruf ---------------------------------------------------------------------------------------------------------------------

base = replace(settings, seed=0)
if kind != "textbook":
    st.subheader("📉 Der Wert der Kapazität")
    st.caption("Kosten des besten Baums für diese Instanz über alle Kapazitäten (Balken: Zahl der Zweige); Stern und MST als Referenzen.")
    if st.button("Kapazitätskurve für diese Instanz berechnen", key="curve_start"):
        ss["curve_done"] = ss.get("curve_done", set()) | {settings}
    if settings in ss.get("curve_done", set()):
        with st.spinner("Rechne..."):
            rows_c = _curve(settings)
        if rows_c:
            st.plotly_chart(build_capacity_curve(rows_c), width="stretch", key="curve")
            free = next((r["cap"] for r in rows_c if r["mst_free"]), None)
            st.caption("Kapazität ab der der MST schon passt: " + ("Q = " + cap_txt(free) if free is not None else "keine") + f". Ohne Kapazität: {num(rows_c[0]['mst'])}, Stern: {num(rows_c[0]['star'])}.")
    st.markdown("---")

    st.subheader("🎲 Wie gut ist Esau-Williams?")
    st.caption("50 Instanzen mit den Einstellungen der Seitenleiste (nur der Seed wechselt): wie oft trifft Esau-Williams den besten Baum, wie groß ist die Lücke, wie oft schlägt Kruskal mit Kapazität Esau-Williams?")
    if st.button("Qualitäts-Experiment über 50 Instanzen (dauert einige Sekunden)", key="quality_start"):
        ss["quality_done"] = ss.get("quality_done", set()) | {base}
    if base in ss.get("quality_done", set()):
        with st.spinner("Rechne..."):
            q = _quality(base)
        if q["n_runs"]:
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Esau-Williams optimal", f"{q['ew_optimal']:.0f} %", delta=f"mittlere Lücke {q['ew_gap_mean']:.2f} %", delta_color="off")
            f2.metric("Größte Lücke", f"{q['ew_gap_max']:.1f} %", delta="Esau-Williams", delta_color="off")
            f3.metric("Kruskal schlechter", f"{q['kruskal_worse']:.0f} %", delta=f"besser: {q['kruskal_better']:.0f} %", delta_color="off")
            f4.metric("Lokalsuche optimal", f"{q['ls_optimal']:.0f} %", delta=f"verbessert EW: {q['ls_improves']:.0f} %", delta_color="off")
            st.caption(f"Über {q['n_runs']} Instanzen; " + ("Lücken gegen das exakte Optimum." if q["exact_used"] else "Lücken gegen den besten gefundenen Baum (bei dieser Größe ohne exaktes Verfahren).") + f" Kruskal mit Kapazität ist in {q['kruskal_optimal']:.0f} % optimal; der MST passt in {q['mst_free']:.0f} %.")
        else:
            st.info("Bei dieser Kapazität gibt es keine gültigen Bäume (Kapazität kleiner als der größte Bedarf).")
    st.markdown("---")

    st.subheader("📐 Sweeps")
    params = sweep_params(kind)
    if ss.get("sweep_select") not in params:
        ss.pop("sweep_select", None)
    sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", params, format_func=lambda v: SWEEP_LABELS[v], key="sweep_select")
    metric_opts = {"price": "Preis der Kapazität", "excess": "Aufschlag der Verfahren", "branches": "Zweige"}
    if ss.get("sweep_metric") not in metric_opts:
        ss.pop("sweep_metric", None)
    metric = st.radio("Kennzahl", options=list(metric_opts), format_func=lambda v: metric_opts[v], key="sweep_metric", horizontal=True)
    if st.button("Sweep über 5 feste Instanzen berechnen (kann einige Sekunden dauern)", key="sweep_start"):
        ss["sweep_done"] = ss.get("sweep_done", set()) | {(sweep_param, base)}
    if (sweep_param, base) in ss.get("sweep_done", set()):
        with st.spinner("Rechne den Sweep über 5 feste Instanzen..."):
            rows_s = _sweep(sweep_param, base)
        series = {
            "price": ([("price_best", "bester Fund", "#2F6B65"), ("price_ew", "Esau-Williams", "#e8a13a"), ("price_kruskal", "Kruskal mit Kapazität", "#4c78a8")], "Mehrkosten gegen den MST (%)"),
            "excess": ([("excess_kruskal", "Kruskal mit Kapazität", "#4c78a8"), ("excess_ew", "Esau-Williams", "#e8a13a"), ("excess_ls", "Lokalsuche", "#d95f9b")], "Aufschlag gegen den besten Fund (%)"),
            "branches": ([("branches", "Zweige des besten Baums", "#2F6B65"), ("max_branch", "größter Zweig (Bedarf)", "#e8a13a"), ("mst_branches", "Zweige des MST", "#7b3fbf")], "Anzahl bzw. Bedarf"),
        }[metric]
        st.plotly_chart(build_sweep(rows_s, SWEEP_LABELS[sweep_param], series[0], series[1], tick=SWEEP_TICKS.get(sweep_param)), width="stretch", key="sweep_chart")
        st.caption("Median über 5 feste Instanzen (Seeds 100000–100004), Band = 10. bis 90. Perzentil; Instanzen ohne gültigen Baum (Kapazität unter dem größten Bedarf) fehlen. Der Aufschlag ist gegen den besten gefundenen Baum gemessen - "
                   "bei Kunden ≤ 14 ist das das exakte Optimum. Die übrigen Regler stehen wie in der Seitenleiste.")
    st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ein Depot, eine Kapazität für alle Zweige** | Ja hier; reale Netze haben mehrere Kabeltypen (Kapazitätsstufen), mehrere Depots, Redundanz. | Netzentwurf mit Kapazitätsstufen (nicht gebaut) |
| **Exakt lösbar** | Nur klein: die Mengenpartition wird bis n = 14 Kunden angeboten (O(3^n)); größere Instanzen brauchen Branch-Cut-and-Price (Uchoa u. a. 2008, nicht gebaut). Darüber vergleicht die Demo die Heuristiken nur untereinander. | Branch-Cut-and-Price |
| **Esau-Williams ist nah am Optimum** | Nicht immer: bei 12 Kunden und Q = 4 trifft er den optimalen Baum in 52 % der Instanzen (mittlere Lücke 1.37 %, größte 9.4 %), in Ortschaften mit 14 Kunden und Q = 5 nur in 6 % (mittlere Lücke 3.53 %, größte 11.8 %); Kruskal mit Kapazität schlägt ihn dort, wo er versagt, in 14 % der Instanzen (Q = 4, 12 Kunden). | Stärkere Metaheuristiken (nicht gebaut) |
| **Verfahren = ein Lauf** | Esau-Williams ist deterministisch; die Lokalsuche steckt in lokalen Optima fest (Depot in der Mitte). Keine Tabu-/GRASP-Varianten. | - |
| **Synthetisches Modell** | Punkte im Quadrat, vollständiger Graph, Einheits- oder Kleinbedarf, kein Zeitverlauf. | Echte Netze |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben Knoten $0$ (Depot) und $1..n$ (Kunden) mit Bedarf $d_i$ und Kosten $c_{uv}$ sowie eine Kapazität $Q$. Gesucht ist ein Spannbaum, in dem der Bedarf jedes Teilbaums unter einer Depotkante höchstens $Q$ ist,
mit minimalen Kantenkosten. Für $Q \ge \sum d_i$ ist es der MST, für $Q = 1$ (Einheitsbedarf) der Stern.

**Zweigsatz.** Ist $S$ die Kundenmenge eines Zweigs, so kostet der billigste Zweig $\mathrm{MST}(S) + \min_{v \in S} c_{0v}$: entfernt man das Depot (ein Blatt), bleibt ein Baum auf $S$; seine Kosten sind mindestens $\mathrm{MST}(S)$, und die Depotkante
kann an jedem Knoten von $S$ hängen. Der CMST ist also die Partition $\{S_1, \dots, S_m\}$ der Kunden mit $d(S_j) \le Q$ und minimalem $\sum_j (\mathrm{MST}(S_j) + \min_{v \in S_j} c_{0v})$.

**Exakt.** Mit $f(M)$ = kleinste Kosten, $M$ zu zerlegen: $f(M) = \min_{S \subseteq M,\; \ell(M) \in S,\; d(S) \le Q} \big(\mathrm{cost}(S) + f(M \setminus S)\big)$, $\ell(M)$ das niedrigste Bit; Aufwand $O(3^n)$.

**Esau-Williams.** Jede Komponente $C$ hat eine Depotkante der Kosten $w_C$. Für zwei Komponenten $A, B$ mit billigster Verbindung $(u,v)$ ist die Ersparnis $\max(w_A, w_B) - c_{uv}$; verschmolzen wird nur, wenn $d(A) + d(B) \le Q$.

**Literatur.** Esau, L. R., & Williams, K. C. (1966). *On teleprocessing system design, Part II: A method for approximating the optimal network.* IBM Systems Journal 5(3), 142-147. Papadimitriou, C. H. (1978). *The complexity of the
capacitated tree problem.* Networks 8(3), 217-230. Uchoa, E., Fukasawa, R., Lysgaard, J., Pessoa, A., Poggi de Aragão, M., & Andrade, R. (2008). *Robust branch-cut-and-price for the capacitated minimum spanning tree problem over a large
extended formulation.* Mathematical Programming 112, 443-472.

Implementiert in `cmst_algorithm.py` (Verfahren), `cmst_scenario.py` (Instanzen), `cmst_evaluation.py` (Kennzahlen, Sweeps, Experimente).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
