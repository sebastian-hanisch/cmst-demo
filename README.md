# Kapazitierter Spannbaum – Esau-Williams, Kruskal, Lokalsuche, exakt – Streamlit-Demo

Siebtes Stück der **Spannbaum-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning". Ein Depot (Konzentrator, Werk) versorgt Kunden über ein Leitungsnetz, aber **jeder Zweig unter einer Depotkante darf nur Q Bedarfseinheiten tragen** - eine Leitung, ein Port, ein Verteilerkabel hat begrenzte Kapazität. Ohne Grenze ist der Baum der **MST**, bei Q = 1 der **Stern**; dazwischen ist das Problem **NP-schwer** (Papadimitriou 1978, schon bei Einheitsbedarf). Die Standard-Heuristik ist **Esau-Williams** (1966): Start mit dem Stern, dann immer die Verschmelzung zweier Zweige, die am meisten spart, solange der Bedarf passt. Die Demo misst, **was die Kapazität kostet**, wie nah Esau-Williams, **Kruskal mit Kapazität** und eine **Lokalsuche** am **exakten Optimum** liegen und wie **Depotlage, Bedarf und Ortschaften** wirken. Das exakte Optimum kommt ohne Löser aus: ein Zweig über der Kundenmenge S kostet genau **MST(S) + billigste Depotkante zu einem Kunden von S** (das Depot ist im Zweig ein Blatt), der kapazitierte Baum ist also eine **Mengenpartition** der Kunden, die per dynamischer Programmierung über Teilmengen gelöst wird. Esau-Williams ist die Baum-Schwester der Savings-Heuristik aus [vrp-nachbarschaften-demo](../vrp-nachbarschaften-demo); der Baum ohne Kapazität kommt aus [kruskal-demo](../kruskal-demo).

**Einordnung in die Reihe:** geplant sind elf Stücke, dies ist das siebte:

```
Kruskal (Wurzel)                                                                           [gebaut: kruskal-demo]
 ├─ Prim (Kontrast: wächst von einem Punkt)                                                [gebaut: prim-demo]
 ├─ Borůvka (Kontrast: alle Komponenten parallel)                                          [gebaut: boruvka-demo]
 ├─ Euklidischer MST (keine n²-Kantenliste, Delaunay)                                      [gebaut: euclidean-mst-demo]
 ├─ Gerichteter Spannbaum (Chu-Liu/Edmonds)                                                [gebaut: arborescence-demo]
 ├─ Bottleneck-/Grad-/Hop-beschränkter Spannbaum                                           [gebaut: constrained-mst-demo]
 │    └─ Kapazitierter MST                                                                 [DIESES STÜCK]
 ├─ Steiner-Baum → Prize-Collecting Steiner-Baum                                           [nicht gebaut]
 ├─ MST-Sensitivität & dynamischer MST                                                     [nicht gebaut]
 └─ Zufällige Spannbäume & Kirchhoff                                                       [nicht gebaut]
```

Ergebnis in Kürze: **Die Kapazität ist teuer und wirkt stufenweise: bei 12 Kunden (Depot am Rand, Einheitsbedarf) kostet Q = 2 im Median +47 % gegenüber dem MST, Q = 4 +13,5 %, Q = 8 +0,9 %, ab Q = 10 nichts mehr; der Stern (Q = 1) kostet +134 %. Esau-Williams trifft im Median das Optimum, aber nur in 52 bis 78 % der Instanzen den besten Baum (mittlere Lücke 0,5 bis 1,6 %, größte bis 10,8 %) - in Ortschaften nur in 6 % (mittlere Lücke 3,5 %). Kruskal mit Kapazität ist meist schlechter (48 bis 70 % der Instanzen, in Ortschaften 80 %), schlägt Esau-Williams aber in 4 bis 14 %. Die Lokalsuche trifft den besten Baum in 52 bis 90 % der Instanzen, steckt aber fest (Depot in der Mitte: +5,0 %).**

