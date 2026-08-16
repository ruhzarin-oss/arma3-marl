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

HMT_SOCLE_VERSION = "1.8.0-16082026";
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
HMT_PREVOL = {
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
    for "_k" from 0 to 23 do {
        private _a = _k * 15; private _r = 250 + (_k mod 4) * 40;
        private _c = [(getPosATL _ref select 0) + _r * sin _a, (getPosATL _ref select 1) + _r * cos _a];
        // pente moyenne sur le carre de 60 m ou le temoin va vivre et tirer
        private _s = 0;
        for "_i" from -4 to 4 step 4 do { for "_j" from -4 to 4 step 4 do {
            _s = _s + ([(_c select 0) + _i*6.25, (_c select 1) + _j*6.25] call HMT_G_SLOPE);
        }};
        _s = _s / 9;
        if ((getTerrainHeightASL _c) > 3 && _s < _meilleure) then { _meilleure = _s; _pt = [_c select 0, _c select 1, 0] };
        if (_meilleure < 0.10) exitWith {};
    };
    if (count _pt == 0) exitWith {
        HMT_PV_ECARTS = ["T0 AUCUN TERRAIN PLAT trouve pour le temoin en 24 essais"];
        "HMT|SOCLE|PREVOL|ROUGE|aucun terrain plat" call HMT_LOG;
        false
    };
    private _t = [_gt, "B_Soldier_F", _pt, "temoin"] call HMT_POSER_HOMME;
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
    _t reveal [_mann, 4];
    sleep 2;
    HMT_PV_COUPS = 0;
    private _eh = _t addEventHandler ["Fired", { HMT_PV_COUPS = HMT_PV_COUPS + 1 }];
    private _t0 = time;
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

    // T5 · un homme PARCOURT du terrain (setVelocity est une IMPULSION, pas une consigne)
    _t doTarget objNull; _t doWatch objNull;
    private _p0 = getPosATL _t; private _t1 = time;
    // ⚠️ LE JOURNAL DU GESTE ⟨une passe, quatre causes⟩. 1 m en 4 s n est pas 9 m : ce n est
    // pas un homme sans jambes, c est un homme qui ne bouge PAS. Quatre causes possibles,
    // et chacune ecrit une signature differente ici :
    //   (a) POSTURE  — couche/genou apres avoir tire en T4 : anim contient Ppne/Pknl
    //   (b) IA       — re-engagement : conduite = COMBAT et la vitesse relue retombe a 0
    //   (c) OBSTACLE — vitesse relue = 6 mais deplacement nul
    //   (d) FIGE     — vitesse relue = 0 des la 1re relecture (impulsion jamais appliquee)
    private _vrelue = []; private _anims = [];
    while { time - _t1 < 4 } do {
      _t setVelocity [0, 6, 0];
      _vrelue pushBack (round (10 * ((velocity _t) select 1)) / 10);
      _anims pushBack (animationState _t);
      sleep 0.1;
    };
    private _m = _p0 distance2D (getPosATL _t);
    (format ["HMT|SOCLE|GESTE|m|%1|v_apres|%2|v_mediane|%3|v_fin|%4|conduite|%5|anim0|%6|anim9|%7|animfin|%8|posture|%9|sol|%10",
             round _m,
             _vrelue select 0,
             _vrelue select (round ((count _vrelue) / 2)),
             _vrelue select ((count _vrelue) - 1),
             behaviour _t, _anims select 0, _anims select (9 min ((count _anims) - 1)),
             _anims select ((count _anims) - 1),
             stance _t, isTouchingGround _t]) call HMT_LOG;
    if (_m < 10) then { _ec pushBack format ["T5 IMMOBILE : %1 m en 4 s (attendu ~24)", round _m] };

    deleteVehicle _t; deleteGroup _gt;

    // ⚠️ LES ECARTS SONT EXPOSES. Le journal du socle part dans le RPT, invisible du pont :
    // un prevol rouge etait donc MUET sur sa raison. On les garde dans une globale que le
    // pilote peut demander par la socket.
    HMT_PV_ECARTS = _ec;
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

    private _vert = (count _ec == 0);
    (format ["HMT|SOCLE|PREVOL|%1|version|%2|hommes|%3|ecarts|%4",
             (if (_vert) then {"VERT"} else {"ROUGE"}), HMT_SOCLE_VERSION, count _hommes,
             (if (_vert) then {"aucun"} else {str _ec})]) call HMT_LOG;
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
