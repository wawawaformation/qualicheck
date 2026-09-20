"""Revue automatisée d'une PR par LLM.

Récupère le diff entre la branche de base et HEAD, demande une revue au LLM
(rôle « revue », scripts/review_pr_config.yml — même déploiement Azure que
le rôle enrichissement, 3 tentatives avec backoff), poste le résultat en
commentaire sur la PR. Le LLM rend un verdict `ok`/`mineur`/`bloquant` : seul
`bloquant` fait échouer la CI. Une panne de l'outil (LLM injoignable, réponse
hors format) reste non bloquante et est signalée dans le commentaire. Au-delà
de MAX_DIFF_CHARS, le diff est tronqué avec un avertissement.

Script maison plutôt que le Claude Code GitHub Action officiel : celui-ci
n'authentifie qu'en OIDC GitHub, inutilisable sur Gitea (hébergeur
principal du projet). Voir conception/4_ci_cd/strategie_tests_et_gates.md.

Gitea et GitHub tous deux implémentés (même contrat REST issues/{n}/comments,
seuls l'URL de base et le schéma du jeton diffèrent) — la CI (lint, tests)
et cette revue tournent sur les deux hébergeurs jusqu'à dev inclus.

Usage :
    uv run python scripts/review_pr.py --host gitea \
        --api-url https://git.david-legrand.fr --repo david/qualicheck \
        --pr 12 --base dev

    uv run python scripts/review_pr.py --host github \
        --api-url https://api.github.com --repo wawawaformation/qualicheck \
        --pr 12 --base dev
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

import httpx
import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

RACINE = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "review_pr_config.yml"

# ~15k tokens : garde-fou de coût sur une PR anormalement grosse, pas une
# limite technique du modèle.
MAX_DIFF_CHARS = 60_000

PROMPT = """Tu es un relecteur de code expérimenté sur un projet Python \
(FastAPI, SQLAlchemy, LangChain, Alembic).

Relis le diff ci-dessous et signale uniquement les problèmes réels : bugs,
incohérences avec le reste du code, oublis (tests, migrations), failles de
sécurité évidentes. Ignore le style si le linter (ruff) ne le signalerait pas.

Réponds UNIQUEMENT par un objet JSON, sans texte autour, de cette forme :

{{"verdict": "ok|mineur|bloquant", "commentaire": "<ton analyse en Markdown>"}}

- "ok" : rien à signaler.
- "mineur" : des remarques utiles, mais rien qui doive empêcher la fusion
  (lisibilité, test manquant sur un cas secondaire, commentaire trompeur).
- "bloquant" : un problème grave — bug avéré, faille de sécurité, perte de
  données, migration manquante, régression fonctionnelle. Ce verdict fait
  échouer la CI : ne l'utilise que si tu en es sûr.

Le champ "commentaire" est rédigé en français, en Markdown, avec un titre par
fichier concerné. Si le verdict est "ok", dis-le en une ligne.

