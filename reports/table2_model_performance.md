# Table 2. Retained model results

20 models are dependent within studies. NR means unavailable, not zero or poor performance. Source percentages remain separate from count-derived values in the full CSV. Original +/- quantities are not confidence intervals.

| study | model | row | AUROC (source text) | sensitivity (source) | specificity (source) | TP/FP/FN/TN | AUPRC |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lu_2025 | knn dtw | 8 | 55.27 ± 4.21 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | svc gak | 9 | 54.72 ± 3.80 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | knn unif | 10 | 57.41 ± 2.99 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | logistic | 11 | 62.92 ± 1.92 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | rf gini | 12 | 73.29 ± 2.47 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | xgboost | 13 | 72.35 ± 4.00 | 39.04% | 83.14% | NR/NR/NR/NR | NR |
| lu_2025 | lightgbm | 14 | 61.42 ± 11.06 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | tabnn | 15 | 62.16 ± 3.64 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | tresnet | 16 | 72.21 ± 7.22 | NR | NR | NR/NR/NR/NR | NR |
| lu_2025 | gmlp | 17 | 75.04 ± 3.52 | 8.22% | 97% | NR/NR/NR/NR | NR |
| lu_2025 | pedca ft | 18 | 73.99 ± 3.16 | 42.47% | 84.69% | NR/NR/NR/NR | NR |
| bose_2019 | glm | 19 | 0.91 (training set); 0.75 (test set) | 60.6% (test set; unchanged when evaluated on entire dataset excluding patients with <2h data) | 74.1% (test set); 80.2% (entire dataset) | NR/NR/NR/NR | NR |
| yu_2023 | rdn boost | 20 | 0.85 [95% CI 0.79, 0.90] at 1 hour prior to CA (peak performance); values also reported at 13, 9, and 5 hours prior (see Table 1 subgroup analyses; overall model AUROC lower at more distal time points, improving as time to arrest decreased) | 90% | 65% | 36/63/4/115 | NR |
| kenet_2023 | logistic | 23 | 0.867 (auPRC 0.529; accuracy 68.3%; PPV 16.3%; NPV 98.6%) | 87.20% | 66.90% | 184/944/27/1904 | 0.529 |
| kenet_2023 | svm | 24 | 0.955 (auPRC 0.614; accuracy 68.3%; PPV 17.6%; NPV 99.7%) | 97.60% | 66.10% | 206/965/5/1883 | 0.614 |
| kenet_2023 | random forest | 25 | 0.936 (auPRC 0.597; accuracy 78.6%; PPV 23.4%; NPV 99.3%) | 92.40% | 77.80% | 195/639/16/2209 | 0.597 |
| kenet_2023 | xgboost | 26 | 0.971 (auPRC 0.797 — best of all six models on both metrics; accuracy 71.7%; PPV 19.5%; NPV 99.9%) | 99.50% | 69.60% | 210/866/1/1982 | 0.797 |
| kenet_2023 | lightgbm | 27 | 0.950 (auPRC 0.727; accuracy 72.0%; PPV 19.4%; NPV 99.7%) | 97.20% | 70.20% | 205/850/6/1998 | 0.727 |
| kenet_2023 | soft voting | 28 | 0.957 (auPRC 0.733; accuracy 88.1% — highest of all six models; PPV 35.8% — highest of all six models; NPV 99.2%) | 91.00% | 87.90% | 192/345/19/2503 | 0.733 |
| yu_2022 | logistic | 29 | 0.83 at 1 hour before CA (best/peak performance); AUROC increased over time as it approached the arrest, ranging from approximately 0.72–0.74 at 15–10 hours prior, rising to 0.83 at 1 hour prior (see Figure 1 for full hourly trend) | NR | NR | NR/NR/NR/NR | NR |
