// ═══ DEUX SONDES ⟨prescrites par Fable, 18/08⟩ ═══════════════════════════════════════════
// SONDE 1 · LE POINT MAUDIT (4629, 5856). Cinq echecs T7 du lot 5 = UN SEUL point, recu cinq
// fois par l anneau fixe de session. L acte 3 du placeur y tire 5/5 ; T7 y rend 0/5. Ce ne
// sont pas deux tests differents mais DEUX COPIES MANUELLES DU MEME ACTE qui ont diverge.
// Divergences enumerees par lecture, on en bascule UNE A LA FOIS, `PATH` en premier :
//   A · replique ACTE 3  : mannequin GARDE `PATH`, tireur par `createUnit`
//   B · replique T7      : mannequin `disableAI "PATH"`, tireur par `HMT_POSER_HOMME`
//   C · A mais PATH coupe: isole l effet du seul `PATH` du mannequin
// PREDICTION PRE-ENREGISTREE : si `PATH` est le coupable, A tire et B se tait, et C se tait
// comme B. Si C tire comme A, `PATH` est innocent et le suspect suivant est la naissance.
// ⚠️ ON JOURNALISE LA VUE DES DEUX COTES — l acte 3 n en avait aucune, c est ce qui a permis
// a la divergence de vivre.
HMT_SONDE1 = {
    params [["_n", 10]];
    private _x = 4629; private _y = 5856;
    {
        private _bras = _x;
        for "_k" from 1 to _n do {
            private _gE = createGroup east; private _gW = createGroup west;
            private _m = objNull; private _u = objNull;
            // ── le mannequin, selon le bras
            _m = _gE createUnit ["O_Soldier_F", [_x, _y + 40, 0], [], 0, "NONE"];
            [_m] call HMT_ARMER;
            _m allowDamage false; _m disableAI "AUTOCOMBAT"; _m disableAI "FSM";
            _m setBehaviour "CARELESS";
            if (_bras != "A") then { _m disableAI "PATH" };      // B et C coupent PATH
            // ── le tireur, selon le bras
            if (_bras == "B") then {
                _u = [_gW, "B_Soldier_F", [_x, _y, 0], "pilote"] call HMT_POSER_HOMME;
            } else {
                _u = _gW createUnit ["B_Soldier_F", [_x, _y, 0], [], 0, "NONE"];
                [_u] call HMT_ARMER; [_u, "pilote"] call HMT_PILOTER;
            };
            _u allowDamage false;
            sleep 1.5;
            _u reveal [_m, 4];
            private _vue = round (100 * ([objNull,"VIEW"] checkVisibility [eyePos _u, eyePos _m])) / 100;
            private _c = [_u, _m, 4] call HMT_TIRER_C9;
            (format ["HMT|S1|bras|%1|k|%2|coups|%3|vue|%4|path_mann|%5|posmann|%6",
                     _bras, _k, _c, _vue, _m checkAIFeature "PATH",
                     [round (getPosATL _m select 0), round (getPosATL _m select 1)]]) call HMT_LOG;
            deleteVehicle _m; deleteVehicle _u; deleteGroup _gE; deleteGroup _gW;
            sleep 0.3;
        };
    } forEach ["A", "B", "C"];
    "HMT|S1|FINI" call HMT_LOG; true
};

// SONDE 2 · L HOMME NE COINCE. Le T5 fautif du lot 2 : `nt|40 fps|49 m|0 connu|0 path|true
// degats|0` — quarante impulsions a pleine cadence, inconnu des ennemis, indemne, ZERO metre.
// Ni la charge, ni le combat, ni la mort : la naissance. On rejoue `HMT_POSER_HOMME` + marche
// au meme endroit, et on releve la position AVANT et APRES la pose : un homme deplace par le
// moteur a la naissance est un homme incruste.
HMT_SONDE2 = {
    params ["_px", "_py", ["_n", 10]];
    for "_k" from 1 to _n do {
        private _g = createGroup west;
        private _u = [_g, "B_Soldier_F", [_px, _py, 0], "pilote"] call HMT_POSER_HOMME;
        _u allowDamage false;
        private _p1 = getPosATL _u;
        sleep 2;
        private _p2 = getPosATL _u;
        private _mnt = [_u, 4] call HMT_MARCHER;
        (format ["HMT|S2|k|%1|m|%2|nt|%3|derive_pose|%4|z|%5|anim|%6",
                 _k, round ((_mnt select 0) * 10) / 10, _mnt select 1,
                 round (10 * (_p1 distance _p2)) / 10, round (10 * (_p2 select 2)) / 10,
                 animationState _u]) call HMT_LOG;
        deleteVehicle _u; deleteGroup _g; sleep 0.3;
    };
    "HMT|S2|FINI" call HMT_LOG; true
};
