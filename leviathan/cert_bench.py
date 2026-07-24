#!/usr/bin/env python3
"""cert_bench — CERTIFICATION du banc (Fable #6) : le sandbox 2.5D RÉCOMPENSE-t-il le couvert ?
Compare 2 politiques triviales à travers la MÊME couture, SANS entraînement :
  - LIGNE DROITE : cap vers l'objectif (beeline).
  - ORACLE EXPO  : parmi le cône avant, va vers la case d'arrivée la MOINS EXPOSÉE (défenseur qui me voit), + pression d'avance.
Le banc n'est CERTIFIÉ que si : survie(oracle) - survie(ligne droite) >= +0.10, ET l'écart vit dans la bande PROCHE (<50m).
Sinon : le sandbox est aveugle au couvert -> inutile d'entraîner dessus.
Usage : python cert_bench.py            (objectif actuel)
        python cert_bench.py OX OY      (objectif décalé au monde (OX,OY))"""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from corps import mkenv
DEV = "cuda:0"


def defender_dirs(e):
    """positions d'arrivée 14m dans 8 caps + exposition (nb défenseurs qui voient) à chaque arrivée. -> (rad8, expo8) (N,A,8)."""
    N, A = e.apx.shape; D = e.D
    th = torch.arange(8, device=DEV).float() * (math.pi / 4)
    nx = e.apx.unsqueeze(2) + torch.sin(th) * e.move                       # (N,A,8)
    ny = e.apy.unsqueeze(2) + torch.cos(th) * e.move
    rad8 = torch.sqrt(nx ** 2 + ny ** 2)
    expo8 = torch.zeros(N, A, 8, device=DEV)
    for di in range(D):
        bx = e.dpx[:, di:di + 1, None].expand(N, A, 8).reshape(N, -1)
        by = e.dpy[:, di:di + 1, None].expand(N, A, 8).reshape(N, -1)
        l = e._losc(e.hm, nx.reshape(N, -1), ny.reshape(N, -1), bx, by, e.scale).reshape(N, A, 8)
        dist = torch.sqrt((nx - e.dpx[:, di:di + 1, None]) ** 2 + (ny - e.dpy[:, di:di + 1, None]) ** 2)
        inr = (dist < e.fire_range).float()
        arcg = 1.0
        if e.def_line:   # l'oracle CONNAÎT l'arc : une case dans l'angle mort d'un défenseur n'est pas exposée par lui -> il flanque
            ang = torch.atan2(nx - e.dpx[:, di:di + 1, None], ny - e.dpy[:, di:di + 1, None])
            adf = torch.atan2(torch.sin(ang - e.dface[:, di:di + 1, None]), torch.cos(ang - e.dface[:, di:di + 1, None]))
            arcg = (adf.abs() <= e._dfarc.unsqueeze(2)).float()
        expo8 += l * inr * e._dalive()[:, di].view(N, 1, 1).float() * arcg
    return nx, ny, rad8, expo8


def fob_cap(e):
    return (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4)) % 8).long()


def pol_straight_ns(e):   # LIGNE DROITE PURE (sans suppression) : cap vers l'objectif, toujours. Métrique propre (la suppression ne masque pas le couvert).
    return fob_cap(e)


def pol_straight(e):
    cap = fob_cap(e)
    dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV); d2 = torch.where(e._dalive().unsqueeze(1), dx * dx + dy * dy, BIG)
    km = d2.argmin(2); bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km); nd = d2.min(2).values.sqrt()
    eng = (e._losc(e.hm, e.apx, e.apy, bx, by, e.scale) > 0.5) & (nd < e.fire_range)
    near = torch.sqrt(e.apx ** 2 + e.apy ** 2) < e.secure_r + 15
    return torch.where(near, cap, torch.where(eng, torch.full_like(cap, 9), cap))


def make_expo_oracle(w, cone=2):
    def pol(e):
        _, _, rad8, expo8 = defender_dirs(e)
        fob = fob_cap(e)
        diff = (torch.arange(8, device=DEV)[None, None, :] - fob.unsqueeze(2)) % 8
        fwd = (diff <= cone) | (diff >= 8 - cone)
        score = torch.where(fwd, rad8 + w * expo8 * e.move, torch.full_like(rad8, 1e9))  # avance + pénalité d'ÊTRE VU (×move pour homogénéiser)
        best = score.argmin(2).long()
        near = torch.sqrt(e.apx ** 2 + e.apy ** 2) < e.secure_r + 15
        return torch.where(near, fob, best)
    return pol


