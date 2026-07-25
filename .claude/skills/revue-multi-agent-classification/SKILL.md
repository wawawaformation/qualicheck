---
name: revue-multi-agent-classification
description: Audite en parallèle un grand jeu de données classifiées par LLM (ex. les 245 règles Opquast enrichies par le pipeline d'ingestion) à la recherche d'incohérences de diagnostic — plusieurs agents dispatchés sur des lots, consolidés dans un buffer puis un document final de recommandations.
---

# Revue multi-agent d'une classification LLM

Construite et validée sur QualiCheck le 2026-07-25, pour auditer les 245
règles ré-ingérées avec le prompt V4 (`app/ingestion/prompts/enrich_rule.md`)
— voir `docs/problemes_rencontres/ingestion/4_recommandations_v5.md` pour le
résultat concret produit avec cette méthode.

## Quand l'utiliser

Après une (ré-)ingestion réelle qui produit un grand nombre de lignes
classifiées par un LLM (ex. `strategie_analyse` sur `regle`), quand on veut
vérifier la cohérence des diagnostics **à l'échelle du jeu de données entier**
— pas seulement sur un échantillon lu à la main. Un seul agent ou une lecture
manuelle ne passe pas à l'échelle sur 200+ lignes sans perdre en profondeur
d'analyse par ligne ; le découpage en lots parallèles garde la profondeur tout
en couvrant l'ensemble.

## Étapes

### 1. Exporter les données à auditer

Requête SQL (ou export ORM) vers un JSON dans `tmp/`, avec tous les champs
nécessaires au jugement — pas seulement le résultat (`strategie_analyse`),
aussi la donnée source qui permet de le contester (`solution`, `controle`) et
le raisonnement produit (`strategie_justification`, `guide_analyse`).

```bash
psql ... -c "SELECT json_agg(row_to_json(t) ORDER BY t.numero) FROM (
  SELECT numero, intitule, strategie_analyse, strategie_justification,
         guide_analyse, solution, controle
  FROM regle
) t;" > tmp/toutes_regles_vX.json
```

### 2. Découper en lots

Un fichier JSON par lot (`tmp/audit_lot_1.json`, `_2.json`...). Taille
raisonnable : ~40-50 lignes par lot — assez pour donner du contexte à l'agent,
assez peu pour qu'il reste précis sur chaque ligne plutôt que de survoler.
Sur 245 lignes, 5 lots de 49 a bien fonctionné.

### 3. Dispatcher un agent par lot, en parallèle

Un seul message, plusieurs appels `Agent` (`subagent_type: general-purpose`)
— jamais en série, sinon le parallélisme ne sert à rien. Chaque prompt
d'agent doit être **auto-suffisant** (l'agent n'a aucun contexte de la
conversation) et contenir :

1. **Le contexte du domaine** : à quoi sert la donnée, quelles règles de
   classification sont en vigueur (ex. citer verbatim les critères actuels du
   prompt d'enrichissement).
2. **Un cas de calibrage** : un exemple déjà confirmé comme problématique
   (trouvé en revue manuelle avant le balayage), donné en exemple pour ancrer
   le niveau de rigueur attendu — sans qu'il soit dans le lot de l'agent.
3. **Les critères précis à chercher**, numérotés, pas un vague "trouve les
   problèmes". Ex. utilisés sur QualiCheck : classement `manuel` manqué,
   guide spéculatif plutôt que factuel, incohérence entre justification et
   guide, composite injustifié.
4. **Le chemin exact du fichier JSON** de son lot, et le format de réponse
   attendu (liste numéro + raison, pas un résumé vague).
5. **La consigne de confiance** : "ne remonte que des cas où tu es réellement
   confiant — pas de nitpicking". Sans cette phrase, les agents remontent
   trop de faux positifs sur du phrasé plutôt que du fond.

Squelette de prompt réutilisable :

```text
Contexte : [domaine + ce que représentent les champs du JSON]

Règles de classification en vigueur : [citer verbatim les critères actuels]

Exemple d'incohérence déjà repérée (calibrage, pas dans ton lot) : [cas confirmé]

Ta tâche : lis [chemin du lot]. Pour chaque ligne, cherche :
1. [critère 1]
2. [critère 2]
3. [critère 3]
...

Ne remonte que des cas où tu es réellement confiant — pas de nitpicking.
Réponds en français, concis : liste des cas à problème (identifiant + une
phrase expliquant le problème précis). Si aucun, dis-le clairement.
```

### 4. Consolider dans un buffer, au fil de l'eau

Un document "brouillon" (`docs/problemes_rencontres/.../N_recommandations_vX.md`,
même famille numérotée que les précédents), écrit progressivement à mesure
que les résultats des agents arrivent et que les décisions humaines se
prennent en discussion — pas d'un coup à la fin. Noter aussi le **pourquoi**
de chaque décision, pas seulement le constat, pour ne pas le reperdre plus
tard. Le format buffer (accumulation brute, consolidation différée) est
délibéré — voir `docs/problemes_rencontres/ingestion/1_prompt_engineering.md`
pour le précédent qui a inspiré cette méthode (démarche type
`ob_start`/`ob_get_clean`).

### 5. Vérifier soi-même un échantillon avant de faire confiance à l'ensemble

Ne jamais consolider aveuglément les résultats des agents. Reprendre au moins
un cas par lot, lire la donnée source directement (pas le résumé de l'agent),
et confirmer que le raisonnement tient — citation exacte du contrôle, pas
d'interprétation flottante. Sur QualiCheck, ça a permis de corriger
l'interprétation d'un agent (règle 222 vs 223 : pas une "inversion de
complexité" comme dit, mais un cas de mauvais classement isolé) sans pour
autant invalider le reste de son travail.

### 6. Consolider en document final structuré

Une fois la revue jugée close (pas de round supplémentaire prévu) : réécrire
le buffer en document final avec Résumé exécutif, chantiers par priorité
(du plus systémique au plus isolé), candidats few-shot identifiés, **points
positifs à préserver** (pas seulement les problèmes — sert de base de
non-régression pour la prochaine itération), et décisions actées avec la
suite (ex. ré-ingestion complète vs ciblée, script de correction ciblée
reporté ou non).

## Principes clés

- **Toujours un cas de calibrage dans chaque prompt d'agent.** Sans lui, les
  agents inventent leur propre seuil de rigueur, incohérent d'un lot à
  l'autre.
- **Toujours demander explicitement de ne pas nitpicker.** Le risque sinon
  n'est pas l'absence de résultats, c'est un excès de faux positifs sur du
  style plutôt que du fond.
- **Documenter les points positifs autant que les problèmes.** Utile pour
  juger, au tour suivant, si une correction a fait régresser autre chose.
- **Vérifier, ne pas croire.** Un agent qui cite le texte source exact est
  fiable ; un agent qui résume/interprète doit être recoupé avant d'être
  consolidé dans un document définitif.
- **Le buffer précède la spec, jamais l'inverse.** Les décisions de
  correction (reformulation de prompt, nouveaux few-shot...) se prennent en
  discussion après consolidation, puis passent par le cycle spec →
  validation → implémentation habituel du projet — cette revue ne fait que
  produire la matière première.
