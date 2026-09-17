"""Reproducible retrieval evaluation. No LLM judge and no invented RAGAS metrics."""
import json
from pathlib import Path
from src.config import Settings, ROOT
from src.retrieval.retriever import Retriever
from src.agents.router import route


def evaluate(settings, cases):
    retriever = Retriever(settings)
    results = []
    for case in cases:
        intent, _ = route(case['question'])
        hits = retriever.search(case['question'], 5) if case['expected_sources'] else []
        sources = [h['source'] for h in hits]
        expected = set(case['expected_sources'])
        intersection = expected.intersection(sources)
        rank = next((i+1 for i, source in enumerate(sources) if source in expected), None)
        results.append(dict(case, retrieved_sources=sources, intent=intent,
            source_recall=len(intersection)/len(expected) if expected else None,
            source_precision=len(intersection)/len(set(sources)) if sources else (0 if expected else None),
            reciprocal_rank=1/rank if rank else 0,
            route_correct=intent == case['expected_intent']))
    relevant = [r for r in results if r['expected_sources']]
    def average(key):
        return sum(r[key] for r in relevant)/len(relevant) if relevant else None
    return {'cases': len(results), 'policy_cases': len(relevant), 'retrieval_mode': settings.retrieval_mode,
        'source_recall_at_5': average('source_recall'), 'source_precision_at_5': average('source_precision'),
        'mean_reciprocal_rank': average('reciprocal_rank'),
        'router_accuracy': sum(r['route_correct'] for r in results)/len(results),
        'not_measured': ['LLM faithfulness', 'LLM answer relevancy', 'RAGAS context precision/recall'],
        'method': 'Document-level gold-source coverage and rank on a small authored development set. Not an independent test benchmark.',
        'results': results}


def main():
    cases = json.loads((ROOT / 'evaluation/questions.json').read_text(encoding='utf-8'))
    report = evaluate(Settings(), cases)
    destination = ROOT / 'reports/retrieval_metrics.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}, indent=2))


if __name__ == '__main__':
    main()
