// =====================================================================
// CHACAL - L ENREGISTREUR. Morceaux independants, chacun annonce sa ligne OK.
// Si l un tombe, les autres vivent et le lecteur voit LEQUEL manque.
// Mecanique reprise de hmt_capture v7, qui a tenu des nuits entieres.
//
// LE POINT QUI JUSTIFIE CE FICHIER : TROIS JOURNAUX DE PERCEPTION.
//   VC - la vue DU CAMP. `east knowsAbout _homme` est une valeur de CAMP,
//        partagee par radio. C est ce que LAMBS a REELLEMENT utilise.
//   VH - la vue DE L HOMME au sens du moteur ( knowsAbout reste de groupe ).
//   VG - la vue GEOMETRIQUE : portee, cone, ligne de vue, et RIEN d autre.
//        C est le seul canal opposable a la vue de camp, donc le seul qui
//        puisse prouver, apres coup, que le maitre n a pas triche.
// =====================================================================

MC2_CAP_VERSION = 1;
if (isNil "MC2_NEXT_ID") then { MC2_NEXT_ID = 1 };
MC2_TICK = 0; MC2_LAST = -1;
MC2_MAXCAR = 850;
MC2_CHRONO = [0, 0];
MC2_DTV = 2;                                   // la perception se rejoue moins vite que la position

MC2_TOUS = { (allUnits + allDeadMen) select { private _c = _x getVariable ["multi_c", -1]; if (_c < 0) then { _c = _x call MULTI_fnc_cellule }; _c == 2 } };
MC2_fnc_side = {
    private _s = _this;
    if (_s == east) exitWith {0};
    if (_s == west) exitWith {1};
    if (_s == resistance) exitWith {2};
    3
};
MC2_fnc_posture = {
    private _p = stance _this;
    if (_p == "STAND")  exitWith {0};
    if (_p == "CROUCH") exitWith {1};
    if (_p == "PRONE")  exitWith {2};
    3
};
MC2_fnc_comport = {
    private _b = behaviour _this;
    if (_b == "CARELESS") exitWith {0};
    if (_b == "SAFE")     exitWith {1};
    if (_b == "AWARE")    exitWith {2};
    if (_b == "COMBAT")   exitWith {3};
    if (_b == "STEALTH")  exitWith {4};
    5
};

// ! Un vehicule n a pas d identifiant d unite : `EntityKilled` rendait donc
// tueur -1 et " morts de cause inconnue " la ou il fallait lire " fauches par
// la mitrailleuse de la patrouille ". On retombe sur le servant, puis le chef
// de bord, puis le pilote.
MC2_fnc_idTueur = {
    private _t = _this;
    if (isNull _t) exitWith { [-1, ""] };
    private _id = _t getVariable ["chacal_id", -1];
    if (_id >= 0) exitWith { [_id, ""] };
    private _h = gunner _t;
    if (isNull _h) then { _h = effectiveCommander _t };
    if (isNull _h) then { _h = driver _t };
    if (!isNull _h) then { _id = _h getVariable ["chacal_id", -1] };
    [_id, typeOf _t]
};

// ======================= 1. L IDENTITE =======================
// ! Toute unite creee en cours d episode passait DEUX SECONDES sans identite,
// et sa premiere victime a ete le canari lui-meme - l instrument de controle.
// L identite se donne donc unite par unite, et l emetteur la RECLAME avant
// d ecrire une ligne : la fenetre est fermee, pas raccourcie.
MC2_fnc_identifier = {
    private _u = _this;
    if (!isNil { _u getVariable "chacal_id" }) exitWith { _u getVariable "chacal_id" };
    _u setVariable ["chacal_id", MC2_NEXT_ID];
    _u setVariable ["chacal_side", (side _u) call MC2_fnc_side];
    _u setVariable ["chacal_fire", 0];
    (format ["CHACAL|E|spawn|%1|%2|%3|%4|%5", round (time * 100) / 100, MC2_NEXT_ID,
        (side _u) call MC2_fnc_side, typeOf _u,
        (_u getVariable ["chacal_role", ""])]) call MC2_LOG;
    _u addEventHandler ["Fired", {
        params ["_tireur"];
        _tireur setVariable ["chacal_fire", 1];
        (format ["CHACAL|E|tir|%1|%2|%3|%4", round (time * 100) / 100,
            (_tireur getVariable ["chacal_id", -1]),
            (if (isNull (assignedTarget _tireur)) then {-1} else {(assignedTarget _tireur) getVariable ["chacal_id", -1]}),
            MC2_PHASE]) call MC2_LOG;
    }];
    MC2_NEXT_ID = MC2_NEXT_ID + 1;
    MC2_NEXT_ID - 1
};

