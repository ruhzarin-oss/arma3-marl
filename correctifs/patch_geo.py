#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-GEOMETRIE-SEULE
# CHACAL_GEOMETRIE : la mission rend sa geometrie et s arrete, sans jouer un seul coup de feu.
#
# POURQUOI. Le decideur d azimut doit noter douze azimuts a partir de la geometrie d un site AVANT
# de l avoir joue. Pour les huit graines juges, c est indispensable : jouer un episode pour connaitre
# leur geometrie les userait au moment meme ou l on veut qu elles soient vierges.
#
# POURQUOI PAS UNE REPLIQUE. J ai d abord reecrit le tirage du monde au labo. Le controle positif l a
# refusee : 0 site retrouve sur 4, avec des ecarts de 2,8 a 13 km. Cause lue ensuite dans le code :
# CHACAL_fnc_plat tire sqrt(rnd) * r la ou j avais ecrit rnd * r, evalue huit voisins a 20 m et non
# six a 12, et penalise les maisons. Meme nombre de tirages, positions differentes.
# Et meme reparee, une replique serait une dette : elle deriverait en silence au premier changement
# de la mission, et on ne le verrait que des mois plus tard.
#
# LA BONNE PIECE. On demande a la mission son propre tirage. C est exact par construction, ca ne peut
# pas deriver, et ca coute une quarantaine de secondes au lieu de dix minutes.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)

p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_GEOMETRIE" in s:
    print("  00_socle : deja present")
else:
    a = 'CHACAL_OBS = ["CHACAL_OBS", 1] call BIS_fnc_getParamValue;'
    if a not in s:
        a = 'CHACAL_AZIMUT = ["CHACAL_AZIMUT", 0] call BIS_fnc_getParamValue;'
    if a not in s: print("  !! ancre absente"); sys.exit(1)
    n = (a + '\n'
         '// ! CHACAL_GEOMETRIE : rendre la geometrie du site SANS jouer la mission.\n'
         '// Le decideur d azimut doit noter douze azimuts avant l episode ; pour les graines juges,\n'
         '// jouer pour connaitre la geometrie les userait au moment ou on les veut vierges.\n'
         '// A 1, la mission tire son monde, ecrit une ligne GEO, et s arrete. Une quarantaine de\n'
         '// secondes, et c est le VRAI tirage - pas une replique qui deriverait en silence.\n'
         'CHACAL_GEOMETRIE = ["CHACAL_GEOMETRIE", 0] call BIS_fnc_getParamValue;')
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : parametre CHACAL_GEOMETRIE")

p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "GEOMETRIE_SEULE" in s:
    print("  60_phases : deja present")
else:
    import re
    m = re.search(r'^\[1, "INSERTION"[^\n]*$', s, re.M)
    if m:
        anc = m.group(0); pos = m.start()
    else:
        m2 = re.search(r'^[^\n]*CHACAL_fnc_debutPhase;[^\n]*$', s, re.M)
        if not m2: print("  !! aucune ancre de phase 1"); sys.exit(1)
        anc = m2.group(0); pos = m2.start()
    bloc = ('// ! GEOMETRIE SEULE : le monde est tire, on le publie, et on s arrete. Aucun coup de feu,\n'
            '// aucune issue de mission. C est la facon exacte de connaitre un site sans l user.\n'
            'if (CHACAL_GEOMETRIE == 1) exitWith {\n'
            '    (format ["CHACAL|GEO|%1|graine|%2|site|%3|crete|%4|route|%5|lz|%6|qrf|%7|pz|%8|rally|%9|ouvertures|%10|az_site|%11|gain_crete|%12",\n'
            '        round (time * 100) / 100, CHACAL_GRAINE, CHACAL_SITE, CHACAL_OP, CHACAL_ROUTE,\n'
            '        CHACAL_LZ, CHACAL_QRF_BASE, CHACAL_PZ, CHACAL_RALLY,\n'
            '        (if (isNil "CHACAL_OUVERTURES") then {[]} else {CHACAL_OUVERTURES apply { round (CHACAL_SITE getDir _x) }}),\n'
            '        (if (isNil "CHACAL_AZ") then {-1} else {round CHACAL_AZ}), round CHACAL_OP_GAIN]) call CHACAL_LOG;\n'
            '    CHACAL_ISSUE = "VOID"; CHACAL_CAUSE = "GEOMETRIE_SEULE"; CHACAL_FIN = true;\n'
            '};\n\n')
    s2 = s[:pos] + bloc + s[pos:]
    if bil(s) != bil(s2): print("  !! equilibre 60_phases", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print(f"  PATCHE : 60_phases : sortie GEOMETRIE_SEULE avant « {anc[:48]}... »")

p = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_GEOMETRIE" in s:
    print("  description.ext : deja present")
else:
    i = s.index("class CHACAL_AZIMUT"); j = s.index("{", i); prof = 0
    for k in range(j, len(s)):
        if s[k] == "{": prof += 1
        elif s[k] == "}":
            prof -= 1
            if prof == 0: fin = s.index(";", k) + 1; break
    bloc = ('\n    class CHACAL_GEOMETRIE\n    {\n'
            '        title = "Geometrie seule : 1 = tirer le monde, le publier, et s arreter";\n'
            '        values[] = {0,1};\n        texts[]  = {"NON","OUI"};\n        default  = 0;\n    };')
    s2 = s[:fin] + bloc + s[fin:]
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    t = open(p, encoding="utf-8", errors="surrogateescape").read()
    pr = lambda n: t[:t.index(n)].count("{") - t[:t.index(n)].count("}")
    a1, a2 = pr("class CHACAL_AZIMUT"), pr("class CHACAL_GEOMETRIE")
    print(f"  PATCHE : description.ext | imbrication AZIMUT={a1} GEOMETRIE={a2}", "-> OK" if a1 == a2 else "-> !! DIFFERENTES")
    if a1 != a2: sys.exit(1)

p = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "GEOMETRIE" in s:
    print("  lancer.sh : deja present")
else:
    a = "AZIMUT=$(lit azimut 0);"
    b = 'ecrire_param AZIMUT "$AZIMUT";'
    if a not in s or b not in s: print("  !! ancres absentes"); sys.exit(1)
    s = s.replace(a, a + " GEOMETRIE=$(lit geometrie 0);", 1)
    s = s.replace(b, b + ' ecrire_param GEOMETRIE "$GEOMETRIE";', 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  PATCHE : lancer.sh : geometrie lue et ecrite")
