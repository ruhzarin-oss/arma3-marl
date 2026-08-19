// ═══════════════════════════════════════════════════════════════════════════
//  SOCLE HARMATTAN — les bancs COMPOSENT, ils ne reecrivent plus.
//
//  Cause racine mesuree le 15/08 : sur 543 fichiers de banc, 185 refont l armement et
//  182 refont le pilotage. Chacun sa copie, donc chacun sa faute. L arme au sac a coute
//  TROIS fois la meme journee : reparee dans banc_appui.sqf le matin, non reportee dans
//  banc_live.py ni dans feu_force.sqf.
//    ⟨Fable⟩ « Une reparation dans un fichier n est pas une reparation — c est une
//             reparation dans UNE copie. »
//
//  Trois principes, aucun negociable :
//    1. Chaque brique DECLARE l etat qu elle pose.
//    2. Le prevol RELIT le monde et refuse de lancer si la relecture differe.
//    3. Chaque faute attrapee devient un test permanent du prevol — le CLIQUET.
// ═══════════════════════════════════════════════════════════════════════════

HMT_SOCLE_VERSION = "5.3.0-20082026";
HMT_LOG = { diag_log _this };

// ─────────────────────────────────────────────── BRIQUE 1 : LES GRANDEURS
// UNE seule definition, avec son unite. Les quatre versions de `dcover` meurent ici.

// pente : gradient central du relief, en METRES PAR CELLULE de 6,25 m, puis /5.
// ⛔ PAS `surfaceNormal` : borne a 0,40 quand le gymnase donne 0,589 de mediane.
HMT_G_SLOPE = {
    params ["_cx", "_cy"];
    private _gx = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
    private _gy = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
    (sqrt (_gx*_gx + _gy*_gy)) / 5
};
// ligne de vue : la vue que l IA emploie REELLEMENT, geometrie complete.
// ⛔ PAS `terrainIntersectASL` : relief SEUL, constant a 1 sur 170 m.
HMT_G_LOS = { params ["_a","_b"]; [objNull,"VIEW"] checkVisibility [eyePos _a, eyePos _b] };

// couvert : seuil LOCAL, 1,4 x le gradient moyen du carre de 64x64 cellules autour de
// l objectif — la moyenne est celle DE L ENVIRONNEMENT, comme terrain_gpu.py:47.
// ⛔ PAS une constante globale de carte : elle ne trouve rien sur un relief doux.
HMT_G_COVER_MOY = {
    params ["_o"];
    private _s = 0;
    for "_a" from -32 to 31 do { for "_b" from -32 to 31 do {
        _s = _s + 5 * ([(_o select 0) + _a*6.25, (_o select 1) + _b*6.25] call HMT_G_SLOPE);
    }};
    _s / 4096
};
// dcover : distance de Tchebychev EN CELLULES, sentinelle 16, recherche jusqu a 15.
HMT_G_DCOVER = {
    params ["_px","_py","_seuil"];
    private _d = 16; private _k = 0;
    while { _k <= 15 && _d >= 16 } do {
        private _f = false;
        for "_a" from -_k to _k do { for "_b" from -_k to _k do {
            if (!_f && {(abs _a == _k) || (abs _b == _k)}) then {
                if ((5 * ([_px + _a*6.25, _py + _b*6.25] call HMT_G_SLOPE)) > _seuil) then { _d = _k; _f = true };
            };
        }};
        _k = _k + 1;
    };
    _d
};

// ─────────────────────────────────────────────── BRIQUE 2 : L ARMEMENT
// Le socle POSSEDE l arme. Il la donne, la MET EN MAIN, et RELIT `currentWeapon`.
HMT_ARMER = {
    params ["_u"];
    if ((primaryWeapon _u) isEqualTo "") then { _u addWeapon "arifle_MX_F"; _u addMagazines ["30Rnd_65x39_caseless_mag", 8] };
    _u selectWeapon (primaryWeapon _u);
    _u setUnitPos "UP";
    _u setVariable ["hmt_arme_declaree", true, true];
    ((currentWeapon _u) != "")                    // RELECTURE : l arme est-elle EN MAIN ?
};

// ─────────────────────────── BRIQUE 9 : L ACTE DE MARCHE DU SERVI, UN SEUL CODE
// ⚠️ MEME FAUTE QUE LE TIR, SUR L AUTRE CANAL. Le 19/08, la porte a rendu ZERO echec T7 sur
// 58 tirages une fois l acte de tir unifie — et QUATRE faux-recus T5. L acte 2 du placeur et
// T5 sont restes DEUX CODES : l un pose son homme par `createUnit` en mode « statue » avec
// `PATH` rendu, l autre par `HMT_POSER_HOMME` en mode « temoin ». Exactement la configuration
// qui avait produit la divergence du tir, et qu on a mis trois jours a nommer.
// Un acte, un code : meme pose, meme mode, meme telemetrie des deux cotes ⟨Fable⟩.
HMT_ACTE_MARCHE_SERVI = {
    params ["_pos", ["_duree", 4], ["_vy", 6]];
    private _g = createGroup west;
    private _u = [_g, "B_Soldier_F", [_pos select 0, _pos select 1, 0], "pilote"] call HMT_POSER_HOMME;
    if (isNull _u) exitWith { deleteGroup _g; [-1, 0, -1, "naissance refusee"] };
    _u allowDamage false;
    _u setDir 0;
    sleep 1.5;
    private _p0 = getPosATL _u;
    private _mnt = [_u, _duree, _vy] call HMT_MARCHER;
    private _derive = round (10 * (_p0 distance2D (getPosATL _u))) / 10;
    private _r = [_mnt select 0, _mnt select 1, _mnt select 2, _mnt select 3];
    deleteVehicle _u; deleteGroup _g;
    _r                                    // [metres, iterations, vitesse relue, animation]
};

// ─────────────────────────────── BRIQUE 8 : L ACTE DE TIR DU SERVI, UN SEUL CODE
// ⚠️ DEUX COPIES MANUELLES DU MEME ACTE ONT DIVERGE, ET LA SONDE N A PAS PU LES DEPARTAGER.
// Point (4629, 5856), lot 5 du 18/08 : l acte 3 du placeur RECOIT 5 fois sur 5 quand T7 rend
// 0 coup 5 fois sur 5. Trente tirages de sonde — repliques de l acte 3, de T7, et de l acte 3
// sans `PATH` — rendent TOUS zero, vue nulle : `PATH` du mannequin ecarte, naissance du
// tireur ecartee. Ma replique n est donc pas le vrai acte 3, et aucune sonde ne le dira :
// tant que ce sont DEUX CODES, la difference peut se loger n importe ou.
// La sortie n est pas une sonde de plus, c est UN ACTE, UN CODE ⟨Fable, 18/08⟩ — appele par
// l acte 3 du placeur ET par T7, avec la MEME pose du mannequin, la MEME pose du tireur, et
// LA MEME TELEMETRIE DE VUE DES DEUX COTES. L acte 3 n en avait aucune : c est ce qui a laisse
// la divergence vivre.
HMT_ACTE_TIR_SERVI = {
    params ["_pos", ["_duree", 4]];
    private _px = _pos select 0; private _py = _pos select 1;
    private _gE = createGroup east;
    private _mm = _gE createUnit ["O_Soldier_F", [_px, _py + 40, 0], [], 0, "NONE"];
    [_mm] call HMT_ARMER;
    _mm allowDamage false; _mm disableAI "AUTOCOMBAT"; _mm disableAI "FSM";
    _mm disableAI "PATH"; _mm setBehaviour "CARELESS";
    private _gW = createGroup west;
    private _u = [_gW, "B_Soldier_F", [_px, _py, 0], "pilote"] call HMT_POSER_HOMME;
    _u allowDamage false;
    sleep 1.5;
    // ⚠️ LE SABOTAGE DU TIR VIT DESORMAIS DANS LA BRIQUE — DEUXIEME FOIS QU UN REFACTORING
    // L AVALAIT. Le bloc B1 l avait deja emporte avec le `reveal` et la telemetrie ; il
    // vivait dans le bloc que la fonction remplacait. Ici il profite AUX DEUX appelants
    // (acte 3 du placeur ET T7) au lieu d un seul — c est ce que « composer » doit donner.
    // ⚠️ Et c est le DIFF qui l a attrape, pas le smoke : un sabotage absent ne fait rien
    // ECHOUER, il rend seulement un controle positif silencieusement vide.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "tir") then { _u setVehicleAmmo 0 };
    _u reveal [_mm, 4];
    private _vue = round (100 * ([objNull, "VIEW"] checkVisibility [eyePos _u, eyePos _mm])) / 100;
    private _c = [_u, _mm, _duree] call HMT_TIRER_C9;
    private _dm = round (_u distance _mm);
    deleteVehicle _mm; deleteVehicle _u; deleteGroup _gE; deleteGroup _gW;
    [_c, _vue, _dm]                              // [coups, vue, distance]
};

