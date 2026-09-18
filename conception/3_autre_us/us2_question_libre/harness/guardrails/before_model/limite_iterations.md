# Guardrail `before_model` — limite d'itérations

## Rôle général

Empêche la boucle de l'agent de tourner indéfiniment (ou trop longtemps)
sur une même question — chaque itération coûte un appel LLM réel (et
parfois un tool payant, ex. `chercher_regles_semantique`), sur un projet
qui compte ses centimes (voir les runs d'acceptance chiffrés dans
`CHANGELOG.md`). Sans limite, une question qui met l'agent en tâtonnement
(tool qui échoue, réponse ambiguë) peut boucler sans fin.

**Décidé (David, 2026-09-18)** : ce garde-fou existe, pas de discussion
sur son principe. Ce qui reste ouvert : la valeur du seuil.

## Mécanisme

Compte les itérations (ou les messages) de la boucle en cours ; au-delà
d'un seuil, interrompt et renvoie une réponse explicite plutôt que de
continuer — jamais un timeout silencieux ni une erreur brute. Cohérent
avec le principe déjà appliqué au guardrail périmètre : **fail-open vers
une réponse honnête**, pas un échec opaque pour l'utilisateur.

## Implémentation (LangChain)

Hook `before_model`, `can_jump_to=["end"]` — exemple donné par la doc
officielle : `if len(messages) >= N: jump_to("end")`. Voir
[Custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom).

## Seuil — à trancher, pas à deviner

**Pas de valeur en dur** (cf. règle projet `pas_de_constantes_en_dur`) —
en config, comme `top_n` (`app/retrieval/config.yml`). Pas encore de base
pour choisir un chiffre : aucune mesure réelle du nombre d'itérations
qu'une question US2 nécessite en pratique (l'agent n'existe pas encore).

**À faire avant d'implémenter** : mesurer sur des questions réelles
variées (simple lookup vs question nécessitant plusieurs tools en
chaîne) combien d'itérations sont normalement utilisées, puis fixer le
seuil avec une marge — même méthode que le seuil d'acceptance RAG
(`jury/decisions/2026-09-09-seuil-acceptance-rag-90-pourcent.md` : calé
sur des taux réellement mesurés, pas au doigt mouillé).
