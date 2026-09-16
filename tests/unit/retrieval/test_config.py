"""Tests unitaires pour app/retrieval/config.py"""

from app.retrieval.config import load_config


class TestLoadConfig:
    """Vérifie la lecture des 4 rôles retrieval."""

    def test_load_config_reads_rag_acceptance_role(self):
        config = load_config()

        assert config["rag_acceptance"]["top_n"] == 15
        assert config["rag_acceptance"]["taux_reussite_minimum"] == 0.9

    def test_load_config_reads_decomposition_role(self):
        config = load_config()

        assert config["decomposition"]["modele"] == "gpt-5.4-mini"
        assert config["decomposition"]["env_var"] == "AZURE_MODEL_GPT_MINI"
        assert config["decomposition"]["temperature"] == 0

    def test_load_config_reads_jugement_role(self):
        config = load_config()

        assert config["jugement"]["modele"] == "gpt-5.4-mini"
        assert config["jugement"]["temperature"] == 0

    def test_load_config_reads_guardrail_role(self):
        config = load_config()

        assert config["guardrail"]["modele"] == "gpt-5.4-mini"
        assert config["guardrail"]["temperature"] == 0
