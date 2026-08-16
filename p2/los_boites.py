"""
LOS contre des BOITES ORIENTEES -- ce qui manque au gymnase.

Le gymnase actuel voit le monde en 2,5D : `los_clear(hm, ...)` echantillonne
UNE hauteur par case. Un champ de hauteur ne sait pas dire "plein de 0,90 a
2,10 m et vide en dessous". Donc ni fenetre, ni etage, ni breche.

Ici : intersection rayon / boite orientee (test des dalles), vectorisee.
Meme forme de calcul que l'existant, meme place dans la boucle, mais un
monde qui a une TROISIEME dimension.

Convention identique a Unreal : "degage" = rien touche entre A et B.
"""
try:
    import torch
    XP, TORCH = torch, True
except ImportError:                     # repli sans GPU, pour pouvoir tester
    import numpy as XP
    TORCH = False


def _empile(boites, dev=None):
    c = [b["centre"] for b in boites]
    h = [b["demi"] for b in boites]
    y = [b["yaw_rad"] for b in boites]
    if TORCH:
        f = dict(dtype=torch.float32, device=dev)
        return (torch.tensor(c, **f), torch.tensor(h, **f), torch.tensor(y, **f))
    return (XP.array(c, dtype=XP.float32),
            XP.array(h, dtype=XP.float32),
            XP.array(y, dtype=XP.float32))


def vue_degagee(boites, A, B, dev=None, eps=1e-6):
    """A(M,3) -> B(M,3) contre N boites. Renvoie (M,) booleen : True = ca passe.

    Test des dalles dans le repere propre de chaque boite. Un segment est
    bloque si un intervalle d'intersection non vide tombe dans [0,1].
    """
    c, h, yaw = _empile(boites, dev)
    if TORCH:
        f = dict(dtype=torch.float32, device=c.device)
        A = torch.as_tensor(A, **f).reshape(-1, 3)
        B = torch.as_tensor(B, **f).reshape(-1, 3)
    else:
        A = XP.asarray(A, dtype=XP.float32).reshape(-1, 3)
        B = XP.asarray(B, dtype=XP.float32).reshape(-1, 3)

    d = B - A                                        # (M,3)
    o = A[:, None, :] - c[None, :, :]                # (M,N,3) origine relative
    dd = d[:, None, :].repeat(1, c.shape[0], 1) if TORCH \
        else XP.repeat(d[:, None, :], c.shape[0], axis=1)

    cs, sn = XP.cos(yaw), XP.sin(yaw)                # (N,)
    def au_repere(v):
        x = cs[None, :] * v[..., 0] + sn[None, :] * v[..., 1]
        y = -sn[None, :] * v[..., 0] + cs[None, :] * v[..., 1]
        return x, y, v[..., 2]

    ox, oy, oz = au_repere(o)
    dx, dy, dz = au_repere(dd)

    def dalle(op, dp, hp):
        """Intervalle [t0,t1] ou le rayon est dans la dalle de demi-epaisseur hp."""
        sur = XP.where(XP.abs(dp) < eps, XP.full_like(dp, eps), dp)
        t1 = (-hp - op) / sur
        t2 = (hp - op) / sur
        lo = XP.minimum(t1, t2)
        hi = XP.maximum(t1, t2)
        # rayon parallele a la dalle : dedans pour toujours, ou jamais
        dedans = XP.abs(op) <= hp
        grand = XP.full_like(lo, 1e9)
        lo = XP.where(XP.abs(dp) < eps, XP.where(dedans, -grand, grand), lo)
        hi = XP.where(XP.abs(dp) < eps, XP.where(dedans, grand, -grand), hi)
        return lo, hi

    hx, hy, hz = h[None, :, 0], h[None, :, 1], h[None, :, 2]
    l1, u1 = dalle(ox, dx, hx)
    l2, u2 = dalle(oy, dy, hy)
    l3, u3 = dalle(oz, dz, hz)

    tmin = XP.maximum(XP.maximum(l1, l2), l3)
    tmax = XP.minimum(XP.minimum(u1, u2), u3)
    zero = XP.zeros_like(tmin)
    un = XP.ones_like(tmin)
    touche = (tmax >= XP.maximum(tmin, zero)) & (tmin <= un) & (tmax >= zero)
    bloque = touche.any(1) if TORCH else touche.any(axis=1)
    return ~bloque
