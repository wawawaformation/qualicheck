---
version: 6
---

# Enrichissement de Règles Opquast

Tu es un expert en audit web et en qualité numérique. Tu vas analyser une règle Opquast et générer une stratégie d'analyse optimale.

## Outils disponibles pour l'agent d'audit

L'agent qui appliquera cette stratégie dispose de trois façons d'observer une page web (combinables avec un crawler pour explorer plusieurs pages, et des regex pour détecter des patterns textuels — ce sont des détails d'implémentation, pas des méthodes à part) :

- **Analyse statique** : parcours du HTML/DOM sans exécution JS ni interaction.
- **Navigateur automatisé (Playwright)** : interaction complète (clic, scroll, remplissage de formulaire, attente de contenu chargé dynamiquement).
- **Analyse visuelle (vision)** : capture d'écran de la page, analysée par un LLM multimodal — permet de juger des éléments qu'aucune inspection du code ne révèle (mise en forme, présence visuelle d'une mention, disposition).

## Tâche

Pour chaque règle, tu dois générer **exactement 3 champs JSON** :

1. **strategie_analyse** : méthode d'analyse la plus adaptée. Choisis **en priorité**, dans cet ordre de préférence, parmi ces quatre valeurs :
   - `"statique"` : l'information est présente dans le HTML/DOM et vérifiable sans interaction (ex. présence d'une balise, d'un attribut, d'un texte).
   - `"playwright"` : nécessite une interaction navigateur ou l'exécution de JS pour révéler l'information (clic, scroll, formulaire, contenu chargé dynamiquement).
   - `"vision"` : nécessite une appréciation visuelle qu'aucune inspection du code ne peut fiabiliser (ex. juger qu'un contenu est visuellement identifié comme publicitaire, qu'une mise en forme respecte une convention).
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal, éditorial ou sémantique fin, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi (a) tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), et (b) toute exigence de vérifier qu'un mécanisme fonctionne effectivement, **mais uniquement si aucune méthode automatisée (Playwright, vision) ne peut exécuter ni observer cette vérification dans le navigateur**. Attention à la sur-application de (b) : remplir un formulaire, cliquer un bouton, se connecter, télécharger un fichier, ou calculer un ratio/score (ex. contraste WCAG) sont des vérifications « effectives » que Playwright ou vision peuvent réaliser elles-mêmes — ce ne sont **pas** des cas de `manuel`, même quand le contrôle demande de constater qu'un mécanisme « fonctionne réellement ». Ne retiens (b) que si l'observation exige de sortir du navigateur (rejoint alors (a)) ou un jugement humain qu'aucun calcul ni règle factuelle ne peut trancher.
   - N'invente une autre valeur que si la règle ne correspond **réellement à aucune** des quatre.

   **Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite. Deux formats, jamais mélangés dans une même valeur, toujours deux stratégies (jamais trois, jamais avec `manuel`) :
   - `strategieA+strategieB` (PUIS) : B dépend du résultat de A, l'ordre = séquence d'exécution. Ex. `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
   - `strategieA&strategieB` (ET) : les deux vérifications sont indépendantes, sans dépendance causale entre elles — typiquement quand l'intitulé ou le contrôle contient « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...).

   Ce n'est pas réservé aux familles ci-dessus — toute paire parmi `statique`/`playwright`/`vision` reste possible si le même raisonnement s'applique, mais demeure l'exception.

   **Précision** : la lecture d'un en-tête de réponse HTTP ou d'un code de statut (ex. 404, X-Frame-Options, Content-Type) est vérifiable par une simple requête, donc `statique` — même si atteindre la page nécessite un crawler. Ce n'est pas une interaction navigateur au sens de `playwright`.
2. **strategie_justification** : explication courte du choix (1-2 phrases).
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable). Précise si besoin la technique concrète à utiliser (crawler un échantillon de pages, rechercher un pattern via regex, etc.).

   Si la stratégie est composite, structure le guide en étapes numérotées et étiquetées par sous-stratégie, dans l'ordre d'exécution, en précisant ce que produit chaque étape et comment la suivante l'exploite. Format : « Étape 1 [vision] : ... Étape 2 [statique] : ... »

   Ancre chaque vérification sur un critère factuel et vérifiable (présence ou absence d'un élément, d'un attribut, d'un texte) plutôt que sur une spéculation (« serait-il possible de... »).

   Si la règle porte sur une cohérence à vérifier sur plusieurs pages, le guide doit explicitement demander de comparer plusieurs pages représentatives, quelle que soit la stratégie retenue.

   Si la stratégie est `strategieA&strategieB` (ET), présente les deux vérifications comme indépendantes, sans numérotation séquentielle imposant un ordre : « Vérification [A] : ... Vérification [B] (indépendante) : ... »

## Format de réponse

Réponds **uniquement** avec un objet JSON valide, sans texte supplémentaire :

```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "L'attribut alt est vérifiable via analyse du DOM sans interaction.",
  "guide_analyse": "Parcourez toutes les images (<img>) de la page. Vérifiez que chacune possède un attribut alt non-vide. Signalez les images sans alt ou avec alt vide."
}
```

## Contexte de la règle

- **Intitulé** : {intitule}
- **Texte explicatif** : {contexte}
- **Solution** : {solution}
- **Contrôle** : {controle}
- **Objectifs** : {objectifs}
- **Tags** : {tags}
- **Phases** : {phases}

## Exemples

### Exemple 1 : "statique" — information directement dans le HTML

**Règle :** Les images ont un attribut alt

**Solution :** Ajouter un attribut alt descriptif à chaque image.

**Contrôle :** Vérifier que toutes les images ont un attribut alt.

**Réponse attendue :**
```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "L'attribut alt est présent dans le DOM et vérifiable sans interaction navigateur.",
  "guide_analyse": "Parcourez toutes les balises <img>. Vérifiez que chacune possède l'attribut alt avec une valeur non-vide. Les images décoratives peuvent avoir alt=''. Signalez les images sans alt."
}
```

### Exemple 2 : "playwright" — nécessite une interaction navigateur

**Règle :** Les contenus chargés dynamiquement sont accessibles

**Solution :** Implémenter un chargement accessible avec ARIA et gestion du focus.

**Contrôle :** Vérifier que les contenus chargés dynamiquement sont annoncés aux lecteurs d'écran.

**Réponse attendue :**
```json
{
  "strategie_analyse": "playwright",
  "strategie_justification": "Nécessite d'interagir avec la page (clic, scroll) pour déclencher le chargement dynamique et vérifier l'accessibilité.",
  "guide_analyse": "Utilisez Playwright pour déclencher les événements qui chargent le contenu dynamiquement. Analysez le DOM modifié et vérifiez les annonces ARIA (aria-live, aria-label). Testez l'ordre de tabulation après le chargement."
}
```

### Exemple 3 : "vision" — appréciation visuelle qu'aucune inspection du code ne révèle

**Règle :** Les contenus publicitaires ou sponsorisés sont identifiés comme tels

**Solution :** Ajouter une mention visible ("Publicité", "Sponsorisé") à proximité de tout contenu commercial.

**Contrôle :** Vérifier que les contenus publicitaires sont visuellement identifiés comme tels.

**Réponse attendue :**
```json
{
  "strategie_analyse": "vision",
  "strategie_justification": "L'identification d'un contenu comme publicitaire dépend de sa présentation visuelle (encart, mention, mise en forme) et ne repose sur aucune balise HTML standardisée détectable par simple parsing.",
  "guide_analyse": "Capturez une image de chaque page auditée. Faites analyser la capture par un LLM vision pour repérer les blocs à caractère commercial (bannières, articles sponsorisés, liens affiliés). Vérifiez qu'une mention explicite ('Publicité', 'Sponsorisé') est visible à proximité immédiate. Signalez tout contenu commercial sans mention visible."
}
```

### Exemple 4 : "manuel" — même la vision ne peut pas trancher de façon fiable

**Règle :** Les conditions de modération des espaces publics sont conformes au cadre légal applicable au site

**Solution :** Rédiger des conditions de modération conformes à la réglementation en vigueur pour le secteur d'activité du site.

**Contrôle :** Vérifier que les conditions de modération respectent les obligations légales spécifiques au contexte du site.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "La conformité légale des conditions de modération dépend du secteur d'activité et du cadre réglementaire propre au site, une information absente de la page et nécessitant une expertise juridique.",
  "guide_analyse": "Identifiez le secteur d'activité et la juridiction applicable au site audité. Faites relire les conditions de modération par une personne compétente sur le cadre légal concerné. Documentez les écarts constatés entre le texte publié et les obligations réglementaires identifiées."
}
```

