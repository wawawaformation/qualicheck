"""
Tests unitaires pour app/agent_us2/loop.py

Boucle de l'agent US2 (increment A1) — LLM et outil entièrement mockés,
même patron que tests/unit/retrieval/test_decomposition.py. Un seul LLM
configuré (app/agent_us2/config.yml, clé "llm") : pas de sélection de
candidat au niveau de la boucle.
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from langchain_core.messages import ToolMessage

from app.agent_us2 import loop
from app.agent_us2.loop import repondre

CONFIG_STUB = {
    "llm": {
        "env_var_endpoint": "AZURE_AI_ENDPOINT",
        "env_var_api_key": "AZURE_AI_API_KEY",
        "env_var_deployment": "AZURE_MODEL_DEEPSEEK_FLASH",
        "temperature": 0,
        "prix_entree_par_million": 0.15,
        "prix_sortie_par_million": 0.60,
    },
    "agent_a1": {"max_tours_securite": 10},
}


def _ai_message(content: str, tool_calls: list, input_tokens: int, output_tokens: int):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    message.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return message


class TestRepondre:
    """Tests de la boucle repondre()."""

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reponse_directe_sans_appel_outil(self, mock_llm_class, mock_load_config):
        """Le modèle répond directement, sans appeler l'outil — un seul tour."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "Réponse directe.", tool_calls=[], input_tokens=100, output_tokens=20
        )

        resultat = repondre("Une question ?")

        assert resultat.reponse == "Réponse directe."
        assert resultat.nb_tours == 1
        assert resultat.regles_citees == []
        assert resultat.tokens_entree == 100
        assert resultat.tokens_sortie == 20
        # 100 tokens entrée x 0.15 €/M + 20 tokens sortie x 0.60 €/M
        assert resultat.cout_euros_estime == pytest.approx(0.000027)

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reponse_apres_appel_outil(self, mock_llm_class, mock_load_config):
        """Le modèle appelle l'outil, obtient un résultat, puis répond."""
        mock_outil = MagicMock()
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            _ai_message(
                "",
                tool_calls=[
                    {
                        "name": "rechercher_regles",
                        "args": {"mots_cles": "prix TTC"},
                        "id": "call_1",
                    }
                ],
                input_tokens=50,
                output_tokens=10,
            ),
            _ai_message(
                "Le prix doit être TTC (règle 56).",
                tool_calls=[],
                input_tokens=150,
                output_tokens=30,
            ),
        ]
        mock_outil.invoke.return_value = json.dumps(
            {
                "resultats": [{"numero": 56, "intitule": "Prix TTC", "solution": "..."}],
                "total_trouve": 1,
            }
        )

        with patch.dict(loop.OUTILS, {"rechercher_regles": mock_outil}):
            resultat = repondre("Faut-il le prix TTC ?")

        assert resultat.nb_tours == 2
        assert resultat.regles_citees == [{"numero": 56, "intitule": "Prix TTC"}]
        assert resultat.tokens_entree == 200
        assert resultat.tokens_sortie == 40
        mock_outil.invoke.assert_called_once_with({"mots_cles": "prix TTC"})

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_construit_le_client_avec_temperature_zero(self, mock_llm_class, mock_load_config):
        """Décodage glouton (temperature=0) — même raison que le retrieval."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "ok", tool_calls=[], input_tokens=1, output_tokens=1
        )

        repondre("question")

        assert mock_llm_class.call_args.kwargs["temperature"] == 0

    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_filet_de_securite_apres_max_tours(self, mock_llm_class, mock_load_config):
        """Le modèle appelle l'outil en boucle — filet de sécurité après max_tours_securite."""
        mock_outil = MagicMock()
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _ai_message(
            "",
            tool_calls=[{"name": "rechercher_regles", "args": {"mots_cles": "x"}, "id": "c"}],
            input_tokens=10,
            output_tokens=5,
        )
        mock_outil.invoke.return_value = json.dumps({"resultats": [], "total_trouve": 0})

        with patch.dict(loop.OUTILS, {"rechercher_regles": mock_outil}):
            resultat = repondre("question sans fin")

        assert resultat.nb_tours == 10
        assert "n'a pas conclu" in resultat.reponse

    @patch("tenacity.nap.time.sleep")
    @patch("app.agent_us2.loop.load_config")
    @patch("app.agent_us2.loop.ChatOpenAI")
    def test_reessaie_puis_reussit(self, mock_llm_class, mock_load_config, mock_sleep):
        """Réessaie après échec transitoire, puis réussit (3 tentatives max)."""
        mock_load_config.return_value = CONFIG_STUB
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.bind_tools.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _ai_message("ok", tool_calls=[], input_tokens=5, output_tokens=5),
        ]

        resultat = repondre("question")

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat.reponse == "ok"


