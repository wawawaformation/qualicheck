"""
Tests unitaires du routeur POST /questions (increment A1b).

app/agent_us2/loop.repondre() est mocké — déjà couvert entièrement par
tests/unit/agent_us2/test_loop.py. Ces tests vérifient seulement la couche
HTTP : code de statut, forme JSON, dérivation de `statut`, conforme à
conception/3_autre_us/us2_question_libre/increments/A_agent_nu/openapi.json.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent_us2.loop import ResultatAgent
from app.agent_us2.main import app

client = TestClient(app)


def _resultat(regles_citees: list[dict], reponse: str = "Réponse.", **extra) -> ResultatAgent:
    return ResultatAgent(
        reponse=reponse,
        regles_citees=regles_citees,
        nb_tours=1,
        duree_s=1.0,
        tokens_entree=10,
        tokens_sortie=10,
        cout_euros_estime=0.0000075,
        trace_id=None,
        **extra,
    )


class TestPoserQuestion:
    """Tests de POST /questions."""

    @patch("app.agent_us2.api.repondre")
    def test_statut_repondu_quand_des_regles_sont_citees(self, mock_repondre):
        mock_repondre.return_value = _resultat(
            [{"numero": 56, "intitule": "Prix TTC"}], reponse="Il faut le prix TTC."
        )

        reponse = client.post("/questions", json={"question": "Faut-il le prix TTC ?"})

        assert reponse.status_code == 200
        assert reponse.json() == {
            "statut": "repondu",
            "reponse": "Il faut le prix TTC.",
            "regles_citees": [{"numero": 56, "intitule": "Prix TTC"}],
            "trace_id": None,
        }

    @patch("app.agent_us2.api.repondre")
    def test_statut_aucune_regle_pertinente_quand_rien_nest_cite(self, mock_repondre):
        mock_repondre.return_value = _resultat([], reponse="Rien trouvé.")

        reponse = client.post("/questions", json={"question": "Une question quelconque ?"})

        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "aucune_regle_pertinente"

    @patch("app.agent_us2.api.repondre")
    def test_statut_service_indisponible_quand_un_outil_est_en_panne_sans_regle_citee(
        self, mock_repondre
    ):
        """Casse si une panne de l'API des règles est classée « rien ne correspond »."""
        mock_repondre.return_value = _resultat(
            [], reponse="Service indisponible.", panne_outil=True
        )

        reponse = client.post("/questions", json={"question": "Comment traiter les images ?"})

        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "service_indisponible"

    @patch("app.agent_us2.api.repondre")
    def test_statut_repondu_quand_une_panne_a_ete_rattrapee(self, mock_repondre):
        """Casse si une panne survenue puis rattrapée déclasse une vraie réponse sourcée."""
        mock_repondre.return_value = _resultat(
            [{"numero": 116, "intitule": "Images décoratives"}], panne_outil=True
        )

        reponse = client.post("/questions", json={"question": "Comment traiter les images ?"})

        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "repondu"

    @patch("app.agent_us2.api.repondre")
    def test_503_quand_lagent_est_indisponible(self, mock_repondre):
        mock_repondre.side_effect = TimeoutError("LLM injoignable")

        reponse = client.post("/questions", json={"question": "Une question ?"})

        assert reponse.status_code == 503
        assert reponse.json() == {"detail": "Agent indisponible"}

    def test_422_quand_la_question_est_absente(self):
        reponse = client.post("/questions", json={})

        assert reponse.status_code == 422

    @pytest.mark.parametrize("question", ["", "   ", "\n\t "])
    @patch("app.agent_us2.api.repondre")
    def test_422_quand_la_question_est_vide_sans_appeler_lagent(self, mock_repondre, question):
        """Casse si une question vide (ou d'espaces) atteint l'agent : elle coûterait un appel
        LLM pour rien, et le contrat promet un 422 avant tout appel."""
        reponse = client.post("/questions", json={"question": question})

        assert reponse.status_code == 422
        mock_repondre.assert_not_called()
