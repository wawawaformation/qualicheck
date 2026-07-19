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
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal fin, éditorial, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire.
   - N'invente une autre valeur que si la règle ne correspond **réellement à aucune** des quatre.
2. **strategie_justification** : explication courte du choix (1-2 phrases).
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable). Précise si besoin la technique concrète à utiliser (crawler un échantillon de pages, rechercher un pattern via regex, etc.).

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

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
