"""Auditor-editable, publication-style figures. Blue=model, green=match, red=mismatch."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BLUE='#245B94'; GREEN='#26805D'; RED='#B5443C'; GREY='#59616A'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,'axes.labelsize':16,'axes.titlesize':18,'xtick.labelsize':15,'ytick.labelsize':15,'text.color':'#24292F','axes.labelcolor':'#39424C','axes.edgecolor':'#89939D','axes.linewidth':.7,'axes.facecolor':'white','figure.facecolor':'white','savefig.facecolor':'white','legend.frameon':False,'svg.fonttype':'none'})
def save(fig,out,name):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    for ext in ('png','svg'): fig.savefig(out/f'{name}.{ext}',dpi=300,bbox_inches='tight',pad_inches=.2)
    plt.close(fig); return out/f'{name}.png'
def clean(ax):
    ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color='#DCE2E7',lw=.6); ax.set_axisbelow(True)
def atom_counts(rows,out):
    fig,ax=plt.subplots(figsize=(7.6,3.7),layout='constrained'); x=np.arange(3); w=.24
    for shift,vals,label,col in [(-w,[r['onehot_plus_slack'] for r in rows],'Textbook slack',GREY),(0,[r['ours'] for r in rows],'Direct QUBO baseline',BLUE),(w,[4,10,15],'Seed model B',GREEN)]:
        bars=ax.bar(x+shift,vals,w,color=col,label=label); ax.bar_label(bars,padding=4,fontsize=16)
    ax.axhline(80,color=RED,ls='--',lw=1); ax.text(1.95,83,'80 atoms',color=RED,fontsize=14)
    ax.set(xticks=x,xticklabels=['S','M','L'],ylabel='Binary variables / atoms',ylim=(0,108)); ax.legend(loc='upper left',fontsize=13); clean(ax)
    return save(fig,out,'01_atom_counts')
def instance_maps(instances,out):
    fig,axs=plt.subplots(1,3,figsize=(13.8,4.4),layout='constrained'); cols=[BLUE,GREEN,RED,'#A77922']
    for ax,inst in zip(axs,instances):
        xy=np.asarray(inst.coords)
        for k in range(inst.K):
            ids=[i for i,t in enumerate(inst.certificate) if t==k]; ax.scatter(*xy[ids].T,s=65,color=cols[k],edgecolor='white',linewidth=.7)
        ax.scatter(*inst.depot,marker='s',s=70,color='#24292F')
        ax.set(xlim=(-5,105),ylim=(-5,105),xlabel='x / distance units',ylabel='y / distance units')
        ax.set_title(f'{inst.tier}: N={inst.N}, K={inst.K}, Q={inst.Q}',loc='left',pad=16); ax.set_aspect('equal'); clean(ax)
        ax.text(.02,.03,f'ρ = {inst.rho:.2f}\ndmax/Q = {inst.dmax_ratio:.2f}',transform=ax.transAxes,fontsize=14)
    return save(fig,out,'02_certified_instances')
def loss_equations(out):
    fig=plt.figure(figsize=(13.6,4.5)); fig.text(.03,.88,r'$\mathcal{L}=C_{\mathrm{cluster}}+A\,P_{\mathrm{assign}}+\lambda\,P_{\mathrm{balance}}$',fontsize=30,color=BLUE)
    fig.text(.03,.67,'CLUSTER FUNCTION — optimize',color=BLUE,fontsize=17,weight='bold'); fig.text(.03,.49,r'$C=\sum_k\sum_{i<j} c_{ij}\,x_{ik}x_{jk}$',fontsize=26)
    fig.text(.54,.67,'CAPACITY — pass/fail: every load ≤ Q',color=RED,fontsize=17,weight='bold'); fig.text(.54,.49,r'$P_{\mathrm{balance}}=\sum_k(L_k-D/K)^2$',fontsize=26)
    fig.text(.54,.34,'Surrogate keeps rewarding balance.',fontsize=17,color=RED)
    fig.text(.03,.13,r'$\mathcal{L}=\mathrm{const}+\sum_a a_a x_a+\sum_{a<b}b_{ab}x_ax_b$',fontsize=29,color=BLUE)
    return save(fig,out,'03_loss_and_expansion')
def energy_comparison(out):
    fig=plt.figure(figsize=(13.7,4.6)); fig.text(.02,.86,'OUR QUBO (scaled)',fontsize=18,color=BLUE,weight='bold')
    fig.text(.02,.68,r'$s\mathcal{L}-\mathrm{const}\ =$',fontsize=28,color=BLUE); fig.text(.40,.68,r'$\sum_a s a_a x_a$',fontsize=28,color=RED); fig.text(.69,.68,r'$+\ \sum_{a<b}s b_{ab}x_ax_b$',fontsize=28,color=GREEN)
    fig.text(.02,.43,'PASQAL E EQUATION (Ω = 0)',fontsize=18,color=BLUE,weight='bold'); fig.text(.02,.22,r'$E_{\mathrm{hw}}/\hbar\ =$',fontsize=28,color=BLUE); fig.text(.40,.22,r'$-\delta\sum_a x_a$',fontsize=28,color=RED); fig.text(.69,.22,r'$+\ \sum_{a<b}C_6\,r_{ab}^{-6}\,x_ax_b$',fontsize=28,color=GREEN)
    fig.text(.40,.04,'per-atom constant',fontsize=15,color=GREY); fig.text(.71,.04,'per-pair constant (set by distance)',fontsize=15,color=GREY)
    return save(fig,out,'04_qubo_vs_pasqal')
def distances(target,C6,out,coords=None):
    vals=target[np.triu_indices(len(target),1)]; wanted=(C6/vals[vals>0])**(1/6)
    fig,axs=plt.subplots(1,2,figsize=(8.4,3.9),layout='constrained'); ax=axs[0]
    ax.axvspan(wanted.min(),wanted.max(),color=RED,alpha=.08,lw=0); ax.hist(wanted,bins=13,color=BLUE,edgecolor='white',lw=.8)
    ax.axvline(5,color=RED,lw=1.4,ls='--')
    ax.set(xlabel='Wanted distance / µm',ylabel='Atom pairs'); ax.set_title(f'Model A: all pairs want {wanted.min():.0f}–{wanted.max():.0f} µm',fontsize=15,loc='left'); clean(ax)
    ax=axs[1]
    if coords is not None:
        c=np.array(coords); d=np.linalg.norm(c[:,None]-c[None],axis=-1)[np.triu_indices(len(c),1)]; R=np.linalg.norm(c,axis=1).max(); m=R*1.25
        ax.scatter(*c.T,color=GREEN,s=70,edgecolor='white',lw=.8)
        ax.set(xlim=(-m,m),ylim=(-m,m)); ax.set_title(f'Model B: radius {R:.0f} µm, min gap {d.min():.1f} µm',fontsize=15,loc='left')
    ax.set(xlabel='x / µm',ylabel='y / µm'); ax.set_aspect('equal'); clean(ax)
    return save(fig,out,'05_requested_atom_distances')
def expected_loss(out):
    fig=plt.figure(figsize=(13.8,1.1))
    fig.text(.02,.3,r'$\mathbb{E}[C\mid F]=\dfrac{1}{P(F)}\sum_{x\in F}p(x\mid\mathbf{r},\Omega,\delta,T)\,C(\mathrm{decode}(x))$',fontsize=26,color=BLUE)
    return save(fig,out,'05_expected_loss')
def pulse_waveforms(amp,det,out):
    fig,axs=plt.subplots(2,1,figsize=(8.4,4.2),sharex=True,layout='constrained'); t=np.arange(len(amp))/1000
    axs[0].plot(t,amp,color=BLUE,lw=2); axs[0].set(ylabel='Ω / rad µs⁻¹',ylim=(-.5,13.5)); axs[0].axhline(12.566370614,color=RED,lw=1,ls='--')
    axs[1].plot(t,det,color=BLUE,lw=2); axs[1].set(ylabel='δ / rad µs⁻¹',xlabel='Time / µs')
    for ax in axs: clean(ax)
    return save(fig,out,'06_proposed_pulse')
def mock_results(rows,out):
    fig,axs=plt.subplots(1,3,figsize=(13.6,3.5),layout='constrained')
    for ax,key,title in zip(axs,['feasibility_rate','model_gap_pct','cvrp_gap_pct'],['Feasibility rate / %','Model gap / %','CVRP gap / %']):
        for method,col,shift in [('Baseline pulse',GREY,-.06),('Tuned pulse',BLUE,.06)]:
            means=[]; mins=[]; maxs=[]
            for i,t in enumerate('SML'):
                v=np.array([float(r[key]) for r in rows if r['instance'].startswith(t) and r['method']==method]); v=v*100 if key=='feasibility_rate' else v
                means.append(v.mean()); mins.append(v.mean()-v.min()); maxs.append(v.max()-v.mean()); ax.scatter(np.full(len(v),i+shift),v,color=col,s=18,alpha=.5)
            ax.errorbar(np.arange(3)+shift,means,yerr=[mins,maxs],color=col,marker='o',lw=1.6,capsize=3,label=method)
        ax.set(xticks=np.arange(3),xticklabels=list('SML'),title=title); clean(ax); ax.set_ylim(bottom=0)
    axs[0].set_ylim(0,105); axs[0].legend(fontsize=13,loc='lower left'); return save(fig,out,'07_MOCK_metrics')