// ! Un `Fired` pose sur l HOMME ne voit pas les armes de BORD. Le MRAP de route
// a tue le chef et l adjoint et le corpus ne contenait aucun de ses tirs : on
// meurt sans qu un coup soit parti. Les vehicules armes ont donc le leur.
MC2_fnc_identifierVehicule = {
    private _v = _this;
    if (!isNil { _v getVariable "chacal_veh" }) exitWith {};
    _v setVariable ["chacal_veh", 1];
    _v addEventHandler ["Fired", {
        params ["_veh"];
        private _t = _veh call MC2_fnc_idTueur;
        (format ["CHACAL|E|tir|%1|%2|%3|%4|bord|%5", round (time * 100) / 100,
            (_t select 0),
            (if (isNull (assignedTarget _veh)) then {-1} else {(assignedTarget _veh) getVariable ["chacal_id", -1]}),
            MC2_PHASE, typeOf _veh]) call MC2_LOG;
    }];
};

MC2_fnc_recenser = {
    { _x call MC2_fnc_identifier } forEach (call MC2_TOUS);
    { if ((count (crew _x) > 0) && { ((crew _x select 0) call MULTI_fnc_cellule) == 2 }) then { _x setVariable ["multi_c", 2]; _x call MC2_fnc_identifierVehicule } } forEach vehicles;
};
call MC2_fnc_recenser;
[] spawn { while { !MC2_FIN } do { call MC2_fnc_recenser; sleep 2 } };
(format ["CHACAL|OK|recenseur|1|au_premier_passage|%1", MC2_NEXT_ID - 1]) call MC2_LOG;

// ======================= 2. L EMETTEUR D ETAT =======================
// EachFrame + accumulateur : contexte non ordonnance, immunise contre la famine
// du scheduler SQF. Les MORTS RESTENT dans le tick, position figee - la mort
// est une transition a predire, pas une disparition.
MC2_EH_FRAME = addMissionEventHandler ["EachFrame", {
    if (MC2_CAP_VERSION != 1) exitWith {};
    private _t = time;
    if (_t - MC2_LAST < MC2_DT) exitWith {};
    MC2_LAST = _t;
    private _d0 = diag_tickTime;
    MC2_TICK = MC2_TICK + 1;
    private _tr = round (_t * 100) / 100;
    private _tous = call MC2_TOUS;
    private _n = count _tous;
    private _bouts = []; private _cour = "";
    {
        private _u = _x;
        private _id = _u getVariable ["chacal_id", -1];
        if (_id < 0) then { _id = _u call MC2_fnc_identifier };
        private _p = getPosASL _u;
        private _e = str [
            _id,
            round ((_p select 0) * 10) / 10, round ((_p select 1) * 10) / 10, round ((_p select 2) * 10) / 10,
            round (getDir _u),
            (if (alive _u) then {1} else {0}),
            (_u getVariable ["chacal_side", 3]),
            (_u call MC2_fnc_posture),
            (_u call MC2_fnc_comport),
            round (speed _u),
            (_u getVariable ["chacal_fire", 0])
        ];
        if ((_u getVariable ["chacal_fire", 0]) == 1) then { _u setVariable ["chacal_fire", 0] };
        if ((count _cour) + (count _e) + 1 > MC2_MAXCAR) then { _bouts pushBack _cour; _cour = "" };
        _cour = if (_cour == "") then { _e } else { _cour + "," + _e };
    } forEach _tous;
    _bouts pushBack _cour;
    { (format ["CHACAL|S|%1|%2|%3|%4|%5|[%6]", MC2_TICK, _forEachIndex, _tr, _n, MC2_PHASE, _x]) call MC2_LOG; } forEach _bouts;

    MC2_CHRONO set [0, (MC2_CHRONO select 0) + (diag_tickTime - _d0)];
    MC2_CHRONO set [1, (MC2_CHRONO select 1) + 1];
    if ((MC2_CHRONO select 1) % 400 == 0) then {
        (format ["CHACAL|C|cout_ms|%1|ticks|%2|unites|%3|fps|%4",
            round (1000 * (MC2_CHRONO select 0) / (MC2_CHRONO select 1) * 100) / 100,
            (MC2_CHRONO select 1), _n, round diag_fps]) call MC2_LOG;
        MC2_CHRONO = [0, 0];
    };
}];
"CHACAL|OK|emetteur|1" call MC2_LOG;

