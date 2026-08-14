// choix_site.sqf — CHOISIR LE SITE DU BANC LIVE. Criteres deposes dans DEPOT_CHOIX_SITE.md
// AVANT cette mesure. Ce script ne choisit pas : il MESURE et journalise. Le choix se fait
// au depouillement, par la regle deja ecrite.

HMT_LOG = { diag_log _this };
"HMT|CS|debut" call HMT_LOG;

HMT_GRAD = {
    params ["_cx", "_cy"];
    private _gx = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
    private _gy = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
    sqrt (_gx*_gx + _gy*_gy)
};

// EXACTEMENT le dcover EN SERVICE : seuil 1.4 x 2.315, recherche k <= 8, garde-fou 16.
// On ne le repare pas ici — on mesure ce que le banc verra vraiment.
HMT_DCOVER = {
    params ["_px", "_py"];
    private _seuil = 1.4 * 2.315;
    private _dcell = 16; private _k = 0;
    while { _k <= 8 && _dcell >= 16 } do {
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
    private _cands = [];
    private _essais = 0;
    while { count _cands < 80 && _essais < 4000 } do {
        _essais = _essais + 1;
        private _c = [300 + random 7400, 300 + random 7400];
        // terre ferme, et le disque de 200 m aussi : quatre sondes cardinales hors de l eau
        if ((getTerrainHeightASL _c) > 8
            && {(getTerrainHeightASL [(_c select 0)+200, _c select 1]) > 3}
            && {(getTerrainHeightASL [(_c select 0)-200, _c select 1]) > 3}
            && {(getTerrainHeightASL [_c select 0, (_c select 1)+200]) > 3}
            && {(getTerrainHeightASL [_c select 0, (_c select 1)-200]) > 3}) then {
            _cands pushBack _c;
        };
    };
    (format ["HMT|CS|candidats|%1|essais|%2", count _cands, _essais]) call HMT_LOG;

    {
        private _o = _x;
        for "_j" from 1 to 30 do {
            private _ang = random 360; private _r = sqrt (random 1) * 200;
            private _px = (_o select 0) + _r * (sin _ang);
            private _py = (_o select 1) + _r * (cos _ang);
            private _g = [_px, _py] call HMT_GRAD;
            (format ["HMT|CS|PT|%1|ox|%2|oy|%3|slope|%4|dcell|%5",
                     _forEachIndex, round (_o select 0), round (_o select 1),
                     _g/5, [_px, _py] call HMT_DCOVER]) call HMT_LOG;
        };
        sleep 0.01;
    } forEach _cands;

    "HMT|CS|TERMINE" call HMT_LOG;
};
