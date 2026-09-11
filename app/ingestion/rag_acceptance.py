"""
Jeu d'acceptance RAG : vérifie que la recherche sémantique pgvector
retrouve la bonne règle Opquast pour une question en langage naturel.

Formalise les vérifications manuelles du 2026-07-26 — voir
docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md.
"""

import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.referentiel import Regle


def load_cases(jsonl_path: Path) -> list[dict]:
    """Charge le jeu de cas d'acceptance RAG depuis un fichier JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


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


def query_top_n_numeros(
    session: Session, vector: list[float], top_n: int
) -> list[tuple[int, float]]:
    """Retourne les (numéro, score) des top_n règles les plus proches du vecteur.

    Score de similarité cosinus (1 - distance) : 1 = identique, 0 = aucun
    rapport. Ordonné par similarité décroissante (le plus proche en premier).
    """
    resultats = (
        session.query(Regle.numero, Regle.embedding.cosine_distance(vector))
        .order_by(Regle.embedding.cosine_distance(vector))
        .limit(top_n)
        .all()
    )
    return [(numero, 1 - distance) for numero, distance in resultats]


def metriques_scores(candidats: list[tuple[int, float]]) -> dict:
    """Calcule top1 (meilleur score) et top15 (15e meilleur, ou le dernier si moins de 15).

    Trie localement par score décroissant, indépendamment de l'ordre de la
    liste passée (retrieve() ordonne par première apparition entre
    sous-questions, pas par score).
    """
    tries = sorted(candidats, key=lambda c: c[1], reverse=True)
    top1 = tries[0][1]
    index_top15 = min(14, len(tries) - 1)
    top15 = tries[index_top15][1]
    return {"top1": top1, "top15": top15, "ecart": top1 - top15}


def rang_meilleure_cible(candidats_tries: list[int], cibles: list[int]) -> int | None:
    """Rang (1-indexé) de la première cible rencontrée dans les candidats
    déjà triés par pertinence décroissante. None si aucune cible n'y figure."""
    for rang, numero in enumerate(candidats_tries, start=1):
        if numero in cibles:
            return rang
    return None


def calculer_mrr(rangs: list[int | None]) -> float:
    """Mean Reciprocal Rank : moyenne de 1/rang, 0 pour une cible absente
    (rang None). 0.0 sur une liste vide (pas de division par zéro)."""
    if not rangs:
        return 0.0
    return sum(1 / rang if rang is not None else 0.0 for rang in rangs) / len(rangs)


def calculer_recall_a_k(candidats_tries: list[int], cibles: list[int], k: int) -> float:
    """Proportion des cibles présentes dans les k premiers candidats.
    0.0 si cibles est vide (pas de division par zéro)."""
    if not cibles:
        return 0.0
    top_k = set(candidats_tries[:k])
    trouves = sum(1 for cible in cibles if cible in top_k)
    return trouves / len(cibles)


def cosine_similarity_matrix(
    vecteur_question: list[float], vecteurs_regles: dict[int, list[float]]
) -> list[tuple[int, float]]:
    """Similarité cosinus entre un vecteur question et un ensemble de
    vecteurs de règles, calculée en numpy (pas de requête SQL). Retourne
    les (numéro, score) triés par similarité décroissante."""
    numeros = list(vecteurs_regles.keys())
    matrice = np.array([vecteurs_regles[numero] for numero in numeros])
    q = np.array(vecteur_question)
    normes = np.linalg.norm(matrice, axis=1) * np.linalg.norm(q)
    scores = (matrice @ q) / normes
    resultat = sorted(zip(numeros, scores.tolist(), strict=True), key=lambda t: t[1], reverse=True)
    return resultat


def retrieve_variante(
    sous_questions_vecteurs: list[list[float]],
    vecteurs_regles: dict[int, list[float]],
    top_n: int,
) -> list[tuple[int, float]]:
    """Même logique de fusion que app.retrieval.retrieval.retrieve(), en
    numpy plutôt que pgvector : top_n par sous-question, union
    dédoublonnée en gardant le meilleur score, ordre de première
    apparition."""
    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for vecteur in sous_questions_vecteurs:
        top = cosine_similarity_matrix(vecteur, vecteurs_regles)[:top_n]
        for numero, score in top:
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score
    return [(numero, meilleurs_scores[numero]) for numero in ordre]


