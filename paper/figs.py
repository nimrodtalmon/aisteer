import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R='/home/claude/aisteer/results/'
plt.rcParams.update({'font.size':8,'font.family':'serif','axes.spines.top':False,'axes.spines.right':False,
                     'axes.linewidth':0.6,'xtick.major.width':0.6,'ytick.major.width':0.6,'pdf.fonttype':42})
OR, GR, DK = '#E07A1F', '#8A8D91', '#222222'
d=json.load(open(R+'frontier_base.json'))
def series(n):
    pts=sorted((v['attention'][0],100*v['error'][0],100*v['error'][1]) for k,v in d.items() if k.split('|')[0]==n and isinstance(v,dict) and 'attention' in v and v['attention'][0]>0.5)
    return [p[0] for p in pts],[p[1] for p in pts],[p[2] for p in pts]
fig,ax=plt.subplots(figsize=(3.3,2.15))
eng=100*d['engine only|0']['error'][0]
ax.axhline(eng,color=DK,ls=(0,(4,3)),lw=0.9); ax.text(1.0,eng+0.6,'AI alone',color=DK,fontsize=7.5)
for n,c,ls,lab,lw in [('panel, random pairs',GR,'-','uniform pairs',1.0),('panel, money-weighted',GR,(0,(3,2)),'share-weighted',1.0),('flag and sample',OR,'-','flag and sample',1.6)]:
    x,y,e=series(n); ax.errorbar(x,y,yerr=e,color=c,ls=ls,lw=lw,marker='o',ms=3 if c==GR else 3.8,capsize=0,elinewidth=0.6,label=lab)
for k,lab,dy in [('open, nudges|0','open forum, nudges',-0.2),('open, multipliers|0','open forum, multipliers',-0.2)]:
    v=d[k]; ax.plot(v['attention'][0],100*v['error'][0],'o',mfc='white',mec=DK,ms=4.5,mew=0.9)
    ax.text(v['attention'][0]*1.12,100*v['error'][0]+dy,lab,fontsize=7,va='center')
ax.legend(loc='lower left',frameon=False,fontsize=7,handlelength=2.2)
ax.set_xscale('log'); ax.set_xticks([1,2.5,5,10,20,40]); ax.set_xticklabels(['1','2.5','5','10','20','40'])
ax.set_xlim(0.8,60); ax.set_ylim(0,23)
ax.set_xlabel('attention (answered questions per day)'); ax.set_ylabel('misallocated funding (%)')
fig.tight_layout(pad=0.2); fig.savefig('frontier.pdf')

S=json.load(open(R+'inflation_sweep.json'))
B=[1.0,1.3,1.6,2.0,2.7]
fig,ax=plt.subplots(figsize=(3.3,2.0))
def y(k): return [100*S[str(b)][k]['error'][0] for b in B]
ax.plot(B,y('AI alone'),color=DK,ls=(0,(4,3)),lw=0.9)
for k,c,ls,lw,mk in [('flag and sample, 5 a day',OR,'-',1.6,'o'),('flag and sample, 12 a day',OR,(0,(3,2)),1.2,'o'),('share-weighted, 12 a day',GR,(0,(3,2)),1.0,'o'),('open forum, nudges',DK,'-',0.8,'s'),('open forum, multipliers',DK,':',0.8,'s')]:
    ax.plot(B,y(k),color=c,ls=ls,lw=lw,marker=mk,ms=3)
lab={'AI alone':('AI alone',2.72,0),'flag and sample, 5 a day':('flag and sample, 5/day',2.72,0),'flag and sample, 12 a day':('flag and sample, 12/day',2.72,0),
     'share-weighted, 12 a day':('share-weighted, 12/day',2.72,0),'open forum, nudges':('open forum, nudges',2.72,0),'open forum, multipliers':('open forum, multipliers',2.72,0)}
ys={k:y(k)[-1] for k in lab}
order=sorted(ys,key=lambda k:ys[k]); pos=[]; 
for k in order:
    p=ys[k]
    if pos and p-pos[-1]<1.4: p=pos[-1]+1.4
    pos.append(p); ax.text(2.76,p,lab[k][0],fontsize=6.3,va='center',color=OR if 'flag' in k else (GR if 'share' in k else DK))
ax.set_xlim(0.95,3.6); ax.set_xticks(B); ax.set_xticklabels(['1','1.3','1.6','2','2.7'])
ax.set_ylim(5,27); ax.set_xlabel('belief exaggeration (typing carries the rest of 2.7)'); ax.set_ylabel('misallocated funding (%)')
fig.tight_layout(pad=0.2); fig.savefig('sweep.pdf')
print('ok')
