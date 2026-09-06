#!/usr/bin/env python3
"""levier_gym — LE PLACEUR A-T-IL UN LEVIER ? 12 contre 12, au gymnase.

C est la PORTE avant les trois etages. Dans Arma j ai mesure que le feu EFFACE la forme
commandee (etendue 1,12 pour un plancher de 1,55, p = 0,204). Si c est vrai ici aussi, un
etage qui positionne n a rien a gagner et rien ne s apprendra.

AUCUNE POLITIQUE N INTERVIENT. Le mouvement est entierement determine par la geometrie, le
feu part quand on est en place. Zero variance d apprentissage : la question est posee pure.

DEUX CONDITIONS — et leur ecart decide de l ARCHITECTURE, pas seulement du verdict :
  DEPART · la geometrie n existe qu au spawn, puis tout le monde avance frontalement.
  TENUE  · la geometrie est TENUE : chaque homme rejoint sa place, l ancre avance vers
           l objectif a vitesse d homme.
  Si DEPART ne dit rien et TENUE beaucoup, alors le placeur doit agir EN CONTINU — et c est
  le monde qui l aura dit, pas moi.

LES GEOMETRIES : les 15 du catalogue + 15 TIREES AU SORT. Les tirees au sort ne sont pas un
decor : sans elles on ne saurait pas si le catalogue vaut mieux que n importe quoi.

SEUIL DIMENSIONNE : plancher par PERMUTATION des etiquettes de geometrie (2000 tirages).
"""
import sys, math, json
import torch
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
import formations as F

DEV = "cuda:0"
A, D, N, PAS = 12, 12, 256, 60
GRAINES = [11, 12, 13, 14, 15, 16]
SP, RR = 7.0, 24.0
CATALOGUE = sorted(F.FORMATIONS)

def cap8(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)

def geom_catalogue(nom):
    t = F.slots(nom, A, SP, RR)[:, :2]                     # (A,2) reperes locaux, avant = +y
    return t.to(DEV)

def geom_hasard(k):
    g = torch.Generator(device="cpu").manual_seed(1000 + k)
    # meme ENVERGURE que le catalogue : sinon on comparerait des tailles, pas des formes.
    r = torch.rand(A, 2, generator=g) * 2 - 1
    ech = float(np.mean([float(geom_catalogue(n).abs().max()) for n in CATALOGUE]))
    return (r * ech).to(DEV)

def poser(e, off, cap_rad):
    """Ecrase les positions : meme ANCRE (le barycentre du spawn), meme CAP, autre FORME."""
    ax = e.apx.mean(1, keepdim=True); ay = e.apy.mean(1, keepdim=True)
    c, s = math.cos(cap_rad), math.sin(cap_rad)
    ox, oy = off[:, 0].unsqueeze(0), off[:, 1].unsqueeze(0)
    e.apx = (ax + ox * c + oy * s).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
    e.apy = (ay - ox * s + oy * c).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
    return ax, ay

