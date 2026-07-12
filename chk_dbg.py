"""lit les sondes HMT_DBG posees dans initPlayerLocal."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
sqf = ('diag_log format ["HARMATTAN_DBG1 %1", if (isNil "HMT_DBG1") then {"(non pose)"} else {HMT_DBG1}]; '
       'diag_log format ["HARMATTAN_DBG2 %1", if (isNil "HMT_DBG2") then {"(non pose)"} else {HMT_DBG2}]; '
       'diag_log format ["HARMATTAN_DBG3 %1", if (isNil "HMT_DBG3") then {"(non pose)"} else {HMT_DBG3}]; '
       'diag_log format ["HARMATTAN_PLY2 players=%1", count allPlayers];')
ls = env._query(sqf, settle=1.5)
for tag in ["HARMATTAN_DBG1", "HARMATTAN_DBG2", "HARMATTAN_DBG3", "HARMATTAN_PLY2"]:
    line = next((l for l in ls if tag in l), "")
    m = re.search(tag + r" (.+)", line)
    print(tag.replace("HARMATTAN_", ""), ":", m.group(1).strip()[:80] if m else "(rien)")
