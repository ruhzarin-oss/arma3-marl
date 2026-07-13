"""shamal_teacher — le PROF scripté (distillation de LAMBS) pour le sandbox AssaultTerrain.

Politique PRIVILÉGIÉE (elle lit l'état VRAI de l'env, comme un prof qui voit tout) qui reproduit
les 7 règles tactiques TRANSFÉRABLES de LAMBS Danger, traduites dans l'espace obs/action du sandbox :

  1. AVANCER vers l'objectif (Rush/Assault)                -> cap vers l'origine (actions 0-7)
  2. TIRER / SUPPRIMER sur LOS+portée (doSuppress)         -> action 9
  3. SE METTRE À COUVERT (doCover)                          -> cap vers le bâti le + proche
  4. BAISSER LA POSTURE sous le feu (doDodge / hull-down)  -> action 11 (accroupi), avant de tirer
  5. FLANQUER (doGroupFlank)                                -> biais latéral ±30° de l'axe d'approche
  6. PARTAGER L'INFO (doShareInformation)                  -> NO-OP ici : l'obs donne déjà l'ennemi le
       plus proche en clair (info parfaite). La carte brouillard-mémoire est un AUTRE env (carte.py,
       flag use_carte) ; rule 6 s'activera là-bas, pas dans AssaultTerrain.
  7. ROMPRE LE CONTACT si débordé (doHide/doFleeing)       -> cap opposé à l'objectif

Le prof fournit les cibles (obs_étudiant -> action_prof) pour le behavior cloning SHAMAL (shamal_bc.py).
Sortie : acts (N,A) long. 100% vectorisé GPU, aucun rendu, aucune physique (géométrie seule).
"""
import math
import torch
import terrain_gpu as TG


