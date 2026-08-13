// banc_appui.sqf — v2 — L'APPUI-FEU FIGE-T-IL UN DÉFENSEUR À COUVERT ?
//
// ⟨Fable, 08/08⟩ « Un peloton d'exécution ne certifie pas un appui. 366 impacts en deux
// minutes, aucune mission n'y ressemblera. Refais le banc dans le RÉGIME DE LA MISSION :
// défenseurs à couvert comme ils le seront, appui à 100-200 m, feu de zone, peu d'impacts et
// beaucoup de proches — c'est le régime où la suppression certifiée vit réellement. »
//
// LA V1 EST MORTE DE SON PROPRE SUCCÈS. Elle a fini par mordre : riposte 738 -> 293,
// suppression relevée 0 -> 0,75. Mais avec 366 balles au but sur 6 hommes debout et
// découverts. Certifier « ça mord » dans ce régime, c'est certifier un autre monde.
//
// ET ELLE N'ÉTAIT MÊME PAS REPRODUCTIBLE : site suivant, géométrie déclarée MEILLEURE
// (24/24 et 18/18 de vue franche), et 5 impacts sur 362 coups, riposte inchangée. Trois
// lignes existent — mon rayon à 1,50 m, l'axe réel de l'arme, la trajectoire de la balle —
// et je n'en vérifiais qu'une. ⟨règle 6, troisième face : ne vérifie pas l'abstraction qui
// t'arrange, vérifie la propriété que le mécanisme utilise⟩
//
// CE QUI CHANGE, ET POURQUOI
//   1. LES DÉFENSEURS SONT À COUVERT — un muret de sacs devant chacun, accroupis derrière.
//      C'est le régime de la mission : on ne les touche presque plus, on les frôle.
//   2. LE TIR EST CONDITIONNÉ À `aimedAtTarget` — le jugement de visée de l'IA elle-même, et
//      non plus `forceWeaponFire` à l'aveugle. C'est la réparation de la non-reproductibilité.
//   3. L'ANGLE DE VISÉE EST INSTRUMENTÉ — écart entre l'axe de l'arme et la direction de la
//      cible au moment du tir. Grand angle = le pivot n'a pas eu lieu. C'est l'instrument qui
//      manquait pour diagnostiquer au lieu de deviner.
//   4. LE CONTRÔLE D'ARRIVÉE PASSE SUR LES MURETS. Dans ce régime les corps ne sont plus
//      touchés — donc « zéro impact sur les corps » ne prouverait plus rien. Ce sont les
//      IMPACTS SUR LES COUVERTS qui disent que les balles arrivent au bon endroit.
//
// LE DISPOSITIF. Terrain plat et dégagé, hors de tout lieu certifié. Trois corps, tous
// invulnérables et immobiles :
//   · 6 DÉFENSEURS accroupis derrière un muret, cap nord, libres de viser et tirer.
//   · 4 VICTIMES à 150 m plein nord, debout, qui NE TIRENT PAS : elles donnent aux défenseurs
//     quelque chose à viser, identiquement dans les deux bras.
//   · 3 APPUIS à 150 m, à 90° de l'axe des victimes.
//
// LES DEUX BRAS NE DIFFÈRENT QUE PAR UNE CHOSE : l'appui tire, ou l'appui se tait.
//
// TOUT LE MONDE EST INVULNÉRABLE : si l'appui tuait des défenseurs on mesurerait « moins de
// défenseurs », pas « des défenseurs figés » ; si les victimes mouraient, les défenseurs
// cesseraient de tirer faute de cible et pas du tout à cause de l'appui.
//
// GRANDEUR PRIMAIRE : les IMPACTS DÉLIVRÉS par les 6 défenseurs sur les victimes, en 120 s.
// Les coups tirés passent en second. ⟨Fable, 08/08 : le fait certifié dit capacité ×0,08, et
// il a été mesuré en impacts, par `HitPart`. La suppression d'Arma dégrade surtout la visée :
// le nombre de coups peut ne pas bouger quand leur valeur s'effondre.⟩
//
// LA PORTE, RÉÉCRITE AVANT DE RELANCER, EN DEUX ÉTAGES ⟨Fable, 08/08⟩ :
//   · ÉTAGE 1, ici : la baisse de riposte doit être LISIBLE — intervalle excluant zéro. Pas
//     de seuil chiffré emprunté : l'ancre certifiée du −92 % vient du régime À DÉCOUVERT et
//     ne se convertit pas dans le régime à couvert. On refuse d'inventer la conversion.
//   · ÉTAGE 2, PAS ICI : le verdict qui compte est la PORTE 0 du lieu, professeur contre
//     témoin, ses 10 points sur la prise.
//   > Ce banc n'a qu'UN SEUL DROIT : tuer la mission à bas prix si la suppression est NULLE.
//   > S'il la trouve faiblement vivante, il se tait et laisse le banc du lieu trancher.
//   > Un banc de mécanique qui prétend prédire le banc de mission outrepasse sa taille.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE POSITIF : dans le bras APPUI, les appuis doivent RÉELLEMENT tirer.
//   · CONTRÔLE D'ARRIVÉE : les murets doivent encaisser des impacts. Zéro impact sur les
//     couverts = les balles n'arrivent pas, et le banc ne dit RIEN sur la suppression — il
//     dit que je tire à côté. C'est l'erreur qui a tué deux lancements de la v1.
//   · CONTRÔLE DE VISÉE : l'angle médian de tir doit être petit. S'il est grand, le pivot
//     n'a pas eu lieu et `aimedAtTarget` n'a pas fait son travail.
//   · CONTRÔLE NUL : dans le bras TÉMOIN, les appuis doivent tirer ZÉRO coup.
//   · CONTRÔLE DE PRÉSENCE : dans le bras TÉMOIN, les défenseurs doivent tirer.
//   · EFFECTIF CONSTANT : 6 défenseurs et 4 victimes vivants à la fin de CHAQUE essai.
//   · RECENSEMENT DES CAPACITÉS — repris d'Antistasi, ajouté le 09/08. Avant et après chaque
//     fenêtre : combien des 9 hommes armés peuvent COMBATTRE, TIRER (arme intacte ET chargée),
//     BOUGER (donc pivoter) et sont PRÊTS à recevoir un ordre. Aucun de ces compteurs ne
//     corrige quoi que ce soit — ils constatent, et le dépouillement refuse le verdict si les
//     hommes ne pouvaient pas obéir. Une panne constatée vaut mieux qu'un zéro plausible.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|AP|debut|3" call HMT_LOG;
// « demander si un homme PEUT, avant de lui ordonner » — repris d Antistasi, qui verifie
// canFight/canMove/unitReady 124 fois quand nous ne le faisions jamais. Trois pannes de la
// nuit du 08/08 avaient leur reponse dans le moteur, et personne ne la demandait.
call compile preprocessFileLineNumbers "capacites.sqf";

