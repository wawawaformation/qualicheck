"""
Tests unitaires pour app/ingestion/aggregation.py

Teste la fusion de données acquises (API + scraping) en objets Rule validés,
et la composition d'une collection Rules complètement validée.
"""

from app.ingestion.aggregation import Rule, Rules, aggregate_rules


class TestRule:
    """Tests de la classe Rule (modèle de domaine)."""

    def test_regle_creation_with_all_fields(self):
        """Crée une Rule avec tous les champs requis."""
        regle = Rule(
            id=1,
            number=1,
            intitule="Titule de la règle",
            solution="Mettre en place X",
            controle="Vérifier Y",
            objectifs=["Accessibilité"],
            tags=["HTML"],
            phases=["Intégration"],
            slug="regle-avec-des-tirets",
        )

        assert regle.id == 1
        assert regle.number == 1
        assert regle.intitule == "Titule de la règle"
        assert regle.solution == "Mettre en place X"
        assert regle.controle == "Vérifier Y"
        assert regle.objectifs == ["Accessibilité"]
        assert regle.tags == ["HTML"]
        assert regle.phases == ["Intégration"]
        assert regle.slug == "regle-avec-des-tirets"

    def test_regle_fails_if_intitule_empty(self):
        """Lève une erreur si intitulé vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_solution_empty(self):
        """Lève une erreur si solution vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                solution="",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_controle_empty(self):
        """Lève une erreur si contrôle vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                solution="Solution",
                controle="",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_objectifs_empty(self):
        """Lève une erreur si liste d'objectifs vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                solution="Solution",
                controle="Contrôle",
                objectifs=[],
                tags=["Tag"],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_tags_empty(self):
        """Lève une erreur si liste de tags vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=[],
                phases=["Phase"],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass

    def test_regle_fails_if_phases_empty(self):
        """Lève une erreur si liste de phases vide."""
        try:
            Rule(
                id=1,
                number=1,
                intitule="Intitulé",
                solution="Solution",
                controle="Contrôle",
                objectifs=["Objectif"],
                tags=["Tag"],
                phases=[],
                slug="slug",
            )
            assert False, "Should have raised an error"
        except ValueError:
            pass


class TestRules:
    """Tests de la classe Rules (collection)."""

    def test_regles_creation_from_regle_list(self):
        """Crée une collection Rules à partir d'une liste de Regle."""
        regle1 = Rule(
            id=1,
            number=1,
            intitule="Règle 1",
            solution="Solution 1",
            controle="Contrôle 1",
            objectifs=["Objectif 1"],
            tags=["Tag 1"],
            phases=["Phase 1"],
            slug="regle-1",
        )
        regle2 = Rule(
            id=2,
            number=2,
            intitule="Règle 2",
            solution="Solution 2",
            controle="Contrôle 2",
            objectifs=["Objectif 2"],
            tags=["Tag 2"],
            phases=["Phase 2"],
            slug="regle-2",
        )

        regles = Rules([regle1, regle2])

        assert len(regles.regles) == 2
        assert regles.regles[0].number == 1
        assert regles.regles[1].number == 2

    def test_regles_fails_if_empty_list(self):
        """Lève une erreur si collection vide."""
        try:
            Rules([])
            assert False, "Should have raised an error"
        except ValueError:
            pass


class TestAggregateRules:
    """Tests de la fonction aggregate_rules."""

    def test_aggregate_rules_from_acquisition_output(self):
        """Agrège des règles acquises (dicts API + scraping) en Rules validé."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                "solution": "Solution 1",
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            },
            {
                "id": 2,
                "number": 2,
                "intitule": "Règle 2",
                "solution": "Solution 2",
                "controle": "Contrôle 2",
                "objectifs": ["Performance"],
                "tags": ["CSS"],
                "phases": ["Design"],
                "slug": "regle-2",
            },
        ]

        regles = aggregate_rules(acquired_rules)

        assert isinstance(regles, Rules)
        assert len(regles.regles) == 2
        assert regles.regles[0].number == 1
        assert regles.regles[0].intitule == "Règle 1"
        assert regles.regles[1].number == 2

    def test_aggregate_rules_fails_if_missing_intitule(self):
        """Lève une erreur si champ 'intitule' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                # intitule manquant
                "solution": "Solution 1",
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass

    def test_aggregate_rules_fails_if_missing_solution(self):
        """Lève une erreur si champ 'solution' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                # solution manquante
                "controle": "Contrôle 1",
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass

    def test_aggregate_rules_fails_if_missing_controle(self):
        """Lève une erreur si champ 'controle' manquant."""
        acquired_rules = [
            {
                "id": 1,
                "number": 1,
                "intitule": "Règle 1",
                "solution": "Solution 1",
                # controle manquant
                "objectifs": ["Accessibilité"],
                "tags": ["HTML"],
                "phases": ["Intégration"],
                "slug": "regle-1",
            }
        ]

        try:
            aggregate_rules(acquired_rules)
            assert False, "Should have raised an error"
        except (KeyError, ValueError):
            pass
