# Mesure des variantes de chunk — Vague 2 (combinaisons de champs) — design

2026-09-11

## Contexte

La vague 1 (`docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md`,
exécutée) a mesuré MRR/recall@k pour les 11 champs de la règle pris
**isolément**, plus le chunk complet de production comme référence.
Résultat : `theme`/`tags`/`phases`/`strategie_analyse` quasi inutiles
isolément (cardinalité trop faible pour porter un signal) ; `intitule` et
`guide_analyse` généralistes (bon signal sur presque toutes les
familles) ; `objectifs` spécialiste extrême (bat la baseline sur sa
propre famille cible, faible ailleurs). Détail complet : mémoire
assistant `protocole_mesure_retrieval.md`.

Cette vague 1 était volontairement exploratoire : elle mesurait des
champs isolés, pas des combinaisons, et n'appliquait pas les points 2
et 3 du protocole (jeu réservé, critère de décision écrit d'avance) —
réservés à la vague qui **choisit** vraiment, celle-ci.

## Objectif de cette vague

Décider si une combinaison de champs bat le chunk de production actuel
sur les cas d'acceptance, **sur preuve et avec un critère écrit
d'avance** — pas seulement mesurer comme en vague 1. Cette vague peut
conclure "on garde le chunk actuel" : c'est une issue valide, pas un
échec du protocole.

## Hors périmètre

- **Vague 3 (affinage)** : sujet d'un futur cycle spec → plan, si cette
  vague ne tranche pas définitivement (voir critère de décision, point 4).
- **Bascule en production** : cette vague décide sur le papier. Si un
  candidat gagne, modifier `build_chunk_text()` et ré-ingérer
  `regle.embedding` en production est un chantier séparé, hors périmètre.
- **Late fusion** (moyenne de vecteurs déjà vectorisés séparément) :
  piste distincte évoquée en brainstorming, pas dans cette vague.
- **Temps 2 du mécanisme de refus** (carte Kanboard #17) : reste après ce
  chantier, sur l'ordre déjà acté (David, 2026-09-11 : vague 2 d'abord).
- **Biais de construction du jeu** (point 4 du protocole — les 114
  questions ont été écrites en connaissant la règle cible) : documenté
  comme limite connue, pas traité par cette vague.

## Les 6 candidats mesurés

| Nom | Champs | Motivation (mémoire `protocole_mesure_retrieval.md`) |
|---|---|---|
| **baseline** | `build_chunk_text()` actuel (9 champs) | référence de production, candidate au classement (peut gagner = ne rien changer) |
| **A — chunk épuré** | intitulé+contexte+solution+controle+guide_analyse+objectifs | retirer les champs nuls (theme/tags/phases) dégrade-t-il le rappel ou juste le bruit ? |
| **B — duo généraliste** | intitulé+guide_analyse | approche-t-il la baseline avec un texte bien plus court ? |
| **C — duo+spécialiste** | intitulé+guide_analyse+objectifs | comble-t-il le trou `vocabulaire_objectif` sans bruit ailleurs ? |
| **D — source Opquast seule** | baseline moins guide_analyse | l'enrichissement LLM sert-il vraiment le RAG, ou la richesse vient-elle du texte source ? |
| **E — enrichissement seul** | guide_analyse+strategie_justification | symétrique de D |

Vérifié en vague 1 (245 règles) : tous les champs impliqués dans ces 6
candidats (`intitule`, `contexte`, `solution`, `controle`,
`guide_analyse`, `objectifs`, `strategie_justification`, `theme`) sont
renseignés sur les 245 règles — aucun cas d'exclusion comme pour `tags`
(absent de tous les candidats de cette vague).

## Jeu réservé (point 2 du protocole)

Tirage aléatoire **stratifié par famille**, ~1/3 des 114 cas
d'acceptance, mis de côté et jamais utilisé pour comparer les
candidats — uniquement pour valider le gagnant provisoire (voir
critère ci-dessous). Seed fixée en dur dans le code (reproductible tant
que `tests/acceptance/rag_acceptance.jsonl` ne change pas).

La liste des cas réservés est **persistée** dans
`tests/acceptance/rag_acceptance_holdout.json` (liste des questions du
jeu réservé) au premier run — un fichier auditable indépendamment d'un
rerun futur, plutôt qu'un simple recalcul par seed qui deviendrait
invisible si le fichier de cas change entre-temps.

## Métriques

Mêmes métriques que la vague 1, calculées par candidat × famille sur
chacun des deux sous-ensembles (exploration et réservé) :

- **MRR** (Mean Reciprocal Rank), rang de la meilleure cible pour un cas
  à cibles multiples.
- **recall@k** (k ∈ {1, 3, 5, 10, 15}).

## Critère de décision (écrit avant de voir les chiffres)

1. Calculer, **sur le jeu d'exploration uniquement** (~76 cas), le MRR
   moyen **non pondéré entre familles** (chaque famille compte pareil,
   indépendamment de son nombre de cas) pour les 6 candidats.
2. **Éliminer** tout candidat parmi A-E qui régresse **strictement** en
   dessous du MRR de la baseline sur **au moins une famille** (plancher
   relatif à la baseline, pas de marge de tolérance — un candidat qui
   fait moins bien que l'existant sur une famille n'est pas retenu).
3. Parmi les candidats survivants et la baseline, celui dont le MRR
   moyen (non pondéré) est le plus haut est le **gagnant provisoire**.
4. **Valider** ce gagnant sur le jeu réservé (~38 cas), jamais utilisé
   jusqu'ici : si son MRR moyen non pondéré y bat ou égale celui de la
   baseline, il devient le **choix retenu** pour un futur chantier de
   bascule en production. Sinon, **on garde le chunk actuel** ; une
   vague 3 (affinage) reste une option future, pas automatique.

Le jeu réservé ne sert **qu'à cette étape 4** — jamais à comparer les 6
candidats entre eux (ce qui reviendrait à l'utiliser comme un second
jeu d'exploration et annulerait sa fonction de validation).

## Architecture

Même schéma que la vague 1 : aucune écriture dans `regle.embedding`,
similarité cosinus calculée en numpy, décomposition et embedding des
114 questions calculés une seule fois et réutilisés pour les 6
candidats.

```text
app/ingestion/chunking.py
  + build_combo_text(rule, champs: list[str]) -> str   # nouveau
    # texte labellisé multi-champs, mêmes labels que build_chunk_text
    # (+ label pour strategie_justification, absent de build_chunk_text
    # mais nécessaire pour le candidat E)
    # saute une ligne si un champ est vide (même convention que le
    # traitement optionnel de "Contexte" dans build_chunk_text) — aucun
    # des 6 candidats ne devrait déclencher ce cas sur les 245 règles

tests/acceptance/
  + rag_acceptance_holdout.json   # nouveau, écrit au premier run

scripts/mesure_combinaisons_chunks.py   # nouveau point d'entrée
Makefile
  + cible mesure-combinaisons-chunks
```

### Déroulé du script

1. Charger les 114 cas d'acceptance (`load_cases`).
2. Si `rag_acceptance_holdout.json` n'existe pas : tirer le jeu réservé
   (stratifié par famille, seed fixée), l'écrire. Sinon le charger tel
   quel (garantit la stabilité entre runs).
3. Décomposer et vectoriser les 114 questions une seule fois
   (`DecompositionClient` + `EmbeddingClient`).
4. Pour chacun des 6 candidats : construire le texte de chaque règle
   (`build_combo_text` ou `build_chunk_text` pour la baseline),
   vectoriser en lot (`BATCH_SIZE=50`, pause de 20s entre lots — cf.
   incident rate limit de la vague 1), calculer MRR/recall@k **séparément
   sur le sous-ensemble exploration et le sous-ensemble réservé**.
5. Appliquer le critère de décision (ci-dessus), écrire la conclusion
   en clair dans le résumé Markdown (candidat éliminé/gagnant
   provisoire/validé ou non).
6. Écrire `docs/eval/mesure_combinaisons_chunks_<horodatage>.csv`
   (même format long que la vague 1, avec une colonne `sous_ensemble`
   ∈ {exploration, reserve}) et un résumé Markdown
   `docs/eval/mesure_combinaisons_chunks_<horodatage>.md`.

## Budget

Négligeable (6 candidats à vectoriser contre 12 en vague 1, questions
déjà décomposées/vectorisées une seule fois) — de l'ordre de 0,005 à
0,01 €, à confirmer en conversation avant l'exécution réelle comme pour
la vague 1.

## Tests

- **Unitaire** (`build_combo_text`) : plusieurs champs renseignés →
  texte attendu avec labels ; champ vide → ligne sautée ; liste
  (`objectifs`) jointe par `, ` comme `build_chunk_text`.
- **Unitaire** (tirage stratifié du jeu réservé) : proportions
  respectées par famille, déterministe pour une seed donnée.
- **Unitaire** (application du critère de décision, fonction pure) :
  cas où un candidat est éliminé par le plancher, cas où le gagnant
  provisoire est validé, cas où il ne l'est pas.
- **Pas de test unitaire pour le script complet** (même convention que
  `mesure_variantes_chunks.py` : couplé à l'API Azure réelle, validé par
  exécution réelle).

## Traçage

`CHANGELOG.md` à l'exécution ; mémoire assistant
`protocole_mesure_retrieval.md` mise à jour avec le résultat ; `TODO.md`
(vague 2 passée de `[ ]` à `[x]` ou reformulée selon le résultat).
