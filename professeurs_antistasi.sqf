// professeurs_antistasi.sqf — TROIS PROFESSEURS REPRIS D'ANTISTASI ULTIMATE, PORTÉS AUTONOMES.
//
// ⟨Younes, 08/08, a envoyé le dépôt. J'avais répondu « pas maintenant » ; en allant lire, j'ai
//  trouvé nos gestes n°3 et n°5 déjà écrits, et une commande du moteur que j'ignorais.⟩
//
// ⟨Fable, 08/08⟩ « On reprend les professeurs — et ils passent exactement les mêmes portes, ni
// plus ni moins. Le tribunal se moque de la provenance. Un professeur n'est ni des nôtres ni
// des leurs : il est CERTIFIÉ ou pas, par la PORTE 0 du lieu, ses 10 points contre le témoin.
// Quatorze mille commits ne valent pas une exemption, et n'appellent pas non plus un soupçon
// spécial : la porte est le soupçon, pour tout le monde. »
//
// ═══════════════════════════════════════════════════════════════════════════════════════════
// PROVENANCE ET LICENCE — vérifiées sur pièces avant d'en reprendre une ligne.
//   Source : github.com/Antistasi-Ultimate-Community/A3-Antistasi-Ultimate, branche unstable.
//   Fichiers : core/functions/AI/{fn_coverage, fn_unitGetToCover, fn_doFlank, fn_canFight}.sqf
//   Licence  : MIT — usage, modification et vente autorisés, notice à conserver.
//
//   MIT License · Copyright (c) 2023 Antistasi Ultimate Team
//   Permission is hereby granted, free of charge, to any person obtaining a copy of this
//   software and associated documentation files (the "Software"), to deal in the Software
//   without restriction, including without limitation the rights to use, copy, modify, merge,
//   publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
//   to whom the Software is furnished to do so, subject to the following conditions:
//   The above copyright notice and this permission notice shall be included in all copies or
//   substantial portions of the Software.
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
// ═══════════════════════════════════════════════════════════════════════════════════════════
//
// CE QUI A ÉTÉ COUPÉ, ET POURQUOI — un professeur doit tourner SEUL chez nous :
//   · `A3A_fnc_canFight` lisait des variables de leur framework (`incapacitated`,
//     `surrendered`) : remplacé par vivant + non capturé, qui est tout ce dont on dispose.
//   · `A3A_fnc_recallGroup` rappelait le groupe dans leur logique de campagne : remplacé par
//     un simple retour au point de départ.
//   · `A3A_fnc_chargeWithSmoke` (35 % de chance de fumigène) : RETIRÉ. Il mêle deux gestes —
//     la prise de couvert et l'emploi du fumigène — et un professeur qui fait deux choses ne
//     s'enseigne pas proprement. Le fumigène sera son propre geste, ou rien.
//
// ⚠️ UNE ADAPTATION QUI CHANGE LE SENS, ÉCRITE ICI PLUTÔT QUE CACHÉE :
//   leur prise de couvert ne se déclenche qu'AU-DELÀ de 300 m (`if (_unit distance _enemy <
//   300) exitWith {}`). Notre geste n°3 vit à 100-150 m, sous le feu, à mi-traversée. J'ai
//   donc retiré cette barrière. Ce n'est plus tout à fait leur professeur : c'est le nôtre,
//   et il se re-certifie comme tel. La distance de déclenchement devient un paramètre, posé
//   par le banc, pas par un chiffre hérité dont on ignore la raison.
//
// AUCUN DE CES TROIS N'EST CERTIFIÉ. Ils entrent au répertoire comme candidats professeurs :
//   HMT_getToCover -> geste n°3, prise de couvert sous le feu (grandeur : les pertes)
//   HMT_doFlank    -> geste n°5, débordement (grandeur : la prise)
//   HMT_coverage   -> outil, pas geste : il trouve un couvert derrière un objet réel.
//
// ET CE QUE J'EN RETIENS POUR MON PROPRE GÉOMÈTRE : `HMT_coverage` ne compte pas des objets
// dans un rayon comme je le fais — il mesure la BOÎTE ENGLOBANTE de chacun et exige plus de
// 2 m de large, 2 m de haut, 50 cm d'épaisseur. C'est du couvert qui arrête une balle, pas un
// buisson. Mon compteur à 15 m est plus grossier que le leur. À reprendre.

