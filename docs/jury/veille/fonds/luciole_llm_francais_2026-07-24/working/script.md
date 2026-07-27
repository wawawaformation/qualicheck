# Script — « Pourquoi je ne veux pas de Luciole »

Brouillon de script pour la restitution Mini Manifest (10 min + 20 min
discussion). Matériau de travail, à retravailler en support de partage
accessible (MD/ODT) une fois validé — cf. `journal.md` pour le rappel du
format retenu (ODP = support live, MD/ODT = document diffusé).

Minutage validé : voir tableau dans `decouverte.md` (section « Plan de
restitution »).

---

## 1. Référentiel C6 veille (1 min 30)

- C6 : animer le travail **collectif** de sélection, collecte, traitement et
  partage des informations — pas une lecture solitaire.
- Ce que le référentiel exige concrètement, pas ce qu'on croit qu'il exige :
  - **Régularité** : temps de veille planifiés régulièrement, minimum
    1h/semaine. Le référentiel n'impose pas un "journal" — c'est ma façon
    de le prouver honnêtement, parce que ça ne se fabrique pas après coup.
  - **Fiabilité des sources** : auteur identifié, compétences confirmées,
    contenu daté et sourcé.
  - **Accessibilité des synthèses** : format accessible (renvoi Valentin
    Haüy / AcceDe) — pas juste "facile à consulter".
  - **Travail collectif** : le cadre Mini Manifest lui-même.
- Comment je le fais concrètement : dossier centralisé (`fonds/`), un
  journal daté écrit au moment de la veille, des sources justifiées, des
  synthèses en MD/ODT à styles sémantiques plutôt qu'en images/PPTX.
- Ton : factuel, pas moralisateur — l'attendu, puis ma pratique.

## 2. Découverte de Luciole, tilt RAG (1 min 30)

- Axe personnel déjà ouvert : souveraineté des LLM (`ia_souverain`, Apertus-70B).
- Luciole (OpenLLM France + LINAGORA, juin 2026) : suite de Lucie (lancement
  raté janvier 2025), 3 tailles (1B/8B/23B), positionné "briques brutes pour
  adaptation métier", pas un assistant grand public.
- Le tilt : la model card de Luciole-23B-Instruct-1.1 documente
  explicitement le RAG comme cas d'usage — et recommande d'augmenter le
  modèle par de la récupération documentaire plutôt que de compter sur ses
  connaissances internes.
- Or j'ai déjà un outil de retrieval sur un domaine que je maîtrise
  personnellement (`dirty_retriever`, 245 règles Opquast, QualiCheck) →
  terrain de test concret, pas un exemple jouet.
- Cadrage : ceci reste une démo pour le groupe, pas une décision
  d'architecture pour QualiCheck.

## 3. Tests réalisés, peu concluants (1 min 45)

- Setup : Ollama en conteneur Docker sur un serveur perso (`cloclo`, 32 Go)
  — le PC de travail (5,9 Go disponibles) était trop juste pour un 8B.
- Tool calling : aucune mention dans la model card ni la page Ollama — pas
  testé positif à date.
- Latence sur une question triviale ("Salut") :
  - 1er appel Luciole 8B : 15,57 s
  - 2e appel Luciole 8B : 17,86 s → élimine l'hypothèse du chargement à
    froid (encore plus lent, pas plus rapide)
  - Mistral 7B, déjà chaud : 6,39 s / 9,26 s selon la longueur de réponse
- Vérification CPU (`docker stats`) : les deux modèles plafonnent à 400%
  (4 cœurs sur 8) — donc pas un problème d'allocation de ressources.
- Le vrai chiffre qui compte : `prompt_eval` (traitement du prompt) —
  134 ms/tok pour Luciole contre 32 ms/tok pour Mistral. Le goulot n'est pas
  la génération, c'est le prefill.
- S'appuyer sur les tables déjà prêtes (`decouverte.md`) plutôt que tout
  redérouler à l'oral.

## 4. RNN, Transformers, GPU/CPU, puis Mamba (3 min 15)

Construire dans cet ordre — chaque brique sert à comprendre la suivante :

- **RNN (recurrent neural network)**, le point de départ historique : traite
  la séquence token par token, chaque état dépend du précédent. Inférence
  bon marché (un seul état à faire évoluer), mais **entraînement
  intrinsèquement séquentiel** — impossible à paralléliser correctement sur
  GPU, donc lent à entraîner sur de gros corpus.
