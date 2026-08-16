// hmt_capture.sqf — CAPTURE version 9. Le corpus devient un GRAPHE.
//
// ============================ CE QUI FONDE CETTE VERSION ============================
// Tout ci-dessous est MESURÉ le 02/08/2026, contexte non ordonnancé, 260 entités.
// ⟨la mesure d'avant, faite dans un spawn, annonçait 459 ms là où la production en fait 6,7 :
//  elle comptait les attentes entre images. Contrôle de vraisemblance obligatoire depuis.⟩
//
// COÛT PAR HOMME (net du plancher de parcours, 0,52 ms) :
//   la plupart des lectures ................ 0,2 à 0,4 ms   <- bon marché
//   getAllHitPointsDamage .................. 1,40 ms
//   getUnitLoadout ......................... 5,64 ms        <- cher, mais CONSTANT
//   magazinesAmmoFull ...................... 9,44 ms        <- le plus cher de tous
//   str d'un tableau de 10 nombres ......... 1,68 ms
//
// COÛT PAR PAIRE :
//   knowsAbout ............................. 4,8 µs         <- bon marché
//   targetKnowledge ........................ 6,3 µs
//   checkVisibility ........................ 29 µs
//   lineIntersectsSurfaces ................. 51,8 µs        <- 11x, le poste lourd
//
// D'OÙ LA CONCEPTION : ce qui est cher et constant se lit UNE FOIS ; ce qui est cher et
// variable se lit RAREMENT et sur PEU DE PAIRES ; ce qui est bon marché se lit souvent.
//
// ============================ CE QUE L'ARÊTE SIGNIFIE ============================
// Mesuré au contrôle positif (six essais) :
//   · knowsAbout est une connaissance de CAMP, pas de soldat. Cible cachée derrière un mur :
//     4,00 avec un camarade qui la voit sur le flanc, 0,00 pour un observateur SEUL.
//   · Le cône de vision domine la distance : un observateur seul ne voit PAS un ennemi à 50 m
//     sur son flanc, et voit celui à 300 m droit devant. La « falaise des 100 m » était un
//     effet d'ORIENTATION. Aucune coupure de distance sous 350 m — elle jetterait du réel.
//   · Géométrie et connaissance sont deux canaux DISTINCTS. Il faut les deux.
//
// ============================ CE QU'ON N'ÉMET PAS ============================
// Distance, gisement, angle au regard : RECALCULÉS hors ligne depuis les positions et
// l'azimut. Coût zéro sur le serveur. On ne paie en direct que ce que seul le moteur sait.
//
// Appel :  [<instance>, <dt>] execVM "hmt_capture.sqf";

params [["_inst", 0], ["_dt", 0.2]];

HMT_V = 9;
HMT_DT = _dt;
HMT_INST = _inst;
HMT_LOG = { diag_log _this };

if (isNil "HMT_NEXT_ID") then { HMT_NEXT_ID = 1 };
if (isNil "HMT_VUS") then { HMT_VUS = [] };
HMT_TICK = 0;
HMT_LAST = -1;
HMT_TOUS = { allUnits + allDeadMen };
HMT_MAXCAR = 700;
HMT_BUDGET_N = 10;          // ms par tick de nœuds, au-delà on espace
HMT_CHRONO = [0,0,0];                       // [somme noeuds, somme aretes, nb ticks]

HMT_SIDE = { private _s = _this;
    if (_s == east) exitWith {0}; if (_s == west) exitWith {1};
    if (_s == resistance) exitWith {2}; 3 };

HMT_POST = { private _p = unitPos _this;
    if (_p == "UP") exitWith {0}; if (_p == "MIDDLE") exitWith {1};
    if (_p == "DOWN") exitWith {2}; 3 };

