// orch_features.sqf — calcule les 10 features de orchestration_arma_voyant.pt (recette HANDOFF).
// Ordre EXACT : [0]dist [1]visible(LOS) [2]ennemi-derriere-couvert [3]ennemi-retranche
//   [4]mon-exposition [5]terrain-ouvert [6]feu-entrant [7]grenades/2 [8]fumis/2 [9]allies-proches.
// Reutilise : coque 12-rayons (exposition), checkVisibility (LOS), getSuppression (feu entrant), inventaire.
if (!isServer) exitWith {};

// grenades/fumis detectees PAR CONFIG (robuste RHS+vanilla+mods) : compte [grenades_frag, fumis]
HMT_COUNT_THROW = {
    params ["_u"];
    private _g = 0; private _s = 0;
    {
        private _am = getText (configFile >> "CfgMagazines" >> _x >> "ammo");
        if (_am isKindOf ["SmokeShell", configFile >> "CfgAmmo"]) then { _s = _s + 1; }
        else { if (_am isKindOf ["GrenadeHand", configFile >> "CfgAmmo"]) then { _g = _g + 1; }; };
    } forEach (magazines _u);
    [_g, _s]
};

// coque 12 rayons horizontaux autour de _u (origine getPosASL + 0.9, longueur _len) -> fraction bloquee 0..1
HMT_SHELL12 = {
    params ["_u", ["_len", 8]];
    private _o = (getPosASL _u) vectorAdd [0,0,0.9];
    private _blk = 0;
    for "_k" from 0 to 11 do {
        private _a = _k * 30;
        private _p1 = _o vectorAdd [_len * sin _a, _len * cos _a, 0];
        if (count (lineIntersectsSurfaces [_o, _p1, _u, objNull, true, 1]) > 0) then { _blk = _blk + 1; };
    };
    _blk / 12
};

// vecteur des 10 features pour l'unite _u
// LOS coherente (positions ASL + hauteur) entre _a et _b
HMT_LOS = {
    params ["_a", "_b"];
    [_a, "VIEW"] checkVisibility [(getPosASL _a) vectorAdd [0,0,1.5], (getPosASL _b) vectorAdd [0,0,1.2]]
};

HMT_ORCH_FEATS = {
    params ["_u"];
    // perception SITUATIONNELLE : reference l'ennemi que l'unite peut TRAITER
    //   = le plus proche VISIBLE (LOS>0.3) parmi les connus ; sinon le plus proche connu (fallback -> couvert/grenade).
    private _e = _u findNearestEnemy _u;
    if (isNull _e) then { _e = _u findNearestEnemy (getPosATL _u); };
    private _bestD = 1e9; private _visE = objNull;
    {
        if (((side _x) getFriend (side _u)) < 0.6 && {alive _x} && {(_u knowsAbout _x) > 1}) then {
            private _d = _u distance _x;
            if (_d < _bestD && {([_u, _x] call HMT_LOS) > 0.3}) then { _bestD = _d; _visE = _x; };
        };
    } forEach (_u nearEntities [["Man"], 250]);
    if (!isNull _visE) then { _e = _visE; };
    private _dist = 1; private _vis = 0; private _behind = 0; private _entr = 0; private _openg = 0;
    if (!isNull _e) then {
        _dist = ((_u distance _e) min 300) / 300;
        _vis  = [_u, _e] call HMT_LOS;
        private _known = _u knowsAbout _e;
        private _dm = _u distance _e;
        // "derriere couvert" (=> grenade) n'a de sens qu'a PORTEE DE JET (~45 m) ; au-dela, ennemi non-vu = retranche/loin, pas grenade-able
        if (_known > 1 && {_dm < 45}) then { _behind = 1 - _vis; };
        // "retranche" (=> flanc) : ennemi immobile + connu + PAS a portee de grenade (loin & couvert)
        if ((vectorMagnitude velocity _e < 1) && {_known >= 1.5} && {_dm >= 45}) then { _entr = 0.4 + 0.6 * (1 - _vis); };
        private _o  = (getPosASL _u) vectorAdd [0,0,0.9];
        private _pe = (getPosASL _e) vectorAdd [0,0,0.9];
        private _uv = vectorNormalized (_pe vectorDiff _o);
        private _end = _o vectorAdd (_uv vectorMultiply 30);
        private _hit = lineIntersectsSurfaces [_o, _end, _u, _e, true, 1];
        _openg = if (count _hit == 0) then { 1 } else { (((_hit select 0) select 0) vectorDistance _o) / 30 };
    };
    private _expo   = 1 - ([_u] call HMT_SHELL12);
    private _fire   = ((getSuppression _u) max 0) min 1;
    private _thr    = [_u] call HMT_COUNT_THROW;
    private _gren   = ((_thr select 0) / 2) min 1;
    private _smoke  = ((_thr select 1) / 2) min 1;
    private _allies = ((({(side _x == side _u) && alive _x && _x != _u} count (_u nearEntities [["Man"], 30]))) / 6) min 1;
    [_dist, _vis, _behind, _entr, _expo, _openg, _fire, _gren, _smoke, _allies]
};

// dump : emet le vecteur 10-features des _n unites east vivantes proches de _ctr (pour le smoke-test parite)
HMT_ORCH_DUMP = {
    params [["_ctr",[4279,3856,0]], ["_n",10]];
    private _men = (allUnits select { alive _x && (side _x == east) && (_x distance _ctr < 140) });
    _men = _men select [0, _n];
    {
        private _f = [_x] call HMT_ORCH_FEATS;
        private _fr = _f apply { (round (_x * 100)) / 100 };
        diag_log format ["HARMATTAN_FEAT %1 known=%2 supp=%3 v=%4", _forEachIndex, round (_x knowsAbout (_x findNearestEnemy _x)), round ((getSuppression _x)*100)/100, _fr];
    } forEach _men;
    diag_log format ["HARMATTAN_FEATDONE n=%1", count _men];
    count _men
};

// snapshot : les _n unites east au CONTACT proches de _ctr -> UNE ligne [vecteurs] | [netIds] (pont natif, 1 aller-retour)
HMT_ORCH_SNAP = {
    params [["_ctr", [0,0,0]], ["_n", 8], ["_sd", east]];
    private _men = (allUnits select { alive _x && side _x == _sd && (_x distance _ctr) < 240 && !isNull (_x findNearestEnemy _x) });
    _men = _men select [0, _n];
    private _vs = _men apply { ([_x] call HMT_ORCH_FEATS) apply { (round (_x * 1000)) / 1000 } };
    private _ids = _men apply { netId _x };
    private _line = format ["HARMATTAN_ORCH %1 | %2", _vs, _ids];
    if (!isNil "HMT_EMIT") then { _line call HMT_EMIT } else { diag_log _line };
    count _men
};

diag_log "HARMATTAN_ORCHFEAT charge (FEATS / DUMP / SNAP)";
