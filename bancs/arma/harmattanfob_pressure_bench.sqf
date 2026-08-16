// pressure_bench.sqf — LE BANC DE PRESSION de l'officier de theatre (leviathan001).
//
// Trois fonctions, rien d'autre :
//   HMT_PB_RESET   remet le theatre dans un etat CONNU (memes garnisons, memes cibles).
//                  Sans reset, deux ordres ne sont pas comparables : c'est la faute n.1 de
//                  l'ancienne tache officier (le monde n'instanciait pas la situation).
//   HMT_PB_ATTACK  pose une pression CALIBREE. L'audit de la recompense impose de frapper les
//                  CIBLES VITALES (0.125/cible) et de faire des MORTS (0.025/homme) : contester
//                  du terrain ne pese que 0.010 par FOB, sous le bruit.
//   HMT_PB_ORDER   EXECUTE un verbe sur un FOB. Sans executeur, tous les ordres font la meme
//                  chose (rien) et le paysage est plat par construction.
//
// Charge une fois : call compile preprocessFileLineNumbers "pressure_bench.sqf";

if (isNil "HMT_PB_STATE") then { HMT_PB_STATE = createHashMap; };

// --- composition d'un FOB : les 6 premieres ancres sont MAIN, le reste OUTPOST (cf. fob_network) ---
HMT_PB_COMP = {
    params ["_main"];
    if (_main) then {
        ["rhs_msv_officer","rhs_msv_sergeant","rhs_msv_rifleman","rhs_msv_rifleman","rhs_msv_machinegunner","rhs_msv_at","rhs_msv_marksman","rhs_msv_medic"]
    } else {
        ["rhs_msv_sergeant","rhs_msv_rifleman","rhs_msv_machinegunner","rhs_msv_at","rhs_msv_marksman","rhs_msv_medic"]
    };
};

// --- memorise l'etat de reference des cibles au tout premier appel ---
HMT_PB_SNAPSHOT = {
    if (count HMT_PB_STATE > 0) exitWith { false };
    private _cib = [];
    { _x params ["_nom","_obj"];
      if (!isNull _obj) then { _cib pushBack [_nom, typeOf _obj, getPosATL _obj, (_obj isKindOf "CAManBase")]; };
    } forEach HMT_TARGETS;
    HMT_PB_STATE set ["cibles", _cib];
    diag_log format ["HARMATTAN_PB snapshot cibles=%1", count _cib];
    true
};

