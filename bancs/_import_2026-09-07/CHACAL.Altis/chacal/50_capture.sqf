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

CHACAL_CAP_VERSION = 1;
if (isNil "CHACAL_NEXT_ID") then { CHACAL_NEXT_ID = 1 };
CHACAL_TICK = 0; CHACAL_LAST = -1;
CHACAL_MAXCAR = 850;
CHACAL_CHRONO = [0, 0];
CHACAL_DTV = 2;                                   // la perception se rejoue moins vite que la position

CHACAL_TOUS = { allUnits + allDeadMen };
CHACAL_fnc_side = {
    private _s = _this;
    if (_s == east) exitWith {0};
    if (_s == west) exitWith {1};
    if (_s == resistance) exitWith {2};
    3
};
CHACAL_fnc_posture = {
    private _p = stance _this;
    if (_p == "STAND")  exitWith {0};
    if (_p == "CROUCH") exitWith {1};
    if (_p == "PRONE")  exitWith {2};
    3
};
CHACAL_fnc_comport = {
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
CHACAL_fnc_idTueur = {
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
CHACAL_fnc_identifier = {
    private _u = _this;
    if (!isNil { _u getVariable "chacal_id" }) exitWith { _u getVariable "chacal_id" };
    _u setVariable ["chacal_id", CHACAL_NEXT_ID];
    _u setVariable ["chacal_side", (side _u) call CHACAL_fnc_side];
    _u setVariable ["chacal_fire", 0];
    (format ["CHACAL|E|spawn|%1|%2|%3|%4|%5", round (time * 100) / 100, CHACAL_NEXT_ID,
        (side _u) call CHACAL_fnc_side, typeOf _u,
        (_u getVariable ["chacal_role", ""])]) call CHACAL_LOG;
    _u addEventHandler ["Fired", {
        params ["_tireur"];
        _tireur setVariable ["chacal_fire", 1];
        (format ["CHACAL|E|tir|%1|%2|%3|%4", round (time * 100) / 100,
            (_tireur getVariable ["chacal_id", -1]),
            (if (isNull (assignedTarget _tireur)) then {-1} else {(assignedTarget _tireur) getVariable ["chacal_id", -1]}),
            CHACAL_PHASE]) call CHACAL_LOG;
    }];
    CHACAL_NEXT_ID = CHACAL_NEXT_ID + 1;
    CHACAL_NEXT_ID - 1
};

// ! Un `Fired` pose sur l HOMME ne voit pas les armes de BORD. Le MRAP de route
// a tue le chef et l adjoint et le corpus ne contenait aucun de ses tirs : on
// meurt sans qu un coup soit parti. Les vehicules armes ont donc le leur.
CHACAL_fnc_identifierVehicule = {
    private _v = _this;
    if (!isNil { _v getVariable "chacal_veh" }) exitWith {};
    _v setVariable ["chacal_veh", 1];
    _v addEventHandler ["Fired", {
        params ["_veh"];
        private _t = _veh call CHACAL_fnc_idTueur;
        (format ["CHACAL|E|tir|%1|%2|%3|%4|bord|%5", round (time * 100) / 100,
            (_t select 0),
            (if (isNull (assignedTarget _veh)) then {-1} else {(assignedTarget _veh) getVariable ["chacal_id", -1]}),
            CHACAL_PHASE, typeOf _veh]) call CHACAL_LOG;
    }];
};

CHACAL_fnc_recenser = {
    { _x call CHACAL_fnc_identifier } forEach (call CHACAL_TOUS);
    { if (count (crew _x) > 0) then { _x call CHACAL_fnc_identifierVehicule } } forEach vehicles;
};
call CHACAL_fnc_recenser;
[] spawn { while { !CHACAL_FIN } do { call CHACAL_fnc_recenser; sleep 2 } };
(format ["CHACAL|OK|recenseur|1|au_premier_passage|%1", CHACAL_NEXT_ID - 1]) call CHACAL_LOG;

// ======================= 2. L EMETTEUR D ETAT =======================
// EachFrame + accumulateur : contexte non ordonnance, immunise contre la famine
// du scheduler SQF. Les MORTS RESTENT dans le tick, position figee - la mort
// est une transition a predire, pas une disparition.
CHACAL_EH_FRAME = addMissionEventHandler ["EachFrame", {
    if (CHACAL_CAP_VERSION != 1) exitWith {};
    private _t = time;
    if (_t - CHACAL_LAST < CHACAL_DT) exitWith {};
    CHACAL_LAST = _t;
    private _d0 = diag_tickTime;
    CHACAL_TICK = CHACAL_TICK + 1;
    private _tr = round (_t * 100) / 100;
    private _tous = call CHACAL_TOUS;
    private _n = count _tous;
    private _bouts = []; private _cour = "";
    {
        private _u = _x;
        private _id = _u getVariable ["chacal_id", -1];
        if (_id < 0) then { _id = _u call CHACAL_fnc_identifier };
        private _p = getPosASL _u;
        private _e = str [
            _id,
            round ((_p select 0) * 10) / 10, round ((_p select 1) * 10) / 10, round ((_p select 2) * 10) / 10,
            round (getDir _u),
            (if (alive _u) then {1} else {0}),
            (_u getVariable ["chacal_side", 3]),
            (_u call CHACAL_fnc_posture),
            (_u call CHACAL_fnc_comport),
            round (speed _u),
            (_u getVariable ["chacal_fire", 0])
        ];
        if ((_u getVariable ["chacal_fire", 0]) == 1) then { _u setVariable ["chacal_fire", 0] };
        if ((count _cour) + (count _e) + 1 > CHACAL_MAXCAR) then { _bouts pushBack _cour; _cour = "" };
        _cour = if (_cour == "") then { _e } else { _cour + "," + _e };
    } forEach _tous;
    _bouts pushBack _cour;
    { (format ["CHACAL|S|%1|%2|%3|%4|%5|[%6]", CHACAL_TICK, _forEachIndex, _tr, _n, CHACAL_PHASE, _x]) call CHACAL_LOG; } forEach _bouts;

    CHACAL_CHRONO set [0, (CHACAL_CHRONO select 0) + (diag_tickTime - _d0)];
    CHACAL_CHRONO set [1, (CHACAL_CHRONO select 1) + 1];
    if ((CHACAL_CHRONO select 1) % 400 == 0) then {
        (format ["CHACAL|C|cout_ms|%1|ticks|%2|unites|%3|fps|%4",
            round (1000 * (CHACAL_CHRONO select 0) / (CHACAL_CHRONO select 1) * 100) / 100,
            (CHACAL_CHRONO select 1), _n, round diag_fps]) call CHACAL_LOG;
        CHACAL_CHRONO = [0, 0];
    };
}];
"CHACAL|OK|emetteur|1" call CHACAL_LOG;

// ======================= 3. LES TROIS VUES =======================
[] spawn {
    while { !CHACAL_FIN } do {
        private _tr = round (time * 100) / 100;
        private _vivants = allUnits select { alive _x };
        private _bl = _vivants select { side _x == west };
        private _op = _vivants select { side _x == east };

        private _cb = _bl apply { [(_x getVariable ["chacal_id",-1]), round ((east knowsAbout _x) * 100) / 100] };
        private _co = _op apply { [(_x getVariable ["chacal_id",-1]), round ((west knowsAbout _x) * 100) / 100] };
        (format ["CHACAL|VC|%1|%2|est_sur_ouest|%3", _tr, CHACAL_PHASE, str _cb]) call CHACAL_LOG;
        (format ["CHACAL|VC|%1|%2|ouest_sur_est|%3", _tr, CHACAL_PHASE, str _co]) call CHACAL_LOG;

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
            (format ["CHACAL|VH|%1|%2|%3|%4", _tr, CHACAL_PHASE, _etiq, str _lignes]) call CHACAL_LOG;
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
                if ([_u, _x] call CHACAL_fnc_voit) then {
                    private _d = _u distance _x;
                    if (_d < _dm) then { _dm = _d; _cible = _x getVariable ["chacal_id", -1] };
                };
            } forEach _op;
            if (_cible >= 0) then { _vg pushBack [(_u getVariable ["chacal_id",-1]), _cible, round _dm] };
        } forEach _bl;
        (format ["CHACAL|VG|%1|%2|ouest|%3", _tr, CHACAL_PHASE, str _vg]) call CHACAL_LOG;

        sleep CHACAL_DTV;
    };
};
"CHACAL|OK|vues|1" call CHACAL_LOG;

