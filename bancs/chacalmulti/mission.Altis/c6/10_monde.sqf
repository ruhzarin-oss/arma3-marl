// =====================================================================
// CHACAL - LE MONDE. Le site est TIRE a chaque graine, jamais fige.
//
// Pourquoi tirer : une politique entrainee sur un site fige apprend un azimut,
// pas une manoeuvre - l echec croissait avec l ecart a l azimut appris, et
// c etait un cap absolu. Un corpus d imitation herite du meme defaut si le
// decor ne bouge pas. Le tirage est reproductible, donc un episode douteux se
// rejoue a l identique.
//
// Pourquoi VALIDER : la mission a besoin d une geometrie, pas d un point. S il
// n existe pas de hauteur qui VOIT le site, la phase d observation n existe pas
// et l episode serait un assaut deguise. On sort alors en VOID avec la cause.
// =====================================================================

MC6_SITE = []; MC6_OP = []; MC6_LZ = []; MC6_PZ = [];
MC6_ROUTE = []; MC6_QRF_BASE = []; MC6_OP_GAIN = -1e9; MC6_OP_VUE = false;
MC6_ROUTE_A = []; MC6_ROUTE_B = []; MC6_RALLY = [];

private _essais = 0; private _trouve = false;
// Un refus qui ne nomme pas sa cause envoie chercher au hasard : on compte.
MC6_REFUS = ["ancre",0,"replat",0,"crete",0,"vue",0,"route",0,"lz",0,"qrf",0,"pz",0];
MC6_fnc_refus = {
    private _i = MC6_REFUS find _this;
    if (_i >= 0) then { MC6_REFUS set [_i + 1, (MC6_REFUS select (_i + 1)) + 1] };
};

while { _essais < 120 && !_trouve } do {
    _essais = _essais + 1;

    // --- 1. l ancre : tiree PAR NOUS, jamais par BIS_fnc_findSafePos, qui
    // utilise le hasard du moteur et rendrait le site non reproductible.
    private _a = [];
    for "_k" from 1 to 80 do {
        private _p = [4000 + (22000 call MC6_fnc_al), 4000 + (22000 call MC6_fnc_al), 0];
        if (!surfaceIsWater _p && { (getTerrainHeightASL _p) > 12 }
            && { count (nearestObjects [_p, ["House"], 90]) <= 2 }) exitWith { _a = _p };
    };
    if (count _a == 0) then { "ancre" call MC6_fnc_refus; continue };

    private _site = [_a, 90, 200] call MC6_fnc_plat;
    if (surfaceIsWater _site) then { "replat" call MC6_fnc_refus; continue };

    // --- 2. la hauteur qui VOIT. Sans elle, pas de phase d observation ---
    private _op = []; private _gain = -1e9; private _vue = false;
    for "_i" from 1 to 500 do {
        private _p = _site getPos [480 + (340 call MC6_fnc_al), 360 call MC6_fnc_al];
        _p set [2, 0];
        if (!surfaceIsWater _p && { count (nearestObjects [_p, ["House"], 45]) == 0 }) then {
            private _g = (getTerrainHeightASL _p) - (getTerrainHeightASL _site);
            if (_g > _gain) then { _gain = _g; _op = _p };
        };
    };
    if (count _op == 0 || { _gain < 18 }) then { "crete" call MC6_fnc_refus; continue };
    _vue = [_op, _site] call MC6_fnc_libre;
    if (!_vue) then {
        // On releve la vue autour du meilleur point plutot que d exiger la
        // perfection : a 600 m un seul buisson disqualifie une crete.
        for "_i" from 1 to 220 do {
            private _q = _op getPos [90 call MC6_fnc_al, 360 call MC6_fnc_al]; _q set [2, 0];
            if (!surfaceIsWater _q && { [_q, _site] call MC6_fnc_libre }) exitWith { _op = _q; _vue = true };
        };
    };
    if (!_vue) then { "vue" call MC6_fnc_refus; continue };

    // --- 3. la route a franchir, entre 1,2 et 2,6 km ---
    // ! `nearRoads` NE REND PAS UN ORDRE STABLE. Meme graine, meme build, meme
    // site - et deux routes opposees d un run a l autre, donc deux LZ, donc
    // deux missions. Toute la reproductibilite tombait la-dessus, en silence.
    // On trie sur des coordonnees, jamais sur l ordre du moteur.
    private _rs = (_site nearRoads 2600) select { (_x distance2D _site) > 1200 };
    if (count _rs == 0) then { "route" call MC6_fnc_refus; continue };
    private _cles = _rs apply { [round ((getPosATL _x) select 0) * 100000 + round ((getPosATL _x) select 1), _x] };
    _cles sort true;
    private _route = getPosATL ((_cles select 0) select 1);
    _route set [2, 0];

    // --- 4. la depose, cherchee AUTOUR de l ancre ---
    // Un refus de LZ jetait TOUTE l ancre - donc la crete, sa vue, la route,
    // tout le travail cher. Quarante ancres brulees pour vingt refus de depose.
    //
    // La menace n est pas la route mais LA PATROUILLE, qui reste a 900 m du
    // point de franchissement : 2200 m d ecart laissent 1300 m au plus pres.
    // Mesure du 03/09 : trois FS tues a la descente par la mitrailleuse de bord.
    private _azLz = _site getDir _route;
    private _lz = [];
    for "_j" from 1 to 30 do {
        private _c1 = [_site getPos [3500 + (1000 call MC6_fnc_al), _azLz + (60 call MC6_fnc_al) - 30], 130, 160] call MC6_fnc_plat;
        if (!surfaceIsWater _c1
            && { count (nearestObjects [_c1, ["House"], 90]) == 0 }
            && { count (_c1 nearRoads 300) == 0 }
            && { (_c1 distance2D _route) >= 2200 }) exitWith { _lz = _c1 };
    };
    if (count _lz == 0) then { "lz" call MC6_fnc_refus; continue };

    // --- 5. la base de la reserve, a 5-7 km, sur route ---
    private _qrs = (_site nearRoads 7000) select { private _d = _x distance2D _site; _d > 5000 && _d < 7000 };
    if (count _qrs == 0) then { "qrf" call MC6_fnc_refus; continue };
    private _qcles = _qrs apply { [round ((getPosATL _x) select 0) * 100000 + round ((getPosATL _x) select 1), _x] };
    _qcles sort true;
    private _qb = getPosATL ((_qcles select (floor ((count _qcles) call MC6_fnc_al))) select 1);
    _qb set [2, 0];

    // --- 6. le point d extraction de secours ---
    private _pz = [];
    for "_j" from 1 to 15 do {
        private _c2 = [_site getPos [1200 + (400 call MC6_fnc_al), _azLz + 120 + (80 call MC6_fnc_al)], 110, 160] call MC6_fnc_plat;
        if (!surfaceIsWater _c2) exitWith { _pz = _c2 };
    };
    if (count _pz == 0) then { "pz" call MC6_fnc_refus; continue };

    MC6_SITE = _site; MC6_OP = _op; MC6_LZ = _lz; MC6_PZ = _pz;
    MC6_ROUTE = _route; MC6_QRF_BASE = _qb;
    MC6_OP_GAIN = _gain; MC6_OP_VUE = _vue;
    _trouve = true;
};

