"""
BANC DE DEBIT -- le monde 3D tient-il le rythme du gymnase ?

On compare ce qui remplace quoi :
  - la reference : `los_clear` du champ de hauteur, tel qu'il tourne aujourd'hui
  - le candidat  : `vue_degagee` contre des boites orientees

A l'echelle reelle de l'entrainement : 4096 environnements x 3 agents.

Avant de chronometrer quoi que ce soit, on verifie que le candidat repond
JUSTE. Chronometrer un noyau faux ne mesure que la vitesse de l'erreur.
"""
import json
import sys
import time

import torch

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/p2")

import monde
import los_boites

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
N_ENV, N_AG = 4096, 3
RAYONS = N_ENV * N_AG


def chrono(fn, n=5, echauffe=2):
    for _ in range(echauffe):
        fn()
    if DEV.startswith("cuda"):
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    if DEV.startswith("cuda"):
        torch.cuda.synchronize()
    return (time.perf_counter() - t0) / n * 1e3        # ms par appel


# ------------------------------------------------------------ 0. justesse
def controle_justesse():
    b = json.load(open("batiment.json"))
    m = monde.charger_pour_gymnase("batiment.json")
    s = monde.points_de_sonde(b)
    noms = list(s["segments"].keys())
    A = [s["segments"][k][0] for k in noms]
    B = [s["segments"][k][1] for k in noms]
    r = los_boites.vue_degagee(m["boites"], A, B)
    obtenu = {k: bool(v) for k, v in zip(noms, r.cpu().numpy())}
    attendu = {                      # ce qu'Unreal a repondu, verbatim
        "debout_par_la_fenetre": True,
        "accroupi_sous_allege": False,
        "derriere_le_trumeau": False,
        "ctrl_pos_ouverture": True,
        "ctrl_pos_terrain": True,
    }
    juste = obtenu == attendu
    print("DEBIT justesse   : %s  %s" % ("OK" if juste else "FAUX", obtenu))
    return juste, m


# ------------------------------------------------------------ 1. reference
def reference_champ_hauteur():
    """Le cout d'aujourd'hui : K echantillons bilineaires le long du segment."""
    G, K, R = 48, 24, 256.0
    g = torch.Generator(device=DEV).manual_seed(0)
    hm = torch.rand(N_ENV, G, G, generator=g, device=DEV) * 20.0
    ax = (torch.rand(N_ENV, N_AG, generator=g, device=DEV) * 2 - 1) * R
    ay = (torch.rand(N_ENV, N_AG, generator=g, device=DEV) * 2 - 1) * R
    bx = (torch.rand(N_ENV, N_AG, generator=g, device=DEV) * 2 - 1) * R
    by = (torch.rand(N_ENV, N_AG, generator=g, device=DEV) * 2 - 1) * R
    ts = torch.linspace(0, 1, K, device=DEV)

    def pas():
        lx = ax[..., None] * (1 - ts) + bx[..., None] * ts
        ly = ay[..., None] * (1 - ts) + by[..., None] * ts
        gx = ((lx + R) / (2 * R) * (G - 1)).clamp(0, G - 1)
        gy = ((ly + R) / (2 * R) * (G - 1)).clamp(0, G - 1)
        x0, y0 = gx.long(), gy.long()
        f = hm.view(N_ENV, -1)
        terr = f.gather(1, (y0 * G + x0).reshape(N_ENV, -1)).reshape(N_ENV, N_AG, K)
        return (~(terr > 5.0).any(-1)).float()

    return chrono(pas)


