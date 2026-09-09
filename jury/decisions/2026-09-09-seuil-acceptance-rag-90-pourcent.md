# Seuil d'acceptance RAG : 80% → 90%, garde-fou régression

2026-09-09 · retenu

## Contexte

`taux_reussite_minimum: 0.8` (`app/ingestion/manifest.yml`, section
`rag_acceptance`) a été fixé le 2026-07-26 (commit `2a0bf1d`) en renvoyant
vers `jury/decisions/2026-07-25-rag-us2-petit-corpus.md`, qui justifie le
**principe** d'accepter un rappel imparfait du RAG sémantique — mais ne
dérive nulle part le chiffre **80%** lui-même. Contrairement à `top_n=3`
(justifié à l'époque par une observation concrète : « top 2 observé lors
des vérifications manuelles »), 80% était un seuil rond choisi au doigt
mouillé.

Repéré en creusant pourquoi `multi_sujets` était historiquement compris
sous ce seuil (67% à `top_n` bas), question posée par David en relisant
un rapport de mesure : « pourquoi on a fixé le seuil à 80% ? ».

## Ce que la mesure établit aujourd'hui

Avec 99 cas / 7 familles (`tests/acceptance/rag_acceptance.jsonl`) et le
mécanisme de décomposition multi-sujets (`app/retrieval/`), les taux
mesurés par famille à `top_n=10` :

| Famille | Taux |
|---|---|
| paraphrase_intitule | 100% |
| vocabulaire_source_opquast | 100% |
| vocabulaire_genere_llm | 95% |
| multi_sujets | 100% |
| regles_concurrentes | 100% |
| vocabulaire_objectif | 92% |

Un seuil à 80% laisse 10 à 20 points de dégradation possibles sur chaque
famille avant qu'un run `make rag-acceptance` échoue — largement au-delà
du bruit normal (1-2 cas isolés) observé jusqu'ici.

## Options envisagées

**Garder 80%** — pour : aucun changement, aucun risque de casser un run
existant. Contre : ne détecte une régression réelle qu'une fois qu'elle
est déjà sévère (10+ points de perte sur une famille), pas au moment où
elle apparaît.

**90% (retenu)** — pour : colle aux taux réellement mesurés aujourd'hui
avec une marge de sécurité raisonnable (quelques points), détecte une
régression bien plus tôt. Cohérent avec le rôle du seuil tranché par
David : garde-fou technique (attraper une régression), pas barre de
qualité produit (ce que l'utilisateur final d'US2 peut tolérer — question
distincte, non tranchée ici, pas encore pertinente tant qu'US2 n'est pas
conçue). Contre : plus sensible sur les familles à petit effectif
(`regles_concurrentes` = 7 cas, `multi_sujets` = 4 cas) — un seul cas en
échec y fait chuter le taux sous 90% (85,7% et 75% respectivement).
Accepté comme voulu : plus l'échantillon est petit, plus un seuil serré
est le comportement recherché pour un garde-fou.

**Barre de qualité produit dérivée d'une exigence métier** — écarté pour
l'instant : suppose de savoir ce qu'un utilisateur final d'US2 tolère
comme taux d'erreur de retrieval, question qui n'a de sens qu'une fois
US2 conçue en détail (`conception/3_autre_us/us2_question_libre/`,
`harness/` encore vide). Prématuré.

## Décision

`taux_reussite_minimum` passe de `0.8` à `0.9` dans `manifest.yml`. Rôle
explicité en commentaire : garde-fou de non-régression technique, pas
barre de qualité produit — à rouvrir si/quand US2 est conçue en détail et
qu'une exigence métier sur le taux d'erreur tolérable existe.

## Conséquences

- `manifest.yml` : commentaire mis à jour avec ce rationnel, renvoi vers
  ce document plutôt que vers `2026-07-25-rag-us2-petit-corpus.md` seul.
- Aucun changement de code, aucun test à modifier — `make rag-acceptance`
  passe toujours avec les données actuelles (marge confirmée par le
  tableau ci-dessus).
- Si un run futur échoue à 90% sur une famille jusque-là verte, c'est un
  signal à traiter comme une vraie régression, pas du bruit — ne pas
  remonter le seuil pour faire passer un échec sans comprendre sa cause.
