// generateur_engagements_v12.sqf — VERSION 12 : le verdict ET LE MECANISME.
//
// LA v11 NE JOURNALISAIT QUE LE VERDICT. Elle a produit le +12,3 points du 02/08 — le seul
// fait fort du projet — sans jamais dire POURQUOI le flanc paie. Ses journaux bruts sont
// perdus, et de toute facon ils n auraient rien appris : ils ne portaient que debut et fin.
//
// QUATRE JOURNAUX AJOUTES, et rien d autre :
//   HMT|G|POS  position de chaque homme, 1 Hz
//   HMT|G|TIR  chaque coup, avec assignedTarget — qui VISE qui (intention, 36-62 %)
//   HMT|G|IMP  chaque coup QUI PORTE, via HitPart — qui TOUCHE qui (solide, toujours)
//   HMT|G|SU   knowsAbout par paire vivante, toutes les 5 s
//   HMT|G|ARR  premier franchissement du rayon de tenue, PAR GROUPE
//
// LE QUATRIEME EST LE COEUR. Le A/B mesure la PRISE D OBJECTIF, pas la survie. On a cherche
// son mecanisme dans la mortalite toute la nuit du 04 au 05/08, et les quatre canaux ont
// ferme. La lecture non testee : le flanc ne protege pas, il fait ARRIVER — deux axes, et
// l un des deux passe. ARR la mesure directement.
//
// ---- ci-dessous, l en-tete de la v11, conserve tel quel ----
//
// generateur_engagements.sqf — VERSION 6 : un verdict qui ne ment pas, et une victoire POSSIBLE.
//
// DEUX DEFAUTS DE LA v5, mesures sur son premier lot.
//
// (a) LE VERDICT ETAIT FAUX. Il lisait un INSTANTANE a la fermeture : un homme ayant derive a
//     moins de 60 m du point suffisait a declarer le point << pris >>. C est du bruit d etiquette,
//     et le bruit d etiquette empoisonne tout l aval bien plus qu un monde de moins. Desormais
//     TENIR se merite : des vivants dans le rayon, ZERO adverse dedans, et cela SOIXANTE SECONDES
//     CONTINUES. On mesure toutes les 5 s et on remet le compteur a zero des que la condition casse.
//
// (b) LES SIX ACCROCHAGES ONT FINI AU CHRONOMETRE, 1 631 coups pour 2 morts. L IA refuse de charger
//     une garnison de face, et elle a raison. On ne FORCE donc pas la decision — ce serait
//     fabriquer un monde qui recompense la charge stupide, l erreur qu on vient de quitter. On rend
//     la victoire POSSIBLE :
//       - rapport de force jusqu a 3 ou 4 contre 1 ;
//       - l assaut arrive en DEUX groupes sur deux azimuts ECARTES (60 a 140 degres), ce qui est ce
//         qui declenche le contournement chez LAMBS — et notre courbe de juillet dit que le flanc
//         paie ;
//       - mitrailleuse et fumigenes a l assaut : LAMBS les emploie de lui-meme.
//     Et le chronometre devient une VICTOIRE DU DEFENSEUR, pas un match nul : un assaut qui n a pas
//     conclu en dix minutes a echoue. C est la verite, pas une fabrication.
//
// CIBLE DE PILOTAGE : 40 a 60 % d accrochages resolus. Tout se resout -> le monde recompense la
// charge. Rien ne se resout -> il n enseigne rien sur la prise. La frontiere EST le signal.
//
// Appel : [<n_max>, <duree_s>, <n_axes>, <fige>] execVM "generateur_engagements_v12.sqf";

params [["_maxAcc", 1], ["_dureeMax", 600], ["_nAxes", 2], ["_fige", false]];
if (!isServer) exitWith {};
HMT_GEN_VERSION = 12;

private _periode = 20;
private _rTenue = 50;           // rayon de tenue
private _tenueRequise = 60;     // secondes CONTINUES d occupation exclusive
HMT_ACC = [];

