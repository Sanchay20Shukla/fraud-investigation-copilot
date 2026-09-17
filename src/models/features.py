import numpy as np
import pandas as pd

TYPES = ['TRANSFER', 'CASH_OUT', 'CASH_IN', 'PAYMENT', 'DEBIT']


def features(rows):
    """Post-transaction triage features. Labels and IDs are never model inputs."""
    df = pd.DataFrame(rows)
    names = ['amount', 'origin_balance_before', 'origin_balance_after',
             'destination_balance_before', 'destination_balance_after']
    result = df[names].astype(float).copy()
    result['amount_balance_ratio'] = df.amount / (df.origin_balance_before + 1)
    outgoing = df.transaction_type.isin(['TRANSFER', 'CASH_OUT', 'PAYMENT', 'DEBIT'])
    expected = np.where(outgoing, df.origin_balance_before - df.amount, df.origin_balance_before + df.amount)
    result['origin_balance_error'] = abs(expected - df.origin_balance_after)
    result['origin_balance_change'] = df.origin_balance_before - df.origin_balance_after
    result['destination_balance_change'] = df.destination_balance_after - df.destination_balance_before
    result['zero_balance_after'] = (df.origin_balance_after == 0).astype(int)
    result['large_transaction'] = (df.amount >= 200000).astype(int)
    for kind in TYPES:
        result[f'type_{kind}'] = (df.transaction_type == kind).astype(int)
    return result.replace([np.inf, -np.inf], 0)
