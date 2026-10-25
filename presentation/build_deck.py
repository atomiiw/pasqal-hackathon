"""User's A2 → A1 → A3 → A4 storyline. Independent figure functions: charts.py.
Run: .venv/Scripts/python.exe presentation/build_deck.py
"""
from pathlib import Path
import sys,json,csv
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import numpy as np
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
from cvrp.instances import Instance,validate
from cvrp.qubo import build_qubo,variable_count_table
from cvrp.hardware import make_map,C6
from cvrp.pulse.sequence import PulseParams,build_sequence
import charts

OUT=ROOT/'presentation'; ASSETS=OUT/'charts'
insts={t:Instance.load(ROOT/f'instances/{t}_seed0.json') for t in 'SML'}
weights=json.loads((ROOT/'instances/weights.json').read_text())
for inst in insts.values(): assert validate(inst,inst.certificate)[0]
inst=insts['M']; wt=weights[inst.name]; q=build_qubo(inst,wt['lam'],wt['A']); hmap=make_map(q.a,q.B,False,s_factor=.85)
coords=np.array([[6*(c+.5*(r%2)),6*np.sqrt(3)/2*r] for r in range(5) for c in range(6)]); coords-=coords.mean(axis=0)
p=PulseParams(10,4000,-30,hmap.delta_global); seq=build_sequence(coords,q.labels,p)
pulse=next(slot.type for slot in seq._schedule['ryd'] if hasattr(slot.type,'amplitude'))
amp=np.array(pulse.amplitude.samples); det=np.array(pulse.detuning.samples)
rows=list(csv.DictReader((OUT/'mock_metrics.csv').open(encoding='utf-8')))
figs={'atoms':charts.atom_counts(variable_count_table(),ASSETS),'instances':charts.instance_maps(list(insts.values()),ASSETS),
 'loss':charts.loss_equations(ASSETS),'energy':charts.energy_comparison(ASSETS),'distance':charts.distances(hmap.target_U,C6,ASSETS,json.loads((OUT/'seed_layout_example.json').read_text())['coords_um']),
 'pulse':charts.pulse_waveforms(amp,det,ASSETS),'results':charts.mock_results(rows,ASSETS),'expected':charts.expected_loss(ASSETS)}
prs=Presentation(); prs.slide_width=Inches(16); prs.slide_height=Inches(9)
INK='#24292F'; MUTED='#59616A'; BLUE=charts.BLUE; GREEN=charts.GREEN; RED=charts.RED
def rgb(s): return RGBColor.from_string(s.lstrip('#'))
def text(s,x,y,w,h,value,size=22,color=INK,bold=False):
    sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=sh.text_frame; tf.word_wrap=True
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    for i,line in enumerate(value.split('\n')):
        pp=tf.paragraphs[0] if i==0 else tf.add_paragraph(); pp.text=line; pp.font.name='Arial'; pp.font.size=Pt(size); pp.font.color.rgb=rgb(color); pp.font.bold=bold; pp.space_after=Pt(9)
    return sh
def rule(s,x,y,w):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(.018)); sh.fill.solid(); sh.fill.fore_color.rgb=rgb('#DCE2E7'); sh.line.fill.background()
def pic(s,path,x,y,w,h):
    iw,ih=Image.open(path).size; scale=min(w/iw,h/ih); nw,nh=iw*scale,ih*scale
    s.shapes.add_picture(str(path),Inches(x+(w-nw)/2),Inches(y+(h-nh)/2),width=Inches(nw),height=Inches(nh))
def base(n,section,title,sub,status='MODEL / CLASSICAL DATA'):
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=rgb('#FFFFFF')
    text(s,.65,.33,14,.3,f'TRACK A  |  {section}',13,BLUE,True); text(s,.65,.94,14.7,.72,title,32,INK,True); text(s,.65,1.8,14.7,.65,sub,19,MUTED)
    rule(s,.65,2.5,14.7); rule(s,.65,8.35,14.7); text(s,.65,8.55,13.3,.25,f'DuQuantum × Pasqal  |  {status}',11,RED if 'MOCK' in status else MUTED); text(s,14.3,8.55,1,.25,f'{n} / 7',11,MUTED)
    return s
