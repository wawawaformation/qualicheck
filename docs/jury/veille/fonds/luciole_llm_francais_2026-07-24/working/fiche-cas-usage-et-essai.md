# Fiche — cas d'usage et comment essayer Luciole

Matériau de travail (recherche du 2026-07-24), à retravailler pour `final/`.

## Base vs Instruct — laquelle essayer

Deux familles de modèles distinctes sur Hugging Face, à ne pas confondre :

- **Luciole-*B-Base** : le modèle brut, juste entraîné à prédire la suite
  d'un texte — pas conçu pour dialoguer directement.
- **Luciole-Instruct-1.1** : version affinée pour suivre des instructions et
  dialoguer. **C'est celle-ci qu'il faut essayer** pour un usage concret
  (chat, assistant).

## Alignement post-entraînement — corrige le point resté incertain

`fiche-lucie-vers-luciole.md` notait comme incertain si Luciole avait reçu un
travail d'alignement équivalent au RLHF (cf. `glossaire.md`). Réponse trouvée :
oui, en 3 phases —

1. SFT (*supervised fine-tuning*, entraînement supervisé sur des exemples
   d'instructions) avec traces de raisonnement (« thinking »)
2. SFT sans traces de raisonnement
3. **DPO** (*Direct Preference Optimization*) — une alternative plus simple au
   RLHF classique : au lieu d'entraîner un reward model séparé puis de faire
   de l'apprentissage par renforcement, le DPO ajuste directement le modèle à
   partir de paires de réponses classées (préférée / rejetée), en une seule
   étape d'optimisation. Objectif identique au RLHF (aligner le modèle sur
   des préférences humaines), méthode plus légère à mettre en œuvre.

À corriger dans `fiche-lucie-vers-luciole.md` : le tableau disait ce point
« non documenté » — en fait documenté et positif, à mettre à jour avant
`final/`.

## Cas d'usage documentés (model card Luciole-23B-Instruct-1.1)

Données d'entraînement couvrant : mathématiques, sciences, code, chat général,
**RAG**, traduction.

Deux usages entreprise explicitement recommandés par les auteurs :

- **Fine-tuning** pour un cas d'usage spécifique — le 23B est présenté comme
  un point de départ à spécialiser, pas un produit final
- **Intégration dans un pipeline RAG** — le 23B a une capacité de mémorisation
  limitée par sa taille ; les auteurs recommandent explicitement de
  l'augmenter par de la récupération documentaire plutôt que de compter sur
  ses connaissances internes seules

**Réserve explicite des auteurs** : « le modèle doit être testé rigoureusement
pour le cas d'usage visé avant intégration dans un pipeline industriel » — pas
un modèle presse-bouton, un travail de validation reste nécessaire.

## Comment l'essayer

### Ollama (le plus rapide pour un premier test)

```bash
ollama run OpenLLM-France/Luciole-Instruct-1.1:1B
```

(remplacer `1B` par `8B` ou `23B` selon la taille voulue). Les fichiers
Ollama sont des versions **quantifiées Q4_K_M** — la quantification réduit
la précision numérique des poids pour diviser la taille du modèle et la
mémoire nécessaire, au prix d'une petite perte de qualité. C'est ce qui rend
un modèle de plusieurs milliards de paramètres exécutable sur une machine
personnelle plutôt qu'un serveur GPU dédié.

Une fois le prompt `>>>` affiché : taper directement, `/clear` pour repartir
à zéro, `/bye` pour quitter.

### Hugging Face Transformers (pour intégrer dans du code Python)

```bash
pip install transformers datasets evaluate accelerate
```

Puis chargement du modèle via l'API `transformers` standard, comme n'importe
quel modèle Hugging Face — pas de spécificité Luciole à ce niveau. Cette voie
convient si le but est d'intégrer le modèle dans un pipeline applicatif, pas
juste de discuter avec en CLI.

### LangChain

Pas de documentation Luciole spécifique trouvée pour LangChain — mais comme
Luciole est servable via Ollama, l'intégration standard `langchain-ollama`
(déjà générique, pas propre à un modèle) devrait s'appliquer directement. À
vérifier par un essai réel plutôt qu'à affirmer sans l'avoir testé.

## À faire avant restitution

- Tester réellement `ollama run OpenLLM-France/Luciole-Instruct-1.1:8B` (ou
  1B selon la machine disponible) pour avoir un retour d'usage concret, pas
  seulement de la documentation lue
- Si le temps le permet, un test rapide RAG (une question avec contexte
  injecté sur un domaine connu) donnerait un point de comparaison direct avec
  des modèles déjà pratiqués par ailleurs

## Sources

- https://ollama.com/OpenLLM-France/Luciole-Instruct-1.1
- https://ollama.com/OpenLLM-France/Luciole-Instruct-1.1:8B
- https://ollama.com/OpenLLM-France/Luciole-Instruct-1.1:1B
- https://huggingface.co/OpenLLM-France/Luciole-23B-Instruct-1.1
- https://huggingface.co/docs/hub/ollama
