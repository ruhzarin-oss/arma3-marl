// sonde_impact.sqf — LE CAPTEUR D IMPACT VOIT-IL LES BALLES ?
//
// Le banc de l etage 1 rend 37,5 pour cent d essais natifs sans AUCUN impact sur les murets,
// alors que le groupe tire 46 coups en moyenne. Un groupe qui tire 46 coups a pris son ordre.
// Deux explications, et on ne repare pas ce qu on n a pas separe :
//   · les balles partent ailleurs — c est le TIR qui rate ;
//   · les balles arrivent mais le compteur ne les voit pas — c est le CAPTEUR qui est aveugle.
//
// Cette sonde tranche la seconde. Un tireur POSE, une distance CONNUE, un muret en face, et
// l ordre de tirer dessus. Si le compteur `HitPart` ne bouge pas, il est aveugle et tout ce
// qu on a lu sur ce canal ne vaut rien.
//
// ⚠️ CE QUI FERAIT ECHOUER — ecrit avant :
//   · zero coup tire -> ce n est pas le capteur qu on mesure, c est encore l ordre. On le dit.
//   · le tireur ne voit pas le muret -> la pose est mauvaise, on ne conclut rien.
//   · des impacts comptes SANS coup tire -> le compteur invente, ce qui serait pire.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|SI|debut|1" call HMT_LOG;

HMT_BASE = [1734, 5391, 0];
HMT_DIST = [30, 60, 90, 120];   // quatre distances : le capteur peut etre aveugle DE LOIN

[] spawn {
    sleep 25;
    {
        private _d = _x;
        // ─── le muret, avec le MEME compteur que le banc
        private _pm = HMT_BASE vectorAdd [0, 0, 0];
        private _m = createVehicle ["Land_BagFence_Long_F", _pm, [], 0, "CAN_COLLIDE"];
        _m setPosATL _pm; _m setDir 0; _m allowDamage false;
        _m setVariable ["si_touche", 0];
        _m addEventHandler ["HitPart", { private _o = (_this select 0) select 0;
            _o setVariable ["si_touche", (_o getVariable ["si_touche",0]) + 1] }];

        // ─── un tireur, a distance connue, face au muret
        private _g = createGroup east;
        private _pt = HMT_BASE vectorAdd [_d, 0, 0];
        private _u = _g createUnit ["O_Soldier_F", _pt, [], 0, "NONE"];
        _u setPosATL _pt; _u allowDamage false;
        _u disableAI "AUTOCOMBAT"; _u disableAI "FSM"; _u disableAI "AUTOTARGET";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setUnitPos "UP";
        _u setDir (_u getDir _m);
        _u setVariable ["si_n", 0];
        _u addEventHandler ["Fired", { (_this select 0) setVariable ["si_n",
            ((_this select 0) getVariable ["si_n",0]) + 1] }];
        _u addEventHandler ["Fired", { (_this select 0) setVehicleAmmo 1 }];   // lint:ok
        _u setVehicleAmmo 1;                                                   // lint:ok
        sleep 3;

        private _vue = [objNull, "VIEW"] checkVisibility [eyePos _u, getPosASL _m];
        private _t0 = time;
        while { time - _t0 < 30 } do {
            _u doWatch _m; _u doTarget _m; _u doSuppressiveFire _m;
            sleep 3;
        };
        (format ["HMT|SI|MESURE|%1|coups|%2|impacts|%3|vue|%4", _d,
                 _u getVariable ["si_n", 0], _m getVariable ["si_touche", 0],
                 (round (_vue * 100)) / 100]) call HMT_LOG;
        { deleteVehicle _x } forEach [_u, _m];
        sleep 2;
        if (count (units _g) == 0) then { deleteGroup _g };
    } forEach HMT_DIST;
    "HMT|SI|TERMINE|1" call HMT_LOG;
};
