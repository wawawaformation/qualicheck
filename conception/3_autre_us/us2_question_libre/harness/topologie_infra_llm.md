# Topologie infra / LLM par environnement

Contexte de fond pour les guardrails de l'agent US2 (notamment
`guardrails/before_model/`), pas une décision RGPD tranchée — voir
`docs/rgpd/registre_traitements.md` pour les traitements réellement en
œuvre.

## Constat de départ : deux axes indépendants

**Où tourne l'infra applicative** (l'API, la base) et **où tournent les
modèles LLM appelés** ne sont pas la même question, et ne varient pas
ensemble. Une infra auto-hébergée ne protège rien si le modèle appelé
depuis cette infra est un service tiers — le contenu du prompt quitte de
toute façon la frontière de QualiCheck à ce moment-là.

## État par environnement (2026-09-18)

| Environnement | Infra applicative | Backend(s) LLM | Statut du backend |
|---|---|---|---|
| Dev | `cloclo` (serveur auto-hébergé, `.gitea/workflows/cd-staging.yml`) | Azure OpenAI | Société US, exposée au Cloud Act même en région EU |
| Staging | `cloclo` aujourd'hui, migration vers Infomaniak prévue (commentaire `cd-staging.yml`) | Azure OpenAI | Idem dev |
| Prod (David, pas encore tranché) | Infomaniak « certainement » | Infomaniak AI Tools **et** Ollama Cloud (pas de self-host Ollama) | Infomaniak : DPA suisse reconnu équivalent RGPD (Commission UE, 2023), prompts non stockés. Ollama Cloud : société US, politique moins précise qu'Infomaniak sur ce point |

**Ce qui est confirmé** : dev/staging tournent sur Azure aujourd'hui. Ollama
sera utilisé en mode cloud (pas auto-hébergé) — donc son usage transmet
aussi le contenu à un tiers, contrairement à l'hypothèse initiale d'un
Ollama purement local.

**Ce qui reste une hypothèse de David, pas une décision figée** : l'infra
prod sur Infomaniak (« certainement »), et le partage exact des rôles LLM
entre Infomaniak et Ollama en prod (lequel pour quoi n'est pas encore
précisé).

## Conséquence pour les guardrails

Dans **les trois environnements et sur les trois backends actuels ou
envisagés (Azure, Infomaniak, Ollama Cloud)**, le contenu envoyé au modèle
quitte l'infra QualiCheck vers un tiers. Aucun cas ne permet de sauter
l'anonymisation par construction — y compris le meilleur cas légal
(Infomaniak) : sa conformité réduit le risque de *transfert*
juridictionnel, pas le devoir de minimisation (RGPD art. 5.1.c), qui
s'applique à tout sous-traitant.

**Conclusion retenue** : anonymisation uniforme, indépendante du backend
actif — un seul chemin de code, pas de comportement conditionnel par
environnement. Le dev tourne déjà sur le backend le plus exposé (Azure),
donc le garde-fou doit exister dès maintenant, pas seulement au moment du
choix définitif de prod. Détail du guardrail : `guardrails/before_model/`.