// ─────────────────────────────────── BRIQUE 7 : LES POSITIONS DE LA SCENE, CERTIFIEES AVANT
// ⚠️ LA SCENE NE TESTAIT RIEN — zero test compte dans `SCENE` (`banc_live.py`). Les huit
// hommes de chaque episode naissaient au PUR HASARD autour de l objectif (`random 360`,
// rayon `10 + random 25`), sans eau, sans hauteur, sans vue, sans praticabilite. Ce n est pas
// mal choisir, c est NE PAS CHOISIR ⟨lecture du 17/08⟩.
//
// ⚠️ ET LE PREVOL NE LES TESTAIT PAS NON PLUS : T5 et T7 eprouvent un TEMOIN pose a 250-370 m
// de la scene. Le placeur v2 garantit un bon lieu POUR LE TEMOIN, et rien pour ceux qui jouent.
//
// ⚠️ POURQUOI *AVANT* LA SCENE, ET EN PARALLELE ⟨plan de Fable⟩ :
//   · le placeur v2 en serie sur 12 positions x 2 actes serait long ;
//   · un test « leger » sur l ETAT est exclu — `path:true` a menti toute la semaine ;
//   · et certifier DANS la scene vivante la CORROMPT : un homme qui tire renseigne le camp
//     adverse, et `knowsAbout` est de CAMP et non de soldat.
//   Avant la scene, personne n existe : rien a corrompre, personne a alerter. Une seule
//   fenetre de traverse pour tous, une seule de tir. Cout ~15 s par episode.
// ─────────────────────────────────────────────────────────────────────────────
// ⛔ DESACTIVE PAR DRAPEAU LE 19/08/2026 — ET LE MOTIF EST UNE MESURE, PAS UNE GENE.
// Son critere (23 m parcourus en 4 s) vient d etre mesure INFRANCHISSABLE EN MONTEE :
// sur 188 actes, ZERO acte finissant au sol n atteint 23 m ; en descente, 101 sur 111
// le franchissent. Le critere ne mesure donc pas la praticabilite mais « ca descend
// vers le nord » — la direction de marche etant CABLEE (`[0, 6, 0]`).
// Actif, il rejette LE MONDE : 37 positions jugees le 19/08 a 19h25 -> 32 « encombre »,
// 5 « muet », ZERO recue, sur SIX essais d azimut a 0/4.
// Voir VERDICT_LA_PENTE_DANS_LE_SENS_DE_LA_MARCHE.md.
// ⚠️ IL SE RALLUME AVEC LE CRITERE NEUF, PAS AVANT — et le critere neuf attend
// l arbitrage de Younes sur le tempo du gymnase (le canal rend 2,8-3,7 m/s en montee
// contre 6 m/s supposes). AUCUNE PORTE NE SE LANCE AVANT : le placeur partage ce
// critere, donc une porte lancee aujourd hui re-selectionnerait des descentes en silence.
// ⚠️ LE BANC DECLARE SON CANAL, comme la couture. La porte comparera les deux.
HMT_CANAL = "sv_vz_preserve_10hz";
HMT_CERTIFIER = false;
HMT_CERTIFIER_POSITIONS = {
    params ["_positions", ["_duree", 4], ["_seuil", 23]];
    if (!HMT_CERTIFIER) exitWith {
        ("HMT|SOCLE|BLOC_C|DESACTIVE|drapeau HMT_CERTIFIER=false|positions|"
         + str (count _positions)) call HMT_LOG;
        _positions apply { ["non certifie", -1, -1, -1] }
    };
    private _gW = createGroup west; private _gE = createGroup east;
    private _hs = []; private _ms = [];
    {
        private _u = _gW createUnit ["B_Soldier_F", [_x select 0, _x select 1, 0], [], 0, "NONE"];
        // tout homme jetable est invulnerable ET neutre, uniformement
        _u allowDamage false; _u setCaptive true;
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u setBehaviour "CARELESS";
        _u enableAI "PATH"; [_u] call HMT_ARMER;
        private _m = _gE createUnit ["O_Soldier_F", [_x select 0, (_x select 1) + 40, 0], [], 0, "NONE"];
        // meme faute evitee ici : la cible n est PAS `setCaptive`, sinon nul ne lui tire dessus
        _m allowDamage false;
        _m disableAI "AUTOCOMBAT"; _m disableAI "FSM"; _m setBehaviour "CARELESS";
        [_m] call HMT_ARMER;
        _hs pushBack _u; _ms pushBack _m;
    } forEach _positions;
    sleep 2;
    // ── ACTE 1 · TRAVERSE, TOUS EN MEME TEMPS, UNE SEULE FENETRE
    private _p0 = _hs apply { getPosATL _x };
    private _t0 = time;
    while { time - _t0 < _duree } do { { _x setVelocity [0, 6, (velocity _x) select 2] } forEach _hs; sleep 0.1 };
    private _met = [];
    { _met pushBack (round ((_p0 select _forEachIndex) distance2D (getPosATL _x))) } forEach _hs;
    // ── ACTE 2 · TIR, TOUS EN MEME TEMPS. On remet chacun a sa position d origine d abord.
    { _x setPosATL (_p0 select _forEachIndex) } forEach _hs;
    sleep 1;
    HMT_CP_COUPS = []; { HMT_CP_COUPS pushBack 0 } forEach _hs;
    private _ehs = [];
    {
        private _i = _forEachIndex;
        _ehs pushBack (_x addEventHandler ["Fired", {
            HMT_CP_COUPS set [(HMT_CP_I), (HMT_CP_COUPS select HMT_CP_I) + 1];
        }]);
    } forEach _hs;
    private _t1 = time;
    while { time - _t1 < _duree } do {
        {
            HMT_CP_I = _forEachIndex;
            _x setDir (_x getDir (_ms select _forEachIndex));
            _x doWatch (_ms select _forEachIndex);
            _x forceWeaponFire [currentWeapon _x, currentMuzzle _x];
        } forEach _hs;
        sleep 0.33;
    };
    { _x removeEventHandler ["Fired", _ehs select _forEachIndex] } forEach _hs;
    private _coups = +HMT_CP_COUPS;
    { deleteVehicle _x } forEach _hs; { deleteVehicle _x } forEach _ms;
    deleteGroup _gW; deleteGroup _gE;
    // ── verdicts, un par position
    private _v = [];
    {
        private _i = _forEachIndex;
        _v pushBack [(if ((_met select _i) >= _seuil && (_coups select _i) >= 1) then {"recu"}
                      else { if ((_met select _i) < _seuil) then {"encombre"} else {"muet"} }),
                     _met select _i, _coups select _i];
        (format ["HMT|SOCLE|SCENE_POS|i|%1|x|%2|y|%3|verdict|%4|metres|%5|coups|%6",
                 _i, round (_x select 0), round (_x select 1),
                 (_v select _i) select 0, _met select _i, _coups select _i]) call HMT_LOG;
    } forEach _positions;
    _v
};

