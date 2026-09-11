# Mesure des variantes de chunk — Vague 1 (champs isolés) — design

2026-09-11

## Contexte

Le Temps 1 du chantier refus (`docs/superpowers/specs/2026-09-11-retrieval-refus-design.md`,
déjà exécuté) a fait remonter le score de similarité jusqu'au contrat
HTTP. Un test ad hoc pendant cette mesure a montré qu'un chunk réduit
(intitulé seul) donne des scores très différents du chunk complet actuel
sur les mêmes faux positifs (0.28-0.33 contre 0.53) — signal fort que le
choix du texte vectorisé (le « chunk ») a un impact direct sur la qualité
du retrieval, jamais mesuré systématiquement jusqu'ici.

Le retrieval est la matière première d'US2 (mots de David) : les chunks
doivent être fixés sur preuve, pas au doigt mouillé. Protocole de mesure
conçu en brainstorming le 2026-09-11 (conservé en mémoire assistant,
`protocole_mesure_retrieval.md`), dont cette spec couvre la **première
vague seulement**.

## Objectif de cette vague

Mesurer, pour chacun des 11 champs de la règle pris **isolément**, sa
capacité à retrouver la bonne règle — afin de savoir quel champ porte
quel signal, avant de composer des chunks combinés (vague 2, hors
périmètre de cette spec).

## Hors périmètre

- **Vague 2 (combinaisons de champs)** et **vague 3 (affinage)** : sujet
  d'un futur cycle spec → plan, une fois les résultats de la vague 1
  disponibles pour les motiver.
- **Décision finale sur le chunk à utiliser en production** : cette spec
  mesure, elle ne tranche pas. `build_chunk_text()` (production) n'est
  pas modifié par ce chantier.
- **Jeu de validation réservé** et **critère de décision écrit d'avance**
  (points 2 et 3 du protocole en mémoire) : nécessaires avant de
  **choisir** un chunk, pas avant de **mesurer** les champs isolés. À
  poser au moment de la vague où un choix sera réellement fait.
- **Late fusion** (moyenne de vecteurs de champs déjà vectorisés
  séparément) : piste distincte évoquée en brainstorming, pas dans cette
  vague.
