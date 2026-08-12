// sonde_radio.sqf v2 — LA RADIO PREND-ELLE, ET SOUS QUELLE CONDITION ?
//
// Le bras natif du banc de l etage 1 a tire 260, 206, 0, 0 coups sur quatre runs dont
// l empreinte du monde est IDENTIQUE. Le seul marqueur qui separe est l etat d entree du
// groupe, lu par `unitReady` SEPT SECONDES AVANT l ordre de feu : 0/3 prets quand ca tire,
// 3/3 prets quand ca ne tire pas. ⟨protocole depose : PROTOCOLE_SONDE_RADIO.md⟩
// RIEN DU BANC N EST TOUCHE.
//
// ⚠️ POURQUOI IL Y A UNE v2, ET CE QUE LA v1 A COUTE. La v1 posait UN muret et AUCUN ennemi
// derriere. Son controle positif — `doSuppressiveFire`, la variante directe — a rendu ZERO
// coup sur trois repetitions. Ce n etait pas une reponse, c etait une sonde aveugle : des
// hommes n appuient pas sur du vide. Le banc, lui, pose SIX murets et SIX defenseurs derriere.
// Une sonde qui ne reproduit pas le monde du banc ne mesure pas le banc.
// ⟨R13 : cet amendement RESSERRE — il rend la sonde plus fidele — et il est enonce sans
//  reference a aucune grandeur : seul le controle positif avait parle, et aucun bloc RADIO
//  n avait tourne.⟩
//
// ⚠️ CE QUI FERAIT ECHOUER LA SONDE — ecrit avant, et lu avant la grandeur :
//   · CONTROLE DE VISIBILITE : les appuis doivent VOIR les murets. Sinon on ne lance rien.
//   · CONTROLE POSITIF : `doSuppressiveFire` doit faire tirer dans LES DEUX etats (>= 10/12).
//   · CONTROLE D ETAT : chaque repetition RELIT son etat d entree ; etat lu != etat voulu ->
//     repetition REFUSEE, non comptee. Un etat qu on croit poser sans le verifier n est pas
//     un facteur, c est une intention.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|SR|debut|2" call HMT_LOG;

HMT_DOTER = {
    params ["_u"];
    if (_u getVariable ["sr_dote", false]) exitWith {};
    _u setVariable ["sr_dote", true];
    _u addEventHandler ["Fired", { (_this select 0) setVehicleAmmo 1 }];   // lint:ok
    _u setVehicleAmmo 1;                                                   // lint:ok
};

// un des six terrains candidats deposes du banc — pas un point tire au hasard comme en v1.
HMT_BASE = [1734, 5391, 0];

HMT_REPET = {
    params ["_etat", "_cmd", "_i"];
    private _mur = []; private _def = []; private _app = [];

    // ─── LE MONDE DU BANC, COPIE : six murets, un par defenseur, face a l appui (plein est).
    {
        private _p = HMT_BASE vectorAdd [_x + 1.5, 0, 0];
        private _m = createVehicle ["Land_BagFence_Long_F", _p, [], 0, "CAN_COLLIDE"];
        _m setPosATL _p; _m setDir 0; _m allowDamage false;
        _mur pushBack _m;
    } forEach [-40, -24, -8, 8, 24, 40];

    private _gD = createGroup east;
    {
        private _p = HMT_BASE vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setUnitPos "MIDDLE";
        _def pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];

    private _g = createGroup west;
    {
        private _p = HMT_BASE vectorAdd [150, _x, 0];
        private _u = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u disableAI "AUTOTARGET"; _u disableAI "FSM";
        _u setCombatMode "BLUE"; _u setBehaviour "COMBAT";
        _u setUnitPos "UP"; _u setDir 270;
        _u setVariable ["sr_n", 0];
        _u addEventHandler ["Fired", {
            (_this select 0) setVariable ["sr_n", ((_this select 0) getVariable ["sr_n",0]) + 1] }];
        _app pushBack _u;
    } forEach [-10, 0, 10];
    sleep 3;
    { [_x] call HMT_DOTER } forEach _app;

    // ─── CONTROLE DE VISIBILITE, avant tout ordre : l appui voit-il la LIGNE qu il doit battre ?
    // ⚠️ v2.1 — LA v2 VISAIT LE PIED DU MURET, que le muret lui-meme masque. Elle rendait
    // `vue|0` alors que les hommes tiraient 219 coups : un controle qui refuse une repetition
    // parfaitement valide. C est la meme faute que le second chemin du geste n°3 — verifier
    // une abstraction commode au lieu de la propriete que le mecanisme emploie. Ce que l appui
    // doit voir, c est l HOMME derriere le muret ; c est aussi ce que la chasse de sites du
    // banc mesure (`vueDV`, oeil a oeil).
    private _vue = [objNull, "VIEW"] checkVisibility [eyePos (_app select 1), eyePos (_def select 3)];

    // ─── POSER L ETAT D ENTREE
    if (_etat == "OCCUPE") then {
        // un ordre de deplacement PENDANT, que `PATH` coupe rend inexecutable : l homme reste
        // occupe indefiniment. C est l etat qu avaient les sessions 1 et 2.
        { _x doMove (HMT_BASE vectorAdd [300, 0, 0]) } forEach _app;
    } else {
        { doStop _x } forEach _app;
        for "_k" from 1 to 20 do {
            if (({ unitReady _x } count _app) == 3) exitWith {};
            sleep 1;
        };
    };
    sleep 4;

    // ─── LE CONTROLE D ETAT, lu AVANT l ordre — comme au banc, ou la lecture d entree
    // (ligne 452) precede l ordre (ligne 480) de sept secondes.
    private _prets = { unitReady _x } count _app;
    private _voulu = if (_etat == "OCCUPE") then { 0 } else { 3 };
    private _conforme = (_prets == _voulu) && (_vue > 0);

    { _x setCombatMode "RED"; _x enableAI "TARGET"; _x enableAI "FIREWEAPON" } forEach _app;
    { _x setVariable ["sr_n", 0] } forEach _app;

    private _t0 = time;
    while { time - _t0 < 60 } do {
        private _c = _mur select (floor (random (count _mur)));
        if (_cmd == "RADIO") then { { _x commandSuppressiveFire _c } forEach _app }
                             else { { _x doSuppressiveFire _c } forEach _app };
        sleep 4;
    };

    private _coups = 0;
    { _coups = _coups + (_x getVariable ["sr_n", 0]) } forEach _app;
    private _tireurs = { (_x getVariable ["sr_n", 0]) > 0 } count _app;
    private _reussi = if (_tireurs == 3) then { 1 } else { 0 };

    (format ["HMT|SR|rep|%1|etat|%2|cmd|%3|prets|%4|vue|%5|conforme|%6|coups|%7|tireurs|%8|reussi|%9",
             _i, _etat, _cmd, _prets, (round (_vue * 100)) / 100, _conforme,
             _coups, _tireurs, _reussi]) call HMT_LOG;

    // RENDRE LES GROUPES, pas seulement les hommes — la panne du 235e accrochage.
    { deleteVehicle _x } forEach (_app + _def);
    { deleteVehicle _x } forEach _mur;
    sleep 1;
    { if (count (units _x) == 0) then { deleteGroup _x } } forEach [_g, _gD];
    [_conforme, _reussi]
};

