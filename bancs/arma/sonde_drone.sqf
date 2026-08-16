// ═══════════════════════════════════════════════════════════════════════════
//  sonde_drone.sqf — CONTROLE POSITIF du lien drone -> soldat.
//  Criteres deposes AVANT lancement : CONTROLE_POSITIF_DRONE.md
//
//  Deux facons pour le tuyau `reveal` de ne pas exister :
//    1. il ne transmet rien           -> bras B ne tire pas -> instrument MORT
//    2. il transmet DEJA sans nous    -> bras A1 tire comme B -> temoin CONTAMINE
//  Trois bras APPARIES par scene : A0 (pas de drone) / A1 (drone qui voit, tuyau
//  coupe) / B (reveal 4 toutes les secondes).
//
//  ⟨regle 16⟩ On juge l ACTE (`Fired`). `knowsAbout` est JOURNALISE, jamais juge.
//  L escouade est en mode `natif` : aucun disableAI, aucun forceWeaponFire.
//  C est l IA entiere qui decide de tirer, sinon on mesurerait notre propre main.
// ═══════════════════════════════════════════════════════════════════════════

call compile preprocessFileLineNumbers "socle.sqf";
HMT_LOG = { diag_log _this };

HMT_DR_ORIGINE = [4644, 5652];
// ⚠️ 300 m, PAS 150. Smoke du 16/08 a 150 m : bras A0 (aucun drone) a tire 79 coups en
// 8,9 s — l escouade repere l ennemi DANS SON DOS. L angle mort certifie ne tient pas a
// cette distance dans ce montage. On s eloigne, on ne bricole pas la vue des hommes.
HMT_DR_DIST    = 300;     // m — ennemi DERRIERE l escouade, hors de son cone
HMT_DR_FEN     = 30;      // s — fenetre d observation par bras
HMT_DR_VUE_MIN = 0.5;     // LOS exigee : revele, l homme doit POUVOIR tirer
HMT_DR_ESSAIS  = 12;      // azimuts essayes avant de declarer la repetition VOID
if (isNil "HMT_DR_REPS") then { HMT_DR_REPS = 20 };

// ── compteurs globaux (les event handlers ne voient pas les variables privees) ──
HMT_DR_T0 = 0;
HMT_DR_N  = 0;    // tirs de l escouade au sol
HMT_DR_T1 = -1;   // temps au premier tir
HMT_DR_NE = 0;    // tirs de l ENNEMI — s il tire, le bruit donne une detection native : VOID

// ───────────────────────────────────────────── OU EST L ENNEMI, ET VOIT-ON JUSQU A LUI
// La position de l ennemi ne depend que de l azimut : on la calcule au lieu de la lire
// sur une unite, pour pouvoir la connaitre AVANT de poser quoi que ce soit.
HMT_DR_POS_ENNEMI = {
    params ["_az"];
    [(HMT_DR_ORIGINE select 0) + HMT_DR_DIST * sin (_az + 180),
     (HMT_DR_ORIGINE select 1) + HMT_DR_DIST * cos (_az + 180)]
};

// ⚠️ LIGNE DE VUE PAR LE CALCUL, PAS PAR DES HOMMES. La version d avant posait puis
// detruisait JUSQU A 12 ESCOUADES COMPLETES par repetition rien que pour tester un
// azimut. Mesure du 16/08 : le serveur mourait AVANT le premier bras, donc avant qu
// aucun aeronef n existe — c etait cette valse d unites. Un test de visibilite ne doit
// rien creer. Hauteur d oeil 1,70 m des deux cotes.
HMT_DR_LOS_GEO = {
    params ["_az"];
    private _pe = [_az] call HMT_DR_POS_ENNEMI;
    private _x1 = HMT_DR_ORIGINE select 0; private _y1 = HMT_DR_ORIGINE select 1;
    private _x2 = _pe select 0;            private _y2 = _pe select 1;
    private _p1 = [_x1, _y1, (getTerrainHeightASL [_x1, _y1]) + 1.7];
    private _p2 = [_x2, _y2, (getTerrainHeightASL [_x2, _y2]) + 1.7];
    (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1, "VIEW", "GEOM"])) == 0
};

