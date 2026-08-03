// hmt_capture.sqf — CAPTURE du monde persistant. Trois morceaux independants.
//
// POURQUOI PAS LE PONT : le pont TCP meurt en service (mutisme apres 20-40 min, mesure chez
// nous). Une nuit de capture n y survivrait pas. Le canal est donc diag_log : les lignes
// prefixees HMT| tombent dans le journal du serveur, qu un lecteur Python suit. Le journal
// survit a tout ce qui tue le pont.
//
// POURQUOI TROIS MORCEAUX INSTALLES SEPAREMENT : le 29/07, un gestionnaire qui referencait une
// commande inexistante est mort en silence et a emporte TOUT le script avec lui. Ici chaque
// morceau s installe seul et annonce sa propre ligne OK. Si l un tombe, les autres vivent, et le
// lecteur voit immediatement lequel manque.
//
// Appel :  [<numero_instance>, <dt_secondes>] execVM "capture\hmt_capture.sqf";

params [["_inst", 0], ["_dt", 0.2]];

HMT_CAP_VERSION = 7;                       // toute reinstallation invalide les gestionnaires anciens
HMT_CAP_DT = _dt;
HMT_CAP_INST = _inst;
HMT_LOG = { diag_log _this };              // canal unique : le journal, pas l extension

// Les identifiants sont A NOUS, jamais la reference objet : ALiVE detruit et recree les objets,
// donc une unite rematerialisee porte un NOUVEL identifiant — c est voulu, c est un evenement
// d apparition et non une continuite a truquer.
// Le garde isNil protege contre une re-execution du script : le compteur ne repart pas a zero,
// sinon deux unites differentes porteraient le meme identifiant dans le meme corpus.
if (isNil "HMT_NEXT_ID") then { HMT_NEXT_ID = 1 };
if (isNil "HMT_VUS") then { HMT_VUS = [] };          // identifiants vus au passage precedent
HMT_TICK = 0;
HMT_LAST = -1;
HMT_TIRS = [];                                       // identifiants ayant tire depuis le dernier tick

// LES MORTS NE SONT PAS DANS allUnits. Defaut de conception du 31/07 : le tick n emettait que
// allUnits, donc un homme disparaissait du corpus a l instant de sa mort — et sa mort devenait
// indiscernable d une virtualisation ALiVE, c est-a-dire exactement la confusion que l audit doit
// trancher. On lit donc les vivants ET les cadavres.
HMT_TOUS = { allUnits + allDeadMen };

HMT_SIDE = {                                          // camps en entier : 0 EAST 1 WEST 2 GUER 3 CIV
    private _s = _this;
    if (_s == east) exitWith {0};
    if (_s == west) exitWith {1};
    if (_s == resistance) exitWith {2};
    3
};

HMT_ID = {                                           // identifiant d une unite, -1 si non recensee
    private _u = _this;
    private _v = _u getVariable ["hmt_id", -1];
    _v
};

// ============================ 1. LE RECENSEUR ============================
// C est LUI qui repond a « les entites apparaissent en continu ». Un gestionnaire pose au
// demarrage de la mission manquerait la quasi-totalite des unites, qui n existent pas encore.
// Boucle volontairement bete, periode 2 s, auto-reparante : elle repasse derriere elle-meme.
// Apres le gestionnaire mort en silence, je prefere un mecanisme qui se verifie a un mecanisme
// evenementiel elegant.
[] spawn {
    private _v = HMT_CAP_VERSION;
    while { HMT_CAP_VERSION == _v } do {
        private _t = time;
        private _presents = [];
        {
            private _u = _x;
            private _id = _u getVariable ["hmt_id", -1];
            if (_id < 0) then {
                _id = HMT_NEXT_ID; HMT_NEXT_ID = HMT_NEXT_ID + 1;
                _u setVariable ["hmt_id", _id];
                // le camp ne change jamais : on le convertit UNE FOIS ici. L emetteur faisait
                // 240 appels de bloc par tick pour le recalculer — 7,65 ms mesurees, seuil 5.
                _u setVariable ["hmt_side", (side _u) call HMT_SIDE];
                _u setVariable ["hmt_fire", 0];

                // TIR : le projectile sert au filet « tir sans projectile ». Le gestionnaire est
                // pose sur le TIREUR ; l impact sera pose sur la CIBLE. Deux instruments
                // independants : leur recoupement mesure le monde, pas l instrumentation.
                _u addEventHandler ["Fired", {
                    params ["_u", "", "", "", "", "", "_proj"];
                    private _i = _u getVariable ["hmt_id", -1];
                    _u setVariable ["hmt_fire", 1];      // marque sur l unite : pas de recherche dans un tableau
                    (format ["HMT|E|fired|%1|%2|%3", (round (time * 100)) / 100, _i,
                             (if (isNull _proj) then {0} else {1})]) call HMT_LOG;
                }];

                // IMPACT : HitPart et pas HandleDamage — HandleDamage sous-compte d un facteur 4,
                // c est mesure. Le tableau recu contient une entree par partie touchee ; on les
                // parcourt, on ne fait PAS deux select de suite (bug du 29/07 : le gestionnaire
                // levait une erreur en silence et zero impact etait enregistre).
                _u addEventHandler ["HitPart", {
                    // FORME DU TABLEAU RECU. Bug du 31/07 : je parcourais « _this select 0 »,
                    // c est-a-dire les CHAMPS de la premiere entree, donc _x etait le soldat et
                    // « _x select 0 » levait « Type Object, expected Array ». Trois impacts reels
                    // n ont rien enregistre. Meme famille que le gestionnaire mort du 29/07.
                    // Le garde ci-dessous accepte les deux formes possibles : une liste d entrees,
                    // ou une entree seule.
                    private _lot = _this;
                    if ((count _lot) > 0 && { !((_lot select 0) isEqualType []) }) then { _lot = [_lot] };
                    {
                        private _cib = _x select 0;
                        private _tir = _x select 1;
                        (format ["HMT|E|hit|%1|%2|%3|%4", (round (time * 100)) / 100,
                                 (_cib getVariable ["hmt_id", -1]),
                                 (if (isNull _tir) then {-1} else {_tir getVariable ["hmt_id", -1]}),
                                 (round ((damage _cib) * 100)) / 100]) call HMT_LOG;
                    } forEach _lot;
                }];

                private _p = getPosASL _u;
                (format ["HMT|E|spawn|%1|%2|%3|%4|%5|%6", (round (_t * 100)) / 100, _id,
                         (round ((_p select 0) * 10)) / 10, (round ((_p select 1) * 10)) / 10,
                         (round ((_p select 2) * 10)) / 10, (side _u) call HMT_SIDE]) call HMT_LOG;
            };
            _presents pushBack _id;
        } forEach (call HMT_TOUS);

        // DISPARITION : present au passage precedent, absent maintenant. C est soit la
        // virtualisation par ALiVE, soit un nettoyage de corps. Dans les deux cas la tranche
        // d entrainement doit etre COUPEE ici : ce qui suit n est plus la meme scene.
        {
            if (!(_x in _presents)) then {
                (format ["HMT|E|despawn|%1|%2", (round (_t * 100)) / 100, _x]) call HMT_LOG;
            };
        } forEach HMT_VUS;
        HMT_VUS = _presents;
        sleep 2;
    };
};
"HMT|OK|recenseur|7" call HMT_LOG;

