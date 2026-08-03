#!/usr/bin/env python3
"""combat_sans_joueur.py — L'IA d'Arma combat-elle SANS joueur connecte ?

Deux notes du projet se contredisent. L'une dit l'IA inerte sans joueur. L'autre, du
20/07, dit l'inverse : « le combat se joue sans joueur connecte — defenseurs qui tombent,
tirs echanges ; setCombatMode RED + LAMBS + nos ordres suffisent ». J'ai passe la soiree
du 26/07 a appliquer la premiere SANS JAMAIS LA TESTER, et j'ai meme ajoute un garde-fou
« 0 joueur = ARRET » dans le banc de suppression.

Si la seconde note dit vrai, Younes n'a plus a rester connecte pour que les mesures
tournent. C'est la difference entre un projet qui avance la nuit et un projet qui attend
quelqu'un.

TROIS BRAS EN MEME TEMPS, memes conditions, meme terrain, zero joueur :
  A  normal              acquisition de cible ACTIVE, aucune revelation
  B  acquisition COUPEE  la configuration exacte de mon banc d'hier — je soupconne que
                         c'est MOI qui rendais les tireurs dependants de sa presence
  C  connaissance forcee acquisition active + reveal mutuel

CANARI OBLIGATOIRE (correction de Fable, et elle me vise) : si mon compteur de tirs est
casse, je conclurai « l'IA est inerte » alors que c'est mon CAPTEUR qui est muet. Donc on
force un tir par script en ouverture. Le compteur doit l'enregistrer. Sinon on ARRETE :
sans capteur prouve, zero tir ne veut rien dire.

SEUILS FIGES AVANT LE RUN :
  ca combat  = au moins 20 tirs cumules ET au moins une perte, sur 5 minutes
  inerte     = zero tir, AVEC canari passe
  entre deux = resultat intermediaire, on rapproche les groupes et on refait
Deux repetitions par bras, pour ne pas conclure sur un coup de des.
"""
import sys, time, json, argparse
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

# ---- ARRET PROPRE (27/07) --------------------------------------------------
# Tuer un banc laisse le pont d'Arma occupe par un client mort : l'extension ne
# detecte pas la socket fermee et garde la place. Il faut DEMANDER l'arret.
#   demander : touch /tmp/hmt_stop     |     reprendre : rm -f /tmp/hmt_stop
import os as _os, signal as _signal


def _arret_demande():
    return _os.path.exists('/tmp/hmt_stop')


_PONTS = []


def _enregistrer_pont(b):
    """tout pont ouvert est note ici pour pouvoir etre ferme quoi qu'il arrive"""
    _PONTS.append(b)
    return b


def _fermer_tout(*_a):
    for _b in _PONTS:
        try:
            _b.close()
        except Exception:
            pass
    raise SystemExit(3)


_signal.signal(_signal.SIGTERM, _fermer_tout)
_signal.signal(_signal.SIGINT, _fermer_tout)
# ---------------------------------------------------------------------------


Q = chr(34); P = chr(37)
LEV = '/home/younes/arma3-marl/leviathan'

ap = argparse.ArgumentParser()
ap.add_argument('--duree', type=int, default=300, help='secondes par repetition')
ap.add_argument('--reps', type=int, default=2)
ap.add_argument('--zone', default='23000,17400')
ap.add_argument('--dx', type=int, default=600, help='ecart entre bras (m)')
ap.add_argument('--dist', type=int, default=100, help='distance entre les deux camps')
ap.add_argument('--n', type=int, default=4, help='hommes par camp')
ap.add_argument('--out', default='combat_sans_joueur.json')
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
zx, zy = [int(v) for v in a.zone.split(',')]

BRAS = [('A_normal', True, False), ('B_acquisition_coupee', False, False), ('C_connaissance_forcee', True, True)]


def _fermer(b):
    """le pont ne parle qu a UN client : sortir sans fermer le rend muet pour tous"""
    try:
        b.close()
    except Exception:
        pass