def notes(s,t): s.notes_slide.notes_text_frame.text=t
def caption(s,t,color=MUTED): text(s,.8,7.78,14.35,.45,t,16,color)

s=base(1,'TWO QUESTIONS','What QUBO? Where do the atoms go?','One variable = one atom. A1 designs the loss; A3 makes Pasqal’s E equation approximate it.')
text(s,.8,2.9,6.4,.5,'A1 — design the QUBO',26,BLUE,True); text(s,.8,3.55,6.3,1.1,'Cluster function: optimize.\nCapacity: meet the passing line.',23)
text(s,.8,5.05,6.4,.5,'A3 — choose atom positions',26,BLUE,True); text(s,.8,5.7,6.3,1.0,'Minimize disagreement between\nour QUBO and the machine’s energy.',23)
pic(s,figs['atoms'],7.2,2.85,8.1,4.6); caption(s,'Workflow: A2 instances → A1 loss → A3 atom distances → A4 pulse. Model B counts are a direction under test.')
notes(s,'[45 秒] 我们按自己的理解，把 challenge 拆成两个主要问题：A1 怎么设计 QUBO，以及 A3 怎么摆放 atoms，使 Pasqal 的 E equation 尽量接近我们的 loss。A2 是自动生成可行 instances 和 references；A4 是把模型接到 pulse 和 emulator。右边是真实变量数量：direct baseline 是 4/30/60，textbook slack 是 14/45/80。Model B 选择 seeds，用 4/10/15 atoms，但仍在测试，不能当作已验证的量子结果。')

s=base(2,'A2 — GROUND TRUTH','Instances come with a feasible answer and a reference.','A2 is automated: seeded generation → certificate → validator → exact classical reference.')
pic(s,figs['instances'],.75,2.7,14.5,3.65)
for j,(t,i) in enumerate(insts.items()):
    x=.95+j*4.85; text(s,x,6.6,4.55,.8,f'{t}_seed0  |  C* = {i.references["model_optimum"]:.2f}',21,BLUE,True); text(s,x,7.18,4.55,.35,'Proven constrained clustering optimum',16,MUTED)
caption(s,'3 seeds per tier (0, 1, 2); maps show certificates, not EMU outputs. Depot fixed at (50, 50).')
notes(s,'[35 秒] A2 是支持步骤，快速讲完。S/M/L 的 N K Q 按比赛要求固定；locations 和 demands 从 seeds 生成。每个 instance 有 feasible certificate 和 validator，并报告 load ratio 和最大 demand ratio。图上是 seed0 certificates，下面是 repository 保存的 proven constrained model optima。三个 seeds 一共九个 instances，参考值通过 exact classical DP 得到，不能称为 quantum output。')

s=base(3,'A1 — LOSS','Cluster: optimize. Capacity: pass the line.','The desired constraint is Lₖ ≤ Q. Our direct QUBO uses load balance as a slack-free surrogate.')
pic(s,figs['loss'],.75,2.68,14.5,4.5)
text(s,.95,7.18,14,.45,'aₐ = constant per atom   |   bₐᵦ = constant per atom pair   |   assignment: exactly one vehicle',20,BLUE)
caption(s,'M/L one-hot model shown; S uses one bit/customer. Balance still penalizes unequal feasible loads: it is not a flat pass/fail penalty.',RED)
notes(s,'[80 秒] 先定义我们真正想要的 loss：cluster function 越小越好；capacity 只要通过及格线，也就是每个 load 不超过 Q，就可以，不应继续追求更满或更平均。实际 direct baseline 使用 sum(L-D/K)^2 来省 slack，它会在 feasible 范围内继续奖励 balance，因此不完全符合我们想要的 pass/fail。这是明确的模型失真。M/L 还需要 assignment penalty，保证每个 customer exactly one vehicle。展开后每个 atom 前有一个 linear coefficient a，每对 atoms 有一个 coupling b，constant 不改变排序。下一页就将这两个 coefficient slots 和 Pasqal energy 对齐。S 使用二元 vehicle 标签，exactly-one assignment 自动满足。')

