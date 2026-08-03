#!/usr/bin/env python3
"""qui.py — qui est reellement sur ce serveur, et a quel stade ?

"Connecte au serveur" et "entre dans la mission" sont deux choses differentes :
tant qu'un joueur reste au lobby (choix de slot), `allPlayers` est vide et l'IA
reste inerte. On distingue les deux au lieu de supposer.
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)
q = ('private _n = ' + Q + Q + '; { _n = _n + (name _x) + ' + Q + '/' + Q + ' } forEach allPlayers; '
     '(format [' + Q + 'Q joueurs=' + P + '1 unites=' + P + '2 west=' + P + '3 noms=' + P + '4 mission=' + P + '5' + Q +
     ', count allPlayers, count allUnits, playersNumber west, _n, missionName]) call HMT_EMIT;')
r = b.query(q, r'Q joueurs=(\d+) unites=(\d+) west=(\d+) noms=(\S*) mission=(\S*)', want=1, timeout=25)
b.close()
if not r:
    print('PAS DE REPONSE'); sys.exit(1)
j, u, w, noms, mis = r[-1].groups()
print('mission      : ' + mis)
print('allPlayers   : ' + j + '   (joueurs ENTRES dans la mission)')
print('playersNumber west : ' + w + '   (clients connectes cote WEST, lobby compris)')
print('unites       : ' + u)
print('noms         : ' + (noms if noms.strip('/') else '(aucun)'))
print()
if int(j) > 0:
    print('>>> tu es DANS la mission : la mesure peut tourner.')
elif int(w) > 0:
    print('>>> tu es connecte mais RESTE AU LOBBY : choisis un slot et clique OK/Continuer.')
    print('    Tant que tu n as pas pris de personnage, l IA d Arma ne bouge pas.')
else:
    print('>>> personne sur ce serveur : verifie que tu es bien sur MELTEMI (port 3912),')
    print('    et non sur un autre serveur du meme poste.')
