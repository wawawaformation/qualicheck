# Enrich Again Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un script `enrich_again` qui rappelle le LLM d'enrichissement
uniquement sur les règles marquées `review_status = 'a_revoir'`/`'invalide'`,
en tenant compte de leur `review_note`, puis vide ces champs de revue une
fois la correction appliquée.

**Architecture:** `llm_client.py` est étendu (pas dupliqué) avec des
paramètres optionnels rétrocompatibles pour injecter le contexte de revue
dans le prompt existant. Un nouveau module `app/ingestion/enrich_again.py`
porte la logique de sélection des règles, le nettoyage des champs de revue,
et l'orchestration (commit par règle, fail-fast comme le reste du pipeline).
`scripts/enrich_again.py` est le point d'entrée CLI, sur le modèle de
`scripts/ingestion.py`.

**Tech Stack:** Python, SQLAlchemy, Pydantic, LangChain (`ChatOpenAI`),
`tenacity` (retry), pytest.

## Global Constraints

- Spec source : `conception/2_ingestion/J_chantier_enrich_again.md` (validée,
  commit `cf9198a`) — toute valeur exacte de ce plan en est extraite
  verbatim.
- Sélection SQL : `regle` où `review_status IS NOT NULL AND review_status != 'valide'`.
- Un seul fichier de prompt (`app/ingestion/prompts/enrich_rule.md`) — jamais
  de duplication. La section de revue est injectée par le code, pas par un
  second fichier.
- `strategie_source` écrit par ce chemin : `"ia_reingest"`. Le chemin
  d'ingestion normale garde `"ia_import"` par défaut — **rétrocompatibilité
  stricte** : tout appel existant à `load_prompt(rule)` ou
  `enrich_single_rule(rule)` sans les nouveaux paramètres doit produire un
  résultat strictement identique à aujourd'hui.
- `prompt_version` enregistré : celui du frontmatter courant de
  `enrich_rule.md` (`load_prompt_version()`, déjà existant) — pas de version
  dédiée.
- Retry LLM : réutiliser tel quel le décorateur `@retry` déjà présent sur
  `enrich_single_rule` (3 tentatives, backoff exponentiel 2/4/8s) — ne pas le
  retoucher.
- Pas de `LIMIT=`, pas de confirmation interactive dans `scripts/enrich_again.py`.
- **Commit par règle**, jamais un commit global pour tout le batch — décision
  actée, ne pas "harmoniser" vers le style `store_rules()` (commit unique).
  Comportement fail-fast : si une règle échoue après ses 3 tentatives,
  l'exception se propage et arrête le script — les règles précédentes,
  déjà commitées individuellement, restent acquises.
- **Aucune tâche de ce plan ne doit exécuter `scripts/enrich_again.py` ou
  `make enrich-again` pour de vrai** contre la base réelle (`qualicheck`) —
  cela déclencherait un appel LLM payant réel sur les 11 règles actuellement
  marquées `a_revoir`. Toute vérification se fait via les tests
  automatisés (unitaires avec mocks, intégration contre `qualicheck_test`).
  Le lancement réel est un acte délibéré de David, hors de ce plan.
- Hors périmètre (ne pas implémenter dans ce plan) : décision sur la règle
  96, prompt V6 complet (few-shot `&`, reformulation R2.4), invalidation
  automatique post-ré-ingestion, table d'historique des revues.

---

### Task 1: Étendre `llm_client.py` pour le contexte de revue

**Files:**

- Modify: `app/ingestion/llm_client.py:83-142` (`load_prompt`, `enrich_single_rule`)
- Test: `tests/unit/ingestion/test_enrichment.py` (nouvelle classe `TestEnrichAgainPromptContext`)

**Interfaces:**

- Consumes : rien de nouveau (fonctions déjà existantes, signatures étendues).
- Produces : `LLMClient.load_prompt(rule, review_note=None, current_strategie_analyse=None)`
  et `LLMClient.enrich_single_rule(rule, review_note=None, current_strategie_analyse=None, strategie_source="ia_import")`
  — consommés par la Task 3 (`enrich_again()`).

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à la fin de `tests/unit/ingestion/test_enrichment.py` :

