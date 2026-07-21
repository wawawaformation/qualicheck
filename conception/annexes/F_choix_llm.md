---
title: "Choix des modèles LLM – QualiCheck"
subtitle: "Benchmark et argumentation — C7 du référentiel RNCP37827"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
toc: true
toc-depth: 3
numbersections: true
---

\newpage

## Contexte et besoins

QualiCheck mobilise des LLM dans quatre contextes distincts, avec des exigences différentes en termes de qualité de raisonnement et de latence :

**Agent enrichissement (US0 — ingestion)** — traite chaque règle Opquast pour produire un JSON structuré contenant la stratégie d'analyse, le score de confiance, la justification et le `guide_analyse`. Tâche d'**instruction following** avec sortie courte et structurée (~600 tokens en entrée, ~400 tokens en sortie). Script CLI autonome — pas d'interaction temps réel. La **fiabilité** et la **qualité du JSON** priment sur la latence. Ce modèle traite les 245 règles en séquence.

**Agent d'audit — phase 1 : génération des constats (US1)** — analyse des pages HTML en s'appuyant sur le `guide_analyse` injecté par SQL. Tâche de **raisonnement dense** sur un contexte long (page HTML + règles + guide). Pas d'interaction temps réel à ce stade. La **qualité d'analyse** prime.

**Agent d'audit — phase 2 : dialogue et validation (US1 suite)** — dialogue interactif avec l'auditeur expert sur les constats générés. Échanges courts et nombreux. L'auditeur attend la réponse en temps réel. La **fluidité et la latence** priment.

**Agent question libre (US2)** — dialogue libre sur une page soumise, RAG sémantique pur sur les 245 règles, guardrails et mémoire de session. Raisonnement ouvert sans cadre prédéfini. La **qualité de raisonnement** prime. Les aspects guardrails et mémoire seront documentés dans les sections dédiées.

**Embedding (toutes phases)** — All MiniLM L12 v2 via Infomaniak, gratuit, déjà acté — voir section dédiée.

---

## Contraintes du projet

### Contraintes réglementaires

Le choix des modèles s'inscrit dans une réflexion sur la **souveraineté numérique** et la **conformité réglementaire européenne**, documentée dans la veille
(cf. [Annexe D — Synthèse IA souveraine](annexes/D_synthese_ia_souveraine.md)).

Trois piliers structurent cette analyse (Benjamin Bayart) :

- **Juridique** : le droit européen protège la personne, le droit américain protège le business. Le Cloud Act américain permet aux agences fédérales d'accéder aux données de toute entreprise américaine, quel que soit le lieu de stockage des serveurs.
- **Économique** : la plus-value doit rester dans l'espace économique local.
- **Régalien** : les fonctions vitales ne doivent pas dépendre d'infrastructures étrangères incontrôlables.

La CJUE a successivement invalidé le Safe Harbor et le Privacy Shield, rendant structurellement risqué tout hébergement de données personnelles chez un fournisseur américain soumis au RGPD.

**Conséquence directe** : OpenAI, Anthropic et Google sont écartés pour la phase de production, indépendamment de leur qualité technique. Leur usage en développement reste acceptable sur des données non sensibles.

### Contraintes budgétaires

**Phase de développement — Azure AI Foundry (crédits école)**

