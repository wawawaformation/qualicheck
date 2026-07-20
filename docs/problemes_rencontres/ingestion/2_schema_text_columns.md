---
title: "Dimensionnement des colonnes textuelles — VARCHAR vs TEXT"
subtitle: "Étape 4 (Stockage) — calibrage du schéma BDD en fonction des données réelles"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

L'ingestion des 245 règles Opquast a révélé un problème de dimensionnement du schéma : plusieurs colonnes définies en `VARCHAR(N)` se sont avérées trop courtes pour les données acquises (via API + scraping du site Opquast). Ce document trace l'identification du problème, la solution appliquée, et la stratégie de recalibrage final basée sur les données réelles.

Fichiers concernés : `app/models/referentiel.py`, `app/migration/versions/`.

## Problème initial — Hypothèses incorrectes

**Hypothèse de départ** : les colonnes textuelles des règles Opquast étaient dimensionnées selon une estimation "raisonnable" :
- `intitule` : `VARCHAR(512)`
- `solution` : `VARCHAR(512)`
- `controle` : `VARCHAR(512)`
- `objectif` : `VARCHAR(256)`

## Observation 1 — Première erreur en ingestion réelle

**Contexte** : première tentative complète d'ingestion des 245 règles (acquisition + agrégation + enrichissement LLM + stockage).

**Erreur** — Étape 4 (Stockage), règle 154 :
```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(256)
[...objectif: "Éviter à des utilisateurs d'aides techniques d'être désorientés par l'ouverture d'une nouvelle fenêtre qui ne sera pas toujours aisément perceptible..."]
```

**Cause** : les `objectifs` Opquast proviennent directement de l'API (pas enrichis par LLM) et peuvent dépasser 256 caractères. L'objectif en question fait ~280 caractères.

## Correction 1 — Migration 0002

**Action** : agrandir `objectif` de `VARCHAR(256)` à `VARCHAR(512)`.

**Résultat** : l'ingestion relancée progresse jusqu'à la règle 166 avant de s'arrêter à nouveau.

## Observation 2 — Deuxième erreur, chaîne plus longue

**Erreur** — Étape 4 (Stockage), règle 166 :
```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(512)
[...solution: "Recourir à des gestionnaires d'événements universels en cas d'interaction basée sur Javascript [...]"]
```

**Cause identifiée** : les champs `solution` et `controle` ne viennent **pas** de l'API brute, mais du scraping du site Opquast (`app/ingestion/acquisition.py`, lignes 74-121). Le scraping extrait le premier `<p>` après les headings "solution" et "contrôle", ce qui produit du contenu HTML rendu — souvent beaucoup plus long que les données API seules.

Exemple : la règle 166 a une `solution` qui dépasse 512 caractères.

## Décision — Convertir en TEXT

Plutôt que de relancer l'ingestion à l'aveugle et de découvrir d'autres dépassements (coûteux en tokens LLM et en euros), **trois migrations créées** :

- **Migration 0002** : `objectif` : `VARCHAR(256)` → `VARCHAR(512)` (correction immédiate)
- **Migration 0003** : `intitule`, `solution`, `controle` : `VARCHAR(512)` → `TEXT` (données de scraping imprévisibles)
- **Migration 0004** : `objectif` : `VARCHAR(512)` → `TEXT` (cohérence et sécurité)

**Justification** : le scraping extrait du contenu HTML brut qui n'a pas de limite connue a priori. `TEXT` en PostgreSQL n'a pas de limite pratique (~1 Go par valeur), donc c'est la seule approche vraiment robuste pour les données acquises. Les colonnes LLM-enrichies (`guide_analyse`, `strategie_justification`) étaient déjà en `TEXT`.

## Stratégie de recalibrage futur — Script de test sans LLM

**Problème** : relancer une ingestion complète avec enrichissement LLM coûte cher (245 règles × appel Kimi K2.6 = tokens et €). On ne peut pas se permettre plusieurs essais pour tester le schéma.

**Solution** : créer un **script d'ingestion parallèle avec bouchons LLM** (`scripts/test_storage.py`) qui :
1. Réutilise les étapes 1-3 (acquisition + agrégation = données réelles Opquast, pas de LLM)
2. Remplace l'étape 3 (enrichissement LLM) par un remplissage générique (ex. `strategie_analyse = "test"`, `guide_analyse = "Lorem ipsum..."`)
3. Complète le stockage des 245 règles dans la BDD **gratuitement**

Une fois la BDD peuplée :
```sql
SELECT column_name, MAX(LENGTH(column_value)) as max_length
FROM regle
GROUP BY column_name;
```

On peut alors :
- **Identifier les colonnes vraiment longues** (doivent rester `TEXT`)
- **Réduire celles qui sont courtes** (ex. `strategie_analyse = 'playwright'` est toujours < 15 chars → `VARCHAR(20)` suffit)
- **Optimiser le schéma final** en connaissance de cause, pas par conjecture

## Validation du schéma — Test de stockage

**Avant le full-ingestion**, un test isolé (`scripts/test_storage.py`) vérifie que `TEXT` fonctionne :

```
✓ Test insertion réussi
  Règle 999 créée
  Intitule: 750 chars (simulé scraping long)
  Solution: 1326 chars (3× contenu scraping)
  Controle: 1142 chars (2× contenu scraping)
  Objectif: 281 chars (données API réelles)
```

**Conclusion** : le schéma en `TEXT` pour les colonnes textuelles longues supporte sans problème les données de scraping existantes.

## Mesure des données réelles — Ingestion de test complète

