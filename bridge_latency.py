"""bridge_latency — MESURE LE BUDGET TEMPS REEL DU PONT. Un soldat, boucle serree perception->action,
on chronometre le round-trip. Decide si la 'prise Matrice' peut etre vraiment temps reel."""
import time, sys, statistics
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = M.COMPLEXE
env = OpArma(squads=(("X", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge3.Altis",
             log=SB + "/logs/server3.out", acc=1.0, seed=3)
env.spawn({"X": (OBJ[0] + 150, OBJ[1])}, [])
time.sleep(2)
print("=== mesure latence pont (1 soldat, server3) ===", flush=True)

# 1) latence PERCEPTION seule (query -> reponse lue)
percept = []
for i in range(15):
    t0 = time.time()
    env._query('private _u = X select 0; private _p = getPosATL _u; diag_log format ["RT %1 %2 %3 %4", round(_p#0), round(_p#1), round((getSuppression _u)*100), round((getDammage _u)*100)];', settle=0.05)
    percept.append(time.time() - t0)

# 2) latence boucle COMPLETE : perception + decision triviale + ORDRE renvoye
loop = []
for i in range(15):
    t0 = time.time()
    env._query('private _u = X select 0; private _p = getPosATL _u; diag_log format ["RT %1 %2", round(_p#0), round(_p#1)];', settle=0.05)
    env.b.send('private _u = X select 0; _u doMove [%d, %d, 0];' % (OBJ[0], OBJ[1]), wait=True)
    loop.append(time.time() - t0)


def stats(name, xs):
    print("  %-22s moy %5.0f ms | min %5.0f | max %5.0f  -> ~%.1f Hz" % (
        name, 1000 * statistics.mean(xs), 1000 * min(xs), 1000 * max(xs), 1.0 / statistics.mean(xs)), flush=True)


stats("perception seule", percept)
stats("boucle perc+ordre", loop)
print("LATENCE FINI", flush=True)
