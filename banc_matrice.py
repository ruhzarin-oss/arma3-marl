#!/usr/bin/env python3
"""banc_matrice.py — LE BANC-MATRICE. On ne simule rien : on relit le passe.

Criteres deposes AVANT ce code : CRITERES_BANC_MATRICE.md (commit d547c3b). Recopies sans
retouche :

  PORTE 0   deux paires dont l ORDRE EST CONNU :
              dans le cone / hors du cone   -> dedans est plus mortel (angle mort 18/18 vs 0/26)
              vu / non vu                   -> vu tue ~2x plus
            TAILLE DE LA PORTE, declaree avant : avec >= 20 000 instants par paquet ce banc
            voit environ 1 point d ecart. Il exige donc >= 3 POINTS, dans le sens connu.
  AIGUILLE  on ne juge que dans les strates ou la mortalite tombe entre 20 % et 80 %.
  C1 NEGATIF  le predicteur lisse DOIT ECHOUER la porte du contraste de falaise : l ecart
            qu il attribue a la paire du cone doit etre nettement plus faible que celui que
            le corpus mesure. S il la passe, la porte est DECORATIVE et rien ne se lit.
  C2 NUL    sur etiquettes brassees, tout retombe a l indifference.
  STRATIFIER  toute comparaison a SUPPRESSION SUBIE CONSTANTE — 92 % de l ecart entre
            predicteur enrichi et transferable vient de cette quasi-tautologie.

CE BANC NE DIRA JAMAIS si agir sur la lecture PAIE : les instants sont figes, l agent ne peut
pas changer la suite. Cette question reste a Arma, une seule campagne, a la fin.
"""
import sys, math, numpy as np

DEMI_CONE = 35.0          # MESURE, banc du 03/08 : bascule entre 30 et 40 degres
N_MIN = 20000             # taille de paquet sous laquelle la porte ne voit rien
ECART_MIN = 0.03          # 3 points — la taille de la porte, declaree avant

# ---------------------------------------------------------------- le corpus
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__matrice__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y = g['SOI'], g['ENN'], g['MASQ'], g['Y']

d_e = ENN[..., 3] * 400.0
a_lui = ENN[..., 4] * 180.0
vu_e = ENN[..., 1]
vivant = MASQ > 0.5

dans_cone = ((a_lui < DEMI_CONE) & vivant).any(axis=1)
est_vu = ((vu_e > 0.5) & vivant).any(axis=1)
d_min = np.where(vivant, d_e, 1e9).min(axis=1)
supp = SOI[:, 5]                       # suppression SUBIE — la quasi-tautologie a neutraliser

print(f"\n  {len(Y)} instants · mortalite globale {Y.mean():.2%}")
print(f"  dans le cone {dans_cone.mean():.1%} · vu {est_vu.mean():.1%}"
      f" · supprimes {(supp > 0.01).mean():.1%}")


def ecart_stratifie(masque, y=None, poids=None):
    """difference de mortalite entre le paquet et son complement, A SUPPRESSION CONSTANTE.

    On decoupe la suppression subie en trois tranches, on mesure l ecart dans chacune, et on
    rend la moyenne ponderee par l effectif. Sans ca, on mesurerait surtout « on meurt quand
    on est deja arrose »."""
    y = Y if y is None else y
    tr = [(supp <= 0.01), (supp > 0.01) & (supp <= 0.3), (supp > 0.3)]
    num = den = 0.0
    n_a = n_b = 0
    for m in tr:
        a, b = masque & m, (~masque) & m
        if a.sum() < 500 or b.sum() < 500:
            continue
        w = a.sum() + b.sum()
        num += (y[a].mean() - y[b].mean()) * w
        den += w
        n_a += int(a.sum()); n_b += int(b.sum())
    return (num / den if den else float('nan')), n_a, n_b


print("\n" + "=" * 78)
print("  PORTE 0 — deux paires dont l ORDRE EST CONNU  (taille declaree : >= 3 points)")
print("  " + "-" * 76)
ok0 = True
for nom, masque, sens in (("dans le cone / hors", dans_cone, "dedans plus mortel"),
                          ("vu / non vu       ", est_vu, "vu plus mortel")):
    e, na, nb = ecart_stratifie(masque)
    assez = na >= N_MIN and nb >= N_MIN
    passe = assez and e >= ECART_MIN
    ok0 &= passe
    print(f"     {nom}  ecart {e:+.1%}  ({na} contre {nb})"
          f"   -> {'OK' if passe else ('effectif insuffisant' if not assez else 'ECHEC')}")
    print(f"     {'':18s}  ⟨ordre connu : {sens}⟩")

