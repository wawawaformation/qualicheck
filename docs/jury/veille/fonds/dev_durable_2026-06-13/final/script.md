# script des slides

## slide 3
« Avant d'entrer dans le sujet, pourquoi est-ce qu'on parle d'écologie dans une formation de dev IA ? Parce que ce n'est pas un supplément militant qu'on ajoute par conviction : c'est écrit noir sur blanc dans notre référentiel.
Mais pas comme une compétence à part — plutôt comme un réflexe qui traverse trois compétences qu'on a déjà. Quand je fais un benchmark de services, en C7, je dois évaluer leur niveau de démarche éco-responsable. Quand je conçois une architecture, en C15, je dois privilégier les prestataires les plus sobres. Et quand je développe, en C17, je dois respecter les bonnes pratiques d'éco-conception, type éco-index ou Green IT.
Autrement dit, ce n'est jamais une case "écologie" qu'on coche à la fin. C'est une question qu'on se pose à chaque étape : la collecte, l'archi, le code. C'est ce fil-là que je vais dérouler aujourd'hui. »

## slide 4
« Le CO2, contrairement à d'autres polluants, ne se dégrade pas tout seul dans l'air : c'est une molécule stable, rien ne la détruit. Donc le carbone qu'on émet aujourd'hui s'accumule et y reste pour des siècles — ce qu'on fait maintenant engage le climat de plusieurs générations après nous. Et pour rester sous les 2 degrés, il ne suffit pas de stabiliser : Jancovici le résume d'une formule — il faudrait baisser les émissions mondiales d'environ 5 % par an, soit l'équivalent de la chute du Covid, mais tous les ans pendant trente ans. C'est là-dedans qu'arrive l'IA. Elle nous aide à tenir ce cap, ou elle nous en éloigne ? »

## slide 5
« Passons aux chiffres concrets. Aujourd'hui, les centres de données, c'est environ 1,5 % de l'électricité mondiale — autour de 415 térawattheures en 2024. Ça paraît modeste… sauf que cette moyenne mondiale est trompeuse, à deux titres.
D'abord la dynamique : selon le Shift Project, sur la trajectoire actuelle, la consommation des data centers pourrait doubler d'ici 2030 — un quasi-doublement en moins de sept ans. À comparer au numérique dans son ensemble, qui croît plutôt de 6 à 7 % par an : les data centers, eux, sont sur une pente bien plus raide. Et ce sont eux que l'IA fait gonfler.
Ensuite la répartition : les data centers ne sont pas étalés uniformément, ils se concentrent là où le foncier, le climat et la fiscalité sont favorables. Dans ces zones-là, la part locale explose — les États-Unis sont déjà bien au-dessus de la moyenne, l'Europe monte vite, et on verra le cas de l'Irlande tout à l'heure. Le vrai problème, ce n'est pas la moyenne mondiale, c'est la concentration. »

## slide 6
« Maintenant, regardons à l'intérieur d'un data center : où part vraiment l'énergie ? Et là il y a une surprise. On imagine des serveurs qui calculent à plein régime — et c'est vrai, le calcul, c'est à peu près la moitié, 45 à 55 %. Mais l'autre moitié ne calcule pas du tout. Le refroidissement, à lui seul, c'est 30 à 40 % : il faut évacuer en permanence la chaleur des machines, sinon elles grillent. Ajoutez la distribution électrique et les pertes, environ 10 %, et l'éclairage et le reste, 5 %.
Autrement dit : pour une unité d'énergie qui sert vraiment à calculer, on en dépense presque autant juste pour faire tourner et refroidir l'installation.
C'est ce que mesure un indicateur que vous croiserez partout : le PUE, le Power Usage Effectiveness. C'est le rapport entre l'énergie totale du site et l'énergie utile au calcul. Un PUE de 1, ce serait le parfait théorique — tout au calcul, zéro perte. En vrai, la moyenne tourne autour de 1,5 : 50 % de surcoût. Les meilleurs descendent vers 1,1 — et c'est là qu'on retrouvera Infomaniak tout à l'heure. Retenez juste ça : refroidir et alimenter, ce n'est pas un détail, c'est le principal levier pour rendre un data center sobre. »