// ======================= 4. LES MORTS =======================
CHACAL_EH_MORT = addMissionEventHandler ["EntityKilled", {
    params ["_vic", "_tueur"];
    private _t = _tueur call CHACAL_fnc_idTueur;
    (format ["CHACAL|E|mort|%1|%2|%3|%4|%5|par|%6", round (time * 100) / 100,
        (_vic getVariable ["chacal_id", -1]),
        (_t select 0), CHACAL_PHASE,
        (_vic getVariable ["chacal_role", ""]), (_t select 1)]) call CHACAL_LOG;
}];
"CHACAL|OK|morts|1" call CHACAL_LOG;

// ! 6 193 lignes avaient ete ecrites APRES le verdict, 16 % du fichier, dont
// trois morts de FS posterieures a l episode. Un enregistreur qui survit a
// l episode fabrique du corpus qui n appartient a rien.
CHACAL_fnc_arreterCapture = {
    if (CHACAL_CAP_VERSION == 0) exitWith {};
    CHACAL_CAP_VERSION = 0;
    removeMissionEventHandler ["EachFrame", CHACAL_EH_FRAME];
    removeMissionEventHandler ["EntityKilled", CHACAL_EH_MORT];
    { _x removeAllEventHandlers "Fired" } forEach ((call CHACAL_TOUS) + vehicles);
    (format ["CHACAL|OK|capture_arretee|ticks|%1|t|%2", CHACAL_TICK, round (time * 100) / 100]) call CHACAL_LOG;
};

(format ["CHACAL|OK|capture|%1|dt|%2|dtv|%3", CHACAL_CAP_VERSION, CHACAL_DT, CHACAL_DTV]) call CHACAL_LOG;
