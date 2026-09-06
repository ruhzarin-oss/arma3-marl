// =====================================================================
// CHACAL - SOCLE. Journal, tirage reproductible, garde-fous, vocabulaire.
//
// Regle de la maison : rien ici ne doit pouvoir rendre un episode VERT sur
// du vide. Chaque instrument annonce sa propre ligne OK ; le lecteur Python
// exige ces lignes avant d accepter le corpus.
// =====================================================================

CHACAL_VERSION = 1;
CHACAL_LOG = { diag_log _this };            // le RPT survit a ce qui tue le pont

// --- parametres de l episode ( reecrits par le harnais dans server.cfg ) ---
CHACAL_GRAINE  = (["CHACAL_GRAINE", 0] call BIS_fnc_getParamValue)
               + 32 * (["CHACAL_GRAINE_HAUT", 0] call BIS_fnc_getParamValue);
CHACAL_ECHELLE = (["CHACAL_ECHELLE", 100] call BIS_fnc_getParamValue) / 100;
CHACAL_DT      = (["CHACAL_DTCS", 100] call BIS_fnc_getParamValue) / 100;
if (CHACAL_ECHELLE <= 0) then { CHACAL_ECHELLE = 1 };
if (CHACAL_DT <= 0) then { CHACAL_DT = 1 };
// 0 = le PLAN en six phases, 1 = le TEMOIN qui marche droit
CHACAL_BRAS   = if ((["CHACAL_BRAS", 0] call BIS_fnc_getParamValue) == 1) then {"NUL"} else {"PLAN"};
CHACAL_JOUR   = ["CHACAL_JOUR", 0] call BIS_fnc_getParamValue;
CHACAL_DEPART = ["CHACAL_DEPART", 1] call BIS_fnc_getParamValue;
CHACAL_PALIER = ["CHACAL_PALIER", 3] call BIS_fnc_getParamValue;
CHACAL_IMMORTEL = ["CHACAL_IMMORTEL", 0] call BIS_fnc_getParamValue;

// --- LE TIRAGE EST A NOUS, PAS AU MOTEUR -----------------------------
// `setRandomSeed` n existe pas dans ce build ( mesure du 03/09 : Missing ; a
// la compilation ). On porte donc son propre generateur, et c est mieux ainsi :
// reproductible independamment du moteur, et il ne perturbe pas le hasard
// interne d Arma, qui doit rester libre pour que LAMBS decide vraiment.
//
// Lehmer, modulo 65537, multiplicateur 75. Le produit intermediaire plafonne a
// 4,9 millions : sous 2^24, donc EXACT en flottant simple - le scalaire SQF est
// un float32 et un generateur a grand module y perdrait des bits en silence.
CHACAL_RNG = ((CHACAL_GRAINE * 7919) + 104729) % 65537;
if (CHACAL_RNG == 0) then { CHACAL_RNG = 1 };
CHACAL_fnc_rnd = {
    CHACAL_RNG = ((CHACAL_RNG * 75) + 74) % 65537;
    CHACAL_RNG / 65537
};
CHACAL_fnc_al = { (call CHACAL_fnc_rnd) * _this };      // uniforme sur [0 ; _this[
// On brule les premiers tirages : deux graines voisines commenceraient sinon
// au meme endroit.
for "_i" from 1 to 20 do { call CHACAL_fnc_rnd };

// --- etat de l episode ---
CHACAL_PHASE      = 0;
CHACAL_PHASE_NOM  = "AUCUNE";
CHACAL_ALARME     = false;      // le camp EST a compris - irreversible
CHACAL_COMPROMIS  = false;      // NOUS nous en sommes rendu compte
CHACAL_FIN        = false;
CHACAL_ISSUE      = "";
CHACAL_CAUSE      = "";
CHACAL_MANQUANTES = [];
CHACAL_PROPS      = [];
CHACAL_OUVERTURES = []; CHACAL_OUV_AZ = [];

// --- plafonds : valeurs de repli, RECALCULEES dans 10_monde ----------
// La phase 2 avait 1800 s au tableau et en a pris 4163 : ses sous-etapes
// etaient budgetees sur la distance, le total ne l etait pas. Un plafond qu on
// depasse de 130 pour cent n est pas un plafond.
CHACAL_DUREES = [900, 1800, 1500, 900, 900, 600];
CHACAL_fnc_duree = { (CHACAL_DUREES select (_this - 1)) * CHACAL_ECHELLE };

// L HORLOGE DE PHASE. Toute attente s y refere : une sous-etape ne peut pas
// emprunter du temps a la phase suivante.
CHACAL_TPHASE = 0;
CHACAL_PLAFOND_COURANT = 1e9;
CHACAL_fnc_reste = { (CHACAL_TPHASE + CHACAL_PLAFOND_COURANT) - time };

CHACAL_fnc_has = { isClass (configFile >> "CfgVehicles" >> (_this select 0)) };

// --- un groupe vide rend des distances absurdes ( 19 632 m le 26/08 ) ---
CHACAL_fnc_centre = {
    private _v = _this select { alive _x };
    if (count _v == 0) exitWith { [] };
    private _sx = 0; private _sy = 0;
    { private _p = getPosATL _x; _sx = _sx + (_p select 0); _sy = _sy + (_p select 1); } forEach _v;
    [_sx / (count _v), _sy / (count _v), 0]
};

// --- LE GARDE-FOU ETAIT LE PIEGE ( mesure du 04/09 ) -----------------
// La phase 6 demandait le budget du repli a CHACAL_gFS - un groupe VIDE depuis
// la scission - et la fonction rendait son defaut " prudent " de 120 s :
// exfiltration de 4 088 m avec deux minutes au compteur, PLAFOND garanti, et
// rien dans le journal pour le dire. La fonction accepte donc une LISTE autant
// qu un groupe, et son defaut CRIE au lieu de se faire passer pour un calcul.
CHACAL_fnc_budget = {
    params ["_g", "_p", ["_v", 0.5]];
    private _u = if (_g isEqualType grpNull) then { units _g } else { _g };
    if (isNil "_u") exitWith { 120 };
    _u = _u select { alive _x };
    if (count _u == 0) exitWith {
        (format ["CHACAL|AVERT|budget_defaut|%1|aucun_homme|vers|%2", round (time * 100) / 100, _p]) call CHACAL_LOG;
        120
    };
    private _c = _u call CHACAL_fnc_centre;
    if (count _c == 0) exitWith {
        (format ["CHACAL|AVERT|budget_defaut|%1|centre_vide|vers|%2", round (time * 100) / 100, _p]) call CHACAL_LOG;
        120
    };
    600 + ((_c distance2D _p) / _v)
};

CHACAL_fnc_pose = {
    params ["_cls", "_c", "_dx", "_dy", "_dir"];
    if (!([_cls] call CHACAL_fnc_has)) exitWith { CHACAL_MANQUANTES pushBackUnique _cls; objNull };
    private _p = [(_c select 0) + _dx, (_c select 1) + _dy, 0];
    private _o = createVehicle [_cls, _p, [], 0, "CAN_COLLIDE"];
    _o setDir _dir; _o setPosATL [_p select 0, _p select 1, 0];
    CHACAL_PROPS pushBack _o; _o
};
// Pose en POLAIRE RELATIVE a l axe du site. Le premier jet batissait l enceinte
// en gisement absolu pendant que les batiments tournaient : l assaut visait un mur.
CHACAL_fnc_poseP = {
    params ["_cls", "_c", "_dist", "_gis", ["_dirRel", 0]];
    private _p = _c getPos [_dist, CHACAL_AZ + _gis];
    [_cls, _c, (_p select 0) - (_c select 0), (_p select 1) - (_c select 1), CHACAL_AZ + _dirRel] call CHACAL_fnc_pose
};

// --- vue franche entre deux POINTS ( pour choisir la crete ) ---
CHACAL_fnc_libre = {
    params ["_p", "_q"];
    private _a = [_p select 0, _p select 1, (getTerrainHeightASL _p) + 1.6];
    private _b = [_q select 0, _q select 1, (getTerrainHeightASL _q) + 1.6];
    if (terrainIntersectASL [_a, _b]) exitWith { false };
    (count (lineIntersectsSurfaces [_a, _b, objNull, objNull, true, 1, "VIEW", "VIEW"])) == 0
};

