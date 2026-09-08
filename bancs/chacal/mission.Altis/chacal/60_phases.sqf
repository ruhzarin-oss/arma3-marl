// =====================================================================
// CHACAL - LA MACHINE A PHASES. Six phases, six criteres, six plafonds.
//
// Regle : une phase se termine sur son CRITERE ou elle EXPIRE. Aucune ne se
// termine parce que le temps prevu s est ecoule - sinon la mission serait une
// bande-son et le corpus ne contiendrait aucune decision.
//
// Ce que ce fichier doit garantir, et qui a coute cher a obtenir :
//   . le PLAN est une fonction de l ORDRE et des OBSERVATIONS, jamais d une
//     variable que le detachement ne peut pas connaitre ;
//   . le renseignement est CONSOMME : il choisit l ouverture, conditionne le
//     declenchement, et lui seul est restitue a l appui ;
//   . chaque ordre porte son POURQUOI - c est l etiquette dont un imitateur a
//     besoin, et elle manquait ;
//   . renoncer est une ISSUE, pas une panne.
// =====================================================================

CHACAL_SAUT = false;
CHACAL_ABANDON = false;
CHACAL_CAUSE_ABANDON = "";
CHACAL_INTEL = false;
CHACAL_CHARGES = [];              // ACTES : objectifs sur lesquels une charge a ete posee
CHACAL_DETRUITS = [];             // EFFET SCRIPTE : hors jugement tactique
CHACAL_VUES = [];                 // [unite, k] reellement observees par la reco
CHACAL_INSERTION_FORCEE = false;
CHACAL_QRF_PARTIE = false;
CHACAL_OUV_CHOISIE = [];
// ! Fable, 06/09 : la mise a feu devient une CONDITION ( personne a moins de
// 35 m ) et non une horloge, et les trois charges sautent ENSEMBLE - c est ce
// qu un detachement fait, et ca retire trois allers-retours, trois attentes et
// trois occasions de fratricide. Le succes compte des ACTES, donc l instant de
// la destruction n entre pas dans le verdict.
CHACAL_CHARGES_OBJ = [];          // [objectif, charge] : ce qui reste a faire sauter
CHACAL_RESERVE_FEU = 180;         // s gardees en fin de phase : un degagement, une mise a feu
CHACAL_SECURITE_FEU = 35;         // m : personne a moins de ca d une charge quand elle part
CHACAL_EXPLOITANT = objNull;
CHACAL_SEUIL_RENS = 3;            // sous ce compte, la crete n a rien vu
CHACAL_T_ALARME = -1; CHACAL_T_COMPROMIS = -1;
CHACAL_EXFIL_POINT = [];
CHACAL_GEL = false;

CHACAL_fnc_debutPhase = {
    params ["_n", "_nom", ["_plafond", 1e9]];
    // ! VIGNETTE : une phase posterieure a CHACAL_ARRET n ouvre rien et n ecrit
    // rien. Sinon le RPT porterait des phases jamais jouees et `phase_max` mentirait.
    if (CHACAL_FIN) exitWith {};
    CHACAL_PHASE = _n; CHACAL_PHASE_NOM = _nom;
    CHACAL_TPHASE = time; CHACAL_PLAFOND_COURANT = _plafond;
    (format ["CHACAL|PH|%1|%2|debut|%3|vivants|%4|compromis|%5|alarme|%6", _n, _nom, round (time * 100) / 100,
        count (CHACAL_FS select { alive _x }),
        (if (CHACAL_COMPROMIS) then {1} else {0}), (if (CHACAL_ALARME) then {1} else {0})]) call CHACAL_LOG;
};
CHACAL_fnc_finPhase = {
    params ["_n", "_nom", "_issue"];
    if (CHACAL_FIN && { _n > CHACAL_ARRET }) exitWith {};
    (format ["CHACAL|PH|%1|%2|fin|%3|%4|vivants|%5|compromis|%6|alarme|%7", _n, _nom, round (time * 100) / 100, _issue,
        count (CHACAL_FS select { alive _x }),
        (if (CHACAL_COMPROMIS) then {1} else {0}), (if (CHACAL_ALARME) then {1} else {0})]) call CHACAL_LOG;
    // ! LA VIGNETTE SE FERME ICI, et par le VERDICT : 70_verdict attend CHACAL_FIN,
    // emet sa ligne FINI, et le lanceur arrete le serveur dessus. On ne coupe pas
    // au plafond - un episode coupe au plafond n a pas d issue lisible.
    if (_n >= CHACAL_ARRET) then {
        (format ["CHACAL|OK|vignette|arret|%1|issue|%2", _n, _issue]) call CHACAL_LOG;
        CHACAL_FIN = true;
    };
};

CHACAL_fnc_ordreAller = {
    params ["_g", "_p", ["_vit", "LIMITED"], ["_comp", "STEALTH"], ["_form", "FILE"], ["_pourquoi", "-"]];
    if (isNull _g) exitWith {};
    // ! UN HOMME A QUI L ON ORDONNE DE MARCHER NE DOIT PAS ETRE EPINGLE A UNE
    // POSTURE. Mesure du 06/09, sonde de blocage, monde VIDE :
    //   blocage|ASSAUT|reste|171|commande|MOVE|pret|0|posture|CROUCH|eau|0
    // L ordre etait bien la, la cible etait sur la terre ferme, et les cinq
    // hommes n avancaient plus d un metre pendant onze minutes. La cause est de
    // mon fait : la phase 3 fait `setUnitPos "MIDDLE"` sur le gros pour qu il se
    // terre, la phase 4 detache l assaut DE CE MEME GROUPE, il herite de la
    // posture forcee, et un homme accroupi de force ne franchit pas ce qui
    // demande de se relever - `unitReady` reste faux et la file se fige.
    // La posture forcee n a de sens qu a l ARRET.
    // On libere la posture ET le regard : `doWatch CHACAL_SITE` pose sur l appui
    // et la reco n etait jamais leve - une main qui tire sur la tete pendant 2 km.
    { if (alive _x) then { _x setUnitPos "AUTO"; _x doWatch objNull } } forEach (units _g);
    while { count (waypoints _g) > 0 } do { deleteWaypoint ((waypoints _g) select 0) };
    _g setBehaviour _comp; _g setSpeedMode _vit; _g setFormation _form;
    private _w = _g addWaypoint [_p, 0];
    _w setWaypointType "MOVE"; _w setWaypointSpeed _vit; _w setWaypointBehaviour _comp; _w setWaypointFormation _form;
    (format ["CHACAL|E|ordre|%1|%2|%3|%4|pourquoi|%5", round (time * 100) / 100,
        (_g getVariable ["chacal_element", "DETACHEMENT"]), _p, CHACAL_PHASE, _pourquoi]) call CHACAL_LOG;
};

// ! LE DEFAUT LE PLUS COUTEUX DE TOUTE LA MISSION.
// Les `exitWith` de cette boucle etaient IMBRIQUES dans un `if ... then { }`.
// En SQF, `exitWith` quitte le scope COURANT : ici le bloc `then`, pas la
// boucle. La sortie " ils sont arrives " ne sortait de rien du tout, et
// `fnc_arrive` tournait TOUJOURS jusqu a son plafond, hommes poses sur
// l objectif depuis dix minutes. CHAQUE phase consommait son plafond au lieu
// de finir sur son critere : la phase 2 de 69 minutes, les 203 minutes
// annoncees, la phase 3 muette - c est cette ligne, et une seule.
// Remede : plus un seul `exitWith` imbrique. Un drapeau, et rien d autre.
//
// Une marche echoue quand elle CESSE DE SE RAPPROCHER, pas quand une horloge
// sonne : le critere est la stagnation, le plafond n est qu un filet.
//   ATTEINT . ENLISE . DETRUIT . PLAFOND . PLAFOND_PHASE . COMPROMIS . ABSENT
CHACAL_fnc_arrive = {
    params ["_g", "_p", "_ray", "_plafond", ["_stagn", 300]];
    if (isNull _g) exitWith { "ABSENT" };
    private _reste = call CHACAL_fnc_reste;
    if (_reste < _plafond) then { _plafond = _reste };
    if (_plafond <= 0) exitWith { "PLAFOND_PHASE" };
    if (CHACAL_SAUT) exitWith { "COMPROMIS" };
    private _t0 = time;
    private _dRef = 1e9; private _tRef = time;
    private _enlise = false; private _fini = false; private _mort = false;
    while { !_fini && (time - _t0 < _plafond) && !CHACAL_FIN && !CHACAL_SAUT } do {
        private _v = (units _g) select { alive _x };
        if (count _v == 0) then { _fini = true; _mort = true }
        else {
            private _c = _v call CHACAL_fnc_centre;
            if (count _c > 0) then {
                private _d = _c distance2D _p;
                if (_d < _ray) then { _fini = true }
                else {
                    if (_d < _dRef - 25) then { _dRef = _d; _tRef = time };
                    if (time - _tRef > _stagn) then { _fini = true; _enlise = true };
                };
            };
        };
        if (!_fini) then { sleep 2 };
    };
    if (_mort) exitWith { "DETRUIT" };
    private _v2 = (units _g) select { alive _x };
    if (count _v2 == 0) exitWith { "DETRUIT" };
    private _c2 = _v2 call CHACAL_fnc_centre;
    if (count _c2 > 0 && { (_c2 distance2D _p) < _ray }) exitWith { "ATTEINT" };
    if (_enlise) exitWith { "ENLISE" };
    if (CHACAL_SAUT) exitWith { "COMPROMIS" };
    "PLAFOND"
};

