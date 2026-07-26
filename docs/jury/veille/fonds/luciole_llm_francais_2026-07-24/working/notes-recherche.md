# Notes brutes — Luciole (OpenLLM France)

Matériau de travail, pas encore retravaillé pour restitution — cf. `final/` une
fois la synthèse produite.

## Ce qui a motivé la piste

Rattachement à l'axe déjà entamé dans `fonds/ia_souverain_2026-05-27/`
(souveraineté des données, Apertus-70B) — Luciole est un point de comparaison
français plus récent (juin 2026), pas un sujet neuf sans lien avec le thème
assigné.

## Faits recueillis (recherche web du 2026-07-24)

- **Luciole** : famille de 3 modèles de langage fondations (1B, 8B, 23B),
  publiée juin 2026 par le collectif **OpenLLM France** et **LINAGORA**,
  financée par BPI France (programme France 2030).
- Entraînés à ~30 % sur du français.
  - 1B : cas d'usage edge
  - 8B : architecture Mamba hybrid, pensée pour le contexte long
  - 23B : performance et raisonnement accrus
- Positionnement assumé : **pas un assistant grand public**, des briques
  brutes pour adaptation/fine-tuning métier — approche scientifique, pas
  produit commercial (propos du président de LINAGORA).
- Licences, point notable : poids en **Apache 2.0**, scripts d'entraînement en
  **AGPL v3**, **corpus d'entraînement publié en CC-BY-SA 4.0** — rare, la
  plupart des LLM ouverts ne publient que les poids, pas le corpus.
- **Lucie** (même collectif, CNRS/LINAGORA) : lancement chahuté en janvier
  2025 (cf. analyse SIDE Blog) — Luciole en est la suite, avec des choix qui
  semblent répondre aux critiques faites à Lucie. Angle de restitution
  potentiellement plus intéressant que "Luciole existe" : *pourquoi Lucie a
  raté son lancement et ce que Luciole change concrètement*.
- Paysage LLM souverain européen 2026 pour situer Luciole : Mistral AI
  (France), Lucie (France), Teuken (Allemagne, OpenGPT-X), EuroLLM (consortium
  UE), CroissantLLM (France, bilingue FR/EN, 1.3B, Llama-based).

## Sources (à vérifier/re-consulter avant citation dans `final/`)

- https://openllm-france.fr/
- https://huggingface.co/collections/OpenLLM-France/luciole-llm
- https://github.com/OpenLLM-France/Luciole-Training
- https://goodtech.info/openllm-france-linagora-luciole-modeles-fondations-ia-open-source/
- https://alain.goudey.eu/side/2025/01/26/analyse-du-lancement-manque-de-lucie-llm-open-source-francais/

## Point de vigilance

Pas de flux RSS officiel OpenLLM France trouvé lors de cette recherche — si
la source doit rejoindre `sources.md` ou `candidats-sources.md`, vérifier par
récupération réelle du flux avant de le lister (cf. piège documenté dans
`CLAUDE.md` : jamais d'URL reconstituée de mémoire).

## À creuser pour la synthèse finale

- Comparer concrètement Luciole 23B à Mistral Small / Apertus-70B : performance,
  coût d'hébergement, disponibilité via un provider comme Infomaniak
- Creuser l'angle Lucie → Luciole (ce qui a changé, ce qui explique l'échec
  initial)
- Vérifier s'il existe un flux RSS/actualités OpenLLM France exploitable