// ============================================================ RESET
HMT_PB_RESET = {
    HMT_PB_SAPE_ON = false;                         // la sape s'arrete entre deux episodes
    call HMT_PB_SNAPSHOT;

    // 1. les assaillants du banc disparaissent
    if (!isNil "HMT_PB_ATK") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_PB_ATK; };
    HMT_PB_ATK = [];
    if (!isNil "HMT_PB_ATKG") then { { if (!isNull _x) then { deleteGroup _x } } forEach HMT_PB_ATKG; };
    HMT_PB_ATKG = [];
    if (!isNil "HMT_OFFT") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_OFFT; HMT_OFFT = []; };

    // 2. on efface TOUS les hommes de garnison (vivants ou morts) et leurs groupes
    { _x params ["_u"]; if (!isNull _u) then { deleteVehicle _u }; } forEach HMT_FOB_MEN;
    HMT_FOB_MEN = [];
    { if (!isNull _x && {count units _x == 0}) then { deleteGroup _x }; } forEach HMT_FOB_GRP;
    HMT_FOB_GRP = [];

    // 3. on reconstruit 3 groupes par FOB, meme composition qu'a la construction initiale
    private _i = 0;
    while { _i < count HMT_FOB_ANCHORS } do {
        private _o = HMT_FOB_ANCHORS select _i;
        private _main = _i < 6;
        private _comp = [_main] call HMT_PB_COMP;
        private _g = 0;
        while { _g < 3 } do {
            private _grp = createGroup east; HMT_FOB_GRP pushBack _grp; _grp enableDynamicSimulation true;
            {
                private _pos = [(_o select 0) + 6 + _g * 5, (_o select 1) - 12 - _forEachIndex * 2, 0];
                private _u = _grp createUnit [_x, _pos, [], 3, "FORM"];
                HMT_FOB_MEN pushBack [_u, _x select [8]];
            } forEach _comp;
            _grp setBehaviour "SAFE"; _grp setCombatMode "YELLOW"; _grp allowFleeing 0;
            if (!isNil { missionNamespace getVariable "lambs_wp_fnc_taskGarrison" }) then {
                [_grp, _o, 60] call lambs_wp_fnc_taskGarrison;
            };
            _g = _g + 1;
        };
        _i = _i + 1;
        if (_i mod 6 == 0) then { sleep 0.1 };
    };

    // 4. on re-arme les statiques laissees vides (leurs servants sont morts)
    private _vides = (vehicles select { (_x isKindOf "StaticWeapon") && {alive _x} && {count crew _x == 0}
                                        && {[_x] call { params ["_v"]; private _d = 1e9;
                                            { _d = _d min (_v distance2D _x) } forEach HMT_FOB_ANCHORS; _d < 120 } } });
    if (count _vides > 0) then {
        private _gs = createGroup east; HMT_FOB_GRP pushBack _gs;
        { private _u = _gs createUnit ["rhs_msv_machinegunner", position _x, [], 0, "NONE"];
          _u moveInGunner _x; HMT_FOB_MEN pushBack [_u, "machinegunner"]; } forEach _vides;
    };

    // 5. on equipe tout le monde
    { [_x select 0, _x select 1] call HMT_KIT; if (_forEachIndex mod 60 == 0) then { sleep 0.15 }; } forEach HMT_FOB_MEN;

    // 6. les cibles vitales reviennent intactes
    private _cib = HMT_PB_STATE get "cibles";
    private _neuf = [];
    {
        _x params ["_nom","_type","_pos","_estHomme"];
        private _vivant = objNull;
        { _x params ["_n","_o"]; if (_n == _nom && {!isNull _o} && {alive _o}) then { _vivant = _o }; } forEach HMT_TARGETS;
        if (!isNull _vivant) then {
            _vivant setDamage 0;
            _neuf pushBack [_nom, _vivant];
        } else {
            private _o = if (_estHomme) then {
                private _g = createGroup east; HMT_PB_ATKG pushBack _g;
                private _u = _g createUnit [_type, _pos, [], 0, "NONE"]; _u setPosATL _pos; _u
            } else {
                private _v = createVehicle [_type, _pos, [], 0, "CAN_COLLIDE"]; _v setPosATL _pos; _v
            };
            _o setVariable ["HMT_TARGET", _nom];
            _neuf pushBack [_nom, _o];
        };
    } forEach _cib;
    HMT_TARGETS = _neuf;
    HMT_TARGET = HMT_TARGETS apply { _x select 1 };

    private _vivants = { alive (_x select 0) } count HMT_FOB_MEN;
    private _ci = { !isNull _x && alive _x } count HMT_TARGET;
    diag_log format ["HARMATTAN_PB_RESET hommes=%1 cibles=%2/%3 grps=%4", _vivants, _ci, count HMT_TARGET, count HMT_FOB_GRP];
    (format ["HARMATTAN_PB_RESET %1#%2#%3", _vivants, _ci, count HMT_TARGET]) call HMT_EMIT;
};


// ============================================================ COHORTE NOMMEE (correctif 1)
// `total_force` est un compteur MENTEUR : le monde vivant fait naitre des hommes pendant la
// bataille (caserne, convois) et la force MONTE alors qu'on perd des gens (mesure : 564 -> 579).
// On fige donc la liste des defenseurs a t0 et on compte les SURVIVANTS de cette liste-la.
// Immunise aux naissances ; immunise aussi au ramassage des corps (un mort efface devient null).
HMT_PB_COHORTE = {
    private _c = (HMT_FOB_MEN apply { _x select 0 }) select { !isNull _x && alive _x };
    HMT_PB_STATE set ["cohorte", _c];
    HMT_PB_STATE set ["cohorte_n", count _c];
    diag_log format ["HARMATTAN_PB_COHORTE n=%1", count _c];
    (format ["HARMATTAN_PB_COHORTE %1", count _c]) call HMT_EMIT;
};

