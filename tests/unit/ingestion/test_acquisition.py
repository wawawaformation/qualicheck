"""
Tests unitaires pour app/ingestion/acquisition.py

Teste la construction d'URLs de scraping et l'interfaçage avec l'API Opquast.
Utilise des mocks pour éviter les appels réseau réels.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.acquisition import build_rule_url, fetch_api, scrape_rule


class TestBuildRuleUrl:
    """Tests de la fonction build_rule_url."""

    def test_build_rule_url_basic(self):
        """Vérifie que l'URL est construite correctement à partir d'un slug."""
        slug = "regle-avec-des-tirets"
        expected_url = "https://checklists.opquast.com/fr/qualite-numerique/regle-avec-des-tirets"

        url = build_rule_url(slug)

        assert url == expected_url


class TestFetchApi:
    """Tests de la fonction fetch_api."""

    @patch("app.ingestion.acquisition.requests.get")
    def test_fetch_api_returns_list(self, mock_get):
        """Vérifie que fetch_api retourne une liste de règles avec les champs attendus."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "number": 1,
                "description": {"fr": "Règle 1"},
                "goal": {"fr": ["Accessibilité"]},
                "metadata": {
                    "Tags": ["HTML"],
                    "Thématiques": ["Contenus"],
                    "Phases projet": ["Intégration"],
                },
                "slug": {"fr": "regle-1"},
            },
            {
                "id": 2,
                "number": 2,
                "description": {"fr": "Règle 2"},
                "goal": {"fr": ["Performance"]},
                "metadata": {
                    "Tags": ["CSS"],
                    "Thématiques": ["Navigation"],
                    "Phases projet": ["Design"],
                },
                "slug": {"fr": "regle-2"},
            },
        ]
        mock_get.return_value = mock_response

        rules = fetch_api()

        assert isinstance(rules, list)
        assert len(rules) == 2
        assert rules[0]["id"] == 1
        assert rules[0]["intitule"] == "Règle 1"
        assert rules[0]["theme"] == "Contenus"
        assert rules[1]["id"] == 2
        assert rules[1]["theme"] == "Navigation"

    @patch("app.ingestion.acquisition.requests.get")
    def test_fetch_api_accepts_empty_tags(self, mock_get):
        """Vérifie que fetch_api accepte une liste Tags vide."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": 3,
                "number": 3,
                "description": {"fr": "Règle 3"},
                "goal": {"fr": ["Sécurité"]},
                "metadata": {
                    "Tags": [],
                    "Thématiques": ["Sécurité"],
                    "Phases projet": ["Développement"],
                },
                "slug": {"fr": "regle-3"},
            },
        ]
        mock_get.return_value = mock_response

        rules = fetch_api()

        assert rules[0]["tags"] == []


class TestScrapeRule:
    """Tests de la fonction scrape_rule."""

    HTML_SIMPLE = """
    <html>
        <body>
            <div class="c-rule-hero__subtitle">Texte explicatif de la règle.</div>
            <div class="c-rule-content">
                <h2 class="c-emoji-target">Objectif</h2>
                <ul><li>Permettre X</li></ul>
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Mettre en place un flux RSS pour les nouveaux contenus</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Vérifier la présence d'un flux RSS valide</p>
            </div>
            <footer><p>SAS au capital de 1000 euros - Lucien Granet</p></footer>
        </body>
    </html>
    """

    HTML_MULTI_BLOCS = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Ne pas utiliser d'ouverture automatique de fenêtre</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Cette bonne pratique est à vérifier manuellement.</p>
                <p>Dans toutes les pages internes du site :</p>
                <ul>
                    <li>Vérifier que la navigation ne provoque pas de popup</li>
                    <li>Vérifier chaque lien externe</li>
                </ul>
            </div>
            <footer><p>SAS au capital de 1000 euros - Lucien Granet</p></footer>
        </body>
    </html>
    """

    HTML_NO_SUBTITLE = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                <p>Solution simple</p>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <p>Contrôle simple</p>
            </div>
        </body>
    </html>
    """

    HTML_NO_CONTENT_DIV = """
    <html><body><p>Page inattendue</p></body></html>
    """

    HTML_TEXT_NODE = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                Utiliser les fonctions natives des éditeurs de contenus.
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                Vérifier que les contenus ne contiennent pas de caractères détournés.
            </div>
        </body>
    </html>
    """

    HTML_DIV_WRAPPER = """
    <html>
        <body>
            <div class="c-rule-content">
                <h2 class="c-emoji-tools">Solution technique</h2>
                <div>Mettre en place une procédure de création de compte.</div>
                <h2 class="c-emoji-check">Moyen de contrôle</h2>
                <div>Vérifier qu'il est possible de créer un compte sans service tiers.</div>
            </div>
        </body>
    </html>
    """

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_extracts_solution_and_controle(self, mock_get):
        """Vérifie l'extraction simple solution + controle + contexte."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_SIMPLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["solution"] == "Mettre en place un flux RSS pour les nouveaux contenus"
        assert result["controle"] == "Vérifier la présence d'un flux RSS valide"
        assert result["contexte"] == "Texte explicatif de la règle."

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_never_captures_footer(self, mock_get):
        """Vérifie que le footer n'est jamais capturé (bornage c-rule-content)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_SIMPLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["solution"] is not None
        assert result["controle"] is not None
        assert "SAS au capital" not in result["solution"]
        assert "SAS au capital" not in result["controle"]

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_collects_multiple_blocks_and_ul(self, mock_get):
        """Vérifie que plusieurs <p> + un <ul> sont tous capturés et concaténés (règle 154)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_MULTI_BLOCS
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        expected_controle = (
            "Cette bonne pratique est à vérifier manuellement.\n"
            "Dans toutes les pages internes du site :\n"
            "- Vérifier que la navigation ne provoque pas de popup\n"
            "- Vérifier chaque lien externe"
        )
        assert result["controle"] == expected_controle

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_contexte_none_when_subtitle_absent(self, mock_get):
        """Vérifie que contexte est None si .c-rule-hero__subtitle est absent."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_NO_SUBTITLE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["contexte"] is None

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_raises_when_content_div_absent(self, mock_get):
        """Vérifie le fail-fast si c-rule-content est absent (structure inattendue)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_NO_CONTENT_DIV
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="c-rule-content"):
            scrape_rule("regle-exemple")

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_captures_direct_text_node_without_p(self, mock_get):
        """Vérifie la capture d'un texte directement enfant, sans <p> englobant
        (structure réelle observée sur la règle 14 Opquast)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_TEXT_NODE
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["solution"] == "Utiliser les fonctions natives des éditeurs de contenus."
        assert result["controle"] == (
            "Vérifier que les contenus ne contiennent pas de caractères détournés."
        )

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_captures_div_wrapped_content(self, mock_get):
        """Vérifie la capture d'un contenu enveloppé dans <div> plutôt que <p>
        (structure réelle observée sur une autre règle Opquast)."""
        mock_response = MagicMock()
        mock_response.text = self.HTML_DIV_WRAPPER
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert result["solution"] == "Mettre en place une procédure de création de compte."
        assert result["controle"] == (
            "Vérifier qu'il est possible de créer un compte sans service tiers."
        )