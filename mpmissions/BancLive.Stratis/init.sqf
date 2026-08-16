// init.sqf — mission AGENT-READY côté serveur.
//  1) sonde de démarrage   2) pont d'actuation (exécute les commandes Python)
//  3) heartbeat / émission d'état (pont OUT vers le store)
diag_log "HARMATTAN_INIT init.sqf demarre cote serveur";

// --- pont IN : l'actuateur lit les cmd_N.sqf écrits par arma_actuate.py et les exécute ---
// ATTENTION : ACTUATEUR FICHIER DESACTIVE SUR CE BANC. La mission a ete copiee d un pont
// qui avait tourne : son repertoire hmt_bridge/ portait une file de cmd_N.sqf herites,
// rejoues au demarrage — dont un cmd_3 casse, et une attente infinie sur un cmd_221
// inexistant. Le compteur est monotone et ne se remet pas a zero tout seul.
// Ce banc n utilise QUE le pont TCP natif.
// call compile preprocessFileLineNumbers "harmattan_actuator.sqf";
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
