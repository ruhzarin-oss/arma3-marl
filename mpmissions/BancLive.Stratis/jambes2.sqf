// ═══ LE BANC DES JAMBES II — LIEU × COMPORTEMENT ═══════════════════════════════════════
// ⚠️ « LE CORPS REND 62 % DES JAMBES DU GYMNASE » EST PEUT-ETRE UNE GRANDEUR COMPOSITE.
// Mesure du 16/08 : 12,2 m en 3,28 s au banc des jambes, soit 3,72 m/s. Mesure du 17/08 :
// 25 m en 4 s au placeur, soit 6,25 m/s — et le gymnase suppose 6 m/s, que le placeur ATTEINT.
// Facteur 1,68 entre deux mesures du meme corps. Deux suspects, non departages :
//   · LE LIEU — le banc des jambes tirait ses positions au hasard dans +/-60 m et ne filtrait
//     que l eau ; le placeur ne mesure que sur des lieux qu il vient de RECEVOIR.
//   · LE COMPORTEMENT — l homme servi vit en AWARE (`arma_couture.py:27`) quand tous les
//     bancs testent en COMBAT RED (`HMT_PILOTER`). Les `disableAI` sont identiques des deux
//     cotes ; le `setBehaviour` ne l est pas ⟨lecture de Fable, 17/08⟩.
//
// PLAN 2x2 : {lieu RECU, lieu ALEATOIRE} x {AWARE, COMBAT}. Les memes lieux servent aux deux
// comportements, sans quoi on melangerait encore deux facteurs.
//
// CRITERES ECRITS AVANT — grandeur : metres parcourus en 3,28 s (la fenetre du gymnase) ;
// statistique : MEDIANE par condition ; n minimum : 8 par condition, en deca on ne lit pas.
//   · LE LIEU EXPLIQUE ...... les lieux recus battent les aleatoires DANS LES DEUX comportements
//   · LE MODE EXPLIQUE ...... AWARE bat COMBAT DANS LES DEUX lieux
//   · LES DEUX EXPLIQUENT ... les deux ecarts existent
//   · AUCUN N EXPLIQUE ...... pas de separation, et le 62 % tient tel quel
// Reference : 19,7 m = 6 m/s x 3,28 s, ce que le gymnase suppose.

HMT_JAMBES2 = {
    params [["_n", 8]];
    private _cx = 4644; private _cy = 5652;
    // ── 1 · huit lieux RECUS par le placeur v2, et huit tires AU HASARD sans filtre
    private _recus = []; private _hasard = []; private _essais = 0;
    while { count _recus < _n && _essais < 60 } do {
        _essais = _essais + 1;
        private _a = random 360; private _r = 150 + random 250;
        private _c = [_cx + _r * sin _a, _cy + _r * cos _a];
        private _v = [_c] call HMT_G_PRATICABLE;
        if ((_v select 0) == "recu") then { _recus pushBack _c };
    };
    for "_i" from 1 to _n do {
        private _a = random 360; private _r = 150 + random 250;
        _hasard pushBack [_cx + _r * sin _a, _cy + _r * cos _a];
    };
    (format ["HMT|J2|LIEUX|recus|%1|essais|%2|hasard|%3", count _recus, _essais, count _hasard]) call HMT_LOG;
    if (count _recus < _n) exitWith {
        (format ["HMT|J2|ECHEC|seulement %1 lieux recus sur %2 demandes", count _recus, _n]) call HMT_LOG;
        false
    };
    // ── 2 · les quatre conditions, memes lieux pour les deux comportements
    {
        private _nomL = _x select 0; private _lieux = _x select 1;
        {
            private _comp = _x;
            {
                private _c = _x; private _i = _forEachIndex;
                private _g = createGroup west;
                private _u = _g createUnit ["B_Soldier_F", [_c select 0, _c select 1, 0], [], 0, "NONE"];
                if (!isNull _u) then {
                    [_u] call HMT_ARMER;
                    // le pilotage du SERVI : AUTOCOMBAT et FSM coupes — c est le `setBehaviour`
                    // qu on fait varier, et lui seul.
                    _u enableAI "ALL"; _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
                    _u setBehaviour _comp; _u setCombatMode "RED"; _u allowFleeing 0;
                    _u allowDamage false;      // tout homme jetable est invulnerable
                    _u setDir 0;
                    sleep 2;
                    private _mnt = [_u, 3.28] call HMT_MARCHER;    // LA fenetre du gymnase
                    (format ["HMT|J2|lieu|%1|comp|%2|i|%3|m|%4|nt|%5|x|%6|y|%7",
                             _nomL, _comp, _i, round ((_mnt select 0) * 10) / 10, _mnt select 1,
                             round (_c select 0), round (_c select 1)]) call HMT_LOG;
                    deleteVehicle _u;
                };
                deleteGroup _g;
                sleep 0.3;
            } forEach _lieux;
        } forEach ["AWARE", "COMBAT"];
    } forEach [["recu", _recus], ["hasard", _hasard]];
    "HMT|J2|FINI" call HMT_LOG;
    true
};
