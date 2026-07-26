---
title: "Design — Jeu d'acceptance RAG (JSONL)"
subtitle: "Vérification automatisée du retrieval sémantique sur le référentiel des 245 règles Opquast"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Contexte

Suite à l'exécution réelle de `make embed-rules` (2026-07-26, 245/245 règles
vectorisées, `text-embedding-3-small`, 1536 dimensions, 0,0016 €), deux
vérifications manuelles au rapprochement cosinus (`SELECT ... ORDER BY
embedding <=> requête`) ont confirmé une recherche sémantique cohérente :

- « Peut-on souligner les titres ? » → règle 139 (« soulignement réservé aux
  liens ») en top 2
- « Il faut mettre en rouge les infos de danger » → règle 181 (« information
  non véhiculée uniquement par couleur ») en top 2

Ce chantier formalise ces vérifications ponctuelles en un jeu de test
d'acceptance rejouable, conformément à `TODO.md` (entrée « Jeu de règles
d'acceptance RAG (JSONL) »). Le choix du RAG sémantique malgré le petit
corpus (245 règles) est déjà acté et son rappel imparfait déjà assumé —
voir `docs/jury/decisions/2026-07-25-rag-us2-petit-corpus.md`.

Ce chantier ne construit que la brique de vérification du retrieval — pas
l'agent de dialogue US2 (question libre), non conçu à ce stade.

## Vue d'ensemble

```
tests/acceptance/rag_acceptance.jsonl (15-20 cas)
  {question, numero_regle_attendue}
        ↓
scripts/check_rag_acceptance.py
  Pour chaque cas :
    - embedding réel de la question (EmbeddingClient.embed_batch)
    - recherche pgvector : ORDER BY embedding <=> vecteur LIMIT top_n
    - succès si numero_regle_attendue dans les résultats
        ↓
  Taux de réussite global = cas réussis / total
  Comparé à taux_reussite_minimum (manifest.yml)
        ↓
  Code de sortie 0 (taux ≥ seuil) ou 1 (taux < seuil)
```

Suite manuelle, volontairement **hors CI** : chaque exécution déclenche un
appel réel à l'API Azure embeddings (coût réel, faible sur 15-20 questions),
lancée à la demande via `make rag-acceptance`.

## Modules

### `tests/acceptance/rag_acceptance.jsonl` (nouveau)

Une ligne JSON par cas :

```json
{"question": "Peut-on souligner les titres ?", "numero_regle_attendue": 139}
{"question": "Il faut mettre en rouge les infos de danger", "numero_regle_attendue": 181}
```

Les 2 cas déjà vérifiés manuellement sont repris tels quels. ~13-18 cas
supplémentaires sont ajoutés — voir « Constitution du jeu de cas » ci-dessous.

### `app/ingestion/manifest.yml`

Nouvelle section, au même niveau que `enrichissement`/`embedding` :

```yaml
rag_acceptance:
  top_n: 3
  taux_reussite_minimum: 0.8
```

- `top_n` : nombre de résultats pgvector considérés par cas (marge par
  rapport au top 2 observé manuellement).
- `taux_reussite_minimum` : proportion minimale de cas réussis pour que la
  suite soit globalement acceptable — le rappel imparfait du RAG est déjà
  assumé (jury 2026-07-25), on n'exige donc pas 100% de réussite par cas.

### `scripts/check_rag_acceptance.py` (nouveau)

Sur le modèle de `scripts/embed_rules.py` :

1. Charge `tests/acceptance/rag_acceptance.jsonl`.
2. Charge `top_n` et `taux_reussite_minimum` depuis `manifest.yml`
   (section `rag_acceptance`).
3. Pour chaque cas : calcule l'embedding réel de la question
   (`EmbeddingClient.embed_batch`), interroge la base (`ORDER BY embedding
   <=> :vecteur LIMIT top_n` sur la table `regle`), vérifie si
   `numero_regle_attendue` figure dans les résultats retournés.
