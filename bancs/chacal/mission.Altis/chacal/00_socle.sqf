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
// ! CHACAL_ORACLE ( Fable, 11/09 ) : les defenseurs reveles a tous et inscrits comme vus. 0 = origine.
CHACAL_ORACLE = ["CHACAL_ORACLE", 0] call BIS_fnc_getParamValue;
// ! LE SOCLE ET LES TACTIQUES ( 11/09 ). 0 = comportement d origine dans les deux cas.
CHACAL_SOCLE = ["CHACAL_SOCLE", 0] call BIS_fnc_getParamValue;
// ! LA COUTURE DE L AZIMUT. C est le premier endroit de la mission ou un agent decide.
// L atelier du 13/09 a mesure que l axe d approche commande l entree : azimut 45, zero entree
// sur cinq essais ; azimut 0, 3,8 en moyenne ; azimut 126, 2,6. Le script, lui, ne choisit
// qu entre les deux ouvertures - il s interdit le mur plein a l azimut 0, qui fait mieux.
//   0 SCRIPT : le score sur les deux ouvertures, inchange.
//   1 HASARD : tirage uniforme parmi douze azimuts. LE PLANCHER, et il est obligatoire.
//   2 IMPOSE : l azimut vient du job, en degres. C est par la qu un agent decide.
CHACAL_AZIMUT = ["CHACAL_AZIMUT", 0] call BIS_fnc_getParamValue;
CHACAL_AZIMUT_VAL = ["CHACAL_AZIMUT_VAL", 0] call BIS_fnc_getParamValue;
CHACAL_AZIMUT_CHOISI = -1;   // ce qui a REELLEMENT ete joue, ecrit dans la ligne FINI
// ! CHACAL_EXFIL : ce qui fait echouer l exfiltration. 12 episodes sur 12 finissent en PLAFOND
// avec des hommes vivants - jusqu a 9 vivants pour 3 exfiltres. Deux causes possibles, un levier
// pour les separer. 0 = la reference. 1 = repasser en AWARE une fois le contact rompu, a plus de
// 300 m du site, le plafond inchange : si cela suffit, la cause est le comportement. 2 = garder
// le comportement et calculer le budget a 1,2 m/s au lieu de 1,8 : si cela suffit, la cause est
// le chronometre, et c est l estimation qui etait fausse.
CHACAL_EXFIL = ["CHACAL_EXFIL", 0] call BIS_fnc_getParamValue;
CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;
// ! CONTROLE POSITIF DE L APPUI ( Fable, regle 16 ) : 0 non, 1 appui CLOUE comme dans le socle, 2 appui NON CLOUE.
// L appui reste a SA position : on ne change qu une chose a la fois.
// ! LE PLACEUR ( banc du 12/09 ) : 0 = ancien ( vue sur l ouverture ), 1 = nouveau ( bat le plancher du site ).
CHACAL_PLACEUR = ["CHACAL_PLACEUR", 0] call BIS_fnc_getParamValue;
CHACAL_COUV = -1;   // part des points interieurs battus depuis la position retenue
CHACAL_BANC_APPUI = ["CHACAL_BANC_APPUI", 0] call BIS_fnc_getParamValue;
CHACAL_TIRS_BANC = 0;
// ! ABLATION PAR RETRAIT ( revue du 12/09 ) : masque de ce qu on ENLEVE au socle.
//   1 sans chien de garde . 2 sans porteurs non combattants . 4 sans appui cloue . 8 sans revelation par le tir.
CHACAL_ABLATION = ["CHACAL_ABLATION", 0] call BIS_fnc_getParamValue;
CHACAL_fnc_sans = { (floor (CHACAL_ABLATION / _this)) % 2 == 1 };   // _this = le bit teste
CHACAL_CONNUS = [];          // defenseurs qui se sont trahis en tirant
CHACAL_T_PREMIER_TIR_APPUI = -1;
CHACAL_RELANCES_SOCLE = 0; CHACAL_FUMIGENES = 0; CHACAL_ZONES = 0;
CHACAL_SANS_JAMBES = 0;   // hommes vivants incapables de marcher a l exfiltration - la garde du 13/09
CHACAL_CIBLE_ASSAUT = [];   // ! posee ici : le chien de garde demarrait avant son initialisation
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
// ! LE PLANCHER DU SITE : 37 points fixes a l interieur, a 1,1 m du sol, la ou des hommes se tiennent.
// Aucune connaissance des defenseurs : c est de la geometrie, disponible au moment du choix.
CHACAL_fnc_plancher = {
    private _R = 45;
    if (count CHACAL_OBJETS > 0) then {
        { _R = _R max ((_x distance2D CHACAL_SITE) + 15) } forEach CHACAL_OBJETS;
    };
    _R = (_R max 30) min 80;
    private _pts = [];
    private _c = +CHACAL_SITE; _c set [2, (getTerrainHeightASL CHACAL_SITE) + 1.1];
    _pts pushBack _c;
    {
        _x params ["_r", "_n", "_dec"];
        for "_i" from 0 to (_n - 1) do {
            private _p = CHACAL_SITE getPos [_R * _r, _dec + (_i * 360 / _n)];
            _p set [2, (getTerrainHeightASL _p) + 1.1];
            _pts pushBack _p;
        };
    } forEach [[0.30, 8, 0], [0.60, 12, 15], [0.85, 16, 7]];
    _pts
};

