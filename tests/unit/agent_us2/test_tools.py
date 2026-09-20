"""
Tests unitaires pour app/agent_us2/tools.py

Outils rechercher_regles et lire_regle — appel HTTP mocké, aucun réseau réel. L'URL de
l'API des règles vient de .env (API_REGLES_URL_DEV, nom déclaré dans
app/agent_us2/config.yml), pas d'une valeur figée en config ni d'un
import de app.api_regles.config — l'URL diffère par environnement
(dev/staging/prod), .env est le bon endroit, pas un fichier versionné.
"""

import json
import logging
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.agent_us2.tools import lire_regle, rechercher_regles


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
            {
                "numero": 56,
                "intitule": "Prix TTC",
                "solution": "Afficher le prix TTC.",
                "solution_tronquee": False,
            }
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


# ---------------------------------------------------------------------------
# A4 — contrat de résilience commun aux deux outils : jamais d'exception vers
# l'agent, toujours un résultat {"statut": ..., "erreur": ...}. Les doubles
# reflètent la réalité : vraies httpx.Response (raise_for_status réel) et
# vraies exceptions httpx, pas de MagicMock qui accepterait n'importe quoi.
# ---------------------------------------------------------------------------

URL_API = "http://localhost:9999"

# Une règle complète, avec les 13 champs exposés par GET /regles/{numero}
# (app/api_regles/schemas.py::RegleRead) et une solution bien plus longue que
# les 300 caractères de la recherche.
SOLUTION_LONGUE = "Renseigner un attribut alt vide pour chaque image décorative. " * 10
REGLE_116 = {
    "numero": 116,
    "intitule": "Chaque image décorative est dotée d'une alternative textuelle appropriée.",
    "theme": "Contenus",
    "contexte": "Images purement décoratives.",
    "solution": SOLUTION_LONGUE,
    "controle": "Vérifier que l'attribut alt est présent et vide.",
    "strategie_analyse": "dom",
    "outils": ["validateur HTML"],
    "strategie_justification": None,
    "strategie_source": "expert",
    "guide_analyse": "Inspecter chaque balise img décorative.",
    "objectifs": ["accessibilité"],
    "tags": ["images", "alt"],
}


@pytest.fixture
def env_api(monkeypatch):
    """URL de l'API des règles lue depuis l'environnement, comme en production."""
    monkeypatch.setattr("app.agent_us2.tools.load_config", _config_stub)
    monkeypatch.setenv("API_REGLES_URL_DEV", URL_API)


def _reponse(statut: int, corps: dict | list | None = None, texte: str = "") -> httpx.Response:
    """Vraie réponse httpx : raise_for_status() se comporte comme en réel."""
    requete = httpx.Request("GET", URL_API)
    if corps is not None:
        return httpx.Response(statut, json=corps, request=requete)
    return httpx.Response(statut, text=texte, request=requete)


class TestLireRegle:
    """Outil lire_regle : une règle entière, désignée par son numéro."""

    def test_renvoie_la_regle_complete_sans_troncature(self, env_api):
        """Casse si un champ est perdu ou si la solution est coupée comme en recherche."""
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(200, REGLE_116)):
            resultat = json.loads(lire_regle.invoke({"numero": 116}))

        assert resultat == REGLE_116
        assert len(resultat["solution"]) == len(SOLUTION_LONGUE) > 300

    def test_appelle_la_route_du_numero(self, env_api):
        """Casse si l'outil appelle la mauvaise URL (ex. la recherche au lieu du numéro)."""
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(200, REGLE_116)) as get:
            lire_regle.invoke({"numero": 116})

        get.assert_called_once()
        assert get.call_args.args[0] == "http://localhost:9999/regles/116"

    def test_regle_inconnue_renvoie_le_404_a_lagent(self, env_api):
        """Casse si un 404 devient une exception ou perd son code : l'agent doit savoir."""
        corps = {"detail": "Règle 999 inconnue"}
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(404, corps)):
            resultat = json.loads(lire_regle.invoke({"numero": 999}))

        assert resultat == {"statut": 404, "erreur": "Règle 999 inconnue"}

    @pytest.mark.parametrize("statut", [422, 500, 502, 503])
    def test_statut_derreur_de_lapi_transmis_tel_quel(self, env_api, statut):
        """Casse si une panne lève une exception ou est déguisée en « règle inconnue »."""
        corps = {"detail": "Service indisponible"}
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(statut, corps)):
            resultat = json.loads(lire_regle.invoke({"numero": 116}))

        assert resultat == {"statut": statut, "erreur": "Service indisponible"}

    def test_panne_sans_corps_json_renvoie_quand_meme_le_statut(self, env_api):
        """Un proxy peut répondre 502 en HTML : l'agent reçoit le statut, pas une exception."""
        with patch(
            "app.agent_us2.tools.httpx.get", return_value=_reponse(502, texte="Bad Gateway")
        ):
            resultat = json.loads(lire_regle.invoke({"numero": 116}))

        assert resultat["statut"] == 502
        assert isinstance(resultat["erreur"], str) and resultat["erreur"]

    @pytest.mark.parametrize(
        "erreur_reseau",
        [httpx.ReadTimeout("délai dépassé"), httpx.ConnectError("connexion refusée")],
    )
    def test_service_sans_reponse_renvoie_503(self, env_api, erreur_reseau):
        """Casse si un délai dépassé ou une connexion impossible remonte en exception."""
        with patch("app.agent_us2.tools.httpx.get", side_effect=erreur_reseau):
            resultat = json.loads(lire_regle.invoke({"numero": 116}))

        assert resultat["statut"] == 503
        assert isinstance(resultat["erreur"], str) and resultat["erreur"]


