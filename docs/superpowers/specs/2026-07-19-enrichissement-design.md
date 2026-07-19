---
title: "Design — Étape 3 : Enrichissement"
subtitle: "Appel LLM (Kimi K2.6) avec retry logic et génération de stratégies d'analyse"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Vue d'ensemble

L'Étape 3 transforme chaque `Rule` agrégée en objet enrichi `EnrichedRule`, en appelant un agent LLM (Kimi K2.6 sur Azure) pour générer trois champs critiques :

- **`strategie_analyse`** : méthode d'extraction (statique, playwright, manuel, ou autre découverte)
- **`strategie_justification`** : explication du choix
- **`guide_analyse`** : instruction opérationnelle pour l'agent d'audit

Pipeline :
```
Rules (collection Étape 2)
  ↓
enrich_rules(rules: Rules) → EnrichedRules
  ↓
  Pour chaque Rule :
    - Construire prompt (intitule + solution + controle + objectifs/tags/phases)
    - Appel LLM via LangChain (retry 3×, backoff 2s/4s/8s)
    - Parser réponse JSON
    - Log : timeout individuel, erreur critique, synthèse final
  ↓
EnrichedRules (collection d'EnrichedRule)
```

## Modèles de données

### EnrichedRule

Extension de `Rule` avec champs d'enrichissement (dans `app/ingestion/schema.py`) :

```python
class EnrichedRule(BaseModel):
    # Champs hérités de Rule
    id: int
    number: int
    intitule: str
    objectifs: list[str]
    tags: list[str]
    phases: list[str]
    slug: str
    solution: str
    controle: str
    
    # Champs d'enrichissement LLM
    strategie_analyse: str          # Valeur libre (découverte possible)
    strategie_justification: str    # Explication du choix
    guide_analyse: str              # Instruction pour l'agent d'audit
    strategie_source: str = "ia_import"  # Trace : première ingestion
    llm_provider: str = "kimi-k2.6"     # Trace : modèle utilisé
```

### EnrichedRules

Collection non-vide d'`EnrichedRule` (dans `app/ingestion/agregation.py` ou fichier séparé) :

```python
class EnrichedRules:
    def __init__(self, enriched_rules: list[EnrichedRule]):
        if not enriched_rules:
            raise ValueError("Collection cannot be empty")
        self.enriched_rules = enriched_rules
    
    @property
    def regles(self):
        """Rétrocompatibilité : alias français."""
        return self.enriched_rules
```

## Prompt et Few-Shot

**Fichier** : `app/ingestion/prompts/enrich_rule.md`

Contient :
1. **Instructions** : rôle du LLM, contexte d'audit web, tâche précise
2. **Format attendu** : structure JSON exacte, 3 champs obligatoires
3. **Few-shot** : 1-2 exemples complets (règle → réponse JSON idéale)
4. **Contexte de la règle** : placeholders `{intitule}`, `{solution}`, `{controle}`, `{objectifs}`, `{tags}`, `{phases}`

Format du prompt (pseudocode) :
```
Tu es un expert en audit web qualité...

Pour cette règle :
- Intitulé : {intitule}
- Solution : {solution}
- Contrôle : {controle}
- Objectifs : {objectifs}
- Tags : {tags}
- Phases : {phases}

Génère une réponse JSON stricte avec ces 3 champs :
{
  "strategie_analyse": "...",
  "strategie_justification": "...",
  "guide_analyse": "..."
}

Exemple :
Intitulé : "Les images ont un attribut alt"
→ Réponse JSON : { "strategie_analyse": "statique", ... }
```

## Implémentation

### Modules

#### `app/ingestion/llm_client.py` (nouveau)

Encapsule LangChain + Azure :