// ---------------------------------------------------------------- INSTRUMENTATION v12
HMT_DT_POS = 1.0;          // cadence des positions, desserree d office si le budget saute
HMT_BUDGET_POS = 6;        // ms par passage ⟨v9 tenait 6,7 ms pour 260 entites⟩
HMT_NPOS = 0;

// chaque coup part avec sa cible. ⟨v9 : FiredMan ne livre PAS la cible, son 8e parametre est
//  un objet nul, verifie. currentTarget n existe pas dans ce build. assignedTarget repond.
//  Et la cible ainsi journalisee predit la mort a +17 points — mesure le 05/08.⟩
HMT_ID_SUIV = 0;
HMT_ARMER_TIR = {
    params ["_u", "_idAcc"];
    _u setVariable ["hmt_acc", _idAcc];
    HMT_ID_SUIV = HMT_ID_SUIV + 1;
    _u setVariable ["hmt_id", HMT_ID_SUIV, true];
    // L IMPACT : qui touche qui. HitPart livre la victime et le tireur, a chaque coup qui
    // porte. C est la donnee solide ; assignedTarget n est que l intention, et elle ne
    // repond que 36 a 62 % du temps selon le tirage — mesure aux deux smokes du 05/08.
    _u addEventHandler ["HitPart", {
        // `_this` EST DEJA le tableau des impacts : [[victime, tireur, projectile, ...], ...].
        // Le premier jet faisait params ["_liste"] puis forEach _liste — il prenait le PREMIER
        // impact et iterait sur ses CHAMPS, d ou « isNull attend un objet, recu un nombre »,
        // 237 fois. Attrape par le smoke avant le run long.
        {
            _x params ["_victime", "_tireur"];
            if (!isNull _victime && !isNull _tireur && {_victime != _tireur}) then {
                (format ["HMT|G|IMP|%1|%2|%3|%4|%5", _victime getVariable ["hmt_acc", -1],
                         (round (time*100))/100, _tireur getVariable ["hmt_id", -1],
                         _victime getVariable ["hmt_id", -1],
                         round (_tireur distance _victime)]) call HMT_LOG;
            };
        } forEach _this;
    }];
    _u addEventHandler ["Fired", {
        params ["_tireur"];
        private _c = assignedTarget _tireur;
        (format ["HMT|G|TIR|%1|%2|%3|%4", _tireur getVariable ["hmt_acc", -1],
                 (round (time*100))/100, _tireur getVariable ["hmt_id", -1],
                 (if (isNull _c) then {-1} else {_c getVariable ["hmt_id", -1]})]) call HMT_LOG;
    }];
};

HMT_POINT = {
    private _res = [];
    for "_k" from 1 to 120 do {
        private _p = [7000 * random 1 - 500, 7000 * random 1 - 500, 0];
        _p = [(_p select 0) max 300 min 6800, (_p select 1) max 300 min 6800, 0];
        if (surfaceIsWater _p) then { continue };
        private _loin = true;
        { if ((_p distance2D (_x select 2)) < 700) then { _loin = false } } forEach HMT_ACC;
        if (!_loin) then { continue };
        private _bats = nearestTerrainObjects [_p, ["HOUSE", "BUILDING", "RUIN"], 120, false, true];
        if (count _bats >= 3) exitWith { _res = [_p, _bats] };
    };
    _res
};

// --- QUI TIENT EXCLUSIVEMENT LE POINT, a cet instant : 0 EAST, 1 WEST, -1 personne ---
HMT_QUI_TIENT = {
    params ["_unites", "_pt", "_r"];
    private _viv = _unites select { alive _x && (_x distance2D _pt) < _r };
    private _e = count (_viv select { side _x == east });
    private _o = count (_viv select { side _x == west });
    if (_e > 0 && _o == 0) exitWith { 0 };
    if (_o > 0 && _e == 0) exitWith { 1 };
    -1
};