// La couverture d un candidat : la part du plancher que son oeil atteint. 0 = il ne bat rien, 1 = il bat tout.
CHACAL_fnc_couverture = {
    params ["_p", "_plancher"];
    private _oeil = +_p; _oeil set [2, (getTerrainHeightASL _p) + 1.5];
    private _n = 0;
    { if (count (lineIntersectsSurfaces [_oeil, _x, objNull, objNull, true, 1]) == 0) then { _n = _n + 1 } } forEach _plancher;
    _n / (count _plancher)
};

CHACAL_fnc_positionAppui = {
    params ["_site", "_ouverture", "_axeAssaut", "_repli"];
    private _azOuv = _site getDir _ouverture;
    // ! PLACEUR QUI BAT LE PLANCHER ( 12/09 ). L ancien certifiait la vue vers l OUVERTURE : 79 postes sur 80
    // ne voyaient aucun defenseur, et l appui s est tu dans quatre mesures d affilee.
    if (CHACAL_PLACEUR == 1) exitWith {
        // ! CONTROLE POSITIF ( regle 16 ). Deux episodes identiques ont repondu 0,541 et 0 sur les memes 288
        // candidats, avec les memes refus geometriques : ce n est pas le terrain qui change, c est la mesure qui
        // ne repond pas toujours. Le temoin est un rayon dont on connait la reponse : depuis le centre du site,
        // a 2 m de haut, on voit forcement une large part du plancher. Si le temoin repond 0, la mesure est
        // muette, et on RECOMMENCE au lieu de conclure qu aucune position ne bat le site.
        private _plancher = call CHACAL_fnc_plancher;
        private _np = count _plancher;
        private _solSite = getTerrainHeightASL _site;
        private _azAss = _site getDir _axeAssaut;
        private _best = []; private _sc = -1e9; private _couv = 0;
        private _passe = 0; private _temoin = 0; private _meilleurBrut = 0;
        private _vus = 0; private _refus = [0, 0, 0];   // eau, pente, axe d assaut
        while { _passe < 3 && { count _best == 0 } } do {
            _passe = _passe + 1;
            if (_passe > 1 && { canSuspend }) then { sleep 6 };
            private _oT = +_site; _oT set [2, _solSite + 2]; _temoin = 0;
            { if (count (lineIntersectsSurfaces [_oT, _x, objNull, objNull, true, 1]) == 0) then { _temoin = _temoin + 1 } } forEach _plancher;
            _temoin = _temoin / _np;
            _sc = -1e9; _meilleurBrut = 0; _vus = 0; _refus = [0, 0, 0];
            for "_a" from 0 to 35 do {
                for "_k" from 3 to 10 do {
                    private _dist = _k * 50;
                    private _az = _a * 10;
                    private _p = _site getPos [_dist, _az];
                    _vus = _vus + 1;
                    if (surfaceIsWater _p) then { _refus set [0, (_refus select 0) + 1]; continue };
                    // ne pas tirer dans le dos de son propre assaut : au moins 25 degres d ecart a son axe
                    private _ecart = abs (((_az - _azAss) + 540) % 360 - 180);
                    if (_ecart < 25) then { _refus set [2, (_refus select 2) + 1]; continue };
                    private _h = getTerrainHeightASL _p; private _dev = 0;
                    for "_j" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [5, _j * 60])) - _h)) };
                    if (_dev > 3) then { _refus set [1, (_refus select 1) + 1]; continue };
                    private _c = [_p, _plancher] call CHACAL_fnc_couverture;
                    if (_c > _meilleurBrut) then { _meilleurBrut = _c };
                    private _gain = _h - _solSite;
                    private _s = 3 * _c + (((_gain max -10) min 20) / 20) - ((abs (_dist - 250)) / 250) - (_dev / 12);
                    if (_c > 0 && { _s > _sc }) then { _sc = _s; _best = _p; _couv = _c };
                };
            };
            // ! SONDES : quatre points fixes a 150 m, pour NOMMER ce qui arrete les rayons.
            {
                private _az = _x;
                private _ps = _site getPos [150, _az];
                private _os = +_ps; _os set [2, (getTerrainHeightASL _ps) + 1.5];
                private _libre = 0; private _terr = 0; private _types = [];
                {
                    private _r = lineIntersectsSurfaces [_os, _x, objNull, objNull, true, 1];
                    if (count _r == 0) then { _libre = _libre + 1 } else {
                        private _e = (_r select 0) select 3;
                        if (isNull _e) then { _terr = _terr + 1 } else { _types pushBackUnique (typeOf _e) };
                    };
                } forEach _plancher;
                (format ["CHACAL|E|appui_sonde|%1|passe|%2|azimut|%3|libres|%4|sur|%5|terrain|%6|objets|%7|gain|%8",
                    round (time * 100) / 100, _passe, _az, _libre, _np, _terr, _types,
                    round ((getTerrainHeightASL _ps) - _solSite)]) call CHACAL_LOG;
            } forEach [0, 90, 180, 270];
            (format ["CHACAL|E|appui_balayage|%1|passe|%2|temoin|%3|balayes|%4|refus_eau|%5|refus_pente|%6|refus_axe|%7|meilleure_couverture|%8|retenue|%9",
                round (time * 100) / 100, _passe, round (_temoin * 1000) / 1000, _vus, _refus select 0, _refus select 1,
                _refus select 2, round (_meilleurBrut * 1000) / 1000, count _best]) call CHACAL_LOG;
        };
        CHACAL_COUV = round (_couv * 1000) / 1000;
        if (count _best == 0 || { _couv < 0.25 }) exitWith {
            (format ["CHACAL|AVERT|appui_feu|aucune_position_battante|meilleure_couverture|%1|temoin|%2|passes|%3",
                round (_meilleurBrut * 1000) / 1000, round (_temoin * 1000) / 1000, _passe]) call CHACAL_LOG;
            (format ["CHACAL|E|appui_feu|%1|placeur|1|couverture|%2|temoin|%3|refuse|1",
                round (time * 100) / 100, CHACAL_COUV, round (_temoin * 1000) / 1000]) call CHACAL_LOG;
            _repli
        };
        _best set [2, 0];
        (format ["CHACAL|E|appui_feu|%1|placeur|1|position|%2|couverture|%3|temoin|%4|passes|%5|points|%6|dist_site|%7|gain_sol_site|%8|score|%9|azimut|%10",
            round (time * 100) / 100, _best, CHACAL_COUV, round (_temoin * 1000) / 1000, _passe, _np,
            round (_best distance2D _site), round ((getTerrainHeightASL _best) - _solSite),
            round (_sc * 100) / 100, round (_site getDir _best)]) call CHACAL_LOG;
        _best
    };
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