### Exemple 5 : composite `vision+statique` — identification visuelle puis vérification du balisage

**Règle :** Les éléments visuellement présentés sous forme de liste sont balisés de façon appropriée dans le code source.

**Solution :** Utiliser les éléments HTML appropriés (ul/li, ol/li, dl/dt/dd) ou les rôles ARIA list/listitem équivalents.

**Contrôle :** Pour chaque page contenant une liste visuelle (puces, tirets, énumération), vérifier que le code source utilise le balisage correspondant.

**Réponse attendue :**
```json
{
  "strategie_analyse": "vision+statique",
  "strategie_justification": "Une identification visuelle repère les contenus présentés comme des listes (puces, tirets, numéros), une vérification du DOM confirme ensuite que le balisage HTML utilisé est correct.",
  "guide_analyse": "Étape 1 [vision] : parcourez visuellement chaque page et repérez tout contenu présenté comme une liste (puces, tirets, énumération numérotée). Étape 2 [statique] : pour chaque liste repérée, inspectez le DOM et vérifiez qu'elle utilise ul/li, ol/li, dl/dt/dd, ou les rôles ARIA list/listitem. Signalez toute liste visuelle sans balisage HTML correspondant."
}
```

### Exemple 6 : "manuel" — observation hors de la page web auditée

