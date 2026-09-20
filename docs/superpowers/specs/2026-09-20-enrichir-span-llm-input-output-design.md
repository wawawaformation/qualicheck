# Spec — Enrichir les spans `appel_llm` avec input / output

**Date** : 2026-09-20  
**Outil** : OpenCode  
**Statut** : approuvé pour implémentation  
**Fichiers concernés** : `app/observability/tracing.py`, `app/agent_us2/loop.py`, `tests/unit/observability/test_tracing.py`, `CHANGELOG.md`

## Contexte

L'agent US2 est instrumenté depuis l'incrément A2 : chaque exécution produit un
arbre de spans OpenTelemetry (`repondre` → `appel_llm`, `appel_outil`). Les
spans `appel_llm` portent déjà des métriques (tour, tokens d'entrée / de
sortie), mais pas le contenu échangé. Cela limite la valeur diagnostique :
les métriques de coût sont visibles, mais pas la question / la réponse / les
tool_calls de chaque tour.

## Objectif

Ajouter sur chaque span `appel_llm` deux attributs structurés :

- `llm.input` : la liste des messages envoyés au modèle pour cet appel.
- `llm.output` : la réponse du modèle, y compris les `tool_calls` éventuels.

Les valeurs doivent rester exploitables dans Langfuse, sans dépasser les
limites d'attributs OTel/Langfuse.

## Décisions

### 1. Quoi stocker : contenu structuré (option C)

- **Input** : liste JSON compacte des messages, chaque élément contenant :
  - `role` (`system`, `user`, `assistant`, `tool`)
  - `content` (texte brut, potentiellement vide)
  - `tool_call_id` (uniquement pour les `ToolMessage`)
- **Output** : objet JSON compact avec :
  - `role` : `assistant`
  - `content` : texte généré (peut être vide si tool_calling)
  - `tool_calls` : liste des appels d'outils structurés (`name`, `args`)

On ne stocke pas les métadonnées lourdes (`usage_metadata`, `response_metadata`,
ids internes LangChain) afin de garder les attributs lisibles et compacts.

### 2. Où mettre la logique : helper dans `app/observability/tracing.py` (approche 2)

Une fonction `set_llm_span_io(span, messages, ai_message, max_len=4000)` est
ajoutée au module d'observabilité. La boucle `repondre()` dans
`app/agent_us2/loop.py` l'appelle juste après `_appeler_llm(...)`, à
l'intérieur du span `appel_llm`.

Cette approche garde la logique de sérialisation / troncature isolée du code
métier, testable unitairement et réutilisable si d'autres points d'entrée
appellent un LLM plus tard.

### 3. Plafonnement : tronquer à 4000 caractères par attribut (option B)

Chaque attribut (`llm.input`, `llm.output`) est tronqué individuellement à
`max_len` caractères. La troncature conserve le début et la fin du JSON, avec
la marque `[... tronqué ...]` au milieu.

Deux attributs booléens indiquent l'état :

- `llm.input_truncated`
- `llm.output_truncated`

Cela évite d'atteindre les limites de taille des attributs OTel / Langfuse et
de surcharger l'export sans valeur ajoutée.

## Interface

```python
def set_llm_span_io(
    span: trace.Span,
    messages: Sequence[SystemMessage | HumanMessage | AIMessage | ToolMessage],
    ai_message: AIMessage,
    max_len: int = 4000,
) -> None:
    """Sérialise et attache input/output LLM au span courant.

    - input : liste JSON des messages (role, content, tool_call_id).
    - output : JSON de la réponse AI (role, content, tool_calls).
    - Les deux attributs sont tronqués séparément à `max_len` caractères.
    - `llm.input_truncated` / `llm.output_truncated` reflètent l'état.
    """
```

## Modification de `app/agent_us2/loop.py`

À l'intérieur du bloc `with tracer.start_as_current_span("appel_llm", ...)` :

```python
ai_message = _appeler_llm(llm, messages)
set_llm_span_io(span, messages, ai_message)
usage = ai_message.usage_metadata or {}
span.set_attribute("tokens_entree", usage.get("input_tokens", 0))
span.set_attribute("tokens_sortie", usage.get("output_tokens", 0))
```

L'appel à `set_llm_span_io` se place juste après `_appeler_llm`, avant la
mise à jour des compteurs de tokens.

## Tests

Ajout d'un test dans `tests/unit/observability/test_tracing.py` qui couvre :

1. Sérialisation simple d'un `HumanMessage` en input.
2. Sérialisation d'un `AIMessage` avec `tool_calls` en output.
3. Sérialisation d'un `ToolMessage` avec `tool_call_id` en input.
4. Marquage `llm.input_truncated = False` quand l'input tient dans la limite.
5. Marquage `llm.input_truncated = True` quand l'input dépasse `max_len`.
6. Gestion d'un `content` vide.
7. Vérification que le JSON tronqué reste valide / lisible (pas de
   corruption structurelle, marque centrale visible).

## Non-scope

- Pas d'enrichissement du span racine `repondre` (la réponse finale reste
  dans la payload API, pas dans les attributs de span).
- Pas d'enrichissement du span `appel_outil`.
- Pas de transformation des messages en format Langfuse natif : on reste sur
  des attributs OTel génériques (`llm.input`, `llm.output`).
- Pas de redondance avec `trace_id` déjà exposé dans la réponse API.

## Prochaine étape

Passer à l'écriture du plan d'implémentation via `writing-plans`.
