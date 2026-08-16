// ═══ LE BANC DES JAMBES, v3 ═══════════════════════════════════════════════════════════
// v1 MUETTE (controle positif echoue, aucun bras lu). v2 COUPEE AVANT LECTURE : relue
// pendant qu elle tournait, elle portait quatre trous dont deux invalidants. On ne lit pas
// les chiffres d un banc dont on vient de trouver les trous — meme s ils sont deja calcules.
//
// LES QUATRE, ET CE QU ILS AURAIENT FAIT
//   1. LES HOMMES N ETAIENT PAS ARMES. Le socle appelle `HMT_ARMER` (l.115) et le banc live
//      aussi. Un homme sans arme EN MAIN n est pas dans l etat du banc live : sa posture,
//      son animation et sa vitesse different. Corrige : `HMT_ARMER` sur chaque homme.
//   2. LE BRAS 7 NE REPRODUISAIT PAS T5. Il tirait par `forceWeaponFire`, alors que T5 laisse
//      l IA tirer par `AUTOCOMBAT` — mesure du 16/08, « le tir suit AUTOCOMBAT et rien
//      d autre ». Un bras cense mettre le verdict a l epreuve doit reproduire le geste EXACT.
//      Corrige : `reveal`, on ATTEND que l EH `Fired` compte, et le tir est PROUVE ou l essai
//      est ecarte ⟨regle 16 : juger l ACTE, pas l ETAT⟩.
//   3. LE TAUX D ITERATION N ETAIT PAS RELEVE. Les bras `vel` dependent du nombre
//      d impulsions emises, les bras `mov` non. Un serveur qui rame penalise donc les uns et
//      pas les autres, et l ecart se lirait comme une propriete des primitives. Corrige :
//      `_nt` et `diag_fps` journalises, et tout essai sous 25 iterations pour 3,28 s est
//      ECARTE — seuil pose ICI, avant de regarder quoi que ce soit.
//   4. `_py + 60 max (_d * 6)` — en SQF `+` lie plus fort que `max`, donc l expression valait
//      `(_py + 60) max (_d*6)`, soit toujours `_py + 60`. Sans effet pratique, mais une
//      intention non respectee dans un banc est une faute en attente. Parenthese.
//
// CE QUE CE BANC NE DIT PAS, et il faut le dire AVANT : il mesure la primitive en
// LABORATOIRE — un homme seul, sans ennemi, hors du feu. Le banc live fait courir quatre
// hommes en groupe sous le feu a 170 m. Ce banc ne prononce donc rien sur ce que la
// primitive rend EN COMBAT ; il repond a « qu est-ce qui deplace un fantassin », rien de plus.

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
    //          nom                       mode         prim  Z    forcer duree tir
    private _bras = [
        ["0_CONTROLE_natif_15s",       "natif",     "mov", 0.0, false, 15.0, false],
        ["1_pilote_vel_plat",          "pilote",    "vel", 0.0, false,  3.28,false],
        ["2_pilote_vel_haut",          "pilote",    "vel", 1.5, false,  3.28,false],
        ["3_pilote_domove",            "pilote",    "mov", 0.0, false,  3.28,false],
        ["4_natif_domove",             "natif",     "mov", 0.0, false,  3.28,false],
        ["5_sansengag_domove",         "sansengag", "mov", 0.0, false,  3.28,false],
        ["6_sansengag_domove_force",   "sansengag", "mov", 0.0, true,   3.28,false],
        ["7_REPRO_T5_temoin_apres_tir","temoin",    "vel", 0.0, false,  4.0, true ]
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
            if (isNull _u) then { (format ["HMT|JAMBES|ECHEC|%1", _nom]) call HMT_LOG } else {
                private _enmain = [_u] call HMT_ARMER;          // ⟨1⟩ comme le socle et le banc live
                [_u, _mode] call HMT_JB_PILOTER;
                _u setDir 0;
                sleep 2;
                private _coups = 0;
                if (_tir) then {
                    // ⟨2⟩ T5 A L IDENTIQUE : l IA tire d elle-meme par `AUTOCOMBAT`, on ne
                    // force RIEN, et on ATTEND l acte au lieu de le supposer.
                    HMT_JB_COUPS = 0;
                    private _eh = _u addEventHandler ["Fired", { HMT_JB_COUPS = HMT_JB_COUPS + 1 }];
                    private _gm = createGroup east;
                    private _mann = _gm createUnit ["O_Soldier_F", [_px, _py + 40, 0], [], 0, "NONE"];
                    [_mann] call HMT_ARMER;
                    sleep 0.5; _u reveal [_mann, 4];
                    private _ta = time;
                    waitUntil { sleep 0.2; HMT_JB_COUPS > 0 || time - _ta > 6 };
                    _coups = HMT_JB_COUPS;
                    _u removeEventHandler ["Fired", _eh];
                    deleteVehicle _mann; deleteGroup _gm; sleep 1;
                    _u doTarget objNull; _u doWatch objNull;
                };
                private _but = [_px, _py + (60 max (_d * 6)), 0];      // ⟨4⟩ parenthese
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
                // ⟨3⟩ `nt` et `fps` journalises : sans eux, un serveur qui rame se lirait
                // comme une propriete des primitives.
                (format ["HMT|JAMBES|bras|%1|rep|%2|m|%3|sol|%4|duree|%5|nt|%6|fps|%7|coups|%8|enmain|%9|anim|%10",
                         _nom, _r, round (10 * _m) / 10,
                         round (100 * _nsol / (_nt max 1)), _d, _nt,
                         round (diag_fps), _coups, _enmain, animationState _u]) call HMT_LOG;
                deleteVehicle _u;
            };
            deleteGroup _g;
            sleep 0.3;
        } forEach _bras;
    };
    (format ["HMT|JAMBES|FINI|%1", _nrep]) call HMT_LOG;
    true
};
