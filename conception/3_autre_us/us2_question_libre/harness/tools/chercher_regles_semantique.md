# Tool `chercher_regles_semantique`

## Docstring

Cherche les règles Opquast pertinentes pour une question en langage
naturel, par similarité sémantique. Le guardrail de périmètre et le
jugement de pertinence sont déjà intégrés côté API — un retour vide
signifie soit hors périmètre, soit aucune règle réellement pertinente
(refus explicite, jamais une invention). À utiliser en priorité pour une
question formulée librement, sans mot-clé exact ni numéro de règle connu.

Implémente `POST /regles/dense` (`app/api_regles/regles.py`).

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `question` | string | oui | Question en langage naturel, non vide, longueur bornée (`config.QUESTION_MAX_LENGTH`) |

## Sortie

Liste de règles avec score de similarité (peut être vide) :

```json
[
  {
    "regle": { "numero": 12, "intitule": "...", "theme": "...", "...": "..." },
    "score": 0.83
  }
]
```

- Liste vide : hors périmètre Opquast, ou aucune règle jugée pertinente
  parmi les candidats retrouvés — l'agent doit le signaler explicitement,
  pas combler avec une réponse hors référentiel.
- `score` (similarité cosinus, 1 = identique, 0 = aucun rapport) informatif
  uniquement — la pertinence a déjà été tranchée par le jugement LLM côté
  API, l'agent ne doit pas re-filtrer sur ce score.
