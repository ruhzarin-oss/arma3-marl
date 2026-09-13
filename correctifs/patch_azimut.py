#!/usr/bin/env python3
# MARQUEUR-COUTURE-AZIMUT
# LA PREMIERE COUTURE OU UN AGENT PEUT DECIDER.
#
# Pourquoi l azimut, et pourquoi celui-la d abord.
#   L atelier MCP du 13/09, cinq essais par bras, a mesure que l axe d approche commande l entree
#   dans l enceinte : azimut 45, ZERO entree sur cinq essais ; azimut 0, 3,8 entrees en moyenne ;
#   azimut 126, 2,6. C est la seule decision de la mission dont on connaisse deja l ampleur de
#   l effet, donc la seule ou l on saura dire si un agent fait mieux que le hasard.
#   Et le script s interdit des options qui marchent : il ne choisit qu entre les DEUX ouvertures
#   de l enceinte, alors que le mur plein a l azimut 0 fait mieux que l ouverture a 126.
#
# Ce que la couture fait.
#   Elle publie DOUZE azimuts candidats, tous les 30 degres, et laisse un decideur en choisir un.
#   Le decideur est designe par CHACAL_AZIMUT :
#     0  SCRIPT  - le comportement actuel, inchange : le score sur les deux ouvertures.
#     1  HASARD  - tirage uniforme parmi les douze. C EST LE PLANCHER, et il est obligatoire :
#                  sans lui, un agent qui fait 47 % serait indistinguable d un agent qui devine.
#     2  IMPOSE  - l azimut vient du job, en degres, dans CHACAL_AZIMUT_VAL. C est par la qu un
#                  agent decide : il lit le site, il calcule, il ecrit le job.
#
# Pourquoi le mode IMPOSE plutot qu un pont vivant.
#   La decision est prise UNE FOIS, avant le contact, et elle ne depend que de la geometrie du site,
#   qui est une fonction deterministe de la graine. Un agent n a donc pas besoin de parler a la
#   mission pendant qu elle tourne : il lui suffit de decider avant. Pas de pont, pas de delai
#   d attente, pas de repli silencieux qui ferait passer le script pour l agent.
#
# Le tirage du mode HASARD utilise CHACAL_fnc_rnd, le generateur seme par la graine : deux episodes
# de meme graine tirent le meme azimut. Le hasard est reproductible, sinon ce n est pas un temoin.
import re, sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)

# --- 1. les parametres --------------------------------------------------------
p = f"{M}/chacal/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_AZIMUT " in s or "CHACAL_AZIMUT=" in s:
    print("  00_socle : deja present")
else:
    a = 'CHACAL_SOCLE = ["CHACAL_SOCLE", 0] call BIS_fnc_getParamValue;'
    if a not in s: print("  !! ancre socle absente"); sys.exit(1)
    n = (a + '\n'
         '// ! LA COUTURE DE L AZIMUT. C est le premier endroit de la mission ou un agent decide.\n'
         '// L atelier du 13/09 a mesure que l axe d approche commande l entree : azimut 45, zero entree\n'
         '// sur cinq essais ; azimut 0, 3,8 en moyenne ; azimut 126, 2,6. Le script, lui, ne choisit\n'
         '// qu entre les deux ouvertures - il s interdit le mur plein a l azimut 0, qui fait mieux.\n'
         '//   0 SCRIPT : le score sur les deux ouvertures, inchange.\n'
         '//   1 HASARD : tirage uniforme parmi douze azimuts. LE PLANCHER, et il est obligatoire.\n'
         '//   2 IMPOSE : l azimut vient du job, en degres. C est par la qu un agent decide.\n'
         'CHACAL_AZIMUT = ["CHACAL_AZIMUT", 0] call BIS_fnc_getParamValue;\n'
         'CHACAL_AZIMUT_VAL = ["CHACAL_AZIMUT_VAL", 0] call BIS_fnc_getParamValue;\n'
         'CHACAL_AZIMUT_CHOISI = -1;   // ce qui a REELLEMENT ete joue, ecrit dans la ligne FINI')
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 00_socle"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : CHACAL_AZIMUT, CHACAL_AZIMUT_VAL, CHACAL_AZIMUT_CHOISI")

# --- 2. la decision, juste apres le choix du script ---------------------------
p = f"{M}/chacal/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_AZIMUT" in s:
    print("  60_phases : deja present")
