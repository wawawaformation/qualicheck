# QualiCheck

Application web d'aide à l'audit qualité web, basée sur le référentiel Opquast (245 règles). Agents LLM + pipeline RAG (pgvector) + feedback loop.

> Ce fichier ne répète pas les règles générales déjà posées dans `~/.claude/CLAUDE.md` (philosophie, conventions de code, pédagogie). Il ne couvre que ce qui est spécifique à QualiCheck.

## Contexte du projet

QualiCheck est le **projet de certification** présenté devant un jury pour valider une formation développeur IA agentique — **courte**. L'utilisateur est développeur PHP confirmé, à l'aise en ligne de commande/Linux, mais **pas Python, pas agentique, pas LLM à la base** : ce sont les compétences que la formation (et ce projet) doivent démontrer.

Conséquence directe sur la façon de travailler : **comprendre chaque ligne générée n'est pas optionnel**. Ce n'est pas un projet perso où "ça marche" suffit — c'est un projet où l'utilisateur doit pouvoir expliquer et défendre chaque choix devant un jury. D'où la validation à chaque étape et la pédagogie ciblée ci-dessous : elles découlent directement de cet enjeu, pas d'une préférence de confort.

**Périmètre de couverture** : l'objectif est que QualiCheck couvre l'intégralité des 3 blocs de compétences (C1-C21). À ce stade (2/3 de la formation restant), la visibilité est encore incomplète sur certains blocs — si une compétence s'avère trop artificielle à rattacher à QualiCheck, un brief distinct et ponctuel pourra être traité séparément pour cette compétence précise, plutôt que de forcer un rattachement mal justifié.

## Changelog

L'utilisateur alterne entre plusieurs outils agentiques (Claude Code, OpenCode...) qui ne partagent pas de mémoire entre eux. Un fichier `CHANGELOG.md` à la racine du projet est donc la seule continuité fiable : **chaque réalisation (fichier créé, migration appliquée, script modifié...) doit y être déclarée**, quel que soit l'outil utilisé.

Format d'entrée, une ligne par réalisation :

```
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

**Règle : le CHANGELOG est mis à jour à chaque commit**, pas en fin de session. Chaque commit doit être précédé d'une mise à jour du CHANGELOG couvrant exactement ce qui est committé.

Avant de commencer une tâche d'implémentation, lire `CHANGELOG.md` pour savoir où en est le projet, en complément (pas en remplacement) des documents de `conception/`.

## Stack

- Backend : FastAPI (Python)
- Frontend : Vue.js
- BDD : PostgreSQL + pgvector (index HNSW, `vector(384)`)
- Migrations : Alembic
- Gestion de paquets/environnement : `uv`
- Linter : Ruff
- LLM (dev) : Kimi K2.6 (enrichissement ingestion), gpt-5.4 / gpt-5.4-mini (audit, question libre) via Azure
- Embedding : All MiniLM L12 v2 via Infomaniak (gratuit, 384 dim)
- Déploiement : Docker + docker-compose

## `.env`

Un seul fichier, à la racine, jamais versionné : connexion BDD + accès LLM (endpoint Azure, clés, noms de déploiements).

## Ordre d'exécution du projet

1. `scripts/migration.py` — crée le schéma BDD complet (vide). Voir `conception/1_BDD/bdd.md`.
2. `scripts/ingestion.py` — peuple le référentiel Opquast (245 règles). Voir `conception/2_ingestion/ingestion.md`.
3. Reste de l'application (audits, dialogue, question libre) — non conçu à ce stade.

## Structure du repo

```
conception/          # documents de conception, non exécutés — source de vérité fonctionnelle
  conception.md       # dossier de conception complet (US0/US1/US2, flux, MCD, choix techniques...) — document central
  1_BDD/bdd.md
  2_ingestion/ingestion.md
  MLD_qualicheck.md
  A_dictionnaire_donnees_qualicheck.xlsx
  B_MCD_qualicheck.drawio
  referentiel_competences.md   # référentiel de certification (C1-C21) — à consulter au moment de rédiger un livrable
  certif_deroule.md             # déroulé, épreuves (E1-E5), critères pratiques de la certification
scripts/             # points d'entrée uniquement, à plat — voir scripts/CLAUDE.md
  migration.py
  ingestion.py
app/                  # domaine métier + modules de support — voir app/CLAUDE.md
  models/
  migration/
  ingestion/
logs/                # logs d'exécution des scripts (une ligne par règle × étape pour l'ingestion) — distinct du CHANGELOG.md
docker-compose.yml
.env
CHANGELOG.md         # historique des réalisations (implémentation), mis à jour par tout outil agentique utilisé
```

## Méthodologie : spec-driven, par incrément

Chaque brique du projet suit un cycle **spec → validation → implémentation**, jamais l'inverse : pas de code écrit sans document de conception validé au préalable dans `conception/` pour le périmètre concerné. Chaque document de conception (`bdd.md`, `ingestion.md`, les suivants à venir) est une spec complète pour *sa* brique, pas pour l'application entière — la vision globale se précise brique par brique, pas d'un coup.

Le risque à surveiller : le **spec drift** (le code qui s'éloigne de la spec au fil des sessions, en particulier en alternant Claude Code et OpenCode). D'où l'importance de toujours relire la spec correspondante avant de modifier du code existant, et de tenir `CHANGELOG.md` à jour — c'est ce qui maintient le lien entre "ce qui a été décidé" et "ce qui existe réellement".

## Mode de travail sur ce projet

*(découle directement du contexte de certification ci-dessus)*

- **Validation à chaque étape** : contrairement au défaut plus autonome de `~/.claude/CLAUDE.md`, sur QualiCheck on s'arrête et on fait valider chaque étape avant de continuer — même quand ce n'est pas strictement bloquant. Priorité sur le défaut général pour ce projet.
- **Pédagogie ciblée** : expliciter le raisonnement sur les outils/concepts découverts via ce projet (Alembic, pgvector/HNSW, RAG, `uv`, agents LLM...) — pas seulement sur ce qui relève de PHP/ligne de commande, déjà maîtrisés.

## Principes généraux (tout le projet)

- **Retry LLM** : 3 tentatives avec backoff croissant sur tout appel LLM, avant de considérer l'appel en échec définitif.

## Documents de référence à consulter avant toute implémentation

- `conception/conception.md` — document central : US0/US1/US2, flux fonctionnels, MCD, choix techniques, personas, RGPD, budget
- `conception/1_BDD/bdd.md` — création et gestion du schéma (Alembic, pgvector, HNSW)
- `conception/2_ingestion/ingestion.md` — pipeline d'ingestion en détail (7 étapes)
- `conception/MLD_qualicheck.md` — modèle logique de données, source de vérité pour les champs/contraintes
- `conception/A_dictionnaire_donnees_qualicheck.xlsx` — dictionnaire de données détaillé

## Documents de référence pour la certification (à consulter au moment de rédiger un livrable, pas pour le code courant)

- `conception/referentiel_competences.md` — référentiel détaillé C1-C21 : ce que chaque compétence exige concrètement (versionnement Git, documentation accessible, tests, etc.)
- `conception/certif_deroule.md` — déroulé de la certification, épreuves E1-E5, critères pratiques (nombre de pages, timing...)
