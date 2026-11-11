"""Semantic metric parsing with explicit uncertainty and analysis-unit provenance."""
import math
import re
from .ingest import missing_state

NUM = r'(?:\d+(?:\.\d+)?)'
MODEL_BY_ROW = {
3:'decision_tree',4:'random_forest',5:'xgboost',6:'logistic',7:'svm',
8:'knn_dtw',9:'svc_gak',10:'knn_unif',11:'logistic',12:'rf_gini',13:'xgboost',14:'lightgbm',
15:'tabnn',16:'tresnet',17:'gmlp',18:'pedca_ft',19:'glm',20:'rdn_boost',21:'logistic_reference',
22:'gnb',23:'logistic',24:'svm',25:'random_forest',26:'xgboost',27:'lightgbm',28:'soft_voting',29:'logistic'}


def proportion(value):
    state=missing_state(value)
    if state not in {'observed','observed_zero'}:
        return None
    s=str(value).strip()
    if not re.fullmatch(NUM+r'\s*%?',s):
        raise ValueError(f'Ambiguous proportion: {s}')
    x=float(s.replace('%','').strip())
    if '%' in s or x>1:
        x/=100
    if not 0<=x<=1:
        raise ValueError(f'Out-of-range proportion: {value}')
    return x


def count(value):
    if missing_state(value) not in {'observed','observed_zero'}:
        return None
    # Explicit source annotation allowed after integer, but no decimal or hidden counts.
    m=re.fullmatch(r'(\d+)\s*(?:\(from representative confusion matrix, Figure 2\))?',str(value).strip())
    if not m:
        raise ValueError(f'Ambiguous count: {value}')
    return int(m[1])


def rates(tp,fp,fn,tn):
    for x in (tp,fp,fn,tn):
        if x is None or not isinstance(x,int) or x<0:
            raise ValueError('Complete nonnegative integer 2x2 counts required')
    div=lambda a,b: a/b if b else None
    return {'sensitivity_recalculated':div(tp,tp+fn),'specificity_recalculated':div(tn,tn+fp),
            'ppv_recalculated':div(tp,tp+fp),'npv_recalculated':div(tn,tn+fn),
            'accuracy_recalculated':div(tp+tn,tp+fp+fn+tn),'positive_units':tp+fn,
            'negative_units':tn+fp,'total_units':tp+fp+fn+tn}


def uncertainty(estimate, low=None, high=None, variation=None, kind='not_reported', **extra):
    if not 0<=estimate<=1:
        raise ValueError('AUROC outside 0-1')
    se_raw=se_logit=None
    if kind=='95%_confidence_interval':
        if not (0<low<estimate<high<1):
            raise ValueError('Invalid confidence interval')
        # Endpoint normal approximation on logit scale; CI construction not supplied.
        logit=lambda x: math.log(x/(1-x))
        se_raw=(high-low)/(2*1.959963984540054)
        se_logit=(logit(high)-logit(low))/(2*1.959963984540054)
    return dict(auroc=estimate,ci_lower=low,ci_upper=high,reported_variation=variation,
                uncertainty_type=kind,se_raw_approx=se_raw,se_logit_approx=se_logit,**extra)