[] spawn {
    sleep 25;
    private _res = createHashMap;
    {
        _x params ["_etat", "_cmd"];
        private _cle = _etat + "/" + _cmd;
        private _ok = 0; private _n = 0; private _refus = 0;
        for "_i" from 1 to 12 do {
            private _r = [_etat, _cmd, _i] call HMT_REPET;
            if (_r select 0) then { _n = _n + 1; _ok = _ok + (_r select 1) }
            else { _refus = _refus + 1 };
        };
        _res set [_cle, [_ok, _n, _refus]];
        (format ["HMT|SR|BLOC|%1|reussites|%2|sur|%3|refusees|%4", _cle, _ok, _n, _refus]) call HMT_LOG;
    } forEach [["OCCUPE","DIRECT"], ["OISIF","DIRECT"], ["OCCUPE","RADIO"], ["OISIF","RADIO"]];

    // ─── LES CONTROLES SE LISENT AVANT LA GRANDEUR
    private _cd = _res getOrDefault ["OCCUPE/DIRECT", [0,0,0]];
    private _od = _res getOrDefault ["OISIF/DIRECT",  [0,0,0]];
    private _cr = _res getOrDefault ["OCCUPE/RADIO",  [0,0,0]];
    private _or = _res getOrDefault ["OISIF/RADIO",   [0,0,0]];

    if ((_cd select 0) < 10 || {(_od select 0) < 10}) exitWith {
        (format ["HMT|SR|SONDE_EN_PANNE|direct|occupe|%1|oisif|%2|le_controle_positif_tombe",
                 _cd select 0, _od select 0]) call HMT_LOG;
        "HMT|SR|AUCUNE_LECTURE|1" call HMT_LOG;
        "HMT|SR|TERMINE|1" call HMT_LOG;
    };
    "HMT|OK|sr_controle_positif|1" call HMT_LOG;

    private _a = _cr select 0; private _b = _or select 0;
    private _verdict = if ((_a >= 10 && _b <= 2) || {_b >= 10 && _a <= 2}) then { "CONDITION_CONFIRMEE" }
        else { if (_a <= 2 && _b <= 2) then { "RADIO_NE_PREND_JAMAIS" }
        else { if (_a >= 10 && _b >= 10) then { "RADIO_PREND_TOUJOURS" } else { "PAS_DE_SEPARATION" }}};
    (format ["HMT|SR|VERDICT|%1|radio_occupe|%2|sur|%3|radio_oisif|%4|sur|%5",
             _verdict, _a, _cr select 1, _b, _or select 1]) call HMT_LOG;
    "HMT|SR|TERMINE|1" call HMT_LOG;
};