def episode(seed, off, tenue):
    e = AssaultTerrain(num_envs=N, A=A, D=D, seed=seed, device=DEV, max_steps=PAS, **MONDE_ARMA)
    e.reset()
    ax, ay = poser(e, off, 0.0)                            # cap : vers l objectif, en (0,0)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dprec = d0.clone(); pris = torch.zeros(N, dtype=torch.bool, device=DEV)
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    anx, any_ = ax.clone(), ay.clone()
    for t in range(PAS):
        if tenue:
            # L ANCRE AVANCE vers l objectif a vitesse d homme. La forme la suit.
            da = torch.sqrt(anx ** 2 + any_ ** 2).clamp(min=1e-3)
            anx = anx - (anx / da) * e.move; any_ = any_ - (any_ / da) * e.move
            sx = anx + off[:, 0].unsqueeze(0); sy = any_ + off[:, 1].unsqueeze(0)
            dx, dy = sx - e.apx, sy - e.apy
            loin = torch.sqrt(dx ** 2 + dy ** 2) > e.move
            act = torch.where(loin, cap8(dx, dy), torch.full_like(e.posture, 9))
        else:
            act = cap8(-e.apx, -e.apy)                     # DEPART : tout le monde avance de front
        _, _, done, info = e.step(act, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        pris |= (info["took"] & ~fini); dprec = torch.where(fini, dprec, d)
        fini |= done.bool()
        if bool(fini.all()): break
    return (100.0 * float(pris.float().mean()), float((d0 - dprec).mean()),
            float(e._aalive().float().sum(1).mean()))

def permutation(par_geo, k=2000):
    lab, val = [], []
    for g, v in par_geo.items():
        for x in v: lab.append(g); val.append(x)
    lab, val = np.array(lab), np.array(val)
    obs = float(np.ptp([np.mean(val[lab == g]) for g in par_geo]))
    rng = np.random.default_rng(0); nul = []
    for _ in range(k):
        p = rng.permutation(lab)
        nul.append(np.ptp([np.mean(val[p == g]) for g in par_geo]))
    nul = np.array(nul)
    return obs, float(np.percentile(nul, 95)), float((nul >= obs).mean())

if __name__ == "__main__":
    print("=" * 92); print(" LE LEVIER DU PLACEUR — 12 contre 12, aucune politique"); print("=" * 92, flush=True)
    GEOS = [(n, geom_catalogue(n)) for n in CATALOGUE] + [("hasard%02d" % k, geom_hasard(k)) for k in range(15)]
    print("  %d geometries (%d du catalogue + 15 tirees) x %d graines x %d mondes x 2 conditions"
          % (len(GEOS), len(CATALOGUE), len(GRAINES), N), flush=True)
    R = {}
    for cond, tenue in (("DEPART", False), ("TENUE", True)):
        print("\n─── %s ───" % cond, flush=True)
        R[cond] = {}
        for nom, off in GEOS:
            pr, me, viv = [], [], []
            for g in GRAINES:
                p, m, v = episode(g, off, tenue); pr.append(p); me.append(m); viv.append(v)
            R[cond][nom] = {"prise": pr, "metres": me, "vivants": viv}
            print("  %-14s prise %5.1f %%   metres tenus %6.1f   vivants %4.1f/%d"
                  % (nom, np.mean(pr), np.mean(me), np.mean(viv), A), flush=True)
        json.dump(R, open('/mnt/data/levier_gym.json', 'w'), indent=1)

    print("\n" + "=" * 92)
    V = {}
    for cond in R:
        print("\n  %s" % cond)
        for k in ("prise", "metres"):
            obs, p95, pv = permutation({g: R[cond][g][k] for g in R[cond]})
            V[(cond, k)] = (obs, p95, pv)
            best = max(R[cond], key=lambda g: np.mean(R[cond][g][k]))
            worst = min(R[cond], key=lambda g: np.mean(R[cond][g][k]))
            print("     %-8s etendue %7.2f  | plancher95 %7.2f | p = %.3f   %s"
                  % (k, obs, p95, pv, "✅ SEPARE" if obs > p95 else "⛔ indistinguable"))
            print("              meilleure %-14s %7.2f   pire %-14s %7.2f"
                  % (best, np.mean(R[cond][best][k]), worst, np.mean(R[cond][worst][k])))
            cat = [np.mean(R[cond][g][k]) for g in CATALOGUE]
            haz = [np.mean(R[cond][g][k]) for g in R[cond] if g.startswith("hasard")]
            print("              catalogue %7.2f   vs   tirees au sort %7.2f   ecart %+.2f"
                  % (np.mean(cat), np.mean(haz), np.mean(cat) - np.mean(haz)))
    print("\n" + "─" * 92)
    dep = V[("DEPART", "prise")]; ten = V[("TENUE", "prise")]
    if ten[0] > ten[1]:
        print("  ✅ LE PLACEUR A UN LEVIER : tenir une geometrie change l issue (p = %.3f)." % ten[2])
        print("     Un etage qui positionne a donc quelque chose a gagner.")
        if not (dep[0] > dep[1]):
            print("  ⭐ ET LE MONDE DIT L ARCHITECTURE : placer AU DEPART ne suffit pas (p = %.3f)." % dep[2])
            print("     Le placeur devra agir EN CONTINU, pas une fois au spawn.")
    else:
        print("  ⛔ AUCUN LEVIER : la geometrie ne change pas l issue, meme TENUE (p = %.3f)." % ten[2])
        print("     Un etage qui positionne n aurait rien a apprendre. Les trois etages ne se")
        print("     montent pas — pas avant d avoir trouve ce qui, lui, change l issue.")
    json.dump({"mesures": R, "verdict": {str(k): v for k, v in V.items()}},
              open('/mnt/data/levier_gym.json', 'w'), indent=1)
