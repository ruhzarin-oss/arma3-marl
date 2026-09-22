// =====================================================================
// CHACAL - LA SITUATION. Des menaces qui varient d un episode a l autre, dans chacune des six phases.
//
// POURQUOI ( Younes, 16/09 ) : l agent doit rencontrer le plus grand nombre de situations et
// apprendre a choisir selon la situation pour reussir la mission. Or au palier 4 les phases 1 et 2
// n offraient AUCUNE menace ( ni ronde, ni patrouille, ni vehicule sur la route ; la zone de poser
// est meme tiree a plus de 2,2 km de la route ) : aucun choix n y pouvait rien changer.
//
// DEUX GENERATEURS, DEUX OBJETS. Le MONDE ( site, crete, route, poser ) reste tire par la graine
// du monde. La SITUATION ( quelle menace, ou ) est tiree par un generateur a part, seme par
// MC1_SITUATION, la graine du monde et la phase :
//   - un meme monde porte autant de situations qu on veut ;
//   - poser une menace ne consomme AUCUN tirage du monde. MC1_fnc_creer tire dans
//     MC1_fnc_al : l utiliser ici aurait decale la reserve, les positions et les delais, et un
//     episode avec menace n aurait plus ete comparable au meme sans ( piege de la faute n7 ) ;
//   - chaque phase est ressemee : le niveau choisi pour une phase ne deplace pas les menaces d une autre.
//
// NIVEAUX, les memes pour chaque phase : 0 aucune menace, 1 et 2 deux menaces de type different,
// 3 les deux a la fois et plus pres. Tout est a 0 par defaut : sans levier, rien n est cree et
// aucune ligne n est ecrite.
//
// Chaque menace ecrit une ligne CHACAL|E|situation : phase, niveau, type, hommes, reference,
// distance, azimut, centre. C est elle qui dit a dbt ce que l agent a affronte.
// =====================================================================

MC1_MENACES = [];
// Au palier 9 ( monde vide, controle positif de l acte ) 30_opfor.sqf sort avant de definir MC1_PAL_SKILL.
private _skillS = missionNamespace getVariable ["MC1_PAL_SKILL", 0.5];

// --- le generateur de SITUATION : reproductible, distinct du monde et du temoin ---
MC1_fnc_semerS = {
    private _phase = _this;
    MC1_RNG_S = ((MC1_SITUATION * 251) + (MC1_GRAINE * 17) + (_phase * 4099) + 3) % 65537;
    if (MC1_RNG_S == 0) then { MC1_RNG_S = 1 };
    for "_i" from 1 to 20 do { MC1_RNG_S = ((MC1_RNG_S * 75) + 74) % 65537 };
};
MC1_fnc_rndS = {
    MC1_RNG_S = ((MC1_RNG_S * 75) + 74) % 65537;
    MC1_RNG_S / 65537
};
MC1_fnc_alS = { (call MC1_fnc_rndS) * _this };
MC1_fnc_bandeS = { params ["_a", "_b"]; _a + ((_b - _a) call MC1_fnc_alS) };
0 call MC1_fnc_semerS;

// --- creer un groupe SANS toucher l alea du monde ---
MC1_fnc_creerS = {
    params ["_classes", "_p", "_ray", ["_skill", 0.5], ["_nvg", false]];
    private _g = ([east, 1] call MULTI_fnc_groupe);
    {
        private _u = _g createUnit [_x, _p getPos [_ray call MC1_fnc_alS, 360 call MC1_fnc_alS], [], 0, "NONE"];
        [_u, _skill, _nvg] call MC1_fnc_kitEst;
    } forEach _classes;
    _g
};

// --- un poste fixe : il ne bouge pas et regarde ce qu il garde ---
MC1_fnc_posteS = {
    params ["_g", "_regard"];
    _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g allowFleeing 0;
    { doStop _x; _x setUnitPos "MIDDLE"; _x doWatch _regard } forEach (units _g);
};

// --- une patrouille a pied autour d un point ---
MC1_fnc_patrouilleS = {
    params ["_classes", "_p", "_rayon"];
    private _g = [_classes, _p, 15, 0.5, false] call MC1_fnc_creerS;
    _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g setSpeedMode "LIMITED"; _g allowFleeing 0.2;
    [_g, _p, _rayon] call MC1_fnc_patrouille;
    _g
};

