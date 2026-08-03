#!/usr/bin/env python3
"""sonde_suppression.py — la commande getSuppression repond-elle, oui ou non ?

Le banc de suppression reste bloque sur sa premiere seance : 7 minutes pour 60 secondes
de mesure. Les trois envois sont pourtant passes en mode direct. Il reste deux endroits
possibles : le releve de suppression, et le releve final.

On teste chacun ISOLEMENT, avec un delai court, pour voir lequel ne repond pas — au lieu
d'attendre 15 secondes dix fois de suite sans savoir pourquoi.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)


def essai(nom, sqf, motif, timeout=8):
    t0 = time.time()
    r = b.query(sqf, motif, want=1, timeout=timeout)
    dt = time.time() - t0
    print('  %-34s %-18s (%.1f s)' % (nom, (r[-1].group(0)[:40] if r else 'PAS DE REPONSE'), dt), flush=True)
    return bool(r)


print('=== quelles commandes repondent ? ===', flush=True)
essai('1. le pont lui-meme', '(format [' + Q + 'A ' + P + '1' + Q + ', round diag_tickTime]) call HMT_EMIT;', r'A (\d+)')

# une unite pour tester getSuppression dessus
b.send('if (!isNil ' + Q + 'HMT_Z' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_Z }; '
       'HMT_Z = []; private _g = createGroup east; '
       'private _u = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', [23000,17400,0], [], 0, ' + Q + 'NONE' + Q + ']; '
       '_u setPosATL [23000,17400,0]; HMT_Z pushBack _u; HMT_UZ = _u;', wait=False)
time.sleep(4)
essai('2. l unite existe', '(format [' + Q + 'B ' + P + '1' + Q + ', count HMT_Z]) call HMT_EMIT;', r'B (\d+)')
essai('3. getSuppression brut', '(format [' + Q + 'C ' + P + '1' + Q + ', getSuppression HMT_UZ]) call HMT_EMIT;', r'C (\S+)')
essai('4. getSuppression x1000 arrondi',
      '(format [' + Q + 'D ' + P + '1' + Q + ', round (1000 * getSuppression HMT_UZ)]) call HMT_EMIT;', r'D (-?\d+)')
essai('5. la requete EXACTE du banc',
      'private _s = 0; { _s = _s + (getSuppression _x) } forEach HMT_Z; '
      '(format [' + Q + 'DEC ' + P + '1' + Q + ', round (1000 * _s / (count HMT_Z max 1))]) call HMT_EMIT;', r'DEC (\d+)')
essai('6. le releve final du banc (forme)',
      'HMT_SHOTS = [3]; HMT_HITS = [1]; HMT_SUP = [0.5]; HMT_NECH = 2; '
      'private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1/' + P + '2/' + P + '3;' + Q +
      ', _x, HMT_HITS select _forEachIndex, round (1000 * (HMT_SUP select _forEachIndex) / (HMT_NECH max 1))] } forEach HMT_SHOTS; '
      '(format [' + Q + 'RES ' + P + '1' + Q + ', _o]) call HMT_EMIT;', r'RES (.*)')

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_Z; HMT_Z = []; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;', wait=False)
time.sleep(2)
b.close()
print('', flush=True)
print('>>> la premiere ligne SANS reponse designe le coupable.', flush=True)