4. Logge par cas : question, règle attendue, règles retournées, ✅/❌.
5. Calcule le taux de réussite global, le compare à `taux_reussite_minimum`.
6. Logge le coût total (tokens embeddings consommés), même format que les
   autres scripts (`embed_rules.py`, `enrich_again.py`).
7. Code de sortie : `0` si taux ≥ seuil, `1` sinon.

Pas de `--dry-run` : chaque run coûte un appel réel, assumé — volume
faible (15-20 questions ≈ quelques centaines de tokens).

### `Makefile`

Nouvelle cible, section « Ingestion et données réelles » :

```makefile
## Rejoue le jeu d'acceptance RAG (appel réel API embeddings, coût réel)
rag-acceptance:
	uv run python scripts/check_rag_acceptance.py
```

## Constitution du jeu de cas

- Les 2 cas déjà validés manuellement sont repris tels quels.
- ~13-18 nouveaux couples `{question, numero_regle_attendue}` sont
  proposés par l'assistant, en parcourant les 245 règles en base pour
  couvrir des thématiques variées (accessibilité, formulaires, sécurité,
  mentions légales...), puis soumis à validation de David avant intégration
  au JSONL.
- Chaque candidat proposé est vérifiable après coup par une exécution
  réelle du script (`make rag-acceptance`) : un candidat qui échoue de
  façon répétée peut être retiré ou reformulé plutôt que forcé dans le jeu.

## Tests / Validation

Point de contrôle formalisé en Gherkin (documentation de spec — pas de
`pytest-bdd`/fichier `.feature` réel, cf. « Scope et limites ») :

```gherkin
Fonctionnalité : Recherche sémantique RAG sur les règles Opquast

  Scénario : Une question retrouve la règle attendue (un cas du JSONL)
    Étant donné le référentiel des règles Opquast vectorisées (embeddings réels, text-embedding-3-small)
    Et la question « Peut-on souligner les titres ? »
    Et la règle numéro 139 attendue en réponse
    Quand je calcule l'embedding de la question
    Et que je recherche les règles les plus proches par similarité cosinus
    Alors la règle numéro 139 figure parmi les "top_n" premiers résultats (top_n déclaré dans le manifest)

  Scénario : Le jeu de cas est globalement acceptable malgré un rappel imparfait
    Étant donné un jeu de cas {question, règle attendue} (fichier JSONL)
    Quand chaque cas est rejoué indépendamment selon le scénario précédent
    Alors le taux de réussite global est supérieur ou égal au "taux_reussite_minimum" déclaré dans le manifest
```

Validation technique :

1. `scripts/check_rag_acceptance.py` : tests unitaires avec mock de
   `EmbeddingClient`/session BDD (pas d'appel réseau ni de BDD réelle dans
   `pytest tests/`) — vérifient le calcul du taux de réussite, la
   comparaison au seuil, le code de sortie.
2. `make rag-acceptance` : exécution réelle contre les 245 règles en base
   (action manuelle de David, hors périmètre de l'implémentation
   elle-même — même logique que `make embed-rules`).
3. `pytest`/`ruff` verts sur le reste de la suite.

## Gestion des erreurs

Pas de fail-fast à l'échelle du cas : un cas en échec n'interrompt pas les
suivants (on veut le taux de réussite global, pas juste le premier échec).
Une erreur technique (API embeddings en échec après retries, BDD
inaccessible) reste fatale pour tout le run (comportement des autres
scripts du pipeline).

## Scope et limites (Hors périmètre - YAGNI)

- **US2 (dialogue, question libre complète)** — ce chantier ne construit
  que la brique de vérification retrieval.
- **Intégration CI** — suite manuelle uniquement, pour ne pas engager un
  coût API réel à chaque push/PR.
- **Cache/enregistrement des embeddings de test** — appel réel à chaque
  run, assumé (coût minime sur 15-20 questions).
- **`pytest-bdd`/fichiers `.feature` réels** — aucun outillage BDD n'est
  installé dans le projet ; les scénarios Gherkin ci-dessus documentent la
  spec, ils ne sont pas exécutés par un framework dédié.
