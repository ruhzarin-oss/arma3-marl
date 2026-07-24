#!/usr/bin/env python3
"""corps.py — CORPS-SOUS-LE-FEU : recette SHAMAL sur le micro calibré (assault_terrain secure_task, hit=0.18).
  bc  : imite le prof TIMIDE (avance + suppress si LOS) -> colonne d'exploration (corps_bc.pt)
  rl  : PPO fine-tune « prendre le FOB » depuis le warm-start BC -> l'agent découvre couvert/tempo/postures (corps_rl.pt)
Obs = variante Arma-17 (arma_obs+team+suffer+postures) -> se redéploie par la couture shamal_obs.sqf.
Baselines à battre (Arma-calibré) : timide 20% pris ; l'appris doit MONTER en coupant les pertes.
Smoke : python corps.py smoke"""
import sys, math, time, json, torch
import torch.nn as nn
from torch.distributions import Categorical
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net, ppo_mb
import terrain_gpu as TG
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl"
BC_OUT = BASE + "/corps_bc.pt"; RL_OUT = BASE + "/corps_rl.pt"


def save_meta(path, kind, iters):   # HYGIÈNE (audit #4) : chaque .pt embarque ses hyperparamètres + son env
    e = mkenv(2, 0)
    meta = {"kind": kind, "obs_dim": e.obs_dim, "n_actions": e.n_actions, "A": e.A, "D": e.D,
            "hit": e.hit, "move": e.move, "R_spawn": e.R_spawn, "secure_r": e.secure_r,
            "secure_task": e.secure_task, "secure_only": e.secure_only, "supp_kill": e.supp_kill,
            "replica": e.replica, "arma_obs": True, "teacher": "timid", "iters": iters, "net": "Net(256,3)"}
    json.dump(meta, open(path + ".meta.json", "w"), indent=1)
    print("  meta -> %s.meta.json" % path, flush=True)


def mkenv(n, sd, win_bonus=1.0, suffer_pen=1.1, death_pen=0.4, approach_w=0.5, kill_w=1.5, hull=True, replica_path=None):
    # RECALIBRÉ Arma : secure_only + feu faible -> force à CLORE ; + TERRAIN répliqué (LOS variable, comme Arma -> transfert)
    return AssaultTerrain(num_envs=n, A=18, D=12, R_spawn=140.0, secure_r=25.0, hit=0.18,
                          secure_task=True, secure_only=True, supp_kill=0.25, approach_w=approach_w, win_bonus=win_bonus,
                          suffer_pen=suffer_pen, death_pen=death_pen, kill_w=kill_w, postures=True, suffer=True, hull=hull,
                          team_obs=True, arma_obs=True, replica=True, replica_path=replica_path or (BASE + "/replica.npz"),
                          max_steps=55, device=DEV, seed=sd)   # hull : posture couchée = petite cible -> couvert/posture COMPTENT


def timid(e):   # PROF COVER-AWARE : avance vers le FOB ; SE COUCHE (12) s'il prend du feu (couvert) ; sinon SUPPRESS (9) si cible
    cap = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    los = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale)
    engaged = (los > 0.5) & (nd < e.fire_range)
    hit = e.last_dmg_in > 0.005                                       # a pris du feu au dernier tick -> plonger au sol (posture COUCHÉE = petite cible)
    act = torch.where(hit, torch.full_like(cap, 12), torch.where(engaged, torch.full_like(cap, 9), cap))
    return act


def timid_plain(e):   # PROF PLAIN (config du 60%) : avance vers le FOB, SUPPRESS si cible en LOS+portée, PAS de posture
    cap = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    los = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale)
    return torch.where((los > 0.5) & (nd < e.fire_range), torch.full_like(cap, 9), cap)


def fsm_teacher(e, R=4, C=1):
    # PROF FSM À BONDS (Fable) : horloge = PROGRESSION (e.t), JAMAIS le feu. Cycle : STAND(1) -> MOVE(R-1) -> PRONE(C) -> répète.
    # Le rythme est dans la FSM (mémoire de phase), pas réactif -> pas de gel absorbant. Assaut continu sous le rayon.
    P = R + C
    ph = (e.t % P).unsqueeze(1)                                   # (N,1) phase partagée par l'escouade (bond synchronisé)
    cap = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    engaged = (e._losc(e.hm, e.apx, e.apy, bx, by, e.scale) > 0.5) & (nd < e.fire_range)
    stand = torch.full_like(cap, 10); prone = torch.full_like(cap, 12); fire = torch.full_like(cap, 9)
    act = torch.where(ph == 0, stand, torch.where(ph < R, cap, torch.where(engaged, fire, prone)))   # STAND -> MOVE -> COUVERT(couché/tire)
    near = (torch.sqrt(e.apx ** 2 + e.apy ** 2) < e.secure_r + 15)                                    # près du FOB -> ASSAUT continu (fonce)
    return torch.where(near, cap, act)


