# Model Governance and Escalation Procedure
Synthetic portfolio policy, version 1.0.

## 7.1 Model explanations
SHAP values describe contributions to the model output in log-odds. Positive SHAP values increase estimated risk; negative values decrease estimated risk. They are not percentage-point contributions or causal explanations. Uncalibrated fraud probabilities are model estimates, not empirical certainty.

## 7.2 Evaluation and escalation evidence
Report precision, recall, F1, PR-AUC and ROC-AUC on a later-time holdout. Select decision thresholds on validation data only. Keep fraud labels out of investigator tools. Escalation reports must retain model version, policy source, policy section and transaction evidence for audit.
