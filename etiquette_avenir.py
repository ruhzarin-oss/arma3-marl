#!/usr/bin/env python3
"""etiquette_avenir.py — ANTICIPER D OU VIENT LE DANGER, pas seulement combien il y en aura.

⟨PRÉSAGE, 13-14/07⟩ deux avertissements, relus AVANT de coder (regle 10) :
  1. « exposition ultra-persistante -> mesurer sur les TRANSITIONS, pas le niveau ». Global
     0,031 contre 0,059 ; sur les transitions sur->expose, 0,34 contre 1,00. Recopier le
     present marche presque toujours : une etiquette qui ne bouge pas ne juge rien.
  2. PRÉSAGE rendait meilleur SURVIVANT, pas meilleur tueur. La fiche prescrit elle-meme la
     reparation : « signal plus riche — DIRECTION de la menace, pas juste le niveau ».

Fiches relues : presage-anticipation, etre-vu-tue-deux-fois-plus, angle-mort-certifie-arma,
cout-exposition-par-metre, registre-des-sursitaires. Aucune ne porte deja ce calcul.

CE QU ON MESURE, en deux questions :
  A  LE NIVEAU     « serai-je vu dans DELTA secondes ? »   -> mesure SUR LES TRANSITIONS
  B  LA DIRECTION  « d ou viendra celui qui me verra ? »   -> quadrant, relatif a MON cap

CONTROLES NEGATIFS, tous deux OBLIGATOIRES :
  A : la PERSISTANCE (recopier l etat present) doit ECHOUER sur les transitions. Si elle
      passe, la porte ne mesure que l inertie du monde.
  B : le PRIOR (toujours repondre le quadrant le plus frequent) doit echouer.

TAILLE DE LA PORTE, declaree avant : un ecart d AUC est lisible au-dela de 0,010 ; pour la
direction, un gain d exactitude est lisible au-dela de 3 points sur le prior.
"""
import sys, math, numpy as np, torch, torch.nn as nn

DELTA_S, DEMI_CONE = 10.0, 35.0
ECART_AUC, ECART_DIR = 0.010, 0.03
D = '/mnt/data/corpus/tenseurs'

X = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P = np.load(f'{D}/presence.npy', mmap_mode='r')
AR = np.load(f'{D}/aretes.npy')
TPS = np.load(f'{D}/temps.npy')
T, N, _ = X.shape
print(f"\n  corpus : {T} ticks, {N} noeuds, {len(AR)} aretes")

# --- arêtes par tick : (a, b, k, vue)
from collections import defaultdict
par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    if mes > 0.5:
        par_tick[int(t)].append((int(a), int(b), v))
ticks = np.array(sorted(par_tick.keys()))
dt = np.median(np.diff(TPS[ticks])) if len(ticks) > 1 else 0.2
saut = max(1, int(round(DELTA_S / max(dt, 1e-6))))
print(f"  pas median entre releves {dt:.2f} s -> DELTA de {DELTA_S:.0f} s = {saut} releves")

# --- etat « vu directionnel » par (tick, soldat), et la direction de la menace
def table(ti):
    """identifiant -> (x, y, azimut, posture, suppression), vivants presents seulement."""
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    d = {}
    for j in range(N):
        if pt[j] and xt[j, 0] > 0 and xt[j, 4] > 0.5:
            d[int(xt[j, 0])] = (xt[j, 1], xt[j, 2], xt[j, 7], xt[j, 8], xt[j, 9])
    return d


