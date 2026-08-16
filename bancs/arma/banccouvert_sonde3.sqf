// sonde3.sqf — DEUX SCRIPTS, MEME LIEU, 64 % CONTRE 10 %. Lequel ment ?
// On calcule le lieu n°3 des DEUX facons dans la MEME session, pas a pas, et on imprime tout.
if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 20;
    private _cou = [4355,6210,0];      // couvert d arrivee
    private _dep = [4595,6210,0];      // depart
    private _pos = [4475,6085,0];      // poste de tir
    private _a = _dep; private _b = _cou;
    private _d = _a distance2D _b;
    private _pas = round (_d / 10) max 1;
    (format ["HMT|SD|geo|d|%1|pas|%2", round _d, _pas]) call HMT_LOG;

    private _m1 = ""; private _m2 = "";
    for "_k" from 0 to _pas do {
        private _f = _k / _pas;
        private _p = [(_a select 0) + ((_b select 0) - (_a select 0)) * _f,
                      (_a select 1) + ((_b select 1) - (_a select 1)) * _f, 0];
        // FACON A — celle de verif_couvert (HMT_MESURE)
        private _p1 = AGLToASL [_pos select 0, _pos select 1, 1.2];
        private _p2 = AGLToASL [_p select 0, _p select 1, 1.2];
        private _r1 = lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1];
        // FACON B — celle de verif_bruit (HMT_MASQUE) : STRICTEMENT LA MEME FORMULE.
        private _q1 = AGLToASL [_pos select 0, _pos select 1, 1.2];
        private _q2 = AGLToASL [_p select 0, _p select 1, 1.2];
        private _r2 = lineIntersectsSurfaces [_q1, _q2, objNull, objNull, true, 1];
        _m1 = _m1 + (if (count _r1 == 0) then {"1"} else {"0"});
        _m2 = _m2 + (if (count _r2 == 0) then {"1"} else {"0"});
        if (_k < 4) then {
            (format ["HMT|SD|pas|%1|p|%2|%3|p1|%4|p2|%5|bloque1|%6|bloque2|%7",
                     _k, round (_p select 0), round (_p select 1),
                     str (_p1 apply {round _x}), str (_p2 apply {round _x}),
                     count _r1, count _r2]) call HMT_LOG;
        };
    };
    (format ["HMT|SD|masqueA|%1", _m1]) call HMT_LOG;
    (format ["HMT|SD|masqueB|%1", _m2]) call HMT_LOG;
    (format ["HMT|SD|BILAN|A|%1|B|%2|sur|%3|identiques|%4",
             count (toArray _m1 select {_x == 49}), count (toArray _m2 select {_x == 49}),
             _pas + 1, (if (_m1 == _m2) then {1} else {0})]) call HMT_LOG;
    "HMT|SD|TERMINE|1" call HMT_LOG;
};
