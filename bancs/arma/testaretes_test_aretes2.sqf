// test_aretes2.sqf — CONTRÔLE POSITIF v2.
//
// v1 a trouvé deux défauts réels, c'est pour ça qu'on l'avait écrit :
//   · le mur bloque la PERCEPTION (knowsAbout tombe à 0) mais nos deux sondes géométriques
//     le déclarent transparent (los=1, vis=1). Une capture lancée en l'état aurait écrit
//     « à découvert » sur des hommes à l'abri — et la coque de couvert repose sur la même
//     commande.
//   · knowsAbout vaut 2,0 à 300 m en terrain dégagé. La falaise des 100 m est FAUSSE dans
//     ces conditions ; la coupure à 150 m aurait jeté des liens réels.
//
// v2 répond à UNE question : quelle sonde géométrique voit le couvert ?
// On met le mur en travers, on VÉRIFIE qu'il y est, et on tire huit sondes différentes à
// travers lui. Celle qui le voit est celle qu'on câblera.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 8;
    private _base = [1700, 5450, 0];
    (format ["HMT|A|base|%1|%2", _base select 0, _base select 1]) call HMT_LOG;

    private _grpE = createGroup east;
    private _grpW = createGroup west;
    private _A  = _grpE createUnit ["O_Soldier_F", _base, [], 0, "NONE"]; _A setPosATL _base;

    private _posB1 = _base vectorAdd [50, 0, 0];      // dégagé, référence
    private _posB2 = _base vectorAdd [0, -50, 0];     // MUR au milieu
    private _posB3 = _base vectorAdd [0, 300, 0];     // 300 m dégagé
    private _posC1 = _base vectorAdd [-50, 0, 0];     // ami

    private _B1 = _grpW createUnit ["B_Soldier_F", _posB1, [], 0, "NONE"]; _B1 setPosATL _posB1;
    private _B2 = _grpW createUnit ["B_Soldier_F", _posB2, [], 0, "NONE"]; _B2 setPosATL _posB2;
    private _B3 = _grpW createUnit ["B_Soldier_F", _posB3, [], 0, "NONE"]; _B3 setPosATL _posB3;
    private _C1 = _grpE createUnit ["O_Soldier_F", _posC1, [], 0, "NONE"]; _C1 setPosATL _posC1;

    { removeAllWeapons _x; _x allowDamage false; _x disableAI "PATH";
      _x disableAI "AUTOCOMBAT"; _x setBehaviour "COMBAT"; _x setUnitPos "UP";
    } forEach [_A, _B1, _B2, _B3, _C1];
    _A setDir 180;                                     // face à B2

    // ============ LE MUR, ET LA PREUVE QU IL EST EN TRAVERS ============
    // v1 posait le mur et le croyait sur parole. Ici on l ESSAIE dans les deux orientations
    // et on garde celle qui intercepte réellement le segment A→B2, mesurée sans rien ignorer.
    private _milieu = _base vectorAdd [0, -25, 0];
    private _sonde = {                                  // le segment touche-t-il quelque chose ?
        private _r = lineIntersectsSurfaces [
            (ATLToASL (_base vectorAdd [0,0,1.6])),
            (ATLToASL (_milieu vectorAdd [0,0,1.0])),
            objNull, objNull, true, 8, "GEOM", "NONE"];
        count _r
    };

    private _murs = [];
    private _garde = 0;
    {
        private _dir = _x;
        { deleteVehicle _x } forEach _murs; _murs = [];
        {
            private _m = createVehicle ["Land_CncWall4_F", (_milieu vectorAdd [_x, 0, 0]), [], 0, "CAN_COLLIDE"];
            _m setDir _dir;
            _murs pushBack _m;
        } forEach [-8, -4, 0, 4, 8];
        sleep 1;
        private _touche = call _sonde;
        (format ["HMT|A|mur_essai|dir|%1|intersections|%2", _dir, _touche]) call HMT_LOG;
        if (_touche > 0 && _garde == 0) then { _garde = _dir };
    } forEach [90, 0];

    if (_garde == 0) exitWith { "HMT|OK|mur|0|ECHEC|aucune_orientation_intercepte" call HMT_LOG };

    // on repose l orientation retenue
    { deleteVehicle _x } forEach _murs; _murs = [];
    {
        private _m = createVehicle ["Land_CncWall4_F", (_milieu vectorAdd [_x, 0, 0]), [], 0, "CAN_COLLIDE"];
        _m setDir _garde;
        _murs pushBack _m;
    } forEach [-8, -4, 0, 4, 8];
    sleep 1;
    (format ["HMT|OK|mur|1|dir|%1|panneaux|%2|hauteur|%3|intersections|%4", _garde, count _murs,
             (((boundingBoxReal (_murs select 0)) select 1) select 2), call _sonde]) call HMT_LOG;

    // ============ HUIT SONDES, LA MÊME PAIRE ============
    // On cherche laquelle voit le béton. Les LOD ne se valent pas : un objet peut n avoir
    // aucune géométrie de VUE et rester transparent à la sonde qui l interroge.
    HMT_SONDES = {
        params ["_o", "_c"];
        private _r = [];

        // 1-5 : lineIntersectsSurfaces, cinq couples de LOD, yeux -> torse
        {
            private _i = lineIntersectsSurfaces [eyePos _o, aimPos _c, _o, _c, true, 1,
                                                 (_x select 0), (_x select 1)];
            _r pushBack (if (count _i == 0) then {1} else {0});
        } forEach [["VIEW","FIRE"], ["GEOM","NONE"], ["FIRE","NONE"], ["IFIRE","NONE"], ["VIEW","GEOM"]];

        // 6 : lineIntersectsWith — la variante « objets » et non « surfaces »
        _r pushBack (if (count (lineIntersectsWith [eyePos _o, aimPos _c, _o, _c, true]) == 0) then {1} else {0});

        // 7 : checkVisibility depuis les yeux
        _r pushBack (round (([objNull, "VIEW"] checkVisibility [eyePos _o, aimPos _c]) * 100) / 100);

        // 8 : checkVisibility en passant les OBJETS et non des positions
        _r pushBack (round (([_o, "VIEW"] checkVisibility [eyePos _o, aimPos _c]) * 100) / 100);

        _r
    };

    private _noms = [[_B1,"B1_degage_50m"], [_B2,"B2_MUR_50m"], [_B3,"B3_degage_300m"], [_C1,"C1_AMI_50m"]];
    "HMT|OK|scene2|1" call HMT_LOG;

    private _n = 0;
    while { _n < 60 } do {                              // 60 × 2 s = 120 s
        _n = _n + 1;
        private _t = round (time * 10) / 10;
        {
            private _B = _x select 0;
            private _s = [_A, _B] call HMT_SONDES;
            private _tk = _A targetKnowledge _B;
            // « jamais vu » se lit sur le drapeau, pas sur un âge : quand la cible n a jamais
            // été vue, l horodatage vaut 0 et l âge devient le temps mission — un nombre en
            // notation scientifique qui a cassé le lecteur en v1.
            private _vu = if ((count _tk) > 1 && {_tk select 1}) then {1} else {0};
            (format ["HMT|AR2|%1|%2|A|%3|k|%4|vu|%5|s1|%6|s2|%7|s3|%8|s4|%9|s5|%10|s6|%11|s7|%12|s8|%13|host|%14",
                     _n, _t, (_x select 1),
                     (round ((_A knowsAbout _B) * 100) / 100), _vu,
                     (_s select 0), (_s select 1), (_s select 2), (_s select 3),
                     (_s select 4), (_s select 5), (_s select 6), (_s select 7),
                     (if ((side _B) == (side _A)) then {0} else {1})]) call HMT_LOG;
        } forEach _noms;
        sleep 2;
    };
    (format ["HMT|OK|aretes2|1|ticks|%1", _n]) call HMT_LOG;
};
"HMT|OK|test_aretes2|1" call HMT_LOG;