// ======================= 3. LES TROIS VUES =======================
MC2_T_VUES = time - (2 * 0.37);
MC2_EH_VUES = addMissionEventHandler ["EachFrame", {
    if (MC2_FIN || { MC2_CAP_VERSION != 1 } || { (time - MC2_T_VUES) < MC2_DTV }) exitWith {};
    MC2_T_VUES = time;
    call {
        private _tr = round (time * 100) / 100;
        private _vivants = (call MC2_TOUS) select { alive _x };
        private _bl = _vivants select { side _x == west };
        private _op = _vivants select { side _x == east };

        private _cb = _bl apply { [(_x getVariable ["chacal_id",-1]), round ((east knowsAbout _x) * 100) / 100] };
        private _co = _op apply { [(_x getVariable ["chacal_id",-1]), round ((west knowsAbout _x) * 100) / 100] };
        (format ["CHACAL|VC|%1|%2|est_sur_ouest|%3", _tr, MC2_PHASE, str _cb]) call MC2_LOG;
        (format ["CHACAL|VC|%1|%2|ouest_sur_est|%3", _tr, MC2_PHASE, str _co]) call MC2_LOG;

        // VH : son meilleur ennemi connu, et a quel prix. L angle compte : un
        // homme ne voit pas derriere lui, et le cone a ete certifie ( 18/18
        // dedans, 0/26 dehors ). Sans lui, le corpus laisse croire a une vue a 360.
        private _fnc = {
            params ["_liste", "_adv", "_etiq"];
            private _lignes = [];
            {
                private _u = _x;
                private _pu = (getPosASL _u) vectorAdd [0,0,1.5];
                private _best = -1; private _bk = 0; private _bd = -1; private _ba = -1; private _bv = 0; private _nb = 0;
                {
                    private _e = _x;
                    private _k = _u knowsAbout _e;
                    if (_k > 0.05) then { _nb = _nb + 1 };
                    if (_k > _bk) then {
                        _bk = _k; _best = _e getVariable ["chacal_id", -1];
                        _bd = round (_u distance _e);
                        _ba = round ((((_u getDir _e) - (getDir _u) + 540) % 360) - 180);
                        private _pe = (getPosASL _e) vectorAdd [0,0,1.2];
                        _bv = if (count (lineIntersectsSurfaces [_pu, _pe, _u, _e, true, 1, "VIEW", "VIEW"]) == 0) then {1} else {0};
                    };
                } forEach _adv;
                _lignes pushBack [(_u getVariable ["chacal_id",-1]), _best, round (_bk * 100) / 100, _bd, _ba, _bv, _nb];
            } forEach _liste;
            (format ["CHACAL|VH|%1|%2|%3|%4", _tr, MC2_PHASE, _etiq, str _lignes]) call MC2_LOG;
        };
        [_bl, _op, "ouest"] call _fnc;
        // Cote rouge on n emet que pour ceux qui ont un contact : trente hommes
        // qui ne voient rien produiraient trente lignes de zeros par pas.
        private _actifs = _op select { private _e = _x; ({ (_e knowsAbout _x) > 0.05 } count _bl) > 0 };
        [_actifs, _bl, "est"] call _fnc;

        // VG : ce que l oeil peut atteindre, sans rien demander a l IA.
        private _vg = [];
        {
            private _u = _x;
            private _cible = -1; private _dm = 9999;
            {
                if ([_u, _x] call MC2_fnc_voit) then {
                    private _d = _u distance _x;
                    if (_d < _dm) then { _dm = _d; _cible = _x getVariable ["chacal_id", -1] };
                };
            } forEach _op;
            if (_cible >= 0) then { _vg pushBack [(_u getVariable ["chacal_id",-1]), _cible, round _dm] };
        } forEach _bl;
        (format ["CHACAL|VG|%1|%2|ouest|%3", _tr, MC2_PHASE, str _vg]) call MC2_LOG;

    };
}];
"CHACAL|OK|vues|1" call MC2_LOG;
// MULTI : le POULS de la cellule - une boucle ordonnancee de 2 s qui ne fait rien d'autre que dire quand elle
// tourne. Son retard est celui de toute la logique de mission de la cellule : c'est la porte de cadence.
[] spawn { while { !MC2_FIN } do { sleep 2; (format ["CHACAL|C|pouls|%1", round (time * 100) / 100]) call MC2_LOG } };

