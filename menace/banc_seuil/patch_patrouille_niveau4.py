"""Le niveau 4 de la menace de phase 2 ( patrouille motorisee seule, posee pres ) a ete ajoute a 35_menaces.sqf ( 16e4b32 ) mais pas a 30_opfor.sqf :
au palier leger le vehicule de route n est cree que pour les niveaux 1 et 3, donc au niveau 4 AUCUNE menace n existe ( fumee de P2, 19/09 ).
Usage : python3 patch_patrouille_niveau4.py --racine <dossier du banc>"""
import sys
B = sys.argv[sys.argv.index("--racine") + 1]; P = f"{B}/mission.Altis/chacal/30_opfor.sqf"
s = open(P, encoding="utf-8").read()
a = "    if (CHACAL_LEGER && { !(CHACAL_MENACE_P2 in [1, 3]) }) exitWith {};"
assert s.count(a) == 1, s.count(a)
open(P, "w", encoding="utf-8").write(s.replace(a, "    if (CHACAL_LEGER && { !(CHACAL_MENACE_P2 in [1, 3, 4]) }) exitWith {};   // 4 = patrouille seule, posee pres ( oubliee par 16e4b32 )"))
print("patch patrouille niveau 4 applique :", B)
