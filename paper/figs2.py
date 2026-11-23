import json, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R='/home/claude/aisteer/results/'
plt.rcParams.update({'font.size':8,'font.family':'serif','axes.spines.top':False,'axes.spines.right':False,
                     'axes.linewidth':0.6,'xtick.major.width':0.6,'ytick.major.width':0.6,'pdf.fonttype':42})
OR, GR, DK = '#E07A1F', '#8A8D91', '#222222'
def ms(v): e=100*np.array(v['error']); return e.mean(), e.std()/np.sqrt(len(e)), np.mean(v['attention'])
d=json.load(open(R+'ecai_frontier.json'))
fig,ax=plt.subplots(figsize=(3.3,2.15))
eng=ms(d['engine only'])[0]
ax.axhline(eng,color=DK,ls=(0,(4,3)),lw=0.9); ax.text(1.0,eng+0.6,'AI alone',color=DK,fontsize=7.5)
KS=(2,5,10,20,40,80)
for n,c,ls,lab,lw in [('panel, random pairs',GR,'-','uniform pairs',1.0),('panel, money-weighted',GR,(0,(3,2)),'share-weighted',1.0),('flag and sample',OR,'-','flag and sample',1.6)]:
    pts=[ms(d[f'{n}|{K}']) for K in KS]
    ax.errorbar([p[2] for p in pts],[p[0] for p in pts],yerr=[p[1] for p in pts],color=c,ls=ls,lw=lw,marker='o',ms=3 if c==GR else 3.8,capsize=0,elinewidth=0.6,label=lab)
for k,lab in [('open, nudges','open forum, nudges'),('open, multipliers','open forum, multipliers'),('open, clipped','open forum, clipped')]:
    mu,se,a=ms(d[k]); ax.plot(a,mu,'o',mfc='white',mec=DK,ms=4.5,mew=0.9)
    ax.text(a*1.12,mu,lab,fontsize=6.6,va='center',bbox=dict(fc='white',ec='none',pad=0.4))
ax.legend(loc='lower left',frameon=False,fontsize=7,handlelength=2.2)
ax.set_xscale('log'); ax.set_xticks([1,2.5,5,10,20,40]); ax.set_xticklabels(['1','2.5','5','10','20','40'])
ax.set_xlim(0.8,110); ax.set_ylim(0,22)
ax.set_xlabel('attention (answered questions per day)'); ax.set_ylabel('misallocated funding (%)')
fig.tight_layout(pad=0.2); fig.savefig('frontier.pdf')
print('frontier ok')

S=json.load(open(R+'ecai_belief.json'))
B=[1.0,1.3,1.6,2.0,2.7]
fig,ax=plt.subplots(figsize=(3.3,2.0))
def y(k): return [100*np.mean(S[f'{k}|{b}']['error']) for b in B]
ax.plot(B,y('AI alone'),color=DK,ls=(0,(4,3)),lw=0.9)
spec=[('flag and sample, 5 a day',OR,'-',1.6,'o','flag and sample, 5/day'),('flag and sample, 12 a day',OR,(0,(3,2)),1.2,'o','flag and sample, 12/day'),
      ('share-weighted, 12 a day',GR,(0,(3,2)),1.0,'o','share-weighted, 12/day'),('open forum, nudges',DK,'-',0.8,'s','open forum, nudges'),
      ('open forum, multipliers',DK,':',0.8,'s','open forum, multipliers')]
for k,c,ls,lw,mk,_ in spec: ax.plot(B,y(k),color=c,ls=ls,lw=lw,marker=mk,ms=3)
labs=[(k,l,c) for k,c,_,_,_,l in spec]+[('AI alone','AI alone',DK)]
ys=sorted(((y(k)[-1],l,c) for k,l,c in labs)); pos=[]
for v,l,c in ys:
    p=v if not pos or v-pos[-1]>=1.45 else pos[-1]+1.45
    pos.append(p); ax.text(2.76,p,l,fontsize=6.3,va='center',color=c)
ax.set_xlim(0.95,3.65); ax.set_xticks(B); ax.set_xticklabels(['1','1.3','1.6','2','2.7'])
ax.set_ylim(5,27); ax.set_xlabel('belief exaggeration (typing carries the rest of 2.7)'); ax.set_ylabel('misallocated funding (%)')
fig.tight_layout(pad=0.2); fig.savefig('sweep.pdf'); print('sweep ok')