```python
class TestEnrichAgainPromptContext:
    """Vérifie l'injection du contexte de revue humaine dans le prompt."""

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_load_prompt_without_review_note_unchanged(self, mock_azure_llm):
        """Sans review_note, le prompt ne contient aucune section de revue."""
        mock_azure_llm.return_value = MagicMock()
        client = LLMClient()
        rule = Rule(
            id=1, number=1, intitule="Titre", theme="Thème",
            solution="Solution", controle="Contrôle",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"], slug="regle-1",
        )

        prompt = client.load_prompt(rule)

        assert "Contexte de revue humaine" not in prompt
        assert prompt.count(
            "Génère maintenant une réponse JSON pour la règle ci-dessus."
        ) == 1

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_load_prompt_with_review_note_adds_context_section(self, mock_azure_llm):
        """Avec review_note, la section de revue apparaît avant l'instruction finale."""
        mock_azure_llm.return_value = MagicMock()
        client = LLMClient()
        rule = Rule(
            id=65, number=65, intitule="Titre", theme="Thème",
            solution="Solution", controle="Contrôle",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"], slug="regle-65",
        )

        prompt = client.load_prompt(
            rule,
            review_note="Devrait être vision&statique (ET), pas vision+statique.",
            current_strategie_analyse="vision+statique",
        )

        assert "Contexte de revue humaine" in prompt
        assert 'strategie_analyse = "vision+statique"' in prompt
        assert "Devrait être vision&statique (ET), pas vision+statique." in prompt
        section_index = prompt.index("Contexte de revue humaine")
        instruction_index = prompt.index(
            "Génère maintenant une réponse JSON pour la règle ci-dessus."
        )
        assert section_index < instruction_index

    @patch("app.ingestion.llm_client.ChatOpenAI")
    def test_enrich_single_rule_with_review_note_writes_ia_reingest(self, mock_azure_llm):
        """enrich_single_rule avec review_note écrit strategie_source='ia_reingest'
        et transmet le contexte de revue au prompt envoyé au LLM."""
        mock_llm_instance = MagicMock()
        mock_azure_llm.return_value = mock_llm_instance
        mock_response = MagicMock()
        mock_response.content = (
            '{"strategie_analyse": "vision&statique", '
            '"strategie_justification": "Les deux vérifications sont indépendantes.", '
            '"guide_analyse": "Étape 1 [vision] : ... Étape 2 [statique] : ..."}'
        )
        mock_response.usage_metadata = {"input_tokens": 120, "output_tokens": 60}
        mock_llm_instance.invoke.return_value = mock_response

        client = LLMClient()
        rule = Rule(
            id=65, number=65, intitule="Titre", theme="Thème",
            solution="Solution", controle="Contrôle",
            objectifs=["Obj"], tags=["Tag"], phases=["Phase"], slug="regle-65",
        )

        enriched = client.enrich_single_rule(
            rule,
            review_note="Devrait être vision&statique (ET).",
            current_strategie_analyse="vision+statique",
            strategie_source="ia_reingest",
        )

        assert enriched.strategie_analyse == "vision&statique"
        assert enriched.strategie_source == "ia_reingest"

        sent_prompt = mock_llm_instance.invoke.call_args[0][0]
        assert "Devrait être vision&statique (ET)." in sent_prompt
```

- [ ] **Step 2: Vérifier que les tests échouent**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py::TestEnrichAgainPromptContext -v`
Expected: `FAILED` — `TypeError: load_prompt() got an unexpected keyword argument 'review_note'` (et équivalent pour `enrich_single_rule`).

- [ ] **Step 3: Étendre `load_prompt()`**

Dans `app/ingestion/llm_client.py`, remplacer :

```python
    def load_prompt(self, rule: Rule) -> str:
        """
        Charge le prompt depuis prompts/enrich_rule.md et remplace les placeholders.

        Remplacement manuel (pas de str.format()) car le prompt contient des
        accolades JSON littérales dans les exemples few-shot, qui entreraient
        en conflit avec la syntaxe de formatage de PromptTemplate.
        """
        prompt_text = _read_prompt_file()
        if prompt_text.startswith("---\n"):
            _, _, prompt_text = prompt_text.split("---", 2)
            prompt_text = prompt_text.lstrip("\n")

        values = {
            "intitule": rule.intitule,
            "contexte": rule.contexte or "(non disponible)",
            "solution": rule.solution,
            "controle": rule.controle,
            "objectifs": ", ".join(rule.objectifs),
            "tags": ", ".join(rule.tags),
            "phases": ", ".join(rule.phases),
        }
        for placeholder in PROMPT_PLACEHOLDERS:
            prompt_text = prompt_text.replace(f"{{{placeholder}}}", values[placeholder])

        return prompt_text
