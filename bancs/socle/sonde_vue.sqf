// ─────────────────────────────────────────────────────────────────────────────
// sonde_vue.sqf — LE CONTROLE VISUEL DU GESTE  ⟨demande de Younes, 19/08⟩
//
// TOUT le dossier du vol repose jusqu ici sur une CHAINE DE CARACTERES : l animation
// `afal...` contre `amov...`, lue au DERNIER tick. Une chaine ne dit pas de combien
// l homme est au-dessus du sol, ni sur quoi il marche. Cette sonde remplace la chaine
// par la GRANDEUR PHYSIQUE — hauteur au-dessus du terrain, a chaque tick — et releve
// le relief et les objets autour, pour qu on VOIE le lieu et la trace dessus.
//
// ⚠️ LES TEMOINS SE LISENT EN FIN D INTERVALLE, JAMAIS APRES LE `setVelocity`.
// La ligne GESTE lisait `velocity` immediatement apres l avoir ecrite : elle mesurait
// L ORDRE, pas le monde, et rendait `vmed|6` sur les actes a 14 m comme a 25 m.
//
// ⚠️ CETTE SONDE EST UN INSTRUMENT, DONC ELLE SE JUGE ⟨regle 18⟩ : deux bras de
// controle sont joues avec les lieux — un bras JAMBES COUPEES (`_vy = 0`) qui doit
// rendre part_sol = 100 % et distance ~0, et un bras VOL FORCE (impulsion verticale
// initiale) qui doit rendre part_sol = 0 % et une hauteur qui monte. Une sonde qui ne
// sait pas distinguer ces deux-la ne dira rien des lieux.
// ─────────────────────────────────────────────────────────────────────────────

// ── LE RELIEF ET LES OBJETS AUTOUR D UN POINT ────────────────────────────────
HMT_VUE_LIEU = {
    params ["_px", "_py", "_etq"];
    // relief : 13 x 13 sur +/- 30 m, pas de 5 m, en hauteur ABSOLUE du terrain
    // ⚠️ UNE LIGNE PAR RANGEE : le journal coupe a 1031 caracteres, et 169 nombres
    // d un coup depassaient. Mesure du 19/08 : RELIEF et TICKS tronques a 1031 pile.
    for "_i" from -6 to 6 do {
        private _r = [];
        for "_j" from -6 to 6 do {
            _r pushBack (round (10 * (getTerrainHeightASL [_px + 5*_i, _py + 5*_j])) / 10);
        };
        (format ["HMT|VUE|RELIEF|etq|%1|x|%2|y|%3|pas|5|n|13|i|%4|r|%5",
                 _etq, round _px, round _py, _i + 6, _r]) call HMT_LOG;
    };
    // objets : ce sur quoi et entre quoi l homme marche
    private _os = nearestObjects [[_px, _py, 0], [], 30];
    private _l = [];
    {
        if (count _l < 40) then {
            private _p = getPosATL _x;
            _l pushBack [typeOf _x, round ((_p select 0) - _px), round ((_p select 1) - _py),
                         round (10 * (_p select 2)) / 10];
        };
    } forEach _os;
    (format ["HMT|VUE|OBJETS|etq|%1|n|%2|o|%3", _etq, count _os, _l]) call HMT_LOG;
};

