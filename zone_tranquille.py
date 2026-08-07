#!/usr/bin/env python3
"""zone_tranquille.py — DE QUOI EST FAITE LA ZONE TRANQUILLE, ET LA SANDBOX PEUT-ELLE L EXPRIMER ?

⟨Fable, regle 9 deposee ce soir : « avant de juger un comportement, verifier que le monde
 laisse varier la grandeur dont ce comportement fait commerce, sur la plage ou le corpus la
 fait varier. »⟩

LE FAIT : sur le corpus le score du predicteur descend a 0,086. Dans la sandbox il ne descend
JAMAIS sous 0,406. Le monde de la sandbox ne contient aucune situation que le predicteur juge
tranquille — donc aucune prudence ne peut y etre recompensee.

LE TEST DISCRIMINANT, avant toute reparation :
  1. on prend les lignes du corpus sous 0,20 — la zone tranquille — et on lit SUR PIECES ce
     qui les fabrique : distance, nombre d ennemis, angle, suppression ;
  2. on regarde si la sandbox peut EXPRIMER ces etats.

  -> si la zone tranquille est faite de DISTANCE et de PEU D ENNEMIS, la sandbox peut les
     exprimer, et le probleme est ailleurs (une entree du predicteur) ;
  -> si elle est faite de quelque chose que la sandbox n a pas — pas d ennemi du tout,
     angles impossibles a atteindre a six defenseurs — c est la GEOMETRIE du scenario.
"""
import sys, numpy as np, torch

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__zt__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y = g['SOI'], g['ENN'], g['MASQ'], g['Y']

src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__zt2__'}
exec(compile(src2[:src2.index("def percevoir")], 'agent_complet.py', 'exec'), h)
RISQUE, dev, CHAMP = h['RISQUE'], h['dev'], h['CHAMP']

with torch.no_grad():
    pc = torch.tensor(SOI[:, [4]], device=dev)
    ent = torch.tensor(ENN[:, :, 3:6], device=dev)
    msk = torch.tensor(MASQ, device=dev)
    s = []
    for i in range(0, len(pc), 65536):
        s.append(torch.sigmoid(RISQUE(pc[i:i+65536], ent[i:i+65536], msk[i:i+65536])).cpu())
    score = torch.cat(s).numpy()

viv = MASQ > 0.5
n_enn = viv.sum(1)
d_min = np.where(viv, ENN[..., 3] * 400.0, 1e9).min(axis=1)
a_min = np.where(viv, ENN[..., 4] * 180.0, 1e9).min(axis=1)   # le plus petit ecart au cone
dans_cone = ((a_min < CHAMP)).astype(float)
supp = SOI[:, 5]

TRANQ = score < 0.20
DUR = score > 0.60
print(f"\n  {len(score)} instants · score min {score.min():.3f} · max {score.max():.3f}")
print(f"  zone TRANQUILLE (< 0,20) : {TRANQ.mean():.1%} des instants"
      f" · mortalite reelle {Y[TRANQ].mean():.2%}")
print(f"  zone DURE       (> 0,60) : {DUR.mean():.1%}"
      f" · mortalite reelle {Y[DUR].mean():.2%}")

print("\n" + "=" * 78)
print("  DE QUOI EST FAITE CHAQUE ZONE  (mediane)")
print("  " + "-" * 76)
print(f"  {'':22s} {'TRANQUILLE':>12} {'DURE':>12} {'sandbox ?':>22}")
lignes = [
    ("ennemis vivants",      np.median(n_enn[TRANQ]),  np.median(n_enn[DUR]),  "6,5 en moyenne, fixe"),
    ("distance au + proche", np.median(d_min[TRANQ]),  np.median(d_min[DUR]),  "de 40 a 250 m"),
    ("ecart au cone le +",   np.median(a_min[TRANQ]),  np.median(a_min[DUR]),  "libre, 0 a 180"),
    ("part dans un cone",    dans_cone[TRANQ].mean(),  dans_cone[DUR].mean(),  "45 % du trajet"),
    ("suppression subie",    np.median(supp[TRANQ]),   np.median(supp[DUR]),   "ABSENTE"),
]
for nom, a, b, sb in lignes:
    print(f"  {nom:22s} {a:12.2f} {b:12.2f} {sb:>22}")

print("\n" + "=" * 78)
print("  CE QUE LA SANDBOX PEUT EXPRIMER")
print("  " + "-" * 76)
# la sandbox : 6,5 defenseurs, tous vivants, distances 40-250 m, pas de suppression
sb_enn = float(h['MSK'].sum(1).float().mean())
print(f"     ennemis vivants dans la sandbox : {sb_enn:.1f} en moyenne, JAMAIS moins")
q = np.quantile(n_enn[TRANQ], [0.25, 0.5, 0.75])
print(f"     ennemis dans la zone tranquille du corpus : quartiles {q[0]:.0f} / {q[1]:.0f} / {q[2]:.0f}")
part_1enn = (n_enn[TRANQ] <= 2).mean()
print(f"     part de la zone tranquille avec <= 2 ennemis : {part_1enn:.1%}")
part_supp0 = (supp[TRANQ] < 0.01).mean()
print(f"     part de la zone tranquille sans suppression subie : {part_supp0:.1%}")

print("\n" + "=" * 78)
if part_1enn > 0.5 and sb_enn > 4:
    print("  LA ZONE TRANQUILLE DU CORPUS EST FAITE DE SOLITUDE : peu d ennemis a portee.")
    print("  La sandbox en pose 6,5, toujours, tous vivants, tous a portee. Elle ne peut pas")
    print("  EXPRIMER cet etat — et c est pourquoi son score ne descend jamais.")
    print("  -> le defaut est la GEOMETRIE DU SCENARIO, pas une entree du predicteur.")
else:
    print("  La zone tranquille n est pas faite de solitude. Voir la table ci-dessus pour")
    print("  savoir de quoi — et si la sandbox peut l exprimer.")
print("  " + "=" * 76)
