# Scénarios détaillés — US2 Question libre

Détaille les cas d'utilisation de `cas_utilisation_us2.drawio`. Acteurs :
**Professionnel du web** (utilisateur), **Agent IA (LLM)**.

## Se connecter

**Précondition** : l'utilisateur possède un jeton API.

**Scénario nominal** :
1. L'utilisateur présente son jeton (`Authorization: Bearer`) sur un appel à `api_business`.
2. Le système vérifie le jeton.
3. Le système associe la requête au profil `utilisateur` correspondant (créé s'il n'existe pas encore).

**Scénarios alternatifs** :
- Jeton absent ou invalide → rejet (`401`), aucune action effectuée.

## Gérer mon profil (CRUD)

**Précondition** : Se connecter.

**Scénario nominal** :
1. L'utilisateur consulte, crée ou modifie son profil (nom, prénom).
2. Le système applique la modification et la retourne.

**Scénarios alternatifs** :
- Suppression du profil → à trancher avec le volet RGPD (rétention des
  discussions liées), non détaillé ici.

## Créer une discussion

**Précondition** : Se connecter.

**Scénario nominal** :
1. L'utilisateur crée une nouvelle discussion (aucun contenu requis à la
   création — une discussion vide n'existe que dans l'instant qui précède sa
   première question).
2. Le système retourne l'identifiant de la discussion.

## Continuer une discussion

**Précondition** : Se connecter, discussion existante appartenant à l'utilisateur.

**Scénario nominal** :
1. L'utilisateur reprend une discussion existante.
2. Le système retourne l'historique des questions/réponses de cette discussion.

**Scénarios alternatifs** :
- Discussion inexistante ou n'appartenant pas à l'utilisateur → rejet
  (`404` — pas de fuite d'information sur l'existence d'une discussion d'un
  autre utilisateur).

## Supprimer une discussion

**Précondition** : Se connecter, discussion existante appartenant à l'utilisateur.

**Scénario nominal** :
1. L'utilisateur supprime une discussion.
2. Le système supprime la discussion et l'ensemble de ses questions/réponses.

**Scénarios alternatifs** :
- Discussion inexistante ou n'appartenant pas à l'utilisateur → rejet (`404`).

## Poser une question

**Précondition** : Se connecter, discussion existante (nouvelle ou reprise).

**Scénario nominal** :
1. L'utilisateur pose une question dans une discussion (obligatoire).
2. *(Optionnel)* L'utilisateur associe un contexte de page (URL ou capture
   d'écran) à cette question — `«extend»` *Associer un contexte de page*.
3. Le système vérifie que la question relève du périmètre Opquast —
   `«include»` *Filtrer les questions hors périmètre (Guardrails)*.
4. Le système assemble le contexte pertinent — `«include»` *Maintenir le
   contexte de la discussion* : historique de la discussion et, si présent,
   le contexte de page le plus récent applicable.
5. L'agent IA recherche les règles Opquast pertinentes par RAG sémantique
   pur — `«include»` *Rechercher les règles pertinentes*.
6. L'agent IA formule une réponse argumentée, appuyée sur les règles
   trouvées — *Recevoir une réponse argumentée*.
7. Le système enregistre la question et la réponse dans la discussion.

**Scénarios alternatifs / exceptions** :
- **Question hors périmètre** (étape 3) : le système refuse poliment,
  n'appelle pas le RAG ni le LLM de réponse — pas de coût engagé sur une
  question hors sujet.
- **Contexte de page fourni mais extraction impossible** (URL inaccessible,
  image illisible) : la question est traitée sans ce contexte, l'utilisateur
  en est informé plutôt que de recevoir une erreur bloquante.
- **Aucune règle pertinente trouvée** (étape 5) : l'agent le signale
  explicitement plutôt que d'inventer une réponse hors référentiel.

---

## Points volontairement non détaillés ici

- Retour pouce haut/bas sur une réponse — mis de côté pour le MVP
  (cf. mémoire [[stade_projet_mvp]]).
- Modèle de crédits — hors périmètre MVP (cf. `en_commun.md`).
- Interface graphique — aucun écran/maquette décrit ici, volontairement
  (cf. mémoire [[focus_api_avant_client]]) ; ces scénarios restent au niveau
  fonctionnel/API.
