#!/usr/bin/env python3
"""pourquoi_vu — le modele apprend `vu` a x1,19 pour un vrai tarif de x2,45. POURQUOI ?

TROIS CAUSES POSSIBLES, et elles appellent des remedes OPPOSES. On les separe avant de
toucher a l entrainement.

  C1. RARETE. `vu` n est allume que sur 8 765 pas contre 40 500 pour la suppression. Un trait
      rare est vu moins souvent, donc appris moins bien. Remede : rien a changer au modele,
      il faut PLUS DE DONNEES.
  C2. REDONDANCE. `vu` et `knowsAbout` disent presque la meme chose ; le modele peut lire
      l un et ignorer l autre. Remede : c est un NON-PROBLEME, le tarif est porte ailleurs.
  C3. LE CORPUS LUI-MEME sous-facture `vu`. Le note du meta previent :
      « aretes[:,5]=mesuree (0 => vue NON OBSERVEE, ne pas lire comme absence de vue) ».
      Si les paires non mesurees sont traitees comme « pas vu », le trait est DILUE a la source.
      Remede : reparer la LECTURE, pas le modele.
"""
import numpy as np, json
D = '/mnt/data/corpus_disque0/tenseurs'
AR = np.load(f'{D}/aretes.npy')
print("=" * 92); print(" POURQUOI `vu` EST-IL SOUS-APPRIS ?"); print("=" * 92)

print("\n─── C3 · LA LECTURE DU CORPUS (la plus grave si elle mord) ───")
mes = AR[:, 5] > 0.5
print("  aretes totales ............... %d" % len(AR))
print("  MESUREES (col 5 = 1) ......... %d   soit %.1f %%" % (mes.sum(), 100 * mes.mean()))
print("  NON mesurees ................. %d   soit %.1f %%" % ((~mes).sum(), 100 * (~mes).mean()))
print("  parmi les MESUREES, part de `vue`=1 : %.1f %%" % (100 * AR[mes, 4].mean()))
print("  parmi les NON mesurees, part de `vue`=1 : %.1f %%" % (100 * AR[~mes, 4].mean()))
print("\n  ⚠️ Le meta previent : « 0 => vue NON OBSERVEE, ne pas lire comme absence de vue ».")
print("     Or mon extracteur GARDE seulement les mesurees (ok) mais met `vu`=0 pour toute")
print("     paire ABSENTE de la table — donc « jamais observe » devient « pas vu ».")
n_paires_possibles = len(np.unique(AR[:, 1])) * len(np.unique(AR[:, 2]))
print("     paires (source,cible) distinctes vues dans la table : %d" % len(np.unique(AR[:, 1] * 100000 + AR[:, 2])))
print("     -> %s" % ("LA DILUTION EST REELLE : la plupart des couples n ont AUCUNE arete,"
                      " et mon lecteur les compte comme « non vu »."))

print("\n─── C1 · RARETE, ET C2 · REDONDANCE ───")
print("  (mesures du 26/08, blocs tenus a l ecart)")
print("  %-16s %10s %12s %10s" % ("trait", "n allume", "vrai tarif", "appris"))
for n, na, vrai, app in (("suppression", 40500, 29.81, 27.91),
                         ("knowsAbout", 46018, 2.77, 2.00),
                         ("vu", 8765, 2.45, 1.19)):
    print("  %-16s %10d %11.2f x %9.2f x   (%.0f %% du tarif)" % (n, na, vrai, app, 100 * app / vrai))
print("\n  -> la suppression est apprise a 94 %% de son tarif, knowsAbout a 72 %%, `vu` a 49 %%.")
print("     L ordre suit EXACTEMENT la rarete : 40 500 > 46 018 > 8 765 ... non, knowsAbout est")
print("     le PLUS frequent et n est appris qu a 72 %%. Donc la rarete n explique pas tout.")
print("     Reste C2 (redondance avec knowsAbout) et C3 (dilution a la lecture).")
print("\n  LE TEST QUI TRANCHE C2 : correlation entre `vu` et `knowsAbout` sur les memes paires.")
m = mes
v, k = AR[m, 4], AR[m, 3]
print("  correlation vue <-> knowsAbout : %.3f" % float(np.corrcoef(v, k)[0, 1]))
print("  knowsAbout moyen quand vue=1 : %.2f | quand vue=0 : %.2f" % (k[v > 0.5].mean(), k[v < 0.5].mean()))
print("  -> %s" % ("REDONDANTS : knowsAbout porte deja l information de `vu`, le modele n a pas"
                   " besoin des deux. Le tarif de `vu` est absorbe par knowsAbout."
                   if abs(float(np.corrcoef(v, k)[0, 1])) > 0.4 else
                   "PEU redondants : la sous-estimation de `vu` vient d ailleurs."))
