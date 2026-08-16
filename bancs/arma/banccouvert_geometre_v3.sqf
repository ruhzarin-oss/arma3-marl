// geometre_v3.sqf — LE GÉOMÈTRE QUI MESURE CE QUE LE MÉCANISME UTILISE.
//
// ═══ CE QUI A TUÉ LES DEUX PREMIÈRES VERSIONS, ET CE QUI CHANGE ═══
//
// ① L'EXPOSITION SE MESURAIT PAR MES RAYONS. Trois de mes scripts ont donné 64 %, 10 % et
//    100 % pour le même couloir. Une sonde a montré que le calcul était identique — donc
//    c'était l'état du monde. L'expérience de chargement a tranché : le nombre d'objets ne
//    bouge pas (167 dans les trois états), mais dès qu'on peuple le monde mes rayons tombent
//    à ZÉRO. La cause, c'était moi : le rayon part du poste à 1,20 m, et j'y avais posé un
//    soldat — il démarrait DANS son corps, sans rien à ignorer.
//    → ON MESURE DÉSORMAIS D'ŒIL À ŒIL, avec `checkVisibility` entre deux hommes RÉELS.
//      C'est la visibilité DU MOTEUR — celle que l'IA utilise pour décider si elle tire —
//      et le moteur gère l'auto-occlusion. ⟨règle 6 : vérifie la propriété que le mécanisme
//      utilise ; et Antistasi le faisait déjà, `checkVisibility [eyePos _a, eyePos _b]`⟩
//
// ② LE COUVERT SE COMPTAIT AU RAYON. Je comptais des objets d'une liste de classes dans un
//    rayon de 15 m. Le chercheur de couvert d'Antistasi fait mieux : il mesure la BOÎTE
//    ENGLOBANTE de chaque objet et exige plus de 2 m de large, 2 m de haut, 50 cm d'épaisseur.
//    → C'est du couvert qui arrête une balle, pas une classe qui porte le bon nom. Repris.
//      ⟨MIT · Copyright (c) 2023 Antistasi Ultimate Team — notice conservée, licence vérifiée⟩
//
// ③ LE MONDE EST MESURÉ DANS L'ÉTAT OÙ IL SERVIRA. ⟨Fable⟩ « La propriété qui fait foi est
//    celle que le mécanisme utilise, DANS L'ÉTAT où il l'utilisera — et le banc tournera dans
//    un monde peuplé. » Donc : défenseur au poste, marcheur sur le trajet, corps réels.
//
// ④ LE MONDE EST PRÊT QUAND IL RÉPOND DEUX FOIS PAREIL — pas quand une horloge le décrète.
//    On relit jusqu'à deux passages consécutifs identiques, huit tentatives au plus.
//
// ⑤ RÈGLE 11, déposée cette nuit : toute grandeur qui décide d'un certificat se mesure par
//    DEUX CHEMINS INDÉPENDANTS ; un désaccord ne s'arbitre pas, il déclare l'instrument en
//    panne. On garde donc les deux mesures — rayons ET moteur — et on les journalise toutes
//    les deux. Le certificat s'appuie sur le moteur ; l'écart entre les deux est SURVEILLÉ.
//
// ═══ LES CRITÈRES — inchangés depuis leur dépôt, aucun assoupli ═══
//   · un PAS est SERVI s'il a un couvert de plus de 2 m × 2 m × 0,5 m à moins de 15 m ;
//   · un PAS est VU si le moteur donne une visibilité non nulle d'œil à œil depuis le poste ;
//   · une traversée est RETENUE si : ≥ 70 % servis, ≥ 60 % vus, aucun trou de plus de 2 pas.
//   · et la barre s'applique au MINIMUM des sessions, pas à une mesure isolée.
//
// ═══ CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant ═══
//   · CONTRÔLE POSITIF : trois points en bâti dense doivent sortir très bien servis.
//   · CONTRÔLE NUL : trois points en pleine mer doivent sortir à zéro.
//   · CONTRÔLE DE STABILITÉ : si une traversée n'atteint jamais deux lectures identiques en
//     huit tentatives, elle est déclarée INSTABLE et écartée — pas moyennée.
//   · CONTRÔLE DES DEUX CHEMINS : l'écart moyen entre rayons et moteur est journalisé. On ne
//     s'en sert pas pour trancher, on s'en sert pour savoir si l'instrument est sain.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|G3|debut|1" call HMT_LOG;

