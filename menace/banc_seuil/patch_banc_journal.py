"""
Banc de perception : JOURNALISER LA DEUXIEME VARIABLE, et ne plus payer ce qui ne sert pas au banc ( 18/09 au soir ).
S applique APRES patch_banc_vue_fine.py ( il s appuie sur ses lignes ). Ne change rien hors du mode banc, sauf la cadence de sonde.

  1. sonde toutes les 1 s pendant les 120 premieres secondes de la fenetre, 5 s ensuite ( lire finement les delais pres du seuil ) ;
  2. chaque ligne de sonde porte vis_max et vis_moy : la valeur CONTINUE de checkVisibility ( 0 a 1 ) des hommes vers le chef
     de la cible du banc. C est la candidate pour « la visibilite du lieu » ( -1 hors banc ) ;
  3. en mode banc ( controle_perception = 5 ), la fenetre se ferme 30 s apres la premiere connaissance du groupe : la suite
     n apprend rien au banc ( et de jour le detachement engage : 118 tirs a 280 m ) ;
  4. en mode banc, l episode se termine a la fin de la fenetre ( VOID, cause BANC_TERMINE ) : la traversee qui suit ne sert pas
     au banc et coutait ~5 min par episode. Un episode deja refuse ( BANC_SANS_LIGNE_DE_VUE ) garde sa cause.
Usage : python3 patch_banc_journal.py [depot]   ( vise bancs/chacalvue ; --fichier <chemin> pour une copie )
"""
import sys
if "--fichier" in sys.argv:
    P = sys.argv[sys.argv.index("--fichier") + 1]
else:
    D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
    P = f"{D}/bancs/chacalvue/mission.Altis/chacal/60_phases.sqf"
s = open(P, encoding="utf-8").read()
assert "RECHERCHE FINE" in s, "patch_banc_vue_fine.py doit etre applique avant"
assert "BANC_TERMINE" not in s, "patch deja applique"


def remplacer(s, ancre, nouveau, quoi):
    assert s.count(ancre) == 1, f"ancre « {quoi} » trouvee {s.count(ancre)} fois"
    return s.replace(ancre, nouveau)


# a. deux variables de fonction : le groupe cible du banc, et l instant de la premiere connaissance
s = remplacer(s, "    private _regards = [];\n",
              "    private _regards = [];\n    private _gBanc = grpNull; private _tConnue = -1;   // banc : groupe cible, et instant ou le groupe le connait\n",
              "declaration de _regards")

# b. retenir le groupe cible, juste apres la verification de la cible reelle
ancre_b = '''        CHACAL_MENACES pushBack [_phase, "BANC_PERCEPTION", _g];
'''
s = remplacer(s, ancre_b, ancre_b + "        _gBanc = _g;\n", "inscription de la menace du banc")

# c. dans la boucle : cadence de sonde, visibilite continue, premiere connaissance
ancre_c = '''            _prochain = time + 5;
'''
nouveau_c = '''            _prochain = time + (if ((time - _t0) < 120) then {1} else {5});   // 1 s pendant deux minutes : les delais pres du seuil
            // ! LA DEUXIEME VARIABLE : checkVisibility rend une valeur CONTINUE ( 0 a 1 ). On l ecrit telle quelle, max et moyenne
            // des hommes vers le chef de la cible du banc ; -1 hors banc. Le compte d hommes > 0,5 la jetait.
            private _visMax = -1; private _visMoy = -1;
            if (!isNull _gBanc && { alive (leader _gBanc) }) then {
                private _cB = leader _gBanc;
                private _vis = (CHACAL_FS select { alive _x }) apply { [_x, "VIEW", _cB] checkVisibility [eyePos _x, aimPos _cB] };
                if (count _vis > 0) then {
                    _visMax = (round ((selectMax _vis) * 100)) / 100;
                    private _somme = 0; { _somme = _somme + _x } forEach _vis;
                    _visMoy = (round ((_somme / (count _vis)) * 100)) / 100;
                };
            };
'''
s = remplacer(s, ancre_c, nouveau_c, "cadence de la sonde")
s = remplacer(s, '''            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3|angle_min|%4%5", round (time * 100) / 100, _phase,''',
              '''            (format ["CHACAL|E|sonde_perception|%1|phase|%2|depuis|%3|angle_min|%4%5|vis_max|%6|vis_moy|%7", round (time * 100) / 100, _phase,''',
              "format de la sonde")
s = remplacer(s, '''                call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
        };
        CHACAL_FIN || ((time - _t0) >= (CHACAL_OBSERVATION * CHACAL_ECHELLE))''',
              '''                call CHACAL_fnc_perceptionMenace, _visMax, _visMoy]) call CHACAL_LOG;
        };
        // ! BANC : des que le groupe connait la cible, 30 s de plus et on ferme. Meme test que menaces_connues ( chefs, champ 0 ).
        if ((CHACAL_CONTROLE_PERCEPTION == 5) && { !isNull _gBanc } && { _tConnue < 0 }) then {
            private _chefsB = call CHACAL_fnc_chefsDetachement;
            if (({ private _t = _x; ({ (_x targetKnowledge _t) select 0 } count _chefsB) > 0 } count ((units _gBanc) select { alive _x })) > 0) then { _tConnue = time };
        };
        CHACAL_FIN || ((time - _t0) >= (CHACAL_OBSERVATION * CHACAL_ECHELLE)) || ((_tConnue >= 0) && { (time - _tConnue) >= 30 })''',
              "fin de la boucle de la fenetre")

# d. apres la fenetre, en mode banc : l episode n a plus d objet
ancre_d = '''    (format ["CHACAL|E|observation|%1|phase|%2|fin|duree|%3%4", round (time * 100) / 100, _phase, round (time - _t0),
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
'''
nouveau_d = ancre_d + '''    // ! BANC : la traversee qui suit n apprend rien au banc. On rend l episode tout de suite ; un refus garde sa cause.
    if ((CHACAL_CONTROLE_PERCEPTION == 5) && { !CHACAL_FIN }) then { CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "BANC_TERMINE"; CHACAL_FIN = true };
'''
s = remplacer(s, ancre_d, nouveau_d, "fin de la fenetre")
open(P, "w", encoding="utf-8").write(s)
print("patch banc_journal applique :", P)
