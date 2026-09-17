import json
import joblib
import numpy as np
from sqlalchemy import select, delete, insert, Table, Column, String, MetaData
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.db import chunks, engine_for
from src.ingestion.chunker import load_chunks


def vector_table():
    from pgvector.sqlalchemy import VECTOR
    return Table('policy_vectors', MetaData(), Column('chunk_id', String, primary_key=True),
                 Column('embedding', VECTOR(384)))


def index_documents(settings, engine):
    records = load_chunks(settings.documents)
    settings.artifacts.mkdir(parents=True, exist_ok=True)
    texts = [r['section'] + ' ' + r['content'] for r in records]
    if settings.retrieval_mode == 'lexical':
        encoder = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', sublinear_tf=True)
        matrix = encoder.fit_transform(texts)
        bundle = {'mode': 'lexical', 'encoder': encoder, 'matrix': matrix, 'records': records}
    elif settings.retrieval_mode == 'semantic':
        from src.ingestion.embeddings import SemanticEncoder
        vectors = SemanticEncoder().encode(texts)
        bundle = {'mode': 'semantic', 'matrix': np.array(vectors), 'records': records}
        if engine.dialect.name == 'postgresql':
            table = vector_table()
            table.create(engine, checkfirst=True)
            with engine.begin() as conn:
                conn.execute(delete(table))
                conn.execute(insert(table), [{'chunk_id': r['chunk_id'], 'embedding': v} for r, v in zip(records, vectors)])
    else:
        raise ValueError('RETRIEVAL_MODE must be lexical or semantic')
    with engine.begin() as conn:
        conn.execute(delete(chunks))
        conn.execute(insert(chunks), records)
    joblib.dump(bundle, settings.artifacts / 'retrieval.joblib')
    return {'chunks': len(records), 'mode': settings.retrieval_mode}


class Retriever:
    def __init__(self, settings):
        self.settings = settings
        self.bundle = joblib.load(settings.artifacts / 'retrieval.joblib')
        if self.bundle['mode'] != settings.retrieval_mode:
            raise ValueError('Retrieval mode changed; rebuild the policy index')
        self.engine = engine_for(settings.read_database_url or settings.database_url, readonly=True)
        self.encoder = None
        if settings.retrieval_mode == 'semantic':
            from src.ingestion.embeddings import SemanticEncoder
            self.encoder = SemanticEncoder()

    def search(self, query, k=5):
        k = max(1, min(k, 10))
        if self.bundle['mode'] == 'lexical':
            vector = self.bundle['encoder'].transform([query])
            scores = cosine_similarity(vector, self.bundle['matrix'])[0]
            threshold = .08
        else:
            vector = self.encoder.encode([query])[0]
            threshold = .28
            if self.engine.dialect.name == 'postgresql':
                table = vector_table()
                distance = table.c.embedding.cosine_distance(vector)
                statement = select(chunks, (1 - distance).label('score')).join(table,
                    chunks.c.chunk_id == table.c.chunk_id).order_by(distance).limit(k)
                with self.engine.connect() as conn:
                    return [dict(r) for r in conn.execute(statement).mappings() if r['score'] >= threshold]
            scores = cosine_similarity([vector], self.bundle['matrix'])[0]
        return [dict(self.bundle['records'][i], score=float(scores[i]))
                for i in np.argsort(scores)[::-1][:k] if scores[i] >= threshold]
