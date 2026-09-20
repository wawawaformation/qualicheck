"""
Tests unitaires pour app/agent_us2/tools.py

Outil recherche_regles — appel HTTP mocké, aucun réseau réel. L'URL de
l'API des règles vient de .env (API_REGLES_URL_DEV, nom déclaré dans
app/agent_us2/config.yml), pas d'une valeur figée en config ni d'un
import de app.api_regles.config — l'URL diffère par environnement
(dev/staging/prod), .env est le bon endroit, pas un fichier versionné.
"""

import json
from unittest.mock import MagicMock, patch

from app.agent_us2.tools import rechercher_regles


def _config_stub() -> dict:
    return {"api_regles": {"env_var_url": "API_REGLES_URL_DEV"}}


class TestRechercherRegles:
    """Tests de l'outil recherche_regles."""

    @patch("app.agent_us2.tools.httpx.get")
    @patch("app.agent_us2.tools.load_config")
    def test_formate_les_resultats_trouves(self, mock_load_config, mock_get):
        mock_load_config.return_value = _config_stub()
        mock_reponse = MagicMock()
        mock_reponse.json.return_value = [
            {"numero": 56, "intitule": "Prix TTC", "solution": "Afficher le prix TTC."},
        ]
        mock_get.return_value = mock_reponse

        resultat = json.loads(rechercher_regles.invoke({"mots_cles": "prix TTC"}))

        assert resultat["total_trouve"] == 1
        assert resultat["resultats"] == [
            {"numero": 56, "intitule": "Prix TTC", "solution": "Afficher le prix TTC."}
        ]

    @patch("app.agent_us2.tools.httpx.get")
    @patch("app.agent_us2.tools.load_config")
    def test_tronque_au_dela_de_max_resultats(self, mock_load_config, mock_get):
        mock_load_config.return_value = _config_stub()
        mock_reponse = MagicMock()
        mock_reponse.json.return_value = [
            {"numero": i, "intitule": f"Règle {i}", "solution": "x"} for i in range(1, 16)
        ]
        mock_get.return_value = mock_reponse

        resultat = json.loads(rechercher_regles.invoke({"mots_cles": "x"}))

        assert resultat["total_trouve"] == 15
        assert len(resultat["resultats"]) == 10

    @patch.dict("os.environ", {"API_REGLES_URL_DEV": "http://localhost:9999"})
    @patch("app.agent_us2.tools.httpx.get")
    @patch("app.agent_us2.tools.load_config")
    def test_appelle_lurl_lue_depuis_env(self, mock_load_config, mock_get):
        """L.URL vient de .env (API_REGLES_URL_DEV) — diffère par environnement."""
        mock_load_config.return_value = _config_stub()
        mock_reponse = MagicMock()
        mock_reponse.json.return_value = []
        mock_get.return_value = mock_reponse

        rechercher_regles.invoke({"mots_cles": "accessibilité"})

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:9999/regles"
        assert kwargs["params"] == {"q": "accessibilité"}
