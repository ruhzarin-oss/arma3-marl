#!/usr/bin/env python3
"""coevo_league.py — la LEAGUE casse le cycle. Jeu fictif (fictitious play) sur la matrice 7 manoeuvres :
chaque camp repond a la MOYENNE historique de l'adversaire -> converge vers un META MIXTE stable (Nash),
plus de cycle envelopper<->PINCE. Montre la distribution finale."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
MAN = {0: "assaut", 1: "defend", 2: "hunt", 3: "bounding", 4: "envelopper", 5: "PINCE", 6: "ECHELON"}; IDS = list(MAN)


def ext_action(e, side):
    base = repertoire_action(e, side); man = e.a_maneuver if side == 0 else e.b_maneuver; d = e.dev
    if side == 0:
        sx, sy, sal = e.ax, e.ay, e._a_alive(); ex, ey, eal = e.bx, e.by, e._b_alive(); spost = e.apost
    else:
        sx, sy, sal = e.bx, e.by, e._b_alive(); ex, ey, eal = e.ax, e.ay, e._a_alive(); spost = e.bpost
    N, n = sx.shape; ar = torch.arange(n, device=d)[None]
    ew = eal.float(); ews = ew.sum(1, keepdim=True).clamp(min=1); ecx = (ex * ew).sum(1, keepdim=True) / ews; ecy = (ey * ew).sum(1, keepdim=True) / ews
    sw = sal.float(); sws = sw.sum(1, keepdim=True).clamp(min=1); mcx = (sx * sw).sum(1, keepdim=True) / sws; mcy = (sy * sw).sum(1, keepdim=True) / sws
    dirx = ecx - mcx; diry = ecy - mcy; dn = torch.sqrt(dirx * dirx + diry * diry).clamp(min=1e-3); perpx = -diry / dn; perpy = dirx / dn
    dxe = ex.unsqueeze(1) - sx.unsqueeze(2); dye = ey.unsqueeze(1) - sy.unsqueeze(2)
    ed2 = torch.where(eal.unsqueeze(1), dxe * dxe + dye * dye, torch.tensor(1e18, device=d)); km = ed2.argmin(2)
    bx = torch.gather(ex, 1, km); by = torch.gather(ey, 1, km); nd = ed2.min(2).values.clamp(max=1e17).sqrt()
    los = e._losc(sx, sy, bx, by, eye_a=e._eye(spost), eye_b=1.7); engaged = (los > 0.5) & (nd < e.fire_range)
    grp = ar % 3
    px = ecx.expand(N, n) + perpx * 55.0 * (grp == 1).float() - perpx * 55.0 * (grp == 2).float()
    py = ecy.expand(N, n) + perpy * 55.0 * (grp == 1).float() - perpy * 55.0 * (grp == 2).float()
    a5 = (torch.round(torch.atan2(px - sx, py - sy) / (math.pi / 4.0)) % 8).long()
    lat = (ar.float() / max(n - 1, 1)) * 60.0; ex6 = ecx.expand(N, n) + perpx * lat; ey6 = ecy.expand(N, n) + perpy * lat
    a6 = (torch.round(torch.atan2(ex6 - sx, ey6 - sy) / (math.pi / 4.0)) % 8).long()
    a5 = torch.where(engaged, torch.full_like(a5, 9), a5); a6 = torch.where(engaged, torch.full_like(a6, 9), a6)
    out = torch.where((man == 5).unsqueeze(1), a5, base); out = torch.where((man == 6).unsqueeze(1), a6, out)
    return torch.where(sal, out, torch.full_like(out, 8))


@torch.no_grad()
def winrate(att, dfd):
    e = DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
    e.reset(); e.a_maneuver = torch.full((e.N,), att, dtype=torch.long, device=DEV); e.b_maneuver = torch.full((e.N,), dfd, dtype=torch.long, device=DEV)
    w = 0.0; nep = 0; done = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for _ in range(60):
        (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        m = dn.bool() & ~done
        if m.any(): w += info["att_wins"][m].float().sum().item(); nep += int(m.sum())
        done |= dn.bool()
    return w / max(nep, 1)


print("Matrice 7x7...", flush=True)
W = np.array([[winrate(a, b) for b in IDS] for a in IDS]); K = len(IDS)
ca = np.zeros(K); cd = np.zeros(K); ca[0] = cd[0] = 1                             # depart : assaut vs assaut
for t in range(1, 4000):
    avg_a = ca / ca.sum(); avg_d = cd / cd.sum()
    ca[int(np.argmax(W @ avg_d))] += 1                                            # att maximise vs moyenne def
    cd[int(np.argmin(avg_a @ W))] += 1                                            # def minimise vs moyenne att
avg_a = ca / ca.sum(); avg_d = cd / cd.sum(); val = float(avg_a @ W @ avg_d)
print("\n=== LEAGUE (jeu fictif) : META MIXTE STABLE — plus de cycle ===")
print("  ATTAQUANT joue :")
for i in np.argsort(-avg_a):
    if avg_a[i] > 0.03: print("    %-10s : %.0f%%" % (MAN[i], 100 * avg_a[i]))
print("  DEFENSEUR joue :")
for i in np.argsort(-avg_d):
    if avg_d[i] > 0.03: print("    %-10s : %.0f%%" % (MAN[i], 100 * avg_d[i]))
print("  valeur du jeu (winrate attaquant a l'equilibre) : %.2f" % val)
print("  -> le cycle envelopper<->PINCE est remplace par un MELANGE stable.")