// ======================== 2. L EMETTEUR DE TICKS ========================
// Handler EachFrame avec accumulateur de temps : contexte NON ORDONNANCE, donc immunise contre
// la famine du scheduler SQF qui nous plafonnait a 10 Hz. Il parcourt TOUT allUnits et non un
// sous-ensemble spatial : la coupe d appartenance d ensemble exige de voir tout le monde.
// Les MORTS RESTENT dans le tick, position figee : la mort est une transition a predire, pas une
// disparition. Une ligne trop longue est tronquee par diag_log, donc on decoupe en morceaux
// numerotes que le lecteur reassemble.
HMT_MAXCAR = 850;
HMT_CHRONO = [0, 0];                                  // [somme des durees, nombre de ticks]
addMissionEventHandler ["EachFrame", {
    if (HMT_CAP_VERSION != 7) exitWith {};            // anti-zombie : une version plus recente m a remplace
    private _t = time;
    if (_t - HMT_LAST < HMT_CAP_DT) exitWith {};
    HMT_LAST = _t;
    private _d0 = diag_tickTime;
    HMT_TICK = HMT_TICK + 1;
    private _tr = round (_t * 100) / 100;
    private _tous = call HMT_TOUS;
    private _n = count _tous;
    private _bouts = [];
    private _cour = "";
    {
        private _u = _x;
        private _p = getPosASL _u;
        private _i = _u getVariable ["hmt_id", -1];
        private _e = str [_i,
            (round ((_p select 0) * 10)) / 10, (round ((_p select 1) * 10)) / 10,
            (round ((_p select 2) * 10)) / 10,
            (if (alive _u) then {1} else {0}), (_u getVariable ["hmt_side", 3]),
            (_u getVariable ["hmt_fire", 0])];
        if ((_u getVariable ["hmt_fire", 0]) == 1) then { _u setVariable ["hmt_fire", 0] };
        if ((count _cour) + (count _e) + 1 > HMT_MAXCAR) then { _bouts pushBack _cour; _cour = "" };
        _cour = if (_cour == "") then { _e } else { _cour + "," + _e };
    } forEach _tous;
    _bouts pushBack _cour;
    {
        (format ["HMT|S|%1|%2|%3|%4|[%5]", HMT_TICK, _forEachIndex, _tr, _n, _x]) call HMT_LOG;
    } forEach _bouts;
    // l emetteur mesure son propre cout : si p95 depasse 5 ms a densite reelle, on descend la
    // cadence — jamais on ne restreint la liste des unites.
    HMT_CHRONO set [0, (HMT_CHRONO select 0) + (diag_tickTime - _d0)];
    HMT_CHRONO set [1, (HMT_CHRONO select 1) + 1];
    if ((HMT_CHRONO select 1) % 300 == 0) then {
        (format ["HMT|C|cout_ms|%1|ticks|%2|unites|%3",
                 (round (1000 * (HMT_CHRONO select 0) / (HMT_CHRONO select 1) * 100)) / 100,
                 (HMT_CHRONO select 1), _n]) call HMT_LOG;
        HMT_CHRONO = [0, 0];
    };
}];
"HMT|OK|emetteur|7" call HMT_LOG;

// ===================== 3. LES MORTS, AU NIVEAU MISSION =====================
// Un seul gestionnaire de mission : il attrape TOUTES les morts, y compris celles d unites que le
// recenseur n a pas encore visitees (fenetre de 2 s). Le chainage mort <- impact se fait hors
// ligne, en Python, par correlation temporelle — pas ici.
addMissionEventHandler ["EntityKilled", {
    params ["_vic", "_tueur"];
    (format ["HMT|E|killed|%1|%2|%3", (round (time * 100)) / 100,
             (_vic getVariable ["hmt_id", -1]),
             (if (isNull _tueur) then {-1} else {_tueur getVariable ["hmt_id", -1]})]) call HMT_LOG;
}];
"HMT|OK|morts|7" call HMT_LOG;

(format ["HMT|OK|capture|7|instance|%1|dt|%2", HMT_CAP_INST, HMT_CAP_DT]) call HMT_LOG;
