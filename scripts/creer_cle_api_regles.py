"""
Automatise la création d'un nouveau client API pour /regles (dev + staging).

Procédure manuelle de référence :
docs/developpement/creation_cle_api_regles.md

Modifie 4 emplacements et crée un secret GitHub réel dans l'environnement
"staging" — pas une simulation. Usage :

    uv run python scripts/creer_cle_api_regles.py <nom-client>
"""

import re
import secrets
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
MANIFEST = RACINE / "app" / "api_regles" / "manifest.yml"
ENV = RACINE / ".env"
ENV_EXAMPLE = RACINE / ".env.example"
WORKFLOW = RACINE / ".github" / "workflows" / "cd-staging.yml"


def variable_env(nom: str) -> str:
    """Dérive le nom de variable d'environnement depuis le nom de client."""
    return "FASTAPI_API_KEY_" + nom.upper().replace("-", "_")


def valider_nom(nom: str) -> None:
    """Refuse un nom qui ne serait pas du kebab-case (même convention que les clients existants)."""
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nom):
        raise SystemExit(
            f"Nom de client invalide : « {nom} » (attendu : kebab-case, ex. jean-dupont)"
        )


def inserer_dans_manifest(chemin_manifest: Path, nom: str, var: str) -> None:
    """
    Ajoute le client à la fin du bloc `clients:` du manifeste.

    Insertion par position (après la dernière ligne `env_var_token:`) plutôt
    que par parsing YAML : un round-trip PyYAML supprimerait tous les
    commentaires du fichier, qui portent l'essentiel de sa justification.
    """
    contenu = chemin_manifest.read_text(encoding="utf-8")
    if re.search(rf"^\s*-\s*nom:\s*{re.escape(nom)}\s*$", contenu, re.MULTILINE):
        raise SystemExit(f"Le client « {nom} » existe déjà dans {chemin_manifest}")

    correspondances = list(re.finditer(r"^    env_var_token: \S+$", contenu, re.MULTILINE))
    if not correspondances:
        raise SystemExit(f"Bloc clients: introuvable dans {chemin_manifest}")

    position = correspondances[-1].end()
    nouveau_bloc = f"\n  - nom: {nom}\n    env_var_token: {var}"
    chemin_manifest.write_text(
        contenu[:position] + nouveau_bloc + contenu[position:], encoding="utf-8"
    )


def ajouter_ligne_apres_dernier_fastapi(chemin: Path, nouvelle_ligne: str) -> None:
    """Insère `nouvelle_ligne` juste après la dernière ligne mentionnant FASTAPI_API_KEY."""
    lignes = chemin.read_text(encoding="utf-8").splitlines(keepends=True)
    indices = [i for i, ligne in enumerate(lignes) if "FASTAPI_API_KEY" in ligne]
    if not indices:
        raise SystemExit(f"Aucune ligne FASTAPI_API_KEY dans {chemin}")
    dernier = indices[-1]
    if not lignes[dernier].endswith("\n"):
        lignes[dernier] += "\n"  # sinon la ligne insérée se soude à celle-ci (ex. .env sans fin de ligne)
    lignes.insert(dernier + 1, nouvelle_ligne)
    chemin.write_text("".join(lignes), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage : uv run python scripts/creer_cle_api_regles.py <nom-client>")

    nom = sys.argv[1]
    valider_nom(nom)
    var = variable_env(nom)
    jeton = secrets.token_urlsafe(32)

    inserer_dans_manifest(MANIFEST, nom, var)
    print(f"[ok] {MANIFEST.relative_to(RACINE)} : client « {nom} » ajouté ({var})")

    ajouter_ligne_apres_dernier_fastapi(
        ENV_EXAMPLE, f'{var}=  # secret : token Bearer du client "{nom}"\n'
    )
    print(f"[ok] {ENV_EXAMPLE.relative_to(RACINE)} : ligne ajoutée")

    if ENV.exists():
        ajouter_ligne_apres_dernier_fastapi(ENV, f"{var}={jeton}\n")
        print(f"[ok] {ENV.relative_to(RACINE)} : jeton ajouté")
    else:
        print(f"[!] {ENV} absent — à ajouter manuellement : {var}={jeton}")

    ajouter_ligne_apres_dernier_fastapi(WORKFLOW, f"          {var}=${{{{ secrets.{var} }}}}\n")
    print(f"[ok] {WORKFLOW.relative_to(RACINE)} : ligne ajoutée")

    resultat = subprocess.run(
        ["gh", "secret", "set", var, "--env", "staging", "--body", jeton],
        cwd=RACINE,
        capture_output=True,
        text=True,
    )
    if resultat.returncode == 0:
        print(f"[ok] Secret GitHub « {var} » créé dans l'environnement staging")
    else:
        print(f"[!] Échec de la création du secret GitHub : {resultat.stderr.strip()}")
        print(f"    À faire manuellement : gh secret set {var} --env staging --body <jeton>")

    print()
    print(f"Jeton généré pour « {nom} » : {jeton}")
    print("Reste à faire :")
    print("  1. Relire les diffs (manifest.yml, .env.example, workflow)")
    print("  2. Redémarrer l'API locale : make api-regles (ou docker compose restart api-regles)")
    print("  3. Committer manifest.yml + .env.example + le workflow, merger jusqu'à staging")


if __name__ == "__main__":
    main()
