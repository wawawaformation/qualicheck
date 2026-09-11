# Fiche — Protocole de mesure des chunks retrieval : vagues 1 et 2, conclusion

Support de préparation orale (E2/E3). Répond à la question « comment le
texte vectorisé (le chunk) de chaque règle Opquast a-t-il été choisi ? ».
Sources : [app/ingestion/chunking.py](../../../app/ingestion/chunking.py),
[app/ingestion/rag_acceptance.py](../../../app/ingestion/rag_acceptance.py),
`docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md`,
`docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md`,
`docs/eval/mesure_variantes_chunks_2026-09-11_094703.md`,
`docs/eval/mesure_combinaisons_chunks_2026-09-11_191321.md`.

## 1. Pourquoi mesurer plutôt que choisir au jugé

Le chunk vectorisé de chaque règle (`build_chunk_text()`, 9 champs :
intitulé, thème, contexte, solution, controle, guide d'analyse,
objectifs, tags, phases) est **la matière première d'US2** : un mauvais
choix de chunk condamne tout ce qui viendra dessus, quelle que soit la
qualité du reste du pipeline. Un test ad hoc pendant le chantier du
mécanisme de refus (voir `fiche-rag-similarite-cosinus.md` §4.1) avait
montré qu'un chunk réduit à l'intitulé seul donne des scores très
différents du chunk complet sur les mêmes faux positifs (0.28-0.33 contre
0.53) — signal fort que le choix du texte a un impact direct, jamais
mesuré systématiquement jusque-là.

Un protocole a donc été conçu **avant** de tester quoi que ce soit, avec
quatre exigences fixées d'avance :

1. **Métriques graduées** (MRR, recall@k) plutôt que le verdict binaire
   PASS/FAIL — un verdict binaire plafonne les chunks riches à 95-100 %
   et les rend indiscernables.
2. **Jeu de validation réservé**, tiré et figé avant de comparer quoi que
   ce soit, jamais utilisé pour arbitrer entre les candidats — seulement
   pour confirmer le gagnant.
3. **Critère de décision écrit avant de voir les chiffres** — le
   garde-fou anti-doigt-mouillé.
4. **Biais du jeu de cas assumé** : les 114 questions d'acceptance ont
   été écrites en connaissant la règle cible (paraphrase ou vocabulaire
   piochés dans la règle elle-même) — bon score sur ce jeu ne veut pas
   dire bon sur de vraies questions d'auditeurs. Limite documentée, pas
   traitée par ce protocole.

## 2. Vague 1 (exploratoire) : quel champ porte quel signal, isolément

Les 11 champs de la règle mesurés **un par un** (plus le chunk complet
comme référence), sur 114 cas d'acceptance, MRR et recall@k par famille
de question. Coût réel : 0,0130 €.

Résultat en trois profils, expliqués par la **cardinalité** du champ
(nombre de valeurs distinctes pour 245 règles), pas par sa structure de
donnée :

| Champ | Cardinalité | Signal isolé |
|---|---|---|
| `phase` | 3 valeurs (118 règles/valeur) | quasi nul |
| `tag` | 6 valeurs (49 règles/valeur) | quasi nul |
| `theme` | 14 valeurs (18 règles/valeur) | quasi nul |
| `intitule`, `guide_analyse` | texte libre, riche | fort et **généraliste** (bon sur presque toutes les familles) |
| `objectifs` | 491 valeurs (1,3 règle/valeur) | fort mais **spécialiste** : bat même la baseline sur sa famille cible (`vocabulaire_objectif`, MRR 0.851 vs 0.664) mais faible ailleurs (0.28-0.52) |

`theme`/`tags`/`phases` viennent pourtant de tables de référence, comme
`objectifs` — la différence n'est pas la structure de la donnée (table à
côté vs texte libre), c'est la **richesse lexicale distincte par règle**.
Aucune variante isolée ne bat la baseline de façon générale : cette vague
était volontairement exploratoire, elle n'appliquait pas encore les
points 2 et 3 du protocole (réservés à la vague qui choisit pour de
vrai).

## 3. Vague 2 (décisionnelle) : des combinaisons, avec critère écrit d'avance

Cinq combinaisons de champs construites à partir des enseignements de la
vague 1, plus le chunk de production comme candidat à part entière (il
peut gagner = ne rien changer) :

| Candidat | Champs | Question posée |
|---|---|---|
| A — chunk épuré | intitulé+contexte+solution+controle+guide_analyse+objectifs | retirer les champs à cardinalité nulle dégrade-t-il ? |
| B — duo généraliste | intitulé+guide_analyse | approche-t-il la baseline en plus court ? |
| C — duo+spécialiste | intitulé+guide_analyse+objectifs | comble-t-il le trou `vocabulaire_objectif` sans bruit ? |
| D — source Opquast seule | baseline moins guide_analyse | l'enrichissement LLM sert-il vraiment, ou la richesse vient-elle du texte source ? |
| E — enrichissement seul | guide_analyse+strategie_justification | symétrique de D |

