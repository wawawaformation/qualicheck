<template>
  <main class="page-contenu">
    <h1 class="page-contenu__titre">Politique des données</h1>

    <h2>Quelles données sont traitées</h2>
    <p>QualiCheck ne demande aucune création de compte utilisateur.</p>
    <p>
      La seule donnée saisie par l'utilisateur est la <strong>clé API</strong>
      nécessaire pour annoter une règle du référentiel (écran « Clé API »).
      Cette clé :
    </p>
    <ul>
      <li>est stockée uniquement dans le <code>localStorage</code> du navigateur de l'utilisateur ;</li>
      <li>
        n'est jamais transmise à un autre destinataire que l'API QualiCheck
        elle-même (<code>app/api_regles</code>), via l'en-tête
        <code>Authorization</code> ;
      </li>
      <li>
        n'est associée à aucun nom d'utilisateur : le serveur identifie un
        client déclaré par la clé elle-même, il ne trace pas d'auteur
        individuel des annotations.
      </li>
    </ul>

    <h2>Ce que QualiCheck ne fait pas</h2>
    <p>
      Aucun cookie de suivi ni outil d'analyse d'audience n'est mis en place
      à ce stade du projet.
    </p>

    <h2>Contenu du référentiel</h2>
    <p>
      Le référentiel Opquast enrichi, consulté sans authentification, est
      diffusé sous licence
      <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr">CC BY-SA 4.0</a>
      — voir la page « Mentions légales » pour l'attribution complète.
    </p>

    <h2>Contact</h2>
    <p>
      Pour toute question relative aux données traitées par QualiCheck :
      <a href="mailto:contact@david-legrand.fr">contact@david-legrand.fr</a>
    </p>
  </main>
</template>