// pertes = membres de la cohorte qui ne sont plus la. Rend aussi les pertes ennemies du banc.
HMT_PB_PERTES = {
    private _c = HMT_PB_STATE getOrDefault ["cohorte", []];
    private _n0 = HMT_PB_STATE getOrDefault ["cohorte_n", 0];
    private _viv = _c select { !isNull _x && alive _x };
    private _perdus = _n0 - (count _viv);
    private _atk = if (isNil "HMT_PB_ATK") then { [] } else { HMT_PB_ATK };
    private _atk_viv = _atk select { !isNull _x && alive _x };
    private _atk_perdus = (count _atk) - (count _atk_viv);
    private _ci = { !isNull _x && alive _x } count HMT_TARGET;
    diag_log format ["HARMATTAN_PB_PERTES amies=%1/%2 ennemies=%3/%4 cibles=%5", _perdus, _n0, _atk_perdus, count _atk, _ci];
    (format ["HARMATTAN_PB_PERTES %1#%2#%3#%4#%5", _perdus, _n0, _atk_perdus, count _atk, _ci]) call HMT_EMIT;
};


// ============================================================ SAPE (correctif angle mort)
// Une cible-BATIMENT ne tombe pas sous les balles. Elle tombe si des assaillants restent a son
// pied SANS opposition. La condition « aucun defenseur vivant a moins de 40 m » est le coeur du
// banc : c'est elle qui rend RENFORCER/MASSER payant et TENIR-ailleurs couteux.
HMT_PB_SAPE_ON = false;
HMT_PB_SAPE = {
    if (HMT_PB_SAPE_ON) exitWith {};
    HMT_PB_SAPE_ON = true;
    [] spawn {
        while { HMT_PB_SAPE_ON } do {
            {
                private _t = _x;
                if (!isNull _t && { alive _t } && { !(_t isKindOf "CAManBase") }) then {
                    // rayon porte a 40 m : mesure du 11/08, l'assaut met >6 min a passer sous 25 m.
                    private _sap = count (HMT_PB_ATK select { !isNull _x && alive _x && (_x distance2D _t) < 40 });
                    if (_sap >= 3) then {
                        private _def = count (allUnits select { side _x == east && alive _x && (_x distance2D _t) < 40 });
                        // SUPERIORITE LOCALE, pas absence : deux hommes ne doivent pas bloquer
                        // trente. Renforcer casse le rapport -> la sape s'arrete. C'est le
                        // couplage qui rend l'ordre de l'officier mesurable.
                        if (_sap >= 3 * _def) then {
                            private _d = (damage _t) + 0.03 * (_sap min 6);
                            _t setDamage (_d min 1);
                            if (_d >= 1) then {
                                diag_log format ["HARMATTAN_PB_CIBLE_TOMBEE %1", _t getVariable ["HMT_TARGET", "?"]];
                                (format ["HARMATTAN_PB_CIBLE_TOMBEE %1", _t getVariable ["HMT_TARGET", "?"]]) call HMT_EMIT;
                            };
                        };
                    };
                };
            } forEach HMT_TARGET;
            sleep 10;
        };
    };
};