```

par :

```python
    def load_prompt(
        self,
        rule: Rule,
        review_note: str | None = None,
        current_strategie_analyse: str | None = None,
    ) -> str:
        """
        Charge le prompt depuis prompts/enrich_rule.md et remplace les placeholders.

        Remplacement manuel (pas de str.format()) car le prompt contient des
        accolades JSON littérales dans les exemples few-shot, qui entreraient
        en conflit avec la syntaxe de formatage de PromptTemplate.

        Si review_note est fourni (utilisé par enrich_again), insère une
        section "Contexte de revue humaine" juste avant l'instruction finale
        du prompt — comportement strictement inchangé sinon.
        """
        prompt_text = _read_prompt_file()
        if prompt_text.startswith("---\n"):
            _, _, prompt_text = prompt_text.split("---", 2)
            prompt_text = prompt_text.lstrip("\n")

        values = {
            "intitule": rule.intitule,
            "contexte": rule.contexte or "(non disponible)",
            "solution": rule.solution,
            "controle": rule.controle,
            "objectifs": ", ".join(rule.objectifs),
            "tags": ", ".join(rule.tags),
            "phases": ", ".join(rule.phases),
        }
        for placeholder in PROMPT_PLACEHOLDERS:
            prompt_text = prompt_text.replace(f"{{{placeholder}}}", values[placeholder])

        if review_note is not None:
            review_section = (
                "\n## Contexte de revue humaine\n\n"
                "Cette règle a déjà été classée une première fois avec le résultat suivant :\n"
                f'strategie_analyse = "{current_strategie_analyse}"\n\n'
                "Une revue humaine a identifié un problème sur cette classification :\n"
                f"{review_note}\n\n"
                "Reclasse cette règle en tenant compte de cette remarque.\n"
            )
            final_instruction = "Génère maintenant une réponse JSON pour la règle ci-dessus."
            prompt_text = prompt_text.replace(
                final_instruction, review_section + "\n" + final_instruction
            )

        return prompt_text
```

- [ ] **Step 4: Étendre `enrich_single_rule()`**

Remplacer :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def enrich_single_rule(self, rule: Rule) -> EnrichedRule:
        """
        Enrichit une règle via LLM avec retry logic.

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        autre), avec backoff exponentiel (2s, 4s, 8s).

        Args:
            rule: Rule à enrichir

        Returns:
            EnrichedRule avec champs d'enrichissement

        Raises:
            TimeoutError: Si les 3 tentatives échouent (dernière exception relevée)

        Note:
            Seule la tentative réussie est comptabilisée dans les totaux de
            tokens — les tentatives échouées avant succès ne remontent pas
            de usage_metadata exploitable.
        """
        formatted_prompt = self.load_prompt(rule)

        response = self.llm.invoke(formatted_prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
            theme=rule.theme,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=rule.objectifs,
            tags=rule.tags,
            phases=rule.phases,
            slug=rule.slug,
            strategie_analyse=parsed["strategie_analyse"],
            strategie_justification=parsed["strategie_justification"],
            guide_analyse=parsed["guide_analyse"],
            strategie_source="ia_import",
            llm_model=self.model_name,
            prompt_version=self.prompt_version,
        )
```

