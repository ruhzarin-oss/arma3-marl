// init.sqf — mission AGENT-READY côté serveur.
//  1) sonde de démarrage   2) pont d'actuation (exécute les commandes Python)
//  3) heartbeat / émission d'état (pont OUT vers le store)
diag_log "HARMATTAN_INIT init.sqf demarre cote serveur";

// --- pont IN : l'actuateur lit les cmd_N.sqf écrits par arma_actuate.py et les exécute ---
call compile preprocessFileLineNumbers "harmattan_actuator.sqf";
private _hmtv = "hmt_native" callExtension "version";
if (_hmtv != "") then {
    diag_log format ["HARMATTAN_EXT %1 -> actuateur natif TCP actif EN PLUS du fichier", _hmtv];
    call compile preprocessFileLineNumbers "harmattan_actuator_native.sqf";
} else {
    diag_log "HARMATTAN_EXT absente -> actuateur fichier seul";
};

// --- pont OUT : heartbeat + émission d'événements d'état ---
[] spawn {
    private _i = 0;
    while {true} do {
        _i = _i + 1;
        private _json = format [
            "{""scenario"":""agent"",""id"":%1,""kind"":""HEARTBEAT"",""t"":""sim"",""desc"":""monde vivant, tick %1"",""actors"":[],""truth"":""true""}",
            _i
        ];
        diag_log format ["HARMATTAN %1", _json];
        sleep 10;
    };
};