## slide 7
« Jusqu'ici on n'a parlé que d'électricité — la consommation quand ça tourne. Mais il manque une partie qu'on ne voit jamais : l'empreinte de la fabrication, ce qu'on appelle l'empreinte embarquée. Avant même d'allumer une machine, elle a déjà émis. Pour un data center, ce n'est pas marginal : selon les données Schneider Electric, environ 25 % de son empreinte carbone vient de la fabrication — serveurs, équipements, bâtiment — contre 75 % pour l'usage. Et un repère qui parle : fabriquer un ordinateur de 2 kg demande d'extraire environ 800 kg de matières premières, 400 fois son poids. D'où un principe simple : le matériel le plus propre, c'est celui qu'on ne fabrique pas — allonger la durée de vie compte autant que réduire la consommation. »

## slide 8
« Jusqu'ici on a compté des kilowattheures, comme s'ils étaient tous équivalents. Mais un kilowattheure n'a pas le même impact selon d'où il vient. Le même calcul, la même requête, peut être quasi propre ou très sale — tout dépend du mix électrique qui l'alimente.
Un exemple parlant : faire tourner un serveur en France, où l'électricité est très bas-carbone grâce au nucléaire et à l'hydraulique, ou le faire tourner dans une région qui brûle du charbon, ça peut représenter un facteur dix, voire plus, sur les émissions — pour exactement le même service rendu.
Ça veut dire deux choses. D'abord, l'empreinte d'une IA, ce n'est pas qu'une question de technique ou d'efficacité : c'est d'abord une question de où tournent les machines. Et ensuite, ça démonte l'idée que "le numérique, c'est dans le cloud, c'est immatériel, donc neutre". Le cloud est branché quelque part, sur un réseau bien réel, avec une intensité carbone bien précise. Et c'est là que ça se complique — on va le voir. »

## slide 9
« Il y a vingt ans, on répétait qu'une simple recherche Google équivalait à faire bouillir de l'eau. Aujourd'hui, c'est devenu : "ChatGPT, c'est dix fois une recherche Google". Même formule, même exagération — à chaque nouvelle techno, sa stat-épouvantail.
Et à chaque fois, en remontant à la source, le chiffre s'effondre. Sur l'IA, on est en réalité autour de la parité : environ 0,3 wattheure par requête. Deux images pour le sentir : c'est à peu près une seconde de four de cuisine à plein régime — la comparaison qu'emploie même le patron d'OpenAI. Ou, si vous préférez quelque chose qu'on sent dans les jambes, une dizaine de secondes de vélo. Voilà votre requête.
C'est tellement peu que ça en devient le mauvais sujet. Parce que le problème n'a jamais été votre requête à vous. Il est dans l'échelle : des milliards de requêtes, des entraînements géants, des data centers entiers. Le piège, ce n'est pas le clic — c'est la somme des clics.
Et au passage, ça illustre un réflexe de veille, le C6 du référentiel : avant de répéter un chiffre qui circule partout, on remonte à la source. Souvent, il ne tient plus. »

## slide 10

« Normalement, un marché fonctionne dans un sens : c'est la demande qui tire l'offre. Pensez aux masques en 2020 — le besoin explose d'un coup, et l'offre court derrière, d'où la pénurie. Personne n'avait construit des usines de masques avant le Covid : ça aurait été absurde.
L'IA, c'est l'inverse exact. On ne construit pas les data centers parce qu'il y a déjà une demande. On les construit en pariant qu'elle viendra. Avec les masques, l'offre courait derrière la demande ; avec l'IA, l'offre court devant — elle essaie de fabriquer sa propre demande.
Et ce n'est pas neutre, parce qu'on parie gros : sur de l'infrastructure lourde, carbonée, qu'il faudra amortir pendant quinze à vingt ans, que le pari soit gagné ou non. On engage des émissions sur deux décennies pour des usages qui ne sont même pas encore prouvés. C'est ce qu'on appelle un verrouillage : une fois le béton coulé et les turbines installées, on ne revient pas en arrière — on fait tourner pour rentabiliser. »

