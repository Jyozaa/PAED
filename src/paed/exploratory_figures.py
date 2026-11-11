"""Only conditional pooled plots; every figure carries the scenario warning."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from scipy.special import expit
from scipy.stats import chi2

KENET={'kenet_2023_logistic':'Logistic regression','kenet_2023_soft_voting':'Soft voting','kenet_2023_xgboost':'XGBoost'}
PALETTE=['#006D8C','#B55520','#57782B','#84599B','#202E48']


def joint_ellipse(row,alpha=.05,points=241):
    C=np.array([[row['summary_cov_11'],row['summary_cov_12']],[row['summary_cov_12'],row['summary_cov_22']]])
    values,vectors=np.linalg.eigh(C)
    if min(values)<=0:raise ValueError('Positive definite summary covariance required for ellipse')
    angle=np.linspace(0,2*np.pi,points)
    circle=np.stack([np.cos(angle),np.sin(angle)])
    z=np.array([[row['mu_logit_sensitivity']],[row['mu_logit_fpr']]])+vectors@np.diag(np.sqrt(values*chi2.ppf(1-alpha,2)))@circle
    return np.column_stack([expit(z[1]),expit(z[0])])


def save(fig,folder,name):
    fig.savefig(folder/f'{name}.png',dpi=220,facecolor='white',metadata={'Software':'PAED exploratory scenario pipeline'})
    fig.savefig(folder/f'{name}.svg',facecolor='white',metadata={'Date':None})
    plt.close(fig)


def create(results,config,folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'svg.hashsalt':'paed_exploratory_v1'})
    A=[x for x in results['auroc_results'] if x['status']=='success_conditional']
    D=[x for x in results['diagnostic_results'] if x['status']=='success_conditional']
    for row in A:
        inputs=[x for x in results['auroc_inputs'] if x['scenario_id']==row['scenario_id']]
        fig,ax=plt.subplots(figsize=(13,5.8))
        for i,r in enumerate(inputs):
            y=4-i
            actual=r['uncertainty_origin'].startswith('genuine');color='#006D8C' if actual else '#9D572C'
            ax.errorbar(r['auroc'],y,xerr=[[r['auroc']-r['conditional_plot_lower']],[r['conditional_plot_upper']-r['auroc']]],fmt='o',color=color,capsize=4)
            se_label='reported CI' if actual else f'assumed SE={r["se_auroc_used"]:.2f}'
            ax.text(1.02,y,f'{r["auroc"]:.4f} | {se_label} | weight {r["random_effects_weight"]:.1%}',transform=ax.get_yaxis_transform(),va='center',fontsize=9)
        lower=row['conditional_95_lower'];upper=row['conditional_95_upper'];p=row['pooled_auroc']
        ax.add_patch(Polygon([[lower,0],[p,.18],[upper,0],[p,-.18]],facecolor='#264B6A'))
        ax.text(1.02,0,f'{p:.4f} [{lower:.4f}, {upper:.4f}]\nconditional modified H-K interval',transform=ax.get_yaxis_transform(),va='center',fontsize=9)
        names=[r['study_id'].replace('_',' ').title()+' | '+r['model_name'].replace('_',' ') for r in inputs]
        ax.set_yticks([4,3,2,1,0],names+['Conditional pooled AUROC'])
        ax.set(xlim=(0,1),ylim=(-.55,4.6),xlabel='AUROC; conditional intervals for assumed uncertainty')
        ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
        ax.set_title(row['scenario_id']+' | Paule–Mandel random effects',loc='left',weight='bold',pad=15)
        fig.text(.025,.085,config['auroc']['warning'],fontsize=10,weight='bold',color='#8B3E1B')
        fig.text(.025,.025,f'Four source groups assumed independent; heterogeneous horizons/units; Lu ± is not used as SE. Analyst-selected models.\nEstimated logit tau²={row["tau2_logit_estimated"]:.4f}; df=3. Genuine Yu 2023 CI retained when present; no empirical CI claimed for other studies.',fontsize=9)
        fig.subplots_adjust(left=.29,right=.71,top=.87,bottom=.23)
        save(fig,folder,'forest_'+row['scenario_id'])
    if A:
        fig,axes=plt.subplots(1,2,figsize=(13,6.2),sharey=True)
        for ax,dallas in zip(axes,config['auroc']['dallas_alternatives']):
            for model,color in zip(config['auroc']['kenet_alternatives'],PALETTE):
                rows=sorted([r for r in A if r['dallas_estimate_id']==dallas and r['kenet_estimate_id']==model],key=lambda x:x['assumed_se_auroc'])
                x=np.array([r['assumed_se_auroc'] for r in rows]);y=np.array([r['pooled_auroc'] for r in rows])
                ax.plot(x,y,'o-',color=color,label=KENET[model.removesuffix('_a1')])
                ax.fill_between(x,[r['conditional_95_lower'] for r in rows],[r['conditional_95_upper'] for r in rows],color=color,alpha=.07)
            ax.set_title(dallas.split('_')[0].title()+' '+dallas.split('_')[1]+' selected; other Dallas report omitted')
            ax.set_xlabel('Assumed original-AUROC SE for missing uncertainty');ax.set_xticks(config['auroc']['assumed_auroc_scale_ses'])
            ax.set_ylim(.4,1);ax.grid(alpha=.15)
        axes[0].set_ylabel('Conditional pooled AUROC');axes[1].legend(loc='lower right')
        fig.suptitle('AUROC scenario sensitivity; shading is conditional 95% interval',weight='bold')
        fig.text(.025,.065,config['auroc']['warning'],fontsize=10,weight='bold',color='#8B3E1B')
        fig.text(.025,.02,'Only one genuine CI exists (Yu 2023); substitution by Yu 2022 makes all four variances hypothetical. Curves are scenario comparisons, not clinical validation.',fontsize=9)
        fig.subplots_adjust(bottom=.22,top=.85,wspace=.15)
        save(fig,folder,'auroc_sensitivity')
    if D:
        c=config['diagnostic'];fig,axes=plt.subplots(1,3,figsize=(15,6.5),sharex=True,sharey=True)
        for ax,model in zip(axes,c['kenet_models']):
            chosen=[r for r in D if r['kenet_model_id']==model and r['between_covariance_id']==c['plot_between_covariance_id'] and r['yu_variance_inflation']==c['plot_yu_variance_inflation'] and r['rho_within_assumed']==c['primary_within_correlation']]
            for r,color in zip(chosen,PALETTE):
                xy=joint_ellipse(r,config['alpha']);ax.plot(xy[:,0],xy[:,1],color=color,alpha=.8,lw=1)
                ax.scatter(1-r['summary_specificity'],r['summary_sensitivity'],s=35,color=color,label=f'Kenet DE {r["kenet_design_effect"]}')
            ax.set(xlim=(0,1),ylim=(0,1),xlabel='False-positive rate (1 − specificity)');ax.set_title(KENET[model]);ax.grid(alpha=.15)
        axes[0].set_ylabel('Sensitivity');axes[-1].legend(loc='lower left',fontsize=9)
        fig.suptitle('Conditional joint summaries and 95% logit-normal confidence regions — no HSROC fitted',fontsize=13,weight='bold')
        fig.text(.025,.09,c['warning'],fontsize=10,weight='bold',color='#8B3E1B')
        fig.text(.025,.025,'Shown: assumed between-source SDs=0.5, correlation=0; Yu variance inflation=1, within-source correlation=0.\nTwo source summaries only. Counts remain observed window/unresolved-unit counts; ellipses depend on supplied covariance assumptions.',fontsize=9)
        fig.subplots_adjust(top=.84,bottom=.23,wspace=.12)
        save(fig,folder,'diagnostic_joint_summaries')
        fig,axes=plt.subplots(2,3,figsize=(15,8),sharex=True)
        for j,model in enumerate(c['kenet_models']):
            for tau,color in zip(c['between_source_covariances'],PALETTE):
                rows=sorted([r for r in D if r['kenet_model_id']==model and r['between_covariance_id']==tau['id'] and r['yu_variance_inflation']==1 and r['rho_within_assumed']==0],key=lambda r:r['kenet_design_effect'])
                for i,key in enumerate(['summary_sensitivity','summary_specificity']):
                    axes[i,j].plot([r['kenet_design_effect'] for r in rows],[r[key] for r in rows],'o-',color=color,label=tau['id'])
            axes[0,j].set_title(KENET[model]);axes[1,j].set_xlabel('Assumed Kenet design effect')
            for i in range(2):
                axes[i,j].set_xscale('log');axes[i,j].set_xticks(c['kenet_design_effects'],labels=[str(x) for x in c['kenet_design_effects']]);axes[i,j].grid(alpha=.15)
                axes[i,j].set_ylim((.85,1.0) if i==0 else (.6,.9))
        axes[0,0].set_ylabel('Conditional summary sensitivity');axes[1,0].set_ylabel('Conditional summary specificity')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.16),ncol=5)
        fig.suptitle('Diagnostic summaries vary with design effect and assumed heterogeneity',weight='bold')
        fig.text(.025,.075,c['warning'],fontsize=10,weight='bold',color='#8B3E1B')
        fig.text(.025,.015,'T0: zero covariance; T05Rneg/R0/Rpos: logit SDs 0.5 and sensitivity/FPR correlation −0.5/0/+0.5; T1R0: SDs 1.0, correlation 0.\nYu inflation=1 and within-source correlation=0 shown. Curves compare assumptions; full conditional intervals and all Yu/correlation variants are tabulated.',fontsize=9)
        fig.subplots_adjust(top=.9,bottom=.28,hspace=.25,wspace=.15)
        save(fig,folder,'diagnostic_sensitivity')
