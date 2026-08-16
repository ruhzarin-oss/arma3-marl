// banc_agent.sqf — LE CERTIFICATEUR APPLIQUÉ À L'AGENT.
//
// L'agent contourne dans MON simulateur. Rien ne dit qu'il contourne dans Arma.
// ⟨juillet : 96 % de réussite en sandbox, 0 sur 38 dans Arma⟩
//
// LE DISPOSITIF. Pour chaque configuration défensive, on rejoue DEUX trajectoires sur la
// MÊME position : celle que l'agent a choisie, et la ligne droite. Même départ, même
// objectif, même ligne défensive. On relève ce que le camp apprend dans chaque cas.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE DE PRÉSENCE : la LIGNE DROITE doit être détectée. Si même elle passe
//     inaperçue, la position ne voit rien et la comparaison ne vaut rien.
//   · L'agent doit ARRIVER : sa trajectoire doit finir à moins de 45 m de l'objectif.
//     Un agent qui « réussit » en n'arrivant pas ne prouve rien.
//   · SEUIL : l'agent doit être repéré PLUS LOIN de l'objectif que la ligne droite, d'au
//     moins 25 %. En dessous, le transfert est déclaré non concluant.
//
// CE QU'ON MESURE, ET POURQUOI ÇA A CHANGÉ.
// Premier jet : on notait SI l'approchant était détecté. Le contrôle positif l'a invalidé —
// le chemin OPTIMAL, calculé exhaustivement, était détecté 7 fois sur 7 à 4,00, exactement
// comme la ligne droite. Écart de 0 %. Le banc n'avait aucune région de réussite.
// La raison est géométrique : la trajectoire finit AU CENTRE de la position. À dix mètres du
// milieu d'un groupe, on est dans le cône de tout le monde, quel que soit le chemin.
// ON NE PEUT PAS ATTEINDRE LE CENTRE SANS ÊTRE VU. Le banc demandait l'impossible.
// Ce que le contournement achète n'est pas d'arriver invisible, c'est d'arriver PLUS LOIN
// avant d'être vu. On mesure donc la DISTANCE DE DÉTECTION — comme le banc du cône, qui
// avait donné 18/18 dans le cône contre 0/26 hors.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_agent.sqf";
// LE FICHIER DE DONNÉES EST VÉRIFIÉ AVANT TOUT. Premier jet : une virgule finale le rendait
// invalide, HMT_DATA restait indéfini, et le banc partait quand même.
if (isNil "HMT_DATA") exitWith { "HMT|AG|ECHEC|donnees_non_chargees" call HMT_LOG };
if (!(HMT_DATA isEqualType [])) exitWith { "HMT|AG|ECHEC|donnees_mal_formees" call HMT_LOG };
(format ["HMT|AG|debut|%1|configs|points|%2", count HMT_DATA,
         count ((HMT_DATA select 0) select 1)]) call HMT_LOG;

[] spawn {
    sleep 20;
    private _base = [];
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 3000 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        { private _q = _c vectorAdd _x;
                          if (surfaceIsWater _q) then { _ok = false };
                          if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                          // exigence assouplie : aucun endroit de Stratis n'était sans arbre
                          // dans 30 m sur sept points. On teste moins de points, moins loin.
                          if (count (nearestTerrainObjects [_q, ["TREE","HOUSE"], 18]) > 0) then { _ok = false };
                        } forEach [[0,0,0],[140,0,0],[-140,0,0],[0,140,0],[0,-140,0]];
                        if (_ok) then { _base = _c };
                    };
                };
            };
        };
    } forEach [10, 18, 28, 40];
    if (count _base == 0) exitWith { "HMT|AG|ECHEC|terrain" call HMT_LOG };
    (format ["HMT|AG|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    HMT_SU = { private _k = 0; { private _v = _x knowsAbout _this; if (_v > _k) then { _k = _v } } forEach HMT_DEF; _k };

    // rejoue une trajectoire et rend ce que le camp a appris
    HMT_REJOUE = {
        params ["_pts", "_lib", "_cfg"];
        private _g = createGroup west;
        private _p0 = _base vectorAdd [(_pts select 0) select 0, (_pts select 0) select 1, 0];
        private _a = _g createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
        _a setPosATL _p0; _a allowDamage false; removeAllWeapons _a;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP";
        sleep 2;
        private _k = 0;
        private _dDetect = -1;              // distance à l'objectif au moment du repérage
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            _a setPosATL _p;
            sleep 1.2;
            private _v = _a call HMT_SU;
            if (_v > _k) then { _k = _v };
            // LA MESURE QUI COMPTE : à quelle distance de l'objectif est-il repéré ?
            if (_v >= 1.5 && _dDetect < 0) then {
                _dDetect = sqrt (((_x select 0)^2) + ((_x select 1)^2));
            };
        } forEach _pts;
        private _fin = (_pts select ((count _pts) - 1));
        private _reste = sqrt (((_fin select 0)^2) + ((_fin select 1)^2));
        (format ["HMT|AG|essai|%1|%2|know|%3|reste|%4|dist_detect|%5", _cfg, _lib,
                 (round (_k*100))/100, round _reste, round _dDetect]) call HMT_LOG;
        deleteVehicle _a; deleteGroup _g;
        { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
        sleep 4;
        _k
    };

    private _n = 0;
    {
        _n = _n + 1;
        private _defs = _x select 0;
        private _traj = _x select 1;

        // la ligne défensive de CETTE configuration, cap verrouillé sur son azimut propre
        private _gD = createGroup east;
        HMT_DEF = [];
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u allowDamage false; removeAllWeapons _u;
            _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "ANIM";
            _u setBehaviour "SAFE"; _u setUnitPos "UP";
            _u setDir (_x select 2);
            _u setVariable ["cap", _x select 2];
            HMT_DEF pushBack _u;
        } forEach _defs;
        private _garde = [] spawn { while { true } do {
            { _x setDir (_x getVariable ["cap", 0]) } forEach HMT_DEF; sleep 0.5 } };
        sleep 3;

        // la ligne droite : même départ, droit sur l'objectif, même nombre de points
        private _dep = _traj select 0;
        private _np = count _traj;
        private _droite = [];
        for "_i" from 0 to (_np - 1) do {
            private _f = 1 - (_i / (_np - 1));
            _droite pushBack [(_dep select 0) * _f, (_dep select 1) * _f];
        };

        [_traj,   "agent",   _n] call HMT_REJOUE;
        [_droite, "droite",  _n] call HMT_REJOUE;

        terminate _garde;
        { deleteVehicle _x } forEach HMT_DEF;
        deleteGroup _gD;
        sleep 3;
    } forEach HMT_DATA;

    "HMT|AG|TERMINE|1" call HMT_LOG;
};
