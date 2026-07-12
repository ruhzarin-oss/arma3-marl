"""diag_opf — pourquoi HMT_EN est vide ? On rejoue le spawn OPFOR sur server3 et on compte cote Arma."""
import time
from op_arma import OpArma
import run_duel as R
import paros as M
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=R.SQUADS_BLU, mission=SB + "/arma3server/mpmissions/HarmattanBridge3.Altis",
             log=SB + "/logs/server3.out", move=36, acc=1.0, seed=5)
env.spawn(M.SPAWNS, [])
secs = R.opf_secteurs(150)
print("secteurs:", len(secs), "total demande:", sum(s[2] for s in secs))
g = R.spawn_opfor(env, secs)
ls = env._query('diag_log format ["HARMATTAN_DBG hmt=%1 east=%2 grp=%3 p0=%4", count HMT_EN, ({alive _x} count allUnits), count (allGroups select {side _x == east}), (if (count HMT_EN > 0) then {getPosATL (HMT_EN select 0)} else {[-9,-9]})];', settle=1.5)
for l in ls:
    if "HARMATTAN_DBG" in l:
        print(l.strip()[-120:])
print("PY -> en_n:", env.en_n, "| epx[:3]:", env.epx[:3], "| epy[:3]:", env.epy[:3])
