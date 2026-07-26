# Glossaire — termes techniques rencontrés sur Luciole

Matériau de travail (recherche du 2026-07-24). Objectif : comprendre chaque
terme, pas les mémoriser comme des étiquettes — à reformuler dans `final/`
avec tes propres mots si tu restitues à l'oral.

## Les « poids » d'un modèle

Un LLM, une fois entraîné, c'est concrètement un très grand nombre de valeurs
numériques (des milliards) qui définissent la force des connexions entre les
neurones artificiels du réseau — ces valeurs sont les **poids** (*weights*).

Analogie utile si tu viens du PHP/backend classique : un modèle entraîné,
c'est un peu comme un binaire compilé — le résultat figé d'un processus
(l'entraînement) qu'on peut réutiliser sans refaire le processus. Télécharger
« les poids » de Luciole, c'est télécharger ce fichier de résultat, pas
relancer l'entraînement soi-même.

**Pourquoi la licence des poids compte** : publier seulement les poids en
open source (comme le font beaucoup de LLM dits « ouverts ») permet de
réutiliser et modifier le modèle, mais **pas de savoir comment il a été
produit** ni de le reproduire à l'identique. C'est là que Luciole va plus
loin (cf. section suivante).

## Apache 2.0 (licence des poids de Luciole)

Une licence open source **permissive** : autorise l'utilisation, la
modification et la redistribution, y compris à des fins commerciales, avec
peu de contraintes (citer les modifications substantielles, conserver les
mentions de licence). Contraste avec des licences plus restrictives type
GPL, qui imposent de republier tout dérivé sous la même licence
(*copyleft*).

Choisir Apache 2.0 pour les poids signifie : n'importe qui — y compris une
entreprise — peut fine-tuner Luciole et l'intégrer à un produit commercial
sans devoir republier son propre travail en open source.

## Scripts d'entraînement et corpus d'entraînement

Deux éléments distincts des poids eux-mêmes, et c'est le point notable de
Luciole : les trois sont publiés séparément, sous trois licences différentes.

- **Corpus d'entraînement** : les textes bruts sur lesquels le modèle a
  appris (livres, sites web, articles...). Licence **CC-BY-SA 4.0**
  (licence Creative Commons — attribution obligatoire, partage des dérivés
  sous la même licence). Publier le corpus permet de savoir *sur quoi* le
  modèle a été construit — traçabilité rare dans l'écosystème LLM, où le
  corpus d'entraînement est en général le secret le mieux gardé (question
  de droits d'auteur, d'avantage concurrentiel).
- **Scripts d'entraînement** : le code qui a effectivement transformé le
  corpus en poids (pipeline de préparation des données, boucle
  d'entraînement, hyperparamètres). Licence **AGPL v3** — copyleft fort :
  si quelqu'un modifie ces scripts et les fait tourner comme service en
  ligne, il doit republier ses modifications, même sans redistribuer de
  binaire (c'est la clause qui distingue l'AGPL de la GPL classique).

Ensemble, ces trois publications (poids + scripts + corpus) rendent
Luciole **reproductible** : n'importe qui disposant de la puissance de calcul
nécessaire pourrait en théorie refaire l'entraînement à l'identique et
vérifier les résultats annoncés. C'est l'argument scientifique mis en avant
par LINAGORA (« approche scientifique, pas produit commercial »).

## Cas d'usage « edge »

*Edge* (informatique en périphérie) désigne l'exécution d'un traitement
**au plus près de l'endroit où la donnée est produite**, plutôt que sur un
serveur distant/cloud — typiquement sur un appareil local aux ressources
limitées (poste de travail, capteur, petit serveur embarqué), sans connexion
réseau permanente ni envoi des données vers un tiers.

Pour un LLM, « pensé pour l'edge » signifie : un modèle assez petit (le
Luciole 1B, par opposition au 23B) pour tourner sur du matériel modeste, en
local, avec une latence faible et sans dépendre d'une API distante. Deux
bénéfices concrets : confidentialité (la donnée ne quitte jamais la machine)
et coût (pas d'appel API facturé à l'usage).

## Architecture « Mamba hybrid » (modèle Luciole 8B)

Les LLM classiques (GPT, Llama, Mistral...) reposent sur l'architecture
**Transformer**, dont le mécanisme d'attention permet à chaque mot de
« regarder » tous les autres mots du texte — puissant, mais dont le coût de
calcul croît **au carré** de la longueur du texte traité (doubler le
contexte quadruple le coût). C'est la raison structurelle pour laquelle les
contextes très longs restent coûteux et lents sur les modèles purement
Transformer.

**Mamba** est une architecture alternative (*state space model*, un
formalisme emprunté à l'automatique/théorie du contrôle) dont le coût de
calcul croît **linéairement** avec la longueur du texte — un contexte deux
fois plus long coûte environ deux fois plus cher, pas quatre fois.

Un modèle **« hybrid »** (comme Jamba, cité en référence) mélange des
couches Transformer et des couches Mamba dans le même réseau, pour combiner
la qualité de raisonnement du Transformer et l'efficacité de Mamba sur les
longs contextes. C'est ce compromis que reprend Luciole 8B : traiter des
documents longs sans le coût quadratique classique.

## RLHF (alignement post-entraînement)

*Reinforcement Learning from Human Feedback* — apprentissage par renforcement
à partir de retours humains. L'étape qui vient **après** l'entraînement
principal, pour transformer un modèle qui sait juste « prédire la suite d'un
texte » en quelque chose qui répond utilement à des instructions.

**Le problème que ça résout** : un LLM entraîné brut (juste sur un gros
corpus) a appris des statistiques de langage, pas à être un assistant. Face à
une question, il peut continuer le texte comme un forum, halluciner, ou ne
pas vraiment « répondre » au sens attendu — c'est le symptôme observé sur
Lucie (résultats faux sur des tests basiques, cf. `fiche-lucie-vers-luciole.md`).

**Principe en 3 étapes** :
1. Le modèle brut génère plusieurs réponses possibles à une même question.
2. Des humains classent ces réponses (meilleure, moins bonne...).
3. Ce classement entraîne un second modèle (le *reward model*) qui apprend à
   noter une réponse comme le ferait un humain ; ce reward model sert ensuite
   à réajuster le LLM principal par apprentissage par renforcement — il
   apprend à produire des réponses que les humains ont tendance à préférer.

**Effet concret** : c'est ce qui fait suivre des consignes à un modèle,
rester dans le sujet, refuser certaines demandes dangereuses (les
« garde-fous ») — plutôt qu'un générateur de texte brut sans filtre.

Point non tranché pour Luciole : aucune source consultée ne précise si un
travail d'alignement (RLHF ou équivalent) a été fait — cf. le point resté
incertain dans `fiche-lucie-vers-luciole.md`.

## Sources

- https://en.wikipedia.org/wiki/Apache_License
- https://www.gnu.org/licenses/agpl-3.0.html
- https://creativecommons.org/licenses/by-sa/4.0/deed.fr
- https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-mamba-and-state
- https://arxiv.org/pdf/2403.19887 (Jamba: A Hybrid Transformer-Mamba Language Model)
- https://www.ai21.com/blog/rise-of-hybrid-llms/
