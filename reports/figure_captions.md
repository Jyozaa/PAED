# Figure captions

All descriptive figures are PNG and SVG. No confirmatory pooled forest or fitted HSROC is generated.

- **auroc_descriptive**: 18 numerical AUROC evaluations across 17 models/5 reports, including separate Bose training/test results. Only Yu 2023 has a supplied genuine CI. Lu has 8 retained models; XGBoost, gMLP and PEDCA-FT are excluded in full. Unspecified +/- quantities are not error bars. Units/horizons/validation differ and models share cohorts.
- **sensitivity_descriptive**: eight retained model/evaluation points from Bose, Yu 2023 and Kenet; no Lu graph-derived points. Complete tables are recalculated. No patient-level/window-naive CIs are invented.
- **specificity_descriptive**: nine evaluations including separate Bose entire-dataset specificity. Count-derived random-forest specificity remains distinct from reported 77.8%.
- **sroc_descriptive**: eight model-specific operating pairs in ROC space, with no fitted curve, summary operating point or confidence region. Six Kenet points share windows; Yu linkage is unverified. Lu/Yu 2022 contribute no eligible operating points.
- **heterogeneity_overview**: all five reports and ten pairs, retaining possible Dallas reuse and current pooling limitations.
- **inclusion_flow**: extraction-only audit of 27 post-header records, 26 populated models/six original reports, one cross-reference, nine model exclusions and 17 retained models/five reports. Not a PRISMA search/screening flow.

Exploratory figures are separately captioned in their scenario reports and carry explicit assumption warnings. The short LaTeX report includes the revised AUROC figure only; no sensitivity/specificity graph is included in that document.