// --- CE QU UN HOMME PEUT ATTEINDRE DE L OEIL, et rien d autre ---
// Portee, cone, ligne de vue. Aucun appel a knowsAbout : c est le seul canal
// opposable a la vue de camp.
CHACAL_fnc_voit = {
    params ["_u", "_e", ["_portee", 800], ["_cone", 55]];
    if (!alive _u || { !alive _e }) exitWith { false };
    if ((_u distance _e) > _portee) exitWith { false };
    private _rel = abs ((((_u getDir _e) - (getDir _u) + 540) % 360) - 180);
    if (_rel > _cone) exitWith { false };
    private _a = (getPosASL _u) vectorAdd [0, 0, 1.5];
    private _b = (getPosASL _e) vectorAdd [0, 0, 1.2];
    (count (lineIntersectsSurfaces [_a, _b, _u, _e, true, 1, "VIEW", "VIEW"])) == 0
};

// --- replat : critere de SERPENT NOIR, il a fait ses preuves ---
CHACAL_fnc_plat = {
    params ["_c", "_r", ["_essais", 220]];
    private _best = +_c; private _sc = 1e9;
    for "_i" from 1 to _essais do {
        private _p = _c getPos [sqrt(call CHACAL_fnc_rnd) * _r, 360 call CHACAL_fnc_al];
        if (!surfaceIsWater _p) then {
            private _h = getTerrainHeightASL _p; private _dev = 0;
            for "_k" from 0 to 7 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [20, _k * 45])) - _h)) };
            private _s = _dev + 5 * (count (nearestObjects [_p, ["House"], 70]));
            if (_s < _sc) then { _sc = _s; _best = _p };
        };
    };
    _best set [2, 0]; _best
};

// --- LE CONTROLE POSITIF DU MOD ---
// Sans lui, un serveur lance sans -serverMod produirait un corpus d IA VANILLE
// etiquete LAMBS. C est le genre de vert-sur-vide qui coute un mois.
CHACAL_LAMBS = !(isNil "lambs_wp_fnc_taskPatrol") && { !(isNil "lambs_danger_fnc_tactics") };

// --- L EMPREINTE DU MONDE ---
// LAMBS fabrique une part de la vue de camp par ses reglages radio CBA : deux
// nuits aux reglages differents ne sont pas le meme monde. On publie de quoi
// REFUSER une fusion.
CHACAL_fnc_empreinte = {
    private _h = 0;
    { { _h = ((_h * 31) + _x) % 1048573 } forEach (toArray _x); } forEach activatedAddons;
    _h
};
CHACAL_fnc_reglage = {
    private _v = missionNamespace getVariable [_this, -1];
    if (_v isEqualType true) then { if (_v) then {1} else {0} } else { _v }
};
(format ["CHACAL|EMPREINTE|version|%1|addons|%2|somme|%3|lune|%4|radioShout|%5|radioBackpack|%6|maxRange|%7|cqbRange|%8|manoeuvres|%9",
    productVersion select 2, count activatedAddons, call CHACAL_fnc_empreinte,
    round ((moonPhase date) * 1000) / 1000,
    ("lambs_main_radioShout" call CHACAL_fnc_reglage), ("lambs_main_radioBackpack" call CHACAL_fnc_reglage),
    ("lambs_danger_maxRange" call CHACAL_fnc_reglage), ("lambs_danger_cqbRange" call CHACAL_fnc_reglage),
    ("lambs_danger_disableAIAutonomousManoeuvres" call CHACAL_fnc_reglage)]) call CHACAL_LOG;

(format ["CHACAL|OK|socle|%1|graine|%2|echelle|%3|dt|%4|lambs|%5|bras|%6|depart|%7|jour|%8|palier|%9|immortel|%10",
    CHACAL_VERSION, CHACAL_GRAINE, CHACAL_ECHELLE, CHACAL_DT,
    (if (CHACAL_LAMBS) then {1} else {0}), CHACAL_BRAS, CHACAL_DEPART, CHACAL_JOUR, CHACAL_PALIER, CHACAL_IMMORTEL]) call CHACAL_LOG;
