// fiabilite_verdict.sqf — LE MEME MATCH, REJOUE TRENTE FOIS.
//
// Pourquoi. Tout ce qu on batit herite de la definition du verdict : le corpus, l experience
// bi-axe contre mono-axe, et demain le signal d entrainement. Si l issue d un accrochage est un
// tirage au sort deguise, on apprendra du BRUIT a l agent — avec une conviction totale, puisque
// les chiffres auront l air propres.
//
// Le geste est le meme que celui du monde jouet cet apres-midi : avant de croire un instrument,
// lui faire mesurer une chose dont on connait deja la reponse. Ici la chose connue est
// l invariance : le meme accrochage doit rendre le meme verdict.
//
// On fige TOUT ce qu on peut figer — le point, le nombre de defenseurs et d assaillants, les
// azimuts, la distance, les competences — et on ne laisse varier que ce que le moteur tire
// lui-meme : les balles, les reactions, les chemins. Puis on compte les bascules.
//
// Appel : [<repetitions>] execVM "capture\fiabilite_verdict.sqf";

params [["_reps", 30]];
if (!isServer) exitWith {};
HMT_FIAB_VERSION = 1;

// --- L ACCROCHAGE FIGE. Valeurs au centre de la distribution du generateur, pas aux extremes :
//     on veut la fiabilite du cas TYPIQUE, pas d un cas facile ou desespere.
HMT_FIAB = [
    3253, 2984,      // point : FOB Maxwell sur Stratis, un bati dense et connu
    5,               // defenseurs
    6,               // assaillants
    // RAPPORT 1,20 : LA FRONTIERE, mesuree sur les 79 accrochages propres deja collectes.
    // Taux de prise par bande : 1,0-1,4 -> 44,4 % | 1,4-1,7 -> 63,6 % | 1,7-2,0 -> 78,6 %.
    // Premiere version fautive : j avais fige a 2 contre 1, en pleine zone ou le defenseur perd
    // trois fois sur quatre. Mesurer la fiabilite d un verdict la ou l issue est desequilibree ne
    // prouve rien — bien sur qu il est stable si le meme camp gagne toujours. Le seul endroit ou
    // le hasard peut faire basculer, et donc le seul ou la mesure a un sens, est la frontiere.
    // C est aussi la zone ou un agent devra faire la difference.
    300,             // distance de depart
    0,               // azimut du premier axe
    100,             // ecart entre les deux axes
    0.5              // competence, identique pour tous : une variable de moins
];

[_reps] spawn {
    params ["_reps"];
    HMT_FIAB params ["_px", "_py", "_nDef", "_nAtt", "_dist", "_az1", "_ecart", "_skill"];
    private _pt = [_px, _py, 0];
    private _rTenue = 50; private _tenueRequise = 60; private _dureeMax = 600;

    (format ["HMT|F|debut|%1|%2|%3|%4|%5|%6|%7", _reps, _nDef, _nAtt, _dist,
             _az1, _ecart, _skill]) call HMT_LOG;

    for "_rep" from 1 to _reps do {
        private _tous = [];
        private _gDef = createGroup east;
        private _bats = nearestTerrainObjects [_pt, ["HOUSE", "BUILDING", "RUIN"], 120, false, true];
        private _places = [];
        { _places append (_x buildingPos -1) } forEach _bats;
        // PAS de melange aleatoire des places : on veut la MEME garnison a chaque rejeu.
        for "_i" from 1 to _nDef do {
            private _t = if (_i == 1) then {"O_Soldier_AR_F"} else {"O_Soldier_F"};
            private _u = _gDef createUnit [_t, _pt, [], 0, "CAN_COLLIDE"];
            private _q = if (_i - 1 < count _places) then { _places select (_i - 1) }
                         else { [_px + 15 * _i, _py, 0] };
            _u setPosATL _q; _u setSkill _skill;
            _u setBehaviour "COMBAT"; _u setCombatMode "RED";
            _u addMagazines ["SmokeShell", 2];
            _tous pushBack _u;
        };
        if (!isNil "lambs_wp_fnc_taskGarrison") then {
            [_gDef, _pt, 60, [], true, true] call lambs_wp_fnc_taskGarrison;
        };

        private _gs = [];
        {
            private _az = _x;
            private _pa = [_px + _dist * sin _az, _py + _dist * cos _az, 0];
            private _g = createGroup west;
            private _n2 = round (_nAtt / 2);
            for "_i" from 1 to _n2 do {
                private _t = if (_i == 1) then {"B_Soldier_AR_F"} else {"B_Soldier_F"};
                private _u = _g createUnit [_t, _pa, [], 0, "CAN_COLLIDE"];
                // positions DETERMINISTES autour du point de depart
                _u setPosATL [(_pa select 0) + 8 * (_i - _n2 / 2), (_pa select 1), 0];
                _u setSkill _skill;
                _u setBehaviour "COMBAT"; _u setCombatMode "RED";
                _u addMagazines ["SmokeShell", 3];
                _tous pushBack _u;
            };
            _g move _pt;
            _gs pushBack _g;
        } forEach [_az1, _az1 + _ecart];

        // --- meme boucle de verdict que le generateur, a l identique ---
        private _t0 = time; private _tenu = -1; private _depuis = time; private _dmin = 9999;
        private _cause = ""; private _vainqueur = -1;
        while { _cause == "" } do {
            sleep 5;
            private _viv = _tous select { alive _x };
            private _e = _viv select { side _x == east };
            private _o = _viv select { side _x == west };
            { private _a = _x; { private _d = _a distance2D _x; if (_d < _dmin) then { _dmin = _d } } forEach _e } forEach _o;
            private _q = -1;
            private _dedans = _viv select { (_x distance2D _pt) < _rTenue };
            private _ce = count (_dedans select { side _x == east });
            private _co = count (_dedans select { side _x == west });
            if (_ce > 0 && _co == 0) then { _q = 0 };
            if (_co > 0 && _ce == 0) then { _q = 1 };
            if (_q != _tenu) then { _tenu = _q; _depuis = time };
            private _acquis = (_tenu >= 0) && ((time - _depuis) >= _tenueRequise);
            if (count _e == 0) then { _cause = "elimination"; _vainqueur = 1 };
            if (count _o == 0 && _cause == "") then { _cause = "elimination"; _vainqueur = 0 };
            if (_cause == "" && _acquis && _tenu == 1) then { _cause = "prise"; _vainqueur = 1 };
            if (_cause == "" && (time - _t0 > _dureeMax)) then { _cause = "chrono"; _vainqueur = 0 };
        };
        (format ["HMT|F|rejeu|%1|%2|%3|%4|%5|%6|%7", _rep, _cause, _vainqueur,
                 round (time - _t0), round _dmin, count (_tous select { alive _x && side _x == east }),
                 count (_tous select { alive _x && side _x == west })]) call HMT_LOG;
        { if (!isNull _x) then { deleteVehicle _x } } forEach _tous;
        sleep 3;
    };
    "HMT|F|fin" call HMT_LOG;
};
"HMT|OK|fiabilite|1" call HMT_LOG;