// ==================== 1. RECENSEUR — et l'état CONSTANT, lu une seule fois ====================
[] spawn {
    private _v = HMT_V;
    while { HMT_V == _v } do {
        private _t = time;
        private _presents = [];
        {
            private _u = _x;
            private _id = _u getVariable ["hmt_id", -1];
            if (_id < 0) then {
                _id = HMT_NEXT_ID; HMT_NEXT_ID = HMT_NEXT_ID + 1;
                _u setVariable ["hmt_id", _id];
                _u setVariable ["hmt_side", (side _u) call HMT_SIDE];
                _u setVariable ["hmt_fire", 0];
                _u setVariable ["hmt_neuf", 1];      // position non fiable au 1er tick :
                                                     // 31 % des vitesses aberrantes sont des
                                                     // matérialisations ⟨mesuré⟩, pas du recyclage
                                                     // (2 651 identifiants, aucun réutilisé)
                _u setVariable ["hmt_beh", ""];      // pour l'émission SUR CHANGEMENT
                _u setVariable ["hmt_cm", ""];
                _u setVariable ["hmt_po", -1];

                _u addEventHandler ["Fired", {
                    params ["_u", "", "", "", "", "", "_proj"];
                    _u setVariable ["hmt_fire", 1];
                    private _i = _u getVariable ["hmt_id", -1];
                    // ON MARQUE LE PROJECTILE. Mesuré le 03/08 : le champ « tireur » de
                    // l'événement d'impact arrive VIDE dans 85 % des cas sur serveur dédié —
                    // l'unité n'y est pas locale. Le projectile, lui, porte ce qu'on y écrit.
                    // C'est ce qui rend les morts attribuables, donc étiquetables.
                    if (!isNull _proj) then { _proj setVariable ["hmt_tireur", _i] };
                    (format ["HMT|E|fired|%1|%2", (round (time*100))/100, _i]) call HMT_LOG;
                    // QUI TIRE VERS QUI — l'arête d'hostilité.
                    // ⟨FiredMan ne livre PAS la cible : son 8e paramètre est un objet nul, vérifié.
                    //  currentTarget n'existe pas dans ce build. assignedTarget répond, lui.⟩
                    private _c = assignedTarget _u;
                    if (!isNull _c) then {
                        (format ["HMT|AR|tir|%1|%2|%3", (round (time*100))/100, _i,
                                 (_c getVariable ["hmt_id", -1])]) call HMT_LOG;
                    };
                }];

                _u addEventHandler ["HitPart", {
                    private _lot = _this;
                    if ((count _lot) > 0 && { !((_lot select 0) isEqualType []) }) then { _lot = [_lot] };
                    {
                        private _cib = _x select 0; private _tir = _x select 1;
                        private _proj = if ((count _x) > 2) then { _x select 2 } else { objNull };
                        // TROIS SOURCES, dans l'ordre de fiabilité : le champ tireur s'il est
                        // rempli · la marque portée par le projectile · rien.
                        private _idt = -1;
                        if (!isNull _tir) then { _idt = _tir getVariable ["hmt_id", -1] };
                        if (_idt < 0 && {!isNull _proj}) then { _idt = _proj getVariable ["hmt_tireur", -1] };
                        (format ["HMT|E|hit|%1|%2|%3|%4|src|%5", (round (time*100))/100,
                                 (_cib getVariable ["hmt_id", -1]), _idt,
                                 (round ((damage _cib)*100))/100,
                                 (if (!isNull _tir) then {0} else {1})]) call HMT_LOG;
                    } forEach _lot;
                }];

                // L'ÉTAT CONSTANT, LU UNE SEULE FOIS. getUnitLoadout coûte 5,64 ms pour 260
                // hommes — insupportable par tick, dérisoire une fois par homme.
                private _p = getPosASL _u;
                (format ["HMT|N|spawn|%1|%2|%3|%4|%5|%6|%7|%8|%9", (round (_t*100))/100, _id,
                         (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10,
                         (round ((_p select 2)*10))/10, ((side _u) call HMT_SIDE),
                         (typeOf _u), (rank _u), (str (group _u))]) call HMT_LOG;
                (format ["HMT|N|kit|%1|%2|%3|%4", _id, (currentWeapon _u),
                         (count (magazines _u)), (str (weapons _u))]) call HMT_LOG;
            };
            _presents pushBack _id;
        } forEach (call HMT_TOUS);

        { if (!(_x in _presents)) then {
            (format ["HMT|N|despawn|%1|%2", (round (_t*100))/100, _x]) call HMT_LOG } } forEach HMT_VUS;
        HMT_VUS = _presents;
        sleep 2;
    };
};
"HMT|OK|recenseur|9" call HMT_LOG;

// ==================== 2. LES NŒUDS — horloge rapide, 5 Hz ====================
// ONZE nombres : id, x, y, z, vivant, camp, tir, AZIMUT DU REGARD, posture, suppression, neuf.
// L'azimut est la correction décisive : sans lui, l'angle au regard — la variable qui décide
// de la détection — serait incalculable hors ligne.
// Le total des morceaux est ANNONCÉ : 18,66 % des ticks étaient amputés sans que le lecteur
// puisse le savoir ⟨mesuré sur 51 020 ticks⟩.
addMissionEventHandler ["EachFrame", {
    if (HMT_V != 9) exitWith {};
    private _t = time;
    if (_t - HMT_LAST < HMT_DT) exitWith {};
    HMT_LAST = _t;
    private _d0 = diag_tickTime;
    HMT_TICK = HMT_TICK + 1;
    private _tr = round (_t*100)/100;
    private _tous = call HMT_TOUS;
    private _n = count _tous;
    private _l = [];
    {
        private _u = _x;
        private _p = getPosASL _u;
        private _ed = eyeDirection _u;
        _l pushBack (str [(_u getVariable ["hmt_id",-1]),
            (round ((_p select 0)*10))/10, (round ((_p select 1)*10))/10, (round ((_p select 2)*10))/10,
            (if (alive _u) then {1} else {0}), (_u getVariable ["hmt_side",3]),
            (_u getVariable ["hmt_fire",0]),
            (round ((((_ed select 0) atan2 (_ed select 1)) + 360) % 360)),
            (_u call HMT_POST),
            (round ((getSuppression _u)*100))/100,
            (_u getVariable ["hmt_neuf",0])]);
        if ((_u getVariable ["hmt_fire",0]) == 1) then { _u setVariable ["hmt_fire",0] };
        if ((_u getVariable ["hmt_neuf",0]) == 1) then { _u setVariable ["hmt_neuf",0] };
    } forEach _tous;

    private _bouts = []; private _c = "";
    {
        if ((count _c) + (count _x) + 1 > HMT_MAXCAR) then { _bouts pushBack _c; _c = "" };
        _c = if (_c == "") then { _x } else { _c + "," + _x };
    } forEach _l;
    _bouts pushBack _c;
    private _nb = count _bouts;
    { (format ["HMT|S|%1|%2|%3|%4|%5|[%6]", HMT_TICK, _forEachIndex, _nb, _tr, _n, _x]) call HMT_LOG } forEach _bouts;
    private _ms = (diag_tickTime - _d0) * 1000;
    HMT_CHRONO set [0, (HMT_CHRONO select 0) + (diag_tickTime - _d0)];
    HMT_CHRONO set [2, (HMT_CHRONO select 2) + 1];

    // GARDE-FOU DES NŒUDS. Les arêtes en avaient un, pas les nœuds — et ce sont EUX qui ont
    // cédé : 8 ms à 150 hommes, 18,6 ms à 250 ⟨mesuré la nuit du 03/08⟩. Plutôt que de laisser
    // filer, on ESPACE les relevés. Un tick plus rare vaut mieux qu'un tick qui mange l'image,
    // et la cadence effective est journalisée pour que le corpus sache à quel rythme il a été pris.
    if (_ms > HMT_BUDGET_N && HMT_DT < 0.5) then {
        HMT_DT = (HMT_DT + 0.05) min 0.5;
        (format ["HMT|COUT|garde_noeuds|ms|%1|dt|%2|unites|%3",
                 (round (_ms*100))/100, (round (HMT_DT*100))/100, _n]) call HMT_LOG;
    };
    if (_ms < HMT_BUDGET_N / 2.5 && HMT_DT > 0.2) then { HMT_DT = (HMT_DT - 0.02) max 0.2 };
}];
"HMT|OK|noeuds|9" call HMT_LOG;

// ==================== 3. LES ARÊTES — balayage progressif ====================
// Le tour complet des hommes prend une seconde, découpé en cinq tranches d'un tick chacune.
// Sans ce lissage, un tick d'arêtes coûterait tout d'un coup et ferait tomber l'image.
//
// PAS DE COUPURE DE DISTANCE sous 350 m : mesuré, un ennemi à 300 m droit devant est vu.
// La ligne de vue (51,8 µs, onze fois le prix de knowsAbout) n'est calculée QUE là où un lien
// existe déjà — inutile de sonder la géométrie vers quelqu'un que personne ne connaît.
HMT_TRANCHE = 0;
HMT_NTRANCHES = 10;              // ajusté automatiquement, voir le garde-fou plus bas
HMT_PORTEE = 350;                // pas de coupure plus courte : à 300 m droit devant, on VOIT
HMT_ALAST = -1;
HMT_ADT = 0.4;                   // arêtes 2,5 Hz ; tour complet en 4 s. knowsAbout bouge lentement
HMT_BUDGET = 8;                  // ms par passage. Au-delà, on découpe plus fin.
// HMT_KMAX supprimé : plus de plafond sur knowsAbout, il est trop bon marché pour se rationner
HMT_VMAX = 4;                    // dont sondées géométriquement (51,8 µs pièce)
// Ces deux plafonds sont ce qui BORNE le coût quelle que soit la densité. Sans eux, un
// affrontement serré fait exploser le nombre de paires et le serveur tombe — mesuré.
// Les arêtes au-delà du plafond portent vue = -1 : « non mesuré », à ne pas confondre
// avec « pas de vue ». Le lecteur doit distinguer les deux.
addMissionEventHandler ["EachFrame", {
    if (HMT_V != 9) exitWith {};
    private _t = time;
    if (_t - HMT_ALAST < HMT_ADT) exitWith {};
    HMT_ALAST = _t;
    private _d0 = diag_tickTime;
    private _tous = allUnits;
    private _n = count _tous;
    if (_n == 0) exitWith {};
    HMT_TRANCHE = (HMT_TRANCHE + 1) % HMT_NTRANCHES;
    private _tr = round (_t*100)/100;
    private _lignes = [];
    private _ages = [];
    {
        if ((_forEachIndex % HMT_NTRANCHES) == HMT_TRANCHE) then {
            private _a = _x;
            if (alive _a) then {
                private _ida = _a getVariable ["hmt_id",-1];
                private _sa = _a getVariable ["hmt_side",3];
                // TRI SPATIAL. Premier jet mesuré : 26 239 paires distinctes, 110 ms par
                // passage, serveur à 3,9 FPS. Dans un affrontement serré tout le monde voit
                // tout le monde — filtrer sur « le lien existe » ne filtre RIEN, et la ligne
                // de vue à 51,8 µs se payait 26 000 fois.
                // knowsAbout coûte 4,8 µs : on le calcule sur TOUS les ennemis à portée,
                // sans plafond. C'est la géométrie (51,8 µs) qui se rationne.
                // ⟨Fable, 02/08 : knowsAbout est de camp — un ennemi ignoré par A est porté
                //  par un camarade. La géométrie, elle, est propre à chaque homme : c'est
                //  ELLE qui est amputée, donc c'est elle qu'il faut choisir intelligemment.⟩
                private _cands = [];
                private _objs = [];                  // les objets restent HORS du tri :
                                                     // sort compare élément par élément et
                                                     // bute sur un OBJECT à écarts égaux
                private _vus = _a getVariable ["hmt_ar", []];
                {
                    private _b = _x;
                    if (alive _b && {(_b getVariable ["hmt_side",3]) != _sa}) then {
                        private _k = _a knowsAbout _b;
                        if (_k > 0.05) then {
                            private _idb = _b getVariable ["hmt_id",-1];
                            // de combien ce lien a-t-il bougé depuis le dernier passage ?
                            private _av = -1;
                            { if ((_x select 0) == _idb) exitWith { _av = _x select 1 } } forEach _vus;
                            private _delta = if (_av < 0) then { 99 } else { abs (_k - _av) };
                            _objs pushBack _b;
                            _cands pushBack [_delta, _idb, _k, (count _objs) - 1];
                        };
                    };
                } forEach (nearestObjects [getPosATL _a, ["CAManBase"], HMT_PORTEE]);

                // PRIORITÉ AU NEUF ET AU CHANGEANT, pas au proche. Un ennemi stable à 40 m
                // est moins décisif qu'un nouveau venu à 120 m.
                _cands sort false;
                private _memo = [];
                private _nv = 0;
                {
                    private _idb = _x select 1; private _k = _x select 2;
                    private _b = _objs select (_x select 3);
                    _memo pushBack [_idb, _k];
                    private _vue = -1;                 // -1 = NON MESURÉ, à ne pas lire comme « pas de vue »
                    if (_nv < HMT_VMAX) then {
                        _nv = _nv + 1;
                        private _i = lineIntersectsSurfaces
                            [eyePos _a, aimPos _b, _a, _b, true, 1, "VIEW", "FIRE"];
                        _vue = if (count _i == 0) then {1} else {0};
                    };
                    _lignes pushBack (format ["%1,%2,%3,%4", _ida, _idb, (round (_k*100))/100, _vue]);
                } forEach _cands;
                _a setVariable ["hmt_ar", _memo];

                // L'ÂGE DU BALAYAGE et LES ÉCARTÉS. Sans eux, un graphe pauvre demain serait
                // indiscernable d'un émetteur en retard. ⟨Fable : « une mesure doit savoir
                // échouer ; celle-là ne le sait pas encore »⟩
                private _prec = _a getVariable ["hmt_scan", -1];
                if (_prec > 0) then {
                    _ages pushBack (format ["%1,%2,%3,%4", _ida, (round ((_t - _prec)*100))/100,
                                            count _cands, ((count _cands) - _nv)]);
                };
                _a setVariable ["hmt_scan", _t];
            };
        };
    } forEach _tous;

    if (count _lignes > 0) then {
        private _bouts = []; private _c = "";
        {
            if ((count _c) + (count _x) + 1 > HMT_MAXCAR) then { _bouts pushBack _c; _c = "" };
            _c = if (_c == "") then { _x } else { _c + ";" + _x };
        } forEach _lignes;
        _bouts pushBack _c;
        private _nb = count _bouts;
        { (format ["HMT|A|%1|%2|%3|%4|%5|%6", HMT_TICK, HMT_TRANCHE, _forEachIndex, _nb, _tr, _x]) call HMT_LOG } forEach _bouts;
    };
    if (count _ages > 0) then {
        (format ["HMT|AGE|%1|%2|%3", HMT_TICK, _tr, (_ages joinString ";")]) call HMT_LOG;
    };
    private _ms = (diag_tickTime - _d0) * 1000;
    HMT_CHRONO set [1, (HMT_CHRONO select 1) + (diag_tickTime - _d0)];

    // GARDE-FOU. Le coût dépend de la densité, et la densité de Battle Lines n'est pas bornée
    // — 170 entités à 15 min, 264 à 2 h 14, sans palier connu. L'émetteur surveille donc son
    // propre coût et se découpe plus fin s'il dérape, au lieu de faire tomber le serveur.
    // ⟨un tick trop long est un trou aveugle dans le corpus : mieux vaut balayer plus lentement⟩
    if (_ms > HMT_BUDGET && HMT_NTRANCHES < 40) then {
        HMT_NTRANCHES = HMT_NTRANCHES + 2;
        (format ["HMT|COUT|garde|aretes_ms|%1|tranches|%2|unites|%3",
                 (round (_ms*100))/100, HMT_NTRANCHES, count allUnits]) call HMT_LOG;
    };
    if (_ms < HMT_BUDGET / 3 && HMT_NTRANCHES > 4) then { HMT_NTRANCHES = HMT_NTRANCHES - 1 };
}];
"HMT|OK|aretes|9" call HMT_LOG;

// ==================== 4. LES CHANGEMENTS — presque gratuits ====================
// Comportement, mode de combat et posture bougent rarement. Les sonder à cadence fixe, c'est
// réécrire deux cents fois la même valeur ; on ne les émet qu'au changement.
[] spawn {
    private _v = HMT_V;
    while { HMT_V == _v } do {
        private _tr = round (time*100)/100;
        {
            private _u = _x;
            if (alive _u) then {
                private _b = behaviour _u; private _cm = combatMode _u; private _po = _u call HMT_POST;
                if (_b != (_u getVariable ["hmt_beh",""]) || {_cm != (_u getVariable ["hmt_cm",""])}
                    || {_po != (_u getVariable ["hmt_po",-1])}) then {
                    _u setVariable ["hmt_beh", _b]; _u setVariable ["hmt_cm", _cm]; _u setVariable ["hmt_po", _po];
                    (format ["HMT|C|%1|%2|%3|%4|%5|%6", _tr, (_u getVariable ["hmt_id",-1]),
                             _b, _cm, _po, (speedMode _u)]) call HMT_LOG;
                };
            };
        } forEach allUnits;
        sleep 1;
    };
};
"HMT|OK|changements|9" call HMT_LOG;

// ==================== 5. MORTS ET COMPTE-RENDU DE COÛT ====================
addMissionEventHandler ["EntityKilled", {
    params ["_vic","_tueur"];
    (format ["HMT|E|killed|%1|%2|%3", (round (time*100))/100,
             (_vic getVariable ["hmt_id",-1]),
             (if (isNull _tueur) then {-1} else {_tueur getVariable ["hmt_id",-1]})]) call HMT_LOG;
}];
"HMT|OK|morts|9" call HMT_LOG;

[] spawn {
    private _v = HMT_V;
    while { HMT_V == _v } do {
        sleep 60;
        private _nt = HMT_CHRONO select 2;
        if (_nt > 0) then {
            (format ["HMT|COUT|noeuds_ms|%1|aretes_ms|%2|ticks|%3|unites|%4|fps|%5",
                     (round (1000*(HMT_CHRONO select 0)/_nt*100))/100,
                     (round (1000*(HMT_CHRONO select 1)/_nt*100))/100,
                     _nt, (count allUnits), (round (diag_fps*10))/10]) call HMT_LOG;
            HMT_CHRONO = [0,0,0];
        };
    };
};

(format ["HMT|OK|capture|9|instance|%1|dt|%2|noeuds|id,x,y,z,vivant,camp,tir,azimut,posture,suppression,neuf|aretes|de,vers,knowsAbout,vue",
         HMT_INST, HMT_DT]) call HMT_LOG;
