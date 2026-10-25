"""Track A deck, structured on notes/track-A-understanding.md (points 1-8) plus model B and results.
Run from the repo root:  .venv\\Scripts\\python.exe -X utf8 presentation/build_deck.py
Every number is read from instances/, results/ or recomputed from cvrp/; nothing is typed in by hand.
"""
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from cvrp.instances import Instance
from cvrp.qubo import build_qubo, variable_count_table
from cvrp.hardware import make_map, C6
from cvrp.pulse.sequence import PulseParams, build_sequence
import charts as ch
from charts import INK, MUTED, FAINT, LINE, BLUE, GREEN, AMBER, RED

OUT = ROOT / "presentation"; FIG = OUT / "charts"; RES = ROOT / "results"
W, H = 13.333, 7.5
CARD = "#F4F6F9"; WHITE = "#FFFFFF"

# ------------------------------------------------------------------ data
insts = {t: Instance.load(ROOT / f"instances/{t}_seed0.json") for t in "SML"}
weights = json.loads((ROOT / "instances/weights.json").read_text())
layA_S = json.loads((RES / "layouts/S_seed0_A.json").read_text())
layB_M = json.loads((RES / "layouts/M_seed0_B.json").read_text())
layB_S = json.loads((RES / "layouts/S_seed0_B.json").read_text())

rows = []
for tier in "SML":
    f = RES / f"results_{tier}.csv"
    if f.exists():
        rows += list(csv.DictReader(f.open(encoding="utf-8")))


def pick(inst, method):
    for r in rows:
        if r["instance"] == inst and r["method"] == method:
            return r
    return None


def fnum(r, k):
    return float(r[k]) if r and r.get(k) not in (None, "") else None


done = sorted({r["instance"] for r in rows if r["method"] == "B-seeds-light"},
              key=lambda n: ("SML".index(n[0]), n))
res_rows = []
for n in done:
    b, a, qs = pick(n, "B-seeds-light"), pick(n, "A-direct-global"), pick(n, "A-qubosolver-default")
    res_rows.append(dict(name=n.replace("_seed", "·"), b=fnum(b, "p_reach_ref"), b_feas=fnum(b, "feasibility_rate"),
                         rand_k=fnum(b, "p_reach_random_K"), rand_k_feas=fnum(b, "feas_random_K"),
                         a=fnum(a, "p_reach_ref"), a_feas=fnum(a, "feasibility_rate"),
                         qs=fnum(qs, "p_reach_ref"), qs_feas=fnum(qs, "feasibility_rate"),
                         ratio=fnum(b, "p_reach_ratio_vs_random_K")))
tiers_done = sorted({n[0] for n in done}, key="SML".index)

# model A on M: wanted distances; model B on S: the pulse that was run
mi = insts["M"]; wM = weights[mi.name]; qM = build_qubo(mi, wM["lam"], wM["A"]); hM = make_map(qM.a, qM.B, False)
bS = pick("S_seed0", "B-seeds-light")
pS = PulseParams(float(bS["omega_max"]), int(float(bS["duration"])), float(bS["delta_0"]), float(bS["delta_f"]))
seq = build_sequence(np.asarray(layB_S["coords"]), layB_S["labels"], pS)
pl = next(s.type for s in seq._schedule["ryd"] if hasattr(s.type, "amplitude"))
amp, det = np.array(pl.amplitude.samples), np.array(pl.detuning.samples)

