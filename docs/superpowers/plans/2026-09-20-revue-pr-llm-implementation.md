# Revue automatisée de PR par LLM — durcissement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `scripts/review_pr.py` existe et poste une revue de diff en commentaire de PR, mais il ne respecte ni la règle de retry du projet, ni la convention de suivi de coût, n'a aucun test, n'est tracé nulle part, et son unique mode d'échec (diff trop gros) rend la CI rouge pour une raison sans rapport avec le code. Ce plan le rend conforme : verdict structuré qui ne bloque la CI que sur un problème grave, retry 3 tentatives avec backoff, coût mesuré, un test unitaire, documentation et changelog à jour.

**Architecture:** Le script reste un point d'entrée `scripts/` (outil d'ops, exception déjà actée pour `create_api_regles_key.py`) — pas de nouveau module `app/`. Le LLM rend du JSON validé par un modèle Pydantic via `JsonOutputParser`, comme `app/ingestion/llm_client.py`. L'appel LLM et son parsing sont isolés dans une fonction décorée `@retry` et séparés de la construction du client, pour être mockables sans réseau. Le code de sortie du processus est dérivé du seul champ `verdict`.

**Tech Stack:** Python, LangChain (`ChatOpenAI`, `JsonOutputParser`), Pydantic, tenacity, httpx, pytest.

## Global Constraints

- **Principe unique de blocage** : seul un verdict `bloquant` explicitement rendu par le LLM fait échouer la CI. Toute défaillance de l'outil lui-même (réponse hors format, LLM injoignable après 3 tentatives, diff tronqué) reste non bloquante et laisse une trace explicite. Un outil de revue en panne ne doit pas se transformer en gate.
  - **Exception assumée** : si le POST du commentaire échoue (jeton absent, permissions), l'exception remonte et la CI est rouge. C'est une erreur de configuration à corriger, pas un faux positif sur le code. Le corps de la revue est affiché sur stdout **avant** le POST, donc toujours lisible dans les logs CI même dans ce cas.
