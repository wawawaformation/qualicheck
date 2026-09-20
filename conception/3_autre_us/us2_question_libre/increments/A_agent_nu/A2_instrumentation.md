# Instrumentation

**En tant qu'** exploitant
**je veux** voir le détail de chaque étape d'une réponse
**afin de** savoir où passent le temps et l'argent.

Tâche technique — pas de bénéficiaire côté utilisateur (voir `increments.md`).

## Décisions (levées avant implémentation, voir échange du 2026-09-20)

1. **Granularité** : une trace par appel LLM et par appel d'outil, aussi
   bien côté agent (`app/agent_us2/`) que côté retrieval
   (`app/retrieval/`) — c'est le niveau où "temps et argent" ont un sens.
2. **Format et destination** : OpenTelemetry (SDK/API standard, jamais le
   SDK Langfuse directement) → export OTLP → Langfuse Cloud. Faiblement
   couplé exprès : changer de backend plus tard ne touche que la config
   de l'exporteur, pas le code instrumenté. Un exporteur local en
   **JSONL** (un span par ligne, `logs/traces_agent_us2.jsonl`, même
   convention que `logs/agent_us2.log`) reste
   disponible en option (variable d'env) pour vérifier sans dépendre du
   réseau ni d'un compte Langfuse (critère C20 : "opérationnel au moins
   en local suffit") — même structure de données que ce qui part vers
   Langfuse, seule la destination change.
3. **Contenu des traces** : le texte brut des questions/réponses est
   autorisé pour l'instant (pas encore d'utilisateur réel, on est en
   phase de développement) — C2 (anonymisation + règles de
   journalisation) prendra le relais en temps voulu, avant tout usage
   réel. Décision assumée : ce qui part vers Langfuse Cloud avant C2
   reste en clair chez ce sous-traitant, acceptable tant qu'il n'y a pas
   de donnée personnelle réelle en jeu (voir aussi la note équivalente
   dans `increments.md`, "Choix de l'outil de restitution").
4. **Critère observable/exécutable** : chaque requête agent expose son
   `trace_id` (ajout au contrat `openapi.json` — bump de version) ;
   "observer" = l'ouvrir dans l'interface Langfuse, ou retrouver les
   lignes correspondantes dans le fichier JSONL local.

## Sous-tâches

- [ ] Ajouter le SDK OpenTelemetry au projet, configuration de
  l'exporteur OTLP (Langfuse Cloud) + exporteur local JSONL
  (`logs/traces_agent_us2.jsonl`) (bascule par variable d'env, voir
  convention `app/*/config.yml` + `.env`).
- [ ] Instrumenter `app/agent_us2/loop.py` : un span par appel LLM, un
  span par appel d'outil.
- [ ] Instrumenter `app/retrieval/` (décomposition, jugement,
  garde-fou, recherche dense) au même niveau de granularité.
- [ ] Exposer `trace_id` dans `QuestionReponse` (`app/agent_us2/schemas.py`
  + `openapi.json`, version bumpée).
- [ ] Compte/projet Langfuse Cloud — étape manuelle, hors code.

## Questions restées ouvertes

- Nom du projet/workspace Langfuse Cloud à créer — à faire au moment de
  configurer l'exporteur, pas avant.

## Gherkin

```gherkin
Fonctionnalité : Instrumentation des étapes de l'agent

  Scénario : Un appel LLM produit une trace
    Étant donné une question envoyée à l'agent US2
    Quand l'agent appelle un modèle LLM
    Alors une trace OpenTelemetry est émise pour cet appel
    Et elle contient la durée, le coût estimé et le nom de l'étape

  Scénario : Un appel d'outil produit une trace
    Étant donné une question envoyée à l'agent US2
    Quand l'agent appelle un outil (ex. recherche par mots-clés)
    Alors une trace OpenTelemetry est émise pour cet appel
    Et elle contient la durée et le résultat (succès ou erreur)

  Scénario : La réponse expose un identifiant de trace
    Étant donné une question envoyée à l'agent US2
    Quand la réponse est renvoyée
    Alors elle contient un champ `trace_id`
    Et ce `trace_id` permet de retrouver la trace complète dans Langfuse

  Scénario : Développement sans compte Langfuse configuré
    Étant donné la variable d'environnement OTEL_EXPORTER=jsonl
    Quand l'agent traite une question
    Alors chaque span (appel LLM, appel d'outil) est écrit comme une
      ligne JSON dans le fichier de traces local
    Et aucune requête réseau n'est envoyée vers Langfuse Cloud
```

## Schémas

À produire : `A2_instrumentation.drawio` — flux d'une trace (appel
LLM/outil → span OpenTelemetry → exporteur → Langfuse Cloud ou sortie
console locale), et où `trace_id` réapparaît dans la réponse API.
