"""
Tests unitaires pour app/ingestion/acquisition.py

Teste la construction d'URLs de scraping et l'interfaçage avec l'API Opquast.
Utilise des mocks pour éviter les appels réseau réels.
"""

from unittest.mock import MagicMock, patch

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

    @patch("app.ingestion.acquisition.requests.get")
    def test_scrape_rule_extracts_solution_and_controle(self, mock_get):
        """Vérifie que scrape_rule extrait solution et controle du HTML."""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <h2>Solution technique</h2>
            <p>Mettre en place un flux RSS pour les nouveaux contenus</p>
            <h2>Moyen de contrôle</h2>
            <p>Vérifier la présence d'un flux RSS valide</p>
        </html>
        """
        mock_get.return_value = mock_response

        result = scrape_rule("regle-exemple")

        assert isinstance(result, dict)
        assert "solution" in result
        assert "controle" in result
        assert result["solution"] is not None
        assert result["controle"] is not None
 