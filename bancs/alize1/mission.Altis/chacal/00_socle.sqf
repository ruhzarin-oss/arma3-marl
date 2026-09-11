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
CHACAL_ARRET  = ["CHACAL_ARRET", 6] call BIS_fnc_getParamValue;   // vignette : derniere phase jouee
CHACAL_PALIER = ["CHACAL_PALIER", 3] call BIS_fnc_getParamValue;
CHACAL_IMMORTEL = ["CHACAL_IMMORTEL", 0] call BIS_fnc_getParamValue;
// ! DEUX LEVIERS AJOUTES LE 08/09, un par cause mesuree sur les graines 7 et 8.
// -1 laisse le palier decider : par defaut, rien ne change.
// ! CHACAL_TENIR : poursuivre le plan malgre la compromission (0 = regle prudente d origine).
// La compromission reste JOURNALISEE a l identique ; seule la REACTION change.
// ! CHACAL_ACCESSIBLE : exiger qu une position soit ATTEIGNABLE, pas seulement plate.
// 0 = comportement d origine, conserve pour que tout ce qui precede reste comparable.
// ! CHACAL_EFFECTIF : taille du detachement. 10 = d origine.
// A 20, la liste des roles est jouee deux fois : chaque element double, et le corpus
// continue de porter les memes noms de role.
// ! CHACAL_APPUI_FEU : donner a l appui une position choisie pour TIRER, distincte de
// l observatoire. 0 = comportement d origine, ou l appui reste a l observatoire.
CHACAL_APPUI_FEU = ["CHACAL_APPUI_FEU", 0] call BIS_fnc_getParamValue;
// ! CHACAL_FEU_AVANT ( Fable, 10/09 ) : l appui connait et vise les defenseurs, l assaut attend son
// premier coup, puis marche en AWARE avec un ordre relance toutes les 10 s. 0 = comportement d origine.
CHACAL_FEU_AVANT = ["CHACAL_FEU_AVANT", 0] call BIS_fnc_getParamValue;
// ! CAMPAGNE GRAINE 8 ( Fable, 11/09 ) - trois leviers, 0 / 45 = comportement d origine.
CHACAL_MG_ASSAUT = ["CHACAL_MG_ASSAUT", 0] call BIS_fnc_getParamValue;
CHACAL_DELAI_PORTEUR = ["CHACAL_DELAI_PORTEUR", 45] call BIS_fnc_getParamValue;
CHACAL_APPUI_FIXE = ["CHACAL_APPUI_FIXE", 0] call BIS_fnc_getParamValue;
CHACAL_EFFECTIF = ["CHACAL_EFFECTIF", 10] call BIS_fnc_getParamValue;
CHACAL_ACCESSIBLE = ["CHACAL_ACCESSIBLE", 0] call BIS_fnc_getParamValue;
CHACAL_TENIR = ["CHACAL_TENIR", 0] call BIS_fnc_getParamValue;
CHACAL_HMG_FORCE = ["CHACAL_HMG", -1] call BIS_fnc_getParamValue;
CHACAL_ASSAUT_X  = (["CHACAL_ASSAUT_X", 100] call BIS_fnc_getParamValue) / 100;

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
// ! PENALITE DE TRAJET ( 09/09 ). La version d origine gardait le point le plus PLAT
// LOCALEMENT et ne regardait jamais le chemin pour y aller. Un replat perche au-dessus d un
// talus de 30 degres lui convient parfaitement, et le calculateur de chemin d Arma s y arrete
// en declarant le deplacement TERMINE, a 800 m de la cible. C est ce qui a fait echouer le
// palier 4 sans qu un seul coup soit tire.
// Le quatrieme argument est le point de DEPART. Il est optionnel : sans lui, ou si
// CHACAL_ACCESSIBLE vaut 0, la fonction se comporte exactement comme avant.
CHACAL_fnc_penteTrajet = {
    params ["_a", "_b"];
    private _d = _a distance2D _b;
    if (_d < 30) exitWith { 0 };
    private _n = (round (_d / 25)) max 1;
    private _pire = 0; private _hp = getTerrainHeightASL _a;
    for "_i" from 1 to _n do {
        private _q = _a getPos [(_d * _i) / _n, _a getDir _b];
        private _h = getTerrainHeightASL _q;
        _pire = _pire max (abs (atan ((_h - _hp) / (_d / _n))));
        _hp = _h;
    };
    _pire
};
// ! UNE POSITION D APPUI N EST PAS UN OBSERVATOIRE ( mesure du 09/09 ).
// L observatoire veut la vue d ensemble et la distance ; l appui veut la vue SUR L OUVERTURE et
// la portee utile. Les confondre a coute cinq hommes en 38 secondes sans qu une seule balle
// parte du detachement.
// On cherche sur un arc autour du site : portee utile, ligne de vue degagee vers l ouverture,
// azimut decale de l axe d assaut pour ne pas tirer dans le dos de son propre assaut, et un
// terrain ou un homme peut se coucher.
// Rend l observatoire en repli si rien ne convient : une mission qui ne trouve pas sa position
// d appui doit se degrader, pas s arreter.
CHACAL_fnc_positionAppui = {
    params ["_site", "_ouverture", "_axeAssaut", "_repli"];
    private _azOuv = _site getDir _ouverture;
    private _best = []; private _sc = -1e9;
    private _cible = +_ouverture; _cible set [2, (getTerrainHeightASL _ouverture) + 1.0];
    for "_i" from 1 to 160 do {
        // decalage de 40 a 120 degres de l axe d assaut, d un cote ou de l autre
        private _cote = if ((call CHACAL_fnc_rnd) < 0.5) then {1} else {-1};
        private _dec = _cote * (40 + (80 call CHACAL_fnc_al));
        private _dist = 160 + (190 call CHACAL_fnc_al);
        private _p = _site getPos [_dist, _azOuv + _dec];
        if (surfaceIsWater _p) then { continue };
        // un homme couche a besoin d un metre de terrain sain
        private _h = getTerrainHeightASL _p; private _dev = 0;
        for "_k" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [12, _k * 60])) - _h)) };
        if (_dev > 6) then { continue };
        // LA condition qui manquait : voit-il vraiment l ouverture ?
        private _oeil = +_p; _oeil set [2, _h + 1.2];
        if (count (lineIntersectsSurfaces [_oeil, _cible, objNull, objNull, true, 1]) > 0) then { continue };
        // on prefere etre un peu plus haut que la cible, et pas trop loin
        private _dOuv = _p distance2D _ouverture;
        private _gain = _h - (getTerrainHeightASL _ouverture);
        private _s = (0 max (10 - (abs (_dOuv - 250)) / 25)) + ((_gain max -10) min 20) / 4 - _dev / 3;
        if (_s > _sc) then { _sc = _s; _best = _p };
    };
    if (count _best == 0) exitWith {
        (format ["CHACAL|AVERT|appui_feu|aucune_position|repli_observatoire"]) call CHACAL_LOG;
        _repli
    };
    _best set [2, 0];
    (format ["CHACAL|OK|appui_feu|position|%1|dist_ouverture|%2|gain|%3|score|%4|decal_axe|%5",
        _best, round (_best distance2D _ouverture),
        round ((getTerrainHeightASL _best) - (getTerrainHeightASL _ouverture)), round _sc,
        round (abs ((_site getDir _best) - (_site getDir _axeAssaut)))]) call CHACAL_LOG;
    _best
};

