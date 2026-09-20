# A2 — Instrumentation de l'agent US2

2026-09-20 · brainstorming validé, en attente de relecture

## Contexte

Carte Kanboard #24, increment A2 (`conception/3_autre_us/us2_question_libre/increments/increments.md`),
juste après A1 (agent nu, un seul outil, clos le 2026-09-19). A2 est une
tâche technique — pas de bénéficiaire côté utilisateur, portée par
l'exploitant : voir le détail de chaque étape d'une réponse (temps,
argent) alors que rien de tout ça n'est aujourd'hui observable.

`increments.md` laissait volontairement ouvert le choix de l'outil de
restitution : "Langfuse est le candidat noté dans TODO.md, mais son
auto-hébergement est devenu lourd [...] Décision reportée." Cette spec
tranche cette décision, et trois autres, avant tout code.

## Décisions actées pendant le brainstorming

- **Granularité : un span par appel LLM et par appel d'outil**, aussi
  bien côté agent (`app/agent_us2/loop.py`) que côté retrieval
  (`app/retrieval/decomposition.py`, `jugement.py`, `guardrail.py`,
  recherche dense dans `retrieval.py`). C'est le niveau où "temps et
  argent" ont un sens concret — pas le tour de boucle dans son ensemble,
  qui mélangerait plusieurs coûts.

- **Langfuse Cloud retenu, mais faiblement couplé** : le code applicatif
  ne dépend que d'OpenTelemetry (SDK/API standard), jamais du SDK
  Langfuse directement. Les spans sont exportés en OTLP vers Langfuse
  Cloud. Changer de backend plus tard (Grafana Tempo, un Langfuse
  self-hébergé si le besoin grandit, etc.) ne touchera que la
  configuration de l'exporteur, jamais le code instrumenté. Ça tranche
  la décision reportée d'`increments.md` : cloud pour éviter la lourdeur
  du self-hébergement (5 services, 16 Go de RAM recommandés), OTel pour
  ne pas se lier au choix.

- **Exporteur local JSONL en complément**, pas seulement pour le
  développement hors-ligne : `logs/traces_agent_us2.jsonl`, même
  convention que les `.log` déjà existants du projet
  (`logs/agent_us2.log`, `logs/api_regles.log`). Bascule par variable
  d'environnement `OTEL_EXPORTER` (`otlp` ou `jsonl`, défaut `jsonl`).
  Répond au critère C20 ("opérationnel au moins en local suffit") sans
  dépendre d'un compte Langfuse pour développer ou tester.

- **Contenu des traces : texte brut autorisé pour l'instant.** Décision
  explicitement assumée après discussion, pas un oubli : on est en phase
  de développement, sans utilisateur réel. C2 (anonymisation + règles de
  journalisation, plus tard dans `increments.md`) protégera les échanges
  à partir de son arrivée — pas rétroactivement. Alternative envisagée et
  écartée : ne pas envoyer le texte brut avant C2, écartée au motif
  qu'un filtrage partiel ajouté puis retiré risquerait d'être oublié en
  l'état ; plus simple d'assumer la fenêtre d'exposition et de laisser
  C2 la fermer proprement en une fois.

- **`trace_id` exposé dans la réponse HTTP** (`QuestionReponse`) :
  critère "exécutable et observable seule" de `increments.md` — sans
  identifiant retourné au client, il n'y aurait aucun moyen de relier
  une réponse donnée à sa trace, ni dans Langfuse ni dans le fichier
  JSONL local.

## Architecture

```text
POST /questions
      │
      ▼
Boucle agent (A1, voir A1_boucle_et_premier_outil.drawio)
appels LLM + appels d'outils (agent_us2, retrieval)
      │  a chaque appel
      ▼
Span OpenTelemetry (duree, cout, nom de l'etape, resultat)
      │
      ▼
   OTEL_EXPORTER ?
      │
   ┌──┴───────────────┐
   │otlp               │jsonl
   ▼                   ▼
Langfuse Cloud    logs/traces_agent_us2.jsonl
(service externe)      (local)

Reponse HTTP { ..., trace_id } ─── permet de retrouver la trace
                                    ci-dessus, quel que soit l'exporteur
```

Détail complet et rendu visuel : `A2_instrumentation.drawio` (schéma
validé, voir pièce jointe carte #24).

## Ce que cette spec ne couvre pas

- La création du compte/projet Langfuse Cloud (sous-tâche Kanboard #23)
  reste une étape manuelle, hors code — le développement et les tests
  fonctionnent entièrement en mode `jsonl` sans elle.
- Le filtrage du contenu des traces (anonymisation) : hors scope
  assumé, voir décision ci-dessus — c'est le travail de C2.
- Le bug déjà identifié de journalisation de la question brute dans la
  recherche dense en production (`increments.md`, section "Le piège de
  la journalisation") : signalé, pas corrigé ici, reste un chantier
  séparé.

## Suite

Plan d'implémentation détaillé (fichiers, tests, code) :
`docs/superpowers/plans/2026-09-20-a2-instrumentation-implementation.md`.
