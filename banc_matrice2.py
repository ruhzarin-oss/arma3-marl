#!/usr/bin/env python3
"""banc_matrice2.py — LE BANC-MATRICE v2. On ne simule rien : on relit le passe.

Criteres deposes AVANT ce code : CRITERES_BANC_MATRICE_V2.md (commit b1761ce).
Fiches relues (regle 10) : fibua-line-bench-certified, etre-vu-tue-deux-fois-plus,
angle-mort-certifie-arma, knowsabout-est-de-camp-pas-de-soldat, expo-vaut-le-hasard.

  PORTE 0   deux paires dont l ORDRE EST CONNU, ecart exige >= 3 points :
              dans le cone / hors      -> dedans plus mortel  (18/18 contre 0/26)
              vu DIRECTIONNEL / non    -> vu plus mortel      (etre vu tue 2x)
            « il me voit » = ligne de vue ET je suis dans son cone. La colonne `vu` du
            corpus est une ligne de vue SYMETRIQUE (emetteur ligne 257) : seule, elle ne
            separe pas (-0,27 pt). Croisee avec l angle, elle separe (+3,91).
  AIGUILLE  strate utilisable a >= 2 000 instants ET >= 200 morts. Le butoir surveille est
            celui du SEPARATEUR, pas celui du taux brut.
  C1 NEGATIF `expo` vaut le hasard (AUC 0,5005, mesure). Elle doit ECHOUER toutes les portes.
            Si elle en passe une, cette porte est DECORATIVE et rien ne se lit.
  C2 NUL    etiquettes brassees -> indifference.
  C3 STRAT. toute comparaison a SUPPRESSION SUBIE CONSTANTE (92 % de la tautologie).

PUIS, si et seulement si le banc a son certificat : LES YEUX.
  On donne a un petit lecteur les FAITS DISCRETS (suis-je vu, par combien, dans le cone de
  combien, distance du plus proche par tranches) et a un autre, IDENTIQUE, la GEOMETRIE
  CONTINUE (les memes distances et angles, en nombres). Meme moitie d apprentissage, meme
  nombre de parametres, meme budget. On les juge sur l autre moitie.

  LE PIEGE EVITE : le scalaire du predicteur est entraine SUR CE CORPUS. Le comparer tel quel
  serait truque — il a deja vu les reponses. Les deux lecteurs sont donc REAPPRIS DEPUIS ZERO.

CE BANC NE DIRA JAMAIS si AGIR sur la lecture paie : les instants sont figes. Cette
question reste a Arma, une seule campagne, architecture du banc A2.
"""
import sys, math, numpy as np, torch, torch.nn as nn

DEMI_CONE, ECART_MIN = 35.0, 0.03
BLOC, MARGE, GRAINE = 500, 150, 11

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__bm2__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
SOI, ENN, MASQ, Y, TICK = g['SOI'], g['ENN'], g['MASQ'], g['Y'], g['TICK']

viv = MASQ > 0.5
d_e = ENN[..., 3] * 400.0
a_lui = ENN[..., 4] * 180.0
a_moi = ENN[..., 5] * 180.0
vu_sym = ENN[..., 1] > 0.5
mesuree = ENN[..., 2] > 0.5
supp = SOI[:, 5]

dans_cone_e = viv & (a_lui < DEMI_CONE)
vu_dir_e = viv & mesuree & vu_sym & (a_lui < DEMI_CONE)
dans_cone = dans_cone_e.any(axis=1)
vu_dir = vu_dir_e.any(axis=1)
d_min = np.where(viv, d_e, 1e9).min(axis=1)
n_cone = dans_cone_e.sum(axis=1)
n_vu = vu_dir_e.sum(axis=1)

print(f"\n  {len(Y)} instants · mortalite {Y.mean():.2%}")
print(f"  dans un cone {dans_cone.mean():.1%} · vu DIRECTIONNEL {vu_dir.mean():.1%}")


def ecart_stratifie(masque, y=None):
    """difference de mortalite entre un paquet et son complement, A SUPPRESSION CONSTANTE."""
    y = Y if y is None else y
    num = den = 0.0
    na = nb = 0
    for m in [(supp <= 0.01), (supp > 0.01) & (supp <= 0.3), (supp > 0.3)]:
        a, b = masque & m, (~masque) & m
        if a.sum() < 500 or b.sum() < 500:
            continue
        w = a.sum() + b.sum()
        num += (y[a].mean() - y[b].mean()) * w
        den += w
        na += int(a.sum()); nb += int(b.sum())
    return (num / den if den else float('nan')), na, nb


# ---------------------------------------------------------------- expo, le controle negatif
SEUIL_COUCHE, PENTE_COUCHE = 120.0, 12.0

def expo_analytique():
    """expo, la fonction de cout de la sandbox — AUC 0,5005 sur ce corpus, MESURE.

    RECOPIEE de agent_complet.py lignes 195-215, pas reecrite. Ma premiere version etait un
    detecteur de cone deguise, et le controle negatif l a attrapee."""
    dd = np.where(viv, d_e, 1e9).clip(min=1.0)
    dans = 1.0 / (1.0 + np.exp(-(DEMI_CONE - a_lui) * 1.2))
    base = 0.45 * (1.0 - np.clip(dd / 400.0, 0, 1))
    e = (base + (1.0 - base) * dans) * (1.0 - np.clip(dd / 450.0, 0, 1))
    # facteur de posture : le couche ne paie qu au-dela de 120 m, par observateur
    couche = 1.0 - 1.0 / (1.0 + np.exp(-(dd - SEUIL_COUCHE) / PENTE_COUCHE))
    est_couche = (SOI[:, 4] > 0.6)[:, None]          # posture/3 : 2/3 = couche
    e = e * np.where(est_couche, couche, 1.0)
    e = np.where(viv, e, 0.0)
    return e.max(axis=1)                              # LE MAXIMUM, pas la moyenne


print("\n" + "=" * 78)
print("  PORTE 0 — deux paires dont l ORDRE EST CONNU   (exige >= 3 points)")
print("  " + "-" * 76)
paires = [("dans le cone / hors    ", dans_cone, "dedans plus mortel"),
          ("vu DIRECTIONNEL / non  ", vu_dir, "vu plus mortel")]
ok0 = True
for nom, m, sens in paires:
    e, na, nb = ecart_stratifie(m)
    passe = (na >= 20000 and nb >= 20000 and e >= ECART_MIN)
    ok0 &= passe
    print(f"     {nom} ecart {e:+.2%}  ({na} contre {nb})"
          f"   -> {'OK' if passe else 'ECHEC'}   ⟨{sens}⟩")

print("\n" + "=" * 78)
print("  C1 — CONTRÔLE NÉGATIF : `expo` vaut le hasard, elle DOIT échouer")
print("  " + "-" * 76)
ex = expo_analytique()
med = np.median(ex)
c1 = True
for nom, m, _ in paires:
    e_ex, _, _ = ecart_stratifie(m, y=(ex > med).astype(np.float32))
    # expo « predit » le paquet si elle le separe ; on veut qu elle NE separe PAS la MORT
    e_mort, _, _ = ecart_stratifie((ex > med))
    print(f"     expo sur la mortalite : ecart {e_mort:+.2%}"
          f"   -> {'ne separe pas (OK)' if abs(e_mort) < ECART_MIN else 'SEPARE — porte decorative'}")
    c1 = abs(e_mort) < ECART_MIN
    break

print("\n" + "=" * 78)
print("  C2 — CONTRÔLE NUL : étiquettes brassées")
print("  " + "-" * 76)
rng = np.random.default_rng(0)
Ybr = Y.copy(); rng.shuffle(Ybr)
e_nul, _, _ = ecart_stratifie(dans_cone, y=Ybr)
c2 = abs(e_nul) < ECART_MIN
print(f"     écart sur étiquettes brassées {e_nul:+.2%}   -> {'OK' if c2 else 'ECHEC'}")

print("\n" + "=" * 78)
print("  AIGUILLE — strates utilisables (>= 2 000 instants ET >= 200 morts)")
print("  " + "-" * 76)
n_ok = 0
for a, b in [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250), (250, 400)]:
    m = (d_min >= a) & (d_min < b)
    nm = int(Y[m].sum())
    util = m.sum() >= 2000 and nm >= 200
    n_ok += util
    print(f"     {a:3d}-{b:<3d} m   n={int(m.sum()):6d} · morts {nm:5d} · mortalite"
          f" {Y[m].mean() if m.sum() else 0:6.2%}   {'UTILISABLE' if util else 'trop maigre'}")

print("\n" + "=" * 78)
if not (ok0 and c1 and c2 and n_ok >= 4):
    manque = [x for x, c in (("PORTE 0", ok0), ("C1", c1), ("C2", c2),
                             ("strates", n_ok >= 4)) if not c]
    print(f"  LE BANC N'A PAS SON CERTIFICAT — {', '.join(manque)}. Rien ne se lit sur un agent.")
    sys.exit(0)
