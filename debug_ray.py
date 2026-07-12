"""debug_ray — mesure le repere (eyePos vs ASL) pour corriger la coque."""
import time, sys
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=7)
env.spawn({"AV": (M.COMPLEXE[0], M.COMPLEXE[1] - 180)}, [])   # zone degagee
time.sleep(2)
DBG = (
    'private _u = AV select 0;'
    'private _ep = eyePos _u; private _asl = getPosASL _u; private _atl = getPosATL _u;'
    'diag_log format ["DBG eyePos=%1 | posASL=%2 | posATL=%3", _ep, _asl, _atl];'
    # rayon AVANT, origine = eyePos baissee, et variante origine = ASL+0.9
    'private _o1 = +_ep; _o1 set [2, (_ep#2) - 0.7];'
    'private _o2 = +_asl; _o2 set [2, (_asl#2) + 0.9];'
    'private _dir = _u vectorModelToWorld [0,1,0];'
    'private _t1 = _o1 vectorAdd (_dir vectorMultiply 15);'
    'private _t2 = _o2 vectorAdd (_dir vectorMultiply 15);'
    'private _h1 = lineIntersectsSurfaces [_o1,_t1,_u];'
    'private _h2 = lineIntersectsSurfaces [_o2,_t2,_u];'
    'diag_log format ["DBG o1(eye)=%1 nhits=%2 d=%3", _o1, count _h1, if(count _h1>0)then{round(_o1 distance ((_h1 select 0) select 0))}else{-1}];'
    'diag_log format ["DBG o2(asl)=%1 nhits=%2 d=%3", _o2, count _h2, if(count _h2>0)then{round(_o2 distance ((_h2 select 0) select 0))}else{-1}];'
)
ls = env._query(DBG, settle=0.25)
for l in ls:
    if "DBG" in l:
        print(l.strip().split("DBG", 1)[1].strip() if "DBG" in l else l.strip())
print("DEBUG FINI", flush=True)
