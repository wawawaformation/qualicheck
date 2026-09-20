# Spec — Renommage et enrichissement des spans de l'agent US2

**Date** : 2026-09-20  
**Outil** : OpenCode  
**Statut** : approuvé pour implémentation  
**Fichiers concernés** : `app/agent_us2/config.yml`, `app/agent_us2/loop.py`,
`app/observability/tracing.py`, `tests/unit/agent_us2/test_loop_tracing.py`,
`tests/unit/observability/test_tracing.py`, `CHANGELOG.md`

## Contexte

L'agent US2 (question libre, incrément A1/A2) produit actuellement des spans
OpenTelemetry nommés `repondre`, `appel_llm` et `appel_outil`. Ces noms sont
contextuels à l'agent, mais deviendront peu identifiables quand d'autres
services (audit, dialogue, autres US) produiront aussi des traces. De plus,
les spans LLM ne portent pas la configuration du modèle, et les spans outil
ne montrent pas ce qui a été envoyé et reçu.

## Objectif

1. Renommer les spans avec un préfixe métier `questions_libres` pour les
   rendre uniques et compréhensibles à grande échelle.
2. Ajouter `provider`, `model` et `temperature` sur les spans LLM.
3. Ajouter `input` / `output` structurés et tronqués sur les spans outil.

## Décisions

### 1. Renommage des spans

| Ancien nom | Nouveau nom |
|---|---|
| `repondre` | `questions_libres` |
| `appel_llm` | `questions_libres.appel_llm` |
| `appel_outil` | `questions_libres.appel_outil` |

Le séparateur `.` est choisi pour sa sémantique objet : chaque span est un
membre de l'entité `questions_libres`. Cette convention sera documentée
pour être réutilisée par les futurs agents/services du projet.

### 2. Configuration LLM enrichie

`app/agent_us2/config.yml` gagne deux champs sous `llm` :

```yaml
llm:
  provider: azure
  model: gpt-5.4-mini
  env_var_endpoint: AZURE_AI_ENDPOINT
  env_var_api_key: AZURE_AI_API_KEY
  env_var_deployment: AZURE_MODEL_GPT_MINI
  temperature: 0
  ...
```

Le fichier `.env` continue de lister les variables d'environnement (il ne
définit pas le modèle métier). `config.yml` reste la source de vérité du
modèle logique utilisé.

### 3. Attributs sur les spans LLM

Sur chaque span `questions_libres.appel_llm`, en complément de `llm.input` /
`llm.output` existants, on ajoute :

```text
llm.provider     <- config["llm"]["provider"]
llm.model        <- config["llm"]["model"]
llm.temperature  <- config["llm"]["temperature"]
```

### 4. Attributs sur les spans outil

Une nouvelle fonction `set_tool_span_io(span, tool_input, tool_output,
max_len=4000)` est ajoutée dans `app/observability/tracing.py`.

Sur chaque span `questions_libres.appel_outil`, on ajoute :

```text
outil.input            <- JSON compact des arguments de l'outil
outil.output           <- texte JSON retourné par l'outil
outil.input_truncated  <- booléen
outil.output_truncated <- booléen
```

La logique de troncature est identique à celle de `set_llm_span_io` :
- limite par défaut de 4000 caractères par attribut ;
- marqueur central `[... tronqué ...]` ;
- booléens reflétant l'état.

### 5. Tests

- `tests/unit/observability/test_tracing.py` : tests pour
  `set_tool_span_io` (sérialisation, troncature, content vide).
- `tests/unit/agent_us2/test_loop_tracing.py` : mise à jour des noms de
  spans attendus et vérification des nouveaux attributs (`llm.provider`,
  `llm.model`, `llm.temperature`, `outil.input`, `outil.output`).

### 6. Non-régression

- Le `trace_id` exposé dans la réponse API reste inchangé.
- Le comportement fonctionnel de `repondre()` reste inchangé.
- L'export OTLP et JSONL continue de fonctionner.

## Prochaine étape

Passer à l'écriture du plan d'implémentation via `writing-plans`.