CHACAL_fnc_plat = {
    params ["_c", "_r", ["_essais", 220], ["_depuis", []]];
    private _best = +_c; private _sc = 1e9;
    private _garde = (CHACAL_ACCESSIBLE == 1) && { count _depuis > 0 };
    for "_i" from 1 to _essais do {
        private _p = _c getPos [sqrt(call CHACAL_fnc_rnd) * _r, 360 call CHACAL_fnc_al];
        if (!surfaceIsWater _p) then {
            private _h = getTerrainHeightASL _p; private _dev = 0;
            for "_k" from 0 to 7 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [20, _k * 45])) - _h)) };
            private _s = _dev + 5 * (count (nearestObjects [_p, ["House"], 70]));
            // Une pente au-dela de 20 degres sur le trajet coute cher, et tres cher au-dela de 30.
            // On PENALISE au lieu de REFUSER : un terrain entierement raide doit quand meme
            // rendre un point, sinon la mission s arrete au lieu de se degrader.
            if (_garde) then {
                private _pt = [_depuis, _p] call CHACAL_fnc_penteTrajet;
                if (_pt > 20) then { _s = _s + 3 * (_pt - 20) };
                if (_pt > 30) then { _s = _s + 10 * (_pt - 30) };
            };
            if (_s < _sc) then { _sc = _s; _best = _p };
        };
    };
    if (_garde) then {
        (format ["CHACAL|OK|plat|accessible|1|depuis|%1|choisi|%2|pente_trajet|%3|score|%4",
            _depuis, _best, round ([_depuis, _best] call CHACAL_fnc_penteTrajet), round _sc]) call CHACAL_LOG;
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

(format ["CHACAL|OK|socle|%1|graine|%2|echelle|%3|dt|%4|lambs|%5|bras|%6|depart|%7|jour|%8|palier|%9|immortel|%10|tenir|%11|arret|%12",
    CHACAL_VERSION, CHACAL_GRAINE, CHACAL_ECHELLE, CHACAL_DT,
    (if (CHACAL_LAMBS) then {1} else {0}), CHACAL_BRAS, CHACAL_DEPART, CHACAL_JOUR, CHACAL_PALIER, CHACAL_IMMORTEL, CHACAL_TENIR, CHACAL_ARRET]) call CHACAL_LOG;
