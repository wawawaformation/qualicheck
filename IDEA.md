# IDEA.md — Idées en vrac

Idées non actées, capturées avant d'oublier — pas encore des tâches (voir
`TODO.md` pour ce qui est décidé) ni des décisions de conception (voir
`conception/` et `docs/jury/decisions/`). Format libre, à trier/formaliser
plus tard si l'idée tient.

## 2026-07-25

- **C5 (API du jeu de données) = couche de données pour US1/US2** — l'étape 1
  d'US1 (récupération des règles sélectionnées pour la création de constat)
  consommerait cette API plutôt que du SQL direct ad-hoc. Rattachement
  authentique (C5 exige explicitement un usage par "les autres composants du
  projet"), pas un livrable isolé. Une seule application FastAPI, routers
  séparés par domaine (`app/api/referentiel.py` pour C5, `app/api/audit.py`
  pour US1, `app/api/dialogue.py` pour US2) — pas de micro-services, sur-
  ingénierie pour ce projet. À concevoir en même temps ou juste après la spec
  d'US1, pas avant (US1 n'a pas encore de spec). Reste ouvert : l'API doit-elle
  aussi servir US2 (recherche sémantique) ?
  - **Ne pas confondre avec l'idée ci-dessous** (API de revue/curation) : ici
    US1/US2 partagent le même produit, même utilisateur (l'auditeur), même
    session — un seul FastAPI avec routers reste justifié. La frontière change
    pour un consommateur externe (voir idée suivante).

- **API de revue/curation du référentiel — micro-service à part, pas un
  router de plus** : `GET /regles` (filtrable par `review_status`) +
  `PATCH /regles/{numero}/review` (soumet `review_status`/`review_note`,
  `reviewed_at` posé côté serveur). Remplace le `psql` manuel utilisé
  aujourd'hui pour la revue post-V4/V5.
  - **Frontière API vs CLI, à ne pas mélanger** : l'API reste strictement
    lecture + annotation (`GET`/`PATCH review`), jamais un déclencheur d'appel
    LLM. Le futur `enrich_again` (réécriture ciblée des règles `a_revoir` via
    le LLM, lisant les `review_*` déposés par l'API) reste un script **CLI**,
    lancé par David avec le même garde-fou de confirmation explicite que
    `scripts/ingestion.py` — jamais exposé en HTTP à un tiers externe. Élie
    Sloïm alimente la donnée de revue ; le déclenchement de la réécriture
    (coûteux, LLM) reste un acte humain délibéré côté administrateur.
  - **Frontière de service justifiée, contrairement à US1/US2** : persona
    différent (curateur de données, pas auditeur), moment différent du cycle
    de vie (post-ingestion/QA, pas audit en direct), préoccupation différente
    (qualité du référentiel, pas flux d'audit). Sa propre entrée
    `docker-compose.yml`/`Dockerfile`, sa propre instance FastAPI, branchée sur
    le même Postgres (`app/models/referentiel.py` réutilisable tel quel).
  - **Consommateur réel et concret, pas hypothétique** : Élie Sloïm (fondateur
    Opquast, cf. `README.md` "réalisé avec le soutien d'Élie Sloïm") pourrait
    l'utiliser directement via un client REST (Bruno, Postman...) pour
    consulter et corriger les classifications — son expertise Opquast vaut
    bien plus qu'une revue développeur sur ces sujets.
  - **Conséquence technique notable** : l'authentification ne peut plus être
    "simulée" (raccourci MVP déjà noté dans le MLD pour US1/US2) — un vrai
    tiers externe l'utiliserait, donc l'auth doit être réelle dès cette API-là.
    Terrain d'entraînement plus honnête pour les critères OWASP/autorisation
    de C5 qu'un scénario purement interne.
  - **Va au-delà de C5 (Bloc 1)** : validation d'expert externe (matière pour
    argumenter la qualité du référentiel devant le jury, et pour nourrir un
    futur `enrich_again` avec des retours d'expert plutôt que des observations
    de développeur) + un vrai cas d'usage pour une authentification non
    simulée, utile bien au-delà de la seule compétence C5.
  - **Auth — pour l'instant, un token généré à la main** (pas de système de
    comptes/OAuth) : réel plutôt que simulé, mais proportionné au besoin — un
    seul utilisateur externe connu (Élie Sloïm), pas un public large. Cohérent
    avec YAGNI ; un vrai système d'authentification attendrait un besoin
    multi-utilisateurs réel (ex. plusieurs curateurs).

- **Version très future — enrichir le RAG avec l'écosystème Opquast au-delà
  des 245 règles** : glossaire Opquast, référentiel VPTCS, informations
  pratiques. Idée non creusée — périmètre, source d'acquisition, et impact sur
  le chunking/l'embedding restent à évaluer le moment venu.
  - **Motivation concrète (US2, question libre)** : une question sur la
    méthodologie elle-même (ex. « Opquast c'est que de l'accessibilité ? »)
    n'a probablement aucun bon match dans un corpus limité aux 245 chunks de
    règles — le RAG renverrait des règles vaguement liées par similarité de
    mots, sans jamais répondre à la vraie question. Sans contenu type
    glossaire/à-propos indexé, l'agent US2 hallucinerait ou avouerait ne pas
    savoir, cassant la promesse d'un RAG ancré dans les données Opquast.
  - **Point de conception à garder en tête** : mélanger des chunks de règles
    et des chunks de glossaire dans le même index pgvector demandera
    probablement une notion de **type de contenu** par chunk (règle vs
    glossaire vs info pratique), sinon impossible de savoir d'où vient une
    réponse pour la citer correctement à l'auditeur.

## 2026-07-26

- **`app/api_data/` pourrait un jour exposer un endpoint de recherche
  vectorielle "vecteur déjà calculé"** — reçoit `{"vecteur": [...], "top_n":
  3}` et se contente du `ORDER BY embedding <=> :vecteur LIMIT top_n`, sans
  jamais appeler de LLM. Respecterait la contrainte de l'API données (« aucun
  appel LLM, aucun recalcul d'embedding » —
  `docs/superpowers/plans/2026-07-26-api-data-implementation.md`), puisque
  c'est exactement le motif déjà écrit et validé dans
  `app/ingestion/rag_acceptance.py::query_top_n_numeros()`.
  - **Volontairement pas construit maintenant** : personne ne le consomme —
    US2 (question libre, RAG sémantique — décision actée
    `docs/jury/decisions/2026-07-25-rag-us2-petit-corpus.md`) n'est pas
    conçue, et c'est elle qui calculerait la question en vecteur (via un
    appel LLM d'embedding) avant d'appeler ce futur endpoint. `app/CLAUDE.md`
    interdit explicitement d'anticiper une structure avant sa conception —
    construire ce bout maintenant serait spéculatif, YAGNI l'écarte.
  - **Frontière à retrouver le jour où US2 est spécée** : soit
    `app/api_business/` embarque l'appel LLM d'embedding puis appelle cet
    endpoint sur `app/api_data/` (le vecteur transite en HTTP, jamais le
    calcul), soit `api_business` requête pgvector directement — à trancher
    avec les vrais détails d'US2, pas avant.

- **US1 (audit) passera aussi par `app/api_data/`** — pas une nouvelle
  couche CRUD dans un futur `app/api_business/`, mais de nouveaux routers
  dans `api_data` lui-même, sur les tables métier de
  `app/models/metier.py` (`Audit`, `Page`, `AuditPage`, `AuditRegle`,
  `Constat`) : endpoints assez classiques (créer un audit, lister/marquer
  des pages, lister/mettre à jour des constats). Cohérent avec l'écart déjà
  assumé pour l'écran de revue des enrichissements — `api_data` sert le CRUD
  sans logique métier partout où c'en est un, `api_business` reste réservé
  à l'orchestration (routing par `strategie_analyse`, dialogue, RAG US2).
  Piste de David, pas encore tranchée ("je pense") — à confirmer quand US1
  sera spécée, pas avant.
