// sonde_dcover.sqf — verifier l etalonnage de dcover AVANT de le deployer.
// Criteres dans DEPOT_DCOVER.md, deposes avant cette mesure.
HMT_LOG = { diag_log _this };
HMT_GRAD = {
    params ["_cx","_cy"];
    private _gx = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
    private _gy = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
    sqrt (_gx*_gx + _gy*_gy)
};
// moyenne locale sur 64x64 cellules de 6,25 m — exactement ce que la greffe calcule
HMT_MOY = {
    params ["_o"];
    private _s = 0; private _n = 0;
    for "_a" from -32 to 31 do {
        for "_bb" from -32 to 31 do {
            _s = _s + ([(_o select 0) + _a*6.25, (_o select 1) + _bb*6.25] call HMT_GRAD); _n = _n + 1;
        };
    };
    _s / _n
};
HMT_DC = {
    params ["_px","_py","_seuil","_kmax"];
    private _dcell = 16; private _k = 0;
    while { _k <= _kmax && _dcell >= 16 } do {
        private _trouve = false;
        for "_a" from -_k to _k do {
            for "_bb" from -_k to _k do {
                if (!_trouve && {(abs _a == _k) || (abs _bb == _k)}) then {
                    if (([_px + _a*6.25, _py + _bb*6.25] call HMT_GRAD) > _seuil) then { _dcell = _k; _trouve = true };
                };
            };
        };
        _k = _k + 1;
    };
    _dcell
};
[] spawn {
    // les DEUX sites : l ancien (plat, ou la panne est connue) et le nouveau
    { 
        private _o = _x select 0; private _nom = _x select 1;
        private _moy = [_o] call HMT_MOY;
        (format ["HMT|DC|site|%1|moy_locale|%2|seuil_nouveau|%3|seuil_ancien|%4",
                 _nom, _moy, 1.4*_moy, 1.4*2.315]) call HMT_LOG;
        // les points que les hommes TRAVERSENT : rayons de 170 m vers 25 m
        for "_r" from 1 to 24 do {
            private _az = random 360;
            for "_d" from 0 to 7 do {
                private _dist = 170 - _d * 20;
                private _px = (_o select 0) + _dist * sin _az;
                private _py = (_o select 1) + _dist * cos _az;
                (format ["HMT|DC|PT|%1|dist|%2|ancien|%3|nouveau|%4",
                         _nom, _dist,
                         [_px,_py, 1.4*2.315, 8]  call HMT_DC,
                         [_px,_py, 1.4*_moy,  15] call HMT_DC]) call HMT_LOG;
            };
        };
        sleep 0.01;
    } forEach [[[1734,5391], "PLAT"], [[4644,5652], "NOUVEAU"]];
    "HMT|DC|TERMINE" call HMT_LOG;
};
