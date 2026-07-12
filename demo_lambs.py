"""demo_lambs — montre la différence LAMBS vs vanilla, mesurée. 10 attaquants (IA PURE, pas de cerveau RL :
c'est LAMBS/vanilla qui décide) lancés en SAD sur 10 défenseurs dans Paros. On mesure l'ETALEMENT LATERAL
(débordement : LAMBS contourne large, la vanilla fonce en ligne), l'avance, l'entrée dans le bâti, et l'issue.
Usage : demo_lambs.py <srv> <label>"""
import time, re, sys
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
srv = int(sys.argv[1]) if len(sys.argv) > 1 else 0
label = sys.argv[2] if len(sys.argv) > 2 else "?"
OBJ = M.COMPLEXE
START = (OBJ[0], OBJ[1] - 220)
env = OpArma(squads=(("ATQ", 10),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % srv,
             log=SB + "/logs/server%d.out" % srv, acc=1.0, seed=5)
print("[%s srv%d] 10 attaquants a 220m sud -> SAD sur 10 defenseurs dans Paros" % (label, srv), flush=True)
env.spawn({"ATQ": START}, [(OBJ[0], OBJ[1], 10, 35)])
env.b.send('private _g = group (ATQ select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g,0]};'
           'private _wp = _g addWaypoint [[%d,%d],0]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "NORMAL";'
           '_g setBehaviour "COMBAT"; _g setCombatMode "RED";' % (OBJ[0], OBJ[1]), wait=True)
time.sleep(2)
print("t | ATQ | DEF | etal_lateral(m) | avance(m) | atq_bati", flush=True)
lat_max = 0
for i in range(1, 41):
    time.sleep(3)
    env.read()
    al = env.alive(0); eal = env.en_alive()
    if al.any():
        lat = int(env.px[0][al].std()); adv = int(env.py[0][al].mean() - START[1])
        lat_max = max(lat_max, lat)
    else:
        lat = adv = -1
    ls = env._query('private _h = { (alive _x) && {(count (_x nearObjects ["House",10])) > 0} } count ATQ; diag_log format ["HMTB bati=%1", _h];', settle=0.5)
    bati = -1
    for l in ls:
        m = re.search(r"HMTB bati=(\d+)", l)
        if m:
            bati = int(m.group(1))
    if i % 2 == 0:
        print("%3ds | %3d | %3d | %14d | %8d | %d" % (i * 3, int(al.sum()), int(eal.sum()), lat, adv, bati), flush=True)
print(">>> FIN [%s] : ATQ %d/10 vivants, DEF %d/10 | etalement lateral MAX = %dm" % (label, int(env.alive(0).sum()), int(env.en_alive().sum()), lat_max), flush=True)
print("DEMO FINI", flush=True)