def fusionner_meilleur_score(
    resultats: list[list[tuple[int, float]]],
) -> list[tuple[int, float]]:
    """Fusionne plusieurs listes de (numéro, score) déjà produites (ex.
    une par type de vecteur via retrieve_variante), en gardant le
    meilleur score par règle. Ordre de première apparition entre les
    listes, dans l'ordre donné — même principe que la fusion déjà dans
    retrieve_variante, généralisé à des listes déjà calculées."""
    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for resultat in resultats:
        for numero, score in resultat:
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score
    return [(numero, meilleurs_scores[numero]) for numero in ordre]


def mesurer_variante(
    nom_variante: str,
    vecteurs_regles: dict,
    cases: list[dict],
    sous_questions_vecteurs_par_cas: list[list[list[float]]],
    top_n: int,
    recall_ks: list[int],
) -> tuple[list[dict], list[dict]]:
    """Mesure une variante de chunk sur l'ensemble des cas d'acceptance.
    Retourne (lignes_csv, lignes_resume_par_famille).

    Pure : aucun appel réseau, BDD ni log — la progression est loguée par
    l'appelant (scripts/mesure_variantes_chunks.py::main()).
    """
    lignes_csv = []
    rangs_par_famille: dict[str, list] = {}
    recalls_par_famille: dict[str, dict[int, list]] = {}

    for case, sous_questions_vecteurs in zip(cases, sous_questions_vecteurs_par_cas, strict=True):
        candidats = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=top_n)
        candidats_tries = sorted(candidats, key=lambda t: t[1], reverse=True)
        numeros_tries = [numero for numero, _ in candidats_tries]

        cibles = case["numeros_regle_attendus"]
        # Cibles réellement vectorisées pour cette variante (ex. une règle
        # sans tag est absente de vecteurs_regles pour la variante "tags").
        cibles_valides = [c for c in cibles if c in vecteurs_regles]
        cibles_mesurees_str = ";".join(str(c) for c in cibles_valides)

        for rang, (numero, score) in enumerate(candidats_tries, start=1):
            lignes_csv.append(
                {
                    "variante": nom_variante,
                    "question": case["question"],
                    "famille": case["famille"],
                    "numeros_attendus": ";".join(str(c) for c in cibles),
                    "cibles_mesurees": cibles_mesurees_str,
                    "numero_retourne": numero,
                    "rang": rang,
                    "cosinus": f"{score:.6f}",
                    "est_cible": "oui" if numero in cibles else "non",
                }
            )

        if not cibles_valides:
            continue  # cas exclu pour cette variante (ex. cible sans tag, variante "tags")

        famille = case["famille"]
        rang = rang_meilleure_cible(numeros_tries, cibles_valides)
        rangs_par_famille.setdefault(famille, []).append(rang)
        for k in recall_ks:
            recalls_par_famille.setdefault(famille, {}).setdefault(k, []).append(
                calculer_recall_a_k(numeros_tries, cibles_valides, k)
            )

    lignes_resume = []
    for famille in rangs_par_famille:
        mrr = calculer_mrr(rangs_par_famille[famille])
        ligne = {"variante": nom_variante, "famille": famille, "mrr": mrr}
        for k in recall_ks:
            valeurs = recalls_par_famille[famille][k]
            ligne[f"recall_{k}"] = sum(valeurs) / len(valeurs)
        lignes_resume.append(ligne)

    return lignes_csv, lignes_resume


