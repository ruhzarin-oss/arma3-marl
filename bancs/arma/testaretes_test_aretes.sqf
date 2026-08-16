// test_aretes.sqf — CONTRÔLE POSITIF de la capture d'arêtes.
//
// Objet : prouver qu'une arête écrite dans le journal dit la vérité d'une situation connue.
// Les critères sont figés dans CRITERES_CONTROLE_POSITIF.md, écrits AVANT ce script.
//
// Scène : un observateur, quatre cibles, situations connues.
//   B1 ennemi vue directe 50 m   -> l arête doit exister, vue LIBRE
//   B2 ennemi derrière un mur    -> vue BLOQUÉE  (le test le plus important)
//   B3 ennemi vue directe 300 m  -> knowsAbout doit s effondrer (falaise du 30/07)
//   C1 AMI vue directe 50 m      -> AUCUNE arête d hostilité  (le contrôle à zéro)
//
// Personne n est armé, personne n est vulnérable, personne ne bouge : on mesure la
// PERCEPTION seule. Aucun reveal — le reveal fausse structurellement ⟨mesuré 30/07⟩.

if (!isServer) exitWith {};

HMT_AR_VERSION = 1;
HMT_LOG = { diag_log _this };

// ===================== 0. TEST D EXISTENCE — AVANT TOUT APPEL =====================
// ⟨règle payée le 29/07 : une commande absente tue le gestionnaire EN SILENCE et emporte
// tout le script. currentTarget n existe pas dans ce build.⟩
// On demande au moteur sa propre liste. Une commande absente est journalisée et JAMAIS appelée.

private _toutes = supportInfo "";
(format ["HMT|X|catalogue|%1", count _toutes]) call HMT_LOG;

HMT_EXISTE = {
    private _c = toLower _this;
    private _trouve = false;
    {
        private _l = toLower _x;
        // formes rendues : "u:cmd TYPE" · "b:TYPE cmd TYPE" · "n:cmd"
        if ((_l find (":" + _c + " ")) >= 0 || (_l find (" " + _c + " ")) >= 0
            || _l == ("n:" + _c) || _l == ("u:" + _c)) exitWith { _trouve = true };
    } forEach _toutes;
    _trouve
};

HMT_DISPO = [];
{
    private _ok = _x call HMT_EXISTE;
    HMT_DISPO pushBack [_x, _ok];
    (format ["HMT|X|cmd|%1|%2", _x, (if (_ok) then {1} else {0})]) call HMT_LOG;
} forEach ["knowsAbout", "lineIntersectsSurfaces", "checkVisibility", "targetKnowledge",
           "eyePos", "aimPos", "getSuppression", "unitPos", "behaviour", "combatMode",
           "speedMode", "currentCommand", "getFatigue", "lifeState", "currentWeapon",
           "getAllHitPointsDamage", "nearTargets", "currentTarget"];

HMT_A = {                                    // une commande est-elle utilisable ?
    private _c = _this; private _r = false;
    { if ((_x select 0) == _c) exitWith { _r = _x select 1 } } forEach HMT_DISPO;
    _r
};
"HMT|OK|existence|1" call HMT_LOG;

