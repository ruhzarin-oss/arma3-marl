#!/usr/bin/env python3
"""sonde_actionneur.py — le gel vient-il de NOTRE COMMANDE ou DU MOTEUR ?

Criteres : CRITERES_SONDE_ACTIONNEUR.md (d23e6537ee7140c9). Refuse de demarrer si le fichier a bouge.

Six cases : trois mecanismes de feu x deux postures. Deux phases : sans opposition (isole la
locomotion) puis avec opposition (verifie qu il tire). La case jamais testee est 1B — un homme
qu on EMPECHE de s arreter mais qu on LAISSE tirer.

Usage : sonde_actionneur.py --theatre ferme0 [--reps 3] [--pas 60]
"""
import argparse, hashlib, json, math, os, sys, time

sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import theatre
from native_bridge import NativeBridge

LEV = '/home/younes/arma3-marl/leviathan'
CRIT = os.path.join(LEV, 'CRITERES_SONDE_ACTIONNEUR.md')
ATTENDU = 'd23e6537ee7140c9'
emp = hashlib.sha256(open(CRIT, 'rb').read()).hexdigest()[:16]
if emp != ATTENDU:
    sys.exit('REFUS : criteres modifies (%s au lieu de %s).' % (emp, ATTENDU))

ap = argparse.ArgumentParser()
ap.add_argument('--theatre', default='ferme0')
ap.add_argument('--reps', type=int, default=3)
ap.add_argument('--pas', type=int, default=60)
ap.add_argument('--nag', type=int, default=8)
a = ap.parse_args()
T = theatre.use(a.theatre)
FX, FY = T.FOB
SX, SY = T.spawn_for(dist=140.0)

FEUX = {0: 'jamais', 1: 'natif', 2: 'suppressif'}
POSTURES = {0: 'libre', 1: 'forcee'}

# --- l actionneur parametre. Ecrit UNE fois, applique a chaque pas. ---
ACTIONNEUR = (
    'HMT_TIRS = 0; '
    'HMT_SONDE = { params ["_feu", "_pos", "_bouger"]; '
    '  { if (alive _x) then { '
    '      if (_pos == 1) then { _x setUnitPos "UP"; _x forceSpeed 100 } '
    '                     else { _x setUnitPos "AUTO"; _x forceSpeed -1 }; '
    # ORDRE DE DEPLACEMENT RARE. Bug du 31/07 : je le reemettais a chaque pas, soit toutes les
    # 1,1 s. L IA recalculait son chemin en boucle et avancait a 1,1 m/s alors qu on lui forcait
    # la vitesse maximale — elle n avait jamais le temps d executer l ordre recu. La sonde
    # echouait alors son propre controle positif.
    '      if (_bouger == 1) then { _x doMove [%d, %d, 0] }; '
    '      if (_feu == 0) then { _x disableAI "AUTOTARGET"; _x setCombatMode "BLUE" } '
    '                    else { _x enableAI "AUTOTARGET"; _x setCombatMode "RED" }; '
    '      if (_feu == 2) then { '
    '          private _e = _x findNearestEnemy (getPosATL _x); '
    '          if (!isNull _e) then { _x doTarget _e; _x doSuppressiveFire _e }; '
    '      }; '
    '  } } forEach HMT_SP; };' % (FX, FY))


def spawn_sqf(n):
    """Attaquants WEST, avec un compteur de tirs pose sur chacun."""
    return (
        'if (!isNil "HMT_SP") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_SP }; '
        'HMT_SP = []; HMT_TIRS = 0; HMT_GS = createGroup west; '
        'for "_i" from 1 to %d do { '
        '  private _px = %d + (random 40) - 20; private _py = %d + (random 30) - 15; '
        '  private _u = HMT_GS createUnit ["B_Soldier_F", [_px, _py, 0], [], 0, "NONE"]; '
        '  _u setPosATL [_px, _py, 0]; _u setSkill 0.5; _u setBehaviour "COMBAT"; '
        '  _u enableSimulation true; _u enableDynamicSimulation false; '
        '  _u setVehicleAmmo 1; '
        '  _u addEventHandler ["Fired", { HMT_TIRS = HMT_TIRS + 1 }]; '
        '  HMT_SP pushBack _u; }; '
        '(format ["SPAWN %%1", count HMT_SP]) call HMT_EMIT;' % (n, SX, SY))


ETAT = ('private _v = HMT_SP select { alive _x }; '
        'private _d = 9999; { private _q = getPosATL _x; '
        '  private _dd = sqrt (((_q select 0) - %d)^2 + ((_q select 1) - %d)^2); '
        '  if (_dd < _d) then { _d = _dd } } forEach _v; '
        '(format ["ETAT %%1 %%2 %%3", count _v, round _d, HMT_TIRS]) call HMT_EMIT;' % (FX, FY))


def un_essai(b, feu, pos, oppose):
    b.query(spawn_sqf(a.nag), r'SPAWN (\d+)', want=1, timeout=90)
    b.send(ACTIONNEUR, wait=True, timeout=30)
    d_min = 9999
    tirs = 0
    vivants = a.nag
    for pas in range(a.pas):
        # l ordre de deplacement n est reemis que tous les cinq pas
        b.send('[%d, %d, %d] call HMT_SONDE;' % (feu, pos, 1 if pas % 5 == 0 else 0),
               wait=False)
        time.sleep(1.1)
        if pas % 3 == 0 or pas == a.pas - 1:
            r = b.query(ETAT, r'ETAT (\d+) (\d+) (\d+)', want=1, timeout=15)
            if r:
                vivants = int(r[-1].group(1))
                d_min = min(d_min, int(r[-1].group(2)))
                tirs = int(r[-1].group(3))
                if vivants == 0 or d_min < 15:
                    break
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_SP; HMT_SP = [];', wait=False)
    time.sleep(1.5)
    return {'d_min': d_min, 'tirs': tirs, 'vivants': vivants}