# ---------------------------------------------------------------------------
# A4 — deux outils (rechercher_regles, lire_regle). Ces tests utilisent les
# VRAIS outils : seuls le LLM et l'appel réseau (httpx.get) sont remplacés, ce
# qui vérifie le contrat réel entre la boucle et le format JSON des outils.
# ---------------------------------------------------------------------------

URL_API = "http://localhost:9999"
REGLE_116 = {
    "numero": 116,
    "intitule": "Chaque image décorative est dotée d'une alternative textuelle appropriée.",
    "theme": "Contenus",
    "contexte": None,
    "solution": "Renseigner un attribut alt vide.",
    "controle": "Vérifier l'attribut alt.",
    "strategie_analyse": "dom",
    "outils": [],
    "strategie_justification": None,
    "strategie_source": "expert",
    "guide_analyse": "Inspecter les balises img.",
    "objectifs": [],
    "tags": [],
}


def _http(statut: int, corps) -> httpx.Response:
    """Vraie réponse httpx (raise_for_status réel), pas un MagicMock permissif."""
    return httpx.Response(statut, json=corps, request=httpx.Request("GET", URL_API))


def _appel(nom: str, args: dict, identifiant: str = "call_1") -> dict:
    return {"name": nom, "args": args, "id": identifiant}


@pytest.fixture
def llm(monkeypatch):
    """LLM remplacé ; les outils et la boucle restent réels."""
    monkeypatch.setattr("app.agent_us2.loop.load_config", lambda: CONFIG_STUB)
    monkeypatch.setattr(
        "app.agent_us2.tools.load_config",
        lambda: {"api_regles": {"env_var_url": "API_REGLES_URL_DEV"}},
    )
    monkeypatch.setenv("API_REGLES_URL_DEV", URL_API)
    instance = MagicMock()
    instance.bind_tools.return_value = instance
    monkeypatch.setattr("app.agent_us2.loop.ChatOpenAI", MagicMock(return_value=instance))
    return instance


