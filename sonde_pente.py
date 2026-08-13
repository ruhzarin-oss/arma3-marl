#!/usr/bin/env python3
"""sonde_pente — LA PENTE D ARMA EST-ELLE ENFIN COMPARABLE A CELLE DU GYMNASE ?

On ne demande plus si le champ EXISTE : on demande si sa DISTRIBUTION recouvre celle sur
laquelle l agent a appris. Meme formule des deux cotes — gradient central du relief, en metres
par cellule de 6,25 m, divise par 5.

⚠️ CE QUI FERAIT ECHOUER — ecrit avant :
  · la mediane d Arma reste sous le 1er centile du gymnase -> Stratis est BEAUCOUP plus plat
    que le relief genere, et c est le GYMNASE qu il faut corriger, pas la couture.
  · la pente d Arma ne varie pas d un point a l autre -> le capteur est mort, et rien d autre
    ne se lit.
"""
import sys, time, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SQF = '''
HMT_P = [];
for "_i" from 1 to 400 do {
  private _x = 1000 + random 6000; private _y = 1000 + random 6000;
  if (!(surfaceIsWater [_x,_y,0]) && {(getTerrainHeightASL [_x,_y]) > 2}) then {
    private _gx = ((getTerrainHeightASL [_x+6.25,_y]) - (getTerrainHeightASL [_x-6.25,_y]))/2;
    private _gy = ((getTerrainHeightASL [_x,_y+6.25]) - (getTerrainHeightASL [_x,_y-6.25]))/2;
    HMT_P pushBack (round (1000 * (sqrt (_gx*_gx + _gy*_gy))/5));
  };
};
diag_log format ["PENTE %1 %2", count HMT_P, HMT_P];
'''

b = SocketBridge(5830)
time.sleep(1)
b.send(SQF, wait=False)
vals = None
t0 = time.time()
while time.time() - t0 < 25:
    for L in reversed(b._log_lines(400)):
        m = re.search(r"PENTE (\d+) \[([^\]]*)\]", L)
        if m and int(m.group(1)) > 50:
            vals = [int(v) / 1000.0 for v in m.group(2).split(",")]
            break
    if vals: break
    time.sleep(0.5)
b.sock.close()
if not vals:
    print("  la sonde n a rien rendu"); sys.exit(1)

vals.sort()
q = lambda p: vals[int(p * (len(vals) - 1))]
print(f"\n  STRATIS — {len(vals)} points, meme formule que le gymnase")
print(f"    p01 {q(0.01):.3f}   median {q(0.5):.3f}   p99 {q(0.99):.3f}   max {vals[-1]:.3f}")
print(f"    en degres : median {math.degrees(math.atan(q(0.5)*5/6.25)):.1f}°"
      f"   p99 {math.degrees(math.atan(q(0.99)*5/6.25)):.1f}°")
print("\n  GYMNASE (mesure)")
print("    p01 ~0.010   median 0.589   p99 1.523")
print(f"\n  RECOUVREMENT : la mediane d Arma ({q(0.5):.3f}) est"
      f" {'DANS' if 0.010 <= q(0.5) <= 1.523 else 'HORS DE'} la plage du gymnase")
print(f"  VARIATION : {'le capteur varie' if (vals[-1] - vals[0]) > 0.05 else 'CAPTEUR MORT'}"
      f" (etendue {vals[-1]-vals[0]:.3f})")
