"""Write auditable CSVs, readable tables and extraction-bounded interpretation."""
import csv
import html
import json
from pathlib import Path
import markdown
import pandas as pd

STYLE='''body{font:16px/1.55 system-ui,sans-serif;color:#223241;max-width:1200px;margin:40px auto;padding:0 28px}h1{font-size:2.1em;color:#163e53}h2{border-bottom:1px solid #cad9df;padding-top:20px}table{border-collapse:collapse;width:100%;font-size:13px;display:block;overflow-x:auto}td,th{padding:9px 12px;border:1px solid #d9e2e7;vertical-align:top}th{background:#eaf0f4;text-align:left}tbody tr:nth-child(even){background:#f7f9fa}img{max-width:100%;height:auto}code{background:#edf2f5;padding:2px 5px}a{color:#006a87}.notice{background:#fff0d9;padding:15px;border-left:4px solid #b77716}@media print{body{font-size:11px;margin:0}h2{break-after:avoid}img{max-height:85vh}table{display:table;font-size:8px}}'''


def write_csv(path,rows,columns=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if columns is None:
        columns=list(dict.fromkeys(k for row in rows for k in row))
    if not columns:columns=['status']
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader()
        writer.writerows({k:('' if v is None else v) for k,v in r.items()} for r in rows)


def md_table(rows,columns):
    if not rows:return '*No eligible observations.*'
    df=pd.DataFrame(rows)[columns].fillna('Not reported')
    # Escape Markdown delimiters and keep all rows/cells. HTML table also provided.
    s='| '+' | '.join(columns)+' |\n| '+' | '.join('---' for _ in columns)+' |\n'
    for row in df.to_dict('records'):
        s+='| '+' | '.join(str(row[c]).replace('|','/').replace('\n','<br>') for c in columns)+' |\n'
    return s


def write_md(path,text):
    path=Path(path);path.write_text(text.strip()+'\n',encoding='utf-8')
    body=markdown.markdown(text,extensions=['tables','fenced_code','toc'])
    path.with_suffix('.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(path.stem.replace('_',' '))+'</title><style>'+STYLE+'</style><body>'+body+'</body></html>\n',encoding='utf-8')


def principal_tables(data,contexts):
    t1=[]
    for sid,c in contexts.items():
        if not c['working_eligible']:continue
        models=[r for r in data['models'] if r['study_id']==sid]
        r=models[0]
        t1.append({'study_id':sid,'year':r['year'],'country':r['country'],'source_rows':';'.join(str(m['source_row']) for m in models),
                   'doi':r['doi'],'design':r['design'],'icu_setting':c['setting_class'],'population':c['population'],
                   'sample_size_and_ca':c['sample_summary'],'age':r['age'],'sex':c['sex_summary'],
                   'ca_prevalence_raw':r['ca_prevalence'],'outcome':c['outcome_summary'],
                   'model_architectures':'; '.join(m['model_name'] for m in models),'retained_models':len(models),
                   'input_modality':c['modality_summary'],'feature_themes':c['feature_theme'],
                   'training_validation':c['training_summary'],'external_validation':c['external_validation'],
                   'prediction_horizon':c['horizon_group'],'prediction_frequency':c['frequency_summary'],
                   'analysis_unit':c['unit'],'threshold':c['threshold_summary'],'recruitment':c['recruitment_summary'],
                   'dependency_group':c['dependency_group'],'reporting_limitations':c['limitations'],'age_caveat':c['age_caveat']})
    t2=[]
    diag={r['model_id']:r for r in data['diagnostic']}
    for m in data['models']:
        row={k:m.get(k) for k in ['study_id','model_id','model_name','source_row','doi','cohort_id','dependency_group','analysis_unit','prediction_horizon','validation_type','threshold','metric_source','auroc_raw','auroc_point_estimates','sensitivity_raw','specificity_raw','sensitivity_reported','specificity_reported','tp','fp','fn','tn','auprc','accuracy_reported','ppv_reported','npv_reported']}
        a=[r for r in data['auroc'] if r['model_id']==m['model_id'] and r['ci_lower'] is not None]
        row['genuine_95ci']='; '.join(f'{r["ci_lower"]}-{r["ci_upper"]}' for r in a) or None
        d=diag.get(m['model_id'],{})
        for f in ['sensitivity_recalculated','specificity_recalculated','ppv_recalculated','npv_recalculated','accuracy_recalculated','total_units','positive_units','negative_units']:
            row[f]=d.get(f)
        row['other_performance_notes']='Only directional F1/MCC/balanced-accuracy claims supplied for Lu; no numerical values to extract' if m['study_id']=='lu_2025' else ''
        t2.append(row)
    return t1,t2


def risk_evidence(contexts):
    rows=[]
    questions={
      'patient_selection':'Was enrolment consecutive/random and free of inappropriate exclusions and case-control spectrum distortion?',
      'index_test':'Were the model and decision threshold prespecified and evaluated without reference-standard knowledge or leakage?',
      'reference_standard':'Was CA defined and adjudicated reliably, blinded to model output?',
      'flow_timing':'Were all eligible patients included with appropriate lead time, comparable observation windows and valid dependency handling?'}
    for sid,c in contexts.items():
        if not c['working_eligible']:continue
        for domain in questions:
            key={'patient_selection':'patient_selection_evidence','index_test':'index_evidence','reference_standard':'reference_evidence','flow_timing':'flow_evidence'}[domain]
            rows.append({'study_id':sid,'domain':domain,'source_rows':';'.join(map(str,c['source_rows'])),
                         'source_columns':'8-16;37' if domain=='patient_selection' else ('17-24;37-38' if domain=='index_test' else ('26;37' if domain=='reference_standard' else '21-27;37')),
                         'evidence_summary':c[key],'signalling_question':questions[domain],
                         'signalling_answer':'unclear_pending_reviewer','risk_of_bias_rating':'not_assigned_pending_review',
                         'applicability_concern':('general PICU and mixed age require review' if sid=='kenet_2023' else 'pending_review') if domain!='flow_timing' else 'not_applicable',
                         'missing_data_evidence':c['missingness_evidence'],'blinding':'not_established',
                         'reviewer_1':'','reviewer_2':'','consensus':'','decision_needed':'Obtain full public report; independently assess each signalling question and resolve disagreements'})
    return rows


def dictionaries(project,outputs):
    schema=json.loads((project/'config/source_schema.json').read_text())
    rows=[{'source_column_index':r['source_column_index'],'section':r['section'],
           'original_column_name':r['original_column_name'],'analysis_field':r['analysis_field'],
           'publication_policy':r['publication_policy']} for r in schema]
    write_csv(project/'results/data_dictionary_source.csv',rows)
    table=md_table(rows,['source_column_index','section','original_column_name','analysis_field','publication_policy'])
    derived=[]
    for path in sorted((project/'results').glob('*.csv')):
        if path.name.startswith('data_dictionary'):continue
        with path.open(newline='') as f:
            reader=csv.DictReader(f);rs=list(reader)
            for key in reader.fieldnames or []:
                vals=[x.get(key,'') for x in rs if x.get(key,'')!='']
                kind='string'
                if vals and all(x in ['True','False'] for x in vals):kind='boolean'
                elif vals:
                    try:
                        numbers=[float(x) for x in vals];kind='integer' if all(x.is_integer() for x in numbers) else 'number'
                    except ValueError:pass
                meaning=field_meaning(key)
                derived.append({'table':path.name,'field':key,'type':kind,'missing_encoding':'empty cell, never imputed zero','meaning':meaning})
    write_csv(project/'results/data_dictionary_derived.csv',derived)
    write_md(project/'reports/data_dictionary.md',f'''# Data dictionary

Source CSV has 42 columns, two header records and multiline cells. Both exact header rows are preserved in `config/source_schema.json`; section labels are forward-filled only as metadata. Source row means **1-based logical CSV record including both headers**. Physical start/end line numbers are separately retained; these are not interchangeable.

## Source-to-analysis mapping

{table}

## Derived fields and table schemas

Every generated result column, its observed data type, missing-value encoding and meaning is enumerated in [data_dictionary_derived.csv](../results/data_dictionary_derived.csv). This complements the original 42-field mapping. Public minimum aggregate records reside in `data/curated/source_rows.json`; no private notes are needed to rerun the analysis.

- `auroc` is discrimination on 0-1. `reported_variation` is the scaled +/- quantity, **not** a sampling standard error unless its type is established. Here it is unspecified.
- `se_raw_approx=(upper-lower)/(2*1.95996398454)`; `se_logit_approx=(logit(upper)-logit(lower))/(2*1.95996398454)` only for a labelled 95% CI with interior endpoints. Endpoint method and asymmetry remain limitations.
- Sensitivity = TP/(TP+FN); specificity = TN/(TN+FP); PPV = TP/(TP+FP); NPV = TN/(TN+FN); accuracy = (TP+TN)/N. Zero denominators yield missing, not zero.
- Proportions and percentages are 0-1; counts are nonnegative integers in their recorded **analysis unit**. Cohort patients, arrests and repeated windows have distinct denominators.
- Empty CSV cells mean unavailable. `missing_state` distinguishes missing, not_reported, not_applicable, ambiguous, observed_zero and observed. Raw missing markers are retained. A numeric 0 is genuine only when supplied or validly derived.
- `cohort_id` identifies a study-reported cohort; `dependency_group` conservatively groups probable overlaps. This does not assert the exact overlap fraction.
- `pooled_eligible=False` means the current evidence does not support inferential contribution; it is not a judgement that a model performs poorly.
- Rounding tolerance is 0.00055 for Kenet percentage comparisons (allowing effective 0.1 percentage-point rounding) and 0.005 for Yu 2023 integer percentages. Both reported and exact derived values remain available. No statistical test of these differences is implied.
- Lu correspondence-derived outcome/horizon text and free-text notes are withheld. `withheld` is not numerical missingness and does not constitute a public-source verification. Domain evidence summaries are analyst-curated from the extraction with column provenance, not independent full-text verification.
''')


def field_meaning(key):
    known={'source_row':'1-based logical CSV record, including 2 header records',
           'source_line_start':'First physical line of the multiline CSV record',
           'source_line_end':'Last physical line of the multiline CSV record',
           'study_id':'Stable first-author/year publication identifier',
           'model_id':'Study identifier plus normalized architecture; not an independent study',
           'estimate_id':'Model identifier plus evaluation-specific AUROC suffix',
           'cohort_id':'Study-reported population identifier',
           'dependency_group':'Conservative identifier grouping shared/probably overlapping patients',
           'analysis_unit':'Unit counted or evaluated; not necessarily independent patients',
           'metric_source':'Extraction record and metric column provenance',
           'prediction_horizon':'Clinical lead-time context, not necessarily confusion-matrix horizon',
           'table_horizon':'Verified or unresolved lead time for the confusion matrix',
           'validation_type':'Source-reported internal validation method',
           'auroc':'AUROC normalized to 0-1',
           'ci_lower':'Lower genuine 95% AUROC confidence limit when supplied',
           'ci_upper':'Upper genuine 95% AUROC confidence limit when supplied',
           'reported_variation':'Scaled +/- quantity; type specified separately',
           'uncertainty_type':'Explicit CI vs unspecified variation vs not reported',
           'se_logit_approx':'Approximate logit SE from genuine 95% CI endpoints; no imputed variance',
           'se_raw_approx':'Approximate original-scale SE from genuine 95% CI endpoints',
           'pooled_eligible':'Whether evidence and independence checks support inferential pooling',
           'tp':'True positive count in the recorded analysis unit','fp':'False positive count in the recorded analysis unit',
           'fn':'False negative count in the recorded analysis unit','tn':'True negative count in the recorded analysis unit',
           'retained':'Included in team-agreed exploratory working dataset',
           'threshold':'Reported threshold context; not an invented numerical cutoff',
           'genuine_95ci':'Labelled 95% CI supplied for AUROC, else unavailable',
           'auprc':'Source-reported area under precision-recall curve, not AUROC',
           'rating':'No formal rating assigned without reviewer assessment'}
    if key in known:return known[key]
    if key.endswith('_raw'):return 'Original whitelisted extraction text; confidential fields withheld explicitly'
    if key.endswith('_reported'):return key.replace('_reported','').replace('_',' ')+' reported on 0-1 scale, preserved separately from recalculation'
    if key.endswith('_recalculated'):return key.replace('_recalculated','').replace('_',' ')+' derived from complete TP/FP/FN/TN using documented formula'
    if key.endswith('_difference'):return 'Recalculated minus reported proportion; not a hypothesis test'
    if key.endswith('_within_tolerance'):return 'Absolute difference no greater than documented rounding tolerance'
    if key.endswith('_rounding_tolerance'):return 'Absolute proportion difference allowed for reporting precision'
    if key in {'positive_units','negative_units','total_units'}:return {'positive_units':'TP+FN','negative_units':'TN+FP','total_units':'TP+FP+FN+TN'}[key]+' in the recorded analysis unit'
    return 'Descriptive audit/context field: '+key.replace('_',' ')+'; supplied extraction or documented analyst rule, no inferred patient data'


def render_reports(project,data,contexts,statuses,selection,t1,t2):
    out=project/'reports';counts={'records':len(data['audit']),'models':len(data['models']),'studies':len(t1),
                                 'auroc':len(data['auroc']),'tables':len(data['diagnostic'])}
    primary=[r for r in data['auroc'] if r['evaluation']!='training']
    lo=min(r['auroc'] for r in primary);hi=max(r['auroc'] for r in primary)
    yu=next(r for r in data['auroc'] if r['study_id']=='yu_2023')
    rf=next(r for r in data['diagnostic'] if r['model_id']=='kenet_2023_random_forest')
    xgb=next(r for r in data['diagnostic'] if r['model_id']=='kenet_2023_xgboost')
    vote=next(r for r in data['diagnostic'] if r['model_id']=='kenet_2023_soft_voting')
    yd=next(r for r in data['diagnostic'] if r['study_id']=='yu_2023')
    discrepancy=[r for r in data['flags'] if r['code']=='REPORTED_RECALCULATED_DISCREPANCY']
    study_counts=[{'study_id':r['study_id'],'models':r['retained_models'],'unit':r['analysis_unit']} for r in t1]
    table1=md_table(t1,['study_id','sample_size_and_ca','icu_setting','training_validation','model_architectures','prediction_horizon','reporting_limitations'])
    short=[]
    for r in t2:
        short.append({'study':r['study_id'],'model':r['model_name'],'row':r['source_row'],'AUROC (source text)':r['auroc_raw'],
                      'sensitivity (source)':r['sensitivity_raw'],'specificity (source)':r['specificity_raw'],
                      'TP/FP/FN/TN':'/'.join(str(r[x]) if r[x] is not None else 'NR' for x in ['tp','fp','fn','tn']),
                      'AUPRC':r['auprc'] if r['auprc'] is not None else 'NR'})
    table2=md_table(short,list(short[0]))
    write_md(out/'table1_study_characteristics.md','# Table 1. Team-agreed exploratory study characteristics\n\nFive study reports, four conservative potential dependency groups; no confirmed external validation. Full precision and all characteristics are in the CSV.\n\n'+table1)
    write_md(out/'table2_model_performance.md','# Table 2. Retained model results\n\n20 models are dependent within studies. NR means unavailable, not zero or poor performance. Source percentages remain separate from count-derived values in the full CSV. Original +/- quantities are not confidence intervals.\n\n'+table2)
    write_md(out/'data_audit.md',f'''# Full extraction audit

All 3 supplied files were read completely before analysis: the CSV, the 3-page extraction framework, and the 7-page PROSPERO snapshot. PDF text was extracted page by page and its layout checked locally. No original study full texts or patient data were supplied. Original files and extracted PDF text remain local and ignored by Git.

## Counts and source numbering

- 42 columns; two header records (group labels and original field names).
- {counts['records']} records after headers: 26 populated model entries, **1 cross-reference record, 0 completely blank records**.
- Six original study reports: Yu 2026 (5 models), Lu 2025 (11), Bose 2019 (1), Yu 2023 (2 populated, plus 1 unpopulated cross-reference), Kenet 2023 (6), Yu 2022 (1).
- Five Yu 2026 models excluded for composite outcomes, plus one Yu 2023 Gaussian Naive Bayes model excluded for insufficient numerical results.
- The cross-reference at logical record 21 points to Yu 2022 record 29; it is not counted as a seventh exclusion from the 26 populated models and is not forward-filled into an extra result.
- Retained: **{counts['studies']} studies, {counts['models']} models**, four conservative potential cohort groups (Yu 2022/2023 grouped for possible reuse).
- Numerical AUROC: {counts['auroc']} estimates across 20 retained models; Bose contributes distinct training and held-out test values. Only 1 estimate has a labelled 95% CI. Eleven Lu values have unspecified +/- variation.
- Seven complete candidate 2x2 tables: six Kenet models and one Yu 2023 representative fold; two study sources, zero confirmed independent patient-level tables eligible for pooling.

The preliminary “one blank row” checkpoint is corrected to a cross-reference with two non-empty cells. All other preliminary study/model counts reconcile. Source row denotes the **logical record** starting with header record 1; physical multiline spans are retained in `data_audit.csv` and the curated JSON.

## Record decisions

{md_table(data['audit'],['source_row','study_id','model_id','record_type','retained','exclusion_reason'])}

## Scope and metrics

Inventories enumerate every populated original model, study, metric text, outcome context, horizon, validation and dependency identifier. `source_cell_states.csv` audits all 27 x 42 = 1,134 data cells without publishing private text. Excluded results are not used for descriptive working-cohort performance ranges. No 2x2 reconstruction or CI imputation was made.

The supplied framework prioritizes TP/FP/FN/TN and repeated-model extraction. The CSV adds AUROC but lacks dedicated AUROC CI-method, threshold-specific evaluation-unit and cluster-covariance fields. See the complete dictionary and feasibility reports for the consequences.

## Numerical validation

{len(discrepancy)} retained model/metric discrepancy exceeds the documented rounding tolerance: Kenet random-forest specificity, reported 0.778 versus {rf['specificity_recalculated']:.8f} from counts (difference {rf['specificity_difference']:.8f}). Yu 2023 specificity 65% and PPV/NPV 36%/97% agree with exact count-derived values within integer-percentage rounding. Source values are never overwritten.

Other flags include probable Dallas cohort reuse; missing external validation; Kenet repeated-window clustering and 38 adult participants; graph-read Lu operating points; duplicated KNN quality text across Lu models; conflicting recruitment dates; approximate distal AUROC ranges; and uncertain linkage of the Yu 2023 representative-fold table.
''')
    strict=[{'study':sid,'setting':c['setting_class'],'external_validation':c['external_validation'],'strict_status':c['strict_status'],'reason':c['strict_reason']} for sid,c in contexts.items()]
    write_md(out/'protocol_deviations.md',f'''# Protocol discrepancies and exploratory scope

Registered reference: supplied PROSPERO snapshot **CRD420251241478, version 3.0 (1 August 2026), printed 4 November 2026**, pages 2, 4-5 and 7. No amendment was performed by this project. The working decisions below are supplied by the research team in this task, not inferred from apparent performance.

## Registered wording and working decisions

Page 2 limits the population to paediatric patients under 18 in cardiac intensive care and excludes models without external validation or reported accuracy metrics. Page 7 explicitly records narrowing to cardiac intensive care. Page 5 also lists NICU/PICU subgroups, which creates internal ambiguity but does not establish that the restrictive population criterion was waived.

The team explicitly retained **Kenet 2023 general PICU** because cardiac arrest prediction is the working focus. The current five-study cohort is therefore **exploratory and not fully protocol-concordant**. General PICU inclusion does not automatically authorize adult inclusion: Kenet's extraction includes **38 patients aged 18+** with zero CA, with no age-restricted accuracy tables. That additional discrepancy requires confirmation or paediatric-only results.

The team excluded all Yu 2026 models because outcomes combine arrest and therapeutic/composite events, and excluded Yu 2023 Gaussian Naive Bayes because numerical performance cannot be adequately extracted. Yu 2023 RDN Boost remains. Record 21 is a cross-reference to Yu 2022, not a separate quantified logistic model.

## External validation remains unresolved

{md_table(strict,list(strict[0]))}

No retained study **demonstrates** external validation in the supplied extraction. Lu and Bose explicitly lack it; Yu 2022, Yu 2023 and Kenet are recorded NR or only internally validated. NR is not proof that no external validation exists, but it cannot satisfy an affirmative eligibility requirement. Internal held-out testing and cross-validation are not external validation.

Under strict application with demonstrated eligibility required, **0 studies / 0 models** can be confirmed eligible from these files. Four retained CICU study reports / 14 models pass the setting restriction alone; six Kenet models fail that restriction. If the external-validation requirement were explicitly revised, the CICU-only descriptive subset would contain those four reports, with probable overlap in the two Dallas publications. Its AUROC pooling still lacks sufficient independent variances; only one candidate confusion matrix remains, with unresolved linkage. No protocol-concordant pooled analysis is possible now.

## Further issues requiring explicit methodological resolution

- The extraction framework allows multiple models per paper and multiple thresholds. These are repeated results, not independent studies. The present pipeline adds dependency and analysis-unit checks.
- The registration combines AUROC extraction with AUC from HSROC or trapezoidal integration. A study's threshold-integrated AUROC and area under a cross-study summary ROC are different estimands. A single sensitivity/specificity pair cannot recover a study's AUROC.
- Protocol sensitivity/specificity wording mentions neonates despite broader paediatric eligibility. Specificity concerns non-arrest units, not the proportion of arrest cases detected. SMD is mentioned without a defined contrast and is not used here.
- The full-protocol citation in the snapshot is the PRISMA 2020 reporting statement, not an accessible study-specific full protocol. A complete search strategy, screening totals and independent extraction decisions are not supplied. The dataset flow is not represented as a full PRISMA flow.
- QUADAS-2 and adapted GRADE remain registered. No tool replacement, dual-reviewer assessment or formal certainty grade is asserted.

## Team confirmation before publication

Confirm and document the general-PICU change; resolve mixed-age Kenet eligibility; clarify whether to retain the external-validation requirement, seek missing external studies or formally revise the protocol; obtain patient/cluster-adjusted results and genuine AUROC uncertainty; confirm Dallas overlap; confirm representative models and non-peak-driven horizon choices; verify the Yu 2023 table's model, fold, threshold, horizon and unit; independently assess bias/certainty and reconcile any changes with the register. This report does not claim a waiver or amended PROSPERO record.
''')
    selection_table=md_table(selection,['study_id','representative_model','selection_reason','genuine_variance_estimates','reason'])
    write_md(out/'auroc_feasibility.md',f'''# Analysis A: AUROC random-effects synthesis

**Status: Not statistically defensible from the supplied data.** The feasibility workflow completed; no inferential fit was attempted after failed eligibility checks. No pooled AUROC, p-value, tau-squared, I-squared or prediction interval exists.

## Estimand and selection

An exploratory pooled logit AUROC across different algorithms would describe discrimination of selected, validated model estimates in comparable paediatric CA cohorts at comparable horizons. It would not estimate a single deployable AI tool, detection sensitivity, or the fraction of preventable arrests.

Hierarchy is recorded in `config/analysis.json` before the fitting stage: explicitly named index model or sole model; external validation preferred, then patient-disjoint test, then patient-grouped CV; separate horizons; one estimate per independent cohort. No automatic maximum-AUROC rule is used. Lu's PEDCA-FT is the named index tool even though gMLP has higher AUROC. Kenet's performance-selected “best” XGBoost is not automatically designated the primary model. Extracted 1-hour peaks in Yu reports are retained descriptively, not represented as prespecified cross-study endpoints.

{selection_table}

## Actual evidence and variance

Five study reports / 20 models / {len(data['auroc'])} numerical evaluations, including Bose training (0.91) and held-out test (0.75). Twenty nontraining/other reported model points range **{lo:.4f}-{hi:.4f}**; these are descriptive extremes, not a pooled range or CI. AUROC evaluation units differ: admission with patient-grouped CV (Lu), minute scores with patient split (Bose), representative/hourly EHR contexts (Yu), and repeated five-minute windows (Kenet). Four conservative potential dependency groups exist; exact between-study overlap is unverified.

Only Yu 2023 RDN Boost at the extracted 1-hour peak has a genuine CI: **0.85 (95% CI 0.79-0.90)**. The endpoint approximation gives original-scale SE **{yu['se_raw_approx']:.8f}**, logit-scale SE **{yu['se_logit_approx']:.8f}**. The CI construction and the assumptions behind logit normality are not supplied, so even this variance would need methodological verification for pooling. Eleven Lu +/- values have unspecified statistical meaning; 73.29 +/- 2.47 becomes estimate 0.7329 and unspecified variation 0.0247, never SE. Fold variation would not automatically be independent sampling error because CV training sets overlap. Bose describes bootstrap uncertainty, but numerical AUROC limits/SE are absent in the extraction. Kenet and Yu 2022 have no usable AUROC variance.

## Feasibility checks and conditional model

Only **one variance-bearing independent cohort** is available; clinical/validation/horizon comparability is not established; Yu 2022/2023 may reuse the same 160 CA and 711 control patients in Dallas during 2010-2019. There are **0 contributing studies / 0 model estimates in a fitted meta-analysis**. Missing variance is not approximated from AUROC alone or from unrelated patient denominators.

The conditional R workflow `scripts/meta_analysis.R` uses established `metafor::rma.uni`, REML on logit AUROC and a modified Hartung-Knapp interval (t critical value; variance scale bounded below by the conventional inverse-information variance). It requires at least three independent, explicitly selected comparable estimates, usable genuine logit SEs and no duplicated dependency groups. This is a conservative project safeguard, not a universal sample-size rule. An eligibility-authorized fit would back-transform the estimate/CI, report tau-squared on logit scale, record session information and save its genuine forest plot. Current input stops before fitting. This future fitting route is not claimed as empirically validated on the supplied evidence.

No variance-imputation sensitivity analysis, leave-one-out, subgroup model, meta-regression, funnel test, Egger regression, prediction interval or heterogeneity statistic is scientifically supported. Raw AUROC and genuine CI plots remain available without a summary diamond. See [metafor documentation](https://wviechtb.github.io/metafor/reference/rma.uni.html) for the underlying estimator.
''')
    diag_table=md_table(data['diagnostic'],['study_id','model_name','tp','fp','fn','tn','sensitivity_recalculated','specificity_recalculated','ppv_recalculated','npv_recalculated','analysis_unit','table_horizon'])
    write_md(out/'diagnostic_feasibility.md',f'''# Analysis B: bivariate/HSROC diagnostic synthesis

**Status: Not statistically defensible from the supplied data.** Count validation and the hierarchical eligibility workflow completed. There is no fitted bivariate model, HSROC curve, pooled sensitivity/specificity, convergence assessment, CI or heterogeneity estimate.

## Seven tables, two study sources, no confirmed eligible independent patient-level tables

{diag_table}

Each Kenet table totals **3,059 windows = 211 positive + 2,848 negative**, shared across six algorithms. These belong to a **229-patient test set with five CA patients**, not 3,059 independent patients or 211 independent arrests. Overall cohort totals (1,145 patients, 15 CA; 14,714 windows, 516 positive) are distinct from test totals. Patient-disjoint train/test splitting prevents certain leakage but does not remove within-patient dependence among test windows. No intrapatient correlation, cluster-adjusted covariance, patient-level predictions or patient-level confusion table is supplied. No Wilson/binomial interval is displayed for windows.

The Yu 2023 matrix is a representative fold: **36 TP, 63 FP, 4 FN, 115 TN**, total **218 units**. Sensitivity = {yd['sensitivity_recalculated']:.4f}; specificity = {yd['specificity_recalculated']:.6f}; PPV = {yd['ppv_recalculated']:.6f}; NPV = {yd['npv_recalculated']:.6f}. The extractor **assumed** model attribution to RDN Boost; exact fold, threshold, horizon and whether units are patients/events/windows are not established. Its 40 positive units exceed 160/5 = 32, so a simple equally divided patient-fold reconstruction is not justified; this does not prove an error. The matrix is not silently linked to the 1-hour AUROC. It cannot be reconstructed or reweighted from cohort totals.

## Thresholds and conditional synthesis

Kenet thresholds were chosen at validation-ROC operating points, with numeric values unavailable. Bose uses bootstrap-dependent ROC thresholds; example scores 0.5/0.56 are not a common operating point. Yu thresholds are missing; Yu 2022's NIRS predictor cutoff is not a multivariable classifier threshold. Lu's three operating points are graph-read and have no verified count denominators or thresholds. These points are descriptive only.

A full bivariate model has two mean logits, two between-study variances and a correlation. Even granting independence to the **two source cohorts**, covariance estimation would be exceptionally fragile. Here Kenet clustering and Yu linkage fail before this statistical question arises: **0 eligible datasets; 0 independent studies / 0 model estimates contribute to an inferential fit**. Models are not separate studies. Separate univariate pooling cannot solve this dependency or recover a universal threshold.

The conditional R code implements established `mada::reitsma` for eligible interior proportions with REML and zero continuity correction, requires at least five independent datasets plus explicit model/unit/comparability confirmation, checks finite covariance, and records the true summary and fitted SROC only after a successful model. The minimum is an analyst safeguard, not an identifiability theorem. For zero-cell sparse independent data it stops and calls for a binomial HSROC implementation rather than silently correcting counts. No zero cells exist in these seven tables, but their analysis units fail the gate. No artificial convergence attempt or fixed correlation is used.

[Primary simulation research](https://pmc.ncbi.nlm.nih.gov/articles/PMC5564999/) shows that complex hierarchical fits can be problematic with few/sparse studies; simpler models may be considered when scientifically suitable, but cannot make clustered or unlinked extraction rows independent. [Package documentation](https://rdrr.io/cran/mada/man/reitsma.html) defines the candidate bivariate implementation.

Sensitivity/specificity forest-style point plots and a **non-pooled** ROC-space scatter are generated. No smooth curve is drawn through heterogeneous model points. Denominator or clustering uncertainty is not disguised as narrow error bars.
''')
    write_md(out/'heterogeneity.md','''# Heterogeneity and sensitivity analyses

The pairwise matrix contains all 10 pairs among five retained reports. No pair is approved for statistical pooling from current data. Same-setting comparisons may provide clinical context, but setting alone does not establish a common estimand. The matrix distinguishes potential patient overlap from no identified overlap; the latter is not proof of independence.

- **Lead time:** Lu uses first-24h input, with exact outcome interval requiring public verification. Bose reports variable warning time (mean 17h among 16 cases) after selecting a 2h input window; this is not AUROC for a fixed 17h forecast. Yu extracts 1h peak results with other horizons insufficiently numerical. Kenet labels five-minute windows within 3h of arrest.
- **Architecture:** regressions, nearest-neighbour/kernel baselines, tree ensembles, neural networks and multimodal transformer differ alongside inputs, outcome windows and validation. Within-study contrasts remain dependent. No cross-study causal superiority ranking or significance test is supported.
- **Population:** four CICU reports and one general PICU; Bose infants <=1y, broader paediatric cohorts elsewhere. Kenet includes 38 adults. No exact consistent neonatal strata exist for subgroup fitting.
- **Validation:** internal CV or patient split; Yu 2022 independent validation unreported; external validation not demonstrated. Training performance is explicitly separated from test performance.
- **Units:** admission-, minute-score-, hourly observation- and five-minute-window estimands cannot be interchanged. Two Dallas reports probably share patients and are grouped conservatively.
- **Outcome and sampling:** mechanical-function cessation, CPR and registry definitions differ; some samples select cases/controls or negative windows relative to discharge. Case fractions and window proportions are not prospective population CA risks.
- **Inputs:** ECG/HRV in Bose and Kenet; NIRS/vasoactive signals in Yu; EHR static/time-series/tabular-text representations in Lu. Demographics are documented even when not a primary thematic target; they can contribute performance and applicability differences.

The team working cohort has five reports/20 models. Restricting only to registered CICU setting leaves four reports/14 models (at most three conservative dependency groups). Requiring demonstrated external validation leaves zero confirmed eligible studies. Neither sensitivity restriction produces a defensible pooled analysis. No independent pooled estimates exist to support leave-one-out, quantitative subgroups, meta-regression, I-squared, publication-bias regression or prediction intervals.
''')
    write_md(out/'risk_of_bias.md','''# Risk-of-bias evidence worksheet

Registered tool: **QUADAS-2**. Twenty study-domain records cover patient selection, index test, reference standard and flow/timing for all five retained studies. Applicability prompts cover the first three domains; flow applicability is not applicable. These are evidence summaries and reviewer prompts, **not completed formal ratings**. All risk judgements are pending; missing blinding is not automatically high risk, and apparently detailed reporting is not automatically low risk. Blank reviewer fields must be completed by independent assessors with disagreements resolved.

Important evidence to assess includes retrospective single-centre selection, selected case/control spectra, adult inclusion in Kenet, extensive missing-waveform exclusions (1,019 of 2,164 patients, including 57 CA), different case/control reference times, data-dependent feature and threshold selection, potential leakage in normalization/feature selection, unavailable independent validation, and dependence of repeated observations. Kenet extraction repeats a logistic-model index description in all quality fields; Lu repeats KNN-Dtw quality text across architectures. This is a reporting-template limitation and cannot establish each model's conduct. Source columns and rows accompany every worksheet record; private correspondence details are not reproduced.

[PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505) specifically addresses prediction models using regression or AI, including model development and evaluation quality. It may capture overfitting, sample size and validation issues more directly than diagnostic-test QUADAS-2. The team may consider it as an additional or explicitly amended framework; this pipeline does not silently replace the registered instrument. No independent dual-reviewer assessment was performed by software. Obtain public full texts and complete reviewer-level signalling questions before publication.
''')
    write_md(out/'certainty_of_evidence.md','''# Evidence certainty: adapted GRADE preparation

The protocol specifies adapted GRADE for diagnostic/prognostic accuracy. **No definitive certainty rating is assigned** by this extraction-only analysis. There is no defensible pooled effect or common threshold, and formal bias assessment and independent reviewer consensus are incomplete. High AUROC does not itself confer high certainty.

| Domain | Available evidence | Required decision |
| --- | --- | --- |
| Risk of bias | Retrospective single-centre samples; validation, selection and timing concerns; worksheet pending | Independent QUADAS-2 assessment and consensus |
| Inconsistency | Marked differences in horizons, units, algorithms and outcomes; within-study model dependence | Define comparable estimands before quantitative inconsistency assessment |
| Indirectness | General PICU vs cardiac ICU; mixed-age Kenet; selected controls/windows; no demonstrated external validation | Define target use, age and workflow; resolve protocol changes |
| Imprecision | Only one genuine AUROC CI; five CA patients in Kenet test set; only five Bose test cases; cluster uncertainty absent | Obtain genuine study uncertainty, patient-level/cluster-adjusted diagnostic results |
| Publication/reporting bias | Search/screening records and full results unavailable; many missing metrics, graph-read values | Retrieve search history and public full reports; avoid unsupported funnel tests |
| Clinical usefulness | No demonstrated prospective effect on arrests, survival, workload or net benefit | Prospective external evaluation, calibration, decision-curve/utility evidence and alert burden |

No universal sensitivity, false-alarm rate, implementation recommendation or formal GRADE category can be supported. A future summary-of-findings table must define population, index tool, horizon, threshold and analysis unit, identify independent studies, and show reviewer-consensus certainty for each outcome. Do not convert the current absence of estimable pooled precision into evidence of ineffectiveness.
''')
    captions='''# Figure captions

All figures are exported as 220-dpi PNG and vector SVG. All are descriptive; no pooled forest plot or fitted HSROC was generated because neither model passed eligibility checks.

1. **auroc_descriptive**: 21 numerical AUROC evaluations from five reports/20 models. Bose training and test are separate. Only the supplied Yu 2023 genuine 95% CI is an error bar; Lu +/- variability is unspecified and not drawn as a CI. Different horizons, units and validation, plus shared cohorts, preclude pooled inference.
2. **sensitivity_descriptive**: Eleven model/evaluation points. Complete matrices are recalculated; other source proportions remain descriptive. Three Lu points are graph-read (open markers). Kenet units are repeated five-minute windows, and Yu 2023's unit/horizon linkage is unresolved. No naive binomial CI or pooled point is shown.
3. **specificity_descriptive**: Twelve model/evaluation points, including Bose's separate entire-dataset specificity. Count-derived Kenet random-forest specificity differs from its reported 77.8%; both are retained in tables. Units and CI limitations match the sensitivity plot.
4. **sroc_descriptive**: Eleven model-specific sensitivity/specificity pairs in ROC space, with count-derived pairs where complete and reported pairs otherwise. The diagonal is a visual reference only. No threshold-aggregated curve, confidence region or SROC area is fitted. Six Kenet models are dependent; Yu 2023 linkage is uncertain; Lu points are graph-read.
5. **heterogeneity_overview**: Five-report comparability/dependency matrix. All off-diagonal pairs lack adequate evidence for current pooling. Probable Dallas patient reuse is marked separately; no identified overlap elsewhere does not prove independence. Clinical comparability is detailed in the matrix CSV and heterogeneity report.
6. **inclusion_flow**: Dataset audit only: 27 post-header records, 26 populated model entries/six reports, one cross-reference, six populated-model exclusions, five retained reports/20 models. The strict protocol subset has zero demonstrated eligible studies. Search and screening totals were not supplied; this is not a PRISMA literature-search flow chart.
'''
    write_md(out/'figure_captions.md',captions)
    write_md(out/'plain_english_summary.md',f'''# What the supplied evidence tells us

The analysis retained **five study reports and 20 models**, after excluding five models for a combined outcome that was not cardiac arrest alone and one model without usable numerical results. All studies are from single US centres. Two reports may reuse the same Dallas patients, so five reports do not necessarily mean five independent populations.

Reported model AUROCs span **{lo:.4f} to {hi:.4f}**. AUROC describes how well risk scores rank arrest versus non-arrest observations across thresholds. **An AUROC of 0.85 does not mean 85% of cardiac arrests were detected.** Detection sensitivity depends on a chosen threshold, time horizon and what is counted (patients, admissions or time windows).

There is only **one genuine reported AUROC confidence interval**, for Yu 2023: 0.85 (95% CI 0.79-0.90). Eleven Lu models have +/- numbers whose meaning is unspecified. Without reliable uncertainty and independent comparable results, an average would give false confidence. The AUROC meta-analysis is therefore not statistically defensible from these files.

Seven complete confusion matrices come from just **two study sources**. Six Kenet models use repeated five-minute windows from 229 test patients, only five of whom experienced arrest. XGBoost correctly classified {xgb['tp']} of {xgb['positive_units']} positive windows (sensitivity {100*xgb['sensitivity_recalculated']:.2f}%), but produced **{xgb['fp']} false-positive windows**, with PPV {100*xgb['ppv_recalculated']:.2f}%. This does not mean that {xgb['positive_units']} children arrested, or that only one child was missed. Several windows can belong to the same child, and alarm suppression/repeated-alert rules are unknown. The soft-voting model had {vote['fp']} false-positive windows and {vote['fn']} missed positive windows, with PPV {100*vote['ppv_recalculated']:.2f}%. These illustrate a trade-off within one dataset, not proof of the best clinical tool. False-positive windows cannot be converted into alarms per patient-day from the supplied data.

Yu 2023's representative-fold table gives 90% sensitivity and {100*yd['specificity_recalculated']:.2f}% specificity, but its model attribution, prediction horizon, threshold and counted unit need confirmation. Lu's three reported operating points are graph-read and differ markedly in sensitivity; they have no verified count tables. Combining these figures would be misleading. The sensitivity/specificity meta-analysis is also not statistically defensible.

The registered protocol specifies cardiac ICU patients and external validation. The team agreed to include general PICU, making this an exploratory working analysis. Kenet also contains 38 adults, requiring a separate decision. None of the five reports demonstrates external validation in the supplied extraction. Strict protocol eligibility cannot currently be confirmed for any report.

These results support further evaluation of prediction models, but do not establish safety, reliable detection of individual children's arrests, acceptable alert burden or readiness for clinical deployment. Obtain public-source definitions, genuine uncertainty, independent external evaluations and patient-level or cluster-adjusted performance; resolve cohort overlap and protocol eligibility; and complete independent risk-of-bias review before drawing stronger conclusions. Missing results do not imply poor performance.
''')
    main=f'''# AI prediction of paediatric cardiac arrest: statistical analysis of the supplied systematic-review extraction

Analysis reference date: 11 November 2026. Registered review: CRD420251241478. **Exploratory working cohort; not fully protocol-concordant.** This is a completed analysis of the supplied extraction, not a claim that a new comprehensive database search, full-text re-extraction or dual-reviewer systematic review has been completed.

## 1. Research question and objectives

How accurately do AI and machine-learning algorithms predict cardiac arrest in paediatric intensive care? Primary objectives were feasibility-tested random-effects AUROC synthesis and bivariate/HSROC sensitivity-specificity synthesis. Secondary objectives were descriptive comparisons of architecture, lead time, validation, ICU setting and input modality, with dependency, bias and clinical-use assessment.

AUROC is threshold-integrated ranking discrimination. Sensitivity is TP/(TP+FN) at an operating threshold; specificity is TN/(TN+FP). PPV is the fraction of positive predictions that are true positives in the evaluated sample. These are different estimands. The analysis unit must accompany each: repeated windows are not independent children or independent arrests.

## 2. Data sources and study eligibility

All three supplied sources were fully read: the 42-column CSV with two header records, the 3-page List of Variables, and 7-page PROSPERO snapshot version 3.0. Original files remain local; SHA-256 hashes are in the run manifest. Logical CSV record numbers include the two headers; physical line spans account for multiline cells. The public curated inputs contain only whitelisted aggregate facts, metric texts and source identifiers. Private correspondence content, raw PDFs/CSV, personal contact details and unpublished free-text notes are excluded.

The data contain **27 post-header records, six study reports and 26 populated model entries**. Record 21 contains a cross-reference rather than extracted numerical results. It points to the Yu 2022 logistic model in record 29. There are zero fully blank records. No original study full texts, raw patient data, independent reviewer forms, database search logs or full screening totals were supplied. Source study facts below are extraction-based and not independently reverified against full reports. Internet checks were restricted to methodological guidance, not additions to the included-study dataset.

## 3. Agreed exclusions and protocol discrepancies

All five Yu 2026 models were excluded because accuracy concerns composite adverse events rather than arrest alone. Yu 2023 Gaussian Naive Bayes was excluded because numerical results were not adequately extractable. The working cohort retains **five reports and 20 models**: Lu 2025 (11), Bose 2019 (1), Yu 2023 RDN Boost (1), Kenet 2023 (6), Yu 2022 (1).

PROSPERO restricts the population to under-18 cardiac ICU inpatients and excludes models without external validation. The team explicitly accepted general PICU, retaining Kenet. Its 38 adult participants create an additional unresolved eligibility issue. Lu and Bose explicitly lack external validation; none of the other reports demonstrates it in the extraction. Thus **zero studies/zero models demonstrate all strict criteria**. NR is not proof that validation never occurred, and no formal waiver or register amendment is claimed. Restriction to CICU setting alone leaves four reports/14 models. See [protocol deviations](protocol_deviations.md) for the registered wording, affected studies and required decisions.

## 4. Data cleaning and validation

The deterministic pipeline preserves grouped header metadata, source metric text and separate numerical fields. It standardizes percentages and proportions, semantically separates Bose training/test AUROCs, parses the labelled Yu 2023 CI, and retains unspecified +/- variation without treating it as SE or CI. Approximate distal Yu 2022 graphical ranges are not manufactured into hourly observations. Missing, not reported, not applicable, ambiguous and zero states are distinct; 1,134 source data-cell states are auditable. No missing value is set to zero and no 2x2 is reconstructed from rounded percentages.

Seven complete count tables are recalculated using standard formulas, with reported and count-derived values retained separately. One comparison exceeds the study-appropriate rounding tolerance: **Kenet random-forest specificity reported 77.8%, count-derived {100*rf['specificity_recalculated']:.4f}%**. Yu 2023 integer percentages agree within rounding. Each numerical AUROC and count table retains study/model IDs, source record, DOI via the model table, metric source, horizon context, validation and dependency identifiers.

Yu 2022/2023 share institution, recruitment period (November 2010-January 2019), and 160 CA/711 control counts. They are conservatively assigned one potential dependency group. This does not determine exact overlap or permit their variances to be combined. Five reports therefore form at most **four potential independent cohort groups** under this working assumption.

## 5. Characteristics of included studies

All five reports describe retrospective single-centre US populations. Four are cardiac/cardiovascular ICU reports and one is general PICU. Samples vary from Bose's 64 analysed patients (20 held-out test patients, five CA) to Lu's 3,566 patients/4,672 admissions. Kenet has 1,145 retained patients (15 CA) after 1,019 exclusions, including 57 CA; test set is 229 patients with five CA. Both Dallas reports contain 160 cases and 711 controls, with probable patient reuse. The 18.37% Dallas selected-sample fraction is not a natural population incidence. These denominators cannot be summed as independent patient recruitment.

{md_table(study_counts,['study_id','models','unit'])}

[Full Table 1](table1_study_characteristics.html) includes age, sex, setting, outcome definitions, recruitment discrepancies, input modalities, architectures, training/validation, horizon/frequency, units and limitations. [Full Table 2](table2_model_performance.html) includes all 20 model results, original and recalculated performance, genuine CI, counts and available precision-recall metrics.

## 6. Descriptive predictive performance

There are **21 exact numerical AUROC evaluations from 20 models**, because Bose reports training 0.91 and held-out test 0.75. The 20 nontraining/other reported model evaluations span **{lo:.4f}-{hi:.4f}**. This is a descriptive minimum/maximum across heterogeneous dependent results; it is not a pooled estimate, confidence interval or cross-study architecture ranking. Lu's 11 AUROCs span 0.5472-0.7504; named index PEDCA-FT is 0.7399 with unspecified variation 0.0316, while gMLP is 0.7504 with unspecified variation 0.0352. Kenet AUROCs range 0.867-0.971 on repeated windows. Yu 2022 is 0.83 at the extracted 1-hour peak; Yu 2023 is 0.85 (95% CI 0.79-0.90) at 1 hour.

Sensitivity and specificity are numerically supplied for 11 retained models, with an additional entire-dataset specificity for Bose. Three Lu operating points are graph-read: XGBoost 39.04%/83.14%, gMLP 8.22%/97%, PEDCA-FT 42.47%/84.69%; they have unknown thresholds and no verifiable integer tables. These show why high AUROC need not mean high sensitivity at the chosen operating point.

Kenet XGBoost's table gives sensitivity **{100*xgb['sensitivity_recalculated']:.4f}%**, specificity **{100*xgb['specificity_recalculated']:.4f}%**, PPV **{100*xgb['ppv_recalculated']:.4f}%** (210 TP, 866 FP, 1 FN, 1,982 TN). Soft voting gives sensitivity **{100*vote['sensitivity_recalculated']:.4f}%**, specificity **{100*vote['specificity_recalculated']:.4f}%**, PPV **{100*vote['ppv_recalculated']:.4f}%** (192 TP, 345 FP, 19 FN, 2,503 TN). The difference describes window-level threshold trade-offs in a shared sample; inferential paired comparisons are not possible without joint predictions. Six reported AUPRCs range 0.529-0.797; selected negative windows shape these precision/recall values and PPVs.

## 7. AUROC meta-analysis: methods, feasibility, results

**Status: Not statistically defensible from the supplied data.** Five reports/20 models supply 21 points; **one independent cohort supplies a labelled AUROC CI**. **Zero studies and zero model estimates contribute to a pooled fit.** Units and horizons are heterogeneous; the strict-protocol confirmed subset is empty.

The model-selection hierarchy prefers explicitly named/sole index models and appropriate independent validation, with no highest-AUROC rule. Kenet's representative-model decision is unresolved. Yu peak horizons are not treated as prospectively selected for cross-study synthesis. From Yu 2023's labelled CI, endpoint normal approximation yields SE {yu['se_raw_approx']:.8f} on AUROC scale and {yu['se_logit_approx']:.8f} on logit scale. Its CI construction is not established. Eleven unspecified Lu +/- quantities and narrative bootstrap descriptions cannot supply valid inverse-variance weights.

The guarded established-package route is REML `metafor::rma.uni` on logit AUROC with modified Hartung-Knapp t CI and back-transformation, but the eligibility gate stops before optimization. No mean is substituted, variance invented, or pooled diamond drawn. Tau-squared, I-squared, prediction interval and meta-analytic p-values are not estimable here. [Full AUROC feasibility assessment](auroc_feasibility.md) documents all checks.

## 8. Sensitivity/specificity meta-analysis: methods, feasibility, results

**Status: Not statistically defensible from the supplied data.** **Seven model tables from two study sources; zero confirmed eligible independent patient-level datasets; zero studies/model estimates in a pooled fit.** Six tables count repeated five-minute windows from the same Kenet sample; one Yu 2023 table is a representative fold with unresolved model attribution, threshold, horizon and unit. No clusters or patient-level data can be recovered from marginal aggregate counts.

All six Kenet tables total 3,059 windows (211 positive, 2,848 negative), not patients. Its test set has five CA patients. Yu 2023's table totals 218 units and recalculates to sensitivity 0.9000, specificity {yd['specificity_recalculated']:.6f}, PPV {yd['ppv_recalculated']:.6f} and NPV {yd['npv_recalculated']:.6f}. This is not assumed to be a 1-hour operating point corresponding to its AUROC. No naive binomial confidence limits are calculated from windows or unresolved units.

The conditional bivariate implementation uses `mada::reitsma` with REML for independent interior proportions, with no unnecessary count correction. It requires explicit selection and comparability confirmation and a conservative minimum of five independent datasets; binomial HSROC would be needed for sparse boundary data. Even an optimistic two-study fit cannot reliably characterize the full random-effects covariance here, and its underlying unit/linkage assumptions fail first. No model convergence, pooled sensitivity/specificity or fitted summary ROC is claimed. [Full diagnostic feasibility assessment](diagnostic_feasibility.md) includes all validated matrices.

## 9. Heterogeneity and sensitivity analyses

The pairwise matrix examines all 10 report pairs. ICU mix, age, disease spectrum, arrest definitions, case/control selection, input representation, lead time, model selection, validation and sampling unit vary substantially. Mean warning time (Bose), first-24h input (Lu), fixed extracted pre-arrest peak points (Yu) and within-3h positive windows (Kenet) represent different targets. Thematic inputs include vitals, ECG/HRV, labs, NIRS, medication and demographic context, with no universal shared variable set.

The exploratory cohort is compared with CICU-only (four reports/14 models) and strict demonstrated-eligibility (zero) subsets; neither supports pooling. Potential Dallas reuse prevents independent treatment of Yu 2022/2023. No meta-regression, quantitative subgroup fitting, leave-one-out, Egger regression, funnel-asymmetry test or unstable heterogeneity statistic is performed. See [heterogeneity report](heterogeneity.md) and matrix CSV.

## 10. Risk of bias and certainty

Twenty QUADAS-2 domain evidence records and applicability prompts were prepared. All formal judgements remain pending independent reviewer assessment. Concerns needing review include spectrum selection, large missing-data exclusions, sparse events, threshold/model selection, differential time anchoring, repeated observations, model leakage and validation. Reported detail is not proof of low risk, and missing detail is not proof of high risk. [PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505) may be a useful additional prediction-model-specific framework; it has not replaced the registered QUADAS-2 tool.

Adapted GRADE domains are documented without an unsupported final grade. Bias, indirectness, precision and inconsistency cannot be resolved by apparently high AUROC. Search/reporting-bias evidence is incomplete. No software-based claim of independent dual review is made. See [risk-of-bias report](risk_of_bias.md) and [certainty worksheet](certainty_of_evidence.md).

## 11. Clinical interpretation

These studies suggest discriminatory signal in selected retrospective data, while documenting substantial operating-point trade-offs. Kenet's high sensitivity concerns positive five-minute windows, not the proportion of children whose arrests were successfully anticipated. A false-positive window is not automatically a distinct clinical alarm. The negative-window sampling scheme, alarm suppression, treatment actions and prospective CA incidence affect actual workload and PPV. Selected case-control or window PPVs cannot be transported directly to an unselected ICU population.

No evidence here establishes calibration, acceptable alarms per patient-day, clinical net benefit, prospective prevention of arrests, improved survival or safe deployment. External and prospective evaluation at clinically useful horizons, with patient/cluster-aware uncertainty and explicit thresholds, is required to assess clinical usability.

## 12. Limitations

This is analysis of a supplied aggregate extraction, with no independently verified original full texts, IPD, complete search/screening logs or full protocol. Extraction assumptions and graphical readings are traceable but remain uncertain. Private correspondence is withheld rather than treated as public corroboration. Only one genuine AUROC CI exists; eleven variability quantities are unspecified. Multiple models/horizons and probable cohort reuse create dependency. Seven tables do not yield seven independent studies. Kenet clustering, five test CA patients and adult participants limit interpretation; Yu 2023 linkage is unresolved. Case/control and negative-window sampling affect transportability; bias/certainty assessment remains incomplete. Conditional R fitting code is provided, but no ineligible inferential model was run or validated as a current result.

## 13. Evidence-based conclusion

**Neither planned inferential meta-analysis is statistically defensible from the supplied evidence.** The completed descriptive synthesis retains five reports and 20 models, preserves 21 AUROC evaluations, one genuine CI and seven complete candidate diagnostic tables, and explains their provenance, dependency and limitations. These data cannot establish a universal AUROC, sensitivity/specificity pair, architecture winner or clinical readiness. This is a feasibility outcome, not a technical model-fitting failure or evidence that all AI prediction is ineffective.

## 14. Outstanding questions for the review team

1. Confirm/document the scope broadening to general PICU and decide how to handle Kenet's 38 adults; obtain paediatric-only performance if needed.
2. Resolve the registered external-validation requirement through additional evidence or an explicit documented methodological decision; no waiver is presumed.
3. Verify all included-study facts against public full reports, especially Lu outcome/target interval, graphical operating points and +/- definition; keep private correspondence private.
4. Confirm Dallas patient overlap and evaluation independence, including whether comparator estimates are reused.
5. Obtain genuine AUROC SEs/CIs and their construction; do not use fold SD as sampling SE without justification.
6. Confirm Yu 2023's table model, threshold, fold, horizon and unit; reconcile its 40 positive units with cohort/fold descriptions without reconstruction assumptions.
7. Obtain patient-level or cluster-adjusted Kenet diagnostic estimates and prospective alarm-rate denominators; confirm model selection without choosing observed maxima.
8. Reconcile recruitment-date discrepancies, model-specific quality templates and random-forest specificity; resolve exact horizon selection before pooling.
9. Supply search strategy/screening counts and complete independent QUADAS-2/adapted GRADE assessments with consensus.

## 15. Reproducibility information

The command `make all` rebuilds curated-data analyses, CSV tables, figures, Markdown/HTML reports and the run manifest, then runs the full test suite and verifies output completeness. `make raw` re-ingests all three local originals and regenerates the public curated data. Python source separates ingestion, semantic cleaning, feasibility/independence checks, figures and reporting. Conditional R code has its own early eligibility gates and is not needed to reproduce the current no-pooling findings.

Input SHA-256 hashes, software versions, counts, configuration, analysis status, warnings, output hashes, actual commands, execution timestamps, test results and the available source Git revision are in `run_manifest.json`. Public-only reproduction cannot prove fidelity of withheld originals; original-source audit requires local source files. Re-running numerical tables/figures is deterministic; execution timestamps, test duration and source Git metadata naturally change. The manifest Git SHA identifies the source revision at run time, not a claim of containing its own future publication-commit hash.

## Descriptive figures

![AUROC estimates](../figures/auroc_descriptive.png)

![Sensitivity points](../figures/sensitivity_descriptive.png)

![Specificity points](../figures/specificity_descriptive.png)

![ROC-space scatter](../figures/sroc_descriptive.png)

![Comparability overview](../figures/heterogeneity_overview.png)

![Dataset flow](../figures/inclusion_flow.png)

See [full captions](figure_captions.md); all plots are descriptive and no pooled-estimate figure is implied.

## Methodological references

- [Takwoingi et al., performance of diagnostic accuracy meta-analysis with few studies/sparse data](https://pmc.ncbi.nlm.nih.gov/articles/PMC5564999/) supports caution about complex hierarchical fitting in small syntheses; it does not validate pooling the current clustered tables.
- [Cochrane DTA handbook, Chapter 10](https://methods.cochrane.org/sites/methods.cochrane.org.sdt/files/uploads/Chapter%2010%20-%20Version%201.0.pdf) describes bivariate/HSROC models and restrictions on heterogeneity exploration.
- [PROBAST+AI original tool publication](https://www.bmj.com/content/388/bmj-2024-082505) supports considering a prediction-model-specific assessment in addition to the registered tool.
- [metafor package author documentation](https://wviechtb.github.io/metafor/reference/rma.uni.html) and [mada package documentation](https://rdrr.io/cran/mada/man/reitsma.html) define the conditional estimators. Methods sources were checked online; included-study metrics remain based exclusively on supplied extraction.
'''
    write_md(out/'final_analysis_report.md',main)