[] spawn {
    sleep 20;

    // ---------------------------------------------------------------- terrain plat
    private _base = []; private _tol = 0;
    {
        private _t = _x;
        if (count _base == 0) then {
            for "_i" from 0 to 2500 do {
                if (count _base == 0) then {
                    private _c = [1200 + random 4200, 4200 + random 3000, 0];
                    private _h = getTerrainHeightASL _c;
                    if (!(surfaceIsWater _c) && _h > 2) then {
                        private _ok = true;
                        { private _q = _c vectorAdd _x;
                          if (surfaceIsWater _q) then { _ok = false };
                          if (abs ((getTerrainHeightASL _q) - _h) > _t) then { _ok = false };
                        } forEach [[0,160,0],[0,-60,0],[160,0,0],[-160,0,0],[120,120,0],[-120,120,0]];
                        if (_ok) then { _base = _c; _tol = _t };
                    };
                };
            };
        };
    } forEach [8, 14, 22, 32];
    if (count _base == 0) exitWith { "HMT|AP|ECHEC|terrain" call HMT_LOG };

    // DEUX lignes de vue exigées ensemble : celle dont les CONTRÔLES ont besoin
    // (défenseur -> victime) et celle dont la MESURE a besoin (appui -> défenseur). La v1 n'a
    // vérifié que la première, et a mesuré 368 coups pour zéro impact.
    HMT_VUE = {
        params ["_b"];
        private _ok = 0; private _tot = 0;
        {
            private _dx = _x;
            {
                _tot = _tot + 1;
                private _p1 = AGLToASL (_b vectorAdd [_dx, 0, 1.2]);
                private _p2 = AGLToASL (_b vectorAdd [_x, 150, 1.5]);
                if (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1]) == 0)
                    then { _ok = _ok + 1 };
            } forEach [-15, -5, 5, 15];
        } forEach [-40, -24, -8, 8, 24, 40];
        private _ok2 = 0; private _tot2 = 0;
        {
            private _ax = _x;
            {
                _tot2 = _tot2 + 1;
                private _p1 = AGLToASL (_b vectorAdd [150, _ax, 1.5]);
                private _p2 = AGLToASL (_b vectorAdd [_x, 0, 1.2]);
                if (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1]) == 0)
                    then { _ok2 = _ok2 + 1 };
            } forEach [-40, -24, -8, 8, 24, 40];
        } forEach [-10, 0, 10];
        [_ok, _tot, _ok2, _tot2]
    };
    private _v = [_base] call HMT_VUE;
    private _cherche = 0;
    while { ((_v select 0) < 20 || (_v select 2) < 15) && _cherche < 900 } do {
        _cherche = _cherche + 1;
        private _c = [1200 + random 4200, 4200 + random 3000, 0];
        if (!(surfaceIsWater _c) && {(getTerrainHeightASL _c) > 2}) then {
            private _h = getTerrainHeightASL _c; private _pl = true;
            { if (abs ((getTerrainHeightASL (_c vectorAdd _x)) - _h) > 14) then { _pl = false } }
              forEach [[0,160,0],[0,-60,0],[160,0,0],[-160,0,0]];
            if (_pl) then {
                private _w = [_c] call HMT_VUE;
                if (((_w select 0) + (_w select 2)) > ((_v select 0) + (_v select 2)))
                    then { _base = _c; _v = _w };
            };
        };
    };
    (format ["HMT|AP|site|%1|%2|vueDV|%3|sur|%4|vueAD|%5|sur|%6|cherche|%7",
             round (_base select 0), round (_base select 1),
             _v select 0, _v select 1, _v select 2, _v select 3, _cherche]) call HMT_LOG;
    if ((_v select 0) < 20 || (_v select 2) < 15) exitWith {
        (format ["HMT|AP|ECHEC|vue_insuffisante|DV|%1|AD|%2", _v select 0, _v select 2]) call HMT_LOG;
    };

    // ⚠️ QUATRE TERRAINS, PAS UN. ⟨Younes, 09/08 : « teste si les resultats peuvent etre
    // differents »⟩ Le banc tirait un terrain plat AU HASARD a chaque lancement : si le verdict
    // depend du terrain, je ne l aurais decouvert qu en relançant, c est-a-dire trop tard.
    // Meme cout total — 4 terrains x 4 repetitions x 3 bras — et la variation entre terrains
    // devient VISIBLE au lieu d etre invisible. Un banc qui ne tourne que sur un terrain ne
    // sait pas s il mesure une mecanique ou un endroit.
    // DOUZE CANDIDATS CRIBLES POUR HUIT ADMIS ⟨protocole depose⟩. Le surplus est bon marche :
    // deux essais chacun. Et si plus de 4 sur 12 echouent a l admission, ce ne sont plus les
    // terrains qu on accuse, c est le geometre qui les qualifie de « plats et degages ».
    // ⚠️ LES TERRAINS SONT LES MEMES D UNE SESSION A L AUTRE, sinon les deux mesures de ligne
    // de base ne porteraient pas sur les memes lieux et l admission ne voudrait rien dire.
    // La phase 1 CHERCHE et journalise ; les phases 2 et 3 RELISENT la liste.
    // ⚠️ PAS D `exitWith` ICI. En SQF il quitte TOUT LE BLOC ENGLOBANT, pas seulement le `if` :
    // la phase 2 a charge ses sept terrains puis s est arretee net, muette, treize minutes
    // durant. Le tableau de bord l a dit tout de suite ; sans lui je l aurais appris dans une
    // heure. On branche par une condition, pas par une sortie.
    private _relu = !isNil "HMT_CANDIDATS";
    if (_relu) then {
        HMT_SITES = HMT_CANDIDATS;
        (format ["HMT|AP|sites|%1|relus|de|la|liste|%2",
                 count HMT_SITES,
                 str (HMT_SITES apply { [round (_x select 0), round (_x select 1)] })]) call HMT_LOG;
    } else {
        HMT_SITES = [_base];
    };
    private _q = 0;
    // 12 000 tirages n ont rendu que 4 terrains : le critere n accepte qu un point sur trois
    // mille. ON NE TOUCHE PAS AU CRITERE — c est en l abaissant qu on avait admis le terrain 0,
    // celui qui a produit un bras entier de bruit. On paie du calcul : la recherche coutait
    // trois secondes, on lui en donne cent cinquante mille tirages.
    while { !_relu && count HMT_SITES < 12 && _q < 150000 } do {
        _q = _q + 1;
        private _c = [1200 + random 4200, 4200 + random 3000, 0];
        if (!(surfaceIsWater _c) && {(getTerrainHeightASL _c) > 2}
            && {(HMT_SITES findIf { _x distance2D _c < 800 }) < 0}) then {
            private _h = getTerrainHeightASL _c; private _pl = true;
            { if (abs ((getTerrainHeightASL (_c vectorAdd _x)) - _h) > 14) then { _pl = false } }
              forEach [[0,160,0],[0,-60,0],[160,0,0],[-160,0,0]];
            if (_pl) then {
                private _w = [_c] call HMT_VUE;
                if ((_w select 0) >= 20 && {(_w select 2) >= 15}) then {
                    HMT_SITES pushBack _c;
                    (format ["HMT|AP|candidat|%1|%2|%3|vueDV|%4|vueAD|%5|au|%6e|tirage",
                             count HMT_SITES, round (_c select 0), round (_c select 1),
                             _w select 0, _w select 2, _q]) call HMT_LOG;
                };
            };
        };
        if (_q % 10000 == 0) then { sleep 0.1 };
    };
    if (!_relu) then {
        (format ["HMT|AP|sites|%1|trouves|en|%2|essais|%3",
                 count HMT_SITES, _q,
                 str (HMT_SITES apply { [round (_x select 0), round (_x select 1)] })]) call HMT_LOG;
    };
    if (count HMT_SITES < 2) exitWith {
        (format ["HMT|AP|ECHEC|un_seul_terrain|%1", count HMT_SITES]) call HMT_LOG;
    };

    // ⚠️ PREMIER JET : ajouter 30 chargeurs. Il ne PEUT pas marcher — un gilet en contient
    // huit, les autres tombent par terre en silence, et le fil de detente a claque a ZERO coup
    // de reserve. Le critere depose a donc attrape sa propre implementation defaillante, au
    // lieu de laisser passer trois sessions mesurees sous penurie. C est le systeme qui marche.
    //
    // LA DOTATION SE FAIT AU COUP PAR COUP, PAS EN STOCK : un gestionnaire sur `Fired` qui
    // regarnit le chargeur a chaque depart. Le fusil ne se vide jamais, donc la reserve ne
    // descend jamais, donc la mesure n est jamais plafonnee par la rarete.
    HMT_DOTER = {
        params ["_u"];
        if (_u getVariable ["ap_dote", false]) exitWith {};
        _u setVariable ["ap_dote", true];
        _u addEventHandler ["Fired", { (_this select 0) setVehicleAmmo 1 }];   // lint:ok
        _u setVehicleAmmo 1;                                                   // lint:ok
        // ⚠️ EXCEPTION ASSUMEE. Le linteur signale `setVehicleAmmo` parce qu il ne remet pas
        // un fusil VIDE en etat de facon fiable — le banc s etait eteint au 4e essai avec
        // 9 hommes « armes » sur 9. Ici l emploi est l inverse : appele a CHAQUE depart, il
        // regarnit un chargeur qui n est jamais vide. Le piege reste arme pour les autres.
    };

    // ---------------------------------------------------------------- les couverts
    // LE RÉGIME DE LA MISSION. Un muret par défenseur, face à l'appui (plein est). C'est ce
    // qui fait passer le banc de « peloton d'exécution » à « appui-feu ».
    HMT_MUR = [];
    {
        private _p = _base vectorAdd [_x + 1.5, 0, 0];
        private _m = createVehicle ["Land_BagFence_Long_F", _p, [], 0, "CAN_COLLIDE"];
        _m setPosATL _p; _m setDir 0; _m allowDamage false;
        _m setVariable ["ap_touche", 0];
        // le CONTRÔLE D'ARRIVÉE vit désormais ici : les corps ne sont presque plus touchés,
        // donc ce sont les murets qui disent si les balles arrivent au bon endroit.
        _m addEventHandler ["HitPart", { private _o = (_this select 0) select 0;
            _o setVariable ["ap_touche", (_o getVariable ["ap_touche",0]) + 1] }];
        HMT_MUR pushBack _m;
    } forEach [-40, -24, -8, 8, 24, 40];

    // ---------------------------------------------------------------- les défenseurs
    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        // ⚠️ LE CANAL DE POSTURE EST RENDU. Comment un homme supprimé exprime-t-il sa
        // suppression ? IL SE BAISSE, colle au muret, cesse de s'exposer — et c'est EN SE
        // CACHANT qu'il tire moins. Les figer, c'était leur retirer le geste par lequel
        // l'effet devient visible : 0,27 de suppression relevée, et une riposte inchangée.
        // PATH reste coupé — ils ne quittent pas leur muret — mais ils ont le droit de
        // s'accroupir et de se coucher. ⟨Fable, 08/08⟩
        _u disableAI "PATH";
        _u setBehaviour "COMBAT"; _u setCombatMode "RED";
        _u setUnitPos "AUTO"; _u setDir 0;               // la posture est à EUX, désormais
        _u setVariable ["ap_n", 0]; _u setVariable ["ap_touche", 0];
        _u addEventHandler ["Fired", { (_this select 0) setVariable ["ap_n", ((_this select 0) getVariable ["ap_n",0]) + 1] }];
        _u addEventHandler ["HitPart", { private _o = (_this select 0) select 0;
            _o setVariable ["ap_touche", (_o getVariable ["ap_touche",0]) + 1] }];
        _u setVariable ["ap_load", getUnitLoadout _u];   // l equipement d origine, garde
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    sleep 3;

    // ---------------------------------------------------------------- les victimes
    private _gV = createGroup west;
    HMT_VIC = [];
    {
        private _p = _base vectorAdd [_x, 150, 0];
        private _u = _gV createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p;
        // ⚠️ PAS `allowDamage false` SUR LES VICTIMES. Il tuait mon SECOND CHEMIN : l evenement
        // `Hit` ne se declenche pas sur un homme invulnerable, et `delivre2` comptait 0 quand
        // `delivre` comptait 80. J avais depose une tolerance de 10 % entre deux chemins dont
        // l un etait MORT-NE. `HandleDamage` qui rend 0 fait les deux : il compte CHAQUE
        // impact et annule CHAQUE degat. Meme invulnerabilite, un chemin de plus.
        _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT";
        _u disableAI "TARGET"; _u disableAI "AUTOTARGET"; _u disableAI "FSM";
        _u setCombatMode "BLUE"; _u setBehaviour "CARELESS";
        _u setUnitPos "UP"; _u setDir 180;
        // ⚠️ LA GRANDEUR PRIMAIRE VIT ICI. Le fait certifié dit capacité x0,08, et il a été
        // mesuré en IMPACTS DÉLIVRÉS — par `HitPart`, jamais en coups partis. La suppression
        // d'Arma dégrade surtout la VISÉE : le nombre de coups peut ne pas bouger pendant que
        // leur valeur s'effondre. Ce que les défenseurs DÉLIVRENT sur les victimes, c'est leur
        // capacité de nuire. Les coups tirés passent en second.
        _u setVariable ["ap_recu", 0]; _u setVariable ["ap_recu2", 0];
        _u addEventHandler ["HitPart", { private _o = (_this select 0) select 0;
            _o setVariable ["ap_recu", (_o getVariable ["ap_recu",0]) + 1] }];
        // le SECOND chemin, independant du premier : `HandleDamage`, qui compte l impact ET
        // rend 0 pour que l homme n encaisse rien. Deux mecanismes distincts du moteur pour la
        // meme grandeur, comme la regle 11 l exige.
        _u addEventHandler ["HandleDamage", {
            private _o = _this select 0;
            _o setVariable ["ap_recu2", (_o getVariable ["ap_recu2",0]) + 1];
            0
        }];
        HMT_VIC pushBack _u;
    } forEach [-15, -5, 5, 15];

    // ---------------------------------------------------------------- l'appui
    private _gA = createGroup west;
    HMT_APP = [];
    {
        private _p = _base vectorAdd [150, _x, 0];
        private _u = _gA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        // ⚠️ `MOVE` N EST PLUS COUPE SUR L APPUI. Un homme qui ne peut pas bouger ne peut pas
        // TOURNER : le premier pre-vol de la v2 a mesure un angle median de 56 deg entre l axe
        // de l arme et la cible, et 480 tirs refuses sur 480. L appui ne pivotait jamais.
        // C est aussi l explication de la v1 : elle forcait le tir le long d une direction
        // FIXE ; selon le site, cette direction passait sur les defenseurs (366 impacts) ou a
        // cote (5). Ce n etait pas la suppression qui variait, c etait mon azimut fige.
        // PATH reste coupe : il ne doit pas se deplacer, seulement s orienter.
        _u disableAI "PATH"; _u disableAI "AUTOCOMBAT";
        _u disableAI "AUTOTARGET"; _u disableAI "FSM";
        // TARGET reste ACTIF : sans lui, doTarget ne fait pivoter personne.
        // ⚠️ COMBAT, PAS CARELESS. L angle mesure entre l axe de l arme et la cible valait
        // 56,0 puis 55,3 deg sur deux runs : un ecart CONSTANT n est pas une visee qui rate,
        // c est un decalage fixe — l arme etait BAISSEE. `CARELESS` met l arme au repos.
        // `COMBAT` l epaule ; `BLUE` garde le doigt hors de la detente.
        _u setCombatMode "BLUE"; _u setBehaviour "COMBAT";
        _u setUnitPos "UP"; _u setDir 270;
        _u setVariable ["ap_n", 0];
        _u addEventHandler ["Fired", { (_this select 0) setVariable ["ap_n", ((_this select 0) getVariable ["ap_n",0]) + 1] }];
        _u setVariable ["ap_load", getUnitLoadout _u];   // l equipement d origine, garde
        HMT_APP pushBack _u;
    } forEach [-10, 0, 10];
    sleep 3;
    { [_x] call HMT_DOTER } forEach (HMT_DEF + HMT_APP);
    (format ["HMT|AP|corps|def|%1|vic|%2|app|%3|murs|%4",
             count HMT_DEF, count HMT_VIC, count HMT_APP, count HMT_MUR]) call HMT_LOG;

    // ─────────────────── poser tout le dispositif sur un terrain donne
    // On DEPLACE les memes corps plutot que d en creer d autres : memes hommes, meme
    // equipement, memes compteurs — seul le terrain change, et c est ce qu on veut isoler.
    HMT_POSER = {
        params ["_b"];
        { (HMT_MUR select _forEachIndex) setPosATL (_b vectorAdd [_x + 1.5, 0, 0]);
          (HMT_MUR select _forEachIndex) setDir 0;
          (HMT_DEF select _forEachIndex) setPosATL (_b vectorAdd [_x, 0, 0]);
          (HMT_DEF select _forEachIndex) setDir 0;
        } forEach [-40, -24, -8, 8, 24, 40];
        { (HMT_VIC select _forEachIndex) setPosATL (_b vectorAdd [_x, 150, 0]);
          (HMT_VIC select _forEachIndex) setDir 180;
        } forEach [-15, -5, 5, 15];
        { (HMT_APP select _forEachIndex) setPosATL (_b vectorAdd [150, _x, 0]);
          (HMT_APP select _forEachIndex) setDir 270;
        } forEach [-10, 0, 10];
        sleep 4;
        (format ["HMT|AP|pose|%1|%2", round (_b select 0), round (_b select 1)]) call HMT_LOG;
    };

    // ─────────────────── la dotation, et le fil de detente qui la surveille
    // PLANCHER DE RESERVE, depose comme FIL DE DETENTE : aucun homme, d aucun role, d aucun
    // bras, ne descend sous 60 coups pendant un essai. Pas « pouvoir tirer a la fin » — un
    // fusil qui finit a trois cartouches passerait ce test-la apres avoir rationne sa derniere
    // minute, et l IA d Arma module son feu bien avant le chargeur vide. Avec la dotation
    // corrigee, ce controle NE DOIT JAMAIS CLAQUER. ⟨Fable, 09/08⟩
    HMT_RESERVE = {
        params ["_liste"];
        private _min = 99999;
        // `magazinesAmmo` est UNAIRE, pas binaire — et `_x` etait masque par la boucle interne.
        {
            private _u = _x; private _n = 0;
            { _n = _n + (_x select 1) } forEach (magazinesAmmo _u);
            if (_n < _min) then { _min = _n };
        } forEach _liste;
        _min
    };

    // ================================================================ un essai
    HMT_ESSAI = {
        // duree reglable : les PRE-VOLS tournent court (le diagnostic doit revenir vite), les
        // essais juges tournent 120 s. Trois lancements ont coute 5 minutes chacun pour
        // apprendre une chose qu une fenetre de 30 s disait deja.
        params ["_bras", "_rep", ["_T", 120]];

        // ⚠️ LES MUNITIONS SONT REFAITES A CHAQUE ESSAI. Sans ca, le banc s eteint tout seul :
        // un defenseur a tire 727 coups sur un essai, l appui 338 — ils en portent ~300. Au
        // troisieme essai tout le monde etait a sec, et le banc a continue a journaliser
        // consciencieusement des ZEROS pendant dix-huit essais. La visee restait bonne (0,4 deg),
        // les controles ne voyaient rien d anormal essai par essai : c est la panne silencieuse
        // du 235e accrochage sous une autre forme — un CONSOMMABLE non modelise.
        // Refait a l identique dans LES DEUX BRAS : personne n est avantage.
        // ⚠️ L EQUIPEMENT EST RESTAURE, PAS « recharge ». `setVehicleAmmo 1` ne remettait pas
        // le fusil en etat, et mon controle `someAmmo` repondait « oui » parce que l homme
        // gardait une grenade : le banc s eteignait au 4e essai avec 9 hommes « armes » sur 9.
        // Un controle qui ne peut pas voir la panne qu il surveille n est pas un controle.
        // ⚠️ AMENDEMENT N°1 ⟨regle 13, registre du 09/08⟩. La dotation est portee HORS
        // D ATTEINTE : les hommes tiraient 294 a 707 coups en 120 s pour ~300 en dotation, et
        // vidaient donc leur fusil PENDANT la mesure. Un plafond de munitions substitue a la
        // grandeur testee — la capacite a delivrer sous le feu — un mecanisme de PENURIE que
        // personne n a certifie ; le fait ×0,08 ne passe pas par la rarete.
        // Le seuil derive du mecanisme (707 observes, marge franche), pas des cellules.
        { _x setVariable ["ap_n", 0]; _x setVariable ["ap_touche", 0]; _x setDir 0;
          _x setUnitLoadout (_x getVariable "ap_load");
          [_x] call HMT_DOTER } forEach HMT_DEF;
        { _x setVariable ["ap_touche", 0] } forEach HMT_MUR;
        { _x setVariable ["ap_recu", 0]; _x setVariable ["ap_recu2", 0] } forEach HMT_VIC;
        // L'APPUI EST REMIS AU SILENCE, pas seulement remis à zéro : au premier run un coup
        // s'est échappé dans le bras témoin parce que la cible ordonnée au tour précédent
        // survivait. On supprime la cause plutôt que d'assouplir un critère déjà déposé.
        {
            _x setVariable ["ap_n", 0];
            _x setUnitLoadout (_x getVariable "ap_load");
            if (_bras != 0) then { [_x] call HMT_DOTER };
            _x doTarget objNull; _x doWatch objNull;
            _x setCombatMode "BLUE"; _x setBehaviour "COMBAT";
            // ⚠️ LE SILENCE SE COUPE A L ARME. Deux fois un coup s est echappe dans le bras
            // temoin : les defenseurs tirent sur l appui, et un homme en COMBAT riposte par
            // reflexe malgre `BLUE`. `FIREWEAPON` rend le tir impossible, c est net.
            if (_bras == 0) then {
                _x disableAI "TARGET"; _x disableAI "FIREWEAPON";
                // ⚠️ ET ON LUI RETIRE SES MUNITIONS. `disableAI "FIREWEAPON"` a laisse passer
                // jusqu a 3 coups sur 24 essais — negligeable en effet, fatal en principe : le
                // critere depose dit ZERO. On supprime la cause au lieu d assouplir le critere,
                // pour la troisieme fois de la nuit. Memes corps, memes places, meme exposition ;
                // seule la munition change, et le bras temoin est justement « l appui ne tire pas ».
                _x setVehicleAmmo 0;
            } else {
                _x enableAI "TARGET"; _x enableAI "FIREWEAPON";
            };
            // BRAS 2 : le feu de suppression NATIF. Il a besoin d un mode de combat qui
            // autorise le tir ; AUTOTARGET reste coupe pour qu il ne choisisse pas ses cibles.
            if (_bras == 2) then { _x setCombatMode "RED" };
        } forEach HMT_APP;
        HMT_ANGLES = [];
        HMT_VISES = [];
        HMT_REFUS = 0;
        HMT_CHARGE = 0;
        // RECENSEMENT D ENTREE : qui peut faire quoi AVANT qu on demande quoi que ce soit.
        // ⚠️ DESAGREGE PAR ROLE. L agregat cachait que CE NE SONT PAS LES MEMES HOMMES qui
        // s assechent : dans le bras natif les appuis DEVERSENT — c est la definition de
        // `commandSuppressiveFire` — pendant que les defenseurs, s ils sont supprimes,
        // economisent. Et le sens du biais s inverse selon qui a soif. ⟨regle 12⟩
        HMT_CAP0 = [HMT_DEF] call HMT_RECENSER;
        HMT_CAP0A = [HMT_APP] call HMT_RECENSER;
        HMT_RES = 99999;
        { if ((_x ammo (primaryWeapon _x)) > 0) then { HMT_CHARGE = HMT_CHARGE + 1 } }
          forEach (HMT_DEF + HMT_APP);
        sleep 5;
        // RÉVÉLATION IDENTIQUE AUX DEUX BRAS : un déclencheur qui dit QUAND, jamais COMMENT.
        { _gD reveal [_x, 4] } forEach HMT_VIC;
        sleep 2;

        // ─── PIEGE EN LECTURE PURE — pose le 10/08 a 21 h 30. AUCUNE COMMANDE ICI.
        // Le bras natif a tire 260, 206, 0, 0 coups sur quatre runs dont l empreinte du monde
        // est identique. La sonde a etabli que la radio prend 11 fois sur 12 en etat sain, ET
        // que l etat oisif NE SE FABRIQUE PAS par commande : des hommes dont `PATH` est coupe
        // ne sont jamais `unitReady`. Donc `3 sur 3 prets` au banc n etait pas une attente,
        // c est une SIGNATURE PATHOLOGIQUE DU GROUPE. Ce piege releve l etat complet du groupe
        // au moment exact ou l ordre part.
        // ⚠️ LECTURES SEULES : `group`, `leader`, `units`, `combatMode`, `behaviour`,
        // `unitReady`, `isNull`, `alive`, `getVariable`. Rien qui commande, rien qui corrige.
        // Aucun parametre depose n est touche ⟨Fable, 10/08 : « une instrumentation en lecture
        // pure ne touche aucun parametre depose »⟩ — mais elle change le monde, donc R15
        // s applique : le premier lancement garde qui passe le pre-vol sert de relecture
        // d aiguille avant que quoi que ce soit se certifie dessus.
        private _ga = group (HMT_APP select 0);
        private _chef = leader _ga;
        private _memeGrp = ({ group _x == _ga } count HMT_APP);
        private _chefEstApp = if (_chef in HMT_APP) then { 1 } else { 0 };
        // `ap_n` AVANT l ordre : ferme le trou d attribution de sept secondes que les sessions
        // 1 et 2 ne peuvent pas combler retroactivement.
        private _avant = 0;
        { _avant = _avant + (_x getVariable ["ap_n", 0]) } forEach HMT_APP;
        (format ["HMT|AP|GROUPE|bras|%1|effectif|%2|memegroupe|%3|chef_est_appui|%4|chef_nul|%5|chef_vivant|%6|prets|%7|mode|%8|comport|%9|apn_avant|%10",
                 _bras, count (units _ga), _memeGrp, _chefEstApp,
                 (if (isNull _chef) then {1} else {0}),
                 (if (alive _chef) then {1} else {0}),
                 ({ unitReady _x } count HMT_APP),
                 combatMode _ga, behaviour _chef, _avant]) call HMT_LOG;

        private _feu = [_bras, _T] spawn {
            params ["_b", "_T"];
            if (_b == 0) exitWith {};
            // ⟨Antistasi, fn_suppressingFire : `commandSuppressiveFire` + `suppressFor`. Huit
            //  lignes la ou j en ai ecrit deux cents. On les met AU BANC plutot que de les
            //  croire : c est le moteur contre mon script, et le temoin arbitre.⟩
            if (_b == 2) exitWith {
                // ⚠️ LE FEU NATIF A UNE LATENCE D AMORCAGE. Zero coup en 30 s la ou il en tire
                // 248 a 414 en 120 s. Mon feu force n en avait pas — c est une propriete du
                // mecanisme, pas un defaut. On reemet l ordre toutes les 4 s au lieu de 10,
                // et le pre-vol lui laisse 60 s au lieu de 30.
                private _t2 = time;
                while { time - _t2 < _T } do {
                    private _c = HMT_MUR select (floor (random (count HMT_MUR)));
                    // ⚠️ PAS DE `suppressFor` ICI. Je l avais recopie d Antistasi ce matin :
                    // cette commande SUPPRIME CELUI A QUI ON L APPLIQUE. J avais donc supprime
                    // mes propres tireurs, et le natif est passe de 248-414 coups a ZERO.
                    // Copier une ligne sans savoir ce qu elle fait, c est l inverse de la
                    // regle 7 : l inventaire oblige a LIRE, pas a recopier.
                    { _x commandSuppressiveFire _c } forEach HMT_APP;
                    sleep 4;
                };
            };
            private _t0 = time;
            while { time - _t0 < _T } do {
                // ⚠️ FEU DE ZONE : on vise le MURET, pas l homme. C est ce que fait un appui
                // reel — il bat la lisiere. Viser les hommes produisait 12 balles au corps en
                // 30 s : des morts, pas des supprimes. Les corps ne seront plus touches que
                // par debordement, et le regime devient celui de la mission.
                private _c = HMT_MUR select (floor (random (count HMT_MUR)));
                // on ORIENTE le corps vers la cible en plus de l ordre de visee : `doTarget`
                // seul ne suffisait pas. Puis on laisse le temps du pivot avant de tirer.
                { _x setDir (_x getDir _c); _x doWatch _c; _x doTarget _c } forEach HMT_APP;
                sleep 2.0;
                for "_k" from 1 to 4 do {
                    {
                        private _w = currentWeapon _x;
                        // ⚠️ LE TIR EST CONDITIONNÉ À LA VISÉE DE L'IA, plus forcé à l'aveugle.
                        // La v1 forçait le tir : un site rendait 366 impacts, le suivant 5.
                        // ON MESURE L ANGLE REEL entre l axe de l arme et la cible.
                        private _d1 = _x weaponDirection _w;
                        private _d2 = vectorNormalized ((getPosASL _c) vectorDiff (getPosASL _x));
                        private _dot = (_d1 vectorDotProduct _d2) min 1 max -1;
                        private _ang = acos _dot;
                        HMT_ANGLES pushBack _ang;
                        // ⚠️ ON TIRE SUR L ANGLE, PAS SUR `aimedAtTarget`. Une fois l arme
                        // epaulee, l angle est tombe a 0,2 deg — l arme pointe la cible — et
                        // `aimedAtTarget` refusait pourtant 96 tirs sur 96. Un score opaque
                        // disait non pendant que la geometrie disait oui.
                        // ⟨regle 6 : ne verifie pas l abstraction qui t arrange, verifie la
                        // propriete que le MECANISME utilise — ici, ou pointe le canon.⟩
                        // `aimedAtTarget` reste RELEVE, comme temoin, mais ne decide plus.
                        HMT_VISES pushBack (_x aimedAtTarget [_c, _w]);
                        if (_ang < 3.0) then {
                            _x forceWeaponFire [_w, currentWeaponMode _x];
                        } else {
                            HMT_REFUS = HMT_REFUS + 1;
                        };
                    } forEach HMT_APP;
                    sleep 0.45;
                };
            };
        };

        private _sup = [];
        private _t0 = time;
        while { time - _t0 < _T } do {
            private _s = 0;
            { _s = _s + (getSuppression _x) } forEach HMT_DEF;
            _sup pushBack (_s / (count HMT_DEF));
            // le fil de detente est surveille PENDANT la fenetre, pas seulement a la fin
            // ⚠️ LE PLANCHER NE PORTE QUE SUR CEUX QUI DOIVENT TIRER. Au bras temoin, les
            // trois appuis ont le fusil vide EXPRES — c est ainsi qu on garantit leur silence.
            // Prendre le minimum sur tout le monde faisait claquer le fil de detente a chaque
            // essai temoin, par construction. Troisieme fois qu un controle ignore le
            // dispositif qu il surveille : la premiere avec « armes == 9 », la deuxieme avec
            // le recensement agrege, celle-ci avec la reserve.
            private _r = [if (_bras == 0) then { HMT_DEF } else { HMT_DEF + HMT_APP }] call HMT_RESERVE;
            if (_r < HMT_RES) then { HMT_RES = _r };
            sleep 5;
        };
        waitUntil { scriptDone _feu };

        private _cD = 0; { _cD = _cD + (_x getVariable ["ap_n", 0]) } forEach HMT_DEF;
        private _cA = 0; { _cA = _cA + (_x getVariable ["ap_n", 0]) } forEach HMT_APP;
        private _tM = 0; { _tM = _tM + (_x getVariable ["ap_touche", 0]) } forEach HMT_MUR;
        private _tD = 0; { _tD = _tD + (_x getVariable ["ap_touche", 0]) } forEach HMT_DEF;
        private _sm = 0; { _sm = _sm + _x } forEach _sup;
        _sm = if (count _sup > 0) then { _sm / (count _sup) } else { -1 };
        private _am = -1;
        if (count HMT_ANGLES > 0) then {
            private _tri = +HMT_ANGLES; _tri sort true;
            _am = _tri select (floor ((count _tri) / 2));
        };

        private _vm = -1;
        if (count HMT_VISES > 0) then {
            private _s2 = 0; { _s2 = _s2 + _x } forEach HMT_VISES;
            _vm = _s2 / (count HMT_VISES);
        };
        private _dl = 0; { _dl = _dl + (_x getVariable ["ap_recu", 0]) } forEach HMT_VIC;
        // ⚠️ LE CONTROLE DE VITALITE PAR BRAS ⟨Fable, 09/08⟩. Il remplace le test d admission
        // des terrains, qui etait une porte a pile ou face : deux tirages bruites a 45 % ont
        // 60 % de chances de depasser une tolerance de 35 %, donc il recalait des terrains
        // parfaitement stables. Ce qu il faut verifier n est pas que le terrain rend deux fois
        // le meme chiffre — c est que CHAQUE BRAS A REELLEMENT JOUE, dans CHAQUE session.
        //   · le temoin est VIVANT s il delivre au-dessus du plancher ;
        //   · le bras de feu est ACTIF si ses appuis ont vraiment tire.
        // Une session ou le feu natif meurt en silence donne deux temoins impeccables et un
        // ratio qui glisse vers 1 — c est CE mensonge-la que le controle de bras attrape, et
        // qu aucune admission de terrain n aurait vu.
        // ⟨Fable⟩ le canal `behaviour` est journalise SANS ETRE JUGE : si le natif change un
        // jour de signe quelque part, l autopsie aura deja ses pieces. Deux lignes maintenant
        // valent une nuit plus tard.
        private _comb = { (behaviour _x) in ["COMBAT", "STEALTH"] } count HMT_DEF;
        // DOUBLE CHEMIN sur la grandeur qui decide ⟨regle 11⟩ : `HitPart` d un cote,
        // `HandleDamage` de l autre. ⚠️ ILS NE COMPTENT PAS LA MEME UNITE — `HitPart` compte
        // l impact, `HandleDamage` se declenche par partie du corps touchee. Mesure : 96 contre
        // 692 au pre-vol. Une tolerance a 10 % sur les COMPTES etait donc inapplicable ; le
        // critere porte desormais sur la STABILITE DE LEUR RAPPORT — si deux mecanismes voient
        // les memes evenements, leur facteur de conversion est constant. Redepose AVANT toute
        // mesure, seul moment ou l on en a le droit.
        private _dl2 = 0; { _dl2 = _dl2 + (_x getVariable ["ap_recu2", 0]) } forEach HMT_VIC;
        // RECENSEMENT DE SORTIE : ce qui a change pendant la fenetre. Un ecart entre les deux
        // NOMME la panne au lieu de laisser des zeros plausibles.
        private _cap1 = [HMT_DEF] call HMT_RECENSER;
        private _cap1a = [HMT_APP] call HMT_RECENSER;
        // ⚠️ ON NE DEVINE PLUS. Le recensement est passe de 9 hommes a 6 pendant l essai, et
        // les trois manquants sont les appuis — qui portent pourtant `allowDamage false` et ne
        // peuvent donc pas mourir de blessure. Mon hypothese evidente etant fausse, on MESURE
        // au lieu d en essayer une deuxieme : etat exact de chaque appui, en clair.
        {
            (format ["HMT|AP|appui|%1|vivant|%2|captif|%3|etat|%4|degats|%5|position|%6",
                     _forEachIndex,
                     (if (alive _x) then {1} else {0}),
                     (if (captive _x) then {1} else {0}),
                     lifeState _x, (round ((damage _x) * 100)) / 100,
                     str ((getPosATL _x) apply { round _x })]) call HMT_LOG;
        } forEach HMT_APP;
        // LE CONTROLE QUI MANQUAIT : ce qui reste dans les chargeurs a la fin. Un banc doit
        // savoir dire « je me suis eteint », pas seulement produire des zeros credibles.
        private _res = 0;
        { _res = _res + ({_x == (primaryWeapon _y)} count (magazines _y)) } forEach [];
        // on compte les CARTOUCHES DANS LE FUSIL au debut de l essai, pas « a-t-il quelque
        // chose sur lui ». C est la grandeur dont la panne depend.
        private _secs = HMT_CHARGE;
        (format ["HMT|AP|essai|%1|%2|terrain|%17|delivre|%13|delivre2|%18|combat|%19|armes|%14|cap0|%15|cap1|%16|coupsdef|%3|coupsapp|%4|murs|%5|corps|%6|angle|%7|refus|%8|vise|%9|supp|%10|vivants|%11|%12",
                 _bras, _rep, _cD, _cA, _tM, _tD,
                 (round (_am*10))/10, HMT_REFUS, (round (_vm*1000))/1000,
                 (round (_sm*1000))/1000,
                 ({alive _x} count HMT_DEF), ({alive _x} count HMT_VIC), _dl, _secs,
                 (HMT_CAP0 joinString ",") + "/" + (HMT_CAP0A joinString ","),
                 (_cap1 joinString ",") + "/" + (_cap1a joinString ",") + "/res" + str HMT_RES,
                 (missionNamespace getVariable ["HMT_SITE", -1]), _dl2, _comb]) call HMT_LOG;
        sleep 8;
    };

    // ================================================================ le plan
    // PRÉ-VOL DE PRÉSENCE : un essai témoin d'abord. Si les défenseurs ne tirent pas alors que
    // rien ne les gêne, le dispositif est cassé et les 24 essais ne mesureraient que mon erreur.
    [0, 0, 30] call HMT_ESSAI;
    // le pre-vol juge la MONNAIE de la grandeur primaire : sans appui, les defenseurs
    // doivent DELIVRER. S ils tirent sans jamais toucher, la grandeur ne peut pas baisser
    // et le banc serait muet par construction.
    private _pre = 0; { _pre = _pre + (_x getVariable ["ap_recu", 0]) } forEach HMT_VIC;
    if (_pre <= 0) exitWith { "HMT|AP|ECHEC|presence|les_defenseurs_ne_delivrent_rien" call HMT_LOG };
    (format ["HMT|OK|ap_presence|%1", _pre]) call HMT_LOG;

    // PRÉ-VOL D'ARRIVÉE : un essai appui, et les murets doivent encaisser. Sinon on s'arrête
    // tout de suite au lieu d'accumuler une heure de données muettes — c'est exactement ce
    // qui s'est produit deux fois avec la v1.
    [2, 0, 60] call HMT_ESSAI;    // le feu NATIF, avec le temps de s amorcer
    private _arr = 0; { _arr = _arr + (_x getVariable ["ap_touche", 0]) } forEach HMT_MUR;
    if (_arr <= 0) exitWith { "HMT|AP|ECHEC|arrivee|aucun_impact_sur_les_couverts" call HMT_LOG };
    (format ["HMT|OK|ap_arrivee|%1", _arr]) call HMT_LOG;

    // TROIS BRAS, alternes : temoin, feu scripte, feu natif. La regle de decision est
    // deposee AVANT : le professeur du n°2 adoptera l implementation qui passe, le NATIF
    // prefere a egalite — moins de code, moins de fautes. ⟨Fable, 08/08⟩
    private _plan = [];
    // 16 repetitions par bras au lieu de 8 : a n=8, l ecart de 216 a 182 impacts delivres
    // n etait pas separable du bruit. On paie deux heures de serveur pour une reponse
    // TRANCHEE plutot qu une reponse devinee.
    // ⚠️ LE FEU SCRIPTE EST SORTI DU CHEMIN D EXECUTION. Il allait de +57 % a -40 % selon
    // le terrain — et le +57 % venait d un TEMOIN qui s effondrait (79, 66, 314, 0 ; dispersion
    // de 120 %), pas d un appui qui ameliorait quoi que ce soit. Epitaphe : ILLISIBLE.
    // Ses chiffres sont au proces-verbal ; son code ne tourne plus.
    // ⟨Fable : « le professeur meurt, l instrument reste. La vraie production des deux cents
    //  lignes n a jamais ete le feu, ce sont les onze controles que leurs pannes ont forces. »⟩
    private _sess = missionNamespace getVariable ["HMT_SESSION", 1];
    _plan pushBack [2, _sess]; _plan pushBack [0, _sess];
    // LA SESSION EST UN BLOC. Chaque session joue UNE repetition par terrain et par bras ;
    // trois sessions donnent les trois repetitions. La stabilite inter-session se lit alors
    // sur le RATIO qui decide — la propriete que le mecanisme utilise — au lieu de se lire sur
    // un niveau qui ne decide de rien. Et ca ne coute pas un essai de plus. ⟨Fable, 09/08⟩
    private _phase = missionNamespace getVariable ["HMT_PHASE", 3];
    (format ["HMT|AP|phase|%1|terrains|%2", _phase, count HMT_SITES]) call HMT_LOG;

    if (false) then {
        // ─── PHASES 1 et 2 : UNE MESURE DE LIGNE DE BASE PAR TERRAIN, rien d autre.
        // Deux sessions SEPAREES, parce que l ennemi de ce banc est de session : fusils a sec
        // au 3e essai, panne au 235e accrochage. Deux runs adosses peuvent s accorder et
        // mentir ensemble. ⟨Fable, 09/08⟩
        {
            HMT_SITE = _forEachIndex;
            [_x] call HMT_POSER;
            [0, 1] call HMT_ESSAI;
            (format ["HMT|AP|base|phase|%1|terrain|%2|%3|%4",
                     _phase, HMT_SITE, round (_x select 0), round (_x select 1)]) call HMT_LOG;
        } forEach HMT_SITES;
        (format ["HMT|AP|TERMINE|base|phase|%1", _phase]) call HMT_LOG;
    };
    // ─── PLUS D ADMISSION PAR LIGNE DE BASE. Les phases 1 et 2 sont conservees dans le code
    // au cas ou, mais ne sont plus jamais appelees : le test qu elles servaient etait en panne.

    // ─── PHASE 3 : la campagne, sur les terrains ADMIS seulement.
    (format ["HMT|AP|plan|%1|essais|par|terrain|x|%2|terrains|session|%3",
             count _plan, count HMT_SITES, _sess]) call HMT_LOG;
    {
        HMT_SITE = _forEachIndex;
        [_x] call HMT_POSER;
        { _x call HMT_ESSAI } forEach _plan;
        (format ["HMT|AP|terrain_fini|%1", HMT_SITE]) call HMT_LOG;
    } forEach HMT_SITES;
    (format ["HMT|AP|TERMINE|session|%1", _sess]) call HMT_LOG;
};
