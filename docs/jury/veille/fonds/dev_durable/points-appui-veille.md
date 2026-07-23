# Veille IA & Environnement — Points d'appui

*Phrases-clés par slide — à tricoter à l'oral, pas à lire.*

---

## Slide 3 — Éco-responsabilité transversale
- Pourquoi l'écologie dans une formation dev IA ? → pas militant, c'est dans le référentiel
- Pas une compétence à part → un réflexe qui traverse 3 compétences
- C7 = benchmark éco-responsable · C15 = prestataires sobres · C17 = éco-conception (éco-index, Green IT)
- Jamais une case à cocher à la fin → une question à chaque étape
- → c'est ce fil que je déroule

## Slide 4 — Réchauffement climatique
- CO2 = molécule stable, rien ne la détruit dans l'air
- donc il s'accumule, reste des siècles → on engage le climat de générations
- pour rester sous 2°C : pas stabiliser, *baisser*
- Jancovici : ~5 %/an, « l'effet Covid mais tous les ans pendant 30 ans »
- → l'IA arrive là-dedans : elle aide ou elle éloigne ?
- *(schéma pente −5 %/an)*

## Slide 5 — Conso des data centers
- ~1,5 % élec mondiale (~415 TWh, 2024) → paraît modeste
- moyenne trompeuse, 2 raisons
- dynamique : doublement d'ici 2030 (Shift Project) vs +6-7 %/an numérique global → pente bien plus raide
- concentration : pas réparti → là où foncier/climat/fiscalité → explose localement
- US au-dessus, Europe monte, Irlande à venir
- → le problème = la concentration, pas la moyenne

## Slide 6 — Où part l'énergie d'un data center
- surprise : la moitié ne calcule pas
- calcul 45-55 % · refroidissement 30-40 % · distribution/pertes ~10 % · éclairage ~5 %
- pour 1 d'énergie qui calcule, ~autant pour faire tourner/refroidir
- PUE = énergie totale ÷ énergie utile · 1,0 idéal théorique · 1,5 moyenne · 1,1 les meilleurs (→ Infomaniak)
- → refroidir et alimenter = le vrai levier de sobriété

## Slide 7 — Énergie embarquée
- jusqu'ici que l'élec d'usage → manque l'invisible : la fabrication (empreinte embarquée)
- data center : ~25 % empreinte *carbone* = fabrication / 75 % usage (Schneider Electric)
- repère : PC 2 kg = ~800 kg matières extraites, 400× son poids
- → le matériel le plus propre = celui qu'on ne fabrique pas → durée de vie compte autant que conso

## Slide 8 — Chaque énergie ne se vaut pas
- on a compté des kWh comme s'ils étaient égaux → faux
- même requête : propre ou sale selon le mix
- France (nucléaire/hydraulique) vs région charbon = facteur 10 ou +, même service
- 2 conséquences : l'empreinte dépend du *où* · le cloud n'est pas neutre
- → le cloud est branché quelque part, réseau réel, intensité carbone réelle