class TestRechercherReglesResilienceEtTroncature:
    """A4 : la recherche signale ce qu'elle coupe et adopte le même contrat de résilience."""

    def test_marque_les_solutions_tronquees_a_la_limite_de_300(self, env_api):
        """Casse si le marqueur est faux à la frontière : 300 tient, 301 est coupée."""
        regles = [
            {"numero": 1, "intitule": "Longue", "solution": "a" * 301},
            {"numero": 2, "intitule": "Pile", "solution": "b" * 300},
            {"numero": 3, "intitule": "Courte", "solution": "c"},
        ]
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(200, regles)):
            resultat = json.loads(rechercher_regles.invoke({"mots_cles": "x"}))

        par_numero = {r["numero"]: r for r in resultat["resultats"]}
        assert par_numero[1]["solution_tronquee"] is True
        assert len(par_numero[1]["solution"]) == 300
        assert par_numero[2]["solution_tronquee"] is False
        assert par_numero[2]["solution"] == "b" * 300
        assert par_numero[3]["solution_tronquee"] is False

    @pytest.mark.parametrize("statut", [500, 503])
    def test_panne_de_lapi_renvoyee_a_lagent_sans_exception(self, env_api, statut):
        """Casse si raise_for_status() fuit encore (comportement d'A1) ou si la panne
        est présentée comme une liste vide (« rien ne correspond »)."""
        corps = {"detail": "Service indisponible"}
        with patch("app.agent_us2.tools.httpx.get", return_value=_reponse(statut, corps)):
            resultat = json.loads(rechercher_regles.invoke({"mots_cles": "images"}))

        assert resultat == {"statut": statut, "erreur": "Service indisponible"}

    def test_service_sans_reponse_renvoie_503(self, env_api):
        """Casse si un délai dépassé remonte en exception."""
        with patch("app.agent_us2.tools.httpx.get", side_effect=httpx.ReadTimeout("délai dépassé")):
            resultat = json.loads(rechercher_regles.invoke({"mots_cles": "images"}))

        assert resultat["statut"] == 503
        assert isinstance(resultat["erreur"], str) and resultat["erreur"]


class TestReponseIllisibleEtJournalisation:
    """A4 : les cas où le contrat « jamais d'exception » pouvait encore fuir ou se taire."""

    @pytest.mark.parametrize(
        "outil, args",
        [(rechercher_regles, {"mots_cles": "x"}), (lire_regle, {"numero": 116})],
    )
    def test_reponse_200_illisible_renvoie_502(self, env_api, outil, args):
        """Casse si un 200 au corps non JSON (proxy, page d'erreur) fait fuir une exception :
        c'est une mauvaise réponse d'un service amont, donc 502."""
        with patch(
            "app.agent_us2.tools.httpx.get", return_value=_reponse(200, texte="<html>oops</html>")
        ):
            resultat = json.loads(outil.invoke(args))

        assert resultat["statut"] == 502
        assert isinstance(resultat["erreur"], str) and resultat["erreur"]

    @pytest.mark.parametrize(
        "comportement",
        [
            {"return_value": _reponse(503, {"detail": "Service indisponible"})},
            {"side_effect": httpx.ReadTimeout("délai dépassé")},
        ],
    )
    def test_une_panne_est_journalisee_en_avertissement(self, env_api, caplog, comportement):
        """Casse si la panne est avalée sans trace : l'exploitant ne verrait plus rien."""
        with caplog.at_level(logging.WARNING, logger="app.agent_us2.tools"):
            with patch("app.agent_us2.tools.httpx.get", **comportement):
                lire_regle.invoke({"numero": 116})

        assert any(
            r.name == "app.agent_us2.tools" and r.levelno == logging.WARNING
            for r in caplog.records
        )
