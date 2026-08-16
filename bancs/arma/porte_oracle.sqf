// ═══════════════════════════════════════════════════════════════════════════
//  porte_oracle.sqf — LE BANC SAIT-IL PAYER L INFORMATION ?
//  Criteres deposes AVANT lancement : CRITERES_PORTE_ORACLE.md
//
//  Un verdict anterieur dit que « le banc refusait l oracle » : l information
//  parfaite faisait 10/20 la ou un agent ordinaire faisait 15. On le rejoue sur un
//  banc qui contient UNE VRAIE DECISION : par quel axe passer.
//
//  3 bras APPARIES par scene (meme cap, meme cote tenu) :
//    FT      prend toujours l axe TENU   — borne basse
//    AV      tire son axe AU HASARD      — sans information
//    OR      prend toujours l axe LIBRE  — information parfaite
//
//  ⚠️ `reveal` n a RIEN a faire ici. L oracle informe LA DECISION, pas la base de
//  connaissance du moteur. Ce que `reveal` fait est deja certifie ailleurs.
//  ⚠️ On juge la PRISE et l EXPOSITION PAR METRE, jamais les eliminations.
// ═══════════════════════════════════════════════════════════════════════════

call compile preprocessFileLineNumbers "socle.sqf";
HMT_LOG = { diag_log _this };

HMT_PO_O       = [4644, 5652];   // l objectif
HMT_PO_DEPART  = 200;            // m, distance de depart
// 120 m de decalage = 240 m entre les deux axes au milieu. Il FAUT que la planque
// ne couvre qu un seul axe : si elle voit les deux, il n y a pas d axe libre et la
// precondition tombera — c est elle qui le dira.
HMT_PO_ECART   = 120;            // m, decalage lateral des deux axes au milieu
HMT_PO_PLANQUE = 30;             // m, distance de la planque a son axe
HMT_PO_PRISE   = 15;             // m, rayon de prise
HMT_PO_TENUE   = 20;             // s, il faut etre encore vivant apres
// ⚠️ 280 s, ET LA MARCHE EN `AWARE`. Re-dimensionnement du 17/08 : a 150 s en conduite
// COMBAT, PERSONNE n atteignait l objectif — le bras ORACLE traversait pourtant sans
// etre vu (expo 0, 4 survivants) et s arretait a 146 m sur 200. Les hommes rampaient a
// ~1 m/s pour un trajet en deux jambes de ~460 m. On ne lit pas un monde injouable.
HMT_PO_PLAFOND = 280;            // s, plafond de temps
if (isNil "HMT_PO_REPS") then { HMT_PO_REPS = 20 };

// ── geometrie : tout se deduit du cap et du cote ──
HMT_PO_POINTS = {
    params ["_beta", "_cote"];        // _cote : 1 = planque a droite, -1 = a gauche
    private _ox = HMT_PO_O select 0; private _oy = HMT_PO_O select 1;
    // le depart, a 250 m dans la direction _beta
    private _sx = _ox + HMT_PO_DEPART * sin _beta;
    private _sy = _oy + HMT_PO_DEPART * cos _beta;
    // les deux milieux, decales perpendiculairement
    private _mx = (_ox + _sx) / 2; private _my = (_oy + _sy) / 2;
    private _px = sin (_beta + 90); private _py = cos (_beta + 90);
    [[_sx, _sy],                                                   // depart
     [_mx + HMT_PO_ECART * _px, _my + HMT_PO_ECART * _py],         // milieu DROITE (cote +1)
     [_mx - HMT_PO_ECART * _px, _my - HMT_PO_ECART * _py]]         // milieu GAUCHE (cote -1)
};

