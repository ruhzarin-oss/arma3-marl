#!/usr/bin/env python3
"""calibrer_v2.py — LA CALIBRATION, sur un decoupage REPARE.

⟨Fable, 07/08 : « on repare le DECOUPAGE, pas le critere. »⟩

CE QUI A FAIT CEDER V2 HIER : la decoupe du corpus fait 57 blocs de dix minutes, dont 11
tenus a l ecart. L intensite des combats varie d un bloc a l autre, donc les deux moities
n ont pas la meme mortalite — 8,47 % contre ~10,3 %. Ce sont deux bras NON CONTEMPORAINS,
la regle 8 violee a l interieur meme du corpus. La porte V2 a attrape ca, pas la calibration.

LA REPARATION : des blocs PLUS FINS et plus nombreux, pour que chaque moitie echantillonne
toute la duree de la capture. BLOC = 500 ticks (~100 s) donne ~346 blocs au lieu de 57.
Et une MARGE de 150 ticks est jetee aux coutures : l etiquette regarde 30 s en avant, soit
150 ticks, et sans marge un bloc tenu a l ecart lirait la suite d un bloc d ajustement.

LES CRITERES NE BOUGENT PAS D UNE VIRGULE — recopies de calibrer_risque.py :
  V1  l AUC doit rester INCHANGEE a 0,001 pres
  V2  la moyenne calibree doit tomber sur la mortalite de base a 1 point pres
  V3  la mort par pas au PLANCHER doit passer sous 1 %
  V4  ajustee sur l ajustement, verifiee sur ce qui est tenu a l ecart
"""
import sys, numpy as np, torch

BLOC, MARGE, GRAINE = 500, 150, 11

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__c2__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y, TICK = g['SOI'], g['ENN'], g['MASQ'], g['Y'], g['TICK']

src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__c3__'}
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

# --- le decoupage repare : blocs fins, tires au sort, marge aux coutures
T = int(TICK.max()) + 1
nb = max(T // BLOC, 3)
bloc_de = np.minimum(TICK // BLOC, nb - 1)
rng = np.random.default_rng(GRAINE)
ordre = rng.permutation(nb)
ecart = set(ordre[:max(1, nb // 5)].tolist())
te = np.array([b in ecart for b in bloc_de])
# marge : on jette les instants trop proches d une couture
pos_dans = TICK % BLOC
marge = (pos_dans >= BLOC - MARGE)
te, tr = te & ~marge, (~te) & ~marge

print(f"\n  {len(Y)} instants · mortalite globale {Y.mean():.2%}")
print(f"  decoupage : {nb} blocs de {BLOC} ticks ({BLOC*0.2:.0f} s) · marge {MARGE} ticks")
print(f"  ajustement {tr.sum()} ({Y[tr].mean():.2%} de morts)"
      f" · ecart {te.sum()} ({Y[te].mean():.2%})")
print(f"  ecart de mortalite entre les deux moities : {abs(Y[tr].mean()-Y[te].mean())*100:.2f} points"
      f"   ⟨hier, avec 57 blocs : 1,8 point⟩")


def auc(s_, y_):
    o = np.argsort(s_); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    return (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


bords = np.unique(np.quantile(score[tr], np.linspace(0, 1, 61)))
ib = np.clip(np.searchsorted(bords, score[tr], side='right') - 1, 0, len(bords) - 2)
centres, taux = [], []
for b in range(len(bords) - 1):
    m = ib == b
    if m.sum() >= 200:
        centres.append(score[tr][m].mean()); taux.append(Y[tr][m].mean())
centres, taux = np.array(centres), np.array(taux)
for _ in range(300):
    v = np.where(np.diff(taux) < 0)[0]
    if not len(v):
        break
    i = v[0]; taux[i] = taux[i + 1] = (taux[i] + taux[i + 1]) / 2
cal = np.interp(score, centres, taux)

print("\n" + "=" * 76)
print("  LES QUATRE VERIFICATIONS — criteres INCHANGES")
print("  " + "-" * 74)
a1, a2 = auc(score[te], Y[te]), auc(cal[te], Y[te])
v1 = abs(a1 - a2) < 0.001
print(f"     V1  AUC brut {a1:.4f}  calibre {a2:.4f}  ecart {abs(a1-a2):.5f}"
      f"   -> {'OK' if v1 else 'ECHEC'}")
v2 = abs(cal[te].mean() - Y[te].mean()) < 0.01
print(f"     V2  moyenne calibree {cal[te].mean():.2%} contre base {Y[te].mean():.2%}"
      f"  (ecart {abs(cal[te].mean()-Y[te].mean())*100:.2f} pt)   -> {'OK' if v2 else 'ECHEC'}")
pm_a = 1 - (1 - score.min()) ** (1 / 9.15)
pm_b = 1 - (1 - cal.min()) ** (1 / 9.15)
v3 = pm_b < 0.01
print(f"     V3  mort par pas au plancher {pm_a:.2%} -> {pm_b:.3%}   -> {'OK' if v3 else 'ECHEC'}")
print(f"     V4  ajustee sur l ajustement, verifiee sur l ecart, marge aux coutures   -> OK")

print("\n" + "=" * 76)
if v1 and v2 and v3:
    np.savez('/mnt/data/corpus/calibration_risque.npz', centres=centres, taux=taux,
             bloc=BLOC, marge=MARGE, graine=GRAINE)
    print("  CALIBRATION ECRITE — /mnt/data/corpus/calibration_risque.npz")
    print("  Le score devient une probabilite, l ordre n a pas bouge, et « hors de tout cone »")
    print("  veut enfin dire quelque chose.")
else:
    print("  NON ECRITE — une verification a cede. On ne force pas.")
print("  " + "=" * 74)
