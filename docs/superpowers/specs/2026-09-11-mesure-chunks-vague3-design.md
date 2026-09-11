# Mesure des variantes de chunk — Vague 3 (multi-vecteurs par règle) — design

2026-09-11

## Contexte

Les vagues 1 (`docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md`)
et 2 (`docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md`) ont
mesuré et conclu : **un seul texte vectorisé par règle** (le chunk de
production, 9 champs), et aucune des 5 combinaisons en un seul texte
testées en vague 2 ne l'a battu. Détail complet : mémoire assistant
`protocole_mesure_retrieval.md`, `jury/documents_jury/working/fiche-rag-mesure-chunks.md`.

Ces deux vagues ne testaient qu'une hypothèse : quel texte mettre dans
**un** vecteur par règle. David propose maintenant une architecture
différente, anticipée mais jamais mesurée dès la conception du protocole
initial (« la conclusion pourrait être plusieurs vecteurs par règle plutôt
qu'un chunk unique ») : **plusieurs vecteurs séparés par règle**, cherchés
indépendamment à la requête puis fusionnés — pas un texte combiné (déjà
testé et écarté : candidat B de la vague 2, intitulé+guide_analyse en un
seul texte, avait régressé).

Deux hypothèses distinctes ont été identifiées en brainstorming (voir
échange avec David) : (1) plusieurs vecteurs par règle, fusionnés à la
requête, et (2) faire varier la **dimension** de l'embedding selon la
taille du texte (dimension réduite pour un texte court, hypothèse qu'une
grande dimension pourrait diluer le signal d'un texte court). Elles sont
**volontairement isolées** — les mélanger rendrait un résultat
ininterprétable (impossible de savoir laquelle des deux explique un
changement). Cette vague ne couvre que la première ; la seconde est
laissée pour une mesure future, si celle-ci montre un intérêt.

## Objectif de cette vague

Mesurer si un candidat à **3 vecteurs par règle** (chunk complet actuel +
intitulé seul + guide_analyse seul, tous à dimension pleine 1536), fusionnés
à la requête en gardant le meilleur score par règle, bat le chunk unique
de production — avec le même rigueur que la vague 2 (jeu réservé déjà
figé, critère de décision écrit d'avance).

## Hors périmètre

- **Dimension d'embedding réduite** pour les textes courts (intitulé,
  guide_analyse) : hypothèse distincte, non mesurée ici — voir ci-dessus.
- **D'autres combinaisons de vecteurs** (ex. ajouter `objectifs` comme
  4e vecteur) : cette vague teste un seul candidat, motivé par les deux
  champs généralistes forts de la vague 1 (`intitule`, `guide_analyse`).
  Une combinaison différente resterait un futur cycle spec → plan si
  celle-ci montre un intérêt.
- **Décision finale de bascule en production** : cette vague mesure, elle
  ne modifie pas `app/retrieval/retrieval.py::retrieve()` ni le schéma de
  `regle.embedding` (toujours une seule colonne). Une conclusion positive
  ouvrirait un chantier séparé (schéma multi-colonnes ou table dédiée,
  modification de `retrieve()` pour interroger plusieurs vecteurs) — hors
  périmètre ici, comme pour les vagues précédentes.

## Le candidat mesuré

Un seul candidat, `F_multi_vecteurs`, à côté de la baseline :

| Type de vecteur | Texte | Construit par |
|---|---|---|
| `baseline` | chunk complet (9 champs) | `build_chunk_text(rule)` (existant) |
| `intitule` | intitulé seul | `build_variant_text(rule, "intitule")` (existant, vague 1) |
| `guide_analyse` | guide d'analyse seul | `build_variant_text(rule, "guide_analyse")` (existant, vague 1) |

Les trois champs sont renseignés sur les 245 règles (vérifié en vague 1)
— aucun cas d'exclusion.

**Fusion à la requête** : pour une question donnée, chacun des 3 types de
vecteur produit son propre top-`top_n` (fusionné sur les sous-questions,
comme `retrieve_variante` le fait déjà pour un seul vecteur) ; les 3
résultats sont ensuite fusionnés en gardant le **meilleur score par
règle**, ordre de première apparition entre les 3 types — même principe
que la fusion multi-sous-questions déjà en place en production dans
`app/retrieval/retrieval.py::retrieve()`, appliqué ici à des types de
chunk plutôt qu'à des sous-questions.

## Jeu réservé et critère de décision

**Réutilisés tels quels, pas redéfinis** :
- Jeu réservé déjà figé en vague 2 (`tests/acceptance/rag_acceptance_holdout.json`,
  38/114 cas, stratifié par famille) — garantit une comparaison sur le
  même échantillon que les 5 candidats précédents.
- Critère de décision de la vague 2 (`appliquer_critere_decision`, déjà
  générique pour N candidats) : MRR moyen non pondéré entre familles sur
  le jeu d'exploration, élimination si régression stricte vs la baseline
  sur au moins une famille, gagnant provisoire validé sur le jeu réservé.
  Avec un seul nouveau candidat, deux issues possibles : `F_multi_vecteurs`
  survit et est validé (choix retenu), ou il est éliminé/non validé
  (choix retenu : baseline, aucun changement — comme la vague 2).

## Architecture

Même schéma que les vagues 1 et 2 : aucune écriture dans `regle.embedding`,
similarité cosinus en numpy, décomposition et embedding des 114 questions
calculés une seule fois.

```text
app/ingestion/rag_acceptance.py
  + fusionner_meilleur_score(resultats: list[list[tuple[int, float]]]) -> list[tuple[int, float]]
    # généralise le principe déjà dans retrieve_variante (garder le
    # meilleur score par règle, ordre de première apparition) à une
    # fusion de plusieurs listes déjà produites par retrieve_variante
  + mesurer_candidat_fusion(
        nom_candidat: str,
        vecteurs_par_type: dict[str, dict[int, list[float]]],
        cases: list[dict],
        sous_questions_vecteurs_par_cas: list[list[list[float]]],
        top_n: int,
        recall_ks: list[int],
    ) -> tuple[list[dict], list[dict]]
    # équivalent de mesurer_variante pour un candidat à plusieurs
    # vecteurs par règle : calcule la fusion (retrieve_variante par type
    # + fusionner_meilleur_score) puis la même agrégation MRR/recall/CSV.
    # Logique d'agrégation dupliquée depuis mesurer_variante plutôt que
    # paramétrée dessus — chaque fonction garde un seul comportement
    # clair (un vecteur par règle vs plusieurs), pas de mode conditionnel.
  ~ construire_resume_markdown_vague2(...) : + paramètre `titre: str | None
    = None` (valeur par défaut = titre actuel de la vague 2, inchangé pour
    les appels existants) — permet de réutiliser le même formatage pour
    le résumé de la vague 3 avec un titre différent.

scripts/mesure_multi_vecteurs_chunks.py   # nouveau point d'entrée
Makefile
  + cible mesure-multi-vecteurs-chunks
```

### Déroulé du script

1. Charger les 114 cas (`load_cases`), charger le jeu réservé déjà figé
   (même fonction `charger_ou_creer_jeu_reserve` que la vague 2, réutilisée
   telle quelle — le fichier existe déjà, donc uniquement chargé, jamais
   retiré).
2. Décomposer et vectoriser les 114 questions une seule fois.
3. Vectoriser les 3 types de vecteur du candidat `F_multi_vecteurs`
   (`build_chunk_text`, `build_variant_text(rule, "intitule")`,
   `build_variant_text(rule, "guide_analyse")`) — 3 lots de 245 règles,
   dimension 1536 (`EmbeddingClient` par défaut, inchangé).
4. Vectoriser aussi la baseline seule (déjà l'un des 3 types ci-dessus,
   réutilisée directement comme candidat `baseline` pour la comparaison).
5. Mesurer `baseline` avec `mesurer_variante` (existant) et
   `F_multi_vecteurs` avec `mesurer_candidat_fusion` (nouveau), chacun sur
   le jeu d'exploration puis sur le jeu réservé.
6. Appliquer `appliquer_critere_decision`, écrire CSV (colonne
   `sous_ensemble` comme en vague 2) et résumé Markdown
   (`construire_resume_markdown_vague2` avec `titre="Mesure multi-vecteurs
   — vague 3"`).

## Budget

Estimation ~0,010-0,015 € : décomposition des 114 questions (poste
dominant, ~0,008 € mesuré en vague 2, refait à chaque run) + vectorisation
de 245 règles × 3 types de vecteur (baseline + 2 champs isolés, plus
léger que les 6 candidats de la vague 2). Confirmation du coût réel avec
David avant l'exécution, comme pour les vagues précédentes.

## Tests

- **Unitaire** (`fusionner_meilleur_score`) : plusieurs listes avec
  chevauchement (garde le meilleur score), sans chevauchement (union),
  ordre de première apparition entre les listes.
- **Unitaire** (`mesurer_candidat_fusion`) : cas où la fusion retrouve la
  cible via un seul type de vecteur, cas où deux types la retrouvent à
  des rangs différents (le meilleur l'emporte), cible absente des 3 types.
- **Unitaire** (`construire_resume_markdown_vague2` avec `titre`) : titre
  personnalisé apparaît dans la sortie ; appel sans `titre` conserve le
  texte actuel (non-régression vague 2).
- **Pas de test unitaire pour le script complet** (même convention que
  les vagues 1 et 2 : couplé à Azure réel, validé par exécution réelle).

## Traçage

`CHANGELOG.md` à l'exécution ; mémoire assistant
`protocole_mesure_retrieval.md` mise à jour avec le résultat ; `TODO.md`
(la ligne « Vague 3 » actuellement marquée sans objet est réouverte et
reformulée selon le résultat).