| Frage | Ergebnis (12 Kunden, Depot am Rand, Einheitsbedarf, Q = 4, ohne Geländezuschlag, sofern nicht anders angegeben; **Median** über 5 feste Instanzen, Seeds 100000–100004; vollständig deterministisch) |
|---|---|
| **Stimmt der Zweigsatz?** | ✅ ja, direkt geprüft: `MST(S) + billigste Depotkante` ist der billigste Baum auf S ∪ {Depot} mit Depotgrad 1 (Brute-Force über alle Bäume für alle Kundenmengen kleiner Instanzen); die Mengenpartition ist damit gleich Brute-Force über **alle** Spannbäume (90 Instanzen × 7 Kapazitäten, Einheits- und gemischter Bedarf, Gleichstände) und gleich einer unabhängigen Partitionsaufzählung |
| **Was kostet die Kapazität?** | Preis gegen den unbeschränkten MST bei Q = 1/2/3/4/5/6/8/10/∞: **+133,6/+47,2/+25,8/+13,5/+8,5/+3,3/+0,9/0/0 %**; Ersparnis gegen den Stern 0/35,9/46,2/51,0/52,9/56,2/56,8/57,2/57,2 %; der MST passt schon in Q in 0/0/0/0/0/0/40/80/100 % der Instanzen (Q = 8/10/∞) |
| **Eine Instanz über alle Kapazitäten** | Seed 35: Q = 1…12, ∞ kostet 555,17 / 358,88 / 308,84 / 262,60 / 253,26 / 244,78 / 233,47 / 233,47 / 224,14 / 215,65 (Q ≥ 10); Zweige 12/7/5/4/4/3/3/3/3/2; Q = 7 und 8 kosten dasselbe, ab Q = 10 passt der MST (zwei Zweige mit 2 und 10 Kunden) |
| **Depot in der Mitte** | ⚠️ macht die Kapazität **billiger, nicht teurer** (Erwartung widerlegt): Q = 2/4/6/8/∞: **+35,8/+7,0/+2,5/0/0 %** gegen +47,2/+13,5/+3,3/+0,9/0 % am Rand; Ersparnis gegen den Stern bei Q = 4: 47,0 % gegen 51,0 % |
| **Gemischter Bedarf (1 bis 4)** | Q < 4 ist unmöglich (der größte Kunde passt nicht: Q = 2 in 100 %, Q = 3 in 80 % der Instanzen ohne gültigen Baum); Q = 3/4/6/8/∞: **+85,5/+78,3/+52,3/+27,2/0 %**; bei Q = 4 kostet die Kapazität +78,3 % (einheitlich: +13,5 %), der Baum hat 9 statt 4 Zweige und spart nur 17,8 % gegen den Stern (einheitlich 51,0 %) |
| **Wächst der Preis mit n?** (Q = 4) | ✅ ja: n = 8/12/14/20/30/60: **+6,3/+13,5/+20,0/+25,8/+38,2/+85,6 %**, Zweige 3/4/4/6/9/16 (der MST hat immer 2), Ersparnis gegen den Stern 44,5/51,0/53,9/56,7/60,2/65,1 % |
| **Geländezuschlag** | 0/0,3/0,6/1,0: +13,5/+10,3/+10,5/+8,8 % - kein klarer Trend |
| **Wie gut ist Kruskal mit Kapazität?** | Aufschlag gegen den besten Baum (Median) bei Q = 1/2/3/4/5/6/8/10/∞: **0/+4,3/+7,2/+5,2/+6,3/0/0/0/0 %**; optimal in 100/20/20/40/20/60/80/80/100 % der Instanzen |
| **Wie gut ist Esau-Williams?** | Aufschlag im Median **0** bei jedem Q (Lücke zum exakten Optimum ebenso); optimal in 100/60/60/80/80/80/80/100/100 % der Instanzen (Q wie oben) |
| **… über 50 Instanzen** (Lücke gegen das exakte Optimum) | 12 Kunden: **Q = 3:** EW optimal in 60 %, mittlere Lücke 1,59 %, größte 10,8 %, Kruskal schlechter in 70 % / besser in 6 %, Lokalsuche optimal in 90 % (verbessert EW in 38 %), Kruskal optimal in 26 %; **Q = 4:** 52 % / 1,37 % / 9,4 % / 62 % / 14 % / 84 % (38 %) / 20 %; **Q = 6:** 56 % / 0,78 % / 5,7 % / 48 % / 12 % / 74 % (22 %) / 40 %; **Depot in der Mitte (Q = 4):** 78 % / 0,49 % / 6,8 % / 62 % / 4 % / 90 % (12 %) / 34 %; der MST passt in Q = 4 nie, in Q = 6 in 6 % der Instanzen |
| **Ortschaften** (14 Kunden, Q = 5) | ⚠️ Esau-Williams optimal nur in **6 %**, mittlere Lücke **3,53 %**, größte 11,8 %; Kruskal schlechter in 80 % / besser in 12 %, optimal in 2 %; die Lokalsuche verbessert Esau-Williams in 76 % und trifft den besten Baum in 52 %. Preis Q = 2/3/4/5/6/8/∞: +169,8/+99,0/+66,2/+59,9/+32,7/+21,4/0 %; Aufschlag Esau-Williams 0/2,7/2,3/3,9/0/0/0 %, Kruskal 2,5/3,7/4,0/6,5/0/0/0 % |
| **Passt Q zur Ortschaftsgröße?** | Q = 5, 14 Kunden, Anschlüsse je Verteiler 3/4/5/6/8: Preis **+33,3/+28,6/+59,9/+69,4/+62,1 %**, Esau-Williams optimal in 40/80/0/0/20 % - bei 4 Anschlüssen (Ortschaft = 5 Kunden) passt Q = 5 genau |
| **Größere Instanzen** (kein exaktes Verfahren, Lücke gegen den besten gefundenen Baum, Q = 4) | n = 20/30/60: Kruskal +7,9/+4,9/+8,0 %, Esau-Williams +0,7/+0,8/+1,5 % (die Lokalsuche ist dort in jeder der 5 Instanzen der beste Fund, die Werte messen also den Abstand zur Lokalsuche) |
| **Lehrbuchbeispiel** (Kreuz) | MST 80 (ein Zweig mit 4 Kunden); Q = 3/2/1: **88,28/96,57/116,57** (+10,4/+20,7/+45,7 %) |

## Was die Demo zeigt

1. **Der kapazitierte Baum in Aktion** (Schritt-Slider): **Instanz und MST** (Zweige farbig, Zweige über der Kapazität rot; Punktgröße = Bedarf) → **Esau-Williams** (Slider über die Verschmelzungen: Stern → Baum; orange = gewählte Kante, grau gestrichelt = entfallene Depotkante, **rot gepunktet = bessere Verschmelzung, die wegen der Kapazität nicht passt**; Text mit Ersparnis und Kosten) → **Der kapazitierte Baum** (Umschalter Bester Fund / Esau-Williams / Kruskal mit Kapazität / Lokalsuche / Exakt / Stern / MST; grau gestrichelt = MST-Kante fehlt; darunter die Mehrkosten gegen den MST als Balken).
2. **Was ist die Kapazität wert?** Preis der Kapazität, Zweige und größter Zweig, Aufschlag von Esau-Williams und Kruskal, Ersparnis gegen den Stern, Beleg, ob das Optimum exakt bewiesen ist.
3. **📉 Der Wert der Kapazität** (auf Abruf): Kosten des besten Baums über alle Kapazitäten für die aktuelle Instanz, Zweigzahl als Balken, Stern und MST als Referenzen.
4. **🎲 Wie gut ist Esau-Williams?** (auf Abruf): 50 Instanzen - Anteil optimal, mittlere und größte Lücke, Kruskal schlechter/besser, Lokalsuche.
5. **📐 Sweeps** über Q, n, Depotlage, Bedarf, Geländezuschlag und (Ortschaften) die Zahl der Anschlüsse: Preis, Aufschlag der Verfahren, Zweige (5 feste Instanzen, Median, 10.–90. Perzentil-Band).
6. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an".

