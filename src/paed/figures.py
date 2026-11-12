"""Descriptive plots: no invented confidence limits or fitted summary curves."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import ListedColormap

COLORS={'lu_2025':'#007C91','bose_2019':'#9B4D96','yu_2023':'#C66B12','kenet_2023':'#3157A4','yu_2022':'#508633'}
NAMES={'lu_2025':'Lu 2025','bose_2019':'Bose 2019','yu_2023':'Yu 2023','kenet_2023':'Kenet 2023','yu_2022':'Yu 2022'}


def save(fig,root,name):
    fig.savefig(root/f'{name}.png',dpi=220,facecolor='white',metadata={'Software':'PAED reproducible pipeline'})
    fig.savefig(root/f'{name}.svg',facecolor='white',metadata={'Date':None})
    plt.close(fig)


def label(row):
    return NAMES[row['study_id']]+' | '+row['model_name'].replace('pedca ft','PEDCA-FT').replace('rdn boost','RDN Boost').replace('glm','GLM')


def diagnostic_points(data,metric):
    matrices={r['model_id']:r for r in data['diagnostic']}
    rows=[]
    for r in data['operating']:
        if r['metric']!=metric:continue
        x=dict(r)
        if r['model_id'] in matrices and r['evaluation']!='entire_dataset':
            x['estimate']=matrices[r['model_id']][metric+'_recalculated']
            x['source_quality']='counts'
        rows.append(x)
    return rows


def create_figures(data,contexts,output):
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.hashsalt':'paed20261111'})
    a=data['auroc']; fig,ax=plt.subplots(figsize=(12,10))
    for i,r in enumerate(a):
        y=len(a)-1-i; color=COLORS[r['study_id']]
        if r['ci_lower'] is not None:
            ax.errorbar(r['auroc'],y,xerr=[[r['auroc']-r['ci_lower']],[r['ci_upper']-r['auroc']]],fmt='o',color=color,capsize=3)
        else:ax.plot(r['auroc'],y,'o',color=color)
        txt=f'{r["auroc"]:.4f}'
        if r['uncertainty_type']=='unspecified_plus_minus':txt+='  [variation type unknown]'
        elif r['ci_lower'] is not None:txt+=f'  [{r["ci_lower"]:.2f}, {r["ci_upper"]:.2f}]'
        ax.text(1.015,y,txt,va='center',fontsize=8.5,transform=ax.get_yaxis_transform())
    labels=[label(r)+(f' | {r["evaluation"].replace("internal_", "")}' if r['study_id']=='bose_2019' else '') for r in a]
    ax.set_yticks(range(len(a)),labels[::-1]);ax.set_xlim(.45,1.0);ax.axvline(.5,color='#BBBBBB',lw=.7,ls='--')
    ax.set_xlabel('AUROC (0-1); discrimination, not the proportion of arrests detected')
    ax.set_title('Reported AUROC estimates - descriptive, no pooled estimate',loc='left',weight='bold',pad=18)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    fig.text(.02,.018,f'{len(data["models"])} models / {len({r["study_id"] for r in a})} study reports; {len(a)} points include Bose training and test. Only Yu 2023 has a supplied 95% CI.\nModels share cohorts; Yu 2022/2023 may reuse patients. Horizons, units and validation differ. +/- values are not error bars.',fontsize=9)
    fig.subplots_adjust(left=.32,right=.73,top=.92,bottom=.12)
    save(fig,root,'auroc_descriptive')
    for metric in ['sensitivity','specificity']:
        points=diagnostic_points(data,metric)
        fig,ax=plt.subplots(figsize=(12,7))
        for i,r in enumerate(points):
            y=len(points)-1-i;open_marker=r['source_quality']=='graph_read'
            ax.scatter(r['estimate'],y,facecolors='white' if open_marker else COLORS[r['study_id']],
                       edgecolors=COLORS[r['study_id']],s=45)
            unit='5-min windows' if r['study_id']=='kenet_2023' else ('unit unresolved' if r['study_id']=='yu_2023' else ('graph-read' if open_marker else 'reported'))
            ax.text(1.02,y,f'{100*r["estimate"]:.2f}% | {unit}',transform=ax.get_yaxis_transform(),va='center',fontsize=9)
        labels=[label(r)+(' | entire dataset' if r['evaluation']=='entire_dataset' else '') for r in points]
        ax.set_yticks(range(len(points)),labels[::-1]);ax.set_xlim(0,1);ax.set_ylim(-.8,len(points)-.2)
        ax.set_xlabel(metric.capitalize());ax.set_title(f'{metric.capitalize()} by model / evaluation - descriptive',loc='left',weight='bold',pad=18)
        ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
        fig.text(.02,.02,'Counts recalculated where complete; source values retained separately. No eligible Lu or Yu 2022 operating points.\nNo confidence intervals: clustering, analysis unit and/or denominators unresolved. Kenet points describe windows, not independent patients.',fontsize=9)
        fig.subplots_adjust(left=.32,right=.72,bottom=.17,top=.9)
        save(fig,root,f'{metric}_descriptive')
    sens={r['model_id']:r for r in diagnostic_points(data,'sensitivity') if r['evaluation']!='entire_dataset'}
    spec={r['model_id']:r for r in diagnostic_points(data,'specificity') if r['evaluation']!='entire_dataset'}
    fig,ax=plt.subplots(figsize=(11,8))
    offsets={'kenet_2023_logistic':(.40,.84),'kenet_2023_svm':(.40,.99),'kenet_2023_random_forest':(.17,.86),
             'kenet_2023_xgboost':(.23,1.04),'kenet_2023_lightgbm':(.18,.98),'kenet_2023_soft_voting':(.035,.94),
             'yu_2023_rdn_boost':(.40,.91)}
    for mid,s in sens.items():
        if mid not in spec:continue
        p=spec[mid];x=1-p['estimate'];y=s['estimate'];sid=s['study_id']
        ax.scatter(x,y,s=60,facecolors='white' if sid=='lu_2025' else COLORS[sid],edgecolors=COLORS[sid])
        ax.annotate(label(s),(x,y),textcoords='data',xytext=offsets.get(mid,(x+.01,y+.018)),fontsize=8,
                    arrowprops={'arrowstyle':'-','lw':.5,'color':'#888888'})
    ax.plot([0,1],[0,1],ls='--',color='#BBBBBB',lw=.8)
    ax.set(xlim=(0,.62),ylim=(0,1.07),xlabel='False positive rate (1 - specificity)',ylabel='Sensitivity')
    ax.set_title('Descriptive ROC-space scatter - no fitted SROC or pooled operating point',loc='left',weight='bold',pad=18,fontsize=12)
    ax.grid(alpha=.15)
    fig.text(.06,.025,'Each point is a model-specific operating point; thresholds are unreported or not comparable. Units differ across studies.\nSix Kenet points share windows; Yu 2023 linkage is unverified. Lu and Yu 2022 have no eligible operating points. No uncertainty regions are estimable.',fontsize=9)
    fig.subplots_adjust(left=.09,right=.96,top=.9,bottom=.16)
    save(fig,root,'sroc_descriptive')
    ids=[sid for sid,c in contexts.items() if c['working_eligible']]
    matrix=np.zeros((len(ids),len(ids)),int)
    for i,l in enumerate(ids):
        for j,r in enumerate(ids):
            matrix[i,j]=0 if i==j else (2 if contexts[l]['dependency_group']==contexts[r]['dependency_group'] else 1)
    fig,ax=plt.subplots(figsize=(9,7))
    ax.imshow(matrix,cmap=ListedColormap(['#E7ECF0','#B9DCE0','#E7BA88']),vmin=0,vmax=2)
    for i in range(len(ids)):
        for j in range(len(ids)):
            ax.text(j,i,['Same\nstudy','Context only\nNo pooling','Possible patient\noverlap'][matrix[i,j]],ha='center',va='center',fontsize=9)
    ax.set_xticks(np.arange(-.5,len(ids),1),minor=True);ax.set_yticks(np.arange(-.5,len(ids),1),minor=True)
    ax.grid(which='minor',color='white',linewidth=1.2);ax.tick_params(which='minor',bottom=False,left=False)
    ax.set_xticks(range(len(ids)),[NAMES[s] for s in ids]);ax.set_yticks(range(len(ids)),[NAMES[s] for s in ids])
    ax.set_title('Study comparability and dependency overview',loc='left',weight='bold',pad=18)
    fig.text(.04,.025,'All cross-study pairs require additional evidence before pooling. Blue does not establish comparability or independence.\nYu 2022/2023 share institution, period and 160 CA / 711 controls. The matrix uses conservative dependency grouping.',fontsize=9)
    fig.subplots_adjust(top=.88,bottom=.15,left=.15,right=.96)
    save(fig,root,'heterogeneity_overview')
    audit=data['audit'];pop=[r for r in audit if r['record_type']=='populated_model'];exc=[r for r in data['excluded'] if r['record_type']=='populated_model']
    fig,ax=plt.subplots(figsize=(12,8));ax.axis('off');ax.set(xlim=(0,12),ylim=(0,8))
    def box(x,y,w,h,text,color='#E9F0F4'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.13',facecolor=color,edgecolor='#395469',lw=1.0))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    box(.4,6.4,6.2,1.0,f'Supplied extraction: {len(audit)} post-header records\n{len(pop)} populated model entries / 6 study reports')
    box(7.7,6.4,3.7,1.0,'1 cross-reference record\nNo results; linked to Yu 2022', '#F6EDD9')
    box(.4,4.3,6.2,1.1,f'Working cohort: {len(data["models"])} models / 5 studies\n4 conservative potential cohort groups', '#DCF0E8')
    box(7.7,4.3,3.7,1.1,f'{len(exc)} model exclusions\nYu 2026: 5 composite-outcome models\nYu 2023: 1 graphical-only GNB\nLu 2025: 3 whole-model team exclusions', '#F6E3DF')
    box(.4,2.0,6.2,1.2,f'AUROC: {len(a)} points / {len(data["models"])} models / {len({r["study_id"] for r in a})} studies\nGenuine CI: 1 estimate / 1 cohort\nConfirmatory pooling: not defensible')
    box(7.7,2.0,3.7,1.2,'Complete 2x2: 7 models / 2 sources\n6 window tables + 1 unresolved fold\nHierarchical pooling: not defensible')
    for x,y1,y2 in [(3.5,6.25,5.55),(3.5,4.15,3.35)]:ax.annotate('',xy=(x,y2),xytext=(x,y1),arrowprops={'arrowstyle':'->','color':'#395469'})
    ax.annotate('',xy=(7.5,6.9),xytext=(6.75,6.9),arrowprops={'arrowstyle':'->'})
    ax.annotate('',xy=(7.5,4.85),xytext=(6.75,4.85),arrowprops={'arrowstyle':'->'})
    ax.text(.4,.8,f'Strict protocol: 0 studies demonstrate all criteria; 4 CICU studies / {sum(contexts[r["study_id"]]["setting_class"]=="CICU" for r in data["models"])} models pass setting alone.',fontsize=11)
    fig.suptitle('Dataset inclusion flow (extraction audit only)',x=.06,ha='left',fontsize=17,weight='bold')
    fig.text(.06,.035,'No database search or screening totals supplied. This is not a PRISMA literature-search flow diagram.\nThe cross-reference is not an extra independent model. “0 demonstrated eligible” does not prove absent external validation for NR studies.',fontsize=9)
    save(fig,root,'inclusion_flow')