par :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def enrich_single_rule(
        self,
        rule: Rule,
        review_note: str | None = None,
        current_strategie_analyse: str | None = None,
        strategie_source: str = "ia_import",
    ) -> EnrichedRule:
        """
        Enrichit une règle via LLM avec retry logic.

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        autre), avec backoff exponentiel (2s, 4s, 8s).

        Args:
            rule: Rule à enrichir
            review_note: Note de revue humaine (utilisé par enrich_again) —
                None pour un enrichissement initial normal
            current_strategie_analyse: Classification actuelle à corriger
                (utilisé par enrich_again avec review_note)
            strategie_source: Origine de la classification ("ia_import" par
                défaut, "ia_reingest" pour enrich_again)

        Returns:
            EnrichedRule avec champs d'enrichissement

        Raises:
            TimeoutError: Si les 3 tentatives échouent (dernière exception relevée)

        Note:
            Seule la tentative réussie est comptabilisée dans les totaux de
            tokens — les tentatives échouées avant succès ne remontent pas
            de usage_metadata exploitable.
        """
        formatted_prompt = self.load_prompt(rule, review_note, current_strategie_analyse)

        response = self.llm.invoke(formatted_prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return EnrichedRule(
            id=rule.id,
            number=rule.number,
            intitule=rule.intitule,
            theme=rule.theme,
            solution=rule.solution,
            controle=rule.controle,
            objectifs=rule.objectifs,
            tags=rule.tags,
            phases=rule.phases,
            slug=rule.slug,
            strategie_analyse=parsed["strategie_analyse"],
            strategie_justification=parsed["strategie_justification"],
            guide_analyse=parsed["guide_analyse"],
            strategie_source=strategie_source,
            llm_model=self.model_name,
            prompt_version=self.prompt_version,
        )
```

- [ ] **Step 5: Vérifier que les nouveaux tests passent, et qu'aucun test existant ne casse**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: tous les tests passent, y compris `test_enrich_single_rule_success` (déjà
existant, doit rester vert sans modification — preuve de rétrocompatibilité).

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/llm_client.py tests/unit/ingestion/test_enrichment.py
git commit -m "$(cat <<'EOF'
feat: add optional review context params to load_prompt/enrich_single_rule

review_note et current_strategie_analyse (optionnels, défaut None) et
strategie_source (optionnel, défaut "ia_import" inchangé) préparent
l'injection du contexte de revue humaine pour enrich_again — aucun appel
existant modifié.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `load_rules_to_review()` et `clear_review_fields()`

**Files:**

- Create: `app/ingestion/enrich_again.py`
- Test: `tests/integration/ingestion/test_enrich_again.py`

**Interfaces:**

- Consumes : `app.models.referentiel.Regle/Objectif/ObjectifRegle/Phase/PhaseRegle/Tag/RegleTag/Theme`,
  `app.ingestion.schema.RuleAggregation`.
- Produces : `load_rules_to_review(session: Session) -> list[tuple[RuleAggregation, str, str]]`
  (triplet : règle, `review_note`, `strategie_analyse` actuelle) et
  `clear_review_fields(session: Session, numero: int) -> None` (pas de
  commit à l'intérieur) — consommés par la Task 3.

Ces tests sont des tests d'intégration Postgres : ils nécessitent
`make migration-test` déjà exécuté (base `qualicheck_test` existante et
migrée) et utilisent `POSTGRES_TEST_DB` — **jamais** `POSTGRES_DB` (voir
`CLAUDE.md`, convention actée le 2026-07-25).

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `tests/integration/ingestion/test_enrich_again.py` :

```python
"""
Test d'intégration : sélection des règles à revoir et nettoyage des champs
de revue (enrich_again). Nécessite qualicheck-postgres démarré et
POSTGRES_TEST_DB migrée (make migration-test).
"""
import os
from datetime import UTC, datetime

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ingestion.aggregation import EnrichedRules
from app.ingestion.enrich_again import clear_review_fields, load_rules_to_review
from app.ingestion.schema import EnrichedRule
from app.ingestion.stockage import clear_opquast_tables, store_rules
from app.models.referentiel import Regle

load_dotenv()


def _database_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture
def session():
    engine = create_engine(_database_url())
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _rule(number, strategie_analyse):
    return EnrichedRule(
        id=number, number=number, intitule=f"Règle {number}", theme="Thème",
        objectifs=["Obj"], tags=["Tag"], phases=["Phase"],
        slug=f"regle-{number}", solution="Solution", controle="Contrôle",
        strategie_analyse=strategie_analyse, strategie_justification="Justif",
        guide_analyse="Guide",
    )


def test_load_rules_to_review_filters_by_status(session):
    """Seules les règles a_revoir/invalide sont retournées, pas valide ni NULL."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([
        _rule(1, "statique"),
        _rule(2, "playwright"),
        _rule(3, "manuel"),
    ]))

    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Note 1"}
    )
    session.query(Regle).filter_by(numero=2).update(
        {"review_status": "valide", "review_note": "Note 2"}
    )
    # numero=3 reste NULL (jamais revue)
    session.commit()

    to_review = load_rules_to_review(session)

    numeros = {rule.number for rule, _, _ in to_review}
    assert numeros == {1}

    rule, note, current = next(t for t in to_review if t[0].number == 1)
    assert note == "Note 1"
    assert current == "statique"

    clear_opquast_tables(session)


def test_load_rules_to_review_includes_invalide_status(session):
    """review_status='invalide' est aussi sélectionné, pas seulement a_revoir."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "invalide", "review_note": "Note"}
    )
    session.commit()

    to_review = load_rules_to_review(session)

    assert {rule.number for rule, _, _ in to_review} == {1}

    clear_opquast_tables(session)


