"""
Tests unitaires de scripts/review_pr.py : ce qui décide de bloquer ou non la
CI. Aucun appel LLM ni HTTP réel — seul le comportement de décision est testé.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError
from tenacity import wait_none

CHEMIN = Path(__file__).resolve().parents[3] / "scripts" / "review_pr.py"

ROLE = {
    "modele": "kimi-k2.6",
    "env_var": "AZURE_MODEL_KIMI",
    "prix_entree_par_million": 0.8008,
    "prix_sortie_par_million": 3.3875,
}


@pytest.fixture
def script():
    spec = importlib.util.spec_from_file_location("review_pr_script", CHEMIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCodeSortie:
    """Seul un verdict « bloquant » fait échouer la CI."""

    def test_bloquant_fait_echouer(self, script):
        assert script.code_sortie("bloquant") == 1

    @pytest.mark.parametrize("verdict", ["ok", "mineur"])
    def test_le_reste_est_informatif(self, script, verdict):
        """Casse si une remarque mineure ferme la porte de dev."""
        assert script.code_sortie(verdict) == 0


class TestConstruireCorps:
    def test_annonce_la_troncature(self, script):
        """Casse si une revue partielle est postée sans le dire."""
        resultat = {"verdict": "mineur", "commentaire": "Rien de grave.", "cout_usd": 0.01}
        corps = script.construire_corps(resultat, ROLE, tronque=True)
        assert "Revue partielle" in corps
        assert str(script.MAX_DIFF_CHARS) in corps

    def test_pas_d_avertissement_sans_troncature(self, script):
        resultat = {"verdict": "ok", "commentaire": "RAS.", "cout_usd": 0.01}
        corps = script.construire_corps(resultat, ROLE, tronque=False)
        assert "Revue partielle" not in corps
        assert "kimi-k2.6" in corps


class TestInvoquerLlm:
    """Retry : 3 tentatives, la réponse hors format est retentée."""

    def _parser(self, resultats):
        parser = MagicMock()
        parser.parse.side_effect = resultats
        return parser

    def test_retente_puis_reussit(self, script):
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(
            content="peu importe", usage_metadata={"input_tokens": 10, "output_tokens": 5}
        )
        parser = self._parser(
            [ValueError("pas du JSON"), {"verdict": "ok", "commentaire": "RAS."}]
        )
        sans_attente = script.invoquer_llm.retry_with(wait=wait_none())
        parsed, usage = sans_attente(llm, parser, "prompt")
        assert parsed["verdict"] == "ok"
        assert parser.parse.call_count == 2
        assert usage["input_tokens"] == 10

    def test_abandonne_apres_trois_tentatives(self, script):
        """Casse si le script insiste au-delà de 3 essais (coût) ou renonce avant."""
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="x", usage_metadata={})
        parser = self._parser([ValueError("pas du JSON")] * 3)
        sans_attente = script.invoquer_llm.retry_with(wait=wait_none())
        with pytest.raises(ValueError):
            sans_attente(llm, parser, "prompt")
        assert parser.parse.call_count == 3


class TestInvoquerLlmValidation:
    """Vrai JsonOutputParser : la validation du schéma est faite par invoquer_llm."""

    def _appeler(self, script, contenus):
        llm = MagicMock()
        llm.invoke.side_effect = [
            MagicMock(content=c, usage_metadata={"input_tokens": 1, "output_tokens": 1})
            for c in contenus
        ]
        parser = JsonOutputParser(pydantic_object=script.RevueOutput)
        sans_attente = script.invoquer_llm.retry_with(wait=wait_none())
        return llm, lambda: sans_attente(llm, parser, "prompt")

    def test_reponse_valide_passe(self, script):
        llm, appeler = self._appeler(script, ['{"verdict": "mineur", "commentaire": "Un point."}'])
        parsed, usage = appeler()
        assert parsed["verdict"] == "mineur"
        assert parsed["commentaire"] == "Un point."
        assert usage["input_tokens"] == 1
        assert llm.invoke.call_count == 1

    def test_verdict_hors_enumeration_retente_puis_leve(self, script):
        """Casse si "OK" traverse invoquer_llm (KeyError plus loin, CI rouge sans bloquant)."""
        llm, appeler = self._appeler(script, ['{"verdict": "OK", "commentaire": "RAS."}'] * 3)
        with pytest.raises(ValidationError):
            appeler()
        assert llm.invoke.call_count == 3

    def test_reponse_invalide_puis_valide_reussit_a_la_2e_tentative(self, script):
        llm, appeler = self._appeler(
            script,
            [
                '{"verdict": "OK", "commentaire": "RAS."}',
                '{"verdict": "ok", "commentaire": "RAS."}',
            ],
        )
        parsed, _ = appeler()
        assert parsed["verdict"] == "ok"
        assert llm.invoke.call_count == 2


class TestCorpsEchec:
    def test_dit_que_la_ci_n_est_pas_bloquee(self, script):
        """Casse si une panne de l'outil se met à ressembler à un verdict."""
        corps = script.construire_corps_echec(RuntimeError("Azure indisponible"))
        assert "non aboutie" in corps
        assert "Azure indisponible" in corps