// ─────────────────────────── le couvert, mesuré à la boîte englobante ⟨repris d'Antistasi⟩
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

    // ─────────────────────────── les corps : ils font partie de la mesure, pas du décor
    private _gD = createGroup east;
    HMT_OBS = _gD createUnit ["O_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_OBS allowDamage false; HMT_OBS disableAI "PATH"; HMT_OBS disableAI "MOVE";
    HMT_OBS setBehaviour "COMBAT"; HMT_OBS setCombatMode "BLUE";
    private _gA = createGroup west;
    HMT_MAR = _gA createUnit ["B_Soldier_F", [0,0,0], [], 0, "NONE"];
    HMT_MAR allowDamage false; HMT_MAR disableAI "PATH"; HMT_MAR disableAI "MOVE";
    HMT_MAR setBehaviour "CARELESS"; HMT_MAR setCombatMode "BLUE";
    sleep 3;
    "HMT|G3|corps|observateur+marcheur|poses" call HMT_LOG;

    // ─────────────────────────── une lecture : couvert + vue, par les DEUX chemins
    HMT_LIRE = {
        params ["_a", "_b", "_poste"];
        HMT_OBS setPosATL _poste;
        private _d = _a distance2D _b;
        private _pas = round (_d / 10) max 1;
        private _servis = 0; private _vus = 0; private _rayons = 0;
        private _trou = 0; private _pire = 0;
        for "_k" from 0 to _pas do {
            private _f = _k / _pas;
            private _p = [(_a select 0) + ((_b select 0) - (_a select 0)) * _f,
                          (_a select 1) + ((_b select 1) - (_a select 1)) * _f, 0];
            // couvert
            if (([_p] call HMT_COUVERT) > 0) then { _servis = _servis + 1; _trou = 0 }
            else { _trou = _trou + 1; if (_trou > _pire) then { _pire = _trou } };
            // vue — CHEMIN 1 : le moteur, d oeil a oeil, entre deux hommes reels
            HMT_MAR setPosATL _p;
            if (([objNull, "VIEW"] checkVisibility [eyePos HMT_OBS, eyePos HMT_MAR]) > 0)
                then { _vus = _vus + 1 };
            // vue — CHEMIN 2 : mes rayons, gardes comme temoin de sante (regle 11)
            if (count (lineIntersectsSurfaces [AGLToASL [_poste select 0, _poste select 1, 1.5],
                                               AGLToASL [_p select 0, _p select 1, 1.2],
                                               HMT_OBS, HMT_MAR, true, 1]) == 0)
                then { _rayons = _rayons + 1 };
        };
        private _tot = _pas + 1;
        [round (100 * _servis / _tot), round (100 * _vus / _tot),
         _pire, round (100 * _rayons / _tot)]
    };

    // ─────────────────────────── une mesure STABLE : deux lectures identiques d affilee
    HMT_STABLE = {
        params ["_a", "_b", "_poste", "_nom"];
        private _prec = []; private _n = 0; private _ok = false;
        while { _n < 8 && !_ok } do {
            _n = _n + 1;
            private _r = [_a, _b, _poste] call HMT_LIRE;
            (format ["HMT|G3|lecture|%1|%2|servis|%3|vus|%4|piretrou|%5|rayons|%6",
                     _nom, _n, _r select 0, _r select 1, _r select 2, _r select 3]) call HMT_LOG;
            if (count _prec > 0 && {_r isEqualTo _prec}) then { _ok = true };
            _prec = _r;
            sleep 2;
        };
        if (!_ok) then { (format ["HMT|G3|INSTABLE|%1|en|%2|lectures", _nom, _n]) call HMT_LOG };
        [_prec, _ok, _n]
    };

    // ─────────────────────────── contrôles, avant toute traversée
    { private _r = [_x, _x, _x vectorAdd [50,0,0]] call HMT_LIRE;
      (format ["HMT|G3|POSITIF|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[2000,2650,0], [1900,3550,0], [1500,4900,0]];
    { private _r = [_x, _x, _x vectorAdd [50,0,0]] call HMT_LIRE;
      (format ["HMT|G3|NUL|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[500,500,0], [7500,7500,0], [300,7000,0]];

    // ─────────────────────────── les huit candidats, ré-audités
    private _lieux = [
        [[2901,5830,0],[3094,5895,0],[3037,5744,0]], [[2987,3543,0],[2860,3623,0],[2990,3689,0]],
        [[4355,6210,0],[4595,6210,0],[4475,6085,0]], [[2523,3096,0],[2285,3120,0],[2416,3232,0]],
        [[4380,3363,0],[4339,3217,0],[4479,3256,0]], [[4814,3657,0],[4955,3601,0],[4930,3745,0]],
        [[2397,1801,0],[2553,1834,0],[2449,1940,0]], [[2418,3969,0],[2619,3915,0],[2551,4062,0]]
    ];
    private _tiennent = 0; private _ecarts = [];
    {
        _x params ["_cou", "_dep", "_poste"];
        private _s = [_dep, _cou, _poste, str (_forEachIndex + 1)] call HMT_STABLE;
        _s params ["_r", "_stable", "_n"];
        private _retenue = _stable && {(_r select 0) >= 70} && {(_r select 1) >= 60}
                                   && {(_r select 2) <= 2};
        if (_retenue) then { _tiennent = _tiennent + 1 };
        _ecarts pushBack (abs ((_r select 1) - (_r select 3)));
        (format ["HMT|G3|LIEU|%1|servis|%2|vus|%3|piretrou|%4|rayons|%5|stable|%6|lectures|%7|retenue|%8",
                 _forEachIndex + 1, _r select 0, _r select 1, _r select 2, _r select 3,
                 (if (_stable) then {1} else {0}), _n,
                 (if (_retenue) then {1} else {0})]) call HMT_LOG;
        sleep 1;
    } forEach _lieux;

    private _em = 0; { _em = _em + _x } forEach _ecarts;
    _em = _em / (count _ecarts);
    (format ["HMT|G3|BILAN|retenues|%1|sur|%2|ecart_moyen_moteur_vs_rayons|%3",
             _tiennent, count _lieux, round _em]) call HMT_LOG;
    "HMT|G3|TERMINE|1" call HMT_LOG;
};