if (!isServer) exitWith {};

// ───────────────────────────────────────────────────────────── un homme peut-il encore agir
HMT_canFight = {
    params ["_unit"];
    if (isNull _unit) exitWith { false };
    if (!alive _unit) exitWith { false };
    if (captive _unit) exitWith { false };
    if (lifeState _unit == "INCAPACITATED") exitWith { false };
    true
};

// ───────────────────────────────────────────────────── trouver un couvert derrière un objet
// Porté de fn_coverage. Il cherche 5 m derrière l'homme, à l'opposé de l'ennemi, retient les
// objets assez gros pour arrêter une balle, et rend une position DE L'AUTRE CÔTÉ de l'objet.
// Il marque l'objet « pris » 60 s pour que deux hommes ne s'empilent pas derrière le même mur.
HMT_coverage = {
    params ["_unit", "_ennemi"];
    private _petits = []; private _gros = [];
    private _derriere = (position _unit) getPos [5, _ennemi getDir _unit];
    private _groupe = group _unit;
    private _objets = (nearestObjects [_derriere, [], 30])
                      select { !(_x in (_groupe getVariable ["hmt_pris", []])) };
    private _routes = _derriere nearRoads 30;
    private _bruit = ["#crater","#crateronvehicle","#soundonvehicle","#particlesource",
                      "#lightpoint","#slop","#mark","HoneyBee","Mosquito","HouseFly",
                      "FxWindPollen1","ButterFly_random","Snake_random_F","Rabbit_F",
                      "FxWindGrass2","FxWindLeaf1","FxWindGrass1","FxWindLeaf3","FxWindLeaf2"];
    {
        private _t = typeOf _x;
        if (!(_t in _bruit)
            && {!(_x isKindOf "Man")} && {!(_x isKindOf "Bird")}
            && {!(_x isKindOf "BulletCore")} && {!(_x isKindOf "Grenade")}
            && {!(_x isKindOf "WeaponHolder")} && {(_x distance _ennemi) > 5}) then {
            private _bb = boundingBoxReal _x;
            private _p1 = _bb select 0; private _p2 = _bb select 1;
            // LA MESURE QUI VAUT D'ETRE REPRISE : large, epais, haut — du couvert, pas un buisson.
            if ((abs ((_p2 select 0) - (_p1 select 0))) > 2
                && {(abs ((_p2 select 1) - (_p1 select 1))) > 0.5}
                && {(abs ((_p2 select 2) - (_p1 select 2))) > 2}) then {
                if (_t isEqualTo "") then { _petits pushBack _x } else { _gros pushBack _x };
            };
        };
    } forEach (_objets - _routes);

    if (_gros isEqualTo [] && {_petits isEqualTo []}) exitWith { [] };
    private _obj = if !(_gros isEqualTo []) then { [_gros, _unit] call BIS_fnc_nearestPosition }
                                            else { [_petits, _unit] call BIS_fnc_nearestPosition };
    if (isNull _obj) exitWith { [] };

    if !(_obj isKindOf "House") then {
        private _arr = _groupe getVariable ["hmt_pris", []];
        _arr pushBack _obj;
        _groupe setVariable ["hmt_pris", _arr];
        [_obj, _groupe] spawn {
            params ["_obj", "_groupe"];
            sleep 60;
            if (!isNull _groupe && {!isNull _obj}) then {
                private _arr = _groupe getVariable ["hmt_pris", []];
                _groupe setVariable ["hmt_pris", _arr - [_obj]];
            };
        };
    };
    private _pe = position _ennemi;
    _pe getPos [(_obj distance _pe) + 2, _pe getDir _obj]
};

