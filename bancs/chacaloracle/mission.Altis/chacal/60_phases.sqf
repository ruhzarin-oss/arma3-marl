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
// ! MARQUEUR-SEUIL-RENS-DERIVE - SEUIL DERIVE DE LA MESURE, PAS CHOISI ( 15/09 ).
// Distribution de count CHACAL_VUES en fin de phase 3, sur les 148 episodes des journaux qui
// ont joue la phase hors oracle : 0 vue dans 82 episodes soit 55,4 %, 1 vue dans 48 soit
// 32,4 %, 2 vues dans 17 soit 11,5 %, 5 vues dans 1 seul soit 0,7 %.
// Part des episodes qui ATTEIGNENT le seuil S :
//   S=0 -> 100,0 %   une porte qui ne sait pas se fermer
//   S=1 ->  44,6 %   le seul dont l issue soit vraiment incertaine  <<< retenu
//   S=2 ->  12,2 %   atteignable, mais ATTEINT devient un evenement rare
//   S=3 ->   0,7 %   l etat d avant : 110 echecs sur 111, 55 heures pour zero information
// Le maximum jamais atteint au premier poste est 2 : 3 etait hors d atteinte par construction.
// ! CE SEUIL COMMANDE AUSSI LE RAPPROCHEMENT vers le second poste, plus bas. A 1, les 49
// episodes sur 146 qui avaient deja une vue a la crete ne se rapprochent plus - ils ont deja
// atteint le seuil. Mesure du cout : le nombre d episodes finissant avec au moins une vue est
// INCHANGE, 66 sur 146 ; seuls 4 episodes perdaient une vue de plus ( 3 passaient de 1 a 2,
// 1 passait de 2 a 5 ). En echange 49 episodes economisent le trajet et les 300 s du second
// poste. Le couplage est garde parce qu il est juste : on cesse de chercher quand on a assez.
// ! CE CORRECTIF NE FAIT PAS JOUER LA PHASE 3. Elle ne tourne que si CHACAL_DEPART < 4 et
// CHACAL_OBS = 1 ; c est un reglage de job, pas de code.
CHACAL_SEUIL_RENS = 1;            // sous ce compte, la crete n a rien vu
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
// ! LA LIGNE DE DECISION ( plans/plan-choix-par-vignette.md, 16/09 ). Un choix = une ligne, toujours la meme forme,
// lue par la table dbt stg_decision puis par le gymnase. Les observables sont ce que le detachement PEUT savoir au
// moment du choix. verite_defenseurs ne l est pas : il est ecrit pour la lecture, jamais pour decider.
// Ne tire aucun alea : ni le monde ni la situation ne bougent.
"CHACAL|OK|decision|version|3" call CHACAL_LOG;   // 3 : perceptions de la menace en fin de ligne ( plans/plan-menace-visible.md )
// ! LA MENACE VISIBLE ( 17/09 ). Deux canaux : ce qu un homme du detachement VOIT maintenant ( CHACAL_fnc_voit, geometrie ) et
// ce que le GROUPE du detachement CONNAIT ( targetKnowledge, champ 0 « known by group », position crue, erreur, derniere vue ).
// Pas knowsAbout : connaissance de camp. La verite ( verite_* ) est ecrite a part, pour la lecture seulement.
CHACAL_fnc_unitesMenace = {
    private _t = [];
    { private _g = _x select 2; if (!isNull _g) then { _t append ((units _g) select { alive _x }) } } forEach CHACAL_MENACES;
    _t
};
CHACAL_fnc_chefsDetachement = {
    private _g = [];
    { if (alive _x) then { _g pushBackUnique (group _x) } } forEach CHACAL_FS;
    (_g select { !isNull _x && { alive (leader _x) } }) apply { leader _x }
};
CHACAL_fnc_suiviMenaces = {
    while { !CHACAL_FIN } do {
        private _chefs = call CHACAL_fnc_chefsDetachement;
        private _hommesS = CHACAL_FS select { alive _x };
        {
            private _t = _x; private _crue = [];
            { private _k = _x targetKnowledge _t; if (_k select 0) exitWith { _crue = _k select 6 } } forEach _chefs;
            if (count _crue > 0) then {
                private _h = _t getVariable ["chacal_crue", []];
                _h pushBack [time, _crue];
                if (count _h > 6) then { _h deleteAt 0 };
                _t setVariable ["chacal_crue", _h];
            };
            // ! LE MEME SUIVI, MAIS PAR L OEIL. Le canal connaissance est mort ( 0 sur 118 ) : sans ce second
            // suivi, menace_mobile vaut -1 partout et la regle etablie le 19/09 reste injouable.
            if (({ [_x, _t, 800, 70] call CHACAL_fnc_voit } count _hommesS) > 0) then {
                private _hv = _t getVariable ["chacal_vue", []];
                _hv pushBack [time, getPosATL _t];
                if (count _hv > 6) then { _hv deleteAt 0 };
                _t setVariable ["chacal_vue", _hv];
            };
        } forEach (call CHACAL_fnc_unitesMenace);
        sleep 5;
    };
};
[] spawn CHACAL_fnc_suiviMenaces;
CHACAL_fnc_perceptionMenace = {
    // Quatre canaux, jamais la verite : l oeil ( geometrie ), le GROUPE, le CAMP, l HOMME.
    // menace_percue conjugue les deux premiers : 2 connue du groupe, 1 seulement visible, 0 rien ( decision de Younes, 17/09 ).
    private _menaces = call CHACAL_fnc_unitesMenace;
    private _hommes = CHACAL_FS select { alive _x };
    private _chefs = call CHACAL_fnc_chefsDetachement;
    private _vues = 0; private _connues = 0; private _camp = 0; private _homme = 0;
    private _dMin = -1; private _err = -1; private _vueDepuis = -1; private _mobile = -1; private _proche = objNull;
    {
        private _t = _x;
        private _vu = ({ [_x, _t, 800, 70] call CHACAL_fnc_voit } count _hommes) > 0;
        if (_vu) then { _vues = _vues + 1 };
        if ((west knowsAbout _t) > 1.4) then { _camp = _camp + 1 };
        if (({ ((_x targetKnowledge _t) select 1) } count _hommes) > 0) then { _homme = _homme + 1 };
        private _k = [];
        { private _kk = _x targetKnowledge _t; if (_kk select 0) exitWith { _k = _kk } } forEach _chefs;
        if (count _k > 0) then {
            _connues = _connues + 1;
            private _crue = _k select 6;
            private _d = 1e9;
            { _d = _d min (_x distance2D _crue) } forEach _hommes;
            if ((_dMin < 0) || { _d < _dMin }) then {
                _dMin = _d; _err = _k select 5; _proche = _t;
                _vueDepuis = if ((_k select 2) > 0) then { round (time - (_k select 2)) } else { -1 };
            };
        };
    } forEach _menaces;
    if (!isNull _proche) then {
        private _h = (_proche getVariable ["chacal_crue", []]) select { (time - (_x select 0)) <= 25 };
        _mobile = if (count _h >= 2) then { if ((((_h select 0) select 1) distance2D ((_h select ((count _h) - 1)) select 1)) > 10) then {1} else {0} } else {-1};
    };
    private _percue = if (_connues > 0) then {2} else { if (_vues > 0) then {1} else {0} };
    private _veh = 0;
    if ((!isNil "CHACAL_VEH_ROUTE") && { !isNull CHACAL_VEH_ROUTE } && { ({ (_x select 1) == "PATROUILLE_ROUTE" } count CHACAL_MENACES) > 0 }) then {
        if (({ (_x targetKnowledge CHACAL_VEH_ROUTE) select 0 } count _chefs) > 0) then { _veh = 1 };
    };
    // ! MOBILITE VUE : la menace a-t-elle bouge entre deux regards de l oeil ? -1 si l oeil ne l a pas vue deux fois.
    private _mobileVue = -1;
    {
        private _hv = (_x getVariable ["chacal_vue", []]) select { (time - (_x select 0)) <= 40 };
        if (count _hv >= 2) then {
            private _d = ((_hv select 0) select 1) distance2D ((_hv select ((count _hv) - 1)) select 1);
            if (_d > 10) exitWith { _mobileVue = 1 };
            if (_mobileVue < 0) then { _mobileVue = 0 };
        };
    } forEach _menaces;
    // ! LE MOTEUR : un blinde s entend de nuit bien plus loin qu un homme ne se voit, et seul le bras PATROUILLE
    // en a un. Approximation assumee, a valider par le controle : jamais 1 sur un poste a pied.
    private _moteur = 0;
    {
        private _v = vehicle _x;
        if ((_v != _x) && { isEngineOn _v }) then {
            { if ((_x distance2D _v) < CHACAL_PORTEE_SON) exitWith { _moteur = 1 } } forEach _hommes;
        };
    } forEach _menaces;
    private _vDist = -1;
    { private _t = _x; { private _dd = _x distance2D _t; if ((_vDist < 0) || { _dd < _vDist }) then { _vDist = _dd } } forEach _hommes } forEach _menaces;
    format ["|menace_percue|%1|menaces_vues|%2|menaces_connues|%3|menaces_camp|%4|menaces_homme|%5|distance_menace|%6|erreur_position|%7|menace_mobile|%8|vue_depuis|%9|vehicule_connu|%10|menace_mobile_vue|%11|moteur_entendu|%12|verite_menaces|%13|verite_distance_menace|%14|azimut_chef|%15",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        _mobileVue, _moteur,
        count _menaces, round _vDist, (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]
};
CHACAL_fnc_secteurPhase = {
    params ["_phase"];
    switch (_phase) do {
        case 1: { if (isNil "CHACAL_LZ") then { [] } else { CHACAL_LZ } };
        case 2: { if (isNil "CHACAL_ROUTE") then { [] } else { CHACAL_ROUTE } };
        case 4: { if (isNil "CHACAL_SITE") then { [] } else { CHACAL_SITE } };
        default { [] };
    };
};
CHACAL_fnc_fenetreObservation = {
    params ["_phase"];
    if (CHACAL_OBSERVATION <= 0) exitWith {};
    private _t0 = time;
    private _hommes = CHACAL_FS select { alive _x };
    private _secteur = [_phase] call CHACAL_fnc_secteurPhase;
    // ! OBSERVER, C EST SCRUTER UN SECTEUR ( controles du 17/09 : la menace posee a 150 m devant n etait connue que
    // 2 fois sur 8 ; les hommes s arretaient mais gardaient leur cap ). On les fait regarder le point de la phase.
    // ! OBSERVER, C EST BALAYER ( banc du 18/09 : une cible regardee est connue en 6 s jusqu a 150 m ; fixer un seul
    // point laisse la menace hors du champ ). Trois azimuts autour de l axe de la phase, le regard tourne toutes les 10 s.
    private _regards = [];
    if (count _secteur > 0) then {
        private _chefF = leader (group (_hommes select 0));
        private _axe = _chefF getDir _secteur;
        { _regards pushBack (_chefF getPos [(_chefF distance2D _secteur) max 200, _axe + _x]) } forEach [-45, 0, 45];
    };
    { doStop _x; if (_phase == 1) then { _x setUnitPos "MIDDLE" } } forEach _hommes;
    if ((CHACAL_CONTROLE_PERCEPTION in [1, 5]) && { count _hommes > 0 }) then {
        // ! BANC DE PERCEPTION ( 18/09 ) : la cible est posee LA OU ILS PEUVENT LA VOIR, et ils la regardent.
        private _chef = leader (group (_hommes select 0));
        private _oeil = (getPosASL _chef) vectorAdd [0, 0, 1.5];
        private _az = getDir _chef; private _trouve = false;
        {
            private _p = _chef getPos [CHACAL_CONTROLE_DIST, _x];
            private _cible = (ATLToASL _p) vectorAdd [0, 0, 1.6];
            if (!_trouve && { (count (lineIntersectsSurfaces [_oeil, _cible, _chef, objNull, true, 1, "VIEW", "VIEW"])) == 0 }) then { _az = _x; _trouve = true };
        } forEach [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340];
        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE ( mesure du 18/09 : 4 episodes sur 22 posaient la cible derriere un obstacle ) :
            // on refuse l episode plutot que de mesurer le relief au lieu de la perception.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE", round (time * 100) / 100,
                _phase, CHACAL_CONTROLE_DIST]) call CHACAL_LOG;
        };
        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;
        { private _u = _g createUnit [_x, _p, [], 3, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE"; _u setUnitPos "UP" } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE"; _g setBehaviour "SAFE";
        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
        if (CHACAL_CONTROLE_PERCEPTION == 5) then {
            private _cibleU = leader _g;
            { _x doWatch _cibleU } forEach _hommes;   // banc : ils fixent la cible, aucune ambiguite de direction
            _regards = [];                            // le banc ne balaie pas
        } else {
            _regards = [getPosATL (leader _g)];       // controle POSITIF : la cible est dans le secteur balaye
        };
        (format ["CHACAL|E|banc_perception|%1|phase|%2|distance|%3|azimut|%4|ligne_de_vue|%5|heure|%6|lune|%7|jumelles|%8|hommes|%9",
            round (time * 100) / 100, _phase, CHACAL_CONTROLE_DIST, round _az, (if (_trouve) then {1} else {0}),
            (date select 3) + ((date select 4) / 60), moonIntensity,
            ((_hommes apply { hmd _x }) joinString ","), count _hommes]) call CHACAL_LOG;
    };
    if ((CHACAL_CONTROLE_PERCEPTION in [2, 3]) && { count _hommes > 0 }) then {
        private _chef = leader (group (_hommes select 0));
        private _p = if (CHACAL_CONTROLE_PERCEPTION == 2) then { _chef getPos [1500, (getDir _chef) + 180] } else { _chef getPos [150, getDir _chef] };
        private _g = createGroup east;
        {
            private _u = _g createUnit [_x, _p, [], 5, "NONE"];
            _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE";
            _u setUnitPos (if (CHACAL_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"});
        } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE";
        CHACAL_MENACES pushBack [_phase, "CONTROLE_PERCEPTION", _g];
        (format ["CHACAL|E|controle_perception|%1|phase|%2|mode|%3|distance|%4|posture|%5", round (time * 100) / 100, _phase,
            CHACAL_CONTROLE_PERCEPTION, round (_chef distance2D _p), (if (CHACAL_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"})]) call CHACAL_LOG;
    };
    (format ["CHACAL|E|observation|%1|phase|%2|debut|duree_prevue|%3%4", round (time * 100) / 100, _phase, CHACAL_OBSERVATION,
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
    (format ["CHACAL|E|reglage_observation|%1|phase|%2|avant|%3|balayage|%4|distance_secteur|%5|azimuts|%6", round (time * 100) / 100, _phase,
        CHACAL_AVANT, CHACAL_BALAYAGE, (if (count _secteur > 0) then { round (((_hommes select 0) distance2D _secteur)) } else { -1 }), count _regards]) call CHACAL_LOG;
    private _prochain = time; private _tRegard = 0; private _iRegard = -1;
    waitUntil {
        sleep 1;
        if ((count _regards > 0) && { time >= _tRegard }) then {
            _tRegard = time + 10; _iRegard = (_iRegard + 1) % (count _regards);
            // ! levier CHACAL_BALAYAGE : 1 = chaque changement d azimut TOURNE les hommes ( setDir ) avant le doWatch ; 0 = origine
            {
                if (CHACAL_BALAYAGE == 1) then { _x setDir (_x getDir (_regards select _iRegard)) };
                _x doWatch (_regards select _iRegard);
            } forEach (CHACAL_FS select { alive _x });
        };
        if ((CHACAL_SONDE > 0) && { time >= _prochain }) then {
            _prochain = time + 5;
            private _angles = [];
            {
                private _t = _x;
                private _a = 999;
                { private _r = abs ((((_x getDir _t) - (getDir _x) + 540) % 360) - 180); if (_r < _a) then { _a = _r } } forEach (CHACAL_FS select { alive _x });
                _angles pushBack (round _a);
            } forEach (call CHACAL_fnc_unitesMenace);
            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3|angle_min|%4%5", round (time * 100) / 100, _phase,
                round (time - _t0), (if (count _angles > 0) then { selectMin _angles } else { -1 }),
                call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
        };
        CHACAL_FIN || ((time - _t0) >= (CHACAL_OBSERVATION * CHACAL_ECHELLE))
    };
    // ! RENDRE LA MAIN ( faute du 17/09 : sans ceci, les trois elements de la phase 4 ne repartent jamais et les huit
    // episodes finissent au plafond, 55 min au lieu de 5 ).
    {
        if (alive _x) then { _x doWatch objNull; _x setUnitPos "AUTO"; _x doFollow (leader (group _x)) };
    } forEach _hommes;
    (format ["CHACAL|E|observation|%1|phase|%2|fin|duree|%3%4", round (time * 100) / 100, _phase, round (time - _t0),
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
};
CHACAL_fnc_decision = {
    params ["_phase", "_point", "_options", "_choix", "_decideur", ["_extra", ""]];
    private _def = (if (isNil "CHACAL_EST_SITE") then {[]} else {CHACAL_EST_SITE}) select { alive _x };
    (format ["CHACAL|E|decision|%1|phase|%2|point|%3|options|%4|choix|%5|decideur|%6|alarme|%7|depuis_alarme|%8|compromis|%9|vivants|%10|defenseurs_connus|%11|verite_defenseurs|%12|situation|%13%14",
        round (time * 100) / 100, _phase, _point, _options, _choix, _decideur,
        (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_T_ALARME >= 0) then { round (time - CHACAL_T_ALARME) } else { -1 }),
        (if (CHACAL_COMPROMIS) then {1} else {0}),
        count (CHACAL_FS select { alive _x }),
        { (west knowsAbout _x) > 1.4 } count _def,
        count _def, CHACAL_SITUATION, _extra + (call CHACAL_fnc_perceptionMenace)]) call CHACAL_LOG;
};
// Interprete des formules EvoGP ( codes prefixes ). ">" vaut +1 si a > b, sinon -1, comme dans EvoGP ( mesure le 17/09 ).
CHACAL_F_CONST = [-1, -0.5, -0.25, 0, 0.25, 0.5, 1];
CHACAL_fnc_evalNoeud = {
    params ["_i", "_obs"];
    private _c = CHACAL_F select _i;
    if (_c >= 301) exitWith { [CHACAL_F_CONST select (_c - 301), _i + 1] };
    if (_c >= 201) exitWith { [_obs select (_c - 201), _i + 1] };
    if (_c == 106) exitWith { private _m = [_i + 1, _obs] call CHACAL_fnc_evalNoeud; [-(_m select 0), _m select 1] };
    private _g = [_i + 1, _obs] call CHACAL_fnc_evalNoeud;
    private _d = [_g select 1, _obs] call CHACAL_fnc_evalNoeud;
    private _u = _g select 0; private _v = _d select 0;
    private _r = switch (_c) do {
        case 101: { _u + _v };
        case 102: { _u - _v };
        case 103: { _u * _v };
        case 104: { _u min _v };
        case 105: { _u max _v };
        case 107: { if (_u > _v) then {1} else {-1} };
        default { (format ["CHACAL|ERREUR|formule|code_inconnu|%1", _c]) call CHACAL_LOG; 0 };
    };
    [_r, _d select 1]
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
                // ! MESURE, PAS COMPORTEMENT ( 09/09 ). Le moteur peut declarer un deplacement
                // TERMINE loin de la cible : commande vide, unitReady vrai, point de passage
                // consomme. C est la signature exacte du palier 4, ou l assaut est reste a
                // 800 m pendant 2000 s. On la journalise pour savoir si CHACAL_ACCESSIBLE la
                // fait disparaitre — sans elle, on ne pourrait pas dire si le remede a mordu.
                private _l2 = leader _g;
                if (unitReady _l2 && { (currentCommand _l2) == "" } && { (currentWaypoint _g) >= (count (waypoints _g)) } && { _d > _ray }) then {
                    if (_immobile == 5) then {
                        (format ["CHACAL|E|moteur_dit_fini|%1|%2|reste|%3|rayon|%4|pente_trajet|%5",
                            round (time * 100) / 100, _nom, round _d, _ray,
                            round ([getPosATL _l2, _p] call CHACAL_fnc_penteTrajet)]) call CHACAL_LOG;
                    };
                };
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

// ! LE CHOIX DE LA PHASE 4 ( plans/plan-choix-par-vignette.md, 17/09 ) : itineraire direct ou detour. A ITINERAIRE = 2,
// chaque element passe d abord par un point decale de 350 m a droite de son axe, a mi-chemin, puis rejoint sa
// position comme avant. Sans tirage : le point est geometrique ; s il tombe dans l eau, on prend la gauche et on le dit.
CHACAL_fnc_rejoindreItineraire = {
    params ["_g", "_p", "_ray", "_plafond", "_nom"];
    if (isNull _g) exitWith { "ABSENT" };
    if (CHACAL_ITINERAIRE == 2) then {
        private _v = (units _g) select { alive _x };
        if (count _v > 0) then {
            private _c = _v call CHACAL_fnc_centre;
            private _dir = _c getDir _p;
            private _mi = _c getPos [(_c distance2D _p) / 2, _dir];
            private _cote = 90;
            private _wp = _mi getPos [350, _dir + _cote];
            if (surfaceIsWater _wp) then { _cote = -90; _wp = _mi getPos [350, _dir + _cote] };
            _wp set [2, 0];
            private _t0 = time;
            [_g, _wp, "NORMAL", "AWARE", "WEDGE", _nom + "_DETOUR"] call CHACAL_fnc_ordreAller;
            private _rD = [_g, _wp, 80, ([_g, _wp] call CHACAL_fnc_budgetDeuxJambes)] call CHACAL_fnc_arrive;
            (format ["CHACAL|E|choix_joue|%1|point|ITINERAIRE|choix|2|detail|DETOUR|element|%2|cote|%3|point_detour|%4|issue|%5|duree|%6",
                round (time * 100) / 100, _nom, _cote, _wp, _rD, round (time - _t0)]) call CHACAL_LOG;
            _plafond = _plafond - (time - _t0);
        };
    } else {
        if (CHACAL_ITINERAIRE == 1) then {
            (format ["CHACAL|E|choix_joue|%1|point|ITINERAIRE|choix|1|detail|DIRECT|element|%2", round (time * 100) / 100, _nom]) call CHACAL_LOG;
        };
    };
    [_g, _p, _ray, (_plafond max 60), _nom] call CHACAL_fnc_rejoindre
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
    if (CHACAL_PHASE < 5) then { CHACAL_SAUT = (CHACAL_TENIR == 0) };

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
// ! DEPART A LA ROUTE ( 16/09 ). La phase 2 se jouait apres ~50 min de marche depuis la zone de poser.
// DEPART = 2 pose le detachement a 330 m de la route et joue la traversee. Les hommes sont poses en
// anneau fixe, SANS tirage : ni l alea du monde ni celui de la situation ne bougent.
if (CHACAL_DEPART == 2) then {
    "CHACAL|AVERT|hors_corpus|depart|2|insertion_non_jouee" call CHACAL_LOG;
    private _pt = CHACAL_ROUTE getPos [CHACAL_AVANT + 70, CHACAL_ROUTE getDir CHACAL_LZ];   // 70 m derriere le point d observation, comme a l origine ( 260 + 70 = 330 )
    private _k = 0;
    { if (alive _x) then { _x setPosATL (_pt getPos [10, _k * 36]); _k = _k + 1 } } forEach CHACAL_FS;
    CHACAL_gFS setBehaviour "STEALTH"; CHACAL_gFS setCombatMode "GREEN";
    CHACAL_gFS setSpeedMode "LIMITED"; CHACAL_gFS setFormation "FILE";
    (format ["CHACAL|E|depart_direct|%1|a_la_route|%2", round (time * 100) / 100, _pt]) call CHACAL_LOG;
    sleep 5;
} else {
_plafond = 1 call CHACAL_fnc_duree;
// ! GEOMETRIE SEULE : le monde est tire, on le publie, et on s arrete. Aucun coup de feu,
// aucune issue de mission. C est la facon exacte de connaitre un site sans l user.
if (CHACAL_GEOMETRIE == 1) exitWith {
    (format ["CHACAL|GEO|%1|graine|%2|site|%3|crete|%4|route|%5|lz|%6|qrf|%7|pz|%8|rally|%9|ouvertures|%10|az_site|%11|gain_crete|%12",
        round (time * 100) / 100, CHACAL_GRAINE, CHACAL_SITE, CHACAL_OP, CHACAL_ROUTE,
        CHACAL_LZ, CHACAL_QRF_BASE, CHACAL_PZ, CHACAL_RALLY,
        (if (isNil "CHACAL_OUVERTURES") then {[]} else {CHACAL_OUVERTURES apply { round (CHACAL_SITE getDir _x) }}),
        (if (isNil "CHACAL_AZ") then {-1} else {round CHACAL_AZ}), round CHACAL_OP_GAIN]) call CHACAL_LOG;
    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "GEOMETRIE_SEULE"; CHACAL_FIN = true;
};

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

private _morts = CHACAL_EFFECTIF - (count (CHACAL_FS select { alive _x }));
// ! MORTS SOUS LE FEU ENNEMI ( 16/09, decision de Younes ). Avec des menaces pres du poser, un homme
// tue par l ennemi est une ISSUE : un poser mal choisi coute des vies, et l agent doit l apprendre.
// Seule une mort sans tueur ennemi ( physique, ecrasement ) annule encore l episode.
private _parEnnemi = { !alive _x && { _x getVariable ["chacal_tue_par_est", false] } } count CHACAL_FS;
if (_parEnnemi > 0) then {
    (format ["CHACAL|E|insertion_sous_le_feu|%1|morts_par_ennemi|%2|morts_total|%3", round (time * 100) / 100, _parEnnemi, _morts]) call CHACAL_LOG;
};
if ((_morts - _parEnnemi) > 0) exitWith {
    // Une insertion qui tue n est pas une insertion. On ne la rattrape pas : on
    // REFUSE l episode. Continuer a huit produirait un corpus ou l echec serait
    // mis au compte de la tactique.
    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "INSERTION_MORTELLE";
    (format ["CHACAL|VOID|insertion|%1|morts|%2|au_sol|%3", round (time * 100) / 100, _morts, count _auSol]) call CHACAL_LOG;
    CHACAL_FIN = true;
};
if (count _auSol < (CHACAL_EFFECTIF - _parEnnemi)) exitWith {
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
// ! LE CHOIX DE LA PHASE 1 ( plans/plan-choix-par-vignette.md, 17/09 ) : partir tout de suite ou se terrer.
// Les deux options durent 180 s, pour que la consequence ait le meme temps d arriver. 0 = les 60 s d origine.
if (CHACAL_P1_ATTENTE > 0) then {
    [1] call CHACAL_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )
    [1, "INSERTION_ATTENTE", [1, 2], CHACAL_P1_ATTENTE, "IMPOSE"] call CHACAL_fnc_decision;
    if (CHACAL_P1_ATTENTE == 1) then {
        private _dest = CHACAL_LZ getPos [300, CHACAL_LZ getDir CHACAL_ROUTE];
        [CHACAL_gFS, _dest, "LIMITED", "STEALTH", "FILE", "CHOIX_P1_PARTIR"] call CHACAL_fnc_ordreAller;
        (format ["CHACAL|E|choix_joue|%1|point|INSERTION_ATTENTE|choix|1|detail|PARTIR|vers|%2", round (time * 100) / 100, _dest]) call CHACAL_LOG;
    } else {
        { if (alive _x) then { doStop _x; _x setUnitPos "DOWN" } } forEach (units CHACAL_gFS);
        (format ["CHACAL|E|choix_joue|%1|point|INSERTION_ATTENTE|choix|2|detail|SE_TERRER", round (time * 100) / 100]) call CHACAL_LOG;
    };
    private _tC = time;
    waitUntil { sleep 2; ((time - _tC) > 180) || CHACAL_FIN };
    { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units CHACAL_gFS);
} else {
    sleep (60 * CHACAL_ECHELLE);
};
[1, "INSERTION", _issue] call CHACAL_fnc_finPhase;
};   // fin de l alternative DEPART = 2

// ---------------------------------------------------------------------
// PHASE 2 - APPROCHE, et le franchissement de la route
// ---------------------------------------------------------------------
if (CHACAL_FIN) exitWith {};   // vignette close a la phase 1
_plafond = 2 call CHACAL_fnc_duree;
[2, "APPROCHE", _plafond] call CHACAL_fnc_debutPhase;

private _fr = CHACAL_ROUTE;
private _avant = _fr getPos [CHACAL_AVANT, _fr getDir CHACAL_LZ];   // levier : d ou l on observe la route ( origine 260 m )

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
    // ! LE CHOIX DE LA PHASE 2 ( plans/plan-choix-par-vignette.md, 17/09 ) : traverser tout de suite ( 1 ) ou attendre la
    // patrouille ( 2 ). ATTENDRE applique la regle de perception SANS la sortie PATROUILLE_ABSENTE, qui lisait l etat vrai
    // du monde : le detachement ne peut pas savoir qu aucune patrouille ne viendra. 0 = la regle d origine, inchangee.
    if (CHACAL_TRAVERSEE > 0) then {
        [2] call CHACAL_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )
        private _vD = if (isNil "CHACAL_VEH_ROUTE") then { objNull } else { CHACAL_VEH_ROUTE };
        private _vuD = 0;
        if (!isNull _vD && { alive _vD }) then {
            if (({ [_x, _vD, 800, 70] call CHACAL_fnc_voit } count ((units CHACAL_gFS) select { alive _x })) > 0) then { _vuD = 1 };
        };
        [2, "TRAVERSEE", [1, 2], CHACAL_TRAVERSEE, "IMPOSE", format ["|vehicule_vu|%1", _vuD]] call CHACAL_fnc_decision;
    };
    private _tf = time;
    private _dejaVu = false; private _dernierVu = -1; private _traverse = false; private _cause = "";
    while { !_traverse && (time - _tf < 420 * CHACAL_ECHELLE) && ((call CHACAL_fnc_reste) > 0) && !CHACAL_SAUT && !CHACAL_FIN } do {
        if (CHACAL_TRAVERSEE == 1) then { _traverse = true; _cause = "IMPOSE_TOUT_DE_SUITE" } else {
            private _v = CHACAL_VEH_ROUTE;
            private _vu = false;
            if (!isNull _v && { alive _v }) then {
                private _hommes = (units CHACAL_gFS) select { alive _x };
                _vu = ({ [_x, _v, 800, 70] call CHACAL_fnc_voit } count _hommes) > 0;
            };
            if (_vu) then { _dejaVu = true; _dernierVu = time };
            if (_dejaVu && { !_vu } && { (time - _dernierVu) > (45 * CHACAL_ECHELLE) }) then { _traverse = true; _cause = "FENETRE_OBSERVEE" };
            if (!_dejaVu && { (time - _tf) > (240 * CHACAL_ECHELLE) }) then { _traverse = true; _cause = "TRAVERSEE_AVEUGLE" };
            if ((CHACAL_TRAVERSEE != 2) && { isNull _v || { !alive _v } }) then { _traverse = true; _cause = "PATROUILLE_ABSENTE" };
            sleep 3;
        };
    };
    if (!_traverse) then { _cause = "PLAFOND_FENETRE" };
    (format ["CHACAL|E|fenetre|%1|%2|attente|%3|vehicule_vu|%4", round (time * 100) / 100,
        _cause, round (time - _tf), (if (_dejaVu) then {1} else {0})]) call CHACAL_LOG;
    if (CHACAL_TRAVERSEE > 0) then {
        (format ["CHACAL|E|choix_joue|%1|point|TRAVERSEE|choix|%2|detail|%3|attente|%4", round (time * 100) / 100,
            CHACAL_TRAVERSEE, _cause, round (time - _tf)]) call CHACAL_LOG;
    };
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

// ! VIGNETTE DE LA ROUTE ( 16/09 ) : au depart a la route avec arret a la phase 2, la phase s arrete a la
// sortie du couloir, sans la marche de ~1,7 km jusqu au regroupement qui ne decide plus rien.
if (!CHACAL_SAUT && { !(CHACAL_DEPART == 2 && CHACAL_ARRET == 2) }) then {
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
if (CHACAL_TENIR == 0 && CHACAL_COMPROMIS && { ((CHACAL_FS select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_SITE > 1200 }) then {
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
    // ! COUPURE ASSUMEE ET ECRITE. Voir verdicts/phase3-porte-hors-datteinte.md.
    if (CHACAL_OBS == 0) exitWith {
        (format ["CHACAL|AVERT|hors_corpus|observation_coupee|1|seuil|%1|jamais_atteint|1",
            CHACAL_SEUIL_RENS]) call CHACAL_LOG;
        (format ["CHACAL|E|observation_coupee|%1|economie_s|%2", round (time * 100) / 100,
            round _plafond]) call CHACAL_LOG;
        [3, "OBSERVATION", "COUPEE"] call CHACAL_fnc_finPhase;
    };

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
    // ! LE CHOIX DE LA PHASE 3 ( plans/plan-choix-par-vignette.md, 17/09 ) : observer 120 ou 480 s. Le rapprochement
    // vers un second poste est une AUTRE decision : il n est pas joue quand la duree est imposee. 0 = regle d origine.
    private _dureeObs = _plafond * 0.55;
    if (CHACAL_OBS_DUREE > 0) then {
        _dureeObs = CHACAL_OBS_DUREE;
        [3, "OBS_DUREE", [120, 480], CHACAL_OBS_DUREE, "IMPOSE", format ["|reco_vivants|%1", count ((units CHACAL_gReco) select { alive _x })]] call CHACAL_fnc_decision;
    };
    private _tObs = time;
    while { (time - _tObs) < _dureeObs && ((call CHACAL_fnc_reste) > 0) && !CHACAL_SAUT && !CHACAL_FIN } do {
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
    if (CHACAL_OBS_DUREE > 0) then {
        (format ["CHACAL|E|choix_joue|%1|point|OBS_DUREE|choix|%2|detail|OBSERVE|duree_reelle|%3|localisees|%4|rapprochement|0",
            round (time * 100) / 100, CHACAL_OBS_DUREE, round (time - _tObs), count CHACAL_VUES]) call CHACAL_LOG;
    };
    if (!CHACAL_SAUT && { CHACAL_OBS_DUREE == 0 } && { count CHACAL_VUES < CHACAL_SEUIL_RENS }) then {
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

    // ! LA LIGNE DE DECISION ( 16/09 ). Elle porte l OPTION jouee ET l OBSERVABLE sur
    // lequel elle devrait se decider, sur une seule ligne, comme choix_ouverture le fait
    // pour les portes. C est elle qui remplira la table `decision` du socle : sans un
    // triplet ( etat, action, issue ) ecrit noir sur blanc, le banc n est pas un support
    // d apprentissage mais un tableau d affichage.
    // Les comptes sont pris SUR LES GROUPES REELS, pas sur les listes de roles : un homme
    // deja mort ne doit pas etre compte dans son element.
    // ! Le palier 9 ( monde vide, controle positif de l acte ) sort de 30_opfor AVANT de
    // definir CHACAL_PAL_QRF : d ou le garde isNil ci-dessous, sans lequel cette ligne
    // ecrirait une variable non definie dans la trace du controle positif.
    (format ["CHACAL|E|partage|%1|regle|%2|assaut|%3|bouchon|%4|appui|%5|qrf_vehicules|%6|qrf_hommes|%7|delai_qrf|%8",
        round (time * 100) / 100,
        (if (CHACAL_PARTAGE == 1) then {"SEPT_UN"} else {"CINQ_TROIS"}),
        count (units CHACAL_gAssaut), count (units CHACAL_gBouchon), count (units CHACAL_gAppui),
        (if (isNil "CHACAL_PAL_QRF") then {0} else {CHACAL_PAL_QRF}), count CHACAL_QRF, CHACAL_PAL_DELAI]) call CHACAL_LOG;

    // ! LE RENSEIGNEMENT CHOISIT L OUVERTURE. Le premier jet visait az_OP + 99 :
    // une constante deguisee en tactique, et c est " marche au 315 " en repere
    // relatif. Ici on compte les sentinelles LOCALISEES pres de chaque porte et
    // on entre par la moins gardee.
    // ! LE CHOIX PESE LES GARDES *ET* LE TRAJET. Ne regarder que les sentinelles
    // fait entrer par une porte deux fois plus loin pour eviter quatre hommes -
    // et sur une nuit ou l articulation est deja le goulot, ce marche est
    // mauvais. Un garde localise vaut 150 m de marche ; l arbitrage est
    // journalise pour qu il soit discutable.
    // ! L ORACLE COMPLET ( CHACAL_ORACLE = 2, revue de Fable 11/09 ) : les defenseurs sont reveles et
    // inscrits comme vus AVANT le choix de la porte, qui se fait alors en les connaissant.
    if (CHACAL_ORACLE == 2) then {
        private _defO = CHACAL_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _defO } forEach (CHACAL_FS select { alive _x });
        CHACAL_VUES = _defO apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4|avant_choix_porte|1", round (time * 100) / 100,
            count _defO, count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };
    private _dep = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
    if (count _dep == 0) then { _dep = CHACAL_RALLY };
    // ! MARQUEUR-GARDE-PLUS-PROCHE - LE TERME DE GARDE ETAIT INERTE PAR CONSTRUCTION ( 15/09 ).
    // Le seuil de 110 m se voulait " pres de cette porte ". L enceinte a 46 m de rayon, les deux
    // ouvertures sont a 108,0 et 282,857 relatifs - une corde de 92 m - et la garnison se garnit
    // dans 55 m : tout defenseur est donc a moins de 101 m des DEUX ouvertures. Mesure sur les
    // journaux : le champ gardes vaut [k,k] dans 1337 episodes sur 1337, et l indice retenu est
    // l ouverture la plus proche dans 1337 sur 1337. Le terme ne decidait rien.
    // LA REGLE DEVIENT SANS SEUIL : chaque defenseur connu compte pour l ouverture dont il est le
    // PLUS PROCHE. Discriminant par construction des que CHACAL_VUES n est pas vide.
    // Le poids reste " un garde vaut 150 m de marche ", et c est mesure : |d_A - d_B| vaut 18 m en
    // mediane, 83 m au pire, jamais plus que la corde de 92 m, soit 0,55 point au plus contre 1,00
    // pour un garde. Des que les comptes different le compte decide ; a comptes egaux la distance
    // tranche. L intention publiee devient vraie sans qu on touche au 150.
    // ! L affectation est calculee UNE FOIS, HORS de la boucle de score : une boucle imbriquee
    // dedans aurait masque _forEachIndex, dont la ligne du minimum a besoin. Aucun continue,
    // aucun break, aucun waitUntil n est introduit.
    private _connus = (CHACAL_VUES apply { _x select 0 }) select { !isNull _x };
    private _aff  = CHACAL_OUVERTURES apply { 0 };      // defenseurs connus attribues a l ouverture
    private _dgar = CHACAL_OUVERTURES apply { -1 };     // distance du defenseur connu le plus proche
    {
        private _pv = _x;                               // l unite, liee AVANT la boucle interne
        private _jv = -1; private _dv = 1e9;
        {
            private _dd = _pv distance2D _x;            // ici _x est une OUVERTURE
            if (_dd < _dv) then { _dv = _dd; _jv = _forEachIndex };
            if (((_dgar select _forEachIndex) < 0) || { _dd < (_dgar select _forEachIndex) }) then {
                _dgar set [_forEachIndex, _dd];
            };
        } forEach CHACAL_OUVERTURES;
        if (_jv >= 0) then { _aff set [_jv, (_aff select _jv) + 1] };
    } forEach _connus;
    private _meilleure = 0; private _minScore = 1e9; private _comptes = []; private _dists = [];
    {
        private _o = _x;
        private _n = _aff select _forEachIndex;
        private _d = _dep distance2D _o;
        private _sc = _n + (_d / 150);
        _comptes pushBack _n; _dists pushBack round _d;
        if (_sc < _minScore) then { _minScore = _sc; _meilleure = _forEachIndex };
    } forEach CHACAL_OUVERTURES;
    CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select _meilleure;
    // ! LA COUTURE DE L AZIMUT. Douze candidats publies, un decideur designe par CHACAL_AZIMUT.
    // Le mode 0 ne touche a rien : CHACAL_OUV_CHOISIE garde la valeur que le score vient de poser.
    // Les modes 1 et 2 remplacent le POINT VISE par un point de meme rayon a l azimut retenu, ce qui
    // laisse intact tout ce qui en depend en aval : la position d assaut, la cible, le poste d appui.
    private _candidats = [];
    for "_i" from 0 to 11 do { _candidats pushBack (_i * 30) };
    CHACAL_AZIMUT_CHOISI = round (CHACAL_SITE getDir CHACAL_OUV_CHOISIE);
    private _qui = "SCRIPT";
    if (CHACAL_AZIMUT == 1) then {
        // tirage seme par la graine : deux episodes de meme graine tirent le meme azimut, sinon
        // le temoin ne serait pas un temoin.
        // ! le TEMOIN, pas le generateur du monde : sinon le bras hasard tire un azimut fixe par graine
        private _k = floor ((call CHACAL_fnc_rndTemoin) * (count _candidats));
        if (_k >= count _candidats) then { _k = (count _candidats) - 1 };
        CHACAL_AZIMUT_CHOISI = _candidats select _k; _qui = "HASARD";
    };
    if (CHACAL_AZIMUT == 2) then {
        CHACAL_AZIMUT_CHOISI = ((round CHACAL_AZIMUT_VAL) + 360) % 360; _qui = "IMPOSE";
    };
    if (CHACAL_AZIMUT > 0) then {
        CHACAL_OUV_CHOISIE = CHACAL_SITE getPos [CHACAL_RAYON, CHACAL_AZIMUT_CHOISI];
        CHACAL_OUV_CHOISIE set [2, 0];
    };
    (format ["CHACAL|E|couture_azimut|%1|mode|%2|decideur|%3|candidats|%4|choisi|%5|point|%6|az_ouvertures|%7",
        round (time * 100) / 100, CHACAL_AZIMUT, _qui, count _candidats, CHACAL_AZIMUT_CHOISI,
        CHACAL_OUV_CHOISIE, (CHACAL_OUVERTURES apply { round (CHACAL_SITE getDir _x) })]) call CHACAL_LOG;
    // ! Champs AJOUTES EN FIN DE LIGNE. Aucun retire, aucun renomme : les analyses existantes
    // lisent indice, gardes, distances, score et renseignement par expression reguliere.
    //   dgarde : distance en metres du defenseur connu le plus proche de chaque ouverture, -1
    //            si aucun. A gardes egaux, dgarde dit si l egalite est vraie ou fortuite.
    //   regle  : la regle d attribution en vigueur, pour distinguer un journal d avant du patch.
    (format ["CHACAL|E|choix_ouverture|%1|indice|%2|gardes|%3|distances|%4|score|%5|renseignement|%6|dgarde|%7|regle|PLUS_PROCHE",
        round (time * 100) / 100, _meilleure, str _comptes, str _dists,
        round (_minScore * 100) / 100, count CHACAL_VUES,
        str (_dgar apply { if (_x < 0) then { -1 } else { round _x } })]) call CHACAL_LOG;

    // ! L APPUI N EST PLUS L OBSERVATOIRE ( sous parametre ). A 0, on garde la ligne d origine.
    CHACAL_POS_APPUI   = CHACAL_OP;
    // ! Le point de depart est passe depuis l element concerne : c est la seule facon de savoir
    // si le trajet est praticable. Sans CHACAL_ACCESSIBLE, l argument est ignore.
    private _depAssaut  = ((units CHACAL_gAssaut)  select { alive _x }) call CHACAL_fnc_centre;
    private _depBouchon = ((units CHACAL_gBouchon) select { alive _x }) call CHACAL_fnc_centre;
    CHACAL_POS_ASSAUT  = [CHACAL_SITE getPos [230, CHACAL_SITE getDir CHACAL_OUV_CHOISIE], 60, 220, _depAssaut] call CHACAL_fnc_plat;
    // ! 700 m sur l axe de la reserve etait un chiffre ecrit sans justification,
    // et il demandait au bouchon une demi-heure de marche. Son travail est de
    // RETARDER la reserve, pas de tenir un carrefour : 400 m le font aussi bien.
    CHACAL_POS_BOUCHON = [CHACAL_SITE getPos [400, CHACAL_SITE getDir CHACAL_QRF_BASE], 80, 220, _depBouchon] call CHACAL_fnc_plat;
    if (CHACAL_APPUI_FEU == 1) then {
        CHACAL_POS_APPUI = [CHACAL_SITE, CHACAL_OUV_CHOISIE, CHACAL_POS_ASSAUT, CHACAL_OP] call CHACAL_fnc_positionAppui;
    };
    // ! V9 ( Fable, 11/09 ) : une fois en place, l appui tient sa place. YELLOW = tir a volonte,
    // garde ta place ; RED = engage a volonte, et on l a mesure partir au contact a 11-18 km/h.
    if (CHACAL_APPUI_FIXE == 1) then {
        [] spawn {
            waitUntil { sleep 2; CHACAL_FIN || { !isNull CHACAL_gAppui && { [CHACAL_gAppui, CHACAL_POS_APPUI, 70] call CHACAL_fnc_enPlace } } };
            if (CHACAL_FIN || { isNull CHACAL_gAppui }) exitWith {};
            CHACAL_gAppui setCombatMode "YELLOW";
            CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true];
            { if (alive _x) then { _x disableAI "PATH"; _x setVariable ["lambs_danger_disableAI", true, true] } } forEach (units CHACAL_gAppui);
            (format ["CHACAL|E|appui_fixe|%1|position|%2|compromis|%3", round (time * 100) / 100, CHACAL_POS_APPUI,
                (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
        };
    };

    // Le plafond est la SOMME des deux jambes, calculee sur les vitesses
    // reellement ordonnees - 1,1 m/s puis 0,5 - et non sur une constante
    // d infiltration qui mentait d un facteur deux.
    private _b1 = [CHACAL_gAppui,   CHACAL_POS_APPUI]   call CHACAL_fnc_budgetDeuxJambes;
    private _b2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT]  call CHACAL_fnc_budgetDeuxJambes;
    private _b3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON] call CHACAL_fnc_budgetDeuxJambes;
    _plafond = (_b1 max _b2) max _b3;
    // ! Un choix d itineraire impose double le plafond pour LES DEUX options : un detour ne doit pas echouer au chronometre.
    if (CHACAL_ITINERAIRE > 0) then { _plafond = _plafond * 2 };
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
    // ! L ORACLE ( Fable, 11/09 ) : que vaut le renseignement PARFAIT ? Les defenseurs du site sont
    // reveles a TOUS nos hommes et inscrits comme vus, avant la mise en place. 0 = origine.
    if (CHACAL_ORACLE >= 1) then {
        private _def = CHACAL_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (CHACAL_FS select { alive _x });
        CHACAL_VUES = _def apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4", round (time * 100) / 100, count _def,
            count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };
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
        if (CHACAL_ITINERAIRE > 0) then { [4] call CHACAL_fnc_fenetreObservation; [4, "ITINERAIRE", [1, 2], CHACAL_ITINERAIRE, "IMPOSE"] call CHACAL_fnc_decision };
        private _h1 = [CHACAL_gAppui,   CHACAL_POS_APPUI,   70, _plafond, "APPUI"]   spawn CHACAL_fnc_rejoindreItineraire;
        private _h2 = [CHACAL_gAssaut,  CHACAL_POS_ASSAUT,  70, _plafond, "ASSAUT"]  spawn CHACAL_fnc_rejoindreItineraire;
        private _h3 = [CHACAL_gBouchon, CHACAL_POS_BOUCHON, 80, _plafond, "BOUCHON"] spawn CHACAL_fnc_rejoindreItineraire;
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
// ! PRIX DU TEMPS : l attente est prise AVANT le debut de la phase, donc elle ne mange aucun plafond. Le seul cout
// possible est celui du monde qui tourne ( patrouilles, alarme, renfort ) - c est justement ce qu on veut mesurer.
if (CHACAL_ATTENTE_TEST > 0) then {
    private _tA = time;
    // ! V2 - ON FIGE PENDANT L ATTENTE. La v1 laissait les hommes sans ordre : ils reprenaient leur mouvement
    // precedent, marchaient 818 m, puis revenaient. A 600 s l assaut etait a 330-670 m de sa place et la mission
    // renoncait ( ARTICULATION_ROMPUE ) 14 fois sur 16, alarme 0 et 10 vivants sur 10. Une attente doit couter le
    // temps du monde qui tourne, pas la dislocation du detachement.
    // L appui deja fige par CHACAL_APPUI_FIXE n est pas touche : lui rendre PATH le ferait partir, et seulement
    // dans les bras qui attendent.
    private _fige = (CHACAL_FS select { alive _x }) select { !(CHACAL_APPUI_FIXE == 1 && { group _x == CHACAL_gAppui }) };
    private _avant = _fige apply { [_x, getPosATL _x] };
    { doStop _x; _x disableAI "PATH" } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|debut|duree_prevue|%2|vivants|%3|alarme|%4|figes|%5", round (time * 100) / 100,
        CHACAL_ATTENTE_TEST, count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        count _fige]) call CHACAL_LOG;
    waitUntil { sleep 2; CHACAL_FIN || ((time - _tA) >= (CHACAL_ATTENTE_TEST * CHACAL_ECHELLE)) };
    private _derive = 0;
    { _x params ["_u", "_p"]; if (alive _u) then { _derive = _derive max (_u distance2D _p) } } forEach _avant;
    { if (alive _x) then { _x enableAI "PATH"; _x doFollow (leader (group _x)) } } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|fin|duree|%2|vivants|%3|alarme|%4|compromis|%5|derive|%6", round (time * 100) / 100,
        round (time - _tA), count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_COMPROMIS) then {1} else {0}), round _derive]) call CHACAL_LOG;
};
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
// ! L ORACLE : la connaissance se rafraichit au debut de l assaut, pour tous nos hommes.
if (CHACAL_ORACLE >= 1) then {
    private _def = CHACAL_EST_SITE select { alive _x };
    { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (CHACAL_FS select { alive _x });
    (format ["CHACAL|E|oracle|%1|reveles|%2|phase|5", round (time * 100) / 100, count _def]) call CHACAL_LOG;
};
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
    CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode (if (CHACAL_APPUI_FIXE == 1) then {"YELLOW"} else {"RED"}); CHACAL_gAppui setSpeedMode "LIMITED";
    private _cibles = (CHACAL_VUES apply { _x select 0 }) select { alive _x };
    { if (alive _x && { count _cibles > 0 }) then { _x doTarget (_cibles select 0); _x doFire (_cibles select 0) } } forEach (units CHACAL_gAppui);
};

// ! CONTROLE POSITIF DE L APPUI : l episode ne mesure QUE l appui et se ferme ici. L exitWith est indispensable :
// sans lui, toute la suite de la phase 5 s ecrirait APRES la ligne FINI et la porte de lecture refuserait l episode.
if (CHACAL_BANC_APPUI > 0) exitWith {
    call CHACAL_fnc_bancAppui;
    [5, "ASSAUT", "BANC_APPUI"] call CHACAL_fnc_finPhase;
    CHACAL_FIN = true;
};
// ! LE SOCLE ET LA TACTIQUE ( document du 11/09 ). Le socle repare l execution, la tactique conduit l appui.
if (CHACAL_SOCLE == 1) then { call CHACAL_fnc_socleAssaut };
if (CHACAL_TACTIQUE == 5) then {
    // T5 : personne ne tire tant que rien ne nous tire dessus. A la premiere balle, on bascule en T1.
    { if (!isNull _x) then { _x setCombatMode "GREEN" } } forEach [CHACAL_gAppui, CHACAL_gAssaut, CHACAL_gBouchon];
    CHACAL_gAssaut setBehaviour "STEALTH";
    [] spawn {
        waitUntil { sleep 2; CHACAL_FIN || { CHACAL_PHASE != 5 } || { count CHACAL_CONNUS > 0 } || CHACAL_COMPROMIS };
        if (CHACAL_FIN || { CHACAL_PHASE != 5 }) exitWith {};
        CHACAL_TACTIQUE = 1;
        { if (!isNull _x) then { _x setCombatMode "RED" } } forEach [CHACAL_gAppui, CHACAL_gBouchon];
        CHACAL_gAssaut setBehaviour "AWARE"; CHACAL_gAssaut setCombatMode "YELLOW";
        (format ["CHACAL|E|bascule_t5_vers_t1|%1|connus|%2|compromis|%3", round (time * 100) / 100,
            count CHACAL_CONNUS, (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
    };
};
if (CHACAL_TACTIQUE > 0) then { [] spawn CHACAL_fnc_tactiqueAppui };
if (CHACAL_SOCLE == 1 && { !(1 call CHACAL_fnc_sans) }) then { [] spawn CHACAL_fnc_chienDeGarde };
// L assaut attend : T1 le premier coup de l appui ( 120 s au plus ), T2 qu il ne reste au plus qu un defenseur ( 8 min ).
if (CHACAL_TACTIQUE == 1) then {
    private _tA = time;
    waitUntil { sleep 1; (CHACAL_T_PREMIER_TIR_APPUI > 0) || { time - _tA > 120 } || CHACAL_FIN };
    sleep 5;
    (format ["CHACAL|E|t1_depart|%1|premier_tir_appui|%2|attente|%3", round (time * 100) / 100,
        round CHACAL_T_PREMIER_TIR_APPUI, round (time - _tA)]) call CHACAL_LOG;
};
if (CHACAL_TACTIQUE == 2) then {
    private _tA = time;
    waitUntil { sleep 2; (count (CHACAL_EST_SITE select { alive _x }) <= 1) || { time - _tA > 480 } || CHACAL_FIN };
    (format ["CHACAL|E|t2_depart|%1|defenseurs_restants|%2|attente|%3", round (time * 100) / 100,
        count (CHACAL_EST_SITE select { alive _x }), round (time - _tA)]) call CHACAL_LOG;
};

// ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ). Sur les echecs du palier 4, un seul fusilier
// fait 8 des 9 morts et l appui ne tire pas : il visait une cible qu il ne connaissait pas.
// Le compteur tourne dans les deux bras ; la designation et l attente seulement a FEU_AVANT = 1.
CHACAL_TIRS_APPUI = 0; CHACAL_T_PREMIER_TIR = -1; CHACAL_CIBLE_ASSAUT = []; CHACAL_RELANCES = 0;
if (!isNull CHACAL_gAppui) then {
    {
        _x addEventHandler ["Fired", {
            CHACAL_TIRS_APPUI = CHACAL_TIRS_APPUI + 1;
            if (CHACAL_T_PREMIER_TIR < 0) then { CHACAL_T_PREMIER_TIR = time };
        }];
    } forEach ((units CHACAL_gAppui) select { alive _x });
};
if (CHACAL_FEU_AVANT == 1 && { !isNull CHACAL_gAppui }) then {
    [] spawn {
        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
            private _def = CHACAL_EST_SITE select { alive _x };
            private _ref = if (count CHACAL_CIBLE_ASSAUT > 0) then { CHACAL_CIBLE_ASSAUT } else { CHACAL_OUV_CHOISIE };
            if (count _def > 0) then {
                _def = [_def, [_ref], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
                private _c = _def select 0;
                {
                    private _u = _x;
                    if (alive _u) then {
                        { _u reveal [_x, 4] } forEach _def;
                        _u doTarget _c; _u doFire _c;
                    };
                } forEach (units CHACAL_gAppui);
            };
            sleep 5;
        };
    };
    private _tG = time;
    waitUntil { sleep 1; (CHACAL_TIRS_APPUI > 0) || { (time - _tG) > (120 * CHACAL_ECHELLE) } || { CHACAL_FIN } };
    (format ["CHACAL|E|feu_avant|%1|premier_tir|%2|attente|%3|defenseurs_vivants|%4", round (time * 100) / 100,
        (if (CHACAL_T_PREMIER_TIR < 0) then {-1} else {round (CHACAL_T_PREMIER_TIR * 100) / 100}),
        round (time - _tG), count (CHACAL_EST_SITE select { alive _x })]) call CHACAL_LOG;
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

// ! V5 ( Fable, 11/09 ) : une mitrailleuse dans l assaut. L ADJOINT echange son fusil contre une Mk200.
if (CHACAL_MG_ASSAUT == 1) then {
    private _mg = (units CHACAL_gAssaut) select { alive _x && { (_x getVariable ["chacal_role", ""]) == "ADJOINT" } };
    if (count _mg == 0) then { _mg = (units CHACAL_gAssaut) select { alive _x && { !((_x getVariable ["chacal_role", ""]) in ["DEMO_1", "DEMO_2"]) } } };
    if (count _mg > 0) then {
        private _u = _mg select 0;
        { _u removeMagazines _x } forEach (getArray (configFile >> "CfgWeapons" >> (primaryWeapon _u) >> "magazines"));
        _u removeWeapon (primaryWeapon _u);
        for "_i" from 1 to 3 do { _u addMagazine "200Rnd_65x39_cased_Box" };
        _u addWeapon "LMG_Mk200_F";
        (format ["CHACAL|E|mg_assaut|%1|role|%2|arme|%3|munitions_chargees|%4|chargeurs_sac|%5", round (time * 100) / 100,
            (_u getVariable ["chacal_role", ""]), primaryWeapon _u, _u ammo "LMG_Mk200_F",
            { _x == "200Rnd_65x39_cased_Box" } count (magazines _u)]) call CHACAL_LOG;
    } else { "CHACAL|AVERT|mg_assaut|aucun_tireur_disponible" call CHACAL_LOG };
};
// ! LE CHOIX DE LA PHASE 5 ( plans/plan-choix-par-vignette.md, 16/09 ) : combien de temps laisser au porteur.
// Force par le job ( delai_porteur ), ecrit comme une decision juste avant le premier pas de l assaut. La menace
// ALARME_AVANT_ASSAUT est posee par une tache qui regarde la phase toutes les 2 s : on attend son drapeau, 10 s au
// plus, sinon l observable alarme serait lu avant la pose.
if (CHACAL_MENACE_P5 in [2, 3]) then {
    private _tDec = time;
    waitUntil { sleep 0.5; (!isNil "CHACAL_SITUATION_P5_FAITE") || CHACAL_FIN || ((time - _tDec) > 10) };
};
if ((CHACAL_DELAI_MODE == 1) && { CHACAL_F_LEN > 0 }) then {
    // memes perceptions, memes calculs et meme instant que la ligne de decision ecrite juste apres
    private _defF = (if (isNil "CHACAL_EST_SITE") then {[]} else {CHACAL_EST_SITE}) select { alive _x };
    private _obsF = [
        (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_T_ALARME >= 0) then { round (time - CHACAL_T_ALARME) } else { -1 }),
        (if (CHACAL_COMPROMIS) then {1} else {0}),
        count (CHACAL_FS select { alive _x }),
        { (west knowsAbout _x) > 1.4 } count _defF
    ];
    private _res = [0, _obsF] call CHACAL_fnc_evalNoeud;
    private _valF = _res select 0;
    CHACAL_DELAI_JOUE = if (_valF > 0) then {180} else {45};
    [5, "DELAI_PORTEUR", [45, 180], CHACAL_DELAI_JOUE, "FORMULE", format ["|valeur_formule|%1|codes_lus|%2|codes_attendus|%3", _valF, _res select 1, CHACAL_F_LEN]] call CHACAL_fnc_decision;
} else {
    [5, "DELAI_PORTEUR", [45, 180], CHACAL_DELAI_PORTEUR, "IMPOSE"] call CHACAL_fnc_decision;
};
// LE chiffre de Fable : les coups de l appui AVANT le premier pas de l assaut.
(format ["CHACAL|E|premier_pas_assaut|%1|tirs_appui_avant|%2|feu_avant|%3", round (time * 100) / 100,
    CHACAL_TIRS_APPUI, CHACAL_FEU_AVANT]) call CHACAL_LOG;
// ! Le mode COMBAT fige l assaut ( plus de 120 s immobile a 65 m de la tour ). A FEU_AVANT = 1 il
// marche en AWARE, et un ordre donne une seule fois est relance toutes les 10 s.
// Une tactique marche en AWARE : le mode COMBAT fige l assaut ( plus de 120 s mesurees a 65 m de la tour ).
CHACAL_COMP_ASSAUT = if (CHACAL_FEU_AVANT == 1 || { CHACAL_TACTIQUE > 0 }) then {"AWARE"} else {"COMBAT"};
CHACAL_gAssaut setBehaviour CHACAL_COMP_ASSAUT; CHACAL_gAssaut setCombatMode "RED"; CHACAL_gAssaut setSpeedMode "FULL";
CHACAL_CIBLE_ASSAUT = +CHACAL_OUV_CHOISIE;
[CHACAL_gAssaut, CHACAL_OUV_CHOISIE, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "OUVERTURE_CHOISIE"] call CHACAL_fnc_ordreAller;
if (CHACAL_FEU_AVANT == 1 || { CHACAL_TACTIQUE > 0 }) then {
    [] spawn {
        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
            sleep 10;
            if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {
                CHACAL_gAssaut setBehaviour "AWARE";
                { if (alive _x) then { _x doMove CHACAL_CIBLE_ASSAUT } } forEach (units CHACAL_gAssaut);
                CHACAL_RELANCES = CHACAL_RELANCES + 1;
            };
        };
    };
};
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
    CHACAL_CIBLE_ASSAUT = +_pt;
    [CHACAL_gAssaut, _pt, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "OBJECTIF_" + (typeOf _o)] call CHACAL_fnc_ordreAller;
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
    // ! S1 ( 11/09 ) : la releve est ecrite d avance - DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN - et chaque homme
    // de l assaut porte une charge, donc un porteur mort a toujours un suivant.
    private _ordreP = ["DEMO_1", "DEMO_2", "ADJOINT", "CHEF", "MEDECIN"];
    private _demo = [];
    { private _r = _x; { if ((_x getVariable ["chacal_role", ""]) == _r) then { _demo pushBack _x } } forEach _porteurs } forEach _ordreP;
    private _h = if (count _demo > 0) then { _demo select 0 } else { _porteurs select 0 };
    _h doMove _pt;
    private _t = time;
    waitUntil { sleep 1; ((_h distance2D _pt) < 5) || !(alive _h) || (time - _t > CHACAL_DELAI_JOUE * CHACAL_ECHELLE) || CHACAL_FIN };
    private _dH = round (_h distance2D _pt);
    (format ["CHACAL|E|porteur|%1|%2|%3|temps|%4|distance|%5|delai|%6", round (time * 100) / 100, typeOf _o,
        (_h getVariable ["chacal_role", ""]), round (time - _t), _dH, CHACAL_DELAI_JOUE]) call CHACAL_LOG;
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
CHACAL_CIBLE_ASSAUT = +_abri;
[CHACAL_gAssaut, _abri, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "DEGAGEMENT_AVANT_MISE_A_FEU"] call CHACAL_fnc_ordreAller;
(format ["CHACAL|E|degagement|%1|vers|%2|charges|%3", round (time * 100) / 100, _abri, count CHACAL_CHARGES_OBJ]) call CHACAL_LOG;
private _rD = [CHACAL_gAssaut, _abri, 30, ((call CHACAL_fnc_reste) - 60) max 45, 60] call CHACAL_fnc_arrive;
[_rD] call CHACAL_fnc_miseAFeu;

// ! INCOMPLET est nouveau : la file s est terminee AVANT le plafond, et chaque
// manque porte sa cause. Ce n est pas un plafond, il ne faut pas l appeler ainsi.
private _iss5 = if (count CHACAL_CHARGES >= count CHACAL_OBJETS) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if ((call CHACAL_fnc_reste) <= 0) then {"PLAFOND"} else {"INCOMPLET"} } };
(format ["CHACAL|E|feu_appui_total|%1|tirs_appui|%2|relances_assaut|%3|feu_avant|%4", round (time * 100) / 100,
    CHACAL_TIRS_APPUI, CHACAL_RELANCES, CHACAL_FEU_AVANT]) call CHACAL_LOG;
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
private _vitBudget = if (CHACAL_EXFIL == 2) then {1.2} else {1.8};
_plafond = [(CHACAL_FS select { alive _x }), CHACAL_EXFIL_POINT, _vitBudget] call CHACAL_fnc_budget;
[6, "EXFILTRATION", _plafond] call CHACAL_fnc_debutPhase;
// ! LE CHOIX DE LA PHASE 6 ( plans/plan-choix-par-vignette.md, 17/09 ) : repli prudent ( EXFIL = 0 : le comportement du
// detachement tout du long ) ou rapide ( EXFIL = 1 : rompre en COMBAT puis AWARE et FULL au-dela de 200 m ). Ecrit a
// chaque exfiltration, comme le delai du porteur a chaque assaut. Remplace le choix principale / secours du plan :
// il n existe pas de second point d extraction dans la mission.
if (CHACAL_EXFIL in [0, 1]) then {
    private _vD6 = CHACAL_FS select { alive _x };
    private _dD6 = if (count _vD6 > 0) then { round ((_vD6 call CHACAL_fnc_centre) distance2D CHACAL_EXFIL_POINT) } else { -1 };
    [6, "EXFIL_ALLURE", [0, 1], CHACAL_EXFIL, "IMPOSE", format ["|distance_point|%1", _dD6]] call CHACAL_fnc_decision;
};
(format ["CHACAL|E|budget|%1|etape|EXFIL|vers|%2|distance|%3|plafond|%4", round (time * 100) / 100,
    (if (CHACAL_ABANDON) then {"LZ"} else {"PZ"}),
    round (((CHACAL_FS select { alive _x }) call CHACAL_fnc_centre) distance2D CHACAL_EXFIL_POINT),
    round _plafond]) call CHACAL_LOG;

private _pourquoi = if (CHACAL_ABANDON) then {"ABANDON_REPLI_PAR_LA_LZ"} else {"OBJECTIFS_TRAITES"};
// ! Un detachement qui n est PAS compromis ne rompt pas le contact, il s en va.
// En COMBAT sur 1,4 a 2,4 km, 1,8 m/s de moyenne n est pas garanti meme sans
// ennemi : l issue serait EXFIL_MANQUEE sur un detachement intact.
// l appui fixe est rendu a ses jambes pour rentrer
// ! ON REND LES JAMBES A TOUT LE MONDE, SANS CONDITION ( 13/09 ).
// L ancienne ligne ne liberait l appui QUE si CHACAL_APPUI_FIXE valait 1. Or le socle le cloue par sa
// regle S3, et toutes les campagnes tournaient avec socle=1 et appui_fixe=0 : l appui n etait JAMAIS
// libere. Mesure dans les traces : les hommes 6 et 7 parcourent ZERO metre pendant la phase 6 dans 11
// episodes sur 12, pendant que les autres marchent 1000 a 2400 m. Deux hommes sur dix ne pouvaient pas
// rejoindre le point de ramassage, alors que le critere en exige six sur dix.
// On s exfiltre, on ne tient pas : a la phase 6, plus personne n est cloue.
{
    if (!isNull _x) then {
        _x setVariable ["lambs_danger_disableGroupAI", false, true];
        { if (alive _x) then {
            _x enableAI "PATH"; _x enableAI "MOVE";
            _x setVariable ["lambs_danger_disableAI", false, true];
            _x forceSpeed -1;
        } } forEach (units _x);
    };
} forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];
// ! LA GARDE QUI MANQUAIT. Aucune porte du lecteur ne verifiait qu un homme VIVANT peut marcher, et
// c est pourquoi ce defaut a traverse quinze portes vertes et trois campagnes. On compte, et on ecrit.
CHACAL_SANS_JAMBES = 0;
{ if (alive _x && { !(_x checkAIFeature "PATH") }) then { CHACAL_SANS_JAMBES = CHACAL_SANS_JAMBES + 1 } } forEach CHACAL_FS;
(format ["CHACAL|E|exfil_jambes|%1|vivants|%2|sans_path|%3|seuil_exige|%4", round (time * 100) / 100,
    count (CHACAL_FS select { alive _x }), CHACAL_SANS_JAMBES, round (0.6 * CHACAL_EFFECTIF)]) call CHACAL_LOG;
if (CHACAL_SANS_JAMBES > 0) then {
    (format ["CHACAL|AVERT|exfil|hommes_vivants_sans_jambes|%1", CHACAL_SANS_JAMBES]) call CHACAL_LOG;
};
private _compExf = if (CHACAL_COMPROMIS) then {"COMBAT"} else {"AWARE"};
if (CHACAL_EXFIL in [0, 1]) then {
    (format ["CHACAL|E|choix_joue|%1|point|EXFIL_ALLURE|choix|%2|detail|%3|comportement_initial|%4", round (time * 100) / 100,
        CHACAL_EXFIL, (if (CHACAL_EXFIL == 1) then {"RAPIDE"} else {"PRUDENT"}), _compExf]) call CHACAL_LOG;
};
// ! EXFIL=1 : on rompt le contact en COMBAT, puis on rend les jambes. La recolte du moteur du
// 13/09 dit que le chemin se calcule en fonction du comportement ; un homme en COMBAT ne prend
// pas le meme itineraire. Des que le detachement est a plus de 300 m du site, il repasse en
// AWARE. Le plafond ne bouge pas : c est le comportement qu on mesure, pas le chronometre.
if (CHACAL_EXFIL == 1) then {
    [] spawn {
        private _t0 = time;
        waitUntil { sleep 5;
            private _v = CHACAL_FS select { alive _x };
            (count _v == 0) || CHACAL_FIN || ((time - _t0) > 180) ||
            ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE > 200) };
        if (CHACAL_FIN) exitWith {};
        private _v = CHACAL_FS select { alive _x };
        if (count _v == 0) exitWith {};
        { if (!isNull _x) then { _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
            { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x) } }
          forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];
        (format ["CHACAL|E|exfil_degage|%1|distance_site|%2|vivants|%3|comportement|AWARE",
            round (time * 100) / 100, round ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE),
            count _v]) call CHACAL_LOG;
    };
};
{
    if (!isNull _x) then {
        _x setBehaviour _compExf; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
        { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x);
        [_x, CHACAL_EXFIL_POINT, "FULL", _compExf, "WEDGE", _pourquoi] call CHACAL_fnc_ordreAller;
    };
} forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];

private _tE = time;
private _seuilExf = round (0.6 * CHACAL_EFFECTIF);
// ! LE CRITERE PORTE SUR L EFFECTIF, PAS SUR LES SURVIVANTS ( 13/09 ). S il reste moins d hommes
// vivants que le seuil, la condition de sortie ne peut JAMAIS etre vraie : la phase brulait son
// plafond entier, une vingtaine de minutes, pour conclure PLAFOND. C est un critere hors d atteinte,
// la meme famille que arret=5 et le seuil 3 de la phase 3. On sort tout de suite, et on le DIT.
waitUntil { sleep 3;
    (count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } }) >= _seuilExf) ||
    (count (CHACAL_FS select { alive _x }) < _seuilExf) || (time - _tE > _plafond) || CHACAL_FIN };
private _vivExf = count (CHACAL_FS select { alive _x });
if (_vivExf < _seuilExf) then {
    (format ["CHACAL|E|exfil_impossible|%1|vivants|%2|seuil|%3|temps_ecoule|%4", round (time * 100) / 100,
        _vivExf, _seuilExf, round (time - _tE)]) call CHACAL_LOG;
};
CHACAL_EXFILTRES = count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } });
[6, "EXFILTRATION", (if (CHACAL_EXFILTRES >= _seuilExf) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if (count (CHACAL_FS select { alive _x }) < _seuilExf) then {"PERTES_EXCESSIVES"} else {"PLAFOND"} } })] call CHACAL_fnc_finPhase;

CHACAL_FIN = true;
};
