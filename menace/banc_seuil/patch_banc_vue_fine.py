"""
Banc de perception : CHERCHER MIEUX la ligne de vue avant de refuser ( 18/09, propose par la session du balayage TROU ).

Mesure du 18/09 apres-midi : 3 episodes sur 4 sans ligne de vue a 225-300 m. La recherche ne testait que 18 azimuts,
a UNE distance exacte, depuis le SEUL chef, alors que dix hommes regardent. Ce patch :
  1. teste 72 azimuts ( pas de 5 deg ) x 5 distances ( demandee, -3 %, +3 %, -6 %, +6 % ) = 360 candidats ;
  2. compte les HOMMES qui voient le point ( un rayon par homme, depuis ses yeux ) et garde le candidat que le plus
     d hommes voient ; a egalite le premier teste gagne, donc la distance demandee ;
  3. ligne_de_vue = 1 seulement si AU MOINS LA MOITIE des hommes voient le point ;
  4. sinon : ligne banc_refuse ( meme debut que patch_banc_refuse.py, le lecteur lire_banc.sh marche tel quel ) et,
     en mode banc ( controle_perception = 5 ), l episode est rendu VOID tout de suite au lieu de tourner 300 s a vide ;
  5. apres la pose, verifie la cible REELLE avec checkVisibility ( autre noyau que lineIntersectsSurfaces ) et journalise
     hommes_avec_vue, vue_reelle et distance_posee en fin de ligne banc_perception.

REMPLACE patch_banc_refuse.py : s applique que ce dernier ait deja ete joue ou non ( les deux ordres essayes a blanc ).
Usage : python3 patch_banc_vue_fine.py [depot]     ( ecrit 60_phases.sqf ; --fichier <chemin> pour viser une copie )
"""
import sys
args = [a for a in sys.argv[1:] if a != "--fichier"]
if "--fichier" in sys.argv:
    P = sys.argv[sys.argv.index("--fichier") + 1]
else:
    D = args[0] if args else "/mnt/data/hmt/depot"
    P = f"{D}/bancs/chacal/mission.Altis/chacal/60_phases.sqf"
s = open(P, encoding="utf-8").read()
assert "RECHERCHE FINE" not in s, "patch deja applique"


def remplacer(s, ancre, nouveau, quoi):
    assert s.count(ancre) == 1, f"ancre « {quoi} » trouvee {s.count(ancre)} fois"
    return s.replace(ancre, nouveau)


# 1. la recherche : 18 azimuts depuis le chef -> 360 candidats, juges par le nombre d hommes qui voient
recherche_ancienne = '''        private _az = getDir _chef; private _trouve = false;
        {
            private _p = _chef getPos [CHACAL_CONTROLE_DIST, _x];
            private _cible = (ATLToASL _p) vectorAdd [0, 0, 1.6];
            if (!_trouve && { (count (lineIntersectsSurfaces [_oeil, _cible, _chef, objNull, true, 1, "VIEW", "VIEW"])) == 0 }) then { _az = _x; _trouve = true };
        } forEach [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340];
'''
recherche_fine = '''        private _az = getDir _chef; private _trouve = false;
        // ! RECHERCHE FINE ( 18/09 : 3 episodes sur 4 sans ligne de vue a 225-300 m, avec 18 azimuts testes depuis le seul
        // chef ). 72 azimuts x 5 distances ( +-6 % ) ; on compte les HOMMES qui voient le point et on garde le candidat
        // que le plus d hommes voient. A egalite le premier gagne : la distance demandee passe donc avant les autres.
        private _dPose = CHACAL_CONTROLE_DIST; private _nVue = 0; private _nH = count _hommes; private _vueReelle = -1;
        {
            private _d = CHACAL_CONTROLE_DIST * _x;
            for "_a" from 0 to 355 step 5 do {
                if (_nVue < _nH) then {
                    private _pC = _chef getPos [_d, _a];
                    private _cible = (ATLToASL _pC) vectorAdd [0, 0, 1.6];
                    if (!(surfaceIsWater _pC) && { !(terrainIntersectASL [_oeil, _cible]) }) then {
                        private _n = { (count (lineIntersectsSurfaces [eyePos _x, _cible, _x, objNull, true, 1, "VIEW", "VIEW"])) == 0 } count _hommes;
                        if (_n > _nVue) then { _nVue = _n; _az = _a; _dPose = _d };
                    };
                };
            };
        } forEach [1, 0.97, 1.03, 0.94, 1.06];
        _trouve = (_nVue * 2) >= _nH;
'''
s = remplacer(s, recherche_ancienne, recherche_fine, "recherche de la ligne de vue")

