#!/usr/bin/env python3
"""coevo_composer.py — COMPOSEUR APPRIS (a part). Un reseau observe la situation (a t=6, quand la
manoeuvre ennemie est lisible) et CHOISIT sa manoeuvre. Defenseur = manoeuvre aleatoire (league).
REINFORCE, reward=att_wins. Teste : bat-il le 'toujours enveloppement' en S'ADAPTANT au defenseur ?"""
import sys, math, torch, torch.nn as nn, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"; NM = 7; WARM = 6
SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
N = 128 if SMOKE else 384; ITERS = 3 if SMOKE else 250


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


def feats(e):
    aal = e._a_alive().float(); bal = e._b_alive().float()
    aw = aal.sum(1, keepdim=True).clamp(min=1); bw = bal.sum(1, keepdim=True).clamp(min=1)
    acx = (e.ax * aal).sum(1, keepdim=True) / aw; acy = (e.ay * aal).sum(1, keepdim=True) / aw
    bcx = (e.bx * bal).sum(1, keepdim=True) / bw; bcy = (e.by * bal).sum(1, keepdim=True) / bw
    dist = torch.sqrt((bcx - acx) ** 2 + (bcy - acy) ** 2).squeeze(1) / e.scale
    pdx = e.bx.unsqueeze(1) - e.bx.unsqueeze(2); pdy = e.by.unsqueeze(1) - e.by.unsqueeze(2)
    espread = torch.sqrt(pdx * pdx + pdy * pdy).mean((1, 2)) / e.scale
    dirx = bcx - acx; diry = bcy - acy; dnn = torch.sqrt(dirx * dirx + diry * diry).clamp(min=1e-3)
    perpx = (-diry / dnn); perpy = (dirx / dnn)
    lat = ((e.bx - bcx) * perpx + (e.by - bcy) * perpy)
    lat_sp = (lat.abs() * bal).sum(1) / bw.squeeze(1) / e.scale
    return torch.stack([dist, espread, lat_sp, aal.mean(1), bal.mean(1)], 1)                # (N,5)


def mkenv(sd):
    return DuelTerrain(num_envs=N, A=12, B=8, a_form="ligne", flank=0.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)


def rollout(pick, sd):
    """pick(obs)->maneuver (N,). defenseur = manoeuvre aleatoire. rend (obs, man, reward)."""
    e = mkenv(sd); e.reset()
    e.b_maneuver = torch.randint(0, NM, (e.N,), device=DEV)                                 # league defenseur
    e.a_maneuver = torch.full((e.N,), 2, dtype=torch.long, device=DEV)                      # warm : hunt (avance)
    for _ in range(WARM):
        e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
    o = feats(e); man = pick(o); e.a_maneuver = man
    done = torch.zeros(e.N, dtype=torch.bool, device=DEV); wins = torch.zeros(e.N, device=DEV)
    for _ in range(WARM, 60):
        (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        nw = dn.bool() & ~done; wins[nw] = info["att_wins"][nw].float(); done |= dn.bool()
    return o, man, wins


net = nn.Sequential(nn.Linear(5, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, NM)).to(DEV)
opt = torch.optim.Adam(net.parameters(), 3e-3)
for it in range(ITERS):
    e = mkenv(it); e.reset(); e.b_maneuver = torch.randint(0, NM, (e.N,), device=DEV)
    e.a_maneuver = torch.full((e.N,), 2, dtype=torch.long, device=DEV)
    for _ in range(WARM): e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
    o2 = feats(e); logits = net(o2); dstr = torch.distributions.Categorical(logits=logits); man = dstr.sample()
    e.a_maneuver = man; done = torch.zeros(e.N, dtype=torch.bool, device=DEV); wins = torch.zeros(e.N, device=DEV)
    for _ in range(WARM, 60):
        (_, _), _, dn, info = e.step(ext_action(e, 0), ext_action(e, 1), auto_reset=False)
        nw = dn.bool() & ~done; wins[nw] = info["att_wins"][nw].float(); done |= dn.bool()
    R = wins; adv = R - R.mean()
    loss = -(dstr.log_prob(man) * adv).mean() - 0.01 * dstr.entropy().mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if it % 25 == 0 or SMOKE: print("it %3d  winrate %.3f  loss %.3f" % (it, R.mean().item(), loss.item()), flush=True)


@torch.no_grad()
def evalwr(pick, name, seeds=4):
    ws = []
    for s in range(seeds):
        _, _, w = rollout(pick, 5000 + s); ws.append(w.mean().item())
    print("  %-20s winrate %.3f" % (name, np.mean(ws)), flush=True); return np.mean(ws)


print("\n=== TEST : composeur appris vs manoeuvres FIXES (defenseurs aleatoires) ===")
evalwr(lambda o: net(o).argmax(-1), "composeur APPRIS")
evalwr(lambda o: torch.full((o.shape[0],), 4, device=DEV), "toujours enveloppement")
evalwr(lambda o: torch.full((o.shape[0],), 5, device=DEV), "toujours PINCE")
