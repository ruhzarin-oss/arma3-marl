// prevol_ecriture.sqf — COMMENT ÉCRIRE ? Le pre-vol a montre que le formatage coute plus
// que toutes les lectures reunies (104 ms contre 62 pour la plus chere des lectures).
//
// Younes : « c est pour ca que je te dis de tout prendre ». La mesure lui donne raison —
// lire est bon marche. Reste a savoir COMMENT ecrire sans payer.
//
// Quatre strategies, memes 260 entites, memes DIX nombres :
//   A · concatenation cumulative  _cour = _cour + _e     (ce que fait la v7 : quadratique)
//   B · pushBack dans un tableau puis joinString UNE fois
//   C · un appel a l extension native PAR entite          (zero concatenation)
//   D · lecture SEULE, sans rien ecrire                   (le plancher incompressible)

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];
    private _gE = createGroup east; private _gW = createGroup west;
    private _foule = [];
    for "_i" from 0 to 259 do {
        private _p = _base vectorAdd [(random 600) - 300, (random 600) - 300, 0];
        private _u = ((if (_i % 2 == 0) then {_gE} else {_gW})
                      createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}), _p, [], 0, "NONE"]);
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u setVariable ["hmt_id", _i + 1];
        _foule pushBack _u;
    };
    sleep 3;

    private _ext = ("hmt_native" callExtension "version");
    (format ["HMT|W|extension|%1", if (_ext == "") then {"ABSENTE"} else {_ext}]) call HMT_LOG;
    (format ["HMT|W|foule|%1", count _foule]) call HMT_LOG;

    // la lecture, identique pour les quatre — c est l ecriture qu on compare
    private _lire = {
        private _u = _this; private _p = getPosASL _u; private _d = eyeDirection _u;
        [(_u getVariable ["hmt_id", -1]),
         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10, (round ((_p select 2)*10))/10,
         (if (alive _u) then {1} else {0}), 0, 0,
         (round ((((_d select 0) atan2 (_d select 1)) + 360) % 360)),
         (switch (unitPos _u) do { case "UP": {0}; case "MIDDLE": {1}; case "DOWN": {2}; default {3} }), 0]
    };

    private _T = 20;

    // --- D : plancher, lecture seule
    private _t0 = diag_tickTime;
    for "_k" from 1 to _T do { { private _v = _x call _lire } forEach _foule };
    private _mD = (diag_tickTime - _t0) * 1000 / _T;

    // --- A : concatenation cumulative (la v7)
    _t0 = diag_tickTime;
    for "_k" from 1 to _T do {
        private _cour = "";
        { private _e = str (_x call _lire);
          _cour = if (_cour == "") then { _e } else { _cour + "," + _e } } forEach _foule;
    };
    private _mA = (diag_tickTime - _t0) * 1000 / _T;

    // --- B : tableau puis joinString
    _t0 = diag_tickTime;
    for "_k" from 1 to _T do {
        private _l = [];
        { _l pushBack (str (_x call _lire)) } forEach _foule;
        private _s = _l joinString ",";
    };
    private _mB = (diag_tickTime - _t0) * 1000 / _T;

    // --- C : un appel a l extension par entite
    private _mC = -1;
    if (_ext != "") then {
        _t0 = diag_tickTime;
        for "_k" from 1 to _T do {
            { "hmt_native" callExtension ("o|" + (str (_x call _lire))) } forEach _foule;
        };
        _mC = (diag_tickTime - _t0) * 1000 / _T;
    };

    // --- B' : tableau + joinString + UN SEUL appel a l extension (le candidat serieux)
    private _mE = -1;
    if (_ext != "") then {
        _t0 = diag_tickTime;
        for "_k" from 1 to _T do {
            private _l = [];
            { _l pushBack (str (_x call _lire)) } forEach _foule;
            "hmt_native" callExtension ("o|" + (_l joinString ","));
        };
        _mE = (diag_tickTime - _t0) * 1000 / _T;
    };

    // --- A' : la v7 complete, diag_log compris, decoupage en morceaux inclus
    _t0 = diag_tickTime;
    for "_k" from 1 to _T do {
        private _bouts = []; private _cour = "";
        { private _e = str (_x call _lire);
          if ((count _cour) + (count _e) + 1 > 700) then { _bouts pushBack _cour; _cour = "" };
          _cour = if (_cour == "") then { _e } else { _cour + "," + _e } } forEach _foule;
        _bouts pushBack _cour;
        { diag_log format ["HMT|Z|%1|%2|[%3]", _k, _forEachIndex, _x] } forEach _bouts;
    };
    private _mF = (diag_tickTime - _t0) * 1000 / _T;

    (format ["HMT|W|resultat|D_lecture_seule|%1|A_concat|%2|B_join|%3|C_ext_par_entite|%4|E_join_puis_ext|%5|F_v7_complete_diaglog|%6",
             (round (_mD*100))/100, (round (_mA*100))/100, (round (_mB*100))/100,
             (round (_mC*100))/100, (round (_mE*100))/100, (round (_mF*100))/100]) call HMT_LOG;
    "HMT|OK|prevol_ecriture|1" call HMT_LOG;
};
"HMT|OK|prevol_ecriture_lance|1" call HMT_LOG;