**Critère de décision, écrit avant de lancer la mesure** :
1. Calculer le MRR moyen non pondéré entre familles sur un jeu
   d'exploration (76 cas, ~2/3 des 114).
2. Éliminer tout candidat qui régresse **strictement** en dessous de la
   baseline sur **au moins une famille** — plancher relatif, pas de
   marge de tolérance.
3. Le survivant au MRR moyen le plus haut est le gagnant provisoire.
4. Le valider sur un jeu réservé (38 cas, jamais utilisé jusque-là,
   tiré par stratification par famille et figé dans
   `tests/acceptance/rag_acceptance_holdout.json`) : s'il y bat la
   baseline, il devient le choix retenu ; sinon on garde le chunk actuel.

**Résultat (2026-09-11, coût réel 0,0174 €) : les 5 candidats sont tous
éliminés à l'étape 2** — chacun régresse sur au moins une famille du jeu
d'exploration par rapport au chunk de production :

- `A_chunk_epure` perd sur `vocabulaire_objectif` (MRR 0.688 vs 0.741
  baseline) — retirer `theme`/`tags`/`phases` ne coûtait rien en soi,
  mais réduire le texte global déplace aussi le vecteur sur d'autres
  familles.
- `E_enrichissement_seul` s'effondre sur `vocabulaire_objectif` (0.303)
  et sur `multi_sujets`/`regles_concurrentes` (0.556/0.500) — le texte
  source Opquast (`intitule`, `objectifs`...) porte une part du signal
  que l'enrichissement seul ne remplace pas.
- Même les deux candidats les plus proches de la baseline (`C`, `D`)
  perdent chacun sur au moins une famille : aucune combinaison ne
  domine partout.

**Gagnant provisoire : la baseline elle-même** (aucun survivant à
départager) → validée trivialement sur le jeu réservé → **choix retenu :
le chunk de production actuel, aucun changement.**

## 3bis. Vague 3 : une architecture différente, même conclusion

La vague 2 ne teste qu'une hypothèse : quel texte mettre dans **un seul**
vecteur par règle. Une idée distincte, proposée après coup : **plusieurs
vecteurs séparés par règle** (chunk complet + intitulé seul +
guide_analyse seul), cherchés indépendamment à la requête et fusionnés en
gardant le meilleur score — pas un texte combiné (déjà testé et écarté :
candidat B de la vague 2).

Réutilise le jeu réservé et le critère de décision de la vague 2 sans les
redéfinir — seule la vague qui *choisit* doit poser ce garde-fou, pas
chaque nouvelle idée testée derrière. Coût réel 0,0114 €.

**Résultat : le candidat à 3 vecteurs est éliminé** — régresse sur au
moins une famille du jeu d'exploration vs la baseline. Confirmé sous un
second angle (recall@5 global, sans passer par une moyenne de MRR) :
baseline 0,921 (exploration) / 0,903 (réservé) contre 0,889 / 0,839 pour
le multi-vecteurs — l'écart tient sur les deux sous-ensembles, pas un
artefact du bruit de mesure. **Choix retenu : le chunk unique actuel,
aucun changement** — deux architectures différentes (texte combiné,
multi-vecteurs), la même conclusion mesurée.

## 4. L'argument à ne pas perdre à l'oral

La compétence démontrée n'est pas d'avoir amélioré le chunk — c'est
d'avoir **mesuré avant de changer quoi que ce soit**, avec un critère
écrit d'avance, et d'avoir accepté que la mesure ne confirme aucune des
6 hypothèses envisagées (5 combinaisons + le multi-vecteurs). Un chunk
qui survit à six tentatives d'amélioration mesurées et documentées, sous
deux architectures différentes, est une conclusion défendable ; un chunk
jamais interrogé ne l'aurait pas été. La vague 3 (affinage des têtes de
série de la vague 2) devient sans objet — il n'y a pas de tête de série à
affiner ; la vague 3 bis (multi-vecteurs) répond à une hypothèse
distincte et conclut de la même façon.

**Conséquence pour la suite** : le Temps 2 du mécanisme de refus
(jugement LLM sur les chunks retournés, voir `fiche-rag-similarite-cosinus.md`
§4.1), qui attendait la conclusion de ce protocole, a repris sur la base
du chunk actuel (inchangé) — voir cette même fiche pour son résultat et
la découverte architecturale qui en a suivi (guardrail de périmètre).
