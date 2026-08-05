#!/usr/bin/env python3
"""mecanisme_feu.py — LE FEU DES CAMARADES PROTEGE-T-IL ?

C'est la derniere hypothese debout pour expliquer le fait fondateur du projet :
l'attaque a DEUX AXES bat la frontale de +12,3 points sur 1324 engagements, p < 0,0001.

Trois canaux ont ete mesures et ecartes :
  le REGARD     ne se detourne pas vers la base de feu (30° -> 20°, smoke du 04/08)
  les ARMES     ne se detournent pas du flanc (+8°, 9 configurations sur 20)
  la PERCEPTION ne protege pas le flanc (banc d'escouade n°4, vrai negatif)

Reste le FEU. Et le +12,3 est un fait d'ESCOUADE : deux axes, donc quelqu'un qui FIXE.

CE QU'ON N'A PAS, ET IL FAUT LE DIRE
  Les journaux bruts des 1324 engagements N'EXISTENT PLUS — seul le resultat agrege
  subsiste dans RESULTAT_AB_BIAXE.md. Le mecanisme ne peut donc pas y etre cherche.
  Le corpus Battle Lines porte un drapeau `tir` par soldat et par tick, mais PAS la cible :
  on sait QUI tire et QUAND, jamais SUR QUI.

LA QUESTION QU'ON PEUT QUAND MEME POSER, et c'est la bonne
  A DANGER GEOMETRIQUE EGAL, un soldat dont les camarades tirent meurt-il moins ?
  C'est exactement la fixation : le feu ami detourne l'attention adverse.

LE PIEGE, ET COMMENT ON L'EVITE
  Le tir allie est massivement correle au danger — on tire quand ca chauffe. Une correlation
  brute dirait donc « le feu ami TUE », ce qui serait un artefact. On STRATIFIE donc par le
  risque geometrique predit (le modele a 0,7138 appris sur le corpus), et on compare la
  mortalite avec et sans feu ami A L'INTERIEUR de chaque strate.

CRITERES, ecrits avant de regarder :
  F0 VALIDITE   le tir allie doit varier dans chaque strate — au moins 5 % des observations
                de chaque cote. Sinon la comparaison est vide.
  F1 EFFET      a risque egal, la mortalite doit etre PLUS BASSE avec feu ami, sur une
                majorite nette des strates (>= 7 sur 10), et l'ecart global doit depasser
                2 points de mortalite.
  F2 SENS       si l'effet est INVERSE (le feu ami accompagne une mortalite plus forte a
                risque egal), la fixation par le feu est refutee et il faut le dire.
  F3 DOSE       l'effet doit croitre avec le NOMBRE de camarades qui tirent. Un effet
                identique a 1 et a 5 tireurs serait suspect.
  F4 NUL        en brassant le drapeau de tir allie, tout doit disparaitre.
"""
import sys, math
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
exec(src.split('print(f"  apprentissage')[0])

import numpy as np, torch, torch.nn as nn
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
te = est_test
RAYON = 100.0          # « mes camarades proches » : ceux qui peuvent fixer pour moi

# ---------------------------------------------------------------- le feu ami, par observation
# On reparcourt les memes ticks que la sonde 1, dans le meme ordre, et on compte pour chaque
# soldat combien de ses camarades TIRENT au meme instant, a moins de RAYON metres.
# ⟨noeuds : id, x, y, z, vivant, camp, TIR, azimut, posture, suppression, neuf⟩
print("\n  comptage du feu ami…", flush=True)
FEU = []
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    ids, pos, camp, tir, viv = [], [], [], [], []
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            ids.append(int(xt[j,0])); pos.append((xt[j,1], xt[j,2]))
            camp.append(xt[j,5]); tir.append(xt[j,6]); viv.append(xt[j,4] > 0.5)
    if not ids: continue
    ids = np.array(ids); pos = np.array(pos, float)
    camp = np.array(camp); tir = np.array(tir); viv = np.array(viv)
    ou = {int(u): k for k, u in enumerate(ids)}
    liens = defaultdict(list)
    for a, b, k, v, mes in ar_par_tick[int(ti)]:
        if a in ou and b in ou: liens[a].append(1); liens[b].append(1)
    for u in liens:
        k = ou[u]
        # MEME FILTRE QUE LA SONDE 1 : seuls les vivants comptent. Sans lui, 308 observations
        # de decalage — et l'assertion d'alignement l'a attrape avant toute comparaison.
        if not viv[k]: continue
        d = np.linalg.norm(pos - pos[k], axis=1)
        amis = (camp == camp[k]) & (d < RAYON) & (ids != u)
        FEU.append(float((tir[amis] > 0.5).sum()))
FEU = np.array(FEU, np.float32)
print(f"  {len(FEU)} observations · camarades qui tirent : "
      f"moyenne {FEU.mean():.2f} · part avec au moins un {(FEU>0).mean():.1%}", flush=True)
assert len(FEU) == len(Y), f"desalignement : {len(FEU)} contre {len(Y)}"

# ---------------------------------------------------------------- le risque geometrique
class R(nn.Module):
    def __init__(s, ce, cs, h=96):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(ce,h), nn.ReLU(), nn.Linear(h,h))
        s.q = nn.Linear(cs,h)
        s.out = nn.Sequential(nn.Linear(cs+h,h), nn.ReLU(), nn.Linear(h,1))
    def forward(s, soi, enn, msk):
        z = s.enc(enn)
        a = (z*s.q(soi).unsqueeze(1)).sum(-1)/math.sqrt(z.shape[-1])
        a = torch.softmax(a.masked_fill(msk<0.5,-1e9),-1).unsqueeze(-1)
        return s.out(torch.cat([soi,(z*a).sum(1)],-1)).squeeze(-1)

