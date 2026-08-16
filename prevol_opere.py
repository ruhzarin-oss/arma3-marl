"""prevol_opere — le monde OPERE passe-t-il l examen ? Criteres dans DEPOT_CHIRURGIE_COUVERT.md.
Le G2 du prevol devient : la protection vient-elle de la RUPTURE DE VUE (directionnel) ?"""
import sys, math, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B, terrain_gpu as TG
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA, MONDE_OPERE
from porter_boucle import charger
ALIVE, LOS = 4, 7

def monde(n, seed, cfg):
    return AssaultTerrain(num_envs=n, seed=seed, device=B.DEV, max_steps=60, **cfg)

pol = charger(B.DEV)
def gele(o, t):
    with torch.no_grad(): lo, v = pol(o)
    return lo.argmax(-1), None, None

def examen(cfg, nom):
    print(f"\n─── {nom} ───")
    # letalite + protection PAR LA VUE
    e = monde(256, 101, cfg); e.reset()
    E, M = [], []
    morts = pas = 0
    for t in range(60):
        o0 = e._obs().reshape(-1, 12).cpu().numpy()
        e.step(gele(e._obs(), t)[0], auto_reset=False)
        o1 = e._obs().reshape(-1, 12).cpu().numpy()
        v = o0[:, ALIVE] > 0.5
        mort = (o0[:,ALIVE]>0.5) & (o1[:,ALIVE]<=0.5)
        E.append((o0[:, LOS] > 0.5)[v]); M.append(mort[v])
        morts += int(mort.sum()); pas += int(v.sum())
    E, M = np.concatenate(E), np.concatenate(M)
    let = morts/max(pas,1)
    pe = M[E].mean() if E.sum() else 0.0
    pn = M[~E].mean() if (~E).sum() else 0.0
    prot = pe/pn if pn > 0 else float("inf")
    print(f"  letalite                 {let:.4f} par homme-pas   (bande 0,01-0,30)")
    print(f"  P(mort | EXPOSE)         {pe:.4f}")
    print(f"  P(mort | rupture de vue) {pn:.4f}")
    print(f"  PROTECTION PAR LA VUE    x{prot:.2f}   (porte > 2)")
    # les 8 caps
    bons = 0
    for k in range(8):
        e2 = monde(8, 101, cfg); e2.reset()
        px, py = e2.apx.clone(), e2.apy.clone()
        e2.step(torch.full((e2.N, e2.A), k, dtype=torch.long, device=e2.dev), auto_reset=False)
        dx = (e2.apx-px).mean().item(); dy = (e2.apy-py).mean().item()
        n = math.hypot(dx, dy)
        if n > 1.0 and (dx/n*math.sin(k*math.pi/4) + dy/n*math.cos(k*math.pi/4)) > 0.7: bons += 1
    # prise de l ANCIENNE politique dans ce monde
    pr = [B.jouer(monde(256, g, cfg), gele)[0]["prise"] for g in B.GRAINES_TEST]
    p = float(np.mean(pr))
    print(f"  les 8 caps deplacent     {bons}/8")
    print(f"  prise (ancienne politique) {p:.1f} %   (bande 20-80)")
    return dict(let=let, prot=prot, caps=bons, prise=p)

ref = examen(MONDE_ARMA,  "MONDE DE REFERENCE (couvert scalaire)")
ope = examen(MONDE_OPERE, "MONDE OPERE (couvert directionnel)")

print("\n─── LE CONTROLE POSITIF DEPOSE ───")
print(f"  protection par la rupture de vue, monde opere : x{ope['prot']:.2f}   (porte > 2)")
print("  ⇒ " + ("✓ PASSE — le monde opere a des abris, ils sont DIRECTIONNELS"
                if ope['prot'] > 2 else "⛔ TOMBE — MONDE SANS ABRI, on ne reentraine pas dessus"))
print("\n─── LA PORTE : le monde opere reste-t-il jugeable ? ───")
ok = (0.01 <= ope['let'] <= 0.30) and ope['caps'] == 8 and 20 <= ope['prise'] <= 80
print(f"  letalite {ope['let']:.4f} · caps {ope['caps']}/8 · prise {ope['prise']:.1f} %")
print("  ⇒ " + ("✓ VERT — on peut reentrainer" if ok else "⛔ ROUGE — pas de reentrainement"))
print(f"\n  (pour memoire, le monde de reference : protection x{ref['prot']:.2f}, prise {ref['prise']:.1f} %)")
