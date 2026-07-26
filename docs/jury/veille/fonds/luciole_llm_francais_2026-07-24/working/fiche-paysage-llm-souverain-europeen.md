# Fiche — paysage des LLM souverains européens (2026)

Matériau de travail (recherche du 2026-07-24), à retravailler pour `final/`.
Sert à situer Luciole par rapport aux autres initiatives, pas à les
détailler toutes de façon exhaustive.

## Vue d'ensemble

| Modèle | Origine | Tailles | Langues | Angle distinctif |
| --- | --- | --- | --- | --- |
| **Mistral AI** | France (entreprise privée) | plusieurs, dont des modèles propriétaires | multilingue, fort en anglais | Le seul acteur européen à rivaliser commercialement avec les labs US — pas un projet public/académique comme les autres de cette liste |
| **Lucie** | France (CNRS/LINAGORA, collectif OpenLLM France) | — | français prioritaire | Prédécesseur de Luciole — lancement chahuté (cf. `fiche-lucie-vers-luciole.md`) |
| **Luciole** | France (LINAGORA/OpenLLM France, financement Bpifrance France 2030) | 1B / 8B / 23B | ~30 % français | Sujet de cette veille — cf. `notes-recherche.md` |
| **Teuken** (OpenGPT-X) | Allemagne | 7B | 24 langues officielles UE, ~60 % de données non-anglaises | Tokenizer multilingue dédié, moins performant que Mistral en anglais mais pensé pour la couverture linguistique européenne |
| **EuroLLM** | Consortium UE (soutien Horizon Europe, ERC, EuroHPC) | 9B | 24 langues officielles UE | Entraîné sur le supercalculateur européen MareNostrum 5 — le plus institutionnel des cinq, revendique dépasser des modèles de taille comparable |
| **CroissantLLM** | France (bilingue) | 1,3B | français/anglais strictement bilingue | Le plus petit de la liste, architecture Llama — projet plus modeste, déjà identifié dans `ia_souverain_2026-05-27` comme antécédent |

## Ce qui distingue vraiment ces projets

Deux axes de différenciation, pas un seul :

- **Qui porte le projet** : entreprise privée (Mistral) vs consortium
  académique/public (Lucie, Luciole, Teuken, EuroLLM) vs projet réduit sans
  gros backing institutionnel (CroissantLLM). Luciole se distingue par un
  financement public explicite et traçable (Bpifrance, cf.
  `fiche-bpi-france.md`) — plus proche d'EuroLLM/Teuken que de Mistral sur ce
  plan.
- **Couverture linguistique visée** : franco-centré (Lucie, Luciole,
  CroissantLLM) vs paneuropéen 24 langues (Teuken, EuroLLM) vs multilingue
  généraliste fort en anglais (Mistral). Luciole ne vise pas à couvrir toute
  l'UE — c'est un choix de profondeur (le français) plutôt que de largeur
  (24 langues), à l'inverse de Teuken/EuroLLM.

## Où situer Luciole dans ce paysage

Luciole n'est ni le projet le plus ambitieux en couverture linguistique
(EuroLLM/Teuken visent toute l'UE), ni le plus abouti commercialement
(Mistral), ni le plus modeste (CroissantLLM). Sa singularité est ailleurs :
c'est le seul de la liste à publier **poids + scripts + corpus** sous licences
distinctes (cf. `glossaire.md`) — un choix de transparence/reproductibilité
scientifique plus poussé que ses comparables directs.

## Sources

- https://quelllm.fr/meilleur-llm/souverain
- https://quelllm.fr/meilleur-llm/francais
- https://quelllm.fr/meilleur-llm/multilingue-europeen
- https://arxiv.org/pdf/2410.03730 (Teuken-7B-Base & Teuken-7B-Instruct)
- https://huggingface.co/openGPT-X/Teuken-7B-instruct-commercial-v0.4
- https://intelligence-artificielle.developpez.com/actu/377272/EuroLLM-le-modele-open-source-qui-pourrait-redefinir-la-place-de-l-Europe-dans-la-course-mondiale-a-l-IA
- https://techblog.finalist.nl/blog/europes-open-source-ai-pioneers-10-groups-shaping-llms-under-eu-ai-act
- https://osai-index.eu/

## À vérifier avant restitution

Les fiches QuelLLM.fr ne sont pas des sources primaires (média de
comparaison, auteur non identifié dans les pages consultées) — utiles pour le
survol, mais à recouper avec les pages officielles/model cards de chaque
projet avant de citer un chiffre précis en restitution.
