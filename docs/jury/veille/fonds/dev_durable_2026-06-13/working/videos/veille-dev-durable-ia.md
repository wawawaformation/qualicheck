---
title: "Veille — Développement durable × IA"
subtitle: "Présentation entre apprenants · ~15 minutes · angle de la semaine : surtout environnemental"
author: "David"
date: \today
lang: fr-FR
papersize: a4
fontsize: 11pt
geometry: "margin=2.5cm"
toc: true
toc-depth: 2
numbersections: true
colorlinks: true
linkcolor: BrickRed
urlcolor: NavyBlue
---

## 1. L'éco-responsabilité, une exigence du métier

### Ce n'est pas une option militante, c'est dans le référentiel

La sobriété numérique n'est pas une posture qu'on ajoute par conviction personnelle : notre référentiel l'inscrit comme un critère d'évaluation transversal. Elle n'apparaît pas comme une compétence séparée, mais comme une exigence qui traverse trois compétences existantes. Dans la C7, quand on identifie un service d'IA via un benchmark, on doit détailler le niveau de démarche éco-responsable de chaque service étudié. Dans la C15, quand on conçoit le cadre technique d'une application, on doit favoriser les prestataires PaaS et SaaS ayant une démarche éco-responsable. Et dans la C17, quand on développe les composants et les interfaces, on doit respecter les bonnes pratiques d'éco-conception, type éco-index ou Green IT. Autrement dit, ce n'est pas évalué comme un bloc à part : c'est un réflexe attendu à chaque étape du travail.

---

## 2. La réalité physique du numérique

### Le numérique n'est pas immatériel : il pèse lourd

Avant de parler d'IA, il faut poser le décor. Le numérique représente aujourd'hui de l'ordre de 3,5 à 4 % des émissions mondiales de gaz à effet de serre, avec une croissance d'environ 6 à 7 % par an. Une partie de cet impact est invisible : l'énergie grise, c'est-à-dire la fabrication, pèse environ 25 % de l'empreinte du secteur — fabriquer un ordinateur de 2 kg nécessite d'extraire et de transformer à peu près 800 kg de matières premières. Les 75 % restants viennent de l'usage, et les centres de données consomment déjà autour de 1,5 % de l'électricité mondiale (environ 415 TWh en 2024, d'après l'IEA) — une part qui pourrait doubler d'ici 2030. On enchaîne vite : ce n'est que la toile de fond.

---

---

## 3. Où part l'énergie d'un data center ?

### Près de la moitié ne sert pas à calculer

Quand on dit qu'un data center « consomme », on imagine des serveurs qui calculent. La réalité est plus contre-intuitive : une grande partie de l'énergie ne sert pas du tout au calcul. En ordre de grandeur, sur un data center moyen, les serveurs et l'équipement IT (calcul, stockage, réseau) représentent à peu près 45 à 55 % de la consommation ; le refroidissement, à lui seul, en pèse 30 à 40 % — c'est le plus gros poste hors calcul ; la distribution électrique, avec les onduleurs et les pertes de conversion, ajoute 10 à 15 % ; et l'éclairage, la sécurité et le reste comptent pour 3 à 5 %.

