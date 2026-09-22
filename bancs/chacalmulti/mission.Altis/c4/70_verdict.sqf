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
    waitUntil { sleep 1; !isNil "MULTI_DEPART" };   // MULTI : les emprises de toutes les cellules sont connues
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
    private _rngSauve = MC4_RNG;
    MC4_RNG = ((MC4_GRAINE * 2749) + 40507) % 65537;
    if (MC4_RNG == 0) then { MC4_RNG = 1 };
    for "_i" from 1 to 12 do { call MC4_fnc_rnd };
    private _p = []; private _pt = []; private _essaisT = 0; private _trouveT = false;
    for "_k" from 1 to 14 do {
        private _c0 = [MC4_SITE getPos [2400 + (1200 call MC4_fnc_al), 360 call MC4_fnc_al], 150] call MC4_fnc_plat;
        if (surfaceIsWater _c0 || { !([_c0, 4] call MULTI_fnc_loin) }) then { continue };
        private _ha = [(_c0 select 0), (_c0 select 1), (getTerrainHeightASL _c0) + 1.5];
        for "_j" from 1 to 18 do {
            _essaisT = _essaisT + 1;
            private _c1 = _c0 getPos [30 + (30 call MC4_fnc_al), _j * 20];
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
        (format ["CHACAL|AVERT|temoin_sans_vue|%1|aucun_couple_franc_en_%2_essais", round (time * 100) / 100, _essaisT]) call MC4_LOG;
        _p = [MC4_SITE getPos [3000, 360 call MC4_fnc_al], 150] call MC4_fnc_plat;
        { private _c9 = [MC4_SITE getPos [3000, _x], 150] call MC4_fnc_plat; if (!surfaceIsWater _c9 && { [_c9, 4] call MULTI_fnc_loin }) exitWith { _p = _c9 } } forEach [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
        _pt = _p getPos [40, 0];
    };
    (format ["CHACAL|CANARI|couple|%1|essais|%2|franc|%3|distance|%4", round (time * 100) / 100,
        _essaisT, (if (_trouveT) then {1} else {0}), round (_pt distance2D _p)]) call MC4_LOG;
    MC4_RNG = _rngSauve;   // le generateur de la mission est rendu intact

    private _g = ([east, 4] call MULTI_fnc_groupe);
    MC4_CANARI = _g createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    MC4_CANARI setVariable ["chacal_role", "CANARI", true];
    MC4_CANARI call MC4_fnc_identifier;   // l instrument ne doit pas subir son propre defaut
    _g setBehaviour "CARELESS"; _g allowFleeing 0;
    doStop MC4_CANARI;
    sleep 4;
    private _id = MC4_CANARI getVariable ["chacal_id", -1];
    (format ["CHACAL|CANARI|pose|%1|id|%2|pos|%3", round (time * 100) / 100, _id, _p]) call MC4_LOG;

    // --- CANAL TIR : trois coups, a un instant ecrit ---
    // Ce bloc annoncait trois coups et n en tirait AUCUN : `currentMuzzle` rend
    // "" tant que l arme n est pas levee, et `forceWeaponFire ["", ...]` echoue
    // en silence. On leve l arme et on journalise les noms reels.
    MC4_CANARI setBehaviour "AWARE";
    private _arme = primaryWeapon MC4_CANARI;
    MC4_CANARI selectWeapon _arme;
    sleep 2;
    (format ["CHACAL|CANARI|arme|%1|muzzle|%2|mode|%3", _arme,
        currentMuzzle MC4_CANARI, currentWeaponMode MC4_CANARI]) call MC4_LOG;
    (format ["CHACAL|CANARI|tire|%1|id|%2|coups|3", round (time * 100) / 100, _id]) call MC4_LOG;
    for "_i" from 1 to 3 do {
        if (alive MC4_CANARI) then {
            private _m = currentMuzzle MC4_CANARI;
            if (_m == "") then { _m = _arme };
            MC4_CANARI forceWeaponFire [_m, currentWeaponMode MC4_CANARI];
        };
        sleep 1;
    };

    // --- CANAL VUE : un temoin bleu, en vue franche ---
    // VC, VH et VG pouvaient rendre du vide toute une nuit sans qu une porte
    // s allume - or c est VG qui doit prouver que le maitre n a pas triche.
    private _gt = ([west, 4] call MULTI_fnc_groupe);
    MC4_TEMOIN = _gt createUnit ["B_Soldier_F", _pt, [], 0, "NONE"];
    MC4_TEMOIN setVariable ["chacal_role", "TEMOIN_VUE", true];
    MC4_TEMOIN call MC4_fnc_identifier;
    MC4_TEMOIN setDir (MC4_TEMOIN getDir MC4_CANARI);
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
        if ([MC4_TEMOIN, MC4_CANARI] call MC4_fnc_voit) exitWith { _okVue = true };
        private _cand = _p getPos [28 + (34 call MC4_fnc_al), _j * 15];
        _cand set [2, 0];
        if (!surfaceIsWater _cand) then {
            MC4_TEMOIN setPosATL _cand;
            MC4_TEMOIN setDir (MC4_TEMOIN getDir MC4_CANARI);
            sleep 0.5;
        };
    };
    (format ["CHACAL|CANARI|placement_temoin|%1|essais|%2|vue|%3|distance|%4", round (time * 100) / 100,
        _essaisV, (if (_okVue) then {1} else {0}), round (MC4_TEMOIN distance MC4_CANARI)]) call MC4_LOG;
    if (!_okVue) then {
        (format ["CHACAL|AVERT|temoin_sans_vue|%1|aucune_position_mesuree_franche_en_%2_essais", round (time * 100) / 100, _essaisV]) call MC4_LOG;
    };
    _gt setBehaviour "CARELESS"; _gt setCombatMode "BLUE"; _gt allowFleeing 0;
    doStop MC4_TEMOIN;
    // ! LE CONTROLE TUAIT SON PROPRE TEMOIN. Le canari est un soldat arme en
    // AWARE ; on lui `reveal` un ennemi a 34 m, il l abat, et `MC4_fnc_voit`
    // sortait alors sur sa toute premiere garde - `!alive _u`.
    MC4_TEMOIN allowDamage false;
    MC4_CANARI setCombatMode "BLUE";
    MC4_CANARI disableAI "AUTOTARGET";
    MC4_CANARI disableAI "TARGET";
    // On ne coupe JAMAIS "PATH" : mesure du 11/08, ca retire les jambes.
    MC4_CANARI reveal [MC4_TEMOIN, 4];
    MC4_TEMOIN reveal [MC4_CANARI, 4];
    MC4_TEMOIN doWatch MC4_CANARI;
    sleep 5;
    private _rel = abs ((((MC4_TEMOIN getDir MC4_CANARI) - (getDir MC4_TEMOIN) + 540) % 360) - 180);
    private _a = (getPosASL MC4_TEMOIN) vectorAdd [0,0,1.5];
    private _b = (getPosASL MC4_CANARI) vectorAdd [0,0,1.2];
    private _los = (count (lineIntersectsSurfaces [_a, _b, MC4_TEMOIN, MC4_CANARI, true, 1, "VIEW", "VIEW"])) == 0;
    (format ["CHACAL|CANARI|temoin|%1|id|%2|distance|%3|vue|%4|ecart_regard|%5|ligne_de_vue|%6|posture|%7|vivant|%8",
        round (time * 100) / 100, (MC4_TEMOIN getVariable ["chacal_id", -1]),
        round (MC4_TEMOIN distance MC4_CANARI),
        (if ([MC4_TEMOIN, MC4_CANARI] call MC4_fnc_voit) then {1} else {0}),
        round _rel, (if (_los) then {1} else {0}), stance MC4_TEMOIN,
        (if (alive MC4_TEMOIN) then {1} else {0})]) call MC4_LOG;

    // --- CANAL MORT ---
    sleep 45;
    (format ["CHACAL|CANARI|tue|%1|id|%2", round (time * 100) / 100, _id]) call MC4_LOG;
    MC4_CANARI setDamage 1;
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
    waitUntil { sleep 2; MC4_FIN };
    sleep 3;

    private _actes = count MC4_CHARGES;
    private _objTotal = count MC4_OBJETS;
    private _vivants = count (MC4_FS select { alive _x });
    private _exf = if (isNil "MC4_EXFILTRES") then {0} else {MC4_EXFILTRES};
    private _pertesEst = (count MC4_EST_SITE) - (count (MC4_EST_SITE select { alive _x }));
    private _lat = if (MC4_T_ALARME < 0 || MC4_T_COMPROMIS < 0) then {-999}
                   else { round ((MC4_T_COMPROMIS - MC4_T_ALARME) * 100) / 100 };

    if (MC4_ISSUE != "VOID" && !MC4_LAMBS) then { MC4_ISSUE = "VOID"; MC4_CAUSE = "LAMBS_ABSENT" };
    if (MC4_ISSUE != "VOID") then {
        if (MC4_ABANDON && _actes == 0) then {
            MC4_ISSUE = "ABANDON";
            // La cause a ete ecrite a l instant de la decision. On la LIT, on ne
            // la devine pas : le premier jet la reconstruisait d un compteur a
            // zero et sortait OBSERVATION_VIDE pour un episode ou la phase 3
            // n avait jamais eu lieu.
            MC4_CAUSE = if (!isNil "MC4_CAUSE_ABANDON" && { MC4_CAUSE_ABANDON != "" })
                           then {MC4_CAUSE_ABANDON} else {"ABANDON_SANS_CAUSE"};
        } else {
            if (_actes >= _objTotal && _exf >= (round (0.6 * MC4_EFFECTIF))) then { MC4_ISSUE = "SUCCES"; MC4_CAUSE = "CHARGES_ET_EXFIL" }
            else {
                MC4_ISSUE = "ECHEC";
                // ! L ETIQUETTE MENTAIT ( 13/09 ). EXFIL_MANQUEE couvrait deux choses differentes :
                // un detachement qui n a pas rejoint le point de ramassage, et un detachement qui n a
                // plus assez d hommes pour le franchir. Le second n a pas rate son decrochage, il a
                // perdu ses hommes. On separe, sinon le goulot se lit a l envers.
                MC4_CAUSE = if (_vivants == 0) then {"DETACHEMENT_DETRUIT"}
                    else { if (_actes < _objTotal) then {"CHARGES_INCOMPLETES"} else {
                    if (_vivants < (round (0.6 * MC4_EFFECTIF))) then {"PERTES_EXCESSIVES"} else {"EXFIL_MANQUEE"} } };
            };
        };
    };

    (format ["CHACAL|FINI|%1|%2|graine|%3|echelle|%4|dt|%5|bras|%6|palier|%24|phase_max|%7|charges|%8|sur|%9|detruits_scriptes|%10|intel|%11|exfiltres|%12|vivants|%13|pertes_est|%14|renseignement|%15|alarme|%16|compromis|%17|latence_surprise|%18|abandon|%19|insertion_forcee|%20|lambs|%21|ticks|%22|duree|%23|tenir|%25|arret|%26|depart|%27|effectif|%28|appui_feu|%29|accessible|%30|feu_avant|%31|mg_assaut|%32|delai_porteur|%33|appui_fixe|%34|oracle|%35|socle|%36|tactique|%37|relances|%38|fumigenes|%39|zones|%40|ablation|%41|banc_appui|%42|tirs_banc|%43|placeur|%44|couverture|%45|exfil|%46|azimut|%47|azimut_joue|%48|sans_jambes|%49|obs|%50",
        MC4_ISSUE, MC4_CAUSE, MC4_GRAINE, MC4_ECHELLE, MC4_DT, MC4_BRAS, MC4_PHASE,
        _actes, _objTotal, count MC4_DETRUITS, (if (MC4_INTEL) then {1} else {0}),
        _exf, _vivants, _pertesEst, count MC4_VUES,
        (if (MC4_ALARME) then {1} else {0}), (if (MC4_COMPROMIS) then {1} else {0}), _lat,
        (if (MC4_ABANDON) then {1} else {0}), (if (MC4_INSERTION_FORCEE) then {1} else {0}),
        (if (MC4_LAMBS) then {1} else {0}), MC4_TICK, round time, MC4_PALIER, MC4_TENIR, MC4_ARRET, MC4_DEPART, MC4_EFFECTIF, MC4_APPUI_FEU, MC4_ACCESSIBLE, MC4_FEU_AVANT, MC4_MG_ASSAUT, MC4_DELAI_PORTEUR, MC4_APPUI_FIXE, MC4_ORACLE, MC4_SOCLE, MC4_TACTIQUE, MC4_RELANCES_SOCLE, MC4_FUMIGENES, MC4_ZONES, MC4_ABLATION, MC4_BANC_APPUI, MC4_TIRS_BANC, MC4_PLACEUR, MC4_COUV, MC4_EXFIL, MC4_AZIMUT, MC4_AZIMUT_CHOISI, MC4_SANS_JAMBES, MC4_OBS]) call MC4_LOG;

    // L ECHELLE raccourcit les plafonds mais PAS le monde : ni la vitesse de
    // marche, ni la periode des rondes, ni les 6 km de route. Une nuit a 25 %
    // est une AUTRE mission.
    if (MC4_ECHELLE != 1) then {
        (format ["CHACAL|AVERT|hors_corpus|echelle|%1", MC4_ECHELLE]) call MC4_LOG;
    };

    call MC4_fnc_arreterCapture;

    // On N ARRETE PAS la mission : avec persistent=1 un endMission la
    // RELANCERAIT avec les MEMES parametres, donc la meme graine, et deux
    // episodes identiques entreraient dans le corpus sous deux noms.
    "CHACAL|OK|serveur_au_repos|le_harnais_peut_relancer" call MC4_LOG;
};