// --- noter une menace : la ligne de trace, et le groupe rejoint ceux qui reagissent a l alarme ---
MC1_fnc_menaceNoter = {
    params ["_phase", "_type", "_g", "_p", "_ref", "_refNom", ["_ajouterAuCamp", true]];
    _g setVariable ["chacal_menace", format ["P%1_%2", _phase, _type], true];
    MC1_MENACES pushBack [_phase, _type, _g];
    if (_ajouterAuCamp) then { MC1_GROUPES_EST pushBack _g };
    (format ["CHACAL|E|situation|%1|phase|%2|niveau|%3|type|%4|hommes|%5|reference|%6|distance|%7|azimut|%8|centre|%9|graine_situation|%10",
        round (time * 100) / 100, _phase, (missionNamespace getVariable [format ["MC1_MENACE_P%1", _phase], 0]),
        _type, count (units _g), _refNom, round (_ref distance2D _p), round (_ref getDir _p),
        [round (_p select 0), round (_p select 1)], MC1_SITUATION]) call MC1_LOG;
};

// =====================================================================
// PHASE 1 - AUTOUR DE LA ZONE DE POSER
//   1 guetteur : deux hommes a jumelles de nuit, poses, qui regardent la zone de poser
//   2 patrouille a pied : quatre hommes qui tournent autour d un point proche
//   3 les deux, entre 150 et 350 m
// =====================================================================
if (MC1_MENACE_P1 > 0) then {
    1 call MC1_fnc_semerS;
    private _pres = (MC1_MENACE_P1 in [3, 4, 5]);
    if (MC1_MENACE_P1 in [1, 3, 4]) then {
        private _d = if (_pres) then { [150, 350] call MC1_fnc_bandeS } else { [400, 800] call MC1_fnc_bandeS };
        private _p = MC1_LZ getPos [_d, 360 call MC1_fnc_alS];
        private _g = [["O_Soldier_TL_F", "O_Sharpshooter_F"], _p, 6, 0.6, true] call MC1_fnc_creerS;
        [_g, MC1_LZ] call MC1_fnc_posteS;
        [1, "GUETTEUR", _g, _p, MC1_LZ, "POSER"] call MC1_fnc_menaceNoter;
    };
    if (MC1_MENACE_P1 in [2, 3, 5]) then {
        private _d = if (_pres) then { [150, 350] call MC1_fnc_bandeS } else { [250, 600] call MC1_fnc_bandeS };
        private _p = MC1_LZ getPos [_d, 360 call MC1_fnc_alS];
        private _g = [["O_Soldier_SL_F", "O_Soldier_F", "O_Soldier_AR_F", "O_Soldier_F"], _p, ((_d * 0.8) max 200)] call MC1_fnc_patrouilleS;
        [1, "PATROUILLE", _g, _p, MC1_LZ, "POSER"] call MC1_fnc_menaceNoter;
    };
};

// =====================================================================
// PHASE 2 - LA ROUTE
//   1 patrouille motorisee : le blinde de 30_opfor.sqf, section 7, rendu present au palier 4
//   2 poste de controle : trois hommes fixes sur la route, a distance du point de traversee
//   3 les deux, poste entre 150 et 300 m
// =====================================================================
if (MC1_MENACE_P2 > 0) then {
    2 call MC1_fnc_semerS;
    if (MC1_MENACE_P2 in [1, 3, 4]) then {
        if (isNull MC1_VEH_ROUTE) then {
            "CHACAL|AVERT|situation|phase|2|patrouille_route_non_creee" call MC1_LOG;
        } else {
            [2, "PATROUILLE_ROUTE", MC1_gRoute, getPosATL MC1_VEH_ROUTE, MC1_ROUTE, "TRAVERSEE", false] call MC1_fnc_menaceNoter;
        };
    };
    if (MC1_MENACE_P2 in [2, 3, 5]) then {
        private _d = if (MC1_MENACE_P2 in [3, 4, 5]) then { [150, 300] call MC1_fnc_bandeS } else { [300, 700] call MC1_fnc_bandeS };
        // le poste est sur la ROUTE : on garde le troncon dont la distance a la traversee est la plus proche de _d
        private _cands = (MC1_ROUTE nearRoads (_d + 150)) select { abs ((_x distance2D MC1_ROUTE) - _d) < 120 };
        private _p = [];
        if (count _cands > 0) then {
            _cands = [_cands, [MC1_ROUTE, _d], { abs ((_x distance2D _input0) - _input1) }, "ASCEND"] call BIS_fnc_sortBy;
            _p = +(getPosATL (_cands select ((floor (2 call MC1_fnc_alS)) min ((count _cands) - 1))));
        } else {
            _p = MC1_ROUTE getPos [_d, 360 call MC1_fnc_alS];
        };
        _p set [2, 0];
        private _g = [["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_AR_F"], _p, 5, _skillS, true] call MC1_fnc_creerS;
        [_g, MC1_ROUTE] call MC1_fnc_posteS;
        [2, "POSTE_DE_CONTROLE", _g, _p, MC1_ROUTE, "TRAVERSEE"] call MC1_fnc_menaceNoter;
    };
};