def test_clear_review_fields_resets_to_null(session):
    """clear_review_fields remet reviewed_at/review_status/review_note à NULL."""
    clear_opquast_tables(session)

    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    session.query(Regle).filter_by(numero=1).update({
        "review_status": "a_revoir",
        "review_note": "Note",
        "reviewed_at": datetime.now(UTC).replace(tzinfo=None),
    })
    session.commit()

    clear_review_fields(session, numero=1)
    session.commit()

    regle = session.query(Regle).filter_by(numero=1).first()
    assert regle.review_status is None
    assert regle.review_note is None
    assert regle.reviewed_at is None

    clear_opquast_tables(session)
```

- [ ] **Step 2: Vérifier que les tests échouent**

Run: `uv run pytest tests/integration/ingestion/test_enrich_again.py -v`
Expected: `ModuleNotFoundError: No module named 'app.ingestion.enrich_again'`

- [ ] **Step 3: Créer `app/ingestion/enrich_again.py`**

```python
"""
Réécriture ciblée des règles marquées pour revue manuelle.

Sélectionne les règles où review_status IS NOT NULL AND != 'valide',
rappelle le LLM d'enrichissement en tenant compte de review_note, puis
vide les champs de revue une fois la correction appliquée.
"""

import logging

from sqlalchemy.orm import Session

from app.models.referentiel import (
    Objectif,
    ObjectifRegle,
    Phase,
    PhaseRegle,
    Regle,
    RegleTag,
    Tag,
    Theme,
)

from .schema import RuleAggregation

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")


def load_rules_to_review(session: Session) -> list[tuple[RuleAggregation, str, str]]:
    """
    Charge les règles marquées pour revue manuelle (a_revoir ou invalide).

    Args:
        session: Session SQLAlchemy active

    Returns:
        Liste de triplets (règle reconstituée, review_note, strategie_analyse
        actuelle), dans l'ordre des numéros.
    """
    regles = (
        session.query(Regle)
        .filter(Regle.review_status.isnot(None), Regle.review_status != "valide")
        .order_by(Regle.numero)
        .all()
    )

    result = []
    for regle in regles:
        objectifs = (
            session.query(Objectif.objectif)
            .join(ObjectifRegle)
            .filter(ObjectifRegle.regle_id == regle.id)
            .all()
        )
        phases = (
            session.query(Phase.phase)
            .join(PhaseRegle)
            .filter(PhaseRegle.regle_id == regle.id)
            .all()
        )
        tags = (
            session.query(Tag.tag)
            .join(RegleTag)
            .filter(RegleTag.regle_id == regle.id)
            .all()
        )
        theme = session.query(Theme.theme).filter(Theme.id == regle.theme_id).scalar()

        rule = RuleAggregation(
            id=regle.id,
            number=regle.numero,
            intitule=regle.intitule,
            theme=theme,
            contexte=regle.contexte,
            solution=regle.solution,
            controle=regle.controle,
            objectifs=[o[0] for o in objectifs],
            tags=[t[0] for t in tags],
            phases=[p[0] for p in phases],
            slug="",
        )
        result.append((rule, regle.review_note, regle.strategie_analyse))

    return result


def clear_review_fields(session: Session, numero: int) -> None:
    """
    Remet reviewed_at/review_status/review_note à NULL pour une règle.

    Pas de commit ici — reste dans la même transaction que l'upsert qui
    a corrigé la règle (voir enrich_again()).

    Args:
        session: Session SQLAlchemy active
        numero: Numéro de la règle à nettoyer
    """
    regle = session.query(Regle).filter_by(numero=numero).first()
    if regle is None:
        return
    regle.reviewed_at = None
    regle.review_status = None
    regle.review_note = None
    session.flush()
