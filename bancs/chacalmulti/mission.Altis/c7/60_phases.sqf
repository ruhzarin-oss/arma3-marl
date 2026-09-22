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

MC7_SAUT = false;
MC7_ABANDON = false;
MC7_CAUSE_ABANDON = "";
MC7_INTEL = false;
MC7_CHARGES = [];              // ACTES : objectifs sur lesquels une charge a ete posee
MC7_DETRUITS = [];             // EFFET SCRIPTE : hors jugement tactique
MC7_VUES = [];                 // [unite, k] reellement observees par la reco
MC7_INSERTION_FORCEE = false;
MC7_QRF_PARTIE = false;
MC7_OUV_CHOISIE = [];
// ! Fable, 06/09 : la mise a feu devient une CONDITION ( personne a moins de
// 35 m ) et non une horloge, et les trois charges sautent ENSEMBLE - c est ce
// qu un detachement fait, et ca retire trois allers-retours, trois attentes et
// trois occasions de fratricide. Le succes compte des ACTES, donc l instant de
// la destruction n entre pas dans le verdict.
MC7_CHARGES_OBJ = [];          // [objectif, charge] : ce qui reste a faire sauter
MC7_RESERVE_FEU = 180;         // s gardees en fin de phase : un degagement, une mise a feu
MC7_SECURITE_FEU = 35;         // m : personne a moins de ca d une charge quand elle part
MC7_EXPLOITANT = objNull;
// ! MARQUEUR-SEUIL-RENS-DERIVE - SEUIL DERIVE DE LA MESURE, PAS CHOISI ( 15/09 ).
// Distribution de count MC7_VUES en fin de phase 3, sur les 148 episodes des journaux qui
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
// ! CE CORRECTIF NE FAIT PAS JOUER LA PHASE 3. Elle ne tourne que si MC7_DEPART < 4 et
// MC7_OBS = 1 ; c est un reglage de job, pas de code.
MC7_SEUIL_RENS = 1;            // sous ce compte, la crete n a rien vu
MC7_T_ALARME = -1; MC7_T_COMPROMIS = -1;
MC7_EXFIL_POINT = [];
MC7_GEL = false;

MC7_fnc_debutPhase = {
    params ["_n", "_nom", ["_plafond", 1e9]];
    // ! VIGNETTE : une phase posterieure a MC7_ARRET n ouvre rien et n ecrit
    // rien. Sinon le RPT porterait des phases jamais jouees et `phase_max` mentirait.
    if (MC7_FIN) exitWith {};
    MC7_PHASE = _n; MC7_PHASE_NOM = _nom;
    MC7_TPHASE = time; MC7_PLAFOND_COURANT = _plafond;
    (format ["CHACAL|PH|%1|%2|debut|%3|vivants|%4|compromis|%5|alarme|%6", _n, _nom, round (time * 100) / 100,
        count (MC7_FS select { alive _x }),
        (if (MC7_COMPROMIS) then {1} else {0}), (if (MC7_ALARME) then {1} else {0})]) call MC7_LOG;
};
// ! LA LIGNE DE DECISION ( plans/plan-choix-par-vignette.md, 16/09 ). Un choix = une ligne, toujours la meme forme,
// lue par la table dbt stg_decision puis par le gymnase. Les observables sont ce que le detachement PEUT savoir au
// moment du choix. verite_defenseurs ne l est pas : il est ecrit pour la lecture, jamais pour decider.
// Ne tire aucun alea : ni le monde ni la situation ne bougent.
"CHACAL|OK|decision|version|3" call MC7_LOG;   // 3 : perceptions de la menace en fin de ligne ( plans/plan-menace-visible.md )
// ! LA MENACE VISIBLE ( 17/09 ). Deux canaux : ce qu un homme du detachement VOIT maintenant ( MC7_fnc_voit, geometrie ) et
// ce que le GROUPE du detachement CONNAIT ( targetKnowledge, champ 0 « known by group », position crue, erreur, derniere vue ).
// Pas knowsAbout : connaissance de camp. La verite ( verite_* ) est ecrite a part, pour la lecture seulement.
MC7_fnc_unitesMenace = {
    private _t = [];
    { private _g = _x select 2; if (!isNull _g) then { _t append ((units _g) select { alive _x }) } } forEach MC7_MENACES;
    _t
};
MC7_fnc_chefsDetachement = {
    private _g = [];
    { if (alive _x) then { _g pushBackUnique (group _x) } } forEach MC7_FS;
    (_g select { !isNull _x && { alive (leader _x) } }) apply { leader _x }
};
MC7_fnc_suiviMenaces = {
    while { !MC7_FIN } do {
        private _chefs = call MC7_fnc_chefsDetachement;
        private _hommesS = MC7_FS select { alive _x };
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
            if (({ [_x, _t, 800, 70] call MC7_fnc_voit } count _hommesS) > 0) then {
                private _hv = _t getVariable ["chacal_vue", []];
                _hv pushBack [time, getPosATL _t];
                if (count _hv > 6) then { _hv deleteAt 0 };
                _t setVariable ["chacal_vue", _hv];
            };
        } forEach (call MC7_fnc_unitesMenace);
        sleep 5;
    };
};
[] spawn MC7_fnc_suiviMenaces;
MC7_fnc_perceptionMenace = {
    // Quatre canaux, jamais la verite : l oeil ( geometrie ), le GROUPE, le CAMP, l HOMME.
    // menace_percue conjugue les deux premiers : 2 connue du groupe, 1 seulement visible, 0 rien ( decision de Younes, 17/09 ).
    private _menaces = call MC7_fnc_unitesMenace;
    private _hommes = MC7_FS select { alive _x };
    private _chefs = call MC7_fnc_chefsDetachement;
    private _vues = 0; private _connues = 0; private _camp = 0; private _homme = 0;
    private _dMin = -1; private _err = -1; private _vueDepuis = -1; private _mobile = -1; private _proche = objNull;
    {
        private _t = _x;
        private _vu = ({ [_x, _t, 800, 70] call MC7_fnc_voit } count _hommes) > 0;
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
    if ((!isNil "MC7_VEH_ROUTE") && { !isNull MC7_VEH_ROUTE } && { ({ (_x select 1) == "PATROUILLE_ROUTE" } count MC7_MENACES) > 0 }) then {
        if (({ (_x targetKnowledge MC7_VEH_ROUTE) select 0 } count _chefs) > 0) then { _veh = 1 };
    };
    // ! MOBILITE VUE : la menace a-t-elle bouge entre deux regards de l oeil ? -1 si l oeil ne l a pas vue deux fois.
    private _mobileVue = -1;
    private _nVues = 0;
    {
        private _hv = (_x getVariable ["chacal_vue", []]) select { (time - (_x select 0)) <= 40 };
        _nVues = _nVues max (count _hv);
        if (count _hv >= 2) then {
            private _d = ((_hv select 0) select 1) distance2D ((_hv select ((count _hv) - 1)) select 1);
            if (_d > 10) exitWith { _mobileVue = 1 };
            if (_mobileVue < 0) then { _mobileVue = 0 };
        };
    } forEach _menaces;
    // ! LE MOTEUR : un blinde s entend de nuit bien plus loin qu un homme ne se voit, et seul le bras PATROUILLE
    // en a un. Approximation assumee, a valider par le controle : jamais 1 sur un poste a pied.
    private _moteur = 0; private _dMoteur = -1; private _moteurAllume = 0; private _vueVeh = 0;
    {
        private _v = vehicle _x;
        if ((_v != _x) && { isEngineOn _v }) then {
            _moteurAllume = 1;
            { private _d = _x distance2D _v; if ((_dMoteur < 0) || { _d < _dMoteur }) then { _dMoteur = _d } } forEach _hommes;
            if ((_dMoteur >= 0) && { _dMoteur < MC7_PORTEE_SON }) then { _moteur = 1; MC7_MOTEUR_FENETRE = 1 };
            if (({ [_x, _v, 1200, 70] call MC7_fnc_voit } count _hommes) > 0) then { _vueVeh = 1 };
        };
    } forEach _menaces;
    private _vDist = -1;
    { private _t = _x; { private _dd = _x distance2D _t; if ((_vDist < 0) || { _dd < _vDist }) then { _vDist = _dd } } forEach _hommes } forEach _menaces;
    format ["|menace_percue|%1|menaces_vues|%2|menaces_connues|%3|menaces_camp|%4|menaces_homme|%5|distance_menace|%6|erreur_position|%7|menace_mobile|%8|vue_depuis|%9|vehicule_connu|%10|menace_mobile_vue|%11|moteur_entendu|%12|distance_moteur|%13|moteur_allume|%14|vue_vehicule|%15|n_vues_menace|%16|moteur_depuis_fenetre|%17|verite_menaces|%18|verite_distance_menace|%19|azimut_chef|%20",
        _percue, _vues, _connues, _camp, _homme, round _dMin, (round (_err * 10)) / 10, _mobile, _vueDepuis, _veh,
        _mobileVue, _moteur, round _dMoteur, _moteurAllume, _vueVeh, _nVues,
        (missionNamespace getVariable ["MC7_MOTEUR_FENETRE", 0]),
        count _menaces, round _vDist, (if (count _chefs > 0) then { round (getDir (_chefs select 0)) } else { -1 })]
};
MC7_fnc_secteurPhase = {
    params ["_phase"];
    switch (_phase) do {
        case 1: { if (isNil "MC7_LZ") then { [] } else { MC7_LZ } };
        case 2: { if (isNil "MC7_ROUTE") then { [] } else { MC7_ROUTE } };
        case 4: { if (isNil "MC7_SITE") then { [] } else { MC7_SITE } };
        default { [] };
    };
};
MC7_fnc_fenetreObservation = {
    params ["_phase"];
    if (MC7_OBSERVATION <= 0) exitWith {};
    private _t0 = time;
    private _hommes = MC7_FS select { alive _x };
    private _secteur = [_phase] call MC7_fnc_secteurPhase;
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
    if ((MC7_CONTROLE_PERCEPTION in [1, 5]) && { count _hommes > 0 }) then {
        // ! BANC DE PERCEPTION ( 18/09 ) : la cible est posee LA OU ILS PEUVENT LA VOIR, et ils la regardent.
        private _chef = leader (group (_hommes select 0));
        private _oeil = (getPosASL _chef) vectorAdd [0, 0, 1.5];
        private _az = getDir _chef; private _trouve = false;
        {
            private _p = _chef getPos [MC7_CONTROLE_DIST, _x];
            private _cible = (ATLToASL _p) vectorAdd [0, 0, 1.6];
            if (!_trouve && { (count (lineIntersectsSurfaces [_oeil, _cible, _chef, objNull, true, 1, "VIEW", "VIEW"])) == 0 }) then { _az = _x; _trouve = true };
        } forEach [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340];
        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE ( mesure du 18/09 : 4 episodes sur 22 posaient la cible derriere un obstacle ) :
            // on refuse l episode plutot que de mesurer le relief au lieu de la perception.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE", round (time * 100) / 100,
                _phase, MC7_CONTROLE_DIST]) call MC7_LOG;
        };
        private _p = _chef getPos [MC7_CONTROLE_DIST, _az];
        private _g = ([east, 7] call MULTI_fnc_groupe);
        { private _u = _g createUnit [_x, _p, [], 3, "NONE"]; _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE"; _u setUnitPos "UP" } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE"; _g setBehaviour "SAFE";
        MC7_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
        if (MC7_CONTROLE_PERCEPTION == 5) then {
            private _cibleU = leader _g;
            { _x doWatch _cibleU } forEach _hommes;   // banc : ils fixent la cible, aucune ambiguite de direction
            _regards = [];                            // le banc ne balaie pas
        } else {
            _regards = [getPosATL (leader _g)];       // controle POSITIF : la cible est dans le secteur balaye
        };
        (format ["CHACAL|E|banc_perception|%1|phase|%2|distance|%3|azimut|%4|ligne_de_vue|%5|heure|%6|lune|%7|jumelles|%8|hommes|%9",
            round (time * 100) / 100, _phase, MC7_CONTROLE_DIST, round _az, (if (_trouve) then {1} else {0}),
            (date select 3) + ((date select 4) / 60), moonIntensity,
            ((_hommes apply { hmd _x }) joinString ","), count _hommes]) call MC7_LOG;
    };
    if ((MC7_CONTROLE_PERCEPTION in [2, 3]) && { count _hommes > 0 }) then {
        private _chef = leader (group (_hommes select 0));
        private _p = if (MC7_CONTROLE_PERCEPTION == 2) then { _chef getPos [1500, (getDir _chef) + 180] } else { _chef getPos [150, getDir _chef] };
        private _g = ([east, 7] call MULTI_fnc_groupe);
        {
            private _u = _g createUnit [_x, _p, [], 5, "NONE"];
            _u disableAI "AUTOTARGET"; _u disableAI "TARGET"; _u disableAI "MOVE";
            _u setUnitPos (if (MC7_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"});
        } forEach ["O_Soldier_TL_F", "O_Soldier_F", "O_Soldier_F"];
        _g setCombatMode "BLUE";
        MC7_MENACES pushBack [_phase, "CONTROLE_PERCEPTION", _g];
        (format ["CHACAL|E|controle_perception|%1|phase|%2|mode|%3|distance|%4|posture|%5", round (time * 100) / 100, _phase,
            MC7_CONTROLE_PERCEPTION, round (_chef distance2D _p), (if (MC7_CONTROLE_PERCEPTION == 3) then {"UP"} else {"MIDDLE"})]) call MC7_LOG;
    };
    (format ["CHACAL|E|observation|%1|phase|%2|debut|duree_prevue|%3%4", round (time * 100) / 100, _phase, MC7_OBSERVATION,
        call MC7_fnc_perceptionMenace]) call MC7_LOG;
    MC7_MOTEUR_FENETRE = 0;   // la memoire du son commence avec la fenetre
    if (MC7_SONDE_PERCEPTION == 1) then {
        [_phase] spawn {
            params ["_ph"];
            private _t0 = time;
            while { !MC7_FIN && { (time - _t0) < (600 * MC7_ECHELLE) } } do {
                (format ["CHACAL|E|sonde_decision|%1|phase|%2|depuis|%3%4", round (time * 100) / 100, _ph,
                    round (time - _t0), call MC7_fnc_perceptionMenace]) call MC7_LOG;
                sleep (10 * MC7_ECHELLE);
            };
        };
    };
    (format ["CHACAL|E|reglage_observation|%1|phase|%2|avant|%3|balayage|%4|distance_secteur|%5|azimuts|%6", round (time * 100) / 100, _phase,
        MC7_AVANT, MC7_BALAYAGE, (if (count _secteur > 0) then { round (((_hommes select 0) distance2D _secteur)) } else { -1 }), count _regards]) call MC7_LOG;
    private _prochain = time; private _tRegard = 0; private _iRegard = -1;
    waitUntil {
        sleep 1;
        if ((count _regards > 0) && { time >= _tRegard }) then {
            _tRegard = time + 10; _iRegard = (_iRegard + 1) % (count _regards);
            // ! levier MC7_BALAYAGE : 1 = chaque changement d azimut TOURNE les hommes ( setDir ) avant le doWatch ; 0 = origine
            {
                if (MC7_BALAYAGE == 1) then { _x setDir (_x getDir (_regards select _iRegard)) };
                _x doWatch (_regards select _iRegard);
            } forEach (MC7_FS select { alive _x });
        };
        if ((MC7_SONDE > 0) && { time >= _prochain }) then {
            _prochain = time + 5;
            private _angles = [];
            {
                private _t = _x;
                private _a = 999;
                { private _r = abs ((((_x getDir _t) - (getDir _x) + 540) % 360) - 180); if (_r < _a) then { _a = _r } } forEach (MC7_FS select { alive _x });
                _angles pushBack (round _a);
            } forEach (call MC7_fnc_unitesMenace);
            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3|angle_min|%4%5", round (time * 100) / 100, _phase,
                round (time - _t0), (if (count _angles > 0) then { selectMin _angles } else { -1 }),
                call MC7_fnc_perceptionMenace]) call MC7_LOG;
        };
        MC7_FIN || ((time - _t0) >= (MC7_OBSERVATION * MC7_ECHELLE))
    };
    // ! RENDRE LA MAIN ( faute du 17/09 : sans ceci, les trois elements de la phase 4 ne repartent jamais et les huit
    // episodes finissent au plafond, 55 min au lieu de 5 ).
    {
        if (alive _x) then { _x doWatch objNull; _x setUnitPos "AUTO"; _x doFollow (leader (group _x)) };
    } forEach _hommes;
    (format ["CHACAL|E|observation|%1|phase|%2|fin|duree|%3%4", round (time * 100) / 100, _phase, round (time - _t0),
        call MC7_fnc_perceptionMenace]) call MC7_LOG;
};
MC7_fnc_decision = {
    params ["_phase", "_point", "_options", "_choix", "_decideur", ["_extra", ""]];
    private _def = (if (isNil "MC7_EST_SITE") then {[]} else {MC7_EST_SITE}) select { alive _x };
    (format ["CHACAL|E|decision|%1|phase|%2|point|%3|options|%4|choix|%5|decideur|%6|alarme|%7|depuis_alarme|%8|compromis|%9|vivants|%10|defenseurs_connus|%11|verite_defenseurs|%12|situation|%13%14",
        round (time * 100) / 100, _phase, _point, _options, _choix, _decideur,
        (if (MC7_ALARME) then {1} else {0}),
        (if (MC7_T_ALARME >= 0) then { round (time - MC7_T_ALARME) } else { -1 }),
        (if (MC7_COMPROMIS) then {1} else {0}),
        count (MC7_FS select { alive _x }),
        { (west knowsAbout _x) > 1.4 } count _def,
        count _def, MC7_SITUATION, _extra + (call MC7_fnc_perceptionMenace)]) call MC7_LOG;
};
// Interprete des formules EvoGP ( codes prefixes ). ">" vaut +1 si a > b, sinon -1, comme dans EvoGP ( mesure le 17/09 ).
MC7_F_CONST = [-1, -0.5, -0.25, 0, 0.25, 0.5, 1];
MC7_fnc_evalNoeud = {
    params ["_i", "_obs"];
    private _c = MC7_F select _i;
    if (_c >= 301) exitWith { [MC7_F_CONST select (_c - 301), _i + 1] };
    if (_c >= 201) exitWith { [_obs select (_c - 201), _i + 1] };
    if (_c == 106) exitWith { private _m = [_i + 1, _obs] call MC7_fnc_evalNoeud; [-(_m select 0), _m select 1] };
    private _g = [_i + 1, _obs] call MC7_fnc_evalNoeud;
    private _d = [_g select 1, _obs] call MC7_fnc_evalNoeud;
    private _u = _g select 0; private _v = _d select 0;
    private _r = switch (_c) do {
        case 101: { _u + _v };
        case 102: { _u - _v };
        case 103: { _u * _v };
        case 104: { _u min _v };
        case 105: { _u max _v };
        case 107: { if (_u > _v) then {1} else {-1} };
        default { (format ["CHACAL|ERREUR|formule|code_inconnu|%1", _c]) call MC7_LOG; 0 };
    };
    [_r, _d select 1]
};
MC7_fnc_finPhase = {
    params ["_n", "_nom", "_issue"];
    if (MC7_FIN && { _n > MC7_ARRET }) exitWith {};
    (format ["CHACAL|PH|%1|%2|fin|%3|%4|vivants|%5|compromis|%6|alarme|%7", _n, _nom, round (time * 100) / 100, _issue,
        count (MC7_FS select { alive _x }),
        (if (MC7_COMPROMIS) then {1} else {0}), (if (MC7_ALARME) then {1} else {0})]) call MC7_LOG;
    // ! LA VIGNETTE SE FERME ICI, et par le VERDICT : 70_verdict attend MC7_FIN,
    // emet sa ligne FINI, et le lanceur arrete le serveur dessus. On ne coupe pas
    // au plafond - un episode coupe au plafond n a pas d issue lisible.
    if (_n >= MC7_ARRET) then {
        (format ["CHACAL|OK|vignette|arret|%1|issue|%2", _n, _issue]) call MC7_LOG;
        MC7_FIN = true;
    };
};

