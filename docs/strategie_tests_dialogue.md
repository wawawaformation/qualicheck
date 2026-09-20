# Stratégie de tests : atelier de définitions (carte Kanboard #45)

**Sorties de cet atelier** (2026-09-20) : `docs/glossaire_tests.md`
(glossaire propre, sans le dialogue), `conception/4_ci_cd/strategie_tests_et_gates.md`
(décisions CI/CD LLMOps), `conception/4_ci_cd/ci_cd_llmops.drawio` (schéma).
Ce document-ci reste le journal de travail complet (comment on y est
arrivé), pas la source de vérité finale.

Document de travail, tenu **au fur et à mesure** par Claude : chaque échange utile y est noté, pour qu'une nouvelle session ou un autre outil (OpenCode...) reprenne sans rien perdre. Démarré le 2026-09-20 à 15h37.

## Comment reprendre (à lire en premier)

1. Lire ce document jusqu'à « État d'avancement ».
2. Règles de travail avec David : **valider à chaque étape**, **chrono lancé** dès qu'on travaille sur une carte, **aucune carte créée sans demande**, **ne rien supprimer sans accord explicite**, carte terminée = **Done sans la fermer** (voir `docs/agent/02_regles_execution.md`).
3. Ne **pas** proposer de définition avant que David ait écrit la sienne (voir « Méthode »).

## Objectif

Se mettre d'accord sur le vocabulaire (test unitaire, test d'intégration, à quoi ils servent) avant de parler de CI, de mocks et de mesures. David veut « fixer ça dans le marbre, en toute conscience », même pour ce qui est déjà écrit, puis le schématiser et le documenter pour que **n'importe quel agent** le lise.

Pourquoi c'est important pour David : sa mémoire de travail humaine est limitée (loi de Miller) et chaque carte a ses tests et ses mesures ; il faut être au clair sur les stratégies de tests et les métriques.

## Méthode (décidée par David)

1. **David définit** unitaire et intégration, et à quoi ils servent.
2. **Claude définit** les mêmes notions, sans avoir influencé David.
3. **Ensemble** : accords, écarts, ce qui manque ; un vocabulaire commun en sortie.
4. **David montre un schéma** ; Claude le lit, signale les incohérences, n'invente rien.
5. **« On avise »** : on décide ensuite de la suite (CI, mocks, mesures, collection Bruno).

## État d'avancement

| # | Temps | État |
|---|---|---|
| 1 | David définit | **reçu** (unitaire + intégration) |
| 2 | Claude définit | **reçu** (unitaire + intégration + bout en bout) |
| 3 | Mise en commun | **faite** (accords, écart réglé) |
| 4 | Schéma de David | **fait** (lu, confronté au dépôt, incohérences réglées) |
| 5 | On avise | **CI/CD LLMOps fait pour l'instant** (David, 2026-09-20 ~18h) ; reste : tags/manifest de version, etc. |

Kanboard : carte #45 « En cours » depuis le 2026-09-20 15h37, estimée 7,5 h. Trois sous-tâches : (1) définir unitaire et intégration, chrono lancé ; (2) lire et rendre cohérent le schéma de David ; (3) cadrer la suite, « on avise ».

## Définitions de David (mot pour mot)

### Test unitaire (2026-09-20, 15h47)

> un test unitaire.  test qu'un petit bout : un fichier, une classe par exemple. comme en se trouve peut-etre au milieu d'un tout, on peu utiliser des mocks ou des fixtures (je ne sais pas vraiment la différence)

### Test d'intégration (2026-09-20, ~16h)

> pour moi le test d'integration on est plus sur du bout en bout et en principe
> quand on fait genre du PHP, c'est direct pas de boite noir et pas de mock. la
> c'est un peu differrent car on a des LLM et ca compte du temps et de
> l'argent. donc on pourrait faire deux type de tests avec boite noir et reel.

## Définitions de Claude

### Test unitaire

Un test qui vérifie **une seule unité de comportement** (une fonction, une
méthode, une classe) **isolée** de ses dépendances externes (réseau, base de
données, LLM, horloge...). Isolée veut dire : soit la dépendance n'existe pas
dans ce périmètre, soit elle est remplacée par un mock/stub pour ne tester que
la logique propre à l'unité. Rapide, déterministe, pas de coût, s'exécute en
boucle pendant qu'on code.