// ============================================================ ATTAQUE
// [[indices de FOB vises], nb d'assaillants par FOB, viser_les_cibles] call HMT_PB_ATTACK
HMT_PB_ATTACK = {
    // CORRECTIF 3 : 16 assaillants contre une garnison de 30-43 appuyee par des KORD statiques,
    // c'est une charge suicide — mesure : ils meurent en 80 s sans meme apparaitre au SITREP.
    // On triple, on les fait naitre plus pres (200 m au lieu de 260), et on leur donne une
    // composition qui mord (fusiliers + FM + AT) au lieu de fusiliers seuls.
    params ["_cibles_fob", ["_n", 48], ["_viser_cibles", true]];
    // `_viser_cibles` accepte true/false OU un nom de cible. SQF n'accepte qu'un BOOLEEN dans
    // un `if` : passer la chaine directement tuait le script avant la sape (bug du 11/08).
    private _nom_cible = if (_viser_cibles isEqualType "") then { _viser_cibles } else { "" };
    private _viser = if (_viser_cibles isEqualType "") then { true } else { _viser_cibles };
    private _typs = ["rhsusf_army_ocp_rifleman", "rhsusf_army_ocp_autorifleman", "rhsusf_army_ocp_riflemanat"];
    private _fab = {
        params ["_grp", "_p", "_i"];
        private _t = _typs select (if (_i mod 5 == 4) then { 2 } else { if (_i mod 5 == 3) then { 1 } else { 0 } });
        private _u = _grp createUnit [_t, _p, [], 0, "FORM"];
        if (isNull _u) then { _u = _grp createUnit ["B_soldier_F", _p, [], 0, "FORM"]; };
        _u
    };
    if (isNil "HMT_PB_ATK") then { HMT_PB_ATK = []; };
    if (isNil "HMT_PB_ATKG") then { HMT_PB_ATKG = []; };

    {
        private _idx = _x;
        private _o = HMT_FOB_ANCHORS select _idx;
        private _grp = createGroup west; HMT_PB_ATKG pushBack _grp;
        private _k = 0;
        while { _k < _n } do {
            private _p = [(_o select 0) - 200 + (_k mod 8) * 12, (_o select 1) - 190 + (floor (_k / 8)) * 12, 0];
            private _u = [_grp, _p, _k] call _fab;
            if (!isNull _u) then { _u setSkill 0.85; _u allowFleeing 0; HMT_PB_ATK pushBack _u; };
            _k = _k + 1;
        };
        _grp setBehaviour "COMBAT"; _grp setCombatMode "RED"; _grp setSpeedMode "FULL"; _grp allowFleeing 0;
        private _wp = _grp addWaypoint [_o, 25]; _wp setWaypointType "SAD"; _wp setWaypointBehaviour "COMBAT";
        _grp move _o;
    } forEach _cibles_fob;

    // l'audit du score l'exige : la pression doit menacer les CIBLES VITALES (0.125 chacune),
    // pas seulement le terrain (0.010 par FOB, sous le bruit).
    if (_viser) then {
        // nommer la cible ("QG","CASERNE","HVT","OTAGE","INTEL","DEPOT") rend l'episode REPRODUCTIBLE.
        private _vis = HMT_TARGET select { !isNull _x && alive _x };
        if (_nom_cible != "") then {
            private _f = _vis select { (_x getVariable ["HMT_TARGET",""]) == _nom_cible };
            if (count _f > 0) then { _vis = _f };
        };
        if (count _vis > 0) then {
            private _grp = createGroup west; HMT_PB_ATKG pushBack _grp;
            private _cible = _vis select 0;
            private _o = getPosATL _cible;
            private _k = 0;
            while { _k < 24 } do {
                private _p = [(_o select 0) - 120 + (_k mod 6) * 10, (_o select 1) + 110 - (floor (_k / 6)) * 10, 0];
                private _u = [_grp, _p, _k] call _fab;
                if (!isNull _u) then { _u setSkill 0.9; _u allowFleeing 0; HMT_PB_ATK pushBack _u; };
                _k = _k + 1;
            };
            _grp setBehaviour "COMBAT"; _grp setCombatMode "RED"; _grp setSpeedMode "FULL"; _grp allowFleeing 0;
            private _wp = _grp addWaypoint [_o, 12]; _wp setWaypointType "MOVE"; _wp setWaypointBehaviour "COMBAT";
            private _wp2 = _grp addWaypoint [_o, 12]; _wp2 setWaypointType "SAD";
            _grp move _o;
            call HMT_PB_SAPE;                       // la sape ne tourne que pendant un episode
        };
    };

    // l'ennemi est VU (sinon knowsAbout reste bas et le SITREP ne voit aucune menace)
    { private _r = _x;
      { _x reveal [_r, 2.5] } forEach (allUnits select {side _x == east && alive _x && _x distance _r < 700});
    } forEach HMT_PB_ATK;

    diag_log format ["HARMATTAN_PB_ATTACK fobs=%1 assaillants=%2 cible=%3", _cibles_fob, count HMT_PB_ATK, _nom_cible];
    (format ["HARMATTAN_PB_ATTACK %1#%2", count HMT_PB_ATK, _nom_cible]) call HMT_EMIT;
};

