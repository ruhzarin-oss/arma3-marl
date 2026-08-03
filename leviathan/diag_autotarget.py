#!/usr/bin/env python3
"""diag_autotarget.py — est-ce MOI qui bride le tireur ?

0,2 balle/s, c est trop peu pour mesurer. Suspect : j ai coupe l acquisition de cible
(AUTOTARGET) pour isoler les duels, et une IA sans acquisition n entretient peut-etre
pas son tir.

Deux bras, duel isole, memes conditions :
  A. AUTOTARGET coupe  (ce que fait le banc aujourd hui)
  B. AUTOTARGET actif  (l IA engage normalement)

Et on prepare la parade qui rendra l isolement inutile : l impact n est compte que si
sa SOURCE est le tireur apparie. Le tir croise devient alors inoffensif, et on peut
serrer les duels au lieu de chercher des kilometres de terrain plat.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
TH = theatre.use('altis')
zx, zy, D, DUREE = 23000, 18400, 100, 40


def poser(b, dx, autotarget):
    T = '[' + str(zx + dx) + ',' + str(zy) + ',0]'
    C = '[' + str(zx + dx) + ',' + str(zy + D) + ',0]'
    coupe = '' if autotarget else '_t disableAI ' + Q + 'AUTOTARGET' + Q + '; '
    c = ('if (!isNil ' + Q + 'HMT_D' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D }; '
         'HMT_D = []; HMT_S = 0; HMT_H = 0; HMT_HA = 0; HMT_TQ = -9; '
         'private _g = createGroup east; '
         'private _t = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
         '_t setPosATL ' + T + '; _t setSkill 0.5; _t setUnitPos ' + Q + 'UP' + Q + '; '
         '_t setBehaviour ' + Q + 'COMBAT' + Q + '; _t setCombatMode ' + Q + 'RED' + Q + '; '
         '_t disableAI ' + Q + 'PATH' + Q + '; ' + coupe +
         '_t setVehicleAmmo 1; '
         '_t addEventHandler [' + Q + 'Fired' + Q + ', { HMT_S = HMT_S + 1 }]; '
         'private _h = createGroup west; '
         'private _c = _h createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
         '_c setPosATL ' + C + '; _c setUnitPos ' + Q + 'DOWN' + Q + '; '
         '_c disableAI ' + Q + 'PATH' + Q + '; _c disableAI ' + Q + 'AUTOTARGET' + Q + '; _c disableAI ' + Q + 'TARGET' + Q + '; '
         '_c setBehaviour ' + Q + 'CARELESS' + Q + '; '
         # HMT_HA = tous les impacts ; HMT_H = seulement ceux du tireur apparie
         '_c addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
         '  if (diag_tickTime - HMT_TQ > 0.05) then { HMT_TQ = diag_tickTime; HMT_HA = HMT_HA + 1; '
         '    if ((_this select 3) == HMT_TT) then { HMT_H = HMT_H + 1 } }; 0 }]; '
         'HMT_D pushBack _t; HMT_D pushBack _c; HMT_TT = _t; HMT_CC = _c; '
         'HMT_TT reveal [HMT_CC, 4]; HMT_TT doTarget HMT_CC; '
         '(format [' + Q + 'PRET ' + P + '1' + Q + ', count HMT_D]) call HMT_EMIT;')
    return b.query(c, r'PRET (\d+)', want=1, timeout=60)


def tirer_et_relever(b):
    n = 0
    while n < DUREE:
        b.send('HMT_TT reveal [HMT_CC, 4]; HMT_TT doTarget HMT_CC; HMT_TT doFire HMT_CC;')
        time.sleep(2); n += 2
    r = b.query('(format [' + Q + 'R ' + P + '1 ' + P + '2 ' + P + '3' + Q + ', HMT_S, HMT_H, HMT_HA]) call HMT_EMIT;',
                r'R (\d+) (\d+) (\d+)', want=1, timeout=30)
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D; HMT_D = [];')
    return (int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))) if r else (0, 0, 0)


b = NativeBridge(port=TH.PORT)
b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0;')
time.sleep(1)
print('=== acquisition de cible : coupee vs active | ' + str(DUREE) + ' s, cible COUCHEE a ' + str(D) + ' m ===', flush=True)

poser(b, 0, False); time.sleep(3)
sa, ha, _ = tirer_et_relever(b)
print('  A  acquisition COUPEE : ' + str(sa) + ' balles, ' + str(ha) + ' impacts', flush=True)
time.sleep(2)
poser(b, 600, True); time.sleep(3)
sb, hb, _ = tirer_et_relever(b)
print('  B  acquisition ACTIVE : ' + str(sb) + ' balles, ' + str(hb) + ' impacts', flush=True)
b.close()

print('', flush=True)
for lab, s, h in (('A', sa, ha), ('B', sb, hb)):
    print('  ' + lab + ' : ' + (('%.0f' % (100.0 * h / s)) if s else '--') + ' pour cent au but  (' +
          ('%.2f' % (s / float(DUREE))) + ' balles/s)', flush=True)
if sb > 1.8 * max(sa, 1):
    print('\n>>> C EST MOI QUI BRIDAIS : rendre l acquisition, et isoler par la SOURCE de l impact.', flush=True)
elif sa > 0 and abs(sb - sa) <= 0.3 * sa:
    print('\n>>> l acquisition n y est pour rien : la lenteur vient d ailleurs (cadence propre a l IA).', flush=True)
    print('    -> il faudra multiplier les duels en parallele, pas accelerer chacun.', flush=True)
else:
    print('\n>>> resultat ambigu, a refaire avec plus de duree.', flush=True)
print('AUTO_DONE', flush=True)