def mesurer_candidat_fusion(
    nom_candidat: str,
    vecteurs_par_type: dict[str, dict[int, list[float]]],
    cases: list[dict],
    sous_questions_vecteurs_par_cas: list[list[list[float]]],
    top_n: int,
    recall_ks: list[int],
) -> tuple[list[dict], list[dict]]:
    """Comme mesurer_variante, mais pour un candidat à plusieurs vecteurs
    par règle (un par type de chunk, ex. règle complète/intitulé/guide
    d'analyse) : chaque type est cherché séparément (retrieve_variante)
    puis fusionné en gardant le meilleur score par règle
    (fusionner_meilleur_score). Retourne (lignes_csv,
    lignes_resume_par_famille).

    Pure : aucun appel réseau, BDD ni log.
    """
    lignes_csv = []
    rangs_par_famille: dict[str, list] = {}
    recalls_par_famille: dict[str, dict[int, list]] = {}
    numeros_disponibles = next(iter(vecteurs_par_type.values()))

    for case, sous_questions_vecteurs in zip(cases, sous_questions_vecteurs_par_cas, strict=True):
        resultats_par_type = [
            retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=top_n)
            for vecteurs_regles in vecteurs_par_type.values()
        ]
        candidats = fusionner_meilleur_score(resultats_par_type)
        candidats_tries = sorted(candidats, key=lambda t: t[1], reverse=True)
        numeros_tries = [numero for numero, _ in candidats_tries]

        cibles = case["numeros_regle_attendus"]
        cibles_valides = [c for c in cibles if c in numeros_disponibles]
        cibles_mesurees_str = ";".join(str(c) for c in cibles_valides)

        for rang, (numero, score) in enumerate(candidats_tries, start=1):
            lignes_csv.append(
                {
                    "variante": nom_candidat,
                    "question": case["question"],
                    "famille": case["famille"],
                    "numeros_attendus": ";".join(str(c) for c in cibles),
                    "cibles_mesurees": cibles_mesurees_str,
                    "numero_retourne": numero,
                    "rang": rang,
                    "cosinus": f"{score:.6f}",
                    "est_cible": "oui" if numero in cibles else "non",
                }
            )

        if not cibles_valides:
            continue

        famille = case["famille"]
        rang = rang_meilleure_cible(numeros_tries, cibles_valides)
        rangs_par_famille.setdefault(famille, []).append(rang)
        for k in recall_ks:
            recalls_par_famille.setdefault(famille, {}).setdefault(k, []).append(
                calculer_recall_a_k(numeros_tries, cibles_valides, k)
            )

    lignes_resume = []
    for famille in rangs_par_famille:
        mrr = calculer_mrr(rangs_par_famille[famille])
        ligne = {"variante": nom_candidat, "famille": famille, "mrr": mrr}
        for k in recall_ks:
            valeurs = recalls_par_famille[famille][k]
            ligne[f"recall_{k}"] = sum(valeurs) / len(valeurs)
        lignes_resume.append(ligne)

    return lignes_csv, lignes_resume


def construire_resume_markdown(lignes: list[dict], horodatage: datetime) -> str:
    """Construit le texte Markdown du résumé MRR/recall par variante et
    famille. Pure : pas d'écriture disque (voir
    scripts/mesure_variantes_chunks.py::ecrire_resume_markdown)."""
    entete = (
        "| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | "
        "recall@10 | recall@15 |"
    )
    separateur = "|---|---|---|---|---|---|---|---|"
    corps = [
        f"| {r['variante']} | {r['famille']} | {r['mrr']:.3f} | "
        f"{r['recall_1']:.3f} | {r['recall_3']:.3f} | {r['recall_5']:.3f} | "
        f"{r['recall_10']:.3f} | {r['recall_15']:.3f} |"
        for r in lignes
    ]
    return (
        f"# Mesure des variantes de chunk — vague 1 "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"{entete}\n{separateur}\n" + "\n".join(corps) + "\n"
    )


def construire_resume_markdown_vague2(
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
    titre: str | None = None,
) -> str:
    """Construit le texte Markdown du résumé d'une vague de mesure à
    critère de décision (vague 2 et suivantes) : tableau MRR/recall@k sur
    le jeu d'exploration, tableau sur le jeu réservé, et la conclusion du
    critère de décision. `titre` par défaut : celui de la vague 2
    (docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md) —
    une vague suivante (ex. vague 3) passe son propre titre. Pure : pas
    d'écriture disque (voir
    scripts/mesure_combinaisons_chunks.py::ecrire_resume_markdown)."""
    titre_effectif = titre if titre is not None else "Mesure des combinaisons de chunk — vague 2"
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
        f"# {titre_effectif} "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"## Jeu d'exploration\n\n{tableau(lignes_exploration)}\n"
        f"## Jeu réservé\n\n{tableau(lignes_reserve)}\n"
        f"## Décision\n\n{conclusion}\n"
    )


