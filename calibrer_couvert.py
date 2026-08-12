#!/usr/bin/env python3
"""calibrer_couvert — DEUX VERDICTS A LA FOIS, parce qu'un seul se triche.

Le premier balayage a montre qu on peut amener le contraste « vu / pas vu » de +infini vers
+75 % en versant du feu de zone. Mais on ne peut pas lire ce contraste seul : a 0,50 de zone il
ne reste que 3425 observations de « vus » sur 10 898, parce que TOUT LE MONDE MEURT. On aurait
accorde un verdict en detruisant l autre.

LES DEUX ANCRES, toutes deux certifiees sur Arma :
  · CONTRASTE : etre vu multiplie la mortalite par 1,75 (+75 %, 563 000 observations).
  · PRISE     : le balayage du 10/08 place le monde d Arma entre 65 et 79 % de prise,
                onze reglages, 268 accrochages. C est la bande ou l instrument a de la course.

On tient les deux en deplacant la REPARTITION de la letalite, pas sa quantite : le feu de zone
monte, le degat par impact vise descend. Total constant, allocation corrigee.

⚠️ CE QUI FERAIT ECHOUER — ecrit avant :
  · aucun couple n atteint les deux -> on le DIT, et on ne choisit pas le verdict qui arrange.
  · le couple retenu sort la prise de la bande -> refuse, meme si le contraste est parfait.
"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

EPISODES, PAS = 384, 60
CIBLE_C, BANDE = 75.0, (20.0, 80.0)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def appui(e, t, n_fixe=2):
    """⚠️ LA PREMIERE VERSION MARCHAIT SANS JAMAIS TIRER. Elle imposait donc au monde de
    rendre le taux de prise d Arma alors que ses attaquants n avaient AUCUN moyen d agir sur
    le feu qu ils recevaient — ni suppression, ni riposte. Conclure « il manque un mecanisme »
    depuis ce banc-la, c aurait ete accuser le monde d une infirmite de ma doctrine.
    Ici deux hommes sur quatre appuient des qu ils sont a portee."""
    act = cap(-e.apx, -e.apy)
    d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    return torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)


def mesurer(zone, degat, seed=7):
    cfg = dict(MONDE_ARMA); cfg["degat_par_impact"] = degat
    e = AssaultTerrain(num_envs=EPISODES, seed=seed, device="cuda:0", max_steps=PAS,
                       feu_de_zone=zone, **cfg)
    e.reset()
    n_vu = n_non = m_vu = m_non = 0
    viv = e._aalive().clone()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(PAS):
        _, _, done, info = e.step(appui(e, t), auto_reset=False)
        pris |= (info["took"] & ~fini)
        fini |= done.bool()
        neuf = e._aalive(); mort = viv & ~neuf
        vu = (e._vu_geo > 0.5) & viv; pasvu = (e._vu_geo <= 0.5) & viv
        n_vu += int(vu.sum()); m_vu += int((mort & vu).sum())
        n_non += int(pasvu.sum()); m_non += int((mort & pasvu).sum())
        viv = neuf
    prise = 100.0 * float(pris.float().mean())
    if n_vu < 200 or n_non < 200:
        return None, prise, n_vu, n_non
    pv, pn = m_vu / n_vu, m_non / n_non
    c = float("inf") if pn <= 1e-9 else 100.0 * (pv / pn - 1.0)
    return c, prise, n_vu, n_non


print("\n  CALIBRATION DU COUVERT — contraste ET prise, doctrine QUI APPUIE")
print("  " + "=" * 70)
print(f"    {'zone':>6}{'degat':>8}{'contraste':>13}{'prise':>9}{'  verdicts tenus'}")
bons = []
for zone in (0.0, 0.25, 0.40, 0.55, 0.70):
    for degat in (0.233, 0.16, 0.10, 0.06):
        c, pr, nv, nn = mesurer(zone, degat)
        if c is None:
            print(f"    {zone:>6.2f}{degat:>8.3f}{'non lisible':>13}{pr:>8.1f}%")
            continue
        okc = abs(c - CIBLE_C) <= 40.0
        okp = BANDE[0] <= pr <= BANDE[1]
        tenus = ("contraste " if okc else "") + ("prise" if okp else "")
        cs = "inf" if c == float("inf") else f"{c:.0f}%"
        print(f"    {zone:>6.2f}{degat:>8.3f}{cs:>13}{pr:>8.1f}%   {tenus}")
        if okc and okp:
            bons.append((abs(c - CIBLE_C), zone, degat, c, pr))
print("  " + "=" * 70)
if bons:
    _, z, dg, c, pr = sorted(bons)[0]
    print(f"    RETENU : feu_de_zone={z:.2f}  degat_par_impact={dg:.3f}")
    print(f"             contraste {c:.0f} % (Arma 75 %) · prise {pr:.1f} % (bande 20-80)")
else:
    print("    AUCUN COUPLE NE TIENT LES DEUX VERDICTS.")
    print("    On le dit, et on ne choisit pas celui qui arrange : il manque un mecanisme,")
    print("    pas un reglage.")
