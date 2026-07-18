# Notes Azure AI Foundry — évaluation des services (usage interne équipe)

Suivi des services Azure AI Foundry testés dans le cadre du benchmark, avec un avis sur leur fiabilité et une réflexion vers le déploiement en conditions réelles (formation dev IA agentique). Document évolutif : un service par section, complété au fil des tests.

**Usage interne équipe uniquement.** Le document destiné à la SI (constat factuel, sans avis ni recommandations de déploiement) est [FOUNDRY_SI_NOTES.md](FOUNDRY_SI_NOTES.md).

---

## Service 1 — `dlegrandext-6309-resource` (francecentral) + `dlegrandext-4532-resource` (sweeden)

**Modèles couverts** : gpt-5.4, gpt-5.4-mini, gpt-5.4-nano, DeepSeek-V3.2, DeepSeek-V4-Pro, Phi-4-mini-instruct, Kimi-K2.6, claude-sonnet-4-6, claude-haiku-4-5 (claude-opus-4-7 exclu après retrait, échantillon non représentatif).

**Période observée** : ~4 jours, cron toutes les 30 min, 16 820 appels analysés.

### Constat factuel

- Taux d'erreur global de la plateforme : **7,5 %**, dominé par les **timeouts (~35,5 % des erreurs)**.
- Ce taux de fond est présent même sur les modèles individuellement "sains" (2,7 à 4 % d'erreur), pas seulement sur les cas extrêmes.
- Un modèle sort largement du lot : **Phi-4-mini-instruct à 37 % d'erreur**, très au-dessus du reste (le suivant, DeepSeek-V4-Pro, est à 9,1 %).
- Un incident ponctuel d'authentification (HTTP 401) a été observé le 10/07 à 17h31 sur gpt-5.4 et gpt-5.4-mini — cohérent avec un souci de clé/souscription transitoire, pas de l'instabilité chronique.

### Avis : sain ou pas ?

**Pas complètement sain, mais pas critique.**

- Un taux d'erreur de fond de 7,5 % (dominé par des timeouts, pas des refus propres) est élevé pour un service cloud managé — on attend généralement < 1-2 % sur une infra stable. C'est un signal légitime, pas du bruit statistique.
- Cela dit, `Phi-4-mini-instruct` tire fortement la moyenne globale vers le haut. Sans lui, le taux de fond des autres modèles serait plus proche de 3-4 % — mauvais, mais pas alarmant pour un déploiement régional.
- Limite de l'échantillon : 3-4 jours, une seule zone testée intensément (francecentral). Impossible de dire si c'est spécifique à *ce* déploiement Foundry ou à Azure AI en général dans cette région.

**Recommandation à la SI** : signaler le taux d'erreur global (7,5 %, dominance timeout) comme symptôme de plateforme, tout en isolant `Phi-4-mini-instruct` comme cas à part — probablement un déploiement sous-dimensionné plutôt qu'un signe d'instabilité générale.

### Vers le déploiement — points de vigilance

*(à enrichir au fil des services testés)*

- Un service avec ~3-4 % d'erreur de fond, même "sain", nécessite une gestion de retry côté application — ne pas supposer un appel garanti.
- Les timeouts dominent : prévoir un timeout applicatif cohérent avec celui observé ici (30 s) et une stratégie de repli (modèle de secours, message d'erreur utilisateur) plutôt qu'un blocage silencieux.
- Éviter `Phi-4-mini-instruct` en usage pédagogique nécessitant de la fiabilité de démonstration (ex: live devant un groupe) tant que son taux d'erreur n'est pas retombé à un niveau comparable aux autres modèles.

---

## Service 2 — *(à venir)*

## Service 3 — *(à venir)*
