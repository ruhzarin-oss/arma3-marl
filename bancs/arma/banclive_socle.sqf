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

HMT_SOCLE_VERSION = "2.6.0-17082026";
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
HMT_CERTIFIER_POSITIONS = {
    params ["_positions", ["_duree", 4], ["_seuil", 23]];
    private _gW = createGroup west; private _gE = createGroup east;
    private _hs = []; private _ms = [];
    {
        private _u = _gW createUnit ["B_Soldier_F", [_x select 0, _x select 1, 0], [], 0, "NONE"];
        // tout homme jetable est invulnerable ET neutre, uniformement
        _u allowDamage false; _u setCaptive true;
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u setBehaviour "CARELESS";
        _u enableAI "PATH"; [_u] call HMT_ARMER;
        private _m = _gE createUnit ["O_Soldier_F", [_x select 0, (_x select 1) + 40, 0], [], 0, "NONE"];
        _m allowDamage false; _m setCaptive true;
        _m disableAI "AUTOCOMBAT"; _m disableAI "FSM"; _m setBehaviour "CARELESS";
        [_m] call HMT_ARMER;
        _hs pushBack _u; _ms pushBack _m;
    } forEach _positions;
    sleep 2;
    // ── ACTE 1 · TRAVERSE, TOUS EN MEME TEMPS, UNE SEULE FENETRE
    private _p0 = _hs apply { getPosATL _x };
    private _t0 = time;
    while { time - _t0 < _duree } do { { _x setVelocity [0, 6, 0] } forEach _hs; sleep 0.1 };
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
    params ["_u", "_duree", ["_vy", 6]];
    private _p0 = getPosATL _u; private _t0 = time; private _nt = 0;
    while { alive _u && time - _t0 < _duree } do {
        _u setVelocity [0, _vy, 0]; _nt = _nt + 1; sleep 0.1;
    };
    [_p0 distance2D (getPosATL _u), _nt]      // [metres, iterations]
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
    // ── ACTE 2 · UN HOMME PARCOURT-IL SES 24 m ? C est le geste exact de T5.
    private _g = createGroup west;
    private _u = _g createUnit ["B_Soldier_F", [_x, _y, 0], [], 0, "NONE"];
    if (isNull _u) exitWith { deleteGroup _g; ["naissance refusee", 0, _vue] };
    [_u] call HMT_ARMER;
    [_u, "statue"] call HMT_PILOTER;      // ni IA de combat ni decision : on teste le TERRAIN
    _u enableAI "PATH";                   // ...mais les JAMBES restent, sinon on mesure une statue
    // ⚠️ TOUT HOMME JETABLE EST INVULNERABLE, UNIFORMEMENT ⟨lecture de Fable, 17/08⟩.
    // La scene cree ses defenseurs en COMBAT/RED avec `AUTOCOMBAT` actif des la naissance, et
    // les lieux candidats sont a 80-540 m de l objectif — DANS LA PORTEE. Un testeur abattu en
    // pleine traverse rend « encombre », et le placeur rejette alors un lieu qui allait bien.
    _u allowDamage false;
    _u setDir 0;
    sleep 1.5;
    // ⚠️ LE LEVIER DE SABOTAGE ⟨regle 18⟩ : sans lui, « le placeur accepte » ne prouve pas
    // qu il sait REFUSER. `HMT_SABOTER = "traverse"` retire les jambes du testeur : AUCUN
    // lieu ne doit plus etre recu, et le prevol doit rougir en T0.
    // ⚠️ LE SABOTAGE DOIT ATTAQUER CE QUE LE TEST EMPLOIE ⟨regle 6, appliquee au sabotage⟩.
    // Premiere version : `disableAI "PATH"`. INOPERANT PAR NATURE — `setVelocity` est une
    // IMPULSION PHYSIQUE et ne passe pas par le pathfinding ; les deux lieux recus rendaient
    // toujours 25 m et 22 m sous sabotage. Fait etabli du projet, et oublie en concevant le
    // levier. On sabote donc l IMPULSION elle-meme : vitesse nulle, immobilite certaine, et
    // le test doit rendre « encombre ».
    private _vy = 6;
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "traverse") then { _vy = 0 };
    private _m = ([_u, 4, _vy] call HMT_MARCHER) select 0;
    deleteVehicle _u; deleteGroup _g;
    // ⚠️ SEUIL A 23 m, ET LA RAISON NE REGARDE PAS LES RESULTATS ⟨regle 13⟩ :
    // UN PLACEUR NE DOIT JAMAIS ETRE PLUS INDULGENT QUE LE TEST QU IL PREPARE.
    // T5 attend 24 m (6 m/s x 4 s). Le v2 exigeait 18 — une remise de 25 % que rien ne
    // justifiait, et qui n etait qu un chiffre rond. Le seuil est le NOMINAL moins la seule
    // tolerance de mesure. Ca RESSERRE, donc c est licite.
    if (_m < 23) exitWith { deleteVehicle _u; deleteGroup _g; ["encombre", round _m, _vue, 0] };

    // ── ACTE 3 · UN HOMME DANS LE MODE *SERVI* TIRE-T-IL DEPUIS CE LIEU ?
    // ⚠️ LE PLACEUR VERIFIAIT QU ON VOIT, JAMAIS QU ON TIRE. Porte du 17/08 : une fois le
    // deplacement borne, T7 est devenu le canal dominant — 17 echecs sur 50 — et rien dans
    // le placeur ne le couvrait. Voir/tirer ne sont pas la meme chose : l homme SERVI a
    // `AUTOCOMBAT` coupe (`arma_couture.py:27`) et emprunte le canal de l action 9.
    // On rejoue donc ce canal EXACT, sur un homme dans le mode SERVI ⟨regle 6⟩.
    private _gm = createGroup east;
    private _mm = _gm createUnit ["O_Soldier_F", [_x, _y + 40, 0], [], 0, "NONE"];
    [_mm] call HMT_ARMER;
    // ⚠️ RECIDIVE : la revue avait blinde T7 le meme jour, et personne n a transpose ici.
    // Le mannequin etait ARME et en IA LIBRE, le testeur sans protection : quatre secondes de
    // DUEL REEL. Un mannequin qui tue le testeur fabrique un « muet », donc rejette un bon
    // lieu — et il le fait preferentiellement dans les lieux OUVERTS, ou il voit et tire vite.
    // Le placeur biaisait donc CONTRE le degagement, exactement l inverse de ce qu on veut.
    _mm allowDamage false; _mm setCaptive true;
    _mm disableAI "AUTOCOMBAT"; _mm disableAI "FSM"; _mm setBehaviour "CARELESS";
    private _g2 = createGroup west;
    private _u2 = _g2 createUnit ["B_Soldier_F", [_x, _y, 0], [], 0, "NONE"];
    private _enmain = [_u2] call HMT_ARMER;
    [_u2, "pilote"] call HMT_PILOTER;          // le mode SERVI, pas celui du temoin de T4
    _u2 allowDamage false;
    sleep 1.5;
    private _coups = [_u2, _mm, 4] call HMT_TIRER_C9;
    deleteVehicle _mm; deleteVehicle _u2; deleteGroup _gm; deleteGroup _g2;
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
        {
            _essais = _essais + 1;
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
        HMT_PV_ECARTS = ["T0 AUCUN LIEU PRATICABLE recu sur 24 candidats (traverse 18 m ET vue 40 m)"];
        "HMT|SOCLE|PREVOL|ROUGE|aucun terrain plat" call HMT_LOG;
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
    HMT_PV_ETAPE = "T4";
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
    if ((missionNamespace getVariable ["HMT_SABOTER", ""]) == "jambes") then {
        _t disableAI "PATH";
        (format ["HMT|SOCLE|SABOTAGE|jambes|path|%1", _t checkAIFeature "PATH"]) call HMT_LOG;
    };
    sleep 0.5;

    if (HMT_PV_GEN != _gen) exitWith { ("HMT|SOCLE|PREVOL|ABANDONNE|gen|" + str _gen) call HMT_LOG; false };
    HMT_PV_ETAPE = "T5";
    // T5 · un homme PARCOURT du terrain (setVelocity est une IMPULSION, pas une consigne)
    _t doTarget objNull; _t doWatch objNull;
    // ⚠️ LE CLIQUET DU BANC DES JAMBES, QUE JE N AVAIS PAS TRANSPOSE ICI. Ce banc a etabli
    // le 16/08 que les bras `setVelocity` dependent du NOMBRE d impulsions emises, et pas
    // les bras `doMove` — d ou son ecartement sous 25 iterations. T5 emet `setVelocity` a
    // 10 Hz et ne comptait rien. Or un serveur charge emet moins d impulsions dans la meme
    // fenetre : le reveil met huit hommes en IA complete, et T5 rougit 17 fois sur 20 avec
    // reveil contre 2 sur 12 sans. `nt` et `fps` disent si c est la cadence qui tombe.
    private _mnt = [_t, 4] call HMT_MARCHER;
    private _m = _mnt select 0; private _nt = _mnt select 1;

    (format ["HMT|SOCLE|GESTE|m|%1|v_apres|%2|v_mediane|%3|v_fin|%4|conduite|%5|anim0|%6|anim9|%7|animfin|%8|posture|%9|sol|%10",
             round _m,
             _vrelue select 0,
             _vrelue select (round ((count _vrelue) / 2)),
             _vrelue select ((count _vrelue) - 1),
             behaviour _t, _anims select 0, _anims select (9 min ((count _anims) - 1)),
             _anims select ((count _anims) - 1),
             stance _t, isTouchingGround _t]) call HMT_LOG;
    // ⚠️ T5 DIT L ETAT DU TEMOIN QUAND IL ECHOUE — comme T4 le fait depuis ce matin. Un refus
    // muet a deja coute quatre diagnostics faux dans la seule journee du 16/08. Deux choses
    // separent les causes : le temoin est-il CONNU des ennemis (donc sous le feu d un monde
    // reveille), et son `AUTOCOMBAT` a-t-il vraiment ete retire ?
    private _su = 0;
    { private _k = _x knowsAbout _t; if (_k > _su) then { _su = _k } } forEach (allUnits select { side _x == east });
    (format ["HMT|SOCLE|T5|nt|%7|fps|%8|m|%1|connu_des_ennemis|%2|autocombat_reel|%3|fsm|%4|path|%5|degats|%6",
             round _m, round (100 * _su) / 100, _t checkAIFeature "AUTOCOMBAT",
             _t checkAIFeature "FSM", _t checkAIFeature "PATH",
             round (100 * (damage _t)) / 100, _nt, round (diag_fps)]) call HMT_LOG;
    if (_m < 10) then { _ec pushBack format ["T5 IMMOBILE : %1 m en 4 s (attendu ~24) — connu:%2 autoc:%3 path:%4 degats:%5", round _m, round (100*_su)/100, _t checkAIFeature "AUTOCOMBAT", _t checkAIFeature "PATH", round (100*(damage _t))/100] };

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
    private _g7 = createGroup west;
    // ⚠️ T7 TESTE LE LIEU QUE LE PLACEUR A VALIDE, PAS SIX METRES A COTE.
    // Porte du 17/08 : 23 echecs T7 sur 40, et le releve du socle SEPARE PARFAITEMENT —
    // `vue|0` rend 0 coup, `vue|1` rend 12. T7 n echouait pas sur le canal de feu, il
    // echouait parce que SON mannequin n etait pas visible. L acte 3 du placeur valide le
    // point EXACT avec un mannequin a 40 m plein nord ; T7 posait le sien a `_pt + 6` et
    // 35 m. Six metres suffisent a passer derriere un arbre. Le `+6` evitait un chevauchement
    // avec le temoin de T5 — mais celui-ci est deja supprime a ce stade.
    // DEUX TESTS DU MEME SOCLE DOIVENT S ACCORDER SUR LA GEOMETRIE QU ILS EXIGENT.
    private _u7 = [_g7, "B_Soldier_F", [(_pt select 0), (_pt select 1), 0], "pilote"] call HMT_POSER_HOMME;
    // ⚠️ REVUE 17/08 : NI `_u7` NI `_m7` n avaient `allowDamage false`, contrairement au
    // binome de T4 (lignes 196 et 207). Et `_m7` etait ARME (HMT_ARMER) et en IA LIBRE —
    // il ne passait jamais par HMT_PILOTER — a 35 m d un homme en mode `pilote`, donc
    // AUTOCOMBAT coupe et incapable de riposter. `_m7` pouvait donc ABATTRE le temoin
    // pendant les 4 s du test : HMT_PV_C7 restait a 0, T7 rougissait, et le prevol
    // refusait tout l episode pour un MORT et non pour un canal de feu muet.
    _u7 allowDamage false;
    private _gm7 = createGroup east;
    private _m7 = _gm7 createUnit ["O_Soldier_F", [(_pt select 0), (_pt select 1) + 40, 0], [], 0, "NONE"];
    [_m7] call HMT_ARMER;
    _m7 allowDamage false; _m7 disableAI "PATH"; _m7 disableAI "AUTOCOMBAT";
    _m7 setBehaviour "CARELESS";
    sleep 1.5;
    _u7 reveal [_m7, 4];
    HMT_PV_C7 = [_u7, _m7, 4] call HMT_TIRER_C9;
    private _a7 = _u7 checkAIFeature "AUTOCOMBAT";
    (format ["HMT|SOCLE|T7|coups|%1|autocombat_reel|%2|fsm|%3|arme|%4|vue|%5",
             HMT_PV_C7, _a7, _u7 checkAIFeature "FSM", currentWeapon _u7,
             round (100 * ([objNull,"VIEW"] checkVisibility [eyePos _u7, eyePos _m7])) / 100]) call HMT_LOG;
    if (HMT_PV_C7 < 1) then {
        _ec pushBack format ["T7 LE CANAL DE FEU DE L HOMME SERVI EST MUET (0 coup en 4 s) — autoc:%1 fsm:%2 arme:%3", _a7, _u7 checkAIFeature "FSM", currentWeapon _u7];
    };
    HMT_PV_CANAL = [HMT_PV_C7, _a7];
    deleteVehicle _m7; deleteVehicle _u7; deleteGroup _gm7; deleteGroup _g7;

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
