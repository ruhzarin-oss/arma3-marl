// banc_arma.sqf — LE CERTIFICATEUR.
//
// Tout ce qu'on a mesuré depuis hier vient d'un corpus et d'un simulateur qui sont les nôtres.
// ⟨juillet : 96 % de réussite en sandbox, 0/38 dans Arma. Un paramètre sur trois refuse de
//  transférer.⟩ Arma tranche. Ce banc pose DEUX questions dans le même dispositif.
//
// QUESTION 1 — CERTIFICATION. Approcher par l'angle mort retarde-t-il vraiment le repérage
// dans le vrai moteur ? Mesuré sur notre corpus : être dans le champ ennemi multiplie la
// mortalité par 1,75, et l'effet grandit avec la distance. Si Arma ne le confirme pas, tout
// ce qu'on a bâti au-dessus tombe.
//
// QUESTION 2 — LA MESURE QUI MANQUE. Se coucher retarde-t-il le repérage ?
// ⟨Fable : « Arma détient la mesure qui te manque. Si se coucher y retarde réellement le
//  repérage, le répertoire cessera d'être décoratif — et ce sera une mesure, pas une
//  invention. »⟩ Dans notre simulateur, se coucher ne fait que diviser le risque par 1,4
// (courbe n°1) sans rien retarder — d'où un répertoire décoratif. Arma sait, lui.
//
// LE DISPOSITIF. Une ligne défensive de six hommes, tous orientés au NORD, immobiles, sans
// arme (on mesure la PERCEPTION, pas le combat). Un approchant part à 300 m et avance de 4 m
// toutes les secondes vers eux, selon un azimut et une posture imposés. On relève à chaque
// pas ce que le camp défenseur sait de lui.
//
// LES CONDITIONS CROISÉES : azimut d'approche (0° = plein devant eux, 90° = par le flanc,
// 180° = par l'arrière) x posture (debout, accroupi, couché). Chacune rejouée plusieurs fois.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · si l'approche frontale et l'approche par l'arrière donnent la même distance de
//     détection, l'orientation ne compte pas dans Arma et notre +75 % ne transfère pas.
//   · CONTRÔLE NUL : la même condition rejouée doit donner des résultats voisins. Si la
//     variance entre répétitions dépasse l'écart entre conditions, on ne conclut rien.
//   · CONTRÔLE DE PRÉSENCE : un approchant à 30 m plein devant, debout, DOIT être repéré.
//     S'il ne l'est pas, l'instrument ne mesure rien et tout le reste est du vide.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|BANC|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;
    // ---------- CHERCHER un cercle de 300 m plat et sec, au lieu d'en imposer un ----------
    // Le premier jet imposait un point : le garde-fou l'a refusé, à raison. Sur une île, un
    // cercle de 300 m de rayon plat et sec ne se trouve pas au hasard — on le cherche, et on
    // desserre le critère par paliers plutôt que de forcer un terrain qui fausserait la vue.
    // ⟨des soldats se sont noyés le 31/07 faute d'avoir vérifié plus d'un point⟩
    private _base = [];
    private _tolerance = 0;
    {
        private _tol = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 2500 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        {
                            private _q = _c vectorAdd _x;
                            if (surfaceIsWater _q) then { _ok = false };
                            if (abs ((getTerrainHeightASL _q) - _h) > _tol) then { _ok = false };
                        } forEach [[300,0,0],[-300,0,0],[0,300,0],[0,-300,0],
                                   [212,212,0],[-212,-212,0],[212,-212,0],[-212,212,0],
                                   [150,0,0],[0,150,0],[-150,0,0],[0,-150,0]];
                        if (_ok) then { _base = _c; _tolerance = _tol };
                    };
                };
            };
        };
    } forEach [12, 18, 25, 35];
    if (count _base == 0) exitWith { "HMT|BANC|ECHEC|aucun_terrain_plat_sur_la_carte" call HMT_LOG };
    (format ["HMT|BANC|terrain|%1|%2|denivele_max|%3|altitude|%4",
             round (_base select 0), round (_base select 1), _tolerance,
             round (getTerrainHeightASL _base)]) call HMT_LOG;

    private _gD = createGroup east;      // les défenseurs
    private _gA = createGroup west;      // l'approchant

    // ---------- LA LIGNE DÉFENSIVE : six hommes, tous face au NORD ----------
    private _def = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p;
        removeAllWeapons _u;             // on mesure la PERCEPTION, pas le combat
        _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u disableAI "ANIM";             // sinon l'IA fait tourner la tête et balaie
        _u setBehaviour "SAFE";          // COMBAT déclenche le balayage : on veut un regard FIXE
        _u setUnitPos "UP";
        _u setDir 0;                     // plein nord, tous
        _def pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    sleep 3;
    HMT_DEF = _def;
    // LE CAP EST TENU DE FORCE, ET MESURÉ. Premier jet : je posais setDir 0 puis je passais
    // les défenseurs en COMBAT — mode dans lequel l'IA fait tourner la tête et balaie. Je
    // mesurais donc une orientation SUPPOSÉE, pas celle qui existait. Les premiers résultats
    // étaient inversés (approche frontale jamais repérée, approche par le dos repérée à 70 m).
    [] spawn {
        while { true } do {
            { _x setDir 0; _x setFormDir 0 } forEach HMT_DEF;
            sleep 0.5;
        };
    };
    sleep 2;
    private _caps = HMT_DEF apply { round (getDir _x) };
    (format ["HMT|BANC|ligne|%1|caps_reels|%2", count _def, str _caps]) call HMT_LOG;

    // ---------- une approche : azimut imposé, posture imposée ----------
    HMT_APPROCHE = {
        params ["_az", "_posture", "_rep"];
        private _gA = createGroup west;
        private _dep = _base vectorAdd [300 * sin _az, 300 * cos _az, 0];
        if (surfaceIsWater _dep) exitWith { -1 };
        private _a = _gA createUnit ["B_Soldier_F", _dep, [], 0, "NONE"];
        _a setPosATL _dep;
        removeAllWeapons _a; _a allowDamage false;
        _a disableAI "PATH"; _a disableAI "AUTOCOMBAT";
        _a setUnitPos _posture;
        _a setDir (_az + 180);           // il regarde vers l'objectif
        sleep 2;

        private _d = 300;
        private _dDetect = -1;           // distance à laquelle il est repéré
        private _tDetect = -1;
        private _t0 = time;
        while { _d > 25 } do {
            _d = _d - (if (_d > 180) then {8} else {4});
            private _p = _base vectorAdd [_d * sin _az, _d * cos _az, 0];
            _a setPosATL _p;
            sleep 1;                     // une seconde par pas : on laisse le moteur percevoir
            // ce que le CAMP défenseur sait de lui ⟨knowsAbout est de camp, mesuré 02/08⟩
            private _k = 0;
            { private _v = _x knowsAbout _a; if (_v > _k) then { _k = _v } } forEach _def;
            // on journalise le cap RÉELLEMENT tenu, pas celui qu'on croit avoir imposé
            private _capMoy = 0;
            { _capMoy = _capMoy + (getDir _x) } forEach HMT_DEF;
            _capMoy = round (_capMoy / (count HMT_DEF));
            (format ["HMT|BANC|pas|%1|%2|%3|%4|%5|%6|cap|%7", _az, _posture, _rep, _d,
                     (round (_k*100))/100, (round ((time - _t0)*10))/10, _capMoy]) call HMT_LOG;
            if (_k >= 1.5 && _dDetect < 0) then { _dDetect = _d; _tDetect = time - _t0 };
        };
        deleteVehicle _a; deleteGroup _gA;
        (format ["HMT|BANC|fin|%1|%2|%3|dist_detect|%4|temps_detect|%5",
                 _az, _posture, _rep, _dDetect, (round (_tDetect*10))/10]) call HMT_LOG;
        _dDetect
    };

    // ---------- CONTRÔLE DE PRÉSENCE, avant tout le reste ----------
    // un homme debout à 30 m plein devant DOIT être repéré. Sinon l'instrument est mort.
    private _t = _gA createUnit ["B_Soldier_F", (_base vectorAdd [0, 30, 0]), [], 0, "NONE"];
    _t setPosATL (_base vectorAdd [0, 30, 0]);
    removeAllWeapons _t; _t allowDamage false; _t disableAI "PATH"; _t setUnitPos "UP";
    sleep 25;
    private _kt = 0;
    { private _v = _x knowsAbout _t; if (_v > _kt) then { _kt = _v } } forEach _def;
    (format ["HMT|BANC|controle_presence|knowsAbout|%1", (round (_kt*100))/100]) call HMT_LOG;
    deleteVehicle _t;
    if (_kt < 1.0) exitWith { "HMT|BANC|ECHEC|controle_presence_negatif" call HMT_LOG };
    "HMT|OK|banc_presence|1" call HMT_LOG;

    // ---------- LE PLAN D'EXPÉRIENCE ----------
    // 5 azimuts x 3 postures x 3 répétitions. L'ordre est brassé pour qu'une dérive du moteur
    // ne se confonde pas avec un effet de condition.
    private _plan = [];
    {
        private _az = _x;
        { private _po = _x;
          for "_r" from 1 to 3 do { _plan pushBack [_az, _po, _r] };
        } forEach ["UP", "MIDDLE", "DOWN"];
    } forEach [0, 45, 90, 135, 180];
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|BANC|plan|%1|essais", count _plan]) call HMT_LOG;

    {
        _x call HMT_APPROCHE;
        sleep 3;
        // on efface la mémoire des défenseurs entre deux essais : sans ça, le deuxième
        // approchant hérite de ce que le camp savait du premier ⟨knowsAbout est de camp,
        // mesuré le 02/08 : 4,00 avec un camarade qui voit, 0,00 sans⟩
        {
            private _d = _x;
            { _d forgetTarget _x } forEach (allUnits select { side _x != side _d });
        } forEach _def;
        sleep 5;
    } forEach _plan;

    "HMT|BANC|TERMINE|1" call HMT_LOG;
};
