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

params [["_maxAcc", 1], ["_dureeMax", 600], ["_nAxes", 2], ["_fige", false], ["_calib", false], ["_rMin", 1.2], ["_rMax", 2.5]];
if (!isServer) exitWith {};
HMT_GEN_VERSION = 12;
HMT_CALIB = _calib;   // coupe les journaux lourds pendant le reglage

private _periode = 20;
private _rTenue = 50;           // rayon de tenue
private _tenueRequise = 60;     // secondes CONTINUES d occupation exclusive
HMT_ACC = [];

// ---------------------------------------------------------------- INSTRUMENTATION v12
HMT_DT_POS = 2.0;   // 2 s : le coeur du banc est EVENEMENTIEL (ARR, TIR, IMP), pas les positions          // cadence des positions, desserree d office si le budget saute
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

// ---- LE TEMOIN DE PROGRESSION, echantillonne toutes les 2 s ----
// ⚠️ POURQUOI CE BANC EXISTE. On a voulu refaire « l exposition par metre gagne » — le premier
// des six sursitaires — sur le journal du banc n°2. Le NUMERATEUR y etait (le temoin `VISE`
// rend 31 778 echantillons de designation, et la suppression subie porte 92 % du pouvoir
// predictif). Le DENOMINATEUR, lui, n y etait pas : on avait pris `_dmin` pour la distance a
// l objectif alors que c est la distance minimale a un defenseur VIVANT — boucle vide des que
// les defenseurs tombent, donc 3935 m sur une prise reussie, et 168 accrochages PRIS declares
// « a gain nul ». Aucun des quatre controles ne pouvait l attraper : ils verifiaient la taille
// et les separations, aucun ne demandait si le champ MESURE LA CHOSE QU IL NOMME.
// Ici on journalise la distance a l objectif, par homme, toutes les 2 s. Rien d autre ne change.
[] spawn {
    while { true } do {
        {
            _x params ["_unites", "", "_pt", "", "_id"];
            {
                if (alive _x && {(_x getVariable ["hmt_axe", -1]) >= 0}) then {
                    (format ["HMT|G|POS|%1|%2|%3|%4", _id, (round (time*100))/100,
                             _x getVariable ["hmt_id", -1],
                             round (_x distance2D _pt)]) call HMT_LOG;
                };
            } forEach _unites;
        } forEach HMT_ACC;
        sleep 2;
    };
};

// ---- LE TEMOIN D INTENTION, echantillonne toutes les 2 s ----
// `TIR` est emis sur Fired : il ne dit rien des accrochages ou personne ne tire, qui sont
// justement ceux ou le sursis a joue a fond. Ici on releve `assignedTarget` au fil du temps,
// que le defenseur tire ou non. Criteres : CRITERES_TEMOIN_VISE.md, deposes avant lancement.
[] spawn {
    while { true } do {
        {
            _x params ["_unites", "", "", "", "_id"];
            {
                if (alive _x && {(_x getVariable ["hmt_axe", -1]) == -1}) then {
                    private _c = assignedTarget _x;
                    (format ["HMT|G|VISE|%1|%2|%3|%4", _id, (round (time*100))/100,
                             _x getVariable ["hmt_id", -1],
                             (if (isNull _c) then {-1} else {_c getVariable ["hmt_id", -1]})
                            ]) call HMT_LOG;
                };
            } forEach _unites;
        } forEach HMT_ACC;
        sleep 2;
    };
};