## slide 11

Pour comprendre le piège, il faut remonter à un Anglais du XIXe siècle : William Stanley Jevons. Il étudie le charbon. À son époque, Watt vient de rendre les machines à vapeur bien plus efficaces — elles consomment moins de charbon pour le même travail. Tout le monde en conclut qu'on va donc en brûler moins.
Et Jevons observe exactement l'inverse : l'Angleterre n'a jamais autant consommé de charbon. Pourquoi ? Parce qu'une machine plus efficace coûte moins cher à faire tourner — alors on en met partout, dans des usages qui n'étaient pas rentables avant. L'efficacité, au lieu d'économiser la ressource, a fait exploser son usage. C'est l'effet rebond.
(en montrant le schéma) Et à l'échelle de l'histoire, ça donne ça. On croit qu'une énergie remplace la précédente — le pétrole remplace le charbon, le renouvelable remplacera le fossile. En réalité, c'est une thèse que défend Jancovici : aucune énergie n'a jamais remplacé l'autre. Elles s'empilent. On consomme aujourd'hui plus de charbon, et même plus de bois, qu'au XIXe siècle. Le total ne fait que monter.
L'IA, c'est la prochaine couche sur la pile. Les data centers ne remplacent aucune consommation existante : ils s'ajoutent. Et donc, méfiance avec l'argument qu'on va vous servir — "les puces deviennent plus sobres, donc tout va s'arranger". Non : plus c'est efficace, plus on en met. C'est précisément ça, le piège de Jevons.

## slide 12

 Voici un cas très concret, arrivé aux États-Unis. Pour alimenter son intelligence artificielle, xAI — la société d'IA d'Elon Musk — avait besoin d'énormément d'électricité, tout de suite. Solution : installer des dizaines de turbines à gaz. Sans permis.
Et l'astuce pour passer entre les mailles : les laisser sur leurs remorques. Officiellement "mobiles", donc considérées comme temporaires, donc échappant aux contrôles environnementaux qu'on imposerait à une vraie centrale. Pour les chiffres : vingt-sept turbines non autorisées côté Mississippi, et une trentaine de plus repérées par imagerie thermique côté Tennessee, à Memphis.
Et pendant ce temps, qui respire les rejets de ces turbines ? Des quartiers populaires de Memphis, déjà parmi les plus exposés à la pollution de l'air.
Cette histoire dit deux choses. La première : quand on parle d'IA "dans le cloud", on oublie que le cloud a une cheminée — et elle est rarement dans les beaux quartiers. La seconde, c'est que ce n'est pas un dérapage isolé : c'est ce qui arrive quand la demande de calcul va tellement vite que l'électricité propre ne suit pas. On rallume du fossile pour combler le trou. »

## slide 13