// ! LE SOCLE : quatre reparations d execution, sous toutes les tactiques ( document du 11/09 ).
// La moitie des echecs mesures sont des pannes d execution, pas des erreurs de tactique.
CHACAL_fnc_socleAssaut = {
    private _ass = (units CHACAL_gAssaut) select { alive _x };
    // S1 : chaque homme de l assaut porte une charge. Le porteur mort a un suivant.
    { if (!("DemoCharge_Remote_Mag" in (magazines _x))) then { _x addMagazine "DemoCharge_Remote_Mag" } } forEach _ass;
    // S4 : les porteurs ne combattent pas. Ce sont eux qui posent ; un porteur qui riposte est un porteur qui s arrete.
    if !(2 call CHACAL_fnc_sans) then {
        {
            private _r = _x getVariable ["chacal_role", ""];
            if (_r in ["DEMO_1", "DEMO_2", "MEDECIN"]) then {
                _x disableAI "AUTOCOMBAT"; _x setBehaviour "AWARE";
                _x setVariable ["lambs_danger_disableAI", true, true];
            };
        } forEach _ass;
    };
    // S3 : l appui est cloue. Feu libre, mais il ne quitte pas sa place.
    if (!isNull CHACAL_gAppui && { !(4 call CHACAL_fnc_sans) }) then {
        CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED";
        CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true];
        {
            if (alive _x) then {
                _x disableAI "PATH"; _x setUnitPos "MIDDLE";
                _x setVariable ["lambs_danger_disableAI", true, true];
                _x addEventHandler ["Fired", {
                    if (CHACAL_T_PREMIER_TIR_APPUI < 0) then { CHACAL_T_PREMIER_TIR_APPUI = time };
                }];
            };
        } forEach (units CHACAL_gAppui);
    };
    // S5 : reconnaissance par le feu. Un defenseur qui TIRE se trahit : on le revele a l appui. Ce n est pas un oracle.
    {
        if (alive _x && { !(8 call CHACAL_fnc_sans) }) then {
            _x addEventHandler ["Fired", {
                params ["_t"];
                if (!(_t in CHACAL_CONNUS)) then {
                    CHACAL_CONNUS pushBack _t;
                    { _x reveal [_t, 4] } forEach ((units CHACAL_gAppui) + (units CHACAL_gAssaut));
                    (format ["CHACAL|E|trahi_par_son_tir|%1|%2|connus|%3", round (time * 100) / 100,
                        (_t getVariable ["chacal_id", -1]), count CHACAL_CONNUS]) call CHACAL_LOG;
                };
            }];
        };
    } forEach CHACAL_EST_SITE;
    (format ["CHACAL|E|socle|%1|porteurs|%2|appui_cloue|%3|ablation|%4|sans_chien|%5|sans_porteurs|%6|sans_appui|%7|sans_revelation|%8",
        round (time * 100) / 100,
        count (_ass select { "DemoCharge_Remote_Mag" in (magazines _x) }),
        (if (isNull CHACAL_gAppui || { 4 call CHACAL_fnc_sans }) then {0} else {count (units CHACAL_gAppui)}),
        CHACAL_ABLATION,
        (if (1 call CHACAL_fnc_sans) then {1} else {0}), (if (2 call CHACAL_fnc_sans) then {1} else {0}),
        (if (4 call CHACAL_fnc_sans) then {1} else {0}), (if (8 call CHACAL_fnc_sans) then {1} else {0})]) call CHACAL_LOG;
};

