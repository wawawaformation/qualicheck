---
title: "Profil utilisateur — US1/US2"
subtitle: "Données personnelles, rétention et suppression"
author: "David LEGRAND"
date: "Août 2026"
lang: fr-FR
toc: true
toc-depth: 2
---

\newpage

## Contexte

Le profil `utilisateur` (`id`, `nom`, `prenom`) est commun à US1 et US2 —
`audit` y a déjà une FK dans le MLD, US2 y ajoute discussions et profil. Deux
périmètres de rétention distincts, à ne pas confondre :

| Décision | Choix retenu | Justification |
| --- | --- | --- |
| Profil `utilisateur` | `id`, `nom`, `prenom` uniquement — pas de champ crédit/quota | Cohérent avec le hors-périmètre MVP ci-dessous ; pas de colonne inerte dans le schéma (cf. précédent `utilisateur` du MLD, documenté par une note plutôt qu'un champ non exploité) |
| Rétention — discussion | **2 mois** d'inactivité → avertissement → confirmation utilisateur → suppression | Le RGPD interdit une conservation indéfinie « au cas où » ; le stockage brut du contenu (question/réponse) reste conforme tant qu'une durée de conservation est fixée (cf. `docs/rgpd/registre_traitements.md`, section utilisateur à compléter) |
| Rétention — compte | **12 mois** d'inactivité → avertissement → confirmation → suppression ; suppression du compte (inactivité ou demande explicite) **cascade** sur l'ensemble de ses discussions — aucune discussion orpheline | Un compte représente une relation dans la durée (usage ponctuel possible, ex. un audit qualité par trimestre) — une durée plus longue qu'au niveau discussion évite de supprimer des comptes encore légitimement utilisés ; le droit à l'effacement porte sur le compte dans son ensemble, pas discussion par discussion |

**Implémentation** : ces deux durées (2 mois, 12 mois) sont des paramètres de
configuration, pas des constantes codées en dur — même logique que
`app/ingestion/manifest.yml` (`top_n`, `taux_reussite_minimum` de
`rag_acceptance`, prix des modèles). Un futur `manifest.yml` d'`api_business`
les porterait, modifiables sans toucher au code.

## Reste à trancher

- **Modèle de crédits** (« 1 question = X crédits », « 1 audit = Y crédits »)
  — explicitement **hors périmètre du MVP actuel**. Le projet en est au stade
  de valider la faisabilité technique et l'intérêt auprès de la cible
  potentielle (~20 000 certifiés Opquast et professionnels sensibilisés à la
  qualité web), pas de construire un modèle économique. Noté ici pour ne pas
  perdre l'intention, mais l'authentification MVP ne doit pas anticiper de
  mécanique de crédits/quotas — juste verrouiller l'accès (cf. `en_commun.md`).
