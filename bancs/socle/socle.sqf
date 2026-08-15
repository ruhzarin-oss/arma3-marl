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

HMT_SOCLE_VERSION = "1.1.0-15082026";
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

    // ── PREUVES D ACTE : le monde fait-il vraiment ce que je crois ? ──
    private _t = _hommes select 0;
    // T4 · une BALLE REELLE part (regle 16 : juger l acte, pas l etat)
    // ⚠️ IL FAUT UNE CIBLE ACQUERABLE. Mesure du 15/08 (trois balayages) : viser une position
    // vide sans ennemi dans la scene ne produit AUCUN coup — c est ce qui rendait le banc
    // `feu_force` muet, sa cible etant derriere un muret. Sans mannequin, ce test declarerait
    // ROUGE un monde parfaitement sain.
    private _gm = createGroup east;
    private _mann = _gm createUnit ["O_Soldier_F", [(getPosATL _t select 0), (getPosATL _t select 1) + 45, 0], [], 0, "NONE"];
    _mann setPosATL [(getPosATL _t select 0), (getPosATL _t select 1) + 45, 0];
    _mann disableAI "PATH"; _mann setBehaviour "CARELESS"; _mann allowDamage false;
    _t reveal [_mann, 4];
    sleep 2;
    HMT_PV_COUPS = 0;
    private _eh = _t addEventHandler ["Fired", { HMT_PV_COUPS = HMT_PV_COUPS + 1 }];
    private _t0 = time;
    while { time - _t0 < 6 } do { _t doWatch _mann; _t doTarget _mann;
        _t forceWeaponFire [currentWeapon _t, currentMuzzle _t]; sleep 0.33 };
    _t removeEventHandler ["Fired", _eh];
    _t doTarget objNull; _t doWatch objNull;
    deleteVehicle _mann; deleteGroup _gm;
    if (HMT_PV_COUPS < 1) then { _ec pushBack format ["T4 AUCUNE BALLE REELLE (%1 en 6 s, cible acquerable)", HMT_PV_COUPS] };

    // T5 · un homme PARCOURT du terrain (setVelocity est une IMPULSION, pas une consigne)
    private _p0 = getPosATL _t; private _t1 = time;
    while { time - _t1 < 4 } do { _t setVelocity [0, 6, 0]; sleep 0.1 };
    private _m = _p0 distance2D (getPosATL _t);
    if (_m < 10) then { _ec pushBack format ["T5 IMMOBILE : %1 m en 4 s (attendu ~24)", round _m] };

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
