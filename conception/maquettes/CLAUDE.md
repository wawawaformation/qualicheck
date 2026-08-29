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

## Règle : aucun JavaScript dans les maquettes

Les maquettes (composants isolés et écrans assemblés) restent du HTML/CSS
statique, sans comportement interactif réel (pas de redimensionnement au
glisser, pas de filtrage dynamique, pas de drag&drop...). Un comportement
interactif repéré comme nécessaire est documenté comme exigence pour
l'implémentation réelle (le futur client Vue.js), pas simulé ici avec du JS.

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

Exigences repérées pendant le maquettage, à reprendre lors de l'implémentation Vue.js (pas simulées en JS ici, cf. règle ci-dessus) :

- Colonne de liste des règles (`ecran-revue-regles__liste`) redimensionnable par
  l'utilisateur (glisser le bord droit) pour laisser plus ou moins de place au
  panneau de détail/annotation — largeur mini/maxi à définir lors de
  l'implémentation.
- Gestion de la clé API (`ecran-cle-api.html`, 2 états : aucune clé / clé
  enregistrée) : l'utilisateur peut la renseigner, la modifier ou la
  supprimer à tout moment via l'entête (remplace les 3 liens habituels du
  menu — "Renseigner ma clé API" si aucune clé, "Modifier ma clé API" /
  "Supprimer ma clé API" si une clé est enregistrée). Si l'utilisateur tente
  d'enregistrer une annotation sans clé valide, il est redirigé vers cet
  écran. Champ unique (le jeton suffit à l'identification côté serveur, cf.
  `app/api_regles/auth.py`), pas de champ nom d'utilisateur. Stockage côté
  client (localStorage/sessionStorage) non encore décidé — à trancher lors
  de l'implémentation.
- Pied de page : sur les écrans d'administration US0 (revue des règles, clé
  API), les liens "Accueil" et "Préparer un audit" (destinés à l'utilisateur
  final) sont retirés de `pied-de-page__nav` — seuls restent "Le projet",
  "Mentions légales", "Politique des données".

2. Utilisateur : connexion et profil (`maquettes/utilisateur/ecran-connexion.html`,
   `maquettes/utilisateur/ecran-profil.html`)

Dossier séparé de `US2/` : le compte utilisateur (connexion, profil,
suppression) est commun à US1 et US2, pas propre à la question libre — cf.
`conception/3_autre_us/profil/spec.md`. Chaque écran garde son propre
`style/` (même convention que `US0/`, `US2/`), pas de dépendance croisée vers
`US2/style/`.

Basés sur `conception/3_autre_us/us2_question_libre/cas_utilisation_us2.drawio`
et `scenarios.md` (cas d'utilisation "Se connecter", "Gérer mon profil",
"Supprimer une discussion"/"Supprimer mon compte"). Réutilisent le pattern
2 états déjà établi par `ecran-cle-api.html` (US0), adapté : ici le jeton
identifie un profil (nom/prénom), pas seulement un droit d'écriture.

Exigences repérées pendant le maquettage, à reprendre lors de l'implémentation Vue.js (pas simulées en JS ici, cf. règle ci-dessus) :

- `ecran-connexion.html` : jeton stocké côté client (localStorage, même choix
  que `ecran-cle-api.html` et déjà utilisé par `regles_api_client`) — envoyé
  ensuite en `Authorization: Bearer` sur chaque appel `api_business`.
- `ecran-profil.html`, bouton "Se déconnecter (sur cet appareil)" : efface le
  jeton du stockage local uniquement — ne supprime rien côté serveur (le
  jeton reste valide, réutilisable en se reconnectant). Distinct de
  "Supprimer mon compte".
- `ecran-profil.html`, "Supprimer mon compte" : nécessite une étape de
  confirmation explicite (case à cocher + bouton dédié) avant l'appel réel —
  jamais de suppression au premier clic. Cascade sur **toutes** les données
  liées au compte — discussions (US2), audits (US1), pas seulement les
  discussions (cf. `conception/3_autre_us/profil/spec.md`).
- Le décompte affiché dans le bandeau de confirmation ("vos N discussions et
  M audits") doit être injecté dynamiquement, pas une valeur figée comme
  dans la maquette.