if (!_trouve) exitWith {
    MC6_ISSUE = "VOID"; MC6_CAUSE = "SITE_INTROUVABLE";
    (format ["CHACAL|VOID|site|essais|%1|refus|%2", _essais, MC6_REFUS]) call MC6_LOG;
};
(format ["CHACAL|OK|tirage|essais|%1|refus|%2", _essais, MC6_REFUS]) call MC6_LOG;

// ! LA RESERVE RAPPROCHEE ( 16/09 ). Placee ICI, APRES que le monde est fige, et pas dans
// la boucle de tirage : changer la bande 5-7 km a l interieur de la boucle changerait le
// nombre de tirages consommes, donc le monde entier de la graine ( faute n7 du 14/09 :
// MC6_fnc_rnd est un cycle unique, deux marches differentes rendent deux mondes ).
// Ce bloc ne consomme AUCUN alea : il garde l azimut tire, vise la distance imposee, et
// prend la route la plus proche de ce point. Site, crete, route, zone de poser, point
// d extraction et regroupement sont donc identiques a ceux de la meme graine sans levier.
if (MC6_QRF_DIST > 0) then {
    private _d0 = round (MC6_SITE distance2D MC6_QRF_BASE);
    private _az = MC6_SITE getDir MC6_QRF_BASE;
    private _cible = MC6_SITE getPos [MC6_QRF_DIST, _az];
    private _routes = _cible nearRoads 600;
    private _base = +_cible;
    private _surRoute = 0;
    if (count _routes > 0) then {
        _routes = [_routes, [_cible], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
        _base = getPosATL (_routes select 0);
        _surRoute = 1;
    };
    _base set [2, 0];
    MC6_QRF_BASE = _base;
    (format ["CHACAL|E|qrf_rapprochee|%1|dist_tiree|%2|dist_imposee|%3|dist_reelle|%4|sur_route|%5|azimut|%6|base|%7",
        round (time * 100) / 100, _d0, MC6_QRF_DIST, round (MC6_SITE distance2D _base),
        _surRoute, round _az, _base]) call MC6_LOG;
    (format ["CHACAL|AVERT|hors_corpus|qrf_dist|%1", MC6_QRF_DIST]) call MC6_LOG;
};

// les deux bouts du circuit patrouille
private _ext = MC6_ROUTE nearRoads 900;
MC6_ROUTE_A = MC6_ROUTE; MC6_ROUTE_B = MC6_ROUTE;
if (count _ext > 3) then {
    private _far = 0;
    { private _d = _x distance2D MC6_ROUTE; if (_d > _far) then { _far = _d; MC6_ROUTE_B = getPosATL _x } } forEach _ext;
    MC6_ROUTE_B set [2, 0];
    private _far2 = 0;
    { private _d = _x distance2D MC6_ROUTE_B; if (_d > _far2) then { _far2 = _d; MC6_ROUTE_A = getPosATL _x } } forEach _ext;
    MC6_ROUTE_A set [2, 0];
};

// LE POINT DE REGROUPEMENT appartient a l ORDRE, pas a l observation : un rally
// se planifie avant de partir. Il est donc ici, ce qui permet aussi de
// dimensionner les plafonds.
MC6_RALLY = [MC6_SITE getPos [900, (MC6_SITE getDir MC6_OP) + 25], 90] call MC6_fnc_plat;

// --- LES PLAFONDS, CALCULES SUR LES DISTANCES REELLEMENT TIREES ---
// Vitesses de fermeture, a re-mesurer sur corpus : 0,7 m/s en file de nuit hors
// piste ( le trajet n est jamais droit ), 1,8 m/s au repli sous le feu.
MC6_VIT_INFIL = 0.7;
MC6_VIT_REPLI = 1.8;
private _dApp = MC6_LZ distance2D MC6_RALLY;
private _dObs = MC6_RALLY distance2D MC6_OP;
private _dMep = (MC6_SITE distance2D MC6_QRF_BASE) min 900;
private _dExf = (MC6_SITE distance2D MC6_PZ) + 400;
MC6_DUREES = [
    480,                                    // 1 insertion : vol + mise en ordre
    (_dApp / MC6_VIT_INFIL) + 600,       // 2 approche + attente de la fenetre
    (_dObs / MC6_VIT_INFIL) + 1200,      // 3 montee + 20 min d observation
    (_dMep / MC6_VIT_INFIL) + 420,       // 4 articulation des trois elements
    900 * MC6_ASSAUT_X,                  // 5 action sur objectif (seul plafond CONSTANT,
                                            //   d ou le multiplicateur : les autres derivent
                                            //   de la geometrie, celui-ci non)
    (_dExf / MC6_VIT_REPLI) + 300        // 6 rupture jusqu au point de secours
];
(format ["CHACAL|OK|plafonds|%1|total_prevu_min|%2", (MC6_DUREES apply { round _x }),
    round (((MC6_DUREES select 0) + (MC6_DUREES select 1) + (MC6_DUREES select 2)
    + (MC6_DUREES select 3) + (MC6_DUREES select 4) + (MC6_DUREES select 5)) / 60)]) call MC6_LOG;

// meteo : nuit claire. La nuit est le SUJET, pas un decor - c est elle qui
// donne aux dix leur seul avantage mesurable.
0 setOvercast 0.05; 0 setFog 0; 0 setRain 0; forceWeatherChange;
setTimeMultiplier 1;
// Controle positif de l observation : le meme monde, a midi. On ne retire
// jamais la nuit " pour que ca marche mieux " - on la retire UNE FOIS, pour
// savoir si l instrument voit.
if (MC6_JOUR == 1) then {
    setDate [2035, 6, 15, 12, 30];
    (format ["CHACAL|AVERT|hors_corpus|jour|1|controle_positif_observation|heure|%1", date select 3]) call MC6_LOG;
};

(format ["CHACAL|OK|monde|essais|%1|site|%2|alt|%3|op|%4|gain|%5|vue|%6|lz|%7|route|%8|qrf|%9|pz|%10|rally|%11",
    _essais, MC6_SITE, round (getTerrainHeightASL MC6_SITE), MC6_OP,
    round MC6_OP_GAIN, (if (MC6_OP_VUE) then {1} else {0}),
    MC6_LZ, MC6_ROUTE, MC6_QRF_BASE, MC6_PZ, MC6_RALLY]) call MC6_LOG;
(format ["CHACAL|OK|distances|lz_site|%1|op_site|%2|route_site|%3|qrf_site|%4|pz_site|%5|lz_route|%6",
    round (MC6_LZ distance2D MC6_SITE), round (MC6_OP distance2D MC6_SITE),
    round (MC6_ROUTE distance2D MC6_SITE), round (MC6_QRF_BASE distance2D MC6_SITE),
    round (MC6_PZ distance2D MC6_SITE), round (MC6_LZ distance2D MC6_ROUTE)]) call MC6_LOG;
