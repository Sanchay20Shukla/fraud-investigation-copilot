# Recorded results

[Back to the project overview](../README.md)

These files preserve measured outputs from the initial local build. They are included to make the project reviewable; they are not guarantees of performance on new data.

| File | Contents |
|---|---|
| [model_metrics.json](model_metrics.json) | Model version, features, chronological splits, validation threshold and holdout metrics |
| [retrieval_metrics.json](retrieval_metrics.json) | TF-IDF results for 50 authored evaluation cases |
| [semantic_retrieval_metrics.json](semantic_retrieval_metrics.json) | MiniLM results on the same cases |
| [sample_investigation.json](sample_investigation.json) | Full saved investigation with model and policy evidence |
| [verification.json](verification.json) | Recorded verification scope and untested integrations |
| [dashboard.png](dashboard.png) | Screenshot of the local investigator dashboard |

## Model evaluation

The model was trained and evaluated using the first 200,000 PaySim rows. Training covered steps 1–9; validation covered 10–11; test covered 12–13. No time step crosses split boundaries. The threshold of 0.95 was selected on validation data, not the test set.

The holdout contains 54,042 transactions and only 20 fraud labels. Precision was 0.9474, recall 0.9000, F1 0.9231, average precision 0.9087 and ROC-AUC 0.9969. The small positive sample limits the strength of conclusions. Probabilities were not calibrated.

## Retrieval evaluation

The evaluation includes 35 policy-source cases and 15 routing or unsupported-question cases. The lexical baseline achieved source recall@5 of 1.0000; MiniLM achieved 0.9286. The local default remains lexical for this small corpus.

The questions were authored for development and are not an independent held-out benchmark. These document-source metrics are not RAGAS faithfulness or answer-relevancy scores. Those answer-level measures have not been recorded.

## Reproduction

Follow the main README's PaySim setup, then run:

```bash
python -m pytest -q
python -m src.evaluation.rag_evaluation
```

Model training writes current metrics under the configured artifact directory. The evaluation command writes `reports/retrieval_metrics.json` for the active retrieval mode. Keep a separate copy when comparing modes so one experiment does not overwrite another.