// ============================================================ EXECUTION D'UN ORDRE
// [verbe, index de FOB] call HMT_PB_ORDER
// Sans executeur reel, tous les ordres se valent et le banc mesure du bruit.
HMT_PB_ORDER = {
    params ["_verbe", "_idx"];
    private _o = HMT_FOB_ANCHORS select _idx;

    // groupes rattaches a un FOB donne = ceux dont le chef est a moins de 150 m de l'ancre
    private _grpDe = {
        params ["_anc"];
        HMT_FOB_GRP select { !isNull _x && {count units _x > 0} && {(leader _x) distance2D _anc < 150} }
    };

    private _bouge = 0;
    switch (toUpper _verbe) do {
        case "TENIR": {
            { _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach ([_o] call _grpDe);
        };
        case "RENFORCER": {
            // les 2 FOB calmes les plus proches envoient CHACUN un groupe
            private _dist = [];
            { private _i = _forEachIndex; if (_i != _idx) then { _dist pushBack [_o distance2D _x, _i] }; } forEach HMT_FOB_ANCHORS;
            _dist sort true;
            {
                private _src = HMT_FOB_ANCHORS select (_x select 1);
                private _g = [_src] call _grpDe;
                if (count _g > 1) then {
                    private _grp = _g select 0;
                    _grp setBehaviour "AWARE"; _grp setCombatMode "RED"; _grp setSpeedMode "FULL";
                    { deleteWaypoint _x } forEach (reverse (waypoints _grp));
                    private _wp = _grp addWaypoint [_o, 30]; _wp setWaypointType "MOVE";
                    _grp move _o; _bouge = _bouge + count units _grp;
                };
            } forEach (_dist select [0, 2]);
        };
        case "QRF": {
            // la reserve mobile (fob_life) fonce sur le FOB
            if (!isNil "HMT_LIFE_OBJ") then {
                private _veh = HMT_LIFE_OBJ select { !isNull _x && {alive _x} && {_x isKindOf "Car" || _x isKindOf "Truck"} };
                { private _g = group (driver _x);
                  if (!isNull _g) then {
                      { deleteWaypoint _y } forEach (reverse (waypoints _g));
                      private _wp = _g addWaypoint [_o, 40]; _wp setWaypointType "MOVE";
                      _g setBehaviour "AWARE"; _g setSpeedMode "FULL"; _g move _o; _bouge = _bouge + count units _g;
                  };
                } forEach (_veh select [0, 2]);
            };
        };
        case "MASSER": {
            // les 4 FOB les plus proches envoient chacun un groupe : on concentre
            private _dist = [];
            { private _i = _forEachIndex; if (_i != _idx) then { _dist pushBack [_o distance2D _x, _i] }; } forEach HMT_FOB_ANCHORS;
            _dist sort true;
            {
                private _src = HMT_FOB_ANCHORS select (_x select 1);
                private _g = [_src] call _grpDe;
                if (count _g > 1) then {
                    private _grp = _g select 0;
                    _grp setBehaviour "AWARE"; _grp setCombatMode "RED"; _grp setSpeedMode "FULL";
                    { deleteWaypoint _x } forEach (reverse (waypoints _grp));
                    private _wp = _grp addWaypoint [_o, 30]; _wp setWaypointType "MOVE";
                    _grp move _o; _bouge = _bouge + count units _grp;
                };
            } forEach (_dist select [0, 4]);
        };
        case "REPLIER": {
            // la garnison decroche vers le FOB calme le plus proche
            private _dist = [];
            { private _i = _forEachIndex; if (_i != _idx) then { _dist pushBack [_o distance2D _x, _i] }; } forEach HMT_FOB_ANCHORS;
            _dist sort true;
            private _refuge = HMT_FOB_ANCHORS select ((_dist select 0) select 1);
            {
                _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
                { deleteWaypoint _y } forEach (reverse (waypoints _x));
                private _wp = _x addWaypoint [_refuge, 30]; _wp setWaypointType "MOVE";
                _x move _refuge; _bouge = _bouge + count units _x;
            } forEach ([_o] call _grpDe);
        };
    };
    diag_log format ["HARMATTAN_PB_ORDER %1 fob=%2 hommes_engages=%3", _verbe, _idx, _bouge];
    (format ["HARMATTAN_PB_ORDER %1#%2", _verbe, _bouge]) call HMT_EMIT;
};

diag_log "HARMATTAN_PB charge (RESET / ATTACK / ORDER)";
"HARMATTAN_PB_LOADED 1" call HMT_EMIT;
