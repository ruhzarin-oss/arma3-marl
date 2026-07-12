"""leak_probe — churn N spawns sur UN serveur (srv 0, sans reboot) et mesure les compteurs serveur
apres chaque op : groupes / unites / groupes vides / marqueurs. Si ca grimpe -> fuite confirmee + identifiee."""
import re
import officer_geo as OG

def counts(env):
    sqf = ('diag_log format ["HMT_LEAK g=%1 u=%2 eg=%3 m=%4", count allGroups, count allUnits, '
           'count (allGroups select {count units _x == 0}), count allMapMarkers];')
    for ln in reversed(env._query(sqf)):
        mm = re.search(r"HMT_LEAK g=(\d+) u=(\d+) eg=(\d+) m=(\d+)", ln)
        if mm:
            return tuple(int(mm.group(k)) for k in range(1, 5))
    return None

print("op | groupes unites groupes_vides marqueurs", flush=True)
for i in range(12):
    env, garr = OG.setup(0, 7000 + i, "standard")   # spawn sur srv 0, SANS reboot ni close -> churn
    c = counts(env)
    print("%2d | %s" % (i, c), flush=True)
