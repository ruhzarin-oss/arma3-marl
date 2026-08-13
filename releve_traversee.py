#!/usr/bin/env python3
"""releve_traversee — L OBSERVATION LE LONG D UNE TRAVERSEE, HOMME PAR HOMME, PAS PAR PAS.

⚠️ POURQUOI CE RELEVE EXISTE. Hors ligne, sur des observations synthetiques, la politique rend
SIX actions distinctes sur huit azimuts. Branchee sur Arma, elle rend UNE SEULE action, toujours
la meme, pour les huit hommes et a chaque pas. Entre les deux il n y a que la couture.

Et ma sonde precedente ne pouvait pas trancher : elle relevait huit hommes AU MEME ENDROIT et AU
MEME INSTANT, donc tout y paraissait constant sans qu on puisse distinguer une colonne morte
d une situation uniforme. Ici on suit la TRAVERSEE : si une colonne ne bouge pas alors que les
hommes avancent de 170 m, elle est morte.

On compare a la MEME traversee dans le gymnase, meme politique, meme doctrine.
"""
import sys, time, re, math, statistics as stx
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from arma_socket_bridge import SocketBridge
import arma_couture as C
from porter_boucle import charger, COLS
import banc_live as BL

NOMS18 = ["apx/S", "apy/S", "dgx", "dgy", "alive", "slope", "dcover", "los", "nd",
          "dmgin", "ntf", "adx", "ady", "asup", "tff", "p0", "p1", "p2"]
PAS, OBJ = 30, (1734.0, 5391.0)


def sans_com(s):
    return "\n".join(re.sub(r"//.*$", "", l) for l in s.split("\n"))


# ═══ ARMA ═══
C.CX, C.CY, C.SCALE, C.FIRE_RANGE, C.MOVE_SPD = OBJ[0], OBJ[1], 200.0, 110.0, 6.0
b = SocketBridge(5830)
b.send(sans_com(BL.SCENE)); time.sleep(3)
b.send(sans_com(C.WAKE)); time.sleep(2)
pol = charger()
perc = sans_com(C.perc_sqf())
traces, actes = [], []
for t in range(PAS):
    b.send(perc, wait=False)
    o = {}
    for _ in range(10):
        time.sleep(0.3)
        o = C.parse_obs(b._log_lines(900))
        if o: break
    if not o:
        break
    ten = torch.tensor([o[i] for i in sorted(o)], dtype=torch.float32)
    traces.append(ten)
    with torch.no_grad():
        lo, _ = pol(ten[:, COLS])
    a = lo.argmax(-1).tolist(); actes.append(a)
    b.send(sans_com(C.acts_to_sqf(a)), wait=False)
    time.sleep(1.2)
b.sock.close()
if not traces:
    print("  la couture n a rien rendu"); sys.exit(1)
A = torch.cat(traces)          # (pas*hommes, 18)
print(f"\n  ARMA : {len(traces)} pas x {traces[0].shape[0]} hommes = {A.shape[0]} observations")

# ═══ GYMNASE ═══
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
e = AssaultTerrain(num_envs=64, seed=11, device="cpu", max_steps=60, **MONDE_ARMA)
o = e.reset(); G = [o.reshape(-1, o.shape[-1])]
for t in range(PAS):
    with torch.no_grad():
        lo, _ = pol(o.reshape(-1, o.shape[-1]))
    a = lo.argmax(-1).reshape(e.N, e.A)
    o, _, _, _ = e.step(a, auto_reset=False)
    G.append(o.reshape(-1, o.shape[-1]))
Gt = torch.cat(G)
print(f"  GYMNASE : {Gt.shape[0]} observations, meme politique\n")

print(f"  {'colonne':<9}{'ARMA min..max':>22}{'ARMA sigma':>12}{'GYM min..max':>22}{'GYM sigma':>11}   etat")
print("  " + "-" * 90)
morts = []
for j, cj in enumerate(COLS):
    a, g = A[:, cj], Gt[:, j]
    sa, sg = float(a.std()), float(g.std())
    mort = sa < 1e-4 and sg > 1e-3
    if mort: morts.append(NOMS18[cj])
    print(f"  {NOMS18[cj]:<9}{f'{a.min():.3f} .. {a.max():.3f}':>22}{sa:>12.4f}"
          f"{f'{g.min():.3f} .. {g.max():.3f}':>22}{sg:>11.4f}   {'MORTE' if mort else 'vivante'}")
print("  " + "-" * 90)
print(f"  colonnes MORTES sur la traversee : {morts if morts else 'aucune'}")
print(f"\n  actions rendues par pas : {[max(set(x), key=x.count) for x in actes[:12]]}")
d = len({tuple(x) for x in actes})
print(f"  combinaisons d actions distinctes sur {len(actes)} pas : {d}")