print('=== SONDE D ACTIONNEUR — %s (criteres %s) ===' % (a.theatre, ATTENDU))
print('  objectif %d,%d | depart %d,%d | A=%d | %d pas | n=%d par case'
      % (FX, FY, SX, SY, a.nag, a.pas, a.reps))
res = {}
for oppose in (False, True):
    phase = 'AVEC OPPOSITION' if oppose else 'SANS OPPOSITION'
    print()
    print('--- PHASE %s ---' % phase)
    if oppose:
        os.system('cd %s && HMT_THEATRE=%s timeout 180 python3 poser_fob.py 8 >/dev/null 2>&1'
                  % (LEV, a.theatre))
    print('  %-12s %-8s %10s %8s %10s' % ('feu', 'posture', 'dist min', 'tirs', 'survivants'))
    for feu in (0, 1, 2):
        for pos in (0, 1):
            ess = []
            for _ in range(a.reps):
                b = NativeBridge(port=T.PORT, timeout=20)
                try:
                    ess.append(un_essai(b, feu, pos, oppose))
                finally:
                    b.close()
                time.sleep(1)
            dm = sum(e['d_min'] for e in ess) / len(ess)
            ti = sum(e['tirs'] for e in ess) / len(ess)
            vi = sum(e['vivants'] for e in ess) / len(ess)
            res[(oppose, feu, pos)] = {'d_min': dm, 'tirs': ti, 'vivants': vi,
                                       'franchit': sum(1 for e in ess if e['d_min'] < 25)}
            print('  %-12s %-8s %10.0f %8.0f %10.1f  (%d/%d franchissent)'
                  % (FEUX[feu], POSTURES[pos], dm, ti, vi,
                     res[(oppose, feu, pos)]['franchit'], len(ess)))

print()
print('=== CONTROLE POSITIF — la sonde reproduit-elle un comportement CONNU ? ===')
# La case << jamais / forcee >> EST l executeur temeraire, qui prend l objectif 73 a 87 % du temps
# dans le vrai banc. Si elle ne franchit pas ici, la sonde ne reproduit pas ce qu on sait deja, et
# elle ne peut rien dire de ce qu on ignore. Bug du 31/07 : j ai lu son verdict sans ce controle.
_tem = res.get((False, 0, 1))
_ok_pos = _tem is not None and _tem['franchit'] >= max(1, a.reps - 1)
print('  temeraire (jamais / forcee) sans opposition : %d/%d franchissent, distance min %.0f m'
      % (_tem['franchit'] if _tem else -1, a.reps, _tem['d_min'] if _tem else -1))
if not _ok_pos:
    print('  >>> LA SONDE EST NULLE. Elle ne reproduit pas un comportement connu ; aucun verdict')
    print('      ne peut en etre tire. Chercher la cause dans la sonde, pas dans le moteur.')
    json.dump({'%s|%d|%d' % (k[0], k[1], k[2]): v for k, v in res.items()},
              open(os.path.join(LEV, 'sonde_actionneur.json'), 'w'), indent=1)
    print('SONDE_ACTIONNEUR_NULLE')
    sys.exit(3)
print('  >>> controle positif VERT : la sonde reproduit le connu, on peut lire l inconnu.')
print()
print('=== LECTURE (criteres figes) ===')
admissibles = []
for feu in (0, 1, 2):
    for pos in (0, 1):
        s = res.get((False, feu, pos))
        o = res.get((True, feu, pos))
        if not s or not o:
            continue
        c1 = s['franchit'] == a.reps
        c2 = (feu == 0) or (o['tirs'] >= 10)
        nom = '%s / %s' % (FEUX[feu], POSTURES[pos])
        print('  %-24s franchit %s | tire %s'
              % (nom, 'OUI' if c1 else 'NON (%d/%d)' % (s['franchit'], a.reps),
                 'OUI (%.0f)' % o['tirs'] if c2 else 'NON (%.0f)' % o['tirs']))
        if c1 and c2 and feu != 0:
            admissibles.append(nom)
print()
if admissibles:
    print('  ADMISSIBLES a tir non nul : %s' % ', '.join(admissibles))
    print('  >>> le gel vient de NOTRE COMMANDE. Les doctrines emettront des INTENTIONS et le')
    print('      moteur resoudra la locomotion, haltes de visee comprises — qui redeviennent')
    print('      alors un fait du monde et non notre script.')
else:
    print('  AUCUNE case a tir non nul ne franchit.')
    print('  >>> le gel est une propriete DU MOTEUR. Il entre au registre comme contrainte du')
    print('      monde, et la doctrine correcte devient « tirer depuis un couvert » : defaut de')
    print('      nos DOCTRINES, pas de nos actionneurs.')
json.dump({'%s|%d|%d' % (k[0], k[1], k[2]): v for k, v in res.items()},
          open(os.path.join(LEV, 'sonde_actionneur.json'), 'w'), indent=1)
print('SONDE_ACTIONNEUR_DONE')
