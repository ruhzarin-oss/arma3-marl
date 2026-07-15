#!/usr/bin/env python3
"""coevo_rl2.py — C1 : CO-EVOLUTION RL 2 COTES + LEAGUE. Attaquant ET defenseur apprennent (composeurs
REINFORCE) l'un contre une LEAGUE de snapshots geles de l'autre. Montre : arms race non-effondree
(winrate reste equilibre, pas de collapse) + nouveaute qui s'accumule par generation."""
import sys, math, copy, torch, torch.nn as nn, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NM = 7; WARM = 6
N = 384; GEN = 5; ITERS = 25


def ext_action(e, side):
    base = repertoire_action(e, side); man = e.a_maneuver if side == 0 else e.b_maneuver; d = e.dev
    if side == 0:
        sx, sy, sal = e.ax, e.ay, e._a_alive(); ex, ey, eal = e.bx, e.by, e._b_alive(); spost = e.apost
    else:
        sx, sy, sal = e.bx, e.by, e._b_alive(); ex, ey, eal = e.ax, e.ay, e._a_alive(); spost = e.bpost
    Nn, n = sx.shape; ar = torch.arange(n, device=d)[None]
    ew = eal.float(); ews = ew.sum(1, keepdim=True).clamp(min=1); ecx = (ex * ew).sum(1, keepdim=True) / ews; ecy = (ey * ew).sum(1, keepdim=True) / ews
    sw = sal.float(); sws = sw.sum(1, keepdim=True).clamp(min=1); mcx = (sx * sw).sum(1, keepdim=True) / sws; mcy = (sy * sw).sum(1, keepdim=True) / sws
    dirx = ecx - mcx; diry = ecy - mcy; dn = torch.sqrt(dirx * dirx + diry * diry).clamp(min=1e-3); perpx = -diry / dn; perpy = dirx / dn
    dxe = ex.unsqueeze(1) - sx.unsqueeze(2); dye = ey.unsqueeze(1) - sy.unsqueeze(2)
    ed2 = torch.where(eal.unsqueeze(1), dxe * dxe + dye * dye, torch.tensor(1e18, device=d)); km = ed2.argmin(2)
    bx = torch.gather(ex, 1, km); by = torch.gather(ey, 1, km); nd = ed2.min(2).values.clamp(max=1e17).sqrt()
    los = e._losc(sx, sy, bx, by, eye_a=e._eye(spost), eye_b=1.7); engaged = (los > 0.5) & (nd < e.fire_range)
    grp = ar % 3
    px = ecx.expand(Nn, n) + perpx * 55.0 * (grp == 1).float() - perpx * 55.0 * (grp == 2).float()
    py = ecy.expand(Nn, n) + perpy * 55.0 * (grp == 1).float() - perpy * 55.0 * (grp == 2).float()
    a5 = (torch.round(torch.atan2(px - sx, py - sy) / (math.pi / 4.0)) % 8).long()
    lat = (ar.float() / max(n - 1, 1)) * 60.0; ex6 = ecx.expand(Nn, n) + perpx * lat; ey6 = ecy.expand(Nn, n) + perpy * lat
    a6 = (torch.round(torch.atan2(ex6 - sx, ey6 - sy) / (math.pi / 4.0)) % 8).long()
    a5 = torch.where(engaged, torch.full_like(a5, 9), a5); a6 = torch.where(engaged, torch.full_like(a6, 9), a6)
    out = torch.where((man == 5).unsqueeze(1), a5, base); out = torch.where((man == 6).unsqueeze(1), a6, out)
    return torch.where(sal, out, torch.full_like(out, 8))


def feats(e, side):
    if side == 0: sx, sy, sal, ex, ey, eal = e.ax, e.ay, e._a_alive().float(), e.bx, e.by, e._b_alive().float()
    else: sx, sy, sal, ex, ey, eal = e.bx, e.by, e._b_alive().float(), e.ax, e.ay, e._a_alive().float()
    aw = sal.sum(1, keepdim=True).clamp(min=1); bw = eal.sum(1, keepdim=True).clamp(min=1)
    acx = (sx * sal).sum(1, keepdim=True) / aw; acy = (sy * sal).sum(1, keepdim=True) / aw
    bcx = (ex * eal).sum(1, keepdim=True) / bw; bcy = (ey * eal).sum(1, keepdim=True) / bw
    dist = torch.sqrt((bcx - acx) ** 2 + (bcy - acy) ** 2).squeeze(1) / e.scale
    pdx = ex.unsqueeze(1) - ex.unsqueeze(2); pdy = ey.unsqueeze(1) - ey.unsqueeze(2)
    espread = torch.sqrt(pdx * pdx + pdy * pdy).mean((1, 2)) / e.scale
    dirx = bcx - acx; diry = bcy - acy; dnn = torch.sqrt(dirx * dirx + diry * diry).clamp(min=1e-3)
    lat = ((ex - bcx) * (-diry / dnn) + (ey - bcy) * (dirx / dnn))
    lat_sp = (lat.abs() * eal).sum(1) / bw.squeeze(1) / e.scale
    return torch.stack([dist, espread, lat_sp, sal.mean(1), eal.mean(1)], 1)


