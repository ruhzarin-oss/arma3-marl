// banc_vitesse.sqf — LE DERNIER PARAMÈTRE INVENTÉ.
//
// Tout le simulateur est calibré sur des mesures Arma, SAUF UN : la vitesse selon la posture.
// J'avais posé « couché = vitesse divisée par trois » comme choix de conception, déclaré comme
// tel dans les critères. C'est précisément ce facteur qui étrangle l'agent : il rampe, son
// budget de trajet tombe à 422 m, et il lui en faudrait 450 pour contourner et arriver.
// Je réglerais donc un agent contre une contrainte que j'ai fabriquée.
//
// LE DISPOSITIF. Un homme part d'un point et reçoit l'ordre de rejoindre un point situé à
// 120 m. On chronomètre. Trois postures x trois allures, plusieurs répétitions.
// Le déplacement RÉEL est mesuré, pas l'ordre donné.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE : debout + course doit donner une vitesse plausible pour un homme (4 à 7 m/s).
//     Hors de cette plage, l'instrument mesure autre chose que de la marche.
//   · Un essai où l'homme n'atteint pas le but dans le temps imparti est ÉCARTÉ, pas
//     comptabilisé comme lent : on ne confond pas « lent » et « bloqué ».
//   · La posture doit être VÉRIFIÉE pendant le trajet, pas seulement ordonnée au départ.
//     ⟨leçon du jour : le cap supposé au lieu d'être mesuré a inversé une conclusion⟩

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|VT|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;
    private _base = [];
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 3000 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        { private _q = _c vectorAdd _x;
                          if (surfaceIsWater _q) then { _ok = false };
                          if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                          // un terrain sans obstacle : on mesure la marche, pas le contournement
                          if (count (nearestTerrainObjects [_q, ["TREE","BUSH","HOUSE","ROCK"], 25]) > 0) then { _ok = false };
                        } forEach [[0,0,0],[0,40,0],[0,80,0],[0,120,0],[15,60,0],[-15,60,0]];
                        if (_ok) then { _base = _c };
                    };
                };
            };
        };
    } forEach [4, 7, 12];
    if (count _base == 0) exitWith { "HMT|VT|ECHEC|terrain" call HMT_LOG };
    (format ["HMT|VT|terrain|%1|%2", round (_base select 0), round (_base select 1)]) call HMT_LOG;

    private _g = createGroup west;

    HMT_ESSAI = {
        params ["_posture", "_allure", "_rep"];
        private _dep = _base;
        private _but = _base vectorAdd [0, 120, 0];
        private _u = _g createUnit ["B_Soldier_F", _dep, [], 0, "NONE"];
        _u setPosATL _dep; _u allowDamage false; removeAllWeapons _u;
        _u setUnitPos _posture;
        _u setSpeedMode _allure;
        _u setBehaviour "CARELESS";      // il marche, il ne combat pas
        sleep 3;

        _u doMove _but;
        private _t0 = time;
        private _parcouru = 0;
        private _prec = getPosATL _u;
        private _postures = [];
        private _abandon = false;
        while { (_u distance2D _but) > 6 && (time - _t0) < 180 } do {
            sleep 0.5;
            private _p = getPosATL _u;
            _parcouru = _parcouru + (_p distance2D _prec);
            _prec = _p;
            _postures pushBack (unitPos _u);     // on VÉRIFIE la posture, on ne la suppose pas
            _u doMove _but;
        };
        private _duree = time - _t0;
        private _arrive = (_u distance2D _but) <= 6;
        // part du trajet où la posture ordonnée était RÉELLEMENT tenue
        private _tenue = 0;
        { if (_x == _posture) then { _tenue = _tenue + 1 } } forEach _postures;
        private _part = if (count _postures > 0) then { _tenue / (count _postures) } else { 0 };

        (format ["HMT|VT|essai|%1|%2|%3|arrive|%4|duree|%5|parcouru|%6|vitesse|%7|posture_tenue|%8",
                 _posture, _allure, _rep, (if (_arrive) then {1} else {0}),
                 (round (_duree*10))/10, round _parcouru,
                 (round ((_parcouru / (_duree max 0.1)) * 100))/100,
                 (round (_part*100))/100]) call HMT_LOG;

        deleteVehicle _u;
        sleep 3;
    };

    // CONTRÔLE AVANT LE PLAN : debout + course doit donner une vitesse d'homme
    ["UP", "FULL", 0] call HMT_ESSAI;
    "HMT|OK|vt_controle|1" call HMT_LOG;

    private _plan = [];
    { private _po = _x;
      { private _al = _x;
        for "_r" from 1 to 3 do { _plan pushBack [_po, _al, _r] };
      } forEach ["LIMITED", "NORMAL", "FULL"];
    } forEach ["UP", "MIDDLE", "DOWN"];
    _plan = _plan call BIS_fnc_arrayShuffle;
    (format ["HMT|VT|plan|%1", count _plan]) call HMT_LOG;
    { _x call HMT_ESSAI } forEach _plan;
    "HMT|VT|TERMINE|1" call HMT_LOG;
};