def parse_auroc(text):
    """Only recognized source grammars; do not tokenize arbitrary complex cells."""
    if missing_state(text) not in {'observed','observed_zero'}:
        return []
    s=str(text).strip()
    # Cross-horizon semi-colon grammar (applies to excluded Yu 2026 too).
    multi=re.fullmatch(rf'{NUM} \(\d+hr\)(?:; {NUM} \(\d+hr\))+',s)
    if multi:
        return [uncertainty(proportion(a),horizon=f'{h}h',evaluation='unspecified')
                for a,h in re.findall(rf'({NUM}) \((\d+)hr\)',s)]
    m=re.fullmatch(rf'({NUM})\s*±\s*({NUM})',s)
    if m:
        scale=100 if float(m[1])>1 else 1
        return [uncertainty(float(m[1])/scale,variation=float(m[2])/scale,
                            kind='unspecified_plus_minus',horizon='target_interval_unverified',evaluation='internal_cross_validation')]
    m=re.fullmatch(rf'({NUM}) \(training set\); ({NUM}) \(test set\)',s)
    if m:
        return [uncertainty(proportion(m[1]),horizon='warning_time_variable',evaluation='training'),
                uncertainty(proportion(m[2]),horizon='warning_time_variable',evaluation='internal_held_out_test')]
    m=re.fullmatch(rf'({NUM}) \[95% CI ({NUM}), ({NUM})\] at (\d+) hour prior to CA.*',s)
    if m:
        return [uncertainty(proportion(m[1]),proportion(m[2]),proportion(m[3]),kind='95%_confidence_interval',
                            horizon=f'{m[4]}h',evaluation='internal_cross_validation')]
    m=re.fullmatch(rf'({NUM}) \(auPRC .+\)',s)
    if m:
        return [uncertainty(proportion(m[1]),horizon='within_3h_window_label',evaluation='internal_held_out_test')]
    m=re.fullmatch(rf'({NUM}) at (\d+) hour before CA \(best/peak performance\);.*',s)
    if m:
        # Later approximate graphical ranges remain in original text, not invented rows.
        return [uncertainty(proportion(m[1]),horizon=f'{m[2]}h',evaluation='validation_unreported')]
    if re.fullmatch(NUM+r'\s*%?',s):
        return [uncertainty(proportion(s),horizon='not_reported',evaluation='unspecified')]
    if s.startswith('Reported graphically'):
        return []
    raise ValueError(f'Unsupported AUROC grammar; manual review needed: {s}')


def adjunct_metrics(text):
    result={}
    patterns={'auprc':rf'auPRC ({NUM})','accuracy_reported':rf'accuracy ({NUM})%',
              'ppv_reported':rf'PPV ({NUM})%','npv_reported':rf'NPV ({NUM})%'}
    for key, pattern in patterns.items():
        m=re.search(pattern,text,re.I)
        result[key]=float(m[1])/(1 if key=='auprc' else 100) if m else None
    return result


def parse_operating_point(text):
    if missing_state(text) not in {'observed','observed_zero'}:
        return []
    s=text.strip()
    if re.fullmatch(NUM+r'\s*%?',s):
        return [{'value':proportion(s),'evaluation':'source_reported','note':''}]
    if s.startswith('60.6% (test set;'):
        return [{'value':.606,'evaluation':'internal_held_out_test','note':'source also states unchanged for broader analysed dataset'}]
    if s=='74.1% (test set); 80.2% (entire dataset)':
        return [{'value':.741,'evaluation':'internal_held_out_test','note':''},
                {'value':.802,'evaluation':'entire_dataset','note':'dependent additional evaluation'}]
    multi=re.fullmatch(rf'{NUM} \(\d+hr\)(?:; {NUM} \(\d+hr\))+',s)
    if multi:
        return [{'value':proportion(a),'evaluation':f'{h}h','note':''} for a,h in re.findall(rf'({NUM}) \((\d+)hr\)',s)]
    raise ValueError(f'Ambiguous operating point: {s}')


