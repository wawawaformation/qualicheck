# Guardrail de périmètre — intégration en premier maillon d'`api_regles` — design

2026-09-13

## Contexte

Le Temps 2 du mécanisme de refus (jugement LLM sur les candidats
retournés par `retrieve()`, `app/retrieval/jugement.py`) a été mesuré en
réel le 2026-09-11 : la famille `sans_reponse` plafonne à 40-55% selon
le modèle, très loin du seuil garde-fou de 90%. Diagnostic : un **biais
de sélection** — présenter une liste de candidats au LLM le pousse à y
choisir quelque chose, même quand rien ne convient (cas net : « palmarès
Coupe du monde » → une règle citée à tort, deux fois, malgré un
contre-exemple dédié dans le prompt).

Hypothèse testée en conséquence : `GuardrailClient`
(`app/retrieval/guardrail.py`) classe une question dans/hors périmètre
Opquast **sans voir aucun candidat** — mesuré isolément à **100% sur les
20 cas `sans_reponse`, 97,9% sur les 94 cas valides**
(`docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md`). Client
écrit et testé unitairement, jamais intégré à un pipeline réel.

Décision de placement actée en session précédente (discussion du
2026-09-11, carte Kanboard #19, diagramme
`conception/3_autre_us/us2_question_libre/diagramme_retrieval_refus_citation.drawio`) :
le guardrail va en **premier maillon d'`api_regles`** (dans
`POST /regles/dense`), pas dans une future couche agent — il est
stateless (mesuré sans historique de discussion), rien n'empêche de le
brancher dès maintenant.

## Objectif

1. Intégrer `GuardrailClient` comme première étape de
   `chercher_regles_dense` : si la question est hors périmètre, retour
   `[]` immédiat, sans appeler décomposition/retrieval/jugement.
2. Alléger le prompt de `JugementClient`
   (`app/retrieval/prompts/juger_pertinence.md`) en conséquence : son
   rôle se réduit à sélectionner parmi des candidats déjà dans le
   périmètre, il n'a plus à porter la distinction Opquast-organisme vs
   règle de qualité web (désormais la responsabilité du guardrail).
3. Mesurer en réel le taux combiné (guardrail + jugement) sur les 114
   cas d'acceptance, pour confirmer que `sans_reponse` s'approche
   désormais du seuil garde-fou.

## Hors périmètre

- Modifier `retrieve()` ou le contrat `RegleAvecScore` — inchangés.
- La couche agent (mémoire, historique de discussion, choix d'outils) —
  toujours hors périmètre `api_regles`.
- Reformuler à nouveau le guardrail lui-même (son prompt reste celui
  déjà mesuré à 100%/97,9% — on ne touche pas à ce qui fonctionne).

## Architecture

### `chercher_regles_dense` (modifié en place)

Le log initial (question + client) reste la première instruction — pour
observer toute requête entrante, y compris celles rejetées par le
guardrail. Le guardrail est appelé juste après, avant tout autre travail
(y compris le chargement de `top_n`) :

```python
def chercher_regles_dense(...) -> list[RegleAvecScore]:
    """..."""
    logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

    guardrail_client = GuardrailClient()
    if not guardrail_client.est_dans_le_perimetre(requete.question):
        logger.info(
            "Recherche dense par %s — question hors périmètre (guardrail), refus direct",
            client_nom,
        )
        return []

    top_n = load_manifest()["rag_acceptance"]["top_n"]
    # ... reste de la fonction strictement inchangé (retrieve, jugement, réponse)
```

`GuardrailClient.est_dans_le_perimetre()` ne lève jamais (fail-open
interne, déjà testé) — pas besoin de l'envelopper dans le `try/except`
existant autour de `retrieve()`. Une panne technique du guardrail
dégrade silencieusement vers « dans le périmètre » (comportement actuel
inchangé), jamais vers un refus par accident.

### Prompt de jugement allégé

`app/retrieval/prompts/juger_pertinence.md` retire les exemples
Opquast-organisme/VPTCS/gestion de projet (désormais filtrés en amont
par le guardrail), garde :

- la distinction proximité thématique/lexicale ≠ réponse réelle (utile
  même entre candidats déjà dans le périmètre — ex. le cas mesuré
  « handicap » : une règle sur les moyens de contact citée à tort pour
  une question sur le recrutement d'un panel de testeurs handicapés) ;
- le refus par liste vide en cas de doute (toujours légitime : un
  candidat peut être dans le périmètre général sans répondre à la
  question précise — ex. règle non retrouvée par le retrieval malgré
  une question valide).

## Tests

- **Intégration** (`tests/integration/api_regles/test_regles_dense.py`) :
  ajouter `@patch("app.api_regles.regles.GuardrailClient")` sur tous les
  tests qui vont jusqu'au bout du chemin de succès (comme `JugementClient`
  précédemment), `mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True`
  par défaut pour ne pas casser les tests existants.
- **2 nouveaux tests** :
  - hors périmètre → `200` + `[]`, `retrieve()`/`DecompositionClient`/
    `EmbeddingClient`/`JugementClient` jamais appelés (`assert_not_called`).
  - dans périmètre → comportement inchangé (non-régression explicite).
- **Pas de nouveau test unitaire pour `GuardrailClient` lui-même** — déjà
  couvert (`tests/unit/retrieval/test_guardrail.py`, existant).

## Validation

Après intégration, `make api-regles-dense-acceptance` rejoué en réel sur
les 114 cas (coût réel à confirmer avant exécution, même ordre de
grandeur que les mesures précédentes ~0,01-0,02 €) : lire le nouveau
taux de `sans_reponse` et décider si `is_acceptable()` doit retirer son
exclusion de cette famille (actuellement exclue,
`app/ingestion/rag_acceptance.py::is_acceptable`).

## Traçage

`CHANGELOG.md` à l'exécution ; `TODO.md` (carte Kanboard #19 → fermée
si le résultat confirme l'intégration) ; mémoire assistant
`refus_architecture_trois_decisions` mise à jour avec le résultat.
