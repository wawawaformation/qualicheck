# Séparation `api_regles` / `api_audit`, même base de données

2026-07-28 · retenu

## Contexte

`TODO.md` marquait depuis le 2026-07-27 un point **« Important »** non
tranché : où vivent les tables métier de l'audit
(`Audit`/`Page`/`AuditPage`/`AuditRegle`/`Constat`, `app/models/metier.py`)
par rapport à l'API données déjà spécée pour le référentiel Opquast
(`docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`) ?

Une première reformulation (2026-07-26, `IDEA.md`) proposait de les traiter
comme de nouveaux routers **dans** `app/api_data/`. En rediscutant le sujet
le 2026-07-28, ce choix s'est révélé être une mauvaise lecture d'un
précédent plus ancien (`IDEA.md`, 2026-07-25), qui distinguait déjà
explicitement deux cas :

- **US1 (audit) + US2 (dialogue)** : même produit, même utilisateur
  (l'auditeur), même session → justifie un seul FastAPI avec routers par
  domaine.
- **L'API de revue/curation du référentiel** (ce qui deviendra `api_data`,
  aujourd'hui `api_regles`) : **micro-service à part**, justifié par un
  persona différent (le curateur Opquast, ex. Élie Sloïm — pas l'auditeur),
  un moment différent du cycle de vie (post-ingestion/QA, pas un audit en
  direct), une préoccupation différente (qualité du référentiel, pas flux
  d'audit).

Le 2026-07-26 avait mélangé ces deux idées. Cette décision corrige le tir.

## Options envisagées

**Tout dans une seule API (`api_regles` étendue)** — pour : un seul service
à déployer, un seul manifeste. Contre : mélange deux personas et deux
postures de sécurité incompatibles dans le même service — lecture ouverte
(licence CC BY-SA sur le référentiel Opquast) à côté de données
personnelles/business de l'auditeur (RGPD) nécessitant une authentification
réelle sur tout. Contredit aussi le précédent du 2026-07-25, qui avait déjà
tranché ce point pour une paire similaire.

**Deux API, deux bases de données séparées** — pour : indépendance totale
des deux services, isolation en cas d'incident sur l'une des deux. Contre :
`app/models/metier.py` contient déjà de vraies contraintes FK vers
`regle.id` (`AuditRegle.regle_id`, `Constat.regle_id`), migrées et actives.
Une contrainte FK Postgres ne traverse pas deux bases de données distinctes
(même sur le même serveur) — séparer les bases impose de les abandonner et
de les remplacer par une vérification applicative, moins fiable. Contraire
au critère C4 (*« modèle physique fonctionnel, intégré sans erreur »*), pour
un bénéfice (indépendance de déploiement d'équipes) qui ne s'applique pas à
un projet solo.

**Deux API, une seule base de données, chacune l'attaquant directement
(retenu)** — pour : conserve les FK existantes et l'intégrité référentielle
sans rien changer au schéma déjà migré ; chaque service a une politique
d'authentification cohérente (pas de patchwork table par table dans une
seule API) ; `app/models/` reste l'unique source de vérité du schéma,
importée par les deux services sans duplication. Contre : les deux
codebases doivent rester coordonnées sur l'évolution du schéma partagé —
coût jugé faible, un seul développeur maintenant les deux.

## Décision

**Une seule base de données PostgreSQL, un seul `app/models/`, deux
services FastAPI distincts qui l'attaquent chacun directement** :

- **`app/api_regles`** (renommé le jour même depuis `app/api_data`,
  spec/plan/diagramme mis à jour en conséquence) : `regle`, `theme`, `tag`, `phase`,
  `objectif`, et la revue humaine (`review_status`/`review_note`/
  `reviewed_at`). Lecture ouverte, écriture par Bearer — inchangé.
- **`app/api_audit`** (nouveau, à concevoir avec la spec US1) :
  `Audit`/`Page`/`AuditPage`/`AuditRegle`/`Constat`/`Utilisateur`.
  Authentification réelle sur toutes les routes, pas seulement l'écriture —
  données personnelles/business de l'auditeur (RGPD), pas du contenu
  Opquast public.

`api_audit` lit la table `regle` **directement en base** quand il en a
besoin (afficher `guide_analyse`/`intitule` pendant un audit), sans passer
par `api_regles` en HTTP — la contrainte FK garantit l'intégrité au niveau
base, indépendamment de la manière dont l'application interroge les
données. `api_regles` garde son rôle initial : la revue/curation, pas un
proxy interne obligatoire pour tout ce qui touche `regle`.

Un troisième étage reste distinct des deux : **`app/api_business`**
(orchestration IA — routing par `strategie_analyse`, dialogue, RAG US2),
qui ne touche jamais Postgres et consomme les deux API précédentes en HTTP.

## Conséquences

- **Renommage fait dans la foulée de cette décision** : la spec, le plan et
  le diagramme déjà écrits (`docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`,
  `docs/superpowers/plans/2026-07-26-api-regles-implementation.md`,
  `conception/annexes/flux_api_donnees.drawio`), ainsi que le document de
  décision sur la lecture ouverte
  (`docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`, lui aussi
  renommé), utilisaient tous `app/api_data/`. Fait avant que l'implémentation
  ne commence — aucune ligne de code n'existait encore, le coût du
  renommage était nul.
- **`app/api_audit` reste à concevoir** — pas avant la spec US1
  (`app/CLAUDE.md` interdit d'anticiper une structure avant sa conception).
  Cette décision fixe seulement où il vivra et comment il accède aux
  données, pas son contenu détaillé.
- **La frontière CRUD (`api_audit`) vs orchestration (`api_business`)**
  reste un point ouvert distinct, non traité ici — ex. « créer un audit »
  est-il un simple CRUD ou déclenche-t-il déjà une action métier (crawl) ?
  À trancher avec la spec US1.
- **Authentification `api_audit`** : un vrai token par utilisateur externe
  reste hors périmètre tant qu'il n'y a qu'un auditeur (MVP) — cohérent avec
  le choix déjà fait pour `api_regles` (token unique, proportionné au
  besoin réel, pas un système de comptes anticipé).