« Et il y a un dernier point, le plus structurel. Décarboner nos sociétés, ça veut dire une chose : remplacer le fossile par de l'électricité propre — électrifier les voitures, le chauffage, l'industrie. Mais cette électricité bas-carbone n'est pas infinie : elle augmente lentement, et c'est une ressource partagée. Et l'IA arrive, et puise dans le même stock.
Donc le problème n'est plus seulement "l'IA consomme beaucoup". C'est qu'elle entre en concurrence directe avec la décarbonation de tout le reste. Chaque mégawatt propre branché sur un data center, c'est un mégawatt qui ne sert pas à décarboner une usine ou un chauffage.
Et ce n'est pas une hypothèse d'école — l'Irlande l'a vécu. Les data centers y sont passés de 5 % de l'électricité du pays en 2015 à 21 % en 2023, soit plus que tous les foyers urbains réunis. En fait, hors data centers, la consommation du pays était stable : toute la hausse vient d'eux. Le réseau a saturé, au point de risquer des coupures — alors pour garder le courant pour les foyers, les hôpitaux, les écoles, l'Irlande a gelé les nouveaux raccordements de data centers autour de Dublin.
Face à ça, le Shift Project propose une mesure radicale : un plafond de consommation électrique pour les data centers, calé sur nos objectifs climatiques. L'idée n'est pas d'interdire, mais de piloter — décider où, combien, pour quels usages — plutôt que de subir. C'est débattu, d'ailleurs : d'autres, comme l'Agence internationale de l'énergie, préfèrent réguler la flexibilité plutôt que poser un plafond. Mais tout le monde s'accorde sur le constat : on ne peut plus laisser cette demande croître sans la regarder. »


## slide 14

« Après xAI et les turbines, vous pourriez croire que tout est pourri au royaume du Danemark. Eh bien non. L'IA n'est ni bonne ni mauvaise en soi : tout dépend de ce qu'on lui fait faire. D'où une distinction qui structure tout le débat — AI for Brown contre AI for Green, deux usages opposés de la même technologie.
AI for Brown — "brown" comme les énergies sales —, c'est l'IA mise au service de ce qu'on devrait justement arrêter : optimiser un forage pétrolier, repérer de nouveaux gisements, maximiser le rendement d'une mine de charbon. L'IA qui aide à extraire plus, plus vite.
AI for Green, c'est l'usage inverse : équilibrer un réseau électrique, intégrer davantage de renouvelable, éviter mille prototypes quand trois suffisent, optimiser une consommation. La même technologie, mais au service de la transition.
Le point central, c'est donc qu'on ne juge pas "l'IA" en bloc — on juge un usage. Et nous, développeurs, on est exactement là où ça se décide : dans ce qu'on choisit de construire. Alors regardons le versant for Green — et notamment comment, concrètement, on rend l'IA elle-même plus sobre. »


## slide 15

« À quoi ressemble une IA "for Green" côté sobriété ? Bonne nouvelle, on n'a pas à l'inventer : il existe un cadre officiel. Une norme AFNOR, la SPEC 2314, et surtout un Kit d'engagement publié en 2025 par le Commissariat Général au Développement Durable, avec Hub France IA et AFNOR — 15 bonnes pratiques concrètes que je vous joins avec cette présentation.
Et la définition qu'ils donnent de l'IA frugale est plus exigeante qu'une simple "IA efficace". Elle dit deux choses fortes. D'abord : avant de se demander quel modèle, on se demande s'il faut vraiment de l'IA — questionner le besoin lui-même. Ensuite : on place la contrainte sur les ressources avant l'objectif de performance. C'est un renversement complet de réflexe.
Concrètement, ça veut dire arrêter le "je prends le plus gros modèle". Le kit recommande de privilégier des modèles spécialisés — un petit modèle sur une tâche précise plutôt qu'un mastodonte généraliste surdimensionné. Et il existe même un retour de l'IA symbolique, à base de règles : sur certains calculs, plus exacte et bien plus économe qu'un réseau de neurones. Le bon réflexe de développeur, c'est de se poser la question avant de coder : est-ce que ce problème a vraiment besoin de deep learning ? Souvent, non. »


## slide 16