// ---- LES COULOIRS QUI FORCENT LE BOND, choisis sur la carte du bati du 07/08 ----
// [x, y, azimut d approche] — l objectif est dans du bati dense, l approche fait 250 m et
// alterne masques et zones ouvertes. Aucun n a encore d opinion : chacun doit passer sa
// PORTE 0 avant de juger un agent.
// ═══ GESTE N°2 — APPUI-FEU. Les huit lieux CERTIFIES EN GEOMETRIE par la chasse en jeu du
// 09/08 : [objectif, poste d appui, depart de l assaut]. Chacun a >= 60 % de vue poste vers
// objectif, >= 70 % de pas servis en couvert, >= 60 % de pas sous le feu, aucun trou de plus
// de 20 m. Le filtre sur CARTE en avait rendu ZERO sur huit — l appui n y voyait pas
// l objectif (0 a 60 %). La carte donne le gros grain, le geometre en jeu rend les metres.
HMT_LIEUX_AP = [
    [[2680,2365],[2709,2218],[2484,2326]], [[3392,7000],[3252,7056],[3466,7186]],
    [[3413,5934],[3420,6084],[3613,5925]], [[3427,3740],[3543,3645],[3301,3585]],
    [[5729,5805],[5821,5687],[5571,5682]], [[4679,5658],[4795,5752],[4805,5502]],
    [[3453,2607],[3304,2586],[3425,2805]], [[5564,4631],[5528,4485],[5369,4678]]
];
HMT_LIEUX = [[4350,3750,0],[6450,5350,90],[2150,5600,225],[2750,5850,90],[2000,3550,225],[1500,4950,180],[5000,5900,0],[1800,6000,315]];

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
                if (alive _x && !HMT_CALIB) then {
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

[_maxAcc, _periode, _dureeMax, _rTenue, _tenueRequise, _nAxes, _fige, _calib, _rMin, _rMax] spawn {
    params ["_maxAcc", "_periode", "_dureeMax", "_rTenue", "_tenueRequise", "_nAxes", "_fige", "_calib", "_rMin", "_rMax"];
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
            } forEach (if (HMT_CALIB) then {[]} else {_viv});

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
                // RENDRE LES GROUPES, pas seulement les hommes. Sans ceci le banc
                // degenere au 235e accrochage (limite Arma : 144 groupes par camp) et
                // continue d ecrire des accrochages de 5 s que tout depouilleur compte.
                private _grp = []; { if (!isNull _x) then { _grp pushBackUnique (group _x) } } forEach _unites;
                { if (!isNull _x) then { deleteVehicle _x } } forEach _unites;
                [_grp] spawn { params ["_g"]; sleep 1;
                    { if (!isNull _x && {count (units _x) == 0}) then { deleteGroup _x } } forEach _g; };
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
                // COULOIR IMPOSE : on remplace le point tire au hasard par un couloir
                // certifie-en-attente, et l azimut d approche par le sien.
                if (missionNamespace getVariable ["HMT_BOND", false]) then {
                    private _L = HMT_LIEUX select (floor (random (count HMT_LIEUX)));
                    _pt = [_L select 0, _L select 1, 0];
                    HMT_AZ_IMPOSE = _L select 2;
                    HMT_LIEU_ID = HMT_LIEUX find _L;
                };
                if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                    // LE LIEU EST IMPOSE EN ENTIER : objectif, poste d appui, depart. Les trois
                    // ont ete certifies ENSEMBLE — un poste qui voit sans un depart sous le feu
                    // ne forcerait rien.
                    private _L = HMT_LIEUX_AP select (floor (random (count HMT_LIEUX_AP)));
                    _pt = [(_L select 0) select 0, (_L select 0) select 1, 0];
                    HMT_POSTE = [(_L select 1) select 0, (_L select 1) select 1, 0];
                    HMT_DEPART = [(_L select 2) select 0, (_L select 2) select 1, 0];
                    HMT_AZ_IMPOSE = (_pt getDir HMT_DEPART);
                    HMT_LIEU_ID = HMT_LIEUX_AP find _L;
                };
                _n = _n + 1;
                // LES QUATRE BRAS, TIRES AU SORT A CHAQUE ACCROCHAGE
                //   0 frontal · 1 deux axes · 2 frontal FIGE · 3 deux axes FIGE
                if (_calib) then {
                    // CALIBRAGE : UN SEUL BRAS, jamais fige. On ne PEUT pas comparer.
                    _nAxes = 1; _fige = false;
                } else {
                    // DEUX BRAS PLEINS + A2 en tranche de controle a 20 %.
                    // Quatre bras equiprobables diluaient le N : 25 % chacun. Ici 40/40/20,
                    // le controle positif gardant juste de quoi dire si l instrument tient.
                    private _d = random 1;
                    if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                        // GESTE N°2 : le professeur (3 en appui + 5 a l assaut) contre son
                        // temoin (8 hommes tous a l assaut). UN SEUL axe, effectif TOTAL
                        // identique : on mesure le GESTE, pas le nombre d hommes.
                        _nAxes = 1; _fige = false;
                        HMT_APPUI_CE = (_d < 0.5);
                        // pendant le calibrage on ne compare rien : un seul bras, le temoin.
                        if (missionNamespace getVariable ["HMT_CALIBRE", false]) then {
                            HMT_APPUI_CE = false;
                        };
                    } else {
                    if (missionNamespace getVariable ["HMT_BOND", false]) then {
                        // GESTE N°1 : le professeur (bond alterne) contre son temoin
                        // (progression simultanee). UN SEUL axe des deux cotes, effectif
                        // identique : on mesure le GESTE, pas le nombre d hommes ni l angle.
                        _nAxes = 1; _fige = false;
                        HMT_BOND_CE = (_d < 0.5);
                    } else {
                    if (missionNamespace getVariable ["HMT_A2PUR", false]) then {
                        // BANC A2 DEDIE : 100 % fige, deux bras a 50/50.
                        // A 20 % du tirage, le controle positif faisait 18 puis 31 configs :
                        // il a pointe +16,7 % puis -8,3 %, jamais significativement. Une porte
                        // qui ne peut pas se fermer n est pas une porte. On la dimensionne.
                        // Criteres : CRITERES_BANC_A2_DEDIE.md, deposes avant le lancement.
                        _nAxes = (if (_d < 0.5) then {1} else {2}); _fige = true;
                    } else {
                    if (_d < 0.4) then { _nAxes = 1; _fige = false }
                    else { if (_d < 0.8) then { _nAxes = 2; _fige = false }
                    else { _nAxes = (if (_d < 0.9) then {1} else {2}); _fige = true } };
                    };
                    };
                    };
                };
                private _campDef = floor random 2;
                private _nDef = 4 + floor random 5;                 // 4 a 8 defenseurs
                // ⚠️ CALIBRAGE AVEUGLE. L aiguille etait AU BUTOIR : 84,4 % de prise au temoin,
                // hors de la bande 20-80 %. Dans un monde ou l assaut passe huit fois sur dix
                // sans appui, rien ne peut se mesurer — et detourner trois hommes sur huit ne
                // fait que couter. On BALAYE l effectif defenseur et on lira a quel reglage le
                // taux de prise retombe dans la bande. UN SEUL BRAS pendant le calibrage :
                // on regle le monde, on ne compare rien. ⟨le calibrage aveugle du 02/08⟩
                if (missionNamespace getVariable ["HMT_CALIBRE", false]) then {
                    _nDef = 4 + floor random 11;                    // 4 a 14 defenseurs
                };
                // --- EFFECTIF CALIBRE, fige par le balayage aveugle du 10/08 (268 accrochages,
                // onze reglages tous lisibles). Chaque geste prend LE SIEN sur SA grandeur :
                //   geste n2 -> 13 defenseurs (prise 65 %)   ·   geste n3 -> 11 (survie 59 %)
                // ATTENTION : le balayage dit autre chose qu un reglage. De 4 a 14 defenseurs la
                // prise ne passe que de 72 % a 67 %. TRIPLER LA DEFENSE NE CHANGE PRESQUE RIEN.
                // L effectif est un levier faible, et tout le balayage tient dans le HAUT de la
                // bande. L ordre des axes depose le 10/08 - distance, puis competence, puis
                // armement - servira plus tot que prevu.
                if (!isNil "HMT_NDEF") then { _nDef = HMT_NDEF };
                // RAPPORT DE FORCE RESSERRE. Mesure du 01/08 sur 33 verdicts : a 1,5-4 contre 1,
                // l assaillant prenait le point 75,8 % du temps pour une cible de 40-60. J avais
                // corrige l impasse du matin en fabriquant l inverse — un monde ou l attaque paie
                // presque toujours. Quatre defenseurs contre seize cedent meme retranches.
                private _ratio = _rMin + random (_rMax - _rMin);    // plage passee en parametre
                private _nAtt = round (_nDef * _ratio) min 16;
                // ⚠️ L EFFECTIF ATTAQUANT EST FIXE A 8, comme le depot le dit — « 8 hommes :
                // 3 en appui, 5 a l assaut ». Le generateur le calculait depuis un rapport de
                // force et rendait 6 a 16 hommes : mon professeur prenait donc 3 hommes sur un
                // groupe qui pouvait en compter seize. Le banc ne respectait pas son propre
                // depot, et personne ne l avait vu.
                if (missionNamespace getVariable ["HMT_APPUI", false]) then { _nAtt = 8 };
                private _dist = 200 + random 200;
                // ⚠️ LE LIEU EST CERTIFIE SUR UN CHEMIN PRECIS, PAS SUR UN AZIMUT. Le
                // generateur imposait l azimut mais gardait sa propre distance de depart —
                // 362 m mesures au premier accrochage, contre 200 m certifies. Les 160
                // premiers metres se couraient donc sur du terrain dont personne n a mesure
                // ni le couvert ni l exposition. On impose la DISTANCE du lieu, comme on
                // impose son azimut : le banc court le chemin qui a ete certifie.
                if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                    _dist = HMT_DEPART distance2D _pt;
                };
                // LES DEUX AXES DOIVENT ETRE AU SEC. Bug du 01/08 : on tirait un azimut et un
                // ecart sans verifier, et sur une ile le second tombait regulierement a la mer —
                // le groupe etait alors saute en silence et l assaut arrivait sur UN SEUL axe,
                // supprimant precisement ce qui declenche le contournement chez LAMBS.
                private _az1 = -1;
                if (missionNamespace getVariable ["HMT_BOND", false]) then {
                    _az1 = HMT_AZ_IMPOSE;   // l approche du couloir, pas un tirage
                };
                if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                    _az1 = HMT_AZ_IMPOSE;   // l axe d assaut du lieu certifie
                }; private _ecart = 0;
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
                        if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                            // ═══ LE PROFESSEUR DU GESTE N°2 ═══
                            // 3 hommes au POSTE D APPUI, 5 a l assaut. Le temoin garde les 8 a
                            // l assaut : effectif TOTAL identique, sinon on mesure le nombre
                            // d hommes et non la manoeuvre.
                            if (HMT_APPUI_CE) then {
                                private _u = units _g;
                                private _gAp = createGroup _cAtt;
                                for "_k" from 0 to 2 do {
                                    if (_k < count _u) then { [_u select _k] joinSilent _gAp };
                                };
                                _gs pushBack _gAp;
                                // les appuis se postent, couches, et attendent la mi-course
                                {
                                    _x setPosATL [(HMT_POSTE select 0) + (random 8) - 4,
                                                  (HMT_POSTE select 1) + (random 8) - 4, 0];
                                    _x disableAI "PATH"; _x disableAI "AUTOCOMBAT";
                                    _x disableAI "AUTOTARGET"; _x disableAI "FSM";
                                    _x setUnitPos "DOWN"; _x setCombatMode "BLUE";
                                    _x setBehaviour "COMBAT";
                                    _x addEventHandler ["Fired", { (_this select 0) setVehicleAmmo 1 }];  // lint:ok
                                } forEach (units _gAp);
                                // ⚠️ LE FEU EST LE NATIF DU MOTEUR — `commandSuppressiveFire`,
                                // huit lignes, retenu par l ETAGE 1 du 09/08 : moyenne
                                // geometrique 0,549 sur six terrains, intervalle [0,343 ; 0,878],
                                // six terrains sur six sous l unite. Mon feu scripte, lui, allait
                                // de +57 % a -40 % selon l endroit : illisible, enterre.
                                [_gAp, _g, _pt, _n, _dist] spawn {
                                    params ["_gAp", "_gAs", "_pt", "_id", "_dist"];
                                    private _t0 = time;
                                    private _ouvert = false;
                                    while { time - _t0 < 900 && {({alive _x} count (units _gAp)) > 0} } do {
                                        private _dd = (getPosATL (leader _gAs)) distance2D _pt;
                                        // OUVRE a la mi-course, LEVE a 50 m : le declencheur dit
                                        // QUAND le feu commence, jamais COMMENT il se comporte,
                                        // et il est identique aux deux bras — dans le temoin il
                                        // n y a simplement personne pour l entendre.
                                        if (!_ouvert && _dd < (_dist / 2)) then {
                                            _ouvert = true;
                                            (format ["HMT|G|APPUI|%1|ouvre|%2", _id, round _dd]) call HMT_LOG;
                                        };
                                        if (_ouvert && _dd > 50) then {
                                            { _x setCombatMode "RED";
                                              _x commandSuppressiveFire _pt } forEach (units _gAp);
                                        };
                                        if (_ouvert && _dd <= 50) exitWith {
                                            { _x setCombatMode "BLUE"; doStop _x } forEach (units _gAp);
                                            (format ["HMT|G|APPUI|%1|leve|%2", _id, round _dd]) call HMT_LOG;
                                        };
                                        sleep 4;
                                    };
                                };
                            };
                            _g move _pt;
                        } else {
                        if (missionNamespace getVariable ["HMT_BOND", false]
                            && {HMT_BOND_CE}) then {
                            // LE PROFESSEUR. On coupe le groupe en deux equipes et on les fait
                            // alterner : l une bondit de 40 m vers l objectif, l autre s arrete,
                            // tient et tire. Puis elles echangent. C est le bond par binome.
                            private _u = units _g;
                            private _gB = createGroup _cAtt;
                            for "_k" from 0 to ((count _u) - 1) do {
                                if (_k % 2 == 1) then { [_u select _k] joinSilent _gB };
                            };
                            _gs pushBack _gB;
                            [_g, _gB, _pt, _n] spawn {
                                params ["_a", "_b", "_pt", "_id"];
                                private _tour = 0;
                                private _t0 = time;
                                while { time - _t0 < 900
                                        && {({alive _x} count (units _a)) + ({alive _x} count (units _b)) > 0} } do {
                                    private _mob = if (_tour % 2 == 0) then { _a } else { _b };
                                    private _fix = if (_tour % 2 == 0) then { _b } else { _a };
                                    // celui qui tient s arrete et appuie
                                    { doStop _x; _x setUnitPos "MIDDLE" } forEach (units _fix);
                                    // celui qui bondit avance de 40 m vers l objectif
                                    private _p0 = getPosATL (leader _mob);
                                    private _dd = (_p0 distance2D _pt) max 1;
                                    private _f = ((_dd - 40) max 0) / _dd;
                                    private _dest = [(_pt select 0) + ((_p0 select 0) - (_pt select 0)) * _f,
                                                     (_pt select 1) + ((_p0 select 1) - (_pt select 1)) * _f, 0];
                                    // ⚠️ ON RELACHE HOMME PAR HOMME. Un ordre de GROUPE ne leve
                                    // pas le doStop pose sur chaque homme au tour precedent :
                                    // les deux equipes alternaient sans jamais avancer, la
                                    // distance oscillant entre 273 et 260 m sur quatorze bonds.
                                    // Le professeur ne bondissait pas, il pietinait — et il
                                    // arrivait 5 % du temps contre 54 % au temoin.
                                    { _x setUnitPos "AUTO"; _x doFollow (leader _mob);
                                      _x doMove _dest } forEach (units _mob);
                                    _mob move _dest;
                                    (format ["HMT|G|BOND|%1|%2|%3|%4", _id,
                                             (round (time*100))/100, _tour,
                                             round _dd]) call HMT_LOG;
                                    sleep 12;
                                    _tour = _tour + 1;
                                };
                            };
                        } else {
                            _g move _pt;
                        };
                        };
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
                    if (!HMT_CALIB) then { { [_x, _n] call HMT_ARMER_TIR } forEach _tous };
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
                    if (missionNamespace getVariable ["HMT_APPUI", false]) then {
                        (format ["HMT|G|LIEUAP|%1|%2|%3", _n,
                                 (missionNamespace getVariable ["HMT_LIEU_ID", -1]),
                                 (if (missionNamespace getVariable ["HMT_APPUI_CE", false])
                                  then {1} else {0})]) call HMT_LOG;
                    };
                    (format ["HMT|G|LIEU|%1|%2|%3", _n,
                             (missionNamespace getVariable ["HMT_LIEU_ID", -1]),
                             (if (missionNamespace getVariable ["HMT_BOND_CE", false])
                              then {1} else {0})]) call HMT_LOG;
                    // SANTE : une panne silencieuse doit devenir bruyante. Si le nombre de
                    // groupes monte accrochage apres accrochage, le banc se meurt, et ca se VOIT.
                    (format ["HMT|G|SANTE|%1|%2|%3", _n,
                             {side _x == west} count allGroups,
                             {side _x == east} count allGroups]) call HMT_LOG;
                } else {
                    private _grp2 = []; { if (!isNull _x) then { _grp2 pushBackUnique (group _x) } } forEach _tous;
                    { if (!isNull _x) then { deleteVehicle _x } } forEach _tous;
                    [_grp2] spawn { params ["_g"]; sleep 1;
                        { if (!isNull _x && {count (units _x) == 0}) then { deleteGroup _x } } forEach _g; };
                };
            };
        };
    };
};
(format ["HMT|OK|generateur|12|journaux|POS,TIR,IMP,SU,ARR,FIGE|dt_pos|%1", HMT_DT_POS]) call HMT_LOG;
