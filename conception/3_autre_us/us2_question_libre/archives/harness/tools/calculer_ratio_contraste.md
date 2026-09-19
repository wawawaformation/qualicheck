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
| `taille_police` | number | oui | Taille en points (pt) |
| `gras` | bool | oui | Texte en gras ou non |

`taille_police`/`gras` déterminent le seuil applicable (texte large =
seuil allégé), pas le ratio lui-même — le calcul de ratio ne dépend que
des deux couleurs.

**Décidé (David, 2026-09-18)** : on se base sur WCAG 1.4.3 (seuils
4.5:1 texte normal / 3:1 texte large), pas sur le seuil unique `≥ 3:1`
du `controle` de la règle 182 — celui-ci ne distingue pas la taille,
c'est une simplification du référentiel Opquast par rapport à la norme
qu'il cite.

## Sortie

```json
{ "ratio": 4.52, "seuil_applique": 4.5, "conforme": true }
```

- `ratio` : ratio de contraste WCAG (1 à 21).
- `seuil_applique` : 3:1 si texte large (`taille_police ≥ 18` ou
  `taille_police ≥ 14` et `gras`), sinon 4.5:1 (WCAG AA).
- `conforme` : `ratio ≥ seuil_applique`.
