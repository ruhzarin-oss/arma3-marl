#!/usr/bin/env python3
"""LE CHANGEMENT EST-IL ACTIF ? On le prouve AVANT de payer un entrainement.

Premiere version RATEE, et c'est le smoke-test qui l'a dit : les attaquants qui
« supprimaient » restaient plantes a 170 m, hors de la portee de 110 m. Zero degat recu
parce que personne n'etait A PORTEE, pas parce que le parametre agissait. Je mesurais la
distance.

Version corrigee : la MEME sequence d'actions dans les trois mondes — on avance d'abord
jusqu'a etre a portee, PUIS toute l'escouade supprime. Seul `supp_residuel` change.

  1. NON-REGRESSION  supp_residuel=None doit reproduire l'ancien monde a l'identique.
  2. L'EFFET EXISTE  0.08 doit laisser passer des degats la ou l'ancien monde en laissait
                     passer zero.
  3. LE SENS EST BON supprimer doit encore proteger — moins qu'avant, pas plus.
"""
import sys
import torch

sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

N, APPROCHE, ARROSAGE = 256, 8, 10
COMMUN = dict(num_envs=N, device="cuda:0", seed=7)


def joue(arrose=True, **kw):
    """Meme scenario partout : on avance jusqu'a portee, puis on arrose (ou non).
    On ne compte les degats QUE pendant la phase d'arrosage — avant, tout le monde
    est logé a la meme enseigne et ca noierait l'effet."""
    torch.manual_seed(7)
    e = AssaultTerrain(**COMMUN, **kw)
    e.reset()
    dev = e.apx.device
    for _ in range(APPROCHE):                      # action 0 = avancer vers l'objectif
        e.step(torch.zeros((N, e.A), dtype=torch.long, device=dev))
    recu, dsupp_moy = 0.0, 0.0
    for _ in range(ARROSAGE):
        a = torch.full((N, e.A), 9 if arrose else 0, dtype=torch.long, device=dev)
        e.step(a)
        recu += float(e.last_dmg_in.sum())
        dsupp_moy += float((e.dsupp > 0.5).float().mean())
    return recu / N, dsupp_moy / ARROSAGE


print("=== LA COURBE N2 EST-ELLE ACTIVE DANS LE SANDBOX ? ===", flush=True)
print("    %d pas d'approche, puis %d pas d'arrosage ; degats comptes sur l'arrosage seul"
      % (APPROCHE, ARROSAGE), flush=True)
print("", flush=True)
anc, s_anc = joue()
print("  ancien monde   (tout ou rien)   degats %.4f   (part de defenseurs supprimes %.2f)" % (anc, s_anc), flush=True)
neu, s_neu = joue(supp_residuel=0.08)
print("  monde mesure   (8 %% residuel)   degats %.4f   (part de defenseurs supprimes %.2f)" % (neu, s_neu), flush=True)
per, s_per = joue(supp_residuel=0.08, supp_persist=0.35)
print("  + persistance  (report 0,35)    degats %.4f   (part de defenseurs supprimes %.2f)" % (per, s_per), flush=True)
plaf, _ = joue(arrose=False)
print("  personne n'arrose (plafond)     degats %.4f" % plaf, flush=True)

print("", flush=True)
ok = True
if s_neu < 0.01:
    print("  [X] la suppression elle-meme est a ZERO : personne n'est a portee.", flush=True)
    print("      Le test ne prouve rien — corriger le scenario avant de conclure.", flush=True)
    ok = False
if neu <= anc + 1e-9:
    print("  [X] le residuel ne laisse RIEN passer de plus que l'ancien monde", flush=True)
    print("      -> parametre inerte, NE PAS LANCER D'ENTRAINEMENT", flush=True)
    ok = False
else:
    print("  [ok] le defenseur supprime tire ENCORE : %.4f contre %.4f (+%.0f %%)"
          % (neu, anc, 100.0 * (neu - anc) / max(anc, 1e-9)), flush=True)
if plaf > 1e-9:
    if neu >= plaf:
        print("  [X] arroser ne protege plus du tout — le sens est inverse", flush=True)
        ok = False
    else:
        print("  [ok] arroser protege encore : %.0f %% des degats du monde sans arrosage"
              % (100.0 * neu / plaf), flush=True)
