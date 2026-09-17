"""Strict, append-only PaySim ingestion with stable IDs from zero-based source rows."""
import hashlib
import json
import numpy as np
import pandas as pd
from sqlalchemy import insert, select, func
from src.db import transactions, labels

RENAME = {'type': 'transaction_type', 'nameOrig': 'origin_account', 'nameDest': 'destination_account',
    'oldbalanceOrg': 'origin_balance_before', 'newbalanceOrig': 'origin_balance_after',
    'oldbalanceDest': 'destination_balance_before', 'newbalanceDest': 'destination_balance_after',
    'isFraud': 'fraud_label'}
TYPES = {'TRANSFER', 'CASH_OUT', 'CASH_IN', 'PAYMENT', 'DEBIT'}


def normalize(frame, offset=0):
    required = {'step', 'amount', *RENAME.keys()}
    if not required.issubset(frame.columns):
        raise ValueError(f'Missing PaySim columns: {sorted(required - set(frame.columns))}')
    df = frame.rename(columns=RENAME).copy()
    numeric = ['amount', 'origin_balance_before', 'origin_balance_after',
               'destination_balance_before', 'destination_balance_after', 'step', 'fraud_label']
    df[numeric] = df[numeric].apply(pd.to_numeric, errors='raise')
    if not np.isfinite(df[numeric].to_numpy()).all() or (df[numeric] < 0).any().any():
        raise ValueError('Amounts, balances, labels and steps must be finite and nonnegative')
    if not df.fraud_label.isin([0, 1]).all() or (df.step % 1 != 0).any():
        raise ValueError('Invalid fraud label or fractional step')
    if not df.transaction_type.isin(TYPES).all():
        raise ValueError('Unsupported transaction type')
    for key in ['origin_account', 'destination_account']:
        if df[key].isna().any() or df[key].astype(str).str.strip().eq('').any():
            raise ValueError('Missing account identifier')
    df['row_number'] = np.arange(offset, offset + len(df))
    df['transaction_id'] = df.row_number.map(lambda n: f'TXN_{n:07d}')
    return df


def ingest(path, engine, output, limit=200000):
    with engine.connect() as conn:
        if conn.scalar(select(func.count()).select_from(transactions)):
            raise ValueError('Database already contains transactions. Use a new database for a new dataset.')
    count, previous_step = 0, -1
    digest = hashlib.sha256()
    # One transaction ensures validation failures do not leave a partial database.
    with engine.begin() as conn:
        for frame in pd.read_csv(path, chunksize=10000, nrows=limit):
            df = normalize(frame, count)
            if not df.step.is_monotonic_increasing or df.step.iloc[0] < previous_step:
                raise ValueError('PaySim rows must be in ascending step order')
            previous_step = int(df.step.iloc[-1])
            digest.update(df.to_csv(index=False).encode())
            conn.execute(insert(transactions), df[[c.name for c in transactions.columns]].to_dict('records'))
            conn.execute(insert(labels), df[['transaction_id', 'fraud_label']].to_dict('records'))
            count += len(df)
        if count == 0:
            raise ValueError('Dataset is empty')
    manifest = {'source': str(path.resolve()), 'rows': count, 'normalized_sha256': digest.hexdigest(),
                'id_convention': 'TXN_ + zero-based source row padded to 7 digits',
                'currency': 'Unspecified PaySim simulation units', 'sample': limit is not None}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'dataset_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest
