// ═══ LE BANC DES JAMBES, v2 ═══════════════════════════════════════════════════════════
// La v1 est MUETTE par son propre controle positif : `natif+doMove` a rendu 3,8 m pour un
// seuil pose a 5. Aucun bras n a ete lu, et aucun seuil n a ete retouche apres coup.
//
// ⚠️ LA FAUTE DE CONCEPTION, ET ELLE SE NOMME SANS REGARDER LES CHIFFRES : mon controle
// positif ne testait pas l INSTRUMENT, il testait deja le PHENOMENE. « doMove fait-il 5 m
// en 3,28 s » EST la question du banc, demarrage compris — ce n est pas un controle, c est
// un resultat deguise. Un controle demande seulement : ce banc sait-il faire marcher un
// homme ? On le pose donc sur une fenetre LONGUE, ou le demarrage ne pese plus.
//
// ⚠️ ET LE BANC MET LE VERDICT DU JOUR A L EPREUVE. Le bras 7 reproduit T5 A L IDENTIQUE
// (mode temoin, apres un tir force) : si T5 rend 1 m quand le bras 1 en rend 11, la cause
// n est pas la primitive mais l ETAT de l homme, et VERDICT_JAMBES.md tombe de lui-meme.
// Un banc qui ne peut pas contredire celui qui l a fait naitre ne sert a rien.

HMT_JB_PILOTER = {
    params ["_u", "_mode"];
    if (_mode == "sansengag") then {
        _u enableAI "ALL"; _u disableAI "AUTOCOMBAT";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0;
    } else { [_u, _mode] call HMT_PILOTER };
};

HMT_JAMBES = {
    params ["_nrep"];
    private _cx = 4644; private _cy = 5652;
    //          nom                     mode         prim  Z    forcer duree tir
    private _bras = [
        ["0_CONTROLE_natif_15s",      "natif",     "mov", 0.0, false, 15.0, false],
        ["1_pilote_vel_plat",         "pilote",    "vel", 0.0, false,  3.28,false],
        ["2_pilote_vel_haut",         "pilote",    "vel", 1.5, false,  3.28,false],
        ["3_pilote_domove",           "pilote",    "mov", 0.0, false,  3.28,false],
        ["4_natif_domove",            "natif",     "mov", 0.0, false,  3.28,false],
        ["5_sansengag_domove",        "sansengag", "mov", 0.0, false,  3.28,false],
        ["6_sansengag_domove_force",  "sansengag", "mov", 0.0, true,   3.28,false],
        ["7_REPRO_T5_temoin_apres_tir","temoin",   "vel", 0.0, false,  4.0, true ]
    ];
    for "_r" from 1 to _nrep do {
        {
            private _nom=_x select 0; private _mode=_x select 1; private _k=_x select 2;
            private _vz=_x select 3; private _f=_x select 4; private _d=_x select 5;
            private _tir=_x select 6;
            private _px = _cx + (random 120) - 60; private _py = _cy + (random 120) - 60;
            if (surfaceIsWater [_px,_py]) then { _px = _cx; _py = _cy };
            private _g = createGroup west;
            private _u = _g createUnit ["B_Soldier_F", [_px,_py,0], [], 0, "NONE"];
            private _gm = grpNull; private _mann = objNull;
            if (isNull _u) then { (format ["HMT|JAMBES|ECHEC|%1", _nom]) call HMT_LOG } else {
                [_u, _mode] call HMT_JB_PILOTER;
                _u setDir 0;
                sleep 2;
                if (_tir) then {
                    // T5 a l identique : un ennemi nait a 40 m, l homme le voit et tire.
                    _gm = createGroup east;
                    _mann = _gm createUnit ["O_Soldier_F", [_px, _py + 40, 0], [], 0, "NONE"];
                    sleep 1;
                    _u reveal [_mann, 4]; _u doTarget _mann;
                    _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
                    sleep 1;
                    deleteVehicle _mann; deleteGroup _gm; sleep 1;
                    _u doTarget objNull; _u doWatch objNull;
                };
                private _but = [_px, _py + 60 max (_d * 6), 0];
                private _p0 = getPosATL _u; private _nsol=0; private _nt=0;
                if (_k == "mov") then { if (_f) then { _u forceSpeed 6 }; _u doMove _but };
                private _t0 = time;
                while { alive _u && time - _t0 < _d } do {
                    if (_k == "vel") then { _u setVelocity [0, 6, _vz] };
                    _nt = _nt + 1;
                    if (isTouchingGround _u) then { _nsol = _nsol + 1 };
                    sleep 0.1;
                };
                private _m = _p0 distance2D (getPosATL _u);
                (format ["HMT|JAMBES|bras|%1|rep|%2|m|%3|sol|%4|duree|%5|anim|%6",
                         _nom, _r, round (10 * _m) / 10,
                         round (100 * _nsol / (_nt max 1)), _d, animationState _u]) call HMT_LOG;
                deleteVehicle _u;
            };
            deleteGroup _g;
            sleep 0.3;
        } forEach _bras;
    };
    (format ["HMT|JAMBES|FINI|%1", _nrep]) call HMT_LOG;
    true
};