def cover_teacher(e):
    # PROF COVER-ROUTING (SANS mémoire, SANS phase, SANS gel) : = timid_plain, mais le MOUVEMENT suit la route la plus COUVERTE.
    # Pour chaque cap, dcover à l'arrivée (14 m devant) ; on garde le cône avant (cap-FOB ±45°) et on prend le PLUS couvert.
    # dcover bas = près d'un bâti = rayons du corps bloqués = moins d'exposition. Memoryless -> imitable par un feedforward.
    N, A = e.apx.shape
    th = torch.arange(8, device=DEV).float() * (math.pi / 4)                                  # (8,) les 8 caps
    nx = e.apx.unsqueeze(2) + torch.sin(th) * e.move                                          # (N,A,8) arrivée 14 m devant, par cap
    ny = e.apy.unsqueeze(2) + torch.cos(th) * e.move
    dc8 = TG.sample(e.dcover, nx.reshape(N, -1), ny.reshape(N, -1), e.scale).reshape(N, A, 8)  # dist-au-bâti à l'arrivée (bas=couvert)
    fob = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()                # (N,A) cap vers le FOB
    diff = (torch.arange(8, device=DEV)[None, None, :] - fob.unsqueeze(2)) % 8                 # (N,A,8) écart au cap FOB
    forward = (diff <= 1) | (diff >= 7)                                                        # cône avant : cap FOB ±1 (±45°)
    score = torch.where(forward, dc8, torch.full_like(dc8, 1e9))                               # hors cône avant = interdit
    best = score.argmin(2).long()                                                             # cap avant le PLUS couvert
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    engaged = (e._losc(e.hm, e.apx, e.apy, bx, by, e.scale) > 0.5) & (nd < e.fire_range)        # même logique de feu que timid_plain
    near = torch.sqrt(e.apx ** 2 + e.apy ** 2) < e.secure_r + 15
    act = torch.where(engaged, torch.full_like(best, 9), best)                                 # cible en vue -> SUPPRESS ; sinon bond couvert
    return torch.where(near, fob, act)                                                         # près du FOB -> ASSAUT tout droit


@torch.no_grad()
def evaluate(net, envs=2048, seed=100, hull=True):
    e = mkenv(envs, seed, hull=hull); obs = e.reset(); done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
    tk = wn = ls = nep = 0.0
    for t in range(55):
        a = net.a_logits(obs).argmax(-1)
        obs, _, done, info = e.step(a, auto_reset=False); d2 = done.bool() & ~done_once
        if d2.any():
            tk += info["took"][d2].float().sum().item(); wn += info["win"][d2].float().sum().item()
            ls += (info["losses"][d2] * e.A).sum().item(); nep += int(d2.sum())
        done_once |= done.bool()
    n = max(nep, 1); return tk / n, wn / n, ls / n


def bc(iters=2500, envs=4096, T=8):
    env = mkenv(envs, 1); O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 256, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    obs = env.reset(); t0 = time.time()
    print("=== BC : imite le prof TIMIDE | obs=%d actions=%d ===" % (O, NA), flush=True)
    for it in range(iters):
        OB = []; AC = []
        for _ in range(T):
            a = timid(env); OB.append(obs); AC.append(a); obs, _, _, _ = env.step(a)
        ob = torch.stack(OB).reshape(-1, O); ac = torch.stack(AC).reshape(-1)
        logits = net.a_logits(ob); loss = nn.functional.cross_entropy(logits, ac)
        opt.zero_grad(); loss.backward(); opt.step()
        if it % 400 == 0 or it == iters - 1:
            acc = (logits.argmax(-1) == ac).float().mean().item()
            print("  bc it %4d | loss %.3f | acc %.2f | %.0fs" % (it, loss.item(), acc, time.time() - t0), flush=True)
    torch.save(net.state_dict(), BC_OUT); save_meta(BC_OUT, "bc", iters)
    tk, wn, ls = evaluate(net); print("=== BC fini -> %s | éval: FOB pris %.0f%% victoire %.0f%% pertes %.1f/18 ===" % (BC_OUT, 100 * tk, 100 * wn, ls), flush=True)