// La cible que l appui doit prendre : le fusilier-mitrailleur d abord, puis le chef, puis le reste.
CHACAL_fnc_ciblePrio = {
    private _viv = (CHACAL_EST_SITE select { alive _x });
    if (count _viv == 0) exitWith { objNull };
    private _rang = {
        private _t = typeOf _x;
        if (_t find "_AR_" > -1) then { 0 } else { if (_t find "_TL_" > -1) then { 1 } else { 2 } };
    };
    private _tri = [_viv, [], _rang, "ASCEND"] call BIS_fnc_sortBy;
    _tri select 0
};

// ! LA TACTIQUE, cote APPUI. Elle ne bouge personne : elle designe, elle arrose, elle reitere.
// L IA cesse d engager une cible qui ne tombe pas au bout de ~60 s : tout ordre de feu se reitere.
CHACAL_fnc_tactiqueAppui = {
    private _t0 = time; private _derniere = objNull; private _tCible = 0; private _tSupp = -99;
    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } && { !isNull CHACAL_gAppui } } do {
        private _app = (units CHACAL_gAppui) select { alive _x };
        if (count _app == 0) exitWith {};
        private _viv = CHACAL_EST_SITE select { alive _x };
        if (CHACAL_TACTIQUE == 2) then {
            // T2 : une cible a la fois, 60 s au plus, le fusilier-mitrailleur d abord.
            if (isNull _derniere || { !alive _derniere } || { time - _tCible > 60 }) then {
                _derniere = call CHACAL_fnc_ciblePrio; _tCible = time;
                if (!isNull _derniere) then {
                    if (!CHACAL_FIN) then {
                        (format ["CHACAL|E|cible_designee|%1|%2|restants|%3", round (time * 100) / 100,
                            (_derniere getVariable ["chacal_id", -1]), count _viv]) call CHACAL_LOG;
                    };
                };
            };
            if (!isNull _derniere) then {
                { _x reveal [_derniere, 4]; _x doTarget _derniere; _x doFire _derniere } forEach _app;
            };
        } else {
            // T1 et T5 apres bascule : arroser la position du defenseur connu le plus proche de l assaut,
            // sauf si l assaut est a moins de 50 m de cette position ( on deplace alors le tir ).
            private _cn = CHACAL_CONNUS select { alive _x };
            if (count _cn == 0) then {
                // ! AUCUN DEFENSEUR LOCALISE : suppression DE ZONE sur l objectif, comme le prevoit la doctrine.
                // Sans elle, T1 attend un ennemi qui n a aucune raison de tirer le premier, et l assaut part sans appui.
                if (time - _tSupp > 30) then {
                    _tSupp = time; CHACAL_ZONES = CHACAL_ZONES + 1;
                    private _z = if (!isNull CHACAL_PC) then { getPosATL CHACAL_PC } else { CHACAL_SITE };
                    { _x doWatch _z; _x doSuppressiveFire _z } forEach _app;
                    (format ["CHACAL|E|suppression_de_zone|%1|vers|%2|n|%3", round (time * 100) / 100, str _z, CHACAL_ZONES]) call CHACAL_LOG;
                };
            };
            if (count _cn > 0) then {
                private _ca = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
                private _cible = objNull; private _dmax = -1;
                {
                    private _d = if (count _ca > 0) then { _x distance2D _ca } else { 999 };
                    if (_d > 50 && { _d > _dmax }) then { _dmax = _d; _cible = _x };
                } forEach _cn;
                if (!isNull _cible && { time - _tSupp > 30 }) then {
                    _tSupp = time;
                    { _x reveal [_cible, 4]; _x doTarget _cible; _x doFire _cible;
                      _x doSuppressiveFire (getPosATL _cible) } forEach _app;
                    if (!CHACAL_FIN) then {
                        (format ["CHACAL|E|suppression|%1|%2|distance_assaut|%3", round (time * 100) / 100,
                            (_cible getVariable ["chacal_id", -1]), round _dmax]) call CHACAL_LOG;
                    };
                };
            };
        };
        sleep 5;
    };
};

