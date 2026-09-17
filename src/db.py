from datetime import datetime, timezone
import uuid
from sqlalchemy import (create_engine, event, MetaData, Table, Column, String,
                        Integer, Float, JSON, select, insert, text)

metadata = MetaData()
transactions = Table('transactions', metadata,
    Column('transaction_id', String, primary_key=True), Column('row_number', Integer, nullable=False),
    Column('step', Integer, nullable=False, index=True), Column('transaction_type', String, nullable=False),
    Column('amount', Float, nullable=False), Column('origin_account', String, index=True),
    Column('destination_account', String, index=True),
    *[Column(n, Float, nullable=False) for n in ['origin_balance_before', 'origin_balance_after',
        'destination_balance_before', 'destination_balance_after']])
labels = Table('training_labels', metadata, Column('transaction_id', String, primary_key=True),
               Column('fraud_label', Integer, nullable=False))
predictions = Table('fraud_predictions', metadata, Column('prediction_id', String, primary_key=True),
    Column('transaction_id', String, index=True), Column('model_version', String), Column('payload', JSON))
investigations = Table('investigations', metadata, Column('investigation_id', String, primary_key=True),
    Column('transaction_id', String, index=True), Column('created_at', String), Column('report', JSON))
sessions = Table('sessions', metadata, Column('session_id', String, primary_key=True),
    Column('transaction_id', String), Column('updated_at', String))
chunks = Table('policy_chunks', metadata, Column('chunk_id', String, primary_key=True),
    Column('source', String), Column('section', String), Column('content', String), Column('digest', String))


def engine_for(url, readonly=False):
    kwargs = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite') else {}
    engine = create_engine(url, pool_pre_ping=True, **kwargs)
    if readonly and url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def query_only(connection, _):
            connection.execute('PRAGMA query_only = ON')
    if readonly and not url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def read_transaction(connection, _):
            with connection.cursor() as cursor:
                cursor.execute('SET default_transaction_read_only = on')
            connection.commit()
    return engine


def initialize(settings):
    engine = engine_for(settings.database_url)
    if engine.dialect.name == 'postgresql':
        with engine.begin() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    metadata.create_all(engine)
    return engine


class AuditStore:
    """App-owned persistence, never exposed as an agent tool."""
    def __init__(self, settings):
        self.engine = engine_for(settings.audit_database_url or settings.database_url)

    def save_report(self, report):
        report = dict(report, investigation_id=str(uuid.uuid4()),
                      created_at=datetime.now(timezone.utc).isoformat())
        with self.engine.begin() as conn:
            conn.execute(insert(investigations).values(investigation_id=report['investigation_id'],
                transaction_id=report['transaction_id'], created_at=report['created_at'], report=report))
            conn.execute(insert(predictions).values(prediction_id=str(uuid.uuid4()),
                transaction_id=report['transaction_id'], model_version=report['risk']['model_version'],
                payload=report['risk']))
        return report

    def get_report(self, investigation_id):
        with self.engine.connect() as conn:
            return conn.execute(select(investigations.c.report).where(
                investigations.c.investigation_id == investigation_id)).scalar_one_or_none()

    def get_context(self, session_id):
        with self.engine.connect() as conn:
            return conn.execute(select(sessions.c.transaction_id).where(
                sessions.c.session_id == session_id)).scalar_one_or_none()

    def set_context(self, session_id, transaction_id):
        # Dialect-specific upsert is atomic for concurrent requests.
        if self.engine.dialect.name == 'sqlite':
            from sqlalchemy.dialects.sqlite import insert as upsert
        else:
            from sqlalchemy.dialects.postgresql import insert as upsert
        values = dict(session_id=session_id, transaction_id=transaction_id,
                      updated_at=datetime.now(timezone.utc).isoformat())
        with self.engine.begin() as conn:
            conn.execute(upsert(sessions).values(**values).on_conflict_do_update(
                index_elements=['session_id'], set_=values))
