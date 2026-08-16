// chasse_couvert_en_jeu.sqf — GESTE N°3 : LE GÉOMÈTRE NE FILTRE PLUS, IL CHERCHE.
//
// ⚠️ POURQUOI CE SCRIPT EXISTE. La chasse sur carte a rendu huit traversées, et le géomètre
// les a TOUTES écartées : 0 à 38 % de pas servis, des trous de 110 à 290 m sans le moindre
// couvert dur. Les contrôles, eux, passaient — bâti dense à 100 %, pleine mer à 0 % — donc le
// compteur discrimine. Ce n'est pas Stratis qui ne porte pas le geste : c'est ma chasse qui
// était fausse. J'avais sélectionné sur « case masquée ADJACENTE » à 50 m de résolution, et
// une case adjacente peut être à 50 mètres du chemin. J'ai demandé à une carte au pas de 50 m
// de me parler d'objets à 15 m.
//
// LA RÉPARATION : le géomètre coûte une seconde par traversée et il est DANS le monde. Il
// cherche donc lui-même, au lieu de valider les propositions d'une carte trop grossière.
//
// ---------------------------------------------------------------------------------------
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
// ⚠️ « TREE » MANQUAIT, et l en-tete disait « gros troncs » depuis le debut. J avais ecrit un
// critere et code un autre : la premiere chasse a rendu 58 points servis sur 4000 — 1,5 % de
// l ile — et j allais en conclure que Stratis ne porte pas le geste. Ajouter les arbres n est
// PAS assouplir la barre : c est faire dire au code ce que le depot disait deja.
// « SMALL TREE » et « BUSH » restent dehors : ils cachent, ils ne protegent pas, et le n°3 se
// juge sur les PERTES.
HMT_DUR = ["BUILDING", "HOUSE", "WALL", "ROCK", "ROCKS", "FORTRESS", "BUNKER", "RUIN",
           "FUELSTATION", "CHAPEL", "CHURCH", "HOSPITAL", "SHIPWRECK", "TRANSMITTER",
           "TREE"];

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

    // ================================================================ LA CHASSE
    // Les criteres sont EXACTEMENT ceux deposes avant la premiere lecture, sans un mot de
    // moins : >= 70 % de pas servis, aucun trou de plus de 2 pas, >= 60 % de pas vus depuis
    // le poste. On ne les assouplit pas parce que la premiere chasse a echoue.
    private _retenus = [];
    private _essais = 0;
    private _vusServis = 0;
    // ⚠️ BUDGET RELEVE, BARRE INCHANGEE. La chasse a 4000 tirages a rendu UNE traversee
    // (92 % servis, 60 % vus, pire trou 2) en quarante secondes. La geometrie existe donc,
    // elle est simplement RARE — et pour une bonne raison : un couloir boise est servi mais
    // pas vu, un couloir ouvert est vu mais pas servi. La conjonction est exactement la
    // tension dont le geste a besoin. On cherche plus longtemps ; on ne baisse rien.
    while { count _retenus < 8 && _essais < 60000 } do {
        _essais = _essais + 1;
        private _b = [800 + random 6600, 800 + random 6600, 0];
        // le couvert d ARRIVEE doit exister : c est la condition la moins chere, on la teste
        // en premier pour ne pas payer une traversee entiere pour rien.
        if (!(surfaceIsWater _b) && {(getTerrainHeightASL _b) > 2} && {([_b] call HMT_SERVI) > 0}) then {
            _vusServis = _vusServis + 1;
            private _az = random 360;
            private _L = 150 + random 100;
            private _a = [(_b select 0) + _L * sin _az, (_b select 1) + _L * cos _az, 0];
            if (!(surfaceIsWater _a) && {(getTerrainHeightASL _a) > 2}) then {
                private _loin = _retenus findIf { (_x select 0) distance2D _b < 500 };
                if (_loin < 0) then {
                    private _m = [((_a select 0) + (_b select 0))/2, ((_a select 1) + (_b select 1))/2, 0];
                    private _ux = ((_b select 0) - (_a select 0)) / _L;
                    private _uy = ((_b select 1) - (_a select 1)) / _L;
                    private _res = [0, -1, 99]; private _poste = [];
                    {
                        private _s = _x;
                        private _q = [(_m select 0) + (-_uy) * 125 * _s, (_m select 1) + _ux * 125 * _s, 0];
                        if (!(surfaceIsWater _q)) then {
                            private _r = [_a, _b, format ["c%1_%2", _essais, _s], _q] call HMT_MESURE;
                            if ((_r select 1) > (_res select 1)) then { _res = _r; _poste = _q };
                        };
                    } forEach [1, -1];
                    if ((_res select 0) >= 70 && {(_res select 1) >= 60} && {(_res select 2) <= 2}) then {
                        _retenus pushBack [_b, _a, _poste, _res];
                        (format ["HMT|GC|RETENU|%1|couvert|%2|%3|depart|%4|%5|poste|%6|%7|servis|%8|vus|%9|piretrou|%10",
                                 count _retenus, round (_b select 0), round (_b select 1),
                                 round (_a select 0), round (_a select 1),
                                 round (_poste select 0), round (_poste select 1),
                                 _res select 0, _res select 1, _res select 2]) call HMT_LOG;
                    };
                };
            };
        };
        if (_essais % 5000 == 0) then {
            (format ["HMT|GC|chasse|%1|essais|arrivees_servies|%2|retenus|%3",
                     _essais, _vusServis, count _retenus]) call HMT_LOG;
            sleep 0.1;
        };
    };

    (format ["HMT|GC|BILAN|retenues|%1|sur|%2|essais", count _retenus, _essais]) call HMT_LOG;
    if (count _retenus >= 5) then {
        "HMT|OK|gc_assez_de_lieux|1" call HMT_LOG;
    } else {
        // ET SI LA CHASSE ECHOUE, C EST UN RESULTAT, PAS UN ECHEC DE SCRIPT : Stratis ne
        // porterait pas de traversee ou le geste n°3 soit a la fois POSSIBLE et NECESSAIRE.
        // On le dirait tel quel, et on changerait d ile plutot que d assouplir le critere.
        (format ["HMT|GC|ECHEC|pas_assez_de_lieux|%1|il_en_faut|5|sur|%2|essais",
                 count _retenus, _essais]) call HMT_LOG;
    };
    "HMT|GC|TERMINE|1" call HMT_LOG;
};