else:
    a = '''    CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select _meilleure;
    (format ["CHACAL|E|choix_ouverture|%1|indice|%2|gardes|%3|distances|%4|score|%5|renseignement|%6",'''
    if a not in s: print("  !! ancre choix_ouverture absente"); sys.exit(1)
    n = '''    CHACAL_OUV_CHOISIE = CHACAL_OUVERTURES select _meilleure;
    // ! LA COUTURE DE L AZIMUT. Douze candidats publies, un decideur designe par CHACAL_AZIMUT.
    // Le mode 0 ne touche a rien : CHACAL_OUV_CHOISIE garde la valeur que le score vient de poser.
    // Les modes 1 et 2 remplacent le POINT VISE par un point de meme rayon a l azimut retenu, ce qui
    // laisse intact tout ce qui en depend en aval : la position d assaut, la cible, le poste d appui.
    private _candidats = [];
    for "_i" from 0 to 11 do { _candidats pushBack (_i * 30) };
    CHACAL_AZIMUT_CHOISI = round (CHACAL_SITE getDir CHACAL_OUV_CHOISIE);
    private _qui = "SCRIPT";
    if (CHACAL_AZIMUT == 1) then {
        // tirage seme par la graine : deux episodes de meme graine tirent le meme azimut, sinon
        // le temoin ne serait pas un temoin.
        private _k = floor ((call CHACAL_fnc_rnd) * (count _candidats));
        if (_k >= count _candidats) then { _k = (count _candidats) - 1 };
        CHACAL_AZIMUT_CHOISI = _candidats select _k; _qui = "HASARD";
    };
    if (CHACAL_AZIMUT == 2) then {
        CHACAL_AZIMUT_CHOISI = ((round CHACAL_AZIMUT_VAL) + 360) % 360; _qui = "IMPOSE";
    };
    if (CHACAL_AZIMUT > 0) then {
        CHACAL_OUV_CHOISIE = CHACAL_SITE getPos [CHACAL_RAYON, CHACAL_AZIMUT_CHOISI];
        CHACAL_OUV_CHOISIE set [2, 0];
    };
    (format ["CHACAL|E|couture_azimut|%1|mode|%2|decideur|%3|candidats|%4|choisi|%5|point|%6|az_ouvertures|%7",
        round (time * 100) / 100, CHACAL_AZIMUT, _qui, count _candidats, CHACAL_AZIMUT_CHOISI,
        CHACAL_OUV_CHOISIE, (CHACAL_OUVERTURES apply { round (CHACAL_SITE getDir _x) })]) call CHACAL_LOG;
    (format ["CHACAL|E|choix_ouverture|%1|indice|%2|gardes|%3|distances|%4|score|%5|renseignement|%6",'''
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 60_phases", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 60_phases : la couture, douze candidats, trois decideurs")

# --- 3. la ligne FINI ---------------------------------------------------------
p = f"{M}/chacal/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "|azimut_mode|" in s:
    print("  70_verdict : deja present")
else:
    a = "|exfil|%46"
    if a not in s: print("  !! ancre FINI absente"); sys.exit(1)
    s2 = s.replace(a, a + "|azimut_mode|%47|azimut|%48", 1)
    b = "CHACAL_COUV, CHACAL_EXFIL]) call CHACAL_LOG;"
    if b not in s2: print("  !! ancre valeurs absente"); sys.exit(1)
    s3 = s2.replace(b, "CHACAL_COUV, CHACAL_EXFIL, CHACAL_AZIMUT, CHACAL_AZIMUT_CHOISI]) call CHACAL_LOG;", 1)
    if bil(s) != bil(s3): print("  !! equilibre 70_verdict"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 70_verdict : azimut_mode et azimut dans la ligne FINI")

# --- 4. description.ext, au BON niveau -----------------------------------------
# Lecon du 13/09 : une expression reguliere avait imbrique une classe dans une autre, la mission
# lisait le defaut, et six jobs ont joue la reference. On compte les accolades, et on VERIFIE.
p = f"{M}/description.ext"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_AZIMUT" in s:
    print("  description.ext : deja present")
else:
    i = s.index("class CHACAL_SOCLE"); j = s.index("{", i); prof = 0
    for k in range(j, len(s)):
        if s[k] == "{": prof += 1
        elif s[k] == "}":
            prof -= 1
            if prof == 0:
                fin = s.index(";", k) + 1; break
    bloc = ('\n    class CHACAL_AZIMUT\n    {\n'
            '        title = "Azimut d assaut : 0 = script, 1 = hasard (plancher), 2 = impose par le job";\n'
            '        values[] = {0,1,2};\n        texts[]  = {"SCRIPT","HASARD","IMPOSE"};\n        default  = 0;\n    };\n'
            '    class CHACAL_AZIMUT_VAL\n    {\n'
            '        title = "Azimut impose, en degres (mode 2)";\n'
            '        values[] = {0,30,60,90,120,150,180,210,240,270,300,330};\n'
            '        texts[]  = {"0","30","60","90","120","150","180","210","240","270","300","330"};\n'
            '        default  = 0;\n    };')
    s2 = s[:fin] + bloc + s[fin:]
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    t = open(p, encoding="utf-8", errors="surrogateescape").read()
    prof_of = lambda nom: t[:t.index(nom)].count("{") - t[:t.index(nom)].count("}")
    a1, a2, a3 = prof_of("class CHACAL_SOCLE"), prof_of("class CHACAL_AZIMUT"), prof_of("class CHACAL_AZIMUT_VAL")
    print(f"  PATCHE : description.ext : deux classes ajoutees")
    print(f"  controle d imbrication : SOCLE={a1}, AZIMUT={a2}, AZIMUT_VAL={a3}",
          "-> OK" if a1 == a2 == a3 else "-> !! DIFFERENTES")
    if not (a1 == a2 == a3): sys.exit(1)

# --- 5. lancer.sh --------------------------------------------------------------
p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "AZIMUT" in s:
    print("  lancer.sh : deja present")
else:
    a = "SOCLE=$(lit socle 0);"
    b = 'ecrire_param SOCLE "$SOCLE";'
    if a not in s or b not in s: print("  !! ancres lancer.sh absentes"); sys.exit(1)
    s = s.replace(a, a + " AZIMUT=$(lit azimut 0); AZIMUT_VAL=$(lit azimut_val 0);", 1)
    s = s.replace(b, b + ' ecrire_param AZIMUT "$AZIMUT"; ecrire_param AZIMUT_VAL "$AZIMUT_VAL";', 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  PATCHE : lancer.sh : lecture et ecriture de azimut et azimut_val")

# --- 6. le controle d identite doit relire les deux ----------------------------
p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if '"azimut"' in s:
    print("  lancer.sh : leviers deja controles")
else:
    a = '"banc_appui","placeur","exfil")'
    if a not in s: print("  !! ancre LEVIERS_CONTROLES absente"); sys.exit(1)
    s2 = s.replace(a, '"banc_appui","placeur","exfil","azimut")', 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : lancer.sh : azimut entre dans LEVIERS_CONTROLES")
