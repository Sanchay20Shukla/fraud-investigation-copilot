from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from src.config import Settings
from src.service import Copilot
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(title='Fraud Investigation RAG Copilot', version='1.0.0',
              description='Single-user portfolio demo. Evidence-based triage; no automated account actions.')


@lru_cache
def get_copilot():
    try:
        return Copilot(Settings())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(503, 'Initialize the database, model and policy index with scripts.bootstrap first') from exc


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    transaction_id: str = Field(pattern=r'^TXN_\d{7}$')


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


@app.exception_handler(LookupError)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={'detail': str(exc)})


@app.exception_handler(ValueError)
async def bad_request(request, exc):
    return JSONResponse(status_code=400, content={'detail': str(exc)})


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'fraud-investigation-copilot'}


@app.get('/ready')
def ready(copilot: Copilot = Depends(get_copilot)):
    from sqlalchemy import select, func
    from src.db import transactions
    try:
        with copilot.sql.engine.connect() as conn:
            count = conn.scalar(select(func.count()).select_from(transactions))
    except SQLAlchemyError as exc:
        raise HTTPException(503, 'Transaction database is unavailable') from exc
    if not count:
        raise HTTPException(503, 'Transaction database is empty')
    return {'status': 'ready', 'transactions': count, 'retrieval_mode': copilot.settings.retrieval_mode,
            'llm_enabled': copilot.settings.llm_enabled, 'model_version': copilot.fraud.model.metadata['model_version']}


@app.get('/transactions/{transaction_id}')
def transaction(transaction_id: str, copilot: Copilot = Depends(get_copilot)):
    return copilot.sql.transaction(transaction_id)


@app.post('/investigate')
def investigate(body: InvestigationRequest, copilot: Copilot = Depends(get_copilot)):
    return copilot.investigate(body.transaction_id)


@app.post('/chat')
def chat(body: ChatRequest, copilot: Copilot = Depends(get_copilot)):
    return copilot.chat(body.question, body.session_id)


@app.get('/investigations/{investigation_id}')
def investigation(investigation_id: str, copilot: Copilot = Depends(get_copilot)):
    report = copilot.audit.get_report(investigation_id)
    if report is None:
        raise HTTPException(404, 'Investigation not found')
    return report
