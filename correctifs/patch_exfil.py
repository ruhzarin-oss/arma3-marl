#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-EXFIL
# Les 12 echecs d exfiltration de la campagne du 12/09 finissent TOUS en PLAFOND, jamais autrement, et
# les hommes sont vivants : un episode finit a 9 vivants pour 3 exfiltres. Ce n est pas un probleme de
# pertes, c est un probleme de vitesse. Le commentaire de la phase 6 l avait predit mot pour mot :
# « En COMBAT sur 1,4 a 2,4 km, 1,8 m/s de moyenne n est pas garanti meme sans ennemi ».
# L assaut compromet toujours le detachement, donc _compExf vaut TOUJOURS COMBAT, et la recolte du
# moteur dit que le chemin se calcule EN FONCTION du comportement : un homme en COMBAT ne prend pas
# le meme itineraire qu en AWARE.
# Deux causes possibles, et un seul levier pour les separer :
#   EXFIL=0  la reference, telle quelle.
#   EXFIL=1  on rompt le contact en COMBAT, puis on repasse en AWARE des que le detachement est a plus
#            de 300 m du site. Le plafond ne bouge pas. Si cela suffit, la cause est le COMPORTEMENT.
#   EXFIL=2  le comportement ne bouge pas, le budget passe de 1,8 a 1,2 m/s. Si cela suffit, la cause
#            est le CHRONOMETRE, et c est l estimation qui etait fausse, pas les hommes.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"), s.count('"') % 2)

# --- 1. le parametre ---------------------------------------------------------
p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_EXFIL " in s or "CHACAL_EXFIL=" in s:
    print("  00_socle : deja present")
