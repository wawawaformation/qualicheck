# Tool `chercher_regles_mots_cles`

## Docstring

Cherche les règles Opquast contenant des mots ou une syntaxe exacte
(grammaire façon moteur de recherche : `mot1 mot2` = ET, `"phrase exacte"`,
`-exclusion`, `mot1 OR mot2` = union, chaînable). À utiliser quand la
question de l'utilisateur cite un terme technique précis (ex. `aria-expanded`,
`SIRET`, `tabindex`) plutôt qu'une reformulation — le retrieval sémantique
dilue ce type de terme exact, cette recherche ne le dilue pas.

Implémente `GET /regles?q=` (`app/api_regles/regles.py`,
`app/api_regles/recherche.py` pour la grammaire complète du parseur).

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `q` | string | non | Requête au format de la grammaire de recherche (mots, phrase exacte, exclusion, OR) |
| `outil` | list[string] | non | Filtre par stratégie d'analyse : `statique`, `playwright`, `vision`, `manuel` (valeurs fermées) |

Au moins un des deux paramètres doit être fourni. Les deux se combinent en
ET (« règles sur les formulaires **et** vérifiables manuellement ») ; les
valeurs de `outil` entre elles sont un OU. Le filtre matche en *contient*,
donc `outil=playwright` remonte aussi les stratégies composites
(`playwright+vision`).

Le filtre `review_status` de l'endpoint est volontairement hors de la
surface de l'agent : c'est de la gouvernance interne (annotation de revue
humaine), sans intérêt pour quelqu'un qui pose une question.

## Sortie

Liste de règles enrichies (peut être vide), sans score — correspondance
exacte ou non, pas de notion de pertinence graduée :

```json
[
  { "numero": 12, "intitule": "...", "theme": "...", "...": "..." }
]
```

- Liste vide : aucune règle ne contient les termes demandés — l'agent peut
  alors retenter avec `chercher_regles_semantique` avant de conclure à un
  refus.
