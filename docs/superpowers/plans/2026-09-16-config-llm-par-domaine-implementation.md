# Config LLM par domaine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renommer `manifest.yml`/`load_manifest()` en `config.yml`/`load_config()` partout, et scinder `app/ingestion/manifest.yml` en `app/ingestion/config.yml` (enrichissement, embedding) + `app/retrieval/config.yml` (rag_acceptance, decomposition, jugement, guardrail — nouveau module, corrige la mauvaise localisation des rôles retrieval).

**Architecture:** Trois modules `config.py` avec la même signature `load_config() -> dict`, un par domaine (`app/ingestion/`, `app/retrieval/`, `app/api_regles/` — ce dernier existe déjà, juste renommé). Coupure nette : tous les appelants sont migrés dans le même chantier, aucun alias de compatibilité.

**Tech Stack:** Python, PyYAML, pytest.

## Global Constraints

- Coupure nette, pas de période de transition ni d'alias `load_manifest = load_config`.
- Contenu des rôles inchangé (modèles, prix, seuils, température) — déplacement, pas réécriture.
- `docs/superpowers/specs/` et `jury/decisions/` historiques non modifiés.
- Suite de tests complète verte à l'identique avant/après (aucun changement de comportement testable).
- `app/ingestion/rag_acceptance.py` (le module Python de logique d'évaluation : `is_acceptable()`, `compute_taux_par_famille()`, etc.) est **distinct** de la section YAML `rag_acceptance:` (top_n, seuils) malgré le nom identique — ce module ne bouge pas, il ne lit jamais `load_manifest()` lui-même (ses appelants lui passent le seuil en paramètre). Ne pas le confondre avec la section de config du même nom.

---

## Contexte technique déjà vérifié dans le code

Recensement exhaustif (`grep -rln "load_manifest" --include="*.py" .`) : **18 fichiers** référencent `load_manifest` aujourd'hui. Répartition par domaine et par fichier, avec les lignes exactes :

**Domaine ingestion** (5 fichiers, sections `enrichissement` + `embedding`) :
- `app/ingestion/llm_client.py` : définit `load_manifest()` (à retirer, remplacé par un import), l'utilise ligne 69 (`role = manifest["enrichissement"]`)
- `app/ingestion/embedding.py` : ligne 15 `from .llm_client import load_manifest`, ligne 25 `manifest = load_manifest()`, ligne 26 `role = manifest["embedding"]`
- `app/ingestion/enrich_again.py` : ligne 26 `from .llm_client import LLMClient, load_manifest`, ligne 174 `role = load_manifest()["enrichissement"]`
- `scripts/embed_rules.py` : ligne 22 import, ligne 75 `role = load_manifest()["embedding"]`
- `scripts/ingestion.py` : ligne 28 import, ligne 158 `role = load_manifest()["enrichissement"]`

**Domaine retrieval** (5 fichiers, sections `rag_acceptance` + `decomposition` + `jugement` + `guardrail`) :
- `app/retrieval/decomposition.py` : ligne 18 `from app.ingestion.llm_client import load_manifest`, ligne 36 `manifest = load_manifest()`, ligne 37 `role = manifest["decomposition"]`
- `app/retrieval/jugement.py` : ligne 16 import, ligne 34-35 idem avec `"jugement"`
- `app/retrieval/guardrail.py` : ligne 22 import, ligne 40-41 idem avec `"guardrail"`
- `app/api_regles/regles.py` : ligne 24 import, ligne 299 `top_n = load_manifest()["rag_acceptance"]["top_n"]`
- `scripts/mesure_guardrail_perimetre.py` : ligne 24 import, ligne 123 `manifest_role = load_manifest()["guardrail"]`
- `scripts/check_api_regles_dense_acceptance.py` : ligne 24 import, ligne 92 `rag_acceptance_config = load_manifest()["rag_acceptance"]`

**Scripts à double import** (5 fichiers, lisent à la fois `embedding`/`enrichissement` — ingestion — et `decomposition`/`rag_acceptance` — retrieval) :
- `scripts/check_rag_acceptance.py` : ligne 23 import, ligne 59 `config = load_manifest()["rag_acceptance"]` (retrieval), lignes 106-108 `manifest = load_manifest()`, `embedding_role = manifest["embedding"]` (ingestion), `decomposition_role = manifest["decomposition"]` (retrieval)
- `scripts/rag_dense_acceptance.py` : ligne 29 import, lignes 165-167 `manifest = load_manifest()`, `embedding_role = manifest["embedding"]`, `decomposition_role = manifest["decomposition"]`
- `scripts/mesure_variantes_chunks.py` : ligne 31 import, lignes 197-198 `embedding_role = load_manifest()["embedding"]`, `decomposition_role = load_manifest()["decomposition"]`
- `scripts/mesure_multi_vecteurs_chunks.py` : ligne 34 import, lignes 277-278 idem
- `scripts/mesure_combinaisons_chunks.py` : ligne 33 import, lignes 266-267 idem

**Domaine api_regles** (2 fichiers, fichier déjà bien situé — juste le nom) :
- `app/api_regles/config.py` : définit son propre `load_manifest()` (fonction interne à renommer), charge `app/api_regles/manifest.yml`
- `tests/unit/api_regles/test_config.py` : teste `app.api_regles.config` (pas d'import direct de `load_manifest`, seulement via le module)

**Test** :
- `tests/unit/ingestion/test_enrichment.py` : ligne 402-408, `test_load_manifest_reads_enrichissement_role` importe et appelle `load_manifest()` directement

**Fichiers non-Python à mettre à jour** :
- `Makefile` ligne 103 (commentaire) et ligne 149 : `API_REGLES_PORT = $(shell grep 'port:' app/api_regles/manifest.yml | tr -d ' ' | cut -d: -f2)`
- `docs/agent/03_references_impl.md` lignes 11, 12, 14, 22, 23 (tableau de sources de vérité)
- `docs/agent/04_contexte_actif.md` ligne 27
- `tests/integration/api_regles/test_regles.py` ligne 50 (commentaire)
- `tests/unit/api_regles/test_auth.py` ligne 19, `tests/unit/api_regles/test_acceptance.py` ligne 18 (commentaires identiques, docstring de `_un_seul_client`)

**Contenu exact de `app/ingestion/manifest.yml` à répartir** (111 lignes actuelles) :
- Header (lignes 1-11, commentaire général) → répété, adapté, dans les deux nouveaux fichiers
- `enrichissement:` (lignes 13-21) → `app/ingestion/config.yml`
- `embedding:` (lignes 23-30) → `app/ingestion/config.yml`
- `rag_acceptance:` (lignes 32-61) → `app/retrieval/config.yml`
- `decomposition:` (lignes 63-82) → `app/retrieval/config.yml`
- `jugement:` (lignes 84-95) → `app/retrieval/config.yml`
- `guardrail:` (lignes 97-110) → `app/retrieval/config.yml`

---

### Task 1 : `app/ingestion/config.py` + `app/ingestion/config.yml`

**Files:**
- Create: `app/ingestion/config.yml`
- Create: `app/ingestion/config.py`
- Modify: `app/ingestion/llm_client.py`
- Modify: `app/ingestion/embedding.py`
- Modify: `app/ingestion/enrich_again.py`
- Modify: `scripts/embed_rules.py`
- Modify: `scripts/ingestion.py`
- Modify: `tests/unit/ingestion/test_enrichment.py`
- Delete: `app/ingestion/manifest.yml`

**Interfaces:**
- Produces: `app.ingestion.config.load_config() -> dict` — retourne `{"enrichissement": {...}, "embedding": {...}}`.

- [ ] **Step 1 : Créer `app/ingestion/config.yml`**

```yaml
# Décisions courantes du pipeline d'ingestion.
# Aucun historique ici : git s'en charge (git log config.yml).
# Aucun secret ici : voir .env.
#
# Source de vérité pour la configuration à appliquer au *prochain* run
# (quel modèle, quel prix, quel seuil) — jamais pour l'état des données
# déjà en base. La version des données déjà ingérées (prompt_version,
# llm_model par règle) vit dans la table regle elle-même, pas ici : un
# enrich_again partiel peut mélanger les versions règle par règle, ce que
# ce fichier ne pourrait refléter sans devenir une deuxième source de
# vérité redondante et potentiellement fausse.

enrichissement:
  modele: kimi-k2.6
  env_var: AZURE_MODEL_KIMI
  # Prix (€ pour 1M tokens) reconstruit à partir de la facture Azure réelle du
  # 19/07/2026 (9,13 €), pas un tarif publié : le ratio entrée/sortie du tarif
  # public Moonshot/OpenRouter est supposé correct, seule l'échelle est recalée.
  # Détail : conception/2_us0/enrichissement/E_provenance_manifeste.md §6
  prix_entree_par_million: 0.8008
  prix_sortie_par_million: 3.3875

embedding:
  modele: text-embedding-3-small
  env_var: AZURE_MODEL_TEXT_EMBEDDING_SMALL
  # Prix (€ pour 1M tokens d'entrée) — tarif public Azure/OpenAI (~0,02 $/M
  # tokens) converti en euros par estimation, aucune facture Azure réelle
  # disponible pour l'instant (premier usage réel de ce modèle). À corriger
  # dès qu'une vraie facture existe — même logique que le rôle enrichissement.
  prix_entree_par_million: 0.0184
```

- [ ] **Step 2 : Créer `app/ingestion/config.py`**

```python
"""
Configuration du pipeline d'ingestion (app/ingestion/config.yml).
"""

from pathlib import Path

import yaml


def load_config() -> dict:
    """Charge les décisions courantes du pipeline (app/ingestion/config.yml)."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 3 : Lancer la suite pour confirmer qu'elle est encore verte à ce stade**

Run: `uv run pytest tests/unit/ingestion -q`
Expected: PASS (rien n'a encore été modifié dans les fichiers existants, `manifest.yml` original toujours présent)

- [ ] **Step 4 : Modifier `app/ingestion/llm_client.py`**

Retirer la fonction `load_manifest()` et l'import `yaml` associé (plus utilisé
que par elle et par `load_prompt_version()` — `yaml.safe_load` y reste
nécessaire, donc l'import `yaml` est conservé), importer `load_config` depuis
`.config`.

Remplacer :

```python
import logging
import os
from pathlib import Path

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from .schema import EnrichedRule
from .schema import RuleAggregation as Rule

logger = logging.getLogger(__name__)

PROMPT_PLACEHOLDERS = [
    "intitule",
    "contexte",
    "solution",
    "controle",
    "objectifs",
    "tags",
    "phases",
]


def load_manifest() -> dict:
    """Charge les décisions courantes du pipeline (app/ingestion/manifest.yml)."""
    manifest_path = Path(__file__).parent / "manifest.yml"
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _read_prompt_file() -> str:
```

par :

```python
import logging
import os
from pathlib import Path

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import load_config
from .schema import EnrichedRule
from .schema import RuleAggregation as Rule

logger = logging.getLogger(__name__)

PROMPT_PLACEHOLDERS = [
    "intitule",
    "contexte",
    "solution",
    "controle",
    "objectifs",
    "tags",
    "phases",
]


def _read_prompt_file() -> str:
```

Puis, plus bas dans `LLMClient.__init__`, remplacer :

```python
        manifest = load_manifest()
        role = manifest["enrichissement"]
```

par :

```python
        config = load_config()
        role = config["enrichissement"]
```

- [ ] **Step 5 : Modifier `app/ingestion/embedding.py`**

Remplacer :

```python
from .llm_client import load_manifest
```

par :

```python
from .config import load_config
```

Puis, dans `EmbeddingClient.__init__`, remplacer :

```python
        manifest = load_manifest()
        role = manifest["embedding"]
```

par :

```python
        config = load_config()
        role = config["embedding"]
```

- [ ] **Step 6 : Modifier `app/ingestion/enrich_again.py`**

Remplacer :

```python
from .llm_client import LLMClient, load_manifest
```

par :

```python
from .config import load_config
from .llm_client import LLMClient
```

Puis, ligne 174, remplacer :

```python
        role = load_manifest()["enrichissement"]
```

par :

```python
        role = load_config()["enrichissement"]
```

- [ ] **Step 7 : Modifier `scripts/embed_rules.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config  # noqa: E402
```

Puis, ligne 75, remplacer :

```python
        role = load_manifest()["embedding"]
```

par :

```python
        role = load_config()["embedding"]
```

- [ ] **Step 8 : Modifier `scripts/ingestion.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config  # noqa: E402
```

Puis, ligne 158, remplacer :

```python
        role = load_manifest()["enrichissement"]
```

par :

```python
        role = load_config()["enrichissement"]
```

- [ ] **Step 9 : Modifier `tests/unit/ingestion/test_enrichment.py`**

Remplacer :

```python
class TestManifestAndPromptVersion:
    """Vérifie la lecture du manifeste et de la version de prompt."""

    def test_load_manifest_reads_enrichissement_role(self):
        from app.ingestion.llm_client import load_manifest

        manifest = load_manifest()

        assert manifest["enrichissement"]["modele"] == "kimi-k2.6"
        assert manifest["enrichissement"]["env_var"] == "AZURE_MODEL_KIMI"
```

par :

```python
class TestConfigAndPromptVersion:
    """Vérifie la lecture de la config et de la version de prompt."""

    def test_load_config_reads_enrichissement_role(self):
        from app.ingestion.config import load_config

        config = load_config()

        assert config["enrichissement"]["modele"] == "kimi-k2.6"
        assert config["enrichissement"]["env_var"] == "AZURE_MODEL_KIMI"
```

- [ ] **Step 10 : Supprimer `app/ingestion/manifest.yml`**

```bash
git rm app/ingestion/manifest.yml
```

- [ ] **Step 11 : Lancer la suite ingestion, vérifier qu'elle passe**

Run: `uv run pytest tests/unit/ingestion -q`
Expected: PASS, tous les tests verts (y compris `test_load_config_reads_enrichissement_role`)

- [ ] **Step 12 : Lint**

Run: `uv run ruff check app/ingestion/ scripts/embed_rules.py scripts/ingestion.py tests/unit/ingestion/`
Expected: `All checks passed!`

- [ ] **Step 13 : Commit**

```bash
git add app/ingestion/config.py app/ingestion/config.yml app/ingestion/llm_client.py app/ingestion/embedding.py app/ingestion/enrich_again.py scripts/embed_rules.py scripts/ingestion.py tests/unit/ingestion/test_enrichment.py app/ingestion/manifest.yml
git commit -m "refactor: app/ingestion/config.py remplace load_manifest (carte #18)"
```

---

### Task 2 : `app/retrieval/config.py` + `app/retrieval/config.yml`

**Files:**
- Create: `app/retrieval/config.yml`
- Create: `app/retrieval/config.py`
- Test: `tests/unit/retrieval/test_config.py`
- Modify: `app/retrieval/decomposition.py`
- Modify: `app/retrieval/jugement.py`
- Modify: `app/retrieval/guardrail.py`
- Modify: `app/api_regles/regles.py`
- Modify: `scripts/mesure_guardrail_perimetre.py`
- Modify: `scripts/check_api_regles_dense_acceptance.py`

**Interfaces:**
- Produces: `app.retrieval.config.load_config() -> dict` — retourne
  `{"rag_acceptance": {...}, "decomposition": {...}, "jugement": {...}, "guardrail": {...}}`.

- [ ] **Step 1 : Créer `app/retrieval/config.yml`**

```yaml
# Décisions courantes du retrieval (US2 question libre).
# Aucun historique ici : git s'en charge (git log config.yml).
# Aucun secret ici : voir .env.

rag_acceptance:
  # Augmenté de 3 à 15 le 2026-09-09 après mesure réelle sur les 56 cas
  # d'acceptance (docs/eval/rag_dense_acceptance_2026-09-09.md) : seule
  # valeur qui fait passer multi_sujets et vocabulaire_source_opquast à
  # 100%. 3 cas restent en échec/PARTIEL même à top_n=15 (règle 185,
  # cas multi-sujets 106/107) — signal de dilution réelle, pas de top_n.
  top_n: 15
  # Proportion minimale de cas réussis pour que la suite soit globalement
  # acceptable — le rappel imparfait du RAG est déjà assumé, voir
  # jury/decisions/2026-07-25-rag-us2-petit-corpus.md
  # Seuil de 0.8 à 0.9 le 2026-09-09 : rôle de garde-fou de non-régression
  # technique (pas une barre de qualité produit), calé sur les taux réels
  # mesurés à ce moment (92-100% par famille sur 99 cas). L'ancien 0.8
  # n'avait jamais été dérivé, juste choisi par défaut. Détail :
  # jury/decisions/2026-09-09-seuil-acceptance-rag-90-pourcent.md
  taux_reussite_minimum: 0.9
  # Plancher par famille, en dessous du seuil général — n'assouplit que la
  # famille listée, les autres restent au seuil général. Ajouté le
  # 2026-09-13 pour vocabulaire_objectif (74-78% mesurés), à l'époque sans
  # cause connue. Cause trouvée et corrigée le 2026-09-16 (température des
  # clients LLM non fixée, cf. temperature: 0 ci-dessous, carte Kanboard
  # #20) — mais vocabulaire_objectif reste stable à 73-74% sur 2 runs
  # post-correction : ce n'était pas de la variance pour cette famille,
  # c'est un plafond réel (règles quasi-doublons qui piègent le jugement
  # LLM, ex. règle 28 vs 25, 127 vs 153 — diagnostiqué par A/B le
  # 2026-09-13). Ce plancher reste donc justifié, plus comme rustine en
  # attente d'une cause, mais comme limite mesurée et comprise — à retirer
  # seulement si une future correction du jugement fait remonter le taux.
  taux_reussite_minimum_par_famille:
    vocabulaire_objectif: 0.7

decomposition:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  # Timeout applicatif distinct (2s, pas 30s comme le benchmark) : appel
  # dans le chemin d'une requête utilisateur en direct (US2), pas un
  # traitement batch offline. Voir docs/superpowers/specs/
  # 2026-09-09-retrieval-decomposition-multi-sujets-design.md.
  # Tarifs non vérifiés (pas de facture Azure réelle pour ce modèle) —
  # à corriger dès le premier run réel, même logique que le rôle embedding.
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
  # Température explicite à 0 (2026-09-16) : ChatOpenAI appliquait son
  # défaut (0.7) faute de valeur passée — les trois rôles du chemin
  # retrieval (decomposition, jugement, guardrail) échantillonnaient donc
  # au hasard à chaque appel. Cause mesurée de la variance run-à-run de
  # la suite d'acceptance (carte Kanboard #20 : des familles entières
  # passant de 100% à 67% sans aucun changement de code entre deux runs).
  # 0 = décodage glouton, le plus reproductible possible pour une tâche de
  # classification/décision, pas de génération créative.
  temperature: 0

jugement:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  # Meme modele/variable d'environnement que le role decomposition (meme
  # deploiement Azure, prompt different) - juge la pertinence des
  # candidats retournes par retrieve() avant citation. Voir
  # docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
  # Température à 0 — même raison que le rôle decomposition ci-dessus
  # (carte Kanboard #20).
  temperature: 0

guardrail:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  # Role experimental (2026-09-11) : teste l'hypothese qu'un LLM classe
  # correctement une question dans/hors perimetre Opquast SANS voir de
  # candidats retrieval (pas de biais de selection) - avant de decider
  # si ce guardrail merite d'etre construit au niveau agent. Mesure
  # uniquement pour l'instant (scripts/mesure_guardrail_perimetre.py),
  # pas encore integre a un pipeline de production.
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
  # Température à 0 — même raison que le rôle decomposition ci-dessus
  # (carte Kanboard #20).
  temperature: 0
```

- [ ] **Step 2 : Créer `app/retrieval/config.py`**

```python
"""
Configuration du retrieval (US2 question libre) : app/retrieval/config.yml.
"""

from pathlib import Path

import yaml


def load_config() -> dict:
    """Charge les décisions courantes du retrieval (app/retrieval/config.yml)."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
```

- [ ] **Step 3 : Écrire le test de `app/retrieval/config.py` (il doit échouer)**

Créer `tests/unit/retrieval/test_config.py` :

```python
"""Tests unitaires pour app/retrieval/config.py"""

from app.retrieval.config import load_config


class TestLoadConfig:
    """Vérifie la lecture des 4 rôles retrieval."""

    def test_load_config_reads_rag_acceptance_role(self):
        config = load_config()

        assert config["rag_acceptance"]["top_n"] == 15
        assert config["rag_acceptance"]["taux_reussite_minimum"] == 0.9

    def test_load_config_reads_decomposition_role(self):
        config = load_config()

        assert config["decomposition"]["modele"] == "gpt-5.4-mini"
        assert config["decomposition"]["env_var"] == "AZURE_MODEL_GPT_MINI"
        assert config["decomposition"]["temperature"] == 0

    def test_load_config_reads_jugement_role(self):
        config = load_config()

        assert config["jugement"]["modele"] == "gpt-5.4-mini"
        assert config["jugement"]["temperature"] == 0

    def test_load_config_reads_guardrail_role(self):
        config = load_config()

        assert config["guardrail"]["modele"] == "gpt-5.4-mini"
        assert config["guardrail"]["temperature"] == 0
```

- [ ] **Step 4 : Lancer le test, vérifier qu'il passe déjà (Step 1-2 ont créé le fichier et le module avant le test)**

Run: `uv run pytest tests/unit/retrieval/test_config.py -v`
Expected: PASS (4 tests) — le fichier et le module existent déjà depuis les
Steps 1-2 ; ce test sert de garde-fou pérenne, pas d'un cycle rouge/vert
classique ici puisque la donnée existe déjà réellement dans
`app/ingestion/manifest.yml` au moment de ce Step.

- [ ] **Step 5 : Modifier `app/retrieval/decomposition.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest
```

par :

```python
from app.retrieval.config import load_config
```

Puis, dans `DecompositionClient.__init__`, remplacer :

```python
        manifest = load_manifest()
        role = manifest["decomposition"]
```

par :

```python
        config = load_config()
        role = config["decomposition"]
```

- [ ] **Step 6 : Modifier `app/retrieval/jugement.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest
```

par :

```python
from app.retrieval.config import load_config
```

Puis, dans `JugementClient.__init__`, remplacer :

```python
        manifest = load_manifest()
        role = manifest["jugement"]
```

par :

```python
        config = load_config()
        role = config["jugement"]
```

- [ ] **Step 7 : Modifier `app/retrieval/guardrail.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest
```

par :

```python
from app.retrieval.config import load_config
```

Puis, dans `GuardrailClient.__init__`, remplacer :

```python
        manifest = load_manifest()
        role = manifest["guardrail"]
```

par :

```python
        config = load_config()
        role = config["guardrail"]
```

- [ ] **Step 8 : Modifier `app/api_regles/regles.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest
```

par :

```python
from app.retrieval.config import load_config
```

Puis, ligne 299, remplacer :

```python
    top_n = load_manifest()["rag_acceptance"]["top_n"]
```

par :

```python
    top_n = load_config()["rag_acceptance"]["top_n"]
```

- [ ] **Step 9 : Modifier `scripts/mesure_guardrail_perimetre.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.retrieval.config import load_config  # noqa: E402
```

Puis, ligne 123, remplacer :

```python
    manifest_role = load_manifest()["guardrail"]
```

par :

```python
    manifest_role = load_config()["guardrail"]
```

- [ ] **Step 10 : Modifier `scripts/check_api_regles_dense_acceptance.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.retrieval.config import load_config  # noqa: E402
```

Puis, ligne 92, remplacer :

```python
    rag_acceptance_config = load_manifest()["rag_acceptance"]
```

par :

```python
    rag_acceptance_config = load_config()["rag_acceptance"]
```

- [ ] **Step 11 : Lancer les tests retrieval + api_regles + le test d'acceptance dense, vérifier qu'ils passent**

Nécessite `qualicheck-postgres` démarré et `POSTGRES_TEST_DB` migrée.

Run: `uv run pytest tests/unit/retrieval tests/unit/api_regles tests/integration/api_regles -q`
Expected: PASS, tous les tests verts

- [ ] **Step 12 : Lint**

Run: `uv run ruff check app/retrieval/ app/api_regles/regles.py scripts/mesure_guardrail_perimetre.py scripts/check_api_regles_dense_acceptance.py tests/unit/retrieval/`
Expected: `All checks passed!`

- [ ] **Step 13 : Commit**

```bash
git add app/retrieval/config.py app/retrieval/config.yml tests/unit/retrieval/test_config.py app/retrieval/decomposition.py app/retrieval/jugement.py app/retrieval/guardrail.py app/api_regles/regles.py scripts/mesure_guardrail_perimetre.py scripts/check_api_regles_dense_acceptance.py
git commit -m "refactor: app/retrieval/config.py remplace load_manifest (carte #18)"
```

Note : `app/ingestion/manifest.yml` n'est supprimé qu'à la fin de la Task 1
(déjà fait) — à ce stade de la Task 2, il n'existe donc plus : ce Task 2
crée un fichier entièrement nouveau, il ne « déplace » pas littéralement
depuis un fichier qui existe encore au moment de son exécution. Le contenu
exact copié ci-dessus dans le Step 1 est celui documenté dans la section
« Contexte technique déjà vérifié » en tête de ce plan, à recopier tel quel
plutôt qu'à retrouver dans un fichier qui n'existe plus après la Task 1.

---

### Task 3 : Renommer `app/api_regles/manifest.yml` → `config.yml`

**Files:**
- Create: `app/api_regles/config.yml`
- Modify: `app/api_regles/config.py`
- Delete: `app/api_regles/manifest.yml`
- Modify: `tests/unit/api_regles/test_config.py`
- Modify: `tests/unit/api_regles/test_auth.py`
- Modify: `tests/unit/api_regles/test_acceptance.py`
- Modify: `tests/integration/api_regles/test_regles.py`

**Interfaces:**
- Produces: `app.api_regles.config.load_config() -> dict` (remplace
  `load_manifest()`, même contenu retourné).

- [ ] **Step 1 : Créer `app/api_regles/config.yml`** (copie exacte du contenu actuel de `app/api_regles/manifest.yml`, seul l'en-tête change)

```yaml
# Configuration courante de l'API données. Aucun secret ici : voir .env.
# Aucun historique ici : git s'en charge (git log config.yml).

api:
  title: "QualiCheck — API données"
  description: "Accès au référentiel Opquast enrichi et boucle de revue humaine"
  # Version du contrat d'API, distincte de la version du paquet Python de
  # pyproject.toml : elle évolue avec les endpoints, pas avec les dépendances.
  version: "0.1.0"
  port: 8880

cors:
  # Origines autorisées à appeler l'API depuis un navigateur.
  # Développement et production peuvent cohabiter : une origine qui n'existe
  # pas encore ne peut de toute façon appeler personne.
  allowed_origins:
    - http://localhost:5173

validation:
  # Longueur maximale d'une review_note : borne le coût en tokens du prochain
  # enrich_again autant que la surface d'injection de prompt.
  review_note_max_length: 2000
  # Longueur maximale d'une question envoyée à POST /regles/dense — chaque
  # appel a un coût réel (LLM + embedding), cette borne écarte un payload
  # abusif sans gêner un usage normal (la plus longue question du jeu
  # d'acceptance fait ~150 caractères).
  question_max_length: 500

# Clients autorisés à écrire (PATCH). Chacun a son propre jeton (variable
# .env dédiée) : un jeton par expert externe (ex. Élie Sloïm) plutôt qu'un
# secret unique partagé, sans pour autant construire une table Postgres des
# utilisateurs — disproportionné pour ce besoin (un tiers déclaré à la fois).
# Voir docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md
clients:
  - nom: dev
    env_var_token: FASTAPI_API_KEY
  - nom: elie-sloim
    env_var_token: FASTAPI_API_KEY_ELIE
  - nom: david-legrand
    env_var_token: FASTAPI_API_KEY_DAVID
  - nom: formateur
    env_var_token: FASTAPI_API_KEY_FORMATEUR

licence:
  # Le référentiel Opquast est diffusé sous CC BY-SA 4.0 : attribution et
  # partage à l'identique obligatoires. Cette API distribue ce contenu, elle
  # doit donc porter le crédit et le lien vers la licence — c'est une
  # obligation, pas une politesse.
  # Voir docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md
  nom: "CC BY-SA 4.0"
  url: "https://creativecommons.org/licenses/by-sa/4.0/deed.fr"
  attribution: >-
    « Référentiel Opquast - Qualité Numérique » par Opquast, utilisé sous
    licence CC BY-SA 4.0, avec le soutien d'Élie Sloïm (Opquast).
```

- [ ] **Step 2 : Lancer la suite api_regles pour confirmer qu'elle est encore verte (rien de modifié pour l'instant côté .py)**

Run: `uv run pytest tests/unit/api_regles tests/integration/api_regles -q`
Expected: PASS

- [ ] **Step 3 : Modifier `app/api_regles/config.py`**

Remplacer :

```python
def load_manifest() -> dict:
    """Charge la configuration courante de l'API (app/api_regles/manifest.yml)."""
    manifest_path = Path(__file__).parent / "manifest.yml"
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


_MANIFEST = load_manifest()

TITLE: str = _MANIFEST["api"]["title"]
DESCRIPTION: str = _MANIFEST["api"]["description"]
VERSION: str = _MANIFEST["api"]["version"]
PORT: int = _MANIFEST["api"]["port"]
CORS_ALLOWED_ORIGINS: list[str] = _MANIFEST["cors"]["allowed_origins"]
REVIEW_NOTE_MAX_LENGTH: int = _MANIFEST["validation"]["review_note_max_length"]
QUESTION_MAX_LENGTH: int = _MANIFEST["validation"]["question_max_length"]
```

par :

```python
def load_config() -> dict:
    """Charge la configuration courante de l'API (app/api_regles/config.yml)."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


_CONFIG = load_config()

TITLE: str = _CONFIG["api"]["title"]
DESCRIPTION: str = _CONFIG["api"]["description"]
VERSION: str = _CONFIG["api"]["version"]
PORT: int = _CONFIG["api"]["port"]
CORS_ALLOWED_ORIGINS: list[str] = _CONFIG["cors"]["allowed_origins"]
REVIEW_NOTE_MAX_LENGTH: int = _CONFIG["validation"]["review_note_max_length"]
QUESTION_MAX_LENGTH: int = _CONFIG["validation"]["question_max_length"]
```

Puis, plus bas dans le même fichier, remplacer :

```python
LICENCE_NOM: str = _MANIFEST["licence"]["nom"]
LICENCE_URL: str = _MANIFEST["licence"]["url"]
ATTRIBUTION: str = _MANIFEST["licence"]["attribution"]


CLIENTS: list[dict] = _MANIFEST.get("clients", [])


def clients_tokens() -> dict[str, str]:
    """
    {nom_client: jeton} pour chaque client déclaré dans le manifeste.
```

par :

```python
LICENCE_NOM: str = _CONFIG["licence"]["nom"]
LICENCE_URL: str = _CONFIG["licence"]["url"]
ATTRIBUTION: str = _CONFIG["licence"]["attribution"]


CLIENTS: list[dict] = _CONFIG.get("clients", [])


def clients_tokens() -> dict[str, str]:
    """
    {nom_client: jeton} pour chaque client déclaré dans la config.
```

- [ ] **Step 4 : Supprimer `app/api_regles/manifest.yml`**

```bash
git rm app/api_regles/manifest.yml
```

- [ ] **Step 5 : Modifier `tests/unit/api_regles/test_config.py`**

Remplacer l'intégralité du fichier par :

```python
"""La config est la seule source de vérité de la configuration de l'API."""

import pytest

from app.api_regles import config


def test_la_config_expose_le_port():
    assert config.PORT == 8880


def test_la_config_expose_la_longueur_max_de_note():
    assert config.REVIEW_NOTE_MAX_LENGTH == 2000


def test_la_config_expose_la_longueur_max_de_question():
    assert config.QUESTION_MAX_LENGTH == 500


def test_la_config_expose_les_origines_cors():
    assert "http://localhost:5173" in config.CORS_ALLOWED_ORIGINS
    assert "*" not in config.CORS_ALLOWED_ORIGINS


def test_la_config_expose_titre_description_version():
    assert config.TITLE
    assert config.DESCRIPTION
    assert config.VERSION


def test_la_config_expose_lattribution_de_licence():
    """Obligation CC BY-SA : crédit et lien vers la licence."""
    assert config.LICENCE_NOM == "CC BY-SA 4.0"
    assert config.LICENCE_URL.startswith("https://creativecommons.org/licenses/by-sa/4.0")
    assert "Opquast" in config.ATTRIBUTION


def test_la_config_expose_le_client_dev():
    assert {"nom": "dev", "env_var_token": "FASTAPI_API_KEY"} in config.CLIENTS


def _un_seul_client(monkeypatch):
    """Isole CLIENTS : ces tests ne doivent pas dépendre du nombre réel de
    clients déclarés dans la config ni du contenu réel de .env."""
    monkeypatch.setattr(
        config, "CLIENTS", [{"nom": "dev", "env_var_token": "FASTAPI_API_KEY"}]
    )


def test_clients_tokens_renvoie_un_jeton_par_client(monkeypatch):
    _un_seul_client(monkeypatch)
    monkeypatch.setenv("FASTAPI_API_KEY", "jeton-de-test")
    assert config.clients_tokens() == {"dev": "jeton-de-test"}


def test_clients_tokens_refuse_un_secret_vide(monkeypatch):
    """Sans ce garde-fou, ce client serait silencieusement exclu de l'auth."""
    _un_seul_client(monkeypatch)
    monkeypatch.setenv("FASTAPI_API_KEY", "")
    with pytest.raises(RuntimeError, match="FASTAPI_API_KEY"):
        config.clients_tokens()
```

- [ ] **Step 6 : Modifier `tests/unit/api_regles/test_auth.py`**

Remplacer :

```python
    clients déclarés dans le manifeste ni du contenu réel de .env."""
```

par :

```python
    clients déclarés dans la config ni du contenu réel de .env."""
```

- [ ] **Step 7 : Modifier `tests/unit/api_regles/test_acceptance.py`**

Remplacer :

```python
    clients déclarés dans le manifeste ni du contenu réel de .env."""
```

par :

```python
    clients déclarés dans la config ni du contenu réel de .env."""
```

- [ ] **Step 8 : Modifier `tests/integration/api_regles/test_regles.py`**

Remplacer :

```python
    # Les 3 autres clients déclarés dans manifest.yml doivent aussi avoir leur
```

par :

```python
    # Les 3 autres clients déclarés dans config.yml doivent aussi avoir leur
```

- [ ] **Step 9 : Lancer les tests api_regles, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/api_regles tests/integration/api_regles -q`
Expected: PASS

- [ ] **Step 10 : Lint**

Run: `uv run ruff check app/api_regles/config.py tests/unit/api_regles/ tests/integration/api_regles/`
Expected: `All checks passed!`

- [ ] **Step 11 : Commit**

```bash
git add app/api_regles/config.py app/api_regles/config.yml app/api_regles/manifest.yml tests/unit/api_regles/test_config.py tests/unit/api_regles/test_auth.py tests/unit/api_regles/test_acceptance.py tests/integration/api_regles/test_regles.py
git commit -m "refactor: renomme app/api_regles/manifest.yml en config.yml (carte #18)"
```

---

### Task 4 : Scripts à double import + Makefile + docs vivantes

**Files:**
- Modify: `scripts/check_rag_acceptance.py`
- Modify: `scripts/rag_dense_acceptance.py`
- Modify: `scripts/mesure_variantes_chunks.py`
- Modify: `scripts/mesure_multi_vecteurs_chunks.py`
- Modify: `scripts/mesure_combinaisons_chunks.py`
- Modify: `Makefile`
- Modify: `docs/agent/03_references_impl.md`
- Modify: `docs/agent/04_contexte_actif.md`

**Interfaces:**
- Consumes: `app.ingestion.config.load_config()` (Task 1), `app.retrieval.config.load_config()` (Task 2) — les deux existent déjà à ce stade.

**Dépend de :** Task 1 et Task 2 (les deux modules `config.py` doivent exister).

- [ ] **Step 1 : Modifier `scripts/check_rag_acceptance.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config as load_ingestion_config  # noqa: E402
from app.retrieval.config import load_config as load_retrieval_config  # noqa: E402
```

Puis, ligne 59, remplacer :

```python
    config = load_manifest()["rag_acceptance"]
```

par :

```python
    config = load_retrieval_config()["rag_acceptance"]
```

Puis, lignes 106-108, remplacer :

```python
        manifest = load_manifest()
        embedding_role = manifest["embedding"]
        decomposition_role = manifest["decomposition"]
```

par :

```python
        embedding_role = load_ingestion_config()["embedding"]
        decomposition_role = load_retrieval_config()["decomposition"]
```

- [ ] **Step 2 : Modifier `scripts/rag_dense_acceptance.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config as load_ingestion_config  # noqa: E402
from app.retrieval.config import load_config as load_retrieval_config  # noqa: E402
```

Puis, lignes 165-167, remplacer :

```python
    manifest = load_manifest()
    embedding_role = manifest["embedding"]
    decomposition_role = manifest["decomposition"]
```

par :

```python
    embedding_role = load_ingestion_config()["embedding"]
    decomposition_role = load_retrieval_config()["decomposition"]
```

- [ ] **Step 3 : Modifier `scripts/mesure_variantes_chunks.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config as load_ingestion_config  # noqa: E402
from app.retrieval.config import load_config as load_retrieval_config  # noqa: E402
```

Puis, lignes 197-198, remplacer :

```python
    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
```

par :

```python
    embedding_role = load_ingestion_config()["embedding"]
    decomposition_role = load_retrieval_config()["decomposition"]
```

- [ ] **Step 4 : Modifier `scripts/mesure_multi_vecteurs_chunks.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config as load_ingestion_config  # noqa: E402
from app.retrieval.config import load_config as load_retrieval_config  # noqa: E402
```

Puis, lignes 277-278, remplacer :

```python
    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
```

par :

```python
    embedding_role = load_ingestion_config()["embedding"]
    decomposition_role = load_retrieval_config()["decomposition"]
```

- [ ] **Step 5 : Modifier `scripts/mesure_combinaisons_chunks.py`**

Remplacer :

```python
from app.ingestion.llm_client import load_manifest  # noqa: E402
```

par :

```python
from app.ingestion.config import load_config as load_ingestion_config  # noqa: E402
from app.retrieval.config import load_config as load_retrieval_config  # noqa: E402
```

Puis, lignes 266-267, remplacer :

```python
    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
```

par :

```python
    embedding_role = load_ingestion_config()["embedding"]
    decomposition_role = load_retrieval_config()["decomposition"]
```

- [ ] **Step 6 : Modifier le `Makefile`**

Remplacer (ligne ~103, commentaire de `embed-rules`) :

```make
## Recalcule l'embedding de toutes les règles (modèle et dimension définis
## dans app/ingestion/manifest.yml, rôle embedding), puis sauvegarde les
## données réelles
```

par :

```make
## Recalcule l'embedding de toutes les règles (modèle et dimension définis
## dans app/ingestion/config.yml, rôle embedding), puis sauvegarde les
## données réelles
```

Remplacer (ligne ~148-149) :

```make
# Port lu dans le manifeste, seule source de vérité.
API_REGLES_PORT = $(shell grep 'port:' app/api_regles/manifest.yml | tr -d ' ' | cut -d: -f2)
```

par :

```make
# Port lu dans la config, seule source de vérité.
API_REGLES_PORT = $(shell grep 'port:' app/api_regles/config.yml | tr -d ' ' | cut -d: -f2)
```

- [ ] **Step 7 : Modifier `docs/agent/03_references_impl.md`**

Remplacer le tableau (lignes 11-23) :

```markdown
| Prix/modèle LLM à utiliser au prochain run (enrichissement, embedding) | `app/ingestion/manifest.yml` | — |
| Seuils du jeu d'acceptance RAG (`top_n`, `taux_reussite_minimum`) | `app/ingestion/manifest.yml` (section `rag_acceptance`) | — |
```

par :

```markdown
| Prix/modèle LLM à utiliser au prochain run (enrichissement, embedding) | `app/ingestion/config.yml` | — |
| Seuils du jeu d'acceptance RAG (`top_n`, `taux_reussite_minimum`) | `app/retrieval/config.yml` (section `rag_acceptance`) | — |
```

Remplacer :

```markdown
| Version de prompt ayant produit une règle donnée (déjà en base) | Colonne `regle.prompt_version` | `manifest.yml` et le frontmatter du prompt ne le savent pas — un `enrich_again` partiel peut mélanger les versions règle par règle |
```

par :

```markdown
| Version de prompt ayant produit une règle donnée (déjà en base) | Colonne `regle.prompt_version` | `config.yml` et le frontmatter du prompt ne le savent pas — un `enrich_again` partiel peut mélanger les versions règle par règle |
```

Remplacer :

```markdown
| Configuration de l'API données (port, origines CORS, titre, version du contrat) | `app/api_regles/manifest.yml` | — |
| Jetons Bearer des écritures de l'API données (un par client nommé) | `app/api_regles/manifest.yml` (section `clients`) + `.env` (une variable par client) | — |
```

par :

```markdown
| Configuration de l'API données (port, origines CORS, titre, version du contrat) | `app/api_regles/config.yml` | — |
| Jetons Bearer des écritures de l'API données (un par client nommé) | `app/api_regles/config.yml` (section `clients`) + `.env` (une variable par client) | — |
```

Ajouter une ligne pour les rôles retrieval (absente jusqu'ici) juste après la ligne `rag_acceptance` :

```markdown
| Rôles LLM du retrieval (decomposition, jugement, guardrail) | `app/retrieval/config.yml` | — |
```

- [ ] **Step 8 : Modifier `docs/agent/04_contexte_actif.md`**

Remplacer :

```markdown
- Manifest des roles/modeles: `app/ingestion/manifest.yml`
```

par :

```markdown
- Config des roles/modeles: `app/ingestion/config.yml` (enrichissement, embedding), `app/retrieval/config.yml` (decomposition, jugement, guardrail, rag_acceptance)
```

- [ ] **Step 9 : Lancer la suite complète, vérifier qu'elle passe**

Run: `uv run pytest tests/unit tests/integration -q`
Expected: PASS, tous les tests verts (259 tests + les 4 nouveaux de
`test_config.py` retrieval = 263)

- [ ] **Step 10 : Lint**

Run: `uv run ruff check scripts/ app/`
Expected: `All checks passed!`

- [ ] **Step 11 : Vérifier manuellement le Makefile**

Run: `make -n embed-rules 2>&1 | head -5` (ou toute cible qui dépend de
`API_REGLES_PORT`, ex. `make -n api-regles`)
Expected: la commande s'affiche sans erreur, le port résolu vaut `8880`

- [ ] **Step 12 : Commit**

```bash
git add scripts/check_rag_acceptance.py scripts/rag_dense_acceptance.py scripts/mesure_variantes_chunks.py scripts/mesure_multi_vecteurs_chunks.py scripts/mesure_combinaisons_chunks.py Makefile docs/agent/03_references_impl.md docs/agent/04_contexte_actif.md
git commit -m "refactor: migre les scripts a double import vers config.py (carte #18)"
```

---

### Task 5 : Vérification finale, CHANGELOG, Kanboard

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1 : Confirmer qu'aucune référence à `load_manifest`/`manifest.yml` ne subsiste**

Run: `grep -rln "load_manifest" --include="*.py" . | grep -v __pycache__`
Expected: aucune sortie (0 résultat)

Run: `find . -iname "manifest.yml" -not -path "./.git/*"`
Expected: aucune sortie (0 résultat)

Run: `grep -rln "manifest\.yml\|load_manifest" --include="*.md" docs/agent/ Makefile`
Expected: aucune sortie (0 résultat) — hors `docs/superpowers/specs/` et
`jury/decisions/` historiques, volontairement non touchés (hors périmètre,
cf. spec)

- [ ] **Step 2 : Lancer la suite complète une dernière fois**

Run: `uv run pytest tests/unit tests/integration -q`
Expected: PASS

- [ ] **Step 3 : Ajouter une entrée dans `CHANGELOG.md`**

Ajouter en tête (juste après la ligne `# Changelog` et son paragraphe
d'intro, avant la première entrée datée existante) :

```markdown
## 2026-09-16 — Claude Code

- **Config LLM par domaine, dette de la carte Kanboard #18 payée** (spec
  `docs/superpowers/specs/2026-09-16-config-llm-par-domaine-design.md`,
  plan `docs/superpowers/plans/2026-09-16-config-llm-par-domaine-implementation.md`,
  exécuté en inline, 4 tâches) : `manifest.yml`/`load_manifest()` renommés
  en `config.yml`/`load_config()` partout — le nom "manifest" décrivait un
  inventaire figé, pas les paramètres réglables (modèles, prix, seuils,
  température) qu'il contenait réellement.
  `app/ingestion/manifest.yml` scindé en `app/ingestion/config.yml`
  (`enrichissement`, `embedding`) et `app/retrieval/config.yml` (`rag_acceptance`,
  `decomposition`, `jugement`, `guardrail`, nouveau module — corrige la
  mauvaise localisation des 3 derniers rôles, qui vivaient en ingestion
  faute d'endroit dédié). `app/api_regles/manifest.yml` renommé à
  l'identique (fichier déjà bien situé). Coupure nette, 18 fichiers
  Python migrés, Makefile et docs/agent/ vivantes mis à jour, suite de
  tests inchangée en comportement (263 tests verts, +4 nouveaux pour
  `app/retrieval/config.py`).
```

- [ ] **Step 4 : Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: trace le chantier config LLM par domaine dans CHANGELOG"
```

- [ ] **Step 5 : Terminer la carte Kanboard #18**

Ajouter un commentaire sur la carte #18 résumant le résultat (fichiers
créés/renommés, coupure nette, tests verts), puis la déplacer en colonne
"Done" (`column_id: 4`) **sans la fermer** (une carte fermée disparaît du
board) — même méthode que les cartes #19/#20 dans ce projet (`https://kanban.david-legrand.fr/jsonrpc.php`, voir mémoire
assistant `kanboard_access`).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : les 3 modules `config.py`/`config.yml`
  (Task 1, 2, 3), tous les appelants recensés — y compris les 2 scripts à
  double import (`check_rag_acceptance.py`, `rag_dense_acceptance.py`) que
  le spec n'avait pas identifiés explicitement (il n'en citait que 3 sur
  5) — corrigés dans ce plan après vérification exhaustive par `grep`
  (Task 4), le Makefile et les docs vivantes (Task 4), la coupure nette
  (suppression des `.yml` originaux dans chaque tâche concernée).
- **Écart avec le spec, assumé et documenté** : le spec ne listait que 3
  scripts à double import (`mesure_variantes_chunks.py`,
  `mesure_multi_vecteurs_chunks.py`, `mesure_combinaisons_chunks.py`) ; la
  vérification exhaustive par `grep` pour ce plan en a trouvé 2 de plus
  (`check_rag_acceptance.py`, `rag_dense_acceptance.py`, qui lisent aussi
  `embedding` ET `decomposition`/`rag_acceptance`) — les 5 sont traités
  dans la Task 4.
- **Cohérence des types** : `load_config() -> dict` utilisé identiquement
  dans les 3 modules (Task 1 Step 2, Task 2 Step 2, Task 3 Step 3) et par
  tous leurs appelants.
- **Pas de placeholder** : chaque remplacement de code est donné
  intégralement (avant/après), y compris le contenu complet des 3 nouveaux
  `config.yml` et du nouveau fichier de test.
