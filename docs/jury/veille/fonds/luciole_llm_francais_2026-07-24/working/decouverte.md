# Découverte — essai RAG concret avec Luciole (2026-07-27)

Matériau de travail, pas encore retravaillé pour restitution — cf. `final/` une
fois la synthèse produite. Répond au TODO noté dans
`fiche-cas-usage-et-essai.md` : *« un test rapide RAG (une question avec
contexte injecté sur un domaine connu) donnerait un point de comparaison
direct »*.

## Contexte et motivation

La model card de Luciole-23B-Instruct-1.1 couvre explicitement le cas d'usage
RAG et recommande d'augmenter le modèle par de la récupération documentaire
plutôt que de compter sur ses connaissances internes (cf.
`fiche-cas-usage-et-essai.md`). Le "domaine connu" retenu pour tester ça en
conditions réelles : le référentiel Opquast du projet QualiCheck, via un
outil de recherche sémantique déjà construit (`dirty_retriever`,
branche `veille_test` du dépôt QualiCheck) — retrieval pgvector (embeddings
Azure) sur les 245 règles, top 3 par similarité cosinus.

**Cadrage important** : cet essai sert une **démo de restitution au groupe
Mini Manifest**, pas une décision d'architecture pour QualiCheck. Aucun
changement n'est envisagé sur le pipeline d'embedding de production
(Azure `text-embedding-3-small`).

## Setup

- Ollama déployé en conteneur Docker sur un serveur personnel (`cloclo`,
  32 Go RAM) plutôt que sur le PC de travail (15,8 Go, ~5,9 Go disponibles
  seulement — insuffisant pour charger un 8B en confort à côté de l'usage
  courant).

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - 11434:11434

volumes:
  ollama_data:
```

- Point de vigilance identifié (pas encore vérifié) : le port 11434 est bindé
  sur toutes les interfaces — à restreindre (`127.0.0.1:11434:11434` ou
  firewall) si `cloclo` est joignable depuis l'extérieur du réseau local,
  l'API Ollama n'ayant pas d'authentification.
- Modèle chargé : `OpenLLM-France/Luciole-Instruct-1.1:8b` (voir
  `fiche-cas-usage-et-essai.md` pour la commande `ollama pull`), comparé à
  `mistral:7b` déjà pratiqué par ailleurs.
- Tests menés à la main via l'outil Bruno, requêtes `POST` sur
  `/api/chat` (penser à choisir la méthode POST + Body en JSON — un premier
  essai en GET a renvoyé une 405).

## Tool calling — recherche documentaire

Aucune mention de tool use / function calling dans la model card officielle
Luciole (Hugging Face) ni sur la page Ollama. Cas d'usage documentés dans les
données d'entraînement : mathématiques, sciences, code, chat général, RAG,
traduction — pas d'agentique.

L'API Ollama accepte un paramètre `tools` sur `/api/chat` pour n'importe quel
modèle, mais sans entraînement spécifique au format de tool-calling
(contrairement à Llama 3.1, Mistral, Qwen...), Luciole risque de l'ignorer ou
de répondre en texte libre au lieu de produire un `tool_calls` structuré —
**à vérifier empiriquement**, pas encore testé à ce stade (chaîne de test
préparée : requête `get_current_weather` avec `"ville": "Paris"`).

Sources :

- [OpenLLM-France/Luciole-Instruct-1.1 (Ollama)](https://ollama.com/OpenLLM-France/Luciole-Instruct-1.1)
- [OpenLLM-France/Luciole-8B-Instruct-1.1 (Hugging Face)](https://huggingface.co/OpenLLM-France/Luciole-8B-Instruct-1.1)

## Essais de latence — "Salut"

Trois appels successifs, question triviale pour isoler le coût de base
(hors charge de contexte RAG) :

| Appel | Modèle | `total_duration` | Constat |
| --- | --- | --- | --- |
| 1 | Luciole 8B | 15,57 s | Premier appel — chargement à froid suspecté |
| 2 | Luciole 8B | 17,86 s | Deuxième appel, encore plus lent → élimine l'hypothèse du chargement à froid comme facteur principal |
| — | Mistral 7B | 6,39 s (test rapide) / 9,26 s (capture détaillée, réponse plus longue) | Modèle déjà "chaud" au moment du test |

**Point de méthode** : la première comparaison (15,57 s vs 6,39 s) n'était pas
équitable — modèles pas dans le même état (froid vs chaud). Rejouer la
question sur le modèle déjà chargé est nécessaire avant de conclure quoi que
ce soit. Une fois ce biais éliminé (deuxième appel Luciole toujours aussi
lent), l'écart s'est révélé réel.

## Analyse détaillée — où part vraiment le temps

Chiffres bruts renvoyés par Ollama (`total_duration`, `load_duration`,
`prompt_eval_*`, `eval_*`, en nanosecondes), capturés via Bruno sur le
deuxième appel Luciole (17,86 s) et un appel Mistral comparable :

| | Luciole 8B | Mistral 7B |
| --- | --- | --- |
| `total_duration` | 17,86 s | 9,26 s |
| `load_duration` | 2,40 s | 0,05 s (quasi nul, modèle chaud) |
| `prompt_eval_count` / `prompt_eval_duration` | 92 tokens → 12,38 s (≈ 134 ms/tok) | 6 tokens → 0,19 s (≈ 32 ms/tok) |
| `eval_count` / `eval_duration` | 14 tokens → 3,05 s (≈ 218 ms/tok) | 46 tokens → ~9 s restants (≈ 196 ms/tok) |

**Constat central** : le coût dominant n'est pas la génération, c'est le
`prompt_eval` (traitement du prompt, aussi appelé *prefill*).

Sur un Transformer classique (Mistral), le prefill est massivement
parallélisable (calcul matriciel sur tout le prompt d'un coup), donc bien
plus rapide *par token* que la génération séquentielle : ici 32 ms/tok en
prefill contre ~196 ms/tok en génération — rapport ~6x, conforme à ce qu'on
attend normalement d'un moteur d'inférence mature.

Sur Luciole, le prefill (134 ms/tok) est du **même ordre de grandeur** que sa
propre génération (218 ms/tok) — aucun gain de parallélisation visible.

**Hypothèse à vérifier avant restitution** : les couches Mamba de Luciole 8B
ne bénéficieraient pas d'un vrai *parallel scan* dans l'implémentation
GGUF/llama.cpp utilisée par Ollama, et seraient donc traitées quasi
séquentiellement même en phase de prefill — comme la génération. L'efficacité
théorique de Mamba (coût linéaire sur le contexte long, cf. `glossaire.md`)
ne se traduirait donc pas en pratique ici, faute d'un support d'inférence
optimisé pour cette architecture. Décalage classique entre papier de
recherche et maturité de l'outillage — à confirmer (ex. issues GitHub
llama.cpp sur le support Mamba/architectures hybrides) avant `final/`, pas à
affirmer tel quel.

## Vérification `docker stats` — CPU exploité, pas le nombre de cœurs

Point du "à faire" ci-dessous, vérifié plutôt que supposé : `docker exec
ollama nproc` confirme 8 cœurs disponibles côté conteneur. Pendant l'appel,
`docker stats ollama` montre un %CPU qui plafonne à **400% pour les deux
modèles** (Luciole et Mistral) — donc 4 cœurs sur 8 utilisés, identique dans
les deux cas.

**Ce que ça élimine** : l'hypothèse "Ollama sous-exploite le CPU spécifiquement
pour Luciole" ne tient pas — l'allocation de ressources est strictement la
même pour les deux modèles.

**Ce que ça renforce** : à CPU utilisé égal (400% pour les deux), Luciole
reste ~4x plus lent par token en `prompt_eval` (134 ms/tok vs 32 ms/tok, cf.
section précédente). L'écart n'est donc pas une question de ressources
allouées mais d'efficacité algorithmique par cœur — cohérent avec l'hypothèse
d'un manque de parallel scan pour les couches Mamba dans l'implémentation
GGUF/llama.cpp utilisée ici, plutôt qu'un simple problème de configuration de
threads.

**Point secondaire, distinct** : le plafond à 400% (au lieu de 800%) pour les
deux modèles suggère qu'Ollama n'exploite par défaut que la moitié des cœurs
(heuristique de threads de llama.cpp) — piste d'optimisation générale
(`num_thread: 8`), mais qui affecterait les deux modèles pareil et ne change
rien à l'écart relatif observé.

**Réserve importante — CPU vs GPU** : ce constat est probablement spécifique
à l'inférence **CPU** via GGUF/llama.cpp, pas une propriété générale de
l'architecture Mamba. L'implémentation de référence de Mamba (le paquet
`mamba-ssm`, noyaux CUDA) est conçue et optimisée pour tourner sur GPU, où le
parallel scan bénéficie d'une parallélisation matérielle bien plus adaptée
qu'un CPU généraliste. Le résultat observé ici (prefill quasi séquentiel,
aussi lent que la génération) pourrait donc ne pas se reproduire sur une
inférence GPU avec les noyaux natifs — **à ne pas généraliser en "Mamba est
lent" tout court**, seulement "l'implémentation CPU/GGUF disponible via
Ollama l'est, dans ce test précis". Nuance importante à porter dans la partie
4 de la restitution (Transformers vs Mamba, CPU/GPU).

## Apertus-70B — pourquoi il ne convient pas non plus pour ce test

Apertus-70B n'est pas qu'un candidat souverain de plus : c'est déjà **le
modèle retenu en production pour le RAG de QualiCheck**
(`conception/annexes/F_choix_llm.md:198`, US2 "Question libre" — Apertus-70B
via Infomaniak, CHF 0.70/2.50 par million de tokens). Mais en production il
n'est jamais auto-hébergé : il est appelé via l'**API Infomaniak**, servie sur
une infra professionnelle avec GPU dédiés.

Ce n'est donc pas la même cause de disqualification que Luciole :

- **Luciole** : problème d'outillage d'inférence (support Mamba immature en
  CPU/GGUF, cf. analyse ci-dessus).
- **Apertus-70B auto-hébergé sur `cloclo`** : même quantifié, 70B ne rentre
  pas dans 32 Go de RAM et ne tournerait pas décemment sur CPU seul — ce
  n'est simplement pas la catégorie de matériel visée pour un test perso.

Sur le fond RAG, un troisième argument : la model card de Luciole rappelait
déjà que le RAG sert précisément à *ne pas* compter sur les connaissances
internes du modèle. Un 70B n'a donc pas d'avantage évident sur une tâche de
simple synthèse de 3 règles déjà récupérées, face à un modèle plus petit et
rapide — le "surdimensionnement" n'est pas qu'une contrainte matérielle, c'est
aussi un mésusage du principe même du RAG.

**Conclusion pour la suite** : Apertus reste la bonne référence *production*
(via API, hors sujet pour ce test auto-hébergé) ; la prochaine architecture à
tester pour la démo reste un petit modèle Transformer pur et souverain
(Mistral, CroissantLLM — cf. `fiche-paysage-llm-souverain-europeen.md`), pas
Apertus.

## Plan de restitution — « Pourquoi je ne veux pas de Luciole »

Structure retenue pour la présentation Mini Manifest (10 min + 20 min
discussion) :

| # | Section | Durée | Contenu |
| --- | --- | --- | --- |
| 1 | Référentiel C6 veille | 1 min 30 | L'attendu de la compétence (régularité 1h/semaine → `journal.md` comme preuve, pas un format imposé par le référentiel lui-même ; fiabilité des sources ; accessibilité des synthèses ; travail collectif Mini Manifest) + comment je le fais concrètement — factuel, pas moralisateur |
| 2 | Découverte de Luciole, tilt RAG | 1 min 30 | Rattachement à l'axe souveraineté déjà entamé (`ia_souverain_2026-05-27`), tilt avec le projet RAG (`dirty_retriever`) |
| 3 | Tests réalisés, peu concluants | 1 min 45 | Latence Luciole vs Mistral (biais froid/chaud identifié puis éliminé, vérification `docker stats`), tool-calling non documenté — s'appuyer sur les tables/captures déjà prêtes plutôt que tout renarrer à l'oral |
| 4 | RNN, Transformers, GPU/CPU, puis Mamba | 3 min 15 | Construction progressive : RNN (séquentiel, dur à paralléliser) → Transformer (attention, parallélisable mais quadratique) → GPU (petits cœurs, poids parallèles) → CPU (peu de cœurs, procédural/séquentiel) → Mamba (tente de combiner linéaire + parallélisable via parallel scan). Explique le pourquoi technique des résultats de la partie 3, avec la réserve CPU/GPU (le constat pourrait ne pas se reproduire avec les noyaux CUDA natifs de Mamba) |
| 5 | Conclusion | 1 min | Pas de Luciole pour l'instant ; Apertus écarté aussi (surdimensionné, déjà en prod via API Infomaniak) ; piste à tester sur une autre architecture (Mistral/CroissantLLM) |
| — | Marge | 1 min | Transitions, captures d'écran à montrer, imprévu |
| | **Total** | **10 min** | |

**Choix d'ordre 3 puis 4** (délibéré) : effet de suspense — montrer un
résultat surprenant (17 s pour "Salut") avant d'en expliquer la cause capte
l'attention du groupe avant la partie plus théorique, et laisse la question
ouverte pour la discussion de 20 minutes plutôt qu'en amont.

## À faire avant restitution

- Vérifier réellement l'hypothèse Mamba/prefill (recherche ciblée sur le
  support llama.cpp, pas une supposition)
- Tester le tool-calling avec la chaîne préparée (`get_current_weather`) et
  noter le résultat, y compris s'il est négatif
- Décider du format de démo live vs pré-enregistré compte tenu de la latence
  observée (17-18 s pour une question triviale, plus pour une vraie réponse
  RAG avec 3 règles injectées en contexte)
- Restreindre l'exposition réseau du port Ollama sur `cloclo` si le serveur
  est joignable depuis l'extérieur
- **Réviser Transformers avant la partie 4** : notion peu vue jusqu'ici,
  contrairement à Mamba qui a déjà sa fiche dédiée (`fiche-architecture-mamba.md`)
  — pas de fiche symétrique écrite pour l'instant, s'appuyer sur les 3
  sources vidéo listées dans `script.md` pour combler l'écart avant l'oral