// ! LE CHIEN DE GARDE ( S4 ). Un assaut qui n avance plus recoit son ordre une seconde fois ; au deuxieme
// echec, un fumigene tombe entre lui et le defenseur connu le plus proche. « Tout ce qui fige un homme coute ».
CHACAL_fnc_chienDeGarde = {
    private _dRef = 1e9; private _tRef = time; private _rates = 0;
    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
        sleep 10;
        // ! LA PHASE A PU CHANGER PENDANT LE SOMMEIL ( 13/09 ). Sans ce test, le chien ordonnait AWARE
        // et un doMove VERS LE SITE a des hommes qui decrochaient : 8 episodes sur 15, entre 1 et 7 s
        // apres le debut de la phase 6. C est le bug corrige le 12/09 pour CHACAL_FIN, dans cette meme
        // boucle - la garde avait ete posee pour une variable et pas pour l autre.
        if (CHACAL_FIN || { CHACAL_PHASE != 5 }) exitWith {
            (format ["CHACAL|E|chien_de_garde|%1|phase_quittee|%2|relances|%3", round (time * 100) / 100,
                CHACAL_PHASE, CHACAL_RELANCES_SOCLE]) call CHACAL_LOG;
        };
        if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {
            private _v = (units CHACAL_gAssaut) select { alive _x };
            if (count _v > 0) then {
                private _c = _v call CHACAL_fnc_centre;
                private _d = _c distance2D CHACAL_CIBLE_ASSAUT;
                if (_d < _dRef - 5) then { _dRef = _d; _tRef = time; _rates = 0 }
                else {
                    if (time - _tRef > 30) then {
                        _tRef = time; _rates = _rates + 1; CHACAL_RELANCES_SOCLE = CHACAL_RELANCES_SOCLE + 1;
                        CHACAL_gAssaut setBehaviour "AWARE";
                        { if (alive _x) then { _x doMove CHACAL_CIBLE_ASSAUT } } forEach _v;
                            if (CHACAL_FIN) exitWith {};   // ! rien apres la ligne FINI : la porte de lecture refuse l episode
                        (format ["CHACAL|E|chien_de_garde|%1|relance|%2|reste|%3", round (time * 100) / 100,
                            _rates, round _d]) call CHACAL_LOG;
                        if (_rates >= 2) then {
                            private _cn = CHACAL_CONNUS select { alive _x };
                            private _vers = if (count _cn > 0) then { getPosATL (_cn select 0) } else { CHACAL_CIBLE_ASSAUT };
                            private _p = _c getPos [25, _c getDir _vers];
                            createVehicle ["SmokeShell", _p, [], 0, "CAN_COLLIDE"];
                            CHACAL_FUMIGENES = CHACAL_FUMIGENES + 1; _rates = 0;
                            (format ["CHACAL|E|fumigene|%1|entre|%2|et|%3", round (time * 100) / 100, str _p, str _vers]) call CHACAL_LOG;
                        };
                    };
                };
            };
        };
    };
};