def build(rows, contexts, config):
    cleaned=[];auroc=[];diagnostic=[];operating=[];flags=[];changes=[];audit=[];excluded=[]
    def flag(r,code,detail,metric='all',severity='warning'):
        flags.append({**{k:r[k] for k in ('study_id','model_id','source_row')},'code':code,
                      'metric':metric,'severity':severity,'detail':detail})
    for src in rows:
        sid=src['study_id']; n=src['source_row']; c=contexts.get(sid,{})
        mid=f'{sid}_{MODEL_BY_ROW[n]}'
        reason=''
        if src['record_type']!='populated_model':reason='Cross-reference only; no extracted result; links to populated Yu 2022 record 29' if src['record_type']=='cross_reference' else 'Blank extraction record'
        elif sid=='yu_2026':reason=config['exclusions']['yu_2026']
        elif sid=='yu_2023' and MODEL_BY_ROW[n]=='gnb':reason=config['exclusions']['yu_2023_gnb']
        keep=not reason
        base={**src,'model_id':mid,'model_name':MODEL_BY_ROW[n].replace('_',' '),'retained':keep,
              'exclusion_reason':reason,'cohort_id':c.get('cohort_id',''),
              'dependency_group':c.get('dependency_group',''),'analysis_unit':c.get('unit',''),
              'validation_type':src.get('internal_validation','') or 'not_reported',
              'prediction_horizon':c.get('horizon_group',''),'threshold':c.get('threshold','not_reported')}
        base['metric_source']=f'Extraction CSV logical record {n}, columns 28-34 (zero-based); original study DOI in record'
        a={k:base[k] for k in ['source_row','source_line_start','source_line_end','source_nonempty_cells','study_id','model_id','record_type','retained','exclusion_reason']}
        a.update({'nonempty_public_fields':sum(bool(v) for k,v in src.items() if isinstance(v,str)),
                  'auroc_text_present':missing_state(src.get('auroc_raw'))=='observed',
                  'has_complete_2x2':all(missing_state(src.get(x+'_raw')) in {'observed','observed_zero'} for x in ['tp','fp','fn','tn'])})
        audit.append(a)
        if not keep:
            excluded.append(a);continue
        estimates=parse_auroc(base['auroc_raw'])
        base['auroc_point_estimates']='; '.join(f'{v["auroc"]:.4f} ({v["evaluation"]}; {v["horizon"]})' for v in estimates)
        base.update(adjunct_metrics(base['auroc_raw']))
        if sid=='yu_2023':
            # Source comparator field explicitly gives these; do not derive silently.
            base['ppv_reported']=.36;base['npv_reported']=.97
        for metric in ['sensitivity','specificity']:
            values=parse_operating_point(base[metric+'_raw'])
            base[metric+'_reported']=values[0]['value'] if values else None
            base[metric+'_missing_state']=missing_state(base[metric+'_raw'])
            for idx,v in enumerate(values):
                op={k:base[k] for k in ['study_id','model_id','model_name','source_row','cohort_id','dependency_group','analysis_unit','prediction_horizon','validation_type','threshold','metric_source']}
                op.update(metric=metric,estimate=v['value'],evaluation=v['evaluation'],note=v['note'],ci_lower=None,ci_upper=None,
                          uncertainty_status='not_supplied_no_naive_binomial_ci',source_quality='graph_read' if sid=='lu_2025' else 'reported')
                operating.append(op)
            changes.append({'study_id':sid,'model_id':mid,'source_row':n,'field':metric,
                            'original':base[metric+'_raw'],'standardised':str([v['value'] for v in values]),
                            'action':'Semantic parse; percent/proportion conversion; retain every named evaluation'})
        for idx,e in enumerate(estimates,1):
            context={k:base[k] for k in ['study_id','model_id','model_name','source_row','cohort_id','dependency_group','analysis_unit','prediction_horizon','validation_type','metric_source']}
            context.update(e,estimate_id=f'{mid}_a{idx}',original_text=base['auroc_raw'],
                           sampling_variance_available=e['se_logit_approx'] is not None,
                           selection_status='candidate_index_model' if mid==c.get('representative_model') else 'descriptive_only',
                           pooled_eligible=False)
            if sid=='bose_2019' and e['evaluation']=='training':context['selection_status']='training_descriptive_only'
            auroc.append(context)
            changes.append({'study_id':sid,'model_id':mid,'source_row':n,'field':'auroc',
                            'original':base['auroc_raw'],'standardised':str(e['auroc']),
                            'action':f'Semantic parse; {e["evaluation"]}; horizon {e["horizon"]}; uncertainty {e["uncertainty_type"]}'})
            if e['uncertainty_type']=='unspecified_plus_minus':flag(base,'AUROC_VARIATION_UNSPECIFIED','+/- is not identified as SD, SE or CI; not used as variance','auroc')
            if e['se_logit_approx'] is not None:flag(base,'CI_TRANSFORM_APPROXIMATION','Logit SE from 95% CI endpoints assumes approximately normal logit AUROC; CI method not supplied','auroc','information')
        for x in ['tp','fp','fn','tn']:base[x]=count(base[x+'_raw'])
        if all(base[x] is not None for x in ['tp','fp','fn','tn']):
            d={k:base[k] for k in ['study_id','model_id','model_name','source_row','cohort_id','dependency_group','analysis_unit','prediction_horizon','validation_type','threshold','metric_source','tp','fp','fn','tn','sensitivity_reported','specificity_reported','ppv_reported','npv_reported']}
            d.update(rates(base['tp'],base['fp'],base['fn'],base['tn']))
            d.update(table_horizon='within_3h_window_label' if sid=='kenet_2023' else 'not_established',
                     table_model_attribution='source_extract' if sid=='kenet_2023' else 'assumed_by_extractor',
                     threshold_numeric=None,cluster_adjustment_available=False,
                     pairing_with_auroc_verified=sid=='kenet_2023',
                     model_threshold_unit_linkage_verified=sid=='kenet_2023',pooled_eligible=False,
                     ci_status='withheld_clustering_or_unit_linkage_unresolved')
            for metric in ['sensitivity','specificity','ppv','npv']:
                reported=d.get(metric+'_reported');calc=d[metric+'_recalculated']
                delta=calc-reported if reported is not None and calc is not None else None
                d[metric+'_difference']=delta
                raw_value=base.get(metric+'_raw','') if metric in {'sensitivity','specificity'} else ''
                rounding=0.005 if sid=='yu_2023' else config['rounding_tolerance']
                d[metric+'_rounding_tolerance']=rounding
                d[metric+'_within_tolerance']=abs(delta)<=rounding if delta is not None else None
                if delta is not None and abs(delta)>rounding:
                    flag(base,'REPORTED_RECALCULATED_DISCREPANCY',f'{metric}: reported {reported:.6f}; counts {calc:.6f}; difference {delta:.6f}; source unchanged',metric)
                if delta is not None:
                    changes.append({'study_id':sid,'model_id':mid,'source_row':n,'field':metric+'_recalculated',
                                    'original':str(reported),'standardised':str(calc),'action':'Derived from complete counts; reported value preserved separately'})
            diagnostic.append(d)
        flag(base,'MODEL_DEPENDENCE','All models within this source share an evaluation cohort; model entries are not independent studies')
        if sid in {'yu_2022','yu_2023'}:flag(base,'POTENTIAL_COHORT_OVERLAP','Same Dallas institution, 2010-2019 and 160 CA/711 controls; shared dependency group pending verification')
        if sid=='kenet_2023':
            flag(base,'WINDOW_EVENT_COUNT_RECONCILIATION','211 positive windows exceed 5 x 36 = 180 under an unstated one-event-per-test-CA-patient assumption; verify repeated arrests and window labeling; no error asserted')
            flag(base,'WINDOW_CLUSTERING','Six matrices count repeated five-minute windows; five test CA patients, 211 positive windows per matrix; no cluster adjustment')
            flag(base,'DUPLICATED_QUALITY_TEMPLATE','Source quality field repeats logistic-regression index description across all six models')
            flag(base,'MIXED_AGE_COHORT','38 patients aged 18+; no paediatric-only diagnostic table supplied')
            flag(base,'RECRUITMENT_DISCREPANCY','End date July vs August 2021 across model records')
        if sid=='yu_2023':flag(base,'TABLE_LINKAGE_UNVERIFIED','Representative fold; model attribution assumed; horizon, threshold and analysis unit not established','2x2')
        if sid=='yu_2022':flag(base,'DISTAL_AUROC_APPROXIMATE','Approximate 0.72-0.74 graphical range not extracted as exact hourly point estimates','auroc')
        if sid=='bose_2019':
            flag(base,'RECRUITMENT_DISCREPANCY','January vs November 2013 recruitment start recorded')
            flag(base,'PATIENT_TABLE_NOT_RECONSTRUCTABLE','60.6% test sensitivity incompatible with a simple integer table of five test CA patients; bootstrap/minute-score estimand needs verification','2x2')
        if sid=='lu_2025':
            flag(base,'PUBLIC_SOURCE_VERIFICATION_NEEDED','Correspondence content withheld; operational outcome definition and exact target interval require public-source verification')
            flag(base,'DUPLICATED_QUALITY_TEMPLATE','Source quality field repeats KNN-Dtw index description across all models; not model-specific evidence')
            if base['sensitivity_reported'] is not None:flag(base,'GRAPH_READ_OPERATING_POINT','Operating point read from bar chart according to extraction; values are approximate; no integer denominators or threshold verified','sensitivity_specificity')
        flag(base,'EXTERNAL_VALIDATION_NOT_DEMONSTRATED',f'External validation: {c["external_validation"]}; strict protocol eligibility not established')
        cleaned.append(base)
    return {'models':cleaned,'auroc':auroc,'diagnostic':diagnostic,'operating':operating,
            'flags':flags,'changes':changes,'audit':audit,'excluded':excluded}
