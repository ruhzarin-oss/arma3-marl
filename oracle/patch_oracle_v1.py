"""
L ORACLE COMMANDANT, version 1 ( plan a139c63, niveau 1 ) - applique sur la COPIE bancs/chacaloracle.
Niveau 0 = temoin : la mission est strictement celle d aujourd hui, octet pour octet dans son comportement.
Niveau 1 = le commandant tient une croyance sur huit cases, la met a jour par ce que SES groupes savent et par
ce qu ils ne voient pas, puis reoriente ses postes ( gratuit ) et porte sa patrouille de route vers la case la
plus probable ( 1 point de budget ).
"""
import shutil, sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
B = f"{D}/bancs/chacaloracle"
SRC = sys.argv[2] if len(sys.argv) > 2 else "/mnt/c/hmt/tmp/oracle/45_oracle.sqf"


def remplacer(chemin, ancre, nouveau, n=1):
    t = open(chemin, encoding="utf-8").read()
    assert t.count(ancre) == n, f"{chemin} : ancre {ancre[:60]!r} trouvee {t.count(ancre)} fois"
    open(chemin, "w", encoding="utf-8").write(t.replace(ancre, nouveau))


shutil.copy(SRC, f"{B}/mission.Altis/chacal/45_oracle.sqf")

remplacer(f"{B}/mission.Altis/chacal/00_socle.sqf",
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;',
 'CHACAL_SONDE = ["CHACAL_SONDE", 0] call BIS_fnc_getParamValue;\n'
 '// ! L ORACLE COMMANDANT ( plan a139c63 ). 0 = temoin, le decor d aujourd hui. 1 = il cherche.\n'
 'CHACAL_ORACLE_CMD   = ["CHACAL_ORACLE_CMD", 0] call BIS_fnc_getParamValue;\n'
 'CHACAL_ORACLE_B     = ["CHACAL_ORACLE_B", 6] call BIS_fnc_getParamValue;      // budget : nombre de deplacements de patrouille\n'
 'CHACAL_ORACLE_NU    = ["CHACAL_ORACLE_NU", 15] call BIS_fnc_getParamValue;    // doute, en pourcent : il se trompe\n'
 'CHACAL_ORACLE_EPS   = ["CHACAL_ORACLE_EPS", 15] call BIS_fnc_getParamValue;   // erreur volontaire, en pourcent\n'
 'CHACAL_ORACLE_DELTA = ["CHACAL_ORACLE_DELTA", 60] call BIS_fnc_getParamValue; // periode de decision, en secondes')

remplacer(f"{B}/mission.Altis/initServer.sqf",
 'call compile preprocessFileLineNumbers "chacal\\50_capture.sqf";',
 '// ! L Oracle est monte APRES le detachement ( il lui faut la liste pour interroger sa propre connaissance )\n'
 '// et AVANT l enregistreur, pour que ses lignes soient capturees comme les notres.\n'
 'call compile preprocessFileLineNumbers "chacal\\45_oracle.sqf";\n'
 'call compile preprocessFileLineNumbers "chacal\\50_capture.sqf";')

remplacer(f"{B}/mission.Altis/description.ext",
 '    class CHACAL_SONDE\n',
 '    class CHACAL_ORACLE_CMD\n    {\n        title = "Oracle commandant : 0 temoin, 1 il cherche";\n'
 '        values[] = {0,1}; texts[] = {"0","1"}; default = 0;\n    };\n'
 '    class CHACAL_ORACLE_B\n    {\n        title = "Oracle : budget de deplacements";\n'
 '        values[] = {0,2,4,6,8,12}; texts[] = {"0","2","4","6","8","12"}; default = 6;\n    };\n'
 '    class CHACAL_ORACLE_NU\n    {\n        title = "Oracle : doute, en pourcent";\n'
 '        values[] = {0,5,15,30}; texts[] = {"0","5","15","30"}; default = 15;\n    };\n'
 '    class CHACAL_ORACLE_EPS\n    {\n        title = "Oracle : erreur volontaire, en pourcent";\n'
 '        values[] = {0,5,15,30}; texts[] = {"0","5","15","30"}; default = 15;\n    };\n'
 '    class CHACAL_ORACLE_DELTA\n    {\n        title = "Oracle : periode de decision, en secondes";\n'
 '        values[] = {30,60,120}; texts[] = {"30","60","120"}; default = 60;\n    };\n'
 '    class CHACAL_SONDE\n')

remplacer(f"{B}/lancer.sh", 'SONDE=$(lit sonde 0)',
 'SONDE=$(lit sonde 0); ORACLE_CMD=$(lit oracle_cmd 0); ORACLE_B=$(lit oracle_b 6); ORACLE_NU=$(lit oracle_nu 15); ORACLE_EPS=$(lit oracle_eps 15); ORACLE_DELTA=$(lit oracle_delta 60)')
remplacer(f"{B}/lancer.sh", 'ecrire_param SONDE "$SONDE"',
 'ecrire_param SONDE "$SONDE"; ecrire_param ORACLE_CMD "$ORACLE_CMD"; ecrire_param ORACLE_B "$ORACLE_B"; ecrire_param ORACLE_NU "$ORACLE_NU"; ecrire_param ORACLE_EPS "$ORACLE_EPS"; ecrire_param ORACLE_DELTA "$ORACLE_DELTA"')
print("patch oracle v1 applique sur bancs/chacaloracle")
