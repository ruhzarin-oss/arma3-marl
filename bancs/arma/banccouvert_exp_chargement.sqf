// exp_chargement.sqf — POURQUOI LE MEME LIEU DONNE 64, 10 ET 100 % ?
//
// ⚠️ Trois de mes scripts ont mesure l EXPOSITION du meme couloir, memes coordonnees, meme
// formule, et ont rendu 64 %, 8-12 % et 100 %. Une sonde a montre que le CALCUL etait
// identique. Donc ce qui change est l ETAT DU MONDE au moment de mesurer.
//
// MON HYPOTHESE, donnee pour ce qu elle est : le serveur charge les objets de terrain autour
// des points d interet ; sans unite sur la carte, la vue interroge un monde a moitie vide.
// ⟨Fable : « une experience de minutes pour asseoir ta supposition sur pieces. Si le 64-10-100
//  s explique par le chargement, tu tiens la CAUSE, pas une hypothese. »⟩
//
// LE DESSIN : le meme couloir mesure TROIS FOIS dans UNE session.
//   ETAT A — monde vide, tout de suite.
//   ETAT B — monde PEUPLE comme au banc : la sonde au poste de tir, l equipe au depart.
//            ⟨la propriete qui fait foi est celle que le mecanisme utilise, DANS L ETAT ou il
//             l utilisera — et le banc tournera dans un monde peuple.⟩
//   ETAT C — apres stabilisation : on remesure jusqu a DEUX LECTURES CONSECUTIVES IDENTIQUES.
//            Le monde est pret quand il repond deux fois pareil, pas quand une horloge le dit.
//
// ET DEUX VUES A CHAQUE ETAT : mes rayons `lineIntersectsSurfaces` ET `checkVisibility`, la
// visibilite DU MOTEUR — celle que l IA utilise pour decider si elle tire.
// ⟨regle 11, deposee cette nuit : toute grandeur qui decide d un certificat se mesure par deux
//  chemins independants ; un desaccord ne s arbitre pas, il declare l instrument en panne.⟩
//
// CE QUI FERAIT ECHOUER LA LECTURE, ecrit avant :
//   · si les trois etats donnent la MEME chose, mon hypothese tombe et la cause est ailleurs —
//     et je n aurai pas le droit de dire « c est le chargement » ;
//   · on compte AUSSI les objets presents dans le couloir a chaque etat : si le nombre ne
//     bouge pas alors que la vue bouge, ce n est pas le chargement.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|EX|debut|1" call HMT_LOG;

[] spawn {
    sleep 20;
    private _cou = [4355,6210,0];
    private _dep = [4595,6210,0];
    private _pos = [4475,6085,0];
    private _pas = 24;

    HMT_LIRE = {
        params ["_etat"];
        private _m1 = ""; private _m2 = ""; private _n = 0;
        for "_k" from 0 to _pas do {
            private _f = _k / _pas;
            private _p = [(_dep select 0) + ((_cou select 0) - (_dep select 0)) * _f,
                          (_dep select 1) + ((_cou select 1) - (_dep select 1)) * _f, 0];
            // chemin 1 : mes rayons, a 1,2 m
            private _r = lineIntersectsSurfaces [AGLToASL [_pos select 0, _pos select 1, 1.2],
                                                 AGLToASL [_p select 0, _p select 1, 1.2],
                                                 objNull, objNull, true, 1];
            _m1 = _m1 + (if (count _r == 0) then {"1"} else {"0"});
            // chemin 2 : la vue DU MOTEUR
            private _v = [objNull, "VIEW"] checkVisibility
                         [AGLToASL [_pos select 0, _pos select 1, 1.2],
                          AGLToASL [_p select 0, _p select 1, 1.2]];
            _m2 = _m2 + (if (_v > 0) then {"1"} else {"0"});
            // et ce qu il y a REELLEMENT dans le couloir a cet instant
            _n = _n + (count (nearestTerrainObjects [_p, [], 20, false, true]));
        };
        private _c1 = 0; { if (_x == 49) then { _c1 = _c1 + 1 } } forEach (toArray _m1);
        private _c2 = 0; { if (_x == 49) then { _c2 = _c2 + 1 } } forEach (toArray _m2);
        (format ["HMT|EX|%1|rayons|%2|moteur|%3|sur|%4|objets|%5",
                 _etat, _c1, _c2, _pas + 1, _n]) call HMT_LOG;
        [_c1, _c2, _n]
    };

    // ---- ETAT A : monde vide
    private _a = ["A_vide"] call HMT_LIRE;

    // ---- ETAT B : monde peuple, comme au banc
    private _gD = createGroup east;
    private _u = _gD createUnit ["O_Soldier_F", _pos, [], 0, "NONE"];
    _u setPosATL _pos; _u allowDamage false; _u disableAI "PATH";
    private _gA = createGroup west;
    for "_i" from 1 to 4 do {
        private _p = _dep vectorAdd [(_i - 2) * 6, 0, 0];
        private _v = _gA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
        _v setPosATL _p; _v allowDamage false; _v disableAI "PATH";
    };
    sleep 8;
    private _b = ["B_peuple"] call HMT_LIRE;

    // ---- ETAT C : jusqu a deux lectures consecutives identiques
    private _prec = []; private _n = 0; private _stable = false;
    while { _n < 10 && !_stable } do {
        _n = _n + 1;
        sleep 15;
        private _c = [format ["C_%1", _n]] call HMT_LIRE;
        if (count _prec > 0 && {_c isEqualTo _prec}) then { _stable = true };
        _prec = _c;
    };
    (format ["HMT|EX|BILAN|A|%1|%2|B|%3|%4|C|%5|%6|stable_en|%7|lectures",
             _a select 0, _a select 1, _b select 0, _b select 1,
             _prec select 0, _prec select 1, _n]) call HMT_LOG;
    if ((_a select 0) == (_prec select 0)) then {
        "HMT|EX|hypothese|REFUTEE|le_chargement_n_explique_rien" call HMT_LOG;
    } else {
        "HMT|EX|hypothese|SOUTENUE|la_vue_change_avec_l_etat_du_monde" call HMT_LOG;
    };
    "HMT|EX|TERMINE|1" call HMT_LOG;
};