// ! LE CONTROLE POSITIF DE L APPUI. Quatre mesures depuis le 10/09 ( feu avant, oracle, tournoi, ablation ) ont
// constate le meme appui inerte sous quatre noms : 0 coup sur 17 episodes du socle complet. Avant d empiler une
// cinquieme mesure, on certifie le mecanisme lui-meme, comme le veut la regle 16.
// L appui NE BOUGE PAS : il est mesure la ou la mission l a mis. Deux bras : cloue ( 1 ) et non cloue ( 2 ).
CHACAL_fnc_bancAppui = {
    private _app = (units CHACAL_gAppui) select { alive _x };
    private _def = CHACAL_EST_SITE select { alive _x };
    if (count _app == 0 || { count _def == 0 }) exitWith {
        (format ["CHACAL|E|banc_appui_fin|%1|coups|0|tireurs|%2|defenseurs|%3|cause|RIEN_A_MESURER",
            round (time * 100) / 100, count _app, count _def]) call CHACAL_LOG;
    };
    "CHACAL|AVERT|hors_corpus|banc_appui|episode_de_certification" call CHACAL_LOG;
    // l assaut et le bouchon ne jouent pas : on ne mesure QUE l appui
    {
        if (!isNull _x) then {
            _x setBehaviour "CARELESS"; _x setCombatMode "BLUE";
            { if (alive _x) then { doStop _x; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT"; _x setUnitPos "DOWN" } } forEach (units _x);
        };
    } forEach [CHACAL_gAssaut, CHACAL_gBouchon];
    // la cible : le defenseur le plus proche de l appui, et on mesure ce que chaque tireur VOIT vraiment
    private _c0 = _app call CHACAL_fnc_centre;
    private _tri = [_def, [_c0], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
    private _cible = _tri select 0;
    {
        private _u = _x;
        _u setDir (_u getDir _cible);
        _u setUnitPos "MIDDLE";
        if (CHACAL_BANC_APPUI == 1) then {
            _u disableAI "PATH";
            _u setVariable ["lambs_danger_disableAI", true, true];
        };
        { _u reveal [_x, 4] } forEach _def;
        _u addEventHandler ["Fired", { CHACAL_TIRS_BANC = CHACAL_TIRS_BANC + 1; (_this select 0) setVariable ["banc_tirs", ((_this select 0) getVariable ["banc_tirs", 0]) + 1] }];
        private _oeil = eyePos _u;
        private _vu = 0; private _occulteur = "";
        {
            private _r = lineIntersectsSurfaces [_oeil, aimPos _x, _u, _x, true, 1];
            if (count _r == 0) then { _vu = _vu + 1 } else {
                if (_occulteur == "") then { _occulteur = typeOf ((_r select 0) select 2) };
            };
        } forEach _def;
        (format ["CHACAL|E|banc_appui_poste|%1|%2|role|%3|distance_cible|%4|defenseurs_vus|%5|sur|%6|connait|%7|occulteur|%8|mode|%9|couverture|%10",
            round (time * 100) / 100, (_u getVariable ["chacal_id", -1]), (_u getVariable ["chacal_role", ""]),
            round (_u distance _cible), _vu, count _def, round ((_u knowsAbout _cible) * 100) / 100,
            (if (_occulteur == "") then {"aucun"} else {_occulteur}), (combatMode (group _u)), CHACAL_COUV]) call CHACAL_LOG;
    } forEach _app;
    CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED";
    if (CHACAL_BANC_APPUI == 1) then { CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true] };
    { if (alive _x) then { _x doWatch _cible; _x doTarget _cible; _x doFire _cible } } forEach _app;
    private _t0 = time; private _morts0 = { !alive _x } count CHACAL_EST_SITE;
    while { (time - _t0) < (300 * CHACAL_ECHELLE) && { !CHACAL_FIN } } do {
        sleep 10;
        private _viv = CHACAL_EST_SITE select { alive _x };
        private _a = (units CHACAL_gAppui) select { alive _x };
        if (count _viv == 0 || { count _a == 0 }) exitWith {};
        private _c = _viv select 0;
        { _x reveal [_c, 4]; _x doWatch _c; _x doTarget _c; _x doFire _c } forEach _a;
        // ! la vue est une SERIE, pas un instantane : les defenseurs bougent, et un poste aveugle a la pose peut
        // s ouvrir ensuite. On ecrit toutes les 10 s ce que chaque tireur atteint reellement.
        {
            private _u = _x; private _oe = eyePos _u;
            private _v = { count (lineIntersectsSurfaces [_oe, aimPos _x, _u, _x, true, 1]) == 0 } count _viv;
            (format ["CHACAL|E|banc_appui_vue|%1|%2|vus|%3|sur|%4|coups|%5|mode|%6", round (time * 100) / 100,
                (_u getVariable ["chacal_id", -1]), _v, count _viv, (_u getVariable ["banc_tirs", 0]),
                (combatMode (group _u))]) call CHACAL_LOG;
        } forEach _a;
    };
    private _detail = "";
    { _detail = _detail + format ["%1:%2 ", (_x getVariable ["chacal_role", ""]), (_x getVariable ["banc_tirs", 0])] } forEach _app;
    (format ["CHACAL|E|banc_appui_fin|%1|coups|%2|par_tireur|%3|defenseurs_tues|%4|duree|%5|appui_vivant|%6|cloue|%7",
        round (time * 100) / 100, CHACAL_TIRS_BANC, _detail,
        ({ !alive _x } count CHACAL_EST_SITE) - _morts0, round (time - _t0),
        count ((units CHACAL_gAppui) select { alive _x }), CHACAL_BANC_APPUI]) call CHACAL_LOG;
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
