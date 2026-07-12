"""check_lambs — LAMBS est-il vraiment chargé et actif sur server0 ? On interroge la config via le pont."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("X", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", seed=0)
sqf = ('diag_log format ["LAMBSCHK danger=%1 main=%2 cba=%3 fn=%4 ver=%5", '
       'isClass (configFile >> "CfgPatches" >> "lambs_danger"), '
       'isClass (configFile >> "CfgPatches" >> "lambs_main"), '
       'isClass (configFile >> "CfgPatches" >> "cba_main"), '
       '!isNil "lambs_danger_fnc_doGroupDanger", '
       'getNumber (configFile >> "CfgPatches" >> "lambs_main" >> "version")];')
try:
    ls = env._query(sqf, settle=2.5)
    hit = [l.strip()[-120:] for l in ls if "LAMBSCHK" in l]
    print("PONT OK ->", hit[-1] if hit else "(pas de ligne LAMBSCHK capturée)")
except Exception as e:
    print("PONT KO (mission/serveur pas prêt ?) :", str(e)[:100])
