---
title: "Recommandations V5 — Pipeline d'ingestion & classification LLM"
subtitle: "Analyse des 245 règles ré-ingérées avec le prompt V4 : incohérences de diagnostic, limites de format, affinages du prompt"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

Après la ré-ingestion réelle des 245 règles Opquast avec le prompt V4
(chantier 2, `conception/2_ingestion/F_chantier2_prompt_v4.md`), une revue
manuelle ciblée (David) et un balayage complet des 245 règles par 5 agents en
parallèle ont été menés pour vérifier la cohérence des diagnostics produits.
Ce document consolide les observations — le **quoi** et le **pourquoi**, pas
le **comment** (spec et plan : étape suivante, en spec-driven, même méthode
que pour le chantier 2). Démarche identique à `3_recommandations_v4.md` :
accumulation brute en buffer pendant la revue, consolidation ici.

## Résumé exécutif

La classification V4 est globalement de très bonne qualité — généralisation
réelle au-delà des few-shot fournis, `manuel` bien maîtrisé y compris pour
éviter le sur-classement, aucun guide spéculatif détecté sur les 245 règles,
distribution saine (cf. §5). Le balayage complet (245/245, aucun lot ignoré)
a identifié **12 règles à problème** et **1 limite de format systémique**,
qui se répartissent en 2 chantiers :

1. 🔴 **Format composite insuffisant** (O1) — `strategieA+strategieB`
   n'encode que l'ordre, pas la nature de la relation (PUIS/ET/OU)
2. 🟠 **Reformuler le critère "manuel"** (O5, O6) — la frontière actuelle
   (R2.4) est trop étroite ; une incohérence technique indépendante
   (`playwright`/`statique` sur les vérifications HTTP brutes) s'y ajoute

Décisions déjà actées avec David (2026-07-25) :

- **Ré-ingestion complète des 245 règles** avec le prompt V5 (pas un patch
  ciblé) — pour valider que les points positifs de V4 ne régressent pas, pas
  seulement que les problèmes sont corrigés
- **Script `enrich_again`** (réécriture ciblée par LLM des règles marquées
  à revoir) — reporté **après** le prochain audit post-V5, pour être construit
  sur de vraies données de revue plutôt que des cas spéculatifs

## 1. Format composite insuffisant (O1)

**Contexte** : le format `strategieA+strategieB` (spec
`conception/2_ingestion/F_chantier2_prompt_v4.md` §4) n'encode que l'**ordre**
("l'ordre = séquence d'exécution") — implicitement toujours une sémantique
**PUIS** (séquentiel, B dépend du résultat de A).

**Problème repéré** : au moins deux relations distinctes coexistent dans les
245 règles réellement ré-ingérées, sans que le format actuel les distingue :

- **PUIS (séquentiel/dépendant)** — ex. `playwright+statique` sur les règles
  27, 44, 58, 98 : atteindre un état ou une page via interaction navigateur,
  *puis* inspecter le DOM. B ne peut s'exécuter/se juger qu'après A.
- **ET (deux vérifications indépendantes)** — le marqueur « ET » de R2.5 (ex.
  règle 65, « différenciation visuelle ET textuelle ») décrit plutôt deux
  propriétés à vérifier indépendamment, pas une dépendance causale entre elles.
- **OU (alternative contextuelle)** — pas illustré dans les 245 règles
  observées, mais concevable : selon le contexte de la page, soit A soit B
  s'applique, pas nécessairement les deux.

