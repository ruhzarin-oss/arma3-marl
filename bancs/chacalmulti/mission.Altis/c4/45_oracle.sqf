// =====================================================================
// CHACAL - L ORACLE COMMANDANT, version 1 ( plan a139c63, niveau 1 ).
//
// POURQUOI. Mesure du 19/09 : le detachement n est JAMAIS detecte dans 92 % des episodes, la phase 2
// reussit dans 85 %, et vingt minutes d attente ne changent rien. L adversaire est un decor : une
// garnison statique, une patrouille qui fait la navette entre deux points fixes. Sans quelqu un en face
// pour faire payer, aucun choix ne depend de la situation - et c est ce que six campagnes ont mesure.
//
// CE QU IL A LE DROIT DE SAVOIR. Uniquement ce que son camp sait vraiment :
//   - targetKnowledge de SES groupes sur nos hommes : le champ 0 ( connu ) et le champ 6 ( position CRUE ) ;
//   - son propre etat : alarme, pertes ;
//   - le temps.
// INTERDIT, et verifie par le controle de non-triche : lire la position vraie d un homme de l ouest, lire
// la verite theta, ou devoiler nos hommes a l ennemi par commande. Ce fichier ne lit QUE la position CRUE
// que le moteur a donnee au camp est, avec son erreur. Si un jour quelqu un remplace ( _kn select 6 ) par getPos, l Oracle devient un mur et la mesure
// ne vaut plus rien.
// =====================================================================
if (MC4_ORACLE_CMD <= 0) exitWith {};

MC4_O_BUDGET = MC4_ORACLE_B;
MC4_O_CIBLE = -1;

// --- les cases : le couloir d approche, du poser au site, puis l exfiltration ---
private _mid = {
    params ["_a", "_b", "_t"];
    [(_a select 0) + (((_b select 0) - (_a select 0)) * _t), (_a select 1) + (((_b select 1) - (_a select 1)) * _t), 0]
};
private _lz = MC4_LZ; private _rt = MC4_ROUTE; private _op = MC4_OP; private _st = MC4_SITE;
private _ra = if (count MC4_RALLY > 1) then { MC4_RALLY } else { _lz };
MC4_O_CASES = [
    ["POSER",   _lz],
    ["APPROCHE_ROUTE", [_lz, _rt, 0.5] call _mid],
    ["ROUTE",   _rt],
    ["MONTEE",  [_rt, _op, 0.5] call _mid],
    ["CRETE",   _op],
    ["ABORDS",  [_op, _st, 0.6] call _mid],
    ["SITE",    _st],
    ["EXFIL",   _ra]
];
private _n = count MC4_O_CASES;
// ! V2 - UNE CONNAISSANCE DE DOCTRINE, PAS DE RENSEIGNEMENT. En v1 la croyance partait uniforme et restait plate
// ( cinq cases a 16 % ), et le commandant prenait toujours la premiere : le point de poser, sans route - il ne
// bougeait jamais sa patrouille. Un vrai chef sait une chose sans rien savoir du detachement : la route est le
// passage oblige entre la cote et le site. Sa croyance de depart pese donc plus sur la route et ses abords.
// Aucune information sur nos hommes n entre ici : c est la carte.
private _poids = [1, 2, 3, 1.5, 1, 1, 1, 0.5];
private _sp = 0; { _sp = _sp + _x } forEach _poids;
MC4_O_B = _poids apply { _x / _sp };
MC4_O_PRIOR = +MC4_O_B;   // la doctrine, gardee a part : c est vers elle que revient le doute
// les cases que la patrouille de route peut atteindre, et le troncon de route le plus proche de chacune
MC4_O_RTE = MC4_O_CASES apply {
    private _r = (_x select 1) nearRoads 400;
    if (count _r > 0) then { getPosATL (_r select 0) } else { [] }
};

// ! 20/09 : POURQUOI CERTAINS MONDES NE DONNENT AUCUNE PRISE. Calibration cd3a22f : monde 5, la patrouille
// n approche jamais a moins de 530 m et la CRETE n est jamais visee ; monde 12, elle n a que deux cases
// atteignables et ne depense que 1,6 ordre. Ailleurs, elle arrive a 5-35 m et compromet 38 a 62 % des episodes.
// La prise de l adversaire est donc une propriete de la ROUTE, pas du hasard. On la journalise a la mise en place,
// avant que quoi que ce soit bouge : nombre de cases atteignables a 400 m, et distance de chaque case a sa route
// la plus proche dans un rayon de 2 km ( -1 si aucune ). Cela rend l admissibilite d un monde MESURABLE.
private _carte = [];
{
    private _pc = _x select 1;
    private _r2 = _pc nearRoads 2000;
    private _d2 = if (count _r2 > 0) then { round (_pc distance2D (getPosATL (_r2 select 0))) } else { -1 };
    _carte pushBack [(_x select 0), (if (count (MC4_O_RTE select _forEachIndex) > 0) then {1} else {0}), _d2];
} forEach MC4_O_CASES;
(format ["CHACAL|O|carte|%1|cases_routieres|%2|detail|%3", round (time * 100) / 100,
    count (MC4_O_RTE select { count _x > 0 }), str _carte]) call MC4_LOG;

