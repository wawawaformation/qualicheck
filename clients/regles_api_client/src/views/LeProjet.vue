<template>
  <main class="page-contenu">
    <h1 class="page-contenu__titre">Le projet QualiCheck</h1>

    <h2>Présentation</h2>
    <p>
      QualiCheck est un assistant d'aide à l'audit de qualité web, construit
      autour du référentiel Opquast (245 règles de qualité web).
    </p>

    <h2>Comment ça fonctionne aujourd'hui</h2>
    <p>
      Le référentiel Opquast est enrichi par un pipeline d'ingestion appuyé
      sur un modèle de langage (LLM) : chaque règle reçoit une stratégie
      d'analyse (statique, Playwright, vision, manuelle), des outils, des
      objectifs et un guide d'analyse.
    </p>
    <p>
      Cet enrichissement est ensuite revu par un référent humain, qui peut
      annoter une règle mal classée ; l'agent d'enrichissement en tient
      compte au prochain passage. C'est ce que fait cette interface.
    </p>

    <h2>Les fonctionnalités à venir</h2>

    <h3>Question libre (prochain développement)</h3>
    <p>
      Un utilisateur pose une question sur une URL ou une capture d'écran ;
      le système répond par recherche sémantique (RAG) dans le référentiel
      Opquast enrichi, avec des garde-fous (guardrails) et une mémoire de la
      session en cours. C'est la prochaine fonctionnalité développée.
    </p>

    <h3>Audit assisté</h3>
    <p>
      Un crawl léger explore un site, l'utilisateur sélectionne les pages et
      les règles à auditer, un agent LLM génère des constats page par page,
      dialogue avec l'utilisateur pour les affiner, puis produit un rapport
      final validé par un humain à chaque étape — l'IA assiste l'auditeur,
      elle ne se substitue jamais à sa décision.
    </p>

    <h2>Contexte du projet</h2>
    <p>
      QualiCheck est développé par David LEGRAND dans le cadre d'une
      formation certifiante Développeur IA (titre professionnel / RNCP). La
      revue du référentiel (ce que vous utilisez ici) est implémentée ; la
      question libre et l'audit assisté sont encore en conception.
    </p>

    <h2>Licence du contenu</h2>
    <p>
      Le référentiel Opquast enrichi est diffusé sous licence CC BY-SA 4.0,
      avec le soutien d'Élie Sloïm (Opquast). Voir la page « Mentions
      légales » pour le reste du contenu et du code.
    </p>
  </main>
</template>
