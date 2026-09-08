"""Tests du parseur de grammaire de recherche (GET /regles?q=)."""

from app.api_regles.recherche import parse_recherche


def test_un_seul_mot_forme_un_groupe_dun_terme():
    resultat = parse_recherche("foo")

    assert resultat.groupes == [["foo"]]
    assert resultat.exclusions == []


def test_deux_mots_forment_un_et_de_deux_groupes():
    resultat = parse_recherche("a b")

    assert resultat.groupes == [["a"], ["b"]]


def test_espaces_multiples_sont_ignores():
    resultat = parse_recherche("a    b")

    assert resultat.groupes == [["a"], ["b"]]


def test_phrase_entre_guillemets_est_un_seul_terme():
    resultat = parse_recherche('"multi mot"')

    assert resultat.groupes == [["multi mot"]]


def test_terme_negatif_va_dans_les_exclusions():
    resultat = parse_recherche("-foo")

    assert resultat.groupes == []
    assert resultat.exclusions == ["foo"]


def test_phrase_negative_entre_guillemets():
    resultat = parse_recherche('-"multi mot"')

    assert resultat.exclusions == ["multi mot"]


def test_or_forme_un_seul_groupe_de_deux_termes():
    resultat = parse_recherche("a OR b")

    assert resultat.groupes == [["a", "b"]]


def test_or_se_chaine_sans_parentheses():
    resultat = parse_recherche("a OR b OR c")

    assert resultat.groupes == [["a", "b", "c"]]


def test_or_suivi_dune_exclusion_est_ignore():
    """Pas de « OR d'exclusion » : le OR est abandonné, -b reste une exclusion normale."""
    resultat = parse_recherche("a OR -b")

    assert resultat.groupes == [["a"]]
    assert resultat.exclusions == ["b"]


def test_guillemet_non_ferme_prend_jusqua_la_fin_de_la_chaine():
    resultat = parse_recherche('foo "bar baz')

    assert resultat.groupes == [["foo"], ["bar baz"]]


def test_requete_vide_ne_produit_rien():
    resultat = parse_recherche("")

    assert resultat.groupes == []
    assert resultat.exclusions == []


def test_requete_uniquement_des_espaces_ne_produit_rien():
    resultat = parse_recherche("   ")

    assert resultat.groupes == []
    assert resultat.exclusions == []


def test_or_isole_sans_terme_precedent_est_un_terme_litteral():
    """Pas de terme positif avant lui : OR est traité comme un mot de recherche normal."""
    resultat = parse_recherche("OR foo")

    assert resultat.groupes == [["OR"], ["foo"]]


def test_et_et_or_se_combinent():
    resultat = parse_recherche("a OR b c")

    assert resultat.groupes == [["a", "b"], ["c"]]
