import uuid
from src.tools.sql_tool import SQLTool
from src.tools.fraud_model_tool import FraudModelTool
from src.tools.rag_tool import RAGTool
from src.db import AuditStore
from src.agents.graph import build_graph
from src.agents.router import route, UNSUPPORTED


class Copilot:
    def __init__(self, settings):
        self.settings = settings
        self.sql = SQLTool(settings)
        self.fraud = FraudModelTool(settings)
        self.rag = RAGTool(settings)
        self.audit = AuditStore(settings)
        self.graph = build_graph(settings, self.sql, self.fraud, self.rag)

    def investigate(self, transaction_id):
        report = self.graph.invoke({'transaction_id': transaction_id})['report']
        return self.audit.save_report(report)

    def chat(self, question, session_id=None):
        # Session IDs are unguessable capability tokens for this single-user demo.
        if session_id is not None:
            try:
                session_id = str(uuid.UUID(session_id))
            except ValueError:
                raise ValueError('session_id must be a UUID')
        session_id = session_id or str(uuid.uuid4())
        intent, txid = route(question, self.audit.get_context(session_id))
        result = {'session_id': session_id, 'intent': intent, 'sources': []}
        if intent == 'unsupported':
            return dict(result, answer=UNSUPPORTED)
        if intent == 'uncertainty':
            return dict(result, answer='The available evidence is insufficient to establish fraud, money laundering, identity, sanctions status or criminal intent. Further independent investigation is required.')
        if intent == 'policy':
            sources = self.rag.search(question)
            return dict(result, sources=sources, answer='\n\n'.join(
                f"[{p['source']} | {p['section']} | {p['chunk_id']}]\n{p['content']}" for p in sources) or UNSUPPORTED)
        if not txid:
            return dict(result, answer='Provide a transaction ID first, for example: Investigate TXN_0000002.')
        tx = self.sql.transaction(txid)
        if intent == 'investigate':
            report = self.investigate(txid)
            result.update(answer=report['summary'], report=report, sources=report['sources'])
        elif intent == 'score':
            risk = self.fraud.predict(tx)
            result.update(answer=f"Risk score: {risk['risk_score']}/100 ({risk['risk_level']}). This does not confirm fraud.", risk=risk)
        elif intent in ['history', 'counterparties', 'similar']:
            rows = self.sql.similar(tx) if intent == 'similar' else self.sql.history(tx, counterparties=intent == 'counterparties')
            result.update(answer=f'{len(rows)} matching earlier transactions returned. Loaded data only; results are capped. Similarity does not establish suspicion.', transactions=rows)
        elif intent == 'velocity':
            velocity = self.sql.velocity(tx)
            result.update(answer=f"{velocity['count']} earlier transactions over {velocity['window_steps']} steps in the loaded data.", velocity=velocity)
        else:
            result.update(answer=f"{txid}: {tx['transaction_type']}, amount {tx['amount']:,.2f} simulation units.", transaction=tx)
        if not result['sources']:
            result['sources'] = [{'id': txid, 'source': 'transactions', 'scope': 'Loaded data; prior-step queries exclude current step'}]
            if 'risk' in result:
                result['sources'].append({'id': result['risk']['model_version'], 'source': 'fraud_model.ubj'})
        self.audit.set_context(session_id, txid)
        return result