def rl(iters=350, envs=8192, T=16, warm=True):
    # RÉCOMPENSE CENTRÉE PRISE : prendre le FOB DOMINE tout ; kill_w quasi nul (pas de stand-off-attrit) ; mort peu chère
    env = mkenv(envs, 2, win_bonus=4.0, approach_w=0.8, suffer_pen=0.2, death_pen=0.2, kill_w=0.3)
    O, NA, N, A = env.obs_dim, env.n_actions, envs, 18
    net = Net(O, NA, 256, 3).to(DEV)
    if warm:
        net.load_state_dict(torch.load(BC_OUT, map_location=DEV)); print("warm-start depuis BC", flush=True)
    opt = torch.optim.Adam(net.parameters(), 1e-4); cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.005)   # fine-tune DOUX (ne pas casser le BC)
    obs = env.reset(); t0 = time.time()
    print("=== RL : fine-tune « prendre le FOB » | envs=%d T=%d ===" % (N, T), flush=True)
    tk, wn, ls = evaluate(net); print("  [warm] FOB pris %.0f%% | victoire %.0f%% | pertes %.1f/18" % (100 * tk, 100 * wn, ls), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, N, A, O, device=DEV), act=torch.zeros(T, N, A, dtype=torch.long, device=DEV),
                 logp=torch.zeros(T, N, A, device=DEV), rew=torch.zeros(T, N, device=DEV),
                 val=torch.zeros(T, N, device=DEV), done=torch.zeros(T, N, device=DEV))
        for t in range(T):
            with torch.no_grad():
                dd = Categorical(logits=net.a_logits(obs)); a = dd.sample()
                B["obs"][t] = obs; B["act"][t] = a; B["logp"][t] = dd.log_prob(a); B["val"][t] = net.value(obs)
            obs, rew, done, info = env.step(a); B["rew"][t] = rew; B["done"][t] = done
        with torch.no_grad(): lv = net.value(obs)
        ppo_mb(net, opt, B, lv, cfg, DEV, 65536)
        if it % 25 == 0 or it == iters - 1:
            tk, wn, ls = evaluate(net)
            print("  rl it %3d | FOB pris %.0f%% | victoire %.0f%% | pertes %.1f/18 | %.0fs" % (it, 100 * tk, 100 * wn, ls, time.time() - t0), flush=True)
    torch.save(net.state_dict(), RL_OUT); save_meta(RL_OUT, "rl", iters); print("=== RL fini -> %s ===" % RL_OUT, flush=True)


def deconf(iters=800, envs=4096, T=8):
    OUT60 = BASE + "/corps_bc_60.pt"
    env = mkenv(envs, 1, hull=False); O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 256, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    obs = env.reset(); t0 = time.time()
    print("=== RESTORE 60% : BC prof PLAIN, SANS hull (config du 60%) ===", flush=True)
    for it in range(iters):
        OB = []; AC = []
        for _ in range(T):
            a = timid_plain(env); OB.append(obs); AC.append(a); obs, _, _, _ = env.step(a)
        ob = torch.stack(OB).reshape(-1, O); ac = torch.stack(AC).reshape(-1)
        logits = net.a_logits(ob); loss = nn.functional.cross_entropy(logits, ac)
        opt.zero_grad(); loss.backward(); opt.step()
        if it % 400 == 0 or it == iters - 1:
            print("  bc it %4d | loss %.3f | acc %.2f | %.0fs" % (it, loss.item(), (logits.argmax(-1) == ac).float().mean().item(), time.time() - t0), flush=True)
    torch.save(net.state_dict(), OUT60); save_meta(OUT60, "bc_plain_nohull_RESTORE60", iters)
    print("=== restauré+tagué -> %s ===" % OUT60, flush=True)
    e1 = evaluate(net, hull=False); e2 = evaluate(net, hull=True)
    print("=== DÉ-CONFUSION : le MÊME policy (prof plain) évalué dans 2 PHYSIQUES ===", flush=True)
    print("  SANS hull (monde du 60%)  : FOB pris %.0f%% | pertes %.1f/18" % (100 * e1[0], e1[2]), flush=True)
    print("  AVEC hull (nouveau monde) : FOB pris %.0f%% | pertes %.1f/18" % (100 * e2[0], e2[2]), flush=True)
    print("  >>> %s" % ("la PHYSIQUE (hull) a déplacé les buts (le plain s'effondre aussi)" if e1[0] > 0 and e2[0] < e1[0] * 0.6 else "PHYSIQUE INNOCENTE -> le prof cover-aware était bien le coupable du 3%"), flush=True)


