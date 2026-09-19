# Autour de chaque exécution d'outil

**Vérifie que l'utilisateur a l'autorité sur le site avant d'aller le
chercher** — pour `lire_url`, `verifier_avec_navigateur`, `valider_marquage`.

Ces trois outils font parler notre serveur à un site tiers. Sans
vérification, l'agent devient un outil de reconnaissance gratuit : une
quinzaine de règles Opquast révèlent la posture de sécurité d'un site
(HTTPS absent, certificat invalide, en-tête de sécurité manquant,
intégrité des ressources tierces...) — l'équivalent d'un rapport de
faiblesses pour quelqu'un qui voudrait attaquer ce site. Et c'est
l'adresse IP de QualiCheck qui apparaît dans les journaux du site visé,
pas celle de l'utilisateur.

La capture d'écran n'a pas ce problème : l'utilisateur a déjà le contenu,
personne n'est sollicité à sa place.

**Deux niveaux, selon l'usage** :
- **Déclaration** (l'utilisateur affirme être propriétaire ou mandaté) —
  suffisant pour un usage ponctuel.
- **Preuve de propriété** (fichier ou enregistrement DNS à déposer, comme
  Google Search Console) — exigée si le même domaine est sondé de façon
  répétée, seul signal distinguant un usage normal d'un usage qui
  ressemble à du scan.

Reste ouvert : le seuil de répétition qui déclenche la preuve, et le
mécanisme de vérification lui-même.