Regler: Instanz (Karte / **Ortschaften** / **Lehrbuchbeispiel**), **Kapazität Q** (1 bis 30 und ∞), Kunden n (5–60), **Bedarf** (einheitlich / gemischt 1–4), **Depotlage** (Rand / Mitte), Geländezuschlag, Anschlüsse je Verteiler (nur Ortschaften), Seed (+ 🎲), Baumauswahl. Alle Regler wirken auf Kosten, Bedarf oder Grenze; das Lehrbuchbeispiel blendet die Kartenregler aus. Kein Zufall im Kern.

## Messwerte der Presets

| Preset | Instanz | Ergebnis |
|---|---|---|
| Standardfall (Voreinstellung) | 12 Kunden, Depot am Rand, Q = 4, Seed 35 | MST 215,65 (Zweige mit 2 und 10 Kunden, verletzt Q); bester Baum 262,60 (+21,77 %), 4 Zweige (Bedarf 2/4/3/3) - Kruskal mit Kapazität, Esau-Williams, Lokalsuche und exakt finden dasselbe; spart 52,7 % gegen den Stern (555,17) |
| Kapazität 2 | | 7 Zweige, 358,88 (+66,42 %); Esau-Williams, Lokalsuche und exakt dasselbe, Kruskal 375,75 (+4,70 %) |
| Stern (Kapazität 1) | | 555,17 (+157,44 %), 12 Zweige; alle Verfahren gleich |
| Kapazität kostenlos (Q = 10) | | der MST passt (+0,00 %); Q = 9 kostet +3,93 %, Q = 8 +8,26 % |
| Depot in der Mitte | Q = 4 | MST 225,43 (ein Zweig mit 12 Kunden); exakt 264,51 (+17,34 %, 3 Zweige zu je 4 Kunden); Esau-Williams und Lokalsuche 277,77 (+5,01 % über dem Optimum), Kruskal 280,15 (+5,91 %) |
| Kruskal schlägt Esau-Williams | Seed 11 | Esau-Williams 310,64 (+9,59 % über dem Optimum 283,45), Kruskal 289,02 (+1,96 %), Lokalsuche und exakt 283,45 |
| Ortschaften (Q = 5) | 14 Kunden | MST 155,13 (zwei Zweige mit Bedarf 7); bester Baum 238,88 (+53,98 %), 4 Zweige (5/2/5/2); Kruskal +0,93 % darüber |
| Lehrbuchbeispiel (Q = 3) | Kreuz | MST 80; Q = 3: 88,28 (+10,36 %); Q = 2: 96,57 (+20,71 %); Q = 1: 116,57 (+45,71 %) |

Das **Lehrbuchbeispiel** ist von Hand nachzurechnen: das Depot W links, C in der Mitte, E rechts, N oben, S unten, Abstände 20, Diagonalen 20·√2 ≈ 28,28. Ohne Kapazität ist der Stern um C optimal (4 · 20 = 80, ein Zweig mit 4 Kunden). Mit Q = 3 hängt S direkt an W statt an C: {C, E, N} kostet 40 + 20, {S} 28,28 → 88,28. Mit Q = 2 entstehen zwei Zweige: {C, N} (20 + 20) und {E, S} (28,28 + 28,28) → 96,57. Mit Q = 1 hängt jeder direkt am Depot: 20 + 40 + 2 · 28,28 = 116,57. Die Einzelinstanz weicht von den Medianen ab - die Mediane sind die belastbaren Zahlen; die Presets prüfen sich zusätzlich über die 5 festen Instanzen gegen eine gemessene Spannweite des Medians des Preises der Kapazität (`tests/test_presets.py`).

## Modell und Verfahren

