// chasse_appui_en_jeu.sqf — LE GEOMETRE NE FILTRE PLUS, IL CHERCHE.
//
// ⚠️ VERDICT DU FILTRE : ZERO lieu retenu sur huit. Controles bons (bati dense 100 %, pleine
// mer 0 %), huit lieux STABLES, couvert excellent — 81 a 100 % de pas servis. Mais deux
// colonnes s effondrent : l appui ne voit pas l objectif (0, 0, 40, 40, 40, 0, 60, 20 %) et
// l assaut n est pas sous le feu (3, 0, 33, 7, 24, 5, 45, 24 %).
//
// MEME CAUSE QUE POUR LE GESTE N°3, mot pour mot : ces lieux viennent de la chasse sur CARTE
// au pas de 50 m, ou j avais « verifie » les lignes de vue avec des cases OUVERTES. Une case
// ouverte de 50 m ne dit rien de ce qu un oeil voit a 150. La carte donne le gros grain ; le
// geometre en jeu rend les metres.
//
// ET LA REPARATION EST DEJA EPROUVEE : pour le n°3, la chasse EN JEU a trouve huit traversees
// la ou la carte en donnait zero. Meme patron, memes seuils, aucun assoupli.
//
// ⚠️ POURQUOI ILS SONT SUSPECTS. Ils viennent de la chasse sur CARTE au pas de 50 m —
// exactement celle qui a rendu ZERO traversee valide sur huit pour le geste n°3, parce qu on
// ne demande pas a une carte au pas de 50 m de parler d objets a 15 m. Rien ne dit qu ils
// tiennent, et on ne fait pas courir un banc de mission sur un terrain non certifie.
//
// CE QUE LE GESTE N°2 EXIGE DE SON TERRAIN — trois choses, et les trois se mesurent :
//
//  ① L APPUI DOIT VOIR L OBJECTIF. C est la condition de son existence : un poste de tir qui
//     ne voit pas la lisiere ne supprime personne. Mesure d oeil a oeil, `checkVisibility`,
//     entre deux hommes REELS — la visibilite que l IA emploie pour decider si elle tire.
//     ⟨la lecon du geometre v3 : mes rayons a 1,20 m donnaient 64 %, l oeil du moteur 32 %⟩
//
//  ② L ASSAUT DOIT ETRE SOUS LE FEU. Sinon les deux bras se confondent et le lieu certifie un
//     geste qui n a jamais ete necessaire. Meme mesure, depuis l objectif vers le trajet.
//
//  ③ L ASSAUT DOIT AVOIR DU COUVERT. Mesure a la BOITE ENGLOBANTE — plus de 2 m de large,
//     2 m de haut, 50 cm d epaisseur — reprise d Antistasi ⟨MIT, Copyright (c) 2023 Antistasi
//     Ultimate Team⟩. C est du couvert qui arrete une balle, pas une classe au bon nom.
//
// LES SEUILS, DEPOSES AVANT DE LIRE — repris tels quels du geometre du n°3, dont ils sont
// deja l usage. On ne redecoupe pas des seuils pour un nouveau terrain : ce serait les choisir.
//   · l appui voit l objectif   : >= 60 % des lignes poste -> objectif degagees
//   · l assaut est sous le feu  : >= 60 % de ses pas vus depuis l objectif
//   · l assaut a du couvert     : >= 70 % de pas servis, aucun trou de plus de 2 pas
//   · et le monde est PRET quand il repond DEUX FOIS PAREIL, pas quand une horloge le dit
//
// CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
//   · CONTROLE POSITIF : trois points en bati dense doivent sortir tres bien servis.
//   · CONTROLE NUL : trois points en pleine mer doivent sortir a zero.
//   · CONTROLE DE STABILITE : un lieu qui n atteint jamais deux lectures identiques en huit
//     tentatives est declare INSTABLE et ecarte — pas moyenne.
//   · Et si moins de 5 lieux tiennent, ce n est pas le geste qu on condamne : c est la chasse
//     sur carte qu on refait EN JEU, comme pour le n°3.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|GA|debut|1" call HMT_LOG;

// plus de liste : on cherche.