// ─────────────────────────────────────────── GESTE N°3 — se jeter à couvert sous le feu
// Porté de fn_unitGetToCover. La barrière des 300 m est retirée : notre geste vit à 100-150 m.
// La distance de déclenchement est désormais un PARAMETRE, pose par le banc.
HMT_getToCover = {
    params ["_unit", "_ennemi", ["_dmin", 0], ["_tenue", 30]];
    if (isPlayer _unit) exitWith { false };
    if (_unit != vehicle _unit) exitWith { false };
    if !([_unit] call HMT_canFight) exitWith { false };
    if (isNull _ennemi) exitWith { false };
    if ((_unit distance _ennemi) < _dmin) exitWith { false };

    private _couvert = [_unit, _ennemi] call HMT_coverage;
    if (_couvert isEqualTo []) exitWith { false };

    _unit stop false;
    _unit forceSpeed -1;
    { _unit disableAI _x } forEach ["AUTOTARGET","FSM","TARGET","SUPPRESSION",
                                    "AUTOCOMBAT","WEAPONAIM","COVER","CHECKVISIBLE"];
    _unit setUnitPos "MIDDLE";
    _unit setCombatMode "BLUE";
    _unit doMove _couvert;

    [_unit, _couvert, _tenue] spawn {
        params ["_unit", "_couvert", "_tenue"];
        private _fin = time + 15;
        waitUntil { sleep 0.5; (_unit distance _couvert < 1) || (time > _fin) };
        if (_unit distance _couvert < 1) then {
            sleep 1;
            _unit stop true; _unit forceSpeed 0;
            _unit setCombatMode "YELLOW"; _unit setUnitPos "AUTO";
            _unit doWatch (_unit findNearestEnemy _unit);
            sleep _tenue;
        };
        { _unit enableAI _x } forEach ["AUTOTARGET","FSM","TARGET","SUPPRESSION",
                                       "AUTOCOMBAT","WEAPONAIM","COVER","CHECKVISIBLE"];
        _unit setCombatMode "YELLOW"; _unit forceSpeed -1;
        _unit stop false; _unit setUnitPos "AUTO";
    };
    true
};

// ────────────────────────────────────────────────── GESTE N°5 — déborder par les deux ailes
// Porté de fn_doFlank. Les hommes partent alternativement à ±45°, à 1,3 fois la distance,
// puis convergent sur l'ennemi. `A3A_fnc_recallGroup` remplacé par un retour au départ.
HMT_doFlank = {
    params ["_unites", "_ennemi", ["_ecart", 45], ["_delai", 60]];
    if (_unites isEqualTo []) exitWith { false };
    private _chef = leader (_unites select 0);
    private _retour = getPosATL _chef;
    private _ang = _chef getDir _ennemi;
    private _dist = (_chef distance _ennemi) * 1.3;
    private _p1 = _chef getPos [_dist, _ang + _ecart];
    private _p2 = _chef getPos [_dist, _ang - _ecart];

    {
        _x setVariable ["hmt_manoeuvre", true];
        private _p = if ((_forEachIndex % 2) == 0) then { _p1 } else { _p2 };
        _x doMove _p;
        [_x, _ennemi, _p, _delai] spawn {
            params ["_u", "_ennemi", "_p", "_delai"];
            private _fin = time + _delai;
            while { (_u getVariable ["hmt_manoeuvre", true]) && (time < _fin) } do {
                if (_u distance _p < 3) then { _u doMove (position _ennemi) };
                if (!([_ennemi] call HMT_canFight) || {!([_u] call HMT_canFight)}) exitWith {};
                sleep 3;
            };
        };
    } forEach _unites;

    [_unites, _ennemi, _retour, _delai] spawn {
        params ["_unites", "_ennemi", "_retour", "_delai"];
        private _fin = time + _delai;
        waitUntil { sleep 5; !([_ennemi] call HMT_canFight) || (time > _fin) };
        { _x setVariable ["hmt_manoeuvre", false]; _x doMove _retour } forEach _unites;
    };
    true
};

"HMT|PR|professeurs_antistasi_charges|3" call HMT_LOG;
