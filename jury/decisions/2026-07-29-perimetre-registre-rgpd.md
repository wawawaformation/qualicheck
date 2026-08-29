# Périmètre du registre des traitements RGPD (C4) — scindé selon les traitements réels

2026-07-29 · retenu

## Contexte

Le critère C4 (`conception/referentiel_competences.md`) exige un « registre
des traitements de données personnelles complet » et des « procédures de tri
RGPD avec leur fréquence d'exécution ».

État réel du schéma, vérifié dans le code : le schéma cible
(`app/models/metier.py`) contient une table `utilisateur` (`nom`, `prenom`)
et les tables métier de l'audit (`audit`, `page`, `audit_page`,
`audit_regle`, `constat`), créées par migration Alembic mais **jamais
peuplées ni lues par aucun code à ce jour** — l'US1 qui les rendrait
opérationnelles n'a pas encore de spec. Les seules données réellement
traitées aujourd'hui sont :

- le référentiel Opquast (`theme`/`regle`/`objectif`/`phase`/`tag`) — aucune
  donnée personnelle ;
- les jetons API nommément associés à un client (`app/api_regles/manifest.yml`,
  `.env`) — seule donnée nominative réellement en place.

## Options envisagées

**Ne pas produire de registre tant qu'aucune donnée personnelle n'est
réellement traitée** — pour : honnête, rien à documenter côté audit. Contre :
le critère demande un registre « complet » ; risque d'être lu comme un oubli
plutôt qu'un choix ; ne couvre pas la donnée nominative pourtant déjà réelle
(jetons API).

**Produire un registre complet couvrant déjà l'usage futur
d'`utilisateur`/`audit`, comme si US1 existait** — pour : case cochée d'un
coup, pas de retour à prévoir. Contre : fictif — US1 n'a pas de spec, ce
serait documenter une finalité, une base légale et une durée de conservation
inventées ; contredit la démarche spec-driven du projet et le refus des cases
artificielles déjà acté pour C1
(`jury/decisions/2026-07-28-couverture-sources-extraction-c1.md`).

**Registre scindé, borné aux traitements réels (retenu)** — couvre ce qui est
réellement traité aujourd'hui (référentiel Opquast : hors champ RGPD ; jetons
API nominatifs : seul traitement réel), constate explicitement l'absence de
traitement sur le volet audit, et réserve une section dédiée
« traitements anticipés, non actifs » pour `utilisateur`/`audit`/`constat` —
en s'appuyant sur l'article 30 du RGPD, qui porte sur les traitements
réellement mis en œuvre, pas sur un schéma en anticipation.

## Décision

Registre scindé retenu — voir `docs/rgpd/registre_traitements.md`. Critère
qui tranche : un registre honnête documente ce qui existe, pas ce qui est
prévu ; l'article 30 RGPD porte explicitement sur les traitements en cours.
Même logique que la décision C1 : refuser de remplir artificiellement une
case pour un besoin qui n'est pas encore réel.

## Conséquences

- Le registre devra être complété (finalité, base légale, durée de
  conservation, droits des personnes concernées) dès qu'US1 rendra
  `utilisateur`/`audit`/`constat` opérationnels — point à ne pas oublier au
  moment de rédiger cette spec. Le registre devra être complété **et son
  périmètre reconsidéré** à ce moment : il ne s'agira plus seulement
  d'exposer un référentiel documentaire (C4/C5), mais de traiter des données
  personnelles sur la base entière (qui a créé quel audit, quels constats,
  éventuellement quelles URLs auditées) — un changement de nature, pas
  seulement de volume.
- Les procédures de tri RGPD suivent la même logique : rien à purger côté
  référentiel (donnée non personnelle, pérenne) ; à écrire pour le volet
  audit quand il existera réellement.
- Risque assumé : un jury strict peut attendre un registre déjà « prêt à
  recevoir » la partie audit, même vide. La section dédiée du registre
  désamorce ça en l'explicitant plutôt qu'en la passant sous silence — même
  pari que pour C1.