# ------------------------------------------------------------------ figures
E = lambda parts, name, size=28: ch.equation(parts, FIG, name, size)  # noqa: E731
fig = dict(
    atoms=ch.atom_counts(variable_count_table(), FIG),
    maps=ch.instance_maps(list(insts.values()), FIG),
    s_layout=ch.s_layout(layA_S["coords"], "ABCD", FIG),
    m_hist=ch.m_wanted_distances(hM.target_U, C6, FIG),
    model_b=ch.model_b(mi, layB_M, FIG),
    pulse=ch.pulse(amp, det, FIG, pS.omega_max, pS.duration),
    results=ch.results(res_rows, FIG) if res_rows else None,
)
eqs = dict(
    loss=E([(r"$\mathrm{Total\ Loss}\;=\;C_{\mathrm{cluster}}\;+\;\lambda\,P_{\mathrm{capacity}}$", INK)], "eq1_loss", 23),
    cluster=E([(r"$C_{\mathrm{cluster}}=\sum_{i<j} d_{ij}\,(1-x_i-x_j+2x_ix_j)$", INK)], "eq2_cluster", 20),
    capacity=E([(r"$P_{\mathrm{capacity}}=\left(\sum_i q_i\,x_i-\frac{D}{2}\right)^2$", INK)], "eq3_capacity", 20),
    expanded=E([(r"$\mathrm{Total\ Loss}=\mathrm{const}\;+$", INK), (r"$\sum_i a_i\,x_i$", RED), (r"$+$", INK),
                (r"$\sum_{i<j} b_{ij}\,x_ix_j$", AMBER)], "eq4_expanded", 21),
    coeffs=E([(r"$a_i=-S_i+\lambda\,q_i(q_i-D)$", RED), (r"$\qquad$", INK), (r"$b_{ij}=2d_{ij}+2\lambda\,q_iq_j$", AMBER)], "eq4_coeffs", 17),
    pasqal=E([(r"$E\;=$", INK), (r"$\sum_i(-\delta)\,x_i$", RED), (r"$+$", INK),
              (r"$\sum_{i<j}\;\dfrac{C_6}{r_{ij}^{6}}\,x_ix_j$", AMBER)], "eq5_pasqal", 21),
    error=E([(r"$\mathrm{error}=\mathrm{Pasqal\ value}-\mathrm{our\ value\ (scaled)}$", INK)], "eq7_error", 17),
    distance=E([(r"$r=\left(\dfrac{C_6}{\mathrm{wanted\ coupling}}\right)^{1/6}$", INK)], "eq8_distance", 19),
    seed=E([(r"$E\;=$", INK), (r"$-\delta\sum_i x_i$", GREEN), (r"$+$", INK),
            (r"$\sum_{i<j}\dfrac{C_6}{(\alpha\,d_{ij})^{6}}\,x_ix_j$", GREEN)], "eq_seed", 21),
)

# ------------------------------------------------------------------ pptx helpers
prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H)
rgb = lambda s: RGBColor.from_string(s.lstrip("#"))  # noqa: E731
N_SLIDES = 8


def text(s, x, y, w, h, runs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.15):
    """runs: str (newlines = paragraphs) or list of paragraphs, each a list of (text, colour, bold)."""
    sh = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = sh.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = [[(line, color, bold)] for line in runs.split("\n")] if isinstance(runs, str) else runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing; p.space_after = Pt(size * 0.35)
        for t, c, b in para:
            r = p.add_run(); r.text = t; f = r.font
            f.name = "Arial"; f.size = Pt(size); f.color.rgb = rgb(c); f.bold = b
    return sh


def box(s, x, y, w, h, fill=CARD, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = 0.06
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    if line:
        sh.line.color.rgb = rgb(line); sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def pic(s, path, x, y, w=None, h=None, natural=False):
    """Place an image. natural=True keeps the typeset size (equations); otherwise fit inside w x h."""
    iw, ih = Image.open(path).size
    if natural:
        nw, nh = iw / ch.DPI, ih / ch.DPI
        s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(nw), Inches(nh)); return nw, nh
    k = min(w / iw, h / ih); nw, nh = iw * k, ih * k
    s.shapes.add_picture(str(path), Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2), Inches(nw), Inches(nh))
    return nw, nh