E_geo = ENN.copy(); E_geo[:,:,[0,1,2,6]] = 0.0
torch.manual_seed(0); np.random.seed(0)
m = R(ENN.shape[-1], SOI.shape[-1]).to(dev)
opt = torch.optim.Adam(m.parameters(), 2e-3)
tr = np.where(~te)[0]
S = torch.tensor(SOI,device=dev); E = torch.tensor(E_geo,device=dev)
M = torch.tensor(MASQ,device=dev); Yt = torch.tensor(Y,device=dev)
pos_ = float(Y[tr].mean()); w = torch.tensor((1-pos_)/pos_, device=dev)
for _ in range(800):
    b = torch.tensor(np.random.choice(tr,4096), device=dev)
    l = nn.functional.binary_cross_entropy_with_logits(m(S[b],E[b],M[b]), Yt[b], pos_weight=w)
    opt.zero_grad(); l.backward(); opt.step()
with torch.no_grad():
    o = []
    for i in range(0, len(Y), 65536):
        b = torch.arange(i, min(i+65536,len(Y)), device=dev)
        o.append(m(S[b],E[b],M[b]).cpu().numpy())
RISK = np.concatenate(o)
print(f"  risque geometrique calcule sur les {len(RISK)} observations", flush=True)

# ---------------------------------------------------------------- la comparaison stratifiee
def stratifie(feu, nom, seuil=0.5):
    q = np.quantile(RISK, np.linspace(0, 1, 11))
    lignes, n_ok = [], 0
    for i in range(10):
        s = (RISK >= q[i]) & (RISK <= q[i+1])
        a = s & (feu > seuil); b = s & (feu <= seuil)
        if a.sum() < 50 or b.sum() < 50: continue
        part = min(a.sum(), b.sum()) / max(s.sum(), 1)
        ma, mb = Y[a].mean(), Y[b].mean()
        lignes.append((i, a.sum(), b.sum(), ma, mb, ma-mb, part))
        if ma < mb: n_ok += 1
    return lignes, n_ok

print("\n" + "="*80)
print(f"  A RISQUE GEOMETRIQUE EGAL — mortalite a 30 s · feu ami = camarade qui tire dans {RAYON:.0f} m")
print("  " + "-"*78)
print(f"  {'strate':>7s} {'n avec':>8s} {'n sans':>8s} {'mort AVEC':>11s} {'mort SANS':>11s} {'ecart':>9s}")
lignes, n_ok = stratifie(FEU, 'feu ami')
for i, na, nb, ma, mb, d, part in lignes:
    print(f"  {i+1:7d} {na:8d} {nb:8d} {ma:10.2%} {mb:10.2%} {d:+8.2%}")
print("="*80)

f0 = len(lignes) >= 7 and all(p >= 0.05 for *_, p in lignes)
print(f"\n  F0 VALIDITE  {len(lignes)}/10 strates exploitables, variation suffisante "
      f"-> {'OK' if f0 else 'ECHEC : comparaison vide'}")
if lignes:
    glob = np.average([d for *_, d, _ in lignes], weights=[na+nb for _, na, nb, *_ in lignes])
    f1 = n_ok >= 7 and glob < -0.02
    f2 = glob < 0
    print(f"  F1 EFFET     mortalite PLUS BASSE avec feu ami dans {n_ok}/{len(lignes)} strates ; "
          f"ecart global {glob:+.2%} (exige <= -2 pts)  -> {'OK' if f1 else 'ECHEC'}")
    print(f"  F2 SENS      {'le feu ami accompagne MOINS de morts' if f2 else 'INVERSE : le feu ami accompagne PLUS de morts a risque egal'}")

    print(f"\n  F3 DOSE — l'effet croit-il avec le nombre de camarades qui tirent ?")
    for s_ in [0.5, 1.5, 2.5]:
        l2, k2 = stratifie(FEU, 'x', seuil=s_)
        if l2:
            g2 = np.average([d for *_, d, _ in l2], weights=[na+nb for _, na, nb, *_ in l2])
            print(f"     au moins {int(s_+0.5)} tireur(s) : ecart global {g2:+.2%} "
                  f"({k2}/{len(l2)} strates favorables)")

    FEU_BR = np.random.permutation(FEU)
    l3, k3 = stratifie(FEU_BR, 'brasse')
    g3 = np.average([d for *_, d, _ in l3], weights=[na+nb for _, na, nb, *_ in l3]) if l3 else 0
    f4 = abs(g3) < 0.01
    print(f"\n  F4 NUL       drapeau de tir BRASSE : ecart global {g3:+.2%} "
          f"-> {'OK' if f4 else 'ECHEC : la stratification fuit'}")

    print("\n" + "="*80)
    if f0 and f1 and f4:
        print("  LE FEU AMI PROTEGE. A danger geometrique egal, un soldat dont les camarades")
        print("  tirent meurt moins. C'est le mecanisme du +12,3 points : deux axes, donc")
        print("  quelqu'un qui FIXE — et la fixation passe par le FEU, pas par la perception.")
    elif f0 and not f2:
        print("  REFUTE, ET DANS L'AUTRE SENS. A risque geometrique egal, le feu ami accompagne")
        print("  DAVANTAGE de morts. La fixation par le feu n'explique pas le +12,3 :")
        print("  le dernier canal tombe, et le fait fondateur reste sans mecanisme.")
    else:
        print("  PAS D'EFFET NET. Voir les controles avant toute lecture.")
    print("="*80)
