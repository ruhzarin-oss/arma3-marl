"""arma_scan — cherche sur Altis des objectifs a DEFILE FORT : un axe d'approche a basse exposition
(le terrain masque l'approche) avec un bon spread. Ce sont les objectifs ou le CHOIX de l'officier compte.
Une seule requete SQF balaie une grille ; on rapporte les meilleurs defiles (exposition min basse, spread haut)."""
import re
from op_arma import OpArma

XS = list(range(6000, 25000, 3000)); YS = list(range(6000, 25000, 3000))  # grille terre Altis
R_SPAWN = 170.0; NPATH = 10


def scan_sqf(pts):
    arr = "[" + ",".join("[%d,%d]" % (x, y) for x, y in pts) + "]"
    return (
        'HMT_PTS = %s;\n'
        '{ private _o = _x; private _ox = _o#0; private _oy = _o#1;\n'
        '  private _oh = getTerrainHeightASL [_ox,_oy];\n'
        '  if (_oh > 8) then {\n'                                   # au-dessus du niveau de la mer
        '    private _def = []; { _def pushBack [_ox + 12*cos _x, _oy + 12*sin _x] } forEach [0,90,180,270];\n'
        '    private _ax = [];\n'
        '    for "_k" from 0 to 7 do {\n'
        '      private _th = _k*45; private _sx = _ox + %f*cos _th; private _sy = _oy + %f*sin _th;\n'
        '      private _seen = 0;\n'
        '      for "_i" from 1 to %d do {\n'
        '        private _t = _i/%d; private _px = _sx+(_ox-_sx)*_t; private _py = _sy+(_oy-_sy)*_t;\n'
        '        private _pz = (getTerrainHeightASL [_px,_py])+1.5; private _vis = false;\n'
        '        { private _dz = (getTerrainHeightASL [_x#0,_x#1])+1.5;\n'
        '          if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis = true };\n'
        '        } forEach _def;\n'
        '        if (_vis) then { _seen = _seen+1 };\n'
        '      };\n'
        '      _ax pushBack round (100*_seen/%d);\n'
        '    };\n'
        '    private _mn = selectMin _ax; private _mx = selectMax _ax;\n'
        '    diag_log format ["HARMATTAN_SCAN %%1 %%2 %%3 %%4 %%5 %%6", _ox, _oy, round _oh, _mn, _mx, _ax find _mn];\n'
        '  };\n'
        '} forEach HMT_PTS;\n'
        'diag_log "HARMATTAN_SCANDONE";\n'
        % (arr, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH)
    )


if __name__ == "__main__":
    env = OpArma()
    pts = [(x, y) for x in XS for y in YS]
    # on decoupe en lots de 12 points pour ne pas faire exploser une seule requete sous charge
    res = []
    for i in range(0, len(pts), 12):
        lot = pts[i:i + 12]
        try:
            lines = env._query(scan_sqf(lot), settle=2.0)
        except Exception as e:
            print("lot %d : timeout -> %s" % (i // 12, e)); continue
        for ln in lines:
            m = re.search(r"HARMATTAN_SCAN (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)", ln)
            if m:
                ox, oy, h, mn, mx, ba = [int(g) for g in m.groups()]
                res.append((mn, mx - mn, ox, oy, h, ba))
    res.sort(key=lambda r: (r[0], -r[1]))   # defile le plus FORT d'abord (exposition min basse), puis spread
    print("\n=== objectifs a DEFILE FORT sur Altis (exposition min basse = l'officier a un vrai choix) ===")
    print("  %d objectifs terrestres scannes" % len(res))
    for mn, sp, ox, oy, h, ba in res[:8]:
        print("  OBJ (%5d,%5d) h=%3dm | defile = axe%d a %3d%% expo | pire = %d%% | spread %d pts"
              % (ox, oy, h, ba, mn, mn + sp, sp))