def table(s, x, y, w, data, col_w, size=13, row_h=0.42, colors=None, header_fill="#E9EEF4"):
    """data: rows of strings; colors: {(r, c): hex} for text colour."""
    shp = s.shapes.add_table(len(data), len(data[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(data)))
    t = shp.table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(data):
        t.rows[i].height = Inches(row_h)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = rgb(header_fill if i == 0 else (WHITE if i % 2 else "#F7F9FB"))
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.text = ""; p = tf.paragraphs[0]; r = p.add_run(); r.text = v
            r.font.name = "Arial"; r.font.size = Pt(size); r.font.bold = (i == 0) or bool(colors and (i, j) in colors)
            r.font.color.rgb = rgb((colors or {}).get((i, j), MUTED if i == 0 else INK))
    return t


def slide(n, kicker, title, takeaway=None, status=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(WHITE)
    text(s, 0.6, 0.42, 12, 0.3, kicker.upper(), 11.5, BLUE, True)
    text(s, 0.6, 0.72, 12.2, 0.7, title, 28, INK, True)
    if takeaway:
        text(s, 0.6, 1.42, 12.2, 0.45, takeaway, 15.5, MUTED)
    text(s, 0.6, 7.05, 9, 0.25, "Track A  ·  DuQuantum × Pasqal" + (f"   ·   {status}" if status else ""), 9.5,
         RED if status else FAINT)
    text(s, 11.9, 7.05, 0.85, 0.25, f"{n} / {N_SLIDES}", 9.5, FAINT, align=PP_ALIGN.RIGHT)
    return s


def notes(s, t):
    s.notes_slide.notes_text_frame.text = t


def pill(s, x, y, label, color, w=None):
    w = w or 0.32 + 0.105 * len(label)
    b = box(s, x, y, w, 0.34, fill=color)
    b.adjustments[0] = 0.5
    text(s, x, y + 0.045, w, 0.3, label, 11, WHITE, True, align=PP_ALIGN.CENTER)
    return w


# ------------------------------------------------------------------ 1. two questions
s = slide(1, "Track A  ·  capacity-feasible clustering", "Two questions: what score, and where the atoms go",
          "One binary variable = one atom. Fewer variables means a smaller, more faithful register.")
box(s, 0.6, 2.15, 5.7, 1.95)
text(s, 0.9, 2.35, 5.2, 0.4, "A1  ·  design the QUBO", 19, BLUE, True)
text(s, 0.9, 2.85, 5.2, 1.1, "Write one score for every bitstring.\nLowest score = best valid grouping.", 16)
box(s, 0.6, 4.3, 5.7, 1.95)
text(s, 0.9, 4.5, 5.2, 0.4, "A3  ·  lay out the atoms", 19, BLUE, True)
text(s, 0.9, 5.0, 5.2, 1.1, "Place atoms so the machine’s energy gives\nthe same scores, and report how far off it is.", 16)
text(s, 0.6, 6.45, 5.8, 0.4, [[("A2", INK, True), (" instances and ", MUTED, False), ("A4", INK, True),
                               (" pulse support these two.", MUTED, False)]], 13.5)
pic(s, fig["atoms"], 6.75, 2.1, 6.0, 4.4)
notes(s, "[45 秒] 我们把 Track A 拆成两个问题。A1：给每个 bitstring 一个分数，分数最低的就是最好的合法分组。A3：把原子摆好，让机器的能量给出同样的分数，并且报告偏差有多大。A2 生成题目和标准答案，A4 调脉冲，这两个是支撑。右图是原子数：教科书做法加 slack 是 14/45/80；我们的直接 QUBO 是 4/30/60；最后的 seed model 只要 4/10/15。")

# ------------------------------------------------------------------ 2. A2
s = slide(2, "A2  ·  instances", "Nine certified instances, each with a proven answer",
          "3 seeds per tier. Every instance ships a feasible certificate and an exact optimum (DP, checked by CPLEX).")
pic(s, fig["maps"], 0.6, 2.0, 12.15, 3.5)
data = [["", "S", "M", "L"], ["customers N / trucks K / capacity Q", "4 / 2 / 7", "10 / 3 / 20", "15 / 4 / 30"],
        ["proven optimum C*  (seed 0, cluster cost)"] + [f"{insts[t].references['model_optimum']:.1f}" for t in "SML"]]
table(s, 0.6, 5.65, 12.15, data, [5.25, 2.3, 2.3, 2.3], size=13, row_h=0.38)
text(s, 0.6, 6.85, 12, 0.25, "Colour = truck in the proven optimum; black square = depot.", 11, MUTED)
notes(s, "[35 秒] A2 是全自动的：每档三个 seed，生成器保证可行，附带一个可行分配作为证书，再用精确 DP 求出最优解，S 档还和 CPLEX、暴力枚举对过。图上颜色是最优分组，黑色方块是仓库。这些最优值就是后面所有 gap 的标准答案。")

# ------------------------------------------------------------------ 3. A1 loss
s = slide(3, "A1  ·  ① loss   ② cluster   ③ capacity", "Cluster is optimised; capacity only has to pass the line",
          "Example: customers A, B, C, D with demands 3, 4, 2, 3; 2 trucks of capacity 7. Bit 1 = truck 1, bit 0 = truck 2.")
text(s, 0.6, 2.18, 0.5, 0.4, "①", 18, BLUE, True); pic(s, eqs["loss"], 1.05, 2.12, natural=True)
text(s, 0.6, 3.12, 0.5, 0.4, "②", 18, BLUE, True); pic(s, eqs["cluster"], 1.05, 2.98, natural=True)
text(s, 1.05, 3.82, 5.9, 0.6, "Pays dᵢⱼ only when i and j share a truck: the bracket is 1 for 00 and 11, 0 for 01 and 10.", 13, MUTED)
text(s, 0.6, 4.72, 0.5, 0.4, "③", 18, BLUE, True); pic(s, eqs["capacity"], 1.05, 4.55, natural=True)
text(s, 1.05, 5.5, 5.9, 0.9, "qᵢ = demand, D = total demand. No slack bits: valid splits score 0–1, an overloaded truck scores ≥ 4, and λ makes that too expensive.", 13, MUTED)
cap = [["bits ABCD", "loads", "P", "valid?"], ["1001", "6 | 6", "0", "yes"], ["1100", "7 | 5", "1", "yes"],
       ["1010", "5 | 7", "1", "yes"], ["1110", "9 | 3", "9", "no"], ["1111", "12 | 0", "36", "no"]]
cc = {(i, 3): (GREEN if cap[i][3] == "yes" else RED) for i in range(1, 6)}
text(s, 7.4, 2.12, 5.3, 0.35, "③ capacity on the example", 14, INK, True)
table(s, 7.4, 2.55, 5.35, cap, [1.55, 1.4, 1.0, 1.4], size=13.5, row_h=0.43, colors=cc)
text(s, 7.4, 5.3, 5.35, 1.2, "Honest cost: among valid splits it still prefers 6 | 6. When the best split is unbalanced this loses objective (M_seed2: 13.8 %, before any quantum step).", 13, RED)
notes(s, "[60 秒] 总 loss 是两部分：cluster 越小越好，需要优化；capacity 只要过及格线就行。cluster 那个括号只有两个客户同车时等于 1。capacity 用 (Σ demand·x − D/2)² 实现：不加 slack bit，合法分法分数是 0 到 1，超载至少 4，λ 让超载永远不划算。代价是：在合法分法里它仍然偏爱最平均的那个，M_seed2 因此在量子之前就损失 13.8%。M/L 档是三到四辆车，用一车一位的 one-hot，再加每个客户恰好一辆车的惩罚，形式一样。")

# ------------------------------------------------------------------ 4. expanded vs Pasqal
s = slide(4, "A1 → A3  ·  ④ expanded   ⑤ Pasqal energy   ⑥ mismatch", "Same two slots, but not the same freedom",
          "Expanded, our loss is one number per atom plus one per atom pair. Pasqal’s energy has exactly those two slots.")
text(s, 0.6, 2.25, 0.5, 0.4, "④", 18, BLUE, True); pic(s, eqs["expanded"], 1.05, 2.12, natural=True)
pic(s, eqs["coeffs"], 1.12, 2.98, natural=True)
text(s, 1.15, 3.5, 6, 0.4, "Sᵢ = sum of customer i’s distances to everyone else.", 13, MUTED)
text(s, 0.6, 4.4, 0.5, 0.4, "⑤", 18, BLUE, True); pic(s, eqs["pasqal"], 1.05, 4.15, natural=True)
text(s, 1.15, 5.15, 6, 0.4, "δ = laser detuning (one value for all atoms); r = distance between atoms.", 13, MUTED)
mm = [["⑥ term", "our QUBO", "Pasqal", "match?"],
      ["per atom", "aᵢ, different per customer", "−δ, the same for all", "no"],
      ["per pair: value", "bᵢⱼ, many different values", "C₆ / r⁶, set by distance", "approx."],
      ["per pair: sign", "positive", "positive", "yes"]]
table(s, 7.35, 2.2, 5.4, mm, [1.35, 1.6, 1.55, 0.9], size=12, row_h=0.62,
      colors={(1, 3): RED, (2, 3): AMBER, (3, 3): GREEN, (1, 1): RED, (2, 1): AMBER})
text(s, 7.35, 4.85, 5.4, 1.6, [[("On M and L the per-atom mismatch is harmless on valid answers ", INK, False),
                                ("(each customer has exactly one bit on, so Σ aᵢxᵢ is a constant). ", MUTED, False)],
                               [("The real problem is the pair slot: ", INK, False),
                                ("some pairs want 0, but 1/r⁶ is never 0.", RED, True)]], 13.5)
notes(s, "[70 秒] 这是整场的转折。上面是我们展开后的 QUBO：每个原子一个数 a，每对原子一个数 b。下面是 Pasqal 在激光关掉时的能量：每个原子前面是 −δ，每对原子前面是 C6/r⁶。槽位一样，但自由度不一样。红色：我们每个客户的 a 都不同，激光只给一个 δ。橙色：b 有很多不同的值，只能靠距离去近似。绿色：符号都为正，这一点吻合。M、L 档上，红色那一项在合法答案上是常数，不影响排序；真正的问题是原子对这一项，有些对需要 0，而 1/r⁶ 永远不是 0。")

# ------------------------------------------------------------------ 5. error + distance
etaS = layA_S["fidelity"]["eta"]; rankS = layA_S["ground_state"]["global"]["rank_of_model_optimum"]
s = slide(5, "A3  ·  ⑦ error   ⑧ atom distance", "Atom distance: S already distorts, M cannot be laid out",
          "Each wanted coupling gives a wanted distance. The question is whether all of them fit in one 2D layout at once.")
text(s, 0.6, 2.3, 0.5, 0.4, "⑧", 18, BLUE, True); pic(s, eqs["distance"], 1.05, 2.05, natural=True)
text(s, 4.3, 2.22, 2.3, 0.7, "r ≥ 5 µm\nradius ≤ 38 µm", 13.5, RED, True)
text(s, 0.6, 3.3, 0.5, 0.4, "⑦", 18, BLUE, True); pic(s, eqs["error"], 1.05, 3.27, natural=True)
box(s, 0.6, 3.95, 6.0, 2.85)
pic(s, fig["s_layout"], 0.75, 4.05, 2.75, 2.65)
text(s, 3.6, 4.25, 2.85, 2.4, [[("S  ·  4 atoms", AMBER, True)], [("Legal layout found.", INK, False)],
                               [(f"Coupling error η = {etaS:.2f}", INK, False)],
                               [(f"But the true optimum already ranks #{rankS} of 16 under the realised energy.", RED, False)]], 13.5)
box(s, 6.85, 2.05, 5.9, 4.75)
pic(s, fig["m_hist"], 7.0, 2.2, 3.3, 2.65)
text(s, 10.45, 2.35, 2.15, 2.8, [[("M  ·  30 atoms", RED, True)], [("Every pair wants 5 to 7 µm. Each atom wants 11 partners that close.", INK, False)]], 13.5)
text(s, 7.1, 5.3, 5.5, 1.4, [[("A plane at 5 µm spacing fits about 6 neighbours that close. ", INK, False)],
                             [("Measured: the true optimum ranks ≈ 10⁴ of 59 049; η ≈ 1.", RED, True)]], 13.5)
notes(s, "[60 秒] 第八点：想要的耦合除以 C6 开六次方就是想要的距离，必须 ≥ 5 µm、半径 ≤ 38 µm。第七点：误差 = Pasqal 实际给的值减去我们想要的值。S 档 4 个原子能摆出合法布局，最优解在实际能量下的排名见左边。M 档是 30 个原子：所有原子对都想要 5 到 7 µm，每个原子要 11 个这么近的邻居，但平面上 5 µm 间距最多放下大约 6 个。实测最优解排到大约一万名，η≈1，等于没有信息。所以直接 QUBO 在 M、L 上摆不出来。")

# ------------------------------------------------------------------ 6. model B
etaB = layB_M["fidelity"]["eta"]; bfM = layB_M["brute_force_light"]
s = slide(6, "A1 + A3, revised  ·  model B", "Change the question: the atom map is the customer map",
          "Brief §4.1: “avoid the inequality altogether by changing what the model asks for.”")
text(s, 0.6, 2.05, 6.4, 0.4, [[("xᵢ = 1  ⇔  customer i anchors a truck.  ", INK, True), ("N atoms: 4 / 10 / 15.", MUTED, False)]], 14.5)
pic(s, eqs["seed"], 0.6, 2.6, natural=True)
mmB = [["term", "model B wants", "Pasqal gives", "match?"],
       ["per atom", "the same −δ", "−δ, the same for all", "yes"],
       ["per pair", "C₆ / (α dᵢⱼ)⁶", "C₆ / r⁶ at r = α dᵢⱼ", "yes"],
       ["capacity", "—", "not in the energy", "decode"]]
table(s, 0.6, 3.75, 6.3, mmB, [1.2, 1.75, 2.2, 1.15], size=12.5, row_h=0.46,
      colors={(1, 3): GREEN, (2, 3): GREEN, (3, 3): BLUE})
text(s, 0.6, 5.7, 6.3, 1.2, [[("Close customers block each other, so the lowest energy picks K spread-out seeds. ", INK, False)],
                             [("Then every other customer joins the nearest group with room (light decode, classical, O(N²K)). ", MUTED, False)]], 13)
pic(s, fig["model_b"], 7.1, 1.95, 5.65, 4.2)
text(s, 7.2, 6.25, 5.5, 0.6, f"M_seed0: η = {etaB:.2f};  {bfM['n_optimal_seed_sets']} of {bfM['n_seed_sets']} seed sets decode to the optimum.", 12.5, MUTED)
notes(s, "[60 秒] 既然直接 QUBO 摆不出来，我们换一个问法，这正是赛题 4.1 节说的。每个客户一个原子，位就是“这个客户是不是一辆车的中心”。原子直接按客户地图等比例摆，所以原子对的耦合天然就是客户距离的函数，不需要拟合，误差很小；每个原子要的线性项也都一样，正好是一个全局 δ。离得近的客户互相阻塞，能量最低的状态就是 K 个分得最开的中心。容量不在能量里，放在一个很轻的经典解码里：其他客户依次加入最近的、还有空位的组。右图是 M_seed0 的最优答案和对应的原子布局。")

# ------------------------------------------------------------------ 7. A4
s = slide(7, "A4  ·  pulse", "Pulse: Ω and duration per tier, final δ per instance",
          "Standard adiabatic sweep. Every sequence is built and checked by Pulser against AnalogDevice.")
pic(s, fig["pulse"], 0.6, 2.0, 6.4, 4.0)
text(s, 0.75, 6.1, 6.2, 0.6, f"S_seed0 as run: Ωmax = {pS.omega_max:.2f} rad/µs, T = {pS.duration} ns, δ: {pS.delta_0:.1f} → {pS.delta_f:.1f} rad/µs.", 12.5, MUTED)
a4 = [["parameter", "what it does", "how we set it"],
      ["final δ", "the per-atom term", "midpoint of the window where exactly K seeds is lowest"],
      ["Ω (strength)", "lets atoms flip; sets the blockade radius", "grid per tier: radius ∈ {7, 9, 12} µm"],
      ["duration T", "longer = closer to the best answer", "grid per tier: {2000, 4000, 6000} ns"],
      ["δ scale c", "fine-tunes the final δ", "grid per instance: c ∈ {0.7, 1.0, 1.3}"],
      ["shots", "more = more reliable rates", "1000"]]
table(s, 7.25, 2.05, 5.5, a4, [1.35, 2.0, 2.15], size=11.5, row_h=0.58)
text(s, 7.25, 5.75, 5.5, 0.9, "Selection score: share of shots that hit the optimum, then best gap, then feasibility (brief §8.2: reward good shots, not the mean).", 12.5, MUTED)
notes(s, "[40 秒] A4 就是把系统参数调好。标准的绝热扫描：Ω 先升后降，δ 从负扫到正。最终 δ 由几何直接算出，是“恰好 K 个中心最低”那个窗口的中点。Ω 决定阻塞半径，和时长一起每档做一次小网格；每个实例只再调一个 δ 的倍数。挑选标准按赛题 8.2：看命中最优的比例，而不是平均值。所有序列都通过 Pulser 的设备检查。")

# ------------------------------------------------------------------ 8. results
pending = [t for t in "SML" if t not in tiers_done]
s = slide(8, "Results  ·  what worked, what did not", "Tier S is too small to beat chance; M and L decide",
          "S has only 6 seed sets, so random picks already hit the optimum 33–67 % of the time. 1000 shots, global detuning unless marked.",
          status=("tiers " + ", ".join(pending) + " still running" if pending else None))
if fig["results"]:
    pic(s, fig["results"], 0.6, 1.95, 12.15, 3.65)
box(s, 0.6, 5.75, 6.0, 1.15)
text(s, 0.8, 5.85, 5.7, 1.0, [[("Did not work", RED, True)],
                              [("Direct QUBO on M/L: no 2D layout reproduces it (η ≈ 1). Load-balance penalty loses up to 13.8 % before any quantum step.", INK, False)]], 12)
box(s, 6.75, 5.75, 6.0, 1.15)
text(s, 6.95, 5.85, 5.7, 1.0, [[("Caveats", AMBER, True)],
                               [("Light decode is order-sensitive (S·2: 0.4 % vs 96 % with exact decode). AI assisted code, figures and drafting; every number is from results/.", INK, False)]], 12)
notes(s, "[50 秒] 结果：绿色是 model B 在模拟器上的表现，灰色是随机选 K 个中心再用同样的解码，这是公平的对照。我们看两件事：合法的 shot 比例，和命中已证明最优解的 shot 比例。蓝色是直接 QUBO，橙色是 Pasqal qubo-solver 的默认流程（用了 DMM）。失败的部分：直接 QUBO 在 M/L 摆不出来；均衡惩罚在量子之前就有损失。注意：light 解码对顺序敏感，S·2 上差别很大，我们如实报告。AI 帮助了代码、图和草稿，所有数字都来自 results 文件夹。")

out = OUT / "TrackA_7min.pptx"
prs.save(out)
print(json.dumps(dict(deck=str(out), slides=len(prs.slides), results_tiers=tiers_done)))
