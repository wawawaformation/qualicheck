---
title: "Pipeline d'ingestion — QualiCheck"
subtitle: "Ingestion initiale du référentiel Opquast (245 règles)"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
toc: true
toc-depth: 2
numbersections: true
---

\newpage

## Contexte et objectif

Le pipeline d'ingestion constitue la brique **US0** de QualiCheck. Il transforme le référentiel Opquast — 245 règles qualité web, publiques mais dispersées entre une API REST et le site Opquast lui-même — en un socle de connaissance exploitable par les agents LLM d'audit (US1) et de question libre (US2).

Contrairement aux audits (produits en continu par les auditeurs), l'ingestion est une opération **ponctuelle et administrative** : elle peuple la base une fois, avant toute mise en production, et n'est pas déclenchée par les utilisateurs finaux.

Trois objectifs guident sa conception :

- **Complétude** : couvrir les 245 règles dès le MVP, sans sous-ensemble.
- **Valeur ajoutée IA** : ne pas se contenter de stocker le référentiel brut — l'enrichir avec une stratégie d'analyse et un guide exploitable par l'agent d'audit.
- **Sobriété** : embedding gratuit (Infomaniak), pas de GPU, pas de fine-tuning.

**Prérequis** : ce document suppose que le schéma complet de la base (toutes les tables du MLD — pas seulement celles liées au référentiel Opquast, mais aussi le cœur métier `utilisateur`/`audit`/`page`/`constat`) existe déjà, index HNSW inclus. Cf. `bdd.md` (`scripts/migration.py`), exécuté avant `scripts/ingestion.py`.

## Déclenchement

En MVP, le pipeline est lancé **manuellement par l'administrateur**, via un script en ligne de commande. Ce choix découle du persona *Administrateur* : profil technique, à l'aise avec un terminal, responsable de l'initialisation et de la maintenance de QualiCheck.

Pas d'interface web dédiée à ce stade : l'ingestion n'est pas une fonctionnalité auditeur, et une commande CLI suffit à couvrir le besoin (lancement, suivi des logs, relance en cas d'échec partiel).

## Vue d'ensemble

Le pipeline se déroule en **7 étapes séquentielles**, chacune produisant l'entrée de la suivante :

| # | Étape | Sortie |
|---|---|---|
| 1 | Acquisition | Données brutes API + scraping |
| 2 | Agrégation | 1 objet complet par règle |
| 3 | Enrichissement (agent LLM) | Stratégie + guide d'analyse |
| 4 | Stockage PostgreSQL | Table `regle` + tables de référence |
| 5 | Chunking | 1 chunk texte par règle |
| 6 | Embedding | Vecteur 384 dimensions |
| 7 | Indexation pgvector | Colonne `embedding` requêtable (HNSW) |

*(cf. schéma cible `annexes/C_pipeline_ingestion.drawio`. Le hook `--resume`
(§ci-dessous) n'était pas prévu dans la conception initiale — découvert pratique
en implémentant ; schéma réel avec ce bloc :
`docs/schemas/C_pipeline_ingestion_reel.drawio`.)*

## Étape 1 — Acquisition

Deux sources, non équivalentes :

- **API REST Opquast — source de vérité.** Fournit l'intitulé de la règle, les objectifs qualité associés, les tags et les phases projet concernées. Données structurées, fiables, mises à jour côté Opquast.
- **Scraping du site Opquast — complément.** Ne sert qu'à compléter les champs que l'API n'expose pas en v1 : la solution de mise en œuvre et le contrôle de conformité.

Cette dépendance au scraping est documentée comme un compromis temporaire : si l'API Opquast venait à exposer ces champs, le scraping pourrait être retiré sans impact sur le reste du pipeline.

### Configuration des endpoints

**Endpoint API (sans authentification):**

```
https://api.opquast.com/checklist/public/
```

Retourne la liste des 245 règles au format JSON. Chaque règle contient :

- `id` : identifiant numérique unique
- `intitule` : titre de la règle
- `objectifs[]` : liste des objectifs qualité associés
- `tags[]` : tags thématiques
- `phases[]` : phases du projet concernées

**URLs de scraping (une par règle):**

```
https://checklists.opquast.com/fr/qualite-numerique/{rule_id}
```

