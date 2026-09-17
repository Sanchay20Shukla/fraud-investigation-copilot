from dataclasses import replace
from types import SimpleNamespace
import pytest
from src.agents.report import select_facts

FACTS = [
    {'id': 'transaction', 'text': 'TXN_0000002 exists', 'sources': ['TXN_0000002']},
    {'id': 'model', 'text': 'Risk is elevated, not confirmed fraud', 'sources': ['xgb-demo']},
]


def test_valid_llm_selection_is_extractive(settings, monkeypatch):
    def parse(**kwargs):
        assert kwargs['store'] is False
        return SimpleNamespace(output_parsed=SimpleNamespace(evidence_ids=['model']))
    import openai
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    facts, mode, warning = select_facts(replace(settings, llm_enabled=True, openai_model='test-model'), FACTS)
    assert facts == FACTS and mode == 'llm_evidence_selection' and warning is None


@pytest.mark.parametrize('selection', [None, ['fabricated'], []])
def test_invalid_selection_falls_back(settings, monkeypatch, selection):
    def parse(**kwargs):
        return SimpleNamespace(output_parsed=SimpleNamespace(evidence_ids=selection) if selection is not None else None)
    import openai
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    facts, mode, warning = select_facts(replace(settings, llm_enabled=True, openai_model='test-model'), FACTS)
    assert facts == FACTS and mode == 'deterministic_fallback' and warning


def test_unconfigured_model_falls_back(settings):
    assert select_facts(replace(settings, llm_enabled=True, openai_model=''), FACTS)[1] == 'deterministic_fallback'
