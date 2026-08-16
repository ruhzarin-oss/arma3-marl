// certif3.sqf — GESTE N°3 : LA CERTIFICATION DES LIEUX, AVEC SA TOLERANCE DEPOSEE.
//
// ⚠️ LA DETTE QU ON SOLDE. Le geometre v3 a retenu 6 lieux sur 8 le 09/08, mais il mesurait la
// vue par DEUX CHEMINS qui divergeaient de 9 points en moyenne, SANS qu aucune tolerance d
// accord ait ete deposee. La regle 11 tient donc ces six lieux en SURSIS : sans tolerance
// deposee, ce sont des candidats, pas des certifies.
//
// ⚠️ PROTOCOLE REDEPOSE ENTIER. Le premier exigeait 80 % d accord entre un chemin qui rend une
// FRACTION (`checkVisibility`) et un chemin qui rend OUI ou NON (`lineIntersectsSurfaces`).
// Mesure : accord 100 % quand la vue est franche, 75 % quand elle est partielle.
//
// L ANALOGIE QUI L EXPLIQUE : deux medecins lisent la meme radio ; l un dit « tumeur / pas de
// tumeur », l autre dit « 30 % de chances ». Sur les cas francs ils s accordent toujours ; sur
// les cas ambigus ils divergent FORCEMENT — non parce que l un se trompe, mais parce que l un a
// le droit de dire « a moitie » et l autre non. Leur desaccord ne mesurait pas leur competence,
// il mesurait LA DIFFICULTE DES CAS. Et un terrain plein de demi-couvert est precisement ce que
// le geste n°3 exige : le controle recalait les terrains qui lui conviennent le mieux.
//
// LA FAUTE DE FOND : la regle 11 demande deux chemins vers LA MEME GRANDEUR. Les miens n en
// mesuraient pas une seule — « y a-t-il un obstacle solide ? » contre « quelle part est
// visible ? ». Pas deux mesures d une chose : une mesure de chacune de deux choses. Aucune
// valeur de tolerance n aurait sauve cela.
//
// LE SECOND CHEMIN EST DONC REFAIT : CINQ RAYONS vers cinq points du corps — tete, poitrine,
// deux epaules, genoux — et l on compte la FRACTION qui passe. Il rend desormais une fraction,
// comme le moteur, et mesure la meme grandeur : quelle part de cet homme est exposee.
//
//   >>> LES DEUX FRACTIONS NE DOIVENT PAS DIFFERER DE PLUS DE 0,35 EN MOYENNE ABSOLUE. <<<
//   Derivee du mecanisme : cinq rayons discretisent en pas de 0,2 ; le moteur rend un continu
//   qui integre en outre le feuillage. Au-dela d un tiers, ils ne regardent plus le meme monde.
//
// LE CERTIFICAT S APPUIE SUR `checkVisibility`, jamais sur mes rayons ⟨regle 6 : verifie la
// propriete que le MECANISME utilise — c est l IA qui decidera de tirer, donc c est sa vue⟩.
//
// LES HUIT lieux sont re-mesures, pas seulement les six retenus : sinon on heriterait d un tri
// fait sous un instrument non certifie. Seuils INCHANGES : >= 70 % servis, >= 60 % vus, aucun
// trou de plus de 2 pas.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|C3|debut|1" call HMT_LOG;

