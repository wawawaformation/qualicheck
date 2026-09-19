# Archives — conception initiale de l'agent US2

Ce dossier contient la **première conception de l'agent US2**, faite d'un
seul tenant les 18 et 19 septembre 2026 : le schéma d'architecture, les
9 fiches d'outils, les 10 fiches de garde-fous répartis par point
d'accroche, et la topologie infra/LLM.

## Pourquoi c'est ici et pas dans la conception vivante

Cette conception était **complète d'avance**. C'est précisément ce dont
la construction par marches s'éloigne : on a décidé le 2026-09-19 de
construire par petits incréments, chacun apportant une seule chose et
mesurable seul
(`jury/decisions/2026-09-19-decouper-l-agent-en-marches.md`).

Ces documents ne pilotent donc plus le travail. Ils restent **utiles
comme matière** : chaque marche, au moment d'être attaquée, vient y
puiser ce qui la concerne.

## Comment s'en servir

- Ne pas réactiver le dossier en bloc. Une fiche ne redevient vivante que
  reprise dans le cadre d'une marche précise.
- Ce qui y est écrit a été raisonné et parfois mesuré (les répartitions
  d'outils par stratégie d'analyse, les chiffres OWASP, les limites
  connues du garde-fou de périmètre) — donc à relire plutôt qu'à
  réinventer.
- Ce qui y est écrit n'a pas été vérifié depuis. Un chemin de fichier, un
  nom de route ou une valeur de configuration peut avoir changé.

## Ce qui reste vivant ailleurs

- L'échelle des marches : `../increments/`
- La sécurité (modèle de menace, protections, données personnelles) :
  `../../securite.md`
- Les décisions et leur justification : `jury/decisions/`
