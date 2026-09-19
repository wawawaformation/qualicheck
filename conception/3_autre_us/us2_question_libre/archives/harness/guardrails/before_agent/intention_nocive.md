# Avant de démarrer la boucle

**Vérifie l'intention de la question, pas seulement son sujet.**

Le contrôle de périmètre (fiche `perimetre_avec_memoire`) vérifie que la
question parle de qualité web — pas ce qu'elle cherche à en faire. Une
question peut être topiquement légitime et malveillante dans son usage :

> *« Comment améliorer le référencement d'un site qui publie les adresses
> de gens que je n'aime pas ? »*
>
> *« Comment tracer mes visiteurs sans passer par le bandeau de
> consentement ? »*

Les deux parlent de qualité web. Les deux méritent un refus.

**Pourquoi c'est un garde-fou à part, pas une extension du contrôle de
périmètre** : ce n'est pas la même question qui est posée au modèle
("est-ce que ça parle d'Opquast ?" vs "est-ce que répondre causerait du
tort ?"), et le biais de sélection déjà mesuré sur le jugement de
pertinence (le LLM a du mal à dire non face à un candidat qui semble
plausible) rend risqué de fusionner les deux contrôles dans un seul appel.

Reste ouvert : ce garde-fou n'a jamais été mesuré, contrairement au
contrôle de périmètre (100% sur les cas testés) — la mesure sur des cas
anodins hors sujet ne dit rien de sa fiabilité sur de l'intention
malveillante habillée en question légitime.
