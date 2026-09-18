# Tool `demander_a_l_utilisateur`

Stratégie d'analyse couverte : **`manuel`** (28 règles sur 245, invérifiables
sans un humain — c'est lui l'instrument de mesure).

## Docstring

Pose une question à l'utilisateur et attend sa réponse. Deux usages, un
seul mécanisme :

- **Obtenir une observation** que seul un humain peut faire — « ouvre ta
  page, appuie trois fois sur Tab : qu'est-ce qui est surligné ? ». C'est
  le seul moyen de traiter les 28 règles `manuel`.
- **Obtenir un accord** avant une action coûteuse ou intrusive — « je peux
  t'expliquer la procédure, ou aller vérifier moi-même sur ta page : tu
  préfères quoi ? » (notamment avant `verifier_avec_navigateur`).

**Ce tool termine le tour de l'agent.** US2 est une API, pas un CLI
interactif : l'agent ne peut pas bloquer en attendant une réponse au
milieu d'une requête HTTP. Il finit son tour *par* la question, et la
réponse arrive comme message suivant de la discussion. Conséquence sur le
contrat HTTP : une réponse peut être soit une réponse argumentée, soit une
question en retour avec ses options — et l'historique porte la question en
attente.

Pas encore implémenté — contrat de tool posé ici.

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `question` | string | oui | Question posée à l'utilisateur, formulée pour être actionnable |
| `options` | list[string] | non | Réponses proposées, quand le choix est fermé (ex. « explique-moi » / « vérifie toi-même ») |

## Sortie

Pas de retour dans le tour courant — voir la docstring. La réponse de
l'utilisateur arrive au tour suivant, dans l'historique de la discussion.