```python
from langchain_openai import AzureChatOpenAI
from langchain.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel

class EnrichmentOutput(BaseModel):
    strategie_analyse: str
    strategie_justification: str
    guide_analyse: str

class LLMClient:
    def __init__(self):
        # Initialise AzureChatOpenAI avec credentials .env
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            deployment_name=os.getenv("AZURE_DEPLOYMENT_INGESTION"),
            model_name="kimi-k2.6"
        )
        self.parser = JsonOutputParser(pydantic_object=EnrichmentOutput)
    
    def load_prompt(self) -> PromptTemplate:
        # Charge le prompt depuis app/ingestion/prompts/enrich_rule.md
        # Retourne un PromptTemplate prêt à formatter
        pass
    
    def enrich_single_rule(self, rule: Rule) -> EnrichedRule:
        # Construit la chaîne LangChain
        # Appelle LLM avec retry (tenacity)
        # Parse réponse JSON
        # Crée EnrichedRule
        pass
```

#### `app/ingestion/enrichissement.py`

Orchestration :

```python
def enrich_rules(rules: Rules) -> EnrichedRules:
    """
    Enrichit une collection de Rules via LLM.
    
    Args:
        rules: Collection Rules validée (Étape 2)
    
    Returns:
        Collection EnrichedRules avec tous les champs enrichis
    
    Raises:
        ValueError: Si une règle échoue enrichissement (3 timeouts)
    """
    llm_client = LLMClient()
    enriched_list = []
    
    for rule in rules.regles:
        try:
            enriched = llm_client.enrich_single_rule(rule)
            enriched_list.append(enriched)
        except TimeoutError as e:
            logger.error(f"Règle {rule.number} — enrichissement : KO (3 timeouts)")
            raise ValueError(f"Enrichissement échoué pour règle {rule.number}") from e
        except Exception as e:
            logger.error(f"Règle {rule.number} — enrichissement : KO ({e})")
            raise
    
    enriched_rules = EnrichedRules(enriched_list)
    logger.info(f"Enrichissement : {len(enriched_list)} règles enrichies")
    return enriched_rules
```

### Logging

Granularité :
- **Chaque timeout** : `logger.warning(f"Règle N — enrichissement : tentative M timeout")`
- **Erreur critique** : `logger.error(f"Règle N — enrichissement : KO (3 timeouts)")`
- **Synthèse succès** : `logger.info(f"Enrichissement : X règles enrichies")`

### Tests

**Fichier** : `tests/unit/ingestion/test_enrichissement.py`

- Mock Azure API (via LangChain mock ou `unittest.mock`)
- Test réussite : réponse JSON valide → `EnrichedRule` créée
- Test timeout : 3 tentatives échouées → exception levée
- Test parsing : JSON invalide → exception levée
- Test collection : `EnrichedRules` non-vide

Pas de tests d'intégration Azure pour l'instant (coûteux).

## Configuration et dépendances

### `.env`

Variables existantes suffisent :
- `AZURE_AI_ENDPOINT`
- `AZURE_AI_API_KEY`
- `AZURE_DEPLOYMENT_INGESTION` (Kimi K2.6)

### `pyproject.toml`

Ajouter LangChain :
```toml
dependencies = [
    ...
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
]
```

Ou version plus spécifique après vérification de la stabilité.

## Gestion des erreurs

Principe **fail-fast** :

- Timeout unique (tentative 1, 2 ou 3) : log warning, retry
- 3 timeouts sur la même règle : log error, raise `ValueError`
- Parsing JSON invalide : raise `ValueError`
- Champ manquant dans la réponse : raise `ValueError`

Pas de valeurs par défaut, pas de stockage partiel.

## Convention de nommage

- **Code** : anglais (`EnrichedRule`, `enrich_rules`, `LLMClient`)
- **Docs/comments** : français
- **Logging** : français

## Scope et limites (MVP)

✅ **Inclus** :
- Appel LLM (Kimi K2.6)
- Retry logic (3 tentatives, backoff 2s/4s/8s via tenacity)
- Parsing JSON stricte
- Logging granulaire
- Tests unitaires avec mocks

❌ **Exclus** (post-MVP) :
- Tests d'intégration Azure
- Cache local pour les enrichissements réussis
- Métriques/monitoring détaillé
- Optimisations batch

## Prochaines étapes

1. Implémentation (`enrichissement.py`, `llm_client.py`, `schema.py`)
2. Tests unitaires
3. Rédaction du prompt (`enrich_rule.md`)
4. Intégration dans `scripts/ingestion.py` (Étape 4+)
