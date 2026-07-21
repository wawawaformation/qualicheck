# Décisions structurantes

Un fichier par décision, nommé `AAAA-MM-JJ-sujet.md`.

## Pourquoi ces documents existent

Les specs de `conception/` enregistrent ce qui a été **décidé**. Le `CHANGELOG.md`
enregistre ce qui a été **réalisé**. `docs/problemes_rencontres/` enregistre les
problèmes **rencontrés**.

Aucun n'enregistre ce qui a été **envisagé puis écarté**. C'est pourtant là que se
lit un raisonnement : une décision seule peut avoir été prise au hasard ou copiée,
un arbitrage montre qu'on a pesé.

## Format

```markdown
# Titre

Date · état (retenu / révisé le … / abandonné)

## Contexte
Ce qui a amené la question. Les contraintes réelles, pas théoriques.

## Options envisagées
Chacune avec ce qui plaidait pour et ce qui plaidait contre.

## Décision
Ce qui a été retenu, et le critère qui a tranché.

## Conséquences
Ce que ça implique, y compris les limites assumées et ce qui reste ouvert.
```

Une décision révisée plus tard n'est **pas** réécrite : on ajoute une ligne d'état
et on crée un nouveau document. L'historique des changements d'avis a autant de
valeur que les décisions elles-mêmes.

## Décisions antérieures — où elles sont déjà justifiées

Ce dossier n'a été créé qu'en juillet 2026, alors que l'essentiel de la conception
était déjà fait. Les décisions prises avant **ne sont pas réécrites ici** : les
rédiger après coup produirait une reconstruction, moins fidèle que le document
d'origine. L'index ci-dessous y renvoie.

| Décision | Où elle est justifiée | Alternatives écartées consignées ? |
| --- | --- | --- |
| PostgreSQL + pgvector plutôt qu'une base vectorielle externe | `conception/conception.md` §Choix techniques | oui — Chroma et Pinecone nommés |
| Gestion du schéma par migrations (Alembic) | `conception/1_BDD/bdd.md` §Choix technique | oui — script SQL manuel nommé |
| Index HNSW, création avant remplissage | `conception/1_BDD/bdd.md` | partiellement |
| Choix des modèles LLM par usage | `conception/annexes/benchmark/` (16 820 appels, `benchmark.py`, `analyse_models_azure.pdf`) | oui — benchmark comparatif complet |
| Backend FastAPI, frontend Vue.js, Docker | `conception/conception.md` §Choix techniques | non — seule la justification du choix retenu figure |
| Embedding All MiniLM L12 v2, `vector(384)` figé | `conception/conception.md` | non |
| Souveraineté, éco-conception, éthique de l'IA | `conception/conception.md` §Positionnement éthique et technique | oui |
| Itérations du prompt d'enrichissement V1 → V3 | `docs/problemes_rencontres/ingestion/1_prompt_engineering.md` | oui — avec les chiffres qui ont motivé chaque révision |
| Dimensionnement des colonnes textuelles | `docs/problemes_rencontres/ingestion/2_schema_text_columns.md` | oui — trois approches comparées |
| Bornage du scraping, sérialisation des listes, champ `contexte` | `conception/2_ingestion/D_chantier1_scraping_contexte.md` §3 | oui — dont le refus d'une sentinelle mot-clé |
| Méthodologie spec-driven, `CHANGELOG.md` comme continuité entre outils | `CLAUDE.md` | oui |

**Lecture de la troisième colonne** : là où elle indique « non », seul le choix
retenu est documenté, pas ce qui a été écarté. Ce n'est pas rattrapable de façon
fiable aujourd'hui — mais c'est précisément ce que ce dossier évite de reproduire
pour les décisions à venir.

**Une synthèse manque** : `conception/conception.md` renvoie deux fois à
`annexes/F_choix_llm.md`, qui n'existe pas dans le dépôt. Le matériau du benchmark
est bien là, sa rédaction ne l'est pas — c'est du contenu directement exploitable
pour C7 qui reste invisible pour qui lirait le dépôt.
