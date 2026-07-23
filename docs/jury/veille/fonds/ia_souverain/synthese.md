# Une IA souveraine et éthique

## De quoi parle-t-on ?

La souveraineté numérique désigne la capacité d'une nation ou d'une organisation à conserver le contrôle total de ses systèmes d'IA, incluant les modèles, les données et l'infrastructure, en les plaçant sous une juridiction locale. Contrairement au modèle dominant où les données circulent vers des clouds étrangers soumis à des législations tierces, l'IA souveraine garantit que le stockage et le calcul restent à l'intérieur des frontières régionales.

**Benjamin Bayart** structure cette notion autour de trois piliers fondamentaux :

1. **Juridique** : Déterminer quel droit s'applique aux données, le droit européen protégeant l'individu là où le droit américain protège le business.
2. **Économique** : La souveraineté vise à conserver la plus-value au sein de l'espace économique local. Selon l'analogie du "costume", consommer du cloud local permet de maintenir l'emploi (tailleur, tisserand) plutôt que d'importer du chômage en achetant des services tout faits à l'étranger.
3. **Régalien** : Il s'agit de protéger les fonctions vitales de l'État (état civil, défense, santé) en refusant qu'elles dépendent d'infrastructures étrangères incontrôlables.

Pour les ingénieurs, il s'agit de passer d'un idéal marketing à une "optimisation sous contrainte", où l'on choisit la solution la plus résiliente et conforme aux réalités juridiques.

## La législation européenne

La force de l'Europe réside dans sa philosophie du droit, qui considère la protection des données comme un droit de la personne. À l'inverse, le droit américain voit les données comme un droit de propriété ou d'affaires, ce qui crée une incompatibilité structurelle entre le RGPD et des lois comme le Cloud Act ou le Patriot Act. Ces textes permettent en effet aux agences américaines d'accéder aux données de n'importe quelle entreprise américaine, quel que soit le lieu de stockage des serveurs dans le monde.

Cette divergence a conduit à des décisions majeures :

- Invalidation du **Safe Harbor** et du **Privacy Shield** : La Cour de justice de l'Union européenne (CJUE) a cassé ces accords successifs, jugeant que le niveau de protection américain n'était pas équivalent au droit européen.
- **RGPD** : Ce règlement s'impose mondialement dès lors qu'une entreprise traite les données d'un résident européen, car le droit est attaché à la personne et non à la zone d'exercice de l'entreprise.
- **AI Act** : Ce nouveau cadre définit des règles strictes en matière de transparence, de gestion des risques et de responsabilité pour les systèmes d'IA. Il impose notamment une documentation rigoureuse et une classification des modèles selon leur niveau de risque.

L'Europe a également mis en place le Bureau européen de l'IA pour superviser l'innovation tout en appliquant ces mesures de sauvegarde.

## Qu'est-ce qu'un modèle éthique

Un modèle éthique dans le domaine de l'IA se définit par sa transparence, son respect des droits fondamentaux et sa conformité aux réglementations en vigueur. Un tel modèle repose sur plusieurs piliers :

- **Transparence totale** : Il propose des données et des méthodes d'entraînement documentées, offrant ainsi une visibilité inédite sur la manière dont il a été conçu.
- **Conformité légale** : Il respecte strictement les cadres juridiques, notamment l'AI Act européen, qui impose des règles de gestion des risques et de documentation.
- **Respect de la vie privée et de la propriété intellectuelle** : Il est conçu pour ne pas enfreindre les droits des créateurs de contenus ni compromettre les données personnelles des utilisateurs.
- **Explicabilité et auditabilité** : Il permet d'expliquer ses résultats et fournit la documentation nécessaire pour que les régulateurs puissent suivre et auditer ses actions.

Un exemple concret cité dans les sources est le modèle **Apertus-70B**, qualifié de "plus éthique" car il intègre nativement ces exigences de transparence et de respect des droits tout en offrant des performances comparables aux leaders du marché.

## Infomaniak

Infomaniak se positionne comme une alternative opérationnelle majeure en proposant des IA souveraines à la demande via des API compatibles OpenAI. Cette solution permet aux développeurs d'intégrer des modèles performants tout en garantissant que les données sensibles restent hébergées en Suisse ou en Europe, sous juridiction locale.
Infomaniak propose une découverte avec 1M de token gratuit

Les points clés de l'offre Infomaniak incluent :

- **Confidentialité totale** : Aucune requête API n'est stockée, assurant un contrôle total de l'utilisateur sur ses données.

- Modèles éthiques et performants :
  - **Apertus-70B** : Qualifié de modèle "le plus éthique", il est conforme à l'AI Act, transparent sur ses données d'entraînement et respectueux de la propriété intellectuelle.
  - **Kimi-K2.6** : Optimisé pour le "vibe coding" et les workflows agentiques, il propose une fenêtre de contexte de 256k tokens.
  - **Qwen 3.5** : Conçu pour les tâches complexes nécessitant un raisonnement logique de haute précision.

- Infrastructure durable : Le matériel est alimenté par une énergie 100 % renouvelable et la chaleur produite est revalorisée pour le chauffage.

- Stack technique pour agents : Le service supporte le Function Calling et le protocole MCP (Model Context Protocol), permettant de transformer une simple requête en action concrète comme l'interrogation d'une base de données en temps réel.

Cette approche permet de sortir de la dépendance aux "Hyperscalers" américains en offrant une solution flexible facturée à l'usage.

## Quelques sources

- [Infomaniak IA](https://www.infomaniak.com/fr/hebergement/ai-services)
- [Vidéo : Sous le capot du cloud souverain](https://www.youtube.com/watch?v=a5s_I00kuQU)
- [Vidéo : Géopolitique de la data](https://www.youtube.com/watch?v=b1iXIZ71Hek)
- [L'IA souveraine : un guide avec des exemples](https://www.noota.io/fr/blog/ia-souveraine-guide)
