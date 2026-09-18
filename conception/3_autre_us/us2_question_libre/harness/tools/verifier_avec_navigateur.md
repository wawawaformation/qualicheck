# Tool `verifier_avec_navigateur`

Stratégie d'analyse couverte : **`playwright`** (~96 règles sur 245, en
valeur pure ou composite).

## Docstring

Vérifie un point précis sur une page réelle à l'aide d'un navigateur
piloté : DOM après exécution du JavaScript, navigation au clavier, états
après interaction (survol, focus, ouverture d'un menu). À utiliser quand
ni le HTML brut (`lire_url`) ni une capture (`lire_capture_ecran`) ne
peuvent répondre — typiquement l'ordre de parcours au clavier ou un
comportement qui n'existe qu'après interaction.

**Demander l'accord de l'utilisateur avant d'appeler ce tool**
(`demander_a_l_utilisateur`) : c'est une action sur un site tiers, avec un
coût réel. Le défaut reste d'expliquer la procédure (`guide_analyse` de la
règle) plutôt que de vérifier à la place de l'utilisateur.

Pas encore implémenté côté API — contrat de tool posé ici, backend à
concevoir séparément.

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `url` | string | oui | Page à vérifier |
| `verification` | string | oui | Ce qu'il faut observer, en langage naturel (ex. « l'ordre de focus dans le formulaire de contact ») |

## Sortie

Ce qui a été observé, ou un signal d'échec explicite :

```json
{ "observation": "..." }
```

ou :

```json
{ "erreur": "page inaccessible" }
```

- Échec : ne bloque pas la question — l'agent bascule sur l'explication de
  la procédure et le dit à l'utilisateur.
