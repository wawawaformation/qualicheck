# Dossier jury

Méta-documentation du projet QualiCheck pour la certification RNCP37827.

## Ce que contient ce dossier

| Dossier | Contenu |
| --- | --- |
| `veille/` | journal de veille technique et réglementaire, et sources suivies (C6) |
| `decisions/` | décisions structurantes : ce qui a été envisagé, ce qui a été écarté, et pourquoi |
| `documents_jury/` | livrets finaux à remettre (E1 à E5) — seul sous-dossier qui synthétise plutôt que de pointer vers les preuves, voir son propre `README.md` |

## Ce que ce dossier n'est pas

**Ce n'est pas une vitrine.** Un document rédigé pour impressionner se repère
immédiatement — un jury évalue une capacité à raisonner, pas une capacité à se
présenter.

Deux règles en découlent :

1. **On pointe vers les preuves, on ne les recopie pas.** L'index ci-dessous
   renvoie vers le code et les specs. Dès qu'un document d'ici résume ce qui existe
   ailleurs, il commence à diverger de la réalité et devient un piège.
2. **On n'écrit ici que ce qui n'a aucun autre domicile.** Les specs enregistrent
   ce qui a été décidé, le `CHANGELOG.md` ce qui a été réalisé,
   `docs/problemes_rencontres/` les problèmes rencontrés. Ce dossier ne prend en
   charge que le reste : le raisonnement écarté et la veille.

Les meilleures preuves sont des sous-produits du travail réel, pas des documents
écrits après coup. `docs/problemes_rencontres/ingestion/1_prompt_engineering.md`
en est l'exemple : il documente une compréhension qui évolue, avec les chiffres qui
ont motivé chaque changement, et il n'a pas été écrit pour être lu par un jury.

## Index compétences → preuves

État au 2026-07-21. À compléter au fil du projet — l'objectif n'est pas de tout
remplir vite, mais de ne pas avoir à reconstituer ces liens à la fin.

Légende : ✅ couvert · 🟡 partiel · ⬜ rien à ce stade

### Bloc 1 — Collecte, stockage, mise à disposition

| | Compétence | Preuves | État |
| --- | --- | --- | --- |
| C1 | Automatiser l'extraction de données | `app/ingestion/acquisition.py` (API REST Opquast + scraping), `conception/2_us0/ingestion/D_chantier1_scraping_contexte.md` | 🟡 API + scraping faits ; le critère demande aussi fichier de données, BDD et big data |
| C2 | Requêtes SQL d'extraction | `app/ingestion/stockage.py::load_enriched_rules_from_db()` (hook `--resume`) | 🟡 requêtes SQL réelles avec jointures (`objectif_regle`, `phase_regle`, `regle_tag`) déjà fonctionnelles ; documentation des choix de sélection/jointures/optimisations à rédiger. Renforcé plus tard par les requêtes SQL directes de C5/US1 ("SQL déterministe", `conception.md`) |
| C3 | Règles d'agrégation | `app/ingestion/aggregation.py`, `conception/2_us0/ingestion/ingestion.md` | 🟡 agrégation et validation faites ; documentation des choix de nettoyage à formaliser |
| C4 | Créer une base de données | `conception/1_BDD/bdd.md`, `conception/1_BDD/MLD_qualicheck.md`, `conception/annexes/B_MCD_qualicheck.drawio`, `app/migration/versions/`, `docs/rgpd/registre_traitements.md` | ✅ Merise et schéma faits ; registre RGPD et procédures de tri résolus le 2026-07-29 |
| C5 | API de mise à disposition | — | ⬜ non conçu |

### Bloc 2 — Intégrer modèles et services d'IA

