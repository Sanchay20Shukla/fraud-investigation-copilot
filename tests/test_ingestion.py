import pandas as pd
import pytest
from sqlalchemy import select, func
from src.db import initialize, transactions
from src.config import Settings
from src.ingestion.loader import normalize, ingest
from scripts.bootstrap import make_demo


def test_bad_amount_and_missing_column(tmp_path):
    path = tmp_path / 'data.csv'
    make_demo(path, 10)
    frame = pd.read_csv(path)
    frame.loc[0, 'amount'] = -1
    with pytest.raises(ValueError):
        normalize(frame)
    with pytest.raises(ValueError):
        normalize(frame.drop(columns=['nameOrig']))


def test_failed_ingestion_is_atomic(tmp_path):
    path = tmp_path / 'data.csv'
    make_demo(path, 10100)
    frame = pd.read_csv(path)
    frame.loc[10050, 'amount'] = -1
    frame.to_csv(path, index=False)
    engine = initialize(Settings(database_url=f'sqlite:///{tmp_path / "test.db"}'))
    with pytest.raises(ValueError):
        ingest(path, engine, tmp_path / 'output', None)
    with engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(transactions)) == 0
