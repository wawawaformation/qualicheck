# Journal de veille

Sessions de veille technique et réglementaire. Entrées les plus récentes en premier.

Les sources suivies et la justification de leur fiabilité sont dans `sources.md`.

## Pourquoi ce journal existe

La compétence C6 exige des « temps de veille planifiés régulièrement (minimum
1h/semaine) ». C'est la seule exigence du référentiel qui ne peut pas être produite
après coup : on ne fabrique pas rétroactivement la preuve d'une régularité.

La veille est pratiquée en dehors de ce projet ; ce journal sert à en conserver la
trace datée, pas à la créer.

## Format d'une entrée

Volontairement léger — un journal qui demande vingt minutes de rédaction par semaine
est un journal abandonné au bout d'un mois.

```markdown
## AAAA-MM-JJ — durée

**Parcouru** : sources consultées

**Retenu** :
- ce qui change quelque chose pour le projet, ou pour la compréhension du domaine

**À creuser** : pistes ouvertes, sans engagement
```

Trois précisions sur le contenu :

- **« Retenu » n'est pas un résumé.** L'intérêt est ce qu'on en fait, pas ce qu'on a
  lu. Une session qui n'a rien donné se note telle quelle : c'est une information.
- **Ce qui contredit un choix du projet mérite d'être noté**, même — surtout — si on
  ne change rien. C'est la trace d'une veille réellement exercée plutôt que d'une
  collecte de confirmations.
- **Le réglementaire compte autant que le technique** (RGPD, accessibilité RGAA,
  AI Act), et il est plus facile à oublier.

---

## 2026-07-15 — durée non renseignée

**Parcouru** : métiers du web à l'ère de l'IA — support
`fonds/metiers_web_ia_2026-07-15/final/veille-metiers-web-ia-202.pptx` (13
diapositives) : robots IA sur le web, ralentissement des embauches juniors
(dev, cadres IT), grilles d'analyse REAC (DWWM, CDA, CDUI) face à l'IA,
rédacteur web (métier le plus exposé, 57 % automatisable), community
management et gestion de projet, chiffres macro France.

**Retenu** :

- Le bouleversement documenté n'est pas l'emploi existant mais l'**accès** au
  métier — ralentissement des embauches juniors, pas de vague de licenciements
- Lecture transversale des grilles REAC : plus une compétence est procédurale et
  normée, plus elle est absorbée par l'IA ; plus elle exige un jugement
  contextuel, plus elle résiste
- Tension de fond : la rupture du pipeline de formation — les tâches juniors qui
  formaient les seniors de demain sont les premières automatisées

**À creuser** : recouper les sources macro (Numeum, CREDOC/Arcep, compilation
OCDE/McKinsey/FMI) avant citation formelle — signalé comme non fait dans la
bibliographie d'origine.

**Format — résolu (2026-07-23)** : document de lecture généré
(`fonds/metiers_web_ia_2026-07-15/final/script.md`), reconstruit depuis le texte
des diapositives et les tableaux de compétences. Deux écarts mineurs restants
avec la convention à deux rôles : le support live est un PPTX (pas un ODP), et
les légendes visuelles des grilles (couleurs) n'ont pas pu être extraites du
texte brut.

**Thème** : couvert par l'axe assigné (développement durable x IA — volet
sociétal/économique) — le thème est large par construction, pas besoin de
vérifier le rattachement veille par veille.

## 2026-05-13 — cybersécurité x IA — durée non renseignée

**Parcouru** : actualité cybersécurité x IA (armement de l'IA) — premier exploit
zero-day dont le code semble généré par une IA (Google Threat Intelligence Group),
malware Android PromptSpy pilotant l'écran de la victime en temps réel, usage des
LLM par des groupes APT étatiques (APT45 Corée du Nord, APT27/UNC2814 Chine,
groupes russes), « Shadow APIs » donnant un accès non officiel à des modèles
comme Gemini ou Claude (étude CISPA).

**Retenu** :

- L'IA réduit fortement le délai entre découverte d'une vulnérabilité et son
  exploitation — glissement vers des agents semi-autonomes qui automatisent des
  phases entières de reconnaissance et d'attaque
- Deux sources citées explicitement en fin de rapport : TheHackerNews et Korben —
  Korben figure déjà dans le dossier FreshRSS « IA — vulgarisation et outils »
  (cf. `sources.md`), cohérence confirmée entre veille et outillage

**À creuser** : —

**Écart avec le thème assigné, résolu** : ce rapport porte sur la cybersécurité,
pas sur le développement durable x IA. Explication confirmée par David : le
collectif **Mini Manifest a été lancé le 13 mai** — cette pièce, datée du jour
même, est antérieure à l'attribution du thème (cf. `README.md` §Dispositif). Pas
un écart à corriger, un repère temporel sur le début du dispositif.

Document source : `veille_13_mai_David.pdf`.

## 2026-05-13 — mise en place FreshRSS — durée non renseignée

**Parcouru** : mise en place de l'instance FreshRSS personnelle (Docker + Caddy,
domaine `rss.david-legrand.fr`) — rédaction d'un article de synthèse sur la
démarche et les choix techniques.

**Retenu** :

- Choix FreshRSS confirmé pour trois raisons — libre (pas de dépendance à un
  service pouvant fermer ou devenir payant), sobre (pas de push permanent),
  organisation par catégories — cohérent avec la justification déjà donnée dans
  `sources.md`
- SQLite retenu plutôt que MariaDB/PostgreSQL pour un usage personnel : évite un
  conteneur de base de données supplémentaire, suffisant à cette échelle
- Piège identifié dès la mise en place, à ne pas reproduire : ne pas ajouter tous
  les flux d'un coup — « 500 articles non lus » devient aussi décourageant qu'une
  boîte mail pleine. Démarrer petit, ajuster au fil de l'eau, supprimer les flux
  qui ne servent jamais
- Catégories envisagées dès le départ : IA, Python, Développement web, Linux,
  RGPD/CNIL/AI Act, Pédagogie, Cybersécurité — périmètre plus large que le seul
  thème Mini Manifest, cohérent avec la collecte étendue déjà notée dans
  `sources.md`

**À creuser** : —

Document source : `12_mai_article-freshrss-docker_.pdf`. C'est littéralement le
document d'origine de l'outillage décrit dans `sources.md` §Outils d'agrégation —
à citer depuis là plutôt que dupliquer son contenu.

<!-- Les entrées commencent ici, la plus récente en premier. -->
