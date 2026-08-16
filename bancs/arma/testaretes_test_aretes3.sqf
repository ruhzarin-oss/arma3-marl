// test_aretes3.sqf — DIAGNOSTIC GÉOMÉTRIQUE.
//
// v2 : les huit sondes déclarent la vue libre alors que knowsAbout tombe à 0 et que la cible
// n est JAMAIS vue (vu 0 %). Le moteur voit le mur, nos sondes non.
//
// Deux causes possibles, et on ne les départage pas en devinant :
//   (a) la ligne passe AU-DESSUS du mur — pente du terrain, mur de 1,84 m, 50 m de portée
//   (b) les sondes sont mal appelées et le mur leur est réellement transparent
//
// Ici on MESURE : hauteurs du terrain, hauteur des yeux, hauteur de la ligne à l aplomb du
// mur, sommet du mur. Puis on empile jusqu à ce que le mur dépasse la ligne, et on rejoue
// les sondes. Si elles restent aveugles avec un mur qui dépasse de deux mètres, c est (b).

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };

[] spawn {
    sleep 8;
    private _base = [1700, 5450, 0];
    private _milieu = _base vectorAdd [0, -25, 0];
    private _posB2 = _base vectorAdd [0, -50, 0];

    private _grpE = createGroup east;
    private _grpW = createGroup west;
    private _A  = _grpE createUnit ["O_Soldier_F", _base,  [], 0, "NONE"]; _A  setPosATL _base;
    private _B2 = _grpW createUnit ["B_Soldier_F", _posB2, [], 0, "NONE"]; _B2 setPosATL _posB2;
    private _B1 = _grpW createUnit ["B_Soldier_F", (_base vectorAdd [50,0,0]), [], 0, "NONE"];
    _B1 setPosATL (_base vectorAdd [50,0,0]);
    { removeAllWeapons _x; _x allowDamage false; _x disableAI "PATH"; _x disableAI "AUTOCOMBAT";
      _x setBehaviour "COMBAT"; _x setUnitPos "UP" } forEach [_A, _B1, _B2];
    _A setDir 180;
    sleep 3;

    // ---------- LE RELIEF, mesuré et non supposé ----------
    private _hA  = getTerrainHeightASL _base;
    private _hM  = getTerrainHeightASL _milieu;
    private _hB  = getTerrainHeightASL _posB2;
    (format ["HMT|G|terrain|A|%1|mur|%2|B2|%3|denivele_A_M|%4|denivele_A_B|%5",
             (round (_hA*100))/100, (round (_hM*100))/100, (round (_hB*100))/100,
             (round ((_hM-_hA)*100))/100, (round ((_hB-_hA)*100))/100]) call HMT_LOG;

    private _oeil = eyePos _A;                    // ASL
    private _vise = aimPos _B2;                   // ASL
    // hauteur de la ligne de visée à l aplomb du mur : interpolation à mi-parcours
    private _ligneAuMur = ((_oeil select 2) + (_vise select 2)) / 2;
    (format ["HMT|G|ligne|oeil_ASL|%1|vise_ASL|%2|ligne_au_mur_ASL|%3|hauteur_sur_sol_du_mur|%4",
             (round ((_oeil select 2)*100))/100, (round ((_vise select 2)*100))/100,
             (round (_ligneAuMur*100))/100, (round ((_ligneAuMur - _hM)*100))/100]) call HMT_LOG;

    // ---------- ON EMPILE JUSQU À DÉPASSER LA LIGNE ----------
    // Un rang de mur fait ~1,84 m. Il faut que le sommet dépasse la ligne d au moins 1 m.
    private _besoin = (_ligneAuMur - _hM) + 1;
    private _rangs = 1 max (ceil (_besoin / 1.8));
    (format ["HMT|G|besoin|%1|rangs|%2", (round (_besoin*100))/100, _rangs]) call HMT_LOG;

    private _murs = [];
    for "_r" from 0 to (_rangs - 1) do {
        {
            private _p = [ (_milieu select 0) + _x, (_milieu select 1), _r * 1.8 ];
            private _m = createVehicle ["Land_CncWall4_F", [0,0,0], [], 0, "CAN_COLLIDE"];
            _m setDir 90;
            _m setPosATL _p;                       // setPosATL APRÈS setDir, sinon l objet retombe
            _murs pushBack _m;
        } forEach [-8, -4, 0, 4, 8];
    };
    sleep 2;

    // sommet réel du rideau, mesuré sur l objet le plus haut
    private _sommet = 0;
    { private _z = (getPosATL _x select 2) + (((boundingBoxReal _x) select 1) select 2);
      if (_z > _sommet) then { _sommet = _z } } forEach _murs;
    (format ["HMT|G|rideau|panneaux|%1|sommet_sur_sol|%2|ligne_sur_sol|%3|depassement|%4",
             count _murs, (round (_sommet*100))/100,
             (round ((_ligneAuMur - _hM)*100))/100,
             (round ((_sommet - (_ligneAuMur - _hM))*100))/100]) call HMT_LOG;

    // contrôle indépendant : un segment horizontal à hauteur d homme doit toucher le rideau
    private _ctrl = lineIntersectsSurfaces [
        [(_base select 0), (_base select 1), _hA + 1.5],
        [(_posB2 select 0), (_posB2 select 1), _hB + 1.5],
        objNull, objNull, true, 16, "GEOM", "NONE"];
    (format ["HMT|G|controle_segment|intersections|%1", count _ctrl]) call HMT_LOG;

    "HMT|OK|geometrie|1" call HMT_LOG;

    // ---------- LES SONDES, REJOUÉES SUR LE RIDEAU ----------
    HMT_S = {
        params ["_o", "_c"];
        private _r = [];
        {
            private _i = lineIntersectsSurfaces [eyePos _o, aimPos _c, _o, _c, true, 1,
                                                 (_x select 0), (_x select 1)];
            _r pushBack (if (count _i == 0) then {1} else {0});
        } forEach [["VIEW","FIRE"], ["GEOM","NONE"], ["FIRE","NONE"]];
        // sans ignorer aucun objet — c est la seule différence avec la sonde qui MARCHE
        private _j = lineIntersectsSurfaces [eyePos _o, aimPos _c, objNull, objNull, true, 16, "GEOM", "NONE"];
        _r pushBack (if (count _j == 0) then {1} else {0});
        _r pushBack (count _j);
        _r pushBack (round (([objNull, "VIEW"] checkVisibility [eyePos _o, aimPos _c]) * 100) / 100);
        _r
    };

    private _n = 0;
    while { _n < 40 } do {
        _n = _n + 1;
        {
            private _B = _x select 0;
            private _s = [_A, _B] call HMT_S;
            private _tk = _A targetKnowledge _B;
            (format ["HMT|AR3|%1|A|%2|k|%3|vu|%4|viewfire|%5|geom|%6|fire|%7|sansignore|%8|nbinter|%9|checkvis|%10",
                     _n, (_x select 1), (round ((_A knowsAbout _B)*100))/100,
                     (if ((count _tk) > 1 && {_tk select 1}) then {1} else {0}),
                     (_s select 0), (_s select 1), (_s select 2), (_s select 3),
                     (_s select 4), (_s select 5)]) call HMT_LOG;
        } forEach [[_B1,"B1_degage"], [_B2,"B2_RIDEAU"]];
        sleep 2;
    };
    (format ["HMT|OK|aretes3|1|ticks|%1", _n]) call HMT_LOG;
};
"HMT|OK|test_aretes3|1" call HMT_LOG;
