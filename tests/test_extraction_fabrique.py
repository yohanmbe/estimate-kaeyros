import pytest

from src.extraction.fabrique import construire_extracteur, fournisseur_actif
from src.extraction.groq import ExtracteurGroq
from src.extraction.mock import ExtracteurMock


def test_llm_provider_absent_choisit_groq(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    assert fournisseur_actif() == "groq"


def test_llm_provider_mock_evite_tout_appel_reseau(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    assert isinstance(construire_extracteur(), ExtracteurMock)


def test_llm_provider_groq_construit_lextracteur_groq(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "cle-de-test")

    assert isinstance(construire_extracteur(), ExtracteurGroq)


def test_llm_provider_insensible_a_la_casse_et_aux_espaces(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "  Mock  ")

    assert fournisseur_actif() == "mock"


def test_llm_provider_inconnu_est_refuse_plutot_que_remplace(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "grok")

    with pytest.raises(RuntimeError, match="LLM_PROVIDER inconnu"):
        fournisseur_actif()


def test_cle_api_manquante_est_signalee_clairement(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        construire_extracteur()
