# Avant de démarrer la boucle

**Vérifie que la question a un rapport avec Opquast, en tenant compte de
l'historique de la discussion.**

Une seule fois par tour, avant que l'agent commence à réfléchir.

Pourquoi avec l'historique : le garde-fou déjà en place côté API refuse
parfois à tort une question de vocabulaire métier (ex. "remboursement",
"zone desservie") qui semble hors sujet toute seule, mais qui ne l'est
pas dans le fil de la conversation. Ce garde-fou-ci corrige ça.

Si hors sujet : réponse de refus immédiate, la boucle ne démarre pas.
