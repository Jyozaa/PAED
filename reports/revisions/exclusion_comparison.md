# Lu model exclusion: before-and-after comparison

This is an intentional eligibility revision from the saved 20-model analysis on `exploratory-pooling`. Three whole Lu entries are excluded because their sensitivity/specificity was graphically extracted. This does not assert that their AUROCs were graphical. No additional model is excluded solely for missing operating points. Original source files and curated source records are unchanged; historical baselines are independently validated against Git.

| measure | previous | revised |
| --- | --- | --- |
| Retained study reports | 5 | 5 |
| Retained models | 20 | 17 |
| Retained Lu models | 11 | 8 |
| Lu reported AUROC range | 0.5472-0.7504 | 0.5472-0.7329 |
| Core AUROC scenarios | 18 | 18 |
| Core conditional pooled AUROC range | 0.7689-0.8451 | 0.7241-0.8305 |
| Additional retained-Lu AUROC scenarios | 0 | 126 |
| All revised Lu-choice conditional pooled AUROC range | Not previously assessed | 0.7120-0.8441 |
| Diagnostic scenarios | 96 | 96 |
| Conditional diagnostic sensitivity (%) | 87.2956-98.2449 | 87.2956-98.2449 |
| Conditional diagnostic specificity (%) | 65.5968-87.4968 | 65.5968-87.4968 |


Core results use Lu logistic regression instead of the excluded index. Additional scenarios systematically use every other retained Lu algorithm, one at a time. Scenario ranges are not confidence intervals. All paired core estimates/conditional intervals/heterogeneity and their changes are in `results/exploratory/core_before_after.csv`.

All 96 diagnostic scenarios were recalculated. Numerical identity across every original numeric result column: **True**. Maximum absolute numerical difference: **0.0**. Inputs remain one Yu table and one Kenet table per scenario, with identical counts and assumed covariance. No Lu model contributes to those calculations.

| path | byte_identical | previous_sha256 | revised_sha256 |
| --- | --- | --- | --- |
| results/diagnostic_2x2.csv | True | c2b2d48d918ef2fe63a42326a92652a2f585e7430604c6c85fc9e5a6f877cfaf | c2b2d48d918ef2fe63a42326a92652a2f585e7430604c6c85fc9e5a6f877cfaf |
| results/exploratory/diagnostic_scenario_results.csv | True | 23fdcdfdc280227fdb37e22b42792d680dc8c4a477b8e629eb384cd07038a3bd | 23fdcdfdc280227fdb37e22b42792d680dc8c4a477b8e629eb384cd07038a3bd |
| results/exploratory/diagnostic_scenario_inputs.csv | True | 422d125260afb9e0cf4def5a6a4ba9f29c2af653c3efdf4e8ee08aaa71be88c7 | 422d125260afb9e0cf4def5a6a4ba9f29c2af653c3efdf4e8ee08aaa71be88c7 |
| figures/exploratory/diagnostic_joint_summaries.png | True | 39dedfd0ec5705801d62f57d356dcfbd7198909e6412f7e7bf93fd29fa9f008f | 39dedfd0ec5705801d62f57d356dcfbd7198909e6412f7e7bf93fd29fa9f008f |
| figures/exploratory/diagnostic_joint_summaries.svg | True | 22ecba3398bea7d9cd2cf12a228e92ce473f7ff0953ac3488c750985fdc8226c | 22ecba3398bea7d9cd2cf12a228e92ce473f7ff0953ac3488c750985fdc8226c |
| figures/exploratory/diagnostic_sensitivity.png | True | 8bf05cc083dc4b8d78d8d84cd49d11d8533ccfc9656d15acab7fdb5ce958e04f | 8bf05cc083dc4b8d78d8d84cd49d11d8533ccfc9656d15acab7fdb5ce958e04f |
| figures/exploratory/diagnostic_sensitivity.svg | True | aa35d3a012a7b32146037fa30cea3d2cec9cb7c8cc3cb167d9ff9c58a68d131e | aa35d3a012a7b32146037fa30cea3d2cec9cb7c8cc3cb167d9ff9c58a68d131e |


Numerical equality does not validate the diagnostic assumptions. Kenet repeated windows/adults, unresolved Yu units/linkage, sparse cells, missing external validation, possible Dallas overlap and protocol differences remain. The old branch remains the historical analysis, not a current retained-model output.