// ======================= 4. LES MORTS =======================
MC2_EH_MORT = addMissionEventHandler ["EntityKilled", {
    params ["_vic", "_tueur", ["_instig", objNull]];
    if ((_vic call MULTI_fnc_cellule) != 2) exitWith {};   // MULTI : une mort d une autre cellule ne s ecrit pas ici
    // ! QUI A TUE ( 16/09, decision de Younes ). Une mort infligee par l EST pendant l insertion devient
    // une issue tactique et n annule plus l episode ; seule une mort sans tueur ennemi l annule encore.
    // L etiquette ne change rien a la ligne de trace ci-dessous.
    private _qui = if (!isNull _instig) then { _instig } else { _tueur };
    if (!isNull _qui && { _qui != _vic }) then {
        private _cote = if (_qui isKindOf "CAManBase") then { side (group _qui) } else { side _qui };
        if (_cote == east) then { _vic setVariable ["chacal_tue_par_est", true] };
    };
    private _t = _tueur call MC2_fnc_idTueur;
    (format ["CHACAL|E|mort|%1|%2|%3|%4|%5|par|%6", round (time * 100) / 100,
        (_vic getVariable ["chacal_id", -1]),
        (_t select 0), MC2_PHASE,
        (_vic getVariable ["chacal_role", ""]), (_t select 1)]) call MC2_LOG;
}];
"CHACAL|OK|morts|1" call MC2_LOG;

// ! 6 193 lignes avaient ete ecrites APRES le verdict, 16 % du fichier, dont
// trois morts de FS posterieures a l episode. Un enregistreur qui survit a
// l episode fabrique du corpus qui n appartient a rien.
MC2_fnc_arreterCapture = {
    if (MC2_CAP_VERSION == 0) exitWith {};
    MC2_CAP_VERSION = 0;
    removeMissionEventHandler ["EachFrame", MC2_EH_FRAME];
    removeMissionEventHandler ["EachFrame", MC2_EH_VUES];
    removeMissionEventHandler ["EntityKilled", MC2_EH_MORT];
    { _x removeAllEventHandlers "Fired" } forEach ((call MC2_TOUS) + (vehicles select { (_x getVariable ["multi_c", -1]) == 2 }));
    (format ["CHACAL|OK|capture_arretee|ticks|%1|t|%2", MC2_TICK, round (time * 100) / 100]) call MC2_LOG;
};

(format ["CHACAL|OK|capture|%1|dt|%2|dtv|%3", MC2_CAP_VERSION, MC2_DT, MC2_DTV]) call MC2_LOG;
