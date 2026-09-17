# Data guide

[Back to the project overview](../README.md)

## Two starting points

**Generated demonstration:** `python -m scripts.bootstrap --demo` creates educational fixtures. The labels follow simple synthetic rules, so resulting metrics should not be presented as a realistic fraud benchmark.

**PaySim experiment:** obtain a PaySim CSV under its applicable distribution terms and place it at `data/raw/paysim.csv`. The repository does not redistribute the dataset.

```bash
python -m scripts.bootstrap --paysim data/raw/paysim.csv --limit 200000
```

The recorded experiment uses the first 200,000 rows of the supplied PaySim source. `--limit 0` imports the whole file, but training currently materializes the imported data in memory.

## Required source columns

```text
step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,
nameDest,oldbalanceDest,newbalanceDest,isFraud
```

The standard optional `isFlaggedFraud` field is not used as a model feature. Accepted transaction types are TRANSFER, CASH_OUT, CASH_IN, PAYMENT and DEBIT. Rows must be ordered by ascending step. Ingestion validates required values and rolls back the entire import if validation fails.

## Identifiers and storage

- `TXN_0000000` identifies source row zero; IDs preserve source-row position.
- `transactions` contains analyst-visible records.
- `training_labels` contains labels used only for offline model training and evaluation.
- `data/processed/dataset_manifest.json` records source provenance and the normalized-data digest.
- `data/processed/copilot.db` is the default local SQLite database.

Raw rows, local databases and generated models are Git-ignored. Reports in `reports/` are recorded experimental outputs; rerunning locally does not automatically replace every published report.

## Changing datasets

Bootstrap retains an already populated database. To start a separate experiment, set `DATABASE_URL` to a new SQLite database and `ARTIFACTS_DIR` to a separate model directory in `.env`, then bootstrap again. Do not mix models, indexes and databases from different experiments.

## Interpretation

PaySim is simulated data. The application does not assign a real currency or calendar date to its values. Available data cannot establish identity, criminal intent, KYC status or a sanctions match. Post-transaction balance features are useful for retrospective triage, not pre-authorization decisions.
