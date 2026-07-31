# Registre des traitements de données personnelles

État au 2026-07-29. Tenu au sens de l'article 30 du RGPD : il couvre les
traitements **réellement mis en œuvre**, pas les traitements envisagés — voir
`docs/jury/decisions/2026-07-29-perimetre-registre-rgpd.md` pour le
raisonnement qui justifie ce périmètre.

## Traitement 1 — Référentiel Opquast (`theme`/`regle`/`objectif`/`phase`/`tag`)

- **Responsable de traitement** : David Legrand (porteur du projet QualiCheck)
- **Finalité** : mise à disposition du référentiel Opquast enrichi (245
  règles qualité web) via l'API `api_regles`
- **Données traitées** : aucune donnée à caractère personnel — contenu
  éditorial public (intitulés, solutions, contrôles Opquast), diffusé sous
  licence CC BY-SA 4.0
- **Personnes concernées** : aucune
- **Base légale** : sans objet (pas de donnée personnelle)
- **Conservation** : illimitée (référentiel documentaire pérenne, pas de
  personne concernée)
- **Conclusion** : hors champ du RGPD

## Traitement 2 — Jetons API nominatifs (accès en écriture à `api_regles`)

- **Responsable de traitement** : David Legrand
- **Finalité** : traçabilité des annotations de revue
  (`PATCH /regles/{numero}`) — savoir quel expert a produit quelle
  annotation, sans construire de table Postgres dédiée (voir
  `docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md`)
- **Données traitées** : nom associé à un jeton (`app/api_regles/manifest.yml`
  → `clients: nom`), le jeton lui-même (`.env`, non versionné)
- **Personnes concernées** : David Legrand, Élie Sloïm (expert externe), le
  formateur — 4 entrées nommées à ce jour (`dev`, `elie-sloim`,
  `david-legrand`, `formateur`)
- **Base légale** : intérêt légitime (traçabilité d'un accès en écriture,
  périmètre restreint à des tiers connus et consentants dans le cadre du
  projet)
- **Destinataires** : aucun tiers ; accès limité aux personnes elles-mêmes et
  à l'administrateur du projet
- **Conservation** : durée de vie du jeton (révocation = suppression de la
  variable `.env` et de l'entrée correspondante dans `manifest.yml`)
- **Mesures de sécurité** : jetons stockés dans `.env` non versionné,
  transmis hors dépôt Git ; `manifest.yml` (versionné) ne contient que le nom
  du client et le nom de la variable d'environnement, jamais le secret

## Traitements anticipés, non actifs — `utilisateur` / `audit` / `constat`

Le schéma cible (`app/models/metier.py`) définit une table `utilisateur`
(`nom`, `prenom`) et les tables métier de l'audit (`audit`, `page`,
`audit_page`, `audit_regle`, `constat`). Ces tables existent dans le schéma
Postgres (migrations Alembic) mais **ne sont peuplées par aucun code à ce
jour** — l'US1 (dialogue et validation des constats) qui les rendrait
opérationnelles n'est pas encore conçue.

Aucun traitement n'étant réellement mis en œuvre, ce volet reste hors du
présent registre au sens de l'article 30 du RGPD. Il sera complété au moment
de la spec US1, avec au minimum :

- Finalité précise (ex. : identification de l'auditeur pour un audit donné)
- Base légale (probablement exécution d'un contrat ou intérêt légitime)
- Durée de conservation des audits/constats
- Droits des personnes concernées (accès, rectification, suppression)

## Procédures de tri (rétention/purge)

- **Référentiel Opquast** : aucune purge nécessaire — donnée non
  personnelle, pérenne par nature.
- **Jetons API** : révocation manuelle par retrait de la variable `.env` et
  de l'entrée `manifest.yml` — pas d'automatisation à ce jour (volume : 4
  clients), à revoir si le nombre de clients externes grandit.
- **Volet audit** (`utilisateur`/`audit`/`constat`) : procédure à définir
  avec la spec US1.
