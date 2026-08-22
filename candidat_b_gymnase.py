#!/usr/bin/env python3
"""CANDIDAT B, COTE GYMNASE — trois manoeuvres FIXES, zero entrainement.

Pre-inscription 82101f9 + AMENDEMENT_CANDIDAT_B.md (87e06cf).
Les MEMES trois manoeuvres seront jouees dans Arma. Vocabulaire commun : 0-7 caps,
8 TENIR, 9 APPUYER — c est celui de la couture (`acts_to_sqf`), pas un dialecte d ici.

Observables. ⚠️ Deux sont des CONTROLES DE CALIBRATION, pas des preuves pour B1 :
  [calibration] distance du premier tir   — cote gymnase, c est la courbe ajustee sur Arma
  [calibration] coups par pas             — cote gymnase, c est la constante tir_par_pas
  [B1] fraction du temps ou l attaquant est touche  — emergent : depend de l exposition
  [B1] pertes attaquantes a la fin                  — emergent : l issue
"""
import torch, sys, math, json
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B

S = 200.0
GRAINES = B.GRAINES_TEST[:3]

def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)

def manoeuvre(nom, portee):
    """Rend une fonction (apx, apy, t, d0) -> actions. IDENTIQUE a ce qui partira dans Arma."""
    def f(apx, apy, t, d0):
        d = torch.sqrt(apx ** 2 + apy ** 2)
        a = cap(-apx, -apy)                                   # tout le monde cap vers l objectif
        if nom == "frontale":
            return a
        if nom == "flanc":
            # les deux premiers appuient sous 0,9 x portee ; les autres crochetent 14 pas
            f2 = torch.zeros_like(a, dtype=torch.bool); f2[:, :2] = True
            a = torch.where(f2 & (d < portee * 0.9), torch.full_like(a, 9), a)
            if t < 14:
                a = torch.where(~f2, cap(-apy, apx), a)
            return a
        if nom == "arret":
            # on avance jusqu a la MOITIE de la distance de depart, puis on tient ;
            # on appuie si l objectif est a portee utile
            mi = d <= (d0 * 0.5)
            a = torch.where(mi, torch.full_like(a, 8), a)
            a = torch.where(mi & (d < portee * 0.9), torch.full_like(a, 9), a)
            return a
        raise ValueError(nom)
    return f

def jouer(nom, graine):
    e = B.monde(256, graine)
    o = e.reset()
    portee = e.fire_range
    f = manoeuvre(nom, portee)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    admg_prec = e.admg.clone()
    touche = 0.0; vivant_pas = 0.0
    prem_d = []          # distance au premier degat recu, par environnement
    vu_prem = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(60):
        viv = e._aalive()
        a = f(e.apx, e.apy, t, d0)
        o, _, done, _ = e.step(a, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        neuf = (e.admg - admg_prec) > 1e-6
        admg_prec = e.admg.clone()
        m = viv & ~fini.unsqueeze(1)
        touche += float((neuf & m).sum()); vivant_pas += float(m.sum())
        # premier degat recu dans cet environnement : on note la distance MOYENNE a ce pas
        pd = neuf.any(1) & ~vu_prem & ~fini
        if bool(pd.any()):
            prem_d += d[pd].mean(1).tolist(); vu_prem |= pd
        fini |= done.bool()
        if bool(fini.all()):
            break
    pertes = float((~e._aalive()).float().sum(1).mean())
    return dict(touche=100.0 * touche / max(vivant_pas, 1.0),
                pertes=pertes,
                d_premier_tir=(sum(prem_d) / len(prem_d)) if prem_d else float("nan"),
                coups_par_pas=e.tir_par_pas)

print("\n  GYMNASE — trois manoeuvres, 3 graines x 256 environnements\n")
print("  %-10s %14s %12s %16s %14s" % ("manoeuvre", "% temps touche", "pertes", "d 1er tir (m)", "coups/pas"))
res = {}
for nom in ["frontale", "flanc", "arret"]:
    v = [jouer(nom, g) for g in GRAINES]
    r = {k: sum(x[k] for x in v) / len(v) for k in v[0]}
    res[nom] = r
    print("  %-10s %13.1f %% %12.2f %16.1f %14.2f"
          % (nom, r["touche"], r["pertes"], r["d_premier_tir"], r["coups_par_pas"]))
ordre_t = sorted(res, key=lambda n: res[n]["touche"])
ordre_p = sorted(res, key=lambda n: res[n]["pertes"])
print("\n  ordre par %% temps touche (du moins au plus expose) : %s" % " < ".join(ordre_t))
print("  ordre par pertes          (de la moins chere a la plus chere) : %s" % " < ".join(ordre_p))
json.dump({"res": res, "ordre_touche": ordre_t, "ordre_pertes": ordre_p},
          open("/mnt/data/candidat_b_gymnase.json", "w"), indent=1)
print("\n  ecrit : /mnt/data/candidat_b_gymnase.json")