// ── LA TRACE DU GESTE, TICK PAR TICK ─────────────────────────────────────────
// _mode : "normal" | "jambes" (vy=0) | "volforce" (impulsion verticale au depart)
HMT_VUE_TRACE = {
    params ["_px", "_py", "_etq", ["_mode", "normal"], ["_duree", 4], ["_vy", 6]];
    private _grp = createGroup west;
    private _u = [_grp, "B_Soldier_F", [_px, _py, 0], "pilote"] call HMT_POSER_HOMME;
    if (isNull _u) exitWith {
        deleteGroup _grp;
        (format ["HMT|VUE|TRACE|etq|%1|mode|%2|ECHEC|naissance refusee", _etq, _mode]) call HMT_LOG;
    };
    _u allowDamage false; _u setDir 0;
    sleep 1.5;
    if (_mode == "jambes") then { _vy = 0 };
    // ⚠️ LE BRAS SUD : la marche du socle est CABLEE vers le nord (`[0,_vy,0]`).
    // Si le regime tient a la pente DANS LA DIRECTION DE MARCHE, inverser la
    // direction doit inverser le regime. C est le controle de la THESE.
    if (_mode == "sud" || _mode == "gravite_sud") then { _vy = -6 };
    private _p0 = getPosATL _u;
    // hauteur de POSE, avant toute impulsion : dit si `setPosATL` surleve deja l homme
    (format ["HMT|VUE|POSE|etq|%1|mode|%2|z|%3|sol|%4|anim|%5", _etq, _mode,
             round (100 * (_p0 select 2)) / 100, isTouchingGround _u,
             (animationState _u) select [0, 4]]) call HMT_LOG;
    if (_mode == "volforce") then { _u setVelocity [0, _vy, 5] };   // controle positif du VOL
    private _t0 = time; private _tr = []; private _nsol = 0; private _n = 0;
    private _serie = 0; private _seriemax = 0; private _zmax = 0;
    while { alive _u && time - _t0 < _duree } do {
        // ⚠️ DEUX CANAUX, UN SEUL CODE. `gravite` PRESERVE la composante verticale —
        // la forme qu emploient squad_deploy*.py et les theatres LEVIATHAN. Les deux
        // bras se jouent sur les MEMES lieux dans le MEME passage : apparie, sinon la
        // variance du monde se melange a l effet du canal.
        if (_mode != "volforce" || _n > 0) then {
            if (_mode == "gravite" || _mode == "gravite_sud") then {
                _u setVelocity [0, _vy, (velocity _u) select 2];
            } else {
                _u setVelocity [0, _vy, 0];
            };
        };
        sleep 0.1;                                   // ⚠️ ON DORT AVANT DE LIRE
        private _p = getPosATL _u; private _v = velocity _u;
        private _z = round (100 * (_p select 2)) / 100;
        private _sol = isTouchingGround _u;
        _n = _n + 1;
        if (_sol) then { _nsol = _nsol + 1; _serie = _serie + 1;
                         if (_serie > _seriemax) then { _seriemax = _serie }; }
                 else { _serie = 0 };
        if (_z > _zmax) then { _zmax = _z };
        _tr pushBack [round (10 * ((_p select 0) - _px)) / 10,
                      round (10 * ((_p select 1) - _py)) / 10,
                      _z, (if (_sol) then {1} else {0}),
                      round (10 * (_v select 1)) / 10,
                      round (10 * (_v select 2)) / 10,
                      (animationState _u) select [0, 4]];
    };
    private _fin = getPosATL _u;
    // vraie MEDIANE, sur tableau TRIE, de la vitesse relue en FIN d intervalle
    private _vs = []; { _vs pushBack (_x select 4) } forEach _tr;
    _vs sort true;
    private _vmed = if (count _vs > 0) then { _vs select (floor ((count _vs) / 2)) } else { -1 };
    (format ["HMT|VUE|GESTE|etq|%1|mode|%2|m|%3|n|%4|part_sol|%5|serie_sol_max|%6|z_max|%7|v_med_fin|%8|fps|%9",
             _etq, _mode,
             round (10 * (_p0 distance2D _fin)) / 10, _n,
             round (100 * _nsol / (_n max 1)), _seriemax, _zmax, _vmed,
             round diag_fps]) call HMT_LOG;
    // ⚠️ PAR TRANCHES DE 8 TICKS, meme raison : 40 x 7 champs depassaient 1031.
    private _k = 0;
    while { _k < count _tr } do {
        private _tranche = _tr select [_k, 8];
        (format ["HMT|VUE|TICKS|etq|%1|mode|%2|k|%3|tr|%4", _etq, _mode, _k, _tranche]) call HMT_LOG;
        _k = _k + 8;
    };
    deleteVehicle _u; deleteGroup _grp;
};

HMT_VUE_PRETE = true;
diag_log "HMT|VUE|CHARGEE|sonde_vue 1.3.0";
