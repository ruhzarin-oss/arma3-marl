// sonde_terrain.sqf — CONTROLE POSITIF des deux capteurs de terrain, regle 16 clause 1.
//
// On ne repare pas un capteur qu on n a pas vu echouer pour la BONNE raison. Cette sonde
// mesure, sur 400 points de Stratis tires au hasard ET sur le site du banc live, ce que
// slope et dcover rendent vraiment — avec le seuil ACTUEL et avec le seuil CORRIGE.
//
// CE QUI LA FERAIT ECHOUER, ecrit avant de la lancer :
//   · si la mediane du gradient BRUT sur 400 points vaut 0, Stratis est plate et
//     slope=0 n est pas une panne mais une verite. La sonde le dira.
//   · si le seuil corrige ne fait pas remonter le taux de couvert trouve, mon
//     diagnostic arithmetique est FAUX et je ne touche pas au capteur.

HMT_LOG = { diag_log _this };
"HMT|ST|debut" call HMT_LOG;

HMT_GRAD = {
    params ["_cx", "_cy"];
    private _gx = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
    private _gy = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
    sqrt (_gx*_gx + _gy*_gy)
};

// distance de Tchebychev en cellules jusqu au premier point dont le gradient depasse _seuil
HMT_DCOVER = {
    params ["_px", "_py", "_seuil", "_kmax"];
    private _dcell = 16;
    private _k = 0;
    while { _k <= _kmax && _dcell >= 16 } do {
        private _trouve = false;
        for "_a" from -_k to _k do {
            for "_bb" from -_k to _k do {
                if (!_trouve && {(abs _a == _k) || (abs _bb == _k)}) then {
                    if (([_px + _a*6.25, _py + _bb*6.25] call HMT_GRAD) > _seuil) then {
                        _dcell = _k; _trouve = true;
                    };
                };
            };
        };
        _k = _k + 1;
    };
    _dcell
};

[] spawn {
    private _MOY_BRUT = 0.463;          // pente moyenne de Stratis, m/cellule (mesure, 403 points)
    private _S_ACTUEL = 1.4 * 2.315;    // le seuil EN SERVICE  = 3,241  (le x5 de trop)
    private _S_CORRIGE = 1.4 * _MOY_BRUT;   // le seuil CORRIGE = 0,648

    // ─── 1. 400 points au hasard sur Stratis (hors mer)
    private _pts = [];
    while { count _pts < 400 } do {
        private _c = [random 8000, random 8000];
        if ((getTerrainHeightASL _c) > 2) then { _pts pushBack _c };
    };
    // ─── 2. le SITE du banc live, 60 points dans un rayon de 200 m
    private _obj = [1734, 5391];
    for "_i" from 1 to 60 do {
        _pts pushBack [(_obj select 0) + (random 400) - 200, (_obj select 1) + (random 400) - 200];
    };

    {
        private _g = _x call HMT_GRAD;
        private _d0 = [_x select 0, _x select 1, _S_ACTUEL,  8]  call HMT_DCOVER;
        private _d1 = [_x select 0, _x select 1, _S_CORRIGE, 16] call HMT_DCOVER;
        (format ["HMT|ST|PT|%1|grad|%2|slope|%3|dc_actuel|%4|dc_corrige|%5|site|%6",
                 _forEachIndex, _g, _g/5, _d0, _d1,
                 (if (_forEachIndex >= 400) then {1} else {0})]) call HMT_LOG;
        if (_forEachIndex % 50 == 0) then { sleep 0.01 };
    } forEach _pts;

    "HMT|ST|TERMINE" call HMT_LOG;
};