// ───────────────────────────────────────────── POSER LA SCENE
// Renvoie [grpSol, unites, ennemi, grpEnn, vue]. L ennemi est a _az + 180 : DERRIERE.
HMT_DR_POSER = {
    params ["_az"];
    private _ox = HMT_DR_ORIGINE select 0;
    private _oy = HMT_DR_ORIGINE select 1;

    private _grpSol = createGroup west;
    private _unites = [];
    for "_i" from 0 to 3 do {
        private _p = [_ox + (_i - 1.5) * 5, _oy, 0];
        private _u = [_grpSol, "B_Soldier_F", _p, "natif"] call HMT_POSER_HOMME;
        _u allowDamage false;
        _u setDir _az;
        _unites pushBack _u;
    };
    _grpSol setFormDir _az;

    // l ennemi : present, visible, et STRICTEMENT inerte
    private _ex = _ox + HMT_DR_DIST * sin (_az + 180);
    private _ey = _oy + HMT_DR_DIST * cos (_az + 180);
    private _grpEnn = createGroup east;
    private _e = _grpEnn createUnit ["O_Soldier_F", [_ex, _ey, 0], [], 0, "NONE"];
    _e setPosATL [_ex, _ey, 0];
    _e setDir _az;                       // il tourne le dos, lui aussi
    _e disableAI "ALL";
    _e setBehaviour "CARELESS";
    _e setUnitPos "UP";                  // debout : il doit etre VISIBLE, pas cache
    _e allowDamage false;
    sleep 1;

    private _vue = [objNull, "VIEW"] checkVisibility [eyePos (_unites select 0), eyePos _e];
    [_grpSol, _unites, _e, _grpEnn, _vue]
};

HMT_DR_DEPOSER = {
    params ["_grpSol", "_unites", "_e", "_grpEnn"];
    { deleteVehicle _x } forEach _unites;
    deleteVehicle _e;
    deleteGroup _grpSol; deleteGroup _grpEnn;
};

// ───────────────────────────────────────────── L OBSERVATEUR AERIEN
// ⛔ CE N EST PLUS UN DRONE, ET C EST MESURE. Diagnostics du 16/08, 4 + 3 montages :
//   AR-2 Darter    -> knowsAbout 0 sur 4 montages (alt 50/100, combatMode BLUE/YELLOW)
//   MQ-4A Greyhawk -> knowsAbout 0 MEME CLOUE a 148 m juste au-dessus (dist2D = 0)
//   Hummingbird a equipage IA -> 0,91 a 20 s puis 2,87 a 25 s, la valeur de l ETALON
// Dans Arma, le capteur d un UAV alimente le TERMINAL d un operateur humain, pas la
// connaissance des unites IA. Un drone ne donne donc RIEN a l IA par lui-meme.
// On represente l observateur aerien par un helicoptere a equipage IA : c est le seul
// moyen d avoir un oeil ami en l air qui PERCOIVE, donc le seul moyen de poser la
// question de la fuite. La substitution est declaree, pas dissimulee.
// Hummingbird = NON ARME : il ne peut pas polluer la mesure par le bruit d un coup.
// ⚠️ IL SE POSE EN OBLIQUE, JAMAIS A LA VERTICALE. Diagnostic en scene pure du 16/08 :
// pose PILE AU-DESSUS (6 m, 78 m d altitude) il rend 0 pendant 60 s — la cible est sous
// son ventre, hors du champ de l equipage. Lache a 300 m et rentrant en oblique, il passe
// a 4,0 en 15 s. Le placement etait la faute, pas l engin.
HMT_DR_DRONE_POSER = {
    params ["_az"];
    private _p = [_az] call HMT_DR_POS_ENNEMI;
    // 300 m PERPENDICULAIREMENT a l axe escouade-ennemi : il observe depuis le flanc,
    // sans jamais s interposer entre l escouade et sa cible
    private _dx = (_p select 0) + 300 * sin (_az + 90);
    private _dy = (_p select 1) + 300 * cos (_az + 90);
    private _d = createVehicle ["B_Heli_Light_01_F", [_dx, _dy, 80], [], 0, "FLY"];
    createVehicleCrew _d;
    _d flyInHeight 80;
    // ⚠️ `AWARE`, PAS `CARELESS`. Smoke du 16/08 : en CARELESS le drone n acquiert AUCUNE
    // cible (saitdrone = 0 sur 2/2 reps) — CARELESS coupe la recherche de cibles, donc le
    // bras A1 ne mesurait rien. `BLUE` suffit a garantir qu il ne tire pas, et il est
    // desarme de toute facon.
    (group (driver _d)) setBehaviour "AWARE";
    (group (driver _d)) setCombatMode "BLUE";     // BLUE = ne tire jamais. Ici c est VOULU.
    _d doMove [_p select 0, _p select 1, 80];
    _d
};

