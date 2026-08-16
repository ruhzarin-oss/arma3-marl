// cout_par_grandeur.sqf — LE COUT DE CHAQUE GRANDEUR, UNE PAR UNE.
//
// La mesure globale a montre : ~0,27 ms par grandeur ajoutee pour 260 hommes. Mais c est une
// moyenne, et une moyenne ne repartit rien. Certaines lectures sont surement dix fois plus
// cheres que d autres — ce sont elles qui doivent descendre d horloge, pas les autres.
//
// Tout est chronometre en contexte NON ORDONNANCE via isNil { }. ⟨la mesure d avant, faite
// dans un spawn, annonçait 459 ms la ou la production en fait 6,7 : elle comptait les
// attentes entre images.⟩ Controle de vraisemblance : getPosASL sert d etalon, on connait
// son ordre de grandeur.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];
    private _gE = createGroup east; private _gW = createGroup west;
    HMT_F = [];
    for "_i" from 0 to 259 do {
        private _p = _base vectorAdd [(random 700) - 350, (random 700) - 350, 0];
        private _u = ((if (_i % 2 == 0) then {_gE} else {_gW})
                      createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}), _p, [], 0, "NONE"]);
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u setVariable ["hmt_id", _i + 1];
        HMT_F pushBack _u;
    };
    sleep 3;
    (format ["HMT|K|foule|%1", count HMT_F]) call HMT_LOG;

    HMT_CH = {
        params ["_b", "_n"];
        private _t = 0;
        isNil { private _t0 = diag_tickTime; for "_k" from 1 to _n do { call _b }; _t = (diag_tickTime - _t0) * 1000 / _n; };
        round (_t * 1000) / 1000
    };
    private _T = 25;

    // ---------- grandeurs PAR HOMME ----------
    private _res = [];
    {
        private _nom = _x select 0; private _b = _x select 1;
        private _ms = [{ { [_x] call HMT_BLOC } forEach HMT_F }, 1] call HMT_CH;   // amorce
        HMT_BLOC = _b;
        _ms = [{ { [_x] call HMT_BLOC } forEach HMT_F }, _T] call HMT_CH;
        _res pushBack [_nom, _ms];
        (format ["HMT|K|par_homme|%1|%2", _nom, _ms]) call HMT_LOG;
    } forEach [
        ["_vide_etalon",     { }],
        ["getPosASL",        { getPosASL (_this select 0) }],
        ["getPosATL",        { getPosATL (_this select 0) }],
        ["velocity",         { velocity (_this select 0) }],
        ["speed",            { speed (_this select 0) }],
        ["getDir",           { getDir (_this select 0) }],
        ["vectorDir",        { vectorDir (_this select 0) }],
        ["vectorUp",         { vectorUp (_this select 0) }],
        ["eyeDirection",     { eyeDirection (_this select 0) }],
        ["eyePos",           { eyePos (_this select 0) }],
        ["aimPos",           { aimPos (_this select 0) }],
        ["alive",            { alive (_this select 0) }],
        ["damage",           { damage (_this select 0) }],
        ["getAllHitPoints",  { getAllHitPointsDamage (_this select 0) }],
        ["lifeState",        { lifeState (_this select 0) }],
        ["unitPos",          { unitPos (_this select 0) }],
        ["stance",           { stance (_this select 0) }],
        ["getFatigue",       { getFatigue (_this select 0) }],
        ["getSuppression",   { getSuppression (_this select 0) }],
        ["captive",          { captive (_this select 0) }],
        ["currentWeapon",    { currentWeapon (_this select 0) }],
        ["currentMuzzle",    { currentMuzzle (_this select 0) }],
        ["currentWeaponMode",{ currentWeaponMode (_this select 0) }],
        ["ammo_courant",     { (_this select 0) ammo (currentWeapon (_this select 0)) }],
        ["magazines",        { magazines (_this select 0) }],
        ["magazinesAmmoFull",{ magazinesAmmoFull (_this select 0) }],
        ["weapons",          { weapons (_this select 0) }],
        ["getUnitLoadout",   { getUnitLoadout (_this select 0) }],
        ["behaviour",        { behaviour (_this select 0) }],
        ["combatMode",       { combatMode (_this select 0) }],
        ["speedMode",        { speedMode (_this select 0) }],
        ["formation",        { formation (group (_this select 0)) }],
        ["currentCommand",   { currentCommand (_this select 0) }],
        ["assignedTarget",   { assignedTarget (_this select 0) }],
        ["currentWaypoint",  { currentWaypoint (group (_this select 0)) }],
        ["group",            { group (_this select 0) }],
        ["leader",           { leader (group (_this select 0)) }],
        ["rank",             { rank (_this select 0) }],
        ["formationPosition",{ formationPosition (_this select 0) }],
        ["vehicle",          { vehicle (_this select 0) }],
        ["objectParent",     { objectParent (_this select 0) }],
        ["getVariable",      { (_this select 0) getVariable ["hmt_id", -1] }],
        ["getTerrainHeight", { getTerrainHeightASL (getPosATL (_this select 0)) }],
        ["surfaceNormal",    { surfaceNormal (getPosATL (_this select 0)) }],
        ["surfaceType",      { surfaceType (getPosATL (_this select 0)) }],
        ["surfaceIsWater",   { surfaceIsWater (getPosATL (_this select 0)) }],
        ["str_10_nombres",   { str [1,2.5,3.5,4.5,1,0,0,180,0,0] }]
    ];

    // ---------- grandeurs PAR PAIRE — le sujet des aretes ----------
    // On mesure sur 400 paires (20 observateurs x 20 cibles) puis on rapporte a la paire.
    HMT_OBS = HMT_F select [0, 20];
    HMT_CIB = HMT_F select [130, 20];
    private _np = 400;
    {
        private _nom = _x select 0;
        HMT_BLOC2 = _x select 1;
        private _ms = [{ { private _o = _x; { [_o, _x] call HMT_BLOC2 } forEach HMT_CIB } forEach HMT_OBS }, _T] call HMT_CH;
        (format ["HMT|K|par_paire|%1|%2|us_par_paire|%3", _nom, _ms,
                 round (_ms / _np * 1000000) / 1000]) call HMT_LOG;
    } forEach [
        ["distance",       { (_this select 0) distance (_this select 1) }],
        ["knowsAbout",     { (_this select 0) knowsAbout (_this select 1) }],
        ["targetKnowledge",{ (_this select 0) targetKnowledge (_this select 1) }],
        ["checkVisibility",{ [objNull,"VIEW"] checkVisibility [eyePos (_this select 0), aimPos (_this select 1)] }],
        ["lineIntersects", { lineIntersectsSurfaces [eyePos (_this select 0), aimPos (_this select 1),
                                                     (_this select 0), (_this select 1), true, 1, "VIEW", "FIRE"] }]
    ];

    // ---------- le tri spatial : combien coute-t-il de TROUVER les paires proches ? ----------
    private _ms = [{
        { private _o = _x; private _proches = HMT_F inAreaArray [getPosATL _o, 200, 200] } forEach HMT_OBS;
    }, _T] call HMT_CH;
    (format ["HMT|K|tri|inAreaArray_200m|%1|pour|%2|observateurs", _ms, count HMT_OBS]) call HMT_LOG;

    private _ms2 = [{
        { private _o = _x; private _proches = (nearestObjects [getPosATL _o, ["CAManBase"], 200]) } forEach HMT_OBS;
    }, _T] call HMT_CH;
    (format ["HMT|K|tri|nearestObjects_200m|%1|pour|%2|observateurs", _ms2, count HMT_OBS]) call HMT_LOG;

    "HMT|OK|cout_par_grandeur|1" call HMT_LOG;
};
"HMT|OK|cout_lance|1" call HMT_LOG;