// ! REJOINDRE SA POSITION EST UN DEPLACEMENT, PAS UNE INFILTRATION.
// Mesure du 04/09, palier 2 : le detachement traverse la nuit sans etre
// detecte - `compromis|0`, zero perte des deux cotes - et n attaque JAMAIS,
// parce que la phase 4 a consomme ses 34 minutes sans que l assaut ni le
// bouchon soient arrives. Ils marchaient en LIMITED/STEALTH, environ 0,5 m/s
// de fermeture, sur 230 a 700 m. J avais ecrit une articulation que la nuit ne
// permet pas de realiser.
//
// Remede, et c est le motif que la phase 2 utilise deja : DEUX JAMBES. On
// rejoint en NORMAL/AWARE jusqu a 300 m de la position, puis on passe en
// LIMITED/STEALTH pour les derniers metres. La progression est journalisee
// toutes les 30 s - distance restante, vitesse, jambe - pour qu un " ils ne
// sont pas arrives " devienne repondable depuis le corpus, sans sonder le monde.
CHACAL_fnc_rejoindre = {
    params ["_g", "_p", "_ray", "_plafond", "_nom"];
    if (isNull _g) exitWith { "ABSENT" };
    [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_JAMBE_RAPIDE"] call CHACAL_fnc_ordreAller;
    private _t0 = time; private _tLog = time; private _tRef = time;
    private _dRef = 1e9; private _lente = false;
    private _fini = false; private _res = ""; private _immobile = 0;
    private _releve = false; private _dReleve = 1e9;
    while { !_fini && (time - _t0 < _plafond) && !CHACAL_FIN && !CHACAL_SAUT } do {
        private _v = (units _g) select { alive _x };
        if (count _v == 0) then { _fini = true; _res = "DETRUIT" }
        else {
            private _c = _v call CHACAL_fnc_centre;
            if (count _c > 0) then {
                private _d = _c distance2D _p;
                if (time - _tLog >= 30) then {
                    _tLog = time;
                    private _vit = 0;
                    { _vit = _vit + (speed _x) } forEach _v;
                    (format ["CHACAL|E|progression|%1|%2|reste|%3|vitesse|%4|jambe|%5|hommes|%6",
                        round (time * 100) / 100, _nom, round _d,
                        round ((_vit / (count _v)) * 10) / 10,
                        (if (_lente) then {"DISCRETE"} else {"RAPIDE"}), count _v]) call CHACAL_LOG;
                };
                // ! SONDE DE BLOCAGE ( 06/09 ). Au controle positif - monde VIDE,
                // aucun ennemi - l assaut s est arrete net a 170 m de sa position
                // et n a plus bouge pendant cinq minutes, vitesse 0. Ni feu, ni
                // furtivite, ni budget : un blocage. On demande donc au moteur
                // ce qu il croit faire, au lieu de le deduire.
                private _vm = 0; { _vm = _vm + (speed _x) } forEach _v;
                if ((_vm / (count _v)) < 0.5) then {
                    _immobile = _immobile + 1;

                    // ! UNE MISSION NE DOIT PAS DEPENDRE DU BON VOULOIR DU
                    // CALCULATEUR DE CHEMIN. Mesure du 06/09, monde VIDE : l appui
                    // et le bouchon arrivent, l assaut se fige TOUJOURS au meme
                    // anneau - 164 puis 170 m - avec `MOVE` en cours et
                    // `unitReady` faux. Ce n est ni la posture ni la furtivite,
                    // c est le chemin vers CE point.
                    // Un detachement bloque ne reste pas couche a regarder un
                    // obstacle : il se releve, puis il change d approche.
                    if (_immobile == 8) then {
                        (format ["CHACAL|E|deblocage|%1|%2|essai|RELEVER|reste|%3", round (time * 100) / 100, _nom, round _d]) call CHACAL_LOG;
                        [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_DEBLOCAGE_RELEVER"] call CHACAL_fnc_ordreAller;
                        // ! Le premier jet posait `_lente = true` et INTERDISAIT le retour
                        // en jambe discrete : les 170 derniers metres se couraient debout
                        // a 230 m d une garnison. Invisible dans le monde vide, mais dans
                        // le corpus la jambe discrete ne voudrait plus rien dire.
                        _lente = true; _releve = true; _dReleve = _d;
                    };
                    if (_immobile == 20) then {
                        private _neuf = [_p getPos [70, 60 + (240 call CHACAL_fnc_al)], 50] call CHACAL_fnc_plat;
                        (format ["CHACAL|E|deblocage|%1|%2|essai|CONTOURNER|vers|%3", round (time * 100) / 100, _nom, _neuf]) call CHACAL_LOG;
                        _p = _neuf;
                        [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_DEBLOCAGE_CONTOURNER"] call CHACAL_fnc_ordreAller;
                        _immobile = 0; _dRef = 1e9; _tRef = time;
                    };
                    if (_immobile == 5) then {
                        private _l = leader _g;
                        (format ["CHACAL|E|blocage|%1|%2|reste|%3|commande|%4|pret|%5|waypoints|%6|courant|%7|eau|%8|posture|%9|comport|%10|obstacles|%11|pente|%12",
                            round (time * 100) / 100, _nom, round _d,
                            currentCommand _l, (if (unitReady _l) then {1} else {0}),
                            count (waypoints _g), currentWaypoint _g,
                            (if (surfaceIsWater _p) then {1} else {0}),
                            stance _l, behaviour _l,
                            // `typeOf` rend vide sur un objet de terrain ; `str` rend le nom du p3d
                            ((nearestTerrainObjects [getPosATL _l, ["WALL","FENCE","ROCK","ROCKS","HIDE"], 12, false]) select [0,4]) apply { str _x },
                            round (atan (((getTerrainHeightASL ((getPosATL _l) getPos [10, (getPosATL _l) getDir _p])) - (getTerrainHeightASL (getPosATL _l))) / 10))]) call CHACAL_LOG;
                    };
                } else { _immobile = 0 };
                if (_d < _ray) then { _fini = true; _res = "ATTEINT" }
                else {
                    if (!_lente && { _d < 300 }) then {
                        _lente = true;
                        [_g, _p, "LIMITED", "STEALTH", "WEDGE", _nom + "_JAMBE_DISCRETE"] call CHACAL_fnc_ordreAller;
                    };
                    // une fois degage de quarante metres, on se recouche
                    if (_releve && { _d < _dReleve - 40 } && { _d < 300 }) then {
                        _releve = false;
                        [_g, _p, "LIMITED", "STEALTH", "WEDGE", _nom + "_RETOUR_JAMBE_DISCRETE"] call CHACAL_fnc_ordreAller;
                    };
                    if (_d < _dRef - 25) then { _dRef = _d; _tRef = time };
                    if (time - _tRef > 300) then { _fini = true; _res = "ENLISE" };
                };
            };
        };
        if (!_fini) then { sleep 3 };
    };
    if (_res == "") then { _res = if (CHACAL_SAUT) then {"COMPROMIS"} else {"PLAFOND"} };
    _res
};

// Le budget d une position rejointe en deux jambes : la jambe rapide a 1,1 m/s,
// les 300 derniers metres a 0,5 m/s, plus une marge d articulation.
CHACAL_fnc_budgetDeuxJambes = {
    params ["_g", "_p"];
    private _u = if (_g isEqualType grpNull) then { units _g } else { _g };
    _u = _u select { alive _x };
    if (count _u == 0) exitWith { 300 };
    private _c = _u call CHACAL_fnc_centre;
    if (count _c == 0) exitWith { 300 };
    private _d = _c distance2D _p;
    private _rapide = (_d - 300) max 0;
    private _lente = _d min 300;
    240 + (_rapide / 1.1) + (_lente / 0.5)
};

// ! ON DONNE A L IA UN POINT OU UN HOMME PEUT SE TENIR ( Fable, 06/09 ).
// Le premier jet visait `getPosATL _o` - un point situe DANS l objet - mesurait
// une distance 3D vers l origine du modele, et lisait le rayon sur la seule
// etendue X. Trois facons independantes de manquer la pose, et c est pourquoi
// les deux antennes rendaient `aucun_porteur_a_portee` alors que le groupe
// etait arrive. On calcule donc un point HORS de l emprise, DANS l enceinte, le
// plus loin possible des autres structures, et on mesure en 2D vers ce point.
CHACAL_fnc_emprise = {
    private _bb = boundingBoxReal _this;
    private _ex = ((_bb select 1) select 0) - ((_bb select 0) select 0);
    private _ey = ((_bb select 1) select 1) - ((_bb select 0) select 1);
    (_ex max _ey) / 2
};
CHACAL_fnc_pointDePose = {
    params ["_o"];
    private _pO = getPosATL _o; _pO set [2, 0];
    private _r = (_o call CHACAL_fnc_emprise) + 4;
    private _az0 = if (_o isEqualTo CHACAL_PC) then { _pO getDir CHACAL_OUV_CHOISIE } else { _pO getDir CHACAL_SITE };
    private _best = _pO getPos [_r, _az0]; private _sc = -1;
    {
        private _p = _pO getPos [_r, _az0 + _x]; _p set [2, 0];
        if ((_p distance2D CHACAL_SITE) < (CHACAL_RAYON - 5)) then {
            private _dmin = 8;
            { if (!(_x isEqualTo _o)) then { _dmin = _dmin min (_p distance2D _x) } }
                forEach (nearestObjects [_p, ["Building", "Static"], 8]);
            if (_dmin > _sc) then { _sc = _dmin; _best = _p };
        };
    } forEach [0, 45, -45, 90, -90, 135, -135];
    _best
};

// ! L EXPLOITATION NE TIRE JAMAIS LE CHEF ( Fable, 06/09 ). Le premier jet
// faisait `doMove` sur le chef de l assaut toutes les 3 s pendant 600 s, phase 6
// comprise : un `doMove` sur le chef deplace tout l element, et l assaut etait
// ramene vers le portable PENDANT l exfiltration.
CHACAL_fnc_exploiter = {
    private _l = leader CHACAL_gAssaut;
    private _cand = (units CHACAL_gAssaut) select { alive _x && { _x != _l } };
    private _pref = _cand select { (_x getVariable ["chacal_role", ""]) in ["ADJOINT", "MEDECIN"] };
    if (count _pref > 0) then { _cand = _pref };
    if (count _cand == 0) exitWith {};
    CHACAL_EXPLOITANT = _cand select 0;
    private _h = CHACAL_EXPLOITANT;
    (format ["CHACAL|E|ordre|%1|EXPLOITATION|%2|%3|pourquoi|OPORD_TERMINAL|par|%4", round (time * 100) / 100,
        getPosATL CHACAL_PORTABLE, CHACAL_PHASE, (_h getVariable ["chacal_role", ""])]) call CHACAL_LOG;
    _h doMove (getPosATL CHACAL_PORTABLE);
    private _t = time; private _dedans = 0; private _tOrdre = time;
    while { !CHACAL_INTEL && { alive _h } && (time - _t < 100 * CHACAL_ECHELLE) && !CHACAL_FIN } do {
        if ((_h distance2D CHACAL_PORTABLE) < 4) then { _dedans = _dedans + 2 } else {
            _dedans = 0;
            if (time - _tOrdre > 20) then { _h doMove (getPosATL CHACAL_PORTABLE); _tOrdre = time };
        };
        if (_dedans >= (60 * CHACAL_ECHELLE)) then {
            CHACAL_INTEL = true;
            (format ["CHACAL|E|exploitation|%1|reussie|par|%2", round (time * 100) / 100, (_h getVariable ["chacal_role", ""])]) call CHACAL_LOG;
        };
        sleep 2;
    };
    if (!CHACAL_INTEL) then {
        (format ["CHACAL|E|exploitation|%1|manquee|distance|%2", round (time * 100) / 100, round (_h distance2D CHACAL_PORTABLE)]) call CHACAL_LOG;
    };
    if (alive _h) then { _h doFollow (leader CHACAL_gAssaut) };
};

// ! LA MISE A FEU EST UNE CONDITION, PAS UNE HORLOGE. On ne fait pas sauter ses
// propres hommes : si quelqu un est encore a moins de 35 m d une charge apres
// 90 s, l acte reste COMPTE et l effet est REFUSE, et dit.
CHACAL_fnc_miseAFeu = {
    params [["_degagement", "-"]];
    if (count CHACAL_CHARGES_OBJ == 0) exitWith {
        (format ["CHACAL|E|mise_a_feu|%1|aucune_charge|degagement|%2", round (time * 100) / 100, _degagement]) call CHACAL_LOG;
    };
    private _fnProches = {
        private _n = 0;
        {
            private _c = _x select 1;
            if (!isNull _c) then { _n = _n + ({ alive _x && { (_x distance2D _c) < CHACAL_SECURITE_FEU } } count CHACAL_FS) };
        } forEach CHACAL_CHARGES_OBJ;
        _n
    };
    private _t = time; private _proches = call _fnProches;
    while { _proches > 0 && (time - _t < 90 * CHACAL_ECHELLE) && !CHACAL_FIN } do { sleep 3; _proches = call _fnProches };
    if (_proches > 0) exitWith {
        (format ["CHACAL|E|mise_a_feu|%1|REFUSEE|hommes_a_portee|%2|attente|%3|degagement|%4", round (time * 100) / 100,
            _proches, round (time - _t), _degagement]) call CHACAL_LOG;
    };
    (format ["CHACAL|E|mise_a_feu|%1|charges|%2|attente|%3|degagement|%4", round (time * 100) / 100,
        count CHACAL_CHARGES_OBJ, round (time - _t), _degagement]) call CHACAL_LOG;
    { private _c = _x select 1; if (!isNull _c) then { _c setDamage 1 } } forEach CHACAL_CHARGES_OBJ;
    sleep 2;
    {
        private _o = _x select 0;
        if (alive _o) then { _o setDamage 1 };
        CHACAL_DETRUITS pushBackUnique _o;
        (format ["CHACAL|E|destruction|%1|%2|effet_scripte|total|%3", round (time * 100) / 100, typeOf _o, count CHACAL_DETRUITS]) call CHACAL_LOG;
    } forEach CHACAL_CHARGES_OBJ;
};

CHACAL_fnc_enPlace = {
    params ["_g", "_p", "_ray"];
    if (isNull _g) exitWith { false };
    private _v = (units _g) select { alive _x };
    if (count _v == 0) exitWith { false };
    private _c = _v call CHACAL_fnc_centre;
    (count _c > 0) && { (_c distance2D _p) < _ray }
};

// =====================================================================
// L ALARME EST A L ENNEMI. LA COMPROMISSION EST A NOUS. Ce sont deux choses.
//
// L alarme lit `knowsAbout` du camp EST : legitime, c est l ennemi qui reagit a
// ce que l ennemi sait. Elle declenche la garnison et la reserve.
//
// La compromission est ce dont LE DETACHEMENT se rend compte : un coup pres de
// lui, un homme touche, un rouge vu passant en combat. C est elle, et elle
// seule, qui pilote les bleus - le premier jet declenchait la reaction BLUFOR
// sur la connaissance de l ENNEMI, que le detachement ne peut pas avoir.
// L ecart entre les deux instants est journalise : c est une latence de
// surprise que personne n a mesuree.
// =====================================================================
CHACAL_fnc_compromettre = {
    params ["_cause"];
    if (CHACAL_COMPROMIS) exitWith {};
    CHACAL_COMPROMIS = true; CHACAL_T_COMPROMIS = time;
    (format ["CHACAL|E|compromis|%1|cause|%2|phase|%3|latence_oracle|%4", round (time * 100) / 100,
        _cause, CHACAL_PHASE,
        (if (CHACAL_T_ALARME < 0) then {-1} else { round ((time - CHACAL_T_ALARME) * 100) / 100 })]) call CHACAL_LOG;
    if (CHACAL_PHASE < 5) then { CHACAL_SAUT = true };

    // ! LE REFLEXE DE RUPTURE NE VAUT QUE TANT QU ON N ASSAILLE PAS.
    // La premiere fois que la mission a atteint la phase 5, la compromission
    // est tombee - ce qui est NORMAL, on assaille - et ce reflexe a envoye
    // l element d assaut a 800 m de l objectif. J avais corrige " la file
    // marche sous plan apres la mort des chefs " en fabriquant " l assaut rompt
    // le contact au moment d assaillir ".
    private _bl = if (CHACAL_PHASE < 5) then { CHACAL_FS select { alive _x } } else { [] };
    if (count _bl > 0) then {
        private _c = _bl call CHACAL_fnc_centre;
        private _menace = [];
        {
            private _e = _x;
            if ({ [_x, _e, 900] call CHACAL_fnc_voit } count _bl > 0) exitWith { _menace = getPosATL _e };
        } forEach ((allUnits + vehicles) select {
            alive _x && { side (if (_x isKindOf "CAManBase") then {_x} else {effectiveCommander _x}) == east } });
        private _az = if (count _menace > 0) then { _menace getDir _c } else { CHACAL_SITE getDir _c };
        private _fuite = _c getPos [400, _az];
        {
            if (!isNull _x) then {
                _x setBehaviour "COMBAT"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
                [_x, _fuite, "FULL", "COMBAT", "WEDGE", "RUPTURE_CONTACT"] call CHACAL_fnc_ordreAller;
            };
        } forEach ([CHACAL_gFS, CHACAL_gReco, CHACAL_gAppui, CHACAL_gAssaut, CHACAL_gBouchon] select { !isNull _x });
        (format ["CHACAL|E|rupture|%1|vers|%2|menace_percue|%3", round (time * 100) / 100,
            _fuite, (if (count _menace > 0) then {1} else {0})]) call CHACAL_LOG;
    };
};

// les trois sens du detachement
{
    _x addEventHandler ["FiredNear", {
        params ["_u", "_tireur", "_dist"];
        if (_dist < 45 && { side _tireur != west }) then { ["FEU_PROCHE"] call CHACAL_fnc_compromettre };
    }];
    _x addEventHandler ["Hit", {
        params ["_u", "_source"];
        if (!isNull _source && { side _source != west }) then { ["COUP_RECU"] call CHACAL_fnc_compromettre };
    }];
} forEach CHACAL_FS;

// et le troisieme : un rouge que NOUS voyons, et qui vient de passer en combat
[] spawn {
    while { !CHACAL_COMPROMIS && !CHACAL_FIN } do {
        private _bl = CHACAL_FS select { alive _x };
        if (count _bl > 0) then {
            {
                private _e = _x;
                if ({ [_x, _e, 700] call CHACAL_fnc_voit } count _bl > 0) exitWith { ["ENNEMI_VU_EN_COMBAT"] call CHACAL_fnc_compromettre };
            } forEach (CHACAL_EST_SITE select { alive _x && { behaviour _x == "COMBAT" } });
        };
        sleep 2;
    };
};

// ! LE REFLEXE DE LA FILE. Une file de nuit qui voit un rouge a 400 m ne
// continue pas de marcher : elle se fige et se plaque. Sans ce reflexe, la
// seule reponse du corpus a " un ennemi apparait " est " continuer au meme
// pas ", ce qui n est le comportement de personne.
[] spawn {
    waitUntil { sleep 1; CHACAL_PHASE >= 2 };
    // ! LE REFLEXE NE VAUT QUE PENDANT L INFILTRATION. En phase 4 le detachement
    // se porte deliberement a 230 m d une garnison : y voir un rouge est ATTENDU,
    // et figer toute la file 30 s a chaque fois interdit d arriver. Meme erreur
    // que le reflexe de rupture applique a l assaut - un bon reflexe hors de son
    // regime devient un blocage.
    while { !CHACAL_FIN && CHACAL_PHASE < 4 } do {
        private _bl = CHACAL_FS select { alive _x };
        if (count _bl > 0) then {
            private _rouges = (allUnits + vehicles) select {
                alive _x && { (_x distance (_bl select 0)) < 500 }
                && { side (if (_x isKindOf "CAManBase") then {_x} else {effectiveCommander _x}) == east } };
            private _vu = false;
            { private _e = _x; if ({ [_x, _e, 500] call CHACAL_fnc_voit } count _bl > 0) exitWith { _vu = true } } forEach _rouges;
            if (_vu && !CHACAL_GEL && !CHACAL_SAUT) then {
                CHACAL_GEL = true;
                { doStop _x; _x setUnitPos "DOWN" } forEach _bl;
                (format ["CHACAL|E|reflexe|%1|gel|phase|%2", round (time * 100) / 100, CHACAL_PHASE]) call CHACAL_LOG;
                private _t = time;
                while { CHACAL_GEL && !CHACAL_FIN && !CHACAL_SAUT } do {
                    sleep 3;
                    private _b2 = CHACAL_FS select { alive _x };
                    private _encore = false;
                    { private _e = _x; if ({ [_x, _e, 500] call CHACAL_fnc_voit } count _b2 > 0) exitWith { _encore = true } } forEach _rouges;
                    if (_encore) then { _t = time };
                    if (time - _t > 30) then { CHACAL_GEL = false };
                };
                { if (alive _x) then { _x setUnitPos "AUTO"; _x doFollow (leader (group _x)) } } forEach (CHACAL_FS select { alive _x });
                (format ["CHACAL|E|reflexe|%1|degel|phase|%2", round (time * 100) / 100, CHACAL_PHASE]) call CHACAL_LOG;
            };
        };
        sleep 3;
    };
};

// L ORACLE : ce que l ennemi sait. Il pilote l ennemi, JAMAIS les bleus, et
// reste journalise pour mesurer la latence de surprise.
[] spawn {
    while { !CHACAL_ALARME && !CHACAL_FIN } do {
        private _m = 0;
        { private _k = east knowsAbout _x; if (_k > _m) then { _m = _k } } forEach (CHACAL_FS select { alive _x });
        if (_m > 1.4) then { CHACAL_ALARME = true; CHACAL_T_ALARME = time };
        sleep 1;
    };
    if (CHACAL_FIN) exitWith {};
    (format ["CHACAL|E|oracle_alarme|%1|phase|%2", round (time * 100) / 100, CHACAL_PHASE]) call CHACAL_LOG;
    { if (!isNull _x) then { _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSpeedMode "FULL" } } forEach CHACAL_GROUPES_EST;

    // La reserve met du temps a partir, et du temps a arriver : 6 km de route.
    // C est ce delai qui donne un sens au bouchon, donc a la phase 4.
    sleep (CHACAL_PAL_DELAI + (30 call CHACAL_fnc_al));
    CHACAL_QRF_PARTIE = true;
    (format ["CHACAL|E|qrf_partie|%1", round (time * 100) / 100]) call CHACAL_LOG;
    CHACAL_gQrf setBehaviour "AWARE"; CHACAL_gQrf setCombatMode "RED"; CHACAL_gQrf setSpeedMode "FULL";
    while { count (waypoints CHACAL_gQrf) > 0 } do { deleteWaypoint ((waypoints CHACAL_gQrf) select 0) };
    private _w = CHACAL_gQrf addWaypoint [CHACAL_SITE, 0];
    _w setWaypointType "SAD"; _w setWaypointSpeed "FULL"; _w setWaypointBehaviour "AWARE";
    // ! SIGNATURE : LAMBS attend [groupe, RAYON, cycle, aire, position]. Passer
    // [groupe, position, rayon] est rejete - Type Array, expected Number - et
    // la reserve ne chassait JAMAIS de tout l episode sans que rien le dise.
    if (CHACAL_LAMBS) then { [CHACAL_gQrf, 450, 30, [], CHACAL_SITE] spawn lambs_wp_fnc_taskHunt };
};

// =====================================================================
[] spawn {
sleep 3;
if (CHACAL_ISSUE == "VOID") exitWith { CHACAL_FIN = true };

// L ORDRE INITIAL. Ce que le detachement sait LEGITIMEMENT avant de partir :
// site, crete candidate, route, base de reserve, depose, point de secours,
// ouvertures. Tout le reste doit venir de ce qu il observe.
CHACAL_OPORD = [CHACAL_SITE, CHACAL_OP, CHACAL_ROUTE, CHACAL_QRF_BASE, CHACAL_LZ, CHACAL_PZ, CHACAL_RALLY];
(format ["CHACAL|E|opord|%1|site|%2|crete|%3|route|%4|reserve|%5|depose|%6|secours|%7|rally|%8|ouvertures|%9",
    round (time * 100) / 100, CHACAL_SITE, CHACAL_OP, CHACAL_ROUTE, CHACAL_QRF_BASE,
    CHACAL_LZ, CHACAL_PZ, CHACAL_RALLY, CHACAL_OUV_AZ]) call CHACAL_LOG;

private _plafond = 0; private _issue = ""; private _r = ""; private _t0 = time;

// ! DEUX EPISODES COMPLETS, DEUX COMPROMISSIONS DANS L APPROCHE : les phases 3,
// 4 et 5 n avaient jamais ete jouees et la question qui decide de la mission -
// la crete voit-elle a 800 m de nuit - n avait aucune reponse. `CHACAL_DEPART`
// pose le detachement au regroupement. C est un DIAGNOSTIC : l episode est
// marque hors corpus, son approche n ayant pas eu lieu.
if (CHACAL_DEPART >= 3) then {
    (format ["CHACAL|AVERT|hors_corpus|depart|%1|approche_non_jouee", CHACAL_DEPART]) call CHACAL_LOG;
    { if (alive _x) then { _x setPosATL (CHACAL_RALLY getPos [8 + (14 call CHACAL_fnc_al), 360 call CHACAL_fnc_al]) } } forEach CHACAL_FS;
    CHACAL_gFS setBehaviour "STEALTH"; CHACAL_gFS setCombatMode "GREEN";
    CHACAL_gFS setSpeedMode "LIMITED"; CHACAL_gFS setFormation "FILE";
    (format ["CHACAL|E|depart_direct|%1|au_rally|%2", round (time * 100) / 100, CHACAL_RALLY]) call CHACAL_LOG;
    sleep 5;
} else {

// ---------------------------------------------------------------------
// PHASE 1 - INSERTION
// ---------------------------------------------------------------------
_plafond = 1 call CHACAL_fnc_duree;
[1, "INSERTION", _plafond] call CHACAL_fnc_debutPhase;

CHACAL_HELO = objNull;
if (["B_Heli_Transport_01_F"] call CHACAL_fnc_has) then {
    private _dep = CHACAL_LZ getPos [3400, (CHACAL_LZ getDir CHACAL_SITE) + 180];
    CHACAL_HELO = createVehicle ["B_Heli_Transport_01_F", [_dep select 0, _dep select 1, 140], [], 0, "FLY"];
    createVehicleCrew CHACAL_HELO;
    call CHACAL_fnc_recenser;   // un equipage neuf ne doit pas passer 2 s sans identite
    CHACAL_HELO flyInHeight 60;
    private _gh = group (driver CHACAL_HELO);
    _gh setBehaviour "CARELESS"; _gh setCombatMode "BLUE";
    { _x assignAsCargo CHACAL_HELO; _x moveInCargo CHACAL_HELO } forEach CHACAL_FS;
    private _w = _gh addWaypoint [CHACAL_LZ, 0];
    _w setWaypointType "MOVE"; _w setWaypointSpeed "FULL";
};

// Les plafonds physiques ne sont PAS a l echelle : un vol de 3,4 km est une
// duree du MONDE. CHACAL_ECHELLE raccourcit les plafonds TACTIQUES et rien d autre.
private _pose = false;
if (!isNull CHACAL_HELO) then {
    private _tv = time;
    waitUntil { sleep 2; (CHACAL_HELO distance2D CHACAL_LZ < 250) || (time - _tv > 300) || CHACAL_FIN };
    if (CHACAL_HELO distance2D CHACAL_LZ < 600) then {
        CHACAL_HELO land "GET OUT";
        private _tl = time;
        waitUntil { sleep 1; (((getPosATL CHACAL_HELO) select 2) < 1.5 && { (speed CHACAL_HELO) < 3 }) || (time - _tl > 120) || CHACAL_FIN };
    };
    _pose = (((getPosATL CHACAL_HELO) select 2) < 2.5) && { (speed CHACAL_HELO) < 5 };
    if (!_pose) then {
        CHACAL_INSERTION_FORCEE = true;
        CHACAL_HELO setPosATL [CHACAL_LZ select 0, CHACAL_LZ select 1, 0.3];
        CHACAL_HELO setVelocity [0, 0, 0];
        sleep 2;
        (format ["CHACAL|AVERT|insertion_forcee|%1|appareil_pose_a_la_main", round (time * 100) / 100]) call CHACAL_LOG;
    };

    // ! QUATRE INSERTIONS, QUATRE CAUSES DE MORT DIFFERENTES :
    //   debus en vol -> 8 morts de chute ; depose a portee de la patrouille ->
    //   3 morts a la mitrailleuse ; `moveOut` en une passe -> 3 hommes restes
    //   en soute ; moteur coupe puis debus -> 1 mort ECRASE, sans tueur.
    // La cause commune : on laissait la PHYSIQUE placer dix hommes sous huit
    // tonnes. Le VOL est la partie realiste et observable - c est lui qui expose
    // le detachement - ; le debus ne l est pas. On le rend DETERMINISTE.
    private _k = 0;
    {
        if (alive _x) then {
            unassignVehicle _x; moveOut _x;
            _x setPosATL (CHACAL_HELO getPos [15, _k * 36]);
            _k = _k + 1;
        };
    } forEach CHACAL_FS;
    sleep 3;
    {
        if (alive _x && { vehicle _x != _x }) then {
            unassignVehicle _x; moveOut _x;
            _x setPosATL (CHACAL_HELO getPos [15, _k * 36]); _k = _k + 1;
        };
    } forEach CHACAL_FS;
    sleep 2;
};

// Le critere est ETRE SORTI ET VIVANT. L ecart au point prevu est une MESURE,
// pas une porte : un helicoptere qui se pose 350 m plus loin a insere.
private _auSol = CHACAL_FS select { alive _x && { vehicle _x == _x } };
private _ecart = if (count _auSol > 0) then { round ((_auSol call CHACAL_fnc_centre) distance2D CHACAL_LZ) } else { -1 };
(format ["CHACAL|E|debarquement|%1|au_sol|%2|ecart_lz|%3|helico_pose|%4|methode|ANNEAU_SCRIPTE", round (time * 100) / 100,
    count _auSol, _ecart, (if (_pose) then {1} else {0})]) call CHACAL_LOG;

private _morts = 10 - (count (CHACAL_FS select { alive _x }));
if (_morts > 0) exitWith {
    // Une insertion qui tue n est pas une insertion. On ne la rattrape pas : on
    // REFUSE l episode. Continuer a huit produirait un corpus ou l echec serait
    // mis au compte de la tactique.
    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "INSERTION_MORTELLE";
    (format ["CHACAL|VOID|insertion|%1|morts|%2|au_sol|%3", round (time * 100) / 100, _morts, count _auSol]) call CHACAL_LOG;
    CHACAL_FIN = true;
};
if (count _auSol < 10) exitWith {
    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "INSERTION_INCOMPLETE";
    (format ["CHACAL|VOID|insertion|%1|au_sol|%2", round (time * 100) / 100, count _auSol]) call CHACAL_LOG;
    CHACAL_FIN = true;
};
_issue = if (CHACAL_INSERTION_FORCEE) then {"FORCEE"} else {"ATTEINT"};

if (!isNull CHACAL_HELO) then {
    private _gh = group (driver CHACAL_HELO);
    if (!isNull _gh) then {
        while { count (waypoints _gh) > 0 } do { deleteWaypoint ((waypoints _gh) select 0) };
        private _rr = _gh addWaypoint [CHACAL_LZ getPos [5000, (CHACAL_LZ getDir CHACAL_SITE) + 180], 0];
        _rr setWaypointType "MOVE"; _rr setWaypointSpeed "FULL";
    };
    // Sans cette ligne, trois identifiants quittent le flux d etat sans ligne
    // `mort` : un lecteur ne peut pas distinguer un retrait scripte d une mort
    // non journalisee, et il ne doit pas avoir a deviner.
    [] spawn {
        sleep 240;
        if (!isNull CHACAL_HELO) then {
            { (format ["CHACAL|E|retrait|%1|%2|equipage_helicoptere", round (time * 100) / 100,
                (_x getVariable ["chacal_id", -1])]) call CHACAL_LOG; deleteVehicle _x } forEach (crew CHACAL_HELO);
            deleteVehicle CHACAL_HELO;
        };
    };
};

CHACAL_gFS setBehaviour "STEALTH"; CHACAL_gFS setCombatMode "GREEN";
CHACAL_gFS setSpeedMode "LIMITED"; CHACAL_gFS setFormation "FILE";
sleep (60 * CHACAL_ECHELLE);
[1, "INSERTION", _issue] call CHACAL_fnc_finPhase;

// ---------------------------------------------------------------------
// PHASE 2 - APPROCHE, et le franchissement de la route
// ---------------------------------------------------------------------
if (CHACAL_FIN) exitWith {};   // vignette close a la phase 1
_plafond = 2 call CHACAL_fnc_duree;
[2, "APPROCHE", _plafond] call CHACAL_fnc_debutPhase;

private _fr = CHACAL_ROUTE;
private _avant = _fr getPos [260, _fr getDir CHACAL_LZ];

// DEUX JAMBES, et c est de la tactique : loin de l objectif on marche, a moins
// de 1,5 km on se traine. Ramper sur 4 km n est pas de la furtivite.
private _b1 = [CHACAL_gFS, _avant, 0.7] call CHACAL_fnc_budget;
(format ["CHACAL|E|budget|%1|etape|APPROCHE_ROUTE|distance|%2|plafond|%3", round (time * 100) / 100,
    round (((units CHACAL_gFS) call CHACAL_fnc_centre) distance2D _avant), round _b1]) call CHACAL_LOG;
[CHACAL_gFS, _avant, "NORMAL", "AWARE", "FILE", "OPORD_ROUTE_JAMBE_LOINTAINE"] call CHACAL_fnc_ordreAller;
_r = [CHACAL_gFS, _avant, 60, _b1] call CHACAL_fnc_arrive;

// ! LA FENETRE SE DECIDE SUR CE QUE LA FILE PERCOIT, PAS SUR LA POSITION VRAIE.
// Le premier jet lisait `CHACAL_VEH_ROUTE distance2D _avant`, que personne dans
// la file ne peut connaitre : l eleve aurait appris a attendre un nombre
// invisible. Ici, rien que le canal geometrique. Consequence assumee : de nuit
// ils peuvent ne JAMAIS voir le vehicule et traverser en aveugle. C est une
// donnee, et elle est etiquetee.
if ((_r in ["ATTEINT", "ENLISE"]) && !CHACAL_SAUT) then {
    { doStop _x } forEach (units CHACAL_gFS);
    private _tf = time;
    private _dejaVu = false; private _dernierVu = -1; private _traverse = false; private _cause = "";
    while { !_traverse && (time - _tf < 420 * CHACAL_ECHELLE) && ((call CHACAL_fnc_reste) > 0) && !CHACAL_SAUT && !CHACAL_FIN } do {
        private _v = CHACAL_VEH_ROUTE;
        private _vu = false;
        if (!isNull _v && { alive _v }) then {
            private _hommes = (units CHACAL_gFS) select { alive _x };
            _vu = ({ [_x, _v, 800, 70] call CHACAL_fnc_voit } count _hommes) > 0;
        };
        if (_vu) then { _dejaVu = true; _dernierVu = time };
        if (_dejaVu && { !_vu } && { (time - _dernierVu) > (45 * CHACAL_ECHELLE) }) then { _traverse = true; _cause = "FENETRE_OBSERVEE" };
        if (!_dejaVu && { (time - _tf) > (240 * CHACAL_ECHELLE) }) then { _traverse = true; _cause = "TRAVERSEE_AVEUGLE" };
        if (isNull _v || { !alive _v }) then { _traverse = true; _cause = "PATROUILLE_ABSENTE" };
        sleep 3;
    };
    if (!_traverse) then { _cause = "PLAFOND_FENETRE" };
    (format ["CHACAL|E|fenetre|%1|%2|attente|%3|vehicule_vu|%4", round (time * 100) / 100,
        _cause, round (time - _tf), (if (_dejaVu) then {1} else {0})]) call CHACAL_LOG;
    { _x doFollow (leader CHACAL_gFS) } forEach (units CHACAL_gFS);

    // ! ILS ONT BIEN FRANCHI, PUIS SONT RESTES DANS L ENVELOPPE DU VEHICULE.
    // Sept minutes plus tard le MRAP revient et tue le chef et l adjoint. Le
    // franchissement n est pas un POINT, c est un COULOIR : on en sort vite,
    // perpendiculairement a l axe du circuit, et on ne reprend la furtivite
    // qu au-dela de 700 m de cet axe.
    private _perp = (CHACAL_ROUTE_A getDir CHACAL_ROUTE_B) + 90;
    if ((abs (((_perp - (_fr getDir CHACAL_SITE)) + 540) % 360 - 180)) > 90) then { _perp = _perp + 180 };
    private _degage = _fr getPos [750, _perp];
    [CHACAL_gFS, _degage, "NORMAL", "AWARE", "WEDGE", "SORTIE_DE_COULOIR"] call CHACAL_fnc_ordreAller;
    (format ["CHACAL|E|couloir|%1|axe|%2|sortie|%3", round (time * 100) / 100, round _perp, _degage]) call CHACAL_LOG;
    [CHACAL_gFS, _degage, 90, [CHACAL_gFS, _degage, 1.1] call CHACAL_fnc_budget] call CHACAL_fnc_arrive;
};

if (!CHACAL_SAUT) then {
    private _b2 = [CHACAL_gFS, CHACAL_RALLY, 0.5] call CHACAL_fnc_budget;
    (format ["CHACAL|E|budget|%1|etape|APPROCHE_RALLY|distance|%2|plafond|%3", round (time * 100) / 100,
        round (((units CHACAL_gFS) call CHACAL_fnc_centre) distance2D CHACAL_RALLY), round _b2]) call CHACAL_LOG;
    [CHACAL_gFS, CHACAL_RALLY, "LIMITED", "STEALTH", "FILE", "OPORD_RALLY"] call CHACAL_fnc_ordreAller;
    _r = [CHACAL_gFS, CHACAL_RALLY, 70, _b2] call CHACAL_fnc_arrive;
};
[2, "APPROCHE", (if (CHACAL_SAUT) then {"COMPROMIS"} else {_r})] call CHACAL_fnc_finPhase;

// ! ABANDON : compromis LOIN, on ne charge pas a dix contre trente-deux.
// Le premier jet menait toute compromission a l assaut en bloc, plafond 900 s,
// jamais arrive, echec par construction. Le corpus enseignait " detecte, donc
// charge " - la decision la plus importante de la mission n avait qu une
// reponse, toujours la meme.
if (CHACAL_COMPROMIS && { ((CHACAL_FS select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_SITE > 1200 }) then {
    CHACAL_ABANDON = true; CHACAL_SAUT = false;
    CHACAL_CAUSE_ABANDON = "COMPROMIS_LOIN";
    (format ["CHACAL|E|abandon|%1|distance|%2", round (time * 100) / 100,
        round (((CHACAL_FS select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_SITE)]) call CHACAL_LOG;
};

};

// --- LE BRAS TEMOIN : il saute observation et articulation ---
// Sans lui on ne sait pas si le plan en six phases vaut mieux que marcher
// droit, et un corpus dont on ignore s il enseigne quelque chose est un actif
// invendable.
if (CHACAL_BRAS == "NUL" && !CHACAL_SAUT && !CHACAL_ABANDON) then {
    CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select 0;
    CHACAL_POS_ASSAUT = [CHACAL_SITE getPos [230, CHACAL_SITE getDir CHACAL_OUV_CHOISIE], 60] call CHACAL_fnc_plat;
    [CHACAL_gFS, CHACAL_POS_ASSAUT, "NORMAL", "AWARE", "WEDGE", "BRAS_NUL_DROIT_SUR_L_OBJECTIF"] call CHACAL_fnc_ordreAller;
    (format ["CHACAL|E|bras_nul|%1|vers|%2", round (time * 100) / 100, CHACAL_POS_ASSAUT]) call CHACAL_LOG;
    [CHACAL_gFS, CHACAL_POS_ASSAUT, 90, [CHACAL_gFS, CHACAL_POS_ASSAUT, 0.9] call CHACAL_fnc_budget] call CHACAL_fnc_arrive;
};

// ---------------------------------------------------------------------
// PHASE 3 - POINT D OBSERVATION : deux hommes montent, huit se terrent
// ---------------------------------------------------------------------
if (!CHACAL_FIN && !CHACAL_SAUT && !CHACAL_ABANDON && { CHACAL_BRAS != "NUL" } && { CHACAL_DEPART < 4 }) then {
    _plafond = 3 call CHACAL_fnc_duree;
    [3, "OBSERVATION", _plafond] call CHACAL_fnc_debutPhase;

    CHACAL_gReco = [CHACAL_RECO, "RECHERCHE"] call CHACAL_fnc_detacher;
    CHACAL_gFS setVariable ["chacal_element", "GROS", true];
    [CHACAL_gReco, CHACAL_OP, "LIMITED", "STEALTH", "FILE", "OPORD_CRETE"] call CHACAL_fnc_ordreAller;
    private _cache = [CHACAL_RALLY getPos [120, CHACAL_RALLY getDir CHACAL_SITE], 50] call CHACAL_fnc_plat;
    [CHACAL_gFS, _cache, "LIMITED", "STEALTH", "WEDGE", "TENIR_HORS_DE_VUE"] call CHACAL_fnc_ordreAller;

    private _rArr = [CHACAL_gReco, CHACAL_OP, 60, [CHACAL_gReco, CHACAL_OP, 0.5] call CHACAL_fnc_budget] call CHACAL_fnc_arrive;
    (format ["CHACAL|E|montee|%1|issue|%2|reco|%3|distance|%4", round (time * 100) / 100,
        _rArr, count ((units CHACAL_gReco) select { alive _x }),
        (if (count ((units CHACAL_gReco) select { alive _x }) > 0)
         then { round ((((units CHACAL_gReco) select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_OP) }
         else { -1 })]) call CHACAL_LOG;

    // ! LE CONTROLE DE JOUR A TRANCHE. En plein jour, a 675 m, la crete
    // localisait ZERO sentinelle sur 31 - et le canal geometrique voyait bien un
    // rouge a 701 m. L instrument marchait ; c est la scene qui etait fausse :
    // PERSONNE ne disait aux observateurs de regarder l objectif. Ils arrivaient,
    // se couchaient face a leur azimut de marche, et le cone ne contenait jamais
    // le site. Sans ce controle j aurais conclu " la crete ne voit rien de nuit "
    // et redimensionne toute la mission autour d une fausse cause.
    {
        if (alive _x) then {
            _x setUnitPos "DOWN";
            _x setDir (_x getDir CHACAL_SITE);
            _x doWatch CHACAL_SITE;
        };
    } forEach (units CHACAL_gReco);
    (format ["CHACAL|E|orientation|%1|reco|%2|azimut_site|%3|distance|%4", round (time * 100) / 100,
        count ((units CHACAL_gReco) select { alive _x }),
        round (CHACAL_OP getDir CHACAL_SITE), round (CHACAL_OP distance2D CHACAL_SITE)]) call CHACAL_LOG;
    { if (alive _x) then { _x setUnitPos "MIDDLE" } } forEach (units CHACAL_gFS);

    // LE RENSEIGNEMENT EST RETENU, pas seulement compte : ce qui entre dans
    // CHACAL_VUES est ce que la reco a vu GEOMETRIQUEMENT au moins une fois.
    private _tObs = time;
    while { (time - _tObs) < (_plafond * 0.55) && ((call CHACAL_fnc_reste) > 0) && !CHACAL_SAUT && !CHACAL_FIN } do {
        private _obs = (units CHACAL_gReco) select { alive _x };
        if (count _obs > 0) then {
            {
                private _e = _x;
                if ({ [_x, _e, 900] call CHACAL_fnc_voit } count _obs > 0) then {
                    private _k = 0;
                    { private _kk = _x knowsAbout _e; if (_kk > _k) then { _k = _kk } } forEach _obs;
                    private _i = CHACAL_VUES findIf { (_x select 0) isEqualTo _e };
                    if (_i < 0) then { CHACAL_VUES pushBack [_e, _k] }
                    else { if (_k > ((CHACAL_VUES select _i) select 1)) then { (CHACAL_VUES select _i) set [1, _k] } };
                };
            } forEach (CHACAL_EST_SITE select { alive _x });
            (format ["CHACAL|E|renseignement|%1|localisees|%2|sur|%3|seuil|%4", round (time * 100) / 100,
                count CHACAL_VUES, count (CHACAL_EST_SITE select { alive _x }), CHACAL_SEUIL_RENS]) call CHACAL_LOG;
        };
        sleep (60 * CHACAL_ECHELLE);
    };

    // ! UNE CRETE QUI NE VOIT RIEN SE RAPPROCHE ( Fable, 05/09 ).
    // J avais ecrit qu une crete vide n attaque pas. Appliquee a une enceinte
    // vue sous 2 degres, cette regle interdit d attaquer precisement la garnison
    // la PLUS FAIBLE : au palier 0 il n y a plus assez d hommes qui MARCHENT, la
    // crete ne localise rien, et la mission renonce sans jamais attaquer.
    // La crete ne voit que ce qui bouge - a 480-820 m avec 18 m de gain, un mur
    // de 2 m cache une bande de quinze a trente metres, donc la tour, les
    // bunkers et la garnison des batiments ne sont JAMAIS vus.
    // Un detachement qui ne voit pas se rapproche. L abandon reste reserve a la
    // compromission ; un renseignement pauvre devient une CONDITION, pas un veto.
    if (!CHACAL_SAUT && { count CHACAL_VUES < CHACAL_SEUIL_RENS }) then {
        private _second = [CHACAL_SITE getPos [250, CHACAL_SITE getDir CHACAL_OP], 60] call CHACAL_fnc_plat;
        (format ["CHACAL|E|rapprochement|%1|localisees|%2|seuil|%3|vers|%4", round (time * 100) / 100,
            count CHACAL_VUES, CHACAL_SEUIL_RENS, _second]) call CHACAL_LOG;
        [CHACAL_gReco, _second, 60, ([CHACAL_gReco, _second] call CHACAL_fnc_budgetDeuxJambes) min 600, "RECO_SECOND_POSTE"] call CHACAL_fnc_rejoindre;
        { if (alive _x) then { _x setUnitPos "DOWN"; _x setDir (_x getDir CHACAL_SITE); _x doWatch CHACAL_SITE } } forEach (units CHACAL_gReco);
        private _t2 = time;
        while { (time - _t2) < (300 * CHACAL_ECHELLE) && !CHACAL_SAUT && !CHACAL_FIN } do {
            private _obs2 = (units CHACAL_gReco) select { alive _x };
            if (count _obs2 > 0) then {
                {
                    private _e = _x;
                    if ({ [_x, _e, 600] call CHACAL_fnc_voit } count _obs2 > 0) then {
                        private _k = 0;
                        { private _kk = _x knowsAbout _e; if (_kk > _k) then { _k = _kk } } forEach _obs2;
                        private _i = CHACAL_VUES findIf { (_x select 0) isEqualTo _e };
                        if (_i < 0) then { CHACAL_VUES pushBack [_e, _k] };
                    };
                } forEach (CHACAL_EST_SITE select { alive _x });
                (format ["CHACAL|E|renseignement|%1|localisees|%2|sur|%3|seuil|%4|poste|SECOND", round (time * 100) / 100,
                    count CHACAL_VUES, count (CHACAL_EST_SITE select { alive _x }), CHACAL_SEUIL_RENS]) call CHACAL_LOG;
            };
            sleep (60 * CHACAL_ECHELLE);
        };
        if (count CHACAL_VUES < CHACAL_SEUIL_RENS) then {
            (format ["CHACAL|E|renseignement_pauvre|%1|localisees|%2|l_assaut_part_quand_meme", round (time * 100) / 100, count CHACAL_VUES]) call CHACAL_LOG;
        };
    };
    [3, "OBSERVATION", (if (CHACAL_SAUT) then {"COMPROMIS"} else {
        if (count CHACAL_VUES >= CHACAL_SEUIL_RENS) then {"ATTEINT"} else {"RENSEIGNEMENT_PAUVRE"} })] call CHACAL_fnc_finPhase;
};

// ---------------------------------------------------------------------
// PHASE 4 - MISE EN PLACE : appui, assaut, bouchon
// ---------------------------------------------------------------------
if (!CHACAL_FIN && !CHACAL_SAUT && !CHACAL_ABANDON && { CHACAL_BRAS != "NUL" }) then {
    _plafond = 4 call CHACAL_fnc_duree;
    [4, "MISE_EN_PLACE", _plafond] call CHACAL_fnc_debutPhase;

    CHACAL_gAppui   = [CHACAL_APPUI,   "APPUI"]   call CHACAL_fnc_detacher;
    CHACAL_gAssaut  = [CHACAL_ASSAUT,  "ASSAUT"]  call CHACAL_fnc_detacher;
    CHACAL_gBouchon = [CHACAL_BOUCHON, "BOUCHON"] call CHACAL_fnc_detacher;

    // ! LE RENSEIGNEMENT CHOISIT L OUVERTURE. Le premier jet visait az_OP + 99 :
    // une constante deguisee en tactique, et c est " marche au 315 " en repere
    // relatif. Ici on compte les sentinelles LOCALISEES pres de chaque porte et
    // on entre par la moins gardee.
    // ! LE CHOIX PESE LES GARDES *ET* LE TRAJET. Ne regarder que les sentinelles
    // fait entrer par une porte deux fois plus loin pour eviter quatre hommes -
    // et sur une nuit ou l articulation est deja le goulot, ce marche est
    // mauvais. Un garde localise vaut 150 m de marche ; l arbitrage est
    // journalise pour qu il soit discutable.
    private _dep = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
    if (count _dep == 0) then { _dep = CHACAL_RALLY };
    private _meilleure = 0; private _minScore = 1e9; private _comptes = []; private _dists = [];
    {
        private _o = _x;
        private _n = { ((_x select 0) distance2D _o) < 110 } count CHACAL_VUES;
        private _d = _dep distance2D _o;
        private _sc = _n + (_d / 150);
        _comptes pushBack _n; _dists pushBack round _d;
        if (_sc < _minScore) then { _minScore = _sc; _meilleure = _forEachIndex };
    } forEach CHACAL_OUVERTURES;
    CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select _meilleure;
    (format ["CHACAL|E|choix_ouverture|%1|indice|%2|gardes|%3|distances|%4|score|%5|renseignement|%6",
        round (time * 100) / 100, _meilleure, str _comptes, str _dists,
        round (_minScore * 100) / 100, count CHACAL_VUES]) call CHACAL_LOG;

    CHACAL_POS_APPUI   = CHACAL_OP;
    CHACAL_POS_ASSAUT  = [CHACAL_SITE getPos [230, CHACAL_SITE getDir CHACAL_OUV_CHOISIE], 60] call CHACAL_fnc_plat;
    // ! 700 m sur l axe de la reserve etait un chiffre ecrit sans justification,
    // et il demandait au bouchon une demi-heure de marche. Son travail est de
    // RETARDER la reserve, pas de tenir un carrefour : 400 m le font aussi bien.
    CHACAL_POS_BOUCHON = [CHACAL_SITE getPos [400, CHACAL_SITE getDir CHACAL_QRF_BASE], 80] call CHACAL_fnc_plat;

    // Le plafond est la SOMME des deux jambes, calculee sur les vitesses
    // reellement ordonnees - 1,1 m/s puis 0,5 - et non sur une constante
    // d infiltration qui mentait d un facteur deux.
    private _b1 = [CHACAL_gAppui,   CHACAL_POS_APPUI]   call CHACAL_fnc_budgetDeuxJambes;
    private _b2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT]  call CHACAL_fnc_budgetDeuxJambes;
    private _b3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON] call CHACAL_fnc_budgetDeuxJambes;
    _plafond = (_b1 max _b2) max _b3;
    CHACAL_TPHASE = time; CHACAL_PLAFOND_COURANT = _plafond;
    (format ["CHACAL|E|budget|%1|etape|MISE_EN_PLACE|appui|%2|assaut|%3|bouchon|%4|plafond|%5",
        round (time * 100) / 100, round _b1, round _b2, round _b3, round _plafond]) call CHACAL_LOG;

    // Les trois elements rejoignent EN PARALLELE, chacun a son rythme, chacun
    // journalisant sa progression. Le premier jet les interrogeait a tour de
    // role par tranches de 4 s, ce qui ne pilotait rien.
    private _r1 = ""; private _r2 = ""; private _r3 = "";
    // ! LE PASSAGE A VINGT MINUTES ( Fable, 06/09 ). A DEPART=3 un passage coute
    // une heure, dont vingt minutes a observer un site vide, alors que la couture
    // testee est la phase 5-6 et que la phase 4 vient d etre certifiee ATTEINT.
    // On pose les trois elements sur leurs positions, hors corpus, et on itere a
    // l heure. La certification finale se fait UNE FOIS a DEPART=3, deux graines.
    if (CHACAL_DEPART >= 4) then {
        "CHACAL|AVERT|hors_corpus|depart|4|articulation_non_jouee" call CHACAL_LOG;
        {
            _x params ["_g", "_p"];
            if (!isNull _g) then {
                { if (alive _x) then { _x setPosATL (_p getPos [4 + (10 call CHACAL_fnc_al), 360 call CHACAL_fnc_al]) } } forEach (units _g);
            };
        } forEach [[CHACAL_gAppui, CHACAL_POS_APPUI], [CHACAL_gAssaut, CHACAL_POS_ASSAUT], [CHACAL_gBouchon, CHACAL_POS_BOUCHON]];
        sleep 5;
    } else {
        private _h1 = [CHACAL_gAppui,   CHACAL_POS_APPUI,   70, _plafond, "APPUI"]   spawn CHACAL_fnc_rejoindre;
        private _h2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT,  70, _plafond, "ASSAUT"]  spawn CHACAL_fnc_rejoindre;
        private _h3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON, 80, _plafond, "BOUCHON"] spawn CHACAL_fnc_rejoindre;
        waitUntil { sleep 3; (scriptDone _h1 && scriptDone _h2 && scriptDone _h3) || CHACAL_FIN || CHACAL_SAUT };
    };
    _r1 = if ([CHACAL_gAppui,   CHACAL_POS_APPUI,   70] call CHACAL_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    _r2 = if ([CHACAL_gAssaut,  CHACAL_POS_ASSAUT,  70] call CHACAL_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    _r3 = if ([CHACAL_gBouchon, CHACAL_POS_BOUCHON, 80] call CHACAL_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    { if (alive _x) then { _x setUnitPos "DOWN"; _x setDir (_x getDir CHACAL_SITE); _x doWatch CHACAL_SITE } } forEach (units CHACAL_gAppui);
    (format ["CHACAL|E|articulation|%1|appui|%2|assaut|%3|bouchon|%4", round (time * 100) / 100, _r1, _r2, _r3]) call CHACAL_LOG;
    [4, "MISE_EN_PLACE", (if (_r1 == "ATTEINT" && _r2 == "ATTEINT" && _r3 == "ATTEINT") then {"ATTEINT"}
        else { if (CHACAL_SAUT) then {"COMPROMIS"} else {"PLAFOND"} })] call CHACAL_fnc_finPhase;
};

// ---------------------------------------------------------------------
// PHASE 5 - ACTION SUR OBJECTIF
// ---------------------------------------------------------------------
if (!CHACAL_ABANDON && !CHACAL_FIN) then {
CHACAL_SAUT = false;
_plafond = 5 call CHACAL_fnc_duree;
[5, "ASSAUT", _plafond] call CHACAL_fnc_debutPhase;

if (isNull CHACAL_gAssaut) then {
    CHACAL_gAssaut = CHACAL_gFS; CHACAL_gAssaut setVariable ["chacal_element", "ASSAUT_BLOC", true];
    if (count CHACAL_OUV_CHOISIE == 0) then { CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select 0 };
};

// ! LA PORTE D ENTREE DE L ASSAUT.
// Mesure du premier episode complet : la compromission tombe, le reflexe de
// rupture envoie les trois elements a 800 m, la phase 4 se ferme UNE DEMI-
// SECONDE plus tard sur appui|PLAFOND assaut|PLAFOND, et la phase 5 s ouvre
// quand meme. Le chef meurt huit secondes apres, puis les deux demolisseurs, le
// medecin et l adjoint - tues au detail sur douze minutes. Ce n etait pas un
// assaut, c etait une dislocation, et le corpus l aurait enseignee comme une
// tactique.
// La regle est celle du terrain : rompre, se regrouper, PUIS decider.
private _renonce = false;
if (!isNil "CHACAL_POS_ASSAUT") then {
    private _a1 = [CHACAL_gAppui,   CHACAL_POS_APPUI,   130] call CHACAL_fnc_enPlace;
    private _a2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT,  130] call CHACAL_fnc_enPlace;
    private _a3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON, 160] call CHACAL_fnc_enPlace;
    (format ["CHACAL|E|dispositif|%1|appui|%2|assaut|%3|bouchon|%4|vivants|%5", round (time * 100) / 100,
        (if (_a1) then {1} else {0}), (if (_a2) then {1} else {0}), (if (_a3) then {1} else {0}),
        count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;

    if (!_a2 || { !_a1 }) then {
        // ! LA SECONDE CHANCE DOIT CHANGER QUELQUE CHOSE. Le premier jet
        // rejouait les memes ordres au meme pas et rendait le meme resultat -
        // `appui|1|assaut|0|bouchon|0` avant comme apres - en brulant 45 % de la
        // phase pour rien. Si l assaut est a plus de 400 m, aucun re-envoi ne le
        // ramenera dans le temps qui reste : on renonce d emblee et on le dit.
        private _uA = (units CHACAL_gAssaut) select { alive _x };
        private _dA = if (count _uA > 0) then { (_uA call CHACAL_fnc_centre) distance2D CHACAL_POS_ASSAUT } else { 9999 };
        if (_dA > 400) exitWith {
            (format ["CHACAL|E|rearticulation|%1|refusee|assaut_a|%2|trop_loin", round (time * 100) / 100, round _dA]) call CHACAL_LOG;
        };
        (format ["CHACAL|E|rearticulation|%1|cause|DISPOSITIF_ECLATE|assaut_a|%2", round (time * 100) / 100, round _dA]) call CHACAL_LOG;
        private _b = ([CHACAL_gAssaut, CHACAL_POS_ASSAUT] call CHACAL_fnc_budgetDeuxJambes) min (_plafond * 0.45);
        private _hA = [CHACAL_gAssaut, CHACAL_POS_ASSAUT, 130, _b, "ASSAUT_REPRISE"] spawn CHACAL_fnc_rejoindre;
        [CHACAL_gAppui,   CHACAL_POS_APPUI,   "NORMAL", "AWARE", "LINE",  "REARTICULATION"] call CHACAL_fnc_ordreAller;
        [CHACAL_gBouchon, CHACAL_POS_BOUCHON, "NORMAL", "AWARE", "WEDGE", "REARTICULATION"] call CHACAL_fnc_ordreAller;
        waitUntil { sleep 3; scriptDone _hA || CHACAL_FIN };
        _a1 = [CHACAL_gAppui,   CHACAL_POS_APPUI,   130] call CHACAL_fnc_enPlace;
        _a2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT,  130] call CHACAL_fnc_enPlace;
        _a3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON, 160] call CHACAL_fnc_enPlace;
        (format ["CHACAL|E|dispositif|%1|apres_rearticulation|appui|%2|assaut|%3|bouchon|%4|vivants|%5",
            round (time * 100) / 100, (if (_a1) then {1} else {0}), (if (_a2) then {1} else {0}),
            (if (_a3) then {1} else {0}), count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };

    if (!_a2) then {
        _renonce = true; CHACAL_ABANDON = true;
        CHACAL_CAUSE_ABANDON = "ARTICULATION_ROMPUE";
        (format ["CHACAL|E|renoncement|%1|cause|ARTICULATION_ROMPUE|vivants|%2", round (time * 100) / 100,
            count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };
};

// ! LA RESTITUTION REMPLACE LE `reveal` EN GROS. Le premier jet revelait toutes
// les sentinelles a tout l appui - or TIREUR_2 etait en cache a 900 m et n avait
// rien observe : le reveal lui donnait une connaissance jamais gagnee. Et la
// scission avait de toute facon detruit la liste de cibles du groupe de reco.
// Ici on ne restitue QUE ce que la reco a vu, QU AUX hommes qui l ont vu, et au
// niveau observe. Le compte est journalise : N restituees sur M localisees.
private _recoHommes = CHACAL_RECO call CHACAL_fnc_role;
private _restitue = 0;
{
    _x params ["_cible", "_k"];
    if (alive _cible) then {
        { _x reveal [_cible, _k min 2] } forEach _recoHommes;
        _restitue = _restitue + 1;
    };
} forEach CHACAL_VUES;
(format ["CHACAL|E|restitution|%1|restituees|%2|localisees|%3|destinataires|%4", round (time * 100) / 100,
    _restitue, count CHACAL_VUES, count _recoHommes]) call CHACAL_LOG;

// L assaut ne renonce plus faute de renseignement : il part avec ce qu il a et
// la pauvrete est une CONDITION journalisee. Seule la compromission ou une
// articulation rompue arretent la mission.
if (_restitue == 0 && !_renonce) then {
    (format ["CHACAL|E|renseignement_pauvre|%1|restituees|0|l_assaut_part_par_l_ouverture_par_defaut", round (time * 100) / 100]) call CHACAL_LOG;
};

if (_renonce) then {
    [5, "ASSAUT", CHACAL_CAUSE_ABANDON] call CHACAL_fnc_finPhase;
} else {

if (!isNull CHACAL_gAppui) then {
    CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED"; CHACAL_gAppui setSpeedMode "LIMITED";
    private _cibles = (CHACAL_VUES apply { _x select 0 }) select { alive _x };
    { if (alive _x && { count _cibles > 0 }) then { _x doTarget (_cibles select 0); _x doFire (_cibles select 0) } } forEach (units CHACAL_gAppui);
};
sleep (8 * CHACAL_ECHELLE);

if (!isNull CHACAL_gBouchon) then {
    CHACAL_gBouchon setBehaviour "COMBAT"; CHACAL_gBouchon setCombatMode "RED";
    { if (alive _x) then { _x setUnitPos "MIDDLE" } } forEach (units CHACAL_gBouchon);
};

// ! LE DETACHEMENT DES DEMOLISSEURS EST SUPPRIME ( Fable, 05/09 ).
// Je les avais sortis du groupe d assaut pour qu un `taskCQB` n ecrase pas leur
// `doMove`. Resultat mesure : deux hommes seuls traversant une garnison en
// alerte, tues a 80 s d intervalle, zero charge. On ne repare pas ca en
// changeant leur comportement - on cesse de les separer. L assaut avance d un
// seul corps, et les charges sont portees par les cinq.

CHACAL_gAssaut setBehaviour "COMBAT"; CHACAL_gAssaut setCombatMode "RED"; CHACAL_gAssaut setSpeedMode "FULL";
[CHACAL_gAssaut, CHACAL_OUV_CHOISIE, "FULL", "COMBAT", "WEDGE", "OUVERTURE_CHOISIE"] call CHACAL_fnc_ordreAller;
// Sans cette ligne, un `ELEMENT_N_ARRIVE_PAS` sur la premiere antenne serait
// indiscernable d un assaut reste a 200 m de l enceinte.
private _rO = [CHACAL_gAssaut, CHACAL_OUV_CHOISIE, 55, [CHACAL_gAssaut, CHACAL_OUV_CHOISIE, 1.2] call CHACAL_fnc_budget] call CHACAL_fnc_arrive;
(format ["CHACAL|E|ouverture|%1|issue|%2|distance|%3|reste|%4", round (time * 100) / 100, _rO,
    round ((((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_OUV_CHOISIE),
    round (call CHACAL_fnc_reste)]) call CHACAL_LOG;

// =====================================================================
// ! LA PHASE 5 NE POUVAIT PAS RENDRE 3/3, PAR CONSTRUCTION ( Fable, 05/09 ).
//
// Le premier jet lancait TROIS threads, un par objectif ; chacun TIRAIT AU SORT
// un demolisseur parmi deux et lui donnait UN `doMove`. Le dernier `doMove` recu
// par un homme ecrase les precedents, et aucun thread ne renvoyait personne
// apres une pose. Deux hommes, trois cibles, une seule passe : au mieux deux
// charges, et le succes en exige trois. Le zero sur sept episodes ne mesurait
// pas le monde, il mesurait cette couture - et `charge_posee` n apparaissait
// dans AUCUN des vingt-cinq episodes archives.
//
// Remede : l element d assaut avance D UN SEUL CORPS, objectif par objectif,
// dans une FILE et jamais un tirage. L ordre suit la geometrie : les antennes
// sont a 41 m du centre pour un mur a 46, elles se traitent en longeant
// l interieur du mur ; le PC est au centre, c est le seul qui impose de
// traverser, et le CQB ne porte que sur lui, une fois les antennes faites.
// =====================================================================
private _ordre = CHACAL_OBJETS select { _x != CHACAL_PC };
_ordre = [_ordre, [], { _x distance2D CHACAL_OUV_CHOISIE }, "ASCEND"] call BIS_fnc_sortBy;
if (!isNull CHACAL_PC) then { _ordre pushBack CHACAL_PC };
// origines_z : le z minimal de la boite englobante. Proche de 0 = origine au
// sol ; tres negatif = origine en hauteur, et l objet est a moitie enterre.
(format ["CHACAL|E|file_objectifs|%1|%2|origines_z|%3", round (time * 100) / 100,
    (_ordre apply { typeOf _x }),
    (_ordre apply { round ((((boundingBoxReal _x) select 0) select 2) * 10) / 10 })]) call CHACAL_LOG;

// ! `taskCQB` SORT DE LA FILE ( Fable, 06/09 ). Lance en meme temps que l ordre
// de pose, il combat tout ce qui le suit : LAMBS donne ses propres `doMove` sur
// son cycle, et un homme sous `doMove` ignore le waypoint de groupe du
// degagement. Les cinq morts du passage 4 ont ete poses PENDANT un CQB.
// Le nettoyage redeviendra une etape separee, avec son propre controle.
"CHACAL|E|cqb|differe|le_nettoyage_est_une_etape_separee" call CHACAL_LOG;

private _hExpl = scriptNull;
{
    private _o = _x;
    if (CHACAL_FIN || { !alive _o }) then { continue };
    if (count ((units CHACAL_gAssaut) select { alive _x }) == 0) then {
        (format ["CHACAL|E|file_interrompue|%1|restants|0", round (time * 100) / 100]) call CHACAL_LOG;
        continue
    };
    // ! L HORLOGE DE PHASE ENTRE DANS LA FILE. Trois objectifs a 360 s font
    // 1 080 s pour une phase de 900, et le `waitUntil` final attendait 900 s de
    // PLUS quand la file finissait a moins de 3/3 : le meilleur passage a
    // patiente quinze minutes immobile dans l enceinte.
    private _cap = (180 * CHACAL_ECHELLE) min ((call CHACAL_fnc_reste) - CHACAL_RESERVE_FEU);
    if (_cap <= 0) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|PLAFOND_PHASE", round (time * 100) / 100, typeOf _o]) call CHACAL_LOG;
        continue
    };
    private _pt = [_o] call CHACAL_fnc_pointDePose;
    (format ["CHACAL|E|objectif|%1|%2|point_de_pose|%3|emprise|%4|cap|%5", round (time * 100) / 100,
        typeOf _o, _pt, round (_o call CHACAL_fnc_emprise), round _cap]) call CHACAL_LOG;
    [CHACAL_gAssaut, _pt, "FULL", "COMBAT", "WEDGE", "OBJECTIF_" + (typeOf _o)] call CHACAL_fnc_ordreAller;
    private _r = [CHACAL_gAssaut, _pt, 22, _cap, 120] call CHACAL_fnc_arrive;
    private _c0 = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
    private _dG = if (count _c0 > 0) then { round (_c0 distance2D _pt) } else { 9999 };
    // ENLISE a 30 m suffit : le porteur fera les derniers metres seul
    if (_dG > 40) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|ELEMENT_N_ARRIVE_PAS|issue|%3|distance|%4",
            round (time * 100) / 100, typeOf _o, _r, _dG]) call CHACAL_LOG;
        continue
    };
    // ! EXPLOITATION NEUTRALISEE POUR CE RUN ( Fable, 07/09 ).
    // La certification a certifie un mecanisme CASSE : `intel|0` sur les deux
    // graines, avec `exploitation|manquee|distance|5` - a cinq metres du
    // portable, dans un monde vide, avec un homme dedie et cent secondes.
    // Trois defauts, et ce sont les trois memes que les points de pose avant
    // correction : on vise un OBJET et non un point ou un homme peut se tenir ;
    // l homme est en COMBAT donc il avance par bonds ; et le critere exige
    // soixante secondes CONTINUES sous quatre metres alors que rien ne l y
    // retient - il oscille et n accumule jamais.
    // L exploitation n entre pas dans le verdict ( le succes compte les charges
    // et les exfiltres ), donc on ne repare pas a l aveugle avant dix heures de
    // run : on neutralise, et on le DIT. Reparation ensuite, avec son propre
    // controle positif a DEPART=4 - l exploitant pose a 3 m doit rendre
    // `reussie` en 60 s ; sinon c est le critere qui est faux, pas la marche.
    if (_o isEqualTo CHACAL_PC) then {
        "CHACAL|E|exploitation|differee|controle_positif_manquant" call CHACAL_LOG;
    };

    private _porteurs = (units CHACAL_gAssaut) select { alive _x && { "DemoCharge_Remote_Mag" in (magazines _x) } };
    if (count _porteurs == 0) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|AUCUN_PORTEUR_VIVANT", round (time * 100) / 100, typeOf _o]) call CHACAL_LOG;
        continue
    };
    private _demo = _porteurs select { (_x getVariable ["chacal_role", ""]) in ["DEMO_1", "DEMO_2"] };
    private _h = if (count _demo > 0) then { _demo select 0 } else { _porteurs select 0 };
    _h doMove _pt;
    private _t = time;
    waitUntil { sleep 1; ((_h distance2D _pt) < 5) || !(alive _h) || (time - _t > 45 * CHACAL_ECHELLE) || CHACAL_FIN };
    private _dH = round (_h distance2D _pt);
    if (!alive _h || { _dH > 12 }) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|PORTEUR_N_ARRIVE_PAS|%3|distance|%4", round (time * 100) / 100,
            typeOf _o, (_h getVariable ["chacal_role", ""]), _dH]) call CHACAL_LOG;
        if (alive _h && { _h != leader CHACAL_gAssaut }) then { _h doFollow (leader CHACAL_gAssaut) };
        continue
    };
    sleep (4 * CHACAL_ECHELLE);   // le geste a une duree
    private _c = createVehicle ["DemoCharge_Remote_Ammo", _pt getPos [3, _pt getDir _o], [], 0, "CAN_COLLIDE"];
    _h removeMagazine "DemoCharge_Remote_Mag";
    CHACAL_CHARGES pushBackUnique _o;
    CHACAL_CHARGES_OBJ pushBack [_o, _c];
    (format ["CHACAL|E|charge_posee|%1|%2|par|%3|distance|%4|actes|%5|sur|%6", round (time * 100) / 100,
        typeOf _o, (_h getVariable ["chacal_role", ""]), _dH, count CHACAL_CHARGES, count CHACAL_OBJETS]) call CHACAL_LOG;
    if (_h != leader CHACAL_gAssaut) then { _h doFollow (leader CHACAL_gAssaut) };
} forEach _ordre;

// --- l exploitation est coupee AVANT le degagement ---
if (!isNull _hExpl) then {
    private _tX = time;
    waitUntil { sleep 2; scriptDone _hExpl || (time - _tX > 90 * CHACAL_ECHELLE) || CHACAL_FIN };
    if (!scriptDone _hExpl) then { terminate _hExpl };
    if (alive CHACAL_EXPLOITANT) then { CHACAL_EXPLOITANT doFollow (leader CHACAL_gAssaut) };
};

// --- UN SEUL degagement, puis TOUT saute ensemble ---
private _abri = CHACAL_OUV_CHOISIE getPos [70, CHACAL_SITE getDir CHACAL_OUV_CHOISIE];
[CHACAL_gAssaut, _abri, "FULL", "COMBAT", "WEDGE", "DEGAGEMENT_AVANT_MISE_A_FEU"] call CHACAL_fnc_ordreAller;
(format ["CHACAL|E|degagement|%1|vers|%2|charges|%3", round (time * 100) / 100, _abri, count CHACAL_CHARGES_OBJ]) call CHACAL_LOG;
private _rD = [CHACAL_gAssaut, _abri, 30, ((call CHACAL_fnc_reste) - 60) max 45, 60] call CHACAL_fnc_arrive;
[_rD] call CHACAL_fnc_miseAFeu;

// ! INCOMPLET est nouveau : la file s est terminee AVANT le plafond, et chaque
// manque porte sa cause. Ce n est pas un plafond, il ne faut pas l appeler ainsi.
private _iss5 = if (count CHACAL_CHARGES >= count CHACAL_OBJETS) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if ((call CHACAL_fnc_reste) <= 0) then {"PLAFOND"} else {"INCOMPLET"} } };
[5, "ASSAUT", _iss5] call CHACAL_fnc_finPhase;
};
};

// ---------------------------------------------------------------------
// PHASE 6 - RUPTURE ET EXFILTRATION
// ---------------------------------------------------------------------
// ! Sur ABANDON le detachement etait envoye au point de secours situe DERRIERE
// le site : il devait contourner l objectif qu il venait de renoncer a
// attaquer. On se replie par ou l on est venu. Et le plafond se calcule depuis
// la position REELLE des SURVIVANTS - `CHACAL_gFS` est vide depuis la scission,
// et la fonction rendait alors son defaut de 120 s pour 4 km a parcourir.
if (CHACAL_FIN) exitWith {};   // vignette close avant l exfiltration
CHACAL_EXFIL_POINT = if (CHACAL_ABANDON) then { CHACAL_LZ } else { CHACAL_PZ };
_plafond = [(CHACAL_FS select { alive _x }), CHACAL_EXFIL_POINT, 1.8] call CHACAL_fnc_budget;
[6, "EXFILTRATION", _plafond] call CHACAL_fnc_debutPhase;
(format ["CHACAL|E|budget|%1|etape|EXFIL|vers|%2|distance|%3|plafond|%4", round (time * 100) / 100,
    (if (CHACAL_ABANDON) then {"LZ"} else {"PZ"}),
    round (((CHACAL_FS select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_EXFIL_POINT),
    round _plafond]) call CHACAL_LOG;

private _pourquoi = if (CHACAL_ABANDON) then {"ABANDON_REPLI_PAR_LA_LZ"} else {"OBJECTIFS_TRAITES"};
// ! Un detachement qui n est PAS compromis ne rompt pas le contact, il s en va.
// En COMBAT sur 1,4 a 2,4 km, 1,8 m/s de moyenne n est pas garanti meme sans
// ennemi : l issue serait EXFIL_MANQUEE sur un detachement intact.
private _compExf = if (CHACAL_COMPROMIS) then {"COMBAT"} else {"AWARE"};
{
    if (!isNull _x) then {
        _x setBehaviour _compExf; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
        { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x);
        [_x, CHACAL_EXFIL_POINT, "FULL", _compExf, "WEDGE", _pourquoi] call CHACAL_fnc_ordreAller;
    };
} forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];

private _tE = time;
waitUntil { sleep 3;
    (count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } }) >= 6) ||
    (count (CHACAL_FS select { alive _x }) == 0) || (time - _tE > _plafond) || CHACAL_FIN };
CHACAL_EXFILTRES = count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } });
[6, "EXFILTRATION", (if (CHACAL_EXFILTRES >= 6) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {"PLAFOND"} })] call CHACAL_fnc_finPhase;

CHACAL_FIN = true;
};