// =====================================================================
// PHASE 3 - LA CRETE D OBSERVATION
//   1 patrouille a pied qui passe pres de la crete
//   2 sentinelles sur le mur de l enceinte, cote crete : elles font partie de la garnison
//   3 les deux, patrouille entre 100 et 250 m de la crete
// =====================================================================
if (MC1_MENACE_P3 > 0) then {
    3 call MC1_fnc_semerS;
    if (MC1_MENACE_P3 in [1, 3, 4]) then {
        private _d = if (MC1_MENACE_P3 in [3, 4, 5]) then { [100, 250] call MC1_fnc_bandeS } else { [250, 500] call MC1_fnc_bandeS };
        private _p = MC1_OP getPos [_d, 360 call MC1_fnc_alS];
        private _g = [["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"], _p, ((_d * 0.7) max 150)] call MC1_fnc_patrouilleS;
        [3, "PATROUILLE_CRETE", _g, _p, MC1_OP, "CRETE"] call MC1_fnc_menaceNoter;
    };
    if (MC1_MENACE_P3 in [2, 3, 5]) then {
        private _p = MC1_SITE getPos [MC1_RAYON - 4, MC1_SITE getDir MC1_OP];
        private _g = [["O_Soldier_F", "O_Sharpshooter_F"], _p, 3, _skillS, true] call MC1_fnc_creerS;
        [_g, MC1_OP] call MC1_fnc_posteS;
        // des sentinelles de l enceinte SONT la garnison : la crete doit pouvoir les compter
        MC1_EST_SITE append (units _g);
        [3, "SENTINELLE_MUR", _g, _p, MC1_OP, "CRETE"] call MC1_fnc_menaceNoter;
    };
};

// =====================================================================
// PHASE 4 - ENTRE LE REGROUPEMENT ET L ENCEINTE, la ou le detachement se met en place
//   1 patrouille a pied
//   2 poste d ecoute : deux hommes fixes qui regardent vers le regroupement
//   3 les deux, plus pres de l enceinte
// =====================================================================
if (MC1_MENACE_P4 > 0) then {
    4 call MC1_fnc_semerS;
    private _axe = MC1_SITE getDir MC1_RALLY;
    if (MC1_MENACE_P4 in [1, 3, 4]) then {
        private _d = if (MC1_MENACE_P4 in [3, 4, 5]) then { [250, 400] call MC1_fnc_bandeS } else { [350, 650] call MC1_fnc_bandeS };
        private _p = MC1_SITE getPos [_d, _axe - 40 + (80 call MC1_fnc_alS)];
        private _g = [["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_AR_F"], _p, 200] call MC1_fnc_patrouilleS;
        [4, "PATROUILLE_MISE_EN_PLACE", _g, _p, MC1_SITE, "SITE"] call MC1_fnc_menaceNoter;
    };
    if (MC1_MENACE_P4 in [2, 3, 5]) then {
        private _d = if (MC1_MENACE_P4 in [3, 4, 5]) then { [200, 300] call MC1_fnc_bandeS } else { [250, 450] call MC1_fnc_bandeS };
        private _p = MC1_SITE getPos [_d, _axe - 40 + (80 call MC1_fnc_alS)];
        private _g = [["O_Soldier_F", "O_Sharpshooter_F"], _p, 4, _skillS, true] call MC1_fnc_creerS;
        [_g, MC1_RALLY] call MC1_fnc_posteS;
        [4, "POSTE_ECOUTE", _g, _p, MC1_SITE, "SITE"] call MC1_fnc_menaceNoter;
    };
};

