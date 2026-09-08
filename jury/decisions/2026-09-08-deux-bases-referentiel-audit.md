# Deux bases de données : référentiel Opquast et données d'audit

2026-09-08 · retenu — **révise `2026-07-28-separation-api-regles-api-audit.md`**

## Contexte

La décision du 2026-07-28 avait fixé l'architecture en trois étages
(`api_regles` / `api_audit` / `api_business`) sur **une seule base de
données**, en écartant explicitement l'option « deux API, deux bases
séparées ». Le motif du refus était précis :

> `app/models/metier.py` contient déjà de vraies contraintes FK vers
> `regle.id` (`AuditRegle.regle_id`, `Constat.regle_id`), migrées et actives.
> Une contrainte FK Postgres ne traverse pas deux bases de données
> distinctes — séparer les bases impose de les abandonner et de les remplacer
> par une vérification applicative, moins fiable. Contraire au critère C4.

Le sujet revient parce que la conception d'US2 met en évidence une gêne
concrète : brancher le retrieval vectoriel sur une base qui contient aussi
les tables d'audit. La question reposée ici : le motif du refus tient-il
encore ?

**Deux constats mesurés le 2026-09-08 disent que non.**

1. Les six tables métier sont **vides** : 0 audit, 0 page, 0 audit_page,
   0 audit_regle, 0 constat, 0 utilisateur. Les contraintes FK sont bien
   « migrées et actives », mais sur des tables sans une seule ligne.
2. **Deux FK seulement** traversent la frontière : `audit_regle.regle_id` et
   `constat.regle_id`.

Le projet a déjà appliqué ce raisonnement à la migration 0011 (élargissement
de `regle.embedding`) : *« la colonne était `NULL` partout, c'est le moment
le moins coûteux possible »*. La même logique vaut ici, et la fenêtre se
refermera au premier audit réel — la scission deviendrait alors une migration
de données.

## Ce qui rend la décision défendable, et non seulement « plus élégante »

L'intuition de départ était esthétique (« plus naturel »). Quatre critères
observables la soutiennent — c'est sur eux que la décision repose.

**1. Une frontière contrainte plutôt que promise.** Avec une seule base,
« `api_audit` ne lit pas `regle` directement » est une convention, qui tient
tant que personne ne l'oublie en revue. Avec deux bases, la chaîne de
connexion rend la lecture impossible : aucune FK, aucune jointure sans
extension (`dblink`/`postgres_fdw`, non utilisées). Ce projet a déjà la preuve
que les conventions cèdent : `POSTGRES_TEST_DB` en était une, et le
2026-07-25 un test d'intégration a effacé les 245 règles réelles.