- **Temps 2 du mécanisme de refus** (carte Kanboard #17) : reste après ce
  chantier, sur l'ordre déjà acté (le refus dépend de la représentation
  vectorielle qui sera choisie à l'issue des vagues 1-3).

## Les 12 variantes mesurées

Les 11 champs de la règle, pris isolément, **plus** le chunk complet
actuel comme référence :

| Variante | Champ(s) | Source |
|---|---|---|
| intitule | `intitule` | Opquast |
| theme | `theme` (libellé) | Opquast |
| contexte | `contexte` | Opquast |
| solution | `solution` | Opquast |
| controle | `controle` | Opquast |
| objectifs | `objectifs` (liste jointe) | Opquast |
| tags | `tags` (liste jointe) | Opquast |
| phases | `phases` (liste jointe) | Opquast |
| strategie_analyse | `strategie_analyse` | LLM (enrichissement) |
| strategie_justification | `strategie_justification` | LLM (enrichissement) |
| guide_analyse | `guide_analyse` | LLM (enrichissement) |
| **baseline** | `build_chunk_text()` actuel (9 champs) | référence de production |

Vérifié en base (245 règles) : seul `tags` a des trous (64 règles sans
aucun tag, 26 %) — `contexte`, `strategie_justification`, `objectifs`,
`phases` sont renseignés sur les 245 règles.

**Champs vides** : pour la variante `tags`, les 64 règles sans tag ne
sont **pas vectorisées** pour cette variante (pas de texte vide envoyé à
l'API d'embedding) — elles sont donc absentes du pool de candidats
interrogé par cette variante. Pour le calcul des métriques de la variante
`tags` : une cible sans tag est retirée de la liste des cibles attendues
du cas (elle ne peut structurellement jamais être trouvée par cette
variante, ce n'est pas un échec de recherche) ; si **toutes** les cibles
d'un cas sont sans tag, le cas entier est exclu du calcul pour cette
variante. Comparaison honnête sur un sous-ensemble, plutôt qu'une
pénalité mécanique.

## Métriques

Le verdict binaire actuel (PASS si la cible est dans le top-15) plafonne
les variantes riches à 95-100 % et ne les distingue plus. Deux métriques
graduées, calculées par variante × famille :

- **MRR** (Mean Reciprocal Rank) : moyenne de `1 / rang` de la cible
  trouvée. Pour un cas à plusieurs cibles attendues (`regles_concurrentes`,
  `multi_sujets`) : rang de la **meilleure** cible trouvée (optimiste —
  mesure si au moins une bonne règle remonte en tête, cohérent avec un
  agent US2 qui a déjà un point d'entrée exploitable dès qu'une cible est
  bien placée). Une cible absente du top-15 compte comme rang infini
  (contribution nulle au MRR, convention standard).
- **recall@k** (k ∈ {1, 3, 5, 10, 15}) : proportion des cibles attendues
  présentes dans le top-k, moyenne sur les cas de la famille. Pour un cas
  à cible unique, binaire (0 ou 1). Pour un cas à cibles multiples,
  fraction (ex. 1 cible sur 2 trouvée dans le top-5 → 0.5) — définition
  standard de recall en RI, plus informative que « au moins une ».

## Architecture

Aucune écriture dans `regle.embedding` (colonne de production) : les
vecteurs des 12 variantes restent en mémoire le temps du run. La
similarité cosinus est calculée **en Python (numpy)**, pas par requête
SQL pgvector — élimine tout risque sur la colonne de prod et évite une
table temporaire. `numpy` (déjà ajoutée à `pyproject.toml`, non commitée
en début de session) est commitée dans le cadre de ce chantier.

```text
app/ingestion/chunking.py
  + build_variant_text(rule, champ: str) -> str | None   # nouveau
    # listes (objectifs/tags/phases) jointes par ", " — même convention
    # que build_chunk_text() existant, pas une nouvelle règle de jointure

app/ingestion/rag_acceptance.py
  + rang_meilleure_cible(candidats_tries: list[int], cibles: list[int]) -> int | None
  + calculer_mrr(rangs: list[int | None]) -> float
  + calculer_recall_a_k(candidats_tries: list[int], cibles: list[int], k: int) -> float

scripts/mesure_variantes_chunks.py   # nouveau point d'entrée
Makefile
  + cible mesure-variantes-chunks
```

### Déroulé du script

1. Charger les 114 cas d'acceptance (`load_cases`).
2. Décomposer et vectoriser les 114 questions **une seule fois**
   (`DecompositionClient` + `EmbeddingClient`) — sous-questions et
   vecteurs figés, réutilisés pour les 12 variantes.
3. Pour chaque variante (12) :
   a. Construire le texte de chaque règle (`build_variant_text` ou
      `build_chunk_text` pour la baseline), ignorer les règles à texte
      vide pour cette variante.
   b. Vectoriser en lot (`embed_batch`, `BATCH_SIZE=50` comme
      `embed_rules.py`) — vecteurs gardés en mémoire
      (`dict[numero, vecteur]`).
   c. Pour chaque question : pour chaque sous-question déjà vectorisée,
      calculer la similarité cosinus (numpy) contre tous les vecteurs de
      la variante, trier, garder le top-15 ; unir les sous-questions
      (même logique que `retrieve()` — meilleur score gardé sur doublon).
   d. Calculer rang de la meilleure cible, MRR, recall@k ; écrire une
      ligne CSV par candidat retourné.
4. Écrire `docs/eval/mesure_variantes_chunks_<horodatage>.csv` (format
   long : `variante, question, famille, numeros_attendus, numero_retourne,
   rang, cosinus, est_cible`) et un résumé Markdown agrégé (MRR/recall@k
   par variante × famille) dans `docs/eval/mesure_variantes_chunks_<horodatage>.md`.

Le CSV brut n'est **jamais réécrit par-dessus un fichier annoté** : chaque
run produit un nouveau fichier horodaté, distinct de tout tableur de
travail que David créera à partir de ce CSV.

## Budget

~0,011 € (245 règles × 12 variantes à vectoriser, essentiellement des
champs courts, plus la décomposition + embedding des 114 questions payés
une seule fois). Détail confirmé en conversation.

## Tests

- **Unitaires** (`build_variant_text`) : champ renseigné → texte
  attendu ; champ vide/liste vide → `None`.
- **Unitaires** (`rang_meilleure_cible`, `calculer_mrr`,
  `calculer_recall_a_k`) : cas à cible unique trouvée/absente, cas à
  cibles multiples (meilleure cible gagne pour le rang, fraction pour le
  recall), cible absente du top-15.
- **Pas de test unitaire pour le script complet** (même convention que
  `check_rag_acceptance.py`/`rag_dense_acceptance.py`/
  `mesure_scores_refus.py` : couplé à l'API Azure réelle, validé par
  exécution réelle).

## Traçage

`CHANGELOG.md` à l'exécution ; mémoire assistant
`protocole_mesure_retrieval.md` mise à jour avec le résultat une fois la
vague 1 mesurée ; `TODO.md` (nouvelle entrée, chantier distinct du
refus).
