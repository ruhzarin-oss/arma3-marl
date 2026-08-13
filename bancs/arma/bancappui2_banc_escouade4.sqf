// banc_escouade4.sqf — A QUELLE DISTANCE, ET NON COMBIEN.
//
// POURQUOI CE BANC EXISTE
//   Le banc n°3 est mort de sa MESURE, pas de son hypothese. La part d'hommes du groupe
//   manoeuvrant reperes ne prend presque jamais de valeur intermediaire : 3 essais sur 100
//   sur trois bancs cumules. La detection est en CASCADE — des qu'un homme est repere, ses
//   voisins le sont dans la seconde. Coherent avec le fait deja certifie : knowsAbout est
//   de CAMP, pas de soldat.
//   Consequence mesuree le 04/08 : le fameux « 31/60 contre 51/60 » etait 11 groupes
//   reperes contre 17, multiplie par 3 hommes. La part d'hommes vus ETAIT la metrique de
//   groupe, rescalee. Le banc bati pour lui echapper la mesurait.
//
// CE QUI CHANGE
//
//  1. LA MESURE EST UNE DISTANCE. A quelle distance le camp adverse repere le groupe.
//     Continue : elle ne peut pas produire d'egalites. C'est le seul defaut de
//     l'instrument precedent qu'on est SUR de corriger.
//       d_grp  distance du centre du groupe au premier knowsAbout >= 1.5   (-1 si jamais)
//       d_hom  la meme, PAR HOMME, avec la distance propre de cet homme
//       casc   ecart en metres entre le premier et le dernier homme repere (-1 si < 2)
//       repere 0/1 — la metrique de groupe, enfin nommee pour ce qu'elle est
//
//  2. UN CONTROLE POSITIF POUR LA CASCADE — c'est lui qui compte, pas l'hypothese.
//     Bras `flanc_etale` : meme chemin, meme effectif, ecartement 8 m -> 40 m.
//     Si la detection s'etale quand les hommes s'ecartent, la cascade est geometrique.
//     Si elle ne s'etale pas, la connaissance est de camp et instantanee, et toute mesure
//     « combien d'hommes » est morte DEFINITIVEMENT. Ce banc a le droit de refuter la
//     branche entiere : c'est le but, pas un risque.
//
//  3. DEFENSEURS 5 A 8. Le banc n°3 a mesure du plancher (4 defenseurs, personne n'est
//     jamais repere) et du plafond (12, tout le monde l'est). Ces configs ne departagent
//     rien. On reste dans la bande qui bascule.
//
// CE QUI EST REPRIS TEL QUEL DU BANC n°3 — acquis, on n'y touche pas :
//   defenseurs ARMES et RECREES entre chaque bras ⟨la memoire du camp ne decroit jamais⟩
//   ordre des bras BRASSE a chaque configuration
//   caps FORCES jusqu'au premier tir d'un fixateur, puis liberation
//   groupe mesure DESARME et invulnerable ⟨sinon la variable mesuree perd son sens⟩
//   champs vus / jalons / arme_vers_man conserves, pour que les deux bancs restent comparables
//
// CE QUI FERAIT ECHOUER LA MESURE — cf CRITERES_BANC_ESCOUADE4.md, deposé AVANT ce run :
//   D0 CONTROLE POSITIF  flanc_etale doit donner une cascade mediane >= 15 m.
//                        S'il echoue, la branche « combien d'hommes » est close pour de bon.
//   D2 BRUIT             bruit sur d_grp entre rejeux identiques <= 25 m, sinon D3 non lu.
//   D3 HYPOTHESE         lue SEULEMENT si D0 et D2 passent.
//   D4 CONTROLE NEGATIF  rien ne doit apparaitre entre flanc_seul et flanc_seul_bis.
//   D5 PRESENCE          bloc_1axe repere dans >= 18 configs sur 20.
//   D6 TIR               une config ou deux_axes tire 0 coup est EXCLUE de D3.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_escouade4.sqf";
if (isNil "HMT_DATA") exitWith { "HMT|ESC4|ECHEC|donnees_non_chargees" call HMT_LOG };
HMT_JALONS = [120, 90, 60, 40];
HMT_SEUIL = 1.5;
(format ["HMT|ESC4|debut|%1|configs", count HMT_DATA]) call HMT_LOG;