L'organisme de formation met à disposition un accès Azure AI Foundry partagé entre **8 apprenants et les formateurs**, avec un budget d'environ **160€/mois** (à confirmer avec l'OF). Sessions ponctuelles de 2 à 3 heures, sans runs intensifs continus.

**Fallback — Ollama Cloud**

`gpt-oss:20b-cloud` disponible gratuitement, limites de session (reset toutes les 5 heures) et limites hebdomadaires. Adapté aux tests ponctuels.

**Phase finale — Infomaniak (budget personnel)**

Budget personnel plafonné à **20€ (~ CHF 19)**, avec 1M de tokens offerts à l'inscription.

### Contraintes techniques

- API compatible OpenAI requise pour s'intégrer sans adaptation dans le `config.py` multi-modèles
- Support du **structured output / JSON mode** obligatoire pour l'agent enrichissement
- Fenêtre de contexte **≥ 32K tokens** recommandée pour l'agent d'audit
- Modèle **multilingue** (français en priorité)
- Modèles déployables sur le tenant Azure école **sans souscription Marketplace**
- **Taux d'erreur < 10%** requis — les 245 appels séquentiels de l'ingestion ne tolèrent pas l'instabilité
- **Latence < 2 000 ms** médiane recommandée pour les usages interactifs (dialogue auditeur)

---

## Benchmark Azure AI Foundry

### Méthodologie

Un benchmark automatisé a été conduit sur la plateforme Azure AI Foundry pour évaluer la **fiabilité** et la **latence réelle** des modèles disponibles sur le tenant école, avant tout choix définitif.

**Protocole** :
- Cron toutes les 30 minutes sur **4 jours** (10 au 14 juillet 2026)
- **16 820 appels analysés** sur 16 842 lignes de log
- Deux ressources : `dlegrandext-6309-resource` (francecentral) et `dlegrandext-4532-resource` (sweeden)
- 9 modèles surveillés (claude-opus-4-7 retiré du run le 10/07, échantillon non représentatif)
- Latences calculées uniquement sur les appels réussis — les timeouts à 30 000 ms n'entrent pas dans la moyenne

Le script de benchmark, le script d'analyse et le rapport complet sont disponibles en annexe
(cf. [Annexe F3 — benchmark.py](annexes/F3_benchmark.py), [Annexe F4 — Rapport d'analyse PDF](annexes/F4_analyse_models_azure.pdf), [Annexe F1 — FOUNDRY_NOTES.md](annexes/F1_FOUNDRY_NOTES.md), [Annexe F2 — FOUNDRY_SI_NOTES.md](annexes/F2_FOUNDRY_SI_NOTES.md)).

### Résultats

| Modèle | Appels | Taux d'erreur | Latence moyenne | Latence médiane |
|---|---|---|---|---|
| **Phi-4-mini-instruct** | 1 870 | **37.0%** | 3 647 ms | 2 362 ms |
| DeepSeek-V4-Pro | 1 870 | 9.1% | 4 436 ms | 2 814 ms |
| **Kimi-K2.6** | 1 870 | **4.0%** | 4 689 ms | 3 992 ms |
| DeepSeek-V3.2 | 1 870 | 3.3% | 2 120 ms | 1 904 ms |
| gpt-5.4 | 1 870 | 3.1% | 1 576 ms | 1 656 ms |
| **gpt-5.4-mini** | 1 870 | **2.9%** | 1 067 ms | **1 046 ms** |
| **gpt-5.4-nano** | 1 870 | **2.7%** | 1 386 ms | 1 281 ms |
| **claude-sonnet-4-6** | 1 860 | **2.7%** | 4 104 ms | 4 227 ms |
| claude-haiku-4-5 | 1 860 | 2.7% | 2 285 ms | 2 440 ms |

**Observations clés :**

- Taux d'erreur global plateforme : **7.5%**, dominé par les timeouts (~35.5% des erreurs). Élevé pour un service cloud managé — impose une stratégie de retry côté application.
- **Phi-4-mini-instruct à 37% d'erreur** — très au-dessus du reste, probablement un déploiement sous-dimensionné sur le tenant. Écarté sans appel.
- **claude-sonnet-4-6** : taux d'erreur excellent (2.7%) mais **latence médiane de 4 227 ms** — la plus élevée du benchmark. Rédhibitoire pour le dialogue interactif.
- **Kimi K2.6** : 4.0% d'erreur, 3 992 ms de latence médiane. Acceptable pour un usage non interactif (script CLI), problématique pour le dialogue temps réel.
- **gpt-5.4** : 3.1% d'erreur, **1 656 ms** de latence médiane — excellent rapport qualité/vitesse pour un usage interactif.
- **gpt-5.4-mini** : 2.9% d'erreur, **1 046 ms** de latence médiane — le plus rapide du benchmark sur des données saines.
- **gpt-5.4-nano** : 2.7% d'erreur, 1 281 ms — meilleur taux d'erreur, très proche de mini en latence.

---

## Analyse et choix par usage

### Agent enrichissement (US0 — ingestion) → Kimi K2.6

**Contexte de la décision** : script CLI autonome, 245 appels séquentiels, pas d'interaction temps réel. Une ingestion complète dure ~16 minutes (245 × 4s). La latence est acceptable — ce qui compte c'est la fiabilité et la fenêtre de contexte pour la re-ingestion avec feedbacks.

**Pourquoi pas Phi-4-mini-instruct ?** 37% de taux d'erreur sur 1 870 appels mesurés. Pour 245 appels séquentiels, une ingestion complète serait systématiquement interrompue. Écarté.

**Pourquoi pas gpt-5.4-nano ?** Très bon taux d'erreur (2.7%) et validé empiriquement sur un projet similaire (classification + guardrails). Mais Kimi K2.6 présente un avantage décisif pour la re-ingestion avec feedbacks : sa fenêtre de **256K tokens** permet d'injecter l'historique complet des feedbacks auditeurs + les patterns RAG transversaux sans troncature.

**Pourquoi Kimi K2.6 ?**
- Taux d'erreur sain : 4.0%
- Fenêtre de contexte 256K — déterminante pour la re-ingestion intelligente (feedbacks + RAG transversal)
- Tool calling natif — utile pour les workflows agentiques
- 3 992 ms de latence médiane — acceptable pour un script CLI

| Modèle | Taux erreur | Latence médiane | Contexte | Verdict |
|---|---|---|---|---|
| **Kimi K2.6** | 4.0% | 3 992 ms | **256K** | **Retenu** |
| gpt-5.4-nano | 2.7% | 1 281 ms | 128K | Bon mais contexte limité |
| Phi-4-mini-instruct | 37% | 2 362 ms | 128K | **Écarté (instable)** |
| DeepSeek-V4-Pro | 9.1% | 2 814 ms | 128K | Taux limite |

### Agent d'audit — phase 1 : génération des constats (US1) → gpt-5.4

**Contexte de la décision** : analyse de pages HTML + injection SQL du `guide_analyse`. Pas d'interaction temps réel à ce stade — l'auditeur lance l'analyse et attend le résultat. La qualité du raisonnement prime sur la latence.

**Pourquoi pas gpt-5.4-mini ?** La différence de latence entre mini (1 046 ms) et gpt-5.4 (1 656 ms) est de 600 ms — imperceptible pour une tâche non interactive. En revanche gpt-5.4 est le modèle complet, meilleur en raisonnement dense sur des pages HTML complexes.

**Pourquoi pas claude-sonnet-4-6 ?** Taux d'erreur excellent (2.7%) mais latence médiane de 4 227 ms — quasi identique à Kimi. Pour une tâche non interactive c'est tolérable, mais gpt-5.4 offre un meilleur rapport qualité/latence. Et Anthropic reste écarté de la production pour des raisons RGPD.

**Pourquoi gpt-5.4 ?**
- Taux d'erreur sain : 3.1%
- Latence médiane : 1 656 ms — très rapide pour la qualité offerte
- Meilleur raisonnement que gpt-5.4-mini sur des contenus HTML complexes
- Contexte 128K — suffisant pour une page + guide_analyse + historique

| Modèle | Taux erreur | Latence médiane | Verdict |
|---|---|---|---|
| **gpt-5.4** | 3.1% | 1 656 ms | **Retenu** |
| gpt-5.4-mini | 2.9% | 1 046 ms | Alternative si coût trop élevé |
| claude-sonnet-4-6 | 2.7% | 4 227 ms | Écarté (latence + RGPD prod.) |
| Kimi K2.6 | 4.0% | 3 992 ms | Écarté (latence) |

### Agent d'audit — phase 2 : dialogue et validation (US1 suite) → gpt-5.4-mini

**Contexte de la décision** : dialogue interactif avec l'auditeur expert. Échanges courts et nombreux — explication d'un constat, reformulation, question sur une règle. L'auditeur attend la réponse en temps réel. La fluidité prime.

**Pourquoi gpt-5.4-mini et pas gpt-5.4 ?** Pour le dialogue, 1 046 ms vs 1 656 ms fait une vraie différence perçue sur plusieurs échanges successifs. La tâche est moins dense cognitivement que l'analyse de page — gpt-5.4-mini est suffisant et nettement plus fluide.

| Modèle | Taux erreur | Latence médiane | Verdict |
|---|---|---|---|
| **gpt-5.4-mini** | 2.9% | **1 046 ms** | **Retenu** |
| gpt-5.4-nano | 2.7% | 1 281 ms | Alternative si mini non disponible |
| gpt-5.4 | 3.1% | 1 656 ms | Trop lent pour dialogue fluide |
| claude-sonnet-4-6 | 2.7% | 4 227 ms | Écarté (latence) |

### Agent question libre (US2) → gpt-5.4

**Contexte de la décision** : RAG sémantique pur sur les 245 règles, raisonnement ouvert sur une page soumise librement, sans cadre prédéfini. La qualité de raisonnement prime — c'est la US qui démontre le RAG dans sa forme la plus pure. Même logique que la phase 1 de l'audit.

Les aspects guardrails et mémoire de session seront documentés dans les sections dédiées.

| Modèle | Taux erreur | Latence médiane | Verdict |
|---|---|---|---|
| **gpt-5.4** | 3.1% | 1 656 ms | **Retenu** |
| gpt-5.4-mini | 2.9% | 1 046 ms | Alternative si latence suffisante |

### Embedding → All MiniLM L12 v2 (Infomaniak)

Gratuit sur toutes les phases, 384 dimensions, multilingue. Aucun changement prévu — voir `conception.md` section choix techniques.

---

## Stratégie retenue

### Synthèse par usage

| Usage | Dev (Azure) | Justification | Fallback | Production (Infomaniak) |
|---|---|---|---|---|
| Enrichissement (US0) | **Kimi K2.6** | Contexte 256K pour re-ingestion | gpt-oss:20b | Mistral Small |
| Audit — génération (US1 ph.1) | **gpt-5.4** | Qualité raisonnement, 1 656 ms | gpt-oss:20b | Apertus-70B |
| Audit — dialogue (US1 ph.2) | **gpt-5.4-mini** | Fluidité, 1 046 ms | gpt-oss:20b | Apertus-70B |
| Question libre (US2) | **gpt-5.4** | Qualité raisonnement RAG pur | gpt-oss:20b | Apertus-70B |
| Embedding | **All MiniLM L12 v2** | Gratuit, toutes phases | — | All MiniLM L12 v2 |

### Implémentation dans le code

Tous les fournisseurs exposent une API compatible OpenAI. Le switch entre modèles est transparent pour le code métier.

```python
# Quatre variables configurables indépendamment
ENRICHMENT_LLM     = "kimi"          # US0 — ingestion
AUDIT_GENERATE_LLM = "gpt54"         # US1 — génération constats
AUDIT_DIALOG_LLM   = "gpt54_mini"    # US1 — dialogue interactif
FREE_QUESTION_LLM  = "gpt54"         # US2 — question libre

LLM_CONFIGS = {
    # Phase développement (Azure)
    "kimi": {
        "model": "Kimi-K2.6",
        "base_url": "https://models.inference.ai.azure.com",
        "api_key": os.getenv("AZURE_API_KEY"),
        "max_tokens": 4096
    },
    "gpt54": {
        "model": "gpt-5.4",
        "base_url": "https://models.inference.ai.azure.com",
        "api_key": os.getenv("AZURE_API_KEY"),
        "max_tokens": 4096
    },
    "gpt54_mini": {
        "model": "gpt-5.4-mini",
        "base_url": "https://models.inference.ai.azure.com",
        "api_key": os.getenv("AZURE_API_KEY"),
        "max_tokens": 2048
    },
    # Fallback (Ollama Cloud)
    "ollama": {
        "model": "gpt-oss:20b-cloud",
        "base_url": "https://api.ollama.com",
        "api_key": os.getenv("OLLAMA_API_KEY"),
        "max_tokens": 4096
    },
    # Phase production (Infomaniak — souverain, éco-responsable)
    "apertus": {
        "model": "Apertus-70B-Instruct-2509",
        "base_url": "https://api.infomaniak.com/1/ai",
        "api_key": os.getenv("INFOMANIAK_API_KEY"),
        "max_tokens": 4096
    },
    "mistral_small": {
        "model": "mistralai/Ministral-3-14B-Instruct-2512",
        "base_url": "https://api.infomaniak.com/1/ai",
        "api_key": os.getenv("INFOMANIAK_API_KEY"),
        "max_tokens": 1024
    }
}
```

**Stratégie de retry** — le benchmark révèle un taux d'erreur de fond de 3-4% dominé par des timeouts (30s observés). Tout appel LLM dans QualiCheck implémente un retry avec backoff exponentiel et bascule sur le fallback Ollama en cas d'échec persistant.

Le champ `llm_provider` est tracé en base sur chaque règle générée lors de l'ingestion — benchmark en conditions réelles intégré au projet.

---

## Infomaniak AI Services — phase finale et production

Infomaniak est retenu pour la phase de production pour les raisons détaillées dans la veille souveraineté
(cf. [Annexe D1](annexes/D1_ia_souveraine_donnees.jpg), [Annexe D2](annexes/D2_parcours_decision_cloud.jpg), [Annexe D3](annexes/D3_apertus_ethique_souverain.jpg)).

**Démarche éco-responsable** : Infomaniak est alimenté à **100% en énergie renouvelable**. La chaleur produite par les serveurs est revalorisée pour le chauffage des bâtiments environnants. Engagements formalisés et audités indépendamment. Aligné avec les critères C15/C17 du référentiel RNCP37827.

| Modèle | Contexte | Tarif entrants | Tarif sortants | Usage |
|---|---|---|---|---|
| **Mistral Small** | 32K | CHF 0.30/1M | CHF 0.40/1M | Agent enrichissement |
| **Apertus-70B-Instruct-2509** | 128K | CHF 0.70/1M | CHF 2.50/1M | Agent d'audit + question libre |
| **All MiniLM L12 v2** | — | **Gratuit** | **Gratuit** | Embedding |

**Apertus-70B** : modèle qualifié d'"IA la plus éthique" par Infomaniak. Conforme nativement à l'AI Act — documentation rigoureuse, explicabilité, auditabilité. Aucune requête API stockée. Données d'entraînement documentées et respectueuses de la propriété intellectuelle.

**Mistral Small** : accessible sans restriction Marketplace. Meilleur rapport qualité/coût pour les 245 appels JSON courts de l'ingestion. Continuité naturelle avec gpt-5.4-nano en dev (même profil de tâche).

---

## Tableau comparatif final

| Modèle | Fournisseur | Hébergement | RGPD | Éco | Taux erreur | Latence médiane | Phase | Rôle |
|---|---|---|---|---|---|---|---|---|
| GPT-4o | OpenAI | USA | Risqué | Engagement 2030 | N/A | N/A | Écarté prod. | — |
| Gemini 2.0 | Google | USA | Risqué | Engagement 2030 | N/A | N/A | Écarté prod. | — |
| **Phi-4-mini-instruct** | Azure | USA | Dev seul | Engagement 2030 | **37%** | 2 362 ms | **Écarté (instable)** | — |
| DeepSeek-V4-Pro | Azure | Variable | À vérifier | Non certifié | 9.1% | 2 814 ms | Écarté | — |
| claude-sonnet-4-6 | Azure/Anthropic | USA | Risqué prod. | Non certifié | 2.7% | **4 227 ms** | Écarté (latence) | — |
| DeepSeek-V3.2 | Azure | Variable | À vérifier | Non certifié | 3.3% | 1 904 ms | Écarté | — |
| **Kimi K2.6** | Azure | USA | Dev seul | Non certifié | 4.0% | 3 992 ms | **Dev** | **Enrichissement** |
| **gpt-5.4** | Azure/OpenAI | USA | Dev seul | Engagement 2030 | 3.1% | 1 656 ms | **Dev** | **Audit ph.1 + US2** |
| **gpt-5.4-mini** | Azure/OpenAI | USA | Dev seul | Engagement 2030 | 2.9% | 1 046 ms | **Dev** | **Audit ph.2 (dialogue)** |
| gpt-oss:20b | Ollama | Non garanti EU | Acceptable | Non certifié | N/A | N/A | **Fallback** | Tous |
| **Mistral Small** | Infomaniak | Suisse | Conforme | ✓ Certifié | N/A | N/A | **Production** | **Enrichissement** |
| **Apertus-70B** | Infomaniak | Suisse | Conforme | ✓ Certifié | N/A | N/A | **Production** | **Audit + US2** |
| **All MiniLM L12 v2** | Infomaniak | Suisse | Conforme | ✓ Certifié | N/A | N/A | **Toutes phases** | **Embedding** |

---

## TODO — Éléments à compléter pour la certification

### C7 — Identifier des services d'intelligence artificielle préexistants

> *"Le benchmark détaille le niveau d'adéquation du service étudié pour chaque ensemble fonctionnel souhaité par le commanditaire."*

- [ ] Documenter des appels comparatifs Kimi K2.6 vs gpt-5.4-nano sur une règle Opquast — valider la qualité du JSON produit par chacun
- [ ] Comparer gpt-5.4 vs Apertus-70B sur un constat d'audit — valider la continuité dev → production
- [ ] Comparer gpt-5.4-mini vs Apertus-70B sur le dialogue — valider la fluidité en production

> *"Le benchmark détaille le niveau de la démarche éco-responsable du service étudié, en fonction des informations disponibles."*

- [ ] Compléter les données éco d'Ollama Cloud
- [ ] Documenter la consommation estimée en CO₂ par phase (dev Azure vs production Infomaniak)

### C15 — Concevoir le cadre technique

- [ ] Implémenter et documenter la stratégie de retry avec backoff exponentiel sur tous les appels LLM
- [ ] Documenter le mapping entre les 4 variables LLM et les endpoints de l'API FastAPI
