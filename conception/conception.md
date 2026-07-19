---
title: "Dossier de conception – QualiCheck"
subtitle: "Plateforme d'aide à l'audit qualité web basée sur les règles Opquast"
author: "David LEGRAND"
date: "Juin 2026"
lang: fr-FR
toc: true
toc-depth: 3
numbersections: true
---

\newpage

## Contexte

### Cadre de la formation

Ce projet est développé dans le cadre de la formation **Développeur IA agentique** et de la préparation à la certification RNCP37827 « Développeur en intelligence artificielle ».

Il constitue le projet fil rouge de la certification, visant à démontrer les compétences attendues dans les trois blocs du référentiel tout en explorant des usages modernes de l'IA agentique.

### Présentation d'Opquast

Opquast est une organisation française spécialisée dans la qualité web, l'accessibilité, l'expérience utilisateur et les bonnes pratiques numériques.

Elle est notamment connue pour son référentiel de règles qualité web, utilisé dans des contextes de développement, d'audit, de conception, de gestion de projet et de formation. Le référentiel Opquast regroupe actuellement **245 bonnes pratiques** couvrant des domaines variés : accessibilité, contenus, formulaires, SEO, performance, sécurité, confiance utilisateur, architecture de l'information et qualité technique générale.

Opquast propose également une certification reconnue dans le secteur du numérique, permettant d'évaluer la maîtrise des bonnes pratiques qualité web.

Le projet bénéficie du **soutien d'Élie Sloïm**, fondateur et dirigeant d'Opquast, qui garantit la légitimité de l'utilisation du référentiel et du serveur MCP dans le cadre de cette expérimentation technologique.