- **Retry LLM** : 3 tentatives, backoff exponentiel, `reraise=True` — mêmes paramètres que `app/ingestion/llm_client.py` (règle non négociable, `CLAUDE.md`).
- Code en anglais, commentaires et docstrings en français (le script existant est déjà dans cette convention : noms de fonctions en français — **ne pas le renormaliser**, ce n'est pas le périmètre de ce plan).
- Traçage : `CHANGELOG.md` à la fin de ce plan, format `## [date] — [outil]`.
- Fichiers temporaires : `./tmp/` à la racine, jamais `/tmp` système.
- Ne rien changer d'autre dans les workflows que ce que les tâches 6 et 7 désignent. En particulier : **ne pas toucher au garde-fou de tag de `cd-staging.yml`**, son défaut connu est documenté et sa correction est différée après la carte #32 (décision de David, 2026-09-20).

---

## Contexte technique déjà vérifié dans le code

- `scripts/review_pr.py` (état actuel, 137 lignes) expose : `charger_role()`, `recuperer_diff(base)`, `demander_revue(role, diff)`, `poster_commentaire_gitea(...)`, `poster_commentaire_github(...)`, `poster_commentaire(host, **kwargs)`, `main()`. Constantes : `RACINE`, `CONFIG_PATH`, `MAX_DIFF_CHARS = 60_000`, `PROMPT`.
- `scripts/review_pr_config.yml` contient le rôle `revue` avec `modele: kimi-k2.6`, `env_var: AZURE_MODEL_KIMI`, `prix_entree_par_million: 0.8008`, `prix_sortie_par_million: 3.3875`. **Seul `env_var` est lu aujourd'hui** ; `modele` et les deux prix sont morts.
- Pattern de retry de référence — `app/ingestion/llm_client.py:120-125` :
  ```python
  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=2, min=2, max=8),
      reraise=True,
  )
  ```
  Le décorateur y couvre `llm.invoke()` **et** `parser.parse()` : une réponse hors format est donc retentée, pas abandonnée au premier essai. Ce plan reprend ce découpage.
- Pattern de suivi de coût déjà utilisé partout : `app/agent_us2/loop.py:96-97`, `app/ingestion/enrich_again.py:177-178`, `scripts/embed_rules.py:76`, `scripts/ingestion.py:159-160`, `tests/acceptance/check_rag_acceptance.py:112`. Formule : `tokens / 1_000_000 * prix_par_million`.
- `response.usage_metadata` (dict LangChain) expose `input_tokens` / `output_tokens`, avec le `or {}` + `.get(..., 0)` défensif de `llm_client.py:165-167`.
- `tests/unit/scripts/test_clear_opquast_tables.py` donne la convention de test d'un script : `scripts/` n'est pas un paquet, le module est chargé par chemin avec `importlib.util.spec_from_file_location`, via une fixture pytest, et `Path(__file__).resolve().parents[3]` pour remonter à la racine. Un seul autre fichier existe dans `tests/unit/scripts/` — pas de `conftest.py` à respecter.
- `scripts/CLAUDE.md` liste chaque point d'entrée du dossier. `review_pr.py` **n'y figure pas**.
- `CHANGELOG.md` ne mentionne ni `review_pr.py`, ni `ci-review.yml`, ni `.github/workflows/` — rien de cette session n'est tracé.
- `.gitea/workflows/ci-acceptance.yml:6-9` déclenche sur `tags: - "**"`.

---

## Décisions tranchées en amont (ne pas re-décider pendant l'exécution)

| Question | Décision | Raison |
| --- | --- | --- |
| Format du verdict | JSON `{"verdict": "ok\|mineur\|bloquant", "commentaire": "<markdown>"}` | Trois niveaux suffisent pour « informatif vs bloquant » ; un booléen ne distinguerait pas « rien à signaler » de « remarques mineures », ce qui appauvrirait le commentaire. |
| Fail-safe si le LLM ne rend pas ce format | Après les 3 tentatives : **non bloquant**, commentaire posté signalant l'échec de parsing, exit 0 | Un parseur en échec est un défaut de l'outil de revue, pas une preuve de gravité du code. Bloquer là-dessus crée une friction sans valeur et pousserait à désactiver la revue. |
| LLM injoignable après 3 tentatives | Idem : non bloquant, commentaire d'échec, exit 0 | Même raison. Un incident Azure ne doit pas fermer la porte de `dev`. |
| Diff > 60 000 caractères | **Tronquer** + avertissement en première ligne du commentaire, exit 0 | Une PR volumineuse n'est pas un défaut de code. Le `sys.exit(1)` actuel rend la CI rouge sans rapport avec la qualité. L'avertissement préserve l'intention d'origine : jamais partielle en silence. |
| `modele` et prix dans `review_pr_config.yml` | **Exploiter**, ne pas supprimer | Tous les autres appels LLM du dépôt (6 emplacements) affichent leur coût ; le suivi de coût est un enjeu explicite du projet. Coût d'implémentation : 4 lignes. Les supprimer maintenant pour les réintroduire au premier arbitrage de budget serait un faux YAGNI. |
| Filtre de tags de `ci-acceptance.yml` | **Resserrer** au préfixe date | Le déclencheur coûteux doit suivre exactement la convention qui le justifie. Détail et justification : section « Tag » de `conception/4_ci_cd/strategie_tests_et_gates.md`. |

---

### Task 1: Verdict structuré — modèle Pydantic, prompt et parsing

**Files:**
- Modify: `scripts/review_pr.py`

**Interfaces:**
- Produces: `class RevueOutput(BaseModel)` avec `verdict: Literal["ok", "mineur", "bloquant"]` et `commentaire: str`.
- Produces: `construire_llm(role: dict) -> ChatOpenAI`
- Produces: `invoquer_llm(llm, parser, prompt: str) -> tuple[dict, dict]` — retourne `(parsed, usage)`.
- Produces: `demander_revue(role: dict, diff: str) -> dict` — retourne `{"verdict": str, "commentaire": str, "cout_usd": float}`. **Remplace** la fonction `demander_revue(role, diff) -> str` actuelle.

- [ ] **Step 1: Ajouter les imports**

Ajouter à l'en-tête de `scripts/review_pr.py` :

```python
from typing import Literal

from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
```

(`sys` est déjà importé et reste utilisé ; `argparse`, `os`, `subprocess`, `Path`, `httpx`, `yaml`, `ChatOpenAI` restent.)

- [ ] **Step 2: Remplacer `PROMPT` pour exiger le JSON**

Remplacer la constante `PROMPT` existante par :

```python
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
```

**Attention** : les accolades de l'exemple JSON sont doublées (`{{`/`}}`) car `PROMPT` est utilisé avec `str.format(diff=...)`, inchangé.

- [ ] **Step 3: Ajouter le modèle de sortie**

Après les constantes :

```python
class RevueOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    verdict: Literal["ok", "mineur", "bloquant"]
    commentaire: str
```

- [ ] **Step 4: Remplacer `demander_revue`**

Remplacer intégralement la fonction `demander_revue` actuelle par :

```python
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
    retentée, comme dans app/ingestion/llm_client.py.
    """
    reponse = llm.invoke(prompt)
    parsed = parser.parse(reponse.content)
    return parsed, reponse.usage_metadata or {}


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
```

---

### Task 2: Corps du commentaire et code de sortie

**Files:**
- Modify: `scripts/review_pr.py`

**Interfaces:**
- Produces: `construire_corps(resultat: dict, role: dict, tronque: bool) -> str`
- Produces: `construire_corps_echec(erreur: Exception) -> str`
- Produces: `code_sortie(verdict: str) -> int`

- [ ] **Step 1: Ajouter les trois fonctions**

À placer avant `main()` :

```python
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
```

---

### Task 3: Réécrire `main()`

**Files:**
- Modify: `scripts/review_pr.py`

- [ ] **Step 1: Remplacer le corps de `main()`**

Remplacer tout ce qui suit `args = parser.parse_args()` par :

```python
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
```

- [ ] **Step 2: Mettre à jour la docstring de module**

Dans le bloc de docstring en tête de fichier, remplacer la phrase « demande une revue au LLM (rôle « revue », …), poste le résultat en commentaire sur la PR. » par une formulation qui dit aussi : verdict `ok`/`mineur`/`bloquant`, seul `bloquant` fait échouer la CI, 3 tentatives avec backoff, diff tronqué au-delà de `MAX_DIFF_CHARS` avec avertissement.

- [ ] **Step 3: Vérifier**

```bash
uv run ruff check scripts/review_pr.py
uv run python -c "import importlib.util,pathlib;s=importlib.util.spec_from_file_location('r',pathlib.Path('scripts/review_pr.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.code_sortie('bloquant'), m.code_sortie('mineur'), m.code_sortie('ok'))"
```
Attendu : `1 0 0`, ruff propre.

---

### Task 4: Test unitaire

**Files:**
- Create: `tests/unit/scripts/test_review_pr.py`

**Interfaces:** aucune — tests seulement. Aucun appel réseau, aucun appel LLM réel.

- [ ] **Step 1: Écrire le fichier de test**

Même convention de chargement que `test_clear_opquast_tables.py` (module chargé par chemin, `parents[3]`). Contenu attendu :

```python
"""
Tests unitaires de scripts/review_pr.py : ce qui décide de bloquer ou non la
CI. Aucun appel LLM ni HTTP réel — seul le comportement de décision est testé.
"""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tenacity import wait_none

CHEMIN = Path(__file__).resolve().parents[3] / "scripts" / "review_pr.py"

ROLE = {
    "modele": "kimi-k2.6",
    "env_var": "AZURE_MODEL_KIMI",
    "prix_entree_par_million": 0.8008,
    "prix_sortie_par_million": 3.3875,
}


@pytest.fixture
def script():
    spec = importlib.util.spec_from_file_location("review_pr_script", CHEMIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCodeSortie:
    """Seul un verdict « bloquant » fait échouer la CI."""

    def test_bloquant_fait_echouer(self, script):
        assert script.code_sortie("bloquant") == 1

    @pytest.mark.parametrize("verdict", ["ok", "mineur"])
    def test_le_reste_est_informatif(self, script, verdict):
        """Casse si une remarque mineure ferme la porte de dev."""
        assert script.code_sortie(verdict) == 0


class TestConstruireCorps:
    def test_annonce_la_troncature(self, script):
        """Casse si une revue partielle est postée sans le dire."""
        resultat = {"verdict": "mineur", "commentaire": "Rien de grave.", "cout_usd": 0.01}
        corps = script.construire_corps(resultat, ROLE, tronque=True)
        assert "Revue partielle" in corps
        assert str(script.MAX_DIFF_CHARS) in corps

    def test_pas_d_avertissement_sans_troncature(self, script):
        resultat = {"verdict": "ok", "commentaire": "RAS.", "cout_usd": 0.01}
        corps = script.construire_corps(resultat, ROLE, tronque=False)
        assert "Revue partielle" not in corps
        assert "kimi-k2.6" in corps


class TestInvoquerLlm:
    """Retry : 3 tentatives, la réponse hors format est retentée."""

    def _parser(self, resultats):
        parser = MagicMock()
        parser.parse.side_effect = resultats
        return parser

    def test_retente_puis_reussit(self, script):
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(
            content="peu importe", usage_metadata={"input_tokens": 10, "output_tokens": 5}
        )
        parser = self._parser(
            [ValueError("pas du JSON"), {"verdict": "ok", "commentaire": "RAS."}]
        )
        sans_attente = script.invoquer_llm.retry_with(wait=wait_none())
        parsed, usage = sans_attente(llm, parser, "prompt")
        assert parsed["verdict"] == "ok"
        assert parser.parse.call_count == 2
        assert usage["input_tokens"] == 10

    def test_abandonne_apres_trois_tentatives(self, script):
        """Casse si le script insiste au-delà de 3 essais (coût) ou renonce avant."""
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content="x", usage_metadata={})
        parser = self._parser([ValueError("pas du JSON")] * 3)
        sans_attente = script.invoquer_llm.retry_with(wait=wait_none())
        with pytest.raises(ValueError):
            sans_attente(llm, parser, "prompt")
        assert parser.parse.call_count == 3


class TestCorpsEchec:
    def test_dit_que_la_ci_n_est_pas_bloquee(self, script):
        """Casse si une panne de l'outil se met à ressembler à un verdict."""
        corps = script.construire_corps_echec(RuntimeError("Azure indisponible"))
        assert "non aboutie" in corps
        assert "Azure indisponible" in corps
```

- [ ] **Step 2: Vérifier**

```bash
uv run pytest tests/unit/scripts/test_review_pr.py -v
uv run pytest tests/unit -q
uv run ruff check
```
Attendu : les nouveaux tests passent, le total unitaire passe de 291 à 300, ruff propre.

**Vérifié en amont** : tenacity 9.1.4 est installé et `retry_with` est bien disponible sur une fonction décorée — les deux tests de retry tournent sans attente réelle. Rien à adapter.

---

### Task 5: Documenter le script dans `scripts/CLAUDE.md`

**Files:**
- Modify: `scripts/CLAUDE.md`

- [ ] **Step 1: Ajouter l'entrée**

Dans la liste `## Fichiers`, à la suite des autres, ajouter une ligne dans le style des existantes :

```markdown
- **`review_pr.py`** : revue automatisée du diff d'une PR par LLM, postée en commentaire (Gitea ou GitHub, `--host`). Rend un verdict `ok`/`mineur`/`bloquant` ; seul `bloquant` fait échouer la CI. Outil d'ops, pas de logique métier applicative — même exception que `create_api_regles_key.py`. Appelé par `ci-review.yml`. Rôle LLM et tarifs : `scripts/review_pr_config.yml`. Décisions : `conception/4_ci_cd/strategie_tests_et_gates.md`. Tests : `tests/unit/scripts/`.
```

---

### Task 6: Resserrer le déclencheur de `ci-acceptance.yml`

**Files:**
- Modify: `.gitea/workflows/ci-acceptance.yml`

- [ ] **Step 1: Remplacer le filtre de tags**

Remplacer :

```yaml
on:
  push:
    tags:
      - "**"
```

par :

```yaml
on:
  push:
    tags:
      # Format décidé : YYYY-MM-DD-<sha7>. Filtre resserré pour qu'un tag
      # d'une autre nature (doc, release) ne déclenche pas d'appels LLM et
      # d'embeddings réels payants. Actions ne supporte que les globs, pas
      # les expressions régulières : le préfixe date suffit à écarter les
      # tags d'une autre nature.
      - "20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*"
```

- [ ] **Step 2: Vérifier**

```bash
uv run python -c "import yaml,pathlib; print(yaml.safe_load(pathlib.Path('.gitea/workflows/ci-acceptance.yml').read_text())[True])"
```
(`on` est lu comme le booléen `True` par PyYAML — c'est normal.) Attendu : le dict contient `push.tags` avec le glob, et le YAML reste valide.

---

### Task 7: Tracer dans le CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Ajouter une entrée**

En tête de la section `## 2026-09-20 — Claude Code` (les entrées les plus récentes en premier), ajouter :

```markdown
- **Revue automatisée de PR par LLM (carte #45)** — `scripts/review_pr.py` :
  récupère le diff `origin/<base>...HEAD`, le fait relire par le LLM (rôle
  `revue`, `scripts/review_pr_config.yml`, même déploiement Azure que
  l'enrichissement) et poste le résultat en commentaire sur la PR. Écarté :
  le Claude Code GitHub Action officiel (authentification OIDC GitHub
  uniquement, incompatible Gitea). Workflows `ci-review.yml` ajoutés sur les
  deux hébergeurs (`pull_request` vers `dev`), ainsi que les miroirs GitHub
  de `ci-feature.yml`/`ci-dev.yml` — la CI tourne sur Gitea **et** GitHub
  jusqu'à `dev` inclus, au-delà (tag, staging) reste Gitea.
  **Durcissement après revue à froid (Opus)** : verdict structuré
  `ok`/`mineur`/`bloquant` — seul `bloquant` fait échouer la CI, toute panne
  de l'outil (réponse hors format, LLM injoignable, diff tronqué) reste non
  bloquante ; retry 3 tentatives avec backoff exponentiel (règle projet, qui
  manquait) ; coût de chaque revue calculé et affiché dans le commentaire
  (`modele` et tarifs du config, jusque-là morts) ; diff au-delà de 60 000
  caractères désormais tronqué avec avertissement au lieu de faire échouer la
  CI ; 9 tests unitaires dans `tests/unit/scripts/test_review_pr.py`.
  Déclencheur de `ci-acceptance.yml` resserré de `tags: '**'` au préfixe
  `YYYY-MM-DD-*` (tout tag déclenchait sinon des appels LLM payants).
  Décisions : `conception/4_ci_cd/strategie_tests_et_gates.md`, plan :
  `docs/superpowers/plans/2026-09-20-revue-pr-llm-implementation.md`.
  **Défaut connu non corrigé, différé après la carte #32 (C4,
  authentification)** : le garde-fou de tag de `cd-staging.yml`
  (`git describe --tags --exact-match`) porte sur le SHA de `staging`, qui
  diffère du SHA tagué sur la branche feature si le merge n'est pas
  fast-forward — il refuserait alors tout déploiement. Sans effet d'ici là,
  rien ne se déployant sur staging avant #32.
```

Ajuster le nombre de tests (« 9 tests unitaires ») au compte réel obtenu à la tâche 4.

---

### Task 8: Vérification finale

- [ ] **Step 1: Lancer la chaîne complète**

```bash
uv run ruff check
uv run pytest tests/unit tests/integration -q
```
Attendu : ruff propre, aucun test en échec, aucune régression par rapport au compte d'avant (291 unitaires).

- [ ] **Step 2: Vérifier qu'aucun fichier hors périmètre n'a bougé**

```bash
git status --short
```
Attendu, exactement : `conception/4_ci_cd/strategie_tests_et_gates.md`, `CHANGELOG.md`, `scripts/CLAUDE.md`, `scripts/review_pr.py`, `scripts/review_pr_config.yml`, `tests/unit/scripts/test_review_pr.py`, `.gitea/workflows/` (dont `ci-acceptance.yml` et `ci-review.yml`), `.github/`, `tests/fixtures/`, `tests/mesures/mesure_rag_dense.py`, `docs/superpowers/plans/2026-09-20-revue-pr-llm-implementation.md`. **`cd-staging.yml` ne doit pas apparaître comme modifié dans cette session.**

- [ ] **Step 3: Ne pas committer sans accord**

Grouper les changements et proposer le commit à David (règle projet : pas de commit à chaque micro-modification, pas de `git push` sans autorisation explicite au moment T).
