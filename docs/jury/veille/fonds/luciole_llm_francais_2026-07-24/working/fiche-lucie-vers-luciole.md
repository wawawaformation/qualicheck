# Fiche — de Lucie à Luciole : ce qui a changé

Matériau de travail (recherche du 2026-07-24), à retravailler pour `final/`.
Angle identifié comme le plus intéressant à restituer (cf. `notes-recherche.md`).

## Le lancement de Lucie (janvier 2025) — ce qui a été reproché

Analyse détaillée : [SIDE Blog](https://alain.goudey.eu/side/2025/01/26/analyse-du-lancement-manque-de-lucie-llm-open-source-francais/).

**Échecs sur des tests basiques.** À la question « combien de lettres dans le
mot "lettre" ? », Lucie a répondu cinq au lieu de six. Des calculs simples et
des épreuves logiques élémentaires n'ont pas non plus abouti.

**Absence d'alignement post-entraînement.** Pas d'« instruction tuning »
approfondi, pas de RLHF (*Reinforcement Learning from Human Feedback* —
l'étape où un modèle brut apprend à répondre utilement et à respecter des
consignes, plutôt que juste prédire la suite d'un texte), et aucun garde-fou
contre les usages inappropriés. Concrètement : un modèle qui sait produire du
texte, mais pas encore un assistant utilisable en confiance.

**Infrastructure sous-dimensionnée.** L'interface publique `lucie.chat` a
connu des temps d'attente allant jusqu'à 45 minutes — la charge du lancement
n'avait pas été anticipée.

**Communication en décalage avec la réalité du projet.** Une annonce (portée
par Éduscol, le portail national de ressources pédagogiques) présentait Lucie
avec un optimisme ne mentionnant pas qu'il s'agissait d'un **projet de
recherche académique en phase initiale** — un flou entretenu entre « projet
de recherche exploratoire » et « produit prêt à l'usage éducatif », alors
qu'aucun travail spécifique pour ce cas d'usage n'avait été fait.

**Timing de lancement.** Lancement un vendredi, sans équipe mobilisée pour
gérer les retours du week-end — alors que la viralité négative a été
immédiate et forte.

## Ce que Luciole change concrètement (juin 2026)

| Reproche fait à Lucie | Réponse apparente de Luciole |
| --- | --- |
| Présenté comme un quasi-produit alors que c'est de la recherche | Positionnement explicitement revendiqué comme des « briques brutes pour adaptation métier », pas un assistant public — le président de LINAGORA le dit lui-même : approche scientifique, pas commerciale |
| Un seul modèle, taille non adaptée aux usages | Trois tailles (1B edge, 8B contexte long, 23B raisonnement) — un choix par cas d'usage plutôt qu'un modèle unique à tout faire |
| Corpus et méthode opaques, difficile à évaluer sérieusement | Poids + scripts d'entraînement + corpus tous publiés (cf. `glossaire.md`) — la reproductibilité permet une évaluation indépendante, contrairement à un simple « faites-nous confiance » |
| Pas de garde-fous, pas d'alignement pensé | **Résolu (cf. `fiche-cas-usage-et-essai.md`)** : la variante Luciole-Instruct-1.1 a reçu un alignement en 3 phases — SFT avec traces de raisonnement, SFT sans traces, puis DPO (*Direct Preference Optimization*, alternative plus légère au RLHF classique). Contrairement à Lucie, ce n'est donc pas un modèle brut livré tel quel |

## Ce qui reste incertain (à vérifier avant restitution)

- Pas de communication grand public équivalente à l'annonce Éduscol trouvée
  pour Luciole — cohérent avec le positionnement « briques pour spécialistes »,
  mais à confirmer que ça n'a pas simplement été moins médiatisé.

## Sources

- https://alain.goudey.eu/side/2025/01/26/analyse-du-lancement-manque-de-lucie-llm-open-source-francais/
- https://goodtech.info/openllm-france-linagora-luciole-modeles-fondations-ia-open-source/
- https://huggingface.co/collections/OpenLLM-France/luciole-llm
- https://huggingface.co/OpenLLM-France/Luciole-23B-Instruct-1.1
