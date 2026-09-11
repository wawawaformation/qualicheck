# Mesure des combinaisons de chunk — Vague 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mesurer MRR et recall@k pour 6 candidats (baseline + 5 combinaisons de champs) sur les 114 cas d'acceptance, en appliquant un jeu réservé stratifié par famille et un critère de décision écrit d'avance, sans jamais écrire dans `regle.embedding`.

**Architecture:** Le jeu de 114 cas est partitionné une fois (stratifié par famille, ~1/3 réservé, seed fixée) et le partitionnement est persisté dans un fichier JSON pour rester stable entre les runs. Décomposition et embedding des 114 questions calculés une seule fois. Pour chacun des 6 candidats : construction du texte par règle, vectorisation en mémoire, mesure séparée sur le jeu d'exploration et sur le jeu réservé (réutilise `mesurer_variante`, déjà écrit en vague 1). Un critère de décision pur (plancher relatif à la baseline, puis validation sur le jeu réservé) tranche entre les candidats.

**Tech Stack:** Python, numpy, SQLAlchemy (lecture seule), Azure OpenAI (embeddings + décomposition), pytest.

## Global Constraints

- Retry LLM : 3 tentatives avec backoff (déjà en place dans `DecompositionClient`/`EmbeddingClient`, réutilisés tels quels).
- Aucune écriture dans `regle.embedding` (colonne de production) — tous les vecteurs des candidats restent en mémoire le temps du run.
- Pause de 20s entre lots d'embedding (rate limit Azure S0, incident vague 1) — reprise telle quelle, pas de nouveau tuning.
- Traçage : `CHANGELOG.md` à la fin de ce plan, format `## [date] — [outil]`.
- Le CSV brut n'est jamais réécrit par-dessus un fichier annoté par David — chaque run produit un nouveau fichier horodaté.
- Le jeu réservé, une fois écrit dans `tests/acceptance/rag_acceptance_holdout.json`, n'est jamais recalculé par un run suivant tant que ce fichier existe — c'est ce qui garantit qu'il reste "figé" au sens du protocole.

---

## Contexte technique déjà vérifié dans le code

