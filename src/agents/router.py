import re
from src.tools.sql_tool import validate_id

UNSUPPORTED = 'The available evidence is insufficient to answer that question. Ask about a transaction, account history, risk score, or the indexed investigation policies.'


def route(question, context=None):
    q = question.lower()
    if re.search(r'\b(ignore|override|bypass)\b.*\b(instructions|rules|policy|prompt)\b|\b(drop|delete|update|insert|alter)\b|system prompt|api.?key', q):
        return 'unsupported', None
    tokens = re.findall(r'\bTXN_[A-Za-z0-9_]+\b', question, re.I)
    if len(set(tokens)) > 1:
        raise ValueError('Ask about one transaction at a time')
    txid = validate_id(tokens[0].upper()) if tokens else context
    if 'txn_' in q and not tokens:
        raise ValueError('Invalid transaction ID')
    if re.search(r'definitely|confirm.*fraud|money laundering|criminal|sanctions|kyc|beneficial owner', q):
        return 'uncertainty', txid
    if any(word in q for word in ['policy', 'policies', 'sop', 'guideline', 'when should', 'shap mean']):
        return 'policy', txid
    if any(word in q for word in ['counterparty', 'counterparties', 'same destination', 'this destination']):
        return 'counterparties', txid
    if 'velocity' in q or 'last 24' in q:
        return 'velocity', txid
    if 'similar' in q:
        return 'similar', txid
    if any(word in q for word in ['history', 'previous transactions', 'same account', 'other transactions']):
        return 'history', txid
    if txid and any(word in q for word in ['score', 'probability', 'risk level']):
        return 'score', txid
    if txid and any(word in q for word in ['investigate', 'suspicious', 'explain', 'why', 'report']):
        return 'investigate', txid
    if tokens or (txid and 'show transaction' in q):
        return 'transaction', txid
    return 'unsupported', None