**2. La granularité de sauvegarde correspond enfin au domaine.** Aujourd'hui
`make export_sql` fait un `pg_dump --data-only` de **toute** la base. Donc
« sauvegarder le référentiel » sauvegarde tout, et restaurer le référentiel
depuis un dump ancien réinjecterait les données d'audit de la même époque —
`import_sql` ne vidant rien avant restauration, en doublon ou en conflit. Le
référentiel a besoin de snapshots fréquents (il est reconstruit par
ingestion, et coûte de l'argent à régénérer) ; les données d'audit ne doivent
jamais être ramenées en arrière par une restauration du référentiel.

**3. Le périmètre RGPD devient une réponse bornée.** Le registre des
traitements (`docs/rgpd/registre_traitements.md`) doit dire où vivent les
données personnelles. La réponse devient une chaîne de connexion au lieu
d'une liste de tables à tenir à jour, et une purge devient une opération à
périmètre fermé.

**4. Deux régimes de licence cessent de cohabiter dans le même magasin.** Le
référentiel est sous CC BY-SA 4.0 — c'est ce qui a justifié la lecture
ouverte de l'API (`2026-07-26-lecture-ouverte-api-regles.md`). Les données
d'audit appartiennent à l'auditeur. « Qu'est-ce qui est exportable » devient
une réponse par base.

## La FK perdue est en réalité une correction de modélisation

Le côté métier ne doit pas référencer `regle.id` : c'est une clé de
substitution privée au schéma d'un autre service. Il référencera le
**`numero` Opquast** — clé métier stable, publique et signifiante.

Tout le système parle déjà `numero` à ses frontières : `GET /regles/{numero}`
dans l'API, `numero_regle_attendue` dans le jeu d'acceptance RAG,
`query_top_n_numeros()` dans le code de recherche. Référencer une clé métier
stable par-dessus une frontière de service est le motif correct ; référencer
l'auto-incrément privé d'un autre service était le raccourci. L'objection C4
n'est donc pas encaissée, elle est retournée.

## Options envisagées

**Statu quo (une base, lecture directe de `regle` par `api_audit`)** — pour :
zéro travail, FK conservées, décision déjà prise et documentée. Contre : ne
satisfait aucun des quatre critères ci-dessus ; laisse la frontière à l'état
de convention et la sauvegarde à une granularité qui ne correspond à aucun
domaine.

**Deux schémas PostgreSQL dans une seule base (`referentiel.` / `audit.`)** —
pour : les FK fonctionnent entre schémas, donc l'intégrité est conservée ; la
séparation est exprimée ; coût quasi nul (une chaîne Alembic, un backup).
Contre : échoue précisément sur les deux critères les plus forts — la
frontière reste une convention (rien n'empêche `api_audit` de lire
`referentiel.regle`), et la granularité de sauvegarde ne bouge pas.

**Deux bases dans la même instance PostgreSQL (retenu)** — pour : satisfait
les quatre critères ; les 245 règles et leurs vecteurs ne bougent pas (la
base existante devient le référentiel, la base d'audit est créée à côté,
vide) ; un seul conteneur, un seul volume, un seul jeu de secrets à faire
évoluer. Contre : deux chaînes Alembic à maintenir, deux bases déclaratives
SQLAlchemy, `tests/migration/` à scinder, et deux nouveaux modes de
défaillance (ci-dessous).

**Deux instances PostgreSQL (deux conteneurs)** — pour : isolation
opérationnelle complète (versions, ressources, arrêt/redémarrage
indépendants), `pgvector` seulement là où il sert. Contre : un second service
dans `docker-compose` **et dans le CD**, deux volumes, deux jeux de secrets,
pour une isolation supplémentaire qui n'achète rien de mesurable à 245 règles
et un auditeur. Écarté comme non proportionné — mais c'est l'évolution
naturelle si le besoin apparaît, et la scission logique décidée ici la rend
peu coûteuse.

## Décision

**Deux bases de données dans la même instance PostgreSQL** :

- **`qualicheck`** (l'existante) devient la base du **référentiel** :
  `theme`, `regle`, `objectif`, `phase`, `tag`, leurs tables de jointure,
  `etat_donnees`, ainsi que l'extension `pgvector` et l'index HNSW.
- **`qualicheck_audit`** (nouvelle, vide) accueille le **métier** :
  `audit`, `page`, `audit_page`, `audit_regle`, `constat`, `utilisateur`.
- Les deux FK traversantes disparaissent ; `audit_regle` et `constat`
  référencent `regle_numero` (INT), ce qui décale aussi leurs clés primaires.
- `api_audit` et `api_business` n'accèdent au référentiel **qu'en HTTP** via
  `api_regles`. La lecture directe en base, prévue par la décision du
  2026-07-28, est abandonnée.

Critère qui a tranché : la scission est le seul moyen de faire d'une règle
d'architecture une **contrainte** plutôt qu'une promesse — et le projet a
déjà payé une fois pour avoir fait confiance à une convention. Le moment est
choisi parce que les tables concernées sont vides : c'est aujourd'hui gratuit,
ce sera une migration de données après le premier audit.

## Trace du schéma avant scission

Relevé sur la base réelle le 2026-09-08, **avant toute implémentation**.
Conservé ici parce que la migration `0013` fera disparaître ces six tables
de la base du référentiel : après elle, reconstituer l'état d'avant
demanderait de relire l'historique des migrations. Cette trace rend l'écart
lisible directement.

Les deux tables effectivement modifiées par la décision :

```sql
CREATE TABLE audit_regle (
    audit_id integer NOT NULL,
    regle_id integer NOT NULL
);

CREATE TABLE constat (
    audit_id integer NOT NULL,
    page_id integer NOT NULL,
    regle_id integer NOT NULL,
    statut character varying(32) NOT NULL,
    commentaire character varying(512),
    recommandation character varying(512),
    preuve character varying(512),
    validation_humaine boolean,
    feedback_auditeur text
);
```

Inventaire complet des contraintes du domaine métier. Les deux dernières
sont celles qui traversent la frontière et disparaissent :

```sql
-- Clés primaires
audit_pkey        PRIMARY KEY (id)
page_pkey         PRIMARY KEY (id)
utilisateur_pkey  PRIMARY KEY (id)
audit_page_pkey   PRIMARY KEY (audit_id, page_id)
audit_regle_pkey  PRIMARY KEY (audit_id, regle_id)
constat_pkey      PRIMARY KEY (audit_id, page_id, regle_id)

-- Clés étrangères internes au domaine (conservées telles quelles)
audit_utilisateur_id_fkey   FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id)
audit_page_audit_id_fkey    FOREIGN KEY (audit_id)       REFERENCES audit(id)
audit_page_page_id_fkey     FOREIGN KEY (page_id)        REFERENCES page(id)
audit_regle_audit_id_fkey   FOREIGN KEY (audit_id)       REFERENCES audit(id)
constat_audit_id_fkey       FOREIGN KEY (audit_id)       REFERENCES audit(id)
constat_page_id_fkey        FOREIGN KEY (page_id)        REFERENCES page(id)

-- Clés étrangères traversant la frontière (abandonnées par cette décision)
audit_regle_regle_id_fkey   FOREIGN KEY (regle_id)       REFERENCES regle(id)
constat_regle_id_fkey       FOREIGN KEY (regle_id)       REFERENCES regle(id)
```

Ce que la décision change, et rien d'autre :

| | Avant | Après |
| --- | --- | --- |
| Colonne de liaison | `regle_id INT` (FK vers `regle.id`) | `regle_numero INT` (aucune FK) |
| PK `audit_regle` | `(audit_id, regle_id)` | `(audit_id, regle_numero)` |
| PK `constat` | `(audit_id, page_id, regle_id)` | `(audit_id, page_id, regle_numero)` |
| Base d'accueil | `qualicheck`, avec le référentiel | `qualicheck_audit` |

Les quatre autres tables (`audit`, `page`, `audit_page`, `utilisateur`)
changent de base sans changer de forme.

Deux chemins permettront de retrouver cet état si nécessaire : le
`downgrade()` de la migration `0013`, qui recrée les six tables sous leur
forme d'origine — FK comprises — et cette trace.

## Conséquences

- **L'API couvre déjà le besoin de lecture du métier.** `GET /regles` renvoie
  les 245 règles en un seul appel (~500 kB), sans pagination — choix déjà
  acté, le corpus Opquast étant figé — avec les filtres `outil` et
  `review_status`, et `GET /regles/{numero}` pour une règle précise. Aucun
  filtre supplémentaire par numéros n'est donc nécessaire : `api_audit`
  charge le référentiel en un appel. Contrat exposé publiquement sur
  `https://regles.qualicheck.koabana.fr/docs`.
- **Seul `GET /dense` manque, et il est désigné sans être construit.** La
  recherche vectorielle est la seule capacité que l'API n'expose pas, alors
  qu'`api_business` ne peut plus l'obtenir en base. La forme prévue reçoit un
  vecteur **déjà calculé** (`{"vecteur": [...], "top_n": 3}`), pour
  qu'`api_regles` reste sans aucun appel LLM conformément à sa contrainte
  d'origine. Construite **avec son consommateur** (US2), pas avant : du code
  sans appelant est précisément ce que le projet s'interdit.
- **Deux nouveaux modes de défaillance, assumés.** `api_regles` devient une
  dépendance de **disponibilité** pour un audit en cours (plus d'affichage de
  règles si elle est en panne). Et l'intégrité des deux liens passe du SGBD à
  une validation à la frontière API — un `regle_numero` inexistant n'est plus
  refusé par Postgres.
- **`make export_sql` / `import_sql` deviennent explicitement référentiel.**
  Les laisser à l'échelle de « toute la base » viderait de son sens le
  critère 2 qui motive cette décision.
- **`app/models/` garde son rôle de source de vérité unique du schéma**, mais
  avec deux bases déclaratives distinctes — sinon les `autogenerate` des deux
  chaînes Alembic se mélangeraient.
- **`tests/migration/` doit être scindé** : il asserte aujourd'hui les tables
  métier (PK composite de `constat`, index `ix_constat_audit_id` et
  `ix_audit_regle_audit_id`, colonnes NOT NULL d'`audit`) contre
  `POSTGRES_DB`, qui ne les contiendra plus.
- **`api_audit` reste à concevoir avec la spec US1.** Cette décision fixe où
  vivent ses tables et comment il atteint le référentiel, pas son contenu.
  La question ouverte de la frontière CRUD (`api_audit`) vs orchestration
  (`api_business`) reste entière.
- **Le nom `qualicheck` pour la base du référentiel devient asymétrique.** Le
  renommer en `qualicheck_referentiel` toucherait `.env`,
  `docker-compose.yml`, les secrets Actions de Gitea et le déploiement
  staging pour un bénéfice cosmétique — non fait, signalé comme dette
  assumée.
- **Deux bases de test**, une par domaine, en conservant la règle existante :
  aucun test destructeur ne cible une base de développement.