| | Compétence | Preuves | État |
| --- | --- | --- | --- |
| C6 | Veille technique et réglementaire | Dépôt séparé `/projets/veille` | 🟡 veille collective réellement menée (thème assigné, restitution toutes les 2-3 semaines, volet réglementaire couvert) ; manquent la cadence datée, la fiabilité des sources et les outils d'agrégation |
| C7 | Identifier des services d'IA préexistants | `F_choix_llm.md` (récupéré) + source des « 16 820 appels » : projet externe `formation_dev_ia_agentique/lab/benchmark-azure/` (dépôt git séparé, spec-driven : specs + plans + `FOUNDRY_NOTES.md`/`FOUNDRY_SI_NOTES.md`) | 🟡 benchmark réel et documenté, mais hors dépôt QualiCheck — un jury lisant uniquement ce dépôt n'y a pas accès ; `annexes/benchmark/` n'en contient qu'un sous-ensemble (4 fichiers, liens de `F_choix_llm.md` non alignés) |
| C8 | Paramétrer un service d'IA | `app/ingestion/llm_client.py`, `.env.example` + monitorage réel (voir C11) | 🟡 service configuré et opérationnel ; « monitorage disponible opérationnel » désormais couvert par un projet externe, à documenter comme preuve |
| C9 | API exposant un modèle | — | ⬜ non conçu |
| C10 | Intégrer l'API dans une application | — | ⬜ non conçu |
| C11 | Monitorer un modèle | Projet externe `formation_dev_ia_agentique/lab/benchmark-azure/` — collecte cron (30 min), métriques (latence, disponibilité, taux d'erreur par modèle/région), rapport HTML avec graphiques (`analysis_report.html`) | 🟡 candidat fort, **hors QualiCheck** — cron 30 min, taux d'erreur/timeout/HTTP par modèle, restitution HTML en temps réel : couvre C11 mieux que rien dans QualiCheck ne pourrait (l'ingestion est un batch anecdotique, pas un flux à surveiller). Cohérent avec `CLAUDE.md` : « si une compétence s'avère trop artificielle à rattacher à QualiCheck, un brief distinct pourra être traité séparément » — reste à choisir : documenter QualiCheck y renvoyant, ou dossier de certification autonome pour ce projet |
| C12 | Tests automatisés | `tests/`, `.github/workflows/ci.yml` | 🟡 tests unitaires et d'intégration en place ; validation des jeux de données à formaliser |
| C13 | Chaîne de livraison continue | `.github/workflows/ci.yml` | 🟡 intégration continue en place ; livraison à construire |

### Bloc 3 — Réaliser l'application

| | Compétence | Preuves | État |
| --- | --- | --- | --- |
| C14 | Analyser le besoin | `conception/conception.md` (US0/US1/US2, personas, MCD) | 🟡 user stories et modélisation faites ; critères d'acceptation et objectifs d'accessibilité à expliciter |
| C15 | Concevoir le cadre technique | `conception/conception.md`, `docker-compose.yml`, `conception/2_us0/ingestion/C_pipeline_ingestion.drawio` | 🟡 |
| C16 | Coordonner la réalisation | `CHANGELOG.md`, `TODO_PIPELINE_INGESTION.md`, `docs/superpowers/plans/` | 🟡 méthode incrémentale documentée ; outils de pilotage agile à formaliser |
| C17 | Développer composants et interfaces | — | ⬜ backend et frontend non démarrés |
| C18 | Automatiser les tests | `.github/workflows/ci.yml` | ✅ lint, migrations et tests déclenchés à chaque push hors `main` |
| C19 | Livraison continue de l'application | — | ⬜ |
| C20 | Surveiller l'application | — | ⬜ relève d'US1 |
| C21 | Résoudre les incidents | `docs/problemes_rencontres/` + incident d'authentification (HTTP 401, 10/07 17h31) identifié et documenté dans le projet externe `benchmark-azure/` | 🟡 trois incidents QualiCheck documentés (cause, reproduction, solution versionnée) ; l'incident du benchmark externe est factuellement constaté mais sa procédure de résolution n'est pas encore rédigée en suivant les critères C21 |

### Lecture de cet état

Le bloc 1 est le plus avancé, ce qui est cohérent : l'ingestion en est le cœur. Les
blocs 2 et 3 dépendent largement d'US1 et US2, non encore conçus.

Deux manques ne se rattraperont pas tout seuls :

- **C6** — le fonds existe et le dispositif collectif est en place. Ce qui manque est
  la **trace datée** de la cadence : le référentiel demande un minimum d'1h/semaine,
  et des dossiers thématiques prouvent un travail, pas une régularité. C'est le seul
  élément qui ne se reconstitue pas après coup.
- **C4** — le registre des traitements de données personnelles et les procédures de
  tri RGPD sont des livrables à part entière, pas une section de spec.

**Un point structurant découvert le 2026-07-22** : le projet externe
`formation_dev_ia_agentique/lab/benchmark-azure/` (dépôt git séparé, monitorage
réel des déploiements Azure LLM, spec-driven) couvre C11 nettement mieux que
QualiCheck ne pourrait le faire seul — l'ingestion y est un batch lancé 2-3 fois,
sans rien à surveiller en continu (cf. `jury/decisions/2026-07-21-perimetre-mlops-ingestion.md`,
qui avait explicitement renvoyé C11 vers US1). Ce projet en est une preuve plus
directe que ne le sera jamais US1. Reste à décider : le documenter comme preuve
externe de QualiCheck (renvoi, comme pour la veille), ou en faire un dossier de
certification autonome — cf. `TODO.md`.
