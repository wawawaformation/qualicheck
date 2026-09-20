"""
Tests unitaires de scripts/clear_opquast_tables.py : la confirmation avant de
vider le référentiel (TRUNCATE sur POSTGRES_DB, 245 règles enrichies dont la
régénération coûte un appel LLM chacune).

Le script est chargé par son chemin (scripts/ n'est pas un paquet). La base et
le vidage sont remplacés : seul le comportement de la confirmation est testé.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CHEMIN = Path(__file__).resolve().parents[3] / "scripts" / "clear_opquast_tables.py"


@pytest.fixture
def script():
    spec = importlib.util.spec_from_file_location("clear_opquast_tables_script", CHEMIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestConfirmer:
    """confirmer(nb_regles, base) : True seulement si l'utilisateur tape « y »."""

    @pytest.mark.parametrize("reponse", ["y", "Y", " y "])
    def test_accepte_y(self, script, reponse):
        with patch("builtins.input", return_value=reponse):
            assert script.confirmer(245, "qualicheck") is True

    @pytest.mark.parametrize("reponse", ["", "n", "N", "oui", "yes", "yy", " "])
    def test_tout_le_reste_refuse(self, script, reponse):
        """Casse si un réflexe (Entrée, « oui ») déclenche un vidage : seul « y » confirme."""
        with patch("builtins.input", return_value=reponse):
            assert script.confirmer(245, "qualicheck") is False

    def test_refuse_sans_terminal_interactif(self, script):
        """Casse si un lancement sans entrée standard (pipe, cron) vide la base par défaut."""
        with patch("builtins.input", side_effect=EOFError):
            assert script.confirmer(245, "qualicheck") is False

    def test_le_message_annonce_le_nombre_de_regles_et_la_base(self, script):
        """Casse si l'utilisateur ne voit pas ce qu'il va effacer, ni sur quelle base."""
        with patch("builtins.input", return_value="n") as saisie:
            script.confirmer(245, "qualicheck_prod")

        invite = saisie.call_args.args[0]
        assert "245" in invite
        assert "qualicheck_prod" in invite


class TestMain:
    """main() : le vidage n'a lieu qu'après confirmation."""

    def _lancer(self, script, reponse, nb_regles=245):
        session = MagicMock()
        session.query.return_value.count.return_value = nb_regles
        with (
            patch.object(script, "setup_logging"),
            patch.object(script, "load_dotenv"),
            patch.object(script, "get_engine"),
            patch.object(script, "Session") as classe_session,
            patch.object(script, "clear_opquast_tables") as vidage,
            patch.dict("os.environ", {"POSTGRES_DB": "qualicheck"}),
            patch("builtins.input", return_value=reponse),
        ):
            classe_session.return_value.__enter__.return_value = session
            script.main()
        return vidage, session

    def test_ne_vide_pas_sans_confirmation(self, script):
        """Casse si le vidage part sans confirmation : c'est tout l'objet de ce test."""
        vidage, _ = self._lancer(script, reponse="n")

        vidage.assert_not_called()

    def test_vide_apres_confirmation(self, script):
        """Casse si la confirmation n'est jamais suivie du vidage (script devenu inutile)."""
        vidage, session = self._lancer(script, reponse="y")

        vidage.assert_called_once_with(session)