// ---------------------------------------------------------------- POSITIONS A 1 Hz
// Fil separe : la boucle de verdict tourne a 5 s, c est sa resolution de tenue et on n y
// touche pas. Le budget se surveille lui-meme — un generateur qui s effondre sous son propre
// instrument ne mesure plus le meme monde. ⟨motif repris de la capture v9⟩
[] spawn {
    private _v = HMT_GEN_VERSION;
    while { HMT_GEN_VERSION == _v } do {
        private _t0 = diag_tickTime;
        {
            _x params ["_unites", "", "", "", "_id"];
            {
                if (alive _x) then {
                    private _p = getPosATL _x;
                    (format ["HMT|G|POS|%1|%2|%3|%4|%5|%6|%7", _id, (round (time*100))/100,
                             _x getVariable ["hmt_id", -1], round (_p select 0), round (_p select 1),
                             round (getDir _x), _x getVariable ["hmt_axe", -1]]) call HMT_LOG;
                };
            } forEach _unites;
        } forEach HMT_ACC;
        private _ms = (diag_tickTime - _t0) * 1000;
        if (_ms > HMT_BUDGET_POS && HMT_DT_POS < 4.0) then {
            HMT_DT_POS = HMT_DT_POS + 0.5;
            (format ["HMT|G|BUDGET|positions_ms|%1|nouvelle_cadence|%2", round _ms,
                     HMT_DT_POS]) call HMT_LOG;
        };
        HMT_NPOS = HMT_NPOS + 1;
        sleep HMT_DT_POS;
    };
};

