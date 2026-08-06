#!/usr/bin/env python3
"""porte0.py — LE CERTIFICAT DE NAISSANCE DU BANC.

Criteres deposes AVANT execution : CRITERES_PORTE0.md. Recopies sans retouche :

  DESATURATION  arrivee de la DROITE < 95 %       (sinon le monde est gratuit)
  PORTE 0       expo du crochet <= 0,85 x droite  OU  arrivee +10 points
  TARIF         10,5 — derive, pas regle : un pic de risque de 1,0 doit couter l objectif
                entier (0,05 x 210 = 10,5). A 4,7 le risque etait paye 45 % de sa consequence.

INTERDICTION DEPOSEE : on ne pousse pas le tarif au-dela de 10,5 pour forcer la
discrimination. Si la porte n ouvre pas ici, le banc est disqualifie et l etage 1 demenage
sur Arma. Un banc qu on doit forcer a voir n est plus un instrument.
"""
import sys, math, torch
sys.argv = [sys.argv[0], '--champ', '--porte0']

src = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
coupe = src.index("if '--smoke' in sys.argv:")
g = {'__name__': '__porte0__'}
exec(compile(src[:coupe], 'agent_complet.py', 'exec'), g)
# on recupere derouler et les references, definis apres le smoke : on execute la suite en
# sautant le bloc smoke
suite = src[src.index("class Politique(nn.Module):"):src.index('print("\\n" + "="*78, flush=True)')]
exec(compile(suite, 'agent_complet.py', 'exec'), g)

torch = g['torch']
dev, I_TE = g['dev'], g['I_TE']
derouler, risque = g['derouler'], g['risque']

TARIF = 10.5          # DERIVE. Voir CRITERES_PORTE0.md, section 1.
g['DEPART_COURANT'] = 250.0


class Directe:
    """la droite : cap au but, allure et posture libres."""
    def __call__(s, p):
        return -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)


class Crochet:
    """le crochet : on achete l ecart AU TARIF DU LONG, puis on rentre en ligne droite.

    Doctrine mesuree le 27/07 : le crochet fait 74 % de son mouvement lateral au-dela de
    160 m, contre 21 % pour l agent appris. « Meme manoeuvre, meme quantite, mauvais moment. »

    Le COTE se choisit en comparant le risque a gauche et a droite a 100 m : c est un REGARD,
    pas un oracle sur la reponse — on ne lui souffle pas ou est le but, seulement ou ca brule.
    """
    def __init__(s, idx, force=1.2, bascule=90.0):
        s.idx, s.force, s.bascule = idx, force, bascule
        s.cote = None

    def __call__(s, p):
        d = p.norm(dim=-1, keepdim=True).clamp(min=1e-6)
        vers = -p / d
        perp = torch.stack([-vers[..., 1], vers[..., 0]], -1)
        if s.cote is None:                       # choisi UNE FOIS, au depart
            post = torch.zeros(len(p), dtype=torch.long, device=dev)
            rg = risque(p + perp * 100.0, post, s.idx)
            rd = risque(p - perp * 100.0, post, s.idx)
            s.cote = torch.where(rg < rd, 1.0, -1.0).unsqueeze(-1)
        w = ((d - s.bascule) / (250.0 - s.bascule)).clamp(0, 1)
        dr = vers + perp * s.cote * w * s.force
        return dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)


class Gelee:
    """l agent gele : course debout, cap direct. Le plancher gratuit."""
    def __call__(s, p):
        return -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)


print("\n" + "=" * 78)
print(f"  PORTE 0 — le banc sait-il separer un crochet d une ligne droite ?")
print(f"  tarif {TARIF} (derive : un pic de risque de 1,0 coute l objectif entier)")
print("  " + "-" * 76)

with torch.no_grad():
    class _Nul(torch.nn.Module):
        def forward(s, moi, ent, msk):
            B = moi.shape[0]
            z = torch.zeros(B, device=dev)
            return (torch.zeros(B, 2, device=dev), torch.zeros(B, 3, device=dev),
                    torch.zeros(B, 3, device=dev), z)
    nul = _Nul().to(dev)
    res = {}
    for nom, doct in (('DROITE', Directe()), ('CROCHET', Crochet(I_TE)), ('GELEE', Gelee())):
        r = derouler(nul, I_TE, TARIF, echantillonne=False, force_dir=doct,
                     gel=((2, 0) if nom == 'GELEE' else None))
        res[nom] = r
        print(f"     {nom:8s} arrivee {r['arrive'].mean():6.1%} · expo_cum {r['expo'].mean():6.2f} · PIC {r['pic'].mean():6.3f}"
              f" · chemin {r['chemin'].mean():6.1f} m")

print("  " + "-" * 76)
a_dr = res['DROITE']['arrive'].mean().item()
e_dr = res['DROITE']['pic'].mean().item()
a_cr = res['CROCHET']['arrive'].mean().item()
e_cr = res['CROCHET']['pic'].mean().item()

desat = a_dr < 0.95
print(f"\n  DESATURATION : arrivee de la droite {a_dr:.1%}  (exige < 95 %)"
      f"   -> {'OK' if desat else 'ECHEC — le monde reste gratuit'}")

voie_expo = e_cr <= 0.85 * e_dr
voie_arr = (a_cr - a_dr) >= 0.10
print(f"  PORTE 0 :")
print(f"     expo crochet {e_cr:.2f} contre 0,85 x droite = {0.85*e_dr:.2f}"
      f"   -> {'OK' if voie_expo else 'non'}")
print(f"     arrivee crochet {a_cr:.1%} contre droite +10 pts = {a_dr+0.10:.1%}"
      f"   -> {'OK' if voie_arr else 'non'}")

print("\n" + "=" * 78)
if not desat:
    print("  LE MONDE RESTE GRATUIT au tarif derive. Interdiction deposee : on ne pousse pas")
    print("  le tarif plus loin pour forcer la discrimination. LA SANDBOX EST DISQUALIFIEE")
    print("  pour cette question — l etage 1 se jugera sur Arma.")
elif voie_expo or voie_arr:
    print("  LE BANC A SON CERTIFICAT. Il separe deux doctrines dont l ordre est mesure.")
    print("  -> relance de l etage 1 a TROIS bras contemporains : champ, placebo, sans-champ.")
else:
    print("  LE BANC NE SEPARE PAS un crochet d une ligne droite. Il n a rien a dire sur un")
    print("  agent appris. DISQUALIFIE — l etage 1 demenage sur Arma.")
print("  " + "=" * 76)