### Test d'intégration

Un test qui vérifie que **plusieurs unités ou composants réels fonctionnent
ensemble** (ex. code + vraie base de test, ou code + vrai appel HTTP vers une
API interne), sans forcément couvrir le parcours complet de bout en bout. Il
ne mock pas les composants qu'il teste l'assemblage, mais peut encore mocker
ce qui est hors périmètre (ex. un LLM externe payant) si le but est de valider
le câblage plutôt que le contenu produit par ce composant.

Sur ce point je rejoins ton constat : la frontière classique
« pas de mock du tout » tient pour du PHP + base de données, mais craque dès
qu'un composant coûte de l'argent ou du temps à chaque appel (LLM). D'où ta
proposition de deux variantes — boîte noire (LLM mocké, on teste le câblage)
et réel (LLM réellement appelé, on teste le résultat) — qui correspond à ce
que le dépôt fait déjà informellement : `tests/integration/` (HTTP réel vers
`api_regles`, base de test réelle) vs `tests/acceptance/` (appels réels au
LLM, jeux de données réels).

### Test de bout en bout (à distinguer, terme que tu as évoqué)

Un test qui parcourt le chemin complet côté utilisateur (ex. requête HTTP
entrante -> logique -> base -> réponse), sans mock nulle part sur ce chemin. Un
test d'intégration peut être bout en bout, mais tous les tests d'intégration
ne le sont pas forcément (on peut intégrer deux composants sans couvrir tout
le parcours).

## Glossaire (précisions données à David, à valider ensemble)

- **Mock** : un faux objet qui remplace une dépendance du code testé, pour l'isoler. Exemple du projet : `patch("app.agent_us2.tools.httpx.get")` remplace l'appel réseau ; on peut aussi vérifier comment il a été appelé.
- **Fixture** : la préparation réutilisable du décor d'un test (données, configuration, objets), fournie par pytest avec `@pytest.fixture`. Exemples du projet : `env_api` (pose l'URL de l'API), `llm` (remplace le modèle).
- Ce ne sont pas deux alternatives : une fixture est un **mécanisme de préparation** et peut contenir des mocks. Un mock est un faux objet, une fixture est ce qui prépare le test.

## Accords, écarts, manques

- **Accord** : test unitaire = une unité isolée de ses dépendances (mock au besoin).
- **Accord** : avec un LLM qui coûte du temps/argent, la règle « pas de mock »
  ne peut pas tenir partout ; d'où deux variantes du test d'intégration —
  boîte noire (LLM mocké) et réel (LLM réellement appelé).
- **Écart réglé** : David pensait bout en bout et intégration synonymes.
  Clarifié : bout en bout = parcours complet sans aucun mock sur le chemin ;
  intégration = assemblage de composants réels, pas forcément le parcours
  complet. Un test bout en bout est un cas particulier de test d'intégration,
  pas l'inverse.

## Schéma de David (`~/Bureau/ci-feature-dev.drawio.png`, étape 4)

Lu par Claude le 2026-09-20. Points de cohérence vérifiés contre le dépôt
réel (`.gitea/workflows/ci-dev.yml`, `cd-staging.yml`, `Makefile`) :

- `0a -> 0b (CI à chaque push, lint + unit/intégration mockés) -> CI verte ->
  0c (revue/PR)` : conforme à `ci-dev.yml`.
- `make api-regles-acceptance` tourne déjà automatiquement à chaque push sur
  `staging` (`cd-staging.yml`) — possible car ce jeu ne coûte rien (aucun
  appel LLM, un seul `PATCH` réversible). La vraie question ouverte porte
  donc plutôt sur `rag_acceptance`/`agent_us2` (ceux-là appellent un
  LLM/des embeddings, donc coûtent) : les rejouer automatiquement en
  staging, ou seulement à la demande ? **Pas encore tranché.**

Chaîne complète confirmée par David (2026-09-20 ~17h45), corrigeant un
résumé imprécis de Claude qui omettait le merge sur `dev` :

