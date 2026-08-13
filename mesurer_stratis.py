#!/usr/bin/env python3
"""mesurer_stratis — CE QUE LA CARTE DONNE VRAIMENT, pour y ramener le gymnase.

On ne regle pas le monde d entrainement au jugement : on mesure Stratis, colonne par colonne,
avec EXACTEMENT les formules que le pont emploie, et on ramenera le gymnase dessus.

⚠️ CE QUI FERAIT ECHOUER — ecrit avant :
  · moins de 300 points valides -> mesure trop maigre, on ne regle rien.
  · une colonne sans variation sur la carte -> ce n est pas un reglage qu il faut, c est un
    capteur a comprendre.
"""
import sys, time, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SQF = '''
HMT_S = []; HMT_C = [];
for "_i" from 1 to 900 do {
  private _x = 900 + random 6400; private _y = 900 + random 6400;
  if (!(surfaceIsWater [_x,_y,0]) && {(getTerrainHeightASL [_x,_y]) > 2}) then {
    private _gx = ((getTerrainHeightASL [_x+6.25,_y]) - (getTerrainHeightASL [_x-6.25,_y]))/2;
    private _gy = ((getTerrainHeightASL [_x,_y+6.25]) - (getTerrainHeightASL [_x,_y-6.25]))/2;
    HMT_S pushBack (round (1000 * (sqrt (_gx*_gx + _gy*_gy))/5));
    private _nb = nearestObjects [[_x,_y,0], ["House","Building","Wall","Rock"], 40];
    private _dc = 1000;
    if (count _nb > 0) then { _dc = round (1000 * ((([_x,_y,0]) distance (_nb select 0))/30 min 1)) };
    HMT_C pushBack _dc;
  };
};
diag_log format ["STRATIS %1 S %2", count HMT_S, HMT_S];
diag_log format ["STRATIC %1 C %2", count HMT_C, HMT_C];
'''

b = SocketBridge(5830)
time.sleep(1)
b.send(SQF, wait=False)
S = C = None
t0 = time.time()
while time.time() - t0 < 60:
    for L in b._log_lines(600):
        m = re.search(r"STRATIS (\d+) S \[([^\]]*)\]", L)
        if m and int(m.group(1)) > 100: S = [int(v)/1000 for v in m.group(2).split(",")]
        m = re.search(r"STRATIC (\d+) C \[([^\]]*)\]", L)
        if m and int(m.group(1)) > 100: C = [int(v)/1000 for v in m.group(2).split(",")]
    if S and C: break
    time.sleep(1)
b.sock.close()
if not S or not C:
    print("  la sonde n a rien rendu"); sys.exit(1)

def stats(v, nom):
    v = sorted(v); q = lambda p: v[int(p*(len(v)-1))]
    print(f"    {nom:<10}{len(v):>6} pts   p01 {q(0.01):.3f}   median {q(0.5):.3f}   "
          f"p99 {q(0.99):.3f}   moy {sum(v)/len(v):.3f}")
    return q(0.5), q(0.99), sum(v)/len(v)

print(f"\n  STRATIS — memes formules que le pont")
ms, p99s, moys = stats(S, "slope")
mc, p99c, moyc = stats(C, "dcover")

import numpy as np
np.save("/home/younes/arma3-marl/pentes_stratis.npy", np.array(S, dtype=np.float32))
print(f"\n  {len(S)} pentes de Stratis conservees -> pentes_stratis.npy")

print("\n  GYMNASE (a ramener dessus)")
import torch
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
e = AssaultTerrain(num_envs=256, seed=5, device="cuda:0", max_steps=10, **MONDE_ARMA)
o = e.reset().reshape(-1, 12)
for j, nom in ((5, "slope"), (6, "dcover")):
    v = sorted(o[:, j].tolist()); q = lambda p: v[int(p*(len(v)-1))]
    print(f"    {nom:<10}{len(v):>6} pts   p01 {q(0.01):.3f}   median {q(0.5):.3f}   "
          f"p99 {q(0.99):.3f}   moy {sum(v)/len(v):.3f}")
print(f"\n  ECART A COMBLER : slope x{ms/max(o[:,5].median().item(),1e-6):.2f}   "
      f"dcover x{mc/max(o[:,6].median().item(),1e-6):.2f}")