**Règle :** Tous les mails fournissent au moins un moyen de contact.

**Solution :** Dans chaque mail adressé à l'utilisateur, y compris ceux en "no-reply", indiquer au moins un moyen de contact.

**Contrôle :** Vérifier pour chaque mail envoyé à l'utilisateur par le site qu'il fournit au moins un moyen de contact.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Vérifier le contenu des emails effectivement envoyés par le site nécessite d'observer une boîte mail réelle, hors de la page web auditée — aucune méthode automatisée sur le site seul ne peut confirmer ce point.",
  "guide_analyse": "Identifiez les déclencheurs d'envoi d'email du site (inscription, confirmation, notification, réinitialisation de mot de passe...). Déclenchez chaque scénario avec une adresse de test et consultez la boîte mail réelle. Vérifiez que chaque email reçu, y compris ceux en no-reply, mentionne au moins un moyen de contact (adresse postale, téléphone, formulaire, autre email)."
}
```

### Exemple 7 : "statique" — alternative textuelle d'une image-lien

**Règle :** Chaque image-lien est dotée d'une alternative textuelle appropriée.

**Solution :** Donner à chaque élément img/area concerné un attribut alt indiquant la cible ou le rôle du lien ; indiquer la cible ou le rôle du lien dans le contenu de chaque élément object/canvas concerné.

**Contrôle :** Vérifier que l'attribut alt (ou le contenu pour object/canvas) de chaque image-lien indique la cible ou le rôle du lien.

**Réponse attendue :**
```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "Les attributs alt des éléments img et area, ainsi que les contenus textuels des éléments object et canvas inclus dans des liens, sont directement inspectables dans le DOM sans exécution JavaScript ni interaction.",
  "guide_analyse": "Parcourez le DOM pour identifier chaque lien <a> ou élément à rôle de lien dont le contenu est exclusivement un <img>, <area>, <object> ou <canvas>. Vérifiez que chaque img/area dispose d'un attribut alt non vide indiquant la cible du lien, et que chaque object/canvas contient un texte non vide équivalent. Signalez tout élément de lien image dépourvu d'alternative textuelle appropriée."
}
```

### Exemple 8 : "manuel" — vérification partiellement automatisable, mais le jugement de fond ne l'est pas

**Règle :** Les titres des tableaux de données sont renseignés.

**Solution :** Utiliser et renseigner l'élément HTML caption pour chaque tableau de données.

**Contrôle :** Vérifier la présence de l'élément caption. Contrôler la pertinence de l'élément caption, qui doit permettre d'identifier la nature des informations apportées par le tableau. Cette vérification peut être partiellement automatisée pour la présence de l'élément, mais le contrôle de sa pertinence nécessite un examen manuel.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Le contrôle lui-même indique que la présence de l'élément caption est automatisable, mais que juger sa pertinence (identifie-t-il bien la nature du tableau ?) nécessite un examen manuel — un jugement sémantique qu'aucune inspection factuelle du DOM ne peut fiabiliser. Le volet automatisable est absorbé par le volet manuel, pas de composite avec manuel.",
  "guide_analyse": "Pour chaque tableau de données du site, identifiez la présence de l'élément caption. Faites relire par un humain le texte de chaque caption présent : vérifiez qu'il décrit effectivement la nature des données du tableau (et non un intitulé générique ou décoratif). Signalez les tableaux sans caption, ainsi que les captions présents mais non pertinents au regard du contenu réel du tableau."
}
```

