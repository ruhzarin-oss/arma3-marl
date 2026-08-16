// couvert_c3.sqf — LE CONTROLE DE BRAS DU GESTE N°3, reecrit le 11/08.
//
// ⚠️ POURQUOI CE FICHIER EXISTE, ET POURQUOI IL EST SEPARE DU GENERATEUR.
// Le 10/08, en propageant une correction du banc n°2 vers le banc n°3, j ai copie le
// GENERATEUR ENTIER au lieu de rejouer la meme edition. Les deux canaux propres du geste n°3
// — `COUVERT` et `LIEUC3` — vivaient dedans, et ils ont disparu avec :
//     journal du 10/08 : ARR BUDGET COUVERT EMPREINTE IMP LIEU LIEUC3 POS SANTE SU TIR VISE
//     journal du 11/08 : ARR BUDGET         EMPREINTE IMP LIEU        POS SANTE SU TIR VISE
// Ils n etaient ni dans git (`git log -S` sur toute l histoire : jamais entres), ni dans la
// copie miroir `bancs/arma/`, et le disque restic a ete reformate. On REECRIT donc, on ne
// restaure pas — contre la specification, qui elle est intacte : PROTOCOLE_GESTE3_LIEUX.md.
//
// LA LECON, PORTEE DANS LE CODE : ce canal vit dans SON PROPRE FICHIER, appele par l `init`.
// Une copie du generateur ne peut plus l emporter. On propage une EDITION, jamais un FICHIER.
//
// ─────────────────────────────────────────────────────────────────────────────────────
// CE QU IL MESURE, et pourquoi c est un CONTROLE DE BRAS et pas la grandeur.
// La grandeur qui decide le geste n°3, ce sont LES PERTES — le journal generique les porte
// deja. Ce que ces canaux ajoutent, c est la preuve que LE GESTE A EU LIEU :
//   · le bras PROFESSEUR doit vraiment se jeter a couvert et se coucher sous le feu proche ;
//   · le bras TEMOIN ne doit JAMAIS le faire.
// Sans ce controle, un ecart de pertes ne prouve rien — on ne saurait pas si les deux bras
// ont fait deux choses differentes. C est exactement le controle de bras du geste n°1 :
// 1049 accrochages professeur portant tous des bonds reels, ZERO bond chez les 1124 temoins.

if (!isServer) exitWith {};
if (isNil "HMT_LOG") then { HMT_LOG = { diag_log _this } };
"HMT|G|C3CANAL|reecrit|11-08" call HMT_LOG;

// LE COUVERT SE MESURE A LA BOITE ENGLOBANTE, pas au nom de l objet.
// Repris de la chasse de lieux, qui l a deja fait passer sur Arma : un objet compte comme
// couvert s il fait plus de 2 m de large, 0,5 m d epais et 2 m de haut, a moins de 15 m.
// ⟨fn_coverage d Antistasi, MIT, Copyright (c) 2023 Antistasi Ultimate Team⟩
HMT_C3_ACOUVERT = {
    params ["_u"];
    private _p = getPosATL _u;
    private _bruit = ["#crater","#crateronvehicle","#soundonvehicle","#particlesource",
                      "#lightpoint","#slop","#mark","HoneyBee","Mosquito","HouseFly",
                      "FxWindPollen1","ButterFly_random","Snake_random_F","Rabbit_F",
                      "FxWindGrass2","FxWindLeaf1","FxWindGrass1","FxWindLeaf3","FxWindLeaf2"];
    private _n = 0;
    {
        private _t = typeOf _x;
        if (!(_t in _bruit) && {!(_x isKindOf "Man")} && {!(_x isKindOf "Bird")}
            && {!(_x isKindOf "WeaponHolder")}) then {
            private _bb = boundingBoxReal _x;
            private _a = _bb select 0; private _b = _bb select 1;
            if ((abs ((_b select 0) - (_a select 0))) > 2
                && {(abs ((_b select 1) - (_a select 1))) > 0.5}
                && {(abs ((_b select 2) - (_a select 2))) > 2}) then { _n = _n + 1 };
        };
    } forEach (nearestObjects [_p, [], 15]);
    if (_n > 0) then {1} else {0}
};

// SOUS LE FEU : un tir est passe pres de cet homme dans les deux dernieres secondes.
// `FiredNear` est le seul evenement d Arma qui dise « ca m a siffle aux oreilles » ;
// il porte la distance, et on retient 15 m — la portee ou le bruit force la reaction.
HMT_C3_ARMER = {
    params ["_u"];
    if (_u getVariable ["c3_arme", false]) exitWith {};
    _u setVariable ["c3_arme", true];
    _u setVariable ["c3_feu", 0];
    _u addEventHandler ["FiredNear", {
        params ["_unit", "_tireur", "_distance"];
        // meme regle que le professeur : « sous le feu » veut dire SOUS LE FEU ADVERSE.
        // Deux canaux qui comptent differemment le meme mot se contrediraient au depouillement.
        if (!isNull _tireur && {!((side _tireur) isEqualTo (side _unit))} && {_distance < 15}) then {
            _unit setVariable ["c3_feu", time];
        };
    }];
};

