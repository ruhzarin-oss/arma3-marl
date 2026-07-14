#!/usr/bin/env python3
"""coevo_ext.py — AGRANDIR l'espace des strategies (a part). Ajoute 2 manoeuvres au repertoire :
PINCE (man=5, double debordement G+D) et ECHELON (man=6, biais lateral progressif). Puis arms race
sur 7 manoeuvres + traque de nouveaute. Reutilise repertoire_action pour 0-4, sans toucher leur code."""
import sys, math, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NACT = 10
MAN = {0: "assaut", 1: "defend", 2: "hunt", 3: "bounding", 4: "envelopper", 5: "PINCE", 6: "ECHELON"}; IDS = list(MAN)


def ext_action(e, side):
    base = repertoire_action(e, side)
    man = e.a_maneuver if side == 0 else e.b_maneuver
    d = e.dev
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
    grp = ar % 3                                                                  # PINCE : fix / flanc G / flanc D
    px = ecx.expand(N, n) + perpx * 55.0 * (grp == 1).float() - perpx * 55.0 * (grp == 2).float()
    py = ecy.expand(N, n) + perpy * 55.0 * (grp == 1).float() - perpy * 55.0 * (grp == 2).float()
    a5 = (torch.round(torch.atan2(px - sx, py - sy) / (math.pi / 4.0)) % 8).long()
    lat = (ar.float() / max(n - 1, 1)) * 60.0                                     # ECHELON : biais lateral 0->60m
    ex6 = ecx.expand(N, n) + perpx * lat; ey6 = ecy.expand(N, n) + perpy * lat
    a6 = (torch.round(torch.atan2(ex6 - sx, ey6 - sy) / (math.pi / 4.0)) % 8).long()
    a5 = torch.where(engaged, torch.full_like(a5, 9), a5); a6 = torch.where(engaged, torch.full_like(a6, 9), a6)
    out = torch.where((man == 5).unsqueeze(1), a5, base); out = torch.where((man == 6).unsqueeze(1), a6, out)
    return torch.where(sal, out, torch.full_like(out, 8))


def mkenv(sd):
    return DuelTerrain(num_envs=256, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def winrate(att, dfd):
    e = mkenv(0); e.reset(); e.a_maneuver = torch.full((e.N,), att, dtype=torch.long, device=DEV); e.b_maneuver = torch.full((e.N,), dfd, dtype=torch.long, device=DEV)
    w = 0.0; nep = 0; done = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    for _ in range(60):
        (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        m = dn.bool() & ~done
        if m.any(): w += info["att_wins"][m].float().sum().item(); nep += int(m.sum())
        done |= dn.bool()
    return w / max(nep, 1)


@torch.no_grad()
def profile(man):
    e = mkenv(1); e.reset(); e.a_maneuver = torch.full((e.N,), man, dtype=torch.long, device=DEV)
    ah = torch.zeros(NACT, device=DEV); ang = 0.0; steps = 0
    for _ in range(60):
        aA = ext_action(e, 0); aB = ext_action(e, 1)
        ah += torch.bincount(aA.reshape(-1).clamp(0, NACT - 1), minlength=NACT).float()
        al = e._a_alive().float(); bw = e._b_alive().float(); bws = bw.sum(1).clamp(min=1)
        ecx = (e.bx * bw).sum(1) / bws; ecy = (e.by * bw).sum(1) / bws
        dx = e.ax - ecx.unsqueeze(1); dy = e.ay - ecy.unsqueeze(1); nrm = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-3)
        mx = ((dx / nrm) * al).sum(1) / al.sum(1).clamp(min=1); my = ((dy / nrm) * al).sum(1) / al.sum(1).clamp(min=1)
        ang += (1 - torch.sqrt(mx * mx + my * my)).mean().item(); e.step(aA, aB, auto_reset=False); steps += 1
    return np.concatenate([(ah / ah.sum()).cpu().numpy(), [ang / steps]])


print("Matrice 7x7 + profils...", flush=True)
W = np.array([[winrate(a, b) for b in IDS] for a in IDS])
F = {m: profile(m) for m in IDS}; sd = np.maximum(np.abs(np.stack([F[m] for m in IDS])).mean(0), 1e-6)
def nov(a, b): return float(np.sqrt((((F[a] - F[b]) / sd) ** 2).mean()))
print("\n  winrate attaquant par manoeuvre (vs meilleur contre) :")
for a in IDS: print("    %-10s : meilleur = %.2f  | pire = %.2f" % (MAN[a], W[a].max(), W[a].min()))
print("\n=== ARMS RACE sur 7 manoeuvres (meilleure-reponse) ===")
att = 0
print("  round 0 : ATT=%s (depart)" % MAN[att])
for r in range(1, 8):
    dfd = int(np.argmin(W[att, :])); att2 = int(np.argmax(W[:, dfd]))
    print("  round %d : def=%-10s -> att=%-10s | winrate %.2f | NOUVEAUTE vs depart %.2f" % (r, MAN[dfd], MAN[att2], W[att2, dfd], nov(att2, 0)), flush=True)
    if att2 == att: print("    -> equilibre."); break
    att = att2
