#!/usr/bin/env python3
"""nettoyer.py — enleve TOUT ce qu'un banc a pu laisser derriere lui.

Tuer un banc en cours de route laisse ses unites en place : invulnerables, en combat,
et plus personne pour leur dire d'arreter. Elles tirent indefiniment et finissent par
etrangler le serveur — c'est ce qui a rendu le pont muet deux fois le 26/07.

A lancer avant et apres tout banc, et systematiquement apres un arret force.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)
b.send('{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; '
       '{ deleteMarker _x } forEach (allMapMarkers select { (_x find ' + Q + 'hmt' + Q + ') == 0 });')
time.sleep(4)
r = b.query('(format [' + Q + 'N unites=' + P + '1 groupes=' + P + '2 marqueurs=' + P + '3' + Q +
            ', count allUnits, count allGroups, count allMapMarkers]) call HMT_EMIT;',
            r'N unites=(\d+) groupes=(\d+) marqueurs=(\d+)', want=1, timeout=25)
b.close()
print(r[-1].group(0) if r else 'PAS DE REPONSE — le serveur est deja bloque, il faut le relancer')