![Répartition de la consommation d'un data center moyen](dc-repartition.pdf)

C'est ce que mesure le **PUE**, pour *Power Usage Effectiveness* (« efficacité d'usage de l'énergie »). C'est un rapport tout simple : l'énergie totale consommée par le site, divisée par l'énergie qui sert réellement au calcul. Un PUE de 1,0 serait l'idéal théorique — tout irait au calcul, zéro gaspillage — mais c'est impossible en pratique, puisqu'il faut bien refroidir et alimenter les machines. Un PUE moyen tourne autour de 1,5 — autrement dit, pour 1 unité d'énergie qui calcule, on en dépense environ 0,5 de plus pour refroidir et alimenter. Les meilleurs data centers descendent vers 1,1, et c'est exactement là que se situe Infomaniak, sous 1,1 : un surcoût hors calcul de l'ordre de 10 % seulement. Voilà pourquoi le refroidissement et la récupération de chaleur ne sont pas des détails, mais le principal levier d'efficacité.

### Combien ça pèse ? Le repère nucléaire

Pour donner une échelle, le bon point de comparaison, c'est le réacteur nucléaire. Un réacteur moderne d'environ 1 GW produit, sur une année, de l'ordre de 8 TWh d'électricité (en tenant compte d'un facteur de charge réel de l'ordre de 85 à 90 %). C'est notre unité de mesure.

À partir de là, attention à l'échelle dont on parle, parce que « un data center » ne veut pas dire grand-chose. Un data center classique fait souvent 10 à 50 MW : même un gros, à pleine charge, consomme environ 0,4 TWh par an, soit à peine 5 % d'un réacteur. Un seul data center « moyen », ce n'est donc pas une centrale — c'est une fraction de réacteur. En revanche, les nouveaux campus dédiés à l'IA changent de catégorie : on parle de sites de 1 GW et plus. Là, un seul campus consomme à peu près autant qu'un réacteur nucléaire produit — pour lui tout seul. C'est précisément ce qui sature les réseaux électriques aujourd'hui, et pousse les opérateurs à signer des contrats directs avec des centrales.

Et à l'échelle mondiale, les quelque 415 TWh consommés par l'ensemble des data centers en 2024 équivalent à la production d'environ 50 réacteurs tournant à plein temps. La projection vers ~945 TWh en 2030, c'est de l'ordre de 115 réacteurs. Autrement dit : aujourd'hui une cinquantaine de réacteurs rien que pour le numérique, et potentiellement plus du double en 2030.

> _À l'oral : insister sur le contre-pied — « la moitié de l'énergie ne calcule pas, elle refroidit ». C'est ce qui rend concret le « ~1,5 % de l'électricité mondiale » et prépare le cas Infomaniak._

---

## 4. L'IA : accélérateur de crise ou levier de transition ?

### La stat-épouvantail : ce qu'on répète sans vérifier

Il y a vingt ans, on répétait qu'une simple recherche Google équivalait à faire bouillir de l'eau. Aujourd'hui, c'est le « ChatGPT, c'est dix fois Google ». Même formule, même exagération : à chaque nouvelle technologie, sa stat-épouvantail. Et à chaque fois, en remontant à la source, le chiffre s'effondre. Sur l'IA, on est en réalité autour de la parité, à peu près 0,3 wattheure par requête.

Pour donner deux images : c'est une seconde de four de cuisine à plein régime — la comparaison qu'emploie d'ailleurs le patron d'OpenAI lui-même. Ou, si on préfère quelque chose qu'on sent dans les jambes, une dizaine de secondes de vélo. Voilà votre requête.

C'est tellement peu que ça en devient le mauvais sujet, parce que le problème n'a jamais été là. Il est dans l'échelle : des milliards de requêtes, des entraînements géants, des centres de données entiers. (Au passage : remonter à la source avant de répéter une statistique virale, c'est littéralement la compétence de veille, la C6.)

### La surenchère : quand l'offre précède la demande

Normalement, un marché, c'est la demande qui tire l'offre. Pensez aux masques en 2020 : le besoin explose, et l'offre court derrière — d'où la pénurie. Personne n'avait construit des usines de masques avant le Covid, ça aurait été absurde.

L'IA, c'est l'inverse exact. On ne construit pas les centres de données parce qu'il y a une demande : on les construit en pariant qu'elle viendra. Avec les masques, l'offre courait derrière la demande ; avec l'IA, l'offre court devant — elle essaie de fabriquer sa propre demande. Et elle parie gros, sur de l'infrastructure lourde et carbonée, qu'on devra amortir pendant une quinzaine d'années, que le pari soit gagné ou non.

### L'effet rebond : plus c'est efficace, plus on en consomme

Pour comprendre le piège, il faut remonter à un Anglais du XIXe siècle, William Stanley Jevons. Il étudie le charbon. À son époque, Watt vient de rendre les machines à vapeur bien plus efficaces : elles consomment moins de charbon pour le même travail. Tout le monde pense qu'on va donc en brûler moins. Jevons observe l'inverse : l'Angleterre n'a jamais autant consommé de charbon. Parce qu'une machine plus efficace coûte moins cher à faire tourner, donc on en met partout. L'efficacité, au lieu d'économiser la ressource, a fait exploser son usage. C'est l'effet rebond.

