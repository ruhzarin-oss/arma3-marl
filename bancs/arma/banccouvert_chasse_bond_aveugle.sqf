// chasse_bond_aveugle.sqf — QUATRE COULOIRS NEUFS POUR LE GESTE N°1, CHOISIS EN AVEUGLE.
//
// ⚠️ CE QUE « EN AVEUGLE » VEUT DIRE ICI, ET POURQUOI C EST LA CLAUSE LA PLUS IMPORTANTE
// DU FICHIER. La premiere campagne a rendu huit ecarts, de +5,6 a +23,6 points. Si ce
// chasseur les regardait — ne serait-ce que pour « chercher des couloirs qui ressemblent aux
// bons » — il choisirait les familles ou l effet fut grand, et le certificat ne vaudrait plus
// rien. ⟨Fable, 10/08 : « ne le laisse pas favoriser les familles de couloirs ou l effet fut
// grand »⟩
//
// Ce script ne contient donc NI les coordonnees des huit couloirs anciens, NI leurs resultats.
// Il applique les criteres de la premiere chasse, MOT POUR MOT, sur un tirage neuf.
//
// LES CRITERES, REPRIS TELS QUELS DE LA PREMIERE CHASSE — aucun assoupli, aucun resserre :
//   · un OBJECTIF avec du couvert reel autour de lui — la ligne de defenseurs a quelque chose
//     a tenir ; mesure a la BOITE ENGLOBANTE (> 2 m large, 2 m haut, 0,5 m epais)
//     ⟨repris d Antistasi, fn_coverage, MIT · Copyright (c) 2023 Antistasi Ultimate Team⟩ ;
//   · une APPROCHE de 250 m ;
//   · de l ALTERNANCE le long du trajet : >= 70 % de pas servis en couvert, aucun trou de plus
//     de 2 pas (20 m — le sursis au sprint, derive du sursis MESURE de 4 s de l arc de tir) ;
//   · l approche est SOUS LA VUE de l objectif a >= 60 % — sinon le bond ne s achete rien,
//     personne ne voit venir. Mesure d oeil a oeil avec `checkVisibility`, entre deux hommes
//     REELS, dans un monde peuple ⟨la lecon du geometre v3 : mes rayons a 1,20 m donnaient
//     64 %, l oeil du moteur 32 % — c est la visibilite que l IA emploie pour decider⟩ ;
//   · 800 m d ECART entre couloirs retenus.
//
// ⚠️ ET UN ECART A DECLARER : les huit couloirs anciens ont ete choisis sur la CARTE au pas de
// 50 m. Cette chasse-ci est EN JEU. Les nouveaux couloirs seront donc mesures plus finement que
// les anciens — c est un progres, mais ce n est pas la meme procedure, et le dire vaut mieux
// que de le taire. La carte propose, seul le jeu admet.
//
// CE QUI FERAIT ECHOUER LA CHASSE — ecrit avant :
//   · CONTROLE POSITIF : trois points en bati dense doivent sortir tres bien servis.
//   · CONTROLE NUL : trois points en pleine mer doivent sortir a zero.
//   · Moins de quatre couloirs trouves : on le DIT, la campagne tourne sur ce qu on a, et on
//     ne compense pas. Stratis ne porterait pas plus de couloirs de cette forme, voila tout.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|CB|debut|1" call HMT_LOG;

HMT_COUVERT = {
    params ["_p"];
    private _n = 0;
    private _bruit = ["#crater","#crateronvehicle","#soundonvehicle","#particlesource",
                      "#lightpoint","#slop","#mark","HoneyBee","Mosquito","HouseFly",
                      "FxWindPollen1","ButterFly_random","Snake_random_F","Rabbit_F",
                      "FxWindGrass2","FxWindLeaf1","FxWindGrass1","FxWindLeaf3","FxWindLeaf2"];
    {
        private _t = typeOf _x;
        if (!(_t in _bruit) && {!(_x isKindOf "Man")} && {!(_x isKindOf "Bird")}
            && {!(_x isKindOf "WeaponHolder")}) then {
            private _bb = boundingBoxReal _x;
            private _a = _bb select 0; private _b = _bb select 1;
            if ((abs ((_b select 0) - (_a select 0))) > 2
                && {(abs ((_b select 1) - (_a select 1))) > 0.5}
                && {(abs ((_b select 2) - (_a select 2))) > 2}) then { _n = _n + 1 };
        };
    } forEach (nearestObjects [_p, [], 15]);
    _n
};