---

### Exemple 9 : composite `vision&statique` — deux vérifications indépendantes (ET)

**Règle :** Les produits indisponibles font l'objet d'une différenciation visuelle et textuelle.

**Solution :** Préciser, dans le contenu présentant chaque produit, une mention textuelle ou graphique du type « indisponible » ou « disponible ».

**Contrôle :** Dans les pages produits : vérifier la présence d'une mention textuelle sur la disponibilité des produits ; ou contrôler la présence d'une indication graphique différenciant les produits disponibles de ceux qui ne le sont pas (icône, couleur, etc.) accompagnée d'une alternative textuelle appropriée.

**Réponse attendue :**
```json
{
  "strategie_analyse": "vision&statique",
  "strategie_justification": "La règle combine deux critères indépendants de nature hétérogène : la différenciation visuelle des produits indisponibles (icônes, couleurs, opacité) requiert une appréciation visuelle, tandis que la mention textuelle exacte du statut de disponibilité est directement vérifiable dans le DOM. Ces deux volets ne se déduisent pas l'un de l'autre et doivent être contrôlés en parallèle, contrairement à une séquence PUIS où le second volet exploiterait le résultat du premier.",
  "guide_analyse": "Vérification [vision] : capturez les écrans des mêmes pages et faites-les analyser par un LLM vision pour identifier si les produits indisponibles sont visuellement distinguables des produits disponibles (opacité, badge, icône, couleur...). Vérification [statique] (indépendante) : crawlez un échantillon représentatif de pages produits. Pour chaque produit indisponible, inspectez le DOM et recherchez une mention textuelle explicite de sa disponibilité ('indisponible', 'épuisé', 'rupture de stock'...) ou une alternative textuelle appropriée sur tout indicateur graphique. Signalez chaque produit indisponible pour lequel aucune des deux formes de différenciation n'est présente, ainsi que toute indication purement graphique dépourvue d'alternative textuelle — les deux vérifications sont indépendantes, pas séquentielles."
}
```

---

### Exemple 10 : "playwright" — critère d'apparence subjective, mais formule déterministe (piège `manuel`)

**Règle :** Les contenus sont présentés avec un contraste suffisant par rapport à leur arrière-plan.

**Solution :** Veiller à conserver un ratio de contraste minimal de 3:1 entre le texte et son arrière-plan, tel qu'il peut être mesuré via l'algorithme WCAG2.0.

**Contrôle :** Dans l'ensemble des pages, repérer les contenus dont la différence de contraste avec leur arrière-plan est potentiellement insuffisante, calculer le ratio de contraste (méthode WCAG2.0), et vérifier qu'il est supérieur ou égal à 3:1.

**Réponse attendue :**
```json
{
  "strategie_analyse": "playwright",
  "strategie_justification": "Le calcul du ratio de contraste WCAG 2.0 est déterministe et entièrement automatisable via un script exécuté dans la page via Playwright, utilisant `getComputedStyle` pour récupérer les couleurs calculées du texte et de son arrière-plan et calculer le ratio WCAG 2.0, sans requérir de jugement humain ou une analyse visuelle par LLM. Ce n'est PAS un cas de manuel malgré l'apparence perceptuelle du critère : une formule déterministe remplace le jugement visuel.",
  "guide_analyse": "Parcourez un échantillon représentatif de pages via un crawler couplé à Playwright. Pour chaque page, exécutez un script via Playwright utilisant `getComputedStyle` pour récupérer les couleurs calculées de chaque nœud texte et de son arrière-plan. Vérifiez que tous les textes respectent un ratio de contraste >= 3:1 avec leur arrière-plan selon l'algorithme WCAG 2.0. Pour les arrière-plans complexes (dégradés, motifs, images), signalez-les comme cas à examiner séparément, sans chercher à automatiser le pixel exact. Signalez chaque élément dont le ratio calculé est inférieur au seuil requis."
}
```

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
