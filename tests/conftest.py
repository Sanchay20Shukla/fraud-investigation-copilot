import pytest
from src.config import Settings, ROOT
from src.db import initialize
from src.ingestion.loader import ingest
from src.models.train import train
from src.retrieval.retriever import index_documents
from scripts.bootstrap import make_demo


@pytest.fixture(scope='session')
def settings(tmp_path_factory):
    root = tmp_path_factory.mktemp('copilot')
    config = Settings(database_url=f'sqlite:///{root / "test.db"}', read_database_url='',
        audit_database_url='', artifacts=root / 'models', documents=ROOT / 'documents',
        retrieval_mode='lexical', llm_enabled=False)
    engine = initialize(config)
    path = root / 'demo.csv'
    make_demo(path)
    ingest(path, engine, root / 'processed', limit=None)
    train(engine, config.artifacts)
    index_documents(config, engine)
    return config


@pytest.fixture(scope='session')
def copilot(settings):
    from src.service import Copilot
    return Copilot(settings)


@pytest.fixture
def client(copilot):
    from fastapi.testclient import TestClient
    from api.main import app, get_copilot
    app.dependency_overrides[get_copilot] = lambda: copilot
    with TestClient(app) as result:
        yield result
    app.dependency_overrides.clear()
