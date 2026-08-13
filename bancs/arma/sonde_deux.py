#!/usr/bin/env python3
"""sonde_deux — POURQUOI `slope` REND ZERO ET `los` REND UN.

Les deux colonnes sont mortes sur 170 m de traversee. On ne les repare pas avant de savoir
POURQUOI. Deux hypotheses, une mesure chacune, ecrites avant :

  · SLOPE : soit les quatre hauteurs du gradient sont vraiment egales sous ces hommes (terrain
    plat, capteur sain), soit mon calcul rend zero alors que le terrain monte (capteur casse).
    On releve les QUATRE hauteurs brutes, et on les affiche.
  · LOS : `terrainIntersectASL` ne voit QUE LE RELIEF — ni batiment, ni muret, ni vegetation.
    A 170 m sur du plat elle dira toujours « visible ». On la compare a `checkVisibility`,
    qui est la vue que l IA emploie reellement pour decider de tirer ⟨lecon du geometre v3⟩.
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
import banc_live as BL

def sans_com(s):
    return "\n".join(re.sub(r"//.*$", "", l) for l in s.split("\n"))

SONDE = '''
{
  private _u = _x; private _i = _forEachIndex; private _p = getPosATL _u;
  private _x0 = _p select 0; private _y0 = _p select 1;
  private _hE = getTerrainHeightASL [_x0+6.25, _y0]; private _hO = getTerrainHeightASL [_x0-6.25, _y0];
  private _hN = getTerrainHeightASL [_x0, _y0+6.25]; private _hS = getTerrainHeightASL [_x0, _y0-6.25];
  private _gx = (_hE - _hO)/2; private _gy = (_hN - _hS)/2;
  private _pente = (sqrt (_gx*_gx + _gy*_gy))/5;
  private _ne = objNull; private _nd = 1e9;
  { if (alive _x) then { private _d = _u distance _x; if (_d < _nd) then {_nd=_d; _ne=_x} } } forEach HMT_ENNEMI;
  private _ti = -1; private _cv = -1;
  if (!isNull _ne) then {
    private _sp = getPosASL _u; private _ep = getPosASL _ne;
    _ti = if (terrainIntersectASL [[(_sp select 0),(_sp select 1),(_sp select 2)+1.7],
                                   [(_ep select 0),(_ep select 1),(_ep select 2)+1.7]]) then {0} else {1};
    _cv = [objNull,"VIEW"] checkVisibility [eyePos _u, eyePos _ne];
  };
  diag_log format ["SONDE2 %1 h %2 %3 %4 %5 pente %6 dist %7 terrain %8 vue %9",
    _i, round(_hE*100), round(_hO*100), round(_hN*100), round(_hS*100),
    round(_pente*1000), round _nd, _ti, round(_cv*100)];
} forEach HMT_FR;
'''

b = SocketBridge(5830)
b.send(sans_com(BL.SCENE)); time.sleep(3)
b.send(sans_com(BL.SCENE.replace("HMT_OBJ", "HMT_OBJ")) if False else 'diag_log "ok";', wait=False)
lignes = []
for tour in range(3):
    b.send(sans_com(SONDE), wait=False)
    t0 = time.time()
    while time.time() - t0 < 12:
        time.sleep(0.4)
        L = [x for x in b._log_lines(600) if "SONDE2" in x]
        if len(L) >= 8: lignes = L[-8:]; break
    if lignes: break
b.sock.close()
if not lignes:
    print("  la sonde n a rien rendu"); sys.exit(1)

print(f"\n  {'homme':>6}{'h est':>9}{'h ouest':>9}{'h nord':>9}{'h sud':>9}{'pente':>9}"
      f"{'dist':>7}{'terrain':>9}{'checkVis':>10}")
print("  " + "-" * 78)
for L in lignes:
    m = re.search(r"SONDE2 (\d+) h (-?\d+) (-?\d+) (-?\d+) (-?\d+) pente (-?\d+) dist (\d+) terrain (-?\d+) vue (-?\d+)", L)
    if not m: continue
    g = [int(x) for x in m.groups()]
    print(f"  {g[0]:>6}{g[1]/100:>9.2f}{g[2]/100:>9.2f}{g[3]/100:>9.2f}{g[4]/100:>9.2f}"
          f"{g[5]/1000:>9.3f}{g[6]:>7}{g[7]:>9}{g[8]/100:>10.2f}")
print("  " + "-" * 78)
print("  terrain : 1 = le RELIEF ne coupe pas · checkVis : ce que l IA voit vraiment (0..1)")