[] spawn {
    sleep 20;

    private _gD = createGroup east;
    HMT_OBS = _gD createUnit ["O_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_OBS allowDamage false; HMT_OBS disableAI "PATH"; HMT_OBS setBehaviour "COMBAT";
    private _gA = createGroup west;
    HMT_MAR = _gA createUnit ["B_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_MAR allowDamage false; HMT_MAR disableAI "PATH"; HMT_MAR setBehaviour "CARELESS";
    sleep 3;
    "HMT|CB|corps|poses" call HMT_LOG;

    HMT_VUE = {
        params ["_a", "_b"];
        HMT_OBS setPosATL _a; HMT_MAR setPosATL _b;
        sleep 0.05;
        ([objNull, "VIEW"] checkVisibility [eyePos HMT_OBS, eyePos HMT_MAR]) > 0
    };

    HMT_LIRE = {
        params ["_obj", "_dep"];
        private _d = _dep distance2D _obj;
        private _pas = round (_d / 10) max 1;
        private _servis = 0; private _vus = 0; private _trou = 0; private _pire = 0;
        for "_k" from 0 to _pas do {
            private _f = _k / _pas;
            private _p = [(_dep select 0) + ((_obj select 0) - (_dep select 0)) * _f,
                          (_dep select 1) + ((_obj select 1) - (_dep select 1)) * _f, 0];
            if (([_p] call HMT_COUVERT) > 0) then { _servis = _servis + 1; _trou = 0 }
            else { _trou = _trou + 1; if (_trou > _pire) then { _pire = _trou } };
            if ([_obj, _p] call HMT_VUE) then { _vus = _vus + 1 };
        };
        private _tot = _pas + 1;
        [round (100 * _servis / _tot), round (100 * _vus / _tot), _pire]
    };

    // ─── contrôles, avant tout couloir
    { private _r = [_x, _x vectorAdd [200,0,0]] call HMT_LIRE;
      (format ["HMT|CB|POSITIF|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[2000,2650,0], [1900,3550,0], [1500,4900,0]];
    { private _r = [_x, _x vectorAdd [200,0,0]] call HMT_LIRE;
      (format ["HMT|CB|NUL|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[500,500,0], [7500,7500,0], [300,7000,0]];

    // ─── LA CHASSE
    private _retenus = []; private _essais = 0; private _obj_ok = 0;
    while { count _retenus < 4 && _essais < 8000 } do {
        _essais = _essais + 1;
        private _obj = [800 + random 6600, 800 + random 6600, 0];
        if (!(surfaceIsWater _obj) && {(getTerrainHeightASL _obj) > 2}
            && {([_obj] call HMT_COUVERT) > 0}
            && {(_retenus findIf { (_x select 0) distance2D _obj < 800 }) < 0}) then {
            _obj_ok = _obj_ok + 1;
            private _az = random 360;
            private _dep = [(_obj select 0) + 250 * sin _az, (_obj select 1) + 250 * cos _az, 0];
            if (!(surfaceIsWater _dep) && {(getTerrainHeightASL _dep) > 2}) then {
                private _r = [_obj, _dep] call HMT_LIRE;
                if ((_r select 0) >= 70 && {(_r select 1) >= 60} && {(_r select 2) <= 2}) then {
                    _retenus pushBack [_obj, _dep, round ((_obj getDir _dep))];
                    (format ["HMT|CB|RETENU|%1|obj|%2|%3|depart|%4|%5|az|%6|servis|%7|vus|%8|au|%9e",
                             count _retenus, round (_obj select 0), round (_obj select 1),
                             round (_dep select 0), round (_dep select 1),
                             round (_obj getDir _dep), _r select 0, _r select 1, _essais]) call HMT_LOG;
                };
            };
        };
        if (_essais % 1000 == 0) then {
            (format ["HMT|CB|chasse|%1|essais|objectifs_couverts|%2|retenus|%3",
                     _essais, _obj_ok, count _retenus]) call HMT_LOG;
            sleep 0.1;
        };
    };

    (format ["HMT|CB|BILAN|retenus|%1|sur|%2|essais", count _retenus, _essais]) call HMT_LOG;
    if (count _retenus >= 4) then { "HMT|OK|cb_quatre_couloirs|1" call HMT_LOG }
    else { (format ["HMT|CB|ECHEC|seulement|%1|couloirs", count _retenus]) call HMT_LOG };
    "HMT|CB|TERMINE|1" call HMT_LOG;
};
