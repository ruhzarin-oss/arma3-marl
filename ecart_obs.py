#!/usr/bin/env python3
"""ecart_obs — L ECART ENTRE CE QUE LA POLITIQUE A APPRIS ET CE QU ARMA LUI DONNE.

Sur Arma la politique rend l action 4 en permanence, pour les huit hommes, et l escouade
s eloigne. Hors-ligne elle rendait quatre actions distinctes sur huit azimuts. Un reseau qui
devient constant recoit des entrees qu il n a jamais vues.

On mesure donc, colonne par colonne, ce que le GYMNASE donnait et ce qu ARMA donne.

CRITERE DEPOSE AVANT LA MESURE :
  une colonne est DECLAREE HORS DISTRIBUTION si sa moyenne cote Arma tombe hors de
  l intervalle [1er ; 99e centile] du gymnase. C est un critere de position, pas de forme :
  on ne demande pas aux deux mondes d avoir la meme dispersion, seulement que ce qu Arma
  presente ait deja ete vu.
  Et on RAPPORTE le recouvrement des plages, parce qu une moyenne dans la bande ne prouve
  pas qu on ne sorte jamais.
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from arma_socket_bridge import SocketBridge
import arma_couture as C

NOMS = ["apx/S", "apy/S", "dgx", "dgy", "alive", "slope", "dcover", "los", "nd",
        "dmgin", "ntf", "adx", "ady", "asup", "tff", "p0", "p1", "p2"]
COLS = list(range(9)) + [15, 16, 17]          # celles que la politique lit
OBJ = (1734.0, 5391.0)

SCENE = '''
HMT_OBJ = [1734, 5391, 0];
{ deleteVehicle _x } forEach (if (isNil "HMT_FR") then {[]} else {HMT_FR});
{ deleteVehicle _x } forEach (if (isNil "HMT_ENNEMI") then {[]} else {HMT_ENNEMI});
private _gd = createGroup east; HMT_ENNEMI = [];
for "_i" from 1 to 13 do {
    private _a = random 360; private _r = 10 + random 25;
    private _p = [(HMT_OBJ select 0) + _r * sin _a, (HMT_OBJ select 1) + _r * cos _a, 0];
    private _u = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u setSkill 0.5; _u disableAI "PATH";
    _u setBehaviour "COMBAT"; _u setCombatMode "RED";
    HMT_ENNEMI pushBack _u;
};
private _ga = createGroup west; HMT_FR = [];
private _az = random 360;
for "_i" from 1 to 8 do {
    private _p = [(HMT_OBJ select 0) + 200 * sin _az + (_i * 6),
                  (HMT_OBJ select 1) + 200 * cos _az, 0];
    private _u = _ga createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u allowDamage false;
    _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE"; _u setVariable ["HMT_LASTDMG", 0];
    HMT_FR pushBack _u;
};
HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;
diag_log format ["ECART_SCENE %1 %2", count HMT_ENNEMI, count HMT_FR];
'''

def sans_com(s):
    return "\n".join(re.sub(r"//.*$", "", l) for l in s.split("\n"))

# ---------- ARMA ----------
C.CX, C.CY, C.SCALE, C.FIRE_RANGE = OBJ[0], OBJ[1], 200.0, 110.0
b = SocketBridge(5830)
b.send(sans_com(SCENE)); time.sleep(3)
perc = sans_com(C.perc_sqf())
A = []
for k in range(30):
    b.send(perc, wait=False)
    time.sleep(1.2)
    o = C.parse_obs(b._log_lines(1200))
    if o: A = [v for v in o.values()]
b.sock.close()
if not A:
    print("  la couture n a rien rendu — on ne compare rien."); sys.exit(1)
A = torch.tensor(A, dtype=torch.float32)

# ---------- GYMNASE ----------
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
import math
e = AssaultTerrain(num_envs=256, seed=5, device="cpu", max_steps=60, **MONDE_ARMA)
o = e.reset(); G = [o.reshape(-1, o.shape[-1])]
for t in range(25):
    a = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4.0)).long() % 8)
    o, _, _, _ = e.step(a, auto_reset=False)
    G.append(o.reshape(-1, o.shape[-1]))
G = torch.cat(G)                        # (n, 12) dans l ordre base9 + posture3

print(f"\n  ARMA : {A.shape[0]} observations · GYMNASE : {G.shape[0]}")
print("\n  " + f"{'colonne':<9}{'gymnase p1..p99':>22}{'gymnase moy':>13}{'ARMA moy':>11}{'ARMA min..max':>20}   etat")
print("  " + "-" * 92)
hors = []
for j, cj in enumerate(COLS):
    g = G[:, j]
    p1, p99 = torch.quantile(g, 0.01).item(), torch.quantile(g, 0.99).item()
    gm = g.mean().item()
    a = A[:, cj]
    am, amin, amax = a.mean().item(), a.min().item(), a.max().item()
    # ⚠️ UN CRITERE DE POSITION NE VOIT PAS UNE CONSTANTE. `los` avait ete declare « ok »
    # parce que sa moyenne (0,00) tombe dans la plage du gymnase [0 ; 1] — alors qu il est
    # CONSTANT A ZERO sur Arma et vaut 0,69 de moyenne au gymnase. Une entree constante ne
    # porte aucune information : elle sature le reseau, quelle que soit sa valeur.
    constante = (amax - amin) < 1e-6 and (g.max() - g.min()).item() > 1e-6
    dedans = (p1 <= am <= p99) and not constante
    if not dedans: hors.append(NOMS[cj] + ("  (CONSTANTE)" if constante else ""))
    print(f"  {NOMS[cj]:<9}{f'{p1:.2f} .. {p99:.2f}':>22}{gm:>13.2f}{am:>11.2f}"
          f"{f'{amin:.2f} .. {amax:.2f}':>20}   {'ok' if dedans else ('CONSTANTE' if constante else 'HORS')}")
print("  " + "-" * 92)
print(f"  {len(hors)} colonnes sur {len(COLS)} hors distribution : {hors if hors else 'aucune'}")
