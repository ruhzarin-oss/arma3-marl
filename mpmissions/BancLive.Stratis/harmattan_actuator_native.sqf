// harmattan_actuator_native.sqf — actuateur PONT NATIF TCP (serveur dédié Linux, hmt_native_x64.so).
// IN  : poll "p|<n>" -> chunks "M|.."/"D|.." reassembles puis call compile.
// OUT : ack et obs partent par "o|<ligne>" -> TCP -> Python (plus de diag_log/RPT a parser).
HMT_NN = 0;
[] spawn {
    diag_log "HARMATTAN_ACTUATOR (native/TCP) demarree";
    "hmt_native" callExtension "o|HARMATTAN_ACTUATOR (native/TCP) demarree";
    while {true} do {
        private _next = HMT_NN + 1;
        private _acc = ""; private _go = true; private _done = false;
        while {_go} do {
            private _r = "hmt_native" callExtension ("p|" + str _next);
            if (_r == "") then { _go = false }
            else {
                _acc = _acc + (_r select [2]);
                if ((_r select [0, 2]) == "D|") then { _go = false; _done = true; };
            };
        };
        if (_done) then {
            // REVUE 17/08 : DURCISSEMENT restaure depuis harmattan_actuator.sqf, que la
            // voie native avait perdu. (1) le compteur avance AVANT l execution, donc un
            // SQF qui erre ne fige plus la numerotation ; (2) l execution part dans un
            // THREAD ISOLE, donc une erreur ne tue plus la boucle — le pont devenait MUET
            // apres 20-40 min ; (3) HARMATTAN_EXEC prouve l EXECUTION, la ou HARMATTAN_RECV
            // ne prouvait que la reception.
            "hmt_native" callExtension ("o|HARMATTAN_RECV cmd " + str _next);
            HMT_NN = _next;
            [_acc, _next] spawn {
                params ["_code", "_n"];
                call compile _code;
                "hmt_native" callExtension ("o|HARMATTAN_EXEC cmd " + str _n);
            };
        } else { sleep 0.1; };
    };
};
