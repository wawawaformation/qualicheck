# Tool `lire_url`

Stratégie d'analyse couverte : **`statique`** (~96 règles sur 245) — le
HTML tel que servi, sans exécution du JavaScript.

## Docstring

Récupère et extrait le contenu pertinent d'une page web, pour donner à
l'agent le contexte de la page que l'utilisateur audite. À utiliser
quand l'utilisateur associe une URL à sa question (`«extend» Associer un
contexte de page`, `scenarios.md`).

Pas encore implémenté côté API — contrat de tool posé ici, backend à
concevoir séparément (`app/`, hors périmètre de cette réflexion).

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `url` | string | oui | URL de la page à lire |

## Sortie

Le contenu extrait de la page, ou un signal d'échec explicite :

```json
{ "contenu": "..." }
```

ou, si l'extraction échoue :

```json
{ "erreur": "URL inaccessible" }
```

- Échec (URL inaccessible, page inexistante) : ne bloque pas la question —
  conformément au scénario, la question est traitée sans ce contexte et
  l'utilisateur en est informé, pas d'erreur bloquante.
