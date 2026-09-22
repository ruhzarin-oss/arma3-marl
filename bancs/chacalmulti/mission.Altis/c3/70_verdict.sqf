// =====================================================================
// CHACAL - LES CANARIS DE L ENREGISTREUR, puis le VERDICT.
//
// Regle 16 : un instrument qu on n a pas vu detecter n a rien mesure. Ici
// l instrument est l enregistreur, et il doit savoir detecter TROIS choses :
// une MORT, un TIR, et une VUE. On lui donne donc les trois, hors du theatre.
//
// ! Le controle a echoue quatre fois de suite pour quatre causes differentes,
// toutes rendant le meme zero : cuvette de terrain, couple mal cherche,
// puis fratricide - le canari abattait son propre temoin. C est exactement
// pourquoi un zero doit etre DECOMPOSE avant d etre cru.
// =====================================================================

[] spawn {
    waitUntil { sleep 1; !isNil "MULTI_DEPART" };   // MULTI : l horloge part au depart commun
    sleep 20;
    // Le COUPLE se cherche ensemble, avec le MEME critere que la mesure qu il
    // certifie. Poser le canari sur un replat puis le temoin a 40 m donnait
    // trente-six azimuts bloques : l obstacle etait le SOL, `typeOf` vide sur
    // l objet et son parent, et `terrainIntersectASL` - qui echantillonne la
    // grille - ne le voyait pas.
    // ! L INSTRUMENT NE DOIT PAS DEPENDRE DU TRAITEMENT ( Fable, 05/09 ).
    // Le generateur est consomme en SEQUENCE, et 30_opfor en consomme un nombre
    // qui depend du palier - 14 tirages au 0, 27 au 1, 44 au 2. Tout ce qui est
    // tire ensuite tombe donc ailleurs a chaque palier, et au MEME endroit a
    // palier egal : les deux refus de `temoin_vu_par_VG` au palier 0 n etaient
    // pas deux malchances, c etait le meme tirage deux fois. On isole donc la
    // recherche du couple sur un etat derive de la GRAINE SEULE, puis on rend
    // le generateur intact a la mission.
    private _rngSauve = MC3_RNG;
    MC3_RNG = ((MC3_GRAINE * 2749) + 40507) % 65537;
    if (MC3_RNG == 0) then { MC3_RNG = 1 };
    for "_i" from 1 to 12 do { call MC3_fnc_rnd };
    private _p = []; private _pt = []; private _essaisT = 0; private _trouveT = false;
    for "_k" from 1 to 14 do {
        private _c0 = [MC3_SITE getPos [2400 + (1200 call MC3_fnc_al), 360 call MC3_fnc_al], 150] call MC3_fnc_plat;
        if (surfaceIsWater _c0 || { !([_c0, 3] call MULTI_fnc_loin) }) then { continue };
        private _ha = [(_c0 select 0), (_c0 select 1), (getTerrainHeightASL _c0) + 1.5];
        for "_j" from 1 to 18 do {
            _essaisT = _essaisT + 1;
            private _c1 = _c0 getPos [30 + (30 call MC3_fnc_al), _j * 20];
            _c1 set [2, 0];
            if (!surfaceIsWater _c1) then {
                private _hb = [(_c1 select 0), (_c1 select 1), (getTerrainHeightASL _c1) + 1.5];
                if ((count (lineIntersectsSurfaces [_ha, _hb, objNull, objNull, true, 1, "VIEW", "VIEW"])) == 0) exitWith {
                    _p = _c0; _pt = _c1; _trouveT = true;
                };
            };
        };
        if (_trouveT) exitWith {};
    };
    if (!_trouveT) then {
        (format ["CHACAL|AVERT|temoin_sans_vue|%1|aucun_couple_franc_en_%2_essais", round (time * 100) / 100, _essaisT]) call MC3_LOG;
        _p = [MC3_SITE getPos [3000, 360 call MC3_fnc_al], 150] call MC3_fnc_plat;
        { private _c9 = [MC3_SITE getPos [3000, _x], 150] call MC3_fnc_plat; if (!surfaceIsWater _c9 && { [_c9, 3] call MULTI_fnc_loin }) exitWith { _p = _c9 } } forEach [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
        _pt = _p getPos [40, 0];
    };
    (format ["CHACAL|CANARI|couple|%1|essais|%2|franc|%3|distance|%4", round (time * 100) / 100,
        _essaisT, (if (_trouveT) then {1} else {0}), round (_pt distance2D _p)]) call MC3_LOG;
    MC3_RNG = _rngSauve;   // le generateur de la mission est rendu intact

    private _g = ([east, 3] call MULTI_fnc_groupe);
    MC3_CANARI = _g createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    MC3_CANARI setVariable ["chacal_role", "CANARI", true];
    MC3_CANARI call MC3_fnc_identifier;   // l instrument ne doit pas subir son propre defaut
    _g setBehaviour "CARELESS"; _g allowFleeing 0;
    doStop MC3_CANARI;
    sleep 4;
    private _id = MC3_CANARI getVariable ["chacal_id", -1];
    (format ["CHACAL|CANARI|pose|%1|id|%2|pos|%3", round (time * 100) / 100, _id, _p]) call MC3_LOG;

    // --- CANAL TIR : trois coups, a un instant ecrit ---
    // Ce bloc annoncait trois coups et n en tirait AUCUN : `currentMuzzle` rend
    // "" tant que l arme n est pas levee, et `forceWeaponFire ["", ...]` echoue
    // en silence. On leve l arme et on journalise les noms reels.
    MC3_CANARI setBehaviour "AWARE";
    private _arme = primaryWeapon MC3_CANARI;
    MC3_CANARI selectWeapon _arme;
    sleep 2;
    (format ["CHACAL|CANARI|arme|%1|muzzle|%2|mode|%3", _arme,
        currentMuzzle MC3_CANARI, currentWeaponMode MC3_CANARI]) call MC3_LOG;
    (format ["CHACAL|CANARI|tire|%1|id|%2|coups|3", round (time * 100) / 100, _id]) call MC3_LOG;
    for "_i" from 1 to 3 do {
        if (alive MC3_CANARI) then {
            private _m = currentMuzzle MC3_CANARI;
            if (_m == "") then { _m = _arme };
            MC3_CANARI forceWeaponFire [_m, currentWeaponMode MC3_CANARI];
        };
        sleep 1;
    };

    // --- CANAL VUE : un temoin bleu, en vue franche ---
    // VC, VH et VG pouvaient rendre du vide toute une nuit sans qu une porte
    // s allume - or c est VG qui doit prouver que le maitre n a pas triche.
    private _gt = ([west, 3] call MULTI_fnc_groupe);
    MC3_TEMOIN = _gt createUnit ["B_Soldier_F", _pt, [], 0, "NONE"];
    MC3_TEMOIN setVariable ["chacal_role", "TEMOIN_VUE", true];
    MC3_TEMOIN call MC3_fnc_identifier;
    MC3_TEMOIN setDir (MC3_TEMOIN getDir MC3_CANARI);
    // ! LE CRITERE DE RECHERCHE N ETAIT PAS LE CRITERE DE MESURE.
    // Mesure du 05/09 : deux episodes sur six refuses sur `temoin_vu_par_VG`,
    // avec un couple pourtant valide `franc|1`. La recherche teste des points a
    // `getTerrainHeightASL + 1,5` ; la mesure teste des UNITES a
    // `getPosASL + 1,5`. Un homme se tient sur la surface rendue, pas sur la
    // grille de terrain, et a certains endroits l ecart suffit a bloquer la vue.
    // On valide donc avec l unite REELLEMENT POSEE, en la deplacant jusqu a ce
    // que la mesure elle-meme dise oui - ou en declarant l echec.
    private _okVue = false; private _essaisV = 0;
    for "_j" from 1 to 24 do {
        _essaisV = _j;
        if ([MC3_TEMOIN, MC3_CANARI] call MC3_fnc_voit) exitWith { _okVue = true };
        private _cand = _p getPos [28 + (34 call MC3_fnc_al), _j * 15];
        _cand set [2, 0];
        if (!surfaceIsWater _cand) then {
            MC3_TEMOIN setPosATL _cand;
            MC3_TEMOIN setDir (MC3_TEMOIN getDir MC3_CANARI);
            sleep 0.5;
        };
    };
    (format ["CHACAL|CANARI|placement_temoin|%1|essais|%2|vue|%3|distance|%4", round (time * 100) / 100,
        _essaisV, (if (_okVue) then {1} else {0}), round (MC3_TEMOIN distance MC3_CANARI)]) call MC3_LOG;
    if (!_okVue) then {
        (format ["CHACAL|AVERT|temoin_sans_vue|%1|aucune_position_mesuree_franche_en_%2_essais", round (time * 100) / 100, _essaisV]) call MC3_LOG;
    };
    _gt setBehaviour "CARELESS"; _gt setCombatMode "BLUE"; _gt allowFleeing 0;
    doStop MC3_TEMOIN;
    // ! LE CONTROLE TUAIT SON PROPRE TEMOIN. Le canari est un soldat arme en
    // AWARE ; on lui `reveal` un ennemi a 34 m, il l abat, et `MC3_fnc_voit`
    // sortait alors sur sa toute premiere garde - `!alive _u`.
    MC3_TEMOIN allowDamage false;
    MC3_CANARI setCombatMode "BLUE";
    MC3_CANARI disableAI "AUTOTARGET";
    MC3_CANARI disableAI "TARGET";
    // On ne coupe JAMAIS "PATH" : mesure du 11/08, ca retire les jambes.
    MC3_CANARI reveal [MC3_TEMOIN, 4];
    MC3_TEMOIN reveal [MC3_CANARI, 4];
    MC3_TEMOIN doWatch MC3_CANARI;
    sleep 5;
    private _rel = abs ((((MC3_TEMOIN getDir MC3_CANARI) - (getDir MC3_TEMOIN) + 540) % 360) - 180);
    private _a = (getPosASL MC3_TEMOIN) vectorAdd [0,0,1.5];
    private _b = (getPosASL MC3_CANARI) vectorAdd [0,0,1.2];
    private _los = (count (lineIntersectsSurfaces [_a, _b, MC3_TEMOIN, MC3_CANARI, true, 1, "VIEW", "VIEW"])) == 0;
    (format ["CHACAL|CANARI|temoin|%1|id|%2|distance|%3|vue|%4|ecart_regard|%5|ligne_de_vue|%6|posture|%7|vivant|%8",
        round (time * 100) / 100, (MC3_TEMOIN getVariable ["chacal_id", -1]),
        round (MC3_TEMOIN distance MC3_CANARI),
        (if ([MC3_TEMOIN, MC3_CANARI] call MC3_fnc_voit) then {1} else {0}),
        round _rel, (if (_los) then {1} else {0}), stance MC3_TEMOIN,
        (if (alive MC3_TEMOIN) then {1} else {0})]) call MC3_LOG;

    // --- CANAL MORT ---
    sleep 45;
    (format ["CHACAL|CANARI|tue|%1|id|%2", round (time * 100) / 100, _id]) call MC3_LOG;
    MC3_CANARI setDamage 1;
};

// =====================================================================
// LE VERDICT. Quatre issues et JAMAIS deux : SUCCES, ECHEC, ABANDON, VOID.
//
// VOID n est pas un echec attenue : c est l aveu que la mesure n a pas eu lieu.
// ABANDON n est pas un echec non plus : un detachement compromis a 3 km qui
// renonce a charger dix contre trente-deux a pris la bonne decision.
// Un episode VOID ne doit jamais entrer dans un taux de reussite.
//
// Le critere de SUCCES porte sur les CHARGES POSEES - des actes - et non sur
// la destruction, qui est un effet scripte declare hors jugement tactique.
// =====================================================================
[] spawn {
    waitUntil { sleep 2; MC3_FIN };
    sleep 3;

    private _actes = count MC3_CHARGES;
    private _objTotal = count MC3_OBJETS;
    private _vivants = count (MC3_FS select { alive _x });
    private _exf = if (isNil "MC3_EXFILTRES") then {0} else {MC3_EXFILTRES};
    private _pertesEst = (count MC3_EST_SITE) - (count (MC3_EST_SITE select { alive _x }));
    private _lat = if (MC3_T_ALARME < 0 || MC3_T_COMPROMIS < 0) then {-999}
                   else { round ((MC3_T_COMPROMIS - MC3_T_ALARME) * 100) / 100 };

    if (MC3_ISSUE != "VOID" && !MC3_LAMBS) then { MC3_ISSUE = "VOID"; MC3_CAUSE = "LAMBS_ABSENT" };
    if (MC3_ISSUE != "VOID") then {
        if (MC3_ABANDON && _actes == 0) then {
            MC3_ISSUE = "ABANDON";
            // La cause a ete ecrite a l instant de la decision. On la LIT, on ne
            // la devine pas : le premier jet la reconstruisait d un compteur a
            // zero et sortait OBSERVATION_VIDE pour un episode ou la phase 3
            // n avait jamais eu lieu.
            MC3_CAUSE = if (!isNil "MC3_CAUSE_ABANDON" && { MC3_CAUSE_ABANDON != "" })
                           then {MC3_CAUSE_ABANDON} else {"ABANDON_SANS_CAUSE"};
        } else {
            if (_actes >= _objTotal && _exf >= (round (0.6 * MC3_EFFECTIF))) then { MC3_ISSUE = "SUCCES"; MC3_CAUSE = "CHARGES_ET_EXFIL" }
            else {
                MC3_ISSUE = "ECHEC";
                // ! L ETIQUETTE MENTAIT ( 13/09 ). EXFIL_MANQUEE couvrait deux choses differentes :
                // un detachement qui n a pas rejoint le point de ramassage, et un detachement qui n a
                // plus assez d hommes pour le franchir. Le second n a pas rate son decrochage, il a
                // perdu ses hommes. On separe, sinon le goulot se lit a l envers.
                MC3_CAUSE = if (_vivants == 0) then {"DETACHEMENT_DETRUIT"}
                    else { if (_actes < _objTotal) then {"CHARGES_INCOMPLETES"} else {
                    if (_vivants < (round (0.6 * MC3_EFFECTIF))) then {"PERTES_EXCESSIVES"} else {"EXFIL_MANQUEE"} } };
            };
        };
    };

    (format ["CHACAL|FINI|%1|%2|graine|%3|echelle|%4|dt|%5|bras|%6|palier|%24|phase_max|%7|charges|%8|sur|%9|detruits_scriptes|%10|intel|%11|exfiltres|%12|vivants|%13|pertes_est|%14|renseignement|%15|alarme|%16|compromis|%17|latence_surprise|%18|abandon|%19|insertion_forcee|%20|lambs|%21|ticks|%22|duree|%23|tenir|%25|arret|%26|depart|%27|effectif|%28|appui_feu|%29|accessible|%30|feu_avant|%31|mg_assaut|%32|delai_porteur|%33|appui_fixe|%34|oracle|%35|socle|%36|tactique|%37|relances|%38|fumigenes|%39|zones|%40|ablation|%41|banc_appui|%42|tirs_banc|%43|placeur|%44|couverture|%45|exfil|%46|azimut|%47|azimut_joue|%48|sans_jambes|%49|obs|%50",
        MC3_ISSUE, MC3_CAUSE, MC3_GRAINE, MC3_ECHELLE, MC3_DT, MC3_BRAS, MC3_PHASE,
        _actes, _objTotal, count MC3_DETRUITS, (if (MC3_INTEL) then {1} else {0}),
        _exf, _vivants, _pertesEst, count MC3_VUES,
        (if (MC3_ALARME) then {1} else {0}), (if (MC3_COMPROMIS) then {1} else {0}), _lat,
        (if (MC3_ABANDON) then {1} else {0}), (if (MC3_INSERTION_FORCEE) then {1} else {0}),
        (if (MC3_LAMBS) then {1} else {0}), MC3_TICK, round time, MC3_PALIER, MC3_TENIR, MC3_ARRET, MC3_DEPART, MC3_EFFECTIF, MC3_APPUI_FEU, MC3_ACCESSIBLE, MC3_FEU_AVANT, MC3_MG_ASSAUT, MC3_DELAI_PORTEUR, MC3_APPUI_FIXE, MC3_ORACLE, MC3_SOCLE, MC3_TACTIQUE, MC3_RELANCES_SOCLE, MC3_FUMIGENES, MC3_ZONES, MC3_ABLATION, MC3_BANC_APPUI, MC3_TIRS_BANC, MC3_PLACEUR, MC3_COUV, MC3_EXFIL, MC3_AZIMUT, MC3_AZIMUT_CHOISI, MC3_SANS_JAMBES, MC3_OBS]) call MC3_LOG;
    MC3_MUET = true;   // MULTI : la cellule se tait, comme un serveur arrete

    // L ECHELLE raccourcit les plafonds mais PAS le monde : ni la vitesse de
    // marche, ni la periode des rondes, ni les 6 km de route. Une nuit a 25 %
    // est une AUTRE mission.
    if (MC3_ECHELLE != 1) then {
        (format ["CHACAL|AVERT|hors_corpus|echelle|%1", MC3_ECHELLE]) call MC3_LOG;
    };

    call MC3_fnc_arreterCapture;

    // On N ARRETE PAS la mission : avec persistent=1 un endMission la
    // RELANCERAIT avec les MEMES parametres, donc la meme graine, et deux
    // episodes identiques entreraient dans le corpus sous deux noms.
    "CHACAL|OK|serveur_au_repos|le_harnais_peut_relancer" call MC3_LOG;
};
