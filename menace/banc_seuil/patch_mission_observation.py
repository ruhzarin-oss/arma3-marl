"""
Mission, fenetre d observation : DEUX LEVIERS EXPLICITES, tous deux a leur valeur d origine par defaut ( nuit du 18 au 19/09 ).
Vise une COPIE du banc ( bancs/chacalp2 ), jamais bancs/chacal.

  CHACAL_AVANT    : distance, en metres, du point d ou le detachement observe la route avant de la franchir ( origine 260 ).
                    Mesure du 18/09 : les postes de la phase 2 sont a 320-713 m des hommes, alors que de nuit la connaissance
                    d une cible debout et regardee s arrete entre 215 et 300 m. A 260 m en retrait, on n observe rien.
  CHACAL_BALAYAGE : 0 = origine ( doWatch seul sur trois azimuts, 10 s chacun ) ; 1 = balayage REPARE ( setDir puis doWatch ).
                    Mesure du 18/09 : sous doWatch seul un pivot de 24 deg prend jusqu a 90 s ; le balayage d origine ne regarde
                    donc probablement jamais ses azimuts lateraux.
  Une ligne CHACAL|E|reglage_observation dit a la lecture ce qui a ete joue, et d ou les hommes observaient.
Usage : python3 patch_mission_observation.py --racine <dossier du banc>
"""
import sys
B = sys.argv[sys.argv.index("--racine") + 1]
PH, EXT, SOC, LAN = f"{B}/mission.Altis/chacal/60_phases.sqf", f"{B}/mission.Altis/description.ext", f"{B}/mission.Altis/chacal/00_socle.sqf", f"{B}/lancer.sh"
def lire(p): return open(p, encoding="utf-8").read()
def ecrire(p, s): open(p, "w", encoding="utf-8").write(s)
def remplacer(s, a, b, quoi):
    assert s.count(a) == 1, f"ancre « {quoi} » trouvee {s.count(a)} fois"
    return s.replace(a, b)

s = lire(PH)
assert "CHACAL_AVANT" not in s, "patch deja applique"
s = remplacer(s, "private _avant = _fr getPos [260, _fr getDir CHACAL_LZ];",
              "private _avant = _fr getPos [CHACAL_AVANT, _fr getDir CHACAL_LZ];   // levier : d ou l on observe la route ( origine 260 m )", "point d observation de la route")
s = remplacer(s, "            { _x doWatch (_regards select _iRegard) } forEach (CHACAL_FS select { alive _x });\n",
              "            // ! levier CHACAL_BALAYAGE : 1 = chaque changement d azimut TOURNE les hommes ( setDir ) avant le doWatch ; 0 = origine\n"
              "            {\n"
              "                if (CHACAL_BALAYAGE == 1) then { _x setDir (_x getDir (_regards select _iRegard)) };\n"
              "                _x doWatch (_regards select _iRegard);\n"
              "            } forEach (CHACAL_FS select { alive _x });\n", "balayage de la fenetre")
ancre = '''    (format ["CHACAL|E|observation|%1|phase|%2|debut|duree_prevue|%3%4", round (time * 100) / 100, _phase, CHACAL_OBSERVATION,
        call CHACAL_fnc_perceptionMenace]) call CHACAL_LOG;
'''
s = remplacer(s, ancre, ancre + '''    (format ["CHACAL|E|reglage_observation|%1|phase|%2|avant|%3|balayage|%4|distance_secteur|%5|azimuts|%6", round (time * 100) / 100, _phase,
        CHACAL_AVANT, CHACAL_BALAYAGE, (if (count _secteur > 0) then { round (((_hommes select 0) distance2D _secteur)) } else { -1 }), count _regards]) call CHACAL_LOG;
''', "debut de la fenetre")
ecrire(PH, s)
e = lire(EXT); assert "CHACAL_AVANT" not in e
a = '''    class CHACAL_CONTROLE_DIST
    {'''
e = remplacer(e, a, '''    class CHACAL_AVANT
    {
        title = "Phase 2 : distance du point d observation avant la route, en metres ( origine 260 )";
        values[] = {260,180,120,80}; texts[] = {"260","180","120","80"}; default = 260;
    };
    class CHACAL_BALAYAGE
    {
        title = "Fenetre d observation : 0 balayage d origine ( doWatch ), 1 balayage repare ( setDir puis doWatch )";
        values[] = {0,1}; texts[] = {"0","1"}; default = 0;
    };
''' + a, "parametre CONTROLE_DIST")
ecrire(EXT, e)
c = lire(SOC); assert "CHACAL_AVANT" not in c
a = 'CHACAL_CONTROLE_DIST = ["CHACAL_CONTROLE_DIST", 150] call BIS_fnc_getParamValue;'
c = remplacer(c, a, 'CHACAL_AVANT = ["CHACAL_AVANT", 260] call BIS_fnc_getParamValue;   // phase 2 : d ou l on observe la route ( origine 260 m )\n'
              'CHACAL_BALAYAGE = ["CHACAL_BALAYAGE", 0] call BIS_fnc_getParamValue;   // fenetre : 0 balayage d origine, 1 balayage repare\n' + a, "lecture de CONTROLE_DIST")
ecrire(SOC, c)
l = lire(LAN); assert "ecrire_param AVANT" not in l
a = 'ecrire_param OBSERVATION "$OBSERVATION";'
assert l.count(a) == 1
l = l.replace(a, '# fenetre d observation : point d observation de la route et balayage, ecrits a CHAQUE lancement ( origine : 260 et 0 )\n'
              'ecrire_param AVANT "$(lit avant 260)"; ecrire_param BALAYAGE "$(lit balayage 0)"\n' + a)
ecrire(LAN, l)
print("patch mission_observation applique :", B)
