// harmattan_actuator_ext.sqf — actuateur PONT-SOCKET (client SOLO/host, contourne le gel d'index).
// Différence avec harmattan_actuator.sqf (voie dédié) : on remplace
//   preprocessFileLineNumbers "<bridge>/cmd_N.sqf"      (gelé en solo)
// par
//   "hmt_ext" callExtension (str N)                     (lit le fichier au niveau OS via la DLL)
// L'OUT (obs) reste inchangé : diag_log "HARMATTAN_*" -> RPT (fonctionne en solo).
//
// À charger depuis l'init.sqf de la mission cliente :
//   call compile preprocessFileLineNumbers "harmattan_actuator_ext.sqf";
// (preprocessFile sur CE fichier-ci est OK : il existe au lancement ; seul l'ajout APRÈS coup gèle.)

HMT_n = 0;

[] spawn {
    diag_log "HARMATTAN_ACTUATOR (socket/callExtension) demarree";
    // sanity-check : la DLL répond-elle ?
    diag_log format ["HARMATTAN_EXT version=%1", ("hmt_ext" callExtension "version")];
    while {true} do {
        private _next = HMT_n + 1;
        private _code = "hmt_ext" callExtension (str _next);   // "" si cmd_N pas encore écrite
        if (_code != "") then {
            diag_log format ["HARMATTAN_RECV cmd %1", _next];
            call compile _code;     // exécute le SQF généré par Python
            HMT_n = _next;
        };
        sleep 0.2;
    };
};
