// geometre_couvert.sqf — GESTE N°3, ÉTAGE 2 DU FILTRE : LE GÉOMÈTRE EN JEU.
//
// ⟨Fable, 08/08⟩ « Le sel est SOUS le pas de ta carte : les masques utiles sont à 10-20 m du
// trajet, invisibles à 50 m de résolution. Deux étages de filtre — la carte donne "couloir
// ouvert avec cases masquées adjacentes", puis le géomètre en jeu mesure les objets RÉELS à
// moins de 15 m de la ligne de marche. SANS CE SECOND ÉTAGE tu certifierais des lieux dont
// le geste est impossible. »
//
// CE QUE CE SCRIPT FAIT, ET RIEN D'AUTRE : il mesure. Il ne juge aucun geste, ne fait courir
// personne, et n'a pas de bras. Il répond à une seule question par traversée :
//
//     UN HOMME QUI SE JETTE À COUVERT EN A-T-IL UN À MOINS DE 15 m, TOUT LE LONG ?
//
// Si la réponse est non, le lieu est écarté — et si elle est non partout, ce n'est pas le
// geste n°3 qui tombe, c'est Stratis qui ne le porte pas, et on le dira comme ça.
//
// LA MESURE. La ligne de marche est échantillonnée tous les 10 m. À chaque pas on cherche les
// objets réels dans un rayon de 15 m, et on ne garde que ceux qui peuvent ARRÊTER UNE BALLE :
// murs, rochers, bâtiments, épaves, gros troncs. Les buissons ne comptent pas — ils cachent,
// ils ne protègent pas, et le geste n°3 se juge sur les PERTES.
//
// ⚠️ LA MOITIÉ MANQUANTE, ajoutée après l'audit ⟨Fable, 08/08⟩ : le compteur ci-dessus dit
// qu'un homme PEUT se jeter à couvert. Le forçage exige aussi qu'il soit SOUS LE FEU pendant
// la traversée. Un couloir dont tous les masques sont bien placés peut être masqué DU POSTE
// DÉFENSEUR : alors personne ne tire, les deux bras se confondent, et le lieu est certifié
// pour rien — possible, mais jamais nécessaire. D'où une SECONDE COLONNE : à chaque pas, la
// ligne de vue depuis le poste de tir.
//
// LE POSTE DE TIR est posé perpendiculairement au trajet, à sa mi-course, à 125 m — le milieu
// de la bande 100-150 m de la fiche. Les deux côtés sont essayés ; on garde celui qui voit le
// mieux, et sa position est journalisée : elle fait partie du lieu certifié.
//
// LE CRITÈRE, DÉPOSÉ AVANT DE LIRE QUOI QUE CE SOIT :
//   · un PAS est SERVI s'il a au moins un masque dur à moins de 15 m ;
//     ⟨le 15 m n'est plus au jugé : l'arc de tir accorde un sursis MESURÉ de 4 s, et un homme
//      à la course couvre ~20 m dans ce sursis. Un couvert à 15 m est donc atteignable DANS
//      la fenêtre que le monde accorde. Le seuil vient du dossier, pas de mon estimation.⟩
//   · un PAS est VU s'il y a ligne de vue depuis le poste de tir, à 1,2 m de haut ;
//   · une traversée est RETENUE si les TROIS conditions tiennent ensemble :
//       – au moins 70 % de pas servis,
//       – AUCUNE séquence de plus de 2 pas consécutifs non servis (soit 20 m de désert
//         maximum — le sursis au sprint). Un pourcentage sans contrainte de séquence mesure
//         la MOYENNE d'un couloir ; les hommes meurent dans ses pires 30 mètres.
//       – au moins 60 % de pas vus depuis le poste.
//   · il faut au moins 5 traversées retenues pour instruire le geste (3 instruites,
//     2 tenues à l'écart), avec 500 m d'écart entre elles — déjà garanti à la chasse.
//
// CE QUI FERAIT ÉCHOUER LA MESURE — écrit avant :
//   · CONTRÔLE POSITIF : on mesure aussi 3 points pris DANS du bâti dense. Ils doivent sortir
//     très bien servis. S'ils ne le sont pas, c'est le compteur qui est cassé, pas le terrain.
//   · CONTRÔLE NUL : on mesure 3 points pris en pleine mer. Ils doivent sortir à zéro.
//   · Si les huit traversées sortent identiques, se méfier : le compteur ne discrimine pas.

if (!isServer) exitWith {};
HMT_LOG = { diag_log _this };
"HMT|GC|debut|1" call HMT_LOG;

HMT_TRAV = [
    [[3150,1500],[3350,1700]], [[2200,1650],[2400,1650]],
    [[2850,1950],[2650,1950]], [[3400,2100],[3400,1900]],
    [[2300,2150],[2500,2150]], [[2800,2500],[2600,2300]],
    [[3600,2600],[3800,2400]], [[1850,2750],[2050,2550]]
];

// Les types qui ARRÊTENT UNE BALLE. Les buissons en sont exclus volontairement : ils cachent
// mais ne protègent pas, et le geste n°3 se juge sur les pertes, pas sur la discrétion.
HMT_DUR = ["BUILDING", "HOUSE", "WALL", "ROCK", "ROCKS", "FORTRESS", "BUNKER", "RUIN",
           "FUELSTATION", "CHAPEL", "CHURCH", "HOSPITAL", "SHIPWRECK", "TRANSMITTER"];