def expo_at(e, ang):
    """exposition (nb défenseurs qui PEUVENT tirer, arc inclus) à la case 14m le long de ang (N,A). -> (N,A)."""
    N, A = e.apx.shape
    nx = e.apx + torch.sin(ang) * e.move; ny = e.apy + torch.cos(ang) * e.move
    expo = torch.zeros(N, A, device=DEV)
    for di in range(e.D):
        bx = e.dpx[:, di:di + 1].expand(N, A); by = e.dpy[:, di:di + 1].expand(N, A)
        l = e._losc(e.hm, nx, ny, bx, by, e.scale)
        dist = torch.sqrt((nx - e.dpx[:, di:di + 1]) ** 2 + (ny - e.dpy[:, di:di + 1]) ** 2)
        inr = (dist < e.fire_range).float()
        arcg = 1.0
        if e.def_line:
            _a = torch.atan2(nx - e.dpx[:, di:di + 1], ny - e.dpy[:, di:di + 1])
            _adf = torch.atan2(torch.sin(_a - e.dface[:, di:di + 1]), torch.cos(_a - e.dface[:, di:di + 1]))
            arcg = (_adf.abs() <= e._dfarc).float()
        expo += l * inr * e._dalive()[:, di:di + 1].float() * arcg
    return expo


def make_flank_assault(flank=1.0, R_switch=45.0):
    """ORACLE FLANC-PUIS-ASSAUT : LOIN -> approche oblique par le côté le MOINS exposé (contourne le bout de la ligne) ; PRÈS -> fonce sur l'objectif."""
    def pol(e):
        phi = torch.atan2(-e.apx, -e.apy)                     # direction vers l'objectif (origine)
        r = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        eL = expo_at(e, phi + flank); eR = expo_at(e, phi - flank)   # exposition des deux obliques
        sgn = torch.where(eL <= eR, torch.ones_like(phi), -torch.ones_like(phi))
        far_ang = phi + sgn * flank                            # oblique vers le flanc aveugle
        ang = torch.where(r > R_switch, far_ang, phi)          # loin = flanque ; près = assaut direct
        return (torch.round(ang / (math.pi / 4)) % 8).long()
    return pol


def make_rear_oracle(R_wp=42.0):
    """ORACLE PAR L'ARRIÈRE (Fable #1, borne le plafond) : contourne large et entre par DERRIÈRE l'objectif (angle mort profond de la ligne)."""
    def pol(e):
        dcx = e.dpx.mean(1, keepdim=True); dcy = e.dpy.mean(1, keepdim=True)   # centroïde défenseurs ~ axe de menace
        rear = torch.atan2(dcx, dcy) + math.pi                                 # azimut DERRIÈRE l'objectif (côté opposé à la ligne)
        wpx = R_wp * torch.sin(rear); wpy = R_wp * torch.cos(rear)             # (N,1) point d'entrée arrière
        to_wp = torch.atan2(wpx - e.apx, wpy - e.apy)                          # cap vers le point arrière
        to_obj = torch.atan2(-e.apx, -e.apy)                                   # cap vers l'objectif
        behind = (e.apx * dcx + e.apy * dcy) < 0                               # attaquant déjà du côté opposé aux défenseurs
        dwp = torch.sqrt((e.apx - wpx) ** 2 + (e.apy - wpy) ** 2)
        ang = torch.where(behind | (dwp < 18), to_obj, to_wp)                  # arrivé derrière / proche du WP -> fonce sur l'objectif
        return (torch.round(ang / (math.pi / 4)) % 8).long()
    return pol


RPATH = None   # carte au choix (None = replica dense d'origine ; sinon replica_open.npz etc.)
NAV = False    # navigation consciente des murs (contourne au lieu de se coincer)
FIXED_TH = None   # axe d'approche fixe (carte dessinée alignée) ; None = aléatoire
FLANK_KILL = 0.0  # létalité du feu de flanc (0 = mur balistique partout)


@torch.no_grad()
def rollout(pol, envs=1024, steps=32, seed=7, def_arc=math.pi, def_line=False, def_spread=1.0, hit=None, def_rand=False):
    e = mkenv(envs, seed, replica_path=RPATH)
    e.nav_around = NAV; e.fixed_th = FIXED_TH; e.flank_kill = FLANK_KILL
    e.def_arc = def_arc; e.def_line = def_line; e.def_spread = def_spread; e.def_rand = def_rand
    if hit is not None: e.hit = hit   # calibration de la létalité du banc
    e.reset()
    took_ever = torch.zeros(envs, dtype=torch.bool, device=DEV)
    peak_force = torch.zeros(envs, device=DEV)   # MÉTRIQUE INCONDITIONNELLE (Fable #3) : max sur l'épisode d'hommes VIVANTS DANS le rayon / A
    for t in range(steps):
        a = pol(e); e.step(a, auto_reset=False)
        inr = (torch.sqrt(e.apx ** 2 + e.apy ** 2) < e.secure_r) & e._aalive()
        peak_force = torch.maximum(peak_force, inr.float().sum(1) / e.A)   # fraction de l'escouade tenant l'objectif
        took_ever |= inr.any(1)
    surv = e._aalive().float().mean().item()
    took = took_ever.float().mean().item()          # % escouades qui sécurisent (≥1 homme dans le rayon)
    force = peak_force.mean().item()                # scalaire HONNÊTE : massacré=0, planqué=0, prise-à-moitié=0.5*(part tenue)
    return took, force, surv


