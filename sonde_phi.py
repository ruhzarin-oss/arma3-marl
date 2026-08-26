#!/usr/bin/env python3
"""sonde_phi — L AMPLITUDE SE MESURE, ELLE NE SE CHOISIT PAS ⟨exigence de Fable⟩.

Le faconnage doit avoir, PAR PAS, une amplitude comparable au terme de progression du depot
(0,001 x metre gagne). On la mesure sur des trajectoires REELLES — la politique figee et les
deux doctrines — puis on en DEDUIT le poids. Un poids choisi a l oeil serait un parametre
herite d un instrument mort, la faute nommee le 20/08.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import phi, danger_position

DEV = "cuda:0"
pol = B.Politique(12).to(DEV)
pol.load_state_dict(torch.load("/home/younes/arma3-marl/pol_1200_g0.pt", map_location=DEV)); pol.eval()

print("=" * 78); print(" SONDE Φ — regler le poids sur MESURE"); print("=" * 78)

def mesure(nom, choix):
    e = B.monde(256, 11); o = e.reset()
    dpr = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); php = phi(e)
    prog, faco, dgs = [], [], []
    for t in range(B.PAS):
        a = choix(e, o, t)
        o, _, done, _ = e.step(a, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        prog.append(float((0.001 * (dpr - B.GAMMA_PHI * d)).abs().mean()))
        ph = phi(e)
        faco.append(float((B.GAMMA_PHI * ph - php).abs().mean()))
        dgs.append(float(-ph.mean()))
        dpr = d; php = ph
        if bool(done.all()): break
    mp = sum(prog) / len(prog); mf = sum(faco) / len(faco)
    print("  %-22s progression %.5f/pas | Φ brut %.5f/pas | danger moyen %.3f | POIDS -> %.3f"
          % (nom, mp, mf, sum(dgs) / len(dgs), mp / max(mf, 1e-9)))
    return mp / max(mf, 1e-9)

def figee(e, o, t):
    with torch.no_grad(): lo, _ = pol(o)
    return torch.distributions.Categorical(logits=lo).sample()

w = []
w.append(mesure("politique figee", figee))
w.append(mesure("doctrine frontal", lambda e, o, t: B.frontal(e, t)))
w.append(mesure("doctrine flanc", lambda e, o, t: B.flanc(e, t)))
W = sorted(w)[1]
print("\n  POIDS RETENU (mediane des trois) : W_PHI = %.3f" % W)
print("  -> a ce poids, le faconnage pese par pas AUTANT que la progression, ni plus ni moins.")
print("  Rappel : la forme est F = γ·Φ(s′) − Φ(s), donc sa somme telescope et ne peut pas")
print("           deplacer la politique optimale, quel que soit le tarif du danger.")