// ⚠️ LISTE BLANCHE DE CLASSES, PLUS DE FILTRE A LA TAILLE. Le `sizeOf > 1,2` laissait passer
// un grillage, qui n arrete rien. La liste sort le grillage toute seule.
// Et on NE MESURE PAS la protection balistique reelle : ce serait dorer le tamis. Le geometre
// est un filtre a CANDIDATS ; le certificat, c est la PORTE 0 du lieu — si les masques
// n arretent rien, le professeur ne battra pas le temoin et le lieu tombera de lui-meme.
// ⟨Fable : chaque etage de l instrument a sa taille.⟩
HMT_CLASSES = ["Building", "House", "Wall", "Rock", "Ruins", "Land_Wreck_Base_F"];
HMT_SERVI = {
    params ["_p"];
    private _n = 0;
    { _n = _n + 1 } forEach (nearestObjects [_p, HMT_CLASSES, 15]);
    { _n = _n + 1 } forEach (nearestTerrainObjects [_p, HMT_DUR, 15, false, true]);
    _n
};

[] spawn {
    sleep 20;

    HMT_MESURE = {
        params ["_a", "_b", "_nom", ["_poste", []]];
        private _d = _a distance2D _b;
        private _pas = round (_d / 10) max 1;
        private _servis = 0; private _vus = 0;
        private _trou = 0; private _pireTrou = 0;
        private _detail = [];
        for "_k" from 0 to _pas do {
            private _f = _k / _pas;
            private _p = [(_a select 0) + ((_b select 0) - (_a select 0)) * _f,
                          (_a select 1) + ((_b select 1) - (_a select 1)) * _f, 0];
            private _n = [_p] call HMT_SERVI;
            if (_n > 0) then {
                _servis = _servis + 1; _trou = 0;
            } else {
                _trou = _trou + 1;
                if (_trou > _pireTrou) then { _pireTrou = _trou };
            };
            // la SECONDE COLONNE : ce pas est-il sous la vue du poste de tir ?
            if (count _poste > 0) then {
                private _p1 = AGLToASL [_poste select 0, _poste select 1,
                                        (getTerrainHeightASL _poste) + 1.2 - (getTerrainHeightASL _poste)];
                _p1 = AGLToASL [_poste select 0, _poste select 1, 1.2];
                private _p2 = AGLToASL [_p select 0, _p select 1, 1.2];
                if (count (lineIntersectsSurfaces [_p1, _p2, objNull, objNull, true, 1]) == 0)
                    then { _vus = _vus + 1 };
            };
            _detail pushBack _n;
        };
        private _tot = _pas + 1;
        private _pc = round (100 * _servis / _tot);
        private _pv = round (100 * _vus / _tot);
        (format ["HMT|GC|trav|%1|long|%2|pas|%3|servis|%4|pc|%5|vus|%6|pcvus|%7|piretrou|%8|detail|%9",
                 _nom, round _d, _tot, _servis, _pc, _vus, _pv, _pireTrou, str _detail]) call HMT_LOG;
        [_pc, _pv, _pireTrou]
    };

    // ---- CONTRÔLE POSITIF : dans du bâti dense, tout doit être servi
    { [_x, _x, format ["POSITIF_%1", _forEachIndex]] call HMT_MESURE }
      forEach [[2000,2650,0], [1900,3550,0], [1500,4900,0]];
    // ---- CONTRÔLE NUL : en pleine mer, rien ne doit être servi
    { [_x, _x, format ["NUL_%1", _forEachIndex]] call HMT_MESURE }
      forEach [[500,500,0], [7500,7500,0], [300,7000,0]];

    // ---- les huit traversées
    private _ok = 0;
    {
        private _a = [(_x select 1) select 0, (_x select 1) select 1, 0];   // depart
        private _b = [(_x select 0) select 0, (_x select 0) select 1, 0];   // couvert d arrivee
        private _i = _forEachIndex;
        // LE POSTE DE TIR : perpendiculaire au trajet, a mi-course, a 125 m. Les deux cotes
        // sont essayes, on garde celui qui voit le mieux — et sa position est journalisee,
        // elle fait partie du lieu certifie.
        private _m = [((_a select 0) + (_b select 0)) / 2, ((_a select 1) + (_b select 1)) / 2, 0];
        private _ux = ((_b select 0) - (_a select 0)) / (_a distance2D _b);
        private _uy = ((_b select 1) - (_a select 1)) / (_a distance2D _b);
        private _meilleur = []; private _res = [0, -1, 99];
        {
            private _s = _x;
            private _q = [(_m select 0) + (-_uy) * 125 * _s, (_m select 1) + _ux * 125 * _s, 0];
            if (!(surfaceIsWater _q)) then {
                private _r = [_a, _b, format ["%1_poste%2", _i, _s], _q] call HMT_MESURE;
                if ((_r select 1) > (_res select 1)) then { _res = _r; _meilleur = _q };
            };
        } forEach [1, -1];
        private _pc = _res select 0; private _pv = _res select 1; private _pt = _res select 2;
        private _retenue = (_pc >= 70) && (_pv >= 60) && (_pt <= 2);
        (format ["HMT|GC|BILAN_TRAV|%1|pcservis|%2|pcvus|%3|piretrou|%4|poste|%5|%6|retenue|%7",
                 _i, _pc, _pv, _pt, round (_meilleur select 0), round (_meilleur select 1),
                 (if (_retenue) then {1} else {0})]) call HMT_LOG;
        if (_retenue) then { _ok = _ok + 1 };
        sleep 1;
    } forEach HMT_TRAV;

    (format ["HMT|GC|BILAN|retenues|%1|sur|%2", _ok, count HMT_TRAV]) call HMT_LOG;
    if (_ok >= 5) then {
        "HMT|OK|gc_assez_de_lieux|1" call HMT_LOG;
    } else {
        (format ["HMT|GC|ECHEC|pas_assez_de_lieux|%1|il_en_faut|5", _ok]) call HMT_LOG;
    };
    "HMT|GC|TERMINE|1" call HMT_LOG;
};
