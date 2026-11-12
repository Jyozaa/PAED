"""Concise, data-driven LaTeX report with an AUROC figure and no diagnostic graph."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import pandas as pd
from pypdf import PdfReader,PdfWriter
from .ingest import digest


def tex(value):
    s=str(value).replace('\u2014','-').replace('\u2013','-').replace('±',r'$\pm$')
    return ''.join({'&':r'\&','%':r'\%','_':r'\_','#':r'\#'}.get(c,c) for c in s)


def interval(row,metric='auroc',percent=False):
    if metric=='auroc':value=row['pooled_auroc'];low=row['conditional_95_lower'];high=row['conditional_95_upper']
    else:value=row['summary_'+metric];low=row[metric+'_conditional_95_lower'];high=row[metric+'_conditional_95_upper']
    scale=100 if percent else 1
    digits=2 if percent else 4
    return f'{value*scale:.{digits}f} [{low*scale:.{digits}f}, {high*scale:.{digits}f}]'


def build(project,output=None):
    project=Path(project).resolve();root=Path(output).resolve() if output else project
    engine=shutil.which('tectonic')
    if not engine:raise RuntimeError('Tectonic is required to compile the LaTeX report. Install tectonic, then rerun make revised.')
    a=pd.read_csv(root/'results/exploratory/auroc_scenario_results.csv');core=a[(a.scenario_family=='core_lu_logistic')&(a.status=='success_conditional')]
    d=pd.read_csv(root/'results/exploratory/diagnostic_scenario_results.csv');diagnostic=pd.read_csv(root/'results/diagnostic_2x2.csv')
    lu=pd.read_csv(root/'results/exploratory/lu_model_sensitivity.csv');comparison=pd.read_csv(root/'results/exploratory/before_after_comparison.csv').set_index('measure')
    counts=pd.read_csv(root/'results/descriptive_summary.csv').set_index('measure').value
    inventory=pd.read_csv(root/'results/study_inventory.csv');models=pd.read_csv(root/'results/cleaned_models.csv')
    point_data=pd.read_csv(root/'results/auroc_estimates.csv')
    point_by_estimate=point_data.set_index('estimate_id').auroc.to_dict()
    tau=lambda r:f'{r["tau2_logit_estimated"]:.3f}'
    names={'logistic':'LR','xgboost':'XGBoost','soft_voting':'Soft voting','knn_dtw':'KNN-DTW','svc_gak':'SVC-GAK','knn_unif':'KNN-uniform','rf_gini':'RF-Gini','lightgbm':'LightGBM','tabnn':'TabNN','tresnet':'TResNet'}
    pool_rows=[]
    for _,r in core.iterrows():
        yu='Yu 2023 RDN' if '2023' in r.dallas_estimate_id else 'Yu 2022 LR'
        yvalue=point_by_estimate[r.dallas_estimate_id]
        kid=r.kenet_estimate_id.removeprefix('kenet_2023_').removesuffix('_a1')
        individual=f'{point_by_estimate[r.kenet_estimate_id]:.4f}'
        pool_rows.append(' & '.join([f'LR {point_by_estimate[r.lu_estimate_id]:.4f}',f'Test GLM {point_by_estimate["bose_2019_glm_a2"]:.4f}',tex(yu)+f' {yvalue:.4f}',tex(names[kid])+' '+individual,f'{r.assumed_se_auroc:.2f}',interval(r),tau(r)])+r' \\')
    lu_rows=[]
    for _,r in lu.iterrows():
        name=names[r.lu_model_id.removeprefix('lu_2025_')]
        lu_rows.append(' & '.join([tex(name),f'{r.individual_auroc:.4f}',str(int(r.scenario_count)),f'{r.pooled_min:.4f}-{r.pooled_max:.4f}',f'{r.max_absolute_change_from_matched_lu_logistic:.4f}'])+r' \\')
    diag_rows=[]
    for mid in ['kenet_2023_logistic','kenet_2023_xgboost','kenet_2023_soft_voting']:
        r=diagnostic.loc[diagnostic.model_id==mid].iloc[0]
        diag_rows.append(' & '.join([tex(names[mid.removeprefix('kenet_2023_')]),f'{100*r.sensitivity_recalculated:.2f}',f'{100*r.specificity_recalculated:.2f}',f'{100*r.ppv_recalculated:.2f}'])+r' \\')
    baseline=d[(d.kenet_model_id=='kenet_2023_logistic')&(d.kenet_design_effect==5)&(d.yu_variance_inflation==1)&(d.between_covariance_id=='T05R0')&(d.rho_within_assumed==0)].iloc[0]
    current_range=tex(comparison.loc['Core conditional pooled AUROC range','revised']);previous_range=tex(comparison.loc['Core conditional pooled AUROC range','previous'])
    all_range=tex(comparison.loc['All revised Lu-choice conditional pooled AUROC range','revised'])
    compact_auroc_figure(point_data,root)
    text=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=19mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{graphicx,booktabs,array,tabularx,microtype,titlesec}
\usepackage[none]{hyphenat}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\emergencystretch=3em
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\titleformat{\section}{\sffamily\bfseries\large}{}{0em}{}
\titlespacing*{\section}{0pt}{8pt}{4pt}
\begin{document}
{\sffamily\LARGE Paediatric cardiac arrest prediction\par}
{\sffamily\large Revised extraction and exploratory meta-analysis\par}
\vspace{4pt}
\section*{Included studies and exclusions}
Five retrospective study reports contribute \textbf{17 models}: Lu 2025 (8), Kenet 2023 (6), Bose 2019 (1), Yu 2023 (1) and Yu 2022 (1). The original extraction contains six reports and 26 populated model entries, with one additional cross-reference record.

The existing exclusions remain five Yu 2026 composite-outcome models and Yu 2023 Gaussian Naive Bayes. The team additionally excludes Lu XGBoost, gMLP and PEDCA-FT in full because their sensitivity/specificity was extracted graphically and considered insufficiently reliable. Their AUROCs are excluded with the entries; this does not imply that the AUROCs themselves were graph-derived. Missing operating points alone do not exclude the other Lu models.

\section*{Reported AUROC findings}
\begin{center}\small
\begin{tabularx}{\textwidth}{l r X}
\toprule Study & Models & Retained reported AUROC \\
\midrule
Lu 2025 & 8 & \textbf{0.5472-0.7329}; unspecified variation \\
Bose 2019 & 1 & Held-out test \textbf{0.7500}; training 0.9100 \\
Yu 2023 & 1 & \textbf{0.8500 [95\% CI 0.7900, 0.9000]} at one hour \\
Kenet 2023 & 6 & \textbf{0.8670-0.9710}, repeated windows \\
Yu 2022 & 1 & \textbf{0.8300} at the extracted one-hour peak \\
\bottomrule
\end{tabularx}\end{center}
\begin{center}\includegraphics[width=.91\textwidth]{../figures/auroc_short_report.png}\end{center}
{\small The figure above includes all 17 retained models and separates Bose training/test evaluations. Only the supplied Yu 2023 interval is drawn; no confidence limits are inferred from Lu's unspecified variation.}
\newpage
\section*{Revised exploratory pooled AUROC}
The 18 core scenarios now use Lu logistic regression (\textbf{0.6292}) instead of the excluded PEDCA-FT model. Lu logistic is an analyst-selected conventional baseline, not a verified original primary model. Each scenario uses four source groups, with one Dallas report and one Kenet model. Paule-Mandel random effects on logit AUROC and modified Hartung-Knapp intervals are retained. Missing AUROC-scale SEs are assumed to be 0.02, 0.04 or 0.08; the genuine Yu 2023 CI-derived uncertainty is preserved when selected.

The revised core pooled range is \textbf{__CORE_RANGE__}, previously __PREVIOUS_RANGE__. These are scenario extrema, not an uncertainty interval. All brackets in the table below are \textbf{conditional 95\% intervals}, not validated clinical accuracy.

{\scriptsize\setlength{\tabcolsep}{2pt}
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{15mm} >{\raggedright\arraybackslash}p{17mm} >{\raggedright\arraybackslash}p{23mm} >{\raggedright\arraybackslash}p{24mm} r >{\raggedright\arraybackslash}X r}
\toprule Lu 2025 & Bose 2019 & Dallas report & Kenet 2023 & SE & Pooled AUROC [95\%] & $\tau^2$ \\
\midrule
__CORE_ROWS__
\bottomrule
\end{tabularx}}

{\small RDN: functional gradient boosting. LR: logistic regression. Bose GLM is the held-out test. SE applies only where genuine uncertainty is missing. $\tau^2$ is estimated on logit scale under the stated assumptions. Yu 2022 and Yu 2023 are never combined.}

All seven other retained Lu representatives were also crossed with the same 18 configurations, giving \textbf{144 AUROC scenarios} in total. Their combined conditional pooled range is \textbf{__ALL_RANGE__}. The table below reports each representative's scenario range, not a study-level average or confidence interval.

\begin{center}\small
\begin{tabularx}{\textwidth}{l r r X r}
\toprule Lu representative & AUROC & Scenarios & Conditional pooled range & Max change vs LR \\
\midrule
__LU_ROWS__
\bottomrule
\end{tabularx}\end{center}
\newpage
\section*{Sensitivity, specificity and PPV}
Lu 2025 and Yu 2022 have no eligible retained sensitivity/specificity results. Bose reports test sensitivity 60.6\% and specificity 74.1\%. Yu 2023's representative-fold counts yield sensitivity 90.00\%, specificity 64.61\% and PPV 36.36\%; model attribution, threshold, horizon and analysis unit remain unresolved.

The table below gives selected Kenet \textbf{window-level} results recalculated from unchanged counts. Each model uses 3,059 test windows (211 positive), not 3,059 independent patients. The test cohort contains 229 patients with five CA patients.

\begin{center}\small
\begin{tabular}{l r r r}
\toprule Kenet model & Sensitivity (\%) & Specificity (\%) & PPV (\%) \\
\midrule
__DIAG_ROWS__
\bottomrule
\end{tabular}\end{center}
\section*{Exploratory pooled sensitivity and specificity}
All \textbf{96 constrained joint scenarios} were rerun with identical tables and assumptions. Every numerical result is \textbf{identical to the previous analysis}. Conditional sensitivity spans \textbf{__SENS_RANGE__\%} and specificity \textbf{__SPEC_RANGE__\%}; separate extrema are not one operating point or a confidence interval.

The joint normal-logit GLS calculations fix between-source covariance and illustrate variance inflation for Kenet windows and Yu units. They do not estimate unrestricted bivariate heterogeneity or an HSROC curve. For the logistic example with Kenet design effect 5, Yu inflation 1, logit SDs 0.5 and zero correlations, sensitivity is __SENS_CASE__\% and specificity __SPEC_CASE__\% (conditional 95\% intervals). No Lu model contributes a diagnostic count table.
\section*{Prediction timing and possible clinical usefulness}
Lu uses first-24-hour inputs, with the exact outcome interval unverified. Bose reports variable warning times after selecting a two-hour input window; its mean 17-hour warning is not discrimination at a fixed 17-hour forecast. The Yu reports supply extracted one-hour peak AUROCs. Kenet labels five-minute windows within three hours before arrest. These heterogeneous contexts suggest a possible warning signal but do not establish prospective patient detection, acceptable alarm burden or clinical benefit.
\section*{Limitations}
Only one genuine AUROC CI is available; retained Lu variability is unspecified. Missing SEs and diagnostic covariance/design effects are hypothetical. Kenet windows are clustered, sparse positive patients limit inference, and its cohort includes 38 adults. Event multiplicity and window labeling require reconciliation. Yu 2023's representative-fold linkage is unresolved; Yu 2022/2023 may reuse patients. Selected controls and different thresholds, horizons and internal validation limit transportability.

No retained report demonstrates all strict PROSPERO criteria, including external validation. General PICU inclusion is team-agreed but broader than the registered cardiac-ICU scope. Extraction was not independently checked against full papers. Risk-of-bias/certainty review remains incomplete. Conditional intervals omit uncertainty about these assumptions and do not support deployment or safety conclusions.
\section*{Conclusion}
The revised dataset retains \textbf{five reports and 17 models}. Replacing PEDCA-FT with Lu logistic regression changes the exploratory pooled AUROC; considering all eligible Lu alternatives shows additional selection sensitivity. Diagnostic pooling is numerically unchanged because its inputs never included Lu. Confirmatory pooling remains unsupported, and conditional numerical precision does not establish clinical predictive accuracy.
\end{document}
'''
    replacements={'__CORE_RANGE__':current_range,'__PREVIOUS_RANGE__':previous_range,'__CORE_ROWS__':'\n'.join(pool_rows),
        '__ALL_RANGE__':all_range,'__LU_ROWS__':'\n'.join(lu_rows),'__DIAG_ROWS__':'\n'.join(diag_rows),
        '__SENS_RANGE__':f'{100*d.summary_sensitivity.min():.2f}-{100*d.summary_sensitivity.max():.2f}',
        '__SPEC_RANGE__':f'{100*d.summary_specificity.min():.2f}-{100*d.summary_specificity.max():.2f}',
        '__SENS_CASE__':interval(baseline,'sensitivity',True),'__SPEC_CASE__':interval(baseline,'specificity',True)}
    for key,value in replacements.items():text=text.replace(key,value)
    assert '\u2014' not in text and 'Codex' not in text and 'Figure 1' not in text and 'Table 1' not in text
    (root/'reports').mkdir(parents=True,exist_ok=True);source=root/'reports/short_report.tex';source.write_text(text)
    folder=root/'output/pdf';folder.mkdir(parents=True,exist_ok=True)
    epoch=int(datetime.fromisoformat(json.loads((project/'config/revision.json').read_text())['reference_date']).replace(tzinfo=timezone.utc).timestamp())
    env={**os.environ,'SOURCE_DATE_EPOCH':str(epoch),'FORCE_SOURCE_DATE':'1','TZ':'UTC'}
    command=[engine,'--keep-logs','--outdir',str(folder),source.name]
    compiled=subprocess.run(command,cwd=source.parent,env=env,capture_output=True,text=True)
    (folder/'compile_stdout.txt').write_text(compiled.stdout+'\n'+compiled.stderr)
    if compiled.returncode:raise RuntimeError('LaTeX compilation failed:\n'+compiled.stdout+'\n'+compiled.stderr)
    log=(folder/'short_report.log').read_text(errors='replace')
    overflows=[line for line in log.splitlines() if 'Overfull \\hbox' in line or 'Overfull \\vbox' in line or 'Missing character:' in line]
    # Re-serialize pages with stable, minimal metadata. All typesetting and page
    # resources remain from LaTeX; volatile engine metadata is not analytical data.
    pdf=folder/'short_report.pdf';reader=PdfReader(pdf);writer=PdfWriter();writer.append_pages_from_reader(reader)
    writer.add_metadata({'/Title':'Paediatric cardiac arrest prediction','/Subject':'Revised extraction and exploratory meta-analysis','/Author':'','/Creator':'Tectonic','/Producer':'Tectonic; deterministic PDF serialization'})
    with tempfile.NamedTemporaryFile(dir=folder,suffix='.pdf',delete=False) as stream:
        writer.write(stream);temporary=Path(stream.name)
    temporary.replace(pdf);pdf.chmod(0o644)
    reader=PdfReader(pdf);pages=[p.extract_text() or '' for p in reader.pages]
    assert all(p.strip() for p in pages)
    metadata={'analysis_class':'revised_descriptive_and_exploratory','engine':subprocess.check_output([engine,'--version'],text=True).strip(),
        'command':'tectonic --keep-logs --outdir output/pdf reports/short_report.tex (run from reports with adjusted output path)',
        'source_date_epoch':epoch,'pages':len(pages),'source_sha256':digest(source),'pdf_sha256':digest(pdf),
        'page_text_sha256':[hashlib.sha256(p.encode()).hexdigest() for p in pages],
        'layout_warnings':overflows,'included_figures':['figures/auroc_short_report.png'],
        'sensitivity_specificity_graph_included':False,'deterministic_metadata':True}
    (folder/'build_manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if overflows:raise RuntimeError('LaTeX layout requires correction: '+'; '.join(overflows))
    return metadata


def compact_auroc_figure(data,root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from .figures import COLORS,NAMES
    from .exploratory_figures import save
    aliases={'knn dtw':'KNN-DTW','svc gak':'SVC-GAK','knn unif':'KNN-uniform','rf gini':'RF-Gini','tabnn':'TabNN','tresnet':'TResNet','glm':'GLM','rdn boost':'RDN Boost','svm':'SVM','xgboost':'XGBoost','lightgbm':'LightGBM','soft voting':'Soft voting','random forest':'Random forest','logistic':'Logistic'}
    with plt.rc_context({'font.family':'DejaVu Sans','font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'paed_short_report_v1'}):
        fig,ax=plt.subplots(figsize=(6.7,5.3));labels=[]
        for i,(_,r) in enumerate(data.iterrows()):
            y=len(data)-1-i
            if pd.notna(r.ci_lower):ax.errorbar(r.auroc,y,xerr=[[r.auroc-r.ci_lower],[r.ci_upper-r.auroc]],fmt='o',color=COLORS[r.study_id],capsize=2,markersize=3.5)
            else:ax.plot(r.auroc,y,'o',color=COLORS[r.study_id],markersize=3.5)
            ax.text(1.025,y,f'{r.auroc:.4f}',transform=ax.get_yaxis_transform(),va='center',fontsize=8)
            suffix=' (training)' if r.evaluation=='training' else (' (test)' if r.study_id=='bose_2019' else '')
            labels.append(NAMES[r.study_id]+' '+aliases.get(r.model_name,r.model_name)+suffix)
        ax.set_yticks(range(len(data)),labels[::-1],fontsize=8)
        ax.set(xlim=(.45,1),ylim=(-.7,len(data)-.3),xlabel='AUROC')
        ax.axvline(.5,color='#BBBBBB',ls='--',lw=.6);ax.grid(axis='x',alpha=.15)
        ax.set_title('Retained reported AUROC evaluations',loc='left',fontsize=10,fontweight='bold')
        fig.text(.02,.025,f'{data.model_id.nunique()} models; {len(data)} evaluations. Only the genuine supplied CI is shown.\nShared cohorts, differing horizons/units and missing uncertainty preclude confirmatory pooling.',fontsize=6.8)
        fig.subplots_adjust(left=.34,right=.89,bottom=.15,top=.92)
        save(fig,Path(root)/'figures','auroc_short_report')
