// ═══ LE BANC DES JAMBES ═══════════════════════════════════════════════════════════════
// La question : quelle primitive deplace un fantassin POSE sur Arma ?
//
// Nee du VERDICT_JAMBES du 16/08 : `setVelocity` a Z = 0 rend 25 m quand l homme NE TOUCHE
// PAS le sol (animation `afal`, il tombe) et 0-1 m quand il le touche — separation parfaite
// sur 4 tirages. Et `arma_couture.py:185` deplace l agent avec CETTE primitive exacte.
//
// ⚠️ ON CROISE LA PRIMITIVE ET LE MODE, JAMAIS LA PRIMITIVE SEULE. Le mode « pilote » du banc
// coupe `FSM`, et il est DEJA mesure (15/08) que sans FSM les hommes ne suivent plus leur
// point de passage : 0,07 m par pas. `doMove` et le pilotage en service sont donc
// incompatibles PAR CONSTRUCTION. Un banc qui ne testerait que la primitive lirait cette
// incompatibilite comme une propriete de `doMove`, et se tromperait.
//
// Deux grandeurs par essai, parce qu une seule ne separe pas : les metres parcourus disent
// COMBIEN, la part de temps au sol dit SI C EST UNE MARCHE OU UN VOL.

HMT_JB_PILOTER = {
    params ["_u", "_mode"];
    // « sansengag » n existe pas dans le socle et n y sera pas ajoute : le socle est certifie,
    // on ne le retouche pas pour les besoins d un banc. C est le candidat interessant — il
    // garde `FSM` (donc la machine qui sait marcher) et ne retire que l engagement autonome.
    if (_mode == "sansengag") then {
        _u enableAI "ALL"; _u disableAI "AUTOCOMBAT";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    } else { [_u, _mode] call HMT_PILOTER };
};

HMT_JAMBES = {
    params ["_nrep"];
    private _cx = 4644; private _cy = 5652;      // le site certifie, VERDICT_SITE_LIVE.md
    //          nom                   mode         primitive  Z    forcer
    private _bras = [
        ["1_pilote_vel_plat",       "pilote",    "vel", 0.0,   false],   // LE BRAS EN SERVICE
        ["2_pilote_vel_haut",       "pilote",    "vel", 1.5,   false],
        ["3_pilote_domove",         "pilote",    "mov", 0.0,   false],
        ["4_natif_domove",          "natif",     "mov", 0.0,   false],   // CONTROLE POSITIF
        ["5_sansengag_domove",      "sansengag", "mov", 0.0,   false],
        ["6_sansengag_domove_force","sansengag", "mov", 0.0,   true ]
    ];
    for "_r" from 1 to _nrep do {
        {
            private _nom=_x select 0; private _mode=_x select 1;
            private _k=_x select 2; private _vz=_x select 3; private _f=_x select 4;
            // Position tiree a neuf a chaque essai : un banc qui rejoue toujours le meme
            // metre carre mesure ce metre carre. Les bras sont alternes DANS la repetition,
            // donc une derive du serveur les frappe tous pareil.
            private _px = _cx + (random 120) - 60; private _py = _cy + (random 120) - 60;
            if (surfaceIsWater [_px,_py]) then { _px = _cx; _py = _cy };
            private _g = createGroup west;
            private _u = _g createUnit ["B_Soldier_F", [_px,_py,0], [], 0, "NONE"];
            if (isNull _u) then { (format ["HMT|JAMBES|ECHEC|%1", _nom]) call HMT_LOG } else {
                [_u, _mode] call HMT_JB_PILOTER;
                _u setDir 0;
                sleep 2;                         // qu il se pose et finisse sa mise en place
                private _but = [_px, _py + 60, 0];
                private _p0 = getPosATL _u; private _nsol=0; private _nt=0;
                if (_k == "mov") then {
                    if (_f) then { _u forceSpeed 6 };
                    _u doMove _but;
                };
                private _t0 = time;
                while { alive _u && time - _t0 < 3.28 } do {
                    if (_k == "vel") then { _u setVelocity [0, 6, _vz] };
                    _nt = _nt + 1;
                    if (isTouchingGround _u) then { _nsol = _nsol + 1 };
                    sleep 0.1;
                };
                private _m = _p0 distance2D (getPosATL _u);
                (format ["HMT|JAMBES|bras|%1|rep|%2|m|%3|sol|%4|anim|%5|x|%6|y|%7",
                         _nom, _r, round (10 * _m) / 10,
                         round (100 * _nsol / (_nt max 1)),
                         animationState _u, round _px, round _py]) call HMT_LOG;
                deleteVehicle _u;
            };
            deleteGroup _g;
            sleep 0.3;
        } forEach _bras;
    };
    (format ["HMT|JAMBES|FINI|%1", _nrep]) call HMT_LOG;
    true
};
