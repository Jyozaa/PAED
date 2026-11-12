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
    df=pd.DataFrame(rows)[columns].astype(object).fillna('Not reported')
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
        row['other_performance_notes']='No eligible retained sensitivity/specificity results after whole-model graphical-operating-point exclusions' if m['study_id']=='lu_2025' else ''
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
- `source_nonempty_cells` counts all nonempty cells in each original record; `nonempty_public_fields` counts a different, sanitized export and must not be interpreted as raw extraction completeness.
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
    """Current reports derive counts and ranges from the active eligibility set."""
    out=project/'reports';models=data['models'];A=data['auroc'];D=data['diagnostic'];audit=data['audit']
    nontraining=[r for r in A if r['evaluation']!='training'];lu=[r for r in models if r['study_id']=='lu_2025']
    lua=[r for r in A if r['study_id']=='lu_2025'];plus=sum(r['uncertainty_type']=='unspecified_plus_minus' for r in A)
    modelcounts={sid:sum(r['study_id']==sid for r in models) for sid in dict.fromkeys(r['study_id'] for r in models)}
    span=lambda rs:f'{min(r["auroc"] for r in rs):.4f}-{max(r["auroc"] for r in rs):.4f}'
    yu=next(r for r in A if r['study_id']=='yu_2023');excluded=[r for r in data['excluded'] if r['record_type']=='populated_model']
    newexcluded=[r for r in excluded if r['study_id']=='lu_2025']
    reason=newexcluded[0]['exclusion_reason']
    short=[]
    for r in t2:
        short.append({'study':r['study_id'],'model':r['model_name'],'source row':r['source_row'],
            'AUROC (source text)':r['auroc_raw'],'sensitivity (source)':r['sensitivity_raw'],'specificity (source)':r['specificity_raw'],
            'TP/FP/FN/TN':'/'.join(str(r[k]) if r[k] is not None else 'NR' for k in ['tp','fp','fn','tn']),
            'AUPRC':r['auprc'] if r['auprc'] is not None else 'NR'})
    table1=md_table(t1,['study_id','retained_models','sample_size_and_ca','icu_setting','model_architectures','training_validation','prediction_horizon','reporting_limitations'])
    table2=md_table(short,list(short[0]))
    write_md(out/'table1_study_characteristics.md',f'# Study characteristics\n\nRevised dataset: {len(t1)} study reports and {len(models)} models.\n\n'+table1)
    write_md(out/'table2_model_performance.md',f'# Retained model performance\n\nRevised dataset: {len(models)} retained entries, including {len(lu)} Lu models. NR is unavailable, not zero. Original source text remains distinct from recalculated rates. The Lu XGBoost, gMLP and PEDCA-FT entries are wholly excluded, including their AUROCs, because their operating points were graphically extracted. This does not imply that their AUROCs were graph-derived.\n\n'+table2)
    counts_text=f'''There are {len(audit)} post-header records, {sum(r['record_type']=='populated_model' for r in audit)} populated original model entries and {len({r['study_id'] for r in audit if r['record_type']=='populated_model'})} original reports. One record is a cross-reference, with no extracted results, rather than a blank row. After {len(excluded)} whole-model exclusions, **{len(t1)} reports and {len(models)} models remain**, including **{len(lu)} Lu models**. There are **{len(A)} numerical AUROC evaluations**, because Bose contributes separate training and test results, and {plus} unspecified Lu +/- quantities. Only one labelled AUROC CI is supplied. Seven complete candidate diagnostic tables still come from two sources.'''
    exclusion_text=f'''Previous exclusions remain: five Yu 2026 models for composite adverse events and Yu 2023 Gaussian Naive Bayes for inadequate graphical numerical results. The new team decision excludes entire Lu 2025 XGBoost, gMLP and PEDCA-FT entries, including their AUROCs: **{reason}** This is a model-level eligibility decision based on the sensitivity/specificity extraction, not a claim that those AUROCs were necessarily graph-read. Missing sensitivity/specificity alone does not exclude the other Lu models.'''
    source_text='''Only the original extraction CSV, List of Variables (3 pages), PROSPERO snapshot (7 pages) and their existing derivatives are used. No new papers, external data or correspondence were obtained. Original-file hashes are unchanged. Source row means 1-based logical CSV record including both header records; physical multiline spans are separate. Original/curated sources remain immutable, with raw PDFs/CSV and private narratives excluded from Git.'''
    write_md(out/'data_audit.md',f'''# Revised data audit

{source_text}

## Recalculated counts

{counts_text}

{exclusion_text}

## Every source decision

{md_table(audit,['source_row','study_id','model_id','record_type','retained','exclusion_reason'])}

## Retained study/model counts

{md_table([{'study':k,'retained models':v} for k,v in modelcounts.items()],['study','retained models'])}

The original 42 source columns and two header records are preserved in the schema metadata. All 1,134 data-cell missingness states remain audited. Source records 13, 17 and 18 are excluded from retained tables, figures, ranges and pooled inputs. Their original text remains in source provenance and excluded inventory rows only. Lu retained AUROC range is **{span(lua)}**. No arithmetic model average is presented as a study estimate. Lu and Yu 2022 now have no eligible sensitivity/specificity observations; missing is never replaced by zero.

Seven diagnostic tables still have unchanged counts. The Kenet random-forest specificity discrepancy remains: reported 77.8%, counts 77.5632%. Yu integer percentages agree within their rounding tolerance. Other flags preserve possible Dallas reuse, missing external validation, clustered windows, mixed-age Kenet, inconsistent recruitment dates and unresolved Yu 2023 table linkage.
''')
    strict=[{'study':sid,'setting':c['setting_class'],'external validation':c['external_validation'],'strict status':c['strict_status'],'reason':c['strict_reason']} for sid,c in contexts.items()]
    write_md(out/'protocol_deviations.md',f'''# Protocol discrepancies and revised working eligibility

Registered reference: supplied PROSPERO CRD420251241478 version 3.0, published 1 August 2026, printed 4 November 2026. No register amendment or external-validation waiver was performed or inferred.

The population wording on page 2 specifies under-18 cardiac-ICU inpatients and excludes models without external validation or accuracy metrics. Page 7 records narrowing to cardiac intensive care. Page 5 nevertheless lists NICU/PICU subgroups; this ambiguity does not demonstrate a waiver of the restrictive wording. The team accepts general PICU for this working analysis, retaining Kenet. Its 38 adults remain an additional unresolved discrepancy with paediatric-only eligibility.

{exclusion_text}

{md_table(strict,list(strict[0]))}

The revised working cohort contains {len(t1)} reports/{len(models)} models. Restricting setting alone leaves {statuses['strict_protocol']['with_setting_requirement_only_studies']} CICU reports/{statuses['strict_protocol']['with_setting_requirement_only_models']} models. No retained report demonstrates every strict criterion, particularly external validation; NR is not proof that validation never occurred. Lu and Bose explicitly lack external validation. The confirmatory strict subset remains zero demonstrated eligible reports/models.

The extraction framework permits multiple models/thresholds but not independent treatment of repeated results. AUROC across thresholds differs from an area under a cross-study SROC; a single operating point does not recover an AUROC. Protocol specificity wording is imprecise: specificity concerns non-arrest units. The full-protocol citation is the PRISMA statement rather than an accessible study-specific protocol. Search/screening totals and independent reviewer decisions are absent. QUADAS-2 and adapted GRADE remain registered; no replacement or completed dual review is claimed.

Before manuscript publication, the team must resolve scope, adult inclusion, external validation, overlapping Dallas patients, model/horizon selection, source uncertainty and Yu table linkage, and complete independent risk-of-bias/certainty review. The present revision is transparent team-directed eligibility, not a protocol amendment. Historical 20-model results remain on the parent branch and are explicitly separated in the before/after report.
''')
    common_a=f'''**Confirmatory status: not statistically defensible from the supplied evidence.** {len(t1)} reports/{len(models)} models supply {len(A)} AUROC evaluations, but just one cohort has genuine numerical uncertainty. The {plus} retained Lu +/- values are unspecified, not SEs. No confirmatory pooled AUROC, CI, p-value, tau-squared, I-squared or prediction interval is produced.'''
    write_md(out/'auroc_feasibility.md',f'''# AUROC synthesis: revised evidence feasibility

{common_a}

The descriptive nontraining/other reported range is {span(nontraining)}; Lu's {len(lua)} retained values span **{span(lua)}**. Bose training 0.91 and held-out test 0.75 remain separate. Yu 2023 is 0.85 (95% CI 0.79-0.90); approximate SE is {yu['se_raw_approx']:.8f} on AUROC scale and {yu['se_logit_approx']:.8f} on logit scale. The CI construction is unverified.

{md_table(selection,['study_id','representative_model','selection_reason','genuine_variance_estimates','reason'])}

Lu logistic regression is now the analyst-selected conventional representative after the whole-model exclusions. Its AUROC is 0.6292, with unspecified +/- 0.0192. This is not the original paper's verified primary-model designation. No highest-AUROC selection rule is used. Yu 2022/2023 potentially share the same Dallas cohort; horizons, units, definitions and validation differ. Bootstrap narrative does not provide missing numerical AUROC uncertainty. Conventional inverse-variance pooling remains unsupported.

The separately labelled exploratory scenario layer adds hypothetical SEs and fits Paule-Mandel random effects with modified Hartung-Knapp conditional intervals. Those calculations do not change this confirmatory conclusion. They use one model per source group and never combine the Dallas reports. See [revised exploratory report](exploratory/consolidated_exploratory_report.md).
''')
    diag_table=md_table(D,['study_id','model_name','tp','fp','fn','tn','sensitivity_recalculated','specificity_recalculated','ppv_recalculated','npv_recalculated','analysis_unit'])
    common_d='''**Confirmatory status: not statistically defensible from the supplied evidence.** Seven tables represent six Kenet algorithms on shared windows and one Yu 2023 representative fold. Zero confirmed independent patient-level tables contribute to a confirmatory pooled fit. No unrestricted bivariate covariance or HSROC curve is estimated.'''
    write_md(out/'diagnostic_feasibility.md',f'''# Diagnostic synthesis: revised evidence feasibility

{common_d}

{diag_table}

Every Kenet table totals 3,059 five-minute windows (211 positive, 2,848 negative) from a test cohort recorded as 229 patients with five CA patients. Window totals are not independent patient/arrest counts. No patient-level confusion matrix, intrapatient correlation or adequate clustering adjustment is supplied. Conditional reconciliation of 211 positive windows with a 3-hour/five-minute rule and five patients requires event multiplicity/labeling information; no one-arrest-per-patient assumption is asserted.

Yu 2023 has 36 TP, 63 FP, 4 FN and 115 TN, total 218 unresolved units. Rates recalculate to 90% sensitivity, 64.6067% specificity, 36.3636% PPV and 96.6387% NPV. Its model attribution was assumed by the extractor, and fold, threshold, exact horizon and unit remain unresolved. It is not silently linked to its 1-hour AUROC. No integer tables are reconstructed from percentages or cohort totals.

Lu has no eligible retained operating points after the three whole-model exclusions. Yu 2022 also has no model-level sensitivity/specificity. Bose's reported operating percentages do not identify an independent patient table. No naive window binomial intervals are reported in this descriptive layer.

The separate 96-scenario joint normal-logit GLS calculation fixes covariance assumptions rather than learning a full covariance from two sources. Counts and those assumptions are unchanged and the revision pipeline compares all scenarios against their saved previous values. It does not claim a fitted unrestricted bivariate/HSROC model or verified patient-level accuracy.
''')
    write_md(out/'heterogeneity.md',f'''# Heterogeneity and eligibility sensitivity

Five retained reports form four conservative potential dependency groups. All 10 report pairs remain descriptive comparisons, not approved confirmatory pooling pairs. Absence of identified overlap elsewhere is not proof of independence.

- Lead time differs: first-24h input for Lu with exact outcome interval unverified; variable warning time for Bose (mean 17h, SD 7.5h) after a selected 2h input window; extracted 1h peaks for Yu; 3h positive-window labeling for Kenet.
- Units differ: admission with patient-grouped CV, minute risk scores, hourly observations and repeated five-minute windows.
- Population differs: four cardiac-ICU reports and one general PICU; infants only in Bose, broader ages elsewhere; Kenet includes 38 adults.
- Validation is internal or unreported. No retained report demonstrates external validation. Different case/control reference times and discharge-linked negative windows affect transportability.
- Dallas reports have matching institution, period and 160 CA/711 controls, so they are never independent contributors in the same exploratory scenario.
- Retained Lu architectures are now two kernel/neighbour time-series methods, five static-EHR baselines and one numerical time-series network. All eight are retained despite missing operating points. Their AUROCs range {span(lua)}.

CICU-only eligibility leaves {statuses['strict_protocol']['with_setting_requirement_only_models']} models; the strict demonstrated-eligibility subset remains empty. No confirmatory meta-regression, subgroup model, Egger test, leave-one-out analysis, I-squared or prediction interval is supported. The exploratory layer separately quantifies choices of all eight Lu representatives and assumed uncertainty, without interpreting scenario stability as clinical validation.
''')
    write_md(out/'risk_of_bias.md',f'''# Risk-of-bias evidence worksheet

Registered tool: QUADAS-2. The worksheet retains four domains for each of five reports, with applicability prompts for the first three domains. No formal low/high rating is automatically assigned. Independent reviewer decisions and consensus remain pending. The current data include {len(models)} models, including {len(lu)} Lu models; the excluded operating-point entries are not active evidence.

Concerns include retrospective single-centre selection, selected case/control spectra, differential timing, data-dependent features/thresholds, internal or unreported validation, repeated observations, possible normalization leakage and sparse events. Kenet excludes 1,019/2,164 patients including 57 CA, includes adults, and reports clustered windows. Lu's quality text repeats a baseline description across architectures; model-specific conduct cannot be inferred. Public operational definitions and missing-data handling remain uncertain. Row/column provenance accompanies evidence; no private narrative is copied.

PROBAST+AI remains a methodological consideration already documented in the earlier analysis, not a replacement for registered QUADAS-2. No new external tool evidence was retrieved. No independent dual-reviewer assessment is claimed.
''')
    write_md(out/'certainty_of_evidence.md','''# Adapted GRADE preparation

No definitive certainty grade is assigned. Formal risk-of-bias consensus is incomplete, no common validated threshold is identified, and the supplied evidence does not support confirmatory pooling. High AUROC and hypothetical scenario precision do not confer certainty.

| Domain | Current evidence | Outstanding assessment |
| --- | --- | --- |
| Bias | Retrospective selection, missing-data exclusions and unclear validation | Independent QUADAS-2 decisions |
| Inconsistency | Different horizons, units, populations, outcomes and algorithms | Define comparable estimands |
| Indirectness | General PICU, adult participants, selected controls/windows | Resolve target setting, age and protocol |
| Imprecision | One genuine AUROC CI; sparse CA patients; unknown clustering | Genuine uncertainty and patient/cluster-aware results |
| Reporting bias | Search/screening history and full reports unavailable | Review-team assessment without unsupported funnel tests |
| Clinical usefulness | No demonstrated prospective benefit, calibration or alarm rate | No deployment or safety inference from present calculations |

The revised exclusions reduce retained models to 17 without adding evidence. Exploratory assumed-variance and fixed-covariance calculations do not fill missing study information or establish external validity.
''')
    captions=f'''# Figure captions

All descriptive figures are PNG and SVG. No confirmatory pooled forest or fitted HSROC is generated.

- **auroc_descriptive**: {len(A)} numerical AUROC evaluations across {len(models)} models/{len(t1)} reports, including separate Bose training/test results. Only Yu 2023 has a supplied genuine CI. Lu has {len(lua)} retained models; XGBoost, gMLP and PEDCA-FT are excluded in full. Unspecified +/- quantities are not error bars. Units/horizons/validation differ and models share cohorts.
- **sensitivity_descriptive**: eight retained model/evaluation points from Bose, Yu 2023 and Kenet; no Lu graph-derived points. Complete tables are recalculated. No patient-level/window-naive CIs are invented.
- **specificity_descriptive**: nine evaluations including separate Bose entire-dataset specificity. Count-derived random-forest specificity remains distinct from reported 77.8%.
- **sroc_descriptive**: eight model-specific operating pairs in ROC space, with no fitted curve, summary operating point or confidence region. Six Kenet points share windows; Yu linkage is unverified. Lu/Yu 2022 contribute no eligible operating points.
- **heterogeneity_overview**: all five reports and ten pairs, retaining possible Dallas reuse and current pooling limitations.
- **inclusion_flow**: extraction-only audit of 27 post-header records, 26 populated models/six original reports, one cross-reference, nine model exclusions and {len(models)} retained models/five reports. Not a PRISMA search/screening flow.

Exploratory figures are separately captioned in their scenario reports and carry explicit assumption warnings. The short LaTeX report includes the revised AUROC figure only; no sensitivity/specificity graph is included in that document.
'''
    write_md(out/'figure_captions.md',captions)
    write_md(out/'plain_english_summary.md',f'''# Revised plain-English summary

The revised analysis retains **{len(t1)} reports and {len(models)} models**, including **{len(lu)} Lu models**. Three whole Lu entries were excluded by team decision because their sensitivity/specificity values were extracted from a graph. Their AUROCs were excluded with the entries; this does not imply the AUROCs themselves were graphical.

Retained reported AUROCs span {span(nontraining)}, and Lu's retained range is **{span(lua)}**. AUROC describes ranking, not the percentage of arrests detected. Lu and Yu 2022 have no eligible sensitivity/specificity results; missing does not mean zero or poor performance.

Only Yu 2023 has a genuine numerical AUROC confidence interval. Seven complete diagnostic tables still come from two study sources, including six Kenet models on shared repeated windows. Five test patients had CA in Kenet, not 211 independent arrests. False-positive windows cannot be converted to separate alarms or alarms per patient-day. Yu's representative-fold units and linkage remain unresolved.

Confirmatory pooling remains unsupported. The separate exploratory layer replaces the excluded Lu index model with conventional logistic regression (AUROC 0.6292), reruns 18 core scenarios, and examines all seven other retained Lu models. Its intervals depend on hypothetical uncertainty. The 96 diagnostic scenarios are rerun and explicitly compared with the previous analysis because their input tables and assumptions are unchanged.

Potential Dallas cohort reuse, Kenet clustering/adults, different horizons/thresholds, lack of demonstrated external validation and PROSPERO discrepancies remain. No prospective clinical benefit, safety or deployment conclusion follows from these retrospective or assumption-dependent numbers. See the revised exploratory and before/after reports for every numerical scenario.
''')
    sections=[('Research question and objectives','How accurately can predictive algorithms identify impending paediatric cardiac arrest? Both confirmatory feasibility and separately labelled exploratory calculations are retained. AUROC, threshold-specific sensitivity/specificity and PPV concern different estimands and units.'),
      ('Data sources and study eligibility',source_text+'\n\n'+counts_text),
      ('Agreed exclusions and protocol discrepancies',exclusion_text+'\n\nGeneral PICU remains team-agreed; Kenet includes 38 adults. No external-validation waiver or PROSPERO amendment is presumed. Strict demonstrated eligibility remains empty.'),
      ('Data cleaning and validation','Two headers and multiline source provenance are preserved. Percentages are normalized without replacing missing values by zero. All exclusions occur before numerical metric parsing for retained analysis. Original uncertainty text remains distinct from CI/SE. Complete diagnostic tables are recalculated, and the random-forest specificity discrepancy is retained. Original source hashes are unchanged.'),
      ('Characteristics of included studies',f'All five reports are retrospective single-centre US studies. Counts by report are {modelcounts}.\n\n'+table1),
      ('Descriptive predictive performance',f'Nontraining/other reported AUROC span: **{span(nontraining)}**. Lu retained span: **{span(lua)}**. Bose held-out test 0.75 versus training 0.91; Yu 2023 0.85 (95% CI 0.79-0.90); Yu 2022 peak 0.83; Kenet 0.867-0.971. These are dependent descriptive results, not study averages or an architecture ranking. Lu and Yu 2022 have no eligible operating points. The model table preserves every retained result.\n\n'+table2),
      ('AUROC meta-analysis: methods, feasibility, results',common_a+'\n\nThe separate exploratory report recomputes 18 core scenarios with Lu logistic regression and all seven retained alternative representatives. No original PEDCA-FT pooled value is reused as a revised result. The statistical estimator remains Paule-Mandel with modified Hartung-Knapp intervals; only its representative inputs change.'),
      ('Sensitivity/specificity meta-analysis: methods, feasibility, results',common_d+'\n\nThe 96 constrained joint GLS scenarios are rerun with unchanged count tables and covariance assumptions and numerically compared with the saved prior run. These conditional summaries are not an unrestricted bivariate/HSROC fit.'),
      ('Heterogeneity and sensitivity analyses','Different forecast times, definitions, units, sampling and internal validation persist. Yu 2022/2023 are grouped conservatively for possible overlap. Eight Lu representatives are analysed separately, never as independent cohorts in a single pooled scenario. Conditional scenario spread does not establish clinical validity.'),
      ('Risk of bias and certainty','QUADAS-2 evidence and adapted GRADE preparation remain incomplete reviewer worksheets; no definitive software-assigned ratings or dual-reviewer completion are claimed.'),
      ('Clinical interpretation','High AUROC does not establish sensitivity at a chosen threshold. Window-level missed predictions and false positives are not missed children or distinct clinical alarms. Calibration, prospective benefits, alert burden and deployment safety cannot be inferred.'),
      ('Limitations','One genuine AUROC CI, eight unspecified Lu variability quantities, repeated Kenet windows, sparse arrest patients, mixed age, selected controls, missing external validation, possible Dallas reuse and unresolved Yu linkage remain. Sources cannot be independently checked against full papers in this task. Hypothetical uncertainty/covariance does not resolve these gaps.'),
      ('Evidence-based conclusion',f'The revised evidence-supported synthesis contains {len(t1)} reports/{len(models)} models. Confirmatory pooling remains not statistically defensible. Separate conditional scenarios quantify the implications of explicit assumptions and revised model selection; they do not establish clinical accuracy.'),
      ('Outstanding questions for the review team','Resolve scope/adult inclusion, external-validation eligibility, Dallas overlap, prediction horizons, true source uncertainty, table linkage and bias/certainty judgements before manuscript publication. No additional data request or external evidence retrieval was made during this revision.'),
      ('Reproducibility information','Run `make revised` for the full descriptive, exploratory, comparison and LaTeX/PDF workflow with tests. Versioned historical/current baseline records preserve provenance; previous outputs remain on the parent Git branch. See the root, exploratory and revision manifests for commands, source hashes, versions, fit attempts and tests. The PDF requires Tectonic; no sensitivity/specificity graph is included in that short report.')]
    text='# Revised paediatric cardiac arrest analysis\n\nEligibility revision: 12 November 2026. Exploratory working scope, not fully protocol-concordant. This report analyses the supplied extraction rather than claiming new systematic searching or independent full-text verification.\n\n'
    text+='\n\n'.join(f'## {i}. {title}\n\n{body}' for i,(title,body) in enumerate(sections,1))
    text+='\n\n## Descriptive figures\n\n'+'\n\n'.join(f'![{name.replace("_"," ")}](../figures/{name}.png)' for name in ['auroc_descriptive','sensitivity_descriptive','specificity_descriptive','sroc_descriptive','heterogeneity_overview','inclusion_flow'])
    text+='\n\nSee [captions](figure_captions.md), [exploratory results](exploratory/consolidated_exploratory_report.md), and [before/after comparison](revisions/exclusion_comparison.md).'
    write_md(out/'final_analysis_report.md',text)