class TestRepondreAvecDeuxOutils:
    """A4 : la boucle sait aiguiller, compter et signaler avec deux outils."""

    def test_donne_les_deux_outils_au_llm(self, llm):
        """Casse si lire_regle n'est pas proposé au modèle : il ne pourrait jamais l'appeler."""
        llm.invoke.return_value = _ai_message("ok", [], 1, 1)

        repondre("question")

        outils_proposes = llm.bind_tools.call_args.args[0]
        assert {o.name for o in outils_proposes} == {"rechercher_regles", "lire_regle"}

    def test_appelle_lire_regle_quand_le_llm_le_demande(self, llm):
        """Casse si l'aiguillage reste câblé sur rechercher_regles : l'URL serait /regles?q=."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("lire_regle", {"numero": 116})], 1, 1),
            _ai_message("Voir la règle 116.", [], 1, 1),
        ]

        with patch("app.agent_us2.tools.httpx.get", return_value=_http(200, REGLE_116)) as get:
            repondre("Que dit la règle 116 ?")

        get.assert_called_once()
        assert get.call_args.args[0] == "http://localhost:9999/regles/116"

    def test_une_regle_lue_compte_comme_citee(self, llm):
        """Casse si la boucle ne reconnaît que le format « resultats » de la recherche :
        la réponse serait classée aucune_regle_pertinente alors qu'elle cite la règle 116."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("lire_regle", {"numero": 116})], 1, 1),
            _ai_message("Voir la règle 116.", [], 1, 1),
        ]

        with patch("app.agent_us2.tools.httpx.get", return_value=_http(200, REGLE_116)):
            resultat = repondre("Que dit la règle 116 ?")

        assert resultat.regles_citees == [
            {"numero": 116, "intitule": REGLE_116["intitule"]}
        ]
        assert resultat.panne_outil is False

    def test_une_panne_5xx_est_signalee_dans_le_resultat(self, llm):
        """Casse si la panne est avalée : l'API classerait la réponse « rien ne correspond »."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("rechercher_regles", {"mots_cles": "images"})], 1, 1),
            _ai_message("Le service est indisponible.", [], 1, 1),
        ]
        panne = _http(503, {"detail": "Service indisponible"})

        with patch("app.agent_us2.tools.httpx.get", return_value=panne):
            resultat = repondre("Comment traiter les images ?")

        assert resultat.panne_outil is True
        assert resultat.regles_citees == []

    def test_une_regle_inconnue_nest_pas_une_panne(self, llm):
        """Casse si tout statut d'erreur est traité comme une panne : un 404 est un résultat
        normal (la règle n'existe pas), pas un service défaillant."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("lire_regle", {"numero": 999})], 1, 1),
            _ai_message("Cette règle n'existe pas.", [], 1, 1),
        ]
        inconnue = _http(404, {"detail": "Règle 999 inconnue"})

        with patch("app.agent_us2.tools.httpx.get", return_value=inconnue):
            resultat = repondre("Que dit la règle 999 ?")

        assert resultat.panne_outil is False
        assert resultat.regles_citees == []

    def test_une_panne_rattrapee_reste_signalee_et_garde_les_regles(self, llm):
        """Casse si le drapeau est remis à zéro par un appel suivant réussi : la panne a eu
        lieu, c'est à l'API (avec les règles citées) de décider du statut final."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("rechercher_regles", {"mots_cles": "images"}, "c1")], 1, 1),
            _ai_message("", [_appel("lire_regle", {"numero": 116}, "c2")], 1, 1),
            _ai_message("Voir la règle 116.", [], 1, 1),
        ]
        reponses = [_http(503, {"detail": "Service indisponible"}), _http(200, REGLE_116)]

        with patch("app.agent_us2.tools.httpx.get", side_effect=reponses):
            resultat = repondre("Comment traiter les images ?")

        assert resultat.panne_outil is True
        assert resultat.regles_citees == [
            {"numero": 116, "intitule": REGLE_116["intitule"]}
        ]

    def test_un_outil_inconnu_est_signale_a_lagent_sans_planter(self, llm):
        """Casse si un nom d'outil inventé par le LLM lève une exception (KeyError) : la
        question échouerait en 503 au lieu de laisser l'agent se rattraper."""
        llm.invoke.side_effect = [
            _ai_message("", [_appel("outil_inexistant", {})], 1, 1),
            _ai_message("Je n'ai pas cet outil.", [], 1, 1),
        ]

        resultat = repondre("question")

        assert resultat.reponse == "Je n'ai pas cet outil."
        assert resultat.panne_outil is False
        messages_du_dernier_tour = llm.invoke.call_args_list[-1].args[0]
        retour_outil = next(m for m in messages_du_dernier_tour if isinstance(m, ToolMessage))
        assert json.loads(retour_outil.content) == {
            "statut": 404,
            "erreur": "Outil inconnu : outil_inexistant",
        }
