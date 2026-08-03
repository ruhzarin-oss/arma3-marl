#!/usr/bin/env python3
"""diag_compteurs.py — UN seul duel, et on regarde ce que chaque compteur raconte.

La calibration donnait 183 impacts pour 100 balles : impossible. Plutot que de deviner
lequel des deux compteurs ment, on isole un duel et on compte tout en parallele : les
tirs, TOUS les appels du gestionnaire de degats, et seulement ceux du corps entier.
L ecart entre les trois designe le coupable.

(NB : ne jamais formater ces chaines avec % en Python — le SQF utilise %1, %2… )
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34)
TH = theatre.use('altis')
zx, zy, D = 23000, 18400, 100
b = NativeBridge(port=TH.PORT)
b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0;')
time.sleep(1)

T = '[' + str(zx) + ',' + str(zy) + ',0]'
C = '[' + str(zx) + ',' + str(zy + D) + ',0]'
c = ('if (!isNil ' + Q + 'HMT_D' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D }; '
     'HMT_D = []; HMT_S = 0; HMT_TOUS = 0; HMT_CORPS = 0; HMT_DEDUP = 0; HMT_TQ = -9; HMT_SEL = []; '
     'private _g = createGroup east; '
     'private _t = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
     '_t setPosATL ' + T + '; _t setSkill 0.5; _t setUnitPos ' + Q + 'UP' + Q + '; '
     '_t setBehaviour ' + Q + 'COMBAT' + Q + '; _t setCombatMode ' + Q + 'RED' + Q + '; '
     '_t disableAI ' + Q + 'PATH' + Q + '; _t disableAI ' + Q + 'AUTOTARGET' + Q + '; '
     '_t addEventHandler [' + Q + 'Fired' + Q + ', { HMT_S = HMT_S + 1 }]; '
     'private _h = createGroup west; '
     'private _c = _h createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
     '_c setPosATL ' + C + '; _c setUnitPos ' + Q + 'DOWN' + Q + '; '
     '_c disableAI ' + Q + 'PATH' + Q + '; _c disableAI ' + Q + 'AUTOTARGET' + Q + '; _c disableAI ' + Q + 'TARGET' + Q + '; '
     '_c setBehaviour ' + Q + 'CARELESS' + Q + '; '
     '_c addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
     '  HMT_TOUS = HMT_TOUS + 1; '
     '  if (diag_tickTime - HMT_TQ > 0.05) then { HMT_TQ = diag_tickTime; HMT_DEDUP = HMT_DEDUP + 1 }; '
     '  if ((_this select 1) == ' + Q + Q + ') then { HMT_CORPS = HMT_CORPS + 1 }; '
     '  if (count HMT_SEL < 12) then { HMT_SEL pushBack ((_this select 1) + ' + Q + '|' + Q + ' + str (_this select 5)) }; '
     '  0 }]; '
     'HMT_D pushBack _t; HMT_D pushBack _c; HMT_TT = _t; HMT_CC = _c; '
     '(format [' + Q + 'PRET ' + chr(37) + '1' + Q + ', count HMT_D]) call HMT_EMIT;')

r = b.query(c, r'PRET (\d+)', want=1, timeout=60)
print('duel unique a ' + str(D) + ' m, cible COUCHEE : ' + ('pose' if r else 'ECHEC'), flush=True)
if not r:
    sys.exit(1)
time.sleep(2)
# ordre relance chaque SECONDE : a 5 s d intervalle l IA s arretait (6 balles en 15 s)
for k in range(45):
    b.send('HMT_TT setVehicleAmmo 1; HMT_TT reveal [HMT_CC, 4]; HMT_TT doTarget HMT_CC; HMT_TT doFire HMT_CC;')
    time.sleep(1)
P = chr(37)
rr = b.query('(format [' + Q + 'R tirs=' + P + '1 tous=' + P + '2 corps=' + P + '3 dedup=' + P + '5 ech=' + P + '4' + Q +
             ', HMT_S, HMT_TOUS, HMT_CORPS, HMT_SEL, HMT_DEDUP]) call HMT_EMIT;',
             r'R tirs=(\d+) tous=(\d+) corps=(\d+) dedup=(\d+) ech=(.*)', want=1, timeout=30)
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D; HMT_D = [];')
b.close()
if not rr:
    print('pas de reponse'); sys.exit(1)
tirs, tous, corps, dedup = (int(rr[-1].group(i)) for i in (1,2,3,4))
print('  balles tirees             : ' + str(tirs), flush=True)
print('  appels degats (TOUS)      : ' + str(tous), flush=True)
print('  appels degats (corps seul): ' + str(corps), flush=True)
print('  impacts DEDUPLIQUES       : ' + str(dedup), flush=True)
print('  echantillon selection|idx : ' + rr[-1].group(5), flush=True)
print('', flush=True)
if tirs == 0:
    print('>>> LE TIREUR NE TIRE PAS : c est le compteur de tirs (ou l ordre de feu) le probleme.', flush=True)
elif dedup > tirs:
    print('>>> LE COMPTEUR D IMPACTS ment : ' + ('%.1f' % (dedup / float(tirs))) + ' appels corps par balle.', flush=True)
    print('    -> un impact declenche plusieurs appels ; il faut dedupliquer.', flush=True)
else:
    print('>>> compteurs coherents : ' + str(dedup) + ' impacts / ' + str(tirs) + ' balles = ' +
          ('%.0f' % (100.0 * dedup / tirs)) + ' pour cent', flush=True)
print('DIAG_DONE', flush=True)