def evaluate_case(case: dict, numeros_retournes: list[int]) -> dict:
    """Évalue un cas : verdict PASS/FAIL/PARTIEL selon les cibles retrouvées.

    Un cas sans cible attendue (numeros_regle_attendus vide, famille
    sans_reponse) est toujours FAIL : aucun mécanisme de refus n'existe
    aujourd'hui dans le pipeline de retrieval.
    """
    attendus = case["numeros_regle_attendus"]
    trouves = [n for n in attendus if n in numeros_retournes]

    if not attendus:
        verdict = "FAIL"
    elif len(trouves) == len(attendus):
        verdict = "PASS"
    elif len(trouves) == 0:
        verdict = "FAIL"
    else:
        verdict = "PARTIEL"

    return {
        "question": case["question"],
        "famille": case["famille"],
        "numeros_regle_attendus": attendus,
        "numeros_retournes": numeros_retournes,
        "verdict": verdict,
    }


def compute_taux_par_famille(evaluations: list[dict]) -> dict[str, dict]:
    """Calcule le taux de réussite par famille, en excluant les PARTIEL.

    Un cas PARTIEL ne compte ni comme succès ni comme échec : il est
    retiré du dénominateur pour ne pas fausser le taux binaire, mais son
    nombre est conservé (partiels) pour rester visible dans les logs.
    Une famille sans aucun cas PASS/FAIL (uniquement des PARTIEL) a un
    taux de 0.0 par convention — pas de division par zéro.
    """
    par_famille: dict[str, list[dict]] = {}
    for evaluation in evaluations:
        par_famille.setdefault(evaluation["famille"], []).append(evaluation)

    resultat = {}
    for famille, evals in par_famille.items():
        partiels = sum(1 for e in evals if e["verdict"] == "PARTIEL")
        non_partiels = [e for e in evals if e["verdict"] != "PARTIEL"]
        reussis = sum(1 for e in non_partiels if e["verdict"] == "PASS")
        total = len(non_partiels)
        taux = reussis / total if total > 0 else 0.0
        resultat[famille] = {"taux": taux, "reussis": reussis, "total": total, "partiels": partiels}
    return resultat


def is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool:
    """Le jeu est acceptable si chaque famille à cible normale atteint le seuil.

    La famille "sans_reponse" est toujours ignorée : son taux est nul par
    construction (aucun mécanisme de refus), ce n'est pas un défaut du
    retrieval mesuré par les autres familles.
    """
    for famille, stats in taux_par_famille.items():
        if famille == "sans_reponse":
            continue
        if stats["taux"] < seuil:
            return False
    return True


def summarize_dataset_versions(session: Session) -> list[dict]:
    """Résume la distribution prompt_version/llm_model des règles en base.

    Permet de savoir, au moment d'un run, si le jeu de données est
    homogène (une seule version de prompt) ou mélangé (ex. suite à un
    enrich_again partiel) — information invisible sinon.
    """
    resultats = (
        session.query(Regle.prompt_version, Regle.llm_model, func.count(Regle.id))
        .group_by(Regle.prompt_version, Regle.llm_model)
        .order_by(Regle.prompt_version)
        .all()
    )
    return [
        {"prompt_version": prompt_version, "llm_model": llm_model, "nombre_regles": nombre}
        for prompt_version, llm_model, nombre in resultats
    ]


def format_dataset_versions(summary: list[dict]) -> str:
    """Formate la distribution prompt_version/llm_model pour le log."""
    return " ; ".join(
        f"prompt_version={s['prompt_version']} ({s['llm_model']}): {s['nombre_regles']} règles"
        for s in summary
    )