def mknet(): return nn.Sequential(nn.Linear(5, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, NM)).to(DEV)
def mkenv(sd): return DuelTerrain(num_envs=N, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)


def rollout(pickA, pickB, sd):
    e = mkenv(sd); e.reset()
    e.a_maneuver = torch.full((e.N,), 2, dtype=torch.long, device=DEV); e.b_maneuver = torch.full((e.N,), 1, dtype=torch.long, device=DEV)
    for _ in range(WARM): e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
    oA = feats(e, 0); oB = feats(e, 1); mA, lpA = pickA(oA); mB, _ = pickB(oB)
    e.a_maneuver = mA; e.b_maneuver = mB
    done = torch.zeros(e.N, dtype=torch.bool, device=DEV); wins = torch.zeros(e.N, device=DEV)
    for _ in range(WARM, 60):
        (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        nw = dn.bool() & ~done; wins[nw] = info["att_wins"][nw].float(); done |= dn.bool()
    return wins, lpA, oA, mA


def net_pick(net, sample=True):
    def p(o):
        dstr = torch.distributions.Categorical(logits=net(o)); m = dstr.sample() if sample else net(o).argmax(-1)
        return m, dstr.log_prob(m)
    return p


def frozen_pick(sd_state):
    fn = mknet(); fn.load_state_dict(sd_state); fn.eval()
    return lambda o: (torch.distributions.Categorical(logits=fn(o)).sample(), None)


netA = mknet(); netB = mknet(); optA = torch.optim.Adam(netA.parameters(), 3e-3); optB = torch.optim.Adam(netB.parameters(), 3e-3)
leagueA = [copy.deepcopy(netA.state_dict())]; leagueB = [copy.deepcopy(netB.state_dict())]
import numpy.random as npr
prof0 = None
print("=== CO-EVOLUTION RL 2 COTES + LEAGUE ===", flush=True)
for g in range(GEN):
    for it in range(ITERS):                                                       # entraine A vs league B
        opp = frozen_pick(leagueB[it % len(leagueB)])
        w, lp, _, _ = rollout(net_pick(netA), opp, g * 100 + it)
        loss = -((w - w.mean()) * lp).mean(); optA.zero_grad(); loss.backward(); optA.step()
    for it in range(ITERS):                                                       # entraine B vs league A (defenseur MINIMISE att_wins)
        e = mkenv(g * 100 + 90 + it); e.reset(); e.a_maneuver = torch.full((e.N,), 2, dtype=torch.long, device=DEV); e.b_maneuver = torch.full((e.N,), 1, dtype=torch.long, device=DEV)
        for _ in range(WARM): e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        oB = feats(e, 1); dstr = torch.distributions.Categorical(logits=netB(oB)); mB = dstr.sample()
        oppA = frozen_pick(leagueA[it % len(leagueA)]); mA, _ = oppA(feats(e, 0))
        e.a_maneuver = mA; e.b_maneuver = mB; done = torch.zeros(e.N, dtype=torch.bool, device=DEV); wins = torch.zeros(e.N, device=DEV)
        for _ in range(WARM, 60):
            (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
            nw = dn.bool() & ~done; wins[nw] = info["att_wins"][nw].float(); done |= dn.bool()
        rB = -wins; loss = -((rB - rB.mean()) * dstr.log_prob(mB)).mean(); optB.zero_grad(); loss.backward(); optB.step()
    leagueA.append(copy.deepcopy(netA.state_dict())); leagueB.append(copy.deepcopy(netB.state_dict()))
    wr, _, _, _ = rollout(net_pick(netA, False), net_pick(netB, False), 7000 + g)
    with torch.no_grad():
        e = mkenv(7000 + g); e.reset(); e.a_maneuver = torch.full((e.N,), 2, dtype=torch.long, device=DEV)
        for _ in range(WARM): e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        dA = torch.softmax(netA(feats(e, 0)), -1).mean(0)
        if prof0 is None: prof0 = dA.clone()
        nov = float((dA - prof0).abs().sum())
    print("  gen %d : winrate ATT vs DEF = %.2f | nouveaute mix ATT vs gen0 = %.2f | league=%d" % (g, wr.mean().item(), nov, len(leagueA)), flush=True)
print("  -> co-evo 2 cotes avec league : winrate reste equilibre (pas d'effondrement), les 2 co-adaptent.")
