#!/usr/bin/env python3
"""LA POLITIQUE BAT-ELLE UNE MARCHE DROITE, DANS SON PROPRE GYMNASE ?

Zero entrainement. Quatre bras joues par LE MEME `boucle.jouer`, donc notes exactement de
la meme facon (`pris |= neuf`, cumule) : trois manoeuvres FIXES et la politique entrainee.

⚠️ PREDICTION ECRITE AVANT DE LANCER : la politique bat la frontale d au moins 5 points.
Elle a ete entrainee ici, sur ce monde, contre cet adversaire — si elle ne bat pas une
marche droite bete sur son propre terrain, ce n est plus un ecart de transfert, c est un
echec d apprentissage, et le candidat A prend un sens beaucoup plus dur.

⚠️ La frontale est un TEMOIN SANS MODELE. Sans lui, « 50,7 % » n est qu une decoration :
on ne saurait pas contre quoi le lire. C est le cliquet du 19/08, applique ici d avance.
"""
import torch, sys, math
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

S = 200.0
GRAINES = B.GRAINES_TEST[:3]
pol = charger("cpu"); DEV = next(pol.parameters()).device

def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)

def bras(nom):
    etat = {}
    def choisir(o, t):
        apx = o[:, :, 0] * S; apy = o[:, :, 1] * S
        d = torch.sqrt(apx ** 2 + apy ** 2)
        if t == 0: etat["d0"] = d.clone()
        if nom == "politique":
            with torch.no_grad():
                a = pol(o.to(DEV))[0].argmax(-1).to(o.device)
            return a, None, None
        a = cap(-apx, -apy)
        if nom == "flanc":
            f = torch.zeros_like(a, dtype=torch.bool); f[:, :2] = True
            a = torch.where(f & (d < 110.0 * 0.9), torch.full_like(a, 9), a)
            if t < 14: a = torch.where(~f, cap(-apy, apx), a)
        elif nom == "arret":
            mi = d <= (etat["d0"] * 0.5)
            a = torch.where(mi, torch.full_like(a, 8), a)
            a = torch.where(mi & (d < 110.0 * 0.9), torch.full_like(a, 9), a)
        return a, None, None
    return choisir

print("\n  %-12s %12s %14s %16s" % ("bras", "prise", "metres gagnes", "metres TENUS"))
R = {}
for nom in ["frontale", "flanc", "arret", "politique"]:
    v = [B.jouer(B.monde(256, g), bras(nom))[0] for g in GRAINES]
    R[nom] = {k: sum(x[k] for x in v) / len(v) for k in v[0]}
    print("  %-12s %11.1f %% %13.1f m %15.1f m"
          % (nom, R[nom]["prise"], R[nom]["metres"], R[nom]["metres_tenus"]))

e = R["politique"]["prise"] - R["frontale"]["prise"]
print("\n  politique - frontale : %+.1f points   (prediction ecrite : > +5)" % e)
print("  prediction : %s" % ("TENUE" if e > 5 else "⛔ DEMENTIE"))
meilleur = max(R, key=lambda n: R[n]["prise"])
print("  meilleur bras : %s (%.1f %%)" % (meilleur, R[meilleur]["prise"]))
if meilleur != "politique":
    print("\n  ⛔ UNE MANOEUVRE FIXE BAT LE RESEAU ENTRAINE, SUR SON PROPRE TERRAIN.")
    print("     Ce n est plus un probleme de transfert : c est un echec d apprentissage.")
