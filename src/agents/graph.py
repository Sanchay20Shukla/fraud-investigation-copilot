from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from src.agents.report import build_report, validate_report


class State(TypedDict, total=False):
    transaction_id: str
    transaction: dict
    history: list
    velocity: dict
    risk: dict
    policies: list
    report: dict
    trace: list[str]


def build_graph(settings, sql, fraud, rag):
    def fetch(state):
        return {'transaction': sql.transaction(state['transaction_id']), 'trace': ['fetch_transaction']}
    def history(state):
        return {'history': sql.history(state['transaction']), 'velocity': sql.velocity(state['transaction']),
                'trace': state['trace'] + ['fetch_prior_history']}
    def score(state):
        return {'risk': fraud.predict(state['transaction']), 'trace': state['trace'] + ['score_and_explain']}
    def retrieve(state):
        query = 'high risk score 80 enhanced investigation escalation manual review' if state['risk']['risk_score'] >= 80 else 'moderate low scores 50 79 standard review'
        policies = rag.search(query, k=5)
        return {'policies': policies, 'trace': state['trace'] + ['retrieve_policies']}
    def generate(state):
        return {'report': build_report(settings, state['transaction'], state['risk'], state['history'],
            state['velocity'], state['policies']), 'trace': state['trace'] + ['compose_report']}
    def validate(state):
        report = validate_report(state['report'])
        report['workflow'] = state['trace'] + ['validate_evidence']
        return {'report': report}
    graph = StateGraph(State)
    nodes = [('fetch', fetch), ('history', history), ('score', score), ('retrieve', retrieve),
             ('generate', generate), ('validate', validate)]
    previous = START
    for name, fn in nodes:
        graph.add_node(name, fn)
        graph.add_edge(previous, name)
        previous = name
    graph.add_edge(previous, END)
    return graph.compile()
