// human_state.sqf — fonction HMT_HUMAN : emet l'etat du JOUEUR (slot WEST attaquant) pour le recorder.
// Lu via le pont FICHIER (diag_log -> .out). Action = vitesse ; obs reconstruite offline depuis pos+ennemis.
HMT_HUMAN = {
    private _pl = allUnits select { isPlayer _x };
    if (count _pl == 0) exitWith { diag_log "HARMATTAN_HUM NONE"; };
    private _u = _pl select 0;
    private _p = getPosATL _u; private _v = velocity _u;
    private _en = (allUnits select { side _x == east && alive _x && (_u distance _x < 350) }) apply { [round ((getPosATL _x) select 0), round ((getPosATL _x) select 1)] };
    private _st = ["STAND","CROUCH","PRONE"] find (stance _u);
    diag_log format ["HARMATTAN_HUM x=%1 y=%2 vx=%3 vy=%4 dir=%5 st=%6 alive=%7 side=%8 en=%9",
        round (_p select 0), round (_p select 1),
        (round ((_v select 0) * 100)) / 100, (round ((_v select 1) * 100)) / 100,
        round (getDir _u), _st, [0,1] select (alive _u), str (side _u), _en];
};
diag_log "HARMATTAN_HUMAN fn chargee";
