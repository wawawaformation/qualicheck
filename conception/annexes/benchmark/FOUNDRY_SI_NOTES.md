# Notes Azure AI Foundry — constats pour la SI

Suivi factuel des services Azure AI Foundry testés, à destination de la SI. Document évolutif : un service par section, complété au fil des tests.

**Périmètre de ce rapport : uniquement la partie LLM** (déploiements de modèles de langage sur Azure AI Foundry). D'autres rapports suivront au besoin pour les autres composants d'infrastructure (base de données, autres services Foundry, etc.).

## Contexte et méthodologie

Un script automatisé (`benchmark.py`) interroge chaque modèle déployé à intervalle régulier (toutes les 30 minutes), avec deux types de requête à chaque passage : une requête courte ("dis ok") et une requête plus longue ("pourquoi le ciel est bleu en 5 phrases"), répétées 5 fois chacune. Chaque appel a un délai d'attente maximal (timeout) fixé à 30 secondes.

Deux résultats sont possibles par appel :

- **ok** : le modèle a répondu dans le délai imparti.
- **error** : l'appel a échoué, pour l'une de ces raisons :
  - **timeout** — aucune réponse reçue dans les 30 secondes.
  - **http** — le service a renvoyé une erreur explicite (ex : code 401 pour un problème d'authentification, 503 pour un service indisponible).
  - **autre** — erreur réseau (connexion coupée, refusée, etc.), ni timeout ni erreur HTTP.

Le **taux d'erreur** est le pourcentage d'appels en échec sur le total d'appels effectués, tous types d'erreur confondus.

---

## Service 1 — `dlegrandext-6309-resource` (francecentral) + `dlegrandext-4532-resource` (sweeden)

**Modèles couverts** : gpt-5.4, gpt-5.4-mini, gpt-5.4-nano, DeepSeek-V3.2, DeepSeek-V4-Pro, Phi-4-mini-instruct, Kimi-K2.6, claude-sonnet-4-6, claude-haiku-4-5.

**Période observée** : ~4 jours, sondage toutes les 30 min, 16 820 appels analysés.

### Constat factuel

- Taux d'erreur global de la plateforme : **7,5 %**, dominé par les **timeouts (~35,5 % des erreurs)**.
- Ce taux de fond est présent même sur les modèles individuellement les moins touchés (2,7 à 4 % d'erreur), pas seulement sur les cas extrêmes.
- Un déploiement sort largement du lot : **Phi-4-mini-instruct à 37 % d'erreur**, très au-dessus du reste (le suivant, DeepSeek-V4-Pro, est à 9,1 %).
- Un incident ponctuel d'authentification (HTTP 401) a été observé le 10/07 à 17h31 sur gpt-5.4 et gpt-5.4-mini.

---

D'autres rapports suivront pour les prochains services Azure AI Foundry testés, selon le même format et la même méthodologie.