MC7_fnc_ordreAller = {
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
    // On libere la posture ET le regard : `doWatch MC7_SITE` pose sur l appui
    // et la reco n etait jamais leve - une main qui tire sur la tete pendant 2 km.
    { if (alive _x) then { _x setUnitPos "AUTO"; _x doWatch objNull } } forEach (units _g);
    while { count (waypoints _g) > 0 } do { deleteWaypoint ((waypoints _g) select 0) };
    _g setBehaviour _comp; _g setSpeedMode _vit; _g setFormation _form;
    private _w = _g addWaypoint [_p, 0];
    _w setWaypointType "MOVE"; _w setWaypointSpeed _vit; _w setWaypointBehaviour _comp; _w setWaypointFormation _form;
    (format ["CHACAL|E|ordre|%1|%2|%3|%4|pourquoi|%5", round (time * 100) / 100,
        (_g getVariable ["chacal_element", "DETACHEMENT"]), _p, MC7_PHASE, _pourquoi]) call MC7_LOG;
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
MC7_fnc_arrive = {
    params ["_g", "_p", "_ray", "_plafond", ["_stagn", 300]];
    if (isNull _g) exitWith { "ABSENT" };
    private _reste = call MC7_fnc_reste;
    if (_reste < _plafond) then { _plafond = _reste };
    if (_plafond <= 0) exitWith { "PLAFOND_PHASE" };
    if (MC7_SAUT) exitWith { "COMPROMIS" };
    private _t0 = time;
    private _dRef = 1e9; private _tRef = time;
    private _enlise = false; private _fini = false; private _mort = false;
    while { !_fini && (time - _t0 < _plafond) && !MC7_FIN && !MC7_SAUT } do {
        private _v = (units _g) select { alive _x };
        if (count _v == 0) then { _fini = true; _mort = true }
        else {
            private _c = _v call MC7_fnc_centre;
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
    private _c2 = _v2 call MC7_fnc_centre;
    if (count _c2 > 0 && { (_c2 distance2D _p) < _ray }) exitWith { "ATTEINT" };
    if (_enlise) exitWith { "ENLISE" };
    if (MC7_SAUT) exitWith { "COMPROMIS" };
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
MC7_fnc_rejoindre = {
    params ["_g", "_p", "_ray", "_plafond", "_nom"];
    if (isNull _g) exitWith { "ABSENT" };
    [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_JAMBE_RAPIDE"] call MC7_fnc_ordreAller;
    private _t0 = time; private _tLog = time; private _tRef = time;
    private _dRef = 1e9; private _lente = false;
    private _fini = false; private _res = ""; private _immobile = 0;
    private _releve = false; private _dReleve = 1e9;
    while { !_fini && (time - _t0 < _plafond) && !MC7_FIN && !MC7_SAUT } do {
        private _v = (units _g) select { alive _x };
        if (count _v == 0) then { _fini = true; _res = "DETRUIT" }
        else {
            private _c = _v call MC7_fnc_centre;
            if (count _c > 0) then {
                private _d = _c distance2D _p;
                if (time - _tLog >= 30) then {
                    _tLog = time;
                    private _vit = 0;
                    { _vit = _vit + (speed _x) } forEach _v;
                    (format ["CHACAL|E|progression|%1|%2|reste|%3|vitesse|%4|jambe|%5|hommes|%6",
                        round (time * 100) / 100, _nom, round _d,
                        round ((_vit / (count _v)) * 10) / 10,
                        (if (_lente) then {"DISCRETE"} else {"RAPIDE"}), count _v]) call MC7_LOG;
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
                        (format ["CHACAL|E|deblocage|%1|%2|essai|RELEVER|reste|%3", round (time * 100) / 100, _nom, round _d]) call MC7_LOG;
                        [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_DEBLOCAGE_RELEVER"] call MC7_fnc_ordreAller;
                        // ! Le premier jet posait `_lente = true` et INTERDISAIT le retour
                        // en jambe discrete : les 170 derniers metres se couraient debout
                        // a 230 m d une garnison. Invisible dans le monde vide, mais dans
                        // le corpus la jambe discrete ne voudrait plus rien dire.
                        _lente = true; _releve = true; _dReleve = _d;
                    };
                    if (_immobile == 20) then {
                        private _neuf = [_p getPos [70, 60 + (240 call MC7_fnc_al)], 50] call MC7_fnc_plat;
                        (format ["CHACAL|E|deblocage|%1|%2|essai|CONTOURNER|vers|%3", round (time * 100) / 100, _nom, _neuf]) call MC7_LOG;
                        _p = _neuf;
                        [_g, _p, "NORMAL", "AWARE", "WEDGE", _nom + "_DEBLOCAGE_CONTOURNER"] call MC7_fnc_ordreAller;
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
                            round (atan (((getTerrainHeightASL ((getPosATL _l) getPos [10, (getPosATL _l) getDir _p])) - (getTerrainHeightASL (getPosATL _l))) / 10))]) call MC7_LOG;
                    };
                } else { _immobile = 0 };
                // ! MESURE, PAS COMPORTEMENT ( 09/09 ). Le moteur peut declarer un deplacement
                // TERMINE loin de la cible : commande vide, unitReady vrai, point de passage
                // consomme. C est la signature exacte du palier 4, ou l assaut est reste a
                // 800 m pendant 2000 s. On la journalise pour savoir si MC7_ACCESSIBLE la
                // fait disparaitre — sans elle, on ne pourrait pas dire si le remede a mordu.
                private _l2 = leader _g;
                if (unitReady _l2 && { (currentCommand _l2) == "" } && { (currentWaypoint _g) >= (count (waypoints _g)) } && { _d > _ray }) then {
                    if (_immobile == 5) then {
                        (format ["CHACAL|E|moteur_dit_fini|%1|%2|reste|%3|rayon|%4|pente_trajet|%5",
                            round (time * 100) / 100, _nom, round _d, _ray,
                            round ([getPosATL _l2, _p] call MC7_fnc_penteTrajet)]) call MC7_LOG;
                    };
                };
                if (_d < _ray) then { _fini = true; _res = "ATTEINT" }
                else {
                    if (!_lente && { _d < 300 }) then {
                        _lente = true;
                        [_g, _p, "LIMITED", "STEALTH", "WEDGE", _nom + "_JAMBE_DISCRETE"] call MC7_fnc_ordreAller;
                    };
                    // une fois degage de quarante metres, on se recouche
                    if (_releve && { _d < _dReleve - 40 } && { _d < 300 }) then {
                        _releve = false;
                        [_g, _p, "LIMITED", "STEALTH", "WEDGE", _nom + "_RETOUR_JAMBE_DISCRETE"] call MC7_fnc_ordreAller;
                    };
                    if (_d < _dRef - 25) then { _dRef = _d; _tRef = time };
                    if (time - _tRef > 300) then { _fini = true; _res = "ENLISE" };
                };
            };
        };
        if (!_fini) then { sleep 3 };
    };
    if (_res == "") then { _res = if (MC7_SAUT) then {"COMPROMIS"} else {"PLAFOND"} };
    _res
};

// ! LE CHOIX DE LA PHASE 4 ( plans/plan-choix-par-vignette.md, 17/09 ) : itineraire direct ou detour. A ITINERAIRE = 2,
// chaque element passe d abord par un point decale de 350 m a droite de son axe, a mi-chemin, puis rejoint sa
// position comme avant. Sans tirage : le point est geometrique ; s il tombe dans l eau, on prend la gauche et on le dit.
MC7_fnc_rejoindreItineraire = {
    params ["_g", "_p", "_ray", "_plafond", "_nom"];
    if (isNull _g) exitWith { "ABSENT" };
    if (MC7_ITINERAIRE == 2) then {
        private _v = (units _g) select { alive _x };
        if (count _v > 0) then {
            private _c = _v call MC7_fnc_centre;
            private _dir = _c getDir _p;
            private _mi = _c getPos [(_c distance2D _p) / 2, _dir];
            private _cote = 90;
            private _wp = _mi getPos [350, _dir + _cote];
            if (surfaceIsWater _wp) then { _cote = -90; _wp = _mi getPos [350, _dir + _cote] };
            _wp set [2, 0];
            private _t0 = time;
            [_g, _wp, "NORMAL", "AWARE", "WEDGE", _nom + "_DETOUR"] call MC7_fnc_ordreAller;
            private _rD = [_g, _wp, 80, ([_g, _wp] call MC7_fnc_budgetDeuxJambes)] call MC7_fnc_arrive;
            (format ["CHACAL|E|choix_joue|%1|point|ITINERAIRE|choix|2|detail|DETOUR|element|%2|cote|%3|point_detour|%4|issue|%5|duree|%6",
                round (time * 100) / 100, _nom, _cote, _wp, _rD, round (time - _t0)]) call MC7_LOG;
            _plafond = _plafond - (time - _t0);
        };
    } else {
        if (MC7_ITINERAIRE == 1) then {
            (format ["CHACAL|E|choix_joue|%1|point|ITINERAIRE|choix|1|detail|DIRECT|element|%2", round (time * 100) / 100, _nom]) call MC7_LOG;
        };
    };
    [_g, _p, _ray, (_plafond max 60), _nom] call MC7_fnc_rejoindre
};

// Le budget d une position rejointe en deux jambes : la jambe rapide a 1,1 m/s,
// les 300 derniers metres a 0,5 m/s, plus une marge d articulation.
MC7_fnc_budgetDeuxJambes = {
    params ["_g", "_p"];
    private _u = if (_g isEqualType grpNull) then { units _g } else { _g };
    _u = _u select { alive _x };
    if (count _u == 0) exitWith { 300 };
    private _c = _u call MC7_fnc_centre;
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
MC7_fnc_emprise = {
    private _bb = boundingBoxReal _this;
    private _ex = ((_bb select 1) select 0) - ((_bb select 0) select 0);
    private _ey = ((_bb select 1) select 1) - ((_bb select 0) select 1);
    (_ex max _ey) / 2
};
MC7_fnc_pointDePose = {
    params ["_o"];
    private _pO = getPosATL _o; _pO set [2, 0];
    private _r = (_o call MC7_fnc_emprise) + 4;
    private _az0 = if (_o isEqualTo MC7_PC) then { _pO getDir MC7_OUV_CHOISIE } else { _pO getDir MC7_SITE };
    private _best = _pO getPos [_r, _az0]; private _sc = -1;
    {
        private _p = _pO getPos [_r, _az0 + _x]; _p set [2, 0];
        if ((_p distance2D MC7_SITE) < (MC7_RAYON - 5)) then {
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
MC7_fnc_exploiter = {
    private _l = leader MC7_gAssaut;
    private _cand = (units MC7_gAssaut) select { alive _x && { _x != _l } };
    private _pref = _cand select { (_x getVariable ["chacal_role", ""]) in ["ADJOINT", "MEDECIN"] };
    if (count _pref > 0) then { _cand = _pref };
    if (count _cand == 0) exitWith {};
    MC7_EXPLOITANT = _cand select 0;
    private _h = MC7_EXPLOITANT;
    (format ["CHACAL|E|ordre|%1|EXPLOITATION|%2|%3|pourquoi|OPORD_TERMINAL|par|%4", round (time * 100) / 100,
        getPosATL MC7_PORTABLE, MC7_PHASE, (_h getVariable ["chacal_role", ""])]) call MC7_LOG;
    _h doMove (getPosATL MC7_PORTABLE);
    private _t = time; private _dedans = 0; private _tOrdre = time;
    while { !MC7_INTEL && { alive _h } && (time - _t < 100 * MC7_ECHELLE) && !MC7_FIN } do {
        if ((_h distance2D MC7_PORTABLE) < 4) then { _dedans = _dedans + 2 } else {
            _dedans = 0;
            if (time - _tOrdre > 20) then { _h doMove (getPosATL MC7_PORTABLE); _tOrdre = time };
        };
        if (_dedans >= (60 * MC7_ECHELLE)) then {
            MC7_INTEL = true;
            (format ["CHACAL|E|exploitation|%1|reussie|par|%2", round (time * 100) / 100, (_h getVariable ["chacal_role", ""])]) call MC7_LOG;
        };
        sleep 2;
    };
    if (!MC7_INTEL) then {
        (format ["CHACAL|E|exploitation|%1|manquee|distance|%2", round (time * 100) / 100, round (_h distance2D MC7_PORTABLE)]) call MC7_LOG;
    };
    if (alive _h) then { _h doFollow (leader MC7_gAssaut) };
};

// ! LA MISE A FEU EST UNE CONDITION, PAS UNE HORLOGE. On ne fait pas sauter ses
// propres hommes : si quelqu un est encore a moins de 35 m d une charge apres
// 90 s, l acte reste COMPTE et l effet est REFUSE, et dit.
MC7_fnc_miseAFeu = {
    params [["_degagement", "-"]];
    if (count MC7_CHARGES_OBJ == 0) exitWith {
        (format ["CHACAL|E|mise_a_feu|%1|aucune_charge|degagement|%2", round (time * 100) / 100, _degagement]) call MC7_LOG;
    };
    private _fnProches = {
        private _n = 0;
        {
            private _c = _x select 1;
            if (!isNull _c) then { _n = _n + ({ alive _x && { (_x distance2D _c) < MC7_SECURITE_FEU } } count MC7_FS) };
        } forEach MC7_CHARGES_OBJ;
        _n
    };
    private _t = time; private _proches = call _fnProches;
    while { _proches > 0 && (time - _t < 90 * MC7_ECHELLE) && !MC7_FIN } do { sleep 3; _proches = call _fnProches };
    if (_proches > 0) exitWith {
        (format ["CHACAL|E|mise_a_feu|%1|REFUSEE|hommes_a_portee|%2|attente|%3|degagement|%4", round (time * 100) / 100,
            _proches, round (time - _t), _degagement]) call MC7_LOG;
    };
    (format ["CHACAL|E|mise_a_feu|%1|charges|%2|attente|%3|degagement|%4", round (time * 100) / 100,
        count MC7_CHARGES_OBJ, round (time - _t), _degagement]) call MC7_LOG;
    { private _c = _x select 1; if (!isNull _c) then { _c setDamage 1 } } forEach MC7_CHARGES_OBJ;
    sleep 2;
    {
        private _o = _x select 0;
        if (alive _o) then { _o setDamage 1 };
        MC7_DETRUITS pushBackUnique _o;
        (format ["CHACAL|E|destruction|%1|%2|effet_scripte|total|%3", round (time * 100) / 100, typeOf _o, count MC7_DETRUITS]) call MC7_LOG;
    } forEach MC7_CHARGES_OBJ;
};

MC7_fnc_enPlace = {
    params ["_g", "_p", "_ray"];
    if (isNull _g) exitWith { false };
    private _v = (units _g) select { alive _x };
    if (count _v == 0) exitWith { false };
    private _c = _v call MC7_fnc_centre;
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
MC7_fnc_compromettre = {
    params ["_cause"];
    if (MC7_COMPROMIS) exitWith {};
    MC7_COMPROMIS = true; MC7_T_COMPROMIS = time;
    (format ["CHACAL|E|compromis|%1|cause|%2|phase|%3|latence_oracle|%4", round (time * 100) / 100,
        _cause, MC7_PHASE,
        (if (MC7_T_ALARME < 0) then {-1} else { round ((time - MC7_T_ALARME) * 100) / 100 })]) call MC7_LOG;
    if (MC7_PHASE < 5) then { MC7_SAUT = (MC7_TENIR == 0) };

    // ! LE REFLEXE DE RUPTURE NE VAUT QUE TANT QU ON N ASSAILLE PAS.
    // La premiere fois que la mission a atteint la phase 5, la compromission
    // est tombee - ce qui est NORMAL, on assaille - et ce reflexe a envoye
    // l element d assaut a 800 m de l objectif. J avais corrige " la file
    // marche sous plan apres la mort des chefs " en fabriquant " l assaut rompt
    // le contact au moment d assaillir ".
    private _bl = if (MC7_PHASE < 5) then { MC7_FS select { alive _x } } else { [] };
    if (count _bl > 0) then {
        private _c = _bl call MC7_fnc_centre;
        private _menace = [];
        {
            private _e = _x;
            if ({ [_x, _e, 900] call MC7_fnc_voit } count _bl > 0) exitWith { _menace = getPosATL _e };
        } forEach ((allUnits + vehicles) select {
            alive _x && { side (if (_x isKindOf "CAManBase") then {_x} else {effectiveCommander _x}) == east } });
        private _az = if (count _menace > 0) then { _menace getDir _c } else { MC7_SITE getDir _c };
        private _fuite = _c getPos [400, _az];
        {
            if (!isNull _x) then {
                _x setBehaviour "COMBAT"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
                [_x, _fuite, "FULL", "COMBAT", "WEDGE", "RUPTURE_CONTACT"] call MC7_fnc_ordreAller;
            };
        } forEach ([MC7_gFS, MC7_gReco, MC7_gAppui, MC7_gAssaut, MC7_gBouchon] select { !isNull _x });
        (format ["CHACAL|E|rupture|%1|vers|%2|menace_percue|%3", round (time * 100) / 100,
            _fuite, (if (count _menace > 0) then {1} else {0})]) call MC7_LOG;
    };
};

// les trois sens du detachement
{
    _x addEventHandler ["FiredNear", {
        params ["_u", "_tireur", "_dist"];
        if (_dist < 45 && { side _tireur != west }) then { ["FEU_PROCHE"] call MC7_fnc_compromettre };
    }];
    _x addEventHandler ["Hit", {
        params ["_u", "_source"];
        if (!isNull _source && { side _source != west }) then { ["COUP_RECU"] call MC7_fnc_compromettre };
    }];
} forEach MC7_FS;

// et le troisieme : un rouge que NOUS voyons, et qui vient de passer en combat
[] spawn {
    while { !MC7_COMPROMIS && !MC7_FIN } do {
        private _bl = MC7_FS select { alive _x };
        if (count _bl > 0) then {
            {
                private _e = _x;
                if ({ [_x, _e, 700] call MC7_fnc_voit } count _bl > 0) exitWith { ["ENNEMI_VU_EN_COMBAT"] call MC7_fnc_compromettre };
            } forEach (MC7_EST_SITE select { alive _x && { behaviour _x == "COMBAT" } });
        };
        sleep 2;
    };
};

// ! LE REFLEXE DE LA FILE. Une file de nuit qui voit un rouge a 400 m ne
// continue pas de marcher : elle se fige et se plaque. Sans ce reflexe, la
// seule reponse du corpus a " un ennemi apparait " est " continuer au meme
// pas ", ce qui n est le comportement de personne.
[] spawn {
    waitUntil { sleep 1; MC7_PHASE >= 2 };
    // ! LE REFLEXE NE VAUT QUE PENDANT L INFILTRATION. En phase 4 le detachement
    // se porte deliberement a 230 m d une garnison : y voir un rouge est ATTENDU,
    // et figer toute la file 30 s a chaque fois interdit d arriver. Meme erreur
    // que le reflexe de rupture applique a l assaut - un bon reflexe hors de son
    // regime devient un blocage.
    while { !MC7_FIN && MC7_PHASE < 4 } do {
        private _bl = MC7_FS select { alive _x };
        if (count _bl > 0) then {
            private _rouges = (allUnits + vehicles) select {
                alive _x && { (_x distance (_bl select 0)) < 500 }
                && { side (if (_x isKindOf "CAManBase") then {_x} else {effectiveCommander _x}) == east } };
            private _vu = false;
            { private _e = _x; if ({ [_x, _e, 500] call MC7_fnc_voit } count _bl > 0) exitWith { _vu = true } } forEach _rouges;
            if (_vu && !MC7_GEL && !MC7_SAUT) then {
                MC7_GEL = true;
                { doStop _x; _x setUnitPos "DOWN" } forEach _bl;
                (format ["CHACAL|E|reflexe|%1|gel|phase|%2", round (time * 100) / 100, MC7_PHASE]) call MC7_LOG;
                private _t = time;
                while { MC7_GEL && !MC7_FIN && !MC7_SAUT } do {
                    sleep 3;
                    private _b2 = MC7_FS select { alive _x };
                    private _encore = false;
                    { private _e = _x; if ({ [_x, _e, 500] call MC7_fnc_voit } count _b2 > 0) exitWith { _encore = true } } forEach _rouges;
                    if (_encore) then { _t = time };
                    if (time - _t > 30) then { MC7_GEL = false };
                };
                { if (alive _x) then { _x setUnitPos "AUTO"; _x doFollow (leader (group _x)) } } forEach (MC7_FS select { alive _x });
                (format ["CHACAL|E|reflexe|%1|degel|phase|%2", round (time * 100) / 100, MC7_PHASE]) call MC7_LOG;
            };
        };
        sleep 3;
    };
};

// L ORACLE : ce que l ennemi sait. Il pilote l ennemi, JAMAIS les bleus, et
// reste journalise pour mesurer la latence de surprise.
[] spawn {
    while { !MC7_ALARME && !MC7_FIN } do {
        private _m = 0;
        { private _k = east knowsAbout _x; if (_k > _m) then { _m = _k } } forEach (MC7_FS select { alive _x });
        if (_m > 1.4) then { MC7_ALARME = true; MC7_T_ALARME = time };
        sleep 1;
    };
    if (MC7_FIN) exitWith {};
    (format ["CHACAL|E|oracle_alarme|%1|phase|%2", round (time * 100) / 100, MC7_PHASE]) call MC7_LOG;
    { if (!isNull _x) then { _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setSpeedMode "FULL" } } forEach MC7_GROUPES_EST;

    // La reserve met du temps a partir, et du temps a arriver : 6 km de route.
    // C est ce delai qui donne un sens au bouchon, donc a la phase 4.
    sleep (MC7_PAL_DELAI + (30 call MC7_fnc_al));
    MC7_QRF_PARTIE = true;
    (format ["CHACAL|E|qrf_partie|%1", round (time * 100) / 100]) call MC7_LOG;
    MC7_gQrf setBehaviour "AWARE"; MC7_gQrf setCombatMode "RED"; MC7_gQrf setSpeedMode "FULL";
    while { count (waypoints MC7_gQrf) > 0 } do { deleteWaypoint ((waypoints MC7_gQrf) select 0) };
    private _w = MC7_gQrf addWaypoint [MC7_SITE, 0];
    _w setWaypointType "SAD"; _w setWaypointSpeed "FULL"; _w setWaypointBehaviour "AWARE";
    // ! SIGNATURE : LAMBS attend [groupe, RAYON, cycle, aire, position]. Passer
    // [groupe, position, rayon] est rejete - Type Array, expected Number - et
    // la reserve ne chassait JAMAIS de tout l episode sans que rien le dise.
    if (MC7_LAMBS) then { [MC7_gQrf, 450, 30, [], MC7_SITE] spawn lambs_wp_fnc_taskHunt };
};

// =====================================================================
[] spawn {
waitUntil { sleep 1; !isNil "MULTI_DEPART" };   // MULTI : l horloge part au depart commun
sleep 3;
if (MC7_ISSUE == "VOID") exitWith { MC7_FIN = true };

// L ORDRE INITIAL. Ce que le detachement sait LEGITIMEMENT avant de partir :
// site, crete candidate, route, base de reserve, depose, point de secours,
// ouvertures. Tout le reste doit venir de ce qu il observe.
MC7_OPORD = [MC7_SITE, MC7_OP, MC7_ROUTE, MC7_QRF_BASE, MC7_LZ, MC7_PZ, MC7_RALLY];
(format ["CHACAL|E|opord|%1|site|%2|crete|%3|route|%4|reserve|%5|depose|%6|secours|%7|rally|%8|ouvertures|%9",
    round (time * 100) / 100, MC7_SITE, MC7_OP, MC7_ROUTE, MC7_QRF_BASE,
    MC7_LZ, MC7_PZ, MC7_RALLY, MC7_OUV_AZ]) call MC7_LOG;

private _plafond = 0; private _issue = ""; private _r = ""; private _t0 = time;

// ! DEUX EPISODES COMPLETS, DEUX COMPROMISSIONS DANS L APPROCHE : les phases 3,
// 4 et 5 n avaient jamais ete jouees et la question qui decide de la mission -
// la crete voit-elle a 800 m de nuit - n avait aucune reponse. `MC7_DEPART`
// pose le detachement au regroupement. C est un DIAGNOSTIC : l episode est
// marque hors corpus, son approche n ayant pas eu lieu.
if (MC7_DEPART >= 3) then {
    (format ["CHACAL|AVERT|hors_corpus|depart|%1|approche_non_jouee", MC7_DEPART]) call MC7_LOG;
    { if (alive _x) then { _x setPosATL (MC7_RALLY getPos [8 + (14 call MC7_fnc_al), 360 call MC7_fnc_al]) } } forEach MC7_FS;
    MC7_gFS setBehaviour "STEALTH"; MC7_gFS setCombatMode "GREEN";
    MC7_gFS setSpeedMode "LIMITED"; MC7_gFS setFormation "FILE";
    (format ["CHACAL|E|depart_direct|%1|au_rally|%2", round (time * 100) / 100, MC7_RALLY]) call MC7_LOG;
    sleep 5;
} else {

// ---------------------------------------------------------------------
// PHASE 1 - INSERTION
// ---------------------------------------------------------------------
// ! DEPART A LA ROUTE ( 16/09 ). La phase 2 se jouait apres ~50 min de marche depuis la zone de poser.
// DEPART = 2 pose le detachement a 330 m de la route et joue la traversee. Les hommes sont poses en
// anneau fixe, SANS tirage : ni l alea du monde ni celui de la situation ne bougent.
if (MC7_DEPART == 2) then {
    "CHACAL|AVERT|hors_corpus|depart|2|insertion_non_jouee" call MC7_LOG;
    private _pt = MC7_ROUTE getPos [MC7_AVANT + 70, MC7_ROUTE getDir MC7_LZ];   // 70 m derriere le point d observation, comme a l origine ( 260 + 70 = 330 )
    private _k = 0;
    { if (alive _x) then { _x setPosATL (_pt getPos [10, _k * 36]); _k = _k + 1 } } forEach MC7_FS;
    MC7_gFS setBehaviour "STEALTH"; MC7_gFS setCombatMode "GREEN";
    MC7_gFS setSpeedMode "LIMITED"; MC7_gFS setFormation "FILE";
    (format ["CHACAL|E|depart_direct|%1|a_la_route|%2", round (time * 100) / 100, _pt]) call MC7_LOG;
    sleep 5;
} else {
_plafond = 1 call MC7_fnc_duree;
// ! GEOMETRIE SEULE : le monde est tire, on le publie, et on s arrete. Aucun coup de feu,
// aucune issue de mission. C est la facon exacte de connaitre un site sans l user.
if (MC7_GEOMETRIE == 1) exitWith {
    (format ["CHACAL|GEO|%1|graine|%2|site|%3|crete|%4|route|%5|lz|%6|qrf|%7|pz|%8|rally|%9|ouvertures|%10|az_site|%11|gain_crete|%12",
        round (time * 100) / 100, MC7_GRAINE, MC7_SITE, MC7_OP, MC7_ROUTE,
        MC7_LZ, MC7_QRF_BASE, MC7_PZ, MC7_RALLY,
        (if (isNil "MC7_OUVERTURES") then {[]} else {MC7_OUVERTURES apply { round (MC7_SITE getDir _x) }}),
        (if (isNil "MC7_AZ") then {-1} else {round MC7_AZ}), round MC7_OP_GAIN]) call MC7_LOG;
    MC7_ISSUE = "VOID"; MC7_CAUSE = "GEOMETRIE_SEULE"; MC7_FIN = true;
};

[1, "INSERTION", _plafond] call MC7_fnc_debutPhase;

MC7_HELO = objNull;
if (["B_Heli_Transport_01_F"] call MC7_fnc_has) then {
    private _dep = MC7_LZ getPos [3400, (MC7_LZ getDir MC7_SITE) + 180];
    MC7_HELO = createVehicle ["B_Heli_Transport_01_F", [_dep select 0, _dep select 1, 140], [], 0, "FLY"];
    createVehicleCrew MC7_HELO;
    call MC7_fnc_recenser;   // un equipage neuf ne doit pas passer 2 s sans identite
    MC7_HELO flyInHeight 60;
    private _gh = group (driver MC7_HELO);
    _gh setBehaviour "CARELESS"; _gh setCombatMode "BLUE";
    { _x assignAsCargo MC7_HELO; _x moveInCargo MC7_HELO } forEach MC7_FS;
    private _w = _gh addWaypoint [MC7_LZ, 0];
    _w setWaypointType "MOVE"; _w setWaypointSpeed "FULL";
};

// Les plafonds physiques ne sont PAS a l echelle : un vol de 3,4 km est une
// duree du MONDE. MC7_ECHELLE raccourcit les plafonds TACTIQUES et rien d autre.
private _pose = false;
if (!isNull MC7_HELO) then {
    private _tv = time;
    waitUntil { sleep 2; (MC7_HELO distance2D MC7_LZ < 250) || (time - _tv > 300) || MC7_FIN };
    if (MC7_HELO distance2D MC7_LZ < 600) then {
        MC7_HELO land "GET OUT";
        private _tl = time;
        waitUntil { sleep 1; (((getPosATL MC7_HELO) select 2) < 1.5 && { (speed MC7_HELO) < 3 }) || (time - _tl > 120) || MC7_FIN };
    };
    _pose = (((getPosATL MC7_HELO) select 2) < 2.5) && { (speed MC7_HELO) < 5 };
    if (!_pose) then {
        MC7_INSERTION_FORCEE = true;
        MC7_HELO setPosATL [MC7_LZ select 0, MC7_LZ select 1, 0.3];
        MC7_HELO setVelocity [0, 0, 0];
        sleep 2;
        (format ["CHACAL|AVERT|insertion_forcee|%1|appareil_pose_a_la_main", round (time * 100) / 100]) call MC7_LOG;
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
            _x setPosATL (MC7_HELO getPos [15, _k * 36]);
            _k = _k + 1;
        };
    } forEach MC7_FS;
    sleep 3;
    {
        if (alive _x && { vehicle _x != _x }) then {
            unassignVehicle _x; moveOut _x;
            _x setPosATL (MC7_HELO getPos [15, _k * 36]); _k = _k + 1;
        };
    } forEach MC7_FS;
    sleep 2;
};

// Le critere est ETRE SORTI ET VIVANT. L ecart au point prevu est une MESURE,
// pas une porte : un helicoptere qui se pose 350 m plus loin a insere.
private _auSol = MC7_FS select { alive _x && { vehicle _x == _x } };
private _ecart = if (count _auSol > 0) then { round ((_auSol call MC7_fnc_centre) distance2D MC7_LZ) } else { -1 };
(format ["CHACAL|E|debarquement|%1|au_sol|%2|ecart_lz|%3|helico_pose|%4|methode|ANNEAU_SCRIPTE", round (time * 100) / 100,
    count _auSol, _ecart, (if (_pose) then {1} else {0})]) call MC7_LOG;

private _morts = MC7_EFFECTIF - (count (MC7_FS select { alive _x }));
// ! MORTS SOUS LE FEU ENNEMI ( 16/09, decision de Younes ). Avec des menaces pres du poser, un homme
// tue par l ennemi est une ISSUE : un poser mal choisi coute des vies, et l agent doit l apprendre.
// Seule une mort sans tueur ennemi ( physique, ecrasement ) annule encore l episode.
private _parEnnemi = { !alive _x && { _x getVariable ["chacal_tue_par_est", false] } } count MC7_FS;
if (_parEnnemi > 0) then {
    (format ["CHACAL|E|insertion_sous_le_feu|%1|morts_par_ennemi|%2|morts_total|%3", round (time * 100) / 100, _parEnnemi, _morts]) call MC7_LOG;
};
if ((_morts - _parEnnemi) > 0) exitWith {
    // Une insertion qui tue n est pas une insertion. On ne la rattrape pas : on
    // REFUSE l episode. Continuer a huit produirait un corpus ou l echec serait
    // mis au compte de la tactique.
    MC7_ISSUE = "VOID"; MC7_CAUSE = "INSERTION_MORTELLE";
    (format ["CHACAL|VOID|insertion|%1|morts|%2|au_sol|%3", round (time * 100) / 100, _morts, count _auSol]) call MC7_LOG;
    MC7_FIN = true;
};
if (count _auSol < (MC7_EFFECTIF - _parEnnemi)) exitWith {
    MC7_ISSUE = "VOID"; MC7_CAUSE = "INSERTION_INCOMPLETE";
    (format ["CHACAL|VOID|insertion|%1|au_sol|%2", round (time * 100) / 100, count _auSol]) call MC7_LOG;
    MC7_FIN = true;
};
_issue = if (MC7_INSERTION_FORCEE) then {"FORCEE"} else {"ATTEINT"};

if (!isNull MC7_HELO) then {
    private _gh = group (driver MC7_HELO);
    if (!isNull _gh) then {
        while { count (waypoints _gh) > 0 } do { deleteWaypoint ((waypoints _gh) select 0) };
        private _rr = _gh addWaypoint [MC7_LZ getPos [5000, (MC7_LZ getDir MC7_SITE) + 180], 0];
        _rr setWaypointType "MOVE"; _rr setWaypointSpeed "FULL";
    };
    // Sans cette ligne, trois identifiants quittent le flux d etat sans ligne
    // `mort` : un lecteur ne peut pas distinguer un retrait scripte d une mort
    // non journalisee, et il ne doit pas avoir a deviner.
    [] spawn {
        sleep 240;
        if (!isNull MC7_HELO) then {
            { (format ["CHACAL|E|retrait|%1|%2|equipage_helicoptere", round (time * 100) / 100,
                (_x getVariable ["chacal_id", -1])]) call MC7_LOG; deleteVehicle _x } forEach (crew MC7_HELO);
            deleteVehicle MC7_HELO;
        };
    };
};

MC7_gFS setBehaviour "STEALTH"; MC7_gFS setCombatMode "GREEN";
MC7_gFS setSpeedMode "LIMITED"; MC7_gFS setFormation "FILE";
// ! LE CHOIX DE LA PHASE 1 ( plans/plan-choix-par-vignette.md, 17/09 ) : partir tout de suite ou se terrer.
// Les deux options durent 180 s, pour que la consequence ait le meme temps d arriver. 0 = les 60 s d origine.
if (MC7_P1_ATTENTE > 0) then {
    [1] call MC7_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )
    [1, "INSERTION_ATTENTE", [1, 2], MC7_P1_ATTENTE, "IMPOSE"] call MC7_fnc_decision;
    if (MC7_P1_ATTENTE == 1) then {
        private _dest = MC7_LZ getPos [300, MC7_LZ getDir MC7_ROUTE];
        [MC7_gFS, _dest, "LIMITED", "STEALTH", "FILE", "CHOIX_P1_PARTIR"] call MC7_fnc_ordreAller;
        (format ["CHACAL|E|choix_joue|%1|point|INSERTION_ATTENTE|choix|1|detail|PARTIR|vers|%2", round (time * 100) / 100, _dest]) call MC7_LOG;
    } else {
        { if (alive _x) then { doStop _x; _x setUnitPos "DOWN" } } forEach (units MC7_gFS);
        (format ["CHACAL|E|choix_joue|%1|point|INSERTION_ATTENTE|choix|2|detail|SE_TERRER", round (time * 100) / 100]) call MC7_LOG;
    };
    private _tC = time;
    waitUntil { sleep 2; ((time - _tC) > 180) || MC7_FIN };
    { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units MC7_gFS);
} else {
    sleep (60 * MC7_ECHELLE);
};
[1, "INSERTION", _issue] call MC7_fnc_finPhase;
};   // fin de l alternative DEPART = 2

// ---------------------------------------------------------------------
// PHASE 2 - APPROCHE, et le franchissement de la route
// ---------------------------------------------------------------------
if (MC7_FIN) exitWith {};   // vignette close a la phase 1
_plafond = 2 call MC7_fnc_duree;
[2, "APPROCHE", _plafond] call MC7_fnc_debutPhase;

private _fr = MC7_ROUTE;
private _avant = _fr getPos [MC7_AVANT, _fr getDir MC7_LZ];   // levier : d ou l on observe la route ( origine 260 m )

// DEUX JAMBES, et c est de la tactique : loin de l objectif on marche, a moins
// de 1,5 km on se traine. Ramper sur 4 km n est pas de la furtivite.
private _b1 = [MC7_gFS, _avant, 0.7] call MC7_fnc_budget;
(format ["CHACAL|E|budget|%1|etape|APPROCHE_ROUTE|distance|%2|plafond|%3", round (time * 100) / 100,
    round (((units MC7_gFS) call MC7_fnc_centre) distance2D _avant), round _b1]) call MC7_LOG;
[MC7_gFS, _avant, "NORMAL", "AWARE", "FILE", "OPORD_ROUTE_JAMBE_LOINTAINE"] call MC7_fnc_ordreAller;
_r = [MC7_gFS, _avant, 60, _b1] call MC7_fnc_arrive;

// ! LA FENETRE SE DECIDE SUR CE QUE LA FILE PERCOIT, PAS SUR LA POSITION VRAIE.
// Le premier jet lisait `MC7_VEH_ROUTE distance2D _avant`, que personne dans
// la file ne peut connaitre : l eleve aurait appris a attendre un nombre
// invisible. Ici, rien que le canal geometrique. Consequence assumee : de nuit
// ils peuvent ne JAMAIS voir le vehicule et traverser en aveugle. C est une
// donnee, et elle est etiquetee.
if ((_r in ["ATTEINT", "ENLISE"]) && !MC7_SAUT) then {
    { doStop _x } forEach (units MC7_gFS);
    // ! LE CHOIX DE LA PHASE 2 ( plans/plan-choix-par-vignette.md, 17/09 ) : traverser tout de suite ( 1 ) ou attendre la
    // patrouille ( 2 ). ATTENDRE applique la regle de perception SANS la sortie PATROUILLE_ABSENTE, qui lisait l etat vrai
    // du monde : le detachement ne peut pas savoir qu aucune patrouille ne viendra. 0 = la regle d origine, inchangee.
    if (MC7_TRAVERSEE > 0) then {
        [2] call MC7_fnc_fenetreObservation;   // menace visible : regarder avant de choisir ( 0 = origine )
        private _vD = if (isNil "MC7_VEH_ROUTE") then { objNull } else { MC7_VEH_ROUTE };
        private _vuD = 0;
        if (!isNull _vD && { alive _vD }) then {
            if (({ [_x, _vD, 800, 70] call MC7_fnc_voit } count ((units MC7_gFS) select { alive _x })) > 0) then { _vuD = 1 };
        };
        [2, "TRAVERSEE", [1, 2], MC7_TRAVERSEE, "IMPOSE", format ["|vehicule_vu|%1", _vuD]] call MC7_fnc_decision;
    };
    private _tf = time;
    private _dejaVu = false; private _dernierVu = -1; private _traverse = false; private _cause = "";
    while { !_traverse && (time - _tf < 420 * MC7_ECHELLE) && ((call MC7_fnc_reste) > 0) && !MC7_SAUT && !MC7_FIN } do {
        if (MC7_TRAVERSEE == 1) then { _traverse = true; _cause = "IMPOSE_TOUT_DE_SUITE" } else {
            private _v = MC7_VEH_ROUTE;
            private _vu = false;
            if (!isNull _v && { alive _v }) then {
                private _hommes = (units MC7_gFS) select { alive _x };
                _vu = ({ [_x, _v, 800, 70] call MC7_fnc_voit } count _hommes) > 0;
            };
            if (_vu) then { _dejaVu = true; _dernierVu = time };
            if (_dejaVu && { !_vu } && { (time - _dernierVu) > (45 * MC7_ECHELLE) }) then { _traverse = true; _cause = "FENETRE_OBSERVEE" };
            if (!_dejaVu && { (time - _tf) > (240 * MC7_ECHELLE) }) then { _traverse = true; _cause = "TRAVERSEE_AVEUGLE" };
            if ((MC7_TRAVERSEE != 2) && { isNull _v || { !alive _v } }) then { _traverse = true; _cause = "PATROUILLE_ABSENTE" };
            sleep 3;
        };
    };
    if (!_traverse) then { _cause = "PLAFOND_FENETRE" };
    (format ["CHACAL|E|fenetre|%1|%2|attente|%3|vehicule_vu|%4", round (time * 100) / 100,
        _cause, round (time - _tf), (if (_dejaVu) then {1} else {0})]) call MC7_LOG;
    if (MC7_TRAVERSEE > 0) then {
        (format ["CHACAL|E|choix_joue|%1|point|TRAVERSEE|choix|%2|detail|%3|attente|%4", round (time * 100) / 100,
            MC7_TRAVERSEE, _cause, round (time - _tf)]) call MC7_LOG;
    };
    { _x doFollow (leader MC7_gFS) } forEach (units MC7_gFS);

    // ! ILS ONT BIEN FRANCHI, PUIS SONT RESTES DANS L ENVELOPPE DU VEHICULE.
    // Sept minutes plus tard le MRAP revient et tue le chef et l adjoint. Le
    // franchissement n est pas un POINT, c est un COULOIR : on en sort vite,
    // perpendiculairement a l axe du circuit, et on ne reprend la furtivite
    // qu au-dela de 700 m de cet axe.
    private _perp = (MC7_ROUTE_A getDir MC7_ROUTE_B) + 90;
    if ((abs (((_perp - (_fr getDir MC7_SITE)) + 540) % 360 - 180)) > 90) then { _perp = _perp + 180 };
    private _degage = _fr getPos [750, _perp];
    [MC7_gFS, _degage, "NORMAL", "AWARE", "WEDGE", "SORTIE_DE_COULOIR"] call MC7_fnc_ordreAller;
    (format ["CHACAL|E|couloir|%1|axe|%2|sortie|%3", round (time * 100) / 100, round _perp, _degage]) call MC7_LOG;
    [MC7_gFS, _degage, 90, [MC7_gFS, _degage, 1.1] call MC7_fnc_budget] call MC7_fnc_arrive;
};

// ! VIGNETTE DE LA ROUTE ( 16/09 ) : au depart a la route avec arret a la phase 2, la phase s arrete a la
// sortie du couloir, sans la marche de ~1,7 km jusqu au regroupement qui ne decide plus rien.
if (!MC7_SAUT && { !(MC7_DEPART == 2 && MC7_ARRET == 2) }) then {
    private _b2 = [MC7_gFS, MC7_RALLY, 0.5] call MC7_fnc_budget;
    (format ["CHACAL|E|budget|%1|etape|APPROCHE_RALLY|distance|%2|plafond|%3", round (time * 100) / 100,
        round (((units MC7_gFS) call MC7_fnc_centre) distance2D MC7_RALLY), round _b2]) call MC7_LOG;
    [MC7_gFS, MC7_RALLY, "LIMITED", "STEALTH", "FILE", "OPORD_RALLY"] call MC7_fnc_ordreAller;
    _r = [MC7_gFS, MC7_RALLY, 70, _b2] call MC7_fnc_arrive;
};
[2, "APPROCHE", (if (MC7_SAUT) then {"COMPROMIS"} else {_r})] call MC7_fnc_finPhase;

// ! ABANDON : compromis LOIN, on ne charge pas a dix contre trente-deux.
// Le premier jet menait toute compromission a l assaut en bloc, plafond 900 s,
// jamais arrive, echec par construction. Le corpus enseignait " detecte, donc
// charge " - la decision la plus importante de la mission n avait qu une
// reponse, toujours la meme.
// ! 20/09 : quand la patrouille tue les dix, la liste des vivants est VIDE et MC7_fnc_centre erre.
// Le defaut dormait depuis toujours : aucune campagne n avait encore aneanti le detachement.
if (MC7_TENIR == 0 && MC7_COMPROMIS && { count (MC7_FS select { alive _x }) > 0 }
    && { ((MC7_FS select { alive _x }) call MC7_fnc_centre) distance2D MC7_SITE > 1200 }) then {
    MC7_ABANDON = true; MC7_SAUT = false;
    MC7_CAUSE_ABANDON = "COMPROMIS_LOIN";
    (format ["CHACAL|E|abandon|%1|distance|%2", round (time * 100) / 100,
        round (((MC7_FS select { alive _x }) call MC7_fnc_centre) distance2D MC7_SITE)]) call MC7_LOG;
};

};

// --- LE BRAS TEMOIN : il saute observation et articulation ---
// Sans lui on ne sait pas si le plan en six phases vaut mieux que marcher
// droit, et un corpus dont on ignore s il enseigne quelque chose est un actif
// invendable.
if (MC7_BRAS == "NUL" && !MC7_SAUT && !MC7_ABANDON) then {
    MC7_OUV_CHOISIE = MC7_OUVERTURES select 0;
    MC7_POS_ASSAUT = [MC7_SITE getPos [230, MC7_SITE getDir MC7_OUV_CHOISIE], 60] call MC7_fnc_plat;
    [MC7_gFS, MC7_POS_ASSAUT, "NORMAL", "AWARE", "WEDGE", "BRAS_NUL_DROIT_SUR_L_OBJECTIF"] call MC7_fnc_ordreAller;
    (format ["CHACAL|E|bras_nul|%1|vers|%2", round (time * 100) / 100, MC7_POS_ASSAUT]) call MC7_LOG;
    [MC7_gFS, MC7_POS_ASSAUT, 90, [MC7_gFS, MC7_POS_ASSAUT, 0.9] call MC7_fnc_budget] call MC7_fnc_arrive;
};

// ---------------------------------------------------------------------
// PHASE 3 - POINT D OBSERVATION : deux hommes montent, huit se terrent
// ---------------------------------------------------------------------
if (!MC7_FIN && !MC7_SAUT && !MC7_ABANDON && { MC7_BRAS != "NUL" } && { MC7_DEPART < 4 }) then {
    _plafond = 3 call MC7_fnc_duree;
    [3, "OBSERVATION", _plafond] call MC7_fnc_debutPhase;
    // ! COUPURE ASSUMEE ET ECRITE. Voir verdicts/phase3-porte-hors-datteinte.md.
    if (MC7_OBS == 0) exitWith {
        (format ["CHACAL|AVERT|hors_corpus|observation_coupee|1|seuil|%1|jamais_atteint|1",
            MC7_SEUIL_RENS]) call MC7_LOG;
        (format ["CHACAL|E|observation_coupee|%1|economie_s|%2", round (time * 100) / 100,
            round _plafond]) call MC7_LOG;
        [3, "OBSERVATION", "COUPEE"] call MC7_fnc_finPhase;
    };

    MC7_gReco = [MC7_RECO, "RECHERCHE"] call MC7_fnc_detacher;
    MC7_gFS setVariable ["chacal_element", "GROS", true];
    [MC7_gReco, MC7_OP, "LIMITED", "STEALTH", "FILE", "OPORD_CRETE"] call MC7_fnc_ordreAller;
    private _cache = [MC7_RALLY getPos [120, MC7_RALLY getDir MC7_SITE], 50] call MC7_fnc_plat;
    [MC7_gFS, _cache, "LIMITED", "STEALTH", "WEDGE", "TENIR_HORS_DE_VUE"] call MC7_fnc_ordreAller;

    private _rArr = [MC7_gReco, MC7_OP, 60, [MC7_gReco, MC7_OP, 0.5] call MC7_fnc_budget] call MC7_fnc_arrive;
    (format ["CHACAL|E|montee|%1|issue|%2|reco|%3|distance|%4", round (time * 100) / 100,
        _rArr, count ((units MC7_gReco) select { alive _x }),
        (if (count ((units MC7_gReco) select { alive _x }) > 0)
         then { round ((((units MC7_gReco) select { alive _x }) call MC7_fnc_centre) distance2D MC7_OP) }
         else { -1 })]) call MC7_LOG;

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
            _x setDir (_x getDir MC7_SITE);
            _x doWatch MC7_SITE;
        };
    } forEach (units MC7_gReco);
    (format ["CHACAL|E|orientation|%1|reco|%2|azimut_site|%3|distance|%4", round (time * 100) / 100,
        count ((units MC7_gReco) select { alive _x }),
        round (MC7_OP getDir MC7_SITE), round (MC7_OP distance2D MC7_SITE)]) call MC7_LOG;
    { if (alive _x) then { _x setUnitPos "MIDDLE" } } forEach (units MC7_gFS);

    // LE RENSEIGNEMENT EST RETENU, pas seulement compte : ce qui entre dans
    // MC7_VUES est ce que la reco a vu GEOMETRIQUEMENT au moins une fois.
    // ! LE CHOIX DE LA PHASE 3 ( plans/plan-choix-par-vignette.md, 17/09 ) : observer 120 ou 480 s. Le rapprochement
    // vers un second poste est une AUTRE decision : il n est pas joue quand la duree est imposee. 0 = regle d origine.
    private _dureeObs = _plafond * 0.55;
    if (MC7_OBS_DUREE > 0) then {
        _dureeObs = MC7_OBS_DUREE;
        [3, "OBS_DUREE", [120, 480], MC7_OBS_DUREE, "IMPOSE", format ["|reco_vivants|%1", count ((units MC7_gReco) select { alive _x })]] call MC7_fnc_decision;
    };
    private _tObs = time;
    while { (time - _tObs) < _dureeObs && ((call MC7_fnc_reste) > 0) && !MC7_SAUT && !MC7_FIN } do {
        private _obs = (units MC7_gReco) select { alive _x };
        if (count _obs > 0) then {
            {
                private _e = _x;
                if ({ [_x, _e, 900] call MC7_fnc_voit } count _obs > 0) then {
                    private _k = 0;
                    { private _kk = _x knowsAbout _e; if (_kk > _k) then { _k = _kk } } forEach _obs;
                    private _i = MC7_VUES findIf { (_x select 0) isEqualTo _e };
                    if (_i < 0) then { MC7_VUES pushBack [_e, _k] }
                    else { if (_k > ((MC7_VUES select _i) select 1)) then { (MC7_VUES select _i) set [1, _k] } };
                };
            } forEach (MC7_EST_SITE select { alive _x });
            (format ["CHACAL|E|renseignement|%1|localisees|%2|sur|%3|seuil|%4", round (time * 100) / 100,
                count MC7_VUES, count (MC7_EST_SITE select { alive _x }), MC7_SEUIL_RENS]) call MC7_LOG;
        };
        sleep (60 * MC7_ECHELLE);
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
    if (MC7_OBS_DUREE > 0) then {
        (format ["CHACAL|E|choix_joue|%1|point|OBS_DUREE|choix|%2|detail|OBSERVE|duree_reelle|%3|localisees|%4|rapprochement|0",
            round (time * 100) / 100, MC7_OBS_DUREE, round (time - _tObs), count MC7_VUES]) call MC7_LOG;
    };
    if (!MC7_SAUT && { MC7_OBS_DUREE == 0 } && { count MC7_VUES < MC7_SEUIL_RENS }) then {
        private _second = [MC7_SITE getPos [250, MC7_SITE getDir MC7_OP], 60] call MC7_fnc_plat;
        (format ["CHACAL|E|rapprochement|%1|localisees|%2|seuil|%3|vers|%4", round (time * 100) / 100,
            count MC7_VUES, MC7_SEUIL_RENS, _second]) call MC7_LOG;
        [MC7_gReco, _second, 60, ([MC7_gReco, _second] call MC7_fnc_budgetDeuxJambes) min 600, "RECO_SECOND_POSTE"] call MC7_fnc_rejoindre;
        { if (alive _x) then { _x setUnitPos "DOWN"; _x setDir (_x getDir MC7_SITE); _x doWatch MC7_SITE } } forEach (units MC7_gReco);
        private _t2 = time;
        while { (time - _t2) < (300 * MC7_ECHELLE) && !MC7_SAUT && !MC7_FIN } do {
            private _obs2 = (units MC7_gReco) select { alive _x };
            if (count _obs2 > 0) then {
                {
                    private _e = _x;
                    if ({ [_x, _e, 600] call MC7_fnc_voit } count _obs2 > 0) then {
                        private _k = 0;
                        { private _kk = _x knowsAbout _e; if (_kk > _k) then { _k = _kk } } forEach _obs2;
                        private _i = MC7_VUES findIf { (_x select 0) isEqualTo _e };
                        if (_i < 0) then { MC7_VUES pushBack [_e, _k] };
                    };
                } forEach (MC7_EST_SITE select { alive _x });
                (format ["CHACAL|E|renseignement|%1|localisees|%2|sur|%3|seuil|%4|poste|SECOND", round (time * 100) / 100,
                    count MC7_VUES, count (MC7_EST_SITE select { alive _x }), MC7_SEUIL_RENS]) call MC7_LOG;
            };
            sleep (60 * MC7_ECHELLE);
        };
        if (count MC7_VUES < MC7_SEUIL_RENS) then {
            (format ["CHACAL|E|renseignement_pauvre|%1|localisees|%2|l_assaut_part_quand_meme", round (time * 100) / 100, count MC7_VUES]) call MC7_LOG;
        };
    };
    [3, "OBSERVATION", (if (MC7_SAUT) then {"COMPROMIS"} else {
        if (count MC7_VUES >= MC7_SEUIL_RENS) then {"ATTEINT"} else {"RENSEIGNEMENT_PAUVRE"} })] call MC7_fnc_finPhase;
};

// ---------------------------------------------------------------------
// PHASE 4 - MISE EN PLACE : appui, assaut, bouchon
// ---------------------------------------------------------------------
if (!MC7_FIN && !MC7_SAUT && !MC7_ABANDON && { MC7_BRAS != "NUL" }) then {
    _plafond = 4 call MC7_fnc_duree;
    [4, "MISE_EN_PLACE", _plafond] call MC7_fnc_debutPhase;

    MC7_gAppui   = [MC7_APPUI,   "APPUI"]   call MC7_fnc_detacher;
    MC7_gAssaut  = [MC7_ASSAUT,  "ASSAUT"]  call MC7_fnc_detacher;
    MC7_gBouchon = [MC7_BOUCHON, "BOUCHON"] call MC7_fnc_detacher;

    // ! LA LIGNE DE DECISION ( 16/09 ). Elle porte l OPTION jouee ET l OBSERVABLE sur
    // lequel elle devrait se decider, sur une seule ligne, comme choix_ouverture le fait
    // pour les portes. C est elle qui remplira la table `decision` du socle : sans un
    // triplet ( etat, action, issue ) ecrit noir sur blanc, le banc n est pas un support
    // d apprentissage mais un tableau d affichage.
    // Les comptes sont pris SUR LES GROUPES REELS, pas sur les listes de roles : un homme
    // deja mort ne doit pas etre compte dans son element.
    // ! Le palier 9 ( monde vide, controle positif de l acte ) sort de 30_opfor AVANT de
    // definir MC7_PAL_QRF : d ou le garde isNil ci-dessous, sans lequel cette ligne
    // ecrirait une variable non definie dans la trace du controle positif.
    (format ["CHACAL|E|partage|%1|regle|%2|assaut|%3|bouchon|%4|appui|%5|qrf_vehicules|%6|qrf_hommes|%7|delai_qrf|%8",
        round (time * 100) / 100,
        (if (MC7_PARTAGE == 1) then {"SEPT_UN"} else {"CINQ_TROIS"}),
        count (units MC7_gAssaut), count (units MC7_gBouchon), count (units MC7_gAppui),
        (if (isNil "MC7_PAL_QRF") then {0} else {MC7_PAL_QRF}), count MC7_QRF, MC7_PAL_DELAI]) call MC7_LOG;

    // ! LE RENSEIGNEMENT CHOISIT L OUVERTURE. Le premier jet visait az_OP + 99 :
    // une constante deguisee en tactique, et c est " marche au 315 " en repere
    // relatif. Ici on compte les sentinelles LOCALISEES pres de chaque porte et
    // on entre par la moins gardee.
    // ! LE CHOIX PESE LES GARDES *ET* LE TRAJET. Ne regarder que les sentinelles
    // fait entrer par une porte deux fois plus loin pour eviter quatre hommes -
    // et sur une nuit ou l articulation est deja le goulot, ce marche est
    // mauvais. Un garde localise vaut 150 m de marche ; l arbitrage est
    // journalise pour qu il soit discutable.
    // ! L ORACLE COMPLET ( MC7_ORACLE = 2, revue de Fable 11/09 ) : les defenseurs sont reveles et
    // inscrits comme vus AVANT le choix de la porte, qui se fait alors en les connaissant.
    if (MC7_ORACLE == 2) then {
        private _defO = MC7_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _defO } forEach (MC7_FS select { alive _x });
        MC7_VUES = _defO apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4|avant_choix_porte|1", round (time * 100) / 100,
            count _defO, count (MC7_FS select { alive _x })]) call MC7_LOG;
    };
    private _dep = ((units MC7_gAssaut) select { alive _x }) call MC7_fnc_centre;
    if (count _dep == 0) then { _dep = MC7_RALLY };
    // ! MARQUEUR-GARDE-PLUS-PROCHE - LE TERME DE GARDE ETAIT INERTE PAR CONSTRUCTION ( 15/09 ).
    // Le seuil de 110 m se voulait " pres de cette porte ". L enceinte a 46 m de rayon, les deux
    // ouvertures sont a 108,0 et 282,857 relatifs - une corde de 92 m - et la garnison se garnit
    // dans 55 m : tout defenseur est donc a moins de 101 m des DEUX ouvertures. Mesure sur les
    // journaux : le champ gardes vaut [k,k] dans 1337 episodes sur 1337, et l indice retenu est
    // l ouverture la plus proche dans 1337 sur 1337. Le terme ne decidait rien.
    // LA REGLE DEVIENT SANS SEUIL : chaque defenseur connu compte pour l ouverture dont il est le
    // PLUS PROCHE. Discriminant par construction des que MC7_VUES n est pas vide.
    // Le poids reste " un garde vaut 150 m de marche ", et c est mesure : |d_A - d_B| vaut 18 m en
    // mediane, 83 m au pire, jamais plus que la corde de 92 m, soit 0,55 point au plus contre 1,00
    // pour un garde. Des que les comptes different le compte decide ; a comptes egaux la distance
    // tranche. L intention publiee devient vraie sans qu on touche au 150.
    // ! L affectation est calculee UNE FOIS, HORS de la boucle de score : une boucle imbriquee
    // dedans aurait masque _forEachIndex, dont la ligne du minimum a besoin. Aucun continue,
    // aucun break, aucun waitUntil n est introduit.
    private _connus = (MC7_VUES apply { _x select 0 }) select { !isNull _x };
    private _aff  = MC7_OUVERTURES apply { 0 };      // defenseurs connus attribues a l ouverture
    private _dgar = MC7_OUVERTURES apply { -1 };     // distance du defenseur connu le plus proche
    {
        private _pv = _x;                               // l unite, liee AVANT la boucle interne
        private _jv = -1; private _dv = 1e9;
        {
            private _dd = _pv distance2D _x;            // ici _x est une OUVERTURE
            if (_dd < _dv) then { _dv = _dd; _jv = _forEachIndex };
            if (((_dgar select _forEachIndex) < 0) || { _dd < (_dgar select _forEachIndex) }) then {
                _dgar set [_forEachIndex, _dd];
            };
        } forEach MC7_OUVERTURES;
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
    } forEach MC7_OUVERTURES;
    MC7_OUV_CHOISIE = MC7_OUVERTURES select _meilleure;
    // ! LA COUTURE DE L AZIMUT. Douze candidats publies, un decideur designe par MC7_AZIMUT.
    // Le mode 0 ne touche a rien : MC7_OUV_CHOISIE garde la valeur que le score vient de poser.
    // Les modes 1 et 2 remplacent le POINT VISE par un point de meme rayon a l azimut retenu, ce qui
    // laisse intact tout ce qui en depend en aval : la position d assaut, la cible, le poste d appui.
    private _candidats = [];
    for "_i" from 0 to 11 do { _candidats pushBack (_i * 30) };
    MC7_AZIMUT_CHOISI = round (MC7_SITE getDir MC7_OUV_CHOISIE);
    private _qui = "SCRIPT";
    if (MC7_AZIMUT == 1) then {
        // tirage seme par la graine : deux episodes de meme graine tirent le meme azimut, sinon
        // le temoin ne serait pas un temoin.
        // ! le TEMOIN, pas le generateur du monde : sinon le bras hasard tire un azimut fixe par graine
        private _k = floor ((call MC7_fnc_rndTemoin) * (count _candidats));
        if (_k >= count _candidats) then { _k = (count _candidats) - 1 };
        MC7_AZIMUT_CHOISI = _candidats select _k; _qui = "HASARD";
    };
    if (MC7_AZIMUT == 2) then {
        MC7_AZIMUT_CHOISI = ((round MC7_AZIMUT_VAL) + 360) % 360; _qui = "IMPOSE";
    };
    if (MC7_AZIMUT > 0) then {
        MC7_OUV_CHOISIE = MC7_SITE getPos [MC7_RAYON, MC7_AZIMUT_CHOISI];
        MC7_OUV_CHOISIE set [2, 0];
    };
    (format ["CHACAL|E|couture_azimut|%1|mode|%2|decideur|%3|candidats|%4|choisi|%5|point|%6|az_ouvertures|%7",
        round (time * 100) / 100, MC7_AZIMUT, _qui, count _candidats, MC7_AZIMUT_CHOISI,
        MC7_OUV_CHOISIE, (MC7_OUVERTURES apply { round (MC7_SITE getDir _x) })]) call MC7_LOG;
    // ! Champs AJOUTES EN FIN DE LIGNE. Aucun retire, aucun renomme : les analyses existantes
    // lisent indice, gardes, distances, score et renseignement par expression reguliere.
    //   dgarde : distance en metres du defenseur connu le plus proche de chaque ouverture, -1
    //            si aucun. A gardes egaux, dgarde dit si l egalite est vraie ou fortuite.
    //   regle  : la regle d attribution en vigueur, pour distinguer un journal d avant du patch.
    (format ["CHACAL|E|choix_ouverture|%1|indice|%2|gardes|%3|distances|%4|score|%5|renseignement|%6|dgarde|%7|regle|PLUS_PROCHE",
        round (time * 100) / 100, _meilleure, str _comptes, str _dists,
        round (_minScore * 100) / 100, count MC7_VUES,
        str (_dgar apply { if (_x < 0) then { -1 } else { round _x } })]) call MC7_LOG;

    // ! L APPUI N EST PLUS L OBSERVATOIRE ( sous parametre ). A 0, on garde la ligne d origine.
    MC7_POS_APPUI   = MC7_OP;
    // ! Le point de depart est passe depuis l element concerne : c est la seule facon de savoir
    // si le trajet est praticable. Sans MC7_ACCESSIBLE, l argument est ignore.
    private _depAssaut  = ((units MC7_gAssaut)  select { alive _x }) call MC7_fnc_centre;
    private _depBouchon = ((units MC7_gBouchon) select { alive _x }) call MC7_fnc_centre;
    MC7_POS_ASSAUT  = [MC7_SITE getPos [230, MC7_SITE getDir MC7_OUV_CHOISIE], 60, 220, _depAssaut] call MC7_fnc_plat;
    // ! 700 m sur l axe de la reserve etait un chiffre ecrit sans justification,
    // et il demandait au bouchon une demi-heure de marche. Son travail est de
    // RETARDER la reserve, pas de tenir un carrefour : 400 m le font aussi bien.
    MC7_POS_BOUCHON = [MC7_SITE getPos [400, MC7_SITE getDir MC7_QRF_BASE], 80, 220, _depBouchon] call MC7_fnc_plat;
    if (MC7_APPUI_FEU == 1) then {
        MC7_POS_APPUI = [MC7_SITE, MC7_OUV_CHOISIE, MC7_POS_ASSAUT, MC7_OP] call MC7_fnc_positionAppui;
    };
    // ! V9 ( Fable, 11/09 ) : une fois en place, l appui tient sa place. YELLOW = tir a volonte,
    // garde ta place ; RED = engage a volonte, et on l a mesure partir au contact a 11-18 km/h.
    if (MC7_APPUI_FIXE == 1) then {
        [] spawn {
            waitUntil { sleep 2; MC7_FIN || { !isNull MC7_gAppui && { [MC7_gAppui, MC7_POS_APPUI, 70] call MC7_fnc_enPlace } } };
            if (MC7_FIN || { isNull MC7_gAppui }) exitWith {};
            MC7_gAppui setCombatMode "YELLOW";
            MC7_gAppui setVariable ["lambs_danger_disableGroupAI", true, true];
            { if (alive _x) then { _x disableAI "PATH"; _x setVariable ["lambs_danger_disableAI", true, true] } } forEach (units MC7_gAppui);
            (format ["CHACAL|E|appui_fixe|%1|position|%2|compromis|%3", round (time * 100) / 100, MC7_POS_APPUI,
                (if (MC7_COMPROMIS) then {1} else {0})]) call MC7_LOG;
        };
    };

    // Le plafond est la SOMME des deux jambes, calculee sur les vitesses
    // reellement ordonnees - 1,1 m/s puis 0,5 - et non sur une constante
    // d infiltration qui mentait d un facteur deux.
    private _b1 = [MC7_gAppui,   MC7_POS_APPUI]   call MC7_fnc_budgetDeuxJambes;
    private _b2 = [MC7_gAssaut,  MC7_POS_ASSAUT]  call MC7_fnc_budgetDeuxJambes;
    private _b3 = [MC7_gBouchon, MC7_POS_BOUCHON] call MC7_fnc_budgetDeuxJambes;
    _plafond = (_b1 max _b2) max _b3;
    // ! Un choix d itineraire impose double le plafond pour LES DEUX options : un detour ne doit pas echouer au chronometre.
    if (MC7_ITINERAIRE > 0) then { _plafond = _plafond * 2 };
    MC7_TPHASE = time; MC7_PLAFOND_COURANT = _plafond;
    (format ["CHACAL|E|budget|%1|etape|MISE_EN_PLACE|appui|%2|assaut|%3|bouchon|%4|plafond|%5",
        round (time * 100) / 100, round _b1, round _b2, round _b3, round _plafond]) call MC7_LOG;

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
    if (MC7_ORACLE >= 1) then {
        private _def = MC7_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (MC7_FS select { alive _x });
        MC7_VUES = _def apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4", round (time * 100) / 100, count _def,
            count (MC7_FS select { alive _x })]) call MC7_LOG;
    };
    if (MC7_DEPART >= 4) then {
        "CHACAL|AVERT|hors_corpus|depart|4|articulation_non_jouee" call MC7_LOG;
        {
            _x params ["_g", "_p"];
            if (!isNull _g) then {
                { if (alive _x) then { _x setPosATL (_p getPos [4 + (10 call MC7_fnc_al), 360 call MC7_fnc_al]) } } forEach (units _g);
            };
        } forEach [[MC7_gAppui, MC7_POS_APPUI], [MC7_gAssaut, MC7_POS_ASSAUT], [MC7_gBouchon, MC7_POS_BOUCHON]];
        sleep 5;
    } else {
        if (MC7_ITINERAIRE > 0) then { [4] call MC7_fnc_fenetreObservation; [4, "ITINERAIRE", [1, 2], MC7_ITINERAIRE, "IMPOSE"] call MC7_fnc_decision };
        private _h1 = [MC7_gAppui,   MC7_POS_APPUI,   70, _plafond, "APPUI"]   spawn MC7_fnc_rejoindreItineraire;
        private _h2 = [MC7_gAssaut,  MC7_POS_ASSAUT,  70, _plafond, "ASSAUT"]  spawn MC7_fnc_rejoindreItineraire;
        private _h3 = [MC7_gBouchon, MC7_POS_BOUCHON, 80, _plafond, "BOUCHON"] spawn MC7_fnc_rejoindreItineraire;
        waitUntil { sleep 3; (scriptDone _h1 && scriptDone _h2 && scriptDone _h3) || MC7_FIN || MC7_SAUT };
    };
    _r1 = if ([MC7_gAppui,   MC7_POS_APPUI,   70] call MC7_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    _r2 = if ([MC7_gAssaut,  MC7_POS_ASSAUT,  70] call MC7_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    _r3 = if ([MC7_gBouchon, MC7_POS_BOUCHON, 80] call MC7_fnc_enPlace) then {"ATTEINT"} else {"NON"};
    { if (alive _x) then { _x setUnitPos "DOWN"; _x setDir (_x getDir MC7_SITE); _x doWatch MC7_SITE } } forEach (units MC7_gAppui);
    (format ["CHACAL|E|articulation|%1|appui|%2|assaut|%3|bouchon|%4", round (time * 100) / 100, _r1, _r2, _r3]) call MC7_LOG;
    [4, "MISE_EN_PLACE", (if (_r1 == "ATTEINT" && _r2 == "ATTEINT" && _r3 == "ATTEINT") then {"ATTEINT"}
        else { if (MC7_SAUT) then {"COMPROMIS"} else {"PLAFOND"} })] call MC7_fnc_finPhase;
};

// ---------------------------------------------------------------------
// PHASE 5 - ACTION SUR OBJECTIF
// ---------------------------------------------------------------------
if (!MC7_ABANDON && !MC7_FIN) then {
MC7_SAUT = false;
// ! PRIX DU TEMPS : l attente est prise AVANT le debut de la phase, donc elle ne mange aucun plafond. Le seul cout
// possible est celui du monde qui tourne ( patrouilles, alarme, renfort ) - c est justement ce qu on veut mesurer.
if (MC7_ATTENTE_TEST > 0) then {
    private _tA = time;
    // ! V2 - ON FIGE PENDANT L ATTENTE. La v1 laissait les hommes sans ordre : ils reprenaient leur mouvement
    // precedent, marchaient 818 m, puis revenaient. A 600 s l assaut etait a 330-670 m de sa place et la mission
    // renoncait ( ARTICULATION_ROMPUE ) 14 fois sur 16, alarme 0 et 10 vivants sur 10. Une attente doit couter le
    // temps du monde qui tourne, pas la dislocation du detachement.
    // L appui deja fige par MC7_APPUI_FIXE n est pas touche : lui rendre PATH le ferait partir, et seulement
    // dans les bras qui attendent.
    private _fige = (MC7_FS select { alive _x }) select { !(MC7_APPUI_FIXE == 1 && { group _x == MC7_gAppui }) };
    private _avant = _fige apply { [_x, getPosATL _x] };
    { doStop _x; _x disableAI "PATH" } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|debut|duree_prevue|%2|vivants|%3|alarme|%4|figes|%5", round (time * 100) / 100,
        MC7_ATTENTE_TEST, count (MC7_FS select { alive _x }), (if (MC7_ALARME) then {1} else {0}),
        count _fige]) call MC7_LOG;
    waitUntil { sleep 2; MC7_FIN || ((time - _tA) >= (MC7_ATTENTE_TEST * MC7_ECHELLE)) };
    private _derive = 0;
    { _x params ["_u", "_p"]; if (alive _u) then { _derive = _derive max (_u distance2D _p) } } forEach _avant;
    { if (alive _x) then { _x enableAI "PATH"; _x doFollow (leader (group _x)) } } forEach _fige;
    (format ["CHACAL|E|attente_test|%1|fin|duree|%2|vivants|%3|alarme|%4|compromis|%5|derive|%6", round (time * 100) / 100,
        round (time - _tA), count (MC7_FS select { alive _x }), (if (MC7_ALARME) then {1} else {0}),
        (if (MC7_COMPROMIS) then {1} else {0}), round _derive]) call MC7_LOG;
};
_plafond = 5 call MC7_fnc_duree;
[5, "ASSAUT", _plafond] call MC7_fnc_debutPhase;

if (isNull MC7_gAssaut) then {
    MC7_gAssaut = MC7_gFS; MC7_gAssaut setVariable ["chacal_element", "ASSAUT_BLOC", true];
    if (count MC7_OUV_CHOISIE == 0) then { MC7_OUV_CHOISIE = MC7_OUVERTURES select 0 };
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
if (!isNil "MC7_POS_ASSAUT") then {
    private _a1 = [MC7_gAppui,   MC7_POS_APPUI,   130] call MC7_fnc_enPlace;
    private _a2 = [MC7_gAssaut,  MC7_POS_ASSAUT,  130] call MC7_fnc_enPlace;
    private _a3 = [MC7_gBouchon, MC7_POS_BOUCHON, 160] call MC7_fnc_enPlace;
    (format ["CHACAL|E|dispositif|%1|appui|%2|assaut|%3|bouchon|%4|vivants|%5", round (time * 100) / 100,
        (if (_a1) then {1} else {0}), (if (_a2) then {1} else {0}), (if (_a3) then {1} else {0}),
        count (MC7_FS select { alive _x })]) call MC7_LOG;

    if (!_a2 || { !_a1 }) then {
        // ! LA SECONDE CHANCE DOIT CHANGER QUELQUE CHOSE. Le premier jet
        // rejouait les memes ordres au meme pas et rendait le meme resultat -
        // `appui|1|assaut|0|bouchon|0` avant comme apres - en brulant 45 % de la
        // phase pour rien. Si l assaut est a plus de 400 m, aucun re-envoi ne le
        // ramenera dans le temps qui reste : on renonce d emblee et on le dit.
        private _uA = (units MC7_gAssaut) select { alive _x };
        private _dA = if (count _uA > 0) then { (_uA call MC7_fnc_centre) distance2D MC7_POS_ASSAUT } else { 9999 };
        if (_dA > 400) exitWith {
            (format ["CHACAL|E|rearticulation|%1|refusee|assaut_a|%2|trop_loin", round (time * 100) / 100, round _dA]) call MC7_LOG;
        };
        (format ["CHACAL|E|rearticulation|%1|cause|DISPOSITIF_ECLATE|assaut_a|%2", round (time * 100) / 100, round _dA]) call MC7_LOG;
        private _b = ([MC7_gAssaut, MC7_POS_ASSAUT] call MC7_fnc_budgetDeuxJambes) min (_plafond * 0.45);
        private _hA = [MC7_gAssaut, MC7_POS_ASSAUT, 130, _b, "ASSAUT_REPRISE"] spawn MC7_fnc_rejoindre;
        [MC7_gAppui,   MC7_POS_APPUI,   "NORMAL", "AWARE", "LINE",  "REARTICULATION"] call MC7_fnc_ordreAller;
        [MC7_gBouchon, MC7_POS_BOUCHON, "NORMAL", "AWARE", "WEDGE", "REARTICULATION"] call MC7_fnc_ordreAller;
        waitUntil { sleep 3; scriptDone _hA || MC7_FIN };
        _a1 = [MC7_gAppui,   MC7_POS_APPUI,   130] call MC7_fnc_enPlace;
        _a2 = [MC7_gAssaut,  MC7_POS_ASSAUT,  130] call MC7_fnc_enPlace;
        _a3 = [MC7_gBouchon, MC7_POS_BOUCHON, 160] call MC7_fnc_enPlace;
        (format ["CHACAL|E|dispositif|%1|apres_rearticulation|appui|%2|assaut|%3|bouchon|%4|vivants|%5",
            round (time * 100) / 100, (if (_a1) then {1} else {0}), (if (_a2) then {1} else {0}),
            (if (_a3) then {1} else {0}), count (MC7_FS select { alive _x })]) call MC7_LOG;
    };

    if (!_a2) then {
        _renonce = true; MC7_ABANDON = true;
        MC7_CAUSE_ABANDON = "ARTICULATION_ROMPUE";
        (format ["CHACAL|E|renoncement|%1|cause|ARTICULATION_ROMPUE|vivants|%2", round (time * 100) / 100,
            count (MC7_FS select { alive _x })]) call MC7_LOG;
    };
};

// ! LA RESTITUTION REMPLACE LE `reveal` EN GROS. Le premier jet revelait toutes
// les sentinelles a tout l appui - or TIREUR_2 etait en cache a 900 m et n avait
// rien observe : le reveal lui donnait une connaissance jamais gagnee. Et la
// scission avait de toute facon detruit la liste de cibles du groupe de reco.
// Ici on ne restitue QUE ce que la reco a vu, QU AUX hommes qui l ont vu, et au
// niveau observe. Le compte est journalise : N restituees sur M localisees.
// ! L ORACLE : la connaissance se rafraichit au debut de l assaut, pour tous nos hommes.
if (MC7_ORACLE >= 1) then {
    private _def = MC7_EST_SITE select { alive _x };
    { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (MC7_FS select { alive _x });
    (format ["CHACAL|E|oracle|%1|reveles|%2|phase|5", round (time * 100) / 100, count _def]) call MC7_LOG;
};
private _recoHommes = MC7_RECO call MC7_fnc_role;
private _restitue = 0;
{
    _x params ["_cible", "_k"];
    if (alive _cible) then {
        { _x reveal [_cible, _k min 2] } forEach _recoHommes;
        _restitue = _restitue + 1;
    };
} forEach MC7_VUES;
(format ["CHACAL|E|restitution|%1|restituees|%2|localisees|%3|destinataires|%4", round (time * 100) / 100,
    _restitue, count MC7_VUES, count _recoHommes]) call MC7_LOG;

// L assaut ne renonce plus faute de renseignement : il part avec ce qu il a et
// la pauvrete est une CONDITION journalisee. Seule la compromission ou une
// articulation rompue arretent la mission.
if (_restitue == 0 && !_renonce) then {
    (format ["CHACAL|E|renseignement_pauvre|%1|restituees|0|l_assaut_part_par_l_ouverture_par_defaut", round (time * 100) / 100]) call MC7_LOG;
};

if (_renonce) then {
    [5, "ASSAUT", MC7_CAUSE_ABANDON] call MC7_fnc_finPhase;
} else {

if (!isNull MC7_gAppui) then {
    MC7_gAppui setBehaviour "COMBAT"; MC7_gAppui setCombatMode (if (MC7_APPUI_FIXE == 1) then {"YELLOW"} else {"RED"}); MC7_gAppui setSpeedMode "LIMITED";
    private _cibles = (MC7_VUES apply { _x select 0 }) select { alive _x };
    { if (alive _x && { count _cibles > 0 }) then { _x doTarget (_cibles select 0); _x doFire (_cibles select 0) } } forEach (units MC7_gAppui);
};

// ! CONTROLE POSITIF DE L APPUI : l episode ne mesure QUE l appui et se ferme ici. L exitWith est indispensable :
// sans lui, toute la suite de la phase 5 s ecrirait APRES la ligne FINI et la porte de lecture refuserait l episode.
if (MC7_BANC_APPUI > 0) exitWith {
    call MC7_fnc_bancAppui;
    [5, "ASSAUT", "BANC_APPUI"] call MC7_fnc_finPhase;
    MC7_FIN = true;
};
// ! LE SOCLE ET LA TACTIQUE ( document du 11/09 ). Le socle repare l execution, la tactique conduit l appui.
if (MC7_SOCLE == 1) then { call MC7_fnc_socleAssaut };
if (MC7_TACTIQUE == 5) then {
    // T5 : personne ne tire tant que rien ne nous tire dessus. A la premiere balle, on bascule en T1.
    { if (!isNull _x) then { _x setCombatMode "GREEN" } } forEach [MC7_gAppui, MC7_gAssaut, MC7_gBouchon];
    MC7_gAssaut setBehaviour "STEALTH";
    [] spawn {
        waitUntil { sleep 2; MC7_FIN || { MC7_PHASE != 5 } || { count MC7_CONNUS > 0 } || MC7_COMPROMIS };
        if (MC7_FIN || { MC7_PHASE != 5 }) exitWith {};
        MC7_TACTIQUE = 1;
        { if (!isNull _x) then { _x setCombatMode "RED" } } forEach [MC7_gAppui, MC7_gBouchon];
        MC7_gAssaut setBehaviour "AWARE"; MC7_gAssaut setCombatMode "YELLOW";
        (format ["CHACAL|E|bascule_t5_vers_t1|%1|connus|%2|compromis|%3", round (time * 100) / 100,
            count MC7_CONNUS, (if (MC7_COMPROMIS) then {1} else {0})]) call MC7_LOG;
    };
};
if (MC7_TACTIQUE > 0) then { [] spawn MC7_fnc_tactiqueAppui };
if (MC7_SOCLE == 1 && { !(1 call MC7_fnc_sans) }) then { [] spawn MC7_fnc_chienDeGarde };
// L assaut attend : T1 le premier coup de l appui ( 120 s au plus ), T2 qu il ne reste au plus qu un defenseur ( 8 min ).
if (MC7_TACTIQUE == 1) then {
    private _tA = time;
    waitUntil { sleep 1; (MC7_T_PREMIER_TIR_APPUI > 0) || { time - _tA > 120 } || MC7_FIN };
    sleep 5;
    (format ["CHACAL|E|t1_depart|%1|premier_tir_appui|%2|attente|%3", round (time * 100) / 100,
        round MC7_T_PREMIER_TIR_APPUI, round (time - _tA)]) call MC7_LOG;
};
if (MC7_TACTIQUE == 2) then {
    private _tA = time;
    waitUntil { sleep 2; (count (MC7_EST_SITE select { alive _x }) <= 1) || { time - _tA > 480 } || MC7_FIN };
    (format ["CHACAL|E|t2_depart|%1|defenseurs_restants|%2|attente|%3", round (time * 100) / 100,
        count (MC7_EST_SITE select { alive _x }), round (time - _tA)]) call MC7_LOG;
};

// ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ). Sur les echecs du palier 4, un seul fusilier
// fait 8 des 9 morts et l appui ne tire pas : il visait une cible qu il ne connaissait pas.
// Le compteur tourne dans les deux bras ; la designation et l attente seulement a FEU_AVANT = 1.
MC7_TIRS_APPUI = 0; MC7_T_PREMIER_TIR = -1; MC7_CIBLE_ASSAUT = []; MC7_RELANCES = 0;
if (!isNull MC7_gAppui) then {
    {
        _x addEventHandler ["Fired", {
            MC7_TIRS_APPUI = MC7_TIRS_APPUI + 1;
            if (MC7_T_PREMIER_TIR < 0) then { MC7_T_PREMIER_TIR = time };
        }];
    } forEach ((units MC7_gAppui) select { alive _x });
};
if (MC7_FEU_AVANT == 1 && { !isNull MC7_gAppui }) then {
    [] spawn {
        while { !MC7_FIN && { MC7_PHASE == 5 } } do {
            private _def = MC7_EST_SITE select { alive _x };
            private _ref = if (count MC7_CIBLE_ASSAUT > 0) then { MC7_CIBLE_ASSAUT } else { MC7_OUV_CHOISIE };
            if (count _def > 0) then {
                _def = [_def, [_ref], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
                private _c = _def select 0;
                {
                    private _u = _x;
                    if (alive _u) then {
                        { _u reveal [_x, 4] } forEach _def;
                        _u doTarget _c; _u doFire _c;
                    };
                } forEach (units MC7_gAppui);
            };
            sleep 5;
        };
    };
    private _tG = time;
    waitUntil { sleep 1; (MC7_TIRS_APPUI > 0) || { (time - _tG) > (120 * MC7_ECHELLE) } || { MC7_FIN } };
    (format ["CHACAL|E|feu_avant|%1|premier_tir|%2|attente|%3|defenseurs_vivants|%4", round (time * 100) / 100,
        (if (MC7_T_PREMIER_TIR < 0) then {-1} else {round (MC7_T_PREMIER_TIR * 100) / 100}),
        round (time - _tG), count (MC7_EST_SITE select { alive _x })]) call MC7_LOG;
};
sleep (8 * MC7_ECHELLE);

if (!isNull MC7_gBouchon) then {
    MC7_gBouchon setBehaviour "COMBAT"; MC7_gBouchon setCombatMode "RED";
    { if (alive _x) then { _x setUnitPos "MIDDLE" } } forEach (units MC7_gBouchon);
};

// ! LE DETACHEMENT DES DEMOLISSEURS EST SUPPRIME ( Fable, 05/09 ).
// Je les avais sortis du groupe d assaut pour qu un `taskCQB` n ecrase pas leur
// `doMove`. Resultat mesure : deux hommes seuls traversant une garnison en
// alerte, tues a 80 s d intervalle, zero charge. On ne repare pas ca en
// changeant leur comportement - on cesse de les separer. L assaut avance d un
// seul corps, et les charges sont portees par les cinq.

// ! V5 ( Fable, 11/09 ) : une mitrailleuse dans l assaut. L ADJOINT echange son fusil contre une Mk200.
if (MC7_MG_ASSAUT == 1) then {
    private _mg = (units MC7_gAssaut) select { alive _x && { (_x getVariable ["chacal_role", ""]) == "ADJOINT" } };
    if (count _mg == 0) then { _mg = (units MC7_gAssaut) select { alive _x && { !((_x getVariable ["chacal_role", ""]) in ["DEMO_1", "DEMO_2"]) } } };
    if (count _mg > 0) then {
        private _u = _mg select 0;
        { _u removeMagazines _x } forEach (getArray (configFile >> "CfgWeapons" >> (primaryWeapon _u) >> "magazines"));
        _u removeWeapon (primaryWeapon _u);
        for "_i" from 1 to 3 do { _u addMagazine "200Rnd_65x39_cased_Box" };
        _u addWeapon "LMG_Mk200_F";
        (format ["CHACAL|E|mg_assaut|%1|role|%2|arme|%3|munitions_chargees|%4|chargeurs_sac|%5", round (time * 100) / 100,
            (_u getVariable ["chacal_role", ""]), primaryWeapon _u, _u ammo "LMG_Mk200_F",
            { _x == "200Rnd_65x39_cased_Box" } count (magazines _u)]) call MC7_LOG;
    } else { "CHACAL|AVERT|mg_assaut|aucun_tireur_disponible" call MC7_LOG };
};
// ! LE CHOIX DE LA PHASE 5 ( plans/plan-choix-par-vignette.md, 16/09 ) : combien de temps laisser au porteur.
// Force par le job ( delai_porteur ), ecrit comme une decision juste avant le premier pas de l assaut. La menace
// ALARME_AVANT_ASSAUT est posee par une tache qui regarde la phase toutes les 2 s : on attend son drapeau, 10 s au
// plus, sinon l observable alarme serait lu avant la pose.
if (MC7_MENACE_P5 in [2, 3]) then {
    private _tDec = time;
    waitUntil { sleep 0.5; (!isNil "MC7_SITUATION_P5_FAITE") || MC7_FIN || ((time - _tDec) > 10) };
};
if ((MC7_DELAI_MODE == 1) && { MC7_F_LEN > 0 }) then {
    // memes perceptions, memes calculs et meme instant que la ligne de decision ecrite juste apres
    private _defF = (if (isNil "MC7_EST_SITE") then {[]} else {MC7_EST_SITE}) select { alive _x };
    private _obsF = [
        (if (MC7_ALARME) then {1} else {0}),
        (if (MC7_T_ALARME >= 0) then { round (time - MC7_T_ALARME) } else { -1 }),
        (if (MC7_COMPROMIS) then {1} else {0}),
        count (MC7_FS select { alive _x }),
        { (west knowsAbout _x) > 1.4 } count _defF
    ];
    private _res = [0, _obsF] call MC7_fnc_evalNoeud;
    private _valF = _res select 0;
    MC7_DELAI_JOUE = if (_valF > 0) then {180} else {45};
    [5, "DELAI_PORTEUR", [45, 180], MC7_DELAI_JOUE, "FORMULE", format ["|valeur_formule|%1|codes_lus|%2|codes_attendus|%3", _valF, _res select 1, MC7_F_LEN]] call MC7_fnc_decision;
} else {
    [5, "DELAI_PORTEUR", [45, 180], MC7_DELAI_PORTEUR, "IMPOSE"] call MC7_fnc_decision;
};
// LE chiffre de Fable : les coups de l appui AVANT le premier pas de l assaut.
(format ["CHACAL|E|premier_pas_assaut|%1|tirs_appui_avant|%2|feu_avant|%3", round (time * 100) / 100,
    MC7_TIRS_APPUI, MC7_FEU_AVANT]) call MC7_LOG;
// ! Le mode COMBAT fige l assaut ( plus de 120 s immobile a 65 m de la tour ). A FEU_AVANT = 1 il
// marche en AWARE, et un ordre donne une seule fois est relance toutes les 10 s.
// Une tactique marche en AWARE : le mode COMBAT fige l assaut ( plus de 120 s mesurees a 65 m de la tour ).
MC7_COMP_ASSAUT = if (MC7_FEU_AVANT == 1 || { MC7_TACTIQUE > 0 }) then {"AWARE"} else {"COMBAT"};
MC7_gAssaut setBehaviour MC7_COMP_ASSAUT; MC7_gAssaut setCombatMode "RED"; MC7_gAssaut setSpeedMode "FULL";
MC7_CIBLE_ASSAUT = +MC7_OUV_CHOISIE;
[MC7_gAssaut, MC7_OUV_CHOISIE, "FULL", MC7_COMP_ASSAUT, "WEDGE", "OUVERTURE_CHOISIE"] call MC7_fnc_ordreAller;
if (MC7_FEU_AVANT == 1 || { MC7_TACTIQUE > 0 }) then {
    [] spawn {
        while { !MC7_FIN && { MC7_PHASE == 5 } } do {
            sleep 10;
            if (count MC7_CIBLE_ASSAUT > 0 && { !isNull MC7_gAssaut }) then {
                MC7_gAssaut setBehaviour "AWARE";
                { if (alive _x) then { _x doMove MC7_CIBLE_ASSAUT } } forEach (units MC7_gAssaut);
                MC7_RELANCES = MC7_RELANCES + 1;
            };
        };
    };
};
// Sans cette ligne, un `ELEMENT_N_ARRIVE_PAS` sur la premiere antenne serait
// indiscernable d un assaut reste a 200 m de l enceinte.
private _rO = [MC7_gAssaut, MC7_OUV_CHOISIE, 55, [MC7_gAssaut, MC7_OUV_CHOISIE, 1.2] call MC7_fnc_budget] call MC7_fnc_arrive;
(format ["CHACAL|E|ouverture|%1|issue|%2|distance|%3|reste|%4", round (time * 100) / 100, _rO,
    round ((((units MC7_gAssaut) select { alive _x }) call MC7_fnc_centre) distance2D MC7_OUV_CHOISIE),
    round (call MC7_fnc_reste)]) call MC7_LOG;

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
private _ordre = MC7_OBJETS select { _x != MC7_PC };
_ordre = [_ordre, [], { _x distance2D MC7_OUV_CHOISIE }, "ASCEND"] call BIS_fnc_sortBy;
if (!isNull MC7_PC) then { _ordre pushBack MC7_PC };
// origines_z : le z minimal de la boite englobante. Proche de 0 = origine au
// sol ; tres negatif = origine en hauteur, et l objet est a moitie enterre.
(format ["CHACAL|E|file_objectifs|%1|%2|origines_z|%3", round (time * 100) / 100,
    (_ordre apply { typeOf _x }),
    (_ordre apply { round ((((boundingBoxReal _x) select 0) select 2) * 10) / 10 })]) call MC7_LOG;

// ! `taskCQB` SORT DE LA FILE ( Fable, 06/09 ). Lance en meme temps que l ordre
// de pose, il combat tout ce qui le suit : LAMBS donne ses propres `doMove` sur
// son cycle, et un homme sous `doMove` ignore le waypoint de groupe du
// degagement. Les cinq morts du passage 4 ont ete poses PENDANT un CQB.
// Le nettoyage redeviendra une etape separee, avec son propre controle.
"CHACAL|E|cqb|differe|le_nettoyage_est_une_etape_separee" call MC7_LOG;

private _hExpl = scriptNull;
{
    private _o = _x;
    if (MC7_FIN || { !alive _o }) then { continue };
    if (count ((units MC7_gAssaut) select { alive _x }) == 0) then {
        (format ["CHACAL|E|file_interrompue|%1|restants|0", round (time * 100) / 100]) call MC7_LOG;
        continue
    };
    // ! L HORLOGE DE PHASE ENTRE DANS LA FILE. Trois objectifs a 360 s font
    // 1 080 s pour une phase de 900, et le `waitUntil` final attendait 900 s de
    // PLUS quand la file finissait a moins de 3/3 : le meilleur passage a
    // patiente quinze minutes immobile dans l enceinte.
    private _cap = (180 * MC7_ECHELLE) min ((call MC7_fnc_reste) - MC7_RESERVE_FEU);
    if (_cap <= 0) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|PLAFOND_PHASE", round (time * 100) / 100, typeOf _o]) call MC7_LOG;
        continue
    };
    private _pt = [_o] call MC7_fnc_pointDePose;
    (format ["CHACAL|E|objectif|%1|%2|point_de_pose|%3|emprise|%4|cap|%5", round (time * 100) / 100,
        typeOf _o, _pt, round (_o call MC7_fnc_emprise), round _cap]) call MC7_LOG;
    MC7_CIBLE_ASSAUT = +_pt;
    [MC7_gAssaut, _pt, "FULL", MC7_COMP_ASSAUT, "WEDGE", "OBJECTIF_" + (typeOf _o)] call MC7_fnc_ordreAller;
    private _r = [MC7_gAssaut, _pt, 22, _cap, 120] call MC7_fnc_arrive;
    private _c0 = ((units MC7_gAssaut) select { alive _x }) call MC7_fnc_centre;
    private _dG = if (count _c0 > 0) then { round (_c0 distance2D _pt) } else { 9999 };
    // ENLISE a 30 m suffit : le porteur fera les derniers metres seul
    if (_dG > 40) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|ELEMENT_N_ARRIVE_PAS|issue|%3|distance|%4",
            round (time * 100) / 100, typeOf _o, _r, _dG]) call MC7_LOG;
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
    if (_o isEqualTo MC7_PC) then {
        "CHACAL|E|exploitation|differee|controle_positif_manquant" call MC7_LOG;
    };

    private _porteurs = (units MC7_gAssaut) select { alive _x && { "DemoCharge_Remote_Mag" in (magazines _x) } };
    if (count _porteurs == 0) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|AUCUN_PORTEUR_VIVANT", round (time * 100) / 100, typeOf _o]) call MC7_LOG;
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
    waitUntil { sleep 1; ((_h distance2D _pt) < 5) || !(alive _h) || (time - _t > MC7_DELAI_JOUE * MC7_ECHELLE) || MC7_FIN };
    private _dH = round (_h distance2D _pt);
    (format ["CHACAL|E|porteur|%1|%2|%3|temps|%4|distance|%5|delai|%6", round (time * 100) / 100, typeOf _o,
        (_h getVariable ["chacal_role", ""]), round (time - _t), _dH, MC7_DELAI_JOUE]) call MC7_LOG;
    if (!alive _h || { _dH > 12 }) then {
        (format ["CHACAL|E|charge_manquee|%1|%2|cause|PORTEUR_N_ARRIVE_PAS|%3|distance|%4", round (time * 100) / 100,
            typeOf _o, (_h getVariable ["chacal_role", ""]), _dH]) call MC7_LOG;
        if (alive _h && { _h != leader MC7_gAssaut }) then { _h doFollow (leader MC7_gAssaut) };
        continue
    };
    sleep (4 * MC7_ECHELLE);   // le geste a une duree
    private _c = createVehicle ["DemoCharge_Remote_Ammo", _pt getPos [3, _pt getDir _o], [], 0, "CAN_COLLIDE"];
    _h removeMagazine "DemoCharge_Remote_Mag";
    MC7_CHARGES pushBackUnique _o;
    MC7_CHARGES_OBJ pushBack [_o, _c];
    (format ["CHACAL|E|charge_posee|%1|%2|par|%3|distance|%4|actes|%5|sur|%6", round (time * 100) / 100,
        typeOf _o, (_h getVariable ["chacal_role", ""]), _dH, count MC7_CHARGES, count MC7_OBJETS]) call MC7_LOG;
    if (_h != leader MC7_gAssaut) then { _h doFollow (leader MC7_gAssaut) };
} forEach _ordre;

// --- l exploitation est coupee AVANT le degagement ---
if (!isNull _hExpl) then {
    private _tX = time;
    waitUntil { sleep 2; scriptDone _hExpl || (time - _tX > 90 * MC7_ECHELLE) || MC7_FIN };
    if (!scriptDone _hExpl) then { terminate _hExpl };
    if (alive MC7_EXPLOITANT) then { MC7_EXPLOITANT doFollow (leader MC7_gAssaut) };
};

// --- UN SEUL degagement, puis TOUT saute ensemble ---
private _abri = MC7_OUV_CHOISIE getPos [70, MC7_SITE getDir MC7_OUV_CHOISIE];
MC7_CIBLE_ASSAUT = +_abri;
[MC7_gAssaut, _abri, "FULL", MC7_COMP_ASSAUT, "WEDGE", "DEGAGEMENT_AVANT_MISE_A_FEU"] call MC7_fnc_ordreAller;
(format ["CHACAL|E|degagement|%1|vers|%2|charges|%3", round (time * 100) / 100, _abri, count MC7_CHARGES_OBJ]) call MC7_LOG;
private _rD = [MC7_gAssaut, _abri, 30, ((call MC7_fnc_reste) - 60) max 45, 60] call MC7_fnc_arrive;
[_rD] call MC7_fnc_miseAFeu;

// ! INCOMPLET est nouveau : la file s est terminee AVANT le plafond, et chaque
// manque porte sa cause. Ce n est pas un plafond, il ne faut pas l appeler ainsi.
private _iss5 = if (count MC7_CHARGES >= count MC7_OBJETS) then {"ATTEINT"} else {
    if (count (MC7_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if ((call MC7_fnc_reste) <= 0) then {"PLAFOND"} else {"INCOMPLET"} } };
(format ["CHACAL|E|feu_appui_total|%1|tirs_appui|%2|relances_assaut|%3|feu_avant|%4", round (time * 100) / 100,
    MC7_TIRS_APPUI, MC7_RELANCES, MC7_FEU_AVANT]) call MC7_LOG;
[5, "ASSAUT", _iss5] call MC7_fnc_finPhase;
};
};

// ---------------------------------------------------------------------
// PHASE 6 - RUPTURE ET EXFILTRATION
// ---------------------------------------------------------------------
// ! Sur ABANDON le detachement etait envoye au point de secours situe DERRIERE
// le site : il devait contourner l objectif qu il venait de renoncer a
// attaquer. On se replie par ou l on est venu. Et le plafond se calcule depuis
// la position REELLE des SURVIVANTS - `MC7_gFS` est vide depuis la scission,
// et la fonction rendait alors son defaut de 120 s pour 4 km a parcourir.
if (MC7_FIN) exitWith {};   // vignette close avant l exfiltration
MC7_EXFIL_POINT = if (MC7_ABANDON) then { MC7_LZ } else { MC7_PZ };
private _vitBudget = if (MC7_EXFIL == 2) then {1.2} else {1.8};
_plafond = [(MC7_FS select { alive _x }), MC7_EXFIL_POINT, _vitBudget] call MC7_fnc_budget;
[6, "EXFILTRATION", _plafond] call MC7_fnc_debutPhase;
// ! LE CHOIX DE LA PHASE 6 ( plans/plan-choix-par-vignette.md, 17/09 ) : repli prudent ( EXFIL = 0 : le comportement du
// detachement tout du long ) ou rapide ( EXFIL = 1 : rompre en COMBAT puis AWARE et FULL au-dela de 200 m ). Ecrit a
// chaque exfiltration, comme le delai du porteur a chaque assaut. Remplace le choix principale / secours du plan :
// il n existe pas de second point d extraction dans la mission.
if (MC7_EXFIL in [0, 1]) then {
    private _vD6 = MC7_FS select { alive _x };
    private _dD6 = if (count _vD6 > 0) then { round ((_vD6 call MC7_fnc_centre) distance2D MC7_EXFIL_POINT) } else { -1 };
    [6, "EXFIL_ALLURE", [0, 1], MC7_EXFIL, "IMPOSE", format ["|distance_point|%1", _dD6]] call MC7_fnc_decision;
};
(format ["CHACAL|E|budget|%1|etape|EXFIL|vers|%2|distance|%3|plafond|%4", round (time * 100) / 100,
    (if (MC7_ABANDON) then {"LZ"} else {"PZ"}),
    round (((MC7_FS select { alive _x }) call MC7_fnc_centre) distance2D MC7_EXFIL_POINT),
    round _plafond]) call MC7_LOG;

private _pourquoi = if (MC7_ABANDON) then {"ABANDON_REPLI_PAR_LA_LZ"} else {"OBJECTIFS_TRAITES"};
// ! Un detachement qui n est PAS compromis ne rompt pas le contact, il s en va.
// En COMBAT sur 1,4 a 2,4 km, 1,8 m/s de moyenne n est pas garanti meme sans
// ennemi : l issue serait EXFIL_MANQUEE sur un detachement intact.
// l appui fixe est rendu a ses jambes pour rentrer
// ! ON REND LES JAMBES A TOUT LE MONDE, SANS CONDITION ( 13/09 ).
// L ancienne ligne ne liberait l appui QUE si MC7_APPUI_FIXE valait 1. Or le socle le cloue par sa
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
} forEach [MC7_gAssaut, MC7_gAppui, MC7_gBouchon, MC7_gReco, MC7_gFS];
// ! LA GARDE QUI MANQUAIT. Aucune porte du lecteur ne verifiait qu un homme VIVANT peut marcher, et
// c est pourquoi ce defaut a traverse quinze portes vertes et trois campagnes. On compte, et on ecrit.
MC7_SANS_JAMBES = 0;
{ if (alive _x && { !(_x checkAIFeature "PATH") }) then { MC7_SANS_JAMBES = MC7_SANS_JAMBES + 1 } } forEach MC7_FS;
(format ["CHACAL|E|exfil_jambes|%1|vivants|%2|sans_path|%3|seuil_exige|%4", round (time * 100) / 100,
    count (MC7_FS select { alive _x }), MC7_SANS_JAMBES, round (0.6 * MC7_EFFECTIF)]) call MC7_LOG;
if (MC7_SANS_JAMBES > 0) then {
    (format ["CHACAL|AVERT|exfil|hommes_vivants_sans_jambes|%1", MC7_SANS_JAMBES]) call MC7_LOG;
};
private _compExf = if (MC7_COMPROMIS) then {"COMBAT"} else {"AWARE"};
if (MC7_EXFIL in [0, 1]) then {
    (format ["CHACAL|E|choix_joue|%1|point|EXFIL_ALLURE|choix|%2|detail|%3|comportement_initial|%4", round (time * 100) / 100,
        MC7_EXFIL, (if (MC7_EXFIL == 1) then {"RAPIDE"} else {"PRUDENT"}), _compExf]) call MC7_LOG;
};
// ! EXFIL=1 : on rompt le contact en COMBAT, puis on rend les jambes. La recolte du moteur du
// 13/09 dit que le chemin se calcule en fonction du comportement ; un homme en COMBAT ne prend
// pas le meme itineraire. Des que le detachement est a plus de 300 m du site, il repasse en
// AWARE. Le plafond ne bouge pas : c est le comportement qu on mesure, pas le chronometre.
if (MC7_EXFIL == 1) then {
    [] spawn {
        private _t0 = time;
        waitUntil { sleep 5;
            private _v = MC7_FS select { alive _x };
            (count _v == 0) || MC7_FIN || ((time - _t0) > 180) ||
            ((_v call MC7_fnc_centre) distance2D MC7_SITE > 200) };
        if (MC7_FIN) exitWith {};
        private _v = MC7_FS select { alive _x };
        if (count _v == 0) exitWith {};
        { if (!isNull _x) then { _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
            { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x) } }
          forEach [MC7_gAssaut, MC7_gAppui, MC7_gBouchon, MC7_gReco, MC7_gFS];
        (format ["CHACAL|E|exfil_degage|%1|distance_site|%2|vivants|%3|comportement|AWARE",
            round (time * 100) / 100, round ((_v call MC7_fnc_centre) distance2D MC7_SITE),
            count _v]) call MC7_LOG;
    };
};
{
    if (!isNull _x) then {
        _x setBehaviour _compExf; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";
        { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x);
        [_x, MC7_EXFIL_POINT, "FULL", _compExf, "WEDGE", _pourquoi] call MC7_fnc_ordreAller;
    };
} forEach [MC7_gAssaut, MC7_gAppui, MC7_gBouchon, MC7_gReco, MC7_gFS];

private _tE = time;
private _seuilExf = round (0.6 * MC7_EFFECTIF);
// ! LE CRITERE PORTE SUR L EFFECTIF, PAS SUR LES SURVIVANTS ( 13/09 ). S il reste moins d hommes
// vivants que le seuil, la condition de sortie ne peut JAMAIS etre vraie : la phase brulait son
// plafond entier, une vingtaine de minutes, pour conclure PLAFOND. C est un critere hors d atteinte,
// la meme famille que arret=5 et le seuil 3 de la phase 3. On sort tout de suite, et on le DIT.
waitUntil { sleep 3;
    (count (MC7_FS select { alive _x && { (_x distance2D MC7_EXFIL_POINT) < 90 } }) >= _seuilExf) ||
    (count (MC7_FS select { alive _x }) < _seuilExf) || (time - _tE > _plafond) || MC7_FIN };
private _vivExf = count (MC7_FS select { alive _x });
if (_vivExf < _seuilExf) then {
    (format ["CHACAL|E|exfil_impossible|%1|vivants|%2|seuil|%3|temps_ecoule|%4", round (time * 100) / 100,
        _vivExf, _seuilExf, round (time - _tE)]) call MC7_LOG;
};
MC7_EXFILTRES = count (MC7_FS select { alive _x && { (_x distance2D MC7_EXFIL_POINT) < 90 } });
[6, "EXFILTRATION", (if (MC7_EXFILTRES >= _seuilExf) then {"ATTEINT"} else {
    if (count (MC7_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if (count (MC7_FS select { alive _x }) < _seuilExf) then {"PERTES_EXCESSIVES"} else {"PLAFOND"} } })] call MC7_fnc_finPhase;

MC7_FIN = true;
};