if per < neu - 1e-9:
    print("  [ok] la persistance protege un peu plus (%.4f < %.4f)" % (per, neu), flush=True)
elif abs(per - neu) < 1e-9:
    print("  [!] la persistance ne change RIEN : a verifier avant de s'en servir", flush=True)
print("", flush=True)
print("VERDICT : %s" % ("changement ACTIF, on peut entrainer" if ok else "changement NON PROUVE, on ne lance rien"), flush=True)
print("FUMEE_DONE", flush=True)


# --- LA PERSISTANCE NE SE VOIT QU'APRES UN CESSEZ-LE-FEU ---------------------
# Le test ci-dessus arrose sans interruption :  est reecrit a chaque pas, donc le
# report est toujours ecrase par la valeur fraiche et n'a aucun effet visible. C'est
# attendu, pas un bug — mais tant qu'on ne l'a pas EXERCE, on ne sait pas s'il marche.
# Arma dit : apres l'arret du feu, l'adversaire retrouve ~89 % de sa cadence en 2 s, pour
# un pas de sandbox de 3,28 s. C'est ce repit-la qu'on mesure ici.
def cessez_le_feu(**kw):
    torch.manual_seed(7)
    e = AssaultTerrain(**COMMUN, **kw)
    e.reset()
    dev = e.apx.device
    for _ in range(APPROCHE):
        e.step(torch.zeros((N, e.A), dtype=torch.long, device=dev))
    for _ in range(8):                                   # on arrose
        e.step(torch.full((N, e.A), 9, dtype=torch.long, device=dev))
    recu = 0.0
    for _ in range(3):                                   # PUIS on se tait
        e.step(torch.zeros((N, e.A), dtype=torch.long, device=dev))
        recu += float(e.last_dmg_in.sum())
    return recu / N

print('', flush=True)
print('=== APRES LE CESSEZ-LE-FEU (3 pas) : le repit existe-t-il ? ===', flush=True)
sans = cessez_le_feu(supp_residuel=0.08)
avec = cessez_le_feu(supp_residuel=0.08, supp_persist=0.35)
print('  sans report   degats recus %.4f' % sans, flush=True)
print('  report 0,35   degats recus %.4f' % avec, flush=True)
if avec < sans - 1e-9:
    print('  [ok] le repit se voit dans les degats : -%.0f %%'
          % (100.0 * (sans - avec) / max(sans, 1e-9)), flush=True)
else:
    print('  [.] pas visible dans les degats agreges — seuls ~6 %% des defenseurs sont sous', flush=True)
    print('      le feu a un instant donne, l effet est reel mais noye. On verifie donc la', flush=True)
    print('      VARIABLE directement, seule preuve qui vaille ici :', flush=True)

# PREUVE DIRECTE. Les degats agreges sont trop grossiers pour trancher : on regarde dsupp
# lui-meme, avant et apres le cessez-le-feu. C'est la seule mesure qui isole le report.
def sonde_reste(pers):
    torch.manual_seed(7)
    e = AssaultTerrain(num_envs=64, device='cuda:0', seed=7, supp_residuel=0.08, supp_persist=pers)
    e.reset(); dev = e.apx.device
    for _ in range(8): e.step(torch.zeros((64, e.A), dtype=torch.long, device=dev))
    for _ in range(6): e.step(torch.full((64, e.A), 9, dtype=torch.long, device=dev))
    avant = float(e.dsupp.max())
    e.step(torch.zeros((64, e.A), dtype=torch.long, device=dev))
    return avant, float(e.dsupp.max())

a0, b0 = sonde_reste(0.0)
a1, b1 = sonde_reste(0.35)
print('      report 0,00 : suppression %.3f sous le feu -> %.3f au pas suivant' % (a0, b0), flush=True)
print('      report 0,35 : suppression %.3f sous le feu -> %.3f au pas suivant' % (a1, b1), flush=True)
if b1 > b0 + 1e-6:
    print('  [ok] le repit AGIT sur la variable : la suppression survit d un pas.', flush=True)
else:
    print('  [X] le repit est INERTE — ne pas s en servir.', flush=True)
print('PERSIST_DONE', flush=True)