Où `{rule_id}` est l'identifiant numérique retourné par l'API. Opquast redirige automatiquement vers l'URL canonique avec slug (ex. `https://checklists.opquast.com/fr/qualite-numerique/regle-avec-des-tirets`).

Le scraping extrait de la page :

- `solution` : recommandation de mise en œuvre
- `controle` : méthode de vérification de la conformité

**Stockage en `.env`:**

```bash
OPQUAST_API_BASE_URL=https://api.opquast.com/checklist/public/
OPQUAST_SITE_BASE_URL=https://checklists.opquast.com/fr/qualite-numerique/
```

Ces deux variables ne sont jamais versionnées (voir section Infrastructure ci-après).

## Étape 2 — Agrégation

Chaque règle acquise devient un objet `Regle`, complété puis enrichi individuellement (étapes 2 et 3). L'ensemble des 245 `Regle` forme l'objet composite **`Regles`** — c'est cette collection, et non une règle isolée, qui doit être **complète et intégralement enrichie** avant de passer à l'étape 4 : le stockage ne porte jamais sur une règle seule mais sur `Regles` au complet.

Si une règle n'a pas pu être complètement récupérée (échec API ou échec scraping sur un des champs) ou enrichie, le script **s'arrête immédiatement**. L'échec est signalé de façon explicite (numéro de règle, champ manquant, source en cause) pour que l'administrateur corrige avant de relancer.

## Étape 3 — Enrichissement (agent LLM)

Étape à plus forte valeur ajoutée du pipeline. Un agent LLM (Kimi K2.6 en développement) reçoit chaque règle agrégée et produit trois éléments :

- **`strategie_analyse`** : la méthode d'extraction pertinente pour vérifier cette règle lors d'un audit — `statique` (analyse du HTML), `playwright` (nécessite une interaction navigateur), ou `manuel` (non automatisable). Ce champ oriente directement le comportement de l'agent d'audit US1.
- **`strategie_justification`** : l'explication du choix ci-dessus, à des fins de traçabilité et de revue humaine.
- **`guide_analyse`** : une instruction opérationnelle, rédigée pour être injectée telle quelle dans le prompt de l'agent d'audit — le cœur du contenu qui sera vectorisé.

Chaque règle enrichie est aussi tracée par `strategie_source = ia_import` (origine : première ingestion) et `llm_provider` (modèle utilisé), ce qui permet de comparer a posteriori la qualité de différents modèles sur cette tâche.

**Résilience des appels LLM.** Le benchmark Azure AI Foundry mené sur le projet montre un taux d'erreur de fond de 3 à 4 % même sur les modèles sains, dominé par les timeouts — un appel LLM ne peut pas être considéré comme garanti. Chaque appel d'enrichissement est donc retenté automatiquement en cas d'échec (timeout ou erreur HTTP), avec un backoff croissant entre les tentatives (ex. 2 s, 4 s, 8 s) pour ne pas insister immédiatement sur un service en difficulté. Nombre de tentatives : **3**. Si les 3 échouent, la règle est considérée en échec d'enrichissement et déclenche l'arrêt fail-fast décrit plus bas — le retry absorbe l'instabilité ponctuelle du service, pas une indisponibilité prolongée.

## Étape 4 — Stockage PostgreSQL

