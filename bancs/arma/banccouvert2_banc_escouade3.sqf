// banc_escouade3.sqf — COMBIEN D'HOMMES SONT VUS, ET NON SI LE GROUPE L'EST.
//
// CE QUE LE SMOKE TEST A TRANCHE (04/08, trois phases, controle nul a 0°) :
//   phase C, apres liberation au premier tir :
//     erreur du REGARD vers la base de feu : 30° -> 20°   (il ne bouge presque pas)
//     erreur de l ARME  vers la base de feu : 56° ->  3°   (elle vise)
//   -> LA FIXATION EXISTE, ET ELLE PASSE PAR L ARME, PAS PAR LE REGARD.
//   Coherent avec le fait certifie : le cone ne pivote pas, il S OUVRE.
//
// QUATRE CORRECTIONS PAR RAPPORT AU PILOTE
//
//  1. ON MESURE weaponDirection. Le pilote instrumentait eyeDirection : la mauvaise
//     variable. Pire — ses defenseurs etaient DESARMES, donc weaponDirection n aurait
//     rien voulu dire. Les defenseurs sont donc ARMES ici.
//     ⟨consequence assumee : on quitte le regime « perception pure » cote defenseurs. Le
//      groupe MESURE, lui, reste desarme et invulnerable : la variable mesuree — ce que le
//      camp sait du groupe manoeuvrant — garde son sens.⟩
//
//  2. LES DEFENSEURS SONT RECREES ENTRE CHAQUE BRAS. Defaut mesure sur le pilote : le MEME
//     bras rejoue en position 3 puis 5 marque 42 puis 30. Douze points d ecart pour un
//     contenu identique. La memoire du camp NE DECROIT JAMAIS (certifie, 5 min) et
//     forgetTarget ne suffit pas. On ne nettoie plus : on remplace.
//
//  3. L ORDRE DES BRAS EST BRASSE a chaque configuration. Ceinture et bretelles : si un
//     residu d alerte survit au respawn, il ne s alignera plus sur un bras precis.
//
//  4. LIBERATION CONDITIONNELLE au lieu de caps libres. Caps FORCES — le regime dans lequel
//     TOUS nos faits ont ete certifies — jusqu au premier tir d un fixateur. On ne code pas
//     le phenomene : on choisit QUAND le mecanisme natif a le droit d agir.
//     Les bras sans fixateur ne sont donc JAMAIS liberes : ils restent dans le regime certifie.
//
// CINQ BRAS, memes 20 configurations, 150 m -> 40 m :
//   solo · bloc_1axe · deux_axes · flanc_seul · deux_axes_bis
//   ⟨flanc_seul = le meme flanc que deux_axes, SANS base de feu. C est LE controle : s il
//    reussit aussi bien, la fixation n explique rien.⟩
//
// LA MESURE DE MECANISME, exigee par Fable : pendant deux_axes, les armes defensives
// doivent pointer PLUS LOIN de l axe du groupe manoeuvrant que pendant flanc_seul.
// Un effet sans mecanisme n est pas certifiable.
//
// CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
//   P0 VALIDITE  |deux_axes - bis| donne le bruit. Si les ecarts entre bras ne le depassent
//                pas NETTEMENT, banc nul — verdict sur le dispositif, rien de tactique.
//   P1 PRESENCE  bloc_1axe doit etre repere.
//   P2 FIXATION  deux_axes > flanc_seul, test des signes p < 0,05, gain median > bruit.
//   P3 MECANISME arme_vers_manoeuvrant plus GRAND pendant deux_axes que pendant flanc_seul.
//   P4 TIR       si les fixateurs ne tirent pas, il n y a pas de stimulus : les coups sont
//                COMPTES ⟨le 03/08 un tireur cense ne pas tirer en a lache 21⟩.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
call compile preprocessFileLineNumbers "donnees_escouade3.sqf";
if (isNil "HMT_DATA") exitWith { "HMT|ESC3|ECHEC|donnees_non_chargees" call HMT_LOG };
HMT_JALONS = [120, 90, 60, 40];
(format ["HMT|ESC3|debut|%1|configs", count HMT_DATA]) call HMT_LOG;

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
    if (count _base == 0) exitWith { "HMT|ESC3|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|ESC3|terrain|%1|%2|denivele|%3", round (_base select 0), round (_base select 1), _tol]) call HMT_LOG;

    HMT_SU_GRP = {
        private _k = 0;
        { private _u = _x; { private _v = _x knowsAbout _u; if (_v > _k) then { _k = _v } } forEach HMT_DEF } forEach _this;
        _k
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
                // LE GROUPE MESURE RESTE DESARME : la variable mesuree garde son sens.
                // LES FIXATEURS GARDENT LEUR ARME : sans elle ils ne fixent rien.
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
        // LA MESURE DE CE BANC : COMBIEN d'hommes sont vus a chaque jalon, et non si le
        // groupe l'est. ⟨le score de jalons prend le MAXIMUM sur le groupe : des qu'un homme
        //  est repere, les trois comptent comme reperes. Il ecrase par construction un effet
        //  qui porterait sur le NOMBRE. Hypothese deposee avant ce run, cf CRITERES_HOMMES_VUS.md⟩
        private _vusJal = []; { _vusJal pushBack -1 } forEach HMT_JALONS;
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
                    _jal set [_i, (if (_kMan < 1.5) then {1} else {0})];
                    // et COMBIEN d'hommes sont vus a cet instant precis
                    private _nv = 0;
                    { private _u = _x; private _b = 0;
                      { private _z = _x knowsAbout _u; if (_z > _b) then { _b = _z } } forEach HMT_DEF;
                      if (_b >= 1.5) then { _nv = _nv + 1 } } forEach _man;
                    _vusJal set [_i, _nv];
                };
            } forEach HMT_JALONS;
            _dPrec = _d;
        };

        private _vus = 0;
        { private _u = _x; private _b = 0;
          { private _z = _x knowsAbout _u; if (_z > _b) then { _b = _z } } forEach HMT_DEF;
          if (_b >= 1.5) then { _vus = _vus + 1 } } forEach _man;
        private _moy = { private _s = 0; { _s = _s + _x } forEach _this; if (count _this > 0) then { round (_s / count _this) } else { -1 } };

        (format ["HMT|ESC3|essai|%1|%2|man|%3|fix|%4|jalons|%5|vus|%6|sur|%7|pas|%8|tirs|%9|arme_vers_man|%10|regard_vers_man|%11|vus_jalons|%12",
                 _cfg, _lib, (round (_kMan*100))/100, (round (_kFix*100))/100, str _jal,
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
        // L ORDRE EST BRASSE : un residu d alerte ne peut plus s aligner sur un bras precis
        private _ordre = +_bras;
        _ordre = _ordre call BIS_fnc_arrayShuffle;
        (format ["HMT|ESC3|config|%1|defenseurs|%2|ordre|%3", _n, count _defs,
                 str (_ordre apply { _x select 0 })]) call HMT_LOG;
        { [_x select 0, _x select 1, _n, _defs] call HMT_REJOUE } forEach _ordre;
        sleep 2;
    } forEach HMT_DATA;

    "HMT|ESC3|TERMINE|1" call HMT_LOG;
};
