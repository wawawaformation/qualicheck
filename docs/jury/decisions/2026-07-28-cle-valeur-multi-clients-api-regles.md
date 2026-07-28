# Authentification multi-clients de l'API données — clé/valeur, pas Postgres

2026-07-28 · retenu

**Statut : solution provisoire, à la main.** Ajouter ou révoquer un client
est une opération manuelle (éditer `manifest.yml` + `.env`, redémarrer l'API)
— aucune interface, aucune rotation, aucune expiration. Volontairement
minimal pour un besoin actuel d'un tiers externe déclaré à la fois ; à
reconsidérer (table Postgres, self-service) seulement si le nombre de
clients ou la fréquence de rotation rendent la gestion manuelle pénible.

## Contexte

Le PATCH de `app/api_regles/` (annotation de revue) n'avait jusqu'ici qu'un
seul jeton partagé (`FASTAPI_API_KEY`), pensé pour un usage développeur. Le
besoin réel évolue : faire valider/utiliser la fonctionnalité de revue par le
formateur et par Élie Sloïm (fondateur Opquast), voire par d'autres experts
Opquast — plusieurs tiers externes distincts, pas un seul.

Un jeton partagé unique ne permet pas de savoir qui a annoté quoi. Un vrai
système de comptes (table Postgres, mots de passe/OAuth) serait
disproportionné : un tiers déclaré à la fois, pas un public large — le même
raisonnement déjà acté dans `IDEA.md` (2026-07-25, section auth) au moment de
l'ouverture initiale de cette API.

## Options envisagées

**Table Postgres des utilisateurs** — pour : extensible, standard. Contre :
un modèle utilisateur/session complet (hash de mot de passe ou OAuth, gestion
de session) pour un besoin qui se résume à « distinguer 2-3 jetons nommés »
est une sur-ingénierie assumée hors de proportion avec le besoin réel.

**Un seul jeton partagé, inchangé** — pour : rien à construire. Contre :
aucune distinction possible entre annotateurs, contradictoire avec l'objectif
de faire contribuer plusieurs experts et de tracer leurs retours séparément.

**Clé/valeur dans le manifeste, un jeton par client nommé (retenu)** — pour :
même patron déjà en place et validé dans `app/ingestion/manifest.yml` (rôles
LLM → variable d'environnement dédiée) ; proportionné (ajouter un client =
une ligne de manifeste + une variable `.env`) ; le nom du client résolu par
`require_bearer()` ouvre la voie à une future traçabilité (qui a annoté quoi)
sans l'implémenter maintenant. Contre : reste un token statique par personne
(pas de rotation, pas d'expiration) — jugé suffisant pour un nombre de
clients faible et connu.

## Décision

`app/api_regles/manifest.yml` déclare une liste `clients` (`nom` +
`env_var_token`). `config.clients_tokens()` construit `{nom: jeton}` en
lisant chaque variable d'environnement déclarée, avec le même garde-fou
fail-fast qu'avant (une variable absente/vide fait échouer le démarrage,
plutôt que d'exclure silencieusement ce client). `auth.require_bearer()`
compare le jeton reçu à chacun des jetons connus (`secrets.compare_digest`,
temps constant) et renvoie le nom du client résolu au lieu de `None`.

Le client existant est migré tel quel : `nom: dev`, `env_var_token:
FASTAPI_API_KEY` — aucun secret `.env` renommé.

## Conséquences

- Ajouter Élie Sloïm (ou un autre expert) : une entrée `clients` de plus dans
  le manifeste + une variable `.env` dédiée (ex. `FASTAPI_API_KEY_ELIE`) —
  aucun changement de code.
- Le nom de client résolu par `require_bearer()` n'est pour l'instant ni
  loggé ni stocké : cette décision couvre uniquement l'authentification, pas
  la traçabilité « qui a annoté quoi » sur la table `regle` (hors périmètre
  de cette tâche, à instruire séparément si le besoin devient réel).
- Reste un token statique par personne : pas de rotation ni d'expiration. Non
  bloquant pour un nombre de tiers externes faible et connu à l'avance.