@torch.no_grad()
def shamal_action(e, drop_to=1, flank=True, retreat=True):
    """Renvoie l'action scriptée (N,A) du prof SHAMAL, en lisant l'état privilégié de l'env `e`."""
    d = e.dev; N, A, D, S = e.N, e.A, e.D, e.scale
    apx, apy = e.apx, e.apy
    al = e._aalive()                                        # (N,A) attaquant vivant
    dalive = e._dalive()                                    # (N,D) défenseur vivant

    # ---- ennemi le plus proche (miroir de _obs, privilégié) ----
    ex = e.dpx.unsqueeze(1) - apx.unsqueeze(2)              # (N,A,D)
    ey = e.dpy.unsqueeze(1) - apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=d)
    ed2 = torch.where(dalive.unsqueeze(1), ex * ex + ey * ey, BIG)
    km = ed2.argmin(2)                                      # (N,A) index défenseur le + proche
    bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km)
    nd = ed2.min(2).values.clamp(max=1e17).sqrt()          # (N,A) distance ennemi

    # ---- LOS + portée sur l'ennemi le plus proche (règle 2) ----
    los = e._losc(e.hm, apx, apy, bx, by, S, eye_a=e._eye(), eye_b=1.7)   # (N,A) {0,1}
    engage = (los > 0.5) & (nd < e.fire_range)              # je peux tirer

    # ---- règle 1 : AVANCER (cap vers l'origine) + règle 5 : FLANC (biais latéral) ----
    th_obj = torch.atan2(-apx, -apy)                        # cap vers (0,0) (convention step : sin,cos)
    if flank:
        side = torch.ones(A, device=d); side[:A // 2] = -1.0
        side = side[None].expand(N, A)
        far = (nd > 2.5 * e.secure_r).float()               # l'ouverture se resserre en approchant
        th_obj = th_obj + side * (math.pi / 6.0) * far      # ±30° -> deux pointes qui convergent
    a_adv = (torch.round(th_obj / (math.pi / 4.0)) % 8).long()

    # ---- menace : nb de défenseurs vivants qui peuvent me toucher (LOS+portée), privilégié ----
    n_threat = torch.zeros(N, A, device=d)
    for di in range(D):
        bbx = e.dpx[:, di:di + 1].expand(N, A); bby = e.dpy[:, di:di + 1].expand(N, A)
        l = e._losc(e.hm, apx, apy, bbx, bby, S, eye_a=e._eye(), eye_b=1.7)
        dist = torch.sqrt((apx - e.dpx[:, di:di + 1]) ** 2 + (apy - e.dpy[:, di:di + 1]) ** 2)
        n_threat += dalive[:, di:di + 1].float() * l * (dist < e.fire_range).float()
    under_fire = (e.last_dmg_in > 1e-4) | (n_threat > 0.5)  # touché au dernier pas OU dans une ligne de tir

    # ---- règle 3 : COUVERT (cap vers le bâti le + proche) ----
    incover = TG.sample(e.cover, apx, apy, S) > 0.5
    a_cover, cover_found = _cover_heading(e, apx, apy, S)
    cover_cond = under_fire & ~engage & ~incover & cover_found   # menacé, pas de tir possible, pas déjà couvert

    # ---- règles 2 + 4 : TIRER, ou d'abord se baisser (hull-down) une fois ----
    a_engage = torch.full((N, A), 9, dtype=torch.long, device=d)     # 9 = SUPPRESS (tirer)
    if e.postures:
        standing = (e.posture == 0)
        a_engage = torch.where(standing & under_fire,               # debout + sous le feu -> hull-down 1 pas
                               torch.full_like(a_engage, 10 + drop_to),   # 11 accroupi (drop_to=1) / 12 couché (2)
                               a_engage)                            # puis (posture basse) -> tire

    # ---- règle 7 : ROMPRE LE CONTACT si débordé (escouade attritée + sous le feu de plusieurs) ----
    al_frac = al.float().sum(1, keepdim=True) / A                   # (N,1)
    overwhelmed = retreat & (n_threat >= 2) & (al_frac < 0.4)
    a_retreat = ((a_adv + 4) % 8).long()                            # cap opposé à l'objectif

    # ---- cascade de priorité (le plus bas est écrasé par le plus haut) ----
    act = a_adv                                                     # 1+5 avancer/flanquer
    act = torch.where(cover_cond, a_cover, act)                     # 3  se couvrir
    act = torch.where(engage, a_engage, act)                        # 2+4 tirer / se baisser d'abord
    act = torch.where(overwhelmed, a_retreat, act)                  # 7  décrocher
    act = torch.where(al, act, torch.full_like(act, 8))             # morts -> HOLD (sans effet)
    return act


def _cover_heading(e, apx, apy, S, R=45.0, steps=15):
    """Cap (0-7) vers le couvert (bâti) atteignable le + proche ; cover_found=False si aucun sous R.
    Marche 8 rayons (les 8 caps du step) et prend la direction dont le 1er couvert est le + proche."""
    d = e.dev; N, A = e.N, e.A
    offs = torch.arange(8, device=d).float() * (math.pi / 4.0)      # 8 caps (mêmes que step)
    cs = torch.sin(offs); sn = torch.cos(offs)                      # step : (sin, cos)
    stp = (torch.arange(1, steps + 1, device=d).float() / steps) * R
    sx = apx[..., None, None] + cs[None, None, :, None] * stp[None, None, None, :]   # (N,A,8,steps)
    sy = apy[..., None, None] + sn[None, None, :, None] * stp[None, None, None, :]
    cov = TG.sample(e.cover, sx.reshape(N, -1), sy.reshape(N, -1), S).reshape(N, A, 8, steps) > 0.5
    anyh = cov.any(-1)                                              # (N,A,8) cette dir a du couvert ?
    first = torch.where(anyh, cov.float().argmax(-1),               # 1er pas touché (steps si aucun)
                        torch.full_like(cov[..., 0].float(), float(steps)))
    best = first.argmin(-1).long()                                 # (N,A) dir du couvert le + proche
    found = anyh.any(-1)                                            # (N,A)
    return best, found


if __name__ == "__main__":
    import numpy as np
    from assault_terrain import AssaultTerrain
    DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
    RP = "/home/younes/arma3-marl/replica.npz"
    print("=== PROF SHAMAL : compétence vs foncer-aveugle (replica, 9v6) ===", flush=True)

    def mk(sd):
        return AssaultTerrain(num_envs=256, A=9, D=6, R_spawn=115.0, relief=40.0, hit=0.10,
                              shell_obs=True, team_obs=True, suffer=True, postures=True, hull=True,
                              replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)

    @torch.no_grad()
    def ev(is_teacher):
        e = mk(0); e.reset(); win = dk = sv = 0.0; nep = 0
        done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
        for _ in range(70):
            if is_teacher:
                a = shamal_action(e)
            else:
                a = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4.0)) % 8).long()
            _, _, done, info = e.step(a, auto_reset=False); dm = done.bool() & ~done_once
            if dm.any():
                win += info["neutralized"][dm].float().sum().item()
                dk += info["dkilled"][dm].float().sum().item()
                sv += (1.0 - info["losses"][dm]).sum().item(); nep += int(dm.sum())
            done_once |= done.bool()
        return win / max(nep, 1), dk / max(nep, 1), sv / max(nep, 1)

    w1, k1, s1 = ev(True); w0, k0, s0 = ev(False)
    print("  prof SHAMAL : win %.3f | dkilled %.3f | survie %.3f" % (w1, k1, s1), flush=True)
    print("  foncer      : win %.3f | dkilled %.3f | survie %.3f" % (w0, k0, s0), flush=True)
    print("  -> le prof doit DOMINER foncer (surtout dkilled : foncer ne tire jamais)", flush=True)
    print("SHAMAL_TEACHER_OK", flush=True)