// ─────────────────────────────────────────────────────────────────────────────
// LA SONDE DES HUIT AZIMUTS — dérivation du critère neuf du placeur ⟨19/08⟩
//
// L ancien critere marchait TOUJOURS VERS LE NORD : il mesurait donc la pente dans un
// azimut cable, et non la praticabilite. Le critere neuf echantillonne LES HUIT AZIMUTS
// DE LA COUTURE (`_a*45` dans ACT_TPL) — l espace d action exact de la politique — et
// retient le MINIMUM, qui est la statistique du mode d echec : l homme coince.
//
// ⚠️ TOUS LES LIEUX EN PARALLELE, UN AZIMUT A LA FOIS. Huit fenetres de 4 s au lieu de
// huit fois N gestes : le cout ne depend pas du nombre de lieux. C est la lecon du bloc C.
// ⚠️ Chaque homme est REMIS a sa position d origine entre deux azimuts, sinon le second
// azimut mesurerait depuis la ou le premier l a laisse.
HMT_SONDER_AZIMUTS = {
    // ⚠️ `_stop` : le verdict du CANAL est « max >= plancher », donc il est ACQUIS des
    // qu un azimut y arrive — inutile de jouer les sept autres. Un canal sain coute
    // alors 1 a 2 fenetres au lieu de 8 (mediane par azimut ~17 m, plancher 15,2),
    // et seul un canal MORT paie les 8. Sans cet arret, T5 passait de 4 s a 44 s et
    // la porte de 60 tirages gagnait 40 minutes de silence.
    // ⚠️ LE VERDICT EST INCHANGE : on ne change que le moment ou l on cesse de mesurer.
    // Le CHAMP des 8 distances est donc partiel quand on s arrete — le journal dit
    // combien d azimuts ont ete joues, et le releve complet reste disponible en
    // passant `_stop` a false (c est ce que font les sondes de derivation).
    params ["_positions", ["_duree", 4], ["_spd", 6], ["_sab", ""], ["_stop", false]];
    private _g = createGroup west;
    private _hs = [];
    {
        private _u = _g createUnit ["B_Soldier_F", [_x select 0, _x select 1, 0], [], 0, "NONE"];
        _u allowDamage false; _u setCaptive true;
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u setBehaviour "CARELESS";
        [_u] call HMT_ARMER;
        _hs pushBack _u;
    } forEach _positions;
    sleep 2;
    private _res = []; { _res pushBack [] } forEach _positions;
    // ⚠️ `while` ET NON `for ... exitWith` : mesure du 20/08 — `exitWith` dans une
    // boucle `for` sort de LA FONCTION, pas de la boucle. La brique ne retournait
    // alors plus rien (`_r select 0` rendait `bool`, `max` rendait `<null>`), et
    // l arret anticipe fonctionnait tout en cassant la valeur de retour. Le drapeau
    // dans la condition de boucle ne laisse aucune ambiguite.
    private _a = -1; private _fini = false;
    while { _a < 7 && !_fini } do {
        _a = _a + 1;
        private _h = _a * 45;
        private _vx = _spd * sin _h; private _vy = _spd * cos _h;
        if (_sab == "jambes") then { _vx = 0; _vy = 0 };   // ⚠️ CONTROLE : doit tout refuser
        {
            private _p = _positions select _forEachIndex;
            _x setPosATL [_p select 0, _p select 1, 0];
        } forEach _hs;
        sleep 1.5;
        private _p0 = _hs apply { getPosATL _x };
        private _t0 = time;
        while { time - _t0 < _duree } do {
            // ⚠️ LE CANAL ADOPTE : la verticale est PRESERVEE (socle 4.0.0)
            { _x setVelocity [_vx, _vy, (velocity _x) select 2] } forEach _hs;
            sleep 0.1;
        };
        {
            (_res select _forEachIndex) pushBack
                (round (10 * ((_p0 select _forEachIndex) distance2D (getPosATL _x))) / 10);
        } forEach _hs;
        // ⚠️ `exitWith` SORT DU BLOC OU IL EST ECRIT. Place dans un `then {}` il aurait
        // quitte le `then`, pas la boucle — la sortie anticipee n aurait rien coupe et
        // le cout serait reste de 8 fenetres, en silence. Le drapeau se calcule dans le
        // `then`, la sortie se fait AU NIVEAU DE LA BOUCLE.
        if (_stop) then {
            private _tous = true;
            { if (((_res select _forEachIndex) select { _x >= HMT_CANAL_PLANCHER }) isEqualTo []) then { _tous = false } } forEach _hs;
            _fini = _tous;
        };
        (format ["HMT|AZ|FENETRE|az|%1|fps|%2", _h, round diag_fps]) call HMT_LOG;
    };
    {
        private _r = _res select _forEachIndex;
        private _t = +_r; _t sort true;
        // ⚠️ INDICES DYNAMIQUES. Avec l arret anticipe, la liste fait 1 a 8 elements :
        // `select 7` sortait des bornes et faisait AVORTER la fonction en silence
        // (le retour devenait nil, `vivant` s imprimait `bool` et `max` `<null>`).
        // Une longueur qui change oblige a re-deriver TOUT ce qui en depend.
        (format ["HMT|AZ|LIEU|i|%1|x|%2|y|%3|min|%4|med|%5|max|%6|eau|%7|d|%8",
                 _forEachIndex, round (_x select 0), round (_x select 1),
                 _t select 0, _t select ((count _t) / 2), _t select ((count _t) - 1),
                 surfaceIsWater [_x select 0, _x select 1], _r]) call HMT_LOG;
    } forEach _positions;
    { deleteVehicle _x } forEach _hs;
    deleteGroup _g;
    ("HMT|AZ|FINI|sab|" + _sab + "|n|" + str (count _positions)) call HMT_LOG;
    _res                                  // une liste de 8 distances par position
};


// ─────────────────────────── BRIQUE 10 : LE CANAL EST-IL VIVANT DANS CETTE SESSION ?
// ⚠️ CE CRITERE REMPLACE T5 ET L ACTE DE TRAVERSE DU PLACEUR. Il ne certifie PAS un lieu :
// la grandeur « ce lieu est praticable » N EXISTE PAS de facon stable — mesure le 19/08,
// r = 0,771 entre deux passages identiques, plafond r2 ~ 0,59. Cinq derivations s y sont
// cassees. Le prevol ne demandait pas ca : il demande si LES JAMBES REPONDENT.
//
// ⚠️ LA STATISTIQUE EST LE MAXIMUM, PAS LE MINIMUM — et c est le retournement du dossier.
// Le minimum certifiait un LIEU, donc il heritait du scintillement (un blocage sur trois
// change d avis entre deux passages). La panne du CANAL est GLOBALE : jambes coupees =
// 0 m dans TOUS les azimuts. Le maximum absorbe donc le scintillement.
//
// DERIVE puis VALIDE SUR TIRAGE FRAIS (graine 23, pre-inscription ce5e3a0) :
//   sain    n=60  min 17,4  med 22,4     sabote  n=60  max 8,7
//   0/60 faux-rouge, 0/60 faux-vert, 0/60 desaccord entre deux passages.
//   Regle de trois : chaque taux d erreur borne a <= 5 %.
//
// ⚠️ RESERVE ECRITE : « max >= plancher » prouve que LES IMPULSIONS ARRIVENT, pas que
// l homme marche AU SOL. Un azimut parcouru en vol compte comme preuve de vie du canal.
// C est correct pour cette question ; ne pas le lire autrement.
HMT_CANAL_PLANCHER = 15.2;
HMT_CANAL_VIVANT = {
    params ["_pos", ["_sab", ""]];
    private _r = [[[_pos select 0, _pos select 1]], 4, 6, _sab, true] call HMT_SONDER_AZIMUTS;
    private _d = _r select 0;
    private _t = +_d; _t sort true;
    // ⚠️ INDICES DYNAMIQUES. Avec l arret anticipe, la liste fait 1 a 8 elements :
    // `select 7` sortait des bornes et faisait AVORTER la fonction en silence
    // (le retour devenait nil, `vivant` s imprimait `bool` et `max` `<null>`).
    // Une longueur qui change oblige a re-deriver TOUT ce qui en depend.
    private _max = _t select ((count _t) - 1);
        // ⚠️ LE CHAMP S APPELLE `max_joues` ET NON `max` : avec l arret anticipe la liste
    // ne contient QUE les azimuts joues, donc ce nombre est le maximum SUR CE QUI A
    // ETE MESURE, pas sur les huit. Le VERDICT est identique (des qu un azimut passe
    // le plancher, le max des huit le passe aussi), mais un journal qui appelle « max »
    // un maximum partiel finira par etre lu de travers. Une ligne de journal est un
    // instrument : elle nomme ce qu elle contient.
    (format ["HMT|SOCLE|CANAL|x|%1|y|%2|max_joues|%3|med_joues|%4|min_joues|%5|plancher|%6|vivant|%7|azimuts|%8|d|%9",
             round (_pos select 0), round (_pos select 1),
             _max, _t select ((count _t) / 2), _t select 0, HMT_CANAL_PLANCHER,
             _max >= HMT_CANAL_PLANCHER, count _d, _d]) call HMT_LOG;
    (format ["HMT|SOCLE|CANAL_COUT|azimuts_joues|%1|sur|8", count _d]) call HMT_LOG;
    [_max >= HMT_CANAL_PLANCHER, _max, _d]
};

// ─────────────────────────────────────────────── BRIQUE 6 : LES DEUX GESTES, UNE SEULE FOIS
// ⚠️ « LES BANCS COMPOSENT AU LIEU DE REECRIRE » — et ce fichier portait TROIS copies de la
// boucle de marche (acte 2, T5, et `arma_couture.py:ACT_TPL`) et DEUX du tir force (acte 3,
// T7, plus la couture) ⟨lecture de Fable, 17/08⟩. Elles avaient DEJA diverge : 4 s contre
// 3,28 s, arret au premier coup ici et duree pleine la, jeton present ou absent, telemetrie
// ou pas. Chaque divergence est un ecart que personne ne mesure entre le certificateur et le
// certifie.
//
// ⚠️ CHOIX DE FIDELITE : `HMT_TIRER_C9` tire PENDANT TOUTE LA DUREE et ne s arrete pas au
// premier coup. L acte 3 s arretait au premier — c est une economie qui change le test, et
// l action 9 de la couture, elle, tire sans s arreter. On paie les 4 s ⟨regle 6⟩.