« Tout ça, c'est bien en principe — mais est-ce que quelqu'un le fait pour de vrai ? Oui. Prenons Infomaniak, un hébergeur suisse. Et petit clin d'œil : la dernière fois, je vous avais parlé de l'AI Act et du RGPD. Eux en font un argument commercial, donc la boucle est bouclée.
Sur l'infrastructure d'abord : énergie 100 % renouvelable, et surtout la chaleur des serveurs n'est pas jetée — elle est récupérée pour chauffer des logements. Côté indicateurs, ils affichent un PUE sous 1,1 — souvenez-vous, c'est l'élite — et une compensation carbone à 200 % de leurs émissions. Et leurs données restent en Suisse et en Europe, conformes au RGPD et à l'AI Act.
Sur les modèles ensuite, ils donnent accès à de l'open source via une API standard : Apertus, présenté comme le plus éthique et le plus transparent ; des modèles optimisés pour l'efficacité énergétique ; des petits modèles spécialisés pour le RAG. Bref, de quoi monter une IA souveraine et sobre bout en bout.
Mais — et c'est là que je veux rester honnête — un hébergeur vert ne dispense pas de réfléchir. »

« Apertus, le modèle le plus éthique de leur catalogue, c'est un 70 milliards de paramètres : un gros modèle. 
Apertus ne fait pas de function calling natif. On peut quand même lui faire utiliser des outils, via un agent ReAct où les outils sont décrits dans le prompt — LangChain le permet. Mais c'est plus fragile et plus verbeux que le tool calling natif. Donc pour un agent fiable qui enchaîne plusieurs outils, on préférera un modèle entraîné pour ça, comme Qwen ou Ministral. Le plus éthique n'est pas forcément le plus pratique pour l'agentique. »


## slide 17
« On arrive au concret : qu'est-ce qu'on peut faire, nous, à notre niveau ? Un mot d'abord sur ce qui suit. Le but de cette démo, ce n'est pas de vous donner des réponses — c'est d'en faire surgir. Et soyons honnêtes : ce sont les outils que j'ai trouvés et testés à mon niveau. Bonne surprise quand même, je ne les ai pas inventés : ce sont ceux que recommande le Kit d'engagement du CGDD qu'on a vu juste avant. Donc pas si amateur que ça.Petite remarque au passage : les benchmarks dont on entend parler pour comparer les modèles — HELM, MMLU — c'est surtout pour la performance, est-ce que le modèle répond juste. La consommation, elle, n'est quasiment jamais dans le classement. C'est exactement ce trou-là que ces outils viennent combler.Je vais vous en montrer deux en vrai. CodeCarbon, qui mesure l'impact d'un calcul en local. EcoLogits, qui estime celui d'un appel d'API distant. Et un côté interface : GreenIT Analysis, l'éco-index d'une page web — la fameuse compétence C17. D'autres existent, que je cite sans les dérouler : Green Algorithms et ML CO2 Impact, pour estimer un entraînement en amont. L'idée n'est pas de tous les maîtriser : c'est d'en avoir au moins un sous la main quand la question se pose. »

## slide 18
Claude a répondu : Parfait, ton deck est maintenant complet et bien monté — les tableaux récap sont intégrés (Rex 1 et Rex 2), la conclusion « Pas de panique / 42 » est en place.Parfait, ton deck est maintenant complet et bien monté — les tableaux récap sont intégrés (Rex 1 et Rex 2), la conclusion « Pas de panique / 42 » est en place. Voici les scripts des trois slides demandées, dans ton format ## slide N, prêts à coller à la suite de ton script.md.
Une remarque d'abord sur ta slide 17 : tu as écrit « Green IT Analysis - France Soir ». Attention, on avait identifié Le Parisien (note G) comme exemple, pas France Soir — vérifie lequel tu veux tester et garde le même partout. Je mets « un grand site d'actu » dans le script pour que tu sois libre, et tu cites le nom au moment du live.