- `app/ingestion/chunking.py::build_chunk_text(rule) -> str` (baseline, 9 champs) et `build_variant_text(rule, champ) -> str | None` (vague 1) existent déjà. Ce plan ajoute `build_combo_text(rule, champs: list[str]) -> str`, qui ne retourne jamais `None` (contrairement à `build_variant_text`) : un champ vide dans une combinaison est simplement omis de la sortie, comme `build_chunk_text` le fait déjà pour `contexte`.
- `app/ingestion/rag_acceptance.py` contient déjà `load_cases()`, `mesurer_variante(nom_variante, vecteurs_regles, cases, sous_questions_vecteurs_par_cas, top_n, recall_ks) -> tuple[list[dict], list[dict]]` et `construire_resume_markdown(lignes, horodatage) -> str` (vague 1, déplacés depuis le script lors de la revue finale de la vague 1 — convention désormais actée : logique pure dans `app/`, script en simple point d'entrée). Ce plan y ajoute les fonctions du jeu réservé et du critère de décision.
- Vérifié en vague 1 (245 règles) : `intitule`, `theme`, `contexte`, `solution`, `controle`, `guide_analyse`, `objectifs`, `strategie_justification` sont renseignés sur les 245 règles — aucun des 6 candidats de cette vague ne peut produire un texte vide pour une règle (contrairement à la variante `tags` de la vague 1, qui a des trous et n'est utilisée par aucun candidat ici).
- Les 114 cas d'acceptance (`tests/acceptance/rag_acceptance.jsonl`) se répartissent en 7 familles : `paraphrase_intitule` (17), `vocabulaire_source_opquast` (20), `vocabulaire_genere_llm` (22), `multi_sujets` (4), `regles_concurrentes` (7), `vocabulaire_objectif` (24), `sans_reponse` (20, `numeros_regle_attendus` toujours vide — exclue du calcul MRR/recall par `mesurer_variante`, comme en vague 1).
- Convention `scripts/` = points d'entrée seuls, toute logique testable vit dans `app/`. Aucun test unitaire pour les scripts couplés à Azure réel (`mesure_variantes_chunks.py`, `mesure_scores_refus.py`, etc.) — ce plan suit la même règle pour `scripts/mesure_combinaisons_chunks.py`.
- `Makefile:1` porte la ligne `.PHONY` à mettre à jour ; `Makefile:124-127` porte la cible `mesure-variantes-chunks` existante, juste après laquelle ajouter la nouvelle cible.

---

### Task 1: `build_combo_text()` — texte labellisé d'une combinaison de champs

**Files:**
- Modify: `app/ingestion/chunking.py`
- Modify: `tests/unit/ingestion/test_chunking.py` (existe déjà, utilise le helper `_rule(contexte=None, objectifs=None, tags=None, phases=None)`)

**Interfaces:**
- Produces: `build_combo_text(rule, champs: list[str]) -> str`. `rule` porte les mêmes attributs qu'`EnrichedRule`. `champs` est une liste de noms d'attributs, dans l'ordre où ils doivent apparaître dans le texte. Ne retourne jamais `None` — un champ vide est simplement omis (pas de ligne vide, pas d'exclusion de la règle).

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_chunking.py` :

```python
from app.ingestion.chunking import build_combo_text


def test_build_combo_text_plusieurs_champs_labellises():
    """Une combinaison de plusieurs champs produit un texte labellisé,
    un champ par ligne, dans l'ordre donné."""
    rule = _rule(contexte="Un contexte")

    texte = build_combo_text(rule, ["intitule", "contexte", "objectifs"])

    assert texte == (
        "Intitulé : Les images ont un attribut alt\n"
        "Contexte : Un contexte\n"
        "Objectifs : Accessibilité"
    )


def test_build_combo_text_champ_vide_saute_sans_exclure_la_regle():
    """Un champ vide (contexte=None) est omis de la sortie ; la fonction
    retourne quand même un texte (pas None, contrairement à
    build_variant_text)."""
    rule = _rule(contexte=None)

    texte = build_combo_text(rule, ["intitule", "contexte", "solution"])

    assert texte == (
        "Intitulé : Les images ont un attribut alt\n"
        "Solution : Ajouter alt descriptif"
    )


def test_build_combo_text_champ_liste_jointe():
    """Une liste (objectifs/tags/phases) est jointe par ', ', même
    convention que build_chunk_text/build_variant_text."""
    rule = _rule(objectifs=["Un", "Deux"])

    texte = build_combo_text(rule, ["objectifs"])

    assert texte == "Objectifs : Un, Deux"


def test_build_combo_text_strategie_justification_a_un_label():
    """strategie_justification, absent de build_chunk_text, a son propre
    label — nécessaire pour le candidat E de la vague 2."""
    rule = _rule()

    texte = build_combo_text(rule, ["strategie_justification"])

    assert texte == "Stratégie de justification : Justif"


def test_build_combo_text_tous_les_champs_de_la_vague_2():
    """Les 10 champs utilisés par les 5 combinaisons + la baseline de la
    vague 2 ont tous un label et ne lèvent pas d'erreur."""
    rule = _rule(contexte="Contexte présent")
    champs = [
        "intitule", "theme", "contexte", "solution", "controle",
        "objectifs", "tags", "phases", "strategie_justification", "guide_analyse",
    ]

    texte = build_combo_text(rule, champs)

    for champ_attendu in [
        "Intitulé", "Thème", "Contexte", "Solution", "Controle",
        "Objectifs", "Tags", "Phases", "Stratégie de justification", "Guide d'analyse",
    ]:
        assert f"{champ_attendu} : " in texte
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: FAIL (`ImportError: cannot import name 'build_combo_text'`) — les tests déjà présents pour `build_chunk_text`/`build_variant_text` continuent de passer.

- [ ] **Step 3: Implémenter la fonction**

Ajouter dans `app/ingestion/chunking.py`, après `build_variant_text()` :

```python
def build_combo_text(rule, champs: list[str]) -> str:
    """
    Texte labellisé d'une combinaison de champs, pour l'étude de
    combinaisons de chunk (scripts/mesure_combinaisons_chunks.py, voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md).

    Args:
        rule: objet portant les mêmes attributs qu'EnrichedRule
        champs: noms des attributs à inclure, dans l'ordre donné

    Returns:
        Texte structuré avec labels, une section par champ non vide.
        Un champ vide est omis (même convention que le traitement
        optionnel de "Contexte" dans build_chunk_text) — contrairement à
        build_variant_text, la règle n'est jamais exclue : ne retourne
        jamais None.
    """
    labels = {
        "intitule": "Intitulé",
        "theme": "Thème",
        "contexte": "Contexte",
        "solution": "Solution",
        "controle": "Controle",
        "objectifs": "Objectifs",
        "tags": "Tags",
        "phases": "Phases",
        "strategie_justification": "Stratégie de justification",
        "guide_analyse": "Guide d'analyse",
    }
    parts = []
    for champ in champs:
        valeur = getattr(rule, champ)
        texte = ", ".join(valeur) if isinstance(valeur, list) else valeur
        if texte:
            parts.append(f"{labels[champ]} : {texte}")
    return "\n".join(parts)
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: PASS (tous les tests, anciens et nouveaux)

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/chunking.py tests/unit/ingestion/test_chunking.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/chunking.py tests/unit/ingestion/test_chunking.py
git commit -m "feat: build_combo_text pour les combinaisons de champs de la vague 2"
```

---

### Task 2: `tirer_jeu_reserve()` — partition stratifiée par famille

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Produces: `tirer_jeu_reserve(cases: list[dict], proportion: float, seed: int) -> tuple[list[dict], list[dict]]`. Retourne `(exploration, reserve)`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` :

```python
from app.ingestion.rag_acceptance import tirer_jeu_reserve


def _cases_deux_familles() -> list[dict]:
    return [
        {"question": f"Q{i}", "famille": "fam_a", "numeros_regle_attendus": [1]}
        for i in range(6)
    ] + [
        {"question": f"R{i}", "famille": "fam_b", "numeros_regle_attendus": [2]}
        for i in range(3)
    ]


def test_tirer_jeu_reserve_partition_complete_sans_chevauchement():
    """Chaque cas se retrouve dans exactement un des deux sous-ensembles."""
    cases = _cases_deux_familles()

    exploration, reserve = tirer_jeu_reserve(cases, proportion=1 / 3, seed=42)

    assert len(exploration) + len(reserve) == len(cases)
    questions_exploration = {c["question"] for c in exploration}
    questions_reserve = {c["question"] for c in reserve}
    assert questions_exploration.isdisjoint(questions_reserve)
    assert questions_exploration | questions_reserve == {c["question"] for c in cases}


def test_tirer_jeu_reserve_respecte_la_proportion_par_famille():
    """~1/3 de chaque famille est réservé, pas seulement 1/3 du total
    (une famille à 3 cas ne doit pas se retrouver à 0 cas réservés)."""
    cases = _cases_deux_familles()

    exploration, reserve = tirer_jeu_reserve(cases, proportion=1 / 3, seed=42)

    reserve_fam_a = [c for c in reserve if c["famille"] == "fam_a"]
    reserve_fam_b = [c for c in reserve if c["famille"] == "fam_b"]
    assert len(reserve_fam_a) == 2  # round(6 * 1/3)
    assert len(reserve_fam_b) == 1  # round(3 * 1/3)


def test_tirer_jeu_reserve_deterministe_pour_une_meme_seed():
    """Deux appels avec la même seed et le même ordre d'entrée donnent
    exactement le même partitionnement — condition pour que le jeu
    réservé soit reproductible."""
    cases = _cases_deux_familles()

    exploration_1, reserve_1 = tirer_jeu_reserve(cases, proportion=1 / 3, seed=7)
    exploration_2, reserve_2 = tirer_jeu_reserve(cases, proportion=1 / 3, seed=7)

    assert [c["question"] for c in reserve_1] == [c["question"] for c in reserve_2]
    assert [c["question"] for c in exploration_1] == [c["question"] for c in exploration_2]
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError: cannot import name 'tirer_jeu_reserve'`)

- [ ] **Step 3: Implémenter la fonction**

Ajouter en tête de `app/ingestion/rag_acceptance.py` l'import `random` (à côté de `json`) :

```python
import random
```

Ajouter, après `load_cases()` :

```python
def tirer_jeu_reserve(
    cases: list[dict], proportion: float, seed: int
) -> tuple[list[dict], list[dict]]:
    """Tire un jeu réservé stratifié par famille (point 2 du protocole de
    mesure, voir docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md).

    Pour chaque famille, `proportion` de ses cas (arrondi à l'entier le
    plus proche) est tiré au hasard et mis dans le jeu réservé, le reste
    dans le jeu d'exploration. Déterministe pour une seed et un ordre
    d'entrée donnés — reproductible tant que `cases` ne change pas.

    Retourne (exploration, reserve).
    """
    rng = random.Random(seed)
    cas_par_famille: dict[str, list[dict]] = {}
    for case in cases:
        cas_par_famille.setdefault(case["famille"], []).append(case)

    exploration: list[dict] = []
    reserve: list[dict] = []
    for cas_famille in cas_par_famille.values():
        melange = cas_famille[:]
        rng.shuffle(melange)
        n_reserve = round(len(melange) * proportion)
        reserve.extend(melange[:n_reserve])
        exploration.extend(melange[n_reserve:])

    return exploration, reserve
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: tirer_jeu_reserve, partition stratifiee par famille pour la vague 2"
```

---

### Task 3: Critère de décision — `mrr_moyen_non_pondere`, `candidat_regresse`, `appliquer_critere_decision`

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Consumes: rien de nouveau (fonctions pures, entrées = dictionnaires MRR déjà calculés).
- Produces:
  - `mrr_moyen_non_pondere(mrr_par_famille: dict[str, float]) -> float`
  - `candidat_regresse(mrr_candidat_par_famille: dict[str, float], mrr_baseline_par_famille: dict[str, float]) -> bool`
  - `appliquer_critere_decision(mrr_exploration: dict[str, dict[str, float]], mrr_reserve: dict[str, dict[str, float]], nom_baseline: str = "baseline") -> dict` — retourne `{"candidats_elimines": list[str], "gagnant_provisoire": str, "choix_retenu": str, "valide": bool}`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` :

```python
from app.ingestion.rag_acceptance import (
    appliquer_critere_decision,
    candidat_regresse,
    mrr_moyen_non_pondere,
)


def test_mrr_moyen_non_pondere_moyenne_simple_entre_familles():
    """Chaque famille compte pareil, indépendamment de son nombre de cas."""
    assert mrr_moyen_non_pondere({"fam_a": 1.0, "fam_b": 0.0}) == pytest.approx(0.5)


def test_mrr_moyen_non_pondere_dictionnaire_vide():
    assert mrr_moyen_non_pondere({}) == 0.0


def test_candidat_regresse_vrai_si_une_famille_est_pire():
    mrr_baseline = {"fam_a": 0.5, "fam_b": 0.3}
    mrr_candidat = {"fam_a": 0.6, "fam_b": 0.2}

    assert candidat_regresse(mrr_candidat, mrr_baseline) is True


def test_candidat_regresse_faux_si_tout_est_egal_ou_meilleur():
    mrr_baseline = {"fam_a": 0.5, "fam_b": 0.3}
    mrr_candidat = {"fam_a": 0.5, "fam_b": 0.4}

    assert candidat_regresse(mrr_candidat, mrr_baseline) is False


def test_appliquer_critere_decision_elimine_puis_valide_le_gagnant():
    """Un candidat qui régresse sur une famille est éliminé ; parmi les
    survivants, celui au MRR moyen le plus haut est le gagnant
    provisoire ; confirmé par le jeu réservé, il devient le choix
    retenu."""
    mrr_exploration = {
        "baseline": {"fam_a": 0.5, "fam_b": 0.5},
        "candidat_gagnant": {"fam_a": 0.6, "fam_b": 0.6},
        "candidat_regresse": {"fam_a": 0.9, "fam_b": 0.1},
    }
    mrr_reserve = {
        "baseline": {"fam_a": 0.4, "fam_b": 0.4},
        "candidat_gagnant": {"fam_a": 0.5, "fam_b": 0.5},
        "candidat_regresse": {"fam_a": 0.9, "fam_b": 0.1},
    }

    resultat = appliquer_critere_decision(mrr_exploration, mrr_reserve)

    assert resultat == {
        "candidats_elimines": ["candidat_regresse"],
        "gagnant_provisoire": "candidat_gagnant",
        "choix_retenu": "candidat_gagnant",
        "valide": True,
    }


def test_appliquer_critere_decision_gagnant_non_valide_garde_la_baseline():
    """Un gagnant provisoire qui ne se confirme pas sur le jeu réservé
    laisse la baseline comme choix retenu."""
    mrr_exploration = {"baseline": {"fam_a": 0.5}, "candidat": {"fam_a": 0.6}}
    mrr_reserve = {"baseline": {"fam_a": 0.5}, "candidat": {"fam_a": 0.3}}

    resultat = appliquer_critere_decision(mrr_exploration, mrr_reserve)

    assert resultat["gagnant_provisoire"] == "candidat"
    assert resultat["valide"] is False
    assert resultat["choix_retenu"] == "baseline"


def test_appliquer_critere_decision_egalite_favorise_la_baseline():
    """En cas d'égalité de MRR moyen sur le jeu d'exploration, la
    baseline l'emporte (aucun changement par défaut)."""
    mrr_exploration = {"baseline": {"fam_a": 0.5}, "candidat": {"fam_a": 0.5}}
    mrr_reserve = {"baseline": {"fam_a": 0.5}, "candidat": {"fam_a": 0.5}}

    resultat = appliquer_critere_decision(mrr_exploration, mrr_reserve)

    assert resultat["gagnant_provisoire"] == "baseline"
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError` — les 3 fonctions n'existent pas encore)

- [ ] **Step 3: Implémenter les fonctions**

Ajouter, après `tirer_jeu_reserve()` (Task 2) :

```python
def mrr_moyen_non_pondere(mrr_par_famille: dict[str, float]) -> float:
    """Moyenne non pondérée du MRR entre familles (chaque famille compte
    pareil, indépendamment de son nombre de cas). 0.0 si aucune famille."""
    if not mrr_par_famille:
        return 0.0
    return sum(mrr_par_famille.values()) / len(mrr_par_famille)


def candidat_regresse(
    mrr_candidat_par_famille: dict[str, float],
    mrr_baseline_par_famille: dict[str, float],
) -> bool:
    """True si le candidat fait strictement moins bien que la baseline
    sur au moins une famille (plancher strict, point 2 du critère de
    décision de la vague 2)."""
    return any(
        mrr_candidat_par_famille[famille] < mrr_baseline
        for famille, mrr_baseline in mrr_baseline_par_famille.items()
    )


def appliquer_critere_decision(
    mrr_exploration: dict[str, dict[str, float]],
    mrr_reserve: dict[str, dict[str, float]],
    nom_baseline: str = "baseline",
) -> dict:
    """Applique le critère de décision de la vague 2 (voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md) :
    élimine les candidats qui régressent vs la baseline sur au moins une
    famille (jeu d'exploration), désigne le gagnant provisoire par MRR
    moyen non pondéré le plus haut, puis valide ce gagnant sur le jeu
    réservé.

    mrr_exploration / mrr_reserve : {nom_candidat: {famille: mrr}},
    mêmes candidats et familles dans les deux.

    Retourne {"candidats_elimines": [...], "gagnant_provisoire": str,
    "choix_retenu": str, "valide": bool}. En cas d'égalité de MRR moyen
    sur le jeu d'exploration, la baseline l'emporte (aucun changement
    par défaut).
    """
    baseline_exploration = mrr_exploration[nom_baseline]
    survivants = [nom_baseline] + [
        candidat
        for candidat in mrr_exploration
        if candidat != nom_baseline
        and not candidat_regresse(mrr_exploration[candidat], baseline_exploration)
    ]
    candidats_elimines = [c for c in mrr_exploration if c not in survivants]

    gagnant_provisoire = max(survivants, key=lambda c: mrr_moyen_non_pondere(mrr_exploration[c]))

    mrr_baseline_reserve = mrr_moyen_non_pondere(mrr_reserve[nom_baseline])
    mrr_gagnant_reserve = mrr_moyen_non_pondere(mrr_reserve[gagnant_provisoire])
    valide = mrr_gagnant_reserve >= mrr_baseline_reserve

    return {
        "candidats_elimines": candidats_elimines,
        "gagnant_provisoire": gagnant_provisoire,
        "choix_retenu": gagnant_provisoire if valide else nom_baseline,
        "valide": valide,
    }
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: critere de decision (plancher baseline + validation jeu reserve) pour la vague 2"
```

---

### Task 4: `construire_resume_markdown_vague2()` — résumé avec conclusion de la décision

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Consumes: le format des lignes produites par `mesurer_variante` (déjà existant) et le dict retourné par `appliquer_critere_decision` (Task 3).
- Produces: `construire_resume_markdown_vague2(lignes_exploration: list[dict], lignes_reserve: list[dict], decision: dict, horodatage: datetime) -> str`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` :

```python
from app.ingestion.rag_acceptance import construire_resume_markdown_vague2


def _ligne_resume_exemple() -> dict:
    return {
        "variante": "baseline",
        "famille": "fam_a",
        "mrr": 0.5,
        "recall_1": 0.1,
        "recall_3": 0.2,
        "recall_5": 0.3,
        "recall_10": 0.4,
        "recall_15": 0.5,
    }


def test_construire_resume_markdown_vague2_structure():
    """Contient les deux tableaux (exploration/réservé) et la conclusion
    de la décision, avec le choix retenu en évidence."""
    ligne = _ligne_resume_exemple()
    decision = {
        "candidats_elimines": ["D_source_opquast"],
        "gagnant_provisoire": "B_duo_generaliste",
        "choix_retenu": "B_duo_generaliste",
        "valide": True,
    }

    resultat = construire_resume_markdown_vague2(
        [ligne], [ligne], decision, datetime(2026, 9, 11, 10, 0)
    )

    assert "## Jeu d'exploration" in resultat
    assert "## Jeu réservé" in resultat
    assert "Candidats éliminés" in resultat and "D_source_opquast" in resultat
    assert "**Choix retenu : B_duo_generaliste**" in resultat


def test_construire_resume_markdown_vague2_aucun_candidat_elimine():
    """Le texte reste correct quand la liste des candidats éliminés est
    vide."""
    ligne = _ligne_resume_exemple()
    decision = {
        "candidats_elimines": [],
        "gagnant_provisoire": "baseline",
        "choix_retenu": "baseline",
        "valide": True,
    }

    resultat = construire_resume_markdown_vague2(
        [ligne], [ligne], decision, datetime(2026, 9, 11, 10, 0)
    )

    assert "aucun" in resultat


def test_construire_resume_markdown_vague2_non_valide_le_signale():
    """Une validation échouée est visible dans le texte (pas seulement
    dans le dict de décision)."""
    ligne = _ligne_resume_exemple()
    decision = {
        "candidats_elimines": [],
        "gagnant_provisoire": "C_duo_specialiste",
        "choix_retenu": "baseline",
        "valide": False,
    }

    resultat = construire_resume_markdown_vague2(
        [ligne], [ligne], decision, datetime(2026, 9, 11, 10, 0)
    )

    assert "NON confirmée" in resultat
    assert "**Choix retenu : baseline**" in resultat
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError: cannot import name 'construire_resume_markdown_vague2'`)

- [ ] **Step 3: Implémenter la fonction**

Ajouter, après `construire_resume_markdown()` (fonction existante de la vague 1, non modifiée) :

```python
def construire_resume_markdown_vague2(
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
) -> str:
    """Construit le texte Markdown du résumé de la vague 2 : tableau
    MRR/recall@k sur le jeu d'exploration, tableau sur le jeu réservé, et
    la conclusion du critère de décision (voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md).
    Pure : pas d'écriture disque (voir
    scripts/mesure_combinaisons_chunks.py::ecrire_resume_markdown)."""
    entete = (
        "| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | "
        "recall@10 | recall@15 |"
    )
    separateur = "|---|---|---|---|---|---|---|---|"

    def tableau(lignes: list[dict]) -> str:
        corps = [
            f"| {r['variante']} | {r['famille']} | {r['mrr']:.3f} | "
            f"{r['recall_1']:.3f} | {r['recall_3']:.3f} | {r['recall_5']:.3f} | "
            f"{r['recall_10']:.3f} | {r['recall_15']:.3f} |"
            for r in lignes
        ]
        return f"{entete}\n{separateur}\n" + "\n".join(corps) + "\n"

    candidats_elimines = decision["candidats_elimines"]
    conclusion = (
        f"Candidats éliminés (régression vs baseline sur au moins une "
        f"famille, jeu d'exploration) : "
        f"{', '.join(candidats_elimines) if candidats_elimines else 'aucun'}.\n\n"
        f"Gagnant provisoire (MRR moyen non pondéré le plus haut, jeu "
        f"d'exploration) : **{decision['gagnant_provisoire']}**.\n\n"
        f"Validation sur le jeu réservé : "
        f"{'confirmée' if decision['valide'] else 'NON confirmée'}.\n\n"
        f"**Choix retenu : {decision['choix_retenu']}**"
    )

    return (
        f"# Mesure des combinaisons de chunk — vague 2 "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"## Jeu d'exploration\n\n{tableau(lignes_exploration)}\n"
        f"## Jeu réservé\n\n{tableau(lignes_reserve)}\n"
        f"## Décision\n\n{conclusion}\n"
    )
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: resume markdown de la vague 2 (jeu explo/reserve + decision)"
```

---

### Task 5: Script `scripts/mesure_combinaisons_chunks.py` + cible Makefile

**Files:**
- Create: `scripts/mesure_combinaisons_chunks.py`
- Modify: `Makefile:1` (ligne `.PHONY`), `Makefile:124-127` (après la cible `mesure-variantes-chunks`)

**Interfaces:**
- Consumes: `build_chunk_text`, `build_combo_text` (Task 1) ; `load_cases`, `tirer_jeu_reserve` (Task 2) ; `mrr_moyen_non_pondere` (non appelée directement par le script — utilisée en interne par `appliquer_critere_decision`), `appliquer_critere_decision` (Task 3) ; `mesurer_variante`, `construire_resume_markdown_vague2` (Task 4 et vague 1) ; `load_enriched_rules_from_db` (existant) ; `DecompositionClient`, `EmbeddingClient` (existants).
- Pas de test unitaire dédié (même convention que `mesure_variantes_chunks.py` : couplé à Azure réel, validé par exécution réelle).

- [ ] **Step 1: Écrire le script**

```python
"""Mesure MRR et recall@k pour 6 candidats (baseline + 5 combinaisons de
champs) sur les 114 cas d'acceptance — vague 2 du protocole de mesure des
chunks. Applique le jeu réservé stratifié par famille et le critère de
décision écrits d'avance. Voir
docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md.

Aucune écriture dans regle.embedding : tous les vecteurs des candidats
restent en mémoire, la similarité est calculée en numpy (pas de requête
SQL pgvector). Décomposition et embedding des 114 questions calculés une
seule fois, réutilisés pour les 6 candidats.

Coût réel estimé 0,005-0,01 €, volontairement hors CI — lancé à la
demande via `make mesure-combinaisons-chunks`.
"""

import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunking import build_chunk_text, build_combo_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    appliquer_critere_decision,
    construire_resume_markdown_vague2,
    load_cases,
    mesurer_variante,
    tirer_jeu_reserve,
)
from app.ingestion.stockage import load_enriched_rules_from_db  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
HOLDOUT_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance_holdout.json"
)
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