## Slide 9 — 10× une recherche Google ?
- il y a 20 ans : « recherche Google = bouillir de l'eau » (on *répétait* que)
- aujourd'hui : « ChatGPT = 10× Google » → même stat-épouvantail
- en remontant à la source → s'effondre : ~parité, ~0,3 Wh
- images : 1 seconde de four (dixit le patron d'OpenAI) · ~10 s de vélo
- si peu que c'est le mauvais sujet → le problème = l'échelle, la somme des clics
- → réflexe C6 : remonter à la source avant de répéter

## Slide 10 — La surenchère
- normalement la demande tire l'offre → masques 2020, l'offre court derrière
- IA = l'inverse : on construit en pariant que la demande viendra
- offre *devant* la demande → elle fabrique sa propre demande
- pari gros : infra lourde, carbonée, à amortir 15-20 ans
- → verrouillage : béton coulé, turbines installées → on fait tourner pour rentabiliser

## Slide 11 — Effet rebond / Jevons
- Jevons, XIXe, charbon · Watt rend les machines efficaces → on pense « on en brûlera moins »
- inverse : jamais autant de charbon → moins cher à faire tourner → on en met partout
- = effet rebond
- *(schéma empilement)* on croit qu'une énergie remplace l'autre → non, elles s'empilent (thèse Jancovici)
- plus de charbon ET de bois qu'au XIXe · le total monte
- IA = prochaine couche, elle s'ajoute
- → méfiance : « les puces deviennent sobres donc ça ira » → non, plus c'est efficace, plus on en met

## Slide 12 — Turbines à gaz mobiles (xAI)
- *(rester factuel, froid)*
- xAI (Musk) besoin d'élec tout de suite → dizaines de turbines à gaz, sans permis
- astuce : sur remorques = « mobiles » = échappent aux contrôles
- 27 non autorisées Mississippi · ~35 Tennessee (Memphis)
- qui respire les rejets ? quartiers populaires de Memphis
- → le cloud a une cheminée, rarement dans les beaux quartiers
- → pas isolé : la demande va plus vite que l'élec propre → on rallume du fossile

## Slide 13 — Une électricité propre… mais limitée
- décarboner = électrifier au bas-carbone (transport, chauffage, industrie)
- mais élec propre = limitée, croît lentement, ressource partagée
- l'IA puise dans le même stock → concurrence avec la décarbonation du reste
- chaque MW propre pour un data center = un MW en moins ailleurs
- Irlande : 5 % → 21 % de l'élec (2015→2023), + que tous les foyers urbains · hors DC la demande était stable → toute la hausse vient d'eux
- réseau saturé → gel des nouveaux raccordements à Dublin (protéger foyers/hôpitaux/écoles)
- Shift Project : propose un plafond conso DC (calé climat) · débattu (IEA préfère la flexibilité)
- → on ne peut plus laisser croître sans regarder

## Slide 14 — AI for brown / AI for green
- après xAI on croirait tout pourri → non
- l'IA n'est ni bonne ni mauvaise → tout dépend de l'usage
- AI for Brown : optimiser forage, gisements, mine → extraire plus, plus vite
- AI for Green : équilibrer réseau, intégrer renouvelable, éviter 1000 prototypes
- on ne juge pas l'IA, on juge un usage · nous = là où ça se décide
- → regardons le for Green, et comment rendre l'IA elle-même sobre

## Slide 15 — IA frugale
- pas à inventer : cadre officiel → AFNOR SPEC 2314 + Kit d'engagement CGDD / Hub France IA / AFNOR 2025 (joint)
- déf forte : questionner le *besoin* d'IA · ressource *avant* performance → renversement
- concret : arrêter « le plus gros modèle » → modèle spécialisé adapté
- retour de l'IA symbolique (règles) : parfois plus exacte et + économe
- → réflexe avant de coder : ce problème a-t-il vraiment besoin de deep learning ? souvent non

## Slide 16 — Infomaniak
- ça existe pour de vrai → Infomaniak, hébergeur suisse · clin d'œil : ma veille AI Act/RGPD → eux en font un argument
- infra : 100 % renouvelable · chaleur serveurs → chauffe des logements · PUE < 1,1 (l'élite) · compensation 200 % · données Suisse/UE
- modèles open source via API : Apertus (le + éthique/transparent), modèles optimisés, petits modèles RAG
- → IA souveraine et sobre bout en bout
- MAIS lucidité : Apertus = 70B, lourd · pas de function calling natif → ReAct possible mais fragile → pour agentique on préfère Qwen/Ministral
- → le plus éthique ≠ le plus adapté · arbitrage éthique/sobriété/fonctionnalité = notre métier

## Slide 17 — Outils & démo
- le concret : à notre niveau
- but : pas donner des réponses, en faire surgir · outils testés à mon niveau, mais = ceux du Kit CGDD
- HELM/MMLU = perf, pas conso → ces outils comblent le trou
- au menu : CodeCarbon (mesure local) · EcoLogits (estime distant) · GreenIT Analysis (éco-index, C17) · cités : Green Algorithms, ML CO2 Impact

## Slide 18 — Rex 1 : CodeCarbon
- principe : mesurer = 3 lignes (import, `with`, code dedans) → un réflexe
- même question « pourquoi le ciel est bleu ? » à 3 niveaux
- boucle 10M : ~0,5 mg → unitaire = dérisoire
- Mistral 7B : +CO2, +lent, réponse partiellement fausse · Gemma 4B : −CO2, +rapide, juste
- *(sur cet exemple !)* le petit gagne sur les 3 colonnes → IA frugale : adapté > gros
- *(rappel : vieux CPU sans GPU, chiffres variables)*

## Slide 19 — Rex 2 : agent avec API
- changement de situation : modèle distant (API) → aucun capteur → on n'mesure plus, on *estime* (EcoLogits)
- tableau : haut = mesuré (local) · bas = estimé (fourchettes)
- effet tokens : court 63 tk ~0,1 Wh · long 196 tk ~0,4 Wh → + il parle + il consomme
- token = coût financier ET écologique → réduire la facture réduit l'empreinte
- warning « archi non publiée » → opacité des fournisseurs (Shift Project), visible en direct
- *(endpoint commun OK à l'écran ; pas de secret)*

## Slide 20 — Conclusion
- *(rien à dire — silence, slide « Pas de panique / 42 »)*

---

## Garde-fous (à garder en tête)
- « sur cet exemple » (qualité des modèles) · « on répétait que » (stat Google) · « affiché/revendiqué » (Infomaniak) · « gelé les nouveaux raccordements » (Irlande) · plafond = proposition, pas consensus
- xAI : faits documentés, pas les intentions · « des dizaines sur deux États » si on pousse
- 21 % Irlande = tous les data centers, pas que l'IA
- 25 % data center = empreinte *carbone*, pas énergie

## Phrases à poser (les laisser respirer)
- « le cloud a une cheminée »
- « on ne juge pas l'IA, on juge un usage »
- « plus c'est efficace, plus on en met »
- « le token, coût financier ET écologique »
- « pas la réponse, mais la question »
