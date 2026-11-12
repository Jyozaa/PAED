"""Before/after comparisons from immutable saved aggregate results, never literals."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .provenance import historical_checks,historical_files
from .reporting import write_csv,write_md,md_table
from .exploratory import CLASS


def prepare(project,root,results):
    project=Path(project);root=Path(root);revision,_=historical_checks(project)
    olddir=project/'data/history/analysis_20_models'
    olda=pd.read_csv(olddir/'auroc_scenario_results.csv');oldd=pd.read_csv(olddir/'diagnostic_scenario_results.csv')
    newa=pd.DataFrame(results['auroc_results']);newd=pd.DataFrame(results['diagnostic_results'])
    good=newa[newa.status=='success_conditional'];core=good[good.scenario_family=='core_lu_logistic'];alts=good[good.scenario_family=='alternative_lu_model']
    oldsummary=pd.read_csv(olddir/'descriptive_summary.csv').set_index('measure').value
    descriptive_root=root if (root/'results/descriptive_summary.csv').exists() else project
    current=pd.read_csv(descriptive_root/'results/descriptive_summary.csv').set_index('measure').value
    oldinventory=pd.read_csv(olddir/'study_inventory.csv');nowinventory=pd.read_csv(descriptive_root/'results/study_inventory.csv')
    before_lu=int(oldinventory.loc[oldinventory.study_id=='lu_2025','retained_models'].iloc[0]);after_lu=int(nowinventory.loc[nowinventory.study_id=='lu_2025','retained_models'].iloc[0])
    def rng(frame,field,scale=1):return f'{frame[field].min()*scale:.4f}-{frame[field].max()*scale:.4f}'
    comparison=[{'measure':'Retained study reports','previous':str(int(oldsummary['retained_study_reports'])),'revised':str(int(current['retained_study_reports']))},
                {'measure':'Retained models','previous':str(int(oldsummary['retained_models'])),'revised':str(int(current['retained_models']))},
                {'measure':'Retained Lu models','previous':str(before_lu),'revised':str(after_lu)},
                {'measure':'Lu reported AUROC range','previous':f'{oldsummary["lu_2025_nontraining_reported_auroc_min"]:.4f}-{oldsummary["lu_2025_nontraining_reported_auroc_max"]:.4f}','revised':f'{current["lu_2025_nontraining_reported_auroc_min"]:.4f}-{current["lu_2025_nontraining_reported_auroc_max"]:.4f}'},
                {'measure':'Core AUROC scenarios','previous':str(len(olda)),'revised':str(len(core))},
                {'measure':'Core conditional pooled AUROC range','previous':rng(olda,'pooled_auroc'),'revised':rng(core,'pooled_auroc')},
                {'measure':'Additional retained-Lu AUROC scenarios','previous':'0','revised':str(len(alts))},
                {'measure':'All revised Lu-choice conditional pooled AUROC range','previous':'Not previously assessed','revised':rng(good,'pooled_auroc')},
                {'measure':'Diagnostic scenarios','previous':str(len(oldd)),'revised':str(len(newd))},
                {'measure':'Conditional diagnostic sensitivity (%)','previous':rng(oldd,'summary_sensitivity',100),'revised':rng(newd,'summary_sensitivity',100)},
                {'measure':'Conditional diagnostic specificity (%)','previous':rng(oldd,'summary_specificity',100),'revised':rng(newd,'summary_specificity',100)}]
    for r in comparison:r.update(analysis_class='revision_comparison',revision_id=revision['revision_id'])
    paired=[]
    for _,r in core.iterrows():
        p=olda.loc[olda.scenario_id==r.scenario_id]
        if len(p)!=1:raise ValueError('Expected one saved predecessor per core scenario')
        p=p.iloc[0];row={'analysis_class':'revision_comparison','scenario_id':r.scenario_id,
            'previous_model_ids_historical':p.model_ids,'revised_model_ids':r.model_ids,'delta_pooled_auroc':r.pooled_auroc-p.pooled_auroc}
        for f in ['pooled_auroc','conditional_95_lower','conditional_95_upper','tau2_logit_estimated']:
            row['previous_'+f]=float(p[f]);row['revised_'+f]=float(r[f])
        paired.append(row)
    diagnostics=[];numeric=oldd.select_dtypes(include=[np.number]).columns
    if set(oldd.scenario_id)!=set(newd.scenario_id):raise AssertionError('Diagnostic scenario identities changed')
    for _,r in newd.iterrows():
        p=oldd.loc[oldd.scenario_id==r.scenario_id].iloc[0]
        differences={name:abs(float(r[name])-float(p[name])) for name in numeric}
        same=all(r[name]==p[name] for name in numeric)
        diagnostics.append({'analysis_class':'revision_comparison','scenario_id':r.scenario_id,'all_numerical_columns_identical':same,
                            'maximum_absolute_numerical_difference':max(differences.values()),
                            'source_models_identical':r.kenet_model_id==p.kenet_model_id and r.yu_model_id==p.yu_model_id,
                            'interpretation':'Unchanged source tables and covariance assumptions; rerun, not copied'})
    previous_tree=historical_files(str(project.resolve()),revision['parent_commit']);reproduction=[]
    for relative in ['results/diagnostic_2x2.csv','results/exploratory/diagnostic_scenario_results.csv','results/exploratory/diagnostic_scenario_inputs.csv',
                     'figures/exploratory/diagnostic_joint_summaries.png','figures/exploratory/diagnostic_joint_summaries.svg',
                     'figures/exploratory/diagnostic_sensitivity.png','figures/exploratory/diagnostic_sensitivity.svg']:
        target=(descriptive_root if relative=='results/diagnostic_2x2.csv' else root)/relative
        if not target.exists():continue
        before=hashlib.sha256(previous_tree[relative]).hexdigest();after=hashlib.sha256(target.read_bytes()).hexdigest()
        reproduction.append({'analysis_class':'revision_comparison','path':relative,'previous_sha256':before,'revised_sha256':after,'byte_identical':before==after})
    lu=[]
    for ident in dict.fromkeys(good.lu_estimate_id):
        rows=good[good.lu_estimate_id==ident];inputs=[r for r in results['auroc_inputs'] if r['estimate_id']==ident]
        differences=[]
        for _,r in rows.iterrows():
            c=core[(core.kenet_estimate_id==r.kenet_estimate_id)&(core.dallas_estimate_id==r.dallas_estimate_id)&(core.assumed_se_auroc==r.assumed_se_auroc)]
            differences.append(float(r.pooled_auroc-c.pooled_auroc.iloc[0]))
        lu.append({'analysis_class':CLASS,'lu_estimate_id':ident,'lu_model_id':inputs[0]['model_id'],'source_row':inputs[0]['source_row'],'individual_auroc':inputs[0]['auroc'],
            'scenario_family':rows.scenario_family.iloc[0],'scenario_count':len(rows),'pooled_min':float(rows.pooled_auroc.min()),'pooled_max':float(rows.pooled_auroc.max()),
            'max_absolute_change_from_matched_lu_logistic':max(abs(x) for x in differences),
            'limitations':'Each range is the spread across 18 conditional scenarios, not a CI or a model-performance superiority comparison'})
    return {'comparison':comparison,'paired_core':paired,'diagnostic_comparison':diagnostics,'reproduction':reproduction,'lu_sensitivity':lu}


def export(root,data):
    root=Path(root);folder=root/'results/exploratory'
    (root/'reports/revisions').mkdir(parents=True,exist_ok=True)
    for key,name in [('comparison','before_after_comparison'),('paired_core','core_before_after'),('diagnostic_comparison','diagnostic_reproduction_comparison'),('reproduction','diagnostic_file_comparison'),('lu_sensitivity','lu_model_sensitivity')]:
        write_csv(folder/f'{name}.csv',data[key])
    write_md(root/'reports/revisions/exclusion_comparison.md',f'''# Lu model exclusion: before-and-after comparison

This is an intentional eligibility revision from the saved 20-model analysis on `exploratory-pooling`. Three whole Lu entries are excluded because their sensitivity/specificity was graphically extracted. This does not assert that their AUROCs were graphical. No additional model is excluded solely for missing operating points. Original source files and curated source records are unchanged; historical baselines are independently validated against Git.

{md_table(data['comparison'],['measure','previous','revised'])}

Core results use Lu logistic regression instead of the excluded index. Additional scenarios systematically use every other retained Lu algorithm, one at a time. Scenario ranges are not confidence intervals. All paired core estimates/conditional intervals/heterogeneity and their changes are in `results/exploratory/core_before_after.csv`.

All {len(data['diagnostic_comparison'])} diagnostic scenarios were recalculated. Numerical identity across every original numeric result column: **{all(r['all_numerical_columns_identical'] for r in data['diagnostic_comparison'])}**. Maximum absolute numerical difference: **{max(r['maximum_absolute_numerical_difference'] for r in data['diagnostic_comparison']):.1f}**. Inputs remain one Yu table and one Kenet table per scenario, with identical counts and assumed covariance. No Lu model contributes to those calculations.

{md_table(data['reproduction'],['path','byte_identical','previous_sha256','revised_sha256'])}

Numerical equality does not validate the diagnostic assumptions. Kenet repeated windows/adults, unresolved Yu units/linkage, sparse cells, missing external validation, possible Dallas overlap and protocol differences remain. The old branch remains the historical analysis, not a current retained-model output.
''')