else:
    a = 'CHACAL_SOCLE = ["CHACAL_SOCLE", 0] call BIS_fnc_getParamValue;'
    if a not in s: print("  !! ancre socle absente"); sys.exit(1)
    n = (a + '\n'
         '// ! CHACAL_EXFIL : ce qui fait echouer l exfiltration. 12 episodes sur 12 finissent en PLAFOND\n'
         '// avec des hommes vivants - jusqu a 9 vivants pour 3 exfiltres. Deux causes possibles, un levier\n'
         '// pour les separer. 0 = la reference. 1 = repasser en AWARE une fois le contact rompu, a plus de\n'
         '// 300 m du site, le plafond inchange : si cela suffit, la cause est le comportement. 2 = garder\n'
         '// le comportement et calculer le budget a 1,2 m/s au lieu de 1,8 : si cela suffit, la cause est\n'
         '// le chronometre, et c est l estimation qui etait fausse.\n'
         'CHACAL_EXFIL = ["CHACAL_EXFIL", 0] call BIS_fnc_getParamValue;')
    s2 = s.replace(a, n, 1)
    if bilan(s) != bilan(s2): print("  !! equilibre 00_socle"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : parametre CHACAL_EXFIL")

# --- 2. la phase 6 -----------------------------------------------------------
p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "exfil_degage" in s:
    print("  60_phases : deja present")
else:
    a = '_plafond = [(CHACAL_FS select { alive _x }), CHACAL_EXFIL_POINT, 1.8] call CHACAL_fnc_budget;'
    if a not in s: print("  !! ancre plafond absente"); sys.exit(1)
    n = ('private _vitBudget = if (CHACAL_EXFIL == 2) then {1.2} else {1.8};\n'
         '_plafond = [(CHACAL_FS select { alive _x }), CHACAL_EXFIL_POINT, _vitBudget] call CHACAL_fnc_budget;')
    s2 = s.replace(a, n, 1)

    b = 'private _compExf = if (CHACAL_COMPROMIS) then {"COMBAT"} else {"AWARE"};'
    if b not in s2: print("  !! ancre comportement absente"); sys.exit(1)
    n2 = (b + '\n'
          '// ! EXFIL=1 : on rompt le contact en COMBAT, puis on rend les jambes. La recolte du moteur du\n'
          '// 13/09 dit que le chemin se calcule en fonction du comportement ; un homme en COMBAT ne prend\n'
          '// pas le meme itineraire. Des que le detachement est a plus de 300 m du site, il repasse en\n'
          '// AWARE. Le plafond ne bouge pas : c est le comportement qu on mesure, pas le chronometre.\n'
          'if (CHACAL_EXFIL == 1) then {\n'
          '    [] spawn {\n'
          '        private _t0 = time;\n'
          '        waitUntil { sleep 5;\n'
          '            private _v = CHACAL_FS select { alive _x };\n'
          '            (count _v == 0) || CHACAL_FIN || ((time - _t0) > 900) ||\n'
          '            ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE > 300) };\n'
          '        if (CHACAL_FIN) exitWith {};\n'
          '        private _v = CHACAL_FS select { alive _x };\n'
          '        if (count _v == 0) exitWith {};\n'
          '        { if (!isNull _x) then { _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"; _x setSpeedMode "FULL";\n'
          '            { if (alive _x) then { _x setUnitPos "AUTO" } } forEach (units _x) } }\n'
          '          forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];\n'
          '        (format ["CHACAL|E|exfil_degage|%1|distance_site|%2|vivants|%3|comportement|AWARE",\n'
          '            round (time * 100) / 100, round ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE),\n'
          '            count _v]) call CHACAL_LOG;\n'
          '    };\n'
          '};')
    s3 = s2.replace(b, n2, 1)
    if bilan(s) != bilan(s3): print("  !! equilibre 60_phases %s -> %s" % (bilan(s), bilan(s3))); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 60_phases : rupture puis AWARE, et budget selon le levier")

# --- 3. la ligne FINI --------------------------------------------------------
p = f"{M}/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "|exfil|%46" in s:
    print("  70_verdict : deja present")
else:
    a = "|placeur|%44|couverture|%45"
    if a not in s: print("  !! ancre FINI absente"); sys.exit(1)
    s2 = s.replace(a, a + "|exfil|%46", 1)
    b = "CHACAL_PLACEUR, CHACAL_COUV]) call CHACAL_LOG;"
    if b not in s2: print("  !! ancre valeurs FINI absente"); sys.exit(1)
    s3 = s2.replace(b, "CHACAL_PLACEUR, CHACAL_COUV, CHACAL_EXFIL]) call CHACAL_LOG;", 1)
    if bilan(s) != bilan(s3): print("  !! equilibre 70_verdict"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 70_verdict : exfil dans la ligne FINI")

# --- 4. description.ext ------------------------------------------------------
p = f"{M}/../description.ext"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_EXFIL" in s:
    print("  description.ext : deja present")
else:
    import re
    m = re.search(r'class CHACAL_SOCLE\s*\{[^}]*\};', s, re.S)
    if not m: print("  !! classe CHACAL_SOCLE absente de description.ext"); sys.exit(1)
    bloc = m.group(0)
    n = bloc + '\n    class CHACAL_EXFIL { title = "exfil"; values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0; };'
    s2 = s.replace(bloc, n, 1)
    if bilan(s) != bilan(s2): print("  !! equilibre description.ext"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : description.ext : CHACAL_EXFIL")

# --- 5. lancer.sh ------------------------------------------------------------
# Le lanceur lit ses parametres avec la fonction `lit` et les ecrit avec `ecrire_param`, tous sur
# une seule ligne chacun. On se greffe sur SOCLE, qui est du meme type : un entier venu du job.
p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "EXFIL" in s:
    print("  lancer.sh : deja present")
else:
    a = "SOCLE=$(lit socle 0);"
    b = 'ecrire_param SOCLE "$SOCLE";'
    if a not in s or b not in s:
        print("  !! ancres lancer.sh absentes"); sys.exit(1)
    s2 = s.replace(a, a + " EXFIL=$(lit exfil 0);", 1)
    s3 = s2.replace(b, b + ' ecrire_param EXFIL "$EXFIL";', 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : lancer.sh : lecture et ecriture de exfil")
