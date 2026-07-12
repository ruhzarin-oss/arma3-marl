"""arma_expo — JALON 1 du passage Arma de l'officier-axe : calculer l'EXPOSITION PAR AXE sur le RELIEF REEL
d'Altis (terrainIntersectASL = pendant exact du ray-march heightmap du sim). Sans combat, sans spawn :
juste des requetes de LOS terrain depuis des coordonnees -> deterministe, leger, exempt de la discipline-combat.
But : le spread d'exposition par axe (le defile) existe-t-il sur le vrai terrain ? Si oui, l'officier-axe vit en Arma."""
import re
import sys
from op_arma import OpArma

# objectifs candidats a tester (x,y) sur Altis ; on cherche un relief qui donne du spread
OBJECTIFS = [(15000, 16000), (16500, 13800), (20300, 18900), (14200, 18600)]
R_SPAWN = 170.0
NPATH = 12


def expo_sqf(ox, oy):
    return (
        'HMT_OX = %d; HMT_OY = %d; HMT_DEF = [];\n'
        '{ HMT_DEF pushBack [HMT_OX + 12*cos _x, HMT_OY + 12*sin _x] } forEach [0,90,180,270];\n'
        'for "_k" from 0 to 7 do {\n'
        '  private _th = _k * 45;\n'
        '  private _sx = HMT_OX + %f*cos _th; private _sy = HMT_OY + %f*sin _th;\n'
        '  private _seen = 0;\n'
        '  for "_i" from 1 to %d do {\n'
        '    private _t = _i / %d;\n'
        '    private _px = _sx + (HMT_OX - _sx)*_t; private _py = _sy + (HMT_OY - _sy)*_t;\n'
        '    private _pz = (getTerrainHeightASL [_px,_py]) + 1.5;\n'
        '    private _vis = false;\n'
        '    { private _dz = (getTerrainHeightASL [_x#0,_x#1]) + 1.5;\n'
        '      if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis = true };\n'
        '    } forEach HMT_DEF;\n'
        '    if (_vis) then { _seen = _seen + 1 };\n'
        '  };\n'
        '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)];\n'
        '};\n'
        'private _hs = []; { _hs pushBack round getTerrainHeightASL [HMT_OX + 170*cos (_x*45), HMT_OY + 170*sin (_x*45)] } forEach [0,1,2,3,4,5,6,7];\n'
        'diag_log format ["HARMATTAN_OBJH %%1 RING %%2", round getTerrainHeightASL [HMT_OX,HMT_OY], _hs];\n'
        % (ox, oy, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH)
    )


if __name__ == "__main__":
    env = OpArma()
    # ping : round-trip propre avant de charger
    try:
        pl = env._query('diag_log "HARMATTAN_PING";', settle=1.0)
        if not any("HARMATTAN_PING" in l for l in pl):
            print("PONT KO : ping non revenu"); sys.exit(1)
    except Exception as e:
        print("PONT KO : %s" % e); sys.exit(1)
    print("pont OK (server0)\n")
    for (ox, oy) in OBJECTIFS:
        try:
            lines = env._query(expo_sqf(ox, oy), settle=1.5)
        except Exception as e:
            print("objectif (%d,%d) : timeout/charge -> %s" % (ox, oy, e)); continue
        ex = {}
        for ln in lines:
            m = re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)
            if m:
                ex[int(m.group(1))] = int(m.group(2))
        objh = next((re.search(r"HARMATTAN_OBJH (\d+) RING (.+)", l) for l in lines if "HARMATTAN_OBJH" in l), None)
        if len(ex) == 8:
            vals = [ex[k] for k in range(8)]
            spread = max(vals) - min(vals)
            print("OBJ (%5d,%5d) | h=%sm | expo par axe (N..NO) : %s | spread=%d pts | defile=axe%d(%d%%) pire=axe%d(%d%%)"
                  % (ox, oy, objh.group(1) if objh else "?", vals, spread,
                     vals.index(min(vals)), min(vals), vals.index(max(vals)), max(vals)))
        else:
            print("OBJ (%d,%d) : reponse incomplete (%d/8 axes) -> pont sous charge" % (ox, oy, len(ex)))
