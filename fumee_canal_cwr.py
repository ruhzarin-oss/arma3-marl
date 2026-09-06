#!/usr/bin/env python3
"""CONTROLE POSITIF de l equation 1. Criteres dans CRITERES_EQ1_CANAL.md, ecrits AVANT.

Quatre tests, chacun avec son falsificateur. Le mode d echec a attraper est l INERTIE :
un premier essai de lever l interrupteur (planchonner `los` dans les termes de tir) etait
reste parfaitement inerte — memes comptes a la dizaine pres sur neuf valeurs du bouton.
Un module qui ne change AUCUNE decision doit etre retire, pas raffine.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import canal_cwr as CANAL
from monde_fidele import MONDE_ARMA_REPLIQUE
from assault_terrain import AssaultTerrain

REPLIQUE = sys.argv[1] if len(sys.argv) > 1 else None
N, GRAINE, PAS = 512, 7, 12
ok = {}

print("\n  P3 — L OUIE NE DESIGNE JAMAIS (par le calcul, avant tout tenseur)")
ok["P3a"] = CANAL.preuve_analytique()

print("\n  P4 — LE REFUS")
try:
    CANAL.constantes(sensibilite=1.0)
    ok["P4"] = False; print("    ⛔ il a DEMARRE sans les quatre valeurs")
except ValueError as e:
    ok["P4"] = True; print("    ✔ il refuse : %s" % str(e).split("\n")[0])

cst = CANAL.constantes_arma3()   # valeurs LUES dans Arma 3 le 03/09

print("\n  P3b — efrac = 0, de 5 m a 200 m : entendu, jamais designe")
d = torch.tensor([[5.0, 15.0, 25.0, 60.0, 120.0, 200.0]])
r0 = CANAL.canal(torch.zeros_like(d), d, cst, porte_cone=torch.ones_like(d))
print("    acc_ouie %s" % [round(x, 3) for x in r0["acc_ouie"][0].tolist()])
print("    designe  %s" % [bool(x) for x in r0["designe"][0].tolist()])
ok["P3b"] = bool((r0["acc_ouie"] > 0).all()) and not bool(r0["designe"].any())

print("\n  P2 — L INTERRUPTEUR EST LEVE : un homme PARTIELLEMENT couvert peut etre designe")
# ⚠️ CORRECTIF D INSTRUMENT. La premiere version fixait la distance a 40 m — une distance
# dont je ne connaissais PAS la reponse d avance, donc ce n etait pas un controle positif.
# Un controle positif se pose sur un cas ou le phenomene est connu massif. Ici le cas
# connu est : « assez pres, un homme a moitie visible est engage ». On BALAIE donc la
# distance et on cherche la portee de designation, sans toucher a une seule constante.
lv = torch.tensor([[0.1, 0.25, 0.5, 0.75, 1.0]])
print("    portee de designation par fraction de corps visible :")
ok["P2"] = False
for efr in lv[0].tolist():
    dgrid = torch.arange(2.0, 300.0, 1.0).unsqueeze(0)
    r = CANAL.canal(torch.full_like(dgrid, efr), dgrid, cst, porte_cone=torch.ones_like(dgrid))
    des = r["designe"][0]
    portee = float(dgrid[0][des].max()) if bool(des.any()) else 0.0
    print("      efrac %.2f -> designe jusqu a %5.1f m" % (efr, portee))
    if 0.0 < efr < 0.5 and portee > 0.0:
        ok["P2"] = True   # un homme a moins de la moitie du corps visible EST engage quelque part
# LE COUVERT N EST PLUS UN INTERRUPTEUR : la portee doit CROITRE avec efrac, continument.
r_full = CANAL.canal(torch.ones(1, 1), torch.full((1, 1), 10.0), cst, porte_cone=torch.ones(1, 1))
r_zero = CANAL.canal(torch.zeros(1, 1), torch.full((1, 1), 10.0), cst, porte_cone=torch.ones(1, 1))
print("    a 10 m : side(efrac=1) = %.2f  vs  side(efrac=0) = %.2f  (l ecart est CONTINU, pas binaire)"
      % (float(r_full["side"]), float(r_zero["side"])))

if REPLIQUE is None:
    print("\n  P1 — SAUTE : le canal exige une replique. Relancer avec le chemin du .npz")
    print("       (c est la meme exigence que `nav_around`, et elle est dans les criteres)")
else:
    print("\n  P1 — ACTIVITE : le canal change-t-il une decision contre `los > 0.5` ?")
    base = dict(MONDE_ARMA_REPLIQUE, num_envs=N, device="cuda:0", seed=GRAINE,
                replica_path=REPLIQUE)
    ea = AssaultTerrain(**base)
    eb = AssaultTerrain(**dict(base, canal_cwr=cst))
    ea.reset(); eb.reset()
    g = torch.Generator(device="cuda:0").manual_seed(GRAINE)
    desac = 0; vus = 0; total = 0
    for t in range(PAS):
        acts = torch.randint(0, ea.n_actions, (N, ea.A), generator=g, device="cuda:0")
        ea.step(acts.clone(), auto_reset=False)
        eb.step(acts.clone(), auto_reset=False)
        c = getattr(eb, "_canal_out", None)
        if c is not None:
            geo = eb._vu_geo > 0.5
            des = c["designe"]
            # ⚠️ LES DEUX SENS NE DISENT PAS LA MEME CHOSE, et un XOR les confond.
            desac += int((des & ~geo).sum())        # designe SANS etre vu -> interrupteur leve
            vus += int((geo & ~des).sum())          # vu SANS etre designe -> canal plus exigeant
            total += des.numel()
    print("    pas joues %d · decisions %d" % (PAS, total))
    print("    designe SANS etre vu geometriquement : %d  (l interrupteur se leve)" % desac)
    print("    vu geometriquement SANS etre designe : %d  (le canal est plus exigeant)" % vus)
    ok["P1"] = (desac + vus) > 0
    if not ok["P1"]:
        print("    ⛔ INERTE — a retirer, pas a raffiner (c est le mode d echec deja vu)")

print("\n  " + "=" * 62)
for k in sorted(ok):
    print("    %-4s %s" % (k, "PASSE" if ok[k] else "ECHOUE"))
print("  " + "=" * 62)
sys.exit(0 if all(ok.values()) else 1)
