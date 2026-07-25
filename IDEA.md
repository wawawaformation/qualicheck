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