## slide 17
« On arrive au concret : qu'est-ce qu'on peut faire, nous, à notre niveau ? Un mot d'abord sur ce qui suit. Le but de cette démo, ce n'est pas de vous donner des réponses — c'est d'en faire surgir. Et soyons honnêtes : ce sont les outils que j'ai trouvés et testés à mon niveau. Bonne surprise quand même, je ne les ai pas inventés : ce sont ceux que recommande le Kit d'engagement du CGDD qu'on a vu juste avant. Donc pas si amateur que ça.
Petite remarque au passage : les benchmarks dont on entend parler pour comparer les modèles — HELM, MMLU — c'est surtout pour la performance, est-ce que le modèle répond juste. La consommation, elle, n'est quasiment jamais dans le classement. C'est exactement ce trou-là que ces outils viennent combler.
Je vais vous en montrer deux en vrai. CodeCarbon, qui mesure l'impact d'un calcul en local. EcoLogits, qui estime celui d'un appel d'API distant. Et un côté interface : GreenIT Analysis, l'éco-index d'une page web — la fameuse compétence C17. D'autres existent, que je cite sans les dérouler : Green Algorithms et ML CO2 Impact, pour estimer un entraînement en amont. L'idée n'est pas de tous les maîtriser : c'est d'en avoir au moins un sous la main quand la question se pose. »

## slide 18
« Premier retour d'expérience, avec CodeCarbon. Le principe d'abord, et c'est ce qui devrait vous parler : mesurer l'empreinte d'un bout de Python, c'est trois lignes — un import, un bloc with, votre code à l'intérieur. Ce n'est pas un projet, c'est un réflexe qu'on ajoute à n'importe quel script.
J'ai posé la même question — "pourquoi le ciel est bleu ?" — à trois niveaux. D'abord une simple boucle de dix millions d'additions : un demi-milligramme de CO2, autant dire rien. Ça confirme ce qu'on disait : à l'échelle unitaire, l'empreinte est dérisoire.
Ensuite deux modèles en local, sur ma machine. Et là, regardez, parce que ça prend tout le monde à contre-pied. Mistral, le plus gros, 7 milliards de paramètres : presque trois fois plus de CO2, deux fois et demie plus lent… et une réponse partiellement fausse, il me parlait d'oxyde d'azote. Gemma, le plus petit, 4 milliards : moins de CO2, plus rapide, et la bonne réponse — la diffusion de Rayleigh.
Sur cet exemple — et je dis bien sur cet exemple, une seule question ne fait pas une loi — le petit modèle gagne sur les trois colonnes : l'empreinte, la vitesse et la qualité. C'est exactement le message de l'IA frugale : on ne prend pas le plus gros par réflexe, on prend celui qui est adapté à la tâche. »

## slide 19

« Deuxième retour d'expérience, et il illustre un changement de situation. Jusqu'ici, tout tournait en local, donc CodeCarbon pouvait mesurer la vraie consommation de ma machine. Mais dans la vraie vie, vous n'hébergez pas le modèle : vous appelez une API — OpenAI, Azure, peu importe. Le calcul se passe dans un data center à l'autre bout du monde, vous n'avez aucun capteur dessus. Alors on ne mesure plus : on estime. Et c'est le rôle d'EcoLogits.
C'est toute la distinction de ce tableau : en haut, le bloc "mesuré", en local, avec CodeCarbon. En bas, le bloc "estimé", à distance, avec EcoLogits — et vous voyez que ce ne sont plus des valeurs exactes mais des fourchettes, parce qu'on modélise au lieu de mesurer.
Deux choses à retenir. La première : regardez l'effet du nombre de tokens. Une réponse courte, 63 tokens, c'est environ 0,1 wattheure ; une réponse longue, 196 tokens, ça grimpe à 0,4. Plus le modèle parle, plus il consomme — une requête n'a pas un coût fixe. Et ça, c'est une bonne nouvelle, parce que le token, vous le surveillez déjà : c'est ce qu'on paie. Le token est à la fois un coût financier et un coût écologique. Tout ce qu'on fait pour réduire la facture — prompts courts, réponses concises, cache — réduit aussi l'empreinte.
La seconde : l'outil lui-même prévient que l'architecture de ce modèle n'a pas été publiée, d'où une estimation moins précise. C'est exactement ce que pointe le Shift Project — les grands fournisseurs ne communiquent quasiment rien sur l'impact de leurs modèles. L'opacité, on la voit là, en direct, dans un warning. »



