import hashlib
import json
import numpy as np
import pandas as pd
from sqlalchemy import select
from sklearn.metrics import (precision_score, recall_score, f1_score,
    average_precision_score, roc_auc_score, confusion_matrix)
from xgboost import XGBClassifier, DMatrix
from src.db import transactions, labels
from src.models.features import features


def train(engine, artifacts):
    with engine.connect() as conn:
        df = pd.read_sql(select(transactions, labels.c.fraud_label).join(labels,
            transactions.c.transaction_id == labels.c.transaction_id).order_by(
                transactions.c.step, transactions.c.row_number), conn)
    steps = np.sort(df.step.unique())
    if len(steps) < 6:
        raise ValueError('Need at least 6 distinct time steps for chronological evaluation')
    first, second = steps[int(len(steps)*.70)], steps[int(len(steps)*.85)]
    train_df, val, test = df[df.step < first], df[(df.step >= first) & (df.step < second)], df[df.step >= second]
    if any(part.fraud_label.nunique() < 2 for part in [train_df, val, test]):
        raise ValueError('Each time split needs both fraud classes; ingest more rows')
    x, y = features(train_df), train_df.fraud_label
    model = XGBClassifier(n_estimators=180, max_depth=4, learning_rate=.06,
        eval_metric='logloss', tree_method='hist', random_state=42, n_jobs=2,
        scale_pos_weight=float((y == 0).sum() / (y == 1).sum()))
    model.fit(x, y)
    vp = model.predict_proba(features(val))[:, 1]
    thresholds = np.linspace(.05, .95, 91)
    threshold = float(max(thresholds, key=lambda t: f1_score(val.fraud_label, vp >= t, zero_division=0)))
    p = model.predict_proba(features(test))[:, 1]
    pred = p >= threshold
    artifacts.mkdir(parents=True, exist_ok=True)
    model.save_model(artifacts / 'fraud_model.ubj')
    version = 'xgb-' + hashlib.sha256((artifacts / 'fraud_model.ubj').read_bytes()).hexdigest()[:12]
    report = {'model_version': version, 'dataset_rows': len(df), 'feature_names': list(x.columns),
        'threshold_selected_on_validation': threshold,
        'precision': float(precision_score(test.fraud_label, pred, zero_division=0)),
        'recall': float(recall_score(test.fraud_label, pred)), 'f1': float(f1_score(test.fraud_label, pred)),
        'pr_auc': float(average_precision_score(test.fraud_label, p)),
        'roc_auc': float(roc_auc_score(test.fraud_label, p)),
        'confusion_matrix': confusion_matrix(test.fraud_label, pred).tolist(),
        'splits': {name: {'rows': len(part), 'fraud_rows': int(part.fraud_label.sum()),
            'min_step': int(part.step.min()), 'max_step': int(part.step.max())}
            for name, part in [('train', train_df), ('validation', val), ('test', test)]},
        'limitations': ['Uncalibrated model probability; score bands are synthetic policy thresholds.',
            'Post-transaction balance features are unsuitable for pre-authorization scoring.',
            'Subset results are not whole-PaySim or real-world performance.']}
    (artifacts / 'model_metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


class FraudModel:
    def __init__(self, artifacts):
        self.model = XGBClassifier()
        self.model.load_model(artifacts / 'fraud_model.ubj')
        self.metadata = json.loads((artifacts / 'model_metrics.json').read_text(encoding='utf-8'))

    def score(self, transaction):
        x = features([transaction])
        probability = float(self.model.predict_proba(x)[0, 1])
        # Native exact TreeSHAP avoids third-party model-format compatibility issues.
        contributions = self.model.get_booster().predict(DMatrix(x), pred_contribs=True,
                                                        approx_contribs=False)[0]
        values = contributions[:-1]
        base = float(contributions[-1])
        score = int(probability * 100)
        drivers = [{'feature': key, 'value': float(x.iloc[0][key]),
            'shap_value': float(value), 'direction': 'increases risk' if value > 0 else 'decreases risk'}
            for key, value in zip(x.columns, values)]
        drivers.sort(key=lambda item: abs(item['shap_value']), reverse=True)
        return {'fraud_probability': probability, 'risk_score': score,
            'risk_level': 'HIGH' if score >= 80 else 'MEDIUM' if score >= 50 else 'LOW',
            'model_version': self.metadata['model_version'], 'drivers': drivers,
            'shap_base_value': base, 'shap_units': 'log-odds; contributions are not percentage points',
            'probability_note': 'Uncalibrated model estimate, not a confirmed fraud finding'}
