#!/usr/bin/env python3
"""etat.py — l'etat du serveur en une ligne : joueurs, monde, groupes.

A lancer par fichier et non en ligne inline : le passage par ssh mange les guillemets
et le script echoue en silence (constate le 26/07 — sortie vide, aucune erreur).
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)
q = ('(format [' + Q + 'E joueurs=' + P + '1 monde=' + P + '2 taille=' + P + '3 groupes=' + P + '4 unites=' + P + '5' + Q +
     ', count allPlayers, worldName, worldSize, count allGroups, count allUnits]) call HMT_EMIT;')
r = b.query(q, r'E joueurs=(\d+) monde=(\S+) taille=(\d+) groupes=(\d+) unites=(\d+)', want=1, timeout=25)
b.close()
if not r:
    print('PAS DE REPONSE du serveur'); sys.exit(1)
n = int(r[-1].group(1))
print(r[-1].group(0))
# MESURE 27/07 : l IA combat SANS joueur (117 et 406 tirs, canari passe).
# Le nombre de joueurs est une INFORMATION, pas une condition. Ne plus en faire un echec.
print('  -> ' + ('%d joueur(s) present(s)' % n if n else 'aucun joueur — sans importance, l IA combat quand meme'))
sys.exit(0)