// =====================================================================
// PHASE 5 - L ASSAUT
//   1 renfort de garnison : deux defenseurs de plus dans les batiments
//   2 alarme deja donnee quand l assaut commence
//   3 les deux
// =====================================================================
if (MC1_MENACE_P5 > 0) then {
    5 call MC1_fnc_semerS;
    if (MC1_MENACE_P5 in [1, 3, 4]) then {
        private _g = [["O_Soldier_F", "O_Soldier_AR_F"], MC1_SITE, 25, _skillS, false] call MC1_fnc_creerS;
        _g setBehaviour "SAFE"; _g setCombatMode "YELLOW"; _g allowFleeing 0;
        [_g, MC1_SITE, 55] call MC1_fnc_garnison;
        MC1_EST_SITE append (units _g);
        [5, "RENFORT_GARNISON", _g, MC1_SITE, MC1_SITE, "SITE"] call MC1_fnc_menaceNoter;
    };
    if (MC1_MENACE_P5 in [2, 3, 5]) then {
        (format ["CHACAL|E|situation|%1|phase|5|niveau|%2|type|ALARME_AVANT_ASSAUT|hommes|0|reference|SITE|distance|0|azimut|0|centre|[0,0]|graine_situation|%3",
            round (time * 100) / 100, MC1_MENACE_P5, MC1_SITUATION]) call MC1_LOG;
        MC1_MENACES pushBack [5, "ALARME_AVANT_ASSAUT", grpNull];
        [] spawn {
            waitUntil { sleep 2; (MC1_PHASE >= 5) || MC1_FIN };
            if (!MC1_FIN && { !MC1_ALARME }) then {
                // l oracle de 60_phases.sqf voit MC1_ALARME et declenche la suite : garnison en COMBAT, reserve
                MC1_T_ALARME = time;
                MC1_ALARME = true;
                (format ["CHACAL|E|situation_alarme|%1|phase|%2|cause|ALERTE_DONNEE_AVANT_L_ASSAUT", round (time * 100) / 100, MC1_PHASE]) call MC1_LOG;
            };
            // ! 16/09 : la ligne de decision de la phase 5 attend ce drapeau, sinon elle lirait l alarme avant sa pose.
            MC1_SITUATION_P5_FAITE = true;
        };
    };
};

// =====================================================================
// PHASE 6 - L EXFILTRATION
//   1 patrouille a pied sur l itineraire de sortie, entre l enceinte et le point d extraction
//   2 un blesse aux jambes quand l exfiltration commence
//   3 les deux, patrouille entre 300 et 500 m de l enceinte
// =====================================================================
if (MC1_MENACE_P6 > 0) then {
    6 call MC1_fnc_semerS;
    if (MC1_MENACE_P6 in [1, 3, 4]) then {
        private _d = if (MC1_MENACE_P6 in [3, 4, 5]) then { [300, 500] call MC1_fnc_bandeS } else { [500, 900] call MC1_fnc_bandeS };
        private _p = MC1_SITE getPos [_d, (MC1_SITE getDir MC1_PZ) - 25 + (50 call MC1_fnc_alS)];
        private _g = [["O_Soldier_SL_F", "O_Soldier_F", "O_Soldier_AR_F", "O_Soldier_F"], _p, 200] call MC1_fnc_patrouilleS;
        [6, "PATROUILLE_SORTIE", _g, _p, MC1_SITE, "SITE"] call MC1_fnc_menaceNoter;
    };
    if (MC1_MENACE_P6 in [2, 3, 5]) then {
        // tire MAINTENANT, pour que le choix du blesse ne depende pas de l ordre d execution
        private _k = 1 call MC1_fnc_alS;
        (format ["CHACAL|E|situation|%1|phase|6|niveau|%2|type|BLESSE_JAMBES|hommes|1|reference|DETACHEMENT|distance|0|azimut|0|centre|[0,0]|graine_situation|%3",
            round (time * 100) / 100, MC1_MENACE_P6, MC1_SITUATION]) call MC1_LOG;
        MC1_MENACES pushBack [6, "BLESSE_JAMBES", grpNull];
        [_k] spawn {
            params ["_k"];
            waitUntil { sleep 2; (MC1_PHASE >= 6) || MC1_FIN };
            if (MC1_FIN) exitWith {};
            private _viv = MC1_FS select { alive _x };
            if (count _viv == 0) exitWith {};
            private _u = _viv select ((floor (_k * (count _viv))) min ((count _viv) - 1));
            _u setHitPointDamage ["HitLegs", 1];
            (format ["CHACAL|E|situation_blesse|%1|phase|6|homme|%2|role|%3", round (time * 100) / 100,
                _u getVariable ["chacal_id", -1], _u getVariable ["chacal_role", ""]]) call MC1_LOG;
        };
    };
};

if (count MC1_MENACES > 0) then {
    (format ["CHACAL|OK|situation|graine_situation|%1|p1|%2|p2|%3|p3|%4|p4|%5|p5|%6|p6|%7|menaces|%8",
        MC1_SITUATION, MC1_MENACE_P1, MC1_MENACE_P2, MC1_MENACE_P3, MC1_MENACE_P4,
        MC1_MENACE_P5, MC1_MENACE_P6, count MC1_MENACES]) call MC1_LOG;
};
