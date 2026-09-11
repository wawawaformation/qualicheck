"""
Jeu d'acceptance RAG : vérifie que la recherche sémantique pgvector
retrouve la bonne règle Opquast pour une question en langage naturel.

Formalise les vérifications manuelles du 2026-07-26 — voir
docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md.
"""

import json
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
