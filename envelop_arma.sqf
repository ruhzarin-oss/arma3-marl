// envelop_arma.sqf — ACTUATEUR du DÉBORDEMENT scripté. Chaque soldat doMove vers SON point (ligne de feu OU flanc),
// et engage (doTarget/doSuppressiveFire) l'ennemi le plus proche s'il a le feu vert. Le CORPS exécute, déterministe.
// Dépend de HMT_WPILOT + HMT_WNEAR (posés par HMT_SHAMAL_SENSE de shamal_obs.sqf).
// Python fournit chaque tick : HMT_TGTS = [[tx,ty],...] (une cible/soldat) et HMT_FIRE = [0/1,...] (feu si contact).

// ÉCRAN DE FUMÉE : déploie des fumigènes aux positions HMT_SMOKEPOS (nier la détection des défenseurs)
HMT_SMOKE = { { "SmokeShell" createVehicle [(_x select 0), (_x select 1), 0] } forEach HMT_SMOKEPOS; };

// ASSAUT TÉMÉRAIRE (a) : debout + sprint + fonce sur le FOB, écrase l'auto-plat-ventre de l'IA (ré-imposé chaque tick)
HMT_RECKLESS = { { if (alive _x) then { _x setUnitPos "UP"; _x forceSpeed 100; _x doMove [(HMT_FOB select 0), (HMT_FOB select 1), 0]; } } forEach HMT_WPILOT; };

// ACTUATEUR CORPS-FORCÉ : applique HMT_ACTS de la politique mais FORCE le mouvement (override l'auto-plat-ventre d'Arma)
HMT_CORPS_APPLY = {
    {
        private _u = _x; private _i = _forEachIndex;
        if (alive _u && _i < count HMT_ACTS) then {
            private _a = HMT_ACTS select _i;
            if (_a < 8) then {
                private _dir = _a * 45;
                private _tgt = (getPosATL _u) vectorAdd [22 * sin _dir, 22 * cos _dir, 0];
                _u setUnitPos "UP"; _u forceSpeed 100; _u doMove _tgt;
            } else {
                if (_a == 9) then { private _en = HMT_WNEAR select _i; if (!isNull _en) then { _u doTarget _en; _u doSuppressiveFire _en; }; }
                else { if (_a == 10) then { _u setUnitPos "UP" }; if (_a == 11) then { _u setUnitPos "MIDDLE" }; if (_a == 12) then { _u setUnitPos "DOWN" }; };
            };
        };
    } forEach HMT_WPILOT;
};

HMT_ENVELOP_APPLY = {
    {
        private _u = _x; private _i = _forEachIndex;
        if (alive _u && _i < count HMT_TGTS) then {
            private _t = HMT_TGTS select _i;
            _u setUnitPos "AUTO"; _u forceSpeed -1;
            _u doMove [_t select 0, _t select 1, 0];
            if ((_i < count HMT_FIRE) && {(HMT_FIRE select _i) == 1}) then {
                private _en = HMT_WNEAR select _i;
                if (!isNull _en) then { _u doWatch _en; _u doTarget _en; _u doSuppressiveFire _en; };
            };
        };
    } forEach HMT_WPILOT;
};
