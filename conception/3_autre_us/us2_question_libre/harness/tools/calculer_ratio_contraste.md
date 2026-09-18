# Tool `calculer_ratio_contraste`

Sous-capacité de la stratégie **`playwright`** (ex. règle 182, « contraste
suffisant par rapport à l'arrière-plan ») : calcul déterministe, pas une
appréciation — pas au LLM de l'estimer.

## Docstring

Calcule le ratio de contraste WCAG entre deux couleurs. Les couleurs sont
en général obtenues via `verifier_avec_navigateur` (styles calculés sur la
page réelle) avant cet appel — ce tool ne lit rien sur la page, il ne fait
que le calcul.

Pas encore implémenté — contrat de tool posé ici.

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `couleur1` | string | oui | Couleur au format hexadécimal (`#rrggbb`) |
| `couleur2` | string | oui | Couleur au format hexadécimal (`#rrggbb`) |

## Sortie

```json
{ "ratio": 4.52, "conforme_aa": true, "conforme_aaa": false }
```

- `ratio` : ratio de contraste WCAG (1 à 21).
- `conforme_aa`/`conforme_aaa` : seuils WCAG standards (4.5:1 / 7:1 pour
  texte normal) — valeurs fixes de la norme, pas de config projet.
