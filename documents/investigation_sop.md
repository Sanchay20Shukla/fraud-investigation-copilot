# Fraud Investigation SOP
Synthetic portfolio procedure, version 1.0.

## 2.1 Investigation evidence
Investigate a transaction by collecting the transaction record, prior origin account history, model version, model probability, SHAP contributions and relevant policy passages. Preserve transaction IDs, document sections and content hashes in the report. Recommendations require analyst judgment.

## 2.2 Evidence limitations
Do not infer an account holder's identity, geography, device, sanctions status or intent from PaySim. The dataset lacks these fields. No previous transactions in the loaded sample means history is unavailable, not that an account is new. PaySim amounts have unspecified simulation currency units.
