"""quelle carte (worldName) tourne reellement sur chaque serveur ?"""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
for name, mis, log in [("VISU(2302)", "HMT-EcoleDeGuerre.Altis", "visu.out"),
                       ("server0(2402)", "HarmattanBridge0.Altis", "server0.out")]:
    try:
        env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/" + mis, log=SB + "/logs/" + log, seed=0)
        ls = env._query('diag_log format ["HARMATTAN_WORLD %1", worldName];', settle=1.0)
        w = next((re.search(r"HARMATTAN_WORLD (\S+)", l) for l in ls if "HARMATTAN_WORLD" in l), None)
        print(name, "-> worldName =", (w.group(1) if w else "(non lu)"))
    except Exception as e:
        print(name, "-> erreur:", str(e)[:50])