**Confirmé systémique**, pas isolé à un exemple : sur la règle 116, la
`strategie_justification` explique clairement que le jugement visuel doit
être posé *avant* la vérification technique (PUIS) — mais le champ
`strategie_analyse` seul (`vision+statique`) ne porte cette information nulle
part. Un consommateur qui ne lirait que ce champ (ex. un futur agent
d'orchestration US1) ne saurait pas que "+" signifie ici une séquence
obligatoire plutôt que deux vérifications indépendantes.

**Sous-cas — composite avec `manuel` impossible à exprimer** (règle 24,
alias mail `+`) : le `controle` a deux volets de nature différente —
"acceptée" (testable en `playwright`) et "fonctionnelle" (l'exemple donné par
le contrôle lui-même, "réception d'un mail envoyé par le site", est hors-page
donc `manuel`). Le format actuel interdit `manuel` en composite : soit on
perd le volet automatisable (tout classer `manuel`), soit on perd le volet
manuel (classé `playwright` seul, comme ici — ne couvre que la moitié du
contrôle).

**Pistes pour V5** (non tranchées, à décider en spec) :

- Garder `+` pour PUIS uniquement, introduire un séparateur/mot-clé distinct
  pour ET (ex. `strategieA&strategieB`)
- Autoriser `manuel` en composite (ex. `playwright+manuel`), ou accepter que
  `manuel` reste une exception pure qui absorbe tout le reste du contrôle dès
  qu'elle s'applique à une partie
- Alternative plus légère : laisser `guide_analyse` porter seul la
  distinction (déjà le cas en pratique via le format "Étape 1 [x] : ... Étape
  2 [y] : ...") sans toucher au champ `strategie_analyse`

## 2. Sous-application du critère "manuel" (O5)

**Méthode** : 5 agents en parallèle ont passé en revue les 245 règles par
lots de 49 (`tmp/audit_lot_1.json` à `_5.json`), cherchant des incohérences
entre `solution`/`controle` (ce qu'Opquast exige réellement) et
`strategie_analyse`/`guide_analyse` (ce que le LLM a produit).

**Constat** : une même famille de problème revient sur 5 règles distinctes,
dans des lots différents (donc pas un artefact de position) — un contrôle qui
exige une vérification **fonctionnelle réelle** (le mécanisme marche
vraiment, un examen humain est requis, un email est effectivement reçu) est
traité comme une simple vérification **syntaxique/UI** (présence d'un
attribut, d'un message de confirmation) :

- **Règle 24** (alias mail `+`) — `playwright`, mais le contrôle exige un
  test de réception réelle ("réception d'un mail envoyé par le site"). Le
  guide ne vérifie que l'absence d'erreur de validation, jamais la boîte mail.
- **Règle 69** (étiquette de champ de formulaire) — `statique`, mais le
  `controle` source dit explicitement "ne peut donc être automatisée mais
  nécessite un examen manuel de chaque formulaire". Le guide demande pourtant
  un jugement sémantique ("le texte décrit-il effectivement la nature de la
  saisie ?") déguisé en vérification factuelle.
- **Règle 96** (relance 2FA) — `playwright`, ne vérifie qu'un signal UI
  (message de confirmation), jamais la réception réelle du code sur le
  second canal.
- **Règle 113** (contact modérateur) — `statique`, alors que le contrôle dit
  "vérifier qu'il est **effectivement** possible de contacter". La règle 107,
  formulée presque à l'identique ("possible de joindre **effectivement**"),
  est elle correctement classée `manuel`. Incohérence interne entre deux
  règles jumelles.
- **Règle 243** (pertinence d'un caption) — `statique`, alors que le
  `controle` dit littéralement "le contrôle de sa pertinence nécessite un
  examen manuel". Le guide transforme ce jugement en pseudo-contrôle factuel.

**Lecture** : ce n'est pas un problème de qualité de raisonnement du LLM
(cf. points positifs, §5) mais une limite de la consigne R2.4 telle que
formulée en V4 — elle nomme des canaux physiques concrets ("boîte mail, DNS,
document PDF externe, SMS, second appareil") mais ne couvre pas le cas plus
général et plus fréquent : **toute exigence de vérification "effective"/
"réelle" d'un mécanisme, par opposition à sa simple présence syntaxique**,
qu'elle passe ou non par un canal externe nommé. Les règles 69 et 243 n'ont
même pas de canal externe au sens strict — c'est un jugement humain/sémantique
qui manque, pas un second appareil.

**Piste pour V5** : reformuler R2.4 pour couvrir explicitement ce cas plus
large (ex. "si le contrôle exige de vérifier qu'un mécanisme fonctionne
*effectivement*/*réellement*, au-delà de sa simple présence syntaxique, et
qu'aucune méthode automatisée ne peut observer ce résultat sur la page
elle-même, c'est `manuel`"), avec 69 et 243 comme nouveaux few-shot candidats
(jugement sémantique sans canal externe) en complément de 111/24/96/113
(canal externe).

## 3. Incohérence `playwright`/`statique` sur les vérifications HTTP brutes (O6)

**Constat** (lot 5, règles 197-245) : les règles **206, 207, 210, 211, 222,
226, 227** (X-Content-Type-Options, Content-Type, X-XSS-Protection,
X-Frame-Options, code HTTP 404, Content-Encoding/gzip, en-têtes de cache)
sont classées `playwright` ("nécessite l'interception du trafic réseau via
un navigateur automatisé"). Mais des règles techniquement identiques — lire
un en-tête ou un code de statut HTTP de réponse — sont classées `statique`
dans le **même lot** : HSTS (199), CSP (212), en-tête Server (213), charset
(228, 233), et surtout **223** (page 404 personnalisée), qui ne fait qu'une
requête HTTP directe + comparaison de contenu HTML brut, sans aucun rendu JS.

**Analyse** : un en-tête ou un code de statut HTTP se récupère par une
simple requête (crawler/`requests`), sans exécution JS ni rendu navigateur —
la règle 200 le fait déjà en `statique` pour vérifier le protocole des
ressources liées, et 223 confirme qu'une analyse de contenu HTML après coup
(comparaison structurelle avec la page d'accueil) reste `statique`, pas plus
lourd. Rien ne justifie que 7 règles au traitement identique exigent
Playwright quand 6 autres (dont 223, la plus proche de 222) s'en passent.
Contrairement à O5, ce n'est pas une question de frontière `manuel` — c'est
une incohérence pure entre `playwright` et `statique` sur un même type
d'opération technique.

**Piste pour V5** : ajouter un few-shot ou une précision explicite dans le
prompt — "la lecture d'un en-tête ou d'un code de statut de réponse HTTP est
vérifiable par simple requête, donc `statique`, même si la page elle-même a
été chargée via un crawler" — pour ancrer que "réponse HTTP" n'est pas
synonyme d'"interaction navigateur".

## 4. Candidats few-shot pour V5

- **Règle 111** (déjà en Exemple 6 en V4) — reste le meilleur exemple
  "manuel hors-page-web à canal externe nommé"
- **Règle 117** (image-lien) — `statique`, guide jugé exemplaire : couvre
  exhaustivement les 4 éléments concernés (`img`, `area`, `object`, `canvas`),
  critère factuel clair, distingue proprement l'image-lien de l'image simple
  déjà couverte par l'Exemple 1
- **Règle 69 ou 243** — candidats pour illustrer le "manuel sans canal
  externe" (jugement sémantique pur), à choisir un seul pour ne pas alourdir
  le prompt (6 exemples déjà en V4)

## 5. Points positifs à préserver

Constatés indépendamment par les 5 agents du balayage complet (pas seulement
la revue ciblée de David) — à ne pas casser en V5, et à vérifier par
non-régression sur la ré-ingestion complète décidée :

- **Généralisation réelle au-delà des few-shot fournis.** Un seul exemple de
  composite (235) et un seul exemple "hors page web" (111) dans le prompt,
  mais des cas nouveaux et cohérents produits sans les copier : 98, 116, 117,
  65, et toute la famille `playwright+statique` (27, 44, 58 — jamais
  illustrée dans le prompt).
- **`manuel` bien maîtrisé dans la grande majorité des cas**, y compris en
  évitant le sur-classement : les règles 18, 37, 47, 107, 110, 111, 205, 217,
  240, 241 sont correctement en `manuel` et cohérentes entre elles ; la règle
  19 (mécanisme anti-usurpation), proche en surface du cas 2FA/96, n'a **pas**
  été classée `manuel` à tort.
- **Aucun `guide_analyse` spéculatif détecté sur l'ensemble des 245 règles**
  — R2.3 bien appliqué globalement, pas seulement sur les exemples ciblés.
- **Format composite en étapes (R2.2) respecté systématiquement** : partout
  où un composite est utilisé, l'ordre des étapes `[X]`/`[Y]` dans
  `guide_analyse` correspond à l'ordre déclaré dans `strategie_analyse`. Le
  problème n'est pas l'exécution du format (§1) mais ce que le format peut
  exprimer.
- **Distribution globale saine, pas de sur-classement vers une seule
  catégorie** : statique 94, playwright 76, manuel 18, composites 53 répartis
  sur 6 combinaisons différentes — pas de biais massif malgré la hausse des
  composites par rapport à V3 (0 % → 22 %).
- **Lot 4 entier (règles 148-196, 49 règles) jugé propre**, aucune remontée —
  confirme que les problèmes trouvés (§2, §3) sont localisés, pas un défaut
  généralisé du prompt sur l'ensemble du référentiel.

## 6. Décisions actées (2026-07-25)

- **Ré-ingestion complète des 245 règles avec le prompt V5** (pas de
  ré-ingestion ciblée) — pour valider la non-régression sur les points
  positifs (§5) autant que la correction des problèmes (§1-3)
- **`enrich_again`** (script de réécriture ciblée par LLM des règles
  `review_status = a_revoir`/`invalide`, utilisant `review_note` comme
  contexte) — **reporté après le prochain audit** post-V5, pour être conçu
  sur de vraies données de revue

## 7. Hors périmètre immédiat de la spec V5

- **Les 12 règles à problème de cette revue** (24, 69, 96, 113, 206, 207,
  210, 211, 222, 226, 227, 243) ne sont pas corrigées ligne par ligne dans
  cette spec — c'est la ré-ingestion complète avec le prompt V5 corrigé qui
  les redresse, pas une correction manuelle en base
- **`enrich_again`** — cf. §6, chantier séparé après le prochain audit
- **Statut `review_status`/`review_note` en base** pour les 12 règles —
  optionnel avant la ré-ingestion V5 (les valeurs seront de toute façon
  écrasées par le nouveau run), utile seulement si l'on veut tracer la
  décision V4→V5 elle-même