s=base(4,'A1 → A3 — THE PIVOT','Which QUBO terms fit Pasqal’s E equation?','Same two slots: a constant per atom and an interaction per atom pair. Color identifies the inconsistency.')
pic(s,figs['energy'],.75,2.65,14.5,3.6)
text(s,.95,6.25,4.45,1.15,'MATCH: positive pair sign.\nValues still need a joint 2D fit.',20,GREEN,True)
text(s,5.6,6.25,4.55,1.15,'MISMATCH: nonuniform aₐ\nversus one global −δ.',20,RED,True)
text(s,10.4,6.25,4.7,1.15,'MISMATCH: target-zero pairs\nand many strong partners.',20,RED,True)
caption(s,'M/L: linear mismatch is constant on valid one-hot assignments, but changes invalid states. This does not hold for S.')
notes(s,'[85 秒] 这页是主线的转折。上面是 scaled QUBO，下面是 Omega 回到零时 Pasqal 的 classical energy，每项按同样位置对齐。Green 表示 positive pair sign 与硬件一致，但不代表能精确 fit。Red 是 nonuniform linear coefficients 与 shared global detuning 的冲突。对 valid M/L one-hot assignments，这部分差异是常数，所以 valid states 的排序不会因这项而改变，但 invalid strings 的能量会变。另有 target-zero pairs，而 1/r6 永远 positive；以及每个 atom 想要太多相近强度的 partners，无法各自独立设置距离。我们不把 dense baseline 的问题归咎于 detuning，真正重要的是 jointly realizable geometry。')

s=base(5,'A3 — ATOM DISTANCE & EXPECTED LOSS','Fit the energy ranking, not just each distance.','rₐᵦ* = (C₆ / Uₐᵦ*)¹⁄⁶, with U* = s b. Minimum spacing 5 µm; register radius ≤ 38 µm.')
pic(s,figs['distance'],.8,2.87,7.0,3.8)
text(s,8.05,2.95,7.0,.6,'Dense baseline: a measured limit',24,RED,True)
text(s,8.05,3.68,6.8,1.3,'PLAN §6 reports M ranks ≈10⁴ / 59,049\nassignment-valid states; coupling error η ≈ 1.\nApproximate logged findings, not new runs.',19,MUTED)
text(s,8.05,5.2,6.8,1.65,'Next: model B — N seed atoms.\nEnergy selects spread-out seeds.\nNearest-fit decode checks capacity.\nCompare against random K-seed sets.',20,BLUE)
pic(s,figs['expected'],.9,6.95,14.1,.63)
caption(s,'M_seed0: baseline target distances and Pulser-valid model B trial layout. No EMU result; report P(F) separately.')
notes(s,'[95 秒] A3 控制 positions，A4 控制 Omega detuning duration。把一个 coupling 反推为一个 distance 很容易，但所有 distances 必须同时来自一张合法 2D layout。左图来自 M_seed0 真实 target coefficients：目标距离挤在窄范围。PLAN 第六节记录 dense baseline approximate results：M 的 model optimum 在 59049 个 assignment-valid states 中落到大约一万名，eta 大约一。59049 是 3 的十次方，包括 capacity-infeasible assignments；不要说成全都 capacity-feasible。这里是日志摘要，不是本轮重跑。PLAN 仍在写 sparsification，代码新加 seeds.py；所以 Model B 是 next direction under test。量子部分选 spread-out seeds，classical capacity-aware nearest-fit decoder 分配其他 customers，失败计入 feasibility。Expected feasible loss = sum over feasible x of p(x|positions,pulse)*cluster_cost(decode(x)) 除以 feasibility probability。不能把 embedding eta 当作 expected clustering loss。')