def run_all(hit, def_rand):
    fr = rollout(pol_straight_ns, def_line=True, def_rand=def_rand, hit=hit)                      # FRONTAL
    bf = None
    for flank in (0.9, 1.3):
        for rs in (40.0, 55.0):
            o = rollout(make_flank_assault(flank, rs), def_line=True, def_rand=def_rand, hit=hit)
            if bf is None or o[1] > bf[-1][1]: bf = (flank, rs, o)
    br = None
    for rwp in (36.0, 44.0):
        o = rollout(make_rear_oracle(rwp), def_line=True, def_rand=def_rand, hit=hit)
        if br is None or o[1] > br[-1][1]: br = (rwp, o)
    return fr, bf, br


if __name__ == "__main__":
    import sys as _sys
    globals()["RPATH"] = "/home/younes/arma3-marl/replica_open.npz"   # BANC ÉPURÉ : champ ouvert plat (traversée triviale, arc-flanc = seul mécanisme)
    print("=== CERTIF v7 : BANC ÉPURÉ (champ ouvert) — la manœuvre paie-t-elle sans le labyrinthe ? ===", flush=True)
    print("(force = max hommes vivants dans le rayon 25m / 18 ; took = %% escouades qui sécurisent)", flush=True)
    # 1) ATTEIGNABILITÉ : sans défense, l'escouade DOIT pouvoir prendre l'objectif (sinon la carte est encore cassée)
    ra = rollout(pol_straight_ns, def_line=True, def_rand=True, hit=0.0)
    print("--- ATTEIGNABILITÉ (frontal, hit=0) : took %.2f | force %.2f | surv %.2f  (attendu : took~1.0) ---" % (ra[0], ra[1], ra[2]), flush=True)
    # 2) CERTIF : flanc vs frontal vs arrière, banc randomisé, hit=0.11
    for lbl, rand in (("RANDOM", True),):
        fr, (fl, rs, fo), (rwp, ro) = run_all(0.11, rand)
        print("--- géométrie %s (hit=0.11) ---" % lbl, flush=True)
        print("  FRONTAL       : took %.2f | force %.2f | surv %.2f" % (fr[0], fr[1], fr[2]), flush=True)
        print("  FLANC (f=%.1f) : took %.2f | force %.2f | surv %.2f" % (fl, fo[0], fo[1], fo[2]), flush=True)
        print("  ARRIÈRE(Rwp=%.0f): took %.2f | force %.2f | surv %.2f" % (rwp, ro[0], ro[1], ro[2]), flush=True)
        ceil = max(fo[1], ro[1])
        cert = (ra[0] >= 0.85) and (ceil - fr[1] >= 0.15) and (ceil >= 0.35)
        print("  >>> atteignable=%s | manœuvre-vs-frontal (force) Δ%+.2f | %s" % (
            "OUI" if ra[0] >= 0.85 else "NON", ceil - fr[1], "*** BANC CERTIFIÉ ***" if cert else "non"), flush=True)
    print("CERT_DONE", flush=True)


def _old_main():
    import math as _m
    print("=== CERTIF v4 : le FLANC prend-il l'objectif à MOINDRE coût que l'assaut FRONTAL ? (ligne défensive) ===", flush=True)
    print("(métrique : prise = %% escouades qui sécurisent ; coût = pertes au moment de la prise)", flush=True)
    print("(CERTIFIÉ si : prise(flanc) - prise(frontal) >= +0.15  ET  prise(flanc) >= 0.30)", flush=True)
    arc = 55 * _m.pi / 180.0; spread = 20 * _m.pi / 180.0   # géométrie fixée (bon discriminant en v4)
    for hit in (0.14, 0.11, 0.09, 0.07):
        f_surv, f_took, f_cost = rollout(pol_straight_ns, def_arc=arc, def_line=True, def_spread=spread, hit=hit)   # FRONTAL
        best = None
        for flank in (0.9, 1.3):
            for rs in (40.0, 55.0):
                o = rollout(make_flank_assault(flank, rs), def_arc=arc, def_line=True, def_spread=spread, hit=hit)
                if best is None or o[1] > best[-1][1]: best = (flank, rs, o)
        fl, rs, (o_surv, o_took, o_cost) = best
        # CERTIFIÉ : le flanc gagne dans la bande discriminante (frontal 0.2-0.4, flanc >=0.55, écart net)
        cert = (o_took >= 0.55) and (o_took - f_took >= 0.20) and (0.15 <= f_took <= 0.45)
        print("hit=%.2f | FRONTAL prise %.2f (coût %.2f) || FLANC(f=%.1f,Rs=%.0f) prise %.2f (Δ%+.2f, coût %.2f, surv %.2f) || %s" % (
            hit, f_took, f_cost, fl, rs, o_took, o_took - f_took, o_cost, o_surv,
            "*** CERTIFIÉ ***" if cert else "non"), flush=True)
    print("CERT_DONE", flush=True)
