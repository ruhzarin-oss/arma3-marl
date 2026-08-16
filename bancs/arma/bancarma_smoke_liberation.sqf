// smoke_liberation.sqf — LA FIXATION EXISTE-T-ELLE DANS ARMA ?
//
// ⟨Fable, 04/08 : « Smoke test de la liberation conditionnelle, une seule configuration,
//  AVANT tout banc. Il coute dix minutes et tranche entre deux branches entieres. »⟩
//
// LE PROBLEME. Pour qu'une base de feu FIXE, il faut que les defenseurs puissent tourner
// leur secteur. Or tous nos bancs certifies forcent le cap toutes les 0,5 s. Les liberer
// ne marche pas non plus : mesure du 04/08, des qu'on relache, les tetes partent de ~170°
// AVANT meme qu'un approchant soit pose — l'IA reprend l'orientation selon sa logique
// interne, et la configuration defensive n'est plus celle qu'on croit.
//
// LA QUATRIEME VOIE : LIBERATION CONDITIONNELLE. Cap force — le regime certifie — JUSQU'AU
// premier stimulus percu. On ne code pas le phenomene : on choisit QUAND le mecanisme natif
// a le droit d'agir, pas CE qu'il fait.
//
// CE QUE CE TEST TRANCHE. Apres liberation, le regard des defenseurs s'oriente-t-il vers
// les fixateurs ? Et surtout — question de Fable — LES ARCS SUIVENT-ILS ?
// ⟨fait certifie du projet : le cone ne pivote pas, il S'OUVRE. Si les tetes bougent mais
//  que les armes restent dans l'axe, la fixation-par-le-regard n'existe pas, et tout banc
//  d'escouade en perception pure est mort-ne.⟩
//
// TROIS PHASES, dans le meme dispositif, pour que chacune soit le temoin de la suivante :
//   A  caps FORCES, personne en vue        -> CONTROLE NUL : l'ecart doit etre 0°
//   B  caps LIBERES, personne              -> LA REFERENCE : la derive spontanee (~170°)
//   C  caps forces, puis LIBERES au 1er tir de fixateurs ARMES -> LA MESURE
//
// LES FIXATEURS SONT ARMES. Des hommes desarmes ne fixent rien : le stimulus d'Arma est
// FiredNear. Ils sont invulnerables et places a 30° de l'axe defensif — donc DANS le cone
// (demi-cone mesure a 35°) mais DECALES, sans quoi un regard qui ne bouge pas et un regard
// qui les vise donneraient la meme mesure.
//
// LES TROIS SIGNATURES ATTENDUES, ecrites avant :
//   regard qui VISE les fixateurs      -> erreur angulaire proche de 0°
//   regard qui NE BOUGE PAS            -> erreur ~30° (l'angle des fixateurs)
//   derive spontanee, sans rapport     -> erreur large et dispersee, ~90° en moyenne
//
// CE QUI FERAIT ECHOUER LA MESURE :
//   · si la phase A ne donne pas 0°, le verrouillage ne verrouille pas et rien ne vaut ;
//   · si aucun coup n'est tire, il n'y a pas de stimulus et la phase C ne teste rien —
//     le nombre de coups est COMPTE ⟨le 03/08, un tireur cense ne pas tirer a lache 21
//     cartouches : disableAI "AUTOCOMBAT" n'empeche pas de faire feu⟩ ;
//   · si les defenseurs ne PERCOIVENT pas les fixateurs (knowsAbout reste a 0), le
//     stimulus n'a pas atteint sa cible et l'absence de rotation ne prouve rien.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|SMOKE|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;

    // ---------- terrain plat cherche, pas suppose ----------
    private _base = []; private _tol = 0;
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 3000 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        {
                            private _q = _c vectorAdd _x;
                            if (surfaceIsWater _q) then { _ok = false };
                            if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                            if (count (nearestTerrainObjects [_q, ["TREE","HOUSE"], 18]) > 0) then { _ok = false };
                        } forEach [[0,0,0],[0,130,0],[65,113,0],[-65,113,0],[0,60,0],[40,40,0],[-40,40,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [10, 18, 28, 40];
    if (count _base == 0) exitWith { "HMT|SMOKE|ECHEC|aucun_terrain" call HMT_LOG };
    (format ["HMT|SMOKE|terrain|%1|%2|denivele|%3", round (_base select 0), round (_base select 1), _tol]) call HMT_LOG;

    // ---------- la ligne defensive : six hommes, cap NORD (regime du banc du cone) ----------
    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH";
        _u setBehaviour "SAFE"; _u setUnitPos "UP"; _u setDir 0;
        _u setVariable ["cap", 0];
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    sleep 3;

    // le verrou : actif tant que HMT_LIBRE est faux
    HMT_LIBRE = false;
    private _garde = [] spawn {
        while { true } do {
            if (!HMT_LIBRE) then { { _x setDir (_x getVariable ["cap", 0]) } forEach HMT_DEF };
            sleep 0.5;
        };
    };

    // ---------- l'instrument : regard ET ARME, releves ensemble ----------
    // On mesure les DEUX. Le cone ne pivote pas, il s'ouvre : des tetes qui bougent sans
    // que les armes suivent ne seraient pas de la fixation.
    HMT_PHASE = "A"; HMT_CIBLE = objNull;
    private _oeil = [] spawn {
        while { true } do {
            private _re = []; private _ra = []; private _ce = []; private _ca = [];
            {
                private _e = eyeDirection _x;
                private _aze = (((_e select 0) atan2 (_e select 1)) + 360) % 360;
                private _w = _x weaponDirection (currentWeapon _x);
                private _azw = (((_w select 0) atan2 (_w select 1)) + 360) % 360;
                private _c = _x getVariable ["cap", 0];
                _re pushBack (abs ((_aze - _c + 180) % 360 - 180));      // ecart au cap initial
                _ra pushBack (abs ((_azw - _c + 180) % 360 - 180));
                if (!isNull HMT_CIBLE) then {
                    private _v = (getPosATL HMT_CIBLE) vectorDiff (getPosATL _x);
                    private _azc = (((_v select 0) atan2 (_v select 1)) + 360) % 360;
                    _ce pushBack (abs ((_aze - _azc + 180) % 360 - 180));  // erreur VERS la cible
                    _ca pushBack (abs ((_azw - _azc + 180) % 360 - 180));
                };
            } forEach HMT_DEF;
            private _moy = { private _s = 0; { _s = _s + _x } forEach _this; if (count _this > 0) then { round (_s / count _this) } else { -1 } };
            (format ["HMT|SMOKE|releve|%1|libre|%2|regard_cap|%3|arme_cap|%4|regard_cible|%5|arme_cible|%6",
                     HMT_PHASE, (if (HMT_LIBRE) then {1} else {0}),
                     _re call _moy, _ra call _moy, _ce call _moy, _ca call _moy]) call HMT_LOG;
            sleep 1;
        };
    };

    // ================= PHASE A : caps forces, personne =================
    HMT_PHASE = "A"; HMT_LIBRE = false;
    "HMT|SMOKE|phase|A|caps_forces_personne" call HMT_LOG;
    sleep 30;

    // ================= PHASE B : caps liberes, personne =================
    // LA REFERENCE. Sans elle, une rotation observee en phase C ne prouverait rien.
    HMT_PHASE = "B"; HMT_LIBRE = true;
    "HMT|SMOKE|phase|B|caps_liberes_personne" call HMT_LOG;
    sleep 40;

    // on remet tout en place et on efface la memoire du camp
    HMT_PHASE = "T"; HMT_LIBRE = false;
    { _x setDir (_x getVariable ["cap", 0]) } forEach HMT_DEF;
    { private _d = _x; { _d forgetTarget _x } forEach (allUnits select { side _x != side _d }) } forEach HMT_DEF;
    sleep 20;

    // ================= PHASE C : fixateurs armes, liberation au 1er tir =================
    HMT_PHASE = "C"; HMT_LIBRE = false;
    private _gW = createGroup west;
    private _fix = [];
    // a 30° de l'axe defensif, a 110 m : DANS le cone (demi-cone 35°) mais DECALES
    {
        private _a = 30; private _d = 110;
        private _p = _base vectorAdd [(_d * sin _a) + _x, _d * cos _a, 0];
        private _u = _gW createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u setDir (_a + 180);
        _fix pushBack _u;
    } forEach [-8, 0, 8];
    HMT_CIBLE = _fix select 1;
    sleep 5;

    // les defenseurs PERCOIVENT-ILS les fixateurs ? sans quoi le stimulus n'atteint personne
    private _kav = 0;
    { private _u = _x; { private _v = _x knowsAbout _u; if (_v > _kav) then { _kav = _v } } forEach HMT_DEF } forEach _fix;
    (format ["HMT|SMOKE|phase|C|fixateurs|%1|know_avant_tir|%2", count _fix, (round (_kav*100))/100]) call HMT_LOG;

    // ---------- LE STIMULUS : ils tirent, et on COMPTE ----------
    private _coups = 0;
    { _x addEventHandler ["Fired", { HMT_TIRS = HMT_TIRS + 1 }] } forEach _fix;
    HMT_TIRS = 0;
    for "_i" from 1 to 12 do {
        {
            private _w = currentWeapon _x;
            if (_w != "") then { _x forceWeaponFire [_w, "Single"] };
        } forEach _fix;
        if (!HMT_LIBRE && HMT_TIRS > 0) then {
            HMT_LIBRE = true;                       // LA LIBERATION, au premier coup parti
            (format ["HMT|SMOKE|liberation|au_tir|%1", HMT_TIRS]) call HMT_LOG;
        };
        sleep 1.5;
    };
    (format ["HMT|SMOKE|tirs_comptes|%1", HMT_TIRS]) call HMT_LOG;
    if (HMT_TIRS == 0) then {
        "HMT|SMOKE|ECHEC|aucun_tir_le_stimulus_n_existe_pas" call HMT_LOG;
        HMT_LIBRE = true;                            // on libere quand meme pour voir
    };
    sleep 45;

    private _kap = 0;
    { private _u = _x; { private _v = _x knowsAbout _u; if (_v > _kap) then { _kap = _v } } forEach HMT_DEF } forEach _fix;
    (format ["HMT|SMOKE|phase|C|know_apres_tir|%1", (round (_kap*100))/100]) call HMT_LOG;

    terminate _oeil; terminate _garde;
    "HMT|SMOKE|TERMINE|1" call HMT_LOG;
};
