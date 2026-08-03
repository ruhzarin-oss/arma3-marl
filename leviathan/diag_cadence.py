#!/usr/bin/env python3
"""diag_cadence.py — comment faire tirer assez de balles pour que la mesure vaille ?

12 balles en 45 s, c est trop peu : la courbe reposerait sur du bruit. Deux suspects,
donc deux bras compares dans les MEMES conditions :

  A. doFire seul, munitions donnees UNE FOIS  — soupcon : mon setVehicleAmmo chaque
     seconde declenchait un rechargement qui interrompait le tir
  B. forceWeaponFire a cadence imposee        — on commande chaque coup, l IA ne fait
     que viser ; la cadence devient un parametre et non un alea

On garde le bras qui donne assez de balles SANS deformer le taux de touche.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
TH = theatre.use('altis')
zx, zy, D, DUREE = 23000, 18400, 100, 40


def poser(b, dx):
    T = '[' + str(zx + dx) + ',' + str(zy) + ',0]'
    C = '[' + str(zx + dx) + ',' + str(zy + D) + ',0]'
    c = ('if (!isNil ' + Q + 'HMT_D' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D }; '
         'HMT_D = []; HMT_S = 0; HMT_H = 0; HMT_TQ = -9; '
         'private _g = createGroup east; '
         'private _t = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
         '_t setPosATL ' + T + '; _t setSkill 0.5; _t setUnitPos ' + Q + 'UP' + Q + '; '
         '_t setBehaviour ' + Q + 'COMBAT' + Q + '; _t setCombatMode ' + Q + 'RED' + Q + '; '
         '_t disableAI ' + Q + 'PATH' + Q + '; _t disableAI ' + Q + 'AUTOTARGET' + Q + '; '
         '_t setVehicleAmmo 1; '
         '_t addEventHandler [' + Q + 'Fired' + Q + ', { HMT_S = HMT_S + 1 }]; '
         'private _h = createGroup west; '
         'private _c = _h createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
         '_c setPosATL ' + C + '; _c setUnitPos ' + Q + 'DOWN' + Q + '; '
         '_c disableAI ' + Q + 'PATH' + Q + '; _c disableAI ' + Q + 'AUTOTARGET' + Q + '; _c disableAI ' + Q + 'TARGET' + Q + '; '
         '_c setBehaviour ' + Q + 'CARELESS' + Q + '; '
         '_c addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
         '  if (diag_tickTime - HMT_TQ > 0.05) then { HMT_TQ = diag_tickTime; HMT_H = HMT_H + 1 }; 0 }]; '
         'HMT_D pushBack _t; HMT_D pushBack _c; HMT_TT = _t; HMT_CC = _c; '
         'HMT_TT reveal [HMT_CC, 4]; HMT_TT doTarget HMT_CC; '
         '(format [' + Q + 'PRET ' + P + '1' + Q + ', count HMT_D]) call HMT_EMIT;')
    return b.query(c, r'PRET (\d+)', want=1, timeout=60)


def relever(b):
    r = b.query('(format [' + Q + 'R ' + P + '1 ' + P + '2' + Q + ', HMT_S, HMT_H]) call HMT_EMIT;',
                r'R (\d+) (\d+)', want=1, timeout=30)
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D; HMT_D = [];')
    return (int(r[-1].group(1)), int(r[-1].group(2))) if r else (0, 0)


b = NativeBridge(port=TH.PORT)
b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0;')
time.sleep(1)
print('=== cadence de tir : 2 bras, ' + str(DUREE) + ' s chacun, cible COUCHEE a ' + str(D) + ' m ===', flush=True)

# --- bras A : doFire seul, munitions donnees une seule fois ---
poser(b, 0); time.sleep(3)
n = 0
while n < DUREE:
    b.send('HMT_TT doTarget HMT_CC; HMT_TT doFire HMT_CC;')
    time.sleep(2); n += 2
sa, ha = relever(b)
print('  A  doFire seul          : ' + str(sa) + ' balles, ' + str(ha) + ' impacts', flush=True)
time.sleep(2)

# --- bras B : cadence imposee, un coup commande toutes les 0,4 s ---
poser(b, 600); time.sleep(4)   # 4 s pour que l IA ait le temps de VISER avant le 1er coup
n = 0.0
while n < DUREE:
    b.send('HMT_TT forceWeaponFire [currentMuzzle HMT_TT, currentWeaponMode HMT_TT];')
    time.sleep(0.4); n += 0.4
sb, hb = relever(b)
print('  B  cadence imposee      : ' + str(sb) + ' balles, ' + str(hb) + ' impacts', flush=True)
b.close()

print('', flush=True)
for lab, s, h in (('A', sa, ha), ('B', sb, hb)):
    if s > 0:
        print('  ' + lab + ' : ' + ('%.0f' % (100.0 * h / s)) + ' pour cent au but  (' +
              ('%.1f' % (s / float(DUREE))) + ' balles/s)', flush=True)
    else:
        print('  ' + lab + ' : aucun tir', flush=True)
if sb >= 3 * max(sa, 1) and sa > 0 and abs(100.0*hb/max(sb,1) - 100.0*ha/max(sa,1)) < 15:
    print('\n>>> GARDER B : beaucoup plus de balles, meme taux de touche.', flush=True)
elif sb > sa:
    print('\n>>> B tire plus, mais le taux DIFFERE — verifier que l IA a le temps de viser.', flush=True)
else:
    print('\n>>> garder A.', flush=True)
print('CADENCE_DONE', flush=True)