// --- probabilite de detecter a la distance _d : CALIBREE sur le banc de seuil du 19/09 ---
// de nuit, accroupi : sur dans les 125 m ; debout et designe : jusqu a ~250 m ; rare au-dela de 450 m.
MC4_O_fnc_pd = {
    params ["_d"];
    if (_d < 125) exitWith { 0.90 };
    if (_d < 250) exitWith { 0.35 };
    if (_d < 450) exitWith { 0.08 };
    0.01
};

// --- les yeux du camp est : les groupes qu il commande vraiment ---
MC4_O_fnc_yeux = {
    private _y = [];
    { if (!isNull _x) then { { if (alive _x) then { _y pushBack _x } } forEach (units _x) } } forEach
        ((MC4_GROUPES_EST + [MC4_gRoute]) select { !isNull _x });
    { if (alive _x && { !(_x in _y) }) then { _y pushBack _x } } forEach MC4_EST_SITE;
    _y
};

MC4_O_fnc_caseLaPlusProche = {
    params ["_p"];
    private _d = MC4_O_CASES apply { (_x select 1) distance2D _p };
    _d find (selectMin _d)
};

// --- un tour de croyance : on avance, puis on corrige par ce qu on a vu ET par ce qu on n a pas vu ---
MC4_O_fnc_croire = {
    private _n = count MC4_O_CASES;
    // 1. la marche : un detachement d infanterie progresse vers l objectif
    private _bp = [];
    for "_i" from 0 to (_n - 1) do {
        private _v = 0.70 * (MC4_O_B select _i);
        if (_i > 0) then { _v = _v + (0.30 * (MC4_O_B select (_i - 1))) } else { _v = _v + (0.30 * (MC4_O_B select _i)) };
        _bp pushBack _v;
    };
    // 2. ce que ses groupes savent : position CRUE, jamais la vraie
    private _vu = -1; private _fraicheur = 1e9;
    // ! targetKnowledge se demande a un HOMME, pas a un groupe ( « Type Group, expected Object » ), et son
    // premier champ est un BOOLEEN. C est ainsi que 60_phases.sqf l interroge deja, par les chefs.
    {
        private _chef = leader _x;
        if (!isNull _chef && { alive _chef }) then {
            {
                private _kn = _chef targetKnowledge _x;          // [ connu, connu_individu, vu_a, danger_a, camp, erreur, position CRUE ]
                if (_kn select 0) then {
                    private _age = time - (_kn select 2);
                    if (_age < 0) then { _age = 1e9 };
                    if (_age < _fraicheur) then { _fraicheur = _age; _vu = [(_kn select 6)] call MC4_O_fnc_caseLaPlusProche };
                };
            } forEach MC4_FS;                                  // on parcourt la liste, on ne lit QUE sa connaissance
        };
    } forEach ((MC4_GROUPES_EST + [MC4_gRoute]) select { !isNull _x });
    // 3. ce qu il n a pas vu : une case regardee et vide devient moins probable
    private _yeux = call MC4_O_fnc_yeux;
    private _l = [];
    for "_i" from 0 to (_n - 1) do {
        private _p = (MC4_O_CASES select _i) select 1;
        private _q = 1;
        { _q = _q * (1 - ([_x distance2D _p] call MC4_O_fnc_pd)) } forEach _yeux;
        _l pushBack _q;
    };
    if (_vu >= 0 && { _fraicheur < 120 }) then {
        for "_i" from 0 to (_n - 1) do { _l set [_i, (if (_i == _vu) then { 5 } else { 0.2 }) ] };
    };
    // 4. normaliser, puis douter ( un vrai chef se trompe )
    private _s = 0;
    for "_i" from 0 to (_n - 1) do { _bp set [_i, (_bp select _i) * (_l select _i)]; _s = _s + (_bp select _i) };
    if (_s <= 0) then { for "_i" from 0 to (_n - 1) do { _bp set [_i, 1 / _n] }; _s = 1 };
    private _nu = MC4_ORACLE_NU / 100;
    // ! V2.1 - LE DOUTE REVIENT A LA DOCTRINE, PAS A L UNIFORME. Fumee v2 : sans detection, la marche supposee
    // poussait la croyance vers l avant ( route 27 % -> 17 %, puis montee, puis crete ) et le commandant quittait
    // la route avant meme que le detachement l atteigne. Un chef qui doute revient a ce qu il sait : le passage oblige.
    for "_i" from 0 to (_n - 1) do { _bp set [_i, ((1 - _nu) * ((_bp select _i) / _s)) + (_nu * (MC4_O_PRIOR select _i))] };
    MC4_O_B = _bp;
    _vu
};

