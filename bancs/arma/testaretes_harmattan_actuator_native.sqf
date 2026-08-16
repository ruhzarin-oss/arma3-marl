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
            "hmt_native" callExtension ("o|HARMATTAN_RECV cmd " + str _next);
            call compile _acc;
            HMT_NN = _next;
        } else { sleep 0.1; };
    };
};
