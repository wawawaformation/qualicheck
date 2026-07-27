# Fiche — Architecture Mamba

Matériau de travail (recherche du 2026-07-27), à retravailler pour `final/`.
Objectif : comprendre le fonctionnement de Mamba pour étayer la partie 4 de
la restitution (Transformers vs Mamba) — pas juste répéter que "c'est
linéaire", mais expliquer pourquoi, et ce que ça coûte en échange.

## Origine

Introduite en décembre 2023 par **Albert Gu** et **Tri Dao** dans l'article
*"Mamba: Linear-Time Sequence Modeling with Selective State Spaces"*. Dérivée
des **State Space Models (SSM)**, une famille de modèles jusque-là surtout
utilisée en dehors du NLP (traitement du signal, automatique).

## Le problème que ça résout

Deux familles de modèles, deux défauts opposés :

- **Transformer** : entraînement massivement parallélisable (tout le
  prompt traité d'un coup), mais coût d'inférence qui grandit **au carré**
  de la longueur du contexte (doubler le contexte quadruple le coût de
  l'attention).
- **RNN classique** : inférence efficace (état compact, coût linéaire), mais
  entraînement intrinsèquement **séquentiel** — impossible à paralléliser
  correctement sur GPU, donc lent à entraîner sur de gros corpus.

Mamba vise à obtenir les deux avantages à la fois : parallélisable à
l'entraînement (et au prefill), linéaire à l'inférence.

## Les bases : State Space Model (SSM)

Un SSM représente un système dynamique avec deux équations :

- **Équation d'état** : comment l'état interne évolue (matrice **A**), sous
  l'effet de l'entrée (matrice **B**).
- **Équation de sortie** : comment l'état produit une prédiction (matrices
  **C** et **D**).

Pour du texte, ça revient à compresser tout l'historique de la séquence dans
un **vecteur d'état de taille fixe**, plutôt que de garder (comme
l'attention d'un Transformer) un accès direct à chaque token passé. C'est
cette compression qui permet un coût linéaire — mais elle a un prix (cf.
limites plus bas).

**Défaut des SSM classiques** : les matrices A, B, C sont **fixes**,
indépendantes du contenu — le modèle traite chaque token de la même façon
quel que soit ce qu'il contient. Pas de raisonnement "conscient du contenu".

## L'innovation Mamba : la sélectivité

Mamba rend les matrices **B**, **C** et le pas de discrétisation **Δ**
**dépendants de l'entrée** — le modèle apprend à décider, token par token,
quelle information garder dans l'état et laquelle oublier. Un Δ petit tend à
ignorer le token courant (garder l'ancien état), un Δ grand privilégie le
nouveau token. C'est ce qui rapproche Mamba de la capacité d'un Transformer
à ignorer ou privilégier sélectivement des parties du passé.

## Le parallel scan — comment on parallélise quand même

Une SSM récurrente semble condamnée au calcul séquentiel (chaque état dépend
du précédent). Le **parallel scan** (algorithme "hardware-aware", conçu pour
la hiérarchie mémoire du GPU) exploite le fait que la combinaison des états
est une opération **associative** : l'ordre des calculs intermédiaires n'a
pas d'importance tant que le résultat final respecte l'ordre logique. Ça
permet de calculer des segments de la séquence indépendamment, puis de les
recombiner — donc de paralléliser un calcul qui semblait intrinsèquement
séquentiel.

**C'est précisément le point qui relie ça à l'essai Luciole** : ce parallel
scan est le mécanisme qui devrait permettre un prefill rapide sur GPU. S'il
n'est pas implémenté (ou mal) dans le moteur d'inférence utilisé (GGUF via
llama.cpp, sur CPU), le prefill retombe à un calcul quasi séquentiel — ce
qu'on a observé empiriquement (`prompt_eval` aussi lent, par token, que la
génération). À vérifier plus tard si le support llama.cpp implémente ce
parallel scan ou non.

## Avantages mesurés

Sur la modélisation du langage, Mamba-3B dépasserait des Transformers de
même taille et égalerait des Transformers deux fois plus gros, en
pré-entraînement comme en évaluation en aval — combinaison inédite jusque-là
d'entraînement parallélisable et d'inférence linéaire.

## Limites documentées — le point le plus important pour le RAG

C'est ici que ça devient directement pertinent pour l'essai Luciole/RAG,
au-delà du simple problème de vitesse :

- **Faiblesse sur les tâches de copie exacte** : sur des tâches de
  répétition de séquence, de petits Transformers surpassent des modèles
  Mamba ayant 10x plus de paramètres. Mamba apprend éventuellement la tâche
  mais nécessite beaucoup plus d'exemples, et échoue purement et simplement
  au-delà d'une certaine longueur.
- **Apprentissage en contexte (in-context learning) et rappel affaibli** :
  la capacité à copier verbatim un token vu plus tôt dans le contexte (le
  mécanisme des "induction heads", pressenti comme responsable des capacités
  d'apprentissage en contexte des Transformers) est structurellement limitée
  par la **compression à taille fixe** de l'état — contrairement à
  l'attention d'un Transformer, qui peut en principe revenir consulter
  n'importe quel token passé avec une fidélité parfaite.
- **Raisonnement peu sensible au contenu ligne à ligne** : un SSM classique
  traite chaque token de façon uniforme (avant la sélectivité de Mamba, qui
  atténue mais ne supprime pas entièrement ce défaut structurel).

**Pourquoi c'est important au-delà de la vitesse** : le RAG repose
précisément sur la capacité du modèle à **rappeler fidèlement** un contexte
injecté (les 3 règles retrouvées par `dirty_retriever`) plutôt que sur sa
mémoire paramétrique. Si la capacité de rappel verbatim en contexte est
structurellement plus faible sur une architecture Mamba/hybrid que sur un
Transformer pur, ça donne une **deuxième raison, indépendante de la vitesse
d'inférence**, de rester prudent sur Mamba pour du RAG — pas juste "c'est
lent sur cet outillage précis", mais "le compromis architectural lui-même
n'est pas idéalement taillé pour ce cas d'usage".

## Sources

- [Mamba: Linear-Time Sequence Modeling with Selective State Spaces (arXiv, papier original)](https://arxiv.org/abs/2312.00752)
- [A Visual Guide to Mamba and State Space Models](https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-mamba-and-state)
- [What Is A Mamba Model? (IBM)](https://www.ibm.com/think/topics/mamba-model)
- [Achilles' Heel of Mamba: essential difficulties demonstrated by synthetic data (arXiv)](https://arxiv.org/pdf/2509.17514)
- [Exploring the Limitations of Mamba in COPY and CoT Reasoning (arXiv)](https://arxiv.org/pdf/2410.03810)
- [Mimetic Initialization Helps State Space Models Learn to Recall (arXiv)](https://arxiv.org/pdf/2410.11135)
