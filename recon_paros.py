"""recon_paros — reconnaissance fine de Paros (20885,16959) pour batir le theatre : anneaux de points,
chacun avec altitude / eau / bati / ligne-de-vue vers l'objectif. -> on place objectif, base-de-feu, flancs,
lignes de depart sur de la VRAIE terre avec de vrais surplombs."""
import re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
CX, CY = 20885, 16959
env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
CAPS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
sqf = (
    'HMT_CX=%d; HMT_CY=%d; private _cz=(getTerrainHeightASL [HMT_CX,HMT_CY])+1.5;\n' % (CX, CY) +
    '{ private _r=_x;\n'
    '  { private _b=_x; private _th=_b*45;\n'
    '    private _px=HMT_CX + _r*sin _th; private _py=HMT_CY + _r*cos _th;\n'
    '    private _ph=getTerrainHeightASL [_px,_py];\n'
    '    private _los=!(terrainIntersectASL [[_px,_py,_ph+1.5],[HMT_CX,HMT_CY,_cz]]);\n'
    '    private _bat=count (nearestObjects [[_px,_py,0],["House"],25]);\n'
    '    diag_log format ["HARMATTAN_P r=%1 cap=%2 x=%3 y=%4 h=%5 eau=%6 bat=%7 los=%8", _r,_b,round _px,round _py,round _ph,surfaceIsWater [_px,_py,0],_bat,_los];\n'
    '  } forEach [0,1,2,3,4,5,6,7];\n'
    '} forEach [0,150,210,250];\n'
)
ls = env._query(sqf, settle=2.5)
rows = {}
for l in ls:
    m = re.search(r"HARMATTAN_P r=(\d+) cap=(\d+) x=(\d+) y=(\d+) h=(-?\d+) eau=(\w+) bat=(\d+) los=(\w+)", l)
    if m:
        r = int(m.group(1)); rows.setdefault(r, {})[int(m.group(2))] = (int(m.group(3)), int(m.group(4)), int(m.group(5)), m.group(6), int(m.group(7)), m.group(8))
hc = next((v[0][2] for v in [rows.get(0, {})] if 0 in v), "?")
print("=== Paros (%d,%d) — centre alt %sm ===" % (CX, CY, hc))
for r in [150, 210, 250]:
    if r not in rows: continue
    print("\n--- anneau %dm ---" % r)
    for b in range(8):
        if b in rows[r]:
            x, y, h, eau, bat, los = rows[r][b]
            tag = "TERRE" if eau == "false" else "EAU"
            print("  %-3s (%5d,%5d) alt %3dm | %-5s | bati %2d | LOS objectif: %s" % (CAPS[b], x, y, h, tag, bat, "OUI" if los == "true" else "non"))