def fsm(iters=800, envs=4096, T=8):
    OUT = BASE + "/corps_bc_fsm.pt"
    e = mkenv(256, 5); e.reset()
    print("=== SMOKE RYTHME (doit PROUVER : posture oscille stand/prone + distance DÉCROÎT) ===", flush=True)
    for t in range(12):
        a = fsm_teacher(e)
        pr = (a == 12).float().mean().item(); st = (a == 10).float().mean().item()
        al = e._aalive().float(); d = (torch.sqrt(e.apx ** 2 + e.apy ** 2) * al).sum().item() / al.sum().clamp(min=1).item()
        print("  t%2d ph%d | stand %.2f prone %.2f | dist_moy %.0f" % (t, int(e.t[0].item()) % 5, st, pr, d), flush=True)
        e.step(a)
    env = mkenv(envs, 1); O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 256, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    obs = env.reset(); t0 = time.time()
    print("=== BC FSM : imite le prof À BONDS ===", flush=True)
    for it in range(iters):
        OB = []; AC = []
        for _ in range(T):
            a = fsm_teacher(env); OB.append(obs); AC.append(a); obs, _, _, _ = env.step(a)
        ob = torch.stack(OB).reshape(-1, O); ac = torch.stack(AC).reshape(-1)
        logits = net.a_logits(ob); loss = nn.functional.cross_entropy(logits, ac)
        opt.zero_grad(); loss.backward(); opt.step()
        if it % 400 == 0 or it == iters - 1:
            print("  bc it %4d | loss %.3f | acc %.2f | %.0fs" % (it, loss.item(), (logits.argmax(-1) == ac).float().mean().item(), time.time() - t0), flush=True)
    torch.save(net.state_dict(), OUT); save_meta(OUT, "bc_fsm_bonds", iters)
    tk, wn, ls = evaluate(net)
    print("=== BC FSM fini -> %s | eval sandbox DUR: FOB pris %.0f pct | pertes %.1f/18 ===" % (OUT, 100 * tk, ls), flush=True)


def cover(iters=800, envs=4096, T=8):
    OUT = BASE + "/corps_bc_cover.pt"
    # SMOKE : PROUVER que le prof ROUTE (dcover à l'arrivée du prof < dcover d'un beeline) ET AVANCE (dist décroît). Sinon le terrain est plat -> routing inutile.
    e = mkenv(256, 5); e.reset()
    print("=== SMOKE COVER-ROUTING (doit PROUVER : dcover_route < dcover_beeline ET dist décroît) ===", flush=True)
    for t in range(10):
        a = cover_teacher(e)
        capb = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()
        thr = a.clamp(max=7).float() * (math.pi / 4); dcr = TG.sample(e.dcover, e.apx + torch.sin(thr) * e.move, e.apy + torch.cos(thr) * e.move, e.scale)
        thb = capb.float() * (math.pi / 4); dcb = TG.sample(e.dcover, e.apx + torch.sin(thb) * e.move, e.apy + torch.cos(thb) * e.move, e.scale)
        al = e._aalive().float(); d = (torch.sqrt(e.apx ** 2 + e.apy ** 2) * al).sum().item() / al.sum().clamp(min=1).item()
        print("  t%2d | dcover route %.1f vs beeline %.1f | dist_moy %.0f" % (t, dcr.mean().item(), dcb.mean().item(), d), flush=True)
        e.step(a)
    env = mkenv(envs, 1); O, NA = env.obs_dim, env.n_actions
    net = Net(O, NA, 256, 3).to(DEV); opt = torch.optim.Adam(net.parameters(), 3e-4)
    obs = env.reset(); t0 = time.time()
    print("=== BC COVER-ROUTING : imite le prof qui avance par la route couverte ===", flush=True)
    for it in range(iters):
        OB = []; AC = []
        for _ in range(T):
            a = cover_teacher(env); OB.append(obs); AC.append(a); obs, _, _, _ = env.step(a)
        ob = torch.stack(OB).reshape(-1, O); ac = torch.stack(AC).reshape(-1)
        logits = net.a_logits(ob); loss = nn.functional.cross_entropy(logits, ac)
        opt.zero_grad(); loss.backward(); opt.step()
        if it % 400 == 0 or it == iters - 1:
            print("  bc it %4d | loss %.3f | acc %.2f | %.0fs" % (it, loss.item(), (logits.argmax(-1) == ac).float().mean().item(), time.time() - t0), flush=True)
    torch.save(net.state_dict(), OUT); save_meta(OUT, "bc_cover_routing", iters)
    tk, wn, ls = evaluate(net, hull=True)
    print("=== BC COVER fini -> %s | eval sandbox DUR (hull): FOB pris %.0f pct | pertes %.1f/18 (réf plain-BC ~12 pct) ===" % (OUT, 100 * tk, ls), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "cover": cover(); print("CORPS_DONE", flush=True); sys.exit(0)
    if cmd == "deconf": deconf(); print("CORPS_DONE", flush=True); sys.exit(0)
    if cmd == "fsm": fsm(); print("CORPS_DONE", flush=True); sys.exit(0)
    if cmd == "smoke":
        bc(iters=60, envs=512, T=6); rl(iters=6, envs=512, T=8)
    else:
        if cmd in ("bc", "all"): bc(iters=800, envs=4096, T=8)
        if cmd in ("rl", "all"): rl(iters=300, envs=6144, T=16)
    print("CORPS_DONE", flush=True)
