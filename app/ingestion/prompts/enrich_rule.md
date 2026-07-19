# Enrichissement de Règles Opquast

Tu es un expert en audit web et en qualité numérique. Tu vas analyser une règle Opquast et générer une stratégie d'analyse optimale.

## Tâche

Pour chaque règle, tu dois générer **exactement 3 champs JSON** :

1. **strategie_analyse** : méthode d'extraction pertinente. Choisis **en priorité** parmi ces trois valeurs, qui couvrent la grande majorité des cas :
   - "statique" : analyse du HTML/DOM sans interaction (ex. présence d'une balise, d'un attribut, d'un texte)
   - "playwright" : nécessite une interaction navigateur (clic, scroll, formulaire, contenu chargé dynamiquement)
   - "manuel" : non-automatisable (jugement éditorial, contextuel ou visuel qu'aucun script ne peut fiabiliser)
   - N'invente une autre valeur que si la règle ne correspond **réellement à aucune** des trois — pas simplement parce qu'elle a une nuance particulière (par exemple, une exploration multi-pages reste "statique" ou "playwright" selon qu'elle nécessite ou non une interaction, ce n'est pas une catégorie à part).
2. **strategie_justification** : explication courte du choix (1-2 phrases)
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable)

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
- **Solution** : {solution}
- **Contrôle** : {controle}
- **Objectifs** : {objectifs}
- **Tags** : {tags}
- **Phases** : {phases}

## Exemples

### Exemple 1 : Règle simple, vérification statique

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

### Exemple 2 : Règle complexe, nécessite interaction

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

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