BATCH_SIZE = 50
TOP_N = 15
RECALL_KS = [1, 3, 5, 10, 15]
PROPORTION_RESERVE = 1 / 3
SEED_JEU_RESERVE = 42

CHAMPS_COMBOS = {
    "A_chunk_epure": [
        "intitule", "contexte", "solution", "controle", "guide_analyse", "objectifs",
    ],
    "B_duo_generaliste": ["intitule", "guide_analyse"],
    "C_duo_specialiste": ["intitule", "guide_analyse", "objectifs"],
    "D_source_opquast": [
        "intitule", "theme", "contexte", "solution", "controle", "objectifs", "tags", "phases",
    ],
    "E_enrichissement_seul": ["guide_analyse", "strategie_justification"],
}


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def charger_ou_creer_jeu_reserve(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    """Charge le jeu réservé s'il a déjà été tiré (HOLDOUT_PATH existe),
    sinon le tire (stratifié par famille) et l'écrit. Garantit que le
    jeu réservé reste stable entre les runs, même si le code de tirage
    est relancé — condition du point 2 du protocole (jeu "figé")."""
    if HOLDOUT_PATH.exists():
        questions_reserve = set(json.loads(HOLDOUT_PATH.read_text(encoding="utf-8")))
        reserve = [c for c in cases if c["question"] in questions_reserve]
        exploration = [c for c in cases if c["question"] not in questions_reserve]
        return exploration, reserve

    exploration, reserve = tirer_jeu_reserve(cases, PROPORTION_RESERVE, SEED_JEU_RESERVE)
    HOLDOUT_PATH.write_text(
        json.dumps([c["question"] for c in reserve], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return exploration, reserve


def vectoriser_combo(
    regles, champs: list[str] | None, embedding_client: EmbeddingClient
) -> dict[int, list[float]]:
    """Construit le texte de chaque règle pour un candidat (combinaison
    de champs, ou baseline si champs=None) puis vectorise par lots de
    BATCH_SIZE."""
    textes_par_numero = {}
    for rule in regles:
        texte = build_chunk_text(rule) if champs is None else build_combo_text(rule, champs)
        if texte:
            textes_par_numero[rule.number] = texte

    numeros_ordonnes = list(textes_par_numero.keys())
    vecteurs_regles: dict[int, list[float]] = {}
    for i in range(0, len(numeros_ordonnes), BATCH_SIZE):
        lot_numeros = numeros_ordonnes[i : i + BATCH_SIZE]
        lot_textes = [textes_par_numero[n] for n in lot_numeros]
        lot_vecteurs = embedding_client.embed_batch(lot_textes)
        for numero, vecteur in zip(lot_numeros, lot_vecteurs, strict=True):
            vecteurs_regles[numero] = vecteur
        # Pause entre lots : évite le RateLimitReached Azure (tier S0),
        # rencontré lors de la vague 1 (scripts/mesure_variantes_chunks.py).
        time.sleep(20)

    return vecteurs_regles


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "variante",
                "sous_ensemble",
                "question",
                "famille",
                "numeros_attendus",
                "cibles_mesurees",
                "numero_retourne",
                "rang",
                "cosinus",
                "est_cible",
            ],
        )
        writer.writeheader()
        writer.writerows(lignes)


def ecrire_resume_markdown(
    chemin: Path,
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
) -> None:
    chemin.write_text(
        construire_resume_markdown_vague2(lignes_exploration, lignes_reserve, decision, horodatage),
        encoding="utf-8",
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)
    exploration_cases, reserve_cases = charger_ou_creer_jeu_reserve(cases)

    logger.info("=== mesure_combinaisons_chunks : démarrage ===")
    progress_logger.info(
        f"mesure_combinaisons_chunks — jeu d'exploration : {len(exploration_cases)} cas, "
        f"jeu réservé : {len(reserve_cases)} cas"
    )

    with Session(engine) as session:
        enriched_rules = load_enriched_rules_from_db(session)
    regles = enriched_rules.regles

    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    # Décomposition + embedding des 114 questions, une seule fois — figés
    # et indexés par question pour être répartis ensuite entre les deux
    # sous-ensembles.
    vecteurs_par_question: dict[str, list[list[float]]] = {}
    for case in cases:
        sous_questions = decomposition_client.decomposer(case["question"])
        vecteurs_par_question[case["question"]] = embedding_client.embed_batch(sous_questions)

    progress_logger.info(
        f"mesure_combinaisons_chunks — décomposition des {len(cases)} cas terminée "
        f"({decomposition_client.input_tokens}+{decomposition_client.output_tokens} tokens)"
    )

    candidats = [("baseline", None)] + list(CHAMPS_COMBOS.items())

    toutes_lignes_csv = []
    resultats_par_candidat: dict[str, tuple[list[dict], list[dict]]] = {}

    for nom_candidat, champs in candidats:
        vecteurs_regles = vectoriser_combo(regles, champs, embedding_client)
        progress_logger.info(
            f"mesure_combinaisons_chunks — candidat {nom_candidat} : "
            f"{len(vecteurs_regles)}/{len(regles)} règles vectorisées"
        )

        vecteurs_exploration = [vecteurs_par_question[c["question"]] for c in exploration_cases]
        vecteurs_reserve = [vecteurs_par_question[c["question"]] for c in reserve_cases]

        lignes_csv_exploration, lignes_resume_exploration = mesurer_variante(
            nom_candidat, vecteurs_regles, exploration_cases, vecteurs_exploration, TOP_N, RECALL_KS
        )
        lignes_csv_reserve, lignes_resume_reserve = mesurer_variante(
            nom_candidat, vecteurs_regles, reserve_cases, vecteurs_reserve, TOP_N, RECALL_KS
        )

        for ligne in lignes_csv_exploration:
            ligne["sous_ensemble"] = "exploration"
        for ligne in lignes_csv_reserve:
            ligne["sous_ensemble"] = "reserve"
        toutes_lignes_csv.extend(lignes_csv_exploration)
        toutes_lignes_csv.extend(lignes_csv_reserve)

        resultats_par_candidat[nom_candidat] = (lignes_resume_exploration, lignes_resume_reserve)

        for ligne in lignes_resume_exploration:
            progress_logger.info(
                f"mesure_combinaisons_chunks — {nom_candidat} / {ligne['famille']} "
                f"(exploration) : MRR={ligne['mrr']:.3f} recall@5={ligne['recall_5']:.3f}"
            )

    mrr_exploration = {
        nom: {ligne["famille"]: ligne["mrr"] for ligne in lignes_exploration}
        for nom, (lignes_exploration, _) in resultats_par_candidat.items()
    }
    mrr_reserve = {
        nom: {ligne["famille"]: ligne["mrr"] for ligne in lignes_reserve}
        for nom, (_, lignes_reserve) in resultats_par_candidat.items()
    }
    decision = appliquer_critere_decision(mrr_exploration, mrr_reserve)
    progress_logger.info(f"mesure_combinaisons_chunks — décision : {decision}")

    tous_lignes_resume_exploration = [
        ligne
        for lignes_exploration, _ in resultats_par_candidat.values()
        for ligne in lignes_exploration
    ]
    tous_lignes_resume_reserve = [
        ligne for _, lignes_reserve in resultats_par_candidat.values() for ligne in lignes_reserve
    ]

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")

    csv_path = REPORT_DIR / f"mesure_combinaisons_chunks_{suffixe}.csv"
    ecrire_csv(csv_path, toutes_lignes_csv)

    md_path = REPORT_DIR / f"mesure_combinaisons_chunks_{suffixe}.md"
    ecrire_resume_markdown(
        md_path, tous_lignes_resume_exploration, tous_lignes_resume_reserve, decision, horodatage
    )

    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
    embedding_cost = (
        embedding_client.total_tokens * embedding_role["prix_entree_par_million"] / 1_000_000
    )
    decomposition_cost = (
        decomposition_client.input_tokens * decomposition_role["prix_entree_par_million"] / 1_000_000
        + decomposition_client.output_tokens
        * decomposition_role["prix_sortie_par_million"]
        / 1_000_000
    )
    cost = embedding_cost + decomposition_cost
    summary = (
        f"mesure_combinaisons_chunks — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)

    logger.info(f"=== mesure_combinaisons_chunks : rapports écrits dans {csv_path} et {md_path} ===")
    progress_logger.info(
        f"=== mesure_combinaisons_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, remplacer la ligne `.PHONY` (ligne 1) :

```makefile
.PHONY: up up-db up-staging down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again embed-rules rag-acceptance rag-dense-acceptance mesure-scores-refus mesure-variantes-chunks mesure-combinaisons-chunks api-regles api-regles-acceptance api-regles-dense-acceptance regles-api-client-install regles-api-client regles-api-client-test
```

Puis, juste après la cible `mesure-variantes-chunks` (`Makefile:126-127`) :

```makefile

## Mesure MRR/recall@k pour 6 candidats (baseline + 5 combinaisons de
## champs), jeu reserve stratifie + critere de decision — vague 2
mesure-combinaisons-chunks:
	uv run python scripts/mesure_combinaisons_chunks.py
```

- [ ] **Step 3: Vérifier la syntaxe du script sans l'exécuter**

Run: `uv run python -c "import ast; ast.parse(open('scripts/mesure_combinaisons_chunks.py').read())"`
Expected: aucune erreur

- [ ] **Step 4: Lint**

Run: `uv run ruff check scripts/mesure_combinaisons_chunks.py`
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add scripts/mesure_combinaisons_chunks.py Makefile
git commit -m "feat: script mesure_combinaisons_chunks (make mesure-combinaisons-chunks)"
```

---

### Task 6: Exécuter la mesure réelle (coût réel, hors CI) — étape manuelle

**Pas de code produit par cette tâche.**

- [ ] **Step 1: Vérifier les prérequis**

`.env` avec les secrets Azure présents, `POSTGRES_DB` migrée et contenant les 245 règles enrichies (ce script revectorise tout lui-même, pas besoin d'embeddings à jour dans `regle.embedding`).

- [ ] **Step 2: Confirmer le coût avec David avant de lancer**

Ce run coûte réellement de l'argent (~0,005-0,01 €, décomposition + embedding de 114 questions déjà comptés côté vague 1 en ordre de grandeur, plus vectorisation de 245 règles × 6 candidats) — redemander confirmation explicite au moment de l'exécuter.

- [ ] **Step 3: Lancer la mesure**

Run: `make mesure-combinaisons-chunks`
Expected: trois artefacts créés — `tests/acceptance/rag_acceptance_holdout.json` (uniquement si absent avant ce run), `docs/eval/mesure_combinaisons_chunks_<horodatage>.csv` et `.md` — coût affiché dans les logs.

- [ ] **Step 4: Vérifier la répartition du jeu réservé**

Run: `python3 -c "import json; print(len(json.load(open('tests/acceptance/rag_acceptance_holdout.json'))))"`
Expected: de l'ordre de 38 (~1/3 de 114, réparti par famille — voir la table des 7 familles dans "Contexte technique déjà vérifié dans le code").

- [ ] **Step 5: Lire la conclusion du résumé Markdown**

Run: `tail -20 docs/eval/mesure_combinaisons_chunks_*.md`
Expected: la section "## Décision" affiche les candidats éliminés (ou "aucun"), le gagnant provisoire, si la validation sur le jeu réservé est confirmée, et le choix retenu.

- [ ] **Step 6: Tracer dans CHANGELOG.md**

Ajouter une entrée `## [date] — Claude Code` résumant : les 6 candidats mesurés, la taille du jeu réservé, le coût réel observé, et la conclusion du critère de décision (candidat retenu ou "on garde le chunk actuel") — copiée depuis la section "Décision" du résumé Markdown, sans l'interpréter davantage (l'interprétation/discussion suit dans une conversation séparée avec David, pas dans le changelog).

- [ ] **Step 7: Mettre à jour TODO.md et la mémoire assistant**

Dans `TODO.md`, passer la case "Vague 2 — combinaisons de champs motivées par la vague 1" de `[ ]` à `[x]`, avec un résumé équivalent à celui du CHANGELOG. Mettre à jour la mémoire assistant `protocole_mesure_retrieval.md` avec le résultat (candidat retenu ou statu quo), en cohérence avec les points 5-6 de la section "Analyse post-vague-1" déjà présente.

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : les 6 candidats (Task 5, `CHAMPS_COMBOS` + boucle `candidats`), le jeu réservé stratifié et persisté (Task 2 `tirer_jeu_reserve` ; Task 5 `charger_ou_creer_jeu_reserve`/`HOLDOUT_PATH`), les métriques par sous-ensemble (Task 5 : `mesurer_variante` appelé deux fois par candidat, colonne `sous_ensemble` dans le CSV), le critère de décision complet — plancher relatif strict, MRR moyen non pondéré, validation sur le jeu réservé, repli sur la baseline (Task 3), le résumé Markdown avec conclusion explicite (Task 4), aucune écriture dans `regle.embedding` (tout reste en `dict` Python) — tout couvert. Le biais de construction du jeu (point 4 du protocole) reste hors périmètre, comme prévu par la spec.
- **Cohérence des types** : `vecteurs_regles: dict[int, list[float]]` cohérent entre `vectoriser_combo` (Task 5) et `mesurer_variante` (déjà existant, vague 1) ; `mrr_exploration`/`mrr_reserve: dict[str, dict[str, float]]` cohérent entre leur construction dans `main()` (Task 5) et la signature d'`appliquer_critere_decision` (Task 3) ; le dict retourné par `appliquer_critere_decision` (`candidats_elimines`, `gagnant_provisoire`, `choix_retenu`, `valide`) est consommé à l'identique par `construire_resume_markdown_vague2` (Task 4) et par `main()` (Task 5).
- **Pas de placeholder** : le script complet de la Task 5 est donné intégralement, pas de fonction esquissée.