HMT_MARCHER = {
    // ⚠️ LA TELEMETRIE DU GESTE VIT ICI, PAS CHEZ UN SEUL APPELANT. Le refactoring B1 l avait
    // AVALEE avec le reste de la boucle de T5 : la vitesse relue et l animation, celles-la
    // meme qui ont refute trois hypotheses le 16/08 (l impulsion est appliquee, l IA ne la
    // fait pas retomber, la posture reste debout). En la remontant dans la brique, elle
    // profite desormais a l acte 2 du placeur autant qu a T5 — c est ce que « composer »
    // devait donner des le depart.
    params ["_u", "_duree", ["_vy", 6]];
    private _p0 = getPosATL _u; private _t0 = time; private _nt = 0;
    private _vrelue = []; private _anims = [];
    while { alive _u && time - _t0 < _duree } do {
                // ⚠️ CANAL AVEC GRAVITE — ADOPTE LE 19/08/2026 SUR DECISION DE YOUNES (branche 1),
        // APRES mesure appariee (12 lieux x 2 canaux, meme passage, n=28) : le vol est aboli,
        // la hauteur en descente passe de 6,8 m a 0,4 m, et la montee ne bouge pas (P3), ce
        // qui confirme que le controleur d animation y mangeait deja la verticale.
        // Voir PREDICTIONS_CANAL_GRAVITE.md (ecrites AVANT) et RESULTAT_CANAL_GRAVITE.md.
        // ⚠️ LE ZERO EN Z ETAIT LA CAUSE DU VOL : reemis a 10 Hz, il annulait la gravite
        // accumulee, donc un homme lance par une descente ne redescendait plus.
        _u setVelocity [0, _vy, (velocity _u) select 2]; _nt = _nt + 1;
        _vrelue pushBack (round (10 * ((velocity _u) select 1)) / 10);
        _anims pushBack (animationState _u);
        sleep 0.1;
    };
    private _vmed = if (count _vrelue > 0) then { _vrelue select (round ((count _vrelue) / 2)) } else { -1 };
    [_p0 distance2D (getPosATL _u), _nt, _vmed,
     (if (count _anims > 0) then { _anims select ((count _anims) - 1) } else { "" })]
};

HMT_TIRER_C9 = {
    params ["_u", "_cible", "_duree"];
    HMT_C9_COUPS = 0;
    private _eh = _u addEventHandler ["Fired", { HMT_C9_COUPS = HMT_C9_COUPS + 1 }];
    private _t0 = time;
    while { alive _u && time - _t0 < _duree } do {
        _u setDir (_u getDir _cible); _u doWatch _cible;
        _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
        sleep 0.33;
    };
    _u removeEventHandler ["Fired", _eh];
    HMT_C9_COUPS
};

// ─────────────────────────────────────────────── BRIQUE 5 : LE LIEU SE JUGE A L ACTE
// ⚠️ NEE DU VERDICT DU 17/08 (`VERDICT_LIEU_EST_LA_CAUSE.md`). L ancien placeur retenait le
// point de PENTE MOYENNE MINIMALE sur un carre de 60 m. Mesure : 18 echecs sur 18 aux trois
// lieux qu il avait retenus, contre 3 sur 12 a deux autres — et la pente NE SEPARE PAS
// (session 8 a 0,01, parfaitement plate, morte 5 fois sur 6). Ce qui bloque un homme est
// l ENCOMBREMENT, invisible pour une pente moyennee.
//
// ⚠️ ET IL OPTIMISAIT. Un placeur qui choisit « le meilleur » fabrique un monde biaise vers
// le facile ⟨Fable⟩. Le v2 tire les candidats en ordre ALEATOIRE et RECOIT LE PREMIER qui
// passe. Le pre-filtre bon marche (eau, hauteur, vue) sert a ORDONNER et a rejeter vite —
// il ne RECOIT jamais : `path:true` figurait dans toutes les signatures d echec du 16-17/08
// pendant que l homme restait cloue. L etat du moteur a menti toute la semaine ; seul l ACTE
// recoit.
HMT_G_PRATICABLE = {
    params ["_c"];
    private _x = _c select 0; private _y = _c select 1;
    // ── rejets bon marche, qui n autorisent RIEN et ne font qu economiser l acte
    if (surfaceIsWater [_x, _y]) exitWith { ["eau", 0, 0] };
    if ((getTerrainHeightASL [_x, _y]) <= 3) exitWith { ["bord de mer", 0, 0] };
    // ── ACTE 1 · VOIT-ON A 40 m ? (la distance ou T4 pose son mannequin)
    private _z = (getTerrainHeightASL [_x, _y]) + 1.5;
    private _vue = 0;
    for "_i" from 0 to 5 do {
        private _a = _i * 60;
        private _dx = _x + 40 * sin _a; private _dy = _y + 40 * cos _a;
        private _v = [objNull, "VIEW"] checkVisibility
            [[_x, _y, _z], [_dx, _dy, (getTerrainHeightASL [_dx, _dy]) + 1.5]];
        if (_v > _vue) then { _vue = _v };
    };
    if (_vue < 0.5) exitWith { ["sans vue", 0, _vue] };
    // ⛔ L ACTE 2 (TRAVERSE >= 23 m) EST RETIRE LE 20/08 — ET C EST LUI, LE SELECTEUR.
    // Mesure du 19/08 : son seuil n etait franchissable QU EN DESCENTE (0 acte sur 188
    // finissant au sol l atteint, 101 sur 111 finissant en l air le franchissent), et
    // INVERSER LA DIRECTION DE MARCHE INVERSE LE REGIME (3/3 et 3/3, bras sud). La marche
    // etant cablee vers le nord, ce critere disait « ca descend vers le nord » — une
    // boussole deguisee en test de terrain. C est ce selecteur qui a fabrique le « 104 % ».
    // ⚠️ ET IL NE SE REMPLACE PAS PAR UN AUTRE SEUIL : la grandeur « ce lieu est praticable »
    // n existe pas de facon stable (r = 0,771 entre deux passages). Cinq derivations
    // pre-enregistrees s y sont cassees, chacune arretee sur son propre falsificateur.
    // Le placeur cesse donc de TRIER sur la marche. Il garde ses rejets d ORDRE (eau,
    // hauteur) et son ACTE DE TIR, qui sont des actes BINAIRES — la porte y reste juste.
    // La vie du canal se juge desormais par HMT_CANAL_VIVANT, sur les 8 azimuts, au MAX.
    // Voir CRITERE_CANAL_VIVANT_VALIDE.md.

    // ── ACTE 3 · UN HOMME DANS LE MODE *SERVI* TIRE-T-IL DEPUIS CE LIEU ?
    // ⚠️ MEME CODE QUE T7 depuis le 19/08 : `HMT_ACTE_TIR_SERVI`. Les deux copies manuelles
    // avaient diverge sans que rien ne le dise, faute de telemetrie de vue de ce cote.
    private _r3 = [[_x, _y], 4] call HMT_ACTE_TIR_SERVI;
    private _coups = _r3 select 0;
    (format ["HMT|SOCLE|ACTE3|x|%1|y|%2|coups|%3|vue|%4|dist|%5",
             round _x, round _y, _coups, _r3 select 1, _r3 select 2]) call HMT_LOG;
    [(if (_coups >= 1) then {"recu"} else {"muet"}), round _m, _vue, _coups]
};

// ─────────────────────────────────────────────── BRIQUE 3 : LE PILOTAGE
// Le socle POSSEDE l etat `disableAI`. Un banc ne le pose JAMAIS a la main.
// Trois modes, et un seul est autorise par homme.
//   "natif"   : l IA joue entiere. AUCUN disableAI.
//   "pilote"  : la politique decide, Arma execute. AUTOCOMBAT + FSM coupes, PATH GARDE.
//   "statue"  : l homme ne bouge pas et ne choisit pas. PATH + FSM + AUTOCOMBAT coupes.
// ⛔ `disableAI "PATH"` en mode pilote retire les JAMBES : 9 m au lieu de 48, mesure du 11/08.
HMT_PILOTER = {
    params ["_u", "_mode"];
    _u enableAI "ALL";
    switch (_mode) do {
        case "natif":  { _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0 };
        // ⚠️ `RED`, PAS `BLUE`. `combatMode "BLUE"` signifie « NE JAMAIS TIRER » dans le
        // moteur. Les attaquants du banc live l ont porte pendant 67 episodes : ZERO balle.
        // Mesure du 15/08 : memes deux `disableAI`, BLUE = 0 coup, RED = 145, et la
        // progression est IDENTIQUE (154 m) — la politique garde tout son deplacement.
        // ⚠️ ET J AI EXTRAIT CE SOCLE DES BANCS FAUTIFS SANS LE QUESTIONNER : la v1.0.0
        // portait la faute. C est precisement ce que le cliquet doit rendre impossible.
        case "pilote": { _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
                         _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0 };
        case "statue": { _u disableAI "PATH"; _u disableAI "FSM"; _u disableAI "AUTOCOMBAT";
                         _u setBehaviour "COMBAT"; _u setCombatMode "RED" };
        // ⚠️ LE TEMOIN DU PREVOL GARDE `AUTOCOMBAT`. Sonde du 16/08, trois bras : le tir suit
        // `AUTOCOMBAT` et rien d autre — temoin sans (0 coup), attaquant avec (13), temoin
        // pose AU LIEU MEME de la scene et toujours sans (0). Un temoin qui ne peut pas tirer
        // ne peut pas PROUVER qu une balle part, donc il bloquait tout le banc.
        // ⚠️ ANOMALIE OUVERTE : la scene appelle `disableAI "AUTOCOMBAT"` sur ses attaquants
        // et ils l ont pourtant ACTIF. L ordre ne prend pas, et on ne sait pas pourquoi.
        // Voir ANOMALIE_AUTOCOMBAT.md — a mesurer, pas a deviner.
        case "temoin": { _u disableAI "FSM";
                         _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowFleeing 0 };
        default { diag_log format ["HMT|SOCLE|ERREUR|mode inconnu %1", _mode] };
    };
    _u setVariable ["hmt_mode", _mode, true];
    _mode
};

