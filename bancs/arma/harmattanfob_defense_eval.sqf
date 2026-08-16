// vague 3 : defense etendue + evaluation + nettoyage
HMT_ALERT = 0;

// --- ALERTE : un contact reveille les bases proches (budget actif), le reste reste gele ---
[] spawn {
    while { true } do {
        sleep 6;
        private _host = allUnits select { (side _x != east) && (side _x != civilian) && alive _x && (east knowsAbout _x > 1) };
        if (count _host > 0) then {
            HMT_ALERT = 100;
            {
                private _h = _x;
                { if (!isNull _x && { !isNull (leader _x) } && { (leader _x) distance _h < 900 }) then { _x enableDynamicSimulation false; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; }; } forEach HMT_FOB_GRP;
            } forEach _host;
        } else {
            HMT_ALERT = (HMT_ALERT - 3) max 0;
        };
    };
};

// --- EVALUATION : intrus, detection, etat des cibles ---
[] spawn {
    sleep 15;
    while { true } do {
        sleep 20;
        private _hh = allUnits select { (side _x != east) && (side _x != civilian) };
        private _intrus = count (_hh select { alive _x });
        private _det = count (_hh select { alive _x && (east knowsAbout _x > 1) });
        private _ciblesOK = count (HMT_TARGETS select { private _o = _x select 1; !isNull _o && { alive _o } });
        if (_intrus > 0 || HMT_ALERT > 0) then {
            diag_log format ["HARMATTAN_EVAL intrus=%1 detectes=%2 cibles_intactes=%3/%4 alerte=%5 fps=%6", _intrus, _det, _ciblesOK, count HMT_TARGETS, HMT_ALERT, round diag_fps];
        };
    };
};

// --- NETTOYAGE memoire (cadavres + groupes vides) -> recupere des FPS ---
[] spawn {
    while { true } do {
        sleep 120;
        private _n = count allDead;
        { deleteVehicle _x; } forEach allDead;
        { if (!isNull _x && { count units _x == 0 } && { _x != grpNull }) then { deleteGroup _x; }; } forEach allGroups;
        diag_log format ["HARMATTAN_CLEAN morts_supprimes=%1 groupes=%2 fps=%3", _n, count allGroups, round diag_fps];
    };
};

diag_log "HARMATTAN_DEFEVAL defense+eval+cleanup ON";