Diff :
```diff
{diff}
```
"""


class RevueOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    verdict: Literal["ok", "mineur", "bloquant"]
    commentaire: str


def charger_role() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["revue"]


def recuperer_diff(base: str) -> str:
    """Diff entre la branche de base (déjà fetchée par le checkout CI) et HEAD."""
    subprocess.run(["git", "fetch", "origin", base], check=True, cwd=RACINE)
    resultat = subprocess.run(
        ["git", "diff", f"origin/{base}...HEAD"],
        check=True,
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    return resultat.stdout


def construire_llm(role: dict) -> ChatOpenAI:
    """Client LLM du rôle « revue » (même déploiement Azure que l'enrichissement)."""
    return ChatOpenAI(
        base_url=os.environ["AZURE_AI_ENDPOINT"],
        api_key=os.environ["AZURE_AI_API_KEY"],
        model=os.environ[role["env_var"]],
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    reraise=True,
)
def invoquer_llm(llm, parser, prompt: str) -> tuple[dict, dict]:
    """
    Un appel LLM et son parsing, avec retry (3 tentatives, backoff 2s/4s/8s).

    Le parsing est dans le périmètre du retry : une réponse hors format est
    retentée, comme dans app/ingestion/llm_client.py. JsonOutputParser ne valide
    pas le schéma (il renvoie un dict brut) : la validation Pydantic est donc
    faite ici, pour qu'un verdict hors énumération soit retenté puis remonte
    jusqu'au except de main() au lieu de lever un KeyError plus loin.
    """
    reponse = llm.invoke(prompt)
    parsed = parser.parse(reponse.content)
    revue = RevueOutput.model_validate(parsed)
    return revue.model_dump(), reponse.usage_metadata or {}


def demander_revue(role: dict, diff: str) -> dict:
    """Revue du diff : verdict, commentaire et coût de l'appel."""
    llm = construire_llm(role)
    parser = JsonOutputParser(pydantic_object=RevueOutput)
    parsed, usage = invoquer_llm(llm, parser, PROMPT.format(diff=diff))

    cout = (
        usage.get("input_tokens", 0) / 1_000_000 * role["prix_entree_par_million"]
        + usage.get("output_tokens", 0) / 1_000_000 * role["prix_sortie_par_million"]
    )
    return {
        "verdict": parsed["verdict"],
        "commentaire": parsed["commentaire"],
        "cout_usd": cout,
    }


def poster_commentaire_gitea(api_url: str, repo: str, pr: int, corps: str, jeton: str) -> None:
    url = f"{api_url}/api/v1/repos/{repo}/issues/{pr}/comments"
    reponse = httpx.post(url, json={"body": corps}, headers={"Authorization": f"token {jeton}"})
    reponse.raise_for_status()


def poster_commentaire_github(api_url: str, repo: str, pr: int, corps: str, jeton: str) -> None:
    """Même contrat que Gitea (issues/{n}/comments), URL et schéma du jeton différents."""
    url = f"{api_url}/repos/{repo}/issues/{pr}/comments"
    reponse = httpx.post(url, json={"body": corps}, headers={"Authorization": f"Bearer {jeton}"})
    reponse.raise_for_status()


def poster_commentaire(host: str, **kwargs) -> None:
    if host == "gitea":
        poster_commentaire_gitea(**kwargs)
    elif host == "github":
        poster_commentaire_github(**kwargs)
    else:
        raise NotImplementedError(f"Hôte « {host} » non pris en charge.")


LIBELLES_VERDICT = {
    "ok": "rien à signaler",
    "mineur": "remarques mineures (informatif)",
    "bloquant": "problème bloquant",
}


def construire_corps(resultat: dict, role: dict, tronque: bool) -> str:
    """Commentaire Markdown posté sur la PR."""
    lignes = [f"## Revue automatisée — {LIBELLES_VERDICT[resultat['verdict']]}", ""]
    if tronque:
        lignes += [
            f"> **Revue partielle** : le diff dépasse {MAX_DIFF_CHARS} caractères, "
            "il a été tronqué. Ce qui suit ne couvre pas toute la PR.",
            "",
        ]
    lignes += [
        resultat["commentaire"],
        "",
        "---",
        f"_{role['modele']} · coût de cette revue : ~{resultat['cout_usd']:.4f} $_",
    ]
    return "\n".join(lignes)


def construire_corps_echec(erreur: Exception) -> str:
    """
    Commentaire posté quand la revue n'a pas pu aboutir (LLM injoignable ou
    réponse hors format après 3 tentatives). Non bloquant : une panne de
    l'outil de revue n'est pas un défaut du code relu.
    """
    return (
        "## Revue automatisée — non aboutie\n\n"
        "La revue n'a pas pu être produite (3 tentatives). La CI n'est pas "
        "bloquée pour autant : relire manuellement.\n\n"
        f"```\n{type(erreur).__name__}: {erreur}\n```"
    )


def code_sortie(verdict: str) -> int:
    """Seul un verdict « bloquant » fait échouer la CI."""
    return 1 if verdict == "bloquant" else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=["gitea", "github"], required=True)
    parser.add_argument("--api-url", required=True, help="URL de base de l'instance (ex. https://git.david-legrand.fr)")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr", type=int, required=True, help="Numéro de la PR")
    parser.add_argument("--base", required=True, help="Branche de base de la PR")
    args = parser.parse_args()

    diff = recuperer_diff(args.base)
    if not diff.strip():
        print("[info] Diff vide, rien à relire.")
        return

    tronque = len(diff) > MAX_DIFF_CHARS
    if tronque:
        print(f"[!] Diff de {len(diff)} caractères, tronqué à {MAX_DIFF_CHARS}.")
        diff = diff[:MAX_DIFF_CHARS]

    role = charger_role()
    try:
        resultat = demander_revue(role, diff)
    except Exception as erreur:  # noqa: BLE001 — toute panne de l'outil reste non bloquante
        print(f"[!] Revue non aboutie : {erreur}")
        corps = construire_corps_echec(erreur)
        verdict = "ok"
    else:
        corps = construire_corps(resultat, role, tronque)
        verdict = resultat["verdict"]

    # Affiché avant le POST : la revue reste lisible dans les logs CI même si
    # le commentaire ne peut pas être posté (jeton ou permissions).
    print(corps)

    jeton = os.environ["REVIEW_API_TOKEN"]
    poster_commentaire(
        args.host, api_url=args.api_url, repo=args.repo, pr=args.pr, corps=corps, jeton=jeton
    )
    print(f"[ok] Revue postée (verdict : {verdict}).")
    sys.exit(code_sortie(verdict))


if __name__ == "__main__":
    main()
