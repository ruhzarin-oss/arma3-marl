// CONTROLE POSITIF DU LINTEUR — ce fichier contient EXACTEMENT les cinq fautes qui m ont coute
// la nuit du 08 au 09 aout. Le linteur DOIT les attraper toutes les cinq. S il en manque une,
// c est lui qui est casse, pas ce fichier. ⟨une mesure doit savoir echouer⟩
private _u = player;
private _liste = [];

// 1. exitWith employe comme un branchement : l affectation ne servira jamais
if (!isNil "HMT_CANDIDATS") exitWith {
    HMT_SITES = HMT_CANDIDATS;
    diag_log "on croit brancher, on quitte tout le bloc";
};

// 2. commande UNAIRE employee comme binaire
private _n = _u magazinesAmmo;

// 3. `Hit` sur un homme invulnerable : l evenement ne se declenche jamais
_u addEventHandler ["Hit", { diag_log "jamais appele" }];

// 4. suppressFor appliquee au TIREUR : elle le fait taire
_u commandSuppressiveFire _cible; _u suppressFor 8;

// 5. someAmmo pris pour « son fusil est charge »
if (someAmmo _u) then { diag_log "il a une grenade, pas forcement un fusil charge" };
