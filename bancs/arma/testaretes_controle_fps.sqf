// controle_fps.sqf — LE CONTROLE QUI MANQUAIT.
// La capture v9 coute 20 ms/tick a 260 hommes et le serveur tombe a 5 FPS. Mais 5 FPS a
// 260 hommes en COMBAT, est-ce MOI ou est-ce ARMA ? Sans ce chiffre je ne sais pas ce que
// je mesure. ⟨regle du projet : une mesure doit pouvoir echouer, et il lui faut un temoin⟩
//
// Trois phases sur la MEME foule : a vide, puis noeuds seuls, puis tout.
if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];
    private _gE = createGroup east; private _gW = createGroup west;
    for "_i" from 0 to 259 do {
        private _p = if (_i % 2 == 0)
            then { _base vectorAdd [(random 200) - 100, (random 200) - 100, 0] }
            else { _base vectorAdd [(random 200) - 100, 250 + (random 200) - 100, 0] };
        private _u = ((if (_i % 2 == 0) then {_gE} else {_gW})
                      createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}), _p, [], 0, "NONE"]);
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u setBehaviour "COMBAT";
    };
    sleep 8;

    private _releve = {
        params ["_nom", "_duree"];
        private _f = [];
        for "_k" from 1 to _duree do { _f pushBack diag_fps; sleep 1 };
        private _s = 0; { _s = _s + _x } forEach _f;
        _f sort true;
        (format ["HMT|FPS|%1|moyen|%2|median|%3|min|%4|unites|%5", _nom,
                 (round ((_s / count _f)*10))/10,
                 (round ((_f select (floor ((count _f)/2)))*10))/10,
                 (round ((_f select 0)*10))/10, count allUnits]) call HMT_LOG;
    };

    // PHASE 1 — TEMOIN : 260 hommes en combat, AUCUNE capture
    ["temoin_sans_capture", 60] call _releve;

    // PHASE 2 — noeuds seuls
    HMT_SANS_ARETES = true;
    [0, 0.2] execVM "hmt_capture.sqf";
    sleep 20;
    ["avec_noeuds_seuls", 60] call _releve;

    // PHASE 3 — tout (les aretes se sont installees avec le reste)
    HMT_SANS_ARETES = false;
    sleep 20;
    ["avec_tout", 60] call _releve;

    "HMT|OK|controle_fps|1" call HMT_LOG;
};