[Site officiel d'Opquast](https://www.opquast.com/)

---

## Présentation du projet

### À qui s'adresse QualiCheck ?

QualiCheck cible deux profils distincts selon l'US utilisée. Les fiches persona détaillées sont disponibles en annexe (cf. [Annexe J — Personas QualiCheck](annexes/J_personas_qualicheck.jpg)).

**L'auditeur expert** — professionnel certifié Opquast (développeur, intégrateur, chef de projet, consultant qualité). Il maîtrise déjà les 245 règles, comprend les enjeux d'accessibilité, de performance et de SEO. Il n'a pas besoin d'être guidé sur le fond — il a besoin d'aller **vite et sans rien oublier**. QualiCheck est pour lui un **accélérateur d'audit** et un **filet de sécurité** : il automatise les vérifications mécaniques, signale les points d'attention, et lui laisse la décision finale. Il utilise **US1 et US2**.

**L'auditeur curieux** — professionnel du web non certifié Opquast (développeur, intégrateur, chef de projet). Il connaît le web mais pas le référentiel en détail. Il sait qu'il a des points d'amélioration sur ses pages mais ne sait pas quelles règles chercher. Il soumet une page, pose une question en langage naturel, et laisse le **RAG sémantique trouver les règles pertinentes** parmi les 245. Il utilise **US2 uniquement**.

QualiCheck n'est pas un tutoriel. L'agent IA propose, l'auditeur valide — quel que soit son niveau.

### Idée générale

**QualiCheck** est une application web permettant d'assister un auditeur qualité web dans l'analyse d'un site à partir d'un échantillon de pages et d'un ensemble de règles Opquast sélectionnées.

L'agent IA n'est pas conçu comme un système de validation automatique définitive. Il agit comme un **assistant d'analyse**. L'utilisateur conserve toujours la validation finale des constats.

Le workflow général de l'application est le suivant :

**US0 — Ingestion (script CLI)**

1. Import des 245 règles Opquast (API + scraping)
2. Enrichissement par agent IA et indexation pgvector

**US1 — Audit assisté (interface web)**

1. Saisie d'une URL et confirmation des droits
2. Crawl léger et sélection des pages (3 à 10)
3. Sélection des règles parmi les 245 disponibles
4. Génération des constats par l'agent IA
5. Dialogue, validation et génération du rapport

**US2 — Question libre (interface web)**

1. Soumission d'une URL ou d'une image
2. Dialogue libre avec RAG sémantique pur sur les 245 règles

### Cadre légal et conformité

#### Droits d'audit

L'outil intègre un mécanisme de validation où l'utilisateur confirme explicitement qu'il détient les droits nécessaires pour effectuer l'audit de l'URL saisie. Cette mesure encadre l'usage des fonctions de crawl et d'extraction HTML.

#### Conformité RGPD

Conformément aux exigences du référentiel RNCP37827, un registre des traitements de données personnelles sera mis en place. L'application appliquera des procédures strictes de tri et de suppression des données pour garantir la confidentialité et la protection des informations collectées. La section dédiée à la conformité RGPD détaille les traitements identifiés et les mesures appliquées.

---

## MVP — Minimum Viable Product

### Périmètre fonctionnel

Le MVP couvre les trois user stories principales autour d'un référentiel complet de **245 règles Opquast** intégralement ingérées. Le périmètre de chaque audit est maîtrisé côté utilisateur : l'auditeur sélectionne les règles et les pages sur lesquelles il veut travailler.

#### Ce que le MVP inclut

- Import et préparation du référentiel Opquast (RAG)
- Création d'un audit à partir d'une URL
- Crawl léger du premier niveau de navigation
- Sélection des pages et des règles
- Analyse assistée par agent IA
- Dialogue auditeur / agent IA
- Collecte des feedbacks auditeurs par règle (base de la future re-ingestion)
- Génération du rapport final

#### Ce que le MVP n'inclut pas

- Audit automatique de toutes les règles sans sélection
- Crawl profond
- Re-ingestion avec injection des feedbacks terrain (prévu post-MVP)
- Gestion avancée des utilisateurs et des permissions
- Scoring officiel Opquast
- Analyse exhaustive d'accessibilité
- Orchestration multi-agents complexe
- Infrastructure cloud avancée
- Monitoring industriel
- Traitement asynchrone complet

#### La feedback loop : collecte dès le MVP, exploitation post-MVP

Le MVP pose les **bases de la feedback loop** : chaque fois qu'un auditeur valide, modifie ou rejette un constat, ce retour est enregistré via `validation_humaine` et `feedback_auditeur`. Le `strategie_score` agrège ces retours par règle.

Ces données sont collectées dès le premier audit mais **ne sont pas encore exploitées automatiquement** dans le MVP — la re-ingestion avec injection des feedbacks terrain est prévue en post-MVP.

Cette séparation est volontaire : il faut d'abord accumuler suffisamment de données terrain représentatives avant que la re-ingestion ait du sens. Le MVP pose les fondations, le post-MVP les exploite.

### User stories

#### US0 — Importer et préparer le référentiel Opquast

> En tant qu'administrateur de QualiCheck, je souhaite importer et préparer les 245 règles du référentiel Opquast, afin qu'elles soient disponibles dans l'application et exploitables par les agents IA.

**Couverture fonctionnelle :**

- Récupération des règles via l'API REST publique Opquast : intitulé, objectifs, tags, thématiques, phases projet
- Scraping complémentaire des pages publiques Opquast pour les champs non exposés par l'API : `solution` et `contrôle`
- Enrichissement de chaque règle par un agent IA : classification de la stratégie d'analyse, score de confiance, justification, génération du `guide_analyse`
- Stockage en base PostgreSQL (table `regle` et tables associées)
- Construction des chunks (1 chunk par règle, texte dénormalisé)
- Génération des embeddings et indexation pgvector
- Journalisation du résultat de l'import

Cette US est réalisée par un script Python autonome, exécutable en ligne de commande, sans interface web. La re-ingestion avec injection des feedbacks terrain (`--mode reingest`) est prévue en post-MVP.

**Critère d'acceptation** : le script s'exécute sans erreur, les 245 règles sont en base, vectorisées et indexées dans pgvector.

#### US1 — Audit assisté

> En tant qu'auditeur qualité web, je souhaite réaliser un audit d'un site web avec l'assistance d'un agent IA — depuis la sélection des pages et des règles jusqu'à la validation des constats et la génération du rapport — afin de produire une analyse fiable plus rapidement, sans rien oublier.

**Couverture fonctionnelle :**

*Initialisation de l'audit*

- Saisie de l'URL et confirmation des droits d'audit
- Crawl léger du premier niveau
- Sélection des pages à auditer (3 à 10 pages)
- Sélection des règles Opquast par thème ou individuellement parmi les 245 disponibles

*Génération des constats*

- Récupération SQL des règles sélectionnées avec leur `guide_analyse`
- Routing de la stratégie d'extraction par règle : parsing statique, Playwright ou signalement manuel
- Génération des constats par l'agent IA (SQL déterministe — les règles sont connues)
- Stockage des constats en base

*Dialogue et validation*

- Consultation des constats proposés
- Dialogue libre avec l'agent sur les constats — explication, interprétation, reformulation
- Injection SQL du contexte exact de la règle à chaque échange (pas de RAG sémantique ici)
- Modification, validation ou rejet par l'auditeur (`validation_humaine`)
- Saisie d'un feedback qualitatif par constat (`feedback_auditeur`)
- Génération du rapport final

**Critère d'acceptation** : les constats sont générés, dialogués et validés par l'auditeur. Le rapport final ne contient que des constats validés humainement.

#### US2 — Question libre sur une page

> En tant qu'auditeur qualité web, je veux pouvoir soumettre une URL ou une capture d'écran et poser des questions libres, afin d'obtenir une analyse Opquast rapide sans passer par un audit structuré.

**Couverture fonctionnelle :**

- Soumission d'une URL ou d'une image de page
- Extraction légère du contenu à la volée
- **RAG sémantique pur sur les 245 règles** — pas de présélection, pgvector trouve les règles pertinentes à partir de la question
- Dialogue libre avec l'agent, contexte de la page maintenu en **mémoire de session**
- **Guardrails** : l'agent détecte et refuse les questions hors périmètre Opquast
- Les feedbacks de la session alimentent `strategie_score` (feedback loop)
- Session éphémère ou sauvegarde optionnelle

Cette US est le terrain de démonstration privilégié du **RAG sémantique pur**, des **guardrails** et de la **gestion mémoire** — compétences attendues en C11 et C12 du référentiel RNCP37827.

**Critère d'acceptation** : l'agent répond avec précision aux questions sur la page soumise en s'appuyant sur les règles Opquast pertinentes, refuse les questions hors périmètre, et maintient le contexte de la page sur toute la session.

---

## Positionnement éthique et technique

### Une démarche volontaire, pas une contrainte

Les choix techniques de QualiCheck ne sont pas uniquement guidés par la performance ou le coût. Ils reflètent une posture assumée sur trois dimensions : **l'éthique de l'IA**, **l'éco-conception** et **la souveraineté numérique**.

Ces dimensions ont fait l'objet d'une veille documentée, produite en amont des choix d'architecture
(cf. [Annexe D — Synthèse IA souveraine et éthique](annexes/D_synthese_ia_souveraine.md)).

### Éthique de l'IA

Un modèle éthique se définit par sa transparence sur les données d'entraînement, sa conformité à l'AI Act européen, le respect de la propriété intellectuelle des créateurs de contenus, et son explicabilité — la capacité à rendre compte de ses décisions aux régulateurs et aux utilisateurs.

Dans QualiCheck, ce principe se traduit concrètement : l'agent IA ne valide jamais seul. Chaque constat est soumis à la validation humaine de l'auditeur, qui conserve la décision finale. Le choix d'Apertus-70B en production — modèle qualifié d'"IA la plus éthique" par Infomaniak, conforme nativement à l'AI Act — s'inscrit dans cette logique.

### Éco-conception

Le numérique représente une part croissante de la consommation énergétique mondiale. L'éco-conception ne se limite pas à l'interface — elle concerne aussi le choix des infrastructures et des modèles.

QualiCheck applique ce principe à plusieurs niveaux :

- **Modèle d'embedding léger** : All MiniLM L12 v2 (33M paramètres) plutôt qu'un modèle surdimensionné — gratuit, rapide, efficace pour le volume traité
- **Agent enrichissement compact** : gpt-5.4-nano pour une tâche de classification JSON — modèle léger sélectionné sur données benchmark réelles
- **Infrastructure Infomaniak** : énergie 100% renouvelable, chaleur des serveurs revalorisée
- **Pas de base vectorielle externe** : pgvector évite de déployer un service supplémentaire (Chroma, Pinecone) et réduit l'empreinte opérationnelle

### Souveraineté numérique

La souveraineté numérique repose sur trois piliers identifiés par Benjamin Bayart : juridique (quel droit s'applique aux données ?), économique (la plus-value reste-t-elle dans l'espace local ?) et régalien (les fonctions vitales dépendent-elles d'infrastructures étrangères ?).

L'incompatibilité structurelle entre le Cloud Act américain et le RGPD — confirmée par l'invalidation successive du Safe Harbor et du Privacy Shield par la CJUE — rend risqué tout hébergement de données personnelles chez un fournisseur américain pour un projet soumis au droit européen. C'est pourquoi OpenAI, Anthropic et Google sont écartés de la phase de production, indépendamment de leur qualité technique.

Infomaniak (Suisse) est retenu comme fournisseur de production : juridiction européenne, aucune requête API stockée, conformité RGPD native.

### Traçabilité de la démarche

Cette réflexion n'est pas restée théorique. Elle a produit une synthèse documentée, des infographies et un benchmark comparatif des modèles disponibles, qui constituent l'Annexe D et l'Annexe F du présent dossier. Ces documents servent à la fois d'argumentaire de conception et de support pour les compétences C6 et C7 du référentiel RNCP37827.

---

## Flux fonctionnels

Cette section présente les trois flux principaux de QualiCheck sous forme de diagrammes. Ils permettent de comprendre le fonctionnement de l'application avant d'aborder la modélisation des données.

### Le RAG dans QualiCheck : trois usages distincts

Le terme **RAG** (Retrieval-Augmented Generation) recouvre dans QualiCheck trois mécanismes bien distincts. Les distinguer clairement est essentiel — autant pour comprendre l'architecture que pour la défendre devant un jury.

| US | Mode | Justification |
|---|---|---|
| US0 | — | Script CLI, pas d'inférence au retrieval |
| US1 (génération) | SQL déterministe + benchmark RAG | Règles connues, sélectionnées par l'auditeur |
| US1 (dialogue) | SQL déterministe | Contexte d'audit connu, constats posés |
| US2 | RAG sémantique pur | Pas de présélection, l'agent cherche lui-même |

#### US1 — Deux modes comparés : déterministe vs RAG sémantique

En US1, l'auditeur a sélectionné des règles parmi les 245 disponibles en base. QualiCheck propose deux modes d'analyse, utilisés en parallèle pour mesurer l'apport réel du RAG.

**Mode déterministe (SQL)** — accès direct par identifiant, rapide et prévisible :

```sql
SELECT intitule, solution, controle, guide_analyse, strategie_analyse
FROM regle
WHERE id IN (42, 17, 83)
```

Le résultat est injecté dans le prompt de l'agent. L'agent dispose du texte exact de chaque règle et de ses instructions d'analyse — pas de mémoire, pas d'approximation.

**Mode RAG sémantique** — la page analysée est vectorisée et pgvector enrichit le contexte avec des règles proches non sélectionnées initialement. L'agent dispose d'un contexte plus large, potentiellement plus riche.

En comparant les constats produits dans les deux modes sur les mêmes pages et règles, QualiCheck peut répondre à des questions concrètes : le RAG apporte-t-il des constats supplémentaires pertinents ? Génère-t-il du bruit ? L'auditeur valide-t-il plus ou moins souvent les constats RAG ? Ces mesures alimentent directement la feedback loop via `validation_humaine` et `feedback_auditeur`.

**Exemple concret** : l'auditeur a sélectionné la règle 42 "Les images décoratives ont un attribut alt vide". En mode déterministe, le système injecte l'intitulé exact, la solution ("ajouter `alt=""` sur toutes les images décoratives"), le `guide_analyse` et la stratégie ("statique"). En mode RAG, pgvector remonte également la règle 38 "Les liens images ont un attribut alt" et la règle 51 "Les images porteuses d'information ont un attribut alt pertinent" — l'agent peut enrichir son constat avec ces nuances que l'auditeur n'avait pas forcément sélectionnées. L'auditeur expert évalue ensuite si cet enrichissement est pertinent ou superflu — c'est précisément ce que le benchmark mesure.

#### US1 phase 2 — Dialogue sur les constats (SQL déterministe)

En phase 2 d'US1, le contexte est connu : l'auditeur travaille sur des constats issus de règles qu'il a sélectionnées. Le système injecte directement les données des règles concernées par SQL — pas de recherche sémantique, pas d'approximation.

**Exemple concret** : l'auditeur dialogue sur le constat de la règle 42. Le système injecte l'intitulé, le `guide_analyse` et le constat existant dans le prompt. L'agent répond avec précision sur ce contexte exact. Si l'auditeur pose une question sur une nuance de la règle, l'agent s'appuie sur les données injectées — pas sur sa mémoire.

C'est volontairement sobre : le RAG sémantique n'est pas nécessaire quand on sait exactement sur quoi on travaille. Il est réservé à US2 (question libre) où il est vraiment indispensable.

#### Re-ingestion — RAG transversal entre règles

Lors de la re-ingestion, le RAG joue un troisième rôle : détecter des **patterns transversaux**. Quand la règle 17 a un mauvais score, le script interroge pgvector pour trouver des règles sémantiquement proches ayant eu les mêmes types de rejets. L'agent de re-ingestion dispose alors des feedbacks de la règle 17 mais aussi des patterns observés sur des règles similaires — ce qui lui permet de réviser le `guide_analyse` avec un contexte beaucoup plus riche qu'un simple taux de rejet.

**Exemple concret** : la règle 17 "Le site propose un moteur de recherche" et la règle 23 "Le site propose un plan du site" ont toutes deux des feedbacks du type "ne s'applique pas aux pages internes". Le RAG détecte ce pattern commun et l'agent peut généraliser la correction : *"préciser dans le guide_analyse que cette règle s'applique uniquement aux pages principales de navigation"*.

### US0 — Pipeline d'ingestion

Le pipeline d'ingestion est un script autonome exécuté en dehors de l'interface web. Il prépare le référentiel Opquast pour qu'il soit exploitable par les agents IA lors des audits. Il se déroule en 7 étapes séquentielles, depuis l'acquisition des données jusqu'à l'indexation vectorielle dans PostgreSQL.

![Pipeline d'ingestion QualiCheck](annexes/C_pipeline_ingestion.jpg)

*cf. [Annexe C — Pipeline d'ingestion](annexes/C_pipeline_ingestion.jpg)*

Les données Opquast sont acquises depuis deux sources complémentaires : l'API REST publique pour les champs structurés, et un scraping des pages publiques pour les champs `solution` et `contrôle` non encore exposés par l'API. Un agent LLM enrichit chaque règle en une seule inférence, produisant la stratégie d'analyse, le score de confiance et le `guide_analyse`. Les règles sont ensuite stockées en PostgreSQL, chunkées avec tous leurs champs dénormalisés, vectorisées via All MiniLM L12 v2, et indexées dans pgvector.

En post-MVP, le même script pourra être lancé avec `--mode reingest` pour la re-ingestion avec injection des feedbacks terrain.

### US1 — Flux d'audit

L'auditeur saisit une URL, sélectionne les pages et les règles à auditer parmi les 245 disponibles en base. Le système récupère les règles sélectionnées et les injecte dans le prompt de l'agent — en mode déterministe (SQL direct) ou en mode RAG sémantique pour mesurer l'apport de chaque approche. Un agent de routing choisit la stratégie d'extraction adaptée à chaque règle — parsing statique, rendu JavaScript via Playwright, ou signalement pour vérification manuelle. L'agent d'audit génère les constats.

![Flux d'audit — US1](annexes/D_pipeline_audit.jpg)

*cf. [Annexe D — Flux d'audit US1](annexes/D_pipeline_audit.jpg)*

Le routing par stratégie est un point clé : en distinguant les règles vérifiables par parsing HTML statique de celles qui nécessitent un rendu JavaScript, on évite d'instancier Playwright systématiquement. Les règles signalées "manuel" sont présentées à l'auditeur expert comme des points d'attention à vérifier lui-même — ce sont typiquement des règles relevant du jugement éditorial qu'aucun agent ne peut trancher de façon fiable.

### US1 — Dialogue et validation (suite de l'audit)

L'auditeur consulte les constats et engage un dialogue avec l'agent pour les comprendre, les challenger ou les reformuler. Le contexte d'audit est connu — les règles ont été sélectionnées, les constats sont posés. Le système travaille en **SQL déterministe** : il injecte les données exactes des règles concernées dans le prompt de l'agent, sans recherche sémantique. L'agent répond avec précision sur les constats en cours. L'auditeur valide, modifie ou rejette chaque constat, et peut laisser un **feedback qualitatif** qui sera utilisé lors de la prochaine re-ingestion.

![Flux de dialogue — US2](annexes/E_pipeline_dialogue.jpg)

*cf. [Annexe E — Flux de dialogue et validation US1](annexes/E_pipeline_dialogue.jpg)*

Ce flux illustre le principe fondamental de QualiCheck : **l'IA ne valide pas, elle propose**. La boucle de dialogue permet à l'auditeur expert de comprendre le raisonnement derrière chaque constat, de le corriger si nécessaire, et de conserver la maîtrise de la décision finale. Chaque feedback contribue à améliorer la précision du pipeline pour les prochains audits — c'est la feedback loop en action.

---

## Modélisation des données

Les flux fonctionnels décrits ci-dessus s'appuient sur une modélisation des données pensée pour supporter à la fois le référentiel Opquast, le cœur métier des audits, et le pipeline IA avec sa feedback loop.

### MCD — Modèle Conceptuel de Données

Le MCD est réalisé selon la méthode Merise. Il distingue deux ensembles :

**Référentiel Opquast** (données importées à l'ingestion) : `theme`, `regle`, `objectif`, `phase`, `tag` et leurs associations.

**Cœur métier QualiCheck** (données produites lors des audits) : `utilisateur`, `audit`, `page`, `audit_page`, `audit_regle`, `constat`.

Le champ `validation_humaine` sur `constat` est central : il rappelle que l'agent IA assiste l'auditeur mais ne prend pas la décision finale. Le champ `feedback_auditeur` sur `constat` est la matière première de la feedback loop : il stocke le commentaire qualitatif de l'auditeur sur chaque constat, qui sera agrégé et injecté dans le prompt de re-ingestion.

Le MCD complet est disponible en annexe B
(cf. [Annexe B — MCD QualiCheck](annexes/B_MCD_qualicheck.jpg)).

![MCD QualiCheck](annexes/B_MCD_qualicheck.jpg)

Le dictionnaire de données complet est disponible en annexe A
(cf. [Annexe A — Dictionnaire de données](annexes/A_dictionnaire_donnees.xlsx)).

***Avenir** : Modèle Physique de Données (MPD)*

### Champs liés au pipeline IA et à la feedback loop

Les champs suivants sont ajoutés sur la table `regle` pour supporter le pipeline d'ingestion intelligent et la feedback loop :

| Champ | Type | Rôle |
|---|---|---|
| `strategie_analyse` | VARCHAR(20) | Méthode de vérification : `statique`, `playwright`, `manuel` |
| `strategie_justification` | TEXT | Explication du choix produite par le LLM |
| `strategie_source` | VARCHAR(20) | Origine : `ia_import`, `ia_reingest`, `admin` |
| `strategie_score` | DECIMAL(3,2) | Score agrégé des feedbacks terrain (calculé depuis `constat`) |
| `guide_analyse` | TEXT | Instruction pour l'agent d'audit, générée et révisée à chaque ingestion |
| `llm_provider` | VARCHAR(20) | Modèle LLM utilisé pour la génération (benchmark) |
| `embedding` | vector(384) | Vecteur pgvector — All MiniLM L12 v2, 384 dimensions |

Et sur la table `constat` :

| Champ | Type | Rôle |
|---|---|---|
| `feedback_auditeur` | TEXT | Commentaire qualitatif de l'auditeur sur le constat |
| `validation_humaine` | LOGICAL | Décision finale : accepté, modifié ou rejeté |

**Sur le strategie_score** — c'est une valeur calculée, agrégée depuis les feedbacks des auditeurs sur les constats de chaque règle. Un score bas ne signifie pas que la règle est mal définie — il signifie que le LLM ne l'analyse pas bien, et que son `guide_analyse` mérite d'être révisé.

---

## Feedback loop — Architecture et évolutions

### Ce que le MVP collecte

À l'issue de chaque audit (US1), chaque constat porte :

- une décision (`validation_humaine`) : accepté, modifié ou rejeté
- un commentaire optionnel (`feedback_auditeur`) : "constat trop générique", "Playwright inutile ici", "la règle ne s'applique pas aux pages internes"

Ces feedbacks sont stockés en base et agrégés par règle. Le `strategie_score` reflète le taux de validation humaine par règle — une valeur calculée, pas saisie manuellement. **Dans le MVP, ces données sont collectées mais pas encore exploitées pour la re-ingestion.**

Le diagramme ci-dessous illustre le cycle complet — MVP (collecte) et post-MVP (re-ingestion active).

![Feedback loop MLOps — QualiCheck](annexes/I_feedback_loop.jpg)

*cf. [Annexe I — Feedback loop MLOps](annexes/I_feedback_loop.jpg)*

### Post-MVP — Re-ingestion avec injection des feedbacks

Quand suffisamment de données terrain ont été accumulées, l'administrateur pourra lancer manuellement :

```bash
python ingest.py --mode reingest
```

Le script :

1. identifie les règles dont le `strategie_score` est sous le seuil
2. récupère les feedbacks textuels associés
3. utilise le RAG pour détecter des **patterns transversaux** entre règles similaires
4. injecte le contexte terrain dans le prompt de l'agent LLM pour réviser `guide_analyse` et `strategie_analyse`
5. re-vectorise les chunks concernés dans pgvector

**Exemple de prompt de re-ingestion :**

```
Règle 17 — Le site propose un moteur de recherche
score : 0.31 sur 12 audits

Feedbacks auditeurs :
- "Constat trop générique, ne tient pas compte des sites e-commerce"
- "La règle ne s'applique pas aux pages internes, seulement à l'accueil"

Règles similaires avec mêmes patterns (via RAG) :
- Règle 23 : même pattern "ne s'applique pas aux pages internes"

Reconsidère ta classification et révise le guide_analyse en conséquence.
```

### Lien avec le référentiel

Cette architecture constitue une implémentation des pratiques MLOps attendues en **C13** du référentiel RNCP37827 — chaîne de livraison continue d'un modèle d'IA. Le MVP pose les fondations (collecte), le post-MVP active la boucle (re-ingestion). Le "modèle" amélioré est le pipeline RAG dans son ensemble.

---

## Choix techniques

### Vue d'ensemble de la stack

| Composant | Technologie | Justification |
|---|---|---|
| Backend | FastAPI (Python) | Léger, performant, documentation OpenAPI automatique |
| Frontend | Vue.js | Réactif, adapté aux interfaces conversationnelles |
| Base de données | PostgreSQL + pgvector | Source de vérité unique, index vectoriel intégré |
| LLM enrichissement (dev) | gpt-5.4-nano via Azure | Taux d'erreur 2.7%, validé benchmark, JSON fiable |
| LLM enrichissement (dev) | gpt-5.4-nano via Azure | Taux d'erreur 2.7%, validé benchmark, JSON fiable |
| LLM audit génération (dev) | gpt-5.4 via Azure | Qualité raisonnement, 1 656 ms médiane |
| LLM audit dialogue (dev) | gpt-5.4-mini via Azure | Fluidité, 1 046 ms médiane |
| LLM ingestion (dev) | Kimi K2.6 via Azure | Contexte 256K pour re-ingestion, 4.0% erreur |
| LLM fallback | gpt-oss:20b via Ollama Cloud | Gratuit, limites session/semaine |
| LLM enrichissement (prod) | Mistral Small via Infomaniak | Souverain, économique, JSON fiable |
| LLM audit (prod) | Apertus-70B via Infomaniak | Souverain, éthique, conforme AI Act |
| Embedding | All MiniLM L12 v2 (Infomaniak) | Gratuit, multilingue, 384 dimensions, toutes phases |
| Déploiement | Docker + docker-compose | Reproductibilité, portabilité |

Le benchmark complet, l'argumentation des choix et le tableau comparatif des modèles sont détaillés dans le document dédié
(cf. [Annexe F — Choix des modèles LLM](annexes/F_choix_llm.md)).

***Avenir** : Schéma d'architecture technique globale (composants et interactions)*

***Avenir** : Diagramme de séquence RAG (retrieval et injection dans le prompt)*

### Backend — FastAPI

FastAPI est retenu pour sa légèreté, ses performances et sa génération automatique de documentation OpenAPI — critère explicitement attendu en C5 et C9 du référentiel RNCP37827. Un seul service FastAPI couvre US1 et US2, consommé par Vue.js via REST/JSON. Compatible Python natif avec les bibliothèques IA (LangChain, httpx, BeautifulSoup, Playwright).

### Base de données — PostgreSQL + pgvector

PostgreSQL constitue la **source de vérité unique** de l'application. L'extension pgvector permet de stocker les vecteurs d'embedding directement dans une colonne de la table `regle`, sans base vectorielle externe (Chroma, Pinecone, etc.).

Avantages déterminants :

- Pas de synchronisation entre deux systèmes
- Requêtes hybrides natives : recherche sémantique + filtres SQL en une seule requête
- Réduction de la complexité opérationnelle
- Cohérence transactionnelle garantie

Un index **HNSW** (Hierarchical Navigable Small World) sera créé sur la colonne `embedding` pour optimiser les recherches par similarité cosinus.

```sql
CREATE INDEX ON regle USING hnsw (embedding vector_cosine_ops);
```

### LLM — Stratégie multi-modèles

QualiCheck mobilise deux agents aux besoins distincts :

- **Agent enrichissement** (ingestion) — instruction following, sortie JSON courte, contexte limité. Priorité : fiabilité du JSON et économie de tokens.
- **Agent d'audit** (US1 + US2) — raisonnement sur pages HTML longues, dialogue multi-tours. Priorité : fenêtre de contexte et qualité de raisonnement.

Le code permet de basculer entre modèles sans modifier l'intégration métier grâce à quatre variables de configuration indépendantes (cf. [Annexe F — Choix des modèles LLM](annexes/F_choix_llm.md) pour le détail complet).

```python
ENRICHMENT_LLM     = "gpt54_nano"   # US0 — enrichissement ingestion
AUDIT_GENERATE_LLM = "gpt54"        # US1 — génération des constats
AUDIT_DIALOG_LLM   = "gpt54_mini"   # US1 — dialogue interactif
FREE_QUESTION_LLM  = "gpt54"        # US2 — question libre
```

Le champ `llm_provider` est tracé en base sur chaque règle générée — un benchmark en conditions réelles intégré au projet.

### Embedding — All MiniLM L12 v2 via Infomaniak

Le modèle d'embedding retenu est **All MiniLM L12 v2**, disponible **gratuitement** via Infomaniak AI Services sur toutes les phases du projet. 33M paramètres, 384 dimensions, multilingue, très faible latence. La colonne pgvector reste `vector(384)` du début à la fin — aucune migration de schéma.

### Déploiement — Docker + docker-compose

L'ensemble des services (FastAPI, PostgreSQL + pgvector, Vue.js) est conteneurisé via Docker et orchestré avec docker-compose.

---

## Pipeline d'ingestion

### Vue d'ensemble

Le pipeline d'ingestion est un **script Python autonome**, exécutable en ligne de commande, rejouable à tout moment. Il traite les 245 règles du référentiel Opquast en séquence et ne nécessite aucune intervention humaine pendant l'exécution.

```
Acquisition → Agrégation → Enrichissement LLM → Stockage PostgreSQL
→ Chunking → Embedding → Indexation pgvector
```

### Étape 1 — Acquisition

- **API REST Opquast** (publique) : intitulé, objectifs, tags, thématiques, phases projet
- **Scraping complémentaire** (BeautifulSoup / Playwright) : champs `solution` et `contrôle`

Ce mix API + scraping répond directement à l'exigence C1 du référentiel RNCP37827.

### Étape 2 — Agrégation

Fusion en mémoire des données issues des deux sources. Les règles incomplètes sont loggées et exclues sans bloquer les autres.

### Étape 3 — Enrichissement par agent LLM

Un **agent unique** traite chaque règle en un seul appel LLM. Le prompt demande une réponse en JSON strict :

```json
{
  "strategie_analyse": "statique | playwright | manuel",
  "strategie_justification": "explication courte",
  "guide_analyse": "instruction précise pour l'agent d'audit"
}
```

Un seul appel réduit de moitié la consommation de tokens (68 appels au lieu de 136).

**Sur le score de confiance** — le LLM évalue lui-même sa certitude sur chaque classification. Les règles sous 0.70 sont flaggées dans un log dédié, sans bloquer l'ingestion. Ce signal priorise les règles à surveiller lors des premiers audits.

**En post-MVP (`--mode reingest`)**, le prompt sera enrichi avec les feedbacks terrain accumulés pour que le LLM révise sa classification et son `guide_analyse`.

### Étape 4 — Stockage PostgreSQL

Insertion dans `regle` et tables associées. En mode reingest : mise à jour ciblée des règles sous le seuil uniquement.

### Étape 5 — Chunking

```
intitulé + solution + contrôle + guide_analyse + tags + phases
```

Texte dénormalisé : le vecteur capture la sémantique complète, sans jointures SQL au retrieval.

### Étape 6 — Embedding

Appel à **All MiniLM L12 v2** via Infomaniak — vecteur de 384 dimensions. **Gratuit** sur toutes les phases.

### Étape 7 — Indexation pgvector

```sql
UPDATE regle SET embedding = [...] WHERE id = x
```

Pas de base vectorielle externe — PostgreSQL joue les deux rôles.

---

## Conformité RGPD

### Contexte

QualiCheck traite deux catégories de données susceptibles de contenir des informations personnelles : les données des utilisateurs de l'application (MVP : utilisateur simulé, versions futures : comptes authentifiés) et les données issues du crawl et de l'analyse des sites audités (URLs, contenus de pages HTML, constats).

L'hébergement de production est assuré par Infomaniak (Suisse), dont la politique garantit qu'aucune requête API n'est stockée. La conformité RGPD est renforcée par ce choix d'infrastructure souveraine.

### Traitements identifiés

| Traitement | Données concernées | Base légale | Durée de conservation |
|---|---|---|---|
| Gestion des utilisateurs | Nom, prénom (MVP : simulé) | Intérêt légitime | Durée du compte — à définir |
| Journalisation des audits | URL auditée, pages sélectionnées | Intérêt légitime | À définir selon business plan |
| Stockage des constats | Extraits de pages HTML, constats IA | Intérêt légitime | Liée à l'audit — à définir |
| Logs d'ingestion | Journaux d'exécution du script | Intérêt légitime | 30 jours glissants |

> Note : les durées de conservation seront définies lors de l'élaboration du business plan post-MVP. Le MVP ne vise pas une mise en production publique — les données traitées sont non personnelles et à usage interne.

### Mesures appliquées

**Minimisation des données** — seuls les champs strictement nécessaires à l'audit sont collectés. Les pages HTML sont analysées en mémoire et seuls les extraits pertinents sont stockés.

**Droits d'audit explicites** — l'utilisateur confirme détenir les droits nécessaires avant tout crawl.

**Hébergement souverain** — production chez Infomaniak (Suisse), protégée contre l'extraterritorialité du Cloud Act américain.

**Authentification** — MVP : utilisateur simulé. Versions publiques : authentification avec gestion des droits d'accès.

### Registre des traitements

***Avenir** : Registre des traitements de données personnelles (RGPD) — à rédiger lors du passage en version publique*

---

## Budget estimé

### Hypothèses

- **245 règles** Opquast (référentiel complet)
- Sessions de développement ponctuelles (formation en parallèle, pas de runs intensifs continus)
- **20 runs d'ingestion** pendant le développement (tests, ajustements de prompts, re-runs)
- 20 sessions de test d'audit (6 pages, ~10 règles par session)
- 20 sessions de dialogue US2 (validation des constats, ~3 échanges par constat)
- Embedding All MiniLM L12 v2 : **gratuit sur toutes les phases**

### Sources de financement

**Phase de développement — Azure AI Foundry (crédits école)**

L'organisme de formation met à disposition un accès Azure AI Foundry partagé entre les apprenants et les formateurs. Le budget mensuel est d'environ **160€/mois** pour l'ensemble du groupe (estimation — à confirmer avec l'OF). L'accès couvre gpt-5.4-nano, gpt-5.4, gpt-5.4-mini et Kimi K2.6, sélectionnés suite au benchmark Azure (cf. [Annexe F — Choix LLM](annexes/F_choix_llm.md)). Ce budget est mutualisé et non dédié au projet QualiCheck seul.

**Fallback — Ollama Cloud**

`gpt-oss:20b` via Ollama Cloud est disponible gratuitement, avec des limites de session (reset toutes les 5 heures) et des limites hebdomadaires.

**Phase finale — Infomaniak (budget personnel)**

Budget personnel plafonné à **20€ (~ CHF 19)**, avec 1M de tokens offerts à l'inscription.

### Scénario nominal — dev Azure + production Infomaniak

| Poste | Détail | Tokens | Coût (CHF) |
|---|---|---|---|
| Ingestion — entrants | 245 règles × 600 tok. × 20 runs | 2.94M | 2.06 |
| Ingestion — sortants (Mistral Small) | 245 règles × 400 tok. × 20 runs | 1.96M | 0.78 |
| Audit US1 — entrants | 20 sessions × 6 pages × 10 règles × 1 500 tok. | 1.8M | 1.26 |
| Audit US1 — sortants (Apertus) | 20 sessions × 50 échanges × 500 tok. | 500K | 1.25 |
| Dialogue US2 — entrants | 20 sessions × 10 constats × 3 échanges × 2 000 tok. | 1.2M | 0.84 |
| Dialogue US2 — sortants (Apertus) | 20 sessions × 30 échanges × 400 tok. | 240K | 0.60 |
| Embedding (All MiniLM L12 v2) | 68 chunks × 20 runs | — | **Gratuit** |
| **Total brut estimé** | | | **CHF 4.74** |
| Déduction 1M tokens offerts | | | — CHF ~1.50 |
| **Coût réel estimé** | | | **CHF ~3.24** |

> La phase de développement (Azure + Ollama Cloud) est à coût nul pour le projet.

### Scénario catastrophe — Infomaniak uniquement

| Poste | Détail | Tokens | Coût (CHF) |
|---|---|---|---|
| Ingestion — entrants | 245 règles × 600 tok. × 20 runs | 2.94M | 2.06 |
| Ingestion — sortants (Mistral Small) | 245 règles × 400 tok. × 20 runs | 1.96M | 0.78 |
| Audit US1 — entrants | 20 sessions × 6 pages × 10 règles × 1 500 tok. | 1.8M | 1.26 |
| Audit US1 — sortants (Apertus) | 20 sessions × 50 échanges × 500 tok. | 500K | 1.25 |
| Dialogue US2 — entrants | 20 sessions × 10 constats × 3 échanges × 2 000 tok. | 1.2M | 0.84 |
| Dialogue US2 — sortants (Apertus) | 20 sessions × 30 échanges × 400 tok. | 240K | 0.60 |
| Embedding (All MiniLM L12 v2) | — | — | **Gratuit** |
| **Total brut** | | | **CHF 4.74** |
| Déduction 1M tokens offerts | | | — CHF ~1.50 |
| **Coût réel scénario catastrophe** | | | **CHF ~3.24** |

Même dans ce scénario défavorable, le coût reste sous le budget plafond de 20€.

### Budget global fixé

**Budget plafond : 20€ (~ CHF 19)**

Facteur ×6 par rapport au coût réel estimé dans les deux scénarios.

---

## Annexes

### Annexe A — Dictionnaire de données

cf. [Annexe A — Dictionnaire de données](annexes/A_dictionnaire_donnees.xlsx)

### Annexe B — MCD QualiCheck

cf. [Annexe B — MCD QualiCheck](annexes/B_MCD_qualicheck.jpg)

### Annexe C — Pipeline d'ingestion (US0)

cf. [Annexe C — Pipeline d'ingestion](annexes/C_pipeline_ingestion.jpg)

### Annexe D — Flux d'audit (US1)

cf. [Annexe D — Flux d'audit US1](annexes/D_pipeline_audit.jpg)

### Annexe E — Flux de dialogue (US2)

cf. [Annexe E — Flux de dialogue et validation US1](annexes/E_pipeline_dialogue.jpg)

### Annexe F — Choix des modèles LLM

Benchmark complet des modèles évalués, argumentation des choix par phase, critères de souveraineté numérique et tableau comparatif final.

cf. [Annexe F — Choix des modèles LLM](annexes/F_choix_llm.md)

### Annexe G — User stories QualiCheck

Formulation complète des trois user stories (US0, US1, US2) avec scénarios détaillés pour US1 et US2.

cf. [Annexe G — User stories](annexes/G_user_stories_qualicheck.jpg)

### Annexe J — Personas QualiCheck

Fiches persona des trois profils utilisateurs : administrateur, auditeur expert et auditeur curieux.

cf. [Annexe J — Personas QualiCheck](annexes/J_personas_qualicheck.jpg)

### Annexe H — Architecture globale

***Avenir** : schéma d'architecture globale des composants — en cours de révision*

### Annexe I — Feedback loop MLOps

Diagramme illustrant le cycle complet de la feedback loop : collecte des feedbacks auditeurs, re-ingestion manuelle, révision des guides et re-vectorisation.

cf. [Annexe I — Feedback loop MLOps](annexes/I_feedback_loop.jpg)

### Annexe D1 — IA souveraine et données numériques

cf. [Annexe D1](annexes/D1_ia_souveraine_donnees.jpg)

### Annexe D2 — Parcours de décision cloud

cf. [Annexe D2](annexes/D2_parcours_decision_cloud.jpg)

### Annexe D3 — Apertus-70B, IA éthique et souveraine

cf. [Annexe D3](annexes/D3_apertus_ethique_souverain.jpg)

---

*Document en cours de rédaction — sections à venir : architecture technique globale (Annexe H), diagramme de séquence RAG.*