// --- agir : reorienter les postes ( gratuit ), deplacer la patrouille de route ( 1 point ) ---
MC4_O_fnc_agir = {
    params ["_cible"];
    private _p = (MC4_O_CASES select _cible) select 1;
    private _action = "REGARD";
    // les postes fixes tournent leur regard vers la case la plus probable
    { if (alive _x && { !(vehicle _x isKindOf "LandVehicle") }) then { _x doWatch _p } } forEach
        (MC4_EST_SITE select { alive _x });
    // ! V2 - LA PATROUILLE VISE LA MEILLEURE CASE QU ELLE PEUT ATTEINDRE, ET Y RESTE. En v1 elle visait la case la
    // plus probable meme sans route, et faisait un aller-retour avant de reprendre sa navette : elle ne chassait pas.
    // Ici elle ratisse 300 m de route autour de la case ou il nous croit, jusqu a la decision suivante.
    private _bR = MC4_O_B apply { 0 };
    { if (count (MC4_O_RTE select _forEachIndex) > 0) then { _bR set [_forEachIndex, _x] } } forEach MC4_O_B;
    private _mxR = selectMax _bR;
    private _candR = []; { if ((_x > 0) && { _x >= (_mxR - 0.01) }) then { _candR pushBack _forEachIndex } } forEach _bR;
    if (MC4_O_BUDGET > 0 && { count _candR > 0 } && { !isNull MC4_gRoute }
        && { ({ alive _x } count (units MC4_gRoute)) > 0 }) then {
        private _cibleR = if (MC4_O_CIBLE in _candR) then { MC4_O_CIBLE } else { selectRandom _candR };
        if (_cibleR != MC4_O_CIBLE) then {
            private _a = MC4_O_RTE select _cibleR;
            private _r2 = (_a nearRoads 350) select { (_x distance2D _a) > 250 };
            private _b2 = if (count _r2 > 0) then { getPosATL (_r2 select 0) } else { _a };
            while { (count (waypoints MC4_gRoute)) > 0 } do { deleteWaypoint ((waypoints MC4_gRoute) select 0) };
            private _w = MC4_gRoute addWaypoint [_a, 15];  _w setWaypointType "MOVE";  _w setWaypointSpeed "NORMAL";
            private _w2 = MC4_gRoute addWaypoint [_b2, 15]; _w2 setWaypointType "MOVE"; _w2 setWaypointSpeed "LIMITED";
            (MC4_gRoute addWaypoint [_a, 15]) setWaypointType "CYCLE";
            // ! V2.1 - DESIGNER LE POINT A SUIVRE. Fumee du 19/09 : apres le remplacement des points de passage, la
            // patrouille est restee a 923, 927 puis 930 m de sa cible - elle suivait encore son ancien parcours. Arma
            // ne remet pas a zero l indice du point courant quand on les efface : il faut le lui donner.
            MC4_gRoute setCurrentWaypoint _w;
            MC4_O_BUDGET = MC4_O_BUDGET - 1;
            MC4_O_CIBLE = _cibleR;
            _action = format ["PATROUILLE_%1", (MC4_O_CASES select _cibleR) select 0];
        };
    };
    _action
};

// --- la boucle de commandement ---
[] spawn {
    waitUntil { sleep 2; MC4_FIN || { !isNil "MC4_TPHASE" } };
    while { !MC4_FIN } do {
        private _vu = call MC4_O_fnc_croire;
        private _b = +MC4_O_B;
        // ! V2 : egalites departagees au hasard. En v1, find ( selectMax ) rendait TOUJOURS la premiere case ex aequo.
        private _mx = selectMax _b;
        private _cands = []; { if (_x >= (_mx - 0.01)) then { _cands pushBack _forEachIndex } } forEach _b;
        private _cible = selectRandom _cands;
        // il se trompe parfois : sans ca, la situation est deterministe et n apprend rien
        if ((random 1) < (MC4_ORACLE_EPS / 100)) then {
            private _c = +_b; _c set [_cible, -1];
            _cible = _c find (selectMax _c);
        };
        private _action = [_cible] call MC4_O_fnc_agir;
        private _dPat = if ((MC4_O_CIBLE >= 0) && { !isNull MC4_gRoute } && { !isNull (leader MC4_gRoute) }) then {
            round ((leader MC4_gRoute) distance2D (MC4_O_RTE select MC4_O_CIBLE)) } else { -1 };
        (format ["CHACAL|O|decision|%1|action|%2|case|%3|p|%4|vu|%5|budget|%6|croyance|%7|cible_patrouille|%8|patrouille_a|%9|vitesse_patrouille|%10",
            round (time * 100) / 100, _action, (MC4_O_CASES select _cible) select 0,
            round ((_b select _cible) * 100) / 100, (if (_vu >= 0) then { (MC4_O_CASES select _vu) select 0 } else { "RIEN" }),
            MC4_O_BUDGET, str (_b apply { round (_x * 100) }),
            (if (MC4_O_CIBLE >= 0) then { (MC4_O_CASES select MC4_O_CIBLE) select 0 } else { "AUCUNE" }), _dPat,
            (if (!isNull MC4_VEH_ROUTE) then { round (speed MC4_VEH_ROUTE) } else { -1 })]) call MC4_LOG;
        sleep (MC4_ORACLE_DELTA * MC4_ECHELLE);
    };
};
