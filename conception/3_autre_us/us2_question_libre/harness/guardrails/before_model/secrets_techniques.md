# Avant chaque appel au modèle

**Détecte les identifiants techniques avant qu'ils partent vers le
modèle** — clé d'API, jeton de session, mot de passe visible dans une
capture d'écran ou une URL collée dans la question.

Ce n'est ni une donnée personnelle (l'anonymisation ne l'attrape pas), ni
hors sujet (le contrôle de périmètre ne l'attrape pas) : un professionnel
qui partage le back-office de son site pour poser une question peut
laisser une clé visible à l'écran sans y penser. Ça part quand même chez
un fournisseur tiers (Azure, Infomaniak, Ollama).

Reste ouvert : la détection est plus dure sur une image que sur du texte
(même limite que l'anonymisation d'une capture d'écran).
