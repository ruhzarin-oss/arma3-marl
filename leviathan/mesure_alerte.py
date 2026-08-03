#!/usr/bin/env python3
"""mesure_alerte.py — LA DYNAMIQUE D ALERTE, MESUREE SUR ARMA.

On ne l invente pas : on la mesure. C est l erreur qui a coute deux jours — un mecanisme
plausible, ecrit a la main, qui mentait sur l issue.

Arma tient pour chaque unite un niveau de connaissance de chaque ennemi (knowsAbout, de 0 a 4).
Il monte quand on voit, il monte quand on tire, il se PROPAGE aux voisins du groupe, et il
retombe avec le temps. Quatre questions, quatre mesures :

  Q1  ETAT DE REPOS      : que sait la position d un attaquant approchant en silence ?
  Q2  COUT D UN TIR      : de combien un seul tir fait-il monter la connaissance, et chez QUI ?
  Q3  PORTEE DE L ALERTE : jusqu a quelle distance le voisin est-il reveille ?
  Q4  DECROISSANCE       : en combien de temps ca retombe si on cesse ?

Lecture seule cote monde : on pose des unites, on observe, on ne pilote aucune politique.
"""
import sys, time, json
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis')
Q = chr(34)
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


# --- pose : 8 defenseurs en ligne sur l objectif, 1 attaquant a 200 m ---
pose = (
    'if (!isNil %sHMT_AL%s) then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
    'HMT_AL=[]; HMT_DEF=[]; '
    'private _gd = createGroup east; '
    % (Q, Q))
for i in range(8):
    pose += ('private _d%d = _gd createUnit [%sO_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
             '_d%d setPosATL [%d,%d,0]; _d%d setSkill 0.5; _d%d setBehaviour %sCOMBAT%s; '
             '_d%d setCombatMode %sRED%s; _d%d disableAI %sPATH%s; _d%d allowDamage false; '
             'HMT_AL pushBack _d%d; HMT_DEF pushBack _d%d; '
             % (i, Q, Q, fx + (i - 4) * 25, fy, Q, Q, i, fx + (i - 4) * 25, fy, i, i, Q, Q,
                i, Q, Q, i, Q, Q, i, i, i))
pose += ('private _ga = createGroup west; '
         'HMT_ATT = _ga createUnit [%sB_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
         'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.5; HMT_ATT setBehaviour %sCOMBAT%s; '
         'HMT_ATT setCombatMode %sBLUE%s; HMT_ATT disableAI %sPATH%s; HMT_ATT allowDamage false; '
         'HMT_ATT disableAI %sAUTOTARGET%s; HMT_AL pushBack HMT_ATT; '
         % (Q, Q, fx, fy - 200, Q, Q, fx, fy - 200, Q, Q, Q, Q, Q, Q, Q, Q))
pose += '(format [%sPRET %%1%s, count HMT_DEF]) call HMT_EMIT;' % (Q, Q)

print('pose :', 'OK' if q(pose, r'PRET (\d+)', 90) else 'MUET')

LIRE = ('private _s = %s%s; { _s = _s + format [%s%%1,%s, round ((_x knowsAbout HMT_ATT) * 100)] } '
        'forEach HMT_DEF; (format [%sK %%1%s, _s]) call HMT_EMIT;' % (Q, Q, Q, Q, Q, Q))


def connaissance():
    r = q(LIRE, r'K ([\d,]+)')
    if not r:
        return None
    return [int(x) / 100.0 for x in r.group(1).rstrip(',').split(',') if x != '']


print()
print('=== Q1 — ETAT DE REPOS : attaquant a 200 m, silencieux ===')
for t in (0, 5, 10):
    if t:
        time.sleep(5)
    k = connaissance()
    print('  t=%2ds  connaissance par defenseur : %s' % (t, ['%.2f' % x for x in k] if k else 'MUET'))

print()
print('=== Q2/Q3 — COUT D UN TIR : le defenseur central tire une fois ===')
b.send('HMT_ATT reveal [(HMT_DEF select 4), 0.2]; (HMT_DEF select 4) doWatch HMT_ATT; '
       '(HMT_DEF select 4) doTarget HMT_ATT; (HMT_DEF select 4) doFire HMT_ATT;', wait=False)
for t in (2, 5, 10, 20, 40):
    time.sleep(2 if t == 2 else (3 if t == 5 else (5 if t == 10 else (10 if t == 20 else 20))))
    k = connaissance()
    if k:
        print('  t=%2ds  centre %.2f | voisins 25m %.2f/%.2f | 50m %.2f/%.2f | bouts 100m %.2f/%.2f'
              % (t, k[4], k[3], k[5], k[2], k[6], k[0], k[7]))

print()
print('=== Q4 — DECROISSANCE : plus rien ne se passe ===')
for t in (60, 90, 120):
    time.sleep(20 if t == 60 else 30)
    k = connaissance()
    if k:
        print('  t=%3ds  centre %.2f | moyenne position %.2f' % (t, k[4], sum(k) / len(k)))

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('MESURE_ALERTE_DONE')