# ------------------------------------------------------------ 2. candidat
def prepare_boites(boites, n_cible):
    """On replique le batiment jusqu'a n_cible boites, decalees dans le plan."""
    c, h, y = [], [], []
    i = 0
    while len(c) < n_cible:
        dx, dy = (i % 20) * 40.0, (i // 20) * 40.0
        for b in boites:
            if len(c) >= n_cible:
                break
            c.append((b["centre"][0] + dx, b["centre"][1] + dy, b["centre"][2]))
            h.append(b["demi"])
            y.append(b["yaw_rad"])
        i += 1
    f = dict(dtype=torch.float32, device=DEV)
    return torch.tensor(c, **f), torch.tensor(h, **f), torch.tensor(y, **f)


def candidat_boites(C, H, Y, chunk):
    """Rayon contre boite, par paquets de boites pour borner la memoire."""
    g = torch.Generator(device=DEV).manual_seed(1)
    R = 256.0
    A = (torch.rand(RAYONS, 3, generator=g, device=DEV) * 2 - 1) * R
    B = (torch.rand(RAYONS, 3, generator=g, device=DEV) * 2 - 1) * R
    A[:, 2] = 1.5
    B[:, 2] = 1.5
    d = B - A
    N = C.shape[0]

    def pas():
        bloque = torch.zeros(RAYONS, dtype=torch.bool, device=DEV)
        for i0 in range(0, N, chunk):
            c = C[i0:i0 + chunk]
            h = H[i0:i0 + chunk]
            yw = Y[i0:i0 + chunk]
            o = A[:, None, :] - c[None, :, :]
            cs, sn = torch.cos(yw), torch.sin(yw)
            ox = cs * o[..., 0] + sn * o[..., 1]
            oy = -sn * o[..., 0] + cs * o[..., 1]
            oz = o[..., 2]
            dx = cs * d[:, None, 0] + sn * d[:, None, 1]
            dy = -sn * d[:, None, 0] + cs * d[:, None, 1]
            dz = d[:, None, 2].expand_as(dx)
            tmin = torch.full_like(ox, -1e9)
            tmax = torch.full_like(ox, 1e9)
            for op, dp, hp in ((ox, dx, h[None, :, 0]),
                               (oy, dy, h[None, :, 1]),
                               (oz, dz, h[None, :, 2])):
                sur = torch.where(dp.abs() < 1e-6, torch.full_like(dp, 1e-6), dp)
                t1 = (-hp - op) / sur
                t2 = (hp - op) / sur
                lo = torch.minimum(t1, t2)
                hi = torch.maximum(t1, t2)
                par = dp.abs() < 1e-6
                dedans = op.abs() <= hp
                lo = torch.where(par, torch.where(dedans, tmin, -tmin), lo)
                hi = torch.where(par, torch.where(dedans, tmax, -tmax), hi)
                tmin = torch.maximum(tmin, lo)
                tmax = torch.minimum(tmax, hi)
            touche = (tmax >= torch.clamp(tmin, min=0.0)) & (tmin <= 1.0) & (tmax >= 0.0)
            bloque |= touche.any(1)
        return bloque

    return chrono(pas, n=3, echauffe=1)


def main():
    juste, m = controle_justesse()
    if not juste:
        print("DEBIT_VERDICT=TOMBE (le noyau repond faux, inutile de le chronometrer)")
        return

    print("DEBIT peripherique: %s" % DEV)
    if DEV.startswith("cuda"):
        print("DEBIT gpu        : %s" % torch.cuda.get_device_name(0))
    print("DEBIT echelle    : %d env x %d agents = %d rayons" % (N_ENV, N_AG, RAYONS))

    t_ref = reference_champ_hauteur()
    print("DEBIT reference  : champ de hauteur  %8.2f ms/pas" % t_ref)

    for n_boites in (185, 1000, 5000):
        C, H, Y = prepare_boites(m["boites"], n_boites)
        try:
            t = candidat_boites(C, H, Y, chunk=128)
            print("DEBIT boites %5d : %8.2f ms/pas   x%6.1f la reference   "
                  "%.1f Grayons-boites/s"
                  % (n_boites, t, t / t_ref, RAYONS * n_boites / (t * 1e-3) / 1e9))
        except RuntimeError as e:
            print("DEBIT boites %5d : ECHEC %s" % (n_boites, str(e)[:80]))
    print("DEBIT_VERDICT=MESURE")


main()