**branche feature** → CI (unit + intégration mockée) → revue/PR → merge sur
`dev` → **Acceptance** (Gherkin réel) → `staging` (déploiement, **recette/
UAT**) → **prod** (avec observabilité).

Ceci répond en partie à la question ouverte du schéma sur l'observabilité
(LANGFUSE) : elle se situe côté **prod** (trafic réel d'utilisateurs), pas
sur les étapes de test en amont — cohérent avec `app/observability/
tracing.py` (conçu pour tracer une requête, pas un test). Reste ouvert :
l'observabilité couvre-t-elle uniquement la prod, ou aussi `staging`
pendant la recette ?

**Correction ultérieure** : David veut en fait aussi observer les traces
Langfuse **sur une PR** (juger le comportement réel du LLM pendant
l'Acceptance, en même temps que la revue du diff) — l'observabilité n'est
donc pas réservée à la prod. Techniquement, il faudrait :
1. Configurer `OTEL_EXPORTER=otlp` + secrets Langfuse pendant l'étape
   Acceptance en CI (aujourd'hui la CI n'exporte que du local).
2. Un `APP_ENV` distinct (ex. `ci`/`pr`) pour ne pas mélanger ces traces
   avec `dev`/`staging`/`prod` dans Langfuse.
Rien implémenté, juste consigné.

**Gates de blocage à chaque étape** (David) : chaque étape a déjà (CI verte
avant revue, revue avant merge) ou devrait avoir un gate. Pour la mesure
en tant que gate, deux formes possibles, discutées :
1. **Gate automatique à seuil fixé** (retenu par David) — ex. recall@5 ≥ un
   plancher défini. Nuance de vocabulaire : dès qu'un seuil est fixé, ce
   n'est plus une "mesure" au sens strict (pas de verdict) mais un test
   d'acceptance avec critère chiffré.
2. Gate humain (David lit le rapport et décide) — non retenu.

Risques signalés par Claude sur l'option 1 : coût récurrent si rejoué à
chaque merge, et faux échecs possibles à cause du non-déterminisme du LLM
(prévoir une marge sous la valeur mesurée, pas le chiffre exact). **David
répond : ne pas gater à chaque merge sur `dev`, mais plus en aval, à un
rythme moins fréquent** — proposition retenue : le gate se greffe sur la
promotion `dev -> staging` (aujourd'hui un geste manuel, PR occasionnelle),
pas sur chaque push. L'environnement d'exécution reste `dev` (LLM réel,
pas besoin d'un vrai déploiement), seule la fréquence change.

Pour le seuil du retrieval, une preuve existe déjà :
[[protocole_mesure_retrieval]] (mémoire) donne recall@5 = 0,921
(exploration) / 0,903 (réservé) sur le chunk de production actuel — base
défendable pour fixer un plancher avec marge (ex. ≥ 0,85), pas du doigt
mouillé. Pour les autres mesures (refus, guardrail), vérifier qu'un
protocole aussi rigoureux existe avant de leur fixer un seuil.

**Monitoring produit en prod** : sujet noté par David, explicitement
reporté ("on verra plus tard"), rien à faire maintenant.

Points en attente :

- **Revue automatisée "Claude Code GitHub Action, backend Azure AI
  Foundry"** : pas encore mise en place, idée à creuser plus tard (David,
  2026-09-20). Payée par la formation, pas l'abonnement perso.
- **Bloc "PR dev -> Comme feature -> Intégration avec LLM"** — clarifié :
  David confirme, ce bloc devient **Acceptance** sur `dev` (là qu'on rejoue
  le Gherkin pour de vrai, appels réels).
- **Rôle de `staging`** — clarifié : pas des tests automatisés
  supplémentaires, mais le déploiement d'un serveur de préprod pour une
  vérification **humaine** avant la prod (David cherchait le terme : c'est
  la **recette**, parfois "bêta-test" quand ce sont des utilisateurs
  pilotes/externes). À distinguer du "test d'acceptance" automatisé —
  même mot "acceptance" en anglais dans certains usages, mais deux choses
  différentes ici.

## Hors périmètre (renvoyé à une autre carte)

- **Dérive des métriques dans le temps** (comment s'en apercevoir, stockage,
  standards/outils type OpenTelemetry Metrics) : sujet important mais hors
  périmètre de la carte #45 selon David. Carte Kanboard **#49** créée,
  priorité très basse, colonne « En attente ». Précision de David : la carte
  #45 (cet atelier — stratégie de tests, CI, mocks, mesures) **est** le sujet
  LLMOps/CI-CD ; ce n'est pas la carte #49 qui en relève.

## Décisions

- **Pas de dossier `tests/e2e/` séparé** : `tests/acceptance/` en tient lieu
  (bout en bout, sans mock). On ouvrira `tests/e2e/` seulement si un besoin
  concret apparaît (parcours complet sans critère métier rattaché).
- **`tests/integration/`** peut contenir du code qui appelle un LLM, mais le
  LLM y reste **mocké** (câblage testé, pas la qualité de la réponse) ; dès
  qu'un test appelle réellement le LLM, il va dans `tests/acceptance/`.
- **Définition retenue pour "acceptance"** (validée par David, 2026-09-20) :
  le terme vient du monde BDD/Gherkin (un critère métier validé), et se
  retrouve avec des appels réels dans ce projet un peu par nécessité (LLM
  payant/non-déterministe) plus que par définition stricte du mot.

## Constats factuels utiles (repérés dans la session, ne sont pas des définitions)

Ce que le dépôt contient aujourd'hui, pour situer la discussion :

- `tests/unit/` (mocks, sans réseau ni base), `tests/integration/` (dont des appels HTTP réels vers l'API des règles, et une base de test), `tests/migration/` (vise la vraie `POSTGRES_DB`, en lecture seule).
- `tests/acceptance/` : les jeux de données **et** 4 vérifications à appels réels (rangées là depuis la carte #44). `tests/mesures/` : 5 campagnes de mesure (elles produisent des chiffres, pas un vert ou rouge). Aucun n'est collecté par pytest (seuls les `test_*.py` le sont).
- CI Gitea `ci-dev.yml` : `ruff`, migrations, puis `pytest tests/unit tests/integration`. CD `cd-staging.yml` : mêmes tests avant déploiement, puis `make api-regles-acceptance` sur l'hôte de staging.
- Une collection Bruno `qualicheck` (hors dépôt, `~/Documents/bruno/qualicheck_data`) : 16 requêtes, API des règles et API business, en local. Rattachée à cette carte : la versionner comme niveau de preuve « HTTP de bout en bout » (jetons en clair à remplacer par des variables avant).
- Règle du projet : tout test destructif utilise `POSTGRES_TEST_DB`, jamais `POSTGRES_DB` (incident du 2026-07-25).
- Coût : les appels LLM réels sont payants (la régénération des 245 règles coûte un appel chacune) ; le pipeline LLM applique 3 retries avec backoff.
- Écart connu : la méthode de David parle de `tests/acceptation`, le dépôt a `tests/acceptance`.
- Incohérence repérée (2026-09-20, non corrigée) : `tests/acceptance/rag_dense_acceptance.py`
  n'est pas une acceptance (pas de verdict pass/fail) mais une **mesure pour
  décision** (compare plusieurs `top_n`, produit un rapport Markdown) — même
  profil que `tests/mesures/mesure_*.py`. Mal nommé/mal rangé au regard de la
  distinction acceptance/mesure qu'on vient de fixer. David confirme : « très
  mal nommé ». Rien déplacé/renommé pour l'instant, pas de demande explicite
  en ce sens.

## Glossaire final (convention du projet)

Ce n'est pas « LA » définition universelle — certains de ces mots ont des
usages différents ailleurs (ex. acceptance/e2e sont parfois synonymes dans
d'autres équipes). C'est **la convention retenue pour QualiCheck**, actée
dans cet atelier (carte #45), pour qu'on parle tous du même vocabulaire ici.

- **Test unitaire** : vérifie une seule unité de comportement (fonction,
  méthode, classe), isolée de ses dépendances externes (mock au besoin).
  Rapide, déterministe, gratuit.
- **Test d'intégration** : vérifie que plusieurs composants réels
  fonctionnent ensemble (ex. code + vraie base de test, ou vrai appel HTTP
  interne), sans forcément couvrir tout le parcours utilisateur. Deux
  variantes, à cause du coût/temps des LLM :
  - **boîte noire** : le LLM est mocké, on teste le câblage (l'assemblage),
    pas ce que le LLM décide ou produit.
  - **réel** : rare en intégration ; dès qu'un LLM est réellement appelé,
    le test bascule en pratique côté acceptance (coût, non-déterminisme).
- **Test de bout en bout** : parcourt le chemin complet côté utilisateur,
  sans mock nulle part sur ce chemin. Cas particulier de test d'intégration
  (tout bout en bout est une intégration, l'inverse n'est pas vrai) — pas un
  synonyme, malgré un usage confondu ailleurs.
- **Test d'acceptance** : vérifie qu'un critère métier est satisfait
  (verdict pass/fail), au sens BDD/Gherkin. Dans QualiCheck il implique en
  pratique des appels réels (LLM, embeddings) — par nécessité (impossible
  de juger un critère métier avec un LLM mocké dont on décide déjà la
  réponse), pas par définition stricte du mot. Pas de dossier `tests/e2e/`
  séparé : `tests/acceptance/` en tient lieu tant qu'aucun besoin concret
  de parcours complet sans critère métier n'apparaît.
- **Mesure** : script/campagne qui produit des **métriques** pour éclairer
  une décision (ex. comparer plusieurs `top_n` de retrieval). Pas de
  verdict pass/fail — à la différence d'un test d'acceptance.
- **Métrique** : la valeur chiffrée produite par une mesure (ex.
  « recall@10 = 0,82 », « taux de refus = 92 % »).
- **Mock** : un faux objet qui remplace une dépendance du code testé, pour
  l'isoler (ex. `patch("app.agent_us2.tools.httpx.get")`).
- **Fixture** : la préparation réutilisable du décor d'un test (données,
  configuration, objets), fournie par pytest (`@pytest.fixture`). Peut
  contenir des mocks ; ce n'est pas une alternative au mock, mais le
  mécanisme qui le met en place.
- **Recette** (équivalent anglais **UAT**, "User Acceptance Testing" ; parfois
  **bêta-test** avec des utilisateurs pilotes/externes) : vérification
  **humaine**, visuelle, sur un **environnement de recette** réellement
  déployé (`staging` dans QualiCheck), avant passage en prod. Nuance : UAT
  désigne plus précisément la recette faite par l'utilisateur/le métier
  (ex. Élie Sloïm) ; "recette" en français couvre aussi une recette
  technique faite par l'équipe dev elle-même. "Livrer en recette" = déployer
  sur cet environnement de vérification, **pas** livrer en production (la
  confusion est fréquente). À ne pas confondre avec le test d'acceptance
  (automatisé, sans humain) : le mot anglais "acceptance testing" recouvre
  parfois les deux à la fois ailleurs, mais ce sont deux choses différentes
  dans QualiCheck.
- **Dérive** (concept identifié, hors périmètre de cette carte — carte
  Kanboard #49, priorité basse) : évolution non désirée d'une métrique dans
  le temps (ex. baisse de recall après un changement d'embedding), détectée
  en rejouant une mesure régulièrement et en comparant à un historique —
  par opposition à une mesure ponctuelle, qui ne sert qu'une fois.

## Journal du dialogue

- 2026-09-20 15h37 : David lance l'atelier (« d'abord moi, puis toi, puis ensemble ») ; Claude ouvre la carte #45, lance le chrono et crée ce document.
- 2026-09-20 15h47 : David définit le test unitaire (voir plus haut, mot pour mot) et demande la différence entre mock et fixture ; Claude répond (glossaire) sans donner sa propre définition du test unitaire.
- 2026-09-20 ~16h : David définit le test d'intégration (bout en bout, sans mock en PHP classique, mais propose deux variantes — boîte noire / réel — à cause du coût LLM) et demande la version de Claude avant de montrer son schéma. Claude donne ses définitions (unitaire, intégration, bout en bout), rejoint la proposition boîte noire/réel de David en la reliant à ce qui existe déjà dans le dépôt (`tests/integration/` vs `tests/acceptance/`).
- 2026-09-20 ~16h05 : David confirme qu'il pensait bout en bout et intégration synonymes ; écart noté et réglé (voir « Accords, écarts, manques »).
- 2026-09-20 ~16h15 : David demande si `tests/unit`/`integration`/`e2e` serait la bonne structure ; Claude signale l'ambiguïté avec la méthodologie déclarée (`unitaire -> integration -> acceptance`) sans trancher. David ne sait pas ; Claude recommande de ne pas créer `tests/e2e/` (acceptance en tient lieu), David valide implicitement en enchaînant sur la question suivante.
- 2026-09-20 ~16h20 : David demande si `tests/integration/` peut contenir du code appelant un LLM ; vérifié dans le dépôt (`tests/integration/agent_us2/test_repondre.py` : LLM mocké, appel HTTP réel) — confirme la règle : LLM mocké en intégration, réel seulement en acceptance.
- 2026-09-20 ~16h25 : David demande si cette séparation (mock des dépendances externes payantes/lentes, appels réels dans une suite à part) est une pratique courante. Claude confirme (Stripe mode test, contract testing, live/smoke tests) en précisant que l'ampleur coût/latence des LLM justifie une séparation plus stricte que pour un appel HTTP interne classique.
- 2026-09-20 ~16h30 : David valide la formulation de Claude sur l'origine BDD/Gherkin du mot « acceptance » et son usage « par nécessité » ici. Décisions consignées (voir « Décisions »).
- 2026-09-20 ~16h40 : David demande dans quels cas le LLM réel est préférable au mocké ; Claude répond (pertinence/classement, guardrails, régression prompt/modèle, choix d'outil de l'agent, hallucination) en s'appuyant sur les fichiers existants (`rag_dense_acceptance.py`, `mesure_scores_refus.py`, `mesure_guardrail_perimetre.py`).
- 2026-09-20 ~16h45 : en lisant `rag_dense_acceptance.py`, Claude signale qu'il produit un rapport (pas un pass/fail) donc ressemble plus à une mesure. David tranche : c'est bien une mesure pour décision, pas de l'acceptance. Incohérence consignée (voir « Constats factuels »), rien déplacé.
- 2026-09-20 ~16h50 : discussion métrique vs mesure (métrique = la valeur, mesure = la campagne qui la produit) ; David confirme la formulation « script de mesure qui enregistre des métriques pour décider », et que `rag_dense_acceptance.py` est très mal nommé.
- 2026-09-20 ~17h00 : David demande si ces mesures pourraient être partagées avec OpenTelemetry. Claude distingue Traces (déjà utilisé, `app/observability/tracing.py`) et Metrics (API OTel distincte, pas utilisée) ; juge que brancher OTel sur des mesures ponctuelles serait disproportionné aujourd'hui.
- 2026-09-20 ~17h05 : David précise que cette observabilité a servi une fois, ne sert plus pour l'instant, mais qu'un jour ces métriques pourraient indiquer une **dérive**. Il juge le sujet important mais hors périmètre de la carte #45, et demande une petite carte, priorité très basse. Carte Kanboard **#49** créée (voir « Hors périmètre »).
- 2026-09-20 ~17h08 : correction — David précise que « LLMOps/CI-CD » qualifiait la carte #45 (cet atelier) elle-même, pas la carte #49 (dérive). Titre/description de la carte #49 corrigés (retrait de la mention LLMOps/CI-CD), document mis à jour.
- 2026-09-20 ~17h15 : David annonce qu'il va montrer un schéma de CI ensuite. En attendant, il demande un glossaire du vocabulaire défini ensemble dans cet atelier, pour le montrer au jury comme convention explicite du projet (pas une vérité universelle). Glossaire final rédigé (voir « Glossaire final »), à partir des seuls termes actés plus haut dans le document, rien de nouveau inventé.
- 2026-09-20 ~17h25 : David montre `~/Bureau/ci-feature-dev.drawio.png`. Claude le confronte au dépôt réel (`ci-dev.yml`, `cd-staging.yml`, `Makefile`) : cohérent sur `0a/0b/0c` et le mock en intégration ; signale deux points — la revue automatisée Claude Code Action pas encore en place, et le bloc "Intégration avec LLM" qui contredit la convention (LLM réel = acceptance, pas intégration).
- 2026-09-20 ~17h30 : David confirme (« merci de m'avoir repris ») : le bloc devient Acceptance sur `dev`, c'est là que le Gherkin sera testé pour de vrai. Il précise le rôle de `staging` : déployer un serveur de préprod pour une vérification visuelle/humaine (terme cherché : bêta-test), avant la prod. Claude propose le terme **recette** (UAT), distinct du test d'acceptance automatisé malgré le même mot anglais parfois utilisé pour les deux.
- 2026-09-20 ~17h35 : David confirme connaître déjà la pratique mais pas la théorie ; il pensait que « recette » désignait la prod (la livraison). Claude clarifie : recette = l'étape de vérification juste avant la prod (sur un « environnement de recette »), pas la prod elle-même.
- 2026-09-20 ~17h37 : David confirme le terme UAT. Claude précise la nuance : UAT = recette faite par l'utilisateur/le métier (ex. Élie Sloïm), « recette » en français couvre aussi une recette technique par l'équipe dev. Glossaire figé.
- 2026-09-20 ~17h45 : David corrige le résumé de Claude (qui omettait le merge sur `dev`) : la chaîne complète est feature -> CI/revue -> merge dev -> Acceptance (Gherkin réel) -> staging (recette/UAT) -> prod (avec observabilité). Claude relie ça à la question ouverte du schéma sur LANGFUSE : l'observabilité se situe côté prod, cohérent avec `app/observability/tracing.py`. Question restant ouverte : l'observabilité couvre-t-elle aussi `staging` pendant la recette ?
- 2026-09-20 ~17h50 : David introduit deux points — un gate de blocage à chaque étape, et un doute sur où mesurer avant staging (dev ou staging). Claude recommande `dev` (même LLM réel que l'Acceptance, pas besoin de redéployer) et distingue gate automatique (seuil) vs gate humain.
- 2026-09-20 ~17h55 : David choisit le gate automatique à seuil. Claude signale deux risques (coût récurrent, faux échecs par non-déterminisme) et recommande de s'appuyer sur une preuve existante (protocole retrieval conclu) plutôt qu'un seuil arbitraire.
- 2026-09-20 ~18h00 : David répond au risque de coût : ne pas gater à chaque merge sur `dev`, mais à un rythme moins fréquent. Retenu : le gate se greffe sur la promotion `dev -> staging`, pas sur chaque push — l'environnement reste `dev`, seule la fréquence change.
- 2026-09-20 ~18h05 : David ajoute deux points — monitoring produit en prod (explicitement reporté, "on verra plus tard") et souhait d'observer les traces Langfuse **sur une PR** (pas seulement en prod). Claude corrige sa réponse précédente sur l'observabilité et note les prérequis techniques (OTEL_EXPORTER=otlp + secrets en CI, `APP_ENV` distinct pour ne pas mélanger avec dev/staging/prod), rien implémenté.
- 2026-09-20 ~18h10 : David estime avoir fait le tour du volet CI/CD LLMOps de la carte #45 pour l'instant, sauf tags/manifest de version (à traiter séparément).
- 2026-09-20 ~18h15 à ~18h45 : rédaction des sorties de l'atelier — `docs/glossaire_tests.md`, `conception/4_ci_cd/strategie_tests_et_gates.md`, schéma `conception/4_ci_cd/ci_cd_llmops.drawio` (dessiné, contrôlé visuellement, corrigé deux fois — labels qui chevauchaient le texte des nœuds, lignes de notes traversant des boîtes), CHANGELOG mis à jour. Rien implémenté (pas de modification de workflow), conforme à spec -> validation -> implémentation.
- 2026-09-20 ~18h50 : David précise que rien ne sera fait sur `staging` pour l'instant, faute d'authentification. Vérifié : carte Kanboard **#32** ("C4 — Authentification de l'utilisateur"), colonne "En attente", pas démarrée — bloque tout déploiement de `api-business` (agent US2) sur `staging`. Noté comme dépendance explicite dans `conception/4_ci_cd/strategie_tests_et_gates.md`.