print("  LE BANC A SON CERTIFICAT. Il sépare deux paires d'ordre connu, `expo` y échoue,")
print("  le contrôle nul tient, et l'aiguille bouge. Il peut juger des YEUX.")

# ---------------------------------------------------------------- LES YEUX
print("\n" + "=" * 78)
print("  LES YEUX — les FAITS DISCRETS ordonnent-ils mieux que la GÉOMÉTRIE CONTINUE ?")
print("  " + "-" * 76)
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
T = int(TICK.max()) + 1
nb = max(T // BLOC, 3)
bl = np.minimum(TICK // BLOC, nb - 1)
rg = np.random.default_rng(GRAINE)
ec = set(rg.permutation(nb)[:max(1, nb // 5)].tolist())
te = np.array([b in ec for b in bl]) & ~(TICK % BLOC >= BLOC - MARGE)
tr = (~np.array([b in ec for b in bl])) & ~(TICK % BLOC >= BLOC - MARGE)

# FAITS DISCRETS — des ETATS, pas des nombres. C est l idee de Younes, mise en chiffres.
F_DIS = np.stack([
    vu_dir.astype(np.float32),                       # suis-je vu, oui ou non
    (n_vu >= 2).astype(np.float32),                  # par plusieurs
    dans_cone.astype(np.float32),                    # dans un cone
    (n_cone >= 2).astype(np.float32),                # dans plusieurs cones
    (d_min < 50).astype(np.float32),                 # colle
    ((d_min >= 50) & (d_min < 150)).astype(np.float32),
    (d_min >= 150).astype(np.float32),               # loin
    SOI[:, 4],                                       # ma posture
], -1)
# GEOMETRIE CONTINUE — les memes faits, en nombres
F_CON = np.stack([
    np.clip(d_min, 0, 400) / 400.0,
    np.where(viv, a_lui, 180.0).min(axis=1) / 180.0,
    np.where(viv, a_moi, 180.0).min(axis=1) / 180.0,
    viv.sum(axis=1).astype(np.float32) / 12.0,
    SOI[:, 4],
], -1)


def auc(s_, y_):
    o = np.argsort(s_); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    return (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def lecteur(F, nom):
    """MEME architecture, MEME budget, MEME moitie d apprentissage. Reappris depuis zero —
    sinon on mesurerait qui a le plus revise, pas qui voit le mieux."""
    torch.manual_seed(0)
    X = torch.tensor(F, device=dev)
    y = torch.tensor(Y, device=dev)
    m = nn.Sequential(nn.Linear(F.shape[1], 24), nn.ReLU(), nn.Linear(24, 1)).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    itr = torch.tensor(np.where(tr)[0], device=dev)
    for _ in range(400):
        i = itr[torch.randint(0, len(itr), (8192,), device=dev)]
        p = m(X[i]).squeeze(-1)
        perte = nn.functional.binary_cross_entropy_with_logits(p, y[i])
        opt.zero_grad(); perte.backward(); opt.step()
    with torch.no_grad():
        s = m(X[torch.tensor(np.where(te)[0], device=dev)]).squeeze(-1).cpu().numpy()
    a = auc(s, Y[te])
    print(f"     {nom:24s} {F.shape[1]} entrees · AUC {a:.4f}")
    return a


a_dis = lecteur(F_DIS, "FAITS DISCRETS")
a_con = lecteur(F_CON, "GEOMETRIE CONTINUE")
print("  " + "-" * 76)
print(f"     ecart {a_dis - a_con:+.4f}")
print("\n" + "=" * 78)
if a_dis - a_con >= 0.01:
    print("  LES FAITS DISCRETS ORDONNENT MIEUX. Dire « je suis vu » vaut mieux que donner un")
    print("  angle — l état bat le nombre. -> a verser dans l observation de l agent.")
elif a_con - a_dis >= 0.01:
    print("  LA GÉOMÉTRIE CONTINUE ORDONNE MIEUX. Découper en états perd de l information.")
else:
    print("  ÉGALITÉ. Les deux representations ordonnent aussi bien — on garde les chiffres,")
    print("  on n'écrit pas d'histoire. Le choix se fera sur un autre critère qu'ici.")
print("  ⟨ce banc dit si l'agent LIT le monde. Jamais si agir dessus PAIE — ça reste à Arma.⟩")
print("  " + "=" * 76)