[_maxAcc, _periode, _dureeMax, _rTenue, _tenueRequise, _nAxes, _fige] spawn {
    params ["_maxAcc", "_periode", "_dureeMax", "_rTenue", "_tenueRequise", "_nAxes", "_fige"];
    private _v = HMT_GEN_VERSION;
    private _n = 0;
    while { HMT_GEN_VERSION == _v } do {
        sleep 5;                                   // pas de 5 s : c est la resolution de la TENUE

        private _restants = [];
        {
            _x params ["_unites", "_t0", "_pt", "_campDef", "_id", "_tenu", "_depuis", "_dmin", "_arrives"];
            private _viv = _unites select { alive _x };
            private _e = _viv select { side _x == east };
            private _o = _viv select { side _x == west };
            // DISTANCE D APPROCHE MINIMALE entre un assaillant vivant et un defenseur vivant.
            // Elle ancre le filtre des rencontres manquees sur une constante MESUREE et non sur un
            // seuil de gout : un verdict au chronometre ou aucun assaillant n a jamais franchi les
            // 100 m — notre falaise de detection — est un contact physiquement impossible, donc un
            // defaut du generateur et non une defense reussie.
            {
                private _a = _x;
                { private _d = _a distance2D _x; if (_d < _dmin) then { _dmin = _d } }
                    forEach (if (_campDef == 0) then {_e} else {_o});
            } forEach (if (_campDef == 0) then {_o} else {_e});

            // --- ARR : QUI ARRIVE, ET QUAND. Le coeur de la v12. ---
            // Premier franchissement du rayon de tenue par un homme de chaque axe. C est la
            // mesure directe de « le flanc fait ARRIVER » — la lecture que quatre canaux de
            // mortalite n ont pas pu tester.
            {
                private _u = _x;
                private _ax = _u getVariable ["hmt_axe", -1];
                if (_ax >= 0 && alive _u && !(_ax in _arrives) && (_u distance2D _pt) < _rTenue) then {
                    _arrives pushBack _ax;
                    (format ["HMT|G|ARR|%1|%2|%3|%4|%5", _id, (round (time*100))/100, _ax,
                             round (time - _t0), count (_unites select { alive _x })]) call HMT_LOG;
                };
            } forEach _unites;

            // --- SU : qui sait quoi, toutes les 5 s, sur les paires vivantes ---
            {
                private _a = _x;
                {
                    private _k = _a knowsAbout _x;
                    if (_k > 0.05) then {
                        (format ["HMT|G|SU|%1|%2|%3|%4|%5", _id, (round (time*100))/100,
                                 _a getVariable ["hmt_id", -1],
                                 _x getVariable ["hmt_id", -1], (round (_k*100))/100]) call HMT_LOG;
                    };
                } forEach (if (side _a == east) then {_o} else {_e});
            } forEach _viv;

            // --- suivi de la tenue CONTINUE ---
            private _q = [_unites, _pt, _rTenue] call HMT_QUI_TIENT;
            if (_q != _tenu) then { _tenu = _q; _depuis = time };
            private _duree_tenue = if (_tenu >= 0) then { time - _depuis } else { 0 };
            private _acquis = (_tenu >= 0) && (_duree_tenue >= _tenueRequise);

            private _ecrase = (count _e == 0) || (count _o == 0);
            private _expire = (time - _t0 > _dureeMax);
            // un camp acquiert le point s il le tient exclusivement assez longtemps ET qu il n en
            // est pas le proprietaire initial ; le defenseur, lui, gagne par le chronometre.
            private _priseFaite = _acquis && (_tenu != _campDef);
            private _fini = _ecrase || _expire || _priseFaite;

            if (_fini) then {
                private _cause = if (_ecrase) then {"elimination"} else {
                                 if (_priseFaite) then {"prise"} else {"chrono"}};
                // CHRONO = VICTOIRE DU DEFENSEUR, pas match nul.
                private _vainqueur = if (_priseFaite) then { _tenu } else {
                                     if (_ecrase) then {
                                        (if (count _e == 0) then {1} else {0})
                                     } else { _campDef }};
                private _pris = if (_vainqueur == _campDef) then {0} else {1};
                (format ["HMT|G|fin|%1|%2|%3|%4|%5|%6|%7|%8|%9|%10|%11|%12", _id,
                         (round (time * 100)) / 100, round (time - _t0), _cause,
                         _campDef, _vainqueur, _pris, round _duree_tenue,
                         count _e, count _o, round _dmin,
                         count _arrives]) call HMT_LOG;   // COMBIEN D AXES ONT ATTEINT LE POINT
                { if (!isNull _x) then { deleteVehicle _x } } forEach _unites;
            } else {
                _restants pushBack [_unites, _t0, _pt, _campDef, _id, _tenu, _depuis, _dmin, _arrives];
            };
        } forEach HMT_ACC;
        HMT_ACC = _restants;

        // ---- ouvrir, au plus toutes les _periode secondes ----
        if (count HMT_ACC < _maxAcc && {(random 1) < (5 / _periode)}) then {
            private _c = call HMT_POINT;
            if (count _c > 0) then {
                _c params ["_pt", "_bats"];
                _n = _n + 1;
                // LES QUATRE BRAS, TIRES AU SORT A CHAQUE ACCROCHAGE
                //   0 frontal · 1 deux axes · 2 frontal FIGE · 3 deux axes FIGE
                private _bras = floor (random 4);
                _nAxes = if (_bras % 2 == 0) then {1} else {2};
                _fige  = _bras >= 2;
                private _campDef = floor random 2;
                private _nDef = 4 + floor random 5;                 // 4 a 8 defenseurs
                // RAPPORT DE FORCE RESSERRE. Mesure du 01/08 sur 33 verdicts : a 1,5-4 contre 1,
                // l assaillant prenait le point 75,8 % du temps pour une cible de 40-60. J avais
                // corrige l impasse du matin en fabriquant l inverse — un monde ou l attaque paie
                // presque toujours. Quatre defenseurs contre seize cedent meme retranches.
                private _ratio = 1.2 + random 1.3;                  // 1,2 a 2,5 contre 1
                private _nAtt = round (_nDef * _ratio) min 16;
                private _dist = 200 + random 200;
                // LES DEUX AXES DOIVENT ETRE AU SEC. Bug du 01/08 : on tirait un azimut et un
                // ecart sans verifier, et sur une ile le second tombait regulierement a la mer —
                // le groupe etait alors saute en silence et l assaut arrivait sur UN SEUL axe,
                // supprimant precisement ce qui declenche le contournement chez LAMBS.
                private _az1 = -1; private _ecart = 0;
                for "_k" from 1 to 40 do {
                    private _a = random 360;
                    private _e = 60 + random 80;
                    private _p1 = [(_pt select 0) + _dist * sin _a, (_pt select 1) + _dist * cos _a, 0];
                    private _p2 = [(_pt select 0) + _dist * sin (_a + _e), (_pt select 1) + _dist * cos (_a + _e), 0];
                    if (!surfaceIsWater _p1 && !surfaceIsWater _p2) exitWith { _az1 = _a; _ecart = _e };
                };
                if (_az1 < 0) exitWith {};                          // ce point n offre pas deux axes : on renonce
                private _az2 = _az1 + _ecart;
                private _tDef = if (_campDef == 0) then {"O_Soldier_F"} else {"B_Soldier_F"};
                private _tAtt = if (_campDef == 0) then {"B_Soldier_F"} else {"O_Soldier_F"};
                private _tMG  = if (_campDef == 0) then {"B_Soldier_AR_F"} else {"O_Soldier_AR_F"};
                private _cAtt = if (_campDef == 0) then {west} else {east};
                private _tous = [];

                private _gDef = createGroup (if (_campDef == 0) then {east} else {west});
                private _places = [];
                { _places append (_x buildingPos -1) } forEach _bats;
                _places = _places call BIS_fnc_arrayShuffle;
                // SYMETRIE DES MOYENS. Mesure du 01/08 : chaque groupe d assaut recevait une
                // mitrailleuse et des fumigenes, la garnison RIEN — j avais arme un camp et pas
                // l autre, puis je m etonnais que l assaut gagne 70 % du temps.
                private _tMGD = if (_campDef == 0) then {"O_Soldier_AR_F"} else {"B_Soldier_AR_F"};
                for "_i" from 1 to _nDef do {
                    private _t = if (_i == 1) then { _tMGD } else { _tDef };
                    private _u = _gDef createUnit [_t, _pt, [], 0, "CAN_COLLIDE"];
                    private _q = if (_i - 1 < count _places) then { _places select (_i - 1) }
                                 else { [(_pt select 0) + (random 40) - 20,
                                         (_pt select 1) + (random 40) - 20, 0] };
                    _u setPosATL _q; _u setSkill (0.3 + random 0.5);
                    _u setBehaviour "COMBAT"; _u setCombatMode "RED";
                    _u addMagazines ["SmokeShell", 2];
                    _tous pushBack _u;
                };
                // LA GARNISON EST TENUE PAR LA FONCTION DU SYSTEME TACTIQUE LUI-MEME.
                // Deux erreurs successives avant d y venir. D abord disableAI PATH, qui clouait
                // chaque homme dans le batiment ou il etait ne. Puis un point de consigne HOLD,
                // qui veut dire << allez a ce point et attendez-y >> et non << tenez votre
                // position >> : mesure du 01/08, les defenseurs SORTAIENT du couvert pour aller au
                // centre de l objectif et s y faisaient faucher — les eliminations sont passees de
                // 6,7 % a 41,7 % et les resolus a 91,7 %.
                // La bonne reponse etait de cesser de bricoler ce que le systeme fait deja : sa
                // fonction de garnison place les hommes dans le bati, les y maintient, et gere
                // leurs deplacements internes. C est meme sa fonction phare.
                // [groupe, position, rayon, aire, teleporter, trier par hauteur, condition de
                //  sortie, patrouiller]
                if (!isNil "lambs_wp_fnc_taskGarrison") then {
                    [_gDef, _pt, 60, [], true, true] call lambs_wp_fnc_taskGarrison;
                } else {
                    { _x disableAI "PATH" } forEach (units _gDef);   // repli si le mod est absent
                };

                // ---- A2 : CONTROLE POSITIF INTEGRE ----
                // Les defenseurs regardent l axe 1 et n en bougent pas. Un assaut a deux axes
                // prend alors le second groupe entierement a revers : le deux-axes DOIT y
                // ecraser le frontal. S il n y arrive pas, c est l instrument qui est casse.
                // On ne touche ni a leur competence, ni a leur armement, ni a la garnison :
                // SEUL LE CAP est tenu, et il est journalise pour qu on le verifie.
                if (_fige) then {
                    private _capFige = _az1;
                    { _x setDir _capFige; _x setFormDir _capFige } forEach (units _gDef);
                    [_gDef, _capFige, _n] spawn {
                        params ["_g", "_cap", "_id"];
                        private _t0 = time;
                        while { time - _t0 < 900 && {count (units _g) > 0} } do {
                            { _x setDir _cap; _x setFormDir _cap } forEach (units _g);
                            sleep 0.5;
                        };
                    };
                    (format ["HMT|G|FIGE|%1|%2|%3", _n, round _capFige,
                             count (units _gDef)]) call HMT_LOG;
                };

                // DEUX GROUPES D ASSAUT, deux azimuts ecartes : c est ce qui declenche le
                // contournement chez LAMBS. Chacun avec sa mitrailleuse ; fumigenes pour tous.
                private _gs = [];
                {
                    private _az = _x;
                    private _pa = [(_pt select 0) + _dist * sin _az,
                                   (_pt select 1) + _dist * cos _az, 0];
                    if (!surfaceIsWater _pa) then {
                        private _g = createGroup _cAtt;
                        // effectif TOTAL identique quel que soit le nombre d axes : sinon le
                        // controle mesurerait le nombre d hommes et non la manoeuvre.
                        private _n2 = if (_nAxes >= 2) then { round (_nAtt / 2) max 2 } else { _nAtt };
                        for "_i" from 1 to _n2 do {
                            private _t = if (_i == 1) then { _tMG } else { _tAtt };
                            private _u = _g createUnit [_t, _pa, [], 0, "CAN_COLLIDE"];
                            _u setPosATL [(_pa select 0) + (random 24) - 12,
                                          (_pa select 1) + (random 24) - 12, 0];
                            _u setSkill (0.3 + random 0.5);
                            _u setBehaviour "COMBAT"; _u setCombatMode "RED";
                            _u addMagazines ["SmokeShell", 3];
                            _tous pushBack _u;
                        };
                        _g move _pt;
                        _gs pushBack _g;
                    };
                } forEach (if (_nAxes >= 2) then { [_az1, _az2] } else { [_az1] });

                if (count _gs > 0) then {
                    // AUCUNE REVELATION, DES DEUX COTES. C etait la quatrieme aide artificielle
                    // de la serie — apres les actionneurs qui ecrasaient la prudence du mod, la
                    // garnison clouee dans son batiment de naissance, et la garnison envoyee hors
                    // du couvert par une consigne HOLD mal lue. Reveler le chef adverse supprimait
                    // d un trait le probleme de reconnaissance : trouver la garnison, deviner dans
                    // quel batiment du village elle se tient.
                    // L avantage d information du retranche, le monde le produit deja
                    // PHYSIQUEMENT : la garnison est statique, sous couvert, et voit entrer les
                    // assaillants dans son enveloppe de detection. Notre loi mesuree — saturation
                    // sous 30 m, zero au-dela de 100 m, falaise nette — EST cet avantage.
                    // Le scripter serait le remplacer par une cinquieme aide.
                    // INSTRUMENTATION : chaque homme journalise ses coups avec sa cible,
                    // et chaque groupe d assaut sait quel AXE il porte.
                    { [_x, _n] call HMT_ARMER_TIR } forEach _tous;
                    {
                        private _iAxe = _forEachIndex;
                        { _x setVariable ["hmt_axe", _iAxe] } forEach (units _x);
                    } forEach _gs;
                    { _x setVariable ["hmt_axe", -1] } forEach (units _gDef);
                    // [unites, t0, point, campDef, id, tenu, depuis, dmin, ARRIVES]
                    HMT_ACC pushBack [_tous, time, _pt, _campDef, _n, -1, time, 9999, []];
                    (format ["HMT|G|debut|%1|%2|%3|%4|%5|%6|%7|%8|%9|%10|%11|%12|%13", _n,
                             (round (time * 100)) / 100, round (_pt select 0), round (_pt select 1),
                             count _bats, _campDef, _nDef, _nAtt, round _dist,
                             round _ecart, count _gs, _nAxes,
                             (if (_fige) then {1} else {0})]) call HMT_LOG;
                } else {
                    { if (!isNull _x) then { deleteVehicle _x } } forEach _tous;
                };
            };
        };
    };
};
(format ["HMT|OK|generateur|12|journaux|POS,TIR,IMP,SU,ARR,FIGE|dt_pos|%1", HMT_DT_POS]) call HMT_LOG;
