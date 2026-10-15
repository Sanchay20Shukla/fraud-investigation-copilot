"""Isolated, ephemeral synthetic runtime for public portfolio exploration."""
from pathlib import Path
from tempfile import mkdtemp
from threading import RLock
import streamlit as st

@st.cache_resource(show_spinner='Preparing synthetic transactions, model and policy index…')
def runtime():
    from scripts.bootstrap import make_demo
    from src.config import Settings, ROOT
    from src.db import initialize
    from src.ingestion.loader import ingest
    from src.models.train import train
    from src.retrieval.retriever import index_documents
    from src.service import Copilot

    work=Path(mkdtemp(prefix='copilot-public-demo-'))
    artifacts=work/'models'
    output=work/'processed'; output.mkdir()
    settings=Settings(database_url=f'sqlite:///{work / "demo.db"}',
        read_database_url='',audit_database_url='',artifacts=artifacts,
        documents=ROOT/'documents',retrieval_mode='lexical',llm_enabled=False)
    source=work/'synthetic.csv'
    make_demo(source,rows=2000)
    engine=initialize(settings)
    ingest(source,engine,output,None)
    train(engine,artifacts)
    index_documents(settings,engine)
    return Copilot(settings),RLock()

def chat(question,session_id=None):
    copilot,lock=runtime()
    # Serialize SQLite audit writes across visitors; context IDs remain session-specific.
    with lock:
        return copilot.chat(question,session_id)
