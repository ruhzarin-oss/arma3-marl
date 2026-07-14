#!/usr/bin/env python3
"""scripted_formation — le CORPS : contrôleur de formation DÉTERMINISTE. Chaque soldat rejoint SON slot
(numéro i -> place(forme,i)), tire quand il a une cible en LOS+portée, sinon avance vers son slot / tient.
La formation avance seule (l'ancre suit l'objectif). Fiable : dist-au-slot -> ~0. SHAMAL / la co-évo décident
la FORME au-dessus ; ceci exécute. Test intégré : python scripted_formation.py"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")


@torch.no_grad()
def scripted_action(env, side, close=8.0):
    """Renvoie l'action (N,n) du contrôleur scripté pour un camp : rejoindre son slot + tirer si cible."""
    d = env.dev
    if side == 0:
        sx, sy, sal = env.ax, env.ay, env._a_alive(); ex, ey, eal = env.bx, env.by, env._b_alive()
        form_idx, tmpl, spost = env.a_form_idx, env._tmplA, env.apost
        z = torch.zeros(env.N, device=d); tx, ty, fwd = z, z, env.form_forward
    else:
        sx, sy, sal = env.bx, env.by, env._b_alive(); ex, ey, eal = env.ax, env.ay, env._a_alive()
        form_idx, tmpl, spost = env.b_form_idx, env._tmplB, env.bpost
        aw = env._a_alive().float(); aws = aw.sum(1).clamp(min=1)
        tx = (env.ax * aw).sum(1) / aws; ty = (env.ay * aw).sum(1) / aws; fwd = 0.0
    slot_x, slot_y = env._side_slots(sx, sy, sal, form_idx, tmpl, tx, ty, fwd)   # numéro -> son slot
    dxe = ex.unsqueeze(1) - sx.unsqueeze(2); dye = ey.unsqueeze(1) - sy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=d)
    ed2 = torch.where(eal.unsqueeze(1), dxe * dxe + dye * dye, BIG)
    km = ed2.argmin(2); bx = torch.gather(ex, 1, km); by = torch.gather(ey, 1, km)
    nd = ed2.min(2).values.clamp(max=1e17).sqrt()
    los = env._losc(sx, sy, bx, by, eye_a=env._eye(spost), eye_b=1.7)
    engaged = (los > 0.5) & (nd < env.fire_range)                                # cible en LOS + portée -> tire
    vx = slot_x - sx; vy = slot_y - sy; dslot = torch.sqrt(vx * vx + vy * vy)
    a_move = (torch.round(torch.atan2(vx, vy) / (math.pi / 4.0)) % 8).long()      # cap vers mon slot
    act = torch.where(dslot > close, a_move,                                      # loin du slot -> ASSEMBLER (prioritaire)
                      torch.where(engaged, torch.full_like(a_move, 9),            # en place + cible -> feu
                                  torch.full_like(a_move, 8)))                    # en place, pas de cible -> tenir
    return torch.where(sal, act, torch.full_like(act, 8))


@torch.no_grad()
def repertoire_action(env, side, close=8.0):
    """Contrôleur UNIFIÉ : exécute (FORMATION, MANŒUVRE) posées par le cerveau.
    manœuvre 0=assaut (avance vers l'objectif) 1=defend (tient) 2=hunt (vers l'ennemi) 3=bounding (feu+mouvement)."""
    d = env.dev
    if side == 0:
        sx, sy, sal = env.ax, env.ay, env._a_alive(); ex, ey, eal = env.bx, env.by, env._b_alive()
        form_idx, tmpl, spost, man = env.a_form_idx, env._tmplA, env.apost, env.a_maneuver
    else:
        sx, sy, sal = env.bx, env.by, env._b_alive(); ex, ey, eal = env.ax, env.ay, env._a_alive()
        form_idx, tmpl, spost, man = env.b_form_idx, env._tmplB, env.bpost, env.b_maneuver
    N, n = sx.shape; z = torch.zeros(N, device=d)
    ew = eal.float(); ews = ew.sum(1).clamp(min=1)
    ecx = (ex * ew).sum(1) / ews; ecy = (ey * ew).sum(1) / ews                    # centroïde ennemi (pour hunt)
    tx = torch.where(man == 2, ecx, z); ty = torch.where(man == 2, ecy, z)        # hunt -> ennemi ; sinon objectif (origine)
    fwd = torch.where(man == 1, z, torch.full((N,), env.form_forward, device=d))  # defend -> 0 (tient), sinon avance
    slot_x, slot_y = env._side_slots(sx, sy, sal, form_idx, tmpl, tx, ty, fwd)
    dxe = ex.unsqueeze(1) - sx.unsqueeze(2); dye = ey.unsqueeze(1) - sy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=d)
    ed2 = torch.where(eal.unsqueeze(1), dxe * dxe + dye * dye, BIG)
    km = ed2.argmin(2); bx = torch.gather(ex, 1, km); by = torch.gather(ey, 1, km)
    nd = ed2.min(2).values.clamp(max=1e17).sqrt()
    los = env._losc(sx, sy, bx, by, eye_a=env._eye(spost), eye_b=1.7)
    engaged = (los > 0.5) & (nd < env.fire_range)
    vx = slot_x - sx; vy = slot_y - sy; dslot = torch.sqrt(vx * vx + vy * vy)
    a_move = (torch.round(torch.atan2(vx, vy) / (math.pi / 4.0)) % 8).long()
    act = torch.where(dslot > close, a_move,                                      # rejoindre son slot
                      torch.where(engaged, torch.full_like(a_move, 9), torch.full_like(a_move, 8)))
    phase = (env.t // 4) % 2; base = (torch.arange(n, device=d)[None] % 2) == phase[:, None]   # BOUNDING : base cloue, manœuvre bondit
    a_bound = torch.where(base, torch.where(engaged, torch.full_like(a_move, 9), torch.full_like(a_move, 8)), a_move)
    act = torch.where((man == 3).unsqueeze(1), a_bound, act)
    return torch.where(sal, act, torch.full_like(act, 8))


if __name__ == "__main__":
    import formations as FORM
    from duel_terrain import DuelTerrain
    DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
    print("=== CONTRÔLEUR SCRIPTÉ : le corps rejoint-il les slots ? (dist-au-slot au fil du temps) ===")
    for form in ["coin", "ligne", "echelon_gauche", "cercle", "carre"]:
        e = DuelTerrain(num_envs=256, A=12, B=8, a_form=form, form_forward=6.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=0)
        e.reset(); z = torch.zeros(e.N, device=DEV); ds = []; w = 0.0; nep = 0; fired = 0
        done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
        for t in range(60):
            sx, sy = e._side_slots(e.ax, e.ay, e._a_alive(), e.a_form_idx, e._tmplA, z, z, e.form_forward)
            al = e._a_alive().float(); ds.append(((torch.sqrt((e.ax - sx) ** 2 + (e.ay - sy) ** 2) * al).sum() / al.sum().clamp(min=1)).item())
            aA = scripted_action(e, 0); aB = scripted_action(e, 1)
            fired += int((aA == 9).float().sum().item())
            (o), _, done, info = e.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
            if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
            done_once |= done.bool()
        fin = sum(ds[-10:]) / 10
        v = "TIENT ✓" if fin < 8 else ("approx" if fin < 16 else "KO")
        print("  %-14s | début=%4.1f  fin=%4.1f  min=%4.1f  | tirs=%d | winrate=%.2f  -> %s" % (form, ds[0], fin, min(ds), fired, w / max(nep, 1), v))
    print("SCRIPTED_DONE")