Les données brutes et enrichies sont persistées dans la table `regle`, ainsi que dans les tables de référence associées : `theme` (relation simple — une règle a exactement une thématique), `objectif`, `phase`, `tag` (relations many-to-many via tables d'association). `tag` est le seul champ optionnel : 64 des 245 règles Opquast n'ont aucun tag.

Un point de vigilance conceptuel : l'unicité de `numero` permet de faire de l'ingestion une opération **idempotente** — une ré-exécution du pipeline sur les mêmes données peut mettre à jour les règles existantes (upsert) plutôt que créer des doublons. C'est ce mécanisme qui sera réutilisé en post-MVP pour la ré-ingestion ciblée.

## Étape 5 — Chunking

QualiCheck adopte un chunking **simple et déterministe** : une règle Opquast = un chunk. Pas de découpage sémantique complexe, pas de chevauchement (overlap) — la granularité métier de la règle correspond exactement à la granularité de recherche RAG souhaitée pour l'audit.

Le texte du chunk assemble : intitulé + solution + contrôle + `guide_analyse` + tags + phases. Cet assemblage donne au moteur de recherche sémantique (US2, question libre) un contexte complet sur chaque règle en une seule unité récupérable.

## Étape 6 — Embedding

Vectorisation du chunk via **All MiniLM L12 v2** (Infomaniak), modèle gratuit, 384 dimensions, sans appel GPU. Ce choix reflète le principe de sobriété du projet : pas de coût d'embedding, latence raisonnable, dimension suffisante pour une recherche par similarité sur 245 règles.

## Étape 7 — Indexation pgvector

Le vecteur est stocké directement dans la colonne `embedding` de la table `regle` — pas de base vectorielle externe (Chroma, Pinecone...). PostgreSQL, via l'extension pgvector, joue à la fois le rôle de base relationnelle et de moteur de recherche sémantique.

Un index **HNSW** (similarité cosinus) est construit sur cette colonne pour que la recherche RAG reste performante à l'usage, notamment pour US2 (question libre).

## Gestion des erreurs et idempotence

Principe retenu : **fail-fast et explicite**. Le pipeline construit un objet composite `Regles` (la collection des 245), qui doit être complet et intégralement enrichi avant tout passage au stockage. Une règle incomplète ou non enrichie (échec API, échec scraping, échec de l'agent LLM) arrête le script — pas de poursuite en silence, pas de stockage partiel. L'erreur est signalée le plus clairement possible : numéro de règle, étape, champ concerné.

Ce choix, cohérent avec un déclenchement manuel par un administrateur technique, a une conséquence directe sur la reprise après erreur : le stockage n'intervenant qu'à l'**étape 4**, l'objet `Regles` en cours de construction (acquisition → agrégation → enrichissement) ne vit qu'en mémoire le temps du script. Un arrêt sur erreur le fait disparaître intégralement — il n'y a rien à "reprendre" à l'endroit de l'échec.

Après correction du problème source, le script est donc **relancé depuis le début**, sur les 245 règles. L'idempotence via `numero` (upsert à l'étape 4) garantit que cette relance complète ne crée pas de doublons sur les règles déjà stockées lors d'une exécution précédente.

**Compromis assumé** : à l'échelle de 245 règles, le surcoût mémoire de garder `Regles` en RAM jusqu'au stockage est négligeable (texte + vecteur ≈ 1,5 Ko par règle). Le vrai coût est ailleurs — si l'échec survient tard (ex. règle 244), les enrichissements déjà réussis (donc déjà payés en appels LLM) sont perdus et redemandés à la relance. Ce compromis temps/coût de relance contre sécurité de l'écriture (tout-ou-rien, pas de base partiellement peuplée) est jugé acceptable pour un script d'administration à volume fixe et modeste : sur la base du benchmark Azure (Kimi K2.6 ≈ 4 s de latence médiane), une relance complète prend quelques minutes, pas des heures, et le coût financier de 245 appels LLM reste modeste.

**Raffinement possible (non retenu en v1)** : un cache local léger (fichier, indépendant de la BDD) qui persisterait chaque `Regle` au fur et à mesure de son enrichissement. À la relance, le script sauterait les règles déjà présentes dans ce cache, évitant de repayer les appels LLM déjà réussis — sans casser le principe fail-fast + tout-ou-rien pour le stockage PostgreSQL, puisque ce cache resterait un fichier de travail, pas la base finale. Écarté en v1 par principe YAGNI : à réévaluer si les relances s'avèrent fréquentes ou coûteuses en usage réel.

**Logs** — proposition pour ce premier jet :

- **Sortie console (stderr)** à l'arrêt sur erreur : message structuré et explicite (numéro de règle, étape du pipeline, champ ou source en cause), compréhensible sans investigation supplémentaire.
- **Code de sortie non-nul**, pour que le script reste scriptable/vérifiable (utile même si l'exécution MVP est manuelle).
- **Fichier de log local** (texte horodaté, pas d'outil dédié), une ligne par règle et par étape :

```
[2026-07-18 14:32:01] Règle 42 — agrégation : OK
[2026-07-18 14:32:03] Règle 42 — enrichissement : OK
[2026-07-18 14:32:03] Règle 42 — ajout à Regles : OK
...
[2026-07-18 14:35:10] Règle 244 — agrégation : KO (scraping : champ 'controle' introuvable)
→ arrêt du script
```

Trois raisons à cette granularité fine (une ligne par règle × par étape, plutôt qu'un log global) :

- **Granularité** : en cas d'échec, on sait immédiatement *quelle* règle, *quelle* étape, *pourquoi* — sans avoir à déduire ou reproduire.
- **Traçabilité** : même une exécution réussie laisse une trace complète (245 × 3 lignes), exploitable a posteriori (durée totale, lenteurs localisées sur certaines règles).
- **Grep-abilité** : format uniforme, filtrable en une commande sur un numéro de règle pour reconstituer tout son parcours dans le pipeline.

Pas de lien avec Langfuse : celui-ci monitore les appels LLM en production (audit, dialogue), pas un script d'ingestion ponctuel lancé par l'administrateur.

## Organisation technique

Structure conceptuelle des fichiers nécessaires — rôle de chacun, pas leur contenu (l'implémentation reste une étape ultérieure).

### Infrastructure

- **`.env`** : trois catégories de variables, jamais versionnées.
  - **Connexion BDD** : host, port, utilisateur, mot de passe, nom de la base — la base elle-même (service PostgreSQL + pgvector, via `docker-compose.yml`) est un prérequis fourni par `1_BDD/`, pas créée ici.
  - **Endpoints Opquast** : `OPQUAST_API_BASE_URL` (API REST, sans authentification) et `OPQUAST_SITE_BASE_URL` (base pour le scraping). Voir section "Configuration des endpoints" ci-avant.
  - **Accès LLM** : endpoint Azure AI Foundry, clé d'API, noms des déploiements utilisés en développement (Kimi K2.6 pour l'enrichissement).

### Point d'entrée et modules

`2_ingestion/` ne désigne que la numérotation du document de conception — pas l'arborescence réelle du code. Côté code, `scripts/` ne contient que les points d'entrée, à plat (`scripts/migration.py`, `scripts/ingestion.py` — cf. `bdd.md`). Les modules de support vivent sous `app/`, dans `app/ingestion/` :

| Fichier | Rôle |
|---|---|
| `scripts/ingestion.py` | Point d'entrée : orchestre les 7 étapes en séquence, applique le principe fail-fast, écrit les logs |
| `app/ingestion/acquisition.py` | Appel API REST Opquast + scraping complémentaire |
| `app/ingestion/aggregation.py` | Fusion en objet `Regle`, contrôle de complétude (déclenche l'arrêt si champ manquant) |
| `app/ingestion/enrichment.py` | Appel à l'agent LLM (Kimi K2.6), avec la logique de retry (3 tentatives, backoff) |
| `app/ingestion/stockage.py` | Écriture PostgreSQL : upsert sur `regle` (via `numero`) et sur les tables de référence (`theme`, `objectif`, `phase`, `tag`) — s'appuie sur `app/models/` |
| `app/ingestion/chunking.py` | Construction du texte du chunk par règle (intitulé + solution + contrôle + `guide_analyse` + tags + phases) |
| `app/ingestion/embedding.py` | Appel au modèle d'embedding (All MiniLM L12 v2 via Infomaniak) |

Point à trancher plus tard : l'écriture du vecteur dans la colonne `embedding` (un simple `UPDATE`) est naturellement rattachée à `app/ingestion/stockage.py`. La création de la table `regle` elle-même et de son index HNSW **ne fait pas partie de ce document** — cf. note de prérequis en introduction et `bdd.md` (`scripts/migration.py`).

## Post-MVP — Ré-ingestion (mention rapide)

Le champ `strategie_score`, calculé depuis `constat.validation_humaine`, accumule un signal de qualité au fil des audits. Une fois un seuil atteint, une **ré-ingestion ciblée** (post-MVP) reprend l'étape 3 avec le contexte terrain (`feedback_auditeur`), met à jour `guide_analyse` (`strategie_source = ia_reingest`) et re-vectorise uniquement les chunks concernés — sans fine-tuning ni GPU, dans la continuité des principes du pipeline initial. Détail complet : cf. `I_feedback_loop.drawio`.
