// smoke_v10.sqf — PROUVER que les deux réparations sont actives, avant tout run coûteux.
//
// RÉPARATION 1 : le tireur des impacts. Mesuré le 03/08 : le champ « tireur » de l'événement
// d'impact arrive VIDE dans 85 % des cas. On marque désormais le PROJECTILE au départ du coup.
//   CE QUI PROUVE LA RÉPARATION : sur des impacts réels, la part d'impacts attribués doit
//   passer nettement au-dessus de 15 %. En dessous de 50 %, la réparation ne marche pas.
//
// RÉPARATION 2 : le garde-fou des nœuds. Il n'en avait aucun — 8 ms à 150 hommes, 18,6 à 250.
//   CE QUI PROUVE LA RÉPARATION : sous forte densité, la cadence doit s'espacer d'elle-même
//   et le journaliser. Si le coût dépasse le budget sans qu'aucun ajustement n'apparaisse,
//   le garde-fou est mort.
//
// CONTRÔLE DE PRÉSENCE : il doit y avoir des impacts. Zéro impact rendrait le test muet.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 15;
    [0, 0.2] execVM "hmt_capture.sqf";
    sleep 10;

    private _base = [1700, 5450, 0];
    private _gA = createGroup east; private _gB = createGroup west;

    // deux camps ARMÉS et face à face : on veut de vrais impacts, pas de la perception
    for "_i" from 0 to 11 do {
        private _p = _base vectorAdd [(_i % 6) * 6 - 15, -30 - (floor (_i/6)) * 5, 0];
        private _u = _gA createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setSkill 1;
    };
    for "_i" from 0 to 11 do {
        private _p = _base vectorAdd [(_i % 6) * 6 - 15, 30 + (floor (_i/6)) * 5, 0];
        private _u = _gB createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setSkill 1;
    };
    (format ["HMT|SM|combattants|%1", count allUnits]) call HMT_LOG;

    // ---- densité, pour éprouver le garde-fou des nœuds ----
    sleep 60;
    private _g = createGroup resistance;
    for "_i" from 0 to 239 do {
        private _p = _base vectorAdd [(random 600) - 300, (random 600) - 300, 0];
        private _u = _g createUnit ["I_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u allowDamage false;
    };
    (format ["HMT|SM|densite|%1", count allUnits]) call HMT_LOG;
    sleep 180;
    "HMT|SM|FIN" call HMT_LOG;
};