- **Instanz** (`cmst_scenario.py`): Depot (Knoten 0, am Rand bei (15, 50) oder in der Mitte) und n Kunden; **vollständiger Graph**, Kosten = euklidische Länge · Geländefaktor je Knotenpaar (symmetrisch); Bedarf einheitlich 1 oder gemischt 1–4 (eigener Zufallsstrom je Seed). **Ortschaften:** Verteiler mit Anschlussnehmern im Kreis (Radius etwa 6).
- **Zweigsatz** (`branch_cost`): `MST(S) + min_{v∈S} c(0, v)`; `exact_partition` löst die Partition per Teilmengen-DP mit O(3^n): `cost[S]` für jede zulässige Kundenmenge (Bedarf ≤ Q), `f[M]` = kleinste Kosten, M zu zerlegen (die Teilmenge enthält das niedrigste Bit von M). Wird bis n = 14 Kunden angeboten (etwa 2 s im ungünstigsten Fall).
- **Kruskal mit Kapazität** (`capacitated_kruskal`): alle Kanten inklusive Depotkanten nach (Kosten, Index); eine Kundenkante wird genommen, wenn sie zwei Komponenten verbindet, der vereinigte Bedarf ≤ Q ist und nicht beide schon am Depot hängen; eine Depotkante, wenn die Komponente noch nicht am Depot hängt. Findet immer einen Baum.
- **Esau-Williams** (`esau_williams`): Start Stern; die Ersparnis der Verschmelzung zweier Komponenten über die billigste Verbindungskante (u, v) ist max(w_A, w_B) − c_uv (w = Kosten der jeweiligen Depotkante; die teurere entfällt, die billigere bleibt); je Schritt die größte positive Ersparnis, deren vereinigter Bedarf ≤ Q ist (Gleichstand: kleinste Knotenindizes). `history` hält je Schritt Kante, Ersparnis, Kosten, entfallene Depotkante und die beste wegen der Kapazität unzulässige Verschmelzung.
- **Lokalsuche** (`local_search`): Kunden umhängen (auch in einen neuen Zweig), zwei Kunden tauschen, zwei Zweige zusammenlegen; jede Änderung mit den exakten Zweigkosten bewertet, beste Verbesserung je Runde, streng fallende Kosten. In der App startet sie von Esau-Williams **und** von Kruskal; das bessere Ergebnis zählt.
- **Preis** = Kosten / MST-Kosten − 1; **Aufschlag** = Kosten / Kosten des besten gefundenen Baums − 1 (bei Instanzen bis 14 Kunden ist das Optimum der beste Baum).

## Was nicht funktioniert hat / Grenzen

- **Erwartung "Depot in der Mitte macht die Kapazität teurer" - widerlegt:** bei Q = 4 kostet sie am Rand +13,5 %, in der Mitte nur +7,0 %; die Ersparnis gegen den Stern ist in der Mitte kleiner (47,0 % gegen 51,0 %), weil die Depotkanten dort kürzer sind; die Ursache ist nicht isoliert.
- **Erwartung "Esau-Williams ist nah am Optimum" - nur im Median wahr:** der Median des Aufschlags ist bei jedem Q null, aber Esau-Williams trifft den besten Baum nur in 52 bis 78 % der Instanzen, die größte Lücke liegt bei 10,8 %, in Ortschaften trifft er ihn nur in 6 %.
- **Erwartung "Kruskal mit Kapazität ist immer schlechter" - nein:** in 48 bis 70 % der Instanzen schlechter (Ortschaften: 80 %), aber in 4 bis 14 % besser als Esau-Williams (Preset "Kruskal schlägt Esau-Williams", Seed 11: +1,96 % gegen +9,59 %); bei größeren Q oft gleich.
- **Die Lokalsuche ist kein Allheilmittel:** sie steckt in lokalen Optima (Depot in der Mitte: +5,01 % über dem Optimum; als Kleinstinstanz mit 6 Kunden festgeschrieben) und trifft den besten Baum nur in 52 bis 90 % der Instanzen (in Ortschaften in 52 %). Bei Instanzen über 14 Kunden ist sie der beste Fund, wir wissen aber nicht, wie weit er vom Optimum entfernt ist.
- **Exakt ist klein:** die Teilmengen-DP hat O(3^n) und wird bis n = 14 Kunden angeboten; Branch-Cut-and-Price (Uchoa u. a. 2008) löst deutlich größere Instanzen, ist hier nicht gebaut. Aufschläge bei n > 14 sind Abstände zwischen Heuristiken, keine Lücken zum Optimum.
- **Ein Depot, eine Kapazität, ein Kabeltyp:** keine Kapazitätsstufen, keine mehreren Depots, keine Redundanz, kein Zeitverlauf; Einheits- oder Kleinbedarf 1–4; Q = 2 ist polynomiell (Matching), die Demo löst es trotzdem über die Partition.
- **Synthetisches Modell:** Punkte im Quadrat, vollständiger Graph, Geländefaktor; keine echten Netze.
- **Nicht gebaut:** Steiner-Baum, Prize-Collecting Steiner-Baum, Sensitivität, zufällige Spannbäume; Tabu-/GRASP-Varianten für den CMST.

