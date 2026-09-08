"""Parseur de la grammaire de recherche de GET /regles?q=.

Grammaire (validée avec David le 2026-09-08, voir CHANGELOG.md) :
    mot1 mot2        -> ET implicite (chaque terme doit matcher un champ)
    "plusieurs mots" -> un seul terme, phrase exacte (espaces compris)
    -terme           -> exclusion, le terme ne doit apparaître dans aucun champ
    terme1 OR terme2 -> union, chaînable (a OR b OR c), sans parenthèses

Pas de portée au-delà de cette grammaire : ni groupes imbriqués, ni OR
d'exclusion (« a OR -b » abandonne le OR, -b reste une exclusion normale).
"""

from dataclasses import dataclass, field


@dataclass
class RechercheParsee:
    """AND de groupes ; chaque groupe est un OR de termes. Plus les exclusions."""

    groupes: list[list[str]] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)


def _tokeniser(q: str) -> list[tuple[str, bool]]:
    """Termes bruts (texte, négatif) — les guillemets préservent les espaces."""
    tokens: list[tuple[str, bool]] = []
    i, n = 0, len(q)

    while i < n:
        while i < n and q[i].isspace():
            i += 1
        if i >= n:
            break

        negatif = False
        if q[i] == "-" and i + 1 < n:
            negatif = True
            i += 1

        if i < n and q[i] == '"':
            i += 1
            fin = q.find('"', i)
            if fin == -1:
                fin = n
            texte = q[i:fin]
            i = fin + 1
        else:
            debut = i
            while i < n and not q[i].isspace():
                i += 1
            texte = q[debut:i]

        if texte:
            tokens.append((texte, negatif))

    return tokens


def parse_recherche(q: str) -> RechercheParsee:
    resultat = RechercheParsee()
    dernier_groupe: list[str] | None = None
    ou_en_attente = False

    for texte, negatif in _tokeniser(q):
        if negatif:
            resultat.exclusions.append(texte)
            dernier_groupe = None
            ou_en_attente = False
            continue

        if texte == "OR" and dernier_groupe is not None:
            ou_en_attente = True
            continue

        if ou_en_attente and dernier_groupe is not None:
            dernier_groupe.append(texte)
        else:
            dernier_groupe = [texte]
            resultat.groupes.append(dernier_groupe)
        ou_en_attente = False

    return resultat
