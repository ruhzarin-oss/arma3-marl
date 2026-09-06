#!/usr/bin/env python3
"""CONTROLE POSITIF de la LOI DE TIR (l autre moitie). Cinq tests, chacun son falsificateur.

Le mode d echec a attraper reste l INERTIE, et un second : le DOUBLON — deux mecanismes
pour une seule grandeur (`feu_sur_connu` fraction contre la fenetre de 10 s de la source).
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import canal_cwr as CANAL
from monde_fidele import MONDE_ARMA_REPLIQUE
from assault_terrain import AssaultTerrain

REP = sys.argv[1] if len(sys.argv) > 1 else None
N, GRAINE, PAS = 512, 7, 16
ok = {}
cst = CANAL.constantes_arma3()   # valeurs LUES dans Arma 3 le 03/09

# ⛔ P5 A CHANGE DE SENS LE 03/09. Il verifiait que la porte `MinVisibleFire = 0,63` MORD.
# Elle a ete FALSIFIEE sur Arma 3 (37,1 % des impacts au fusil sur victime vivante en dessous
# du seuil, contre 10 % pre-inscrits) et RETIREE. Le test verifie donc maintenant qu elle ne
# mord PLUS — sinon un test perime contredirait le verdict du certificateur.
print("\n  P5 — LA PORTE A 0,63 EST RETIREE (falsifiee sur Arma 3 le 03/09)")
pb = torch.full((1, 6), 0.50)                       # 50 % pour une cible entierement visible
vv = torch.tensor([[0.60, 0.62, 0.629, 0.631, 0.70, 1.00]])
r = CANAL.tir(pb, vv)
print("    visible %s" % [round(x, 3) for x in vv[0].tolist()])
print("    p_tir   %s" % [round(x, 4) for x in r[0].tolist()])
print("    PORTE_VISIBLE = %s" % CANAL.PORTE_VISIBLE)
ok["P5"] = (CANAL.PORTE_VISIBLE is False) and bool((r[0][:3] > 0).all())

# ⛔ P6 A CHANGE DE SENS LE 03/09. Il verifiait le CARRE de RV1. L exposant a ete MESURE sur
# Arma 3 (18 181 coups, 16 duels) : a = 0,72, IC95 [0,39 ; 0,97] — 2 est hors de l intervalle.
# Le test verifie donc l exposant MESURE, et refuse explicitement de revenir au carre.
print("\n  P6 — L EXPOSANT DU COUVERT EST CELUI MESURE SUR ARMA 3, PAS LE CARRE DE RV1")
r1 = float(CANAL.tir(torch.tensor([[0.5]]), torch.tensor([[1.0]])))
r7 = float(CANAL.tir(torch.tensor([[0.5]]), torch.tensor([[0.70]])))
print("    p(visible=1,00) = %.4f · p(visible=0,70) = %.4f · rapport %.3f  (mesure = %.3f, carre RV1 = %.3f)"
      % (r1, r7, r7 / r1, 0.70 ** CANAL.VIS_EXPOSANT, 0.70 ** 2))
a = CANAL.VIS_EXPOSANT
lo, hi = CANAL.VIS_EXPOSANT_IC
print("    exposant en service %.2f  IC95 [%.2f ; %.2f]  (RV1 postulait 2)" % (a, lo, hi))
ok["P6"] = (abs(r7 / r1 - 0.70 ** a) < 1e-6) and (lo <= a <= hi) and not (lo <= 2.0 <= hi)

print("\n  P7 — LE PLANCHER A 0,05 COUPE")
pb2 = torch.tensor([[0.05, 0.08, 0.12, 0.30]])      # p pour cible entierement visible
r2 = CANAL.tir(pb2, torch.full_like(pb2, 0.70))     # x0,49
print("    p_entier %s -> p_tir %s (0,05*0,49=%.4f < 0,05 : coupe)"
      % ([round(x, 2) for x in pb2[0].tolist()], [round(x, 4) for x in r2[0].tolist()], 0.05 * 0.49))
ok["P7"] = bool(r2[0][0] == 0) and bool(r2[0][-1] > 0)

print("\n  P8 — LE DOUBLON EST REFUSE (`feu_sur_connu` et `feu_de_zone`)")
ok["P8"] = True
for cle in ("feu_sur_connu", "feu_de_zone"):
    try:
        AssaultTerrain(**dict(MONDE_ARMA_REPLIQUE, num_envs=8, device="cuda:0", seed=1,
                              replica_path=REP, canal_cwr=cst, **{cle: 0.5}))
        print("    ⛔ %s=0.5 a ETE ACCEPTE avec le canal" % cle); ok["P8"] = False
    except ValueError as e:
        print("    ✔ %-14s refuse : %s" % (cle, str(e).split(":")[0][:60]))

print("\n  P9 — LES DEUX HORLOGES : fenetre de 10 s et verrou de 15 s, converties en pas")
e = AssaultTerrain(**dict(MONDE_ARMA_REPLIQUE, num_envs=N, device="cuda:0", seed=GRAINE,
                          replica_path=REP, canal_cwr=cst))
print("    sec_par_pas %.2f -> memoire de tir %d pas (%.0f s) · verrou %d pas (%.0f s)"
      % (e.sec_par_pas, e.canal_mem_pas, CANAL.MEM_TIR_S, e.canal_verrou_pas, CANAL.FIRE_VALID_S))
ok["P9"] = (e.canal_mem_pas == 3 and e.canal_verrou_pas == 5)
if not ok["P9"]:
    print("    (attendu 3 et 5 pour sec_par_pas=3,28 : 10/3,28=3,05 et 15/3,28=4,57)")

print("\n  P10 — LE VERROU TIENT : un defenseur garde-t-il sa cible plusieurs pas ?")
e.reset()
g = torch.Generator(device="cuda:0").manual_seed(GRAINE)
suites = []; prev = None; tenue = torch.zeros(N, e.D, device="cuda:0")
chg = 0; obs = 0
for t in range(PAS):
    acts = torch.randint(0, e.n_actions, (N, e.A), generator=g, device="cuda:0")
    e.step(acts, auto_reset=False)
    cur = e.d_cible.clone()
    if prev is not None:
        vivant = (prev >= 0) & (cur >= 0)
        chg += int((vivant & (prev != cur)).sum()); obs += int(vivant.sum())
    prev = cur
taux = chg / max(obs, 1)
print("    AVEC verrou (%d pas) : %d couples suivis · %d changements (%.1f %%)"
      % (e.canal_verrou_pas, obs, chg, 100.0 * taux))
# ⚠️ LE CONTROLE QUI MANQUAIT. « moins de 50 % » etait une barre choisie, pas un cas connu.
# Le cas connu, c est le MEME monde avec le verrou reduit a un pas : la, le plus proche est
# re-choisi a chaque pas. Le verrou doit faire BAISSER le taux, et c est ca qui se mesure.
e2 = AssaultTerrain(**dict(MONDE_ARMA_REPLIQUE, num_envs=N, device="cuda:0", seed=GRAINE,
                           replica_path=REP, canal_cwr=cst))
e2.canal_verrou_pas = 1
e2.reset()
g2 = torch.Generator(device="cuda:0").manual_seed(GRAINE)
prev2 = None; chg2 = 0; obs2 = 0
for t in range(PAS):
    acts = torch.randint(0, e2.n_actions, (N, e2.A), generator=g2, device="cuda:0")
    e2.step(acts, auto_reset=False)
    cur2 = e2.d_cible.clone()
    if prev2 is not None:
        v2 = (prev2 >= 0) & (cur2 >= 0)
        chg2 += int((v2 & (prev2 != cur2)).sum()); obs2 += int(v2.sum())
    prev2 = cur2
taux2 = chg2 / max(obs2, 1)
print("    SANS verrou (1 pas)  : %d couples suivis · %d changements (%.1f %%)"
      % (obs2, chg2, 100.0 * taux2))
# ⚠️ P10 PEUT ETRE INDECIS, ET IL DOIT SAVOIR LE DIRE. Le verrou ne se mesure que si
# des cibles sont designees ; or la designation est en amont, et elle depend des quatre
# valeurs de `configFile` NON MESUREES. Sous ce seuil de couples suivis, l instrument ne
# discrimine pas — il ne rend donc pas de verdict. On ne desserre PAS la porte pour voir.
MIN_COUPLES = 2000
if min(obs, obs2) < MIN_COUPLES:
    ok["P10"] = None
    print("    INDECIS : %d couples suivis pour %d requis. Le verrou ne se mesure pas tant"
          % (min(obs, obs2), MIN_COUPLES))
    print("    que la designation est affamee par les 4 valeurs de config non lues.")
else:
    ok["P10"] = taux < taux2

print("\n  P11 — ACTIVITE : la loi de tir change-t-elle les degats ?")
base = dict(MONDE_ARMA_REPLIQUE, num_envs=N, device="cuda:0", seed=GRAINE, replica_path=REP)
ea = AssaultTerrain(**base); eb = AssaultTerrain(**dict(base, canal_cwr=cst))
ea.reset(); eb.reset()
g = torch.Generator(device="cuda:0").manual_seed(GRAINE)
da = db = 0.0
for t in range(PAS):
    acts = torch.randint(0, ea.n_actions, (N, ea.A), generator=g, device="cuda:0")
    ea.step(acts.clone(), auto_reset=False); eb.step(acts.clone(), auto_reset=False)
    da += float(ea.last_dmg_in.sum()); db += float(eb.last_dmg_in.sum())
print("    degats cumules : reference %.1f · loi de tir %.1f  (rapport %.3f)"
      % (da, db, db / max(da, 1e-9)))
ok["P11"] = abs(db - da) > 1e-6

print("\n  " + "=" * 62)
for k in sorted(ok, key=lambda x: int(x[1:])):
    print("    %-4s %s" % (k, "INDECIS" if ok[k] is None else ("PASSE" if ok[k] else "ECHOUE")))
print("  " + "=" * 62)
sys.exit(0 if all(v for v in ok.values() if v is not None) else 1)