// le couvert, mesure a la boite englobante ⟨repris d Antistasi, fn_coverage, MIT⟩
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

    // ─── les corps : la mesure se fait dans l etat ou le banc tournera, pas dans un monde vide
    private _gD = createGroup east;
    HMT_OBS = _gD createUnit ["O_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_OBS allowDamage false; HMT_OBS disableAI "PATH"; HMT_OBS setBehaviour "COMBAT";
    private _gA = createGroup west;
    HMT_MAR = _gA createUnit ["B_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_MAR allowDamage false; HMT_MAR disableAI "PATH"; HMT_MAR setBehaviour "CARELESS";
    sleep 3;
    "HMT|GA|corps|observateur+marcheur|poses" call HMT_LOG;

    // ─── voit-on B depuis A ? d oeil a oeil, entre deux hommes reels
    HMT_VUE = {
        params ["_a", "_b"];
        HMT_OBS setPosATL _a; HMT_MAR setPosATL _b;
        sleep 0.05;
        ([objNull, "VIEW"] checkVisibility [eyePos HMT_OBS, eyePos HMT_MAR]) > 0
    };

    HMT_LIRE = {
        params ["_obj", "_poste", "_dep"];
        // ① l appui voit-il l objectif ? on echantillonne la lisiere sur 40 m
        private _vu1 = 0;
        { if ([_poste, _obj vectorAdd [_x, 0, 0]] call HMT_VUE) then { _vu1 = _vu1 + 1 } }
          forEach [-20, -10, 0, 10, 20];
        // ② et ③ le long du trajet d assaut
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
        [round (100 * _vu1 / 5), round (100 * _servis / _tot), round (100 * _vus / _tot), _pire]
    };

    // ─── deux lectures identiques : le monde est pret quand il repond deux fois pareil
    HMT_STABLE = {
        params ["_o", "_p", "_d", "_nom"];
        private _prec = []; private _n = 0; private _ok = false;
        while { _n < 8 && !_ok } do {
            _n = _n + 1;
            private _r = [_o, _p, _d] call HMT_LIRE;
            (format ["HMT|GA|lecture|%1|%2|appuiVoit|%3|servis|%4|vus|%5|piretrou|%6",
                     _nom, _n, _r select 0, _r select 1, _r select 2, _r select 3]) call HMT_LOG;
            if (count _prec > 0 && {_r isEqualTo _prec}) then { _ok = true };
            _prec = _r; sleep 2;
        };
        if (!_ok) then { (format ["HMT|GA|INSTABLE|%1|en|%2|lectures", _nom, _n]) call HMT_LOG };
        [_prec, _ok]
    };

    // ─── contrôles, avant tout lieu
    { private _r = [_x, _x vectorAdd [40,0,0], _x vectorAdd [200,0,0]] call HMT_LIRE;
      (format ["HMT|GA|POSITIF|%1|servis|%2", _forEachIndex, _r select 1]) call HMT_LOG;
    } forEach [[2000,2650,0], [1900,3550,0], [1500,4900,0]];
    { private _r = [_x, _x vectorAdd [40,0,0], _x vectorAdd [200,0,0]] call HMT_LIRE;
      (format ["HMT|GA|NUL|%1|servis|%2", _forEachIndex, _r select 1]) call HMT_LOG;
    } forEach [[500,500,0], [7500,7500,0], [300,7000,0]];

    // ─── LA CHASSE. Memes seuils qu au filtre, pas un d assoupli : >= 60 % de vue
    // poste->objectif, >= 70 % de pas servis, >= 60 % de pas vus, aucun trou de plus de 2 pas.
    // On paie du calcul, on ne baisse pas la barre — c est en la baissant qu on avait admis le
    // terrain 0 du banc de mecanique, dont la ligne de base variait de 120 %.
    private _retenus = [];
    private _essais = 0; private _vus1 = 0;
    while { count _retenus < 8 && _essais < 6000 } do {
        _essais = _essais + 1;
        // un OBJECTIF : un point qui a du couvert autour de lui — une lisiere a tenir
        private _obj = [800 + random 6600, 800 + random 6600, 0];
        if (!(surfaceIsWater _obj) && {(getTerrainHeightASL _obj) > 2}
            && {([_obj] call HMT_COUVERT) > 0}
            && {(_retenus findIf { (_x select 0) distance2D _obj < 600 }) < 0}) then {
            _vus1 = _vus1 + 1;
            // le POSTE D APPUI : a 150 m, dans une direction tiree ; l assaut arrive a 90°
            private _az = random 360;
            private _poste = [(_obj select 0) + 150 * sin _az, (_obj select 1) + 150 * cos _az, 0];
            private _aza = _az + 90;
            private _dep = [(_obj select 0) + 200 * sin _aza, (_obj select 1) + 200 * cos _aza, 0];
            if (!(surfaceIsWater _poste) && {!(surfaceIsWater _dep)}
                && {(getTerrainHeightASL _poste) > 2} && {(getTerrainHeightASL _dep) > 2}) then {
                private _r = [_obj, _poste, _dep] call HMT_LIRE;
                if ((_r select 0) >= 60 && {(_r select 1) >= 70}
                    && {(_r select 2) >= 60} && {(_r select 3) <= 2}) then {
                    _retenus pushBack [_obj, _poste, _dep];
                    (format ["HMT|GA|RETENU|%1|obj|%2|%3|poste|%4|%5|depart|%6|%7|appuiVoit|%8|servis|%9|vus|%10|au|%11e",
                             count _retenus, round (_obj select 0), round (_obj select 1),
                             round (_poste select 0), round (_poste select 1),
                             round (_dep select 0), round (_dep select 1),
                             _r select 0, _r select 1, _r select 2, _essais]) call HMT_LOG;
                };
            };
        };
        if (_essais % 500 == 0) then {
            (format ["HMT|GA|chasse|%1|essais|objectifs_couverts|%2|retenus|%3",
                     _essais, _vus1, count _retenus]) call HMT_LOG;
            sleep 0.1;
        };
    };

    (format ["HMT|GA|BILAN|retenus|%1|sur|%2|essais", count _retenus, _essais]) call HMT_LOG;
    if (count _retenus >= 5) then { "HMT|OK|ga_assez_de_lieux|1" call HMT_LOG }
    else {
        // ET SI LA CHASSE ECHOUE, c est un RESULTAT : Stratis ne porterait pas de lieu ou
        // l appui-feu soit a la fois POSSIBLE et NECESSAIRE. On le dirait tel quel.
        (format ["HMT|GA|ECHEC|pas_assez|%1|il_en_faut|5|sur|%2|essais",
                 count _retenus, _essais]) call HMT_LOG;
    };
    "HMT|GA|TERMINE|1" call HMT_LOG;
};
