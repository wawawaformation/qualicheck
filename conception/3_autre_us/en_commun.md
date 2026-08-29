---
title: "API commune — US1/US2"
subtitle: "Étage applicatif partagé entre l'audit assisté et la question libre"
author: "David LEGRAND"
date: "Août 2026"
lang: fr-FR
toc: true
toc-depth: 2
---

\newpage

## Contexte et objectif

US1 (audit assisté) et US2 (question libre) sont deux fonctionnalités de la
même application — pas deux produits séparés. Le front (Vue.js) ne doit
appeler qu'une seule API pour les deux : `app/api_business/`, l'étage
d'orchestration déjà prévu dans
`jury/decisions/2026-07-28-separation-api-regles-api-audit.md` et dans
`conception/2_us0/api_regles/api_regles.md` (schéma « Place dans l'architecture »).

Ce document couvre ce qui est **commun** aux deux US côté API — domaine,
organisation des endpoints, forme du service. Les contrats d'API propres à
chaque US restent dans leurs specs respectives
(`3_autre_us/us2_question_libre/`, `3_autre_us/us1_audit/` à venir). Le
profil utilisateur (données, rétention) a sa propre spec :
[`profil/spec.md`](profil/spec.md).

## Place dans l'architecture

```text
Étage présentation (Vue.js)
        │
        ▼ HTTP, un seul point d'entrée
Étage applicatif — app/api_business/
        ├── routes audits (US1)
        └── routes questions (US2)
        │ HTTP
        ▼
Étage données
  app/api_regles/ · app/api_audit/ (à concevoir)
        │
        ▼
  PostgreSQL / pgvector
```

`api_business` ne touche jamais PostgreSQL directement (cf. décision
2026-07-28) — il consomme `api_regles`/`api_audit` en HTTP.

## Décisions actées

| Décision                   | Choix retenu                                                                       | Justification                                                                                                                                                                                                                                                                                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nombre de services         | **Un seul FastAPI** (`app/api_business/`) pour US1 et US2                          | Pas de bénéfice concret à en avoir deux tant que rien n'est construit ; le split reste possible plus tard (même pattern que `api_regles` : nouveau `main.py` + bloc `docker-compose`) à condition de garder les deux groupes de routes cloisonnés dès maintenant (dossiers séparés, pas d'import croisé, code réellement commun isolé à part) |
| Organisation des endpoints | Par **ressource/action** (`/audits/...`, `/questions/...`), jamais par numéro d'US | US1/US2 sont des labels de backlog, pas un contrat d'API — voir [[us1_us2_naming_and_order]] : si la numérotation ou le périmètre bouge, l'API ne s'en trouve pas datée                                                                                                                                                                       |
| Authentification           | **Nécessaire**, pour US1 comme US2                                                 | Un verrou d'accès, pas un compteur : US1 (génération de constats) et US2 (RAG) appellent toutes les deux un LLM payant. Sans authentification, n'importe qui sur Internet peut consommer ces tokens à volonté — contrairement à la lecture `api_regles`, ouverte sans authentification (contenu Opquast sous CC BY-SA, pas d'appel LLM à cet étage, donc pas de coût à protéger) |
| Mécanisme d'authentification | **Jeton API**, réutilisant pour l'instant les mêmes jetons que `api_regles` (`Authorization: Bearer`, jeton par client nommé, `manifest.yml`) | Pas de nouveau système d'identité à ce stade — cohérent avec [[stade_projet_mvp]] : verrouiller l'accès, pas construire une gestion de comptes utilisateurs |
| Nom de domaine              | `api.qualicheck.koabana.fr`                                                        | Suit la convention déjà en place (`regles.qualicheck.koabana.fr` pour `api_regles`) ; `api.` plutôt que `business.` car c'est le point d'entrée public de l'application, pas un terme d'architecture interne |

## Reste à trancher

- **Modèle de crédits** (« 1 question = X crédits », « 1 audit = Y crédits »)
  — explicitement **hors périmètre du MVP actuel**. Le projet en est au stade
  de valider la faisabilité technique et l'intérêt auprès de la cible
  potentielle (~20 000 certifiés Opquast et professionnels sensibilisés à la
  qualité web), pas de construire un modèle économique. Noté ici pour ne pas
  perdre l'intention, mais l'authentification MVP ne doit pas anticiper de
  mécanique de crédits/quotas — juste verrouiller l'accès (point ci-dessus).
  Détail du profil utilisateur concerné : [`profil/spec.md`](profil/spec.md).
