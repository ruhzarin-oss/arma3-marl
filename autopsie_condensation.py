#!/usr/bin/env python3
"""AUTOPSIE — trois mesures en minutes, sur les artefacts existants, sans entrainer.
Prescrites par Fable, 24/08. Chacune separe deux recits que mes chiffres confondent.

  A. ENTROPIE PAR ETAT — « condensation binaire » contre « continuum de nettete ».
     Prediction du continuum : 13/08 et graine 0 basses, graine 1 haute.
  B. BALAYAGE EN TEMPERATURE — une falaise a petit tau dit « quelques etats critiques »,
     une degradation continue dit « etalement partout ».
  C. LE PORTEFEUILLE — la prise est un MAX sur quatre hommes. Echantillonner disperse
     l equipe (quatre chemins decorreles, il suffit qu un passe) ; l argmax rejoue quatre
     fois le meme champ de vecteurs, les hommes se groupent et leurs sorts se correlent.
     Si l argmax GROUPE, une part du 42 -> 3 % n est pas un mauvais mode mais une PERTE DE
     DIVERSITE — et l entropie n y repondrait pas.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

ART = [("graine 1 (TOMBE)", "/home/younes/arma3-marl/pol_1200_g1_rejeu_TOMBE.pt"),
       ("graine 0 (PASSE)", "/home/younes/arma3-marl/pol_1200_g0.pt"),
       ("artefact 13/08",   "/home/younes/arma3-marl/boucle_pol.pt")]
G = B.GRAINES_TEST[:3]

def joue(pol, dev, tau, mesurer=False):
    """tau = 0 -> argmax. Rend (prise, entropie moyenne, ecart top1-top2, dispersion)."""
    ent = []; gap = []; disp = []; pr = []
    for g in G:
        e = B.monde(256, g)
        def choisir(o, t):
            with torch.no_grad():
                lo, _ = pol(o.to(dev))
            p = torch.softmax(lo, -1)
            if mesurer:
                ent.append(float(-(p * torch.log(p + 1e-9)).sum(-1).mean()))
                s = p.sort(-1, descending=True).values
                gap.append(float((s[..., 0] - s[..., 1]).mean()))
                # dispersion de l equipe : ecart-type des positions entre les 4 hommes
                disp.append(float(torch.sqrt(e.apx.var(1) + e.apy.var(1)).mean()))
            a = lo.argmax(-1) if tau == 0 else torch.distributions.Categorical(logits=lo / tau).sample()
            return a.to(o.device), None, None
        pr.append(B.jouer(e, choisir)[0]["prise"])
    m = lambda v: sum(v) / len(v) if v else float("nan")
    return m(pr), m(ent), m(gap), m(disp)

print("\n  ══ A. ENTROPIE PAR ETAT ET NETTETE DU MODE (en argmax) ══\n")
print("  %-20s %12s %14s %16s" % ("artefact", "prise", "entropie", "ecart top1-top2"))
P = {}
for nom, pt in ART:
    pol = charger("cpu", pt); dev = next(pol.parameters()).device
    P[nom] = (pol, dev)
    pr, ent, gap, disp = joue(pol, dev, 0, mesurer=True)
    print("  %-20s %10.1f %% %13.3f %15.3f" % (nom, pr, ent, gap))
print("\n  (entropie maximale possible pour 10 actions : %.3f)" % float(torch.log(torch.tensor(10.0))))

print("\n  ══ B. BALAYAGE EN TEMPERATURE ══\n")
TAUS = [0, 0.1, 0.25, 0.5, 1.0]
print("  %-20s %s" % ("artefact", "".join("%10s" % ("tau=%.2f" % t if t else "argmax") for t in TAUS)))
for nom, _ in ART:
    pol, dev = P[nom]
    l = "  %-20s" % nom
    for t in TAUS:
        l += "%9.1f %%" % joue(pol, dev, t)[0]
    print(l)

print("\n  ══ C. LE PORTEFEUILLE — l argmax groupe-t-il l equipe ? ══\n")
print("  %-20s %18s %18s" % ("artefact", "dispersion argmax", "dispersion tau=1"))
for nom, _ in ART:
    pol, dev = P[nom]
    _, _, _, da = joue(pol, dev, 0, mesurer=True)
    _, _, _, ds = joue(pol, dev, 1.0, mesurer=True)
    print("  %-20s %16.1f m %16.1f m" % (nom, da, ds))
print("\n  ⚠️ Si l argmax groupe (dispersion plus faible) SURTOUT chez la graine 1,")
print("     une part de son effondrement est une perte de diversite d equipe.")
