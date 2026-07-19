---
title: "Base de données — QualiCheck"
subtitle: "Création et gestion du schéma via migrations"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
toc: true
toc-depth: 2
numbersections: true
---

\newpage

## Contexte et objectif

Ce document couvre l'étape désignée `1_BDD` dans le dossier de conception — **prérequis** à toute autre brique de QualiCheck, y compris l'ingestion (`2_ingestion` / `ingestion.md`). Côté code, cette étape correspond au point d'entrée `scripts/migration.py` (cf. section Organisation technique). Elle ne peuple aucune donnée : elle crée le schéma complet, vide, prêt à être rempli.

Contrairement à `ingestion.md` qui ne concerne que le référentiel Opquast, ce document couvre **l'intégralité du schéma** : le référentiel Opquast (`theme`, `regle`, `objectif`, `phase`, `tag` + tables d'association) et le cœur métier QualiCheck (`utilisateur`, `audit`, `page`, `audit_page`, `audit_regle`, `constat`), qui ne sera peuplé que plus tard, au fil des audits.

Ce document ne redéfinit pas le détail des champs — c'est le rôle de `MLD_qualicheck.md`, qui reste la source de vérité pour la structure des tables, contraintes et clés. Ici, on décrit **comment** ce modèle logique devient une base réelle, et avec quels outils.

## Choix technique : gestion du schéma par migrations

Le schéma est géré via un outil de migration (Alembic, cohérent avec la stack FastAPI/SQLAlchemy), plutôt qu'un script SQL exécuté à la main. Trois raisons :

- **Historique versionné** : chaque évolution du schéma est un fichier de migration horodaté et suivi dans Git — cohérent avec vos principes de traçabilité déjà appliqués ailleurs (`strategie_source`, logs d'ingestion).
- **Réversibilité** : une migration Alembic porte une procédure de montée (`upgrade`) et de retour arrière (`downgrade`), utile en développement pour itérer sur le schéma sans tout recréer à la main.
- **Cohérence avec le backend** : FastAPI + SQLAlchemy sont déjà les choix techniques du projet ; Alembic s'intègre nativement à ce couple, sans outil supplémentaire à apprendre.

La première migration crée le schéma complet dans son état initial (toutes les tables du MLD). Les migrations suivantes, si elles existent, porteront les évolutions futures (nouvelles valeurs `strategie_analyse`, ajustements post-MVP...).

## Extension pgvector

PostgreSQL ne gère pas nativement les vecteurs : l'extension **pgvector** doit être activée avant la création de la colonne `embedding` sur `regle`. C'est une opération unique, exécutée dans la première migration, avant toute création de table — l'extension est un prérequis du schéma, pas une option.

## Index HNSW

L'index HNSW (similarité cosinus) sur `regle.embedding` est créé dans la même migration que la table `regle`, même si la table est vide à ce stade. À l'échelle de QualiCheck (245 règles, volume fixe), ce n'est pas un problème : HNSW reste pertinent même construit sur un ensemble qui se peuplera juste après, contrairement à des volumes bien plus importants où l'ordre construction-index / remplissage peut se discuter pour des raisons de performance.

## Déclenchement

Comme pour l'ingestion, l'exécution des migrations est **manuelle**, lancée par l'administrateur en ligne de commande (commande Alembic standard de montée de version). Pas d'automatisation au démarrage du conteneur en MVP : mieux vaut une étape explicite et maîtrisée qu'une migration silencieuse au lancement de Docker, notamment tant que le schéma est encore amené à changer.

Ordre d'exécution du projet, maintenant explicite :

1. `scripts/migration.py` — le conteneur PostgreSQL démarre, les migrations sont appliquées : le schéma existe, vide.
2. `scripts/ingestion.py` — le référentiel Opquast est chargé dans ce schéma.
3. Reste de l'application (audits, dialogue, question libre).

## Organisation technique

Structure conceptuelle des fichiers — rôle de chacun, pas leur contenu.

### Infrastructure

- **`docker-compose.yml`** : service PostgreSQL avec l'extension **pgvector** (image dédiée intégrant l'extension). Port exposé, volume de persistance pour ne pas perdre la base entre deux redémarrages du conteneur.
- **`.env`** : un seul fichier, à la racine du projet, partagé par l'ensemble des dossiers (`1_BDD/`, `2_ingestion/`, backend...). Pas de `.env` propre à `1_BDD/` : la connexion BDD y est définie une fois, réutilisée partout.

### Point d'entrée et modules

`1_BDD/` et `2_ingestion/` ne désignent que la numérotation des documents de conception — pas l'arborescence réelle du code. Côté code, `scripts/` ne contient que les points d'entrée, à plat (`scripts/migration.py`, `scripts/ingestion.py` — cf. `ingestion.md`). Les modules de support vivent sous `app/`, aux côtés de `app/models/` (le domaine métier partagé avec le backend FastAPI) :

| Fichier / dossier | Rôle |
|---|---|
| `scripts/migration.py` | Point d'entrée : déclenche la montée de version Alembic |
| `app/models/` | Déclaration SQLAlchemy des tables — possédée par le backend, importée par la migration (pas l'inverse) |
| `app/migration/alembic.ini` | Configuration de l'outil de migration (connexion BDD, chemin des migrations) |
| `app/migration/env.py` | Point d'entrée technique d'Alembic — charge la configuration et `app/models/` |
| `app/migration/versions/0001_schema_initial.py` | Première migration : extension pgvector, toutes les tables du MLD, index HNSW |

## Points ouverts

*(aucun à ce stade — l'emplacement de `app/models/` est tranché : possédé par le backend, importé par la migration.)*