def etat(ti, T_):
    vu, dirn = {}, {}
    for a, b, v in par_tick[ti]:
        if a not in T_ or b not in T_ or v < 0.5:
            continue
        xa, ya, aa, _, _ = T_[a]
        xb, yb, ab, _, _ = T_[b]
        gis = math.degrees(math.atan2(xa - xb, ya - yb)) % 360
        a_lui = abs(((gis - ab + 180) % 360) - 180)
        if a_lui < DEMI_CONE:                       # il me voit VRAIMENT
            vu[a] = True
            rel = ((gis + 180) % 360 - aa + 180) % 360 - 180
            dirn[a] = int(((rel + 45) % 360) // 90)  # 0 devant 1 droite 2 derriere 3 gauche
    return vu, dirn


# --- construction : present (7 nombres du cahier des charges) + avenir
lignes, y_niv, y_dir, pers = [], [], [], []
for i in range(0, len(ticks) - saut, 3):
    ti, tf = int(ticks[i]), int(ticks[i + saut])
    Tp, Tf = table(ti), table(tf)
    vu_p, dir_p = etat(ti, Tp)
    vu_f, dir_f = etat(tf, Tf)
    ennemis = defaultdict(list)
    for a, b, v in par_tick[ti]:
        if a in Tp and b in Tp:
            ennemis[a].append(b)
    for u, es in ennemis.items():
        if u not in Tf:                       # il doit etre encore la a l arrivee
            continue
        xu, yu, au, pu, su = Tp[u]
        d = [math.hypot(xu - Tp[e][0], yu - Tp[e][1]) for e in es]
        if not d:
            continue
        j = int(np.argmin(d)); e = es[j]
        xe, ye, ae, _, _ = Tp[e]
        gis = math.degrees(math.atan2(xu - xe, yu - ye)) % 360
        a_lui = abs(((gis - ae + 180) % 360) - 180)
        a_moi = abs((((gis + 180) % 360) - au + 180) % 360 - 180)
        lignes.append([min(d[j], 400) / 400, a_lui / 180, a_moi / 180,
                       len(es) / 12.0, pu / 3.0, su,
                       1.0 if u in vu_p else 0.0])
        y_niv.append(1.0 if u in vu_f else 0.0)
        y_dir.append(dir_f.get(u, -1))
        pers.append(1.0 if u in vu_p else 0.0)

F = np.array(lignes, np.float32)
YN = np.array(y_niv, np.float32)
YD = np.array(y_dir, np.int64)
PE = np.array(pers, np.float32)
print(f"  {len(F)} couples present/avenir · vu maintenant {PE.mean():.1%}"
      f" · vu dans {DELTA_S:.0f} s {YN.mean():.1%}")

# --- LES TRANSITIONS : l avertissement de PRÉSAGE
trans = (PE < 0.5)                       # je ne suis PAS vu maintenant
print(f"  instants SÛRS maintenant : {trans.sum()} ({trans.mean():.1%})")
print(f"     parmi eux, vus dans {DELTA_S:.0f} s : {YN[trans].mean():.1%}  <- LA TRANSITION")

n = len(F)
rg = np.random.default_rng(11)
bloc = np.arange(n) // 2000
ec = set(rg.permutation(bloc.max() + 1)[:max(1, (bloc.max() + 1) // 5)].tolist())
te = np.array([b in ec for b in bloc]); tr = ~te
dev = 'cuda' if torch.cuda.is_available() else 'cpu'


def auc(s_, y_):
    o = np.argsort(s_); r = np.empty(len(s_)); r[o] = np.arange(1, len(s_) + 1)
    n1 = y_.sum(); n0 = len(y_) - n1
    if n1 == 0 or n0 == 0:
        return float('nan')
    return (r[y_ > 0.5].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def entraine(Fi, yi, mtr, mte, sortie=1, graine=0):
    torch.manual_seed(graine)
    Xt = torch.tensor(Fi, device=dev)
    yt = torch.tensor(yi, device=dev)
    m = nn.Sequential(nn.Linear(Fi.shape[1], 24), nn.ReLU(), nn.Linear(24, sortie)).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    itr = torch.tensor(np.where(mtr)[0], device=dev)
    for _ in range(400):
        i = itr[torch.randint(0, len(itr), (4096,), device=dev)]
        p = m(Xt[i])
        l = (nn.functional.binary_cross_entropy_with_logits(p.squeeze(-1), yt[i])
             if sortie == 1 else nn.functional.cross_entropy(p, yt[i]))
        opt.zero_grad(); l.backward(); opt.step()
    with torch.no_grad():
        return m(Xt[torch.tensor(np.where(mte)[0], device=dev)]).cpu().numpy()


print("\n" + "=" * 78)
print(f"  A — LE NIVEAU : « serai-je vu dans {DELTA_S:.0f} s ? », SUR LES TRANSITIONS")
print("  " + "-" * 76)
m_tr, m_te = tr & trans, te & trans
a_pers = auc(PE[m_te], YN[m_te])
s = entraine(F[:, :6], YN, m_tr, m_te)      # sans l etat present : on ne recopie pas
a_mod = auc(s.squeeze(-1), YN[m_te])
print(f"     PERSISTANCE (recopier le present)   AUC {a_pers:.4f}   <- contrôle négatif")
print(f"     modèle sur les 6 nombres présents   AUC {a_mod:.4f}")
print(f"     écart {a_mod - a_pers:+.4f}   (lisible au-delà de {ECART_AUC:.3f})")
okA = (a_mod - a_pers) >= ECART_AUC

print("\n" + "=" * 78)
print("  B — LA DIRECTION : « d'où viendra celui qui me verra ? »")
print("  " + "-" * 76)
m2 = trans & (YD >= 0)
m2_tr, m2_te = tr & m2, te & m2
if m2_te.sum() > 200:
    prior = np.bincount(YD[m2_tr], minlength=4).argmax()
    ex_prior = (YD[m2_te] == prior).mean()
    lo = entraine(F[:, :6], YD, m2_tr, m2_te, sortie=4)
    ex_mod = (lo.argmax(1) == YD[m2_te]).mean()
    print(f"     n = {int(m2_te.sum())} transitions avec direction connue")
    print(f"     PRIOR (toujours le quadrant le plus frequent)  exactitude {ex_prior:.1%}")
    print(f"     modèle                                         exactitude {ex_mod:.1%}")
    print(f"     écart {ex_mod - ex_prior:+.1%}   (lisible au-delà de {ECART_DIR:.0%})")
    okB = (ex_mod - ex_prior) >= ECART_DIR
else:
    print(f"     trop peu de transitions avec direction connue ({int(m2_te.sum())}) — illisible")
    okB = False

print("\n" + "=" * 78)
if okA and okB:
    print("  ANTICIPER INFORME, ET LA DIRECTION AUSSI. Le signal ne se réduit pas à l'inertie")
    print("  du monde : sur les transitions, le présent PRÉDIT le danger à venir ET d'où il")
    print("  viendra. -> candidat sérieux pour l'observation de l'étage 1.")
elif okA:
    print("  LE NIVEAU S'ANTICIPE, PAS LA DIRECTION. C'est le signal que PRÉSAGE avait déjà :")
    print("  il apprend à se terrer, pas à choisir par où entrer. On garde le chiffre, on")
    print("  n'écrit pas d'histoire.")
else:
    print("  RIEN NE S'ANTICIPE au-delà de la persistance. L'avenir proche est du présent")
    print("  recopié — et une étiquette qui ne bouge pas ne juge rien.")
print("  ⟨ce banc dit ce qu'une observation CONTIENT, jamais ce qu'une politique EN FAIT⟩")
print("  " + "=" * 76)
