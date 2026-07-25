---
title: "Recommandations V5 — Buffer de revue (brouillon)"
subtitle: "Accumulation brute pendant la revue manuelle post-V4, consolidation à la fin"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

> **Statut : buffer, pas encore consolidé.** Même démarche que
> `3_recommandations_v4.md` — observations brutes notées au fil de la revue
> manuelle des 245 règles ré-ingérées avec le prompt V4, à structurer en
> recommandations priorisées une fois la revue terminée. Ne pas traiter comme
> une spec ou une conclusion définitive.

## Observations brutes

### O1 — `strategie_analyse` composite ne distingue pas ET / OU / PUIS

**Contexte** : le format `strategieA+strategieB` (spec
`conception/2_ingestion/F_chantier2_prompt_v4.md` §4) n'encode que l'**ordre**
("l'ordre = séquence d'exécution") — implicitement toujours une sémantique
**PUIS** (séquentiel, B dépend du résultat de A).

**Problème repéré** : au moins deux relations distinctes coexistent dans les
245 règles réellement ré-ingérées, sans que le format actuel les distingue :

- **PUIS (séquentiel/dépendant)** — ex. `playwright+statique` sur les règles
  27, 44, 58 : atteindre une page via interaction navigateur, *puis* inspecter
  son DOM. B ne peut s'exécuter/se juger qu'après A.
- **ET (deux vérifications indépendantes)** — le marqueur « ET » de R2.5 (ex.
  règle 65, « différenciation visuelle ET textuelle ») décrit plutôt deux
  propriétés à vérifier indépendamment, pas une dépendance causale entre elles.
- **OU (alternative contextuelle)** — pas illustré dans les 245 règles
  observées, mais concevable : selon le contexte de la page, soit A soit B
  s'applique, pas nécessairement les deux.

**Piste non tranchée** : garder `+` pour PUIS uniquement et introduire un
séparateur/mot-clé distinct pour ET (ex. `strategieA&strategieB`), ou laisser
`guide_analyse` porter seul la distinction (déjà le cas en pratique : le
format "Étape 1 [x] : ... Étape 2 [y] : ..." suppose implicitement du PUIS).
À creuser une fois la revue terminée — ne pas trancher à chaud pendant la
revue.

### O2 — Règle 96 : `playwright` classifié malgré un signal "second appareil" (R2.4)

**Contexte** : règle 96 (« Les procédures d'authentification à double facteur
peuvent être relancées ») classée `playwright`. Le guide vérifie qu'un clic
sur « Renvoyer le code » déclenche un signal UI (message de confirmation,
compteur, changement d'état) — pas que le code est réellement reçu sur le
second canal (SMS/mail/appli).

**Tension identifiée** : le prompt V4 (R2.4, cette même itération) dit
explicitement qu'un critère nécessitant d'observer un second appareil est
`manuel`. Ici, either (a) le LLM n'a pas appliqué sa propre consigne, soit
(b) lecture défendable : le contrôle Opquast ("vérifier qu'il est *possible*
de relancer l'envoi") ne demande que l'existence du mécanisme UI, pas la
preuve de délivrance réelle — auquel cas `playwright` reste juste mais avec
une limite de fiabilité à documenter.

**Lien avec l'existant** : `3_recommandations_v4.md` §D1 avait déjà flaggé les
règles 23/62/96 pour une raison différente (nécessitent des données de test —
compte, 2FA). Cette observation-ci est plus fondamentale : même avec un compte
de test valide, la preuve de délivrance réelle reste hors de portée de l'agent.

**Statut proposé** : candidat `review_status = a_revoir` (colonnes de
`conception/2_ingestion/G_revue_manuelle.md`).

## Reste à faire

- Continuer la revue des règles ciblées (`tmp/revue_v4_regles_ciblees.json`)
  et de l'échantillon élargi (65, 96, 98, 116-118, 189, 206-217, 235, 245)
- Consolider en recommandations priorisées une fois la revue terminée,
  sur le modèle de `3_recommandations_v4.md`