// ⚠️ `deleteVehicleCrew`, PAS `deleteVehicle` sur l equipage. Mesure du 16/08 : le serveur
// est mort SILENCIEUSEMENT juste apres ce demontage — log coupe net, aucune erreur, aucun
// message d arret. Supprimer l equipage d un appareil EN VOL laisse un instant un engin
// sans pilote. `deleteVehicleCrew` est la commande faite pour ca.
HMT_DR_DRONE_DEPOSER = {
    params ["_d"];
    if (isNull _d) exitWith {};
    private _g = group (driver _d);
    { _d deleteVehicleCrew _x } forEach (crew _d);
    deleteVehicle _d;
    deleteGroup _g;
};

// ───────────────────────────────────────────── JOUER UN BRAS
// _bras : "A0" (pas de drone) | "A1" (drone, tuyau coupe) | "B" (drone + reveal 4)
// ⚠️ L AERONEF ARRIVE DE L EXTERIEUR : il est cree UNE fois par repetition et PARTAGE
// par les bras A1 et B. Chaque naissance et chaque mort d un appareil en vol secoue le
// serveur, et le serveur meurt. On en cree un seul au lieu de deux.
HMT_DR_JOUER = {
    params ["_rep", "_bras", "_az", "_drone"];

    private _s = [_az] call HMT_DR_POSER;
    _s params ["_grpSol", "_unites", "_e", "_grpEnn", "_vue"];
    // ⚠️ LA MEME ATTENTE POUR LES TROIS BRAS. Smoke du 16/08 : seuls A1 et B attendaient le
    // drone, donc A0 n avait que 30 s d exposition contre 50 — le temoin etait AVANTAGE, et
    // son « il ne tire pas » pouvait n etre qu un manque de temps.
    // 30 s et pas 20 : l helicoptere atteint 2,87 a 25 s (diagnostic du 16/08). On lui laisse
    // le temps d acquerir AVANT d ouvrir la fenetre, sinon on mesurerait sa montee en puissance.
    sleep 30;

    // ── compteurs remis a zero JUSTE avant la fenetre ──
    HMT_DR_N = 0; HMT_DR_T1 = -1; HMT_DR_NE = 0;
    private _ehs = [];
    {
        _ehs pushBack [_x, _x addEventHandler ["Fired", {
            if (HMT_DR_T1 < 0) then { HMT_DR_T1 = time - HMT_DR_T0 };
            HMT_DR_N = HMT_DR_N + 1;
        }]];
    } forEach _unites;
    private _ehE = _e addEventHandler ["Fired", { HMT_DR_NE = HMT_DR_NE + 1 }];

    // ── la fenetre ──
    private _sait_drone = 0; private _sait_grp = 0; private _sait_camp = 0;
    private _tick = 0;
    HMT_DR_T0 = time;
    // ⚠️ CE QU IL SAVAIT DEJA A L OUVERTURE. Smoke du 16/08 : une rep de A1 a tire au bout de
    // 0,3 s — impossible d apprendre si vite. La fuite s etait faite PENDANT l attente, pas
    // pendant la fenetre. Sans ce temoin d ouverture on ne saurait pas distinguer les deux.
    private _sait_grp0 = _grpSol knowsAbout _e;
    while { time - HMT_DR_T0 < HMT_DR_FEN } do {
        // le tuyau, et LUI SEUL. Repete : la fraicheur d un `reveal` decroit toute seule.
        if (_bras == "B") then { _grpSol reveal [_e, 4] };

        if (!isNull _drone) then {
            // on REPETE l ordre toutes les 5 s : sans ca l engin derive (1850 m en 40 s
            // pour l avion, mesure du 16/08) et l observateur quitte la zone qu il observe
            _tick = _tick + 1;
            if (_tick % 10 == 0) then {
                private _pe = [_az] call HMT_DR_POS_ENNEMI;
                _drone doMove [_pe select 0, _pe select 1, 80];
            };
            // ⚠️ on interroge LE VEHICULE ET TOUT L EQUIPAGE. Smoke du 16/08 : `driver _d`
            // rendait 0 sur 4/4 reps alors que le CAMP savait — on lisait la mauvaise entite,
            // et le bras A1 aurait ete declare VOID a tort.
            _sait_drone = _sait_drone max (_drone knowsAbout _e);
            { _sait_drone = _sait_drone max (_x knowsAbout _e) } forEach (crew _drone);
        };
        _sait_grp  = _sait_grp  max (_grpSol knowsAbout _e);
        _sait_camp = _sait_camp max (west knowsAbout _e);
        sleep 0.5;
    };
    { (_x select 0) removeEventHandler ["Fired", _x select 1] } forEach _ehs;
    _e removeEventHandler ["Fired", _ehE];

    private _void = if (HMT_DR_NE > 0) then { 1 } else { 0 };

    (format ["HMT|DR|rep|%1|bras|%2|az|%3|tirs|%4|t1|%5|vue|%6|saitdrone|%7|saitgrp|%8|saitcamp|%9|tirsenn|%10|void|%11|saitgrp0|%12",
             _rep, _bras, round _az, HMT_DR_N,
             (if (HMT_DR_T1 < 0) then { -1 } else { round (10 * HMT_DR_T1) / 10 }),
             round (100 * _vue) / 100,
             round (100 * _sait_drone) / 100, round (100 * _sait_grp) / 100, round (100 * _sait_camp) / 100,
             HMT_DR_NE, _void, round (100 * _sait_grp0) / 100]) call HMT_LOG;

    // l aeronef N EST PAS demonte ici : il appartient a la repetition, pas au bras
    [_grpSol, _unites, _e, _grpEnn] call HMT_DR_DEPOSER;
    sleep 2;
    HMT_DR_N
};

