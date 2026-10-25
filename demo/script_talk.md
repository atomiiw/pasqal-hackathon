# 7-minute talk script (per slide: what to say, then a Chinese cue)

Rules for yourself: one idea per slide, never read the slide, say the number then stop. Total 7:00; times in brackets.

**1 · Cover [0:15]**
"We put a delivery-routing problem on Pasqal's atoms. Our result in one line: one atom per customer, placed like the customer map. Four, ten and fifteen atoms, instead of the fourteen, forty-five and eighty the textbook encoding needs."
> 一句话结论：一客户一原子，按地图摆。

**2 · The problem [0:30]**
"K trucks, N customers, every truck has a weight limit. Which customers ride together, so that each truck's customers are close? Two rules: each customer on exactly one truck, that's an equality; and load at most Q, that's an inequality. The brief says the whole difficulty is that inequality, because every slack bit you add to encode it is an atom you lose."
> 等式容易，不等式是坑：每个 slack bit 都是一个原子。

**3 · Two models [0:20]**
"We built two models. Model A is the direct QUBO everyone writes first. Model B is what we ended up with. I'll show you why A fails, because that failure is the reason B exists."
> 先讲 A 怎么失败，再讲 B。

**4 · Model A idea [0:30]**
"Model A: write the cost directly. Distance between customers that share a truck, plus a penalty when a truck is overloaded. No slack bits: we use a load-balance penalty, every truck pulled toward the average load. That gives 4, 30 and 60 atoms, under the 80 limit."
> 不用 slack：负载平衡罚分。

**5 · Model A versus the machine [0:30]**
"The machine computes one energy: a detuning per atom, the same for all atoms, and a repulsion between every pair that falls off as one over distance to the sixth. Our QUBO's pair terms are all positive, so the sign is right. Per-atom terms we can't match, one global knob. Pair strengths we have to match by placing atoms."
> 符号对，单原子项匹配不了，对项靠摆位置。

**6 · Model A layout fails [0:45]**
"Here's the catch, and it's measured, not argued. The penalty makes far-apart customers need a strong coupling. Strong coupling means close atoms. So far customers need close atoms and near customers need far atoms: the coupling graph is the opposite of the map. For ten customers, no layout in a plane reproduces it. We tried our own optimizer, Pasqal's two embedders, fitting energies instead of couplings, and sparsifying the objective. Best case: the true optimum ranks nine thousandth out of fifty-nine thousand valid assignments. On four atoms it still runs, so we kept S as the honest baseline."
> 耦合图和地图相反，M 层最优解排第 ~9000。这是实测。

**7 · Model A result on S [0:15]**
"On S it works on two of three instances, 90 and 96 percent usable shots, and fails on the third where the penalty weight had to be huge. Fine as a baseline, not as a method."
> S 层两个能跑，一个不行。

**8 · The lesson [0:30]**
"The lesson: don't ask the atoms for couplings they don't naturally have. Atoms give strong coupling to near atoms. So make 'near' mean something useful. In model B, a bit no longer means 'customer i on truck k'. It means 'customer i is the center of a truck'. Two near customers should not both be centers. That is exactly what the atoms refuse to do."
> 换问法：bit = 这个客户是不是一辆车的中心。近的不能同时当中心，这正是原子天然的行为。

**9 · Model B idea [0:30]**
"So: one atom per customer, placed on the customer map, scaled to micrometers. Fire the laser, read a 0 or 1 per atom. The 1s are the centers. Physics guarantees the centers are spread out. Then every other customer joins the nearest center that still has room. That last step is a few lines of classical code, order N times K."
> 地图即布局；激光读出中心；其他人投靠最近有空位的中心。

**10 · Model B energy [0:20]**
"Now look at the energy. Per atom, one detuning, the same for all, exactly what the machine has. Per pair, C6 over distance to the sixth, exactly what the atoms give. We didn't fit a single coefficient. The QUBO is the machine energy. Capacity is not in the energy at all; we check it after reading, and shots that fail are thrown away. The brief allows that explicitly: change what the model asks for."
> 一个系数都没拟合，QUBO 就是机器能量。容量在读出后检查。

**11 · Layout [0:20]**
"Layout is one number, the scale: how many micrometers per map unit. It's chosen so that two customers closer than a threshold land inside one blockade radius, and K centers fit but K plus one don't. Every layout passes Pulser's device check: 5 micrometer spacing, 38 micrometer radius."
> 布局只有一个数：比例尺。

**12 · Laser [0:25]**
"Three knobs: laser strength, which sets the blockade radius; duration; and the final detuning, which sets how many atoms end up as 1. We grid-search the first two per tier and the third per instance, a thousand shots each, and we pick by how often we hit the proven optimum, never by average energy."
> 三个旋钮，网格搜，按命中最优的概率选。

**13 · How it runs [0:40]**
"This is M_seed0, real data. Atoms on the map; overlapping circles mean those two can't both be centers. The laser: strength on, detuning swept from minus five to plus one point three. A thousand reads: 305 come back with exactly three centers, the rest are discarded. The most frequent valid read: three centers, everyone joins the nearest one with room, loads 20, 19, 18, limit 20. And it is the proven optimum, which we know because we solved every instance exactly beforehand."
> 真实数据走一遍：305 次刚好 3 个中心，最常见的那个就是最优。

**14 · Results [0:45]**
"Three tiers, three instances each, 1000 shots. Share of shots that are the proven best: S 51 to 91 percent, M 13 to 20, L 2 to 32. Against random bitstrings with the same decode, that's 2 to 4 times on S, 7 to 12 on M, over 60 on L. Against a stricter baseline, random choice of K centers, we're about even on M and up to 8 times on L. The honest price: on M and L only 30 to 54 percent of shots are usable. And S is too small to prove anything; six possible center pairs."
> 公平基线下 M 持平、L 最多 8 倍；代价是一半 shot 不可用；S 太小说明不了。

**15 · Summary [0:25]**
"What's new: capacity with no slack bits, and then an encoding where the atom map is the customer map, 4, 10, 15 atoms. What did not work: the direct QUBO has no 2D layout on M and L, half of our M and L shots are unusable, and the balance penalty costs up to 14 percent before any shot. Everything, including the failures, is in the repo with one command to reproduce. We used AI for nearly all of the code and drafts; the report lists the six mistakes it made and what caught each one."
> 新点 + 没成功的 + 一条命令复现 + AI 用了且列了错误。

Total ≈ 6:55.
