// harmattan_actuator.sqf — boucle d'actuation DURCIE (ne se bloque JAMAIS).
// Lit les cmd_N.sqf ecrits par Python et les execute, dans l'ordre, sans rejeu (numero monotone).
// A charger depuis init.sqf : call compile preprocessFileLineNumbers "harmattan_actuator.sqf";
//
// DURCISSEMENTS vs version d'origine :
//  1) HMT_n avance AVANT l'execution  -> un SQF qui erre ne fige plus la numerotation.
//  2) chaque commande s'execute dans un THREAD ISOLE (_code spawn) -> une erreur SQF ne tue plus la boucle.
HMT_BRIDGE = "hmt_bridge";   // = <serveur>/hmt_bridge/  (ou Python ecrit)
HMT_n = 0;

[] spawn {
    diag_log "HARMATTAN_ACTUATOR boucle d'actuation demarree";
    while {true} do {
        private _next = HMT_n + 1;
        private _file = format ["%1\cmd_%2.sqf", HMT_BRIDGE, _next];
        private _code = preprocessFileLineNumbers _file;   // "" si pas encore ecrit
        if (_code != "") then {
            diag_log format ["HARMATTAN_RECV cmd %1", _next];
            HMT_n = _next;                                  // (1) avance AVANT exec -> jamais fige
            _code spawn { call compile _this };             // (2) exec ISOLEE -> erreur n'affecte pas la boucle
        };
        sleep 0.2;
    };
};
