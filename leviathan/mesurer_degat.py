#!/usr/bin/env python3
"""mesurer_degat.py — CHANTIER 1 : que vaut UN impact ?

Le sandbox accumule des DEGATS (mort a 0.7), pas des impacts. Convertir la courbe de
toucher en degats demande donc de savoir ce que retire une balle. C'est le troisieme
nombre de la conversion, et le dernier qui manquait.

On le lit a la source : le gestionnaire de degats d'Arma recoit la valeur infligee
(_this select 2). On la releve au lieu de la jeter — la cible reste invulnerable
(on renvoie 0), donc chaque valeur est bien l'effet d'UNE balle et pas un cumul.

On mesure a plusieurs distances : une balle ralentie par 200 m d'air ne frappe pas
comme a bout portant.
"""
import sys, time, json
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

def _fermer(b):
    """Le pont ne parle qu a UN client : sortir sans fermer le rend muet
    pour tout le monde jusqu au redemarrage du serveur."""
    try:
        b.close()
    except Exception:
        pass

Q = chr(34); P = chr(37)
LEV = '/home/younes/arma3-marl/leviathan'
TH = theatre.use('altis')
zx, zy = 23000, 17400
DISTANCES = [25, 100, 200]
DUREE = 70

b = NativeBridge(port=TH.PORT)
b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
time.sleep(2)

c = ['if (!isNil ' + Q + 'HMT_G' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_G }; '
     'HMT_G = []; HMT_TIR = []; HMT_CIB = []; HMT_DG = []; HMT_NB = []; HMT_TQ = []; ']
for k, d in enumerate(DISTANCES):
    K = str(k)
    tx = zx + k * 300
    T = '[' + str(tx) + ',' + str(zy) + ',0]'
    C = '[' + str(tx) + ',' + str(zy + d) + ',0]'
    c.append(
        'HMT_DG pushBack 0; HMT_NB pushBack 0; HMT_TQ pushBack -9; '
        'private _g' + K + ' = createGroup east; '
        'private _t' + K + ' = _g' + K + ' createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
        '_t' + K + ' setPosATL ' + T + '; _t' + K + ' setSkill 0.5; _t' + K + ' setUnitPos ' + Q + 'UP' + Q + '; '
        '_t' + K + ' setBehaviour ' + Q + 'COMBAT' + Q + '; _t' + K + ' setCombatMode ' + Q + 'RED' + Q + '; '
        '_t' + K + ' disableAI ' + Q + 'PATH' + Q + '; _t' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
        '_t' + K + ' allowDamage false; _t' + K + ' setVehicleAmmo 1; '
        'private _h' + K + ' = createGroup west; '
        'private _c' + K + ' = _h' + K + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
        '_c' + K + ' setPosATL ' + C + '; _c' + K + ' setUnitPos ' + Q + 'UP' + Q + '; '
        '_c' + K + ' disableAI ' + Q + 'PATH' + Q + '; _c' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
        '_c' + K + ' disableAI ' + Q + 'TARGET' + Q + '; _c' + K + ' setBehaviour ' + Q + 'CARELESS' + Q + '; '
        '_c' + K + ' addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
        '  if (diag_tickTime - (HMT_TQ select ' + K + ') > 0.05) then { '
        '    HMT_TQ set [' + K + ', diag_tickTime]; '
        '    if ((_this select 3) == (HMT_TIR select ' + K + ')) then { '
        '      HMT_DG set [' + K + ', (HMT_DG select ' + K + ') + (_this select 2)]; '
        '      HMT_NB set [' + K + ', (HMT_NB select ' + K + ') + 1] } }; 0 }]; '
        'HMT_G pushBack _t' + K + '; HMT_G pushBack _c' + K + '; '
        'HMT_TIR pushBack _t' + K + '; HMT_CIB pushBack _c' + K + '; ')
c.append('(format [' + Q + 'PRET ' + P + '1' + Q + ', count HMT_CIB]) call HMT_EMIT;')
r = b.query(''.join(c), r'PRET (\d+)', want=1, timeout=90)
print('duels poses : ' + (r[-1].group(1) if r else 'ECHEC'), flush=True)
if not r:
    _fermer(b)
    sys.exit(1)
time.sleep(3)
n = 0
while n < DUREE:
    b.send('{ private _c = HMT_CIB select _forEachIndex; _x reveal [_c, 4]; _x doTarget _c; _x doFire _c; } forEach HMT_TIR;')
    time.sleep(2); n += 2
q = ('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1/' + P + '2;' + Q +
     ', _x, HMT_NB select _forEachIndex] } forEach HMT_DG; '
     '(format [' + Q + 'DG ' + P + '1' + Q + ', _o]) call HMT_EMIT;')
rr = b.query(q, r'DG (.*)', want=1, timeout=30)
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_G; HMT_G = []; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
b.close()
if not rr:
    print('pas de reponse'); sys.exit(1)

print('', flush=True)
print('=== DEGAT INFLIGE PAR UNE BALLE (fusil 6,5 mm, mort a 1.0) ===', flush=True)
res = {}
vals = []
for d, t in zip(DISTANCES, rr[-1].group(1).strip().rstrip(';').split(';')):
    if '/' not in t:
        continue
    tot, nb = t.split('/')
    try:
        tot = float(tot); nb = int(nb)
    except ValueError:
        continue
    m = tot / nb if nb else None
    res[str(d)] = m
    if m:
        vals.append(m)
    print('  %4d m : %s   (%d impacts)' % (d, ('%.3f' % m) if m else '--', nb), flush=True)

al = []
if len(vals) < len(DISTANCES):
    al.append('des distances sans impact')
if any(v <= 0.0 or v > 1.5 for v in vals):
    al.append('une valeur hors du plausible (0-1.5)')
print('', flush=True)
if al:
    print('[!] MESURE SUSPECTE :', flush=True)
    for x in al: print('    - ' + x, flush=True)
else:
    moy = sum(vals) / len(vals)
    print('[ok] moyenne : %.3f de degat par impact' % moy, flush=True)
    print('     -> il faut environ %.1f impacts pour neutraliser (seuil sandbox 0.7)' % (0.7 / moy), flush=True)
    print('     degat_par_impact = %.3f' % moy, flush=True)
json.dump({'distances': DISTANCES, 'degat_par_impact': res, 'alertes': al},
          open(LEV + '/courbe_degat.json', 'w'), indent=1)
print('-> ' + LEV + '/courbe_degat.json', flush=True)
print('DEGAT_DONE', flush=True)
