# Avant chaque appel au modèle

**Arrête la boucle si elle tourne trop longtemps** sur une même question.

Chaque tour de boucle coûte un appel réel (parfois un outil payant). Sans
limite, une question qui met l'agent en tâtonnement peut boucler sans
fin.

Si la limite est atteinte : réponse honnête à l'utilisateur, jamais une
erreur brute ou un silence.

Reste ouvert : le nombre exact — à mesurer sur des questions réelles une
fois l'agent construit, pas à deviner maintenant.
