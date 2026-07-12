"""eyes_diag — pourquoi l'avatar ne voit pas l'ennemi ? On spawne avatar PRES de la garnison, on attend,
et on lit les faits bruts : la garnison existe-t-elle, est-elle hostile, l'avatar en a-t-il conscience ?"""
import time, sys, re
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = M.COMPLEXE
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge3.Altis",
             log=SB + "/logs/server3.out", acc=1.0, seed=12)
env.spawn({"AV": (OBJ[0] + 25, OBJ[1])}, [(OBJ[0], OBJ[1], 2, 10)])
env.b.send('(AV select 0) setBehaviour "AWARE"; (AV select 0) setCombatMode "YELLOW";', wait=True)
for w in range(6):
    time.sleep(2)
    ls = env._query('private _u = AV select 0;'
                    ' private _ne = _u findNearestEnemy _u;'
                    ' private _k = if (isNull _ne) then {-1} else {_u knowsAbout _ne};'
                    ' diag_log format ["DIAG enHMT=%1 vivHMT=%2 sideAV=%3 sideEN=%4 nearEnemyNull=%5 knows=%6 dist=%7",'
                    '   count HMT_EN, ({alive _x} count HMT_EN), side _u,'
                    '   (if (count HMT_EN > 0) then {side (HMT_EN select 0)} else {"?"}),'
                    '   isNull _ne, _k, (if (count HMT_EN>0) then {round (_u distance (HMT_EN select 0))} else {-1})];', settle=0.3)
    for l in ls:
        m = re.search(r"DIAG .*", l)
        if m:
            print("w=%d  %s" % (w, m.group(0).split("DIAG ")[1].strip().rstrip('"')), flush=True)
print("DIAG FINI", flush=True)
