// harmattan_actuator.sqf — côté IN-GAME du pont d'actuation.
// Boucle serveur : lit les cmd_N.sqf écrits par Python (arma_actuate.py) et les exécute.
// À charger depuis init.sqf :  call compile preprocessFileLineNumbers "harmattan_actuator.sqf";
//
// Le dossier hmt_bridge est sous le dossier serveur (lisible par preprocessFile).
// Nom de fichier incrémenté = contourne le cache de fichiers d'Arma.

HMT_BRIDGE = "hmt_bridge";   // = <serveur>/hmt_bridge/  (où Python écrit)
HMT_n = 0;

[] spawn {
    diag_log "HARMATTAN_ACTUATOR boucle d'actuation demarree";
    while {true} do {
        private _next = HMT_n + 1;
        private _file = format ["%1\cmd_%2.sqf", HMT_BRIDGE, _next];
        // preprocessFile renvoie "" si le fichier n'existe pas encore (pas d'arrêt).
        private _code = preprocessFileLineNumbers _file;
        if (_code != "") then {
            diag_log format ["HARMATTAN_RECV cmd %1", _next];
            private _ok = [_code] call {
                params ["_c"];
                private _r = call compile _c;   // exécute le SQF généré par Python
                true
            };
            HMT_n = _next;
        };
        sleep 0.3;   // cadence de polling (raffinable ; prod = callExtension sans polling)
    };
};