HMT_LIEUX8 = [
    [[2901,5830,0],[3094,5895,0],[3037,5744,0]], [[2987,3543,0],[2860,3623,0],[2990,3689,0]],
    [[4355,6210,0],[4595,6210,0],[4475,6085,0]], [[2523,3096,0],[2285,3120,0],[2416,3232,0]],
    [[4380,3363,0],[4339,3217,0],[4479,3256,0]], [[4814,3657,0],[4955,3601,0],[4930,3745,0]],
    [[2397,1801,0],[2553,1834,0],[2449,1940,0]], [[2418,3969,0],[2619,3915,0],[2551,4062,0]]
];

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
    "HMT|C3|corps|poses" call HMT_LOG;

    // une lecture rend : servis %, vus % (MOTEUR), pire trou, rayons %, ACCORD % entre chemins
    HMT_LIRE = {
        params ["_cou", "_dep", "_poste"];
        private _d = _dep distance2D _cou;
        private _pas = round (_d / 10) max 1;
        private _servis = 0; private _vus = 0; private _ray = 0; private _acc = 0;
        private _trou = 0; private _pire = 0;
        HMT_OBS setPosATL _poste;
        for "_k" from 0 to _pas do {
            private _f = _k / _pas;
            private _p = [(_dep select 0) + ((_cou select 0) - (_dep select 0)) * _f,
                          (_dep select 1) + ((_cou select 1) - (_dep select 1)) * _f, 0];
            if (([_p] call HMT_COUVERT) > 0) then { _servis = _servis + 1; _trou = 0 }
            else { _trou = _trou + 1; if (_trou > _pire) then { _pire = _trou } };
            HMT_MAR setPosATL _p;
            // CHEMIN 1 — la vue du MOTEUR, d oeil a oeil. C est elle qui FAIT FOI ⟨regle 6⟩.
            private _f1 = [objNull, "VIEW"] checkVisibility [eyePos HMT_OBS, eyePos HMT_MAR];
            // CHEMIN 2 — LA SILHOUETTE : cinq rayons vers cinq points du corps. Il rend une
            // FRACTION, comme le moteur, et mesure donc la MEME grandeur.
            private _pass = 0;
            {
                private _h = _x;
                if (count (lineIntersectsSurfaces
                    [AGLToASL [_poste select 0, _poste select 1, 1.5],
                     AGLToASL [(_p select 0) + (_h select 0), (_p select 1) + (_h select 1), _h select 2],
                     HMT_OBS, HMT_MAR, true, 1]) == 0) then { _pass = _pass + 1 };
            } forEach [[0,0,1.7], [0,0,1.2], [-0.25,0,1.4], [0.25,0,1.4], [0,0,0.6]];
            private _f2 = _pass / 5;
            if (_f1 > 0) then { _vus = _vus + 1 };
            if (_f2 > 0) then { _ray = _ray + 1 };
            _acc = _acc + (abs (_f1 - _f2));      // on cumule l ECART, pas l accord binaire
        };
        private _tot = _pas + 1;
        // le 5e champ est desormais l ECART MOYEN ABSOLU entre les deux fractions, en centiemes
        [round (100*_servis/_tot), round (100*_vus/_tot), _pire,
         round (100*_ray/_tot), round (100*_acc/_tot)]
    };

    HMT_STABLE = {
        params ["_c", "_d", "_p", "_nom"];
        private _prec = []; private _n = 0; private _ok = false;
        while { _n < 8 && !_ok } do {
            _n = _n + 1;
            private _r = [_c, _d, _p] call HMT_LIRE;
            (format ["HMT|C3|lecture|%1|%2|servis|%3|vus|%4|piretrou|%5|rayons|%6|accord|%7",
                     _nom, _n, _r select 0, _r select 1, _r select 2, _r select 3,
                     _r select 4]) call HMT_LOG;
            if (count _prec > 0 && {_r isEqualTo _prec}) then { _ok = true };
            _prec = _r; sleep 2;
        };
        [_prec, _ok, _n]
    };

    // ─── contrôles, avant tout lieu
    { private _r = [_x, _x vectorAdd [200,0,0], _x vectorAdd [120,0,0]] call HMT_LIRE;
      (format ["HMT|C3|POSITIF|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[2000,2650,0], [1900,3550,0], [1500,4900,0]];
    { private _r = [_x, _x vectorAdd [200,0,0], _x vectorAdd [120,0,0]] call HMT_LIRE;
      (format ["HMT|C3|NUL|%1|servis|%2", _forEachIndex, _r select 0]) call HMT_LOG;
    } forEach [[500,500,0], [7500,7500,0], [300,7000,0]];

    // ─── LE SONDAGE COMPORTEMENTAL. Les deux chemins ci-dessus restent GEOMETRIQUES, donc
    // aveugles ENSEMBLE au feuillage que le moteur traverse a moitie — et une tolerance ne
    // detecte jamais deux chemins qui se trompent de concert. On pose donc un vrai defenseur
    // ARME et un vrai marcheur, on laisse l IA agir six secondes, et on lit ce que le camp sait.
    // ⚠️ SA LIMITE, NOMMEE D AVANCE : `knowsAbout` est DE CAMP, PAS DE SOLDAT — il voit a 300 m
    // devant et reste aveugle a 50 m de flanc. Ce sondage mesure ce que le CAMP sait, pas ce que
    // ce defenseur voit. IL NE CERTIFIE RIEN : il sert a attraper l aveuglite commune, rien d autre.
    //
    // ⚠️⚠️ LA FENETRE EST PASSEE DE 6 A 60 SECONDES, ET LA LECON ETAIT DEJA DANS NOTRE DOSSIER.
    // Premier jet a 6 s : la geometrie disait ~70 % de vue sur trois lieux, et le camp ne savait
    // RIEN — sonde a 0. Or le banc de tir du 03/08 porte exactement cela, mot pour mot :
    //   « Premier jet : 8 s avant, 12 s apres — trop court pour que la detection s etablisse.
    //     La connaissance restait a 0,00 alors que le banc mobile detectait 18 fois sur 18 a
    //     105 m, mais apres ~50 s d approche. Ma reference n existait pas. »
    // J avais la reponse dans nos propres pieces et j ai donne six secondes la ou la fiche en
    // disait cinquante. ⟨regle 6 : on lit sur pieces, y compris les notres⟩
    //
    // ET LE SONDAGE PORTE DESORMAIS SON PROPRE CONTROLE POSITIF : un pas a moins de 30 m du
    // poste, en vue franche, DOIT etre connu. S il ne l est pas, ce n est pas la geometrie qui
    // ment — c est le sondage qui est trop court, et on ne lit rien d autre.
    HMT_SONDER = {
        params ["_cou", "_dep", "_poste", "_nom"];
        private _gS = createGroup east;
        private _def = _gS createUnit ["O_Soldier_F", _poste, [], 0, "NONE"];
        _def setPosATL _poste; _def allowDamage false; _def disableAI "PATH";
        _def setBehaviour "COMBAT"; _def setCombatMode "BLUE"; _def setUnitPos "MIDDLE";
        private _gW = createGroup west;
        private _w = _gW createUnit ["B_Soldier_F", _dep, [], 0, "NONE"];
        _w allowDamage false; _w disableAI "PATH"; _w disableAI "AUTOCOMBAT";
        _w setBehaviour "CARELESS"; _w setCombatMode "BLUE";
        private _d = _dep distance2D _cou;
        private _pas = round (_d / 10) max 1;
        private _vu = 0; private _n = 0;
        // ── CONTROLE POSITIF DU SONDAGE : un homme a 25 m du poste, a decouvert, DOIT etre connu.
        private _pres = _poste vectorAdd [25, 0, 0];
        _w setPosATL _pres;
        _def forgetTarget _w;
        sleep 60;
        private _ctrl = _def knowsAbout _w;
        (format ["HMT|C3|sonde_controle|%1|a_25m|knowsAbout|%2", _nom,
                 (round (_ctrl*100))/100]) call HMT_LOG;
        if (_ctrl <= 0.5) exitWith {
            (format ["HMT|C3|SONDE_INVALIDE|%1|controle_a_25m|%2|le_sondage_ne_dit_rien",
                     _nom, (round (_ctrl*100))/100]) call HMT_LOG;
            deleteVehicle _def; deleteVehicle _w;
            -1
        };
        // ── trois pas seulement, mais SOIXANTE secondes chacun : la detection a besoin de temps,
        // et une fenetre trop courte fabrique des zeros qu on prendrait pour des faits.
        for "_i" from 1 to 3 do {
            private _k = floor (random (_pas + 1));
            private _f = _k / _pas;
            private _p = [(_dep select 0) + ((_cou select 0) - (_dep select 0)) * _f,
                          (_dep select 1) + ((_cou select 1) - (_dep select 1)) * _f, 0];
            _w setPosATL _p;
            _def forgetTarget _w;
            sleep 60;
            private _sait = _def knowsAbout _w;
            private _geo = ([objNull, "VIEW"] checkVisibility [eyePos _def, eyePos _w]) > 0;
            if (_sait > 0.5) then { _vu = _vu + 1 };
            _n = _n + 1;
            (format ["HMT|C3|sonde|%1|pas|%2|knowsAbout|%3|geometrie|%4",
                     _nom, _k, (round (_sait*100))/100,
                     (if (_geo) then {1} else {0})]) call HMT_LOG;
        };
        deleteVehicle _def; deleteVehicle _w;
        [_gS, _gW] spawn { params ["_a","_b"]; sleep 1;
            { if (!isNull _x && {count (units _x) == 0}) then { deleteGroup _x } } forEach [_a,_b] };
        round (100 * _vu / _n)
    };

    // ─── LES HUIT LIEUX, re-mesures — pas seulement les six retenus
    private _certifies = 0; private _accords = [];
    {
        _x params ["_cou", "_dep", "_poste"];
        private _s = [_cou, _dep, _poste, str (_forEachIndex + 1)] call HMT_STABLE;
        _s params ["_r", "_stable", "_n"];
        private _accord = _r select 4;         // ecart moyen absolu, en centiemes
        _accords pushBack _accord;
        // LA TOLERANCE DEPOSEE : au-dela de 0,35 d ecart moyen, l instrument est en panne
        private _instrument = _accord <= 35;
        private _ok = _instrument && _stable && {(_r select 0) >= 70}
                                   && {(_r select 1) >= 60} && {(_r select 2) <= 2};
        if (_ok) then { _certifies = _certifies + 1 };
        private _sonde = [_cou, _dep, _poste, str (_forEachIndex + 1)] call HMT_SONDER;
        (format ["HMT|C3|LIEU|%1|servis|%2|vus|%3|piretrou|%4|silhouette|%5|ecart|%6|sonde|%7|stable|%8|instrument|%9|certifie|%10",
                 _forEachIndex + 1, _r select 0, _r select 1, _r select 2, _r select 3,
                 _accord, _sonde, (if (_stable) then {1} else {0}),
                 (if (_instrument) then {1} else {0}),
                 (if (_ok) then {1} else {0})]) call HMT_LOG;
        sleep 1;
    } forEach HMT_LIEUX8;

    private _pire = 0; { if (_x > _pire) then { _pire = _x } } forEach _accords;
    (format ["HMT|C3|BILAN|certifies|%1|sur|%2|ecart_maximal|%3",
             _certifies, count HMT_LIEUX8, _pire]) call HMT_LOG;
    if (_pire > 35) then {
        (format ["HMT|C3|ECHEC|instrument_en_panne|ecart|%1|tolerance|35", _pire]) call HMT_LOG;
    } else {
        if (_certifies >= 5) then { "HMT|OK|c3_lieux_certifies|1" call HMT_LOG }
        else { (format ["HMT|C3|ECHEC|seulement|%1|certifies", _certifies]) call HMT_LOG };
    };
    "HMT|C3|TERMINE|1" call HMT_LOG;
};
