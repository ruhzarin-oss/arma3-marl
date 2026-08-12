// fn_postInit.sqf — CAPTEUR + ACTUATEUR Harmattan, greffes sur Antistasi Ultimate.
//
// PRINCIPE : on ne decide rien, on ne corrige rien, on ne suggere rien au jeu.
// Le capteur recopie l'etat que le jeu tient lui-meme (markersX, sidesX, hr,
// resourcesFIA, agressivite, tierWar). L'actuateur execute le SQF que Python
// envoie. Toute doctrine viendrait de Python, jamais d'ici.
//
// OUT : "hmt_native" callExtension ("o|" + ligne) -> TCP -> Python
// IN  : poll "p|<n>" -> chunks "M|"/"D|" -> call compile

if (!isServer) exitWith {};

HMT_OUT = { "hmt_native" callExtension ("o|" + _this); };
HMT_NN = 0;
HMT_PERIODE = 10;          // secondes entre deux releves d'etat

diag_log "HMT_CAPTEUR addon charge";
"HMT_CAPTEUR addon charge" call HMT_OUT;
("HMT_EXT version=" + ("hmt_native" callExtension "version")) call HMT_OUT;

// ─────────────────────────── ACTUATEUR ───────────────────────────
// Recoit le SQF de Python et l'execute tel quel. C'est le seul chemin
// par lequel un agent peut agir.
[] spawn {
    while {true} do {
        private _next = HMT_NN + 1;
        private _acc = ""; private _go = true; private _done = false;
        while {_go} do {
            private _r = "hmt_native" callExtension ("p|" + str _next);
            if (_r isEqualTo "") then { _go = false }
            else {
                _acc = _acc + (_r select [2]);
                if ((_r select [0, 2]) isEqualTo "D|") then { _go = false; _done = true; };
            };
        };
        if (_done) then {
            ("HARMATTAN_RECV cmd " + str _next) call HMT_OUT;
            call compile _acc;
            HMT_NN = _next;
        } else { sleep 0.1; };
    };
};

// ─────────────────────────── CAPTEUR ───────────────────────────
[] spawn {
    // On attend qu'Antistasi ait construit sa carte de zones. Un pont qui
    // repond ne prouve pas que la campagne tourne : c'est ce test-ci qui le prouve.
    private _t0 = time;
    waitUntil {
        sleep 2;
        (!isNil "markersX") && {!isNil "sidesX"} && {count (missionNamespace getVariable ["markersX", []]) > 0}
    };
    ("HMT_PRET zones=" + str (count markersX) + " attente=" + str (round (time - _t0)) + "s") call HMT_OUT;

    // INVENTAIRE FIXE — la geometrie de la campagne, emise une fois.
    {
        private _p = getMarkerPos _x;
        ("A3A_LIEU|" + _x + "|" + (markerType _x) + "|"
            + str (round (_p select 0)) + "|" + str (round (_p select 1))) call HMT_OUT;
    } forEach markersX;
    ("A3A_LIEU_FIN|" + str (count markersX)) call HMT_OUT;

    // RELEVE PERIODIQUE — l'etat brut, sans resume.
    while {true} do {
        private _hr    = server getVariable ["hr", -1];
        private _res   = server getVariable ["resourcesFIA", -1];
        private _tier  = missionNamespace getVariable ["tierWar", -1];
        private _aggO  = missionNamespace getVariable ["aggressionLevelOccupants", -1];
        private _aggI  = missionNamespace getVariable ["aggressionLevelInvaders", -1];
        private _supp  = missionNamespace getVariable ["supportPoints", -1];
        private _skill = missionNamespace getVariable ["skillFIA", -1];

        ("A3A_ETAT|t=" + str (round time)
            + "|date=" + str date
            + "|hr=" + str _hr
            + "|argent=" + str _res
            + "|tier=" + str _tier
            + "|aggOcc=" + str _aggO
            + "|aggInv=" + str _aggI
            + "|soutien=" + str _supp
            + "|compFIA=" + str _skill
            + "|unites=" + str (count allUnits)
            + "|groupes=" + str (count allGroups)) call HMT_OUT;

        // PROPRIETE DES ZONES — qui tient quoi, en une ligne.
        private _z = [];
        {
            private _s = sidesX getVariable [_x, sideUnknown];
            _z pushBack (_x + "=" + (str _s));
        } forEach markersX;
        ("A3A_ZONES|" + (_z joinString ",")) call HMT_OUT;

        sleep HMT_PERIODE;
    };
};
