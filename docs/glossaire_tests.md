# Glossaire des tests et mesures (QualiCheck)

Convention retenue pour ce projet, actée le 2026-09-20 lors de l'atelier de
la carte Kanboard #45 (David + Claude). Ce n'est pas « LA » définition
universelle du vocabulaire — certains de ces mots ont des usages différents
ailleurs (ex. acceptance/e2e sont parfois synonymes dans d'autres équipes).
C'est la convention à laquelle se réfère QualiCheck, pour que tout agent
(Claude Code, OpenCode...) et tout humain sur le projet parlent le même
vocabulaire. Discussion complète et historique : `docs/strategie_tests_dialogue.md`.

## Test unitaire

Vérifie une seule unité de comportement (fonction, méthode, classe), isolée
de ses dépendances externes (mock au besoin). Rapide, déterministe, gratuit.

## Test d'intégration

Vérifie que plusieurs composants réels fonctionnent ensemble (ex. code +
vraie base de test, ou vrai appel HTTP interne), sans forcément couvrir tout
le parcours utilisateur. Deux variantes, à cause du coût/temps des LLM :

- **boîte noire** : le LLM est mocké, on teste le câblage (l'assemblage),
  pas ce que le LLM décide ou produit.
- **réel** : rare en intégration ; dès qu'un LLM est réellement appelé, le
  test bascule en pratique côté acceptance (coût, non-déterminisme).

## Test de bout en bout

Parcourt le chemin complet côté utilisateur, sans mock nulle part sur ce
chemin. Cas particulier de test d'intégration (tout bout en bout est une
intégration, l'inverse n'est pas vrai) — pas un synonyme, malgré un usage
confondu ailleurs.

## Test d'acceptance

Vérifie qu'un critère métier est satisfait (verdict pass/fail), au sens
BDD/Gherkin. Dans QualiCheck il implique en pratique des appels réels (LLM,
embeddings) — par nécessité (impossible de juger un critère métier avec un
LLM mocké dont on décide déjà la réponse), pas par définition stricte du
mot. Pas de dossier `tests/e2e/` séparé : `tests/acceptance/` en tient lieu
tant qu'aucun besoin concret de parcours complet sans critère métier
n'apparaît.

## Mesure

Script/campagne qui produit des **métriques** pour éclairer une décision
(ex. comparer plusieurs `top_n` de retrieval). Pas de verdict pass/fail — à
la différence d'un test d'acceptance. Dès qu'un seuil est fixé dessus pour
bloquer un pipeline, elle devient de fait un test d'acceptance avec critère
chiffré (voir `conception/4_ci_cd/`).

## Métrique

La valeur chiffrée produite par une mesure (ex. « recall@10 = 0,82 »,
« taux de refus = 92 % »).

## Mock

Un faux objet qui remplace une dépendance du code testé, pour l'isoler
(ex. `patch("app.agent_us2.tools.httpx.get")`).

## Fixture

La préparation réutilisable du décor d'un test (données, configuration,
objets), fournie par pytest (`@pytest.fixture`). Peut contenir des mocks ;
ce n'est pas une alternative au mock, mais le mécanisme qui le met en place.

## Recette (UAT)

Équivalent anglais **UAT** ("User Acceptance Testing"), parfois
**bêta-test** avec des utilisateurs pilotes/externes. Vérification
**humaine**, visuelle, sur un **environnement de recette** réellement
déployé (`staging` dans QualiCheck), avant passage en prod. UAT désigne
plus précisément la recette faite par l'utilisateur/le métier (ex. Élie
Sloïm) ; "recette" en français couvre aussi une recette technique faite par
l'équipe dev elle-même. « Livrer en recette » = déployer sur cet
environnement de vérification, **pas** livrer en production (confusion
fréquente). À ne pas confondre avec le test d'acceptance (automatisé, sans
humain) : le mot anglais "acceptance testing" recouvre parfois les deux à
la fois ailleurs, mais ce sont deux choses différentes dans QualiCheck.

## Dérive

Concept identifié, hors périmètre de la carte #45 (carte Kanboard #49,
priorité basse) : évolution non désirée d'une métrique dans le temps (ex.
baisse de recall après un changement d'embedding), détectée en rejouant une
mesure régulièrement et en comparant à un historique — par opposition à une
mesure ponctuelle, qui ne sert qu'une fois.
