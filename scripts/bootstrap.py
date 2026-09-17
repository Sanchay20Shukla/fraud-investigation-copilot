"""python -m scripts.bootstrap --paysim PATH --limit 200000"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import select, func
from src.config import Settings, ROOT
from src.db import initialize, transactions
from src.ingestion.loader import ingest
from src.models.train import train
from src.retrieval.retriever import index_documents


def make_demo(path, rows=6000):
    """Clearly synthetic fixture, not PaySim and not a valid fraud benchmark."""
    rng = np.random.default_rng(42)
    records = []
    for n in range(rows):
        fraud = int(rng.random() < .06)
        balance = float(rng.integers(1000, 200000))
        amount = balance if fraud else float(rng.uniform(1, balance))
        kind = str(rng.choice(['TRANSFER', 'CASH_OUT', 'PAYMENT']))
        records.append({'step': n // 100 + 1, 'type': kind, 'amount': round(amount, 2),
            'nameOrig': f'C{n % 47}', 'oldbalanceOrg': balance,
            'newbalanceOrig': 0 if fraud else round(balance - amount, 2),
            'nameDest': f'C{100 + n % 29}', 'oldbalanceDest': 1000,
            'newbalanceDest': 1000 if fraud else round(1000 + amount, 2),
            'isFraud': fraud, 'isFlaggedFraud': 0})
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paysim', type=Path)
    parser.add_argument('--limit', type=int, default=200000, help='0 loads all rows')
    parser.add_argument('--demo', action='store_true', help='Use generated educational fixtures')
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    if args.demo and args.paysim:
        parser.error('Choose --demo or --paysim')
    settings = Settings()
    output = ROOT / 'data/processed'
    output.mkdir(parents=True, exist_ok=True)
    engine = initialize(settings)
    with engine.connect() as conn:
        count = conn.scalar(select(func.count()).select_from(transactions))
    if not count:
        path = args.paysim or ROOT / 'data/raw/paysim.csv'
        if args.demo:
            path = ROOT / 'data/raw/synthetic_demo.csv'
            make_demo(path)
        if not path.is_file():
            parser.error('Supply --paysim PATH or --demo; no dataset was found')
        print(json.dumps(ingest(path, engine, output, args.limit or None), indent=2), flush=True)
        if args.demo:
            (output / 'SYNTHETIC_DEMO.txt').write_text('Generated educational fixture. Metrics are not PaySim performance.', encoding='utf-8')
    else:
        if args.paysim or args.demo:
            print('Existing dataset retained. To change datasets, configure a new database and artifact directory.', flush=True)
        print(f'Reusing {count} existing transaction rows.', flush=True)
    print('Training XGBoost on chronological splits...', flush=True)
    print(json.dumps(train(engine, settings.artifacts), indent=2), flush=True)
    print(json.dumps(index_documents(settings, engine)), flush=True)
    print('Ready. Run: python -m uvicorn api.main:app --host 127.0.0.1 --port 8010', flush=True)


if __name__ == '__main__':
    main()
