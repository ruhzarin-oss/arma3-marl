"""Fiches ÉCRITES À LA MAIN ( 03/10/2026 ) : les mécanismes de CMO et la doctrine, en synthèse française, d'après le
manuel « CMO manual EBOOK.pdf » ( pagination imprimée ) et la carte des mécanismes. Chaque fiche dit d'où elle vient."""

M = "CMO manual EBOOK.pdf"


def f(id, type, titre, texte, source, tags):
    return {"id": id, "type": type, "titre": titre, "texte": " ".join(texte.split()), "source": source, "tags": tags}


FICHES = [
    # ------------------------------------------------------------------ LES MISSIONS
    f("meca-missions-vue", "mecanisme", "Les types de missions de CMO : vue d'ensemble",
      """CMO confie le travail tactique à des MISSIONS que l'IA exécute ( 7.2 ). Deux familles : les missions de ZONE,
      définies par des points de référence ( patrouille, soutien, mouillage de mines, déminage ), et les missions de
      TÂCHE, définies par des cibles ( frappe, interception ). Les sept classes : Strike ( frappe : interception
      aérienne, frappe terrestre, frappe antinavire ASuW, frappe ASM ), Patrol ( patrouille AAW, ASuW navale, ASuW
      terrestre, ASuW mixte, ASW, SEAD, Sea Control ), Support ( orbite de guet radar AEW, ravitailleur, brouilleur,
      reconnaissance ), Ferry ( convoyage d'un avion vers une base ), Mining ( mouillage de mines ), Mine-Clearing
      ( déminage, chasse aux mines ), Cargo ( livraison ou transfert de fret, de troupes, débarquement amphibie ou
      aéroporté ). Une mission a sa propre doctrine, ses règles d'engagement et son EMCON, que ses unités héritent.
      Catégories : mission ordinaire, réservoir de tâches ( Task Pool ) et paquet ( Package ) qui puise dans le réservoir.
      Une mission peut être active ( elle part dès que possible ) ou inactive ( à activer plus tard ), avec heures
      d'activation en temps Zoulou ; à sa fin : désaffecter les unités, ordonner le retour, ou effacer la mission.""",
      f"{M}, § 7.1-7.2, p. 200-210", ["mission", "Strike", "Patrol", "Support", "Ferry", "Mining", "Cargo"]),
    f("meca-mission-strike", "mecanisme", "Mission de frappe (Strike) : fonctionnement et réglages",
      """La mission Strike ( 7.2.4 ) attaque des cibles désignées ou une catégorie de cibles ; elle comprend aussi
      l'interception aérienne. Les avions décollent, frappent puis RENTRENT quand la cible est détruite : contrairement
      à la patrouille, pas de présence continue. Types : Air Intercept, Land Strike, Naval ASuW Strike, ASW Strike. Une
      frappe contre une catégorie part au premier contact détecté ( utile en ASM et en interception ) ; contre des
      cibles précises, on les ajoute à la liste des cibles. Réglages clés : taille des vols ( Flight Size ) et « forcer
      la taille de vol » ( un groupe plus petit ne part pas ), nombre minimal d'avions prêts pour déclencher, nombre
      maximal de vols, ravitaillement en vol, conduite carburant/munitions si la cible est hors d'atteinte, usage du
      radar ( EMCON existant, radar au point initial IP ou en branche d'attaque ), rayon de frappe minimal et maximal,
      méthode d'attaque et distance d'éclatement du dispositif, attaque hors axe, plans de vol pré-générés, inscription
      à l'ordre de mission aérienne ( ATO ). Même heure sur cible pour plusieurs porteurs ( avions et navires ) : CMO
      retient les tirs pour arriver ensemble. Dans notre pont, une frappe neuve naît « OnHold » et attend des vols de
      quatre : il faut l'activer et régler des vols de deux ( fiche atelier-frappe-onhold ).""",
      f"{M}, § 7.2.4, p. 219-229 ; § 7.1.1 p. 201", ["Strike", "frappe", "mission", "interception", "ATO"]),
    f("meca-mission-strike-escorte", "mecanisme", "Escorte d'une frappe et réglages des escorteurs",
      """Dans une mission Strike, des avions sont marqués comme escorteurs ( air-air ou SEAD ) : ils rejoignent seuls
      les frappeurs et répondent aux menaces qui pèsent sur le paquet ( 7.2.4 ). Réglages propres à l'escorte : nombre
      d'avions qui vont identifier un contact inconnu, nombre qui engagent un contact hostile, distance à laquelle les
      ailiers peuvent se séparer pour traiter des contacts distincts, rayon maximal de réaction à une menace. L'escorte
      a des pages séparées pour navires et sous-marins, pour tireurs et SEAD, et pour non-tireurs comme les avions de
      guerre électronique. Le manuel note que l'escorte rapprochée vaut surtout pour les époques canon ou premiers
      missiles ; avec des missiles air-air à longue portée, une mission de patrouille séparée ( balayage, barrière ) est
      souvent recommandée. Côté Lua, notre pont affecte un escorteur par ScenEdit_AssignUnitToMission(guid, mission,
      true) : le troisième argument vrai marque l'escorte ( sonde du 02/10 ). Règle d'état-major de l'atelier : une
      paire d'escorte pour quatre frappeurs, au plus huit escorteurs, une paire reste toujours défendre chaque base.""",
      f"{M}, § 7.2.4, p. 219-229 ; cmo/lua/hmt_pont.lua ( HMT_escorter ) ; cmo/etat_major.py", ["escorte", "Strike", "SEAD", "paquet"]),
    f("meca-mission-patrol", "mecanisme", "Mission de patrouille (Patrol) : AAW, ASuW, ASW, SEAD, Sea Control",
      """La patrouille ( 7.2.3 ) est une mission de zone définie par au moins trois points de référence ( l'outil
      « Define Area » en pose quatre dans le bon ordre ; un ordre faux donne un « nœud papillon » ). Les avions restent
      en patrouille tant que carburant et armes le permettent. Types : AAW ( cherche et identifie les contacts aériens ),
      ASW ( sous-marins ), ASuW navale ( navires ), ASuW terrestre ( contacts au sol ), ASuW mixte ( tout ce qui n'est pas
      sous l'eau ), SEAD ( cherche et engage les radars qui émettent ), Sea Control ( surface et sous-marins ). Réglages :
      nombre d'unités à garder en station, règle du tiers ( un tiers des avions en l'air pour une couverture continue,
      le plus grand des deux réglages l'emporte ), taille des vols, ravitaillement en vol, nombre d'avions qui
      identifient un inconnu et qui engagent un hostile, distance de séparation des ailiers ( 5 nm par défaut ), zone de
      poursuite ( prosecution area ) avec « enquêter hors de la zone », émissions actives seulement dans la zone,
      style de mouvement ( aléatoire dans la zone, ou boucle répétée comme un soutien mais avec la logique offensive ).
      Un sous-marin en patrouille n'allume pas son radar en surface par défaut. Piège mesuré : une patrouille ne décolle
      que par vols ( au moins deux avions de la même base ).""",
      f"{M}, § 7.2.3, p. 215-219", ["Patrol", "patrouille", "AAW", "ASW", "ASuW", "SEAD", "Sea Control", "règle du tiers"]),
    f("meca-mission-support", "mecanisme", "Mission de soutien (Support) : guet aérien, ravitailleur, brouilleur, reconnaissance",
      """La mission Support ( 7.2.2 ) fait suivre à ses unités un circuit de points de référence ; elle sert au guet
      aérien ( AEW/AWACS ), au ravitaillement en vol, au brouillage offensif et à la reconnaissance. Réglages : nombre
      d'unités par classe à garder en station ( 0 = ignoré ), règle du tiers, « une seule fois » ( l'unité rentre et
      reste à la base quand elle atteint ses limites ), navigation en boucle continue ( jusqu'au carburant de retour :
      pour un ravitailleur, un avion de guet ou de brouillage qui doit durer ) ou boucle unique ( un passage puis
      retour : pour une reconnaissance ), allure de transit et allure sur le circuit. Pour les ravitailleurs : rentrer
      après un cycle quand la file est vide, et limiter le nombre de receveurs servis ( arrondi au vol ). Pour qu'un
      avion de guet émette, la mission doit avoir un EMCON actif ( radar actif ) ; un brouilleur offensif doit avoir
      l'OECM actif et se placer derrière les frappeurs, au plus près de la cible tout en restant hors des défenses.
      Notre pont pose ces missions par HMT_zone ( genre 3, OnStation, ActiveEMCON, ScenEdit_SetEMCON('Mission', nom,
      'Radar=Active;OECM=Active') ).""",
      f"{M}, § 7.2.2, p. 211-215 ; § 9.2.6 p. 309 ; cmo/lua/hmt_pont.lua ( HMT_zone )", ["Support", "AEW", "ravitailleur", "brouilleur", "reconnaissance"]),
    f("meca-mission-ferry", "mecanisme", "Mission de convoyage (Ferry)",
      """La mission Ferry ( 7.2.1 ) transfère un aéronef d'un lieu à un autre ; la destination est toujours une unité,
      une installation ou une base capable de l'accueillir ( amie ou neutre ). Comportement : aller simple ( la mission
      s'efface une fois faite et l'avion reste à destination ), cycle ( aller-retour après le temps de préparation à
      chaque bout ) ou aléatoire. On règle l'altitude et la vitesse de la mission. Usages : redéployer une escadre vers
      une base avancée ou de dispersion, évacuer des avions d'une base menacée ( comme l'aviation irakienne vers l'Iran
      en 1991 ), simuler un trafic civil. Le chargement « Ferry » de la base DB3000 ( réservoirs de convoyage, sans
      armes ) donne le plus long rayon d'action d'un avion ; un avion convoyé n'est pas armé à l'arrivée. Pour un chef
      d'état-major, le convoyage sert à rapprocher les avions du front, à les disperser hors de portée des frappes
      ennemies ou à les rapatrier pour réparation.""",
      f"{M}, § 7.2.1, p. 210-211", ["Ferry", "convoyage", "redéploiement", "dispersion"]),
    f("meca-mission-mining", "mecanisme", "Mission de mouillage de mines (Mining)",
      """La mission Mining ( 7.2.5 ) est une mission de zone : les unités mouillent leurs mines au hasard dans la zone
      définie par les points de référence. Il faut des navires, sous-marins ou avions équipés pour mouiller ET des mines
      disponibles ( chargement « Naval Mine Laying » pour les avions, magasins pour les navires ). Réglages : doctrine,
      EMCON, allure et altitude ( rester dans les conditions de largage des mines ), règle du tiers pour les avions, et
      DÉLAI D'ARMEMENT ( 2 heures par défaut ) qui laisse au mouilleur le temps de sortir de la zone. Le mouillage est
      volontairement irrégulier pour que l'ennemi ne devine pas l'étendue du champ en trouvant quelques mines ; il faut
      contrôler le résultat. Choisir une zone ni trop petite ni trop clairsemée. Types de mines ( 9.2.4 ) : à orin
      ( profondes, plus faciles à trouver ), de fond ( discrètes, eaux peu profondes ), flottantes ou dérivantes,
      ascensionnelles ( les plus dangereuses : roquette ou torpille libérée au passage, comme le CAPTOR ), mobiles
      ( lancées par tube ). Une explosion sous la quille détruit la plupart des navires.""",
      f"{M}, § 7.2.5 p. 229-230 ; § 9.2.4 p. 304-307", ["Mining", "mines", "mouillage", "délai d'armement"]),
    f("meca-mission-deminage", "mecanisme", "Mission de déminage (Mine-Clearing) et contre-mesures",
      """La mission Mine-Clearing ( 7.2.6 ) est une mission de zone pour détecter et neutraliser les mines. Seules les
      unités équipées ( bouton MCM sur leur panneau : chasseurs et dragueurs de mines, hélicoptères MCM, drones et ROV
      embarqués, qui rejoignent la mission avec leur navire ) peuvent draguer ; certaines ne font que détecter. Deux
      méthodes ( 9.2.4 ) : le DRAGAGE, qui fait exploser les mines à distance moins dangereuse ( drague mécanique,
      magnétique, acoustique, multi-influence ) et la CHASSE, mine par mine, par plongeurs ou robots ; beaucoup de
      mines sont indraguables et doivent être chassées. Les dragueurs sont endommagés par les explosions : pour durer,
      prévoir une règle du tiers et un port de réparation où les bâtiments tournent. Les avions détectent moins bien
      mais détruisent mieux les mines ; les navires l'inverse : ils se complètent. Un couloir étroit et sûr vaut mieux
      qu'une zone trop large. Dans la base, les capteurs de dragage donnent largeur de dragage et vitesse maximale.""",
      f"{M}, § 7.2.6 p. 230-232 ; § 9.2.4 p. 304-307", ["Mine-Clearing", "déminage", "MCM", "dragage", "chasse aux mines"]),
    f("meca-mission-cargo", "mecanisme", "Mission de fret (Cargo) : livraison, transfert, débarquement amphibie et aéroporté",
      """La mission Cargo ( 7.2.7-7.2.8 ) sert aux insertions amphibies et aéroportées ( indispensable pour l'IA ) et
      à la logistique. Deux types : LIVRAISON ( Delivery ), vers une zone de points de référence : le fret est déchargé
      dans la simulation ( les unités sortent sur la carte et reçoivent des ordres ; munitions et carburant passent dans
      les magasins et réservoirs des unités ) ; TRANSFERT, d'une unité-hôte à une autre ( base à base, port à port,
      dépôt vers base aérienne ) sans sortir sur la carte. Les unités terrestres d'une mission cargo doivent commencer
      chargées dans leur source ( navire, base ) ; elles débarquent quand la mission s'active et qu'elles sont à portée.
      Options : « déplacer tout le fret de toutes les sources » ( chaînes de missions de fret ), véhicules qui se
      transfèrent eux-mêmes. Le fret « conteneur » ( base DB3K 493 et plus ) porte munitions, carburant ou contenu
      libre : livré, il va dans un dépôt existant à moins de 2 nm ou crée un point avancé de ravitaillement ( FARP ) ;
      les munitions livrées rechargent les unités qui emploient le même numéro d'arme. Note historique du manuel : la
      plupart des débarquements depuis 1900 ont réussi, parce qu'on ne les lance qu'avec des moyens écrasants.""",
      f"{M}, § 7.2.7-7.2.8, p. 232-237", ["Cargo", "fret", "amphibie", "aéroporté", "logistique", "FARP", "conteneur"]),
    f("meca-ato-planificateur", "mecanisme", "Ordre de mission aérienne (ATO), plans de vol et planificateur d'opérations",
      """Une mission peut être inscrite à l'ordre de mission aérienne ( ATO, 7.6 ), qui récapitule missions et paquets.
      L'éditeur de plans de vol permet de fixer pour chaque vol les heures de décollage et sur objectif, les points de
      passage, vitesses, altitudes, la doctrine et l'usage des capteurs par point ; verrouiller une vitesse ou une heure
      peut faire manquer de carburant. Les réservoirs de tâches ( Task Pool ) et les paquets ( Package ) organisent les
      opérations complexes : on met les unités dans le réservoir, puis on crée des paquets qui y puisent. Une unité
      « dynamique » ( multi-mission ) reste disponible pour plusieurs missions ; ses missions suivantes ne partent que
      quand la précédente est marquée satisfaite ( à la main ou par déclencheur ). Le planificateur d'opérations ( 7.4-
      7.5 ) gère des unités dynamiques et des estimations, et se pilote aussi en Lua ( 7.5.2 ). Pour un état-major :
      préparer l'ATO à l'avance, synchroniser l'heure sur objectif des frappeurs, des escortes, des brouilleurs et des
      tirs de missiles de croisière navals, et garder une réserve.""",
      f"{M}, § 7.1.1 p. 201-210, § 7.4-7.6 p. 240-259", ["ATO", "plan de vol", "package", "task pool", "planification"]),
    f("meca-regle-du-tiers", "mecanisme", "Règle du tiers, unités en station et taille des vols",
      """La règle du tiers ( « 1/3 Rule » ) existe sur les missions de patrouille, de soutien, de mouillage et de
      déminage : seul un tiers des avions affectés décolle et reste sur zone à la fois, les autres se préparent au sol ;
      on obtient une présence continue au prix d'une densité plus faible. Sans elle, tout le paquet part ensemble
      ( effort maximal, puis trou de couverture pendant la remise en œuvre ). « Garder N unités par classe en station »
      fixe un nombre ; en cas de conflit avec la règle du tiers, le plus grand l'emporte. La taille des vols ( Flight
      Size ) groupe les avions qui volent sur un même trajet ; avec « forcer la taille », un vol incomplet ne part pas.
      Mesures de l'atelier : une patrouille ne décolle que par vols d'au moins deux avions de la même base ( un avion
      seul reste au parking indéfiniment ) ; une frappe neuve attend des vols de quatre si on ne règle pas la taille.
      Affecter donc les avions par paires, comme dans le réel. En Lua : ScenEdit_SetMission(camp, nom, { OneThirdRule =
      true/false, StrikeFlightSize = 2, StrikeUseFlightSize = false }).""",
      f"{M}, § 7.2.2-7.2.6 ; mesures cmo/lua/hmt_pont.lua ( HMT_patrouille, HMT_frappe ) et banc v8 du 02/10", ["règle du tiers", "OneThirdRule", "taille des vols", "patrouille"]),
    f("meca-ravitaillement-en-vol", "mecanisme", "Ravitaillement en vol (AAR) : réglages des missions et des ravitailleurs",
      """Les missions règlent le ravitaillement en vol ( 7.1.1 ) : autorisé, autorisé sauf ravitailleur à ravitailleur,
      interdit, ou hérité du camp. Le planificateur avancé choisit le ravitailleur le plus proche ayant assez de
      carburant, ou ceux d'une mission précise ( pour éviter que des bombardiers lourds vident de petits ravitailleurs ).
      Options : nombre minimal de ravitailleurs ( en vol ou en station ) sans lequel la mission ne part pas ; lancer sans
      ravitailleur en place ( très risqué : les avions ne trouvent que les ravitailleurs devant eux ) ; nombre maximal
      de receveurs en file par ravitailleur ; seuil de carburant où les receveurs cherchent un ravitailleur ; rayon dans
      lequel un receveur peut réserver un ravitailleur. Compatibilité matérielle : perche rigide ( boom, avions de
      l'USAF ) contre perche et panier ( marine américaine, Europe, Russie ) ; un ravitailleur à boom seul ne sert pas un
      avion à perche. La base DB3000 donne ces capacités dans les fiches avions ( « ravitaillement par perche rigide »,
      « ravitailleur à paniers d'aile »… ). Doctrine du camp : Refuel/UNREP autorisé ou non, choix du ravitailleur,
      ravitaillement d'alliés.""",
      f"{M}, § 7.1.1 p. 201-210 ; § 3.3.13 MISC p. 59 ; DB3000 EnumAircraftCode 8001-9003", ["ravitaillement en vol", "AAR", "ravitailleur", "boom", "perche"]),

    # ------------------------------------------------------------------ DOCTRINE ET ROE
    f("doctrine-heritage", "doctrine", "La doctrine dans CMO : camp, mission, groupe, unité ( héritage )",
      """La doctrine regroupe quatre onglets ( 3.3.12 ) : Général ( règles d'engagement, EMCON, options air, surface,
      sous-marin, terre ), EMCON, autorisation de tir des armes ( WRA ) et Retrait/Redéploiement. Chaque réglage peut être
      « hérité » : une unité hors mission suit la doctrine de son camp ; une unité affectée suit celle de sa mission
      quand elle contredit le camp ; un groupe et ses unités suivent la même chaîne. Des boutons remettent la doctrine à
      l'héritage. On règle la doctrine du camp par le menu Jeu, l'éditeur de camps ou Ctrl+Maj+F9 ; on peut
      l'enregistrer dans un fichier et la recharger. Le manuel insiste : maîtriser doctrine, EMCON, WRA et retrait est
      la clé pour que les unités se conduisent bien sans intervention. En Lua : ScenEdit_SetDoctrine({side=...} ou
      {guid=...} ou {mission=...}, {cle = valeur}) et ScenEdit_GetDoctrine ; clés vues dans notre pont :
      weapon_control_status_air / surface / subsurface / land, engage_opportunity_targets, use_nuclear_weapons,
      quick_turnaround_for_aircraft, air_operations_tempo, bingo_threshold, fuel_state_rtb, weapon_state_rtb,
      withdraw_on_damage, withdraw_on_fuel.""",
      f"{M}, § 3.3.12-3.3.13, p. 55-57 ; cmo/lua/hmt_pont.lua ( HMT_DOCTRINE )", ["doctrine", "héritage", "ScenEdit_SetDoctrine"]),
    f("doctrine-roe-wcs", "doctrine", "Règles d'engagement : statut de contrôle des armes (Weapons Free / Tight / Hold)",
      """Le statut de contrôle des armes se règle séparément contre les cibles aériennes, de surface, sous-marines et
      terrestres ( 3.3.13 ). ARMES RESTREINTES ( Weapons Tight ) : l'unité ne tire que sur des contacts confirmés
      hostiles. ARMES LIBRES ( Weapons Free ) : elle tire sur tout ce qui n'est pas confirmé ami, avec un risque pour les
      neutres et les alliés. ARMES BLOQUÉES ( Weapons Hold ) : elle ne tire jamais d'elle-même, seulement sur ordre
      manuel. Autres règles : ignorer la route tracée pendant une attaque ; engager les contacts ambigus ( voir fiche
      doctrine-ambiguite ) ; engager les cibles d'opportunité ( attaquer des cibles hors mission : à activer avec
      prudence, cela peut entraîner des comportements dangereux ) ; emploi des armes nucléaires ( autorisé ou non ). Une
      défense sol-air ou une patrouille de défense aérienne en temps de guerre est en armes libres contre l'air pour ne
      pas laisser passer un intrus non identifié ; une frappe au-dessus d'un espace aérien partagé avec des neutres doit
      rester en armes restreintes. En Lua : clés weapon_control_status_air et sœurs ( valeurs usuelles de l'API : 0 libres,
      1 restreintes, 2 bloquées ; toujours relire par ScenEdit_GetDoctrine ). La posture entre camps ( hostile, neutre, ami, inconnu ) se règle par ScenEdit_SetSidePosture et se règle
      dans les DEUX sens.""",
      f"{M}, § 3.3.13 Rules of Engagement, p. 57-59 ; cmo/lua/hmt_pont.lua ( HMT_hostiles )", ["ROE", "Weapons Free", "Weapons Tight", "Weapons Hold", "règles d'engagement"]),
    f("doctrine-ambiguite", "doctrine", "Tir sur contact ambigu (Engage Ambiguous) et précision des contacts",
      """Chaque arme tolère une incertitude de position en distance et en travers, calculée à la volée ( 3.3.13 ) : une
      arme à guidage direct veut une cible précise ; une arme à accrochage après tir ( LOAL ) tolère beaucoup en distance
      ( tir sur relèvement ) mais peu en travers ( la largeur balayée par son autodirecteur ) ; une arme de zone tolère
      jusqu'à son rayon d'effet. Un contact ambigu a une zone d'incertitude ( AOU ). Trois réglages : « ignorer
      l'ambiguïté » ( l'IA tire quand même : grand risque de frapper un fantôme ou une position périmée ) ; « optimiste »
      ( l'incertitude doit être inférieure à 3 fois la tolérance de l'arme ) ; « pessimiste » ( inférieure à la
      tolérance ). Si l'incertitude dépasse la tolérance, l'arme ne part pas et la fenêtre d'allocation manuelle
      l'explique ( « downrange ambiguity larger than the weapon's acceptable limit » ). Pour tirer, il faut donc
      améliorer le contact : un capteur actif, une reconnaissance, un drone, une triangulation ESM par plusieurs
      porteurs. Nos missions de frappe affectent des cibles par guid ( pas par nom ) et ne partent que sur un contact
      détecté par le camp.""",
      f"{M}, § 3.3.13 Engage Ambiguous p. 58 ; § 9.2.8 p. 310-321", ["ambiguïté", "contact", "AOU", "doctrine", "tir"]),
    f("doctrine-emcon", "doctrine", "EMCON : contrôle des émissions, niveaux d'alerte et émissions intermittentes",
      """L'EMCON ( 3.3.14 ) décide si les émetteurs sont allumés : radar, sonar actif et brouillage offensif ( OECM ), chacun
      PASSIF ( éteint ) ou ACTIF ( allumé ). Un capteur actif se détecte de plus loin qu'il ne voit ( « comme le faisceau
      d'une lampe torche » ) : on ne l'allume que lorsque c'est nécessaire. L'EMCON s'hérite du concepteur, de la mission,
      du groupe ou de l'unité-mère ; les avions héritent de leur porteur ou de leur mission ; on peut le forcer par unité.
      Option de doctrine : « ignorer l'EMCON sous attaque » ( l'unité découverte allume ses capteurs pour se défendre ).
      Les émissions INTERMITTENTES alternent marche et arrêt ( durée d'émission, intervalle, variation aléatoire, réveil
      sur menace avec filtres de posture et d'identification, délai de mise en veille ) ; elles exigent un capteur réglé
      sur actif. Le niveau d'alerte du camp ( vert, bleu, jaune, orange, rouge ) sélectionne des réglages ; le changer
      sur une unité change TOUT le camp ( utiliser l'onglet personnalisé ). Une mission de patrouille peut n'émettre
      qu'à l'intérieur de sa zone. En Lua : ScenEdit_SetEMCON('Side'|'Mission'|'Group'|'Unit', nom, 'Radar=Active;Sonar=
      Passive;OECM=Active'), ScenEdit_SetSideEmconAlertness, Set/GetUnitIntermittentEmissionConfig.""",
      f"{M}, § 3.3.14, p. 65-70 ; § 3.3.13 EMCON p. 59", ["EMCON", "émissions", "radar", "OECM", "alerte"]),
    f("doctrine-wra", "doctrine", "Autorisation de tir des armes (WRA) : salve, portée de tir, valeur de défense antimissile",
      """La WRA ( Weapon Release Authorization, 3.3.15 ) règle, arme par arme et type de cible par type de cible, COMBIEN
      d'armes tirer par cible, avec COMBIEN de tireurs, à quelle portée ( « tir automatique » à la portée maximale ou à
      25, 50, 75 % ) et la portée d'autodéfense. La catégorie « inconnu » vaut pour les contacts non classés. Exemple du
      manuel : deux AMRAAM contre un chasseur de 4e ou 5e génération, un seul contre un avion de soutien. Contre les
      navires, la WRA s'appuie sur la VALEUR DE DÉFENSE ANTIMISSILE de la cible ( en « équivalents Harpoon » : 2 pour une
      vedette ou un navire civil, jusqu'à 96 pour un Ticonderoga ou un Kirov modernisé ), utilisable seulement contre une
      cible identifiée : tirer autant, deux fois ou quatre fois cette valeur, ou la moitié ou le quart pour des missiles
      supersoniques lourds. La WRA permet aussi de tirer en « zone sans échappatoire » ( la cible ne peut plus fuir par
      un demi-tour ), de réduire la portée de tir pour un meilleur taux de destruction, et de donner une « personnalité » :
      équipage nerveux ( tir au maximum de portée, toutes les armes ) ou prudent ( courte portée, un tir à la fois ). En
      Lua : ScenEdit_SetDoctrineWRA / GetDoctrineWRA. La base donne la WRA par défaut des armes ( DataWeaponWRA ).""",
      f"{M}, § 3.3.15, p. 70-73 ; DB3000 DataWeaponWRA, EnumWeaponWRA*", ["WRA", "salve", "défense antimissile", "doctrine", "portée de tir"]),
    f("doctrine-carburant-armes-rtb", "doctrine", "Retour à la base : Bingo, Joker, Winchester, Shotgun",
      """Deux familles de seuils font rentrer un avion ( 3.3.13 options air ). CARBURANT : l'état « Bingo » ( juste assez
      pour rentrer, défaut ) ou des états « Joker » plus prudents ; « Fuel State/RTB » dit quand le VOL rentre : chaque
      avion seul, au premier avion qui atteint le seuil ( conseillé ), au dernier ( extrêmement risqué ) ou jamais
      ( encore plus risqué ) ; changer ces défauts expose à perdre des avions à sec. ARMES : « Winchester » = armes de la
      mission épuisées ; « Shotgun » = moins que tout ; variantes : toutes les armes BVR ou à distance de sécurité tirées,
      un seul engagement BVR ( frapper et fuir face à un adversaire supérieur ), un seul engagement WVR ou de frappe
      ( attaquant au sol qui ne doit pas traîner sous la défense ), autoriser les cibles d'opportunité au canon.
      « Weapons State/RTB » dit quand le vol rentre ( premier, dernier avion… ), bien moins risqué qu'avec le carburant.
      Les chargements DB3000 portent leur réglage par défaut ( champ WinchesterShotgun ). Clés Lua : bingo_threshold,
      fuel_state_rtb, weapon_state_rtb. Pour une défense aérienne de base, Winchester ; pour une interception en
      infériorité, Shotgun un engagement BVR.""",
      f"{M}, § 3.3.13 Air Options, p. 60-63 ; DB3000 EnumLoadoutWinchesterShotgun", ["Bingo", "Joker", "Winchester", "Shotgun", "RTB", "carburant"]),
    f("doctrine-tempo-rotation", "doctrine", "Tempo des opérations aériennes (Surge / Sustained) et rotation rapide (Quick Turnaround)",
      """Le TEMPO du camp ( 3.3.13 ) règle la cadence des sorties : « Surge » ( effort maximal ) génère des sorties bien
      plus vite que « Sustained » ( effort durable ). Historiquement un effort maximal ne tient pas longtemps : la guerre
      du Golfe a connu deux périodes de surge ( début de la campagne et guerre terrestre ). Le tempo s'ajoute aux temps
      de préparation des chargements ( ReadyTime de la base DB3000 : souvent 180 min en air-air, 360 min pour les armes
      à distance de sécurité JASSM-ER, SDB, Storm Shadow, Kh-59, 1 200 min pour des bombardiers ). La ROTATION RAPIDE
      ( Quick Turnaround ) modélise une activité frénétique ( frappes israéliennes de 1967 ) : un avion refait des
      sorties courtes avec un temps de préparation réduit, puis subit un temps de repos. Réglages : oui ( tous les
      chargements éligibles ), chasse et ASM seulement ( les chargements air-sol gardent le tempo normal ), non. La base
      indique par chargement si la rotation rapide est permise, son temps de préparation, le nombre maximal de sorties et
      la pénalité ( ex. F-16 polonais en AIM-120 : 60 min, 2 sorties ). Clés Lua : air_operations_tempo,
      quick_turnaround_for_aircraft. Doctrine de l'atelier : surge les trois premiers jours, puis effort durable.""",
      f"{M}, § 3.3.13 Air Options, p. 60-61 ; DB3000 DataLoadout ( ReadyTime, QuickTurnaround_* ) ; cmo/doctrine.py", ["tempo", "surge", "sustained", "quick turnaround", "rotation rapide", "ReadyTime"]),
    f("doctrine-air-options", "doctrine", "Options de doctrine air : BVR, largage, mitraillage, évasion",
      """Autres options air de la doctrine ( 3.3.13 ) : LOGIQUE D'ENGAGEMENT BVR : suivre son missile en ligne droite
      ( doctrine rigide, mal entraînée, ou volonté de venir au contact ), « crank » si possible ( défaut : virer jusqu'au
      bord du cône du radar de guidage et ralentir pour rester loin ), « crank and drag » ( puis s'éloigner dès que le
      missile devient autonome : rester à distance coûte que coûte ). LARGUER LES CHARGES sous attaque : l'avion allégé
      manœuvre mieux mais ne remplit plus sa mission ( c'était le vrai but des intercepteurs nord-vietnamiens ).
      MITRAILLAGE air-sol au canon : oui pour un avion sacrifiable en appui, non contre une forte artillerie
      antiaérienne. ÉVASION AUTOMATIQUE : manœuvres préprogrammées sous attaque ; la couper pour qu'un avion presse son
      attaque. Les avions esquivent dès qu'ils détectent l'illumination d'un radar de conduite de tir ( ESM ), avant même
      de voir le missile. Ignorer la route tracée pendant une attaque, et navigation des unités terrestres ( route la
      plus courte ou ligne droite : risque de rester coincé en montagne ).""",
      f"{M}, § 3.3.13 Air Options et Land Warfare, p. 60-65 ; § 9.1.1 ESM p. 283", ["BVR", "crank", "drag", "largage", "mitraillage", "évasion"]),
    f("doctrine-asuw-asw", "doctrine", "Doctrine antinavire et sous-marine (ASuW, ASW)",
      """Antinavire ( 3.3.13 ) : employer les missiles sol-air contre les navires ( mode ASuW de la plupart des SAM à
      guidage radar ) ; GARDER LA DISTANCE ( maintain standoff : rester dans la portée de ses armes mais hors de celle des
      armes connues de l'ennemi ; sinon l'unité charge et tire de tout, jusqu'au canon ) ; utiliser les points de passage
      des missiles ( tir en « baïonnette » pour masquer la position du tireur, si la portée le permet ). Sous-marins :
      éviter le contact ( « toujours », ou « sauf légitime défense » ) ; plonger quand une menace est détectée ( radar,
      ESM ou proximité ) ; seuils de recharge des batteries en transit et en combat ( quand remonter au schnorchel ) ;
      emploi de la propulsion anaérobie ( AIP : toujours, jamais, ou au combat ) ; sonar trempé automatique des
      hélicoptères en vol stationnaire bas. Portée « cinématique » des torpilles : tirer à la portée physique maximale
      au lieu de la portée « pratique » ( qui empêche la cible de fuir à pleine vitesse ) ; le réglage « cinématique pour
      tirs manuels » laisse l'IA prudente mais permet au chef d'achever de loin un marchand sourd. Retrait et
      redéploiement ( 3.3.16 ) : un navire rentre au port s'il est trop endommagé ou à court de carburant ou de munitions,
      et ressort à plein ( défaut : moins de 5 % de dégâts ).""",
      f"{M}, § 3.3.13 ASuW / Submarine & ASW, p. 64-65 ; § 3.3.16 p. 73", ["ASuW", "ASW", "sous-marin", "standoff", "AIP", "torpille", "retrait"]),

    # ------------------------------------------------------------------ CAPTEURS, CONTACTS
    f("meca-capteurs-familles", "mecanisme", "Les capteurs de CMO : radar, ESM, optique, sonar, PCL, MAD",
      """Quatre familles principales ( 9.1.1 ). RADAR : actif, donc brouillable et révélateur de son porteur ; champ de
      vision limité ( les radars de conduite de tir ont des faisceaux de quelques degrés ), balayage mécanique lent ;
      un radar qui illumine une cible ne peut plus en engager d'autre ; attaquer un site sol-air de plusieurs directions
      à la fois le sature. Les générations comptent : impulsions simples ( pas de vision vers le bas ), Doppler pulsé,
      agilité de fréquence ( résiste au brouillage ), NCTR ( identification des réacteurs ), AESA ( balayage électronique,
      précis, insensible aux astuces comme le « Doppler notching », mais moins sensible hors de l'axe ). ESM : détecteurs
      passifs d'émissions, du simple détecteur d'alerte radar à l'identification précise de l'émetteur ; moins précis
      qu'un capteur actif, mais plusieurs porteurs triangulent. OPTIQUE et infrarouge : passifs, identifient la cible,
      mais champ étroit et peu de précision en distance. SONAR : actif précis mais trahit ; passif discret mais imprécis ;
      antennes de flanc et remorquées. PCL : radar passif utilisant les émetteurs civils, alerte avancée mais pas de
      piste de tir. MAD : détecteur magnétique anti-sous-marin, sans distance, à très courte portée. Les fiches capteurs
      de la base donnent portée, bandes, capacités ( veille aérienne, surface, sol ) et particularités.""",
      f"{M}, § 9.1.1, p. 281-286", ["capteurs", "radar", "ESM", "sonar", "infrarouge", "AESA", "MAD", "PCL"]),
    f("meca-contacts-classification", "mecanisme", "Des capteurs à la cible : contacts, classification, identification, OODA",
      """Tout combat commence par VOIR ( 9 ). Un capteur crée un CONTACT avec une zone d'incertitude ( AOU ) ; le camp
      partage ses contacts ( image commune ) si les communications le permettent. La CLASSIFICATION progresse : 0 inconnu,
      1 milieu connu ( air, surface… ), 2 type connu ( chasseur, frégate, site SAM ), 3 classe connue, 4 identifié ( son
      camp et sa plate-forme ). L'IFF donne le camp, la NCTR et l'imagerie donnent la classe, l'ESM peut identifier un
      émetteur. La posture ( hostile, neutre, inconnu ) vient de la posture entre camps et des zones. Le délai entre
      détection et tir est la boucle OODA de l'unité ( détection, ciblage, évasion, en secondes dans la base : par
      exemple un F-16 Block 52 a 5, 7 et 2 ), raccourcie par la compétence du camp. Un tir exige un contact assez précis
      pour l'arme ( fiche doctrine-ambiguite ), une arme à portée ( DLZ ), un directeur de tir disponible si l'arme en a
      besoin. Les contacts vieillissent : sans rafraîchissement ils disparaissent. Dans notre pont, u.ascontact donne les
      camps qui voient une unité, ScenEdit_GetContacts(camp) la liste des contacts avec classificationlevel, age,
      position et areaofuncertainty ; l'état-major ne traite une défense mobile comme menace que vue et classée ≥ 2.""",
      f"{M}, § 9.2 p. 294, § 9.2.8 p. 310-321, § 6.3.4 ; cmo/lua/hmt_pont.lua ( HMT_vus ) ; cmo/etat_major.py ( CLASSIF_MIN )", ["contact", "classification", "identification", "OODA", "IFF", "NCTR", "brouillard de guerre"]),
    f("meca-guerre-electronique", "mecanisme", "Guerre électronique : brouillage défensif (DECM) et offensif (OECM)",
      """Deux sortes de contre-mesures électroniques ( 9.2.6 ). Le brouilleur DÉFENSIF ( DECM, autoprotection ) intervient
      dans le calcul final quand une arme à autodirecteur adapté arrive sur l'unité : réussir à la leurrer dépend du
      hasard et des GÉNÉRATIONS du brouilleur et de l'autodirecteur ( un vieux DECM arrête mal un autodirecteur moderne,
      et inversement ). Le brouilleur OFFENSIF ( OECM ) émet du bruit qui gêne les radars de recherche de plusieurs
      unités : il ne modifie pas directement le calcul final, mais il peut faire échouer un tir semi-actif ou rendre la
      position de la cible si imprécise que l'adversaire ne tire jamais. Faiblesses : l'ESM détecte le brouillage comme
      une émission et localise le brouilleur ; l'efficacité dépend de la géométrie. Placer le brouilleur directement
      derrière les frappeurs, au plus près de la cible tout en restant à l'abri. Les leurres ( paillettes contre radar,
      fusées éclairantes et IRCM contre infrarouge ) sont calculés avant l'esquive. Le radar ennemi qui émet désigne sa
      position aux missiles antiradar ( HARM, AARGM, Kh-31P ). Côté base : les capteurs de type ECM indiquent gain,
      nombre de cibles et réduction de PoK.""",
      f"{M}, § 9.2.6 p. 309-310 ; § 9.2.1 p. 294-298", ["guerre électronique", "DECM", "OECM", "brouillage", "leurres", "antiradar"]),

    # ------------------------------------------------------------------ ARMES ET TIR
    f("meca-armes-guidage", "mecanisme", "Les armes et leurs guidages : inertiel, optique, infrarouge, semi-actif, actif, antiradar",
      """Armes non guidées ( 9.1.2 ) : canons, bombes, roquettes, et missiles balistiques ( trajectoire en cloche, corps de
      rentrée, leurres, planeurs hypersoniques ). Guidages : INERTIEL ( coordonnées programmées, de l'ancien balistique
      imprécis à l'arme ultra-précise recalée GPS ) ; OPTIQUE et INFRAROUGE ( image ou chaleur ; air-air infrarouge en
      poursuite arrière, secteur arrière ou tous secteurs ) ; SEMI-ACTIF RADAR ( la cible doit être illuminée par le radar
      du tireur jusqu'à l'impact : rompre l'accrochage fait perdre le missile ) ; SEMI-ACTIF LASER ( bombe guidée laser,
      désignation possible par un autre avion ou une équipe au sol ) ; ACTIF RADAR ( autodirecteur embarqué ; un AMRAAM
      doit pourtant être lancé sur une cible que le tireur détecte, sauf AIM-120D avec liaison et illuminateur ami comme
      un E-2D ) ; ANTIRADAR, certains avec mémoire de position ou parachute de rôdeur ( ALARM ), ou guidage multiple
      ( AARGM : antiradar puis GPS et radar actif si le radar s'éteint ). Propulsion : la plupart des missiles accélèrent
      puis planent, perdent de l'énergie en air dense et en manœuvre ; les missiles longue portée montent haut ( loft ) ;
      le SM-6 garde un moteur continu. Torpilles : inertielles, filoguidées ( le fil casse au-dessus de 10 nœuds ou en
      virage serré ), autoguidage acoustique ou sur sillage ( plus dur à leurrer ). Les fiches armes donnent portées par
      domaine, PoK, vitesse, autodirecteur, cibles et particularités.""",
      f"{M}, § 9.1.2, p. 286-294", ["armes", "guidage", "missile", "torpille", "antiradar", "laser", "balistique"]),
    f("meca-ogives-degats", "mecanisme", "Ogives, points de dégâts et modèle de dégâts",
      """Chaque arme porte une ou plusieurs ogives ( DataWarhead ) : type ( explosive à souffle et fragmentation,
      perforante, pénétrante pour cibles durcies, charge creuse, à sous-munitions, thermobarique, nucléaire… ), POINTS
      DE DÉGÂTS ( DP ) et masse d'explosif. Chaque cible a ses points de dégâts ( navires : par exemple 1 270 pour un
      Arleigh Burke Flight I ; avions : quelques points, 5 pour un F-16 ) et un blindage ( installations et véhicules :
      de « aucun » à « spécial 201-500 mm RHA » ; navires : ceinture, ponts, cloisons ). Une unité endommagée perd des
      performances ( capteurs, armes, vitesse ) et peut prendre FEU ou, pour un navire, être INONDÉE : tant que le feu ou
      l'inondation dure, les dégâts montent, et l'unité est détruite si l'un d'eux atteint son maximum, quels que soient
      ses points restants ( 9.2.7 ). L'équipage lutte selon sa compétence et la vitesse ( un navire à pleine puissance est
      plus vulnérable ). Les codes de construction des navires réduisent les DP ( coque aluminium -30 %, normes
      marchandes -30 %… ). La 1.10 a refait les dégâts à la base. Pour choisir une arme contre une cible : comparer les
      cibles autorisées et les DP de l'ogive au blindage et aux DP de la cible ; perforante sur abri durci et dépôt
      enterré ( deux GBU-12 n'ont fait que 2,4 % à un dépôt enterré de 3 200 points ).""",
      f"{M}, § 9.2.7 p. 310 ; § 9.1.2 Warhead Types p. 293 ; § 9.3.1 p. 325-330 ; DB3000 DataWarhead, EnumShipCode 4001-4022 ; sonde de frappe du 02/10 ( cmo/catalogue.py )", ["dégâts", "points de dégâts", "ogive", "feu", "inondation", "blindage"]),
    f("meca-pourquoi-pas-de-tir", "mecanisme", "Pourquoi mon arme ne tire pas : les refus de tir de CMO",
      """La section « My weapon won't fire » ( 9.2.8 ) liste les conditions vérifiées avant chaque tir ; l'allocation
      manuelle affiche la raison. Principales : affût hors d'usage ; pas d'autorisation nucléaire ; cible plus RAPIDE ou
      plus HAUTE que le permet l'arme ( vitesse et altitude maximales de cible ), ou plus BASSE que son altitude minimale ;
      arme incapable de tir sur relèvement ( BOL ) ; arme qui exige une position précise ; arme en soute, pas sur l'affût
      ( attendre le rechargement ) ; arme inadaptée à la cible ; lanceur trop haut ou trop bas ( enveloppe de tir ) ;
      cible hors du cône avant ( armes fixes ) ; mauvais secteur pour un missile à poursuite arrière ; délai de la boucle
      OODA pas écoulé ; torpille ASM à larguer à moins de 0,5 nm du point visé ; hors portée maximale ou dans la portée
      minimale ; portée de lancer d'une arme balistique à cette altitude ; cible à moins de 5 nm hors de l'arc de l'affût ;
      glace ; canon sans contrôle local ni directeur ; autodirecteur qui doit accrocher avant le tir ; pas de directeur
      d'illumination, ou tous ses canaux occupés, ou cible non illuminable ( furtivité, pas de ligne de vue ) ; pas de
      canal de liaison de données ; hors de la zone de tir dynamique ( DLZ ) ; ambiguïté de la cible trop grande.""",
      f"{M}, § 9.2.8, p. 310-321", ["tir", "refus", "DLZ", "OODA", "illumination", "BOL", "ambiguïté"]),
    f("meca-dlz", "mecanisme", "Zone de tir dynamique (DLZ) et zone sans échappatoire (NEZ)",
      """La zone sans échappatoire ( NEZ ) suppose qu'au tir la cible fait demi-tour et fuit à sa vitesse connue : le
      missile doit la rattraper en ligne droite. Simple, mais trompeuse : contre un MiG-25 rapide qui arrive de face, il
      faut au contraire tirer PLUS loin. La zone de tir dynamique ( DLZ, 9.2.9 ) répond à « que se passe-t-il si je tire
      maintenant et que la cible continue comme elle va ? » : elle tient compte du cap, de l'altitude, de la vitesse de
      la cible et des particularités cinématiques et de guidage de l'arme ( loft, vitesse quasi constante… ), avec des
      algorithmes distincts pour cibles aérodynamiques, non manœuvrantes ( missiles de croisière ) et balistiques ou
      orbitales. L'IA évite de tirer à l'extrême bord de la portée : elle sacrifie un peu de distance pour assurer la
      destruction, avec quelques tirs « de tireur d'élite ». Être dans la DLZ ne garantit rien contre une cible alertée
      qui manœuvre, mais un tir esquivé la met sur la défensive. La WRA peut imposer un tir en zone sans échappatoire.
      Conséquence pour l'état-major : les portées DB3000 sont des maxima cinématiques ; la portée efficace contre un
      chasseur alerté est nettement plus courte.""",
      f"{M}, § 9.2.9, p. 321-323 ; § 3.3.15 p. 72", ["DLZ", "NEZ", "portée", "missile", "tir"]),
    f("meca-combat-aerien", "mecanisme", "Combat aérien : détection, esquive, contre-mesures, fuite devant un SAM",
      """Engager dépend de la portée, des capteurs et de l'arme ( 9.2.1 ) : du vieux missile infrarouge en poursuite
      arrière au missile actif tiré de loin et guidé par un autre avion via liaison CEC, sans que le tireur n'allume son
      radar. La plupart des vaincus n'ont rien vu venir. Une cible qui détecte l'attaque passe en « défensive » :
      ESQUIVE ( se mettre par le travers, « beaming » ; pénalité au coup selon compétence et agilité ; un cargo ne peut
      presque rien, un chasseur agile beaucoup ), CONTRE-MESURES ( paillettes et DECM contre radar, leurres et IRCM contre
      infrarouge, calculées avant l'esquive selon les générations ). Contre un missile sol-air : fuir à pleine vitesse
      ( un missile à propulsion puis planée perd de l'énergie et peut être distancé ), interposer le relief entre soi et le
      radar de guidage, ou défaite cinématique par manœuvre brutale en fin de course. Les ailiers sont gérés à partir du
      leader du dispositif. Le manuel rappelle ( 9.2.10 ) que la planification opérationnelle compte plus que la qualité
      de l'avion : un MiG-21 peut abattre un F-15 s'il a une occasion claire ; en 1972 les escortes américaines ont
      souffert mais protégé les frappeurs.""",
      f"{M}, § 9.2.1 p. 294-298 ; § 9.2.10 p. 323-325", ["combat aérien", "esquive", "beaming", "paillettes", "SAM", "fuite"]),
    f("meca-combat-naval", "mecanisme", "Combat naval : canons, saturation des défenses, boucle OODA",
      """Au canon, la précision dépend du mode de conduite de tir, de la distance et de la stabilité de la plate-forme :
      gros navire et mer calme tirent juste, petit patrouilleur sur mer formée mal ( 9.2.2 ). Contre les missiles, la cible
      se défend d'abord en abattant les missiles ( selon la qualité des deux camps : certains systèmes ne peuvent rien
      contre un missile rasant ou trop rapide ), puis par contre-mesures ( paillettes, leurres, DECM ). La BOUCLE OODA de
      la cible ( technologie et compétence ) et la vitesse du missile fixent combien de tirs de défense elle peut faire
      avant l'impact : un système ancien ou lent peut être totalement impuissant. Débat réel « furtif ou rapide » :
      CMO permet de le tester. Pour saturer, la WRA s'appuie sur la valeur de défense antimissile de la cible ( fiche
      doctrine-wra ) et les tirs simultanés de plusieurs porteurs avec une même heure sur cible. À moins de 5 nm, un
      navire ne tire qu'avec les armes qui portent dans l'azimut de la menace. Les fiches navires donnent la valeur de
      défense antimissile ( MissileDefense ) de chaque bâtiment.""",
      f"{M}, § 9.2.2 p. 298-299 ; § 9.2.8 p. 316", ["combat naval", "défense antimissile", "saturation", "OODA", "canon"]),
    f("meca-sous-marins", "mecanisme", "Sous-marins et lutte ASM : couche thermique, zones de convergence, datum",
      """Les sous-marins sont plus discrets mais voient moins loin, et sont fragiles ( 9.2.3 ). Une torpille entrante
      ( « torpedo datum » ), un navire touché sans cause visible ( « flaming datum » ) ou un missile qui sort de l'eau
      créent un contact sous-marin pour la victime. Nucléaires : rapides en permanence mais longtemps bruyants ; diesels :
      silencieux mais vident leurs batteries à grande vitesse ( fuir vite est une parade contre eux ). Bandes de
      profondeur : immersion périscopique ( seule où servent radar, ESM, périscope ; tous les missiles se tirent ;
      conduit de surface ; cavitation tôt ), faible immersion, juste au-dessus de la couche ( idéale pour chasser avec
      l'antenne remorquée qui pend sous la couche ), dans la couche ( détections réduites ), juste sous la couche ( chenal
      sonore profond : détections très lointaines, pire endroit si l'ennemi chasse ), grand fond ( transit, embuscade,
      posé sur le fond ). Zones de convergence : possibles avec au moins 200 m d'eau sous la cible, tous les 20 à 40 nm
      selon la latitude, anneaux de 5 nm ; portée directe maximale 20 000 yards ( ≈ 9,5 nm ). Les sonars de coque et
      bouées réglées « peu profond » portent mal sous la couche.""",
      f"{M}, § 9.2.3, p. 299-304", ["sous-marin", "ASM", "couche thermique", "zone de convergence", "datum", "sonar"]),
    f("meca-asm-moyens", "mecanisme", "Moyens de lutte anti-sous-marine : bouées, sonar trempé, MAD, torpilles larguées",
      """La lutte ASM combine plusieurs capteurs ( 9.1.1, 9.2.3 ) : SONARS DE COQUE et d'étrave des navires ( le conduit
      de surface les sert contre les sous-marins à immersion périscopique ), ANTENNES REMORQUÉES et sonars à immersion
      variable ( VDS ) qui passent sous la couche, BOUÉES ACOUSTIQUES larguées par avions de patrouille maritime et
      hélicoptères ( passives DIFAR/LOFAR, actives, réglées « peu profond » ou « profond » ; une option de la 1.10 limite
      leur nombre ), SONAR TREMPÉ des hélicoptères en stationnaire bas ( automatique si la doctrine le permet ), MAD
      ( détecteur magnétique à très courte portée, sans distance : d'où les bouées ). Une torpille ASM larguée doit
      tomber à moins de 0,5 nm de la position estimée. Les sous-marins se défendent par leurres acoustiques, contre-
      torpilles et en restant hors de portée ( doctrine « éviter le contact » ). Sous la glace, on ne tire ni ne largue.
      Mission adaptée : patrouille ASW ( zone ) ou frappe ASW ( contact précis ) ; frégates ASM avec hélicoptère
      embarqué, avions P-8A, Il-38N, sous-marins chasseurs ( SNA ).""",
      f"{M}, § 9.1.1 Sonar p. 284, § 9.2.3 p. 299-304, § 9.2.8 p. 314 ; carte historique ( bouées limitées en 1.10 )", ["ASM", "bouée acoustique", "sonar trempé", "MAD", "torpille", "patrouille maritime"]),
    f("meca-guerre-des-mines", "mecanisme", "Guerre des mines : poser, détecter, draguer",
      """Depuis 1945 les mines ont coulé ou endommagé plus de navires que toute autre arme ( 9.2.4 ). Deux façons de
      poser : le champ « préfabriqué » de l'éditeur ( choisir une mine adaptée à la profondeur, en mettre plus que
      nécessaire : CMO en pose souvent moins que demandé ) et la mission Mining. Le déclenchement dépend du type d'unité
      et de la sophistication de la mine ( contact, influence magnétique, acoustique, pression, sismique, discrimination
      de cible, délai, compteur ) ; une explosion sous la quille détruit la plupart des navires, plusieurs explosions
      lointaines s'additionnent. Les avions volant bas peuvent aussi être touchés. Contre-mesures : dragage ( faire
      exploser à distance ) et chasse ( neutraliser une à une, seule méthode contre les mines indraguables ) ;
      complémentarité avion-navire ; drones idéaux pour la chasse ( pas d'équipage exposé ) ; corridor étroit plutôt que
      zone trop large ; prévoir réparation et rotation des chasseurs de mines. En Lua : ScenEdit_AddMinefield,
      GetMinefield, SetMine, DeleteMine, DeleteMinefield. Les fiches armes de type « mine » donnent la portée de
      détection et les fusées.""",
      f"{M}, § 9.2.4 p. 304-307 ; liste des fonctions Lua 1.10", ["mines", "guerre des mines", "dragage", "chasse aux mines", "champ de mines"]),
    f("meca-combat-terrestre", "mecanisme", "Combat terrestre et unités au sol dans CMO",
      """Le combat terrestre de CMO est volontairement simple ( 9.2.5 ) : les unités au sol servent surtout de cibles aux
      forces aériennes et navales, mais elles tirent et se déplacent ( « la meilleure arme de supériorité aérienne est un
      char au bout de la piste ennemie » ). Le TERRAIN compte beaucoup : marais très lents, forêts qui ralentissent et
      protègent du souffle, zones bâties très protectrices mais rapides par les routes. Les unités terrestres se
      ravitaillent comme des navires : une batterie vide se met à côté d'un camion de munitions qui porte ses missiles
      ( « replenish » ). Contre une cible au sol avec des armes non guidées, le coup dépend de la vitesse de la cible, de
      l'arme, du viseur de bombardement, de l'altitude et de la compétence. Modèle de CMO : les FORMATIONS ( bataillons
      sol-air, batteries, régiments ) sont des installations MOBILES ( catégorie 5001, elles roulent : SetUnit course ) ;
      un véhicule isolé est une unité « Vehicle » de DataGroundUnit ( T-72B3 = 102 ). Le planificateur d'opérations gère
      la scission et la fusion d'unités ( 7.4.3 ). Pour l'état-major : interdiction contre lanceurs ( chasse aux Iskander ),
      postes de commandement, logistique ; appui rapproché quand la guerre terrestre s'engage.""",
      f"{M}, § 9.2.5 p. 307-309 ; § 7.4.3 p. 244 ; sonde sol du 02/10 ( cmo/sonde_sol.py )", ["terrestre", "unités au sol", "terrain", "installation mobile", "véhicule", "ravitaillement"]),
    f("meca-bases-aeriennes", "mecanisme", "Bases aériennes : flux au sol, nœuds critiques, magasins",
      """Une base aérienne est soit une unité unique ( aérodrome générique, à réserver aux bases hors de portée de
      l'ennemi ), soit un GROUPE d'installations ( pistes, taxiways, points d'accès, abris, parkings, dépôts ) qui peut
      être attaqué élément par élément ( 9.3.1 ). Au décollage l'avion va de son abri à un point d'accès ou taxiway puis
      à la piste ; à l'atterrissage il refait le chemin, reçoit carburant et munitions. Cela donne des taux de sorties
      réalistes et rend la base dépendante de quelques NŒUDS. Minimum fonctionnel : une piste assez longue ( comparer à la
      distance de décollage de l'avion ), un point d'accès ou taxiway, un lieu d'accueil de la bonne taille, un dépôt à
      magasin. Le CARBURANT n'est pas suivi ( fourni à l'atterrissage ) ; les MUNITIONS le sont : les magasins doivent
      contenir les armes des chargements, sinon l'avion ne se réarme pas ( piège de notre guerre du 29/09 : magasins
      vides ). Des milliers de bases réelles s'importent ( fichiers .inst, ScenEdit_ImportInst ). Option du scénario
      « munitions illimitées » : rend inutile la destruction des dépôts.""",
      f"{M}, § 9.3.1, p. 325-330 ; cmo/GUERRE-REELLE.md", ["base aérienne", "piste", "taxiway", "abri", "magasin", "munitions"]),
    f("meca-detruire-base", "mecanisme", "Détruire une base aérienne : quoi frapper",
      """Options pour neutraliser une base ( 9.3.1 ) : DÉTRUIRE LES AVIONS dans leurs abris ( souvent la moins efficace :
      abris durcis, avions dispersés ; il faut savoir où ils sont : avions à découvert vus par un capteur optique, avions
      en abri fermé seulement vus entrant ou sortant, d'où une surveillance persistante, par exemple une équipe au sol ) ;
      DÉTRUIRE LES DÉPÔTS DE MUNITIONS ( un chasseur sans armes ne sert presque à rien ; inutile si les munitions
      illimitées sont activées ) ; NEUTRALISER POINTS D'ACCÈS, TAXIWAYS ET ASCENSEURS ( ils ne peuvent pas être détruits
      définitivement et se réparent avec le temps, mais ils sont peu nombreux : excellent moyen de bloquer la base ) ;
      NEUTRALISER LES PISTES ( souvent le plus efficace, armes anti-pistes dédiées : BLU-107 Durandal, BetAB ; mais la
      piste se répare vite, surtout touchée par des armes non spécialisées : il faut refrapper ). Pour juger une arme :
      cibles autorisées ( « pistes », « structures durcies »… ) et points de dégâts de l'ogive contre blindage et points
      de la cible. Les bases navales ( 9.3.2 ) : un quai et un dépôt suffisent ; les navires à quai se détectent comme les
      avions sur une base.""",
      f"{M}, § 9.3.1-9.3.2, p. 325-331", ["OCA", "base aérienne", "piste", "dépôt", "abri", "frappe"]),
    f("meca-defense-aerienne", "mecanisme", "Défense aérienne intégrée (IADS) : construire et détruire",
      """Une défense aérienne doit d'abord VOIR ( 9.3.3 ) : radars de veille souvent éloignés des lanceurs, ESM, guetteurs.
      Trois étages d'armes : basse altitude et courte portée ( canons, MANPADS comme Stinger ), moyenne ( SA-6, Aspide,
      Buk ), haute altitude et longue portée ( SA-2, Nike, Patriot, S-300/S-400 ). Bien placés ils se renforcent : les SAM
      nord-vietnamiens tuaient peu mais forçaient les Américains à voler bas, dans l'artillerie qui abattait le plus.
      Couvrir toutes les altitudes et directions, se soutenir mutuellement, protéger lanceurs longue portée et radars par
      des défenses de point ( surtout contre des missiles de croisière ), ne faire émettre les radars qu'en cas de
      besoin. Pour détruire : soit les frapper comme toute cible, soit des patrouilles SEAD qui chassent les émissions.
      Attaquer un site de plusieurs directions à la fois l'empêche d'engager partout ( faisceaux limités, canaux
      d'illumination comptés ). Les options non cinétiques ( couper les nœuds de communication ) rendent l'IADS fragile.
      Les fiches installations donnent les armes sol-air et leur portée ( ex. bataillon S-400 russe : 48 missiles
      48N6DM à 135 nm ).""",
      f"{M}, § 9.3.3 p. 331-332 ; § 10.7.2 p. 350-355 ; DB3000 DataFacility 543", ["IADS", "défense aérienne", "SAM", "SEAD", "DEAD", "radar"]),
    f("meca-communications", "mecanisme", "Communications, liaisons de données et rupture des communications",
      """Les plates-formes portent des moyens de communication et des liaisons ( Link 11, Link 16, CEC, liaisons d'armes
      comme la liaison AIM-120 ou Aster ; fiches plates-formes, rubrique « Liaisons » ). L'image commune du camp
      repose sur eux. Si l'auteur active « Communications Disruption » ( 10.7 ), une unité dont tous les moyens sont
      détruits, ou mise « hors communications » par script ( ScenEdit_SetUnit({name=..., OutOfComms=true}) ) ou par
      l'éditeur, affiche NOCOMM : le camp ne connaît plus que sa dernière position, ni carburant, ni armes, ni dégâts ;
      l'unité perd l'image commune ( sa conscience se limite à ses capteurs ), garde un instantané de contacts qui se
      périme, peut poursuivre seule sa mission, mais sans coordination ni soutien mutuel ; risque de tir fratricide selon
      ses règles d'engagement. À la reconnexion elle partage ses contacts et son évaluation des dégâts ( BDA ). Le
      brouillage des communications intégré est réservé à l'édition professionnelle ; on l'approche par script. Une
      unité d'essaim ( drone, vedette ) perd beaucoup plus qu'un grand navire sans communications. Les drones perdent
      le contrôle selon leur niveau d'autonomie ( fiche meca-drones ).""",
      f"{M}, § 10.7-10.7.2, p. 347-355", ["communications", "liaison de données", "Link 16", "CEC", "NOCOMM", "cyber"]),
    f("meca-drones", "mecanisme", "Drones (UAV) : autonomie et perte de liaison",
      """CMO modélise le comportement des drones qui perdent le contact avec leur source de signal ( 9.4 ). Les niveaux
      d'autonomie de la base ( EnumAircraftAutonomousControlLevel ) : téléopéré ( « avion fantôme » : continue au même
      cap jusqu'au crash ), auto-récupérable ( attend brièvement le signal puis rentre ), mission modifiable ( termine ses
      derniers ordres puis rentre ), adaptatif ( termine si possible puis rentre ), coordination multi-véhicules ( suit
      le chef ), conscient du champ de bataille ( continue sa mission : contrôle maritime, patrouille ), entièrement
      autonome ( engage les cibles hostiles selon les dernières règles d'engagement reçues ). Brouiller ou couper les
      communications a donc des effets propres à chaque drone. La base décrit aussi les munitions rôdeuses ( « drone
      consommable » ) et les drones de combat ( UCAV ). Dans l'atelier : MQ-9A et Bayraktar TB2 basés à Mirosławiec, rôle
      « reco » ( sur la cible, en stand-off si elle est couverte par un parapluie sol-air ).""",
      f"{M}, § 9.4 p. 332 ; DB3000 EnumAircraftAutonomousControlLevel ; cmo/theatres/baltique_reel.py", ["drone", "UAV", "UCAV", "autonomie", "munition rôdeuse"]),
    f("meca-logistique", "mecanisme", "Logistique : magasins, rechargement, ravitaillement à la mer (UNREP), carburant",
      """Ce que CMO suit et ne suit pas. MUNITIONS : chaque navire, sous-marin, installation et base a des MAGASINS
      ( soutes ) qui rechargent les affûts ( fiches plates-formes : « réserves en soute » ) ; une base aérienne doit
      contenir les armes des chargements de ses avions, sinon pas de réarmement. CARBURANT des avions : non suivi à la
      base ( fourni à l'atterrissage ), mais l'avion en vol consomme et tombe à sec sans base ni ravitailleur. Navires :
      carburant suivi ; RAVITAILLEMENT À LA MER ( UNREP ) entre bâtiments compatibles ( codes de la base : « peut
      ravitailler à bâbord », « peut recevoir »… ; pétroliers-ravitailleurs AOR/AOE ), autorisé par la doctrine
      Refuel/UNREP. Unités terrestres : se ravitaillent auprès d'un camion de munitions. Missions Cargo : livrer munitions
      et carburant ( conteneurs, FARP ). Retrait/redéploiement : un navire rentre au port réparer et recompléter. En Lua :
      ScenEdit_AddWeaponToUnitMagazine, ScenEdit_FillMagsForLoadout, ScenEdit_AddReloadsToUnit,
      ScenEdit_DistributeWeaponAtAirbase, ScenEdit_RefuelUnit, ScenEdit_TransferCargo. La production d'armes et les
      stocks réels ne sont pas dans CMO : c'est au moteur ( l'économie ) de les fournir.""",
      f"{M}, § 9.3.1 p. 325-330, § 9.2.5 p. 308, § 3.3.13 MISC p. 59, § 7.2.7 p. 232 ; liste Lua 1.10 ; cmo/munitions.py", ["logistique", "magasins", "UNREP", "carburant", "rechargement", "dépôt"]),
    f("meca-unites-mesure", "regle", "Unités de mesure de la base DB3000 et du jeu",
      """Toutes les portées de la base DB3000 ( armes, capteurs, rayons d'action des chargements ) sont en MILLES NAUTIQUES
      ( nm ; 1 nm = 1,852 km ) ; les vitesses en NŒUDS ( 1 nœud = 1,852 km/h ; Mach 1 ≈ 661 nœuds en altitude ) ; les
      altitudes de vol, de croisière et de tir en MÈTRES ; les masses en kilogrammes ( déplacement des navires en
      tonnes ) ; les temps de préparation des chargements en minutes ; la consommation de carburant en kg par minute.
      Vérifié le 03/10 sur des valeurs connues : AIM-120D 86,4 nm ( 160 km ), Meteor 100 nm ( 185 km ), Iskander 270 nm
      ( 500 km ), ATACMS 162 nm ( 300 km ). Les fiches de cette base de connaissance donnent nm ET km. Les pièges : un
      calcul en km sur une portée lue en nm sous-estime la portée de 46 % ( l'atelier cmo/doctrine.py commente
      « ATACMS 162 km, Iskander 270 km » et compare des portées air DB à un seuil en km : à vérifier ). Les distances du
      jeu ( Tool_Range ) sont en nm ; les coordonnées en degrés décimaux.""",
      "DB3000 DataWeapon ( AirRangeMax, LandRangeMax ), DataSensor ( RangeMax ), DataLoadout ( DefaultCombatRadius ) ; vérification du 03/10 ; cmo/doctrine.py", ["unités", "nm", "nœuds", "km", "portée"]),
]