**Contexte** : après avoir peuplé la BDD avec les 245 règles via un script de test (bouchons LLM pour l'enrichissement, données réelles pour acquisition + agrégation), on a pu mesurer les vraies longueurs.

**Résultats observés** :

```text
Colonne                           MAX    MIN    AVG
──────────────────────────────────────────────────
controle (scraping)               573     14    113
solution (scraping)               569     24    143
objectif (API)                    359     21     85
intitule (API)                    167     35     77
strategie_justification (LLM stub) 67     67     67
guide_analyse (LLM stub)           56     56     56
```

**Analyse** :

1. **Colonnes de scraping** (`solution`, `controle`) — données imprévisibles du contenu HTML extrait :
   - MAX 569-573 chars
   - Recommandation : `VARCHAR(1024)` pour absorber les variations futures (2× marge)

2. **Colonnes d'API** (`intitule`, `objectif`) — données structurées Opquast :
   - MAX 167 chars (intitule), 359 chars (objectif)
   - Recommandation : `VARCHAR(255)` pour intitule, `VARCHAR(512)` pour objectif (marge conservatrice)

3. **Colonnes d'enrichissement LLM** (`guide_analyse`, `strategie_justification`) — **actuellement bouchons** :
   - Les vraies données LLM peuvent être **beaucoup plus longues** que 67 chars
   - Recommandation : rester en `TEXT` (imprévisible, source de variation à chaque prompt)

## Décision — Recalibrage final

Après analyse, **trois approches possibles** :

### Approche 1 : Conservative (VARCHAR limités)

```sql
intitule: VARCHAR(255)  # MAX 167
objectif: VARCHAR(512)  # MAX 359
solution: VARCHAR(1024) # MAX 569
controle: VARCHAR(1024) # MAX 573
guide_analyse: TEXT     # LLM imprévisible
strategie_justification: TEXT # LLM imprévisible
```

**Avantage** : optimise le stockage, pénalité de perf minimale.
**Risque** : si les données réelles LLM dépassent les limites lors du vrai enrichissement, erreurs en production.

### Approche 2 : Pragmatique (TEXT partout)

```sql
Tout en TEXT
```

**Avantage** : zéro risque de troncature, flexibilité totale.
**Risque** : stockage non optimisé (mineur en pratique pour cette taille de données).

### Approche 3 : Hybride (choisi)

```sql
intitule: VARCHAR(255)  # MAX 167, API stable
objectif: VARCHAR(512)  # MAX 359, API stable
solution: VARCHAR(1024) # MAX 569, scraping stable
controle: VARCHAR(1024) # MAX 573, scraping stable
guide_analyse: TEXT     # LLM imprévisible
strategie_justification: TEXT # LLM imprévisible
```

**Raison du choix** : données métier Opquast (API + scraping) sont stables et mesurées. Seul l'enrichissement LLM reste variable — on le laisse libre, mais on limite les données acquises pour optimiser.

## Mise en œuvre — Migration 0005 et validation

**Actions appliquées** :

1. **Mise à jour des modèles** (`app/models/referentiel.py`) :
   - `Regle.intitule` : `Text` → `VARCHAR(255)`
   - `Regle.solution` : `Text` → `VARCHAR(1024)`
   - `Regle.controle` : `Text` → `VARCHAR(1024)`
   - `Regle.strategie_analyse` : `VARCHAR(20)` → `VARCHAR(32)`
   - `Regle.strategie_source` : `VARCHAR(20)` → `VARCHAR(32)`
   - `Objectif.objectif` : `Text` → `VARCHAR(512)`
   - Conservé en `Text` : `strategie_justification`, `guide_analyse` (enrichissement LLM)

2. **Migration Alembic 0005** : `final_schema_calibration.py` applique ces changements de type.

3. **Validation sur 245 règles** : nouvelle ingestion de test (bouchons LLM) confirme que les données réelles respectent les nouveaux limites :

```text
Colonne           MAX réel     Limite      Marge
──────────────────────────────────────────────────
controle               573       1024        451 ✓
solution               569       1024        455 ✓
objectif               359        512        153 ✓
intitule               167        255         88 ✓
```

**Résultat** : ✓ Stockage de 245 règles sans erreur avec le schéma calibré.

## Résumé du processus — De l'erreur à la donnée

**Ce qui a permis une solution robuste** :

1. **Hypothèse testée rapidement** — Première ingestion réelle a révélé les limites dès la règle 154
2. **Approche pragmatique** — Conversion temporaire en `TEXT` pour débloquer le scraping des 245 règles
3. **Mesure scientifique** — Script de test (bouchons LLM) peuple la BD gratuitement et révèle les vraies max
4. **Recalibrage basé sur des faits** — Redimensionnement avec marge déduite des observations
5. **Validation complète** — Migration appliquée et testée sur l'ensemble des 245 règles

**Coût total** : ~10€ en appels LLM (première tentative incomplète) + temps de débogage, zéro € pour la validation finale grâce aux bouchons.

## Principe retenu pour la suite

Tout dimensionnement de colonne doit être basé sur une **observation des données réelles**, pas sur une intuition de "ce qui devrait suffire" :

1. Utiliser d'abord `TEXT` pour les colonnes au source incertaine (scraping, enrichissement LLM)
2. Une fois les données réelles peuplées, mesurer les max réels
3. Recalibrer à la baisse les colonnes dont la limite réelle est bien inférieure à `TEXT`
4. Documenter ici la décision et les chiffres exacts qui l'ont motivée
