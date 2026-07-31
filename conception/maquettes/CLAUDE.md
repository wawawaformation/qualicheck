# Maquettage 

Les maquettes et l'intégration doivent respecter les règles Opquast :
<https://regles.qualicheck.koabana.fr/regles>

## Les fichiers d'exemple et d'appui

Tu trouveras les fichiers d'exemple et d'appui dans le répertoire `directive`.
Au fur et à mesure des questions et des réponses, tu compléteras ce répertoire avec petits fichiers réutilisables, ainsi
que ce fichier claude.

Le fichier directive/accueil_a_revoir.png est un exemple écran plutôt réussi de la page d'accueil mais il n'intégrait pas
encore l'US 2 question libre.
Par contre les espaces, les volumes, les composants ainsi que le style sont déjà bien définis et peuvent servir de base pour les autres écrans.

Les fichiers elements1.pdf et elements2.pdf sont des fichiers d'appui pour les composants de l'interface. Ils sont à consulter pour comprendre les éléments de l'interface, leur style et leur comportement.

variables.css est un fichier de variables CSS qu'il faudra completer.

Les icônes utilisées dans l'interface sont des Bootstrap Icons.

## Composants HTML/CSS construits depuis Accueil.pdf

Le dossier `directive/composants/` contient la decoupe HTML de la page d'accueil :
un fichier `.html` autonome par composant (bouton, champ-texte, entete, etape-item,
section-etapes, section-hero, section-texte, pied-de-page), consultable isolement.
Pas d'assemblage en page complete pour l'instant (pas de moteur de template choisi).

Conventions a respecter pour tout nouveau composant :

- Tous les CSS (dont `variables.css`) vivent dans `composants/CSS/`, references
  depuis les `.html` en `CSS/xxx.css`.
- `<title>` = nom du composant directement (ex. `bouton`, pas "Composant — Bouton").
- Aucune dependance CDN : Bootstrap Icons et la police Inter sont en fichiers locaux
  dans `composants/CSS/` et `composants/CSS/fonts/` (pas de lien jsdelivr/Google Fonts).
- Penser systematiquement aux etats `:hover` des elements interactifs.


## Composants de l'interface

Au fur et à mesure de la conception, tu complèteras ce dossier avec des petits composant réutilisables. Pour l'instant, tu peux te baser sur les fichiers elements1.pdf et elements2.pdf pour comprendre les composants de l'interface, leur style et leur comportement ainsi que acceuil_a_revoir.png pour le style général de l'interface.

### Les 3 enseble d'interfaces

1. US0 : amélioration des règles et de leur enrichissement
Le fichier ecran_revue_regles_a_nettement _ameliorer.html reflete parfaitement le comportement fonctionnel mais n'est pas en accord avec le style général de l'interface. Il faudra donc le reprendre pour qu'il soit en accord avec le style général de l'interface.