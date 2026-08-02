<template>
  <main class="page-contenu">
    <h1 class="page-contenu__titre">Le projet QualiCheck</h1>

    <h2>Présentation</h2>
    <p>
      QualiCheck est un assistant d'aide à l'audit de qualité web, construit
      autour du référentiel Opquast (245 règles de qualité web).
    </p>

    <h2>Comment ça fonctionne</h2>
    <p>
      Le référentiel Opquast est enrichi par un pipeline d'ingestion appuyé
      sur un modèle de langage (LLM) : chaque règle reçoit une stratégie
      d'analyse (statique, Playwright, vision, manuelle), des outils, des
      objectifs et un guide d'analyse.
    </p>
    <p>
      Cet enrichissement est ensuite revu par un référent humain, qui peut
      annoter une règle mal classée ; l'agent d'enrichissement en tient
      compte au prochain passage.
    </p>

    <h2>Contexte du projet</h2>
    <p>
      QualiCheck est développé par David LEGRAND dans le cadre d'une
      formation certifiante Développeur IA (titre professionnel / RNCP). Le
      projet est en cours de construction ; certaines fonctionnalités (audit
      automatisé, question libre) sont encore en conception.
    </p>

    <h2>Licence du contenu</h2>
    <p>
      Le référentiel Opquast enrichi est diffusé sous licence CC BY-SA 4.0,
      avec le soutien d'Élie Sloïm (Opquast). Voir la page « Mentions
      légales » pour le reste du contenu et du code.
    </p>
  </main>
</template>
