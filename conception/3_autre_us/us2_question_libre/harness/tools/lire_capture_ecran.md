# Tool `lire_capture_ecran`

Stratégie d'analyse couverte : **`vision`** (~30 règles sur 245, en valeur
pure ou composite) — interpréter un rendu, pas le code.

## Docstring

Décrit le contenu visuel d'une capture d'écran, pour donner à l'agent le
contexte de la page que l'utilisateur audite quand une URL n'est pas
fournissable (page nécessitant une authentification, contenu dynamique,
etc.). À utiliser quand l'utilisateur associe une image à sa question
(`«extend» Associer un contexte de page`, `scenarios.md`).

Pas encore implémenté côté API — contrat de tool posé ici, backend à
concevoir séparément (`app/`, hors périmètre de cette réflexion).

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `image` | fichier image (ou référence à un fichier déjà uploadé) | oui | Capture d'écran à analyser |

## Sortie

Une description du contenu visuel pertinent, ou un signal d'échec explicite :

```json
{ "description": "..." }
```

ou, si l'analyse échoue :

```json
{ "erreur": "image illisible" }
```

- Échec (image illisible, format non supporté) : ne bloque pas la
  question — conformément au scénario, la question est traitée sans ce
  contexte et l'utilisateur en est informé, pas d'erreur bloquante.