// ===================== 1. LA SCÈNE =====================
[] spawn {
    sleep 8;

    // -- un sol plat, sec et dégagé. On VÉRIFIE, on ne suppose pas.
    // ⟨des soldats se sont noyés le 31/07 parce que le générateur ne vérifiait qu un point⟩
    private _base = [];
    {
        private _p = _x;
        private _sec = !(surfaceIsWater _p);
        private _h = getTerrainHeightASL _p;
        // planéité : on échantillonne quatre points à 60 m
        private _plat = true;
        {
            private _q = _p vectorAdd _x;
            if (surfaceIsWater _q) then { _plat = false };
            if (abs ((getTerrainHeightASL _q) - _h) > 6) then { _plat = false };
        } forEach [[60,0,0], [-60,0,0], [0,60,0], [0,-60,0], [0,320,0]];
        if (_sec && _plat && (count _base == 0)) then { _base = _p };
    } forEach [[1700,5450,0], [1780,5380,0], [1620,5520,0], [2450,5600,0], [1900,5300,0]];

    if (count _base == 0) exitWith { "HMT|OK|scene|0|ECHEC|aucun_terrain_plat" call HMT_LOG };
    (format ["HMT|A|base|%1|%2", _base select 0, _base select 1]) call HMT_LOG;

    private _grpE = createGroup east;
    private _grpW = createGroup west;

    // -- l observateur
    private _A = _grpE createUnit ["O_Soldier_F", _base, [], 0, "NONE"];
    _A setPosATL _base;

    // -- les cibles, à des azimuts séparés pour qu elles ne se masquent pas entre elles
    private _posB1 = _base vectorAdd [50, 0, 0];        // est,   50 m, dégagé
    private _posB2 = _base vectorAdd [0, -50, 0];       // sud,   50 m, MUR au milieu
    private _posB3 = _base vectorAdd [0, 300, 0];       // nord, 300 m, dégagé
    private _posC1 = _base vectorAdd [-50, 0, 0];       // ouest, 50 m, AMI

    private _B1 = _grpW createUnit ["B_Soldier_F", _posB1, [], 0, "NONE"];  _B1 setPosATL _posB1;
    private _B2 = _grpW createUnit ["B_Soldier_F", _posB2, [], 0, "NONE"];  _B2 setPosATL _posB2;
    private _B3 = _grpW createUnit ["B_Soldier_F", _posB3, [], 0, "NONE"];  _B3 setPosATL _posB3;
    private _C1 = _grpE createUnit ["O_Soldier_F", _posC1, [], 0, "NONE"];  _C1 setPosATL _posC1;

    // -- LE MUR, entre A et B2. Trois murs bout à bout : un seul laisse passer sur les côtés.
    private _murs = [];
    {
        private _m = createVehicle ["Land_CncWall4_F", (_base vectorAdd [_x, -25, 0]), [], 0, "CAN_COLLIDE"];
        _m setDir 90;                                   // face à la ligne A-B2
        _m setVectorUp surfaceNormal position _m;
        _murs pushBack _m;
    } forEach [-4, 0, 4];
    (format ["HMT|A|mur|%1|hauteur|%2", count _murs,
             (((boundingBoxReal (_murs select 0)) select 1) select 2)]) call HMT_LOG;

    // -- personne n est armé, personne ne meurt, personne ne bouge : perception PURE.
    // On garde l IA de ciblage active (c est ce qu on mesure), on coupe le déplacement.
    {
        removeAllWeapons _x;
        _x allowDamage false;
        _x disableAI "PATH";
        _x disableAI "AUTOCOMBAT";
        _x setBehaviour "COMBAT";                       // sens en éveil, sans mouvement
        _x setUnitPos "UP";
    } forEach [_A, _B1, _B2, _B3, _C1];

    _A setDir 0;

    private _noms = [[_B1, "B1_ennemi_50m_degage"], [_B2, "B2_ennemi_50m_MUR"],
                     [_B3, "B3_ennemi_300m_degage"], [_C1, "C1_AMI_50m_degage"]];
    {
        (format ["HMT|A|cible|%1|%2|%3|dist|%4|camp|%5", _forEachIndex, (_x select 1),
                 (if (side (_x select 0) == east) then {"EAST"} else {"WEST"}),
                 round (_A distance (_x select 0)),
                 (if ((side (_x select 0)) == (side _A)) then {"AMI"} else {"ENNEMI"})]) call HMT_LOG;
    } forEach _noms;

    "HMT|OK|scene|1" call HMT_LOG;

    // ===================== 2. L ÉMISSION DES ARÊTES =====================
    // Une ligne par LIEN, jamais une grille : la matrice est creuse ⟨knowsAbout tombe à 0
    // au-delà de 100 m, mesuré 30/07⟩. Python reconstruira la matrice hors ligne.
    //
    // On écrit ici TOUTES les paires, amies comprises, avec le drapeau hostile — c est ce qui
    // permet au contrôle n°4 de répondre zéro sur autre chose que notre bonne foi.

    private _kOk   = "knowsAbout" call HMT_A;
    private _losOk = "lineIntersectsSurfaces" call HMT_A;
    private _visOk = "checkVisibility" call HMT_A;
    private _tkOk  = "targetKnowledge" call HMT_A;

    private _n = 0;
    while { _n < 90 } do {                              // 90 × 2 s = 180 s
        _n = _n + 1;
        private _t = round (time * 10) / 10;
        {
            private _B = _x select 0;
            private _nom = _x select 1;

            // ce que seul le moteur sait — capturé en direct
            private _k = if (_kOk) then { round ((_A knowsAbout _B) * 100) / 100 } else { -9 };

            private _los = -9;
            if (_losOk) then {
                private _i = lineIntersectsSurfaces [eyePos _A, aimPos _B, _A, _B, true, 1, "VIEW", "FIRE"];
                _los = if (count _i == 0) then { 1 } else { 0 };
            };

            private _vis = -9;
            if (_visOk) then {
                _vis = round (([objNull, "VIEW"] checkVisibility [eyePos _A, aimPos _B]) * 100) / 100;
            };

            // targetKnowledge : plus riche que knowsAbout — position CRUE par l IA, âge de l info
            private _tkVu = -9; private _tkAge = -9;
            if (_tkOk) then {
                private _tk = _A targetKnowledge _B;
                if ((count _tk) > 2) then {
                    _tkVu = if (_tk select 1) then { 1 } else { 0 };
                    _tkAge = round ((time - (_tk select 2)) * 10) / 10;
                };
            };

            private _hostile = if ((side _B) == (side _A)) then { 0 } else { 1 };

            // la géométrie n est PAS émise : distance et gisement se recalculent hors ligne
            // à partir des positions ⟨Fable, 02/08 : ne payer en direct que le savoir moteur⟩
            (format ["HMT|AR|%1|%2|A|%3|k|%4|los|%5|vis|%6|tkvu|%7|tkage|%8|host|%9",
                     _n, _t, _nom, _k, _los, _vis, _tkVu, _tkAge, _hostile]) call HMT_LOG;
        } forEach _noms;
        sleep 2;
    };

    (format ["HMT|OK|aretes|1|ticks|%1", _n]) call HMT_LOG;
    "HMT|A|FIN" call HMT_LOG;
};

"HMT|OK|test_aretes|1" call HMT_LOG;
