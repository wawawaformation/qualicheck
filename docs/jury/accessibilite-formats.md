# Rendre un support accessible — PDF, PPTX/ODP, ODT/MD

Aide-mémoire pratique, pas un cours. Objectif : produire des supports conformes au
critère « format accessible » (C6, et par extension C8, C11, C18, C19, C20), au
sens Valentin Haüy / AcceDe — accessibilité pour lecteur d'écran et déficience
visuelle, pas seulement « lisible à l'œil ».

Le principe commun à tous les formats : **le contenu doit exister comme texte
structuré**, pas seulement comme apparence visuelle. Un lecteur d'écran ne voit pas
une mise en page, il lit une structure.

**Format retenu pour les veilles** (`docs/jury/veille/README.md`) : un **ODP** de
présentation avec notes, pour la restitution orale, et un **MD ou ODT** de lecture,
autonome. Les conseils PPTX ci-dessous s'appliquent identiquement à l'ODP —
LibreOffice Impress (`.odp`) et PowerPoint (`.pptx`) partagent le même modèle de
diapositives, dispositions et volet d'accessibilité. Le format de lecture (MD/ODT)
est traité dans sa propre section, plus bas.

## PDF (carrousel, export de synthèse)

### À faire

- **Générer depuis un traitement de texte structuré** (Word, LibreOffice, Markdown
  → Pandoc), jamais depuis une capture d'écran ou un export image-par-page. Un PDF
  "scanné" ou composé d'images n'a aucun texte à lire.
- **Utiliser les styles de titre** (Titre 1, Titre 2...) plutôt que du texte mis en
  gras/agrandi à la main — c'est ce qui construit l'ordre de lecture et la
  navigation par en-têtes pour un lecteur d'écran.
- **Alternative textuelle sur chaque image** — un texte court décrivant ce que
  l'image apporte à la compréhension, pas son nom de fichier.
- **Contraste minimum 4.5:1** entre texte et fond (norme WCAG AA). Les dégradés et
  le texte clair sur fond clair (fréquents dans les carrousels "design") posent
  problème.
- **Langue du document déclarée** (français) dans les métadonnées.
- **Tableaux avec en-têtes de colonnes/lignes marqués**, pas de mise en page en
  tableau simulée avec des espaces.
- **Liens avec un intitulé explicite** (« Rapport CNIL 2026 », pas « cliquez ici »).

### À éviter

- Texte incrusté dans une image (screenshot de texte, citation en image stylisée)
  — invisible pour un lecteur d'écran.
- Information portée uniquement par la couleur (« en rouge = risque » sans autre
  indice).
- Export direct depuis un outil de carrousel/design sans repasser par une structure
  de titres.

### Vérifier

- **Acrobat / LibreOffice Draw** : vérificateur d'accessibilité intégré.
- **PAC (PDF Accessibility Checker)**, gratuit, référence pour la conformité PDF/UA.
- Test rapide et gratuit : sélectionner tout le texte du PDF (`Ctrl+A`) et le coller
  dans un éditeur — si le résultat est vide ou incohérent, le document n'a pas de
  contenu textuel exploitable.

## PPTX (présentations)

### À faire

- **Utiliser les dispositions (layouts) intégrées** de PowerPoint/Impress
  (zone de titre, zone de contenu), jamais des zones de texte libres positionnées
  à la main — c'est ce qui détermine l'ordre de lecture pour un lecteur d'écran.
- **Chaque diapositive a un titre unique**, même s'il n'est pas affiché
  visuellement en grand (utile pour la navigation par lecteur d'écran).
- **Vérifier l'ordre de lecture** via le volet dédié (PowerPoint : *Révision >
  Vérifier l'accessibilité* puis *Ordre de lecture*) — l'ordre visuel à l'écran et
  l'ordre de lecture logique divergent souvent quand des objets sont déplacés.
- **Alternative textuelle sur chaque image, graphique, icône.**
- **Taille de police minimum ~18-20 pt** et contraste suffisant sur fond de
  diapositive (attention aux thèmes sombres avec texte de couleur).
- **Sous-titres/transcription** si la présentation inclut une piste audio ou vidéo.

### À éviter

- Diapositives constituées d'une seule image pleine page (capture, infographie) —
  tout le contenu devient invisible pour un lecteur d'écran.
- SmartArt et graphiques complexes sans description textuelle équivalente.
- Convertir la présentation en images pour l'export (PDF image-par-slide) — reporte
  le problème du PPTX vers le PDF.

### Vérifier

- **PowerPoint / LibreOffice Impress** : vérificateur d'accessibilité intégré
  (*Révision > Vérifier l'accessibilité*), signale titres manquants, alternatives
  textuelles absentes, ordre de lecture, contraste.
- Relire la présentation en ne suivant que le **volet Plan** (mode texte seul) — ce
  que ce mode ne montre pas, un lecteur d'écran ne le lira pas non plus.

## MD / ODT (format de lecture autonome)

Le format qui pose structurellement le moins de risque des trois — l'accessibilité
y est presque acquise par construction, à condition de respecter quelques points.

### À faire

- **Markdown** : utiliser la hiérarchie de titres (`#`, `##`...) de façon continue,
  sans sauter de niveau — c'est elle qui construit la structure de navigation, un
  simple rendu à l'écran (moteur de rendu, éditeur) l'expose automatiquement à un
  lecteur d'écran.
- **ODT** : mêmes règles que le PDF ci-dessus — styles de titre (pas de mise en
  forme manuelle), alternatives textuelles sur les images, contraste, tableaux avec
  en-têtes.
- **Texte alternatif sur les images** dans les deux formats — un Markdown avec des
  captures d'écran non légendées perd le même bénéfice qu'un PDF ou un ODP.
- **Liens avec intitulé explicite**, comme pour le PDF.

### À éviter

- Tableaux Markdown utilisés pour la mise en page plutôt que pour de vraies données
  tabulaires — un lecteur d'écran annonce des cellules là où il n'y a pas de sens
  tabulaire.
- Blocs de code utilisés pour mettre en forme du texte qui n'est pas du code (le
  lecteur d'écran change de mode de lecture sans raison).

### Vérifier

- Un Markdown correctement structuré se vérifie à l'œil en ouvrant le sommaire
  généré automatiquement par la plupart des visionneuses/éditeurs (VS Code, GitHub,
  Pandoc `--toc`) — s'il est cohérent, la structure sous-jacente l'est aussi.
- **LibreOffice Writer** : même vérificateur d'accessibilité intégré que Draw/Impress
  pour l'ODT.

## Ce qui ne change rien au fond

Ces règles ne changent pas le contenu produit ni le temps de conception — elles
changent la façon de le construire dans l'outil (styles plutôt que mise en forme
manuelle, alternatives textuelles à la volée plutôt qu'ajoutées après coup). Le
coût réel est de prendre l'habitude tôt, pas de retravailler chaque support après
sa création.