```

- [ ] **Step 4: Vérifier que les tests passent**

Run: `uv run pytest tests/integration/ingestion/test_enrich_again.py -v`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/enrich_again.py tests/integration/ingestion/test_enrich_again.py
git commit -m "$(cat <<'EOF'
feat: add load_rules_to_review and clear_review_fields

Sélection des règles review_status IN (a_revoir, invalide) et remise à
NULL des champs de revue après correction — base de app.ingestion.enrich_again.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Orchestrateur `enrich_again()`

**Files:**

- Modify: `app/ingestion/enrich_again.py` (ajout de la fonction `enrich_again`)
- Test: `tests/integration/ingestion/test_enrich_again.py` (ajout de tests)

**Interfaces:**

- Consumes : `load_rules_to_review`, `clear_review_fields` (Task 2),
  `LLMClient.enrich_single_rule(rule, review_note, current_strategie_analyse, strategie_source)`
  (Task 1), `app.ingestion.stockage.upsert_rule`, `app.ingestion.llm_client.load_manifest`.
- Produces : `enrich_again(session: Session) -> None` — consommé par la
  Task 4 (`scripts/enrich_again.py`).

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `tests/integration/ingestion/test_enrich_again.py` :

```python
from unittest.mock import MagicMock, patch


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_no_rules_to_review_skips_llm_call(mock_llm_client_class, session):
    """Aucune règle a_revoir/invalide -> aucun appel LLM, aucune erreur."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([_rule(1, "statique")]))
    # Aucune règle marquée pour revue

    enrich_again(session)

    mock_llm_client_class.assert_not_called()

    clear_opquast_tables(session)


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_success_clears_review_and_writes_ia_reingest(
    mock_llm_client_class, session
):
    """Une règle corrigée avec succès : strategie_source='ia_reingest',
    review_* remis à NULL."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([_rule(1, "vision+statique")]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Devrait être vision&statique."}
    )
    session.commit()

    mock_llm_instance = MagicMock()
    mock_llm_client_class.return_value = mock_llm_instance
    mock_llm_instance.input_tokens = 100
    mock_llm_instance.output_tokens = 50
    mock_llm_instance.enrich_single_rule.return_value = _rule(
        1, "vision&statique"
    ).model_copy(update={"strategie_source": "ia_reingest"})

    enrich_again(session)

    regle = session.query(Regle).filter_by(numero=1).first()
    assert regle.strategie_analyse == "vision&statique"
    assert regle.strategie_source == "ia_reingest"
    assert regle.review_status is None
    assert regle.review_note is None
    assert regle.reviewed_at is None

    clear_opquast_tables(session)


@patch("app.ingestion.enrich_again.LLMClient")
def test_enrich_again_partial_failure_preserves_prior_successes(
    mock_llm_client_class, session
):
    """Si la 2e règle échoue après ses tentatives, la 1ère (déjà corrigée et
    commitée) reste acquise ; la 2e garde son review_status intact."""
    from app.ingestion.enrich_again import enrich_again

    clear_opquast_tables(session)
    store_rules(session, EnrichedRules([
        _rule(1, "vision+statique"),
        _rule(2, "statique"),
    ]))
    session.query(Regle).filter_by(numero=1).update(
        {"review_status": "a_revoir", "review_note": "Note 1"}
    )
    session.query(Regle).filter_by(numero=2).update(
        {"review_status": "a_revoir", "review_note": "Note 2"}
    )
    session.commit()

    mock_llm_instance = MagicMock()
    mock_llm_client_class.return_value = mock_llm_instance
    mock_llm_instance.input_tokens = 100
    mock_llm_instance.output_tokens = 50
    fixed_rule_1 = _rule(1, "vision&statique").model_copy(
        update={"strategie_source": "ia_reingest"}
    )
    mock_llm_instance.enrich_single_rule.side_effect = [
        fixed_rule_1,
        TimeoutError("3 tentatives épuisées"),
    ]

    with pytest.raises(TimeoutError):
        enrich_again(session)

    r1 = session.query(Regle).filter_by(numero=1).first()
    assert r1.strategie_analyse == "vision&statique"
    assert r1.review_status is None  # traitée avec succès, nettoyée et acquise

    r2 = session.query(Regle).filter_by(numero=2).first()
    assert r2.review_status == "a_revoir"  # échec, conservée intacte
    assert r2.review_note == "Note 2"

    clear_opquast_tables(session)
