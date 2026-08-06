#!/usr/bin/env python3
"""calibrer_risque.py — DONNER UN SENS ABSOLU A UN SCORE QUI N EN AVAIT PAS.

LE DEFAUT, mesure ce soir : la sortie du predicteur vaut min 0,406 · mediane 0,601 · max
0,742, alors que la mortalite REELLE du corpus a 30 s est de 10,00 %. C est un SCORE DE
CLASSEMENT, pas une probabilite. Le traiter comme une probabilite de mourir — ce que j ai
fait en ecrivant la loi-predicteur — donne un PLANCHER a 5,53 % de mort par pas : meme
totalement hors de tous les cones, on meurt. Sortir du champ n achete alors RIEN, il ne reste
que la longueur du chemin, et le crochet perd mecaniquement.

LA REPARATION : une transformation MONOTONE score -> mortalite observee, ajustee sur la part
du corpus tenue a l ecart. Monotone, donc elle ne change ni l ordre, ni l AUC, ni aucun des
verdicts certifies. Elle ne fait que rendre les valeurs LISIBLES en absolu.

CRITERES, ecrits avant de calibrer :
  V1  l AUC doit rester INCHANGEE a 0,001 pres. Une transformation monotone ne peut pas la
      changer ; si elle change, le code est faux.
  V2  la moyenne calibree doit tomber sur la mortalite de base a 1 point pres (10,00 %).
  V3  le PLANCHER doit descendre franchement : la mort par pas au minimum doit passer sous
      1 %. Sinon « hors du cone » ne veut toujours rien dire et la reparation a echoue.
  V4  la calibration est ajustee sur la partie ENTRAINEMENT et verifiee sur la partie tenue
      a l ecart. On ne se note pas sur sa propre copie.
"""
import sys, numpy as np, torch

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__cal__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y, te = g['SOI'], g['ENN'], g['MASQ'], g['Y'], g['est_test']

src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__cal2__'}
exec(compile(src2[:src2.index("def percevoir")], 'agent_complet.py', 'exec'), h)
RISQUE, dev = h['RISQUE'], h['dev']

with torch.no_grad():
    pc = torch.tensor(SOI[:, [4]], device=dev)
    ent = torch.tensor(ENN[:, :, 3:6], device=dev)
    msk = torch.tensor(MASQ, device=dev)
    s = []
    for i in range(0, len(pc), 65536):
        s.append(torch.sigmoid(RISQUE(pc[i:i+65536], ent[i:i+65536], msk[i:i+65536])).cpu())
    score = torch.cat(s).numpy().astype(np.float64)

tr = ~te
print(f"\n  {len(Y)} instants · mortalite {Y.mean():.2%}"
      f" · ajustement sur {tr.sum()} · verification sur {te.sum()}")
print(f"  score BRUT : min {score.min():.3f} · mediane {np.median(score):.3f}"
      f" · max {score.max():.3f} · moyenne {score.mean():.3f}")


def auc(s_, y_):
    o = np.argsort(s_)
    r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    return (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


# --- la calibration : quantiles, mortalite observee, monotonie forcee (PAVA simplifie)
NB = 60
bords = np.quantile(score[tr], np.linspace(0, 1, NB + 1))
bords = np.unique(bords)
idxb = np.clip(np.searchsorted(bords, score[tr], side='right') - 1, 0, len(bords) - 2)
centres, taux = [], []
for b in range(len(bords) - 1):
    m = idxb == b
    if m.sum() < 200:
        continue
    centres.append(score[tr][m].mean())
    taux.append(Y[tr][m].mean())
centres, taux = np.array(centres), np.array(taux)
# monotonie : moyenne cumulee croissante (pool adjacent violators, version simple)
for _ in range(200):
    v = np.where(np.diff(taux) < 0)[0]
    if len(v) == 0:
        break
    i = v[0]
    m = (taux[i] + taux[i + 1]) / 2
    taux[i] = taux[i + 1] = m
print(f"  calibration : {len(centres)} noeuds · taux de {taux.min():.3%} a {taux.max():.1%}")


def calibre(x):
    return np.interp(x, centres, taux)


cal = calibre(score)

print("\n" + "=" * 76)
print("  LES QUATRE VERIFICATIONS, deposees avant")
print("  " + "-" * 74)
a_brut, a_cal = auc(score[te], Y[te]), auc(cal[te], Y[te])
v1 = abs(a_brut - a_cal) < 0.001
print(f"     V1  AUC  brut {a_brut:.4f}  calibre {a_cal:.4f}  ecart {abs(a_brut-a_cal):.5f}"
      f"   -> {'OK' if v1 else 'ECHEC — le code est faux'}")
v2 = abs(cal[te].mean() - Y[te].mean()) < 0.01
print(f"     V2  moyenne calibree {cal[te].mean():.2%} contre base {Y[te].mean():.2%}"
      f"   -> {'OK' if v2 else 'ECHEC'}")
pm_avant = 1 - (1 - score.min()) ** (1 / 9.15)
pm_apres = 1 - (1 - cal.min()) ** (1 / 9.15)
v3 = pm_apres < 0.01
print(f"     V3  mort par pas au PLANCHER : {pm_avant:.2%} -> {pm_apres:.3%}"
      f"   -> {'OK' if v3 else 'ECHEC'}")
print(f"     V4  ajuste sur l entrainement, verifie sur l ecart   -> OK")
print(f"\n     survie sur 14 pas au plancher : {(1-pm_avant)**14:.1%} -> {(1-pm_apres)**14:.1%}")

print("\n" + "=" * 76)
if v1 and v2 and v3:
    np.savez('/mnt/data/corpus/calibration_risque.npz', centres=centres, taux=taux)
    print("  CALIBRATION ECRITE dans /mnt/data/corpus/calibration_risque.npz")
    print("  Le score devient une probabilite. « Hors de tout cone » veut enfin dire quelque")
    print("  chose. Et l ordre n a pas bouge d un millieme : rien de certifie n est touche.")
else:
    print("  LA CALIBRATION N EST PAS ECRITE — une verification a cede.")
print("  " + "=" * 74)
