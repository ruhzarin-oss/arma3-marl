#!/usr/bin/env python3
"""POURQUOI LE DEFENSEUR NE RIPOSTE-T-IL PAS ? Version elementaire.

La premiere sonde utilisait , qui n'existe pas dans cette version : erreur
SQF, aucun emit, et un diagnostic muet. On ne pose plus que des questions elementaires,
et rien que des nombres.
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre
Q = chr(34)
b = NativeBridge(port=theatre.use('altis').PORT)
print('=== POURQUOI PAS DE RIPOSTE ? ===', flush=True)
q = ('private _o = ' + Q + Q + '; '
     '{ private _d = _x; private _a = HMT_ATT select 0; '
     '  _o = _o + format [' + Q + '%1/%2/%3/%4/%5;' + Q + ', '
     '    (if (alive _d) then {1} else {0}), '
     '    (if (someAmmo _d) then {1} else {0}), '
     '    round (100 * (_d knowsAbout _a)), '
     '    (if (isNull (currentTarget _d)) then {0} else {1}), '
     '    round (_d distance _a)]; '
     '} forEach HMT_DEF; (format [' + Q + 'D %1' + Q + ', _o]) call HMT_EMIT;')
rr = b.query(q, r'D (.*)', want=1, timeout=30)
if rr:
    print('  vivant / a des munitions / connaissance x100 / a une cible / distance', flush=True)
    for i, t in enumerate(rr[-1].group(1).strip().rstrip(';').split(';')):
        if t.strip():
            print('    def %d : %s' % (i, t), flush=True)
else:
    print('  pas de reponse : la requete elle-meme a echoue', flush=True)
b.close()
print('SONDE_FIN', flush=True)