Et ça se voit à l'échelle de l'histoire. *(Projeter le schéma de l'empilement des énergies.)* Voici un schéma que j'ai refait pour illustrer une thèse de Jancovici : on croit qu'une énergie remplace la précédente — le pétrole remplace le charbon, le renouvelable remplacera le fossile. En réalité, aucune n'a jamais remplacé l'autre. Elles s'empilent. On consomme aujourd'hui plus de charbon et plus de bois qu'au XIXe siècle. Le total ne fait que monter. L'IA, c'est la prochaine couche sur la pile : les centres de données ne remplacent aucune consommation existante, ils s'ajoutent. Plus c'est efficace, plus on en met.

### La fin de l'illusion de neutralité

Un kWh n'a pas le même coût carbone selon son origine. Aux États-Unis, la demande de l'IA pousse à relancer des centrales au gaz ou au charbon. L'électricité « propre » n'est pas un acquis : elle dépend d'où elle vient.

### Le cas xAI : le cloud a une cheminée

Pour faire tourner son IA, xAI a installé des dizaines de turbines à gaz. Sans permis. Et pour passer entre les mailles, ils les ont laissées sur leurs remorques — officiellement « mobiles », donc pas soumises aux contrôles d'une vraie centrale. Vingt-sept au Mississippi, une trentaine de plus côté Tennessee. Pendant ce temps, ce sont des quartiers populaires de Memphis qui respirent les rejets. Voilà ce qu'on oublie quand on parle d'IA « dans le cloud » : le cloud, il a une cheminée. Et elle est rarement dans les beaux quartiers. C'est aussi ça, le volet sociétal — une question de justice environnementale.

### Le discernement : AI for Brown ou AI for Green

Après xAI et les turbines, on pourrait croire que tout est pourri au royaume du Danemark, comme on dit. Eh bien non, pas tout. L'IA n'est pas bonne ou mauvaise en soi : tout dépend de ce qu'on lui fait faire. Les Anglo-Saxons ont une distinction utile pour ça : *AI for Brown* contre *AI for Green*. L'*AI for Brown*, c'est l'IA qui sert à extraire plus, plus vite : optimiser un forage, repérer de nouveaux gisements, maximiser une mine — la même technologie, au service de ce qu'on devrait justement arrêter de faire. L'*AI for Green*, c'est l'inverse : équilibrer un réseau électrique, intégrer du renouvelable, éviter mille prototypes quand trois suffisent. Le point, c'est qu'on ne juge pas « l'IA » : on juge un usage. Et nous, développeurs, on est exactement à l'endroit où ça se décide — dans le choix de ce qu'on construit. Je veux maintenant montrer le versant *for Green*.

---

## 5. Sauver les ressources : l'IA comme levier

### Quand la même technologie travaille pour la transition

Il existe une IA frugale, pensée pour faire beaucoup avec peu : des modèles comme BioMistral-7B pour l'expertise médicale, ou des dispositifs comme CAP'TRONIC qui fiabilisent les équipements. On voit aussi revenir l'IA symbolique, à base de règles, souvent plus précise et plus économe que le Deep Learning pour certains calculs physiques — preuve qu'un gros modèle n'est pas toujours la bonne réponse. Et il y a des cas concrets à fort impact : les smart grids, avec un outil comme Apogée de RTE qui traite 40 000 informations par seconde pour équilibrer le réseau et intégrer le renouvelable ; ou la simulation industrielle, qui permet de réduire d'environ 60 % le carbone émis en passant de 1 000 à 300 prototypes physiques.

---

## 6. Étude de cas : Infomaniak, un hébergeur souverain et durable

### Quand la conformité et l'écologie deviennent un argument produit

Petit rappel de ma veille précédente : on avait parlé de l'AI Act et du RGPD. Infomaniak en fait justement un argument produit, donc ça boucle bien. Leur offre AI Services donne accès à des modèles open source via une API compatible OpenAI, hébergée en Suisse, sans stockage des requêtes ni réutilisation pour entraîner les modèles, et alignée sur la LPD suisse et le RGPD.

Côté écologie, les chiffres sont concrets et vérifiables : énergie 100 % renouvelable, et la chaleur des serveurs est revalorisée pour chauffer 6 000 logements en hiver et fournir l'équivalent de 20 000 douches par jour en été. L'entreprise est certifiée B Corp, avec un PUE moyen inférieur à 1,1 et une compensation carbone à 200 % de ses émissions.

Leur modèle vedette côté éthique, c'est Apertus-70B, présenté comme « le plus éthique » : conforme à l'AI Act, données et méthodes documentées, développé par la Swiss AI Initiative (EPFL, ETH Zurich, CSCS). On peut l'utiliser comme générateur dans un RAG souverain, en pipeline LangChain, avec les modèles d'embedding et de re-ranking du même hébergeur.

### La lucidité : FinOps n'est pas GreenOps

Il faut rester honnête : Apertus reste un modèle lourd de 70 milliards de paramètres. Et détail savoureux pour notre formation — sur le catalogue Infomaniak, il ne fait pas de function calling. Pour un agent qui pilote ses propres outils, on se rabattra donc sur Qwen, Gemma, Kimi ou un petit Ministral 14B. Le modèle « le plus éthique » n'est pas forcément celui qu'on utilisera partout : l'arbitrage entre éthique, sobriété et fonctionnalité est bien réel. C'est tout le volet économique — un modèle moins cher financièrement n'est pas forcément moins polluant si son usage global explose.

---

## 7. Démonstration : agir à notre niveau d'apprenant

### Des outils qui ne donnent pas de réponses, mais font surgir les questions

D'ailleurs, les outils dont on entend parler pour comparer les modèles — HELM, MMLU — c'est surtout pour la performance : est-ce que le modèle répond juste, est-ce qu'il raisonne bien. La consommation, elle, n'est quasiment jamais dans le classement. C'est ce trou-là que des outils comme CodeCarbon ou EcoLogits viennent combler, et c'est ce que je voulais vous montrer.

Un mot sur ce qui suit : le but de cette démo, ce n'est pas de donner des réponses, c'est d'en faire surgir. Précision honnête : ce sont les outils que j'ai trouvés et testés à mon niveau, pas forcément les standards du monde professionnel — je montre où j'en suis. Quand on branche CodeCarbon sur une boucle Python, ou qu'on compare deux modèles sous Ollama, on ne mesure pas pour conclure : on mesure pour voir surgir des questions qu'on ne se posait pas. « Tiens, pourquoi ce modèle consomme trois fois plus pour le même résultat ? » Ces outils ne tranchent pas le débat, ils le rendent visible.

> _Prévoir une vidéo ou des captures de secours au cas où la démo en direct planterait._

Côté back-end, pour mesurer le calcul : CodeCarbon, pour visualiser l'impact CO2 d'une boucle Python en direct ; Ollama combiné à CodeCarbon, pour comparer la consommation de deux modèles locaux ; EcoLogits, pour suivre la consommation des appels d'IA générative via API. Côté front-end, pour mesurer l'interface : l'extension Firefox GreenIT Analysis, qui donne le score éco-index d'une interface d'agent — ce qui valide directement la C17. Et pour l'estimation en amont : Green Algorithms, côté entraînement, et ML CO2 Impact.

---

## 8. Clôture

### Pas la réponse, mais la question

Je termine sans vraie conclusion, parce que je n'en ai pas. Les outils que je viens de montrer, honnêtement, je ne sais pas encore si ce sont les bons — ceux qu'on utilise vraiment en entreprise, je ne les connais pas. C'est tout l'objet d'une veille : je partage où j'en suis, pas une vérité. Si certains d'entre vous tombent sur mieux, ça m'intéresse.

Mais il y a une chose dont je suis sûr. Le jour où on choisira un modèle ou une architecture, on aura le réflexe de regarder deux colonnes : la performance et le coût. Ce que j'espère, c'est qu'on en ajoute une troisième — l'empreinte. Pas pour culpabiliser. Juste pour qu'elle soit dans l'équation, à côté des deux autres.

On n'aura pas toujours la réponse. Mais au moins, on aura la question.

…Et si vous voulez la réponse, c'est 42.
