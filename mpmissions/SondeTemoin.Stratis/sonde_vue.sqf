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
diag_log "HMT|VUE|CHARGEE|sonde_vue 1.9.0";

// ─────────────────────────────────────────────────────────────────────────────
// LA SONDE DES HUIT AZIMUTS — dérivation du critère neuf du placeur ⟨19/08⟩
//
// L ancien critere marchait TOUJOURS VERS LE NORD : il mesurait donc la pente dans un
// azimut cable, et non la praticabilite. Le critere neuf echantillonne LES HUIT AZIMUTS
// DE LA COUTURE (`_a*45` dans ACT_TPL) — l espace d action exact de la politique — et
// retient le MINIMUM, qui est la statistique du mode d echec : l homme coince.
//
// ⚠️ TOUS LES LIEUX EN PARALLELE, UN AZIMUT A LA FOIS. Huit fenetres de 4 s au lieu de
// huit fois N gestes : le cout ne depend pas du nombre de lieux. C est la lecon du bloc C.
// ⚠️ Chaque homme est REMIS a sa position d origine entre deux azimuts, sinon le second
// azimut mesurerait depuis la ou le premier l a laisse.
HMT_SONDER_AZIMUTS = {
    params ["_positions", ["_duree", 4], ["_spd", 6], ["_sab", ""]];
    private _g = createGroup west;
    private _hs = [];
    {
        private _u = _g createUnit ["B_Soldier_F", [_x select 0, _x select 1, 0], [], 0, "NONE"];
        _u allowDamage false; _u setCaptive true;
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u setBehaviour "CARELESS";
        [_u] call HMT_ARMER;
        _hs pushBack _u;
    } forEach _positions;
    sleep 2;
    private _res = []; { _res pushBack [] } forEach _positions;
    for "_a" from 0 to 7 do {
        private _h = _a * 45;
        private _vx = _spd * sin _h; private _vy = _spd * cos _h;
        if (_sab == "jambes") then { _vx = 0; _vy = 0 };   // ⚠️ CONTROLE : doit tout refuser
        {
            private _p = _positions select _forEachIndex;
            _x setPosATL [_p select 0, _p select 1, 0];
        } forEach _hs;
        sleep 1.5;
        private _p0 = _hs apply { getPosATL _x };
        private _t0 = time;
        while { time - _t0 < _duree } do {
            // ⚠️ LE CANAL ADOPTE : la verticale est PRESERVEE (socle 4.0.0)
            { _x setVelocity [_vx, _vy, (velocity _x) select 2] } forEach _hs;
            sleep 0.1;
        };
        {
            (_res select _forEachIndex) pushBack
                (round (10 * ((_p0 select _forEachIndex) distance2D (getPosATL _x))) / 10);
        } forEach _hs;
        (format ["HMT|AZ|FENETRE|az|%1|fps|%2", _h, round diag_fps]) call HMT_LOG;
    };
    {
        private _r = _res select _forEachIndex;
        private _t = +_r; _t sort true;
        (format ["HMT|AZ|LIEU|i|%1|x|%2|y|%3|min|%4|med|%5|max|%6|eau|%7|d|%8",
                 _forEachIndex, round (_x select 0), round (_x select 1),
                 _t select 0, _t select 4, _t select 7,
                 surfaceIsWater [_x select 0, _x select 1], _r]) call HMT_LOG;
    } forEach _positions;
    { deleteVehicle _x } forEach _hs;
    deleteGroup _g;
    ("HMT|AZ|FINI|sab|" + _sab + "|n|" + str (count _positions)) call HMT_LOG;
};

// ─────────────────────────────────────────────────────────────────────────────
// LE CORPUS PLAT ET DÉGAGÉ — un contrôle positif CONSTRUIT ⟨19/08, 21 h⟩
//
// Le contrôle positif du premier essai etait HERITE : les 12 lieux « connus » l etaient
// au titre d une marche vers le NORD seulement. Un controle herite d un critere retire
// n est pas un controle — c est la premisse fausse qui revient par la porte de service.
// Celui-ci se selectionne sur le TERRAIN SEUL : eau, platitude, degagement. Aucune de
// ces trois conditions ne regarde une distance parcourue.
HMT_LIEUX_PLATS = {
    params ["_cx", "_cy", "_rayon", "_combien"];
    private _out = []; private _essais = 0;
    while { count _out < _combien && _essais < 6000 } do {
        _essais = _essais + 1;
        private _x = _cx - _rayon + random (2 * _rayon);
        private _y = _cy - _rayon + random (2 * _rayon);
        if (!surfaceIsWater [_x, _y]) then {
            private _hs = [];
            for "_i" from -1 to 1 do {
                for "_j" from -1 to 1 do {
                    _hs pushBack (getTerrainHeightASL [_x + 15 * _i, _y + 15 * _j]);
                };
            };
            private _t = +_hs; _t sort true;
            // ⚠️ 8.1 m = 10e centile du denivele de Stratis, MESURE sur 3000 points
            // le 19/08 (HMT|TERRAIN). Le seuil de 3 m de la premiere spec rendait
            // 1 lieu sur 6000 : il etait sous le 5e centile. Un rang, pas un nombre.
            if (((_t select 8) - (_t select 0)) <= 8.1) then {
                if ((count (nearestObjects [[_x, _y, 0], [], 10])) == 0) then {
                    _out pushBack [round _x, round _y];
                };
            };
        };
    };
    (format ["HMT|PLAT|trouves|%1|essais|%2|cible|%3", count _out, _essais, _combien]) call HMT_LOG;
    _out
};

