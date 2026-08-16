// supp_probe.sqf — SONDE DE SUPPRESSION (réflexion Fable). Mesure si le feu de la base WEST dégrade le TIR des défenseurs.
// Les deux camps sont IMMORTELS -> on isole la SUPPRESSION (les défenseurs tirent-ils moins sous le feu ?) de l'ATTRITION.
// Compteur de tirs EAST via event handler "Fired". HMT_EAST + HMT_WPILOT posés par les spawns.

HMT_SUPP_SETUP = {
    HMT_ESHOTS = 0;
    { if (!isNull _x) then { _x allowDamage false; _x addEventHandler ["Fired", { HMT_ESHOTS = HMT_ESHOTS + 1 }]; } } forEach HMT_EAST;
    { if (!isNull _x) then { _x allowDamage false; } } forEach HMT_WPILOT;   // WEST immortel = appât stable
    // révèle mutuellement (les défenseurs doivent VOIR la base de feu pour lui tirer dessus)
    { private _e=_x; { _e reveal [_x,4] } forEach HMT_WPILOT } forEach HMT_EAST;
    { private _w=_x; { _w reveal [_x,4] } forEach HMT_EAST } forEach HMT_WPILOT;
    (format ["HARMATTAN_SUPPSET east=%1 west=%2", count HMT_EAST, count HMT_WPILOT]) call HMT_EMIT;
};

// PHASE A : WEST TIENT LE FEU (armes bleues) -> les défenseurs tirent librement = baseline
HMT_SUPP_HOLD = { { if (alive _x) then { _x setCombatMode "BLUE"; _x doWatch objNull; } } forEach HMT_WPILOT; };

// PHASE B : WEST SUPPRIME le FOB (tir nourri vers la position tenue)
HMT_SUPP_FIRE = {
    private _p = [HMT_FOB select 0, HMT_FOB select 1, 1];
    { if (alive _x) then { _x setCombatMode "RED"; _x setUnitPos "MIDDLE"; _x doSuppressiveFire _p; } } forEach HMT_WPILOT;
};

// CAPTEUR : tirs EAST cumulés + effectifs vivants
HMT_SUPP_SENSE = { (format ["HARMATTAN_SUPP %1 %2 %3", HMT_ESHOTS, count (HMT_EAST select {alive _x}), count (HMT_WPILOT select {alive _x})]) call HMT_EMIT; };
