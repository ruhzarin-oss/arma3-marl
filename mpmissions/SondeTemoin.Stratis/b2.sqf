// ═══ B2 — LE CERTIFICATEUR TIRE-T-IL PAR LE CANAL DE L HOMME SERVI ? ═══════════════════
// ⚠️ TROIS DIVERGENCES LUES ENTRE LE CERTIFICATEUR ET LE SERVI ⟨Fable, 17/08⟩ :
//   (a) T7 et l acte 3 font `reveal [cible, 4]` — `arma_couture.py:ACT_TPL` (action 9) ne
//       fait JAMAIS de `reveal` ;
//   (b) le socle fait `doWatch` sur un OBJET, la couture sur une POSITION ;
//   (c) l homme servi vit en AWARE (`arma_couture.py:27`), tous les bancs testent en COMBAT.
// Les `disableAI` sont identiques des deux cotes ; le `setBehaviour` ne l est pas.
//
// ⚠️ ET UN ACCIDENT A DEJA POINTE LA REPONSE : le refactoring B1 a supprime le `reveal` de
// l acte 3, et le placeur s est mis a rendre « muet » sur des lieux a vue 1 — ZERO coup.
// Un accident n est pas une mesure : on la fait proprement.
//
// PLAN 2x2 : {avec reveal, sans reveal} x {COMBAT, AWARE}, SUR LIEUX CERTIFIES, pour ne pas
// re-melanger le terrain — la lecon du banc des jambes II.
//
// CRITERES ECRITS AVANT — grandeur : coups tires en 4 s par le canal de l action 9 ;
// statistique : MEDIANE par condition ; n minimum : 8 par condition.
//   · LE `reveal` EST NECESSAIRE ... avec >= 1 coup median ET sans = 0, dans LES DEUX
//     comportements. Alors T7 certifie un canal QUE LA POLITIQUE N EMPRUNTE PAS.
//   · LE `reveal` EST INUTILE ...... sans reveal rend aussi >= 1 coup median.
//   · LE COMPORTEMENT COMPTE ....... ecart net entre AWARE et COMBAT a `reveal` fixe.

HMT_B2 = {
    params [["_n", 8]];
    private _cx = 4644; private _cy = 5652;
    private _lieux = []; private _essais = 0;
    while { count _lieux < _n && _essais < 60 } do {
        _essais = _essais + 1;
        private _a = random 360; private _r = 150 + random 250;
        private _c = [_cx + _r * sin _a, _cy + _r * cos _a];
        if ((([_c] call HMT_G_PRATICABLE) select 0) == "recu") then { _lieux pushBack _c };
    };
    (format ["HMT|B2|LIEUX|certifies|%1|essais|%2", count _lieux, _essais]) call HMT_LOG;
    if (count _lieux < _n) exitWith { "HMT|B2|ECHEC|pas assez de lieux certifies" call HMT_LOG; false };
    {
        private _rev = _x;
        {
            private _comp = _x;
            {
                private _c = _x; private _i = _forEachIndex;
                private _gE = createGroup east;
                private _m = _gE createUnit ["O_Soldier_F", [_c select 0, (_c select 1) + 40, 0], [], 0, "NONE"];
                _m allowDamage false; _m disableAI "AUTOCOMBAT"; _m disableAI "FSM";
                _m setBehaviour "CARELESS"; [_m] call HMT_ARMER;
                private _gW = createGroup west;
                private _u = _gW createUnit ["B_Soldier_F", [_c select 0, _c select 1, 0], [], 0, "NONE"];
                [_u] call HMT_ARMER;
                // l etat EXACT de l homme servi, sauf le `setBehaviour` qu on fait varier
                _u enableAI "ALL"; _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
                _u setBehaviour _comp; _u setCombatMode "RED"; _u allowFleeing 0;
                _u allowDamage false;
                sleep 1.5;
                if (_rev) then { _u reveal [_m, 4] };
                private _coups = [_u, _m, 4] call HMT_TIRER_C9;
                (format ["HMT|B2|reveal|%1|comp|%2|i|%3|coups|%4|vue|%5",
                         _rev, _comp, _i, _coups,
                         round (100 * ([objNull,"VIEW"] checkVisibility [eyePos _u, eyePos _m])) / 100]) call HMT_LOG;
                deleteVehicle _m; deleteVehicle _u; deleteGroup _gE; deleteGroup _gW;
                sleep 0.3;
            } forEach _lieux;
        } forEach ["COMBAT", "AWARE"];
    } forEach [true, false];
    "HMT|B2|FINI" call HMT_LOG;
    true
};