// ─────────────────────────────────────────────────────────────────────────────
// LA DISTRIBUTION DU TERRAIN — avant de dire « plat et dégagé » ⟨19/08, 21 h 30⟩
//
// ⚠️ PREMIERE TENTATIVE : « denivele <= 3 m sur +/- 15 m ET aucun objet a 10 m » a rendu
// UN lieu sur SIX MILLE tirages. Deux chiffres absolus poses sans connaitre le terrain.
// On mesure donc d abord CE QUE STRATIS CONTIENT, puis on definit « plat et degage »
// comme un RANG dans cette distribution — pas contre un nombre invente.
// Aucune unite n est creee : c est de la lecture de terrain, ça coute des secondes.
HMT_PROFIL_TERRAIN = {
    params ["_cx", "_cy", "_rayon", "_n"];
    private _d = []; private _o = [];
    for "_k" from 1 to _n do {
        private _x = _cx - _rayon + random (2 * _rayon);
        private _y = _cy - _rayon + random (2 * _rayon);
        if (!surfaceIsWater [_x, _y]) then {
            private _hs = [];
            for "_i" from -1 to 1 do {
                for "_j" from -1 to 1 do {
                    _hs pushBack (getTerrainHeightASL [_x + 15 * _i, _y + 15 * _j]);
                };
            };
            private _t = +_hs; _t sort true;
            _d pushBack (round (10 * ((_t select 8) - (_t select 0))) / 10);
            _o pushBack (count (nearestObjects [[_x, _y, 0], [], 10]));
        };
    };
    _d sort true; _o sort true;
    private _c = count _d;
    // on ne journalise que les CENTILES : la ligne serait coupee a 1031 caracteres
    (format ["HMT|TERRAIN|n|%1|denivele|c5|%2|c10|%3|c25|%4|med|%5|c75|%6|c90|%7",
             _c, _d select (floor (0.05*_c)), _d select (floor (0.10*_c)),
             _d select (floor (0.25*_c)), _d select (floor (0.50*_c)),
             _d select (floor (0.75*_c)), _d select (floor (0.90*_c))]) call HMT_LOG;
    (format ["HMT|TERRAIN|n|%1|objets|c5|%2|c10|%3|c25|%4|med|%5|c75|%6|c90|%7",
             _c, _o select (floor (0.05*_c)), _o select (floor (0.10*_c)),
             _o select (floor (0.25*_c)), _o select (floor (0.50*_c)),
             _o select (floor (0.75*_c)), _o select (floor (0.90*_c))]) call HMT_LOG;
    [_d, _o]
};

// ─────────────────────────────────────────────────────────────────────────────
// LA PENTE LE LONG DE CHAQUE AZIMUT — lecture de terrain, aucune unité ⟨19/08, 22 h⟩
// Pour chaque lieu et chacun des 8 azimuts de la couture, on releve le denivele sur les
// 25 m que l homme parcourrait — la course REELLE, et non un disque de 10 m autour du
// depart. C est la fenetre que ma spec du soir n avait pas dimensionnee.
HMT_PENTE_AZIMUTS = {
    params ["_positions"];
    {
        // ⚠️ `_x` EST LA VARIABLE MAGIQUE DE `forEach` — la reecrire detruit le couple.
        // Ce piege a invalide la sonde n°1 trois fois le 18/08. On prend un autre nom.
        private _pos = _x;
        private _px = _pos select 0; private _py = _pos select 1;
        private _p = []; private _mx = [];
        for "_a" from 0 to 7 do {
            private _h = _a * 45;
            private _dx = sin _h; private _dy = cos _h;
            private _h0 = getTerrainHeightASL [_px, _py];
            private _h25 = getTerrainHeightASL [_px + 25 * _dx, _py + 25 * _dy];
            // la montee la plus RAIDE rencontree sur un pas de 5 m, le long du chemin
            private _pire = 0;
            for "_k" from 1 to 5 do {
                private _a1 = getTerrainHeightASL [_px + 5 * (_k - 1) * _dx, _py + 5 * (_k - 1) * _dy];
                private _a2 = getTerrainHeightASL [_px + 5 * _k * _dx, _py + 5 * _k * _dy];
                if ((_a2 - _a1) > _pire) then { _pire = _a2 - _a1 };
            };
            _p pushBack (round (10 * (_h25 - _h0)) / 10);
            _mx pushBack (round (10 * _pire) / 10);
        };
        (format ["HMT|PENTE|x|%1|y|%2|d25|%3|pire5|%4", _px, _py, _p, _mx]) call HMT_LOG;
    } forEach _positions;
    ("HMT|PENTE|FINI|n|" + str (count _positions)) call HMT_LOG;
};
