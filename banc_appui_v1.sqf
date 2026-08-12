// banc_appui.sqf — L'APPUI-FEU FIGE-T-IL VRAIMENT LE DÉFENSEUR ?
//
// ⟨Fable, 08/08, geste n°2⟩ « Le risque propre : que l'appui arrose sans supprimer. Vérifie
// SUR PIÈCES, AVANT la chasse aux lieux, que la mécanique mord. Si l'appui ne réduit pas la
// riposte, aucun terrain ne sauvera la mission. »
//
// CE QUI EST DÉJÀ CERTIFIÉ ⟨courbe 2, 05/08⟩ : sous le feu il reste 8 % de la capacité de
// nuire — mesuré par `HitPart`, pas par `HandleDamage`. Mais c'était dans la SANDBOX. Ici on
// demande à Arma, avec ce modset (LAMBS + PinnedDown), si l'effet existe encore.
//
// LE DISPOSITIF. Terrain plat, hors de tout lieu certifié — on teste la MÉCANIQUE, pas un
// terrain. Trois corps, tous invulnérables et immobiles :
//   · 6 DÉFENSEURS, cap nord, libres de tirer. Ils sont la grandeur mesurée.
//   · 4 VICTIMES à 150 m plein nord, dans leur cône, qui NE TIRENT PAS. Elles donnent aux
//     défenseurs quelque chose à viser — identiquement dans les deux bras.
//   · 3 APPUIS à 150 m, à 90° de l'axe des victimes.
//
// LES DEUX BRAS NE DIFFÈRENT QUE PAR UNE CHOSE : l'appui tire, ou l'appui se tait. Mêmes
// corps, mêmes places, même exposition, même révélation. ⟨la règle de Fable : le déclencheur
// dit QUAND le feu commence, jamais COMMENT il se comporte ensuite⟩
//
// POURQUOI TOUT LE MONDE EST INVULNÉRABLE : si l'appui tuait des défenseurs, on mesurerait
// « moins de défenseurs », pas « des défenseurs figés ». Si les victimes mouraient, les
// défenseurs cesseraient de tirer faute de cible, et pas du tout à cause de l'appui.
//
// GRANDEUR : coups tirés par les 6 défenseurs pendant 120 s. Second relevé : `getSuppression`.
//
// LA PORTE, DÉPOSÉE AVANT : l'appui doit faire tomber la cadence des défenseurs d'au moins
// 30 %. Ce seuil est VOLONTAIREMENT INDULGENT — le fait certifié en prédit 92. Un banc qui
// échouerait à 30 % dirait que la mécanique ne mord pas du tout ici, et le geste n°2 tombe.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE POSITIF : dans le bras APPUI, les appuis doivent RÉELLEMENT tirer. Zéro coup
//     compté = essai nul, on ne compare rien. ⟨la leçon de banc_tir : « 0 coup » en valait 21⟩
//   · CONTRÔLE D'ARRIVÉE — ajouté après le premier couple d'essais, qui était ILLISIBLE sans
//     lui : 542 coups partis, 440 contre 500 en riposte, et rien pour dire si les balles
//     ARRIVAIENT. « L'appui arrose sans supprimer » et « je tirais à côté » se confondaient,
//     et c'est précisément ce que ce banc doit trancher.
//     LE CONTRÔLE EST `HitPart` : une balle qui touche le corps est une balle arrivée. À
//     150 m sur des hommes debout et immobiles, quelques centaines de coups DOIVENT en
//     produire. Zéro touche = je tire à côté, et le banc ne dit rien sur la suppression.
//     ⚠️ `FiredNear` est journalisé mais NE PROUVE PAS l'arrivée : il se déclenche quand une
//     arme part PRÈS de l'unité (portée ~500 m), pas quand une balle la frôle. Il sera non
//     nul dans le bras appui quoi qu'il arrive. Écrit ici pour que personne ne le lise
//     comme une preuve d'arrivée — moi le premier, dans deux jours.
//   · CONTRÔLE NUL : dans le bras TÉMOIN, les appuis doivent tirer ZÉRO coup.
//   · CONTRÔLE DE PRÉSENCE : dans le bras TÉMOIN, les défenseurs doivent tirer. S'ils ne
//     tirent pas non plus sans appui, le dispositif est cassé — ce n'est pas de la suppression.
//     IL A DÉJÀ SERVI : le 08/08 à 20 h 53, bras témoin à ZÉRO coup. Le site « plat » retenu
//     masquait la vue entre défenseurs et victimes — un sol plat n'est pas un sol dégagé, les
//     buissons ne sont pas dans l'altitude. D'où deux ajouts : la ligne de vue est vérifiée
//     AVANT de placer les corps, et un essai témoin de PRÉ-VOL décide si le banc a le droit
//     de commencer. PUIS UNE SECONDE FOIS, le 08/08 à 21 h 01 : la ligne de vue vérifiée
//     était DÉFENSEUR -> VICTIME, celle dont le contrôle avait besoin. Celle dont la MESURE
//     a besoin — APPUI -> DÉFENSEUR — ne l'était pas : 368 coups, zéro impact, riposte
//     inchangée. Les deux vues sont désormais exigées ensemble.
//   · EFFECTIF CONSTANT : 6 défenseurs et 4 victimes vivants à la fin de CHAQUE essai. Un
//     seul mort et l'essai est jeté.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|AP|debut|1" call HMT_LOG;

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

    // ⚠️ LA LIGNE DE VUE, VERIFIEE AVANT DE PLACER QUI QUE CE SOIT.
    // Le premier jet ne verifiait que la HAUTEUR du terrain. Il a rendu un site « plat » ou
    // les defenseurs ne voyaient pas les victimes : bras temoin a ZERO coup tire. Le controle
    // de presence l a attrape, et le banc ne disait plus rien du tout sur la suppression.
    // Un sol plat n est pas un sol degage — les buissons ne sont pas dans l altitude.
    // DEUX lignes de vue, pas une. La premiere version n a verifie que DEFENSEUR -> VICTIME —
    // celle dont le CONTROLE DE PRESENCE a besoin — et a oublie APPUI -> DEFENSEUR, celle dont
    // la MESURE a besoin. Resultat sur le site suivant : 368 coups d appui, ZERO impact, et
    // une riposte inchangee. Les appuis tiraient dans un buisson. Un banc peut avoir la vue
    // qu il faut pour ses controles et pas celle qu il faut pour sa question.
    HMT_VUE = {
        params ["_b"];
        private _ok = 0; private _tot = 0;          // defenseur -> victime (plein nord)
        {
            private _dx = _x;
            {
                _tot = _tot + 1;
                private _p1 = AGLToASL (_b vectorAdd [_dx, 0, 1.5]);
                private _p2 = AGLToASL (_b vectorAdd [_x, 150, 1.5]);
                if (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1]) == 0)
                    then { _ok = _ok + 1 };
            } forEach [-15, -5, 5, 15];
        } forEach [-40, -24, -8, 8, 24, 40];
        private _ok2 = 0; private _tot2 = 0;        // appui -> defenseur (plein est)
        {
            private _ax = _x;
            {
                _tot2 = _tot2 + 1;
                private _p1 = AGLToASL (_b vectorAdd [150, _ax, 1.5]);
                private _p2 = AGLToASL (_b vectorAdd [_x, 0, 1.5]);
                if (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1]) == 0)
                    then { _ok2 = _ok2 + 1 };
            } forEach [-40, -24, -8, 8, 24, 40];
        } forEach [-10, 0, 10];
        [_ok, _tot, _ok2, _tot2]
    };
    private _v = [_base] call HMT_VUE;
    (format ["HMT|AP|terrain|%1|%2|tol|%3|vueDV|%4|sur|%5|vueAD|%6|sur|%7",
             round (_base select 0), round (_base select 1), _tol,
             _v select 0, _v select 1, _v select 2, _v select 3]) call HMT_LOG;

    // on redemande un site tant que la vue n est pas franche — et on ABANDONNE plutot que de
    // mesurer sur un site aveugle. ⟨une mesure doit savoir echouer⟩
    private _essais = 0;
    while { ((_v select 0) < 20 || (_v select 2) < 15) && _essais < 900 } do {
        _essais = _essais + 1;
        private _c = [1200 + random 4200, 4200 + random 3000, 0];
        if (!(surfaceIsWater _c) && {(getTerrainHeightASL _c) > 2}) then {
            private _h = getTerrainHeightASL _c; private _pl = true;
            { if (abs ((getTerrainHeightASL (_c vectorAdd _x)) - _h) > 14) then { _pl = false } }
              forEach [[0,160,0],[0,-60,0],[160,0,0],[-160,0,0]];
            if (_pl) then {
                private _w = [_c] call HMT_VUE;
                // on retient sur la SOMME des deux vues : un site excellent d un cote et
                // aveugle de l autre ne vaut rien.
                if (((_w select 0) + (_w select 2)) > ((_v select 0) + (_v select 2)))
                    then { _base = _c; _v = _w };
            };
        };
    };
    (format ["HMT|AP|site|%1|%2|vueDV|%3|sur|%4|vueAD|%5|sur|%6|essais|%7",
             round (_base select 0), round (_base select 1),
             _v select 0, _v select 1, _v select 2, _v select 3, _essais]) call HMT_LOG;
    if ((_v select 0) < 20 || (_v select 2) < 15) exitWith {
        (format ["HMT|AP|ECHEC|vue_insuffisante|DV|%1|sur|%2|AD|%3|sur|%4",
                 _v select 0, _v select 1, _v select 2, _v select 3]) call HMT_LOG;
    };

    // ---------------------------------------------------------------- les défenseurs
    private _gD = createGroup east;
    HMT_DEF = [];
    {
        private _p = _base vectorAdd [_x, 0, 0];
        private _u = _gD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "MOVE";       // immobiles, mais LIBRES de viser et tirer
        _u setBehaviour "COMBAT"; _u setCombatMode "RED";
        _u setUnitPos "UP"; _u setDir 0;
        _u setVariable ["ap_n", 0];
        _u setVariable ["ap_pres", 0];   // balles passees PRES : le controle qui manquait
        _u setVariable ["ap_touche", 0]; // balles qui ARRIVENT sur le corps
        _u addEventHandler ["Fired", { (_this select 0) setVariable ["ap_n", ((_this select 0) getVariable ["ap_n",0]) + 1] }];
        // ⚠️ SANS CECI, « l appui arrose sans supprimer » et « l appui tire a cote » se
        // confondent — et le premier couple d essais (440 contre 500) etait ILLISIBLE.
        // `HitPart` est le vrai controle d arrivee ; `FiredNear` n est qu un signal de bruit.
        _u addEventHandler ["FiredNear", { (_this select 0) setVariable ["ap_pres", ((_this select 0) getVariable ["ap_pres",0]) + 1] }];
        _u addEventHandler ["HitPart", { private _v = (_this select 0) select 0;
            _v setVariable ["ap_touche", (_v getVariable ["ap_touche",0]) + 1] }];
        HMT_DEF pushBack _u;
    } forEach [-40, -24, -8, 8, 24, 40];
    sleep 3;
    (format ["HMT|AP|ligne|%1", count HMT_DEF]) call HMT_LOG;

    // ---------------------------------------------------------------- les victimes (cibles fixes)
    private _gV = createGroup west;
    HMT_VIC = [];
    {
        private _p = _base vectorAdd [_x, 150, 0];
        private _u = _gV createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT";
        _u disableAI "TARGET"; _u disableAI "AUTOTARGET"; _u disableAI "FSM";
        _u setCombatMode "BLUE"; _u setBehaviour "CARELESS";
        _u setUnitPos "UP"; _u setDir 180;
        HMT_VIC pushBack _u;
    } forEach [-15, -5, 5, 15];

    // ---------------------------------------------------------------- l'élément d'appui
    private _gA = createGroup west;
    HMT_APP = [];
    {
        private _p = _base vectorAdd [150, _x, 0];       // à 90° de l'axe des victimes
        private _u = _gA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _u setPosATL _p; _u allowDamage false;
        _u disableAI "PATH"; _u disableAI "MOVE"; _u disableAI "AUTOCOMBAT";
        _u disableAI "AUTOTARGET"; _u disableAI "FSM";
        // TARGET reste ACTIF : sans lui, doTarget ne fait pivoter personne et les balles
        // partent vers setDir. On ne coupe que l ouverture SPONTANEE du feu.
        _u setCombatMode "BLUE"; _u setBehaviour "CARELESS";
        _u setUnitPos "UP"; _u setDir 270;
        _u setVariable ["ap_n", 0];
        _u addEventHandler ["Fired", { (_this select 0) setVariable ["ap_n", ((_this select 0) getVariable ["ap_n",0]) + 1] }];
        HMT_APP pushBack _u;
    } forEach [-10, 0, 10];
    sleep 3;
    (format ["HMT|AP|corps|def|%1|vic|%2|app|%3",
             count HMT_DEF, count HMT_VIC, count HMT_APP]) call HMT_LOG;

    // ================================================================ un essai
    HMT_ESSAI = {
        params ["_bras", "_rep"];                       // _bras : 1 = appui, 0 = témoin
        private _T = 120;

        // remise à zéro, identique aux deux bras
        { _x setVariable ["ap_n", 0]; _x setVariable ["ap_pres", 0];
          _x setVariable ["ap_touche", 0]; _x setDir 0 } forEach HMT_DEF;
        // L APPUI EST REMIS AU SILENCE, PAS SEULEMENT REMIS A ZERO. Au premier run, un coup
        // s est echappe dans le bras temoin : la cible ordonnee au tour precedent survivait.
        // Le controle nul dit ZERO, depose avant — on supprime la cause plutot que d assouplir
        // le critere apres avoir vu la donnee.
        {
            _x setVariable ["ap_n", 0];
            _x doTarget objNull; _x doWatch objNull;
            _x setCombatMode "BLUE"; _x setBehaviour "CARELESS";
            // dans le bras temoin, l appui ne peut meme pas viser ; il retrouve la visee au
            // debut d un bras appui. Meme corps, meme place, meme exposition — seul le feu change.
            if (_bras == 0) then { _x disableAI "TARGET" } else { _x enableAI "TARGET" };
        } forEach HMT_APP;
        { private _d = _x; { _d forgetTarget _x } forEach (HMT_VIC + HMT_APP) } forEach HMT_DEF;
        sleep 5;
        // RÉVÉLATION IDENTIQUE : les défenseurs savent où sont les victimes, dans les deux bras.
        // C'est un déclencheur aveugle au bras — il dit QUAND ça commence, pas COMMENT ça se passe.
        { _gD reveal [_x, 4] } forEach HMT_VIC;
        sleep 2;

        // l'appui tire — ou se tait. C'EST LA SEULE DIFFÉRENCE ENTRE LES DEUX BRAS.
        private _feu = [_bras, _T] spawn {
            params ["_b", "_T"];
            if (_b == 0) exitWith {};
            private _t0 = time;
            while { time - _t0 < _T } do {
                // une cible tenue 3 s : le temps que l arme pivote reellement dessus
                private _c = HMT_DEF select (floor (random (count HMT_DEF)));
                { _x doWatch _c; _x doTarget _c } forEach HMT_APP;
                sleep 1.2;
                for "_k" from 1 to 4 do {
                    { _x forceWeaponFire [currentWeapon _x, currentWeaponMode _x] } forEach HMT_APP;
                    sleep 0.45;
                };
            };
        };

        // relevé de la suppression pendant la fenêtre
        private _sup = [];
        private _t0 = time;
        while { time - _t0 < _T } do {
            private _s = 0;
            { _s = _s + (getSuppression _x) } forEach HMT_DEF;
            _sup pushBack (_s / (count HMT_DEF));
            sleep 5;
        };
        waitUntil { scriptDone _feu };

        private _cD = 0; { _cD = _cD + (_x getVariable ["ap_n", 0]) } forEach HMT_DEF;
        private _cA = 0; { _cA = _cA + (_x getVariable ["ap_n", 0]) } forEach HMT_APP;
        private _sm = 0; { _sm = _sm + _x } forEach _sup;
        _sm = if (count _sup > 0) then { _sm / (count _sup) } else { -1 };
        private _vD = { alive _x } count HMT_DEF;
        private _vV = { alive _x } count HMT_VIC;

        private _pr = 0; { _pr = _pr + (_x getVariable ["ap_pres", 0]) } forEach HMT_DEF;
        private _to = 0; { _to = _to + (_x getVariable ["ap_touche", 0]) } forEach HMT_DEF;
        (format ["HMT|AP|essai|%1|%2|coupsdef|%3|coupsapp|%4|pres|%5|touche|%6|supp|%7|vivants|%8|%9",
                 _bras, _rep, _cD, _cA, _pr, _to, (round (_sm*1000))/1000, _vD, _vV]) call HMT_LOG;
        sleep 8;
    };

    // ================================================================ le plan
    // Bras alternés dans le même quart d'heure : mêmes conditions, aucune dérive de session
    // ne peut se ranger d'un seul côté. ⟨la règle des bras contemporains⟩
    // PRE-VOL : un essai temoin AVANT le plan. Si les defenseurs ne tirent pas alors que rien
    // ne les gene, le dispositif est casse et les 24 essais suivants ne mesureraient que ma
    // propre erreur. C est arrive une fois — on ne le laisse plus arriver en silence.
    [0, 0] call HMT_ESSAI;
    private _pre = 0; { _pre = _pre + (_x getVariable ["ap_n", 0]) } forEach HMT_DEF;
    if (_pre <= 0) exitWith { "HMT|AP|ECHEC|presence|les_defenseurs_ne_tirent_pas" call HMT_LOG };
    (format ["HMT|OK|ap_presence|%1", _pre]) call HMT_LOG;

    private _plan = [];
    for "_r" from 1 to 12 do { _plan pushBack [1, _r]; _plan pushBack [0, _r] };
    (format ["HMT|AP|plan|%1|essais", count _plan]) call HMT_LOG;
    { _x call HMT_ESSAI } forEach _plan;
    "HMT|AP|TERMINE|1" call HMT_LOG;
};
