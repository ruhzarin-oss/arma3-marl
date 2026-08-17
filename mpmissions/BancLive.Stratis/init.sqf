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
// REVUE 17/08 : la porte etait `_hmtv != ""`. Or l extension repond a « version » depuis
// la memoire MEME quand le listener n a pas pu prendre le port (serveur zombie) : la porte
// etait donc VERTE sur un pont mort. On exige desormais le mot « ecoute », que la version
// 1.2 de l extension n emet qu apres un bind() reussi.
// Et le message d echec annoncait « actuateur fichier seul » alors que l actuateur fichier
// est commente ci-dessus : AUCUN actuateur n etait charge, et le journal accusait un mode
// de repli qui n existe pas.
if (_hmtv find "ecoute" >= 0) then {
    diag_log format ["HARMATTAN_EXT %1 -> actuateur natif TCP actif, socket CONFIRMEE", _hmtv];
    call compile preprocessFileLineNumbers "harmattan_actuator_native.sqf";
} else {
    if (_hmtv != "") then {
        // L extension repond mais ne sait pas dire si son listener a pris le port :
        // c est une version ANTERIEURE a 1.2. On charge quand meme — sinon ce
        // correctif casserait le banc — mais on le DIT, fort, a chaque demarrage.
        diag_log format ["HARMATTAN_EXT %1 : version < 1.2, elle NE PEUT PAS prouver que son socket est ouvert. Un serveur zombie sur le port rendrait ce demarrage VERT et le pont MUET. Recompiler socket_bridge/hmt_native.c.", _hmtv];
        call compile preprocessFileLineNumbers "harmattan_actuator_native.sqf";
    } else {
        diag_log "HARMATTAN_EXT ABSENTE -> AUCUN actuateur charge : la mission ne recevra RIEN (l actuateur fichier est commente ci-dessus)";
    };
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