[] spawn {
    sleep 20;
    private _base = []; private _tol = 0;
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 4000 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        {
                            private _q = _c vectorAdd _x;
                            if (surfaceIsWater _q) then { _ok = false };
                            if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                            if (count (nearestTerrainObjects [_q, ["TREE","HOUSE"], 20]) > 0) then { _ok = false };
                        } forEach [[0,0,0],[160,0,0],[-160,0,0],[0,160,0],[0,-160,0],
                                   [113,113,0],[-113,-113,0],[113,-113,0],[-113,113,0],
                                   [75,0,0],[0,75,0],[-75,0,0],[0,-75,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [12, 20, 30, 45];
    if (count _base == 0) exitWith { "HMT|ESC4|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|ESC4|terrain|%1|%2|denivele|%3", round (_base select 0), round (_base select 1), _tol]) call HMT_LOG;

    HMT_SU_GRP = {
        private _k = 0;
        { private _u = _x; { private _v = _x knowsAbout _u; if (_v > _k) then { _k = _v } } forEach HMT_DEF } forEach _this;
        _k
    };
    // ce que le camp sait d'UN homme
    HMT_SU_UN = {
        private _u = _this; private _b = 0;
        { private _z = _x knowsAbout _u; if (_z > _b) then { _b = _z } } forEach HMT_DEF;
        _b
    };

    // ---------- poser une ligne defensive NEUVE ----------
    HMT_POSER = {
        params ["_defs"];
        HMT_GD = createGroup east;
        HMT_DEF = [];
        {
            private _p = _base vectorAdd [_x select 0, _x select 1, 0];
            private _u = HMT_GD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
            _u setPosATL _p; _u allowDamage false;
            _u disableAI "PATH";                    // immobiles, mais ARMES
            _u setBehaviour "SAFE"; _u setUnitPos "UP";
            _u setDir (_x select 2);
            _u setVariable ["cap", _x select 2];
            HMT_DEF pushBack _u;
        } forEach _defs;
        sleep 3;
    };
    HMT_RETIRER = { { deleteVehicle _x } forEach HMT_DEF; deleteGroup HMT_GD; HMT_DEF = []; sleep 2 };

    // ---------- rejouer un bras ----------
    HMT_REJOUE = {
        params ["_lib", "_groupes", "_cfg", "_defs"];
        [_defs] call HMT_POSER;                     // LIGNE NEUVE : aucun souvenir du bras precedent
        HMT_LIBRE = false;
        private _garde = [] spawn {
            while { true } do {
                if (!HMT_LIBRE) then { { _x setDir (_x getVariable ["cap", 0]) } forEach HMT_DEF };
                sleep 0.5;
            };
        };

        private _gW = createGroup west;
        private _unites = []; private _nmax = 0;
        {
            private _role = _x select 0; private _traj = _x select 1;
            private _us = [];
            {
                private _p0 = _base vectorAdd [(_x select 0) select 0, (_x select 0) select 1, 0];
                private _a = _gW createUnit ["B_Soldier_F", _p0, [], 0, "NONE"];
                _a setPosATL _p0; _a allowDamage false;
                _a disableAI "PATH"; _a disableAI "AUTOCOMBAT"; _a setUnitPos "UP";
                if (_role == "M") then { removeAllWeapons _a };
                _us pushBack _a;
                if (count _x > _nmax) then { _nmax = count _x };
            } forEach _traj;
            _unites pushBack [_role, _us, _traj];
        } forEach _groupes;
        sleep 2;

        private _man = []; private _fix = []; private _trajMan = [];
        { if ((_x select 0) == "M") then { _man = _x select 1; _trajMan = _x select 2 }
          else { _fix append (_x select 1) } } forEach _unites;

        HMT_TIRS = 0;
        { _x addEventHandler ["Fired", { HMT_TIRS = HMT_TIRS + 1 }] } forEach _fix;

        private _jal = []; { _jal pushBack -1 } forEach HMT_JALONS;
        private _vusJal = []; { _vusJal pushBack -1 } forEach HMT_JALONS;

        // LA MESURE DE CE BANC. Des distances, donc pas d'egalites possibles.
        private _dGrp = -1;                                     // distance du groupe au 1er contact
        private _dHom = []; { _dHom pushBack -1 } forEach _man;  // la meme, par homme
        private _tHom = []; { _tHom pushBack -1 } forEach _man;  // le pas, pour la cascade en temps

        private _kMan = 0; private _kFix = 0; private _dPrec = 999;
        private _armeMan = []; private _regMan = [];

        for "_t" from 0 to (_nmax - 1) do {
            {
                private _us = _x select 1; private _tr = _x select 2;
                {
                    private _h = _tr select _forEachIndex;
                    private _q = _h select (_t min ((count _h) - 1));
                    _x setPosATL (_base vectorAdd [_q select 0, _q select 1, 0]);
                } forEach _us;
            } forEach _unites;

            // LE STIMULUS : les fixateurs tirent. Au premier coup parti, on LIBERE.
            {
                private _w = currentWeapon _x;
                if (_w != "") then { _x forceWeaponFire [_w, "Single"] };
            } forEach _fix;
            if (!HMT_LIBRE && HMT_TIRS > 0) then { HMT_LIBRE = true };

            sleep 1.2;

            private _v = _man call HMT_SU_GRP;
            if (_v > _kMan) then { _kMan = _v };
            if (count _fix > 0) then {
                private _w2 = _fix call HMT_SU_GRP;
                if (_w2 > _kFix) then { _kFix = _w2 };
            };

            // centre du groupe manoeuvrant
            private _sx = 0; private _sy = 0;
            {
                private _h = _trajMan select _forEachIndex;
                private _q = _h select (_t min ((count _h) - 1));
                _sx = _sx + (_q select 0); _sy = _sy + (_q select 1);
            } forEach _man;
            _sx = _sx / (count _man); _sy = _sy / (count _man);
            private _d = sqrt ((_sx^2) + (_sy^2));

            // ---- PREMIER CONTACT, PAR HOMME ET POUR LE GROUPE ----
            // Chaque homme est note a SA distance, pas a celle du centre : c'est ce qui
            // permet de mesurer si la detection s'etale ou si elle cascade d'un coup.
            {
                private _i = _forEachIndex;
                if ((_dHom select _i) < 0 && (_x call HMT_SU_UN) >= HMT_SEUIL) then {
                    private _h = _trajMan select _i;
                    private _q = _h select (_t min ((count _h) - 1));
                    _dHom set [_i, round (sqrt (((_q select 0)^2) + ((_q select 1)^2)))];
                    _tHom set [_i, _t];
                };
            } forEach _man;
            if (_dGrp < 0 && _kMan >= HMT_SEUIL) then { _dGrp = round _d };

            // LE MECANISME : les armes defensives pointent-elles LOIN du groupe manoeuvrant ?
            private _sa = 0; private _sr = 0;
            {
                private _c = _base vectorAdd [_sx, _sy, 0];
                private _vv = _c vectorDiff (getPosATL _x);
                private _azc = (((_vv select 0) atan2 (_vv select 1)) + 360) % 360;
                private _w = _x weaponDirection (currentWeapon _x);
                private _azw = (((_w select 0) atan2 (_w select 1)) + 360) % 360;
                private _e = eyeDirection _x;
                private _aze = (((_e select 0) atan2 (_e select 1)) + 360) % 360;
                _sa = _sa + abs ((_azw - _azc + 180) % 360 - 180);
                _sr = _sr + abs ((_aze - _azc + 180) % 360 - 180);
            } forEach HMT_DEF;
            _armeMan pushBack (_sa / (count HMT_DEF));
            _regMan pushBack (_sr / (count HMT_DEF));

            {
                private _i = _forEachIndex;
                if (_d <= _x && _dPrec > _x && (_jal select _i) < 0) then {
                    _jal set [_i, (if (_kMan < HMT_SEUIL) then {1} else {0})];
                    private _nv = 0;
                    { if ((_x call HMT_SU_UN) >= HMT_SEUIL) then { _nv = _nv + 1 } } forEach _man;
                    _vusJal set [_i, _nv];
                };
            } forEach HMT_JALONS;
            _dPrec = _d;
        };

        private _vus = 0;
        { if ((_x call HMT_SU_UN) >= HMT_SEUIL) then { _vus = _vus + 1 } } forEach _man;

        // ---- LA CASCADE : de combien de metres la detection s'etale-t-elle ? ----
        // -1 quand moins de deux hommes ont ete reperes : on ne fabrique pas un zero.
        private _dv = []; private _tv = [];
        { if (_x >= 0) then { _dv pushBack _x } } forEach _dHom;
        { if (_x >= 0) then { _tv pushBack _x } } forEach _tHom;
        private _casc = -1; private _cascPas = -1;
        if (count _dv >= 2) then {
            private _mn = _dv select 0; private _mx = _dv select 0;
            { if (_x < _mn) then { _mn = _x }; if (_x > _mx) then { _mx = _x } } forEach _dv;
            _casc = _mx - _mn;
            private _tn = _tv select 0; private _tx = _tv select 0;
            { if (_x < _tn) then { _tn = _x }; if (_x > _tx) then { _tx = _x } } forEach _tv;
            _cascPas = _tx - _tn;
        };
        private _repere = if (_dGrp >= 0) then { 1 } else { 0 };
        private _moy = { private _s = 0; { _s = _s + _x } forEach _this; if (count _this > 0) then { round (_s / count _this) } else { -1 } };

        (format ["HMT|ESC4|essai|%1|%2|d_grp|%3|d_hom|%4|casc|%5|casc_pas|%6|repere|%7|man|%8|fix|%9|jalons|%10|vus|%11|sur|%12|pas|%13|tirs|%14|arme_vers_man|%15|regard_vers_man|%16|vus_jalons|%17",
                 _cfg, _lib, _dGrp, str _dHom, _casc, _cascPas, _repere,
                 (round (_kMan*100))/100, (round (_kFix*100))/100, str _jal,
                 _vus, count _man, _nmax, HMT_TIRS,
                 _armeMan call _moy, _regMan call _moy, str _vusJal]) call HMT_LOG;

        terminate _garde;
        { { deleteVehicle _x } forEach (_x select 1) } forEach _unites;
        deleteGroup _gW;
        call HMT_RETIRER;                            // LA LIGNE EST DETRUITE, pas nettoyee
        sleep 2;
    };

    private _n = 0;
    {
        _n = _n + 1;
        private _defs = _x select 0;
        private _bras = _x select 1;
        private _ordre = +_bras;
        _ordre = _ordre call BIS_fnc_arrayShuffle;
        (format ["HMT|ESC4|config|%1|defenseurs|%2|ordre|%3", _n, count _defs,
                 str (_ordre apply { _x select 0 })]) call HMT_LOG;
        { [_x select 0, _x select 1, _n, _defs] call HMT_REJOUE } forEach _ordre;
        sleep 2;
    } forEach HMT_DATA;

    "HMT|ESC4|TERMINE|1" call HMT_LOG;
};
