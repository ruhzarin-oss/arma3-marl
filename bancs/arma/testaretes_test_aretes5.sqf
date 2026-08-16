// test_aretes5.sqf — LE CONTRÔLE POSITIF, run final contre les critères figés.
//
// Ce que les quatre essais précédents ont établi, et qui est câblé ici :
//   v1 · le lecteur cassait sur la notation scientifique — corrigé côté Python
//   v2 · knowsAbout vaut ~2 à 300 m en terrain dégagé : la falaise des 100 m ne tient PAS
//        dans ces conditions. La coupure à 150 m prévue pour les arêtes jetterait du réel.
//   v3 · géométrie saine (terrain plat, rideau qui dépasse de 2,11 m) : ce n était pas le sol
//   v4 · dir 0 bloque, dir 90 non. Les CINQ sondes voient alors le couvert (1,00 / 0,00).
//        Et B2 gardait knowsAbout 4,00 derrière le mur : il avait été vu pendant les essais.
//        La connaissance PERSISTE. On pose donc le décor AVANT de créer qui que ce soit.
//
// La scène tourne 240 s pour laisser la détection s établir loin.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 8;
    private _base   = [1700, 5450, 0];
    private _milieu = _base vectorAdd [0, -25, 0];

    // ===== 1. LE DÉCOR D ABORD — personne ne doit avoir vu la cible avant qu elle soit couverte
    private _murs = [];
    for "_r" from 0 to 1 do {
        {
            private _m = createVehicle ["Land_CncWall4_F", [0,0,0], [], 0, "CAN_COLLIDE"];
            _m setDir 0;                                   // orientation validée en v4
            _m setPosATL [(_milieu select 0) + _x, (_milieu select 1), _r * 1.8];
            _murs pushBack _m;
        } forEach [-8, -4, 0, 4, 8];
    };
    sleep 2;
    (format ["HMT|G|decor|panneaux|%1|dir|0", count _murs]) call HMT_LOG;

    // ===== 2. LES UNITÉS, ensuite
    private _gE = createGroup east; private _gW = createGroup west;
    private _A  = _gE createUnit ["O_Soldier_F", _base, [], 0, "NONE"]; _A setPosATL _base;

    private _cibles = [];
    {
        private _p = _base vectorAdd (_x select 0);
        private _u = ((if ((_x select 2) == "AMI") then {_gE} else {_gW})
                       createUnit [(if ((_x select 2) == "AMI") then {"O_Soldier_F"} else {"B_Soldier_F"}),
                                   _p, [], 0, "NONE"]);
        _u setPosATL _p;
        _cibles pushBack [_u, (_x select 1)];
    } forEach [
        [[50, 0, 0],   "B1_ennemi_50m_degage",  "ENN"],
        [[0, -50, 0],  "B2_ennemi_50m_COUVERT", "ENN"],
        [[0, 300, 0],  "B3_ennemi_300m_degage", "ENN"],
        [[-50, 0, 0],  "C1_AMI_50m_degage",     "AMI"]
    ];

    { removeAllWeapons _x; _x allowDamage false; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT";
      _x setBehaviour "COMBAT"; _x setUnitPos "UP" } forEach ([_A] + (_cibles apply { _x select 0 }));
    _A setDir 0;
    sleep 2;

    HMT_BLOQUE = { params ["_o","_c"];
        count (lineIntersectsSurfaces [eyePos _o, aimPos _c, _o, _c, true, 16, "GEOM", "NONE"]) };

    {
        (format ["HMT|G|cible|%1|%2|dist|%3|inter|%4|host|%5", _forEachIndex, (_x select 1),
                 round (_A distance (_x select 0)), ([_A, (_x select 0)] call HMT_BLOQUE),
                 (if ((side (_x select 0)) == (side _A)) then {0} else {1})]) call HMT_LOG;
    } forEach _cibles;
    "HMT|OK|scene5|1" call HMT_LOG;

    // ===== 3. ÉMISSION — une ligne par LIEN, jamais de grille (la matrice est creuse)
    // La géométrie (distance, gisement) n est PAS émise : elle se recalcule hors ligne à
    // partir des positions. On ne paie en direct que ce que seul le moteur sait.
    private _n = 0;
    while { _n < 120 } do {                                 // 120 × 2 s = 240 s
        _n = _n + 1;
        private _t = round (time * 10) / 10;
        {
            private _B = _x select 0;
            private _i = lineIntersectsSurfaces [eyePos _A, aimPos _B, _A, _B, true, 1, "VIEW", "FIRE"];
            private _los = if (count _i == 0) then {1} else {0};
            private _vis = round (([objNull, "VIEW"] checkVisibility [eyePos _A, aimPos _B]) * 100) / 100;
            private _tk  = _A targetKnowledge _B;
            private _vu  = if ((count _tk) > 1 && {_tk select 1}) then {1} else {0};
            (format ["HMT|AR5|%1|%2|A|%3|k|%4|los|%5|vis|%6|vu|%7|host|%8",
                     _n, _t, (_x select 1),
                     (round ((_A knowsAbout _B) * 100) / 100), _los, _vis, _vu,
                     (if ((side _B) == (side _A)) then {0} else {1})]) call HMT_LOG;
        } forEach _cibles;
        sleep 2;
    };
    (format ["HMT|OK|aretes5|1|ticks|%1", _n]) call HMT_LOG;
};
"HMT|OK|test_aretes5|1" call HMT_LOG;