# 2. le refus : on retire celui de patch_banc_refuse.py s il est la, puis on pose le notre ( VOID en mode banc )
refus_ancien = '''        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE ( mesure du 18/09 ) : poser la cible derriere un obstacle mesurerait le relief,
            // pas la perception. On refuse l episode plutot que de le polluer.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE", round (time * 100) / 100,
                _phase, CHACAL_CONTROLE_DIST]) call CHACAL_LOG;
        };
'''
if refus_ancien in s:
    s = remplacer(s, refus_ancien, "", "refus de patch_banc_refuse.py")
    print("refus de patch_banc_refuse.py retire ( remplace )")
assert "banc_refuse" not in s, "un autre refus existe deja : relire avant d appliquer"
pose_ancienne = '''        private _p = _chef getPos [CHACAL_CONTROLE_DIST, _az];
        private _g = createGroup east;'''
pose_nouvelle = '''        if (!_trouve) exitWith {
            // ! AUCUNE LIGNE DE VUE, MEME APRES 360 CANDIDATS : poser la cible mesurerait le relief, pas la perception.
            // En mode banc l episode n a plus d objet : on le rend VOID tout de suite au lieu de tourner 300 s a vide.
            (format ["CHACAL|E|banc_refuse|%1|phase|%2|distance|%3|cause|AUCUNE_LIGNE_DE_VUE|hommes_avec_vue|%4|hommes|%5",
                round (time * 100) / 100, _phase, CHACAL_CONTROLE_DIST, _nVue, _nH]) call CHACAL_LOG;
            if (CHACAL_CONTROLE_PERCEPTION == 5) then { CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "BANC_SANS_LIGNE_DE_VUE"; CHACAL_FIN = true };
        };
        private _p = _chef getPos [_dPose, _az];
        private _g = createGroup east;'''
s = remplacer(s, pose_ancienne, pose_nouvelle, "pose de la cible")

# 3. la cible REELLE : createUnit la pose a 3 m pres du point teste ; second instrument, independant du premier
menace_ancienne = '''        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
'''
menace_nouvelle = '''        // ! LA CIBLE REELLE : createUnit la pose a 3 m pres du point teste. checkVisibility est un AUTRE noyau que
        // lineIntersectsSurfaces : on journalise les deux, et un desaccord entre eux est une information.
        _vueReelle = { ([_x, "VIEW", leader _g] checkVisibility [eyePos _x, aimPos (leader _g)]) > 0.5 } count _hommes;
        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
'''
s = remplacer(s, menace_ancienne, menace_nouvelle, "inscription de la menace du banc")

# 4. la ligne banc_perception : trois champs EN FIN de ligne ( le lecteur existant lit toujours ligne_de_vue )
s = remplacer(s, '|lune|%7|jumelles|%8|hommes|%9",',
              '|lune|%7|jumelles|%8|hommes|%9|hommes_avec_vue|%10|vue_reelle|%11|distance_posee|%12",', "format banc_perception")
s = remplacer(s, '((_hommes apply { hmd _x }) joinString ","), count _hommes]) call CHACAL_LOG;',
              '((_hommes apply { hmd _x }) joinString ","), count _hommes, _nVue, _vueReelle, round _dPose]) call CHACAL_LOG;',
              "arguments banc_perception")
open(P, "w", encoding="utf-8").write(s)
print("patch banc_vue_fine applique :", P)