// ─── LE PROFESSEUR DU GESTE N°3 — reecrit le 11/08 avec le canal.
// Specification, mot pour mot du protocole depose : « l equipe se jette a couvert au premier
// tir proche, se couche, repart apres 10 s » ; le temoin « continue debout, meme axe, meme
// lieu, meme effectif ». Le bras est publie par accrochage dans HMT_C3_BRAS par le
// generateur ; ici on ne fait qu APPLIQUER, et seulement au bras professeur.
HMT_C3_PROF = {
    params ["_u"];
    if (_u getVariable ["c3_prof_arme", false]) exitWith {};
    _u setVariable ["c3_prof_arme", true];
    _u addEventHandler ["FiredNear", {
        params ["_unit", "_tireur", "_distance"];
        // ⚠️ LE TIR DOIT ETRE ADVERSE. `FiredNear` se declenche pour tous les hommes PROCHES
        // DU TIREUR — donc aussi quand le VOISIN tire. Mesure du 11/08 : les 90 premiers
        // declenchements portaient tous une distance de ZERO, signature du camarade a deux
        // metres. Le professeur se couchait au feu de son propre binome, ce qui le rendait
        // bien plus facile a declencher que la specification ne le dit — et le temoin, lui,
        // ne subissait pas ce biais puisqu il ne se couche jamais. L ecart entre les bras
        // en etait gonfle. On exige donc que le tireur soit de l autre camp.
        if (isNull _tireur) exitWith {};
        if ((side _tireur) isEqualTo (side _unit)) exitWith {};
        if (_distance >= 15) exitWith {};
        if (_unit getVariable ["c3_a_terre", false]) exitWith {};
        _unit setVariable ["c3_a_terre", true];
        _unit setUnitPos "DOWN";
        (format ["HMT|G|C3GESTE|%1|a_terre|%2|adverse|1",
                 _unit getVariable ["hmt_id", -1], round _distance]) call HMT_LOG;
        [_unit] spawn {
            params ["_u"];
            sleep 10;                      // le sursis depose : dix secondes au sol
            if (alive _u) then {
                _u setUnitPos "AUTO";
                _u setVariable ["c3_a_terre", false];
                (format ["HMT|G|C3GESTE|%1|repart|10",
                         _u getVariable ["hmt_id", -1]]) call HMT_LOG;
            };
        };
    }];
};

// ─── LE CANAL, echantillonne toutes les 2 s. Meme forme que le temoin d intention `VISE`,
// qui tourne depuis des jours sans defaut : on reprend ce qui marche.
[] spawn {
    private _vus = [];
    while { true } do {
        if (!isNil "HMT_ACC") then {
            {
                _x params ["_unites", "", "_pt", "", "_id"];
                // LIEUC3 : QUEL LIEU est joue. Une seule fois par accrochage — la
                // decomposition par lieu est ce que la regle 12 exige, et sans elle un
                // agregat n est pas une lecture.
                if (!(_id in _vus)) then {
                    _vus pushBack _id;
                    (format ["HMT|G|LIEUC3|%1|%2|%3", _id,
                             round (_pt select 0), round (_pt select 1)]) call HMT_LOG;
                };
                {
                    if (alive _x && {(_x getVariable ["hmt_axe", -1]) >= 0}) then {
                        [_x] call HMT_C3_ARMER;
                        // ═══ LE TEMOIN RESTE DEBOUT — reparation du 12/08 ═══
                        // Mesure : le professeur se couchait sur 32,3 % des echantillons, le
                        // temoin sur 31,8 %. AUCUN ECART. Le geste se declenchait bien (2221
                        // mises a terre, toutes sous feu adverse) mais l IA d Arma couche le
                        // temoin TOUTE SEULE sous le feu. Le protocole dit qu il « continue
                        // debout, meme axe, meme lieu, meme effectif » — rien ne l y
                        // contraignait. Deux bras qui font la meme chose ne mesurent rien.
                        // C etait le premier morceau manquant apres l ecrasement du generateur.
                        if (!isNil "HMT_C3_BRAS") then {
                            if (!(HMT_C3_BRAS getOrDefault [_id, false])) then {
                                _x setUnitPos "UP";
                            };
                        };
                        // le geste ne s applique QU AU BRAS PROFESSEUR. Le temoin reste
                        // debout : c est ce qui fait la comparaison.
                        if (!isNil "HMT_C3_BRAS") then {
                            if (HMT_C3_BRAS getOrDefault [_id, false]) then { [_x] call HMT_C3_PROF };
                        };
                        private _post = switch (toLower (animationState _x select [0,4])) do {
                            case "amov": { if ((stance _x) == "PRONE") then {2}
                                           else { if ((stance _x) == "CROUCH") then {1} else {0} } };
                            default { if ((stance _x) == "PRONE") then {2}
                                      else { if ((stance _x) == "CROUCH") then {1} else {0} } };
                        };
                        // ⚠️ LA FENETRE DOIT ETRE PLUS LARGE QUE LE PAS D ECHANTILLONNAGE.
                        // Premiere version : drapeau de 2 s, echantillonne toutes les 2 s.
                        // Un evenement dont la duree egale la periode de mesure est invisible
                        // une fois sur deux — et il l a ete ZERO fois sur 2087 echantillons
                        // pendant que le geste, lui, se declenchait douze fois. Le canal
                        // disait « personne sous le feu » d un monde ou l on tirait a 4 m.
                        // Six secondes : trois fois le pas, donc au moins deux echantillons
                        // portent la trace de chaque rafale.
                        private _sousFeu = if ((time - (_x getVariable ["c3_feu", -999])) < 6) then {1} else {0};
                        (format ["HMT|G|COUVERT|%1|%2|%3|%4|%5|%6", _id,
                                 _x getVariable ["hmt_id", -1],
                                 _post, [_x] call HMT_C3_ACOUVERT, _sousFeu,
                                 (if (!isNil "HMT_C3_BRAS") then {
                                     if (HMT_C3_BRAS getOrDefault [_id, false]) then {1} else {0}
                                  } else {0})]) call HMT_LOG;
                    };
                } forEach _unites;
            } forEach HMT_ACC;
        };
        sleep 2;
    };
};