## Verifikation

- **Zweigsatz direkt:** `branch_cost(S)` gleich dem Minimum über alle Bäume auf S ∪ {Depot} mit Depotgrad 1 (Brute-Force über Prüfer-Folgen, alle Teilmengen, Gleichstände).
- **Exaktheit:** die Mengenpartition gleich Brute-Force über **alle** Spannbäume des vollständigen Graphen mit Zweigbedarf ≤ Q (90 Instanzen mit 3 bis 5 Kunden × 7 Kapazitäten, Einheits- und gemischter Bedarf, Gleichstände; Kapazität kleiner als der größte Bedarf als "nicht lösbar" erkannt) und gleich einer unabhängigen Partitionsaufzählung (6 bis 8 Kunden, 25 Instanzen).
- **Gültigkeit:** jede Ausgabe ist ein Spannbaum aller n + 1 Knoten, jeder Zweig hat Bedarf ≤ Q, jeder Zweig genau eine Depotkante, die Kosten stimmen mit der Summe der Kanten überein.
- **Schrankenkette:** MST ≤ exakt ≤ Lokalsuche ≤ neu optimierter Esau-Williams ≤ Esau-Williams ≤ Stern, exakt ≤ Kruskal; die Lokalsuche endet in einem lokalen Optimum der Nachbarschaft (Umhängen, Tauschen, Zusammenlegen - nachgeprüft über alle Kandidaten).
- **Sonderfälle:** Q = ∞ → MST, Q = 1 → Stern, Q ≥ Zweigbedarf des MST → MST-Kosten, Q = 2 → Zweige mit höchstens 2 Kunden (gleich Brute-Force), n = 0, 1, gleiche Kosten überall, kollineare Kunden.
- **Esau-Williams-Buchführung:** jede Ersparnis > 0 und gleich dem Kostenrückgang, Schritte = Kunden − Zweige, Ende nur wenn keine zulässige Verschmelzung mit positiver Ersparnis übrig ist, jede gemeldete blockierte Verschmelzung verletzt wirklich die Kapazität.
- **Schwierige Fixtures** (per Skriptsuche gefunden, gegen Brute-Force bestätigt): Esau-Williams strikt teurer als exakt, Lokalsuche steckt fest, Kruskal strikt schlechter bzw. besser als Esau-Williams, Lokalsuche verbessert Esau-Williams.
- **Zahlen:** jede Zahl in App-Text und README ist in `tests/test_claims.py` über die echten Auswertungsfunktionen (`ev.analyse`, `ev.run_config`, `ev.sweep`, `ev.ew_quality`, `ev.capacity_curve`) belegt.

## Lokal starten

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app.py
python -m pytest tests -v
```

## Literatur

- Esau, L. R., & Williams, K. C. (1966). *On teleprocessing system design, Part II: A method for approximating the optimal network.* IBM Systems Journal 5(3), 142–147.
- Papadimitriou, C. H. (1978). *The complexity of the capacitated tree problem.* Networks 8(3), 217–230 (NP-schwer schon bei Einheitsbedarf für 3 ≤ Q ≤ ⌊n/2⌋).
- Uchoa, E., Fukasawa, R., Lysgaard, J., Pessoa, A., Poggi de Aragão, M., & Andrade, R. (2008). *Robust branch-cut-and-price for the capacitated minimum spanning tree problem over a large extended formulation.* Mathematical Programming 112, 443–472 (nur genannt, nicht gebaut; Autorenliste vor einer Zitierung gegen die Quelle prüfen).

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
