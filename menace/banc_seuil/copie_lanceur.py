"""Fabrique le lancer.sh d une COPIE de banc : autre mission, autre dossier MPMissions, config serveur a part. Usage : src dst banc MISSION cfg"""
import sys
src, dst, banc, mission, cfg = sys.argv[1:6]
s = open(src, encoding="utf-8").read()
def r(s, a, b):
    assert s.count(a) == 1, f"« {a} » trouve {s.count(a)} fois"; return s.replace(a, b)
s = r(s, "DEP=/mnt/data/hmt/depot/bancs/chacal/mission.Altis", f"DEP=/mnt/data/hmt/depot/bancs/{banc}/mission.Altis")
s = r(s, 'MPMissions/CHACAL.Altis"', f'MPMissions/{mission}.Altis"')
s = r(s, "hmtech$INST\\server.cfg'", f"hmtech$INST\\{cfg}'")
n = s.count('"$PROFIL/server.cfg"'); assert n >= 5, n
s = s.replace('"$PROFIL/server.cfg"', '"$CFG"')
ancre = "PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))\n"
s = r(s, ancre, ancre + f'''# ! COPIE DU BANC : config serveur A PART ( {cfg} ), refaite a chaque lancement depuis le server.cfg de l instance.
# Le server.cfg partage n est JAMAIS ecrit par ce lanceur.
SRC_CFG="$PROFIL/server.cfg"; CFG="$PROFIL/{cfg}"
[ -f "$SRC_CFG" ] || {{ echo "profil hmtech$INST sans server.cfg"; exit 1; }}
cp "$SRC_CFG" "$CFG"; sed -i 's/template = "CHACAL.Altis";/template = "{mission}.Altis";/' "$CFG"
grep -q 'template = "{mission}.Altis";' "$CFG" || {{ echo "{cfg} : template non bascule"; exit 1; }}
''')
open(dst, "w", encoding="utf-8").write(s); print(f"lanceur ecrit pour {banc} ( {mission}.Altis, {cfg} ) : {n} usages de server.cfg bascules")