```

- [ ] **Step 2: Vérifier que les tests échouent**

Run: `uv run pytest tests/integration/ingestion/test_enrich_again.py -v -k enrich_again`
Expected: `ImportError: cannot import name 'enrich_again'`

- [ ] **Step 3: Ajouter `enrich_again()` à `app/ingestion/enrich_again.py`**

Ajouter en tête du fichier (après les imports existants — ne pas dupliquer
`from sqlalchemy.orm import Session`, déjà présent depuis la Task 2) :

```python
import json
from pathlib import Path

from .llm_client import LLMClient, load_manifest
from .stockage import upsert_rule
```

Puis à la fin du fichier :

```python
def enrich_again(session: Session) -> None:
    """
    Rappelle le LLM sur les règles marquées pour revue manuelle et vide
    leurs champs de revue une fois corrigées.

    Fail-fast, commit par règle (pas un commit global) : si une règle
    échoue après ses 3 tentatives, l'exception se propage et arrête le
    traitement — les règles précédentes, déjà commitées individuellement,
    restent acquises.

    Args:
        session: Session SQLAlchemy active

    Raises:
        Exception: Toute erreur d'enrichissement non résolue après les
            tentatives de retry (propagée depuis enrich_single_rule)
    """
    rows = load_rules_to_review(session)

    if not rows:
        progress_logger.info("enrich_again : aucune règle à revoir")
        return

    preview = [
        {"numero": rule.number, "review_note": note, "strategie_analyse_actuelle": current}
        for rule, note, current in rows
    ]
    tmp_dir = Path(__file__).resolve().parents[2] / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    with open(tmp_dir / "enrich_again_preview.json", "w", encoding="utf-8") as f:
        json.dump(preview, f, ensure_ascii=False, indent=2)
    progress_logger.info(f"enrich_again : {len(rows)} règle(s) à revoir")

    llm_client = LLMClient()

    for rule, review_note, current_strategie_analyse in rows:
        try:
            enriched = llm_client.enrich_single_rule(
                rule,
                review_note=review_note,
                current_strategie_analyse=current_strategie_analyse,
                strategie_source="ia_reingest",
            )
            upsert_rule(session, enriched)
            clear_review_fields(session, numero=rule.number)
            session.commit()
            progress_logger.info(f"Règle {rule.number} — enrich_again : OK")
        except Exception as e:
            session.rollback()
            logger.error(f"Règle {rule.number} — enrich_again : KO ({e})")
            raise

    role = load_manifest()["enrichissement"]
    cost = (
        llm_client.input_tokens * role["prix_entree_par_million"]
        + llm_client.output_tokens * role["prix_sortie_par_million"]
    ) / 1_000_000
    summary = (
        f"enrich_again — Tokens — entrée : {llm_client.input_tokens}, "
        f"sortie : {llm_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)
```

- [ ] **Step 4: Vérifier que les tests passent**

Run: `uv run pytest tests/integration/ingestion/test_enrich_again.py -v`
Expected: `7 passed`

- [ ] **Step 5: Nettoyer le fichier de preview généré par les tests**

Run: `rm -f tmp/enrich_again_preview.json`

(Fichier gitignoré via `tmp/` — pas d'ajout git nécessaire, juste éviter de
laisser un fichier de test qui traînerait dans le poste de travail.)

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/enrich_again.py tests/integration/ingestion/test_enrich_again.py
git commit -m "$(cat <<'EOF'
feat: add enrich_again orchestrator

Boucle sur les règles a_revoir/invalide, appelle le LLM avec le contexte
de revue, upsert + vide review_* + commit par règle (fail-fast : une
règle en échec arrête le run mais préserve les règles précédentes déjà
commitées). Dump JSON de prévisualisation dans tmp/ avant tout appel LLM.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Point d'entrée `scripts/enrich_again.py` + Makefile + docs

**Files:**

- Create: `scripts/enrich_again.py`
- Modify: `Makefile` (nouvelle cible `enrich-again`)
- Modify: `CLAUDE.md` (tableau des cibles Makefile)
- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes : `app.ingestion.enrich_again.enrich_again(session)` (Task 3),
  `app.logging_config.setup_logging` (déjà existant, utilisé par
  `scripts/ingestion.py`).
- Produces : rien de consommé par une tâche ultérieure — dernière tâche du plan.

**⚠️ Ne pas exécuter ce script pour de vrai** (`uv run python
scripts/enrich_again.py` ou `make enrich-again`) contre la base réelle
`qualicheck` — cela déclencherait un appel LLM payant réel sur les règles
actuellement marquées `a_revoir`. Vérification uniquement via lint/relecture.

- [ ] **Step 1: Créer `scripts/enrich_again.py`**

```python
"""Point d'entrée pour la réécriture ciblée des règles marquées à revoir.

Rappelle le LLM d'enrichissement sur les règles review_status IN
(a_revoir, invalide), en tenant compte de review_note, puis vide ces
champs une fois la correction appliquée. Fail-fast : toute erreur arrête
immédiatement le script avec un code de sortie non-nul — les règles déjà
corrigées avant l'échec restent acquises (commit par règle).
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.enrich_again import enrich_again  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()

    logger.info("=== enrich_again : démarrage ===")
    progress_logger.info("=== enrich_again : démarrage ===")

    try:
        with Session(engine) as session:
            enrich_again(session)
    except Exception as e:
        logger.error("enrich_again : ÉCHEC (%s)", e)
        sys.exit(1)

    logger.info("=== enrich_again : succès ===")
    progress_logger.info("=== enrich_again : succès ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Vérifier la syntaxe et le style (sans exécuter le script)**

Run: `uv run ruff check scripts/enrich_again.py`
Expected: `All checks passed!`

Run: `uv run python -m py_compile scripts/enrich_again.py`
Expected: aucune sortie, code de sortie 0 (confirme l'absence d'erreur de
syntaxe sans jamais exécuter `main()`).

- [ ] **Step 3: Ajouter la cible Makefile**

Dans `Makefile`, section « Ingestion et données réelles », juste après la
cible `import_sql` (avant la section « Tests ») :

```makefile
## Relance le LLM sur les règles marquées review_status = a_revoir/invalide,
## en tenant compte de review_note, puis sauvegarde les données réelles
enrich-again:
	uv run python scripts/enrich_again.py
	$(MAKE) export_sql
```

Et mettre à jour la ligne `.PHONY` en tête du fichier pour y ajouter
`enrich-again` :

```makefile
.PHONY: up down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again
```

- [ ] **Step 4: Documenter la cible dans `CLAUDE.md`**

Dans la section `## Makefile`, ajouter une ligne au tableau, juste après
`make import_sql` :

```markdown
| `make enrich-again` | Rappelle le LLM sur les règles `review_status = a_revoir`/`invalide` (tient compte de `review_note`), vide ces champs après correction, puis `make export_sql` |
```

- [ ] **Step 5: Ajouter une entrée `CHANGELOG.md`**

Ajouter une entrée datée (2026-07-26, Claude Code) décrivant : le nouveau
module `app/ingestion/enrich_again.py`, le script `scripts/enrich_again.py`,
la cible `make enrich-again`, et les paramètres optionnels ajoutés à
`llm_client.py` (`review_note`, `current_strategie_analyse`,
`strategie_source`).

- [ ] **Step 6: Lancer la suite complète de tests et ruff**

Run: `uv run pytest tests/ -v`
Expected: tous les tests passent (aucun `FAILED`).

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add scripts/enrich_again.py Makefile CLAUDE.md CHANGELOG.md
git commit -m "$(cat <<'EOF'
feat: add scripts/enrich_again.py entry point and make enrich-again

Point d'entrée CLI sur le modèle de scripts/ingestion.py — fail-fast,
même logging. Cible Makefile chaînant export_sql ensuite, comme pour
make ingestion. Non exécuté pour de vrai dans le cadre de ce chantier
(appel LLM payant réel réservé à un lancement manuel délibéré).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Fin de plan

Après la Task 4, utiliser superpowers:finishing-a-development-branch — pas
de nouvelle branche (travail resté sur `feature`, comme les chantiers D à
J). Le lancement réel de `make enrich-again` contre les 11 règles marquées
`a_revoir` reste une décision et une action de David, hors périmètre de ce
plan.