- **Transformer** : remplace la récurrence par l'attention — chaque token
  regarde directement tous les autres. Ça règle le problème d'entraînement
  du RNN (tout le prompt traité d'un coup, massivement parallélisable), mais
  au prix d'un coût qui grandit **au carré** de la longueur du contexte en
  génération.
- **GPU, pourquoi ça compte** : des milliers de petits cœurs simples,
  taillés pour faire le **même calcul en parallèle sur plein de données
  indépendantes** — exactement la forme d'une multiplication matricielle
  (l'attention d'un Transformer, ou le prefill). C'est ce matériel qui rend
  le "tout d'un coup" du Transformer réellement rapide en pratique.
- **CPU, en contraste** : peu de cœurs, mais puissants et polyvalents —
  taillés pour de l'exécution **procédurale/séquentielle**, des branchements,
  une logique pas-à-pas. Un CPU peut faire ce qu'un GPU fait, mais sans le
  parallélisme massif — chaque étape attend la précédente.
- **Mamba** : tente de prendre le meilleur des deux mondes — l'inférence bon
  marché du RNN (état de taille fixe, coût **linéaire**) et l'espoir d'un
  entraînement/prefill parallélisable comme un Transformer. State Space
  Model sélectif : les matrices B, C et le pas Δ deviennent dépendants de
  l'entrée, ce qui lui donne une capacité à ignorer/privilégier le contexte,
  comme l'attention d'un Transformer.
- **Le tour de passe-passe théorique** : le *parallel scan*, un algorithme
  hardware-aware qui exploite l'associativité de la combinaison d'états pour
  paralléliser un calcul qui semble intrinsèquement séquentiel (comme un
  RNN) — pensé pour la hiérarchie mémoire d'un **GPU**, exactement le
  matériel décrit deux points plus haut.
- **Le lien avec le test** : sur CPU, via GGUF/llama.cpp, le prefill de
  Luciole ne montre aucun signe de ce gain de parallélisation attendu
  (134 ms/tok, du même ordre que sa propre génération) — alors que Mistral,
  Transformer classique, en profite pleinement (32 ms/tok, ~6x plus rapide
  que sa génération). Hypothèse : le parallel scan n'est pas (bien)
  implémenté dans ce moteur d'inférence CPU précis — **à vérifier avant
  affirmation définitive**.
- **Réserve** : ce résultat est probablement spécifique à l'inférence CPU
  testée ici, pas une propriété générale de Mamba — l'implémentation de
  référence (noyaux CUDA) est pensée pour GPU.
- **Une deuxième raison, indépendante de la vitesse** : la littérature
  documente une faiblesse structurelle de Mamba sur le **rappel verbatim en
  contexte** (tâches de copie exacte, "induction heads") — due à la
  compression à taille fixe de l'état, contrairement à l'attention d'un
  Transformer qui peut consulter n'importe quel token passé avec une
  fidélité parfaite. Or le RAG repose justement sur ce rappel fidèle du
  contexte injecté — ce n'est donc pas qu'un problème d'outillage, c'est
  potentiellement un mésusage architectural (cf. `fiche-architecture-mamba.md`).

## 5. Conclusion (1 min)

- Pas de Luciole pour l'instant, pour deux raisons indépendantes : un
  outillage CPU probablement immature sur le parallel scan, **et** un
  compromis architectural pas idéal pour le rappel fidèle qu'exige le RAG.
- Apertus-70B écarté aussi, mais pour une autre raison : déjà en production
  via l'API Infomaniak (pas auto-hébergé), et de toute façon surdimensionné
  pour une simple synthèse de 3 règles déjà récupérées.
- Piste suivante : tester un petit modèle Transformer pur souverain
  (Mistral, CroissantLLM) pour un comparatif sur un terrain équitable.
- Ouverture vers la discussion de 20 minutes.

---

## Marge (1 min)

Transitions entre les captures d'écran (Bruno, `docker stats`), imprévu.

## Sources vidéo pour réviser la partie 4

- [Pourquoi l'IA tourne sur des GPU et pas des CPU](https://www.youtube.com/watch?v=28oj_a8Euno) — le point CPU/GPU
- [Comment ChatGPT Génère VRAIMENT un Mot (architecture complète)](https://www.youtube.com/watch?v=S_muRjiuv78) — génération token par token, RNN/Transformer
- [Comprendre Les Transformers en Moins de 20 Min](https://www.youtube.com/watch?v=ujkc11DoMgk) — rappel Transformer, pour débutants