print("\n" + "=" * 78)
print("  AIGUILLE — les strates ou la mortalite vit entre 20 % et 80 %")
print("  " + "-" * 76)
BANDES = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250), (250, 400)]
utiles = []
for a, b in BANDES:
    m = (d_min >= a) & (d_min < b)
    if m.sum() < 500:
        continue
    mort = Y[m].mean()
    dedans = 0.20 <= mort <= 0.80
    utiles.append((a, b, mort, dedans))
    print(f"     {a:3d}-{b:<3d} m   n={int(m.sum()):6d}   mortalite {mort:6.2%}"
          f"   {'DANS LA BANDE' if dedans else 'hors bande'}")
n_utiles = sum(1 for *_, d in utiles if d)
print(f"     -> {n_utiles} strate(s) dans la bande 20-80 %")

print("\n" + "=" * 78)
print("  C1 — CONTRÔLE NÉGATIF : le prédicteur lissé DOIT ÉCHOUER le contraste de falaise")
print("  " + "-" * 76)
import torch
src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__matrice2__'}
exec(compile(src2[:src2.index(chr(39)+chr(39)+chr(39)+chr(10))] if False else src2[:src2.index("def percevoir")], 'agent_complet.py', 'exec'), h)
RISQUE, dev = h['RISQUE'], h['dev']
with torch.no_grad():
    pc = torch.tensor(SOI[:, [4]], device=dev)
    ent = torch.tensor(ENN[:, :, 3:6], device=dev)
    msk = torch.tensor(MASQ, device=dev)
    pred = []
    for i in range(0, len(pc), 65536):
        pred.append(torch.sigmoid(RISQUE(pc[i:i+65536], ent[i:i+65536], msk[i:i+65536])).cpu())
    pred = torch.cat(pred).numpy()

e_corpus, _, _ = ecart_stratifie(dans_cone)
e_pred, _, _ = ecart_stratifie(dans_cone, y=pred)
rap = e_pred / e_corpus if e_corpus else float('nan')
print(f"     le CORPUS mesure sur la paire du cône      {e_corpus:+.1%}")
print(f"     le PRÉDICTEUR attribue à la même paire     {e_pred:+.1%}")
print(f"     il en restitue {rap:.0%} — {'il LISSE, comme mesuré ce soir' if rap < 0.5 else 'IL NE LISSE PAS'}")
c1 = rap < 0.5
print(f"     -> C1 {'OK — la porte mesure bien le contraste' if c1 else 'ÉCHEC — porte DÉCORATIVE'}")

print("\n" + "=" * 78)
print("  C2 — CONTRÔLE NUL : étiquettes brassées")
print("  " + "-" * 76)
rng = np.random.default_rng(0)
Ybr = Y.copy(); rng.shuffle(Ybr)
e_nul, _, _ = ecart_stratifie(dans_cone, y=Ybr)
c2 = abs(e_nul) < ECART_MIN
print(f"     écart sur étiquettes brassées {e_nul:+.2%}   (exige |écart| < 3 points)"
      f"   -> {'OK' if c2 else 'ECHEC'}")

print("\n" + "=" * 78)
if ok0 and c1 and c2 and n_utiles > 0:
    print("  LE BANC-MATRICE A SON CERTIFICAT. Il sépare deux paires dont l'ordre est connu,")
    print("  il possède des strates où l'aiguille bouge, et sa porte du contraste n'est pas")
    print("  décorative — le prédicteur lissé y échoue, comme mesuré.")
    print("  -> il peut juger les YEUX d'un agent. Jamais ses ACTES : ça reste à Arma.")
else:
    manque = []
    if not ok0: manque.append("PORTE 0")
    if not c1: manque.append("C1 (porte décorative)")
    if not c2: manque.append("C2 (contrôle nul)")
    if n_utiles == 0: manque.append("aucune strate dans la bande")
    print(f"  LE BANC N'A PAS SON CERTIFICAT — {', '.join(manque)}.")
    print("  Rien ne se lit sur un agent tant que ce n'est pas réparé.")
print("  " + "=" * 76)
