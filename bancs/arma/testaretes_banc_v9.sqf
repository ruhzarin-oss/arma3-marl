// banc_v9.sqf — l emetteur v9 mis a l epreuve a densite reelle AVANT deploiement.
// On fabrique 260 hommes des deux camps qui se voient, on lance la capture, et on relit :
//   · le cout reel des noeuds et des aretes
//   · le FPS serveur
//   · l integrite des ticks (le total de morceaux doit permettre de detecter un trou)
//   · les aretes sont-elles ecrites, et disent-elles quelque chose ?
if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 10;
    private _base = [1700, 5450, 0];
    private _gE = createGroup east; private _gW = createGroup west;
    for "_i" from 0 to 259 do {
        // deux paquets qui se font face a 250 m : densite et contacts realistes
        private _p = if (_i % 2 == 0)
            then { _base vectorAdd [(random 200) - 100, (random 200) - 100, 0] }
            else { _base vectorAdd [(random 200) - 100, 250 + (random 200) - 100, 0] };
        private _u = ((if (_i % 2 == 0) then {_gE} else {_gW})
                      createUnit [(if (_i % 2 == 0) then {"O_Soldier_F"} else {"B_Soldier_F"}), _p, [], 0, "NONE"]);
        _u setPosATL _p; _u allowDamage false; _u disableAI "PATH"; _u setBehaviour "COMBAT";
    };
    sleep 5;
    (format ["HMT|B|foule|%1", count allUnits]) call HMT_LOG;
    [0, 0.2] execVM "hmt_capture.sqf";
};