// ─────────────────────────────────────────────── BRIQUE 4 : LA SCENE
HMT_POSER_HOMME = {
    params ["_grp", "_type", "_pos", "_mode"];
    private _u = _grp createUnit [_type, _pos, [], 0, "NONE"];
    _u setPosATL _pos; _u setSkill 0.5;
    [_u] call HMT_ARMER;
    [_u, _mode] call HMT_PILOTER;
    _u
};

// ═══════════════════════════════════════════════════════════════════════════
//  LE PREVOL — il RELIT le monde. Pas de prevol vert, pas d episode.
//  Chaque test porte le nom de la faute qui l a fait naitre.
// ═══════════════════════════════════════════════════════════════════════════
// ⚠️ LE BATTEMENT DE COEUR ⟨lecture de Fable⟩. Un prevol qui ne repond pas est aujourd hui
// indistinctement : le pont mort, le prevol LENT, ou le prevol PLANTE. Un instrument qui perd
// 17 % de sa mesure sans savoir lequel des trois n est pas certifiable. `HMT_PV_ETAPE` est
// pose a chaque phase ; python lit l etape et sait ou ca s est arrete.
HMT_PV_ETAPE = "neant";
HMT_PREVOL = {
    // ⚠️ LE JETON DE GENERATION ⟨lecture de Fable, 17/08⟩. `prevol.py` attendait sous un
    // plafond GLOBAL (40 x 1,9 s) un prevol de duree VARIABLE (~30 s fixes + ~5,5 s par
    // candidat atteignant l acte 2, plus les duels). Au depassement, python enchainait
    // PENDANT QUE LE SPAWN TOURNAIT ENCORE : deux `HMT_PREVOL` simultanes ecrivaient alors
    // dans les memes globales (`HMT_PV`, `HMT_PL_COUPS`, `HMT_PV_COUPS`). La revue avait
    // corrige la LECTURE (marqueur numerote) et pas la SUPERPOSITION.
    // La couture a resolu cette classe exacte avec `HMT_NORDRE` (`arma_couture.py:175`) ;
    // le prevol ne l avait jamais adopte. Un prevol dont la generation a ete depassee
    // s ARRETE au lieu d ecrire par-dessus son successeur.
    HMT_PV_GEN = (missionNamespace getVariable ["HMT_PV_GEN", 0]) + 1;
    private _gen = HMT_PV_GEN;
    HMT_PV_ETAPE = "depart"; HMT_PV_T0 = time;
    params ["_hommes"];
    private _ec = [];

    // ── RELECTURE D ETAT : ce que j ai pose est-il vraiment pose ? ──
    // T1 · arme au sac (3 occurrences le 15/08 : banc_appui, banc_live, feu_force)
    private _sac = _hommes select { (currentWeapon _x) isEqualTo "" };
    if (count _sac > 0) then { _ec pushBack format ["T1 arme PAS EN MAIN chez %1 hommes", count _sac] };
    // T2 · munitions
    private _sec = _hommes select { (_x ammo (primaryWeapon _x)) <= 0 };
    if (count _sec > 0) then { _ec pushBack format ["T2 chargeur VIDE chez %1 hommes", count _sec] };
    // T3 · le mode declare est-il celui du monde ? (WAKE recoupait FSM apres la scene)
    {
        private _m = _x getVariable ["hmt_mode", "?"];
        private _fsm = _x checkAIFeature "FSM";
        if (_m == "natif" && !_fsm) then { _ec pushBack "T3 mode natif mais FSM COUPEE (WAKE ?)" };
        if (_m == "pilote" && !(_x checkAIFeature "PATH")) then { _ec pushBack "T3 mode pilote mais PATH coupe (les JAMBES)" };
    } forEach _hommes;

    // T6 · combatMode ⟨CLIQUET, faute du 15/08⟩ : un homme en "BLUE" ne tirera JAMAIS.
    // 67 episodes ont ete joues par des attaquants desarmes par ce seul mot.
    {
        private _m = _x getVariable ["hmt_mode", "?"];
        if (_m != "statue" && {(combatMode (group _x)) == "BLUE" || {(combatMode _x) == "BLUE"}}) then {
            _ec pushBack format ["T6 combatMode BLUE = NE JAMAIS TIRER (mode %1)", _m];
        };
    } forEach _hommes;

    // ── PREUVES D ACTE, SUR UN BINOME JETABLE ──
    // ⚠️ Elles font TIRER et DEPLACER. Les passer sur les hommes de l episode corromprait
    // la scene qu elles doivent garantir : T5 deplace de 24 m, T4 vide un chargeur.
    // On les passe donc sur un homme temporaire, pose a 300 m, arme et pilote PAR LE SOCLE
    // — donc representatif — et supprime aussitot.
    // ⚠️ LE TEMOIN NAIT SUR UN TERRAIN VERIFIE PLAT. Il naissait a 300 m au hasard : quand
    // le relief masquait son mannequin, T4 echouait avec `vue:0` et le prevol bloquait tout
    // le banc — 28 % des episodes refuses le 16/08. Pire, les episodes qui PASSAIENT etaient
    // alors biaises vers les scenes plates.
    // Depuis cette reparation, le temoin ne teste QUE LA CHAINE DE TIR — arme en main,
    // chargee, une balle qui part sur ordre. Il ne teste PLUS la scene ni son relief.
    private _gt = createGroup west;
    private _ref = _hommes select 0;
    private _pt = []; private _meilleure = 99;

    // ⚠️ DISPOSITIF DE TEST — LE LIEU FORCE. Le placeur ci-dessous balaye 24 points FIXES
    // autour du premier attaquant (angles k*15, rayons 250 a 370) : AUCUN alea, donc le lieu
    // est fixe par SESSION, et c est la structure exacte du destin de session mesure le
    // 17/08 (X2 = 56,6). Voir DESTIN_EST_LE_LIEU.md.
    // Ce levier permet de REJOUER un lieu connu et de voir si le destin le suit. Il ne change
    // rien quand la variable n est pas posee.
    if (!isNil "HMT_LIEU_FORCE") then {
        _pt = [(HMT_LIEU_FORCE select 0), (HMT_LIEU_FORCE select 1), 0];
        _meilleure = [(_pt select 0), (_pt select 1)] call HMT_G_SLOPE;
        (format ["HMT|SOCLE|LIEU_FORCE|x|%1|y|%2|pente|%3", round (_pt select 0),
                 round (_pt select 1), round (100 * _meilleure) / 100]) call HMT_LOG;
    };
    if (HMT_PV_GEN != _gen) exitWith { ("HMT|SOCLE|PREVOL|ABANDONNE|gen|" + str _gen) call HMT_LOG; false };
    HMT_PV_ETAPE = "placeur";
    // ⚠️ LA PAUSE VIENT *APRES* L ASSIGNATION, ET ELLE FAIT 10 s. Premiere version : 16 s
    // posees AVANT l assignation suivante — mesure du 18/08, PLANTE 3/3 au lieu de VERT 3/3.
    // Une pause posee avant l assignation s AJOUTE au silence de l etape COURANTE : T4 dure
    // deja ~17 s de silence legitime, plus 16 s de pause = 33 s de stagnation continue sous
    // la meme etiquette, au-dessus du seuil de 12 sondages (~30-36 s). Le detecteur a fait
    // exactement son travail ; c est le dimensionnement qui etait faux.
    // DERIVE, sans regarder de resultat : la pause doit etre ENCADREE par un reset de `fige`,
    // donc posee APRES ; et sa taille doit laisser `silence de l etape + pause` sous le seuil.
    // Le pire cas est T4 (~17 s) : 17 + 10 = 27 s < 30. Cinq pauses de 10 s → +50 s, total
    // ~110 s : au-dessus de l ancien plafond de 90 s, sous la borne de 180, jamais figee.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "lenteur") then {
        ("HMT|SOCLE|LENTEUR|pause 10 s a " + HMT_PV_ETAPE) call HMT_LOG; sleep 10;
    };
    if (isNil "HMT_LIEU_FORCE") then {
        // 24 candidats, MELANGES : angles k*15, rayons 250 a 370. On ne cherche plus le
        // meilleur, on prend LE PREMIER RECU.
        private _cands = [];
        for "_k" from 0 to 23 do {
            private _a = _k * 15; private _r = 250 + (_k mod 4) * 40;
            _cands pushBack [(getPosATL _ref select 0) + _r * sin _a,
                             (getPosATL _ref select 1) + _r * cos _a];
        };
        // melange de Fisher-Yates : `BIS_fnc_arrayShuffle` n est pas garanti sur un serveur
        // sans le module fonctions, et une dependance silencieuse est une economie non declaree.
        for "_k" from (count _cands) - 1 to 1 step -1 do {
            private _q = floor (random (_k + 1));
            private _tmp = _cands select _k;
            _cands set [_k, _cands select _q]; _cands set [_q, _tmp];
        };
        private _essais = 0;
        HMT_PV_NCAND = 0;
        {
            _essais = _essais + 1;
            // ⚠️ LE PROGRES S EXPOSE, SINON LA PATIENCE NE PEUT PAS LE SUIVRE ⟨Fable, 18/08⟩.
            // Le plafond d attente etait GLOBAL contre un prevol dont la duree depend du
            // nombre de candidats brules — et l anneau de 24 points est FIXE PAR SESSION,
            // donc un plafond global convertit la pauvrete d un anneau en echecs REGROUPES
            // par session : le destin de session, gueri dans le canal du verdict, renaissait
            // dans le canal du TEMPS. Python suit desormais `HMT_PV_NCAND` autant que l etape.
            HMT_PV_NCAND = _essais;
            private _r = [_x] call HMT_G_PRATICABLE;
            (format ["HMT|SOCLE|CANDIDAT|n|%1|x|%2|y|%3|verdict|%4|metres|%5|vue|%6",
                     _essais, round (_x select 0), round (_x select 1),
                     _r select 0, _r select 1, round (100 * (_r select 2)) / 100]) call HMT_LOG;
            if ((_r select 0) == "recu") exitWith {
                _pt = [_x select 0, _x select 1, 0];
                _meilleure = [(_x select 0), (_x select 1)] call HMT_G_SLOPE;
            };
        } forEach _cands;
        (format ["HMT|SOCLE|PLACEUR|candidats_essayes|%1|recu|%2", _essais,
                 (count _pt > 0)]) call HMT_LOG;
    };
    if (count _pt == 0) exitWith {
        HMT_PV_ECARTS = ["T0 AUCUN LIEU TENABLE recu sur 24 candidats (vue >= 0.5 ET acte de tir) — la traverse ne trie plus depuis le 20/08"];
        "HMT|SOCLE|PREVOL|ROUGE|aucun lieu tenable (vue ou tir)" call HMT_LOG;
        false
    };
    private _t = [_gt, "B_Soldier_F", _pt, "temoin"] call HMT_POSER_HOMME;

    // ⚠️ LE DISPOSITIF DE SABOTAGE ⟨regle 18 : aucun critere ne juge sans avoir ete juge⟩.
    // Une porte doit avoir ete EXECUTEE sur un cas passant ET sur un cas echouant. Sans ce
    // levier, « T4 est vert » ne prouve pas que T4 sait rougir — il prouve seulement qu il
    // n a pas rougi. Le sabotage est donc PART DU SOCLE, pas un bricolage de banc.
    //   `HMT_SABOTER = "munitions"` retire les cartouches du temoin : T4 DOIT rougir.
    // Toute autre valeur, ou aucune, laisse le prevol intact.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "munitions") then {
        _t setVehicleAmmo 0;
        (format ["HMT|SOCLE|SABOTAGE|munitions|mun_restantes|%1",
                 count (magazines _t)]) call HMT_LOG;
    };
    _t allowDamage false;
    sleep 1;

    // T4 · une BALLE REELLE part ⟨regle 16 : juger l acte, pas l etat⟩
    // ⚠️ LE MANNEQUIN DOIT ETRE VU. Mesure du 16/08 : T4 echouait avec `vue:0` — arme en
    // main, AUTOCOMBAT actif, 30 cartouches, 48 m, et le relief entre les deux. Le test
    // mesurait « sait-il tirer » et butait sur « peut-il voir ». D ou son INTERMITTENCE :
    // le temoin nait a 300 m au hasard, donc la visibilite change a chaque episode.
    // On cherche donc une place D OU IL LE VOIT, et on le dit si on n en trouve aucune.
    private _gm = createGroup east;
    private _mann = _gm createUnit ["O_Soldier_F", [(_pt select 0), (_pt select 1) + 40, 0], [], 0, "NONE"];
    _mann disableAI "PATH"; _mann setBehaviour "CARELESS"; _mann allowDamage false;
    private _vu = 0; private _k = 0;
    while { _vu < 0.3 && _k < 12 } do {
        private _a = _k * 30; private _r = 30 + (_k mod 3) * 8;
        _mann setPosATL [(_pt select 0) + _r * sin _a, (_pt select 1) + _r * cos _a, 0];
        sleep 0.4;
        _vu = [objNull,"VIEW"] checkVisibility [eyePos _t, eyePos _mann];
        _k = _k + 1;
    };
    if (_vu < 0.3) then { _ec pushBack format ["T4 PLACE SANS VUE : 12 essais, meilleure vue %1", round (100*_vu)/100] };
    if (HMT_PV_GEN != _gen) exitWith { ("HMT|SOCLE|PREVOL|ABANDONNE|gen|" + str _gen) call HMT_LOG; false };
    // ⚠️ LES SABOTAGES DE L INSTRUMENT ⟨regle 18 pointee sur ma propre porte, Fable 18/08⟩.
    // Les quatre sabotages existants jugent le MONDE (T4, T5, traverse, tir). Les lignes
    // d INSTRUMENT — « zero prevol plante », « pas de regroupement » — jugeaient sans avoir
    // ete jugees. « gel » fige le prevol 60 s : la porte DOIT rendre PLANTE. « lenteur »
    // allonge le travail sans le figer : la porte doit rester VERTE sous patience-au-progres.
    HMT_PV_ETAPE = "T4";
    // ⚠️ LA PAUSE VIENT *APRES* L ASSIGNATION, ET ELLE FAIT 10 s. Premiere version : 16 s
    // posees AVANT l assignation suivante — mesure du 18/08, PLANTE 3/3 au lieu de VERT 3/3.
    // Une pause posee avant l assignation s AJOUTE au silence de l etape COURANTE : T4 dure
    // deja ~17 s de silence legitime, plus 16 s de pause = 33 s de stagnation continue sous
    // la meme etiquette, au-dessus du seuil de 12 sondages (~30-36 s). Le detecteur a fait
    // exactement son travail ; c est le dimensionnement qui etait faux.
    // DERIVE, sans regarder de resultat : la pause doit etre ENCADREE par un reset de `fige`,
    // donc posee APRES ; et sa taille doit laisser `silence de l etape + pause` sous le seuil.
    // Le pire cas est T4 (~17 s) : 17 + 10 = 27 s < 30. Cinq pauses de 10 s → +50 s, total
    // ~110 s : au-dessus de l ancien plafond de 90 s, sous la borne de 180, jamais figee.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "lenteur") then {
        ("HMT|SOCLE|LENTEUR|pause 10 s a " + HMT_PV_ETAPE) call HMT_LOG; sleep 10;
    };
    // ⚠️ LE GEL DORT *APRES* L ASSIGNATION D ETAPE ⟨Fable, 18/08⟩. Pose avant, l etape lisait
    // encore « placeur » pendant le gel : l instrument aurait menti dans le test cense
    // certifier sa parole — le log annoncait T4 quand l etiquette aurait dit placeur.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "gel") then {
        "HMT|SOCLE|SABOTAGE|gel|60 s SANS progres, a l etape T4" call HMT_LOG;
        sleep 60;
    };
    _t reveal [_mann, 4];
    sleep 2;
    HMT_PV_COUPS = 0;
    private _eh = _t addEventHandler ["Fired", { HMT_PV_COUPS = HMT_PV_COUPS + 1 }];
    private _t0 = time;
    // ⚠️ TROISIEME COPIE DU TIR, DECLAREE ET NON FACTORISEE ⟨lecture de Fable, 17/08⟩.
    // T4 n appelle PAS `HMT_TIRER_C9` parce qu il n emploie pas le meme canal : son temoin
    // GARDE `AUTOCOMBAT` (sans quoi rien ne part — mesure du 16/08) et sa boucle fait
    // `doTarget`, que ni l action 9 ni `HMT_TIRER_C9` ne font. Les aligner SANS MESURE serait
    // regler une divergence « par defaut », ce qui est precisement interdit : elle se regle
    // par UNE mesure — T4 passe-t-il avec `HMT_TIRER_C9` et sans `doTarget` ? — puis
    // alignement. Non mesuree a ce jour. T4 rend 0 echec sur 72 dans la sonde d unite ;
    // on ne touche pas a un test qui tient sans savoir ce qu on casse.
    // fenetre de 12 s, alignee sur la latence MESUREE de l IA (coups a 4-19 en 8 s,
    // balayages du 15/08). Le seuil reste 1 balle : c est la fenetre qui etait trop courte.
    while { time - _t0 < 12 } do { _t doWatch _mann; _t doTarget _mann;
        _t forceWeaponFire [currentWeapon _t, currentMuzzle _t]; sleep 0.33 };
    _t removeEventHandler ["Fired", _eh];
    // ⚠️ T4 DIT L ETAT DU TEMOIN QUAND IL ECHOUE. Sans cela son refus est muet, et j ai
    // deja perdu deux gestes a deviner ce qui manquait a cet homme.
    if (HMT_PV_COUPS < 1) then {
        _ec pushBack format ["T4 AUCUNE BALLE REELLE (0 en 12 s) — arme:%1 autoc:%2 fsm:%3 path:%4 mode:%5 dist:%6 vue:%7 mun:%8",
            (if ((currentWeapon _t) == "") then {"AUCUNE"} else {"oui"}),
            _t checkAIFeature "AUTOCOMBAT", _t checkAIFeature "FSM", _t checkAIFeature "PATH",
            combatMode _t, round (_t distance _mann),
            round (100 * ([objNull,"VIEW"] checkVisibility [eyePos _t, eyePos _mann])) / 100,
            _t ammo (primaryWeapon _t)];
    };

    // ⚠️ LE MANNEQUIN MEURT AVANT T5. Il etait supprime APRES, donc VIVANT pendant le test
    // de deplacement — un ennemi a 40 m a decouvert. Et le temoin garde `AUTOCOMBAT`, ce qui
    // lui permet de tirer en T4 : l IA le re-engageait et refusait d avancer. `doTarget
    // objNull` ne suffit pas, `AUTOCOMBAT` reacquiert de lui-meme, c est sa fonction.
    // Corrobore par la sonde des combinaisons du 15/08 : 111 m avec les facultes d IA
    // actives contre 154 sans. T4 et T5 etaient en CONFLIT sur le meme homme.
    // ⚠️ Ce correctif est le PROCES du diagnostic ⟨Fable⟩ : si T5 ne verdit pas, la cause
    // accusee est innocentee et l eau redevient suspect n°1 — d ou le journal ci-dessous,
    // dans LE MEME commit.
    deleteVehicle _mann; deleteGroup _gm;
    sleep 1;

    // ⚠️ `AUTOCOMBAT` EST RETIRE ENTRE T4 ET T5, ET C EST MESURE.
    // T4 exige que l homme tire DE LUI-MEME, donc `AUTOCOMBAT` actif — sonde du 16/08, « le
    // tir suit AUTOCOMBAT et rien d autre ». T5 exige qu il obeisse a une consigne de
    // deplacement, donc qu aucune IA ne reprenne la main. Deux etats INCOMPATIBLES sur le
    // meme homme : l etat doit changer ENTRE les deux tests, pas avant ni apres.
    // Banc des jambes v3 (`11fa45c`), les deux bras dans la MEME passe :
    //   bras 1, `AUTOCOMBAT` coupe ......... 12,2 m, 7 essais sur 7, dispersion 11,6-12,5
    //   bras 7, `AUTOCOMBAT` garde + tir ... 0,6 a 14,9 m, UN essai sur QUATRE tombe a 0,6
    // Supprimer le mannequin plus tot ne suffisait pas : l IA garde la menace en memoire
    // quelques secondes apres la mort de la cible et reprend la main sur le deplacement.
    _t disableAI "AUTOCOMBAT";

    // ⚠️ LE CONTROLE POSITIF DE T5 ⟨audit Fable, 16/08 : « un test qui rend zero rouge sur
    // cinquante est soit repare, soit devenu INCAPABLE d echouer, et tu ne sais pas lequel »⟩.
    // T4 avait son sabotage (les munitions) et pas T5. Retirer `PATH`, ce sont les JAMBES —
    // mesure du 15/08, 9 m au lieu de 48. T5 DOIT rougir.
    // ⚠️ LE LEVIER « jambes » ETAIT INOPERANT PAR NATURE, ET N AVAIT JAMAIS ETE EXECUTE.
    // Il retire `PATH`, donc le pathfinding — mais T5 se deplace par `setVelocity`, une
    // IMPULSION PHYSIQUE qui ne passe pas par le pathfinding. Mesure du 17/08 : 1 rouge sur
    // 3 seulement, les deux autres tirages restant verts jambes retirees.
    // C est la MEME faute que sur le placeur cet apres-midi (`disableAI "PATH"` la aussi),
    // et ce levier vivait depuis le socle 1.11.0 sans avoir jamais ete joue — exactement ce
    // que la regle 18 interdit : un critere qui n a pas ete juge.
    // On sabote donc L IMPULSION, comme pour l acte 2 du placeur.
    private _vyT5 = 6;
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "jambes") then {
        _vyT5 = 0;
        _t disableAI "PATH";
        (format ["HMT|SOCLE|SABOTAGE|jambes|path|%1", _t checkAIFeature "PATH"]) call HMT_LOG;
    };
    sleep 0.5;

    if (HMT_PV_GEN != _gen) exitWith { ("HMT|SOCLE|PREVOL|ABANDONNE|gen|" + str _gen) call HMT_LOG; false };
    HMT_PV_ETAPE = "T5";
    // ⚠️ LA PAUSE VIENT *APRES* L ASSIGNATION, ET ELLE FAIT 10 s. Premiere version : 16 s
    // posees AVANT l assignation suivante — mesure du 18/08, PLANTE 3/3 au lieu de VERT 3/3.
    // Une pause posee avant l assignation s AJOUTE au silence de l etape COURANTE : T4 dure
    // deja ~17 s de silence legitime, plus 16 s de pause = 33 s de stagnation continue sous
    // la meme etiquette, au-dessus du seuil de 12 sondages (~30-36 s). Le detecteur a fait
    // exactement son travail ; c est le dimensionnement qui etait faux.
    // DERIVE, sans regarder de resultat : la pause doit etre ENCADREE par un reset de `fige`,
    // donc posee APRES ; et sa taille doit laisser `silence de l etape + pause` sous le seuil.
    // Le pire cas est T4 (~17 s) : 17 + 10 = 27 s < 30. Cinq pauses de 10 s → +50 s, total
    // ~110 s : au-dessus de l ancien plafond de 90 s, sous la borne de 180, jamais figee.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "lenteur") then {
        ("HMT|SOCLE|LENTEUR|pause 10 s a " + HMT_PV_ETAPE) call HMT_LOG; sleep 10;
    };
    // T5 · un homme PARCOURT du terrain (setVelocity est une IMPULSION, pas une consigne)
    _t doTarget objNull; _t doWatch objNull;
    // ⚠️ LE CLIQUET DU BANC DES JAMBES, QUE JE N AVAIS PAS TRANSPOSE ICI. Ce banc a etabli
    // le 16/08 que les bras `setVelocity` dependent du NOMBRE d impulsions emises, et pas
    // les bras `doMove` — d ou son ecartement sous 25 iterations. T5 emet `setVelocity` a
    // 10 Hz et ne comptait rien. Or un serveur charge emet moins d impulsions dans la meme
    // fenetre : le reveil met huit hommes en IA complete, et T5 rougit 17 fois sur 20 avec
    // reveil contre 2 sur 12 sans. `nt` et `fps` disent si c est la cadence qui tombe.
    // ⚠️ T5 APPELLE LE MEME CODE QUE L ACTE 2 DU PLACEUR : un acte, un code.
    // ═══ T5 FUSIONNE — LE CANAL EST-IL VIVANT ? ══════════════════════════════════════
    // ⚠️ LE PLACEUR ET T5 NE FONT PLUS QU UN GESTE. L acte de traverse du placeur est
    // retire (c etait le selecteur, il mesurait la pente vers le nord) et T5 ne mesure
    // plus UNE marche mais LES HUIT AZIMUTS de la couture, au MAXIMUM.
    // ⚠️ LA LIGNE `GESTE` EST SUPPRIMEE : ses champs `_vrelue` et `_anims` etaient hors
    // de leur portee depuis le 17/08 23:02 et ecrivaient `any` — 71 lignes mortes sur
    // tout le disque — et ses champs `sol`/`posture` interrogeaient `_t`, un homme qui
    // n avait jamais marche. Une ligne de journal est un instrument : elle se relit sur
    // une ligne REELLE le jour de sa naissance, ou elle ment en silence.
    private _sabT5 = if (_vyT5 == 0) then { "jambes" } else { "" };
    private _cv = [[_pt select 0, _pt select 1], _sabT5] call HMT_CANAL_VIVANT;
    private _vivant = _cv select 0; private _m = _cv select 1; private _d8 = _cv select 2;

    private _su = 0;
    { private _k = _x knowsAbout _t; if (_k > _su) then { _su = _k } } forEach (allUnits select { side _x == east });
    (format ["HMT|SOCLE|T5|max_joues|%1|plancher|%2|vivant|%3|d|%4|fps|%5|connu_des_ennemis|%6|autocombat_reel|%7|fsm|%8|path|%9|degats|%10",
             _m, HMT_CANAL_PLANCHER, _vivant, _d8, round (diag_fps),
             round (100 * _su) / 100, _t checkAIFeature "AUTOCOMBAT",
             _t checkAIFeature "FSM", _t checkAIFeature "PATH",
             round (100 * (damage _t)) / 100]) call HMT_LOG;
    if (!_vivant) then { _ec pushBack format ["T5 CANAL MORT : max %1 m sur 8 azimuts (plancher %2) — connu:%3 autoc:%4 path:%5 degats:%6", _m, HMT_CANAL_PLANCHER, round (100*_su)/100, _t checkAIFeature "AUTOCOMBAT", _t checkAIFeature "PATH", round (100*(damage _t))/100] };

    deleteVehicle _t; deleteGroup _gt;

    // ⚠️ LES ECARTS SONT EXPOSES. Le journal du socle part dans le RPT, invisible du pont :
    // un prevol rouge etait donc MUET sur sa raison. On les garde dans une globale que le
    // pilote peut demander par la socket.
    HMT_PV_ECARTS = _ec;
    // ═══ T7 · PAR QUEL CANAL PART LE FEU DE L HOMME SERVI ? ═══════════════════════════
    // ⚠️ T4 CERTIFIE UN CANAL QUE LA POLITIQUE N EMPRUNTE PAS. Verifie le 16/08 :
    // `arma_couture.py:27` pose `disableAI "AUTOCOMBAT"` sur l homme servi, alors que le
    // temoin de T4 le GARDE — et il le garde parce que, mesure le meme jour,
    // `forceWeaponFire` SEUL ne fait pas tirer. Le vert de T4 couvre donc une capacite que
    // la politique n a pas, et le feu de la politique n est certifie par AUCUN test.
    // T7 le certifie : un homme dans le mode SERVI (`pilote`), et le canal EXACT de
    // l action 9 de la couture — `setDir` + `doWatch` + `forceWeaponFire` a 3 coups/s.
    // ⚠️ Et il RELEVE `AUTOCOMBAT` reellement actif : `ANOMALIE_AUTOCOMBAT.md` dit que
    // l ordre ne prend pas sur les attaquants. Si l homme servi tire, c est ou bien par ce
    // canal, ou bien par une faculte qu on croit coupee. T7 dit lequel.
    if (HMT_PV_GEN != _gen) exitWith { ("HMT|SOCLE|PREVOL|ABANDONNE|gen|" + str _gen) call HMT_LOG; false };
    HMT_PV_ETAPE = "T7";
    // ⚠️ LA PAUSE VIENT *APRES* L ASSIGNATION, ET ELLE FAIT 10 s. Premiere version : 16 s
    // posees AVANT l assignation suivante — mesure du 18/08, PLANTE 3/3 au lieu de VERT 3/3.
    // Une pause posee avant l assignation s AJOUTE au silence de l etape COURANTE : T4 dure
    // deja ~17 s de silence legitime, plus 16 s de pause = 33 s de stagnation continue sous
    // la meme etiquette, au-dessus du seuil de 12 sondages (~30-36 s). Le detecteur a fait
    // exactement son travail ; c est le dimensionnement qui etait faux.
    // DERIVE, sans regarder de resultat : la pause doit etre ENCADREE par un reset de `fige`,
    // donc posee APRES ; et sa taille doit laisser `silence de l etape + pause` sous le seuil.
    // Le pire cas est T4 (~17 s) : 17 + 10 = 27 s < 30. Cinq pauses de 10 s → +50 s, total
    // ~110 s : au-dessus de l ancien plafond de 90 s, sous la borne de 180, jamais figee.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "lenteur") then {
        ("HMT|SOCLE|LENTEUR|pause 10 s a " + HMT_PV_ETAPE) call HMT_LOG; sleep 10;
    };
    // ⚠️ T7 APPELLE LE MEME CODE QUE L ACTE 3 DU PLACEUR ⟨Fable⟩ : un acte, un code.
    private _r7 = [[_pt select 0, _pt select 1], 4] call HMT_ACTE_TIR_SERVI;
    HMT_PV_C7 = _r7 select 0;
    private _a7 = false;
    (format ["HMT|SOCLE|T7|coups|%1|vue|%2|dist|%3|autocombat_reel|%4",
             HMT_PV_C7, _r7 select 1, _r7 select 2, _a7]) call HMT_LOG;
    if (HMT_PV_C7 < 1) then {
        _ec pushBack format ["T7 LE CANAL DE FEU DE L HOMME SERVI EST MUET (0 coup en 4 s) — vue:%1 dist:%2", _r7 select 1, _r7 select 2];
    };
    HMT_PV_CANAL = [HMT_PV_C7, _r7 select 1];

    // ⚠️ LE JOURNAL DES POSITIONS, DANS LE MEME COMMIT QUE LE CORRECTIF. L hypothese de
    // l eau n est PAS verifiee : si l echantillonneur pose des temoins dans l eau, il
    // contamine aussi T1-T4, donc les VERTS. Sans ce journal, elle resterait indecidable.
    (format ["HMT|SOCLE|LIEU|x|%1|y|%2|hauteur|%3|eau|%4|pente|%5|meilleure_pente|%6",
             round (_pt select 0), round (_pt select 1),
             round (getTerrainHeightASL [_pt select 0, _pt select 1]),
             surfaceIsWater [_pt select 0, _pt select 1],
             round (100 * ([_pt select 0, _pt select 1] call HMT_G_SLOPE)) / 100,
             round (100 * _meilleure) / 100]) call HMT_LOG;
    HMT_PV_LIEU = [_pt select 0, _pt select 1,
                   surfaceIsWater [_pt select 0, _pt select 1], _meilleure];

    HMT_PV_ETAPE = "fini";
    // ⚠️ LA PAUSE VIENT *APRES* L ASSIGNATION, ET ELLE FAIT 10 s. Premiere version : 16 s
    // posees AVANT l assignation suivante — mesure du 18/08, PLANTE 3/3 au lieu de VERT 3/3.
    // Une pause posee avant l assignation s AJOUTE au silence de l etape COURANTE : T4 dure
    // deja ~17 s de silence legitime, plus 16 s de pause = 33 s de stagnation continue sous
    // la meme etiquette, au-dessus du seuil de 12 sondages (~30-36 s). Le detecteur a fait
    // exactement son travail ; c est le dimensionnement qui etait faux.
    // DERIVE, sans regarder de resultat : la pause doit etre ENCADREE par un reset de `fige`,
    // donc posee APRES ; et sa taille doit laisser `silence de l etape + pause` sous le seuil.
    // Le pire cas est T4 (~17 s) : 17 + 10 = 27 s < 30. Cinq pauses de 10 s → +50 s, total
    // ~110 s : au-dessus de l ancien plafond de 90 s, sous la borne de 180, jamais figee.
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "lenteur") then {
        ("HMT|SOCLE|LENTEUR|pause 10 s a " + HMT_PV_ETAPE) call HMT_LOG; sleep 10;
    };
    private _vert = (count _ec == 0);
    // ⚠️ REVUE 17/08 : `HMT_SABOTER` est une globale de missionNamespace que RIEN ne
    // remet a zero. Un banc qui la pose puis plante la laisse en place, et TOUTES les
    // sessions suivantes rougissent en T4 avec une ligne de verdict IDENTIQUE a celle
    // d un vrai rouge. Un sabotage oublie devenait un verdict. Le champ est AJOUTE en
    // fin de ligne pour ne pas deplacer les champs que les lecteurs existants comptent.
    private _sab = missionNamespace getVariable ["HMT_SABOTER", ""];
    (format ["HMT|SOCLE|PREVOL|%1|version|%2|hommes|%3|ecarts|%4|sabotage|%5",
             (if (_vert) then {"VERT"} else {"ROUGE"}), HMT_SOCLE_VERSION, count _hommes,
             (if (_vert) then {"aucun"} else {str _ec}),
             (if (_sab == "") then {"aucun"} else {_sab})]) call HMT_LOG;
    _vert
};

// ── LA GARDE : un banc ne joue QUE par ici. Pas de prevol vert, pas d episode.
HMT_JOUER = {
    params ["_hommes", "_episode"];
    if !([_hommes] call HMT_PREVOL) exitWith {
        "HMT|SOCLE|REFUS|prevol rouge — aucun episode ne sera joue" call HMT_LOG;
        false
    };
    call _episode;
    true
};

(format ["HMT|SOCLE|pret|%1", HMT_SOCLE_VERSION]) call HMT_LOG;