s=base(6,'A4 — FIGURING OUT THE SYSTEM','Fix amplitude and duration; tune detuning per instance.','Proposed search policy, not completed optimization. All candidates must pass Pulser device validation.',status='PROPOSED PULSE / NO NEW EMU RESULTS')
pic(s,figs['pulse'],.8,2.8,8.2,4.55)
text(s,9.35,2.95,5.7,.5,'Fixed within each tier — proposed',23,BLUE,True)
text(s,9.35,3.65,5.7,.8,'Ωpeak = 10 rad/µs; T = 4,000 ns\nStarting policy shared across S/M/L.',20)
text(s,9.35,4.63,5.7,.5,'Per-instance detuning grid',23,BLUE,True)
text(s,9.35,5.3,5.7,1.8,'Direct: δf = {0.8, 1, 1.2} × δmap\nSeeds: grid inside candidate K window\nδ₀ = −{0.5, 1, 1.5} × Ωpeak\nCheck range and sequence legality first.',19)
caption(s,'Shown: Pulser-constructed M_seed0 direct candidate, δf = −s mean(a). Seed-window cardinality needs a full-state check.')
notes(s,'[35 秒] A4 讲短一些。Amplitude 和 duration 先在 tier 内固定，proposed starting policy 都用 10 rad/us 和 4000 ns，不是假装已经找到 optimal settings。每个 instance final detuning 根据 mapping 来，direct model 以 minus s mean(a) 为中心，提出 0.8/1/1.2 grid。Seed model 以 candidate K-excitation window 为范围，但必须 full bitstring 检查 cardinality，不能仅看相邻 excitation numbers 就保证 ground state。Initial detuning 是负 0.5/1/1.5 倍 Omega。这是待跑的 search settings，不是实测最佳值。所有参数必须实际通过 Pulser validation。')

s=base(7,'RESULTS / WHAT DID NOT WORK','Report feasibility, model gap, CVRP gap and atoms.','MOCK performance until real EMU output exists. Keep direct QUBO and seed model B results separate.',status='MOCK PERFORMANCE — REPLACE BEFORE SUBMISSION')
pic(s,figs['results'],.75,2.75,14.5,3.5)
text(s,.95,6.4,6.65,1.0,'Known direct-model limit: M_seed2\n329.21 → 374.60 clustering cost (+13.8%).',21,RED,True)
text(s,8.0,6.4,6.9,1.0,'Atoms A: 4 / 30 / 60; B: 4 / 10 / 15.\nB needs random-seed baseline + decode audit.',21,BLUE)
caption(s,'MOCK: means and min–max across 3 seeds. CVRP gap uses exact classical routing. AI assisted code, figures and drafting.')
notes(s,'[45 秒] 上面是明确标记的 mock performance：feasibility rate、model gap、CVRP gap，只是 placeholders，不是 EMU measurements，也不是 Model B 预测。正式结果按模型分别报告 atom count、reference-hit probability、embedding error、emulator settings。真实 failure example 是 M_seed2，balance surrogate 让 clustering objective 从 329.21 到 374.60，多 13.8%，发生在任何量子运行之前。Model B 要和 random K-seed sampler 用同一个 light decoder 对照，明确 classical work。AI 帮助 code、figures 和 draft，团队负责 review。')
deck=OUT/'TrackA_7min_MOCK.pptx'; prs.save(deck)
metadata={'storyline':['Two questions','A2','A1 loss and expansion','QUBO vs Pasqal E','A3 distances and expected loss','A4 pulse','Results and limitations'],'timings_seconds':[45,35,80,85,95,35,45],
 'figure_module':'presentation/charts.py','figure_formats':['PNG 300dpi','SVG'],'model_status':{'direct':'documented baseline','B':'implemented, under test, no EMU results supplied','PLAN_conflict':'PLAN §6 still says sparsification; seeds.py implements B'},
 'real_sources':['cvrp/qubo.py','cvrp/seeds.py','cvrp/pulse/sequence.py','instances/*.json','instances/weights.json','notes/PLAN.md §6'],
 'approximate_logged_findings':{'M_rank':'~10^4 / 59049 assignment-valid states','eta':'~1; PLAN §6, not rerun'},
 'proposed_not_executed_grid':{'omega_peak':10,'duration_ns':4000,'delta0_omega_factors':[-.5,-1,-1.5],'direct_deltaf_map_factors':[.8,1,1.2]},'mock_performance_source':'mock_metrics.csv'}
(OUT/'data_provenance.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(json.dumps({'deck':str(deck),'slides':len(prs.slides),'timing_seconds':sum(metadata['timings_seconds']),'figures':len(figs)}))
