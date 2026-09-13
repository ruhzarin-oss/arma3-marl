#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-EXT
# Mon expression reguliere a insere la classe CHACAL_EXFIL A L INTERIEUR du bloc CHACAL_SOCLE :
# [^}]* s arrete a la premiere accolade fermante, celle de values[] = {0,1}. La classe etait donc
# imbriquee, BIS_fnc_getParamValue ne la trouvait pas, et rendait le defaut 0. Les six jobs de la
# campagne EXFIL jouaient tous la reference. La ligne FINI le disait : exfil|0 sur une instance dont
# le server.cfg portait CHACAL_EXFIL = 1.
# La garde d equilibre des accolades n a rien vu parce que les accolades ETAIENT equilibrees.
# Ce correctif retire la ligne mal placee et pose la classe apres la fermeture reelle de CHACAL_SOCLE.
import re, sys
p = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext"
s = open(p, encoding="utf-8", errors="surrogateescape").read()

mauvaise = '    class CHACAL_EXFIL { title = "exfil"; values[] = {0,1,2}; texts[] = {"0","1","2"}; default = 0; };\n'
if mauvaise in s:
    s = s.replace(mauvaise, "", 1)
    print("  ligne mal placee retiree")

if "CHACAL_EXFIL" in s:
    print("  !! il reste une trace de CHACAL_EXFIL, on s arrete"); sys.exit(1)

# On repere le bloc CHACAL_SOCLE en comptant les accolades, pas avec [^}]*.
i = s.index("class CHACAL_SOCLE")
j = s.index("{", i)
prof = 0
for k in range(j, len(s)):
    if s[k] == "{": prof += 1
    elif s[k] == "}":
        prof -= 1
        if prof == 0:
            fin = s.index(";", k) + 1
            break
else:
    print("  !! fin du bloc CHACAL_SOCLE introuvable"); sys.exit(1)

bloc = ('\n    class CHACAL_EXFIL\n'
        '    {\n'
        '        title = "Exfiltration : 0 = reference, 1 = AWARE apres rupture de contact, 2 = budget a 1,2 m/s";\n'
        '        values[] = {0,1,2};\n'
        '        texts[]  = {"REFERENCE","AWARE","BUDGET"};\n'
        '        default  = 0;\n'
        '    };')
s2 = s[:fin] + bloc + s[fin:]
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  classe CHACAL_EXFIL posee APRES la fermeture reelle de CHACAL_SOCLE")

# Controle : la classe doit etre au meme niveau d imbrication que CHACAL_SOCLE.
t = open(p, encoding="utf-8", errors="surrogateescape").read()
def profondeur(texte, pos):
    return texte[:pos].count("{") - texte[:pos].count("}")
a = profondeur(t, t.index("class CHACAL_SOCLE"))
b = profondeur(t, t.index("class CHACAL_EXFIL"))
print(f"  profondeur CHACAL_SOCLE = {a}, CHACAL_EXFIL = {b}", "-> OK" if a == b else "-> !! DIFFERENTES")
sys.exit(0 if a == b else 1)