// ── un bras ──
HMT_PO_JOUER = {
    params ["_rep", "_bras", "_beta", "_cote"];
    private _pts = [_beta, _cote] call HMT_PO_POINTS;
    _pts params ["_s", "_mD", "_mG"];
    private _o = HMT_PO_O;

    // le milieu TENU est du cote _cote ; l autre est libre
    private _mTenu  = if (_cote > 0) then { _mD } else { _mG };
    private _mLibre = if (_cote > 0) then { _mG } else { _mD };

    // ── LE CHOIX : c est ici, et nulle part ailleurs, que l information se depense ──
    private _choisi = switch (_bras) do {
        case "FT": { _mTenu };                                  // toujours le tenu
        case "OR": { _mLibre };                                 // toujours le libre
        default   { if (random 1 < 0.5) then { _mD } else { _mG } };   // AV : au hasard
    };
    private _aPrisLeTenu = if ((_choisi distance2D _mTenu) < 1) then { 1 } else { 0 };

    // ── la planque : 3 hommes, immobiles, couches, face a leur axe ──
    private _gd = createGroup east;
    private _defs = [];
    // ⚠️ CHAQUE `select` PARENTHESE. En SQF, `_m select 0 - _o select 0` se lit
    // `_m select (0 - _o)` : erreur generique et le bras ne se joue jamais (mesure du 16/08).
    private _vers = (((_mTenu select 0) - (_o select 0)) atan2 ((_mTenu select 1) - (_o select 1)));
    for "_i" from 0 to 2 do {
        // poses a 40 m de l axe tenu, du cote oppose a l objectif
        private _dx = (_mTenu select 0) + HMT_PO_PLANQUE * sin (_vers + 90) + (_i - 1) * 6;
        private _dy = (_mTenu select 1) + HMT_PO_PLANQUE * cos (_vers + 90);
        private _d = _gd createUnit ["O_Soldier_F", [_dx, _dy, 0], [], 0, "NONE"];
        _d setPosATL [_dx, _dy, 0]; _d setSkill 0.5;
        _d disableAI "PATH";                        // il TIENT, il ne poursuit pas
        _d setUnitPos "DOWN";                       // planque = couche
        _d setBehaviour "COMBAT"; _d setCombatMode "RED"; _d allowFleeing 0;
        _d setDir (((_mTenu select 0) - _dx) atan2 ((_mTenu select 1) - _dy));
        _defs pushBack _d;
    };

    // ── les attaquants : 4 hommes, IA entiere, DESTRUCTIBLES ──
    private _ga = createGroup west;
    private _att = [];
    for "_i" from 0 to 3 do {
        private _p = [(_s select 0) + (_i - 1.5) * 5, (_s select 1), 0];
        private _u = [_ga, "B_Soldier_F", _p, "natif"] call HMT_POSER_HOMME;
        _att pushBack _u;
    };
    // deux jambes : le milieu choisi, puis l objectif
    private _w1 = _ga addWaypoint [[_choisi select 0, _choisi select 1, 0], 0];
    _w1 setWaypointType "MOVE"; _w1 setWaypointSpeed "FULL"; _w1 setWaypointBehaviour "AWARE";
    private _w2 = _ga addWaypoint [[_o select 0, _o select 1, 0], 0];
    _w2 setWaypointType "MOVE"; _w2 setWaypointSpeed "FULL"; _w2 setWaypointBehaviour "AWARE";
    sleep 2;

    // ── la mesure ──
    private _t0 = time;
    private _dMin = HMT_PO_DEPART;          // le plus pres qu on soit alle
    private _expo = 0;                      // homme-secondes vus
    private _prise = 0; private _tPrise = -1;
    while { time - _t0 < HMT_PO_PLAFOND && _prise == 0 } do {
        private _vivants = _att select { alive _x };
        if (count _vivants == 0) exitWith {};
        {
            // ⚠️ on NOMME l attaquant : le forEach imbrique ci-dessous redefinit `_x`,
            // et sans ca on testerait la visibilite d un defenseur vers lui-meme.
            private _u = _x;
            private _d = _u distance2D [_o select 0, _o select 1, 0];
            if (_d < _dMin) then { _dMin = _d };
            private _vu = false;
            {
                if (!_vu && { alive _x }) then {
                    if (([objNull, "VIEW"] checkVisibility [eyePos _x, eyePos _u]) > 0.3) then { _vu = true };
                };
            } forEach _defs;
            if (_vu) then { _expo = _expo + 1 };
            if (_d < HMT_PO_PRISE) then { _prise = 1; _tPrise = time };
        } forEach _vivants;
        sleep 1;
    };

    // ── la TENUE : encore vivant 20 s apres ? ──
    private _tenue = 0;
    if (_prise == 1) then {
        sleep HMT_PO_TENUE;
        private _proches = _att select {
            alive _x && { (_x distance2D [_o select 0, _o select 1, 0]) < HMT_PO_PRISE * 2 }
        };
        if (count _proches > 0) then { _tenue = 1 };
    };

    private _gagnes = HMT_PO_DEPART - _dMin;
    private _cout = if (_gagnes > 1) then { _expo / _gagnes } else { -1 };
    private _vivants_fin = count (_att select { alive _x });

    (format ["HMT|PO|rep|%1|bras|%2|beta|%3|cote|%4|pristenu|%5|prise|%6|tenue|%7|gagnes|%8|expo|%9|cout|%10|vivants|%11|defmorts|%12",
             _rep, _bras, round _beta, _cote, _aPrisLeTenu, _prise, _tenue,
             round _gagnes, _expo,
             (if (_cout < 0) then { -1 } else { round (100 * _cout) / 100 }),
             _vivants_fin, count (_defs select { !alive _x })]) call HMT_LOG;

    { deleteVehicle _x } forEach _att; { deleteVehicle _x } forEach _defs;
    deleteGroup _ga; deleteGroup _gd;
    sleep 2;
};

[] spawn {
    sleep 20;
    (format ["HMT|PO|debut|reps|%1|depart|%2|ecart|%3|socle|%4",
             HMT_PO_REPS, HMT_PO_DEPART, HMT_PO_ECART, HMT_SOCLE_VERSION]) call HMT_LOG;
    for "_rep" from 1 to HMT_PO_REPS do {
        private _beta = random 360;
        private _cote = if (random 1 < 0.5) then { 1 } else { -1 };
        // les trois bras partagent EXACTEMENT la meme scene
        { [_rep, _x, _beta, _cote] call HMT_PO_JOUER } forEach ["FT", "AV", "OR"];
    };
    "HMT|PO|TERMINE" call HMT_LOG;
};
