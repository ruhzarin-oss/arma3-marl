"""Fiches ÉCRITES À LA MAIN ( 03/10/2026 ) : comment NOTRE pont et notre moteur emploient CMO ( atelier
/mnt/data/hmt/atelier-cmo/cmo ), les fonctions Lua vérifiées en vrai, et les règles de l'état-major. Sources : le code,
ses commentaires de sonde, et les verdicts des bancs réels ( 28/09-03/10 )."""

A = "/mnt/data/hmt/atelier-cmo/cmo"


def f(id, type, titre, texte, source, tags):
    return {"id": id, "type": type, "titre": titre, "texte": " ".join(texte.split()), "source": source, "tags": tags}


FICHES = [
    # ------------------------------------------------------------------ L'ATELIER : LE PONT
    f("atelier-pont-architecture", "atelier", "Le pont HMT vers CMO : fichiers et événement Lua",
      """Le moteur parle à CMO 1.10 ( build 1900.20, Steam, branche public_beta_multiplayer ) SANS socket ( réservé à
      Command PE ) et sans console : ALLER, le moteur écrit Lua/hmt_pont/cmd_<n>.lua ( un seul écrivain, cmo_labo.py ) ;
      un événement CMO « HMT_PONT » ( déclencheur RegularTime, chaque seconde de jeu ) lit la commande suivante par
      ScenEdit_RunScript et l'exécute sous pcall, UNE par passage ( CMO applique certains effets entre deux passages ) ;
      RETOUR, un reçu ImportExport/hmt_r_<n>.inst écrit par ScenEdit_ExportInst ( texte dans le champ Comments ) avec
      les lignes « R CLE nombres », puis « ECHO n nonce k code detail coeur » et « FIN » ; BATTEMENT hmt_sync.inst à chaque
      passage. Codes : 0 exécutée, 1 erreur Lua, 2 ne compile pas, 3 refus. Que des NOMBRES dans les reçus ( aucun texte
      du jeu ne remonte, aucun texte du moteur n'entre ). Latence mesurée : 0,96 s médiane, 1,36 s au pire ; le limiteur de
      la console 1.10 ( 3 envois puis un toutes les 30 s ) ne touche pas les événements ( 10 min, 0 perte ). Un scénario
      neuf démarre EN PAUSE : pas de battement avant que l'horloge tourne. Installer : deployer.py puis, une fois,
      ScenEdit_RunScript('hmt_pont/installer.lua') dans la console ; recharger le Lua : deployer.py --recharger.""",
      f"{A}/LISEZMOI.md ; {A}/lua/hmt_pont.lua ( en-tête ) ; banc réel du 29/09", ["pont", "Lua", "ExportInst", "RunScript", "événement"]),
    f("atelier-bac-a-sable-110", "atelier", "Bac à sable Lua de CMO 1.10 : ce qui manque, ce qui coûte",
      """Mesuré dans CMO 1.10.1900.20 ( sonde du 29/09 ) : le Lua n'a plus ni io, ni dofile, ni loadfile, ni load ; seule
      la table os reste ( time, clock, date, difftime ). Le lecteur des commandes est donc ScenEdit_RunScript, qui relit
      bien le fichier à chaque fois. Chaque RunScript sur un fichier ABSENT écrit une erreur dans Logs/LuaHistory_<date>.txt
      ( pas de mode silencieux : ≈ 95 octets par seconde, 8 Mo par jour ) : le pont n'interroge qu'un passage sur dix après
      un silence. Un appel Lua de plus de ~250 valeurs ne compile pas ( « too many registers ») : cmo_labo découpe les
      lots en paquets de 180. Les GLOBALES Lua survivent au rechargement d'un scénario. GetBuildNumber() rend « v1.10 -
      Build 1900.20 ». ScenEdit_SetSimulationFidelity vaut nil en mode jeu. Command_SaveScen(nom), non documentée, rend
      nil et semble écrire Scenarios/Autosave.scen. dp_percent des dégâts revient en TEXTE à la virgule française
      ( « 99,9 » ) : tonumber le lit nil ; calculer dp/startdp. La console a un limiteur « anti IA/ML » ( 3 envois puis un
      toutes les 30 s ) ; les événements n'en ont pas.""",
      f"{A}/LISEZMOI.md ; {A}/lua/hmt_pont.lua ( HMT_lecteur, pourcent ) ; mémoire guerre-reelle-cmo", ["Lua", "bac à sable", "1.10", "RunScript", "LuaHistory"]),
    f("atelier-suppression-differee", "atelier", "Suppressions différées et ralentissement de CMO après une table rase",
      """CMO 1.10 applique ScenEdit_DeleteUnit au passage SUIVANT : la fonction rend vrai mais GetUnit et la liste du camp
      montrent l'unité jusque-là ; la preuve d'une table rase est donc une autre commande ( HMT_recompter ) dans un passage
      ultérieur. Un import d'installation peut aussi n'être visible qu'au passage suivant ( HMT_adopter vient après
      HMT_importer ). MESURE CAPITALE du 02/10 : ce qui ralentit CMO, c'est la SUPPRESSION EN MASSE, pas la taille. Vide :
      x1,0 ; avec 1 719 éléments de bases, 257 radars et 47 sites sol-air ( 2 023 éléments ) : toujours x1,0 ; juste après
      la table rase de ces 2 023 éléments : x0,25, jusqu'au rechargement du scénario ( même cause que le x0,13 du 29/09 ).
      Règle : construire le théâtre UNE fois dans un scénario propre, le sauvegarder, repartir de cette sauvegarde à chaque
      guerre ; ne jamais effacer des milliers d'unités dans un scénario qui doit tourner ; sonder la base dans un scénario
      jetable. CMO n'utilise qu'environ un cœur par défaut : voir la fiche des réglages de performance.""",
      f"{A}/lua/hmt_pont.lua ( HMT_nettoyer, HMT_importer ) ; bancs de charge cmo_sondes/charge_paliers_* du 02/10", ["performance", "DeleteUnit", "suppression", "table rase", "vitesse"]),
    f("atelier-reglages-perf", "atelier", "Réglages de performance de CMO ( Command.ini ) et pauses automatiques",
      """La guerre réelle ( 228 avions, 2 056 éléments, 1 348 contacts ) tournait à x0,33 même moteur arrêté ( 02/10 ).
      Causes dans Config/Command.ini : RunCoreMultithreaded = False ( 1,5 cœur utilisé sur 24 ), UseAutosave = True ( 2 Mo
      réécrits toutes les 20 s ), LogDebugInfoToFile = True. cmo/reglages_perf.py les inverse CMO FERMÉ ( copie
      .hmt-avant-perf ), plus « Hi-fidelity mode » et « No-pulse time mode » décochés dans les options : résultat x0,997,
      CMO sur 3,1 cœurs. CMO RÉÉCRIT Command.ini EN QUITTANT : l'éditer pendant qu'il tourne ne sert à rien. Les POP-UPS
      du journal des messages METTENT CMO EN PAUSE ( manuel 6.4.3 ; section [MessageLog Preferences] ; types à pop-up :
      SpecialMessage, CustomUI, UnitLost, NewWeaponContact, UnitAIEmergency ) : cmo/sans_pauses.py les coupe, CMO fermé.
      Les calculs lourds lancés sur la même station ( traduction, embeddings ) doivent rester à 2 fils au plus, sinon la
      guerre tombe sous x0,9 ( 03/10 : x0,53 avec un calcul à 5 cœurs ).""",
      f"{A}/reglages_perf.py ; {A}/sans_pauses.py ; mémoire guerre-reelle-cmo ( 02/10 22 h 50 ) ; consigne du 03/10", ["performance", "Command.ini", "multithread", "pause", "pop-up"]),
    f("atelier-magasins-vides", "atelier", "Piège : les dépôts de munitions de la base DB3000 sont VIDES",
      """Guerre des blocs du 29/09 : après le tour 167, plus aucun combat. Cause prouvée : les aérodromes génériques de la
      base ( 1712, 1877, 1592 ) ET les vrais dépôts ( Ammo Bunker 322 / 325, Ammo Revetment 320 ) ont un magasin
      « Munitions » VIDE ( magasin 1185, capacité 10 000 ) : un avion posé ne se réarme jamais ( relevé final OTAN 18 en vol
      / 57 au sol, Russie 0 / 21 ). Les bases importées ( .inst ) arrivent aussi avec des dépôts vides. Il faut donc
      REMPLIR les dépôts : ScenEdit_FillMagsForLoadout({guid=base, loadoutid=L, quantity=N}) ajoute N « packs » des armes
      d'un chargement ( 4 packs du F-16 7453 = 16 AIM-120C-5, 8 AIM-9X, 8 réservoirs ) ; ScenEdit_AddWeaponToUnitMagazine
      ({guid, wpn_dbid, number}) ajoute une arme. Lecture : u.magazines[i].mag_weapons[j] ( wpn_dbid, wpn_current,
      wpn_maxcap, wpn_name ). Dans le moteur, chaque munition est ACHETÉE sur le budget du pays et livrée à sa base, comme
      dans le réel ( cmo/munitions.py, prix à valider ). Un avion réarmé sans arme en dépôt reste SANS armement
      ( chargement 3 ).""",
      f"{A}/GUERRE-REELLE.md ; {A}/munitions.py ; {A}/lua/hmt_pont.lua ( HMT_armer, HMT_stocks ) ; sonde palier 0 du 02/10", ["magasins", "munitions", "dépôt", "FillMagsForLoadout", "réarmement"]),
    f("atelier-patrouille-par-paires", "atelier", "Piège : une patrouille ne décolle que par vols de deux",
      """Banc v8 du 02/10 : un avion SEUL affecté à une patrouille reste « Parked » indéfiniment ( 8 min de sonde ) ; DEUX
      avions de la MÊME base décollent en ~2 min 45, roulage compris. u:Launch(true) force un décollage. Le moteur affecte
      donc toujours par paires ( comme dans le réel : patrouille, paire, dispositif ). De même, une frappe neuve attend des
      vols de quatre ( fiche atelier-frappe-onhold ). Autres constats du banc : un avion posé doit l'être SUR LE GROUPE de
      la base ( la base elle-même, dbid 0 ) : une piste seule refuse l'ajout ( REFUS 4 ) ; ScenEdit_AddUnit({type='Air',
      base=guid_du_groupe, loadoutid=...}) ; les abris « Medium » ( 4 ) sont trop petits pour Su-30 et Su-35 ( 22 refus ) :
      abris « Large » ( 27 ) ; les avions de guet, ravitailleurs et Il-22 sont « Very Large » ( tarmac 103, piste 4 000 m ).
      Nés en vol sans base, les avions tombaient à sec ( guerre du 29/09 : 37 des 48 pertes de Malden, 18 « run out of
      fuel and crashed »).""",
      f"{A}/lua/hmt_pont.lua ( HMT_poser_base_lot ) ; banc v8 cmo_sondes/banc_v8_20261002_180450.json ; mémoire guerre-reelle-cmo", ["patrouille", "paire", "décollage", "base", "abri", "Launch"]),
    f("atelier-frappe-onhold", "atelier", "Piège : une mission de frappe neuve naît « OnHold » et attend des vols de quatre",
      """Sonde du 02/10 : deux F-16 affectés à une mission Strike neuve sont restés 15 min au parking. Une frappe créée par
      ScenEdit_AddMission(camp, nom, 'Strike', {type='Land'}) naît en attente ( OnHold ) et attend des vols de QUATRE. Le
      pont ( HMT_frappe ) l'ACTIVE en écrivant mission.Phase = 20 et règle ScenEdit_SetMission(camp, nom,
      { StrikeFlightSize = 2, StrikeUseFlightSize = false }). Les cibles s'affectent par GUID : ScenEdit_AssignUnitAsTarget
      (guid, nom_mission) ; par NOM, la fonction ne fait rien. Les frappeurs s'affectent par ScenEdit_AssignUnitToMission
      (guid, nom) et les escorteurs avec un troisième argument vrai. Fermer une frappe : ScenEdit_DeleteMission(camp, nom)
      MARCHE en 1.10 ( relu absent ; ses avions en vol rentrent ) ; sinon la désactiver ( { isactive = false } ). Sans
      clôture, les avions d'une ancienne frappe continuent de l'exécuter. Deux GBU-12 n'ont fait que 2,4 % de dégâts à un
      dépôt enterré : le moteur choisit le chargement le PLUS PUISSANT ( somme des points de dégâts des ogives, x1,5 pour
      une ogive perforante ).""",
      f"{A}/lua/hmt_pont.lua ( HMT_frappe, HMT_clore ) ; {A}/catalogue.py ( chargement_frappe ) ; sonde_frappe du 02/10", ["Strike", "OnHold", "Phase", "AssignUnitAsTarget", "DeleteMission", "frappe"]),
    f("atelier-setloadout", "atelier", "Réarmer un avion : ScenEdit_SetLoadout par NOM, avion au sol, dépôt garni",
      """Réarmer ( changer le chargement ) d'un avion posé : ScenEdit_SetLoadout({ UnitName = 'HMT-<n>', LoadoutID = L,
      TimeToReady_Minutes = m }). PAR GUID, la fonction rend false ( sonde du 02/10 ) : il faut le NOM. Refus si l'avion
      n'est pas prêt ( en vol, en préparation ) : il GARDE son chargement. Le dépôt de sa base doit déjà contenir les armes
      du nouveau chargement, sinon CMO le laisse SANS armement ( chargement 3, « Reserve ») ; le moteur relit loadoutdbid
      et rend l'ancien s'il le faut. Temps de préparation réels de la base ( DataLoadout.ReadyTime ) : 180 min pour les
      chargements air-air courants, 360 min pour JASSM-ER, SDB, Storm Shadow, Kh-59 ( un avion réarmé ne repart que 6 h de
      scénario plus tard ), 1 200 min pour des bombardiers. Renommer une unité : écrire u.name sur l'objet de
      ScenEdit_GetUnit ; ScenEdit_SetUnit{ newname } et { name } sont IGNORÉS sans erreur.""",
      f"{A}/lua/hmt_pont.lua ( HMT_charger, HMT_adopter ) ; mémoire guerre-reelle-cmo ( 02/10 23 h 40 )", ["SetLoadout", "réarmement", "chargement", "ReadyTime", "UnitName"]),
    f("atelier-contacts-brouillard", "atelier", "Brouillard de guerre dans le pont : u.ascontact et ScenEdit_GetContacts",
      """Chaque chef ne voit que les contacts de son camp. Sonde du 03/10 : u.ascontact d'une unité liste les camps qui la
      voient ( { guid du contact, nom, side = GUID du camp qui voit } ) ; ScenEdit_GetContact({side, guid}) ou la liste
      ScenEdit_GetContacts(camp) donne le contact : classificationlevel ( 0 inconnu, 1 milieu connu, 2 type connu,
      3 classe connue, 4 identifié ), age ( s ), latitude, longitude, areaofuncertainty ( sommets de la zone
      d'incertitude ), actualunitid ( guid de la vraie unité ), type_description. L'OTAN avait 559 contacts et voyait 11 des
      14 unités sol russes ( 3 en classe 1 seulement ). HMT_vus rend « VU numéro classification âge lat lon sommets ».
      Règle de l'état-major : une défense mobile ne compte comme parapluie que VUE et classée ≥ 2, à la position du contact
      ( carte des menaces mémorisée jusqu'à destruction ) ; les installations fixes et les garnisons du temps de paix sont
      connues d'avance. Effet immédiat : les DEAD sur des défenses mal identifiées tombent.""",
      f"{A}/lua/hmt_pont.lua ( HMT_vus ) ; {A}/sonde_contacts.py ; {A}/etat_major.py ( renseigner, CLASSIF_MIN ) ; mémoire 03/10 0 h 20", ["contacts", "brouillard de guerre", "ascontact", "GetContacts", "classification"]),
    f("atelier-pertes-bilan", "atelier", "Pertes, dépenses et dégâts : VP_GetSide, journal des messages, HMT_etats",
      """Le coût réel de la guerre se lit dans CMO : VP_GetSide({side}).losses et .expenditures donnent pertes et
      munitions tirées par type ( Aircraft, Ship, Submarine, Facility, Weapon, Vehicle, Satellite ), dbid et nombre
      ( HMT_bilan ; les dbid d'avions et d'installations se recouvrent ). Le JOURNAL DES MESSAGES de CMO est la vérité sur
      les causes ( cmo/causes_cmo.py : « abattu », « run out of fuel and crashed » ) ; une estimation par distance comptait
      à tort des pannes sèches comme des combats. Les dégâts d'un élément : HMT_etats rend ETAT numéro pourcentage feu
      inondation, calculé de dp/startdp ( dp_percent_now est un texte à virgule française ). Les milliers d'éléments fixes
      des vraies bases restent hors du relevé de positions ( sonder des milliers d'installations ralentit CMO ) : leurs
      morts viennent du journal, leurs dégâts de HMT_etats. Un avion mort pendant une bascule est constaté auprès de CMO et
      compté une fois. Pertes et munitions remontent à l'économie du moteur.""",
      f"{A}/lua/hmt_pont.lua ( HMT_bilan, HMT_etats, HMT_positions ) ; {A}/causes_cmo.py ; mémoire pont-cmo-voie2", ["pertes", "dépenses", "VP_GetSide", "journal", "dégâts", "BDA"]),
    f("atelier-installations-reelles", "atelier", "Vraies installations : ImportExport .inst, ImportInst, guids réutilisés",
      """CMO livre 3 879 vraies installations ( ImportExport/<pays>/*.inst, 202 297 éléments : pistes, abris, dépôts, sites
      sol-air, radars, régiments, quais ; inventaire cmo_carte/installations.json ; boîte Baltique 356 installations,
      10 634 éléments ). ScenEdit_ImportInst(camp, 'Lithuania/Siauliai Air Base 2024.inst') crée 92 éléments et un groupe
      ( dépôts VIDES ). Pièges : CMO NE RECRÉE PAS un élément dont le guid a déjà servi dans la partie, même effacé
      ( Łask réimportée : 1 élément sur 62 ) → copies aux identifiants neufs dans ImportExport/HMT/Copies/ ; une
      installation réimportée reprend les guid de son fichier, et les globales Lua survivent au rechargement : un registre
      gardé « reconnaissait » des unités neuves ( REFUS 3 ) → HMT_recensement refait le registre depuis les NOMS
      « HMT-<n> » à chaque ouverture. Aucune base russe de la Baltique n'existe dans CMO ( Tchkalovsk, Donskoïé, Pskov,
      Levachovo, Besovets, Baltiïsk, Kronstadt ) : bases_construites.py les monte au même format. Le Bastion-P posé en mer
      est refusé.""",
      f"{A}/theatres/baltique_reel.py ; {A}/bases_construites.py ; {A}/lua/hmt_pont.lua ( HMT_importer, HMT_recensement ) ; mémoire guerre-reelle-cmo", ["installations", "ImportInst", "inst", "guid", "bases"]),
    f("atelier-troupes-au-sol", "atelier", "Troupes au sol dans le pont : installations mobiles et véhicules",
      """Sonde du 02/10 : les FORMATIONS au sol sont des installations MOBILES ( type 'Facility', catégorie 5001 ) avec
      leurs vraies armes ( u.mounts[i].mount_weapons ) : S-400 ( dbid 1937 ), Iskander ( 254 ), T-90A x4 ( 1918 ), BMP-3
      ( 2045 ), 2S19 ( 1953 ), Krab ( 2048 ) ; elles roulent ( ScenEdit_SetUnit({guid, course={{latitude, longitude,
      TypeOf='ManualPlottedCourseWaypoint'}}}) → OnPlottedCourse ). Un véhicule SEUL est de type 'Vehicle' ( DataGroundUnit,
      T-72B3 = 102 ). Le pont pose par ScenEdit_AddUnit({side, type, unitname='HMT-<n>', dbid, latitude, longitude}) ;
      genres HMT : Air, Ship, Submarine, Facility, Vehicle. Les lanceurs sol-sol ne sont affectés qu'aux cibles à LEUR
      portée ( ATACMS 162 nm, GMLRS, Iskander 270 nm d'après la base ). Paliers prévus : brigades et divisions réelles
      ( 11e corps d'armée à Kaliningrad, brigades polonaises, groupements OTAN des pays baltes ), artillerie, mouvements
      sur le terrain de CMO.""",
      f"{A}/sonde_sol.py ; {A}/lua/hmt_pont.lua ( HMT_poser, HMT_aller ) ; {A}/GUERRE-REELLE.md ( palier 5 )", ["troupes au sol", "installation mobile", "véhicule", "S-400", "Iskander", "SetUnit"]),
    f("atelier-doctrine-du-camp", "atelier", "Doctrine du camp pilotée par le pont ( HMT_doctrine )",
      """Le moteur règle 13 clés de doctrine de camp par index, et RELIT la valeur dans CMO : quick_turnaround_for_aircraft,
      air_operations_tempo, bingo_threshold, fuel_state_rtb, weapon_state_rtb, weapon_control_status_air, _surface,
      _subsurface, _land, engage_opportunity_targets, use_nuclear_weapons, withdraw_on_damage, withdraw_on_fuel
      ( ScenEdit_SetDoctrine({side=camp}, {[cle]=valeur}) puis ScenEdit_GetDoctrine ). La sonde du 02/10 a lu sur un avion :
      condition ( Parked… ), readytime, airbornetime, loadoutdbid, fuel, damage { dp, dp_percent, fires, flood }. Les
      postures : HMT_hostiles règle chaque camp hostile envers l'autre, DANS LES DEUX SENS, et relit. Le scénario de guerre
      avait une durée d'un jour : portée à 365 jours par ScenEdit_SetStartTime({Duration = '365:00:00:00'}) ( relu dans
      VP_GetScenario().Duration ) ; l'installateur doit le faire. L'OTAN est le camp « humain » du scénario, Russie-Chine
      l'ordinateur ; les deux lancent leurs missions de la même façon.""",
      f"{A}/lua/hmt_pont.lua ( HMT_DOCTRINE, HMT_doctrine, HMT_hostiles ) ; banc v8 du 02/10", ["doctrine", "SetDoctrine", "posture", "durée", "SetStartTime"]),
    f("atelier-etat-major", "atelier", "L'état-major automatique de l'atelier ( etat_major.py )",
      """À chaque tour et pour chaque camp : 1. SITUATION : la base aérienne adverse à frapper ( la plus menaçante encore
      opérationnelle ) et les PARAPLUIES sol-air adverses vivants et connus ( portée air DB ≥ seuil ) qui couvrent la cible
      ou le milieu de la route. 2. DÉCISION : parapluie intact → mission DEAD contre lui ( avions armés d'armes à distance
      de sécurité, d'antiradars ou d'armes furtives ; lanceurs sol-sol à portée ) ; ciel ouvert → frappe OCA de la base
      ( pistes, accès, dépôts ). ESCORTE : une paire par 4 frappeurs, au plus 8, prise sur les bases les mieux pourvues,
      une paire restant par base. 3. RÔLES : frappeurs au sol réarmés en DEAD ( dépôt rempli d'abord ) ; sans chargement
      DEAD, un frappeur passe en chasse pendant la DEAD et revient à la frappe ciel ouvert ( swing-role ) ; un camp sans
      avions SEAD dédiés réarme une paire en Kh-31P/Kh-58. 4. APPRENTISSAGE : chaque mission est notée à sa clôture
      ( dégâts infligés / ( avions perdus + 1 ) ) ; la part de DEAD suit l'efficacité comparée ( 0,2 à 0,8, départ 0,5 ).
      Premier résultat ( 02/10 ) : DEAD contre Baranovitchi, une défense détruite en 4 tours, 0 perte, part DEAD 0,50 → 0,64.""",
      f"{A}/etat_major.py ( en-tête, planifier ) ; mémoire guerre-reelle-cmo ( 02/10 23 h 40 )", ["état-major", "DEAD", "OCA", "escorte", "swing-role", "apprentissage"]),
    f("atelier-composante-air", "atelier", "La composante air complète : guet, ravitailleur, brouilleur, SEAD, barrière, reco",
      """Depuis le 03/10, l'état-major pose des missions de ZONE ( HMT_zone : 1 Patrol AAW, 2 Patrol SEAD, 3 Support ),
      nommées HMT-P<id> ( 500 + camp x 10 + rôle ), déplacées quand le front bouge de plus de 10 km. Placement : le GUET
      radar ( E-3A de l'OTAN à Geilenkirchen, Saab 340 AEW à Powidz, A-50U à Ivanovo ) au tiers de la route, reculé hors des
      parapluies connus de 60 km et à 150 km des bases adverses, radar actif ; le RAVITAILLEUR ( KC-135R Mildenhall, Il-78M
      Diaguilevo ) plus en arrière ( 15 % de la route, marges 100 et 250 km ) ; le BROUILLEUR ( EA-18G Spangdahlem,
      Il-22PP ) en stand-off juste hors des défenses de la cible, radar et OECM actifs ; la SEAD ( Tornado ECR AARGM
      Schleswig ) sur les défenses de la cible ; la BARRIÈRE de chasse à mi-route ; le BALAYAGE sur la cible ciel ouvert ;
      la RECO ( drones ) sur la cible ou en stand-off ; l'ELINT ( RC-135, Il-20M ) passif en stand-off. Bombardiers :
      B-52H JASSM-ER + MALD à Fairford, Tu-95MSM et Tu-160M Kh-101 à Engels, Tu-22M3M Kh-32 à Soltsy-2 ; jamais d'arme
      nucléaire ni inerte. Parts et marges : choix à valider par Younes.""",
      f"{A}/etat_major.py ( SOUTIEN, soutiens ) ; {A}/lua/hmt_pont.lua ( HMT_zone ) ; {A}/theatres/baltique_reel.py", ["composante air", "AEW", "ravitailleur", "brouilleur", "SEAD", "barrière", "drone"]),
    f("atelier-theatre-baltique", "atelier", "Le théâtre Baltique réel de la guerre CMO",
      """Guerre OTAN contre Russie-Chine sur de VRAIES installations ( theatres/baltique_reel.py ) : OTAN : bases polonaises
      ( Łask, Poznań, Malbork, Mińsk Mazowiecki, Świdwin, Powidz transport, Gdynia aéronavale ), Šiauliai ( Lituanie ) et
      Ämari ( Estonie ) pour la police du ciel balte, sites radar lituaniens, lettons, estoniens et finlandais, Tampere-
      Pirkkala et Utti ( Finlande ), Såtenäs et Ronneby ( Suède ), Skrydstrup et Bornholm ( Danemark ), Schleswig, Hohn,
      Wunstorf ( Allemagne ), soutiens américains Mildenhall, Spangdahlem, Fairford, Geilenkirchen ( E-3A ), Mirosławiec
      ( drones ). Russie-Chine : Baranovitchi et Babrouïsk ( Biélorussie ), défense sol-air et radars biélorusses ( 2013 ) et
      du district militaire Ouest russe ( 2013 ), bases russes de la Baltique construites ( Tchkalovsk, Donskoïé, Pskov… ),
      Ivanovo, Diaguilevo, Engels, Soltsy-2. Lancée le 02/10 à 21 h 05 : 228 avions, 2 056 éléments, 29 unités au sol.
      Choix à valider : dernière année disponible des modèles biélorusses et russes ( à moderniser : S-400 au lieu de
      S-300 ), positions des bases construites saisies de mémoire.""",
      f"{A}/theatres/baltique_reel.py ; {A}/GUERRE-REELLE.md ; mémoire guerre-reelle-cmo", ["théâtre", "Baltique", "OTAN", "Russie", "Biélorussie", "Kaliningrad"]),
    f("atelier-paliers", "atelier", "Les paliers de la guerre réelle dans CMO",
      """Feuille de route de la guerre réelle ( GUERRE-REELLE.md ) : palier 0 réparer ( magasins remplis et payés, rotation
      rapide, seuils de retour, sondes ) ; 1 vraies bases ( import ImportExport OTAN et Biélorussie, bases russes montées
      élément par élément, état d'une base = ses éléments vivants ) ; 2 toute l'aviation ( chasse, attaque, guet,
      ravitailleurs ; chargements par mission ; stocks par dépôt ) ; 3 frappes et SEAD/DEAD ( Strike, bombes, missiles de
      croisière et balistiques Iskander, Kalibr, Tomahawk ; stocks et cadence de production réels ) ; 4 défense sol-air
      et radars ( Patriot, SAMP/T, NASAMS, S-400, Buk, Pantsir sur leurs vrais sites ) ; 5 troupes au sol ; 6 marine
      ( flottes, ports, antinavires, sous-marins, ASM, mines ) ; 7 logistique ( carburant, convois, cargo, réparation des
      pistes ; l'économie du moteur nourrit la guerre ) ; 8 soutien ( guerre électronique, satellites, communications,
      cyber, météo, jour/nuit ) ; 9 plusieurs théâtres après un banc de charge. Principe : un palier n'avance qu'avec son
      verdict ( porte hors jeu avec mutants, puis 6 h dans le vrai CMO, critères écrits d'avance ) ; on ne modifie jamais
      une guerre en cours.""",
      f"{A}/GUERRE-REELLE.md", ["paliers", "guerre réelle", "feuille de route"]),
    f("atelier-unites-doctrine-py", "atelier", "Alerte : unités des portées dans cmo/doctrine.py ( nm lus comme km )",
      """La base DB3000 donne les portées en MILLES NAUTIQUES. cmo/doctrine.py commente « ATACMS 162 km, GMLRS 45 km,
      Iskander 270 km » et ses fonctions portee_sol_air / portee_sol_sol disent rendre des km, mais renvoient
      AirRangeMax et LandRangeMax BRUTS, donc en nm ( ATACMS 162 nm ≈ 300 km, Iskander 270 nm = 500 km ). L'état-major
      ( etat_major.py ) compare ces valeurs à PORTEE_MENACE_KM = 30 et à des distances calculées en km ( haversine ) :
      un parapluie sol-air y est donc compté avec une portée 1,85 fois TROP COURTE ( un S-400 à 135 nm, 250 km, y vaut
      135 « km » ), le seuil de menace vaut en fait 30 nm ( 56 km ), et un lanceur n'est affecté qu'aux cibles à moins de
      sa portée en nm prise pour des km ( prudent mais faux ). Constat de lecture du 03/10, pas encore corrigé : à signaler
      au chef de projet avant de s'appuyer sur ces portées. Les fiches de la base de connaissance donnent nm ET km.""",
      f"{A}/doctrine.py ( en-tête, portee_sol_air, portee_sol_sol ) ; {A}/etat_major.py ( km, couvrent ) ; DB3000 DataWeapon", ["unités", "nm", "km", "portée", "bug", "doctrine.py"]),
    f("atelier-regles-moteur", "atelier", "Les principes de la guerre réelle : CMO simule, le moteur décide",
      """1. CMO SIMULE, LE MOTEUR DÉCIDE : CMO calcule capteurs, tirs, dégâts, carburant, réparations ; le moteur ( l'agent
      et sa chaîne de commandement ) décide achats, stocks, missions et cibles, par des OUTILS du pont testés hors jeu,
      jamais par du Lua libre. 2. TOUT VIENT DU RÉEL : types, armes, capteurs de la DB3000 ; installations des 3 879 modèles
      de CMO ; budgets SIPRI ; quantités publiques ; prix en ordres de grandeur ( à valider par Younes ). 3. LA DESTRUCTION
      FAIT LA GUERRE : plus de drapeaux ni de score ; une base vaut ce que valent ses éléments ; sans piste pas de
      décollage, sans dépôt plein pas de réarmement ; la réparation prend le temps et le coût réels ; la guerre finit quand
      un camp ne peut plus combattre ou que sa volonté cède. 4. LE BROUILLARD : chaque chef ne voit que les contacts de son
      camp. 5. UN PALIER N'AVANCE QU'AVEC SON VERDICT. Chaîne de commandement visée : chef d'État par pays, commandant de
      théâtre, chefs air, mer, sol, défense sol-air ; le conseil de Qwen tient les décisions politiques ; stratégie à Qwen,
      tactique à CMO.""",
      f"{A}/GUERRE-REELLE.md ; mémoire que-du-reel-pas-de-drapeaux et qwen-chef-etat-major-cmo", ["principes", "guerre réelle", "moteur", "Qwen", "brouillard"]),

    # ------------------------------------------------------------------ LUA
    f("lua-familles", "lua", "Les fonctions Lua de CMO 1.10 ( 181 ) par famille",
      """Liste relevée dans CMO 1.10 ( cmo_carte/lua_fonctions_110.txt ). UNITÉS : ScenEdit_AddUnit ( et AddAircraft,
      AddShip, AddSubmarine, AddFacility ), GetUnit, SetUnit, UpdateUnit, DeleteUnit, KillUnit, SetUnitDamage, SetUnitSide,
      SplitUnit, MergeUnits, HostUnitToParent, TransferMount, SetLoadout, GetLoadout, SetLoadoutAvailable, RefuelUnit.
      MAGASINS : AddWeaponToUnitMagazine, FillMagsForLoadout, AddReloadsToUnit, DistributeWeaponAtAirbase,
      ClearAllMagazines. MISSIONS : AddMission, GetMission(s), SetMission, DeleteMission, AssignUnitToMission,
      AssignUnitAsTarget, RemoveUnitAsTarget, CreateMissionFlightPlan, Export/ImportMission. COMBAT : AttackContact,
      AttackContact_Extra, WeaponAllocation, AddExplosion. CONTACTS : GetContact, GetContacts, VP_GetContact. DOCTRINE :
      SetDoctrine, GetDoctrine, SetDoctrineWRA, GetDoctrineWRA, Import/ExportDoctrineToXML, SetEMCON, SetSideEmconAlertness,
      Set/GetUnitIntermittentEmissionConfig. CAMPS : AddSide, RemoveSide, SetSidePosture, GetSidePosture, SetSideOptions,
      GetScore/SetScore, VP_GetSide(s). CARTE : Add/Set/Get/DeleteReferencePoint, AddZone, SetZone, IsUnitInZone,
      AddMinefield, SetMine. ÉVÉNEMENTS : SetEvent, SetTrigger, SetCondition, SetAction, SetEventTrigger…, AddSpecialAction.
      SCÉNARIO : SetStartTime, SetTime, SetWeather, GetWeather, ImportInst, ExportInst, RunScript ( absente de la liste
      mais employée ), Command_SaveScen. OUTILS : Tool_Range, Tool_Bearing, Tool_LOS, World_GetElevation, QueryDB.""",
      "/mnt/data/hmt/etat/cmo_carte/lua_fonctions_110.txt ; manuel § 5.3 et § 7.8 Lua Reference p. 110-116, 261-266", ["Lua", "fonctions", "API", "ScenEdit"]),
    f("lua-addunit", "lua", "ScenEdit_AddUnit : poser une unité ( vérifié dans le vrai CMO )",
      """ScenEdit_AddUnit({ side = 'OTAN', type = 'Air'|'Ship'|'Submarine'|'Facility'|'Vehicle', unitname = 'HMT-12',
      dbid = 3500, latitude = 54.1, longitude = 18.2, altitude = 9000, loadoutid = 16934 }) rend l'unité ( u.guid ) ou nil.
      Pour un avion POSÉ sur une base : base = guid du GROUPE de la base ( pas d'une piste : refus ), sans latitude ; il
      décolle quand une mission l'emploie et revient s'y ravitailler. Un avion posé en vol sans base tombe à sec. Les
      formations au sol ( SAM, artillerie ) sont des 'Facility' mobiles, un véhicule seul un 'Vehicle'. Exemples vérifiés :
      F-15C dbid 3500 chargement 16934 ; T-72B3 dbid 102 ; S-400 1937 ; Iskander 254. Le dbid est l'ID de la table DataX
      de la base DB3000 ( les fiches de plates-formes donnent « [avion DB n] » ). Suppression : ScenEdit_DeleteUnit
      ( effective au passage suivant ). Une unité supprimée laisse son guid « brûlé » : CMO ne la recrée pas sous ce guid.""",
      f"{A}/lua/hmt_pont.lua ( HMT_poser, HMT_poser_base_lot ) ; {A}/LISEZMOI.md ; sondes du 02/10", ["Lua", "AddUnit", "dbid", "loadoutid", "base"]),
    f("lua-missions", "lua", "Missions en Lua : AddMission, SetMission, AssignUnitToMission, Phase",
      """Créer : ScenEdit_AddMission(camp, nom, 'Patrol', { type = 'AAW', zone = { 'RP-1', 'RP-2', 'RP-3', 'RP-4' } }) ;
      vérifiés dans notre pont : 'Patrol' type 'AAW' et 'SEAD', 'Support' avec zone, 'Strike' type 'Land' ( les libellés
      des autres types, ASW, ASuW, frappe navale, ne sont pas encore vérifiés en vrai ). Les points de référence viennent de ScenEdit_AddReferencePoint({side, name, latitude, longitude})
      et se déplacent par SetReferencePoint ( la mission suit ). Régler : ScenEdit_SetMission(camp, nom, { OneThirdRule =
      true, OnStation = 2, ActiveEMCON = true, StrikeFlightSize = 2, StrikeUseFlightSize = false, isactive = false }).
      Activer une mission en attente : m = ScenEdit_GetMission(camp, nom) ; m.Phase = 20. Affecter :
      ScenEdit_AssignUnitToMission(guid, nom [, escorte]) ; cible d'une frappe : ScenEdit_AssignUnitAsTarget(guid, nom)
      ( par guid seulement ). EMCON de mission : ScenEdit_SetEMCON('Mission', nom, 'Radar=Active;OECM=Active'). Fermer :
      ScenEdit_DeleteMission(camp, nom) ( marche en 1.10 ). Une patrouille ne part que par paires ; une frappe neuve naît
      OnHold et attend des vols de quatre.""",
      f"{A}/lua/hmt_pont.lua ( HMT_patrouille, HMT_zone, HMT_frappe, HMT_affecter, HMT_escorter, HMT_clore )", ["Lua", "AddMission", "SetMission", "AssignUnitToMission", "Phase", "mission"]),
    f("lua-lecture-etat", "lua", "Lire l'état en Lua : unités, magasins, contacts, camp, scénario",
      """Unité : u = ScenEdit_GetUnit({guid=...}) ; champs vus : name ( écrire u.name renomme ), latitude, longitude,
      altitude, condition ( Parked, Airborne… ), readytime, airbornetime, loadoutdbid, fuel, damage { dp, dp_percent ( texte
      à virgule ), fires, flood, startdp }, magazines[i].mag_weapons[j] { wpn_dbid, wpn_current, wpn_maxcap, wpn_name },
      mounts[i].mount_weapons, ascontact { guid, name, side }. Méthode u:Launch(true) : force un décollage. Camp :
      s = VP_GetSide({side=...}) : guid, losses, expenditures, méthodes unitsInArea, unitsBy, contactsBy ; side.units contient
      des FANTÔMES ( rafales de canon tirées ) que GetUnit ne rend pas : les sauter. Contacts : ScenEdit_GetContacts(camp),
      ScenEdit_GetContact({side, guid}) : classificationlevel, age, latitude, longitude, areaofuncertainty, actualunitid,
      type_description. Doctrine : ScenEdit_GetDoctrine({side}). Scénario : VP_GetScenario() ( Duration… ). Posture :
      ScenEdit_GetSidePosture(a, b) == 'H'.""",
      f"{A}/lua/hmt_pont.lua ( HMT_stocks, HMT_vus, HMT_bilan, HMT_etats, HMT_adopter ) ; sondes du 02-03/10", ["Lua", "GetUnit", "VP_GetSide", "GetContacts", "lecture"]),
    f("lua-attaque-directe", "lua", "Attaquer directement en Lua : AttackContact, WeaponAllocation",
      """En dehors des missions, une unité peut recevoir un ordre d'attaque sur un CONTACT : ScenEdit_AttackContact(
      attaquant, contact, { mode = 0 } ) ( 0 = automatique : l'IA choisit les armes ; mode manuel avec arme et quantité ) ;
      AttackContact_Extra et ScenEdit_WeaponAllocation existent aussi. Une attaque ne part que sur un contact DÉTECTÉ par le
      camp : une cible jamais repérée n'est jamais frappée. Le moteur de l'atelier préfère les MISSIONS ( Strike avec cibles
      affectées par guid ), plus robustes : CMO gère vols, escortes, ravitaillement, retour et réarmement. Les paramètres
      exacts de AttackContact ne sont pas encore vérifiés dans notre pont ( carte des mécanismes : « supposition
      mode=0 » ). Pour savoir pourquoi une arme ne part pas : l'allocation manuelle donne la raison ( fiche
      meca-pourquoi-pas-de-tir ).""",
      f"carte des mécanismes cmo_carte/carte_editeur_outils.json ( ordres d'attaque ) ; manuel § 4.1.1 p. 75-77 ; § 5.2.2", ["Lua", "AttackContact", "attaque", "contact", "WeaponAllocation"]),

    # ------------------------------------------------------------------ RÈGLES D'ÉTAT-MAJOR
    f("regle-phases-campagne-aerienne", "regle", "Règle : les phases d'une campagne aérienne",
      """1. SUPÉRIORITÉ AÉRIENNE : tant que l'adversaire a des défenses sol-air à longue portée intactes, aucune frappe
      ordinaire ne passe ( 02/10 : dix JSOW sur quatorze abattus par un S-300 ). On les SUPPRIME ( SEAD : antiradars qui
      font taire ou détruisent les radars ) puis on les DÉTRUIT ( DEAD : croisière furtive hors de portée, balistiques,
      avions furtifs ). En même temps : balayages de chasse et frappes contre ses bases aériennes ( OCA : pistes, points
      d'accès, abris, dépôts ). 2. INTERDICTION : ciel acquis, frapper postes de commandement, logistique, lanceurs ( chasse
      aux Iskander ), dépôts. 3. APPUI AU SOL : appui rapproché et interdiction du champ de bataille quand la guerre
      terrestre s'engage. EN PERMANENCE : défense aérienne de ses bases et de ses moyens rares ( avions de guet,
      ravitailleurs ). Cadence : effort maximal ( surge ) les trois premiers jours, puis effort durable, une sortie par jour
      et par pilote ( 1991, 1999, 2022 ). Missions CMO : Patrol AAW ( défense, barrière, balayage ), Patrol SEAD, Strike
      Land ( OCA, DEAD, interdiction ), Support ( guet, ravitailleur, brouilleur ).""",
      f"{A}/doctrine.py ( en-tête ) ; campagnes 1991, 2003, 2022", ["campagne aérienne", "supériorité aérienne", "SEAD", "DEAD", "OCA", "interdiction"]),
    f("regle-parapluie-sol-air", "regle", "Règle : ne jamais frapper sous un parapluie sol-air intact",
      """Défense COURTE portée ( moins de 30 km : Pantsir, Tor, MANPADS ) : on vole au-dessus de son plafond ( vérifier
      l'altitude maximale de cible de ses missiles dans la fiche arme ). Défense de MOYENNE ou LONGUE portée ( Buk, Patriot,
      SAMP/T, S-300, S-400 ) : c'est un PARAPLUIE. Sous un parapluie intact, on ne frappe jamais avec des armes de courte
      portée : soit on le détruit d'abord ( DEAD ), soit on tire de plus loin que sa portée ( arme à distance de sécurité :
      JASSM, Storm Shadow/SCALP, Taurus, Kh-59, Kh-101, Kalibr, Tomahawk ), soit on pénètre en avion furtif ( F-35, B-2 ).
      Un avion sans arme à distance de sécurité ne va pas sous le parapluie : pendant la DEAD il repasse en chasse ( escorte,
      défense des bases ) et revient à la frappe quand le ciel est ouvert ( swing-role ). Comparer TOUJOURS en mêmes unités :
      portée sol-air de la fiche ( nm ) contre distance de tir de l'arme ( nm ) ; un bataillon S-400 ( 48N6DM ) porte à
      135 nm ( 250 km ), un 40N6 plus loin. Attaquer de plusieurs directions sature les canaux d'illumination.""",
      f"{A}/doctrine.py ; manuel § 9.3.3 p. 331 ; DB3000 DataFacility 543 / DataWeapon", ["parapluie", "SAM", "DEAD", "stand-off", "furtif", "règle"]),
    f("regle-paquet-de-frappe", "regle", "Règle : un paquet de frappe, pas un vol isolé",
      """Une frappe part en PAQUET : frappeurs + escorte de chasse + tireurs antiradar ( SEAD ) + brouilleur, coordonnés par
      une même heure sur objectif ( l'ATO de CMO retient les tirs pour que tous arrivent ensemble ). Une paire d'escorte pour
      quatre frappeurs, une paire reste toujours défendre chaque base. Le brouilleur se place derrière les frappeurs, au
      plus près de la cible en restant à l'abri. Les leurres ( MALD, ADM-160 ) saturent les défenses. Un envahisseur qui
      arrive au compte-gouttes dans une patrouille adverse est détruit avion par avion ( guerre du 29/09 : 32 sur 32 perdus,
      un avion toutes les ~6 min ) : il faut une doctrine de masse ( attendre N avions, nombre minimal d'avions prêts dans
      la mission Strike ). Après la frappe : ÉVALUER LES DÉGÂTS RÉELS ( BDA par les contacts et HMT_etats ) et REFRAPPER ce
      qui vit encore ; une piste se répare vite.""",
      f"{A}/doctrine.py ; {A}/etat_major.py ; manuel § 7.1.1 ( heure sur objectif ) p. 201 ; mémoire pont-cmo-voie2 ( constats du 29/09 )", ["paquet", "frappe", "escorte", "brouilleur", "masse", "BDA"]),
    f("regle-arme-cible", "regle", "Règle : la bonne arme sur la bonne cible",
      """Appariement arme-cible : PERFORANTE ( ogive pénétrante, BLU-109, GBU-31(V)3, Taurus MEPHISTO ) sur abri durci,
      bunker et dépôt enterré ; ANTI-PISTE ( Durandal, BetAB, sous-munitions anti-piste ) sur piste et taxiways ; ANTIRADAR
      ( HARM, AARGM, ALARM, Kh-31P, Kh-58 ) sur radar qui émet ; CROISIÈRE ou BALISTIQUE ( JASSM, Storm Shadow, Tomahawk,
      Kalibr, Iskander, ATACMS ) sur cible très défendue ; bombes guidées laser ou GPS ( Paveway, JDAM, SDB ) ciel ouvert ;
      ANTINAVIRE ( Harpoon, NSM, Exocet, RBS-15, Onyx, Kalibr antinavire, Zircon ) sur navire, en salve dimensionnée par la
      valeur de défense antimissile de la cible ; TORPILLE ou grenade sur sous-marin ; MISSILE AIR-AIR selon la cible ( deux
      AMRAAM contre un chasseur moderne, un contre un avion de soutien ). Vérifier dans la fiche arme : « Cibles possibles »,
      portée dans le bon domaine ( air, surface, sol, sous-marin ), points de dégâts de l'ogive face aux points et au
      blindage de la cible. Les lanceurs ne sont affectés qu'aux cibles à leur portée. Jamais d'arme nucléaire ni de
      munition inerte dans les chargements choisis.""",
      f"{A}/doctrine.py ; {A}/catalogue.py ; manuel § 3.3.15 et § 9.3.1 ; DB3000 DataWeaponTargets, DataWarhead", ["arme", "cible", "appariement", "perforante", "anti-piste", "antiradar", "antinavire"]),
    f("regle-cible-menacante", "regle", "Règle : frapper d'abord ce qui menace le plus, évaluer, apprendre",
      """On frappe d'abord ce qui MENACE le plus : la base qui aligne le plus d'avions le plus près des siennes
      ( Kaliningrad, bulle au milieu de l'OTAN, avant Baranovitchi ). On ÉVALUE les dégâts réels ( CMO ) et on refrappe ce
      qui vit encore. On APPREND : une mission qui coûte plus qu'elle ne détruit perd ses moyens au profit de celles qui
      rapportent ( note = dégâts / ( pertes + 1 ) ). Brouillard : une défense mobile n'est une menace connue que vue et
      classée « type connu » au moins ; les garnisons du temps de paix sont connues d'avance. Le chef d'état-major propose
      deux ou trois MODES D'ACTION, les compare ( forces, risques, délais, stocks de munitions ) et dit lequel il retient et
      pourquoi ; il note ce qu'il attend ( prévu ) pour le comparer à ce qui arrive ( obtenu ). Il respecte les délais réels :
      préparation des chargements ( 3 à 6 h ), ordres de mission préparés à l'avance, renseignement en retard.""",
      f"{A}/doctrine.py ; {A}/etat_major.py ; mémoire qwen-chef-etat-major-cmo", ["priorité", "menace", "BDA", "apprentissage", "mode d'action"]),
    f("regle-guerre-navale", "regle", "Règle : principes de la guerre navale dans CMO",
      """Voir sans être vu : capteurs passifs ( ESM, sonar passif ) d'abord, EMCON passif, radar allumé seulement quand
      il faut un tir. Frapper le premier : la portée de ses antinavires ( fiche arme, domaine « navires ») contre celle de
      l'adversaire ; tirer en SALVE coordonnée ( plusieurs porteurs, même heure sur cible, missiles rasants ou
      hypersoniques ) pour saturer la défense ( valeur de défense antimissile de la cible ) ; garder la distance
      ( doctrine « maintain standoff »). Un groupe de surface se protège en couches : patrouille aérienne, destroyers
      antiaériens ( Aegis, Aster ), défense de point ( CIWS, RAM ), leurres et brouillage. Contre les sous-marins : avions de
      patrouille maritime, hélicoptères à sonar trempé, frégates à sonar remorqué, sous-marins chasseurs ; la vitesse gêne
      les sous-marins diesels. Mines : couloir dragué avant tout passage obligé. Logistique : pétroliers-ravitailleurs,
      retour au port pour réparer et recompléter ( doctrine retrait/redéploiement ). En Baltique : eaux peu profondes
      ( pas de zones de convergence ), mines, missiles côtiers ( Bastion-P, NSM côtier ), forte menace aérienne.""",
      "manuel § 9.2.2-9.2.4, § 3.3.13 ASuW, § 3.3.16 ; synthèse de commandement", ["guerre navale", "salve", "EMCON", "antinavire", "ASM", "Baltique"]),
]
