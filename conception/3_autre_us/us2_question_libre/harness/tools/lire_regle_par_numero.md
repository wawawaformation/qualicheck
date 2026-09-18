# Tool `lire_regle_par_numero`

## Docstring

Lit une règle Opquast précise par son numéro. À utiliser quand la
question de l'utilisateur (ou l'historique de la discussion) cite
explicitement un numéro de règle, ou quand l'agent a besoin de relire le
détail complet d'une règle déjà citée avant de rédiger sa réponse.

Implémente `GET /regles/{numero}` (`app/api_regles/regles.py`).

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `numero` | int | oui | Numéro Opquast de la règle |

## Sortie

Une règle enrichie, ou une erreur si le numéro est inconnu :

```json
{ "numero": 12, "intitule": "...", "theme": "...", "...": "..." }
```

- Numéro inconnu : `404` côté API — l'agent doit le traiter comme
  "cette règle n'existe pas", pas retenter avec un autre numéro deviné.