def poser(b):
    c = ['if (!isNil ' + Q + 'HMT_X' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; '
         'HMT_X = []; HMT_TIRS = [0,0,0]; HMT_MORTS = [0,0,0]; HMT_CANARI = []; '
         '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; ']
    for k, (nom, autotarget, reveler) in enumerate(BRAS):
        K = str(k); bx = zx + k * a.dx
        c.append('private _ge' + K + ' = createGroup east; private _gw' + K + ' = createGroup west; ')
        for i in range(a.n):
            for cote, grp, typ, dy in (('e', '_ge', 'O_Soldier_F', 0), ('w', '_gw', 'B_Soldier_F', a.dist)):
                U = '_u' + cote + K + str(i)
                POS = '[' + str(bx + i * 12) + ',' + str(zy + dy) + ',0]'
                c.append(
                    'private ' + U + ' = ' + grp + K + ' createUnit [' + Q + typ + Q + ', ' + POS + ', [], 0, ' + Q + 'NONE' + Q + ']; '
                    + U + ' setPosATL ' + POS + '; ' + U + ' setSkill 0.5; '
                    + U + ' setBehaviour ' + Q + 'COMBAT' + Q + '; ' + U + ' setCombatMode ' + Q + 'RED' + Q + '; '
                    + U + ' disableAI ' + Q + 'PATH' + Q + '; '
                    + ('' if autotarget else U + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; ')
                    + U + ' addEventHandler [' + Q + 'Fired' + Q + ', { HMT_TIRS set [' + K + ', (HMT_TIRS select ' + K + ') + 1] }]; '
                    + U + ' addEventHandler [' + Q + 'Killed' + Q + ', { HMT_MORTS set [' + K + ', (HMT_MORTS select ' + K + ') + 1] }]; '
                    'HMT_X pushBack ' + U + '; ')
                if i == 0 and cote == 'e':
                    c.append('HMT_CANARI pushBack ' + U + '; ')
        if reveler:
            c.append('{ private _u = _x; { _u reveal [_x, 4] } forEach (units _gw' + K + ') } forEach (units _ge' + K + '); '
                     '{ private _u = _x; { _u reveal [_x, 4] } forEach (units _ge' + K + ') } forEach (units _gw' + K + '); ')
    c.append('(format [' + Q + 'POSE ' + P + '1 ' + P + '2' + Q + ', count HMT_X, count allPlayers]) call HMT_EMIT;')
    return b.query(''.join(c), r'POSE (\d+) (\d+)', want=1, timeout=120)


def canari(b):
    """PROUVER LE CAPTEUR avant de prouver l absence. Sans ca, zero tir ne veut rien dire."""
    b.send('{ _x setVehicleAmmo 1; _x forceWeaponFire [currentMuzzle _x, currentWeaponMode _x] } forEach HMT_CANARI;', wait=False)
    time.sleep(4)
    r = b.query('(format [' + Q + 'CAN ' + P + '1' + Q + ', (HMT_TIRS select 0) + (HMT_TIRS select 1) + (HMT_TIRS select 2)]) call HMT_EMIT;',
                r'CAN (\d+)', want=1, timeout=25)
    return int(r[-1].group(1)) if r else -1


def releve(b):
    r = b.query('(format [' + Q + 'R ' + P + '1|' + P + '2|' + P + '3' + Q + ', HMT_TIRS, HMT_MORTS, count allPlayers]) call HMT_EMIT;',
                r'R \[([\d,]+)\]\|\[([\d,]+)\]\|(\d+)', want=1, timeout=30)
    if not r:
        return None
    tirs = [int(x) for x in r[-1].group(1).split(',')]
    morts = [int(x) for x in r[-1].group(2).split(',')]
    return tirs, morts, int(r[-1].group(3))


if __name__ == '__main__':
    b = _enregistrer_pont(NativeBridge(port=TH.PORT))
    b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;', wait=False)
    time.sleep(2)
    print('=== L IA D ARMA COMBAT-ELLE SANS JOUEUR CONNECTE ? ===', flush=True)
    print('    3 bras en meme temps | %d hommes par camp a %d m | %d repetitions de %d s'
          % (a.n, a.dist, a.reps, a.duree), flush=True)
    print('    seuils figes : combat = >=20 tirs ET >=1 perte | inerte = 0 tir AVEC canari passe', flush=True)

    cumul = {nom: [0, 0] for nom, _, _ in BRAS}
    joueurs_vus = []
    for rep in range(1, a.reps + 1):
        r = poser(b)
        if not r:
            print('  !! mise en place sans reponse — ARRET', flush=True)
            _fermer(b); sys.exit(2)
        n_unites, n_joueurs = int(r[-1].group(1)), int(r[-1].group(2))
        joueurs_vus.append(n_joueurs)
        print('', flush=True)
        print('  repetition %d/%d : %d unites posees, %d joueur(s) connecte(s)'
              % (rep, a.reps, n_unites, n_joueurs), flush=True)
        if n_joueurs > 0:
            print('    !! un joueur est connecte — le test perd tout son sens. ARRET.', flush=True)
            _fermer(b); sys.exit(2)

        nc = canari(b)
        if nc <= 0:
            print('    !! CANARI ECHOUE (%d tir enregistre) : le CAPTEUR est muet.' % nc, flush=True)
            print('       Sans capteur prouve, zero tir ne voudrait rien dire. ARRET.', flush=True)
            _fermer(b); sys.exit(2)
        print('    canari : %d tir(s) enregistre(s) -> le capteur fonctionne' % nc, flush=True)

        t = 0
        while t < a.duree:
            time.sleep(30); t += 30
            v = releve(b)
            if v:
                print('      +%3d s : tirs %s  morts %s' % (t, v[0], v[1]), flush=True)
        v = releve(b)
        b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; '
               '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;', wait=False)
        if v:
            for k, (nom, _, _) in enumerate(BRAS):
                cumul[nom][0] += v[0][k]; cumul[nom][1] += v[1][k]
        time.sleep(3)
    _fermer(b)

    print('', flush=True)
    print('=== RESULTAT (cumul sur %d repetitions, ZERO joueur) ===' % a.reps, flush=True)
    verdicts = {}
    for nom, _, _ in BRAS:
        tirs, morts = cumul[nom]
        if tirs >= 20 and morts >= 1:
            v = 'COMBAT'
        elif tirs == 0:
            v = 'INERTE'
        else:
            v = 'intermediaire'
        verdicts[nom] = {'tirs': tirs, 'morts': morts, 'verdict': v}
        print('  %-24s %5d tirs  %3d morts  -> %s' % (nom, tirs, morts, v), flush=True)

    print('', flush=True)
    va = verdicts['A_normal']['verdict']; vb = verdicts['B_acquisition_coupee']['verdict']
    print('=== CONCLUSION ===', flush=True)
    if va == 'COMBAT':
        print('  >>> L IA COMBAT SANS JOUEUR. Le garde-fou « 0 joueur = ARRET » que j ai', flush=True)
        print('      ajoute hier est FAUX et doit sauter de tous les bancs.', flush=True)
        print('      Younes n a plus a rester connecte : fin des soirees-pile.', flush=True)
        if vb != 'COMBAT':
            print('  >>> ET c est bien MON disableAI AUTOTARGET qui rendait les tireurs', flush=True)
            print('      dependants de sa presence (bras B : %d tirs contre %d en A).'
                  % (verdicts['B_acquisition_coupee']['tirs'], verdicts['A_normal']['tirs']), flush=True)
    elif va == 'INERTE':
        print('  >>> L IA EST BIEN INERTE sans joueur, canari passe. La note du 20/07 ne', flush=True)
        print('      vaut pas dans ce cas de figure. -> passer au client headless.', flush=True)
    else:
        print('  >>> RESULTAT INTERMEDIAIRE : des tirs mais pas de pertes. Rapprocher les', flush=True)
        print('      groupes et refaire avant de conclure quoi que ce soit.', flush=True)

    json.dump({'seuils': '>=20 tirs ET >=1 perte = combat ; 0 tir avec canari passe = inerte',
               'duree_s': a.duree, 'reps': a.reps, 'dist': a.dist, 'n_par_camp': a.n,
               'joueurs_vus': joueurs_vus, 'bras': verdicts},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> ' + LEV + '/' + a.out, flush=True)
    print('SANSJOUEUR_DONE', flush=True)