// ───────────────────────────────────────────── LA BOUCLE
[] spawn {
    sleep 20;                                     // on laisse le monde se poser
    (format ["HMT|DR|debut|reps|%1|fenetre|%2|dist|%3|socle|%4",
             HMT_DR_REPS, HMT_DR_FEN, HMT_DR_DIST, HMT_SOCLE_VERSION]) call HMT_LOG;

    for "_rep" from 1 to HMT_DR_REPS do {
        // ── un azimut ou la ligne de vue passe : PAR LE CALCUL, sans poser un seul homme ──
        private _az = -1; private _k = 0;
        while { _az < 0 && _k < HMT_DR_ESSAIS } do {
            private _cand = random 360;
            if ([_cand] call HMT_DR_LOS_GEO) then { _az = _cand };
            _k = _k + 1;
        };
        if (_az < 0) then {
            (format ["HMT|DR|rep|%1|bras|AUCUN|az|-1|tirs|-1|t1|-1|vue|0|saitdrone|0|saitgrp|0|saitcamp|0|tirsenn|0|void|1|saitgrp0|0",
                     _rep]) call HMT_LOG;
        } else {
            // A0 d abord, SANS aeronef : le temoin ne doit jamais partager le ciel
            [_rep, "A0", _az, objNull] call HMT_DR_JOUER;
            // puis UN SEUL aeronef pour A1 et B
            private _drone = [_az] call HMT_DR_DRONE_POSER;
            [_rep, "A1", _az, _drone] call HMT_DR_JOUER;
            [_rep, "B",  _az, _drone] call HMT_DR_JOUER;
            [_drone] call HMT_DR_DRONE_DEPOSER;
        };
    };

    "HMT|DR|TERMINE" call HMT_LOG;
};
