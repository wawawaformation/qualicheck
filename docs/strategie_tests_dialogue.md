# Stratégie de tests : atelier de définitions (carte Kanboard #45)

Document de travail, tenu **au fur et à mesure** par Claude : chaque échange utile y est noté, pour qu'une nouvelle session ou un autre outil (OpenCode...) reprenne sans rien perdre. Démarré le 2026-09-20 à 15h37.

## Comment reprendre (à lire en premier)

1. Lire ce document jusqu'à « État d'avancement ».
2. Règles de travail avec David : **valider à chaque étape**, **chrono lancé** dès qu'on travaille sur une carte, **aucune carte créée sans demande**, **ne rien supprimer sans accord explicite**, carte terminée = **Done sans la fermer** (voir `docs/agent/02_regles_execution.md`).
3. Ne **pas** proposer de définition avant que David ait écrit la sienne (voir « Méthode »).

## Objectif

Se mettre d'accord sur le vocabulaire (test unitaire, test d'intégration, à quoi ils servent) avant de parler de CI, de mocks et de mesures. David veut « fixer ça dans le marbre, en toute conscience », même pour ce qui est déjà écrit, puis le schématiser et le documenter pour que **n'importe quel agent** le lise.

Pourquoi c'est important pour David : sa mémoire de travail humaine est limitée (loi de Miller) et chaque carte a ses tests et ses mesures ; il faut être au clair sur les stratégies de tests et les métriques.

## Méthode (décidée par David)

1. **David définit** unitaire et intégration, et à quoi ils servent.
2. **Claude définit** les mêmes notions, sans avoir influencé David.
3. **Ensemble** : accords, écarts, ce qui manque ; un vocabulaire commun en sortie.
4. **David montre un schéma** ; Claude le lit, signale les incohérences, n'invente rien.
5. **« On avise »** : on décide ensuite de la suite (CI, mocks, mesures, collection Bruno).

## État d'avancement

| # | Temps | État |
|---|---|---|
| 1 | David définit | **unitaire reçu** ; intégration en attente |
| 2 | Claude définit | pas commencé, volontairement |
| 3 | Mise en commun | à faire |
| 4 | Schéma de David | à faire |
| 5 | On avise | à faire |

Kanboard : carte #45 « En cours » depuis le 2026-09-20 15h37, estimée 7,5 h. Trois sous-tâches : (1) définir unitaire et intégration, chrono lancé ; (2) lire et rendre cohérent le schéma de David ; (3) cadrer la suite, « on avise ».

## Définitions de David (mot pour mot)

### Test unitaire (2026-09-20, 15h47)

> un test unitaire.  test qu'un petit bout : un fichier, une classe par exemple. comme en se trouve peut-etre au milieu d'un tout, on peu utiliser des mocks ou des fixtures (je ne sais pas vraiment la différence)

### Test d'intégration

_En attente._

## Définitions de Claude

_À écrire seulement après celles de David._

## Glossaire (précisions données à David, à valider ensemble)

- **Mock** : un faux objet qui remplace une dépendance du code testé, pour l'isoler. Exemple du projet : `patch("app.agent_us2.tools.httpx.get")` remplace l'appel réseau ; on peut aussi vérifier comment il a été appelé.
- **Fixture** : la préparation réutilisable du décor d'un test (données, configuration, objets), fournie par pytest avec `@pytest.fixture`. Exemples du projet : `env_api` (pose l'URL de l'API), `llm` (remplace le modèle).
- Ce ne sont pas deux alternatives : une fixture est un **mécanisme de préparation** et peut contenir des mocks. Un mock est un faux objet, une fixture est ce qui prépare le test.

## Accords, écarts, manques

_À remplir à la mise en commun._

## Décisions

_Aucune pour l'instant._

## Constats factuels utiles (repérés dans la session, ne sont pas des définitions)

Ce que le dépôt contient aujourd'hui, pour situer la discussion :

- `tests/unit/` (mocks, sans réseau ni base), `tests/integration/` (dont des appels HTTP réels vers l'API des règles, et une base de test), `tests/migration/` (vise la vraie `POSTGRES_DB`, en lecture seule).
- `tests/acceptance/` : les jeux de données **et** 4 vérifications à appels réels (rangées là depuis la carte #44). `tests/mesures/` : 5 campagnes de mesure (elles produisent des chiffres, pas un vert ou rouge). Aucun n'est collecté par pytest (seuls les `test_*.py` le sont).
- CI Gitea `ci-dev.yml` : `ruff`, migrations, puis `pytest tests/unit tests/integration`. CD `cd-staging.yml` : mêmes tests avant déploiement, puis `make api-regles-acceptance` sur l'hôte de staging.
- Une collection Bruno `qualicheck` (hors dépôt, `~/Documents/bruno/qualicheck_data`) : 16 requêtes, API des règles et API business, en local. Rattachée à cette carte : la versionner comme niveau de preuve « HTTP de bout en bout » (jetons en clair à remplacer par des variables avant).
- Règle du projet : tout test destructif utilise `POSTGRES_TEST_DB`, jamais `POSTGRES_DB` (incident du 2026-07-25).
- Coût : les appels LLM réels sont payants (la régénération des 245 règles coûte un appel chacune) ; le pipeline LLM applique 3 retries avec backoff.
- Écart connu : la méthode de David parle de `tests/acceptation`, le dépôt a `tests/acceptance`.

## Journal du dialogue

- 2026-09-20 15h37 : David lance l'atelier (« d'abord moi, puis toi, puis ensemble ») ; Claude ouvre la carte #45, lance le chrono et crée ce document.
- 2026-09-20 15h47 : David définit le test unitaire (voir plus haut, mot pour mot) et demande la différence entre mock et fixture ; Claude répond (glossaire) sans donner sa propre définition du test unitaire.
