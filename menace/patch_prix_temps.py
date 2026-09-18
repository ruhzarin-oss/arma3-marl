"""
Test independant du PRIX DU TEMPS ( saisine de Fable, 18/09 ) : le detachement attend N secondes AVANT la phase 5,
hors de tout plafond de phase, puis la mission continue normalement. Si la reussite ne baisse pas, le temps est gratuit
dans ce monde, et le rapport tau de la forme proposee par Fable n est pas identifiable.
CHACAL_ATTENTE_TEST = 0 ( origine ), 300, 600 ou 1200 secondes. Ne touche a rien d autre.
"""
import sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B, O = f"{D}/bancs/chacal", f"{D}/outils"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:70]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;',
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;\n'
 '// ! PRIX DU TEMPS ( saisine de Fable, 18/09 ) : attente imposee AVANT la phase 5, hors plafond de phase. 0 = origine.\n'
 'CHACAL_ATTENTE_TEST = ["CHACAL_ATTENTE_TEST", 0] call BIS_fnc_getParamValue;')

remplacer(f"{B}/mission.Altis/chacal/60_phases.sqf",
 '''CHACAL_SAUT = false;
_plafond = 5 call CHACAL_fnc_duree;
[5, "ASSAUT", _plafond] call CHACAL_fnc_debutPhase;''',
 '''CHACAL_SAUT = false;
// ! PRIX DU TEMPS : l attente est prise AVANT le debut de la phase, donc elle ne mange aucun plafond. Le seul cout
// possible est celui du monde qui tourne ( patrouilles, alarme, renfort ) - c est justement ce qu on veut mesurer.
if (CHACAL_ATTENTE_TEST > 0) then {
    private _tA = time;
    (format ["CHACAL|E|attente_test|%1|debut|duree_prevue|%2|vivants|%3|alarme|%4", round (time * 100) / 100,
        CHACAL_ATTENTE_TEST, count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0})]) call CHACAL_LOG;
    waitUntil { sleep 2; CHACAL_FIN || ((time - _tA) >= (CHACAL_ATTENTE_TEST * CHACAL_ECHELLE)) };
    (format ["CHACAL|E|attente_test|%1|fin|duree|%2|vivants|%3|alarme|%4|compromis|%5", round (time * 100) / 100,
        round (time - _tA), count (CHACAL_FS select { alive _x }), (if (CHACAL_ALARME) then {1} else {0}),
        (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
};
_plafond = 5 call CHACAL_fnc_duree;
[5, "ASSAUT", _plafond] call CHACAL_fnc_debutPhase;''')

remplacer(f"{B}/mission.Altis/description.ext",
 '    class CHACAL_SONDE\n    {\n        title = "Sonde de perception : 1 = une ligne toutes les 5 s pendant la fenetre d observation";\n        values[] = {0,1}; texts[] = {"0","1"}; default = 0;\n    };\n',
 '    class CHACAL_SONDE\n    {\n        title = "Sonde de perception : 1 = une ligne toutes les 5 s pendant la fenetre d observation";\n        values[] = {0,1}; texts[] = {"0","1"}; default = 0;\n    };\n'
 '    class CHACAL_ATTENTE_TEST\n    {\n        title = "Prix du temps : attente imposee avant la phase 5, en secondes (0 = origine)";\n'
 '        values[] = {0,300,600,1200}; texts[] = {"0","300","600","1200"}; default = 0;\n    };\n')
remplacer(f"{B}/lancer.sh", 'SONDE=$(lit sonde 0)', 'SONDE=$(lit sonde 0); ATTENTE_TEST=$(lit attente_test 0)')
remplacer(f"{B}/lancer.sh", 'ecrire_param SONDE "$SONDE"', 'ecrire_param SONDE "$SONDE"; ecrire_param ATTENTE_TEST "$ATTENTE_TEST"')
remplacer(f"{O}/verifier_valeurs.py", '"sonde": "CHACAL_SONDE",', '"sonde": "CHACAL_SONDE", "attente_test": "CHACAL_ATTENTE_TEST",')
print("patch prix du temps applique")
