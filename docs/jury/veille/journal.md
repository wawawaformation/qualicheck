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

**Parcouru** : métiers du web à l'ère de l'IA — support `veille-metiers-web-ia-202.pptx`
(`~/Téléchargements`, non archivé).

**Retenu** : *(à compléter — support pas encore relu en détail dans cette session)*

**À creuser** : —

**Format** : PPTX produit, **document de lecture (MD) pas encore généré** — David
prévoit de le rédiger. Cette entrée est donc incomplète tant que le MD n'existe
pas : le PPTX seul ne porte pas la charge d'accessibilité du document de partage
(cf. `README.md` — l'ODP/PPTX est un support live, le MD/ODT est le document
réel). Contrairement aux deux entrées du 2026-05-13, celle-ci n'est pas encore un
cas conforme au format à deux rôles retenu — snapshot d'un travail en cours, pas
une session terminée.

**Écart avec le thème assigné, non résolu** : contrairement au rapport
cybersécurité du 2026-05-13 (voir plus bas — antérieur au lancement de Mini
Manifest), celui-ci est daté du **2026-07-15, deux mois après le lancement** du
dispositif (13 mai). L'explication « avant le Mini Manifest » ne s'applique donc
pas ici. Statut réel à clarifier avec David une fois le MD rédigé : hors thème
assumé (veille personnelle plus large que la restitution collective), ou
rattachement au développement durable x IA sous l'angle socio-économique que le
titre seul ne montre pas.

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
