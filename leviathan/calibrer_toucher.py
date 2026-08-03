#!/usr/bin/env python3
"""calibrer_toucher.py v4 — CHANTIER 1, COURBE N1 : PROBABILITE DE TOUCHER.

Le sandbox invente ce parametre depuis le debut (hit=0.06 partout, plus rien au-dela
de 110 m). C est lui qui a refuse de transferer trois fois. On va le MESURER.

Ce que le banc a appris de ses propres echecs, aujourd hui :
  1. compter les BALLES TIREES autant que les impacts — sans ca on ne distingue pas
     il a rate de il n a pas tire (v1 annoncait 183 impacts pour 100 balles)
  2. DEDUPLIQUER les impacts : une balle declenche 1,9 appel du gestionnaire de degats
     (mesure). On ne compte qu un impact par instant.
  3. n accepter un impact que s il vient du TIREUR APPARIE. Le tir croise devient
     inoffensif, donc les duels peuvent etre serres : 750 x 800 m au lieu de 5 km.
  4. rendre les TIREURS invulnerables : une balle perdue qui tue un tireur arreterait
     son tir et biaiserait sa condition.
  5. ne PAS commander les coups (forceWeaponFire) : la cadence monte x15 mais le taux
     de touche s effondre de 33 a 4 pour cent — on mesurerait le canon, pas le tireur.
  6. l IA tire 0,3-0,4 balle/s quoi qu on fasse. On ne l accelere pas : on multiplie
     les duels et on allonge la seance.
  7. le controle de terrain ABANDONNE quand il echoue (il laissait passer 52 m de
     denivele en continuant comme si de rien n etait).

Grille : 6 distances x 3 postures, les 18 conditions en meme temps.
"""
import sys, time, json, argparse, math
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
ap.add_argument('--duree', type=int, default=240, help='secondes de tir par seance')
ap.add_argument('--reps', type=int, default=3)
ap.add_argument('--skill', type=float, default=0.5)
ap.add_argument('--zone', default='23000,17400')
ap.add_argument('--dx', type=int, default=150, help='ecart lateral entre duels (m)')
ap.add_argument('--dy', type=int, default=300, help='ecart entre rangees (m)')
ap.add_argument('--out', default='courbe_toucher.json')
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
zx, zy = [int(v) for v in a.zone.split(',')]

DISTANCES = [25, 50, 75, 100, 150, 200]
POSTURES = ['UP', 'MIDDLE', 'DOWN']
GRILLE = [(d, p) for p in POSTURES for d in DISTANCES]   # ligne = posture, colonne = distance


def _wilson(k, n, z=1.96):
    """intervalle de confiance de Wilson — honnete meme sur petits effectifs"""
    if n == 0:
        return (0.0, 0.0, 0.0)
    ph = k / float(n); d = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / d
    dem = z * math.sqrt(ph * (1 - ph) / n + z * z / (4.0 * n * n)) / d
    return (ph, max(0.0, cen - dem), min(1.0, cen + dem))


def _ecart_significatif(k1, n1, k2, n2):
    """1 si p1>p2 nettement, -1 si p2>p1 nettement, 0 si indiscernable"""
    if n1 < 5 or n2 < 5:
        return 0
    p1 = k1 / float(n1); p2 = k2 / float(n2)
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    if se <= 0:
        return 0
    z = (p1 - p2) / se
    return 1 if z > 1.96 else (-1 if z < -1.96 else 0)


def cellule(k):
    """tireur et cible de la condition k"""
    i = k % len(DISTANCES); j = k // len(DISTANCES)
    d = DISTANCES[i]
    tx = zx + i * a.dx; ty = zy + j * a.dy
    return (tx, ty), (tx, ty + d)


def terrain_valide(b):
    pts = []
    for k in range(len(GRILLE)):
        t, c = cellule(k); pts.append(t); pts.append(c)
    liste = '[' + ','.join('[' + str(x) + ',' + str(y) + ']' for x, y in pts) + ']'
    q = ('private _bad = 0; private _hmin = 9999; private _hmax = -9999; '
         '{ private _c = _x; if (surfaceIsWater _c) then { _bad = _bad + 1 }; '
         '  if (count (nearestTerrainObjects [[_c select 0, _c select 1, 0], '
         '[' + Q + 'HOUSE' + Q + ',' + Q + 'BUILDING' + Q + ',' + Q + 'TREE' + Q + ',' + Q + 'ROCK' + Q + '], 50]) > 2) '
         'then { _bad = _bad + 1 }; '
         '  private _h = getTerrainHeightASL _c; if (_h < _hmin) then {_hmin=_h}; if (_h > _hmax) then {_hmax=_h}; '
         '} forEach ' + liste + '; '
         '(format [' + Q + 'Z mauvais=' + P + '1 sur=' + P + '2 relief=' + P + '3' + Q +
         ', _bad, count ' + liste + ', round(_hmax-_hmin)]) call HMT_EMIT;')
    r = b.query(q, r'Z mauvais=(\d+) sur=(\d+) relief=(-?\d+)', want=1, timeout=40)
    if not r:
        return None
    return int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))


def marqueurs(b, n):
    """ROUGE = tireurs, BLEU = cibles, VERT = toi. Cree une fois, deplace ensuite."""
    q = ('{ deleteMarker _x } forEach (allMapMarkers select { _x find ' + Q + 'hmtcal' + Q + ' == 0 }); '
         'for [{private _i = 0}, {_i < ' + str(n) + '}, {_i = _i + 1}] do { '
         '  private _mt = createMarker [format [' + Q + 'hmtcal_t' + P + '1' + Q + ', _i], getPos (HMT_TIR select _i)]; '
         '  _mt setMarkerType ' + Q + 'mil_dot' + Q + '; _mt setMarkerColor ' + Q + 'ColorRed' + Q + '; '
         '  private _mc = createMarker [format [' + Q + 'hmtcal_c' + P + '1' + Q + ', _i], getPos (HMT_CIB select _i)]; '
         '  _mc setMarkerType ' + Q + 'mil_dot' + Q + '; _mc setMarkerColor ' + Q + 'ColorBlue' + Q + '; '
         '  _mc setMarkerText format [' + Q + P + '1 m' + Q + ', round ((HMT_TIR select _i) distance (HMT_CIB select _i))]; '
         '}; '
         '{ if (isPlayer _x) then { '
         '  private _mj = createMarker [' + Q + 'hmtcal_joueur' + Q + ', getPos _x]; '
         '  _mj setMarkerType ' + Q + 'mil_dot' + Q + '; _mj setMarkerColor ' + Q + 'ColorGreen' + Q + '; '
         '  _mj setMarkerText ' + Q + 'TOI' + Q + '; } } forEach allUnits;')
    b.send(q)


def seance(b):
    c = ['if (!isNil ' + Q + 'HMT_CAL' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_CAL }; '
         'HMT_CAL = []; HMT_TIR = []; HMT_CIB = []; HMT_SHOTS = []; HMT_HITS = []; HMT_TQ = []; ']
    for k, (d, post) in enumerate(GRILLE):
        (tx, ty), (cx, cy) = cellule(k)
        K = str(k)
        T = '[' + str(tx) + ',' + str(ty) + ',0]'
        C = '[' + str(cx) + ',' + str(cy) + ',0]'
        c.append(
            'HMT_SHOTS pushBack 0; HMT_HITS pushBack 0; HMT_TQ pushBack -9; '
            # --- TIREUR : invulnerable (une balle perdue ne doit pas l arreter) ---
            'private _g' + K + ' = createGroup east; '
            'private _t' + K + ' = _g' + K + ' createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_t' + K + ' setPosATL ' + T + '; _t' + K + ' setSkill ' + ('%.2f' % a.skill) + '; '
            '_t' + K + ' setUnitPos ' + Q + 'UP' + Q + '; _t' + K + ' setBehaviour ' + Q + 'COMBAT' + Q + '; '
            '_t' + K + ' setCombatMode ' + Q + 'RED' + Q + '; '
            '_t' + K + ' disableAI ' + Q + 'PATH' + Q + '; _t' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_t' + K + ' allowDamage false; _t' + K + ' setVehicleAmmo 1; '
            '_t' + K + ' addEventHandler [' + Q + 'Fired' + Q + ', { HMT_SHOTS set [' + K + ', (HMT_SHOTS select ' + K + ') + 1] }]; '
            # --- CIBLE : invulnerable ; impact compte SEULEMENT s il vient de son tireur ---
            'private _h' + K + ' = createGroup west; '
            'private _c' + K + ' = _h' + K + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_c' + K + ' setPosATL ' + C + '; _c' + K + ' setUnitPos ' + Q + post + Q + '; '
            '_c' + K + ' disableAI ' + Q + 'PATH' + Q + '; _c' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_c' + K + ' disableAI ' + Q + 'TARGET' + Q + '; _c' + K + ' setBehaviour ' + Q + 'CARELESS' + Q + '; '
            '_c' + K + ' addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
            '  if (diag_tickTime - (HMT_TQ select ' + K + ') > 0.05) then { '
            '    HMT_TQ set [' + K + ', diag_tickTime]; '
            '    if ((_this select 3) == (HMT_TIR select ' + K + ')) then { HMT_HITS set [' + K + ', (HMT_HITS select ' + K + ') + 1] } '
            '  }; 0 }]; '
            'HMT_CAL pushBack _t' + K + '; HMT_CAL pushBack _c' + K + '; '
            'HMT_TIR pushBack _t' + K + '; HMT_CIB pushBack _c' + K + '; ')
    c.append('(format [' + Q + 'CAL n=' + P + '1' + Q + ', count HMT_CIB]) call HMT_EMIT;')
    r = b.query(''.join(c), r'CAL n=(\d+)', want=1, timeout=120)
    if not r:
        return None
    print('    ' + r[-1].group(1) + ' duels poses, tir pendant ' + str(a.duree) + ' s...', flush=True)
    time.sleep(3)
    marqueurs(b, len(GRILLE))
    ordre = ('{ private _c = HMT_CIB select _forEachIndex; '
             '_x reveal [_c, 4]; _x doTarget _c; _x doFire _c; } forEach HMT_TIR;')
    n = 0
    while n < a.duree:
        b.send(ordre)
        # remunitionner rarement : recharger interrompt le tir
        if n > 0 and n % 60 == 0:
            b.send('{ _x setVehicleAmmo 1 } forEach HMT_TIR;')
        time.sleep(2); n += 2
        if n % 60 == 0:
            print('      ... ' + str(n) + ' s', flush=True)
    q = ('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1/' + P + '2;' + Q +
         ', _x, HMT_HITS select _forEachIndex] } forEach HMT_SHOTS; '
         '(format [' + Q + 'RES ' + P + '1' + Q + ', _o]) call HMT_EMIT;')
    rr = b.query(q, r'RES (.*)', want=1, timeout=40)
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_CAL; HMT_CAL = []; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; '
           '{ deleteMarker _x } forEach (allMapMarkers select { _x find ' + Q + 'hmtcal' + Q + ' == 0 });')
    if not rr:
        return None
    out = []
    for t in rr[-1].group(1).strip().rstrip(';').split(';'):
        if '/' in t:
            s, h = t.split('/')
            if s.strip().isdigit() and h.strip().isdigit():
                out.append((int(s), int(h)))
    return out


if __name__ == '__main__':
    b = _enregistrer_pont(NativeBridge(port=TH.PORT))
    b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; ')
    time.sleep(1)
    print('=== COURBE N1 : PROBABILITE DE TOUCHER ===', flush=True)
    print('    18 conditions simultanees | ' + str(a.reps) + ' seances de ' + str(a.duree) +
          ' s | zone ' + a.zone + ' | skill ' + ('%.2f' % a.skill), flush=True)
    z = terrain_valide(b)
    if z is None:
        print('  !! le controle de terrain n a PAS REPONDU. ARRET.', flush=True); sys.exit(2)
    mauvais, total, relief = z
    print('  terrain : ' + str(mauvais) + '/' + str(total) + ' points douteux | relief ' + str(relief) + ' m', flush=True)
    if mauvais > total // 4 or relief > 25:
        print('  !! terrain inadapte — on mesurerait le decor, pas le tir. ARRET.', flush=True); sys.exit(2)

    brut = {c: [0, 0] for c in GRILLE}
    for rep in range(1, a.reps + 1):
        print('  seance ' + str(rep) + '/' + str(a.reps), flush=True)
        v = seance(b)
        if not v or len(v) != len(GRILLE):
            print('    (seance incomplete, ignoree)', flush=True); continue
        for c, (s, h) in zip(GRILLE, v):
            brut[c][0] += s; brut[c][1] += h
        tot = sum(brut[c][0] for c in GRILLE)
        print('    cumul : ' + str(tot) + ' balles', flush=True)
        time.sleep(3)
    b.close()

    print('', flush=True)
    print('=== COUPS AU BUT POUR 100 TIRES (skill ' + ('%.2f' % a.skill) + ', plein jour) ===', flush=True)
    print('%-10s' % 'distance' + ''.join('%12s' % p for p in POSTURES), flush=True)
    lignes = {}; tirs = {}
    for d in DISTANCES:
        row = []; trow = []
        for p in POSTURES:
            s, h = brut[(d, p)]
            row.append(100.0 * h / s if s > 0 else float('nan')); trow.append(s)
        lignes[d] = row; tirs[d] = trow
        print('%-10s' % (str(d) + ' m') + ''.join('%12.1f' % x for x in row), flush=True)
    print('', flush=True)
    print('%-10s' % '(balles)' + ''.join('%12s' % p for p in POSTURES), flush=True)
    for d in DISTANCES:
        print('%-10s' % (str(d) + ' m') + ''.join('%12d' % x for x in tirs[d]), flush=True)

    # ---- VERDICT ----
    # Un ecart n'est une VIOLATION que s'il est statistiquement etabli. Sinon c'est
    # un manque de balles, et il faut le dire ainsi : sans quoi le banc crie au loup
    # et on prend l'habitude de l'ignorer.
    al = []; flou = []
    def _kn(d, p):
        n = brut[(d, p)][0]; return brut[(d, p)][1], n

    for d in DISTANCES:
        ku, nu = _kn(d, 'UP'); kd, nd = _kn(d, 'DOWN')
        sg = _ecart_significatif(ku, nu, kd, nd)
        if sg < 0:
            al.append('a ' + str(d) + ' m, un homme COUCHE est touche NETTEMENT plus qu un homme DEBOUT')
        elif sg == 0:
            flou.append(str(d) + ' m')
    for i in range(len(DISTANCES) - 1):
        d1, d2 = DISTANCES[i], DISTANCES[i + 1]
        k1, n1 = _kn(d1, 'UP'); k2, n2 = _kn(d2, 'UP')
        if _ecart_significatif(k1, n1, k2, n2) < 0:
            al.append('le toucher AUGMENTE nettement de ' + str(d1) + ' a ' + str(d2) + ' m')
    maigres = [(d, p) for d in DISTANCES for p in POSTURES if brut[(d, p)][0] < 30]
    if maigres:
        al.append(str(len(maigres)) + '/18 conditions sous 30 balles')

    print('', flush=True)
    print('=== ce que la mesure permet de conclure ===', flush=True)
    ku = sum(brut[(d, 'UP')][1] for d in DISTANCES); nu = sum(brut[(d, 'UP')][0] for d in DISTANCES)
    kd = sum(brut[(d, 'DOWN')][1] for d in DISTANCES); nd = sum(brut[(d, 'DOWN')][0] for d in DISTANCES)
    km = sum(brut[(d, 'MIDDLE')][1] for d in DISTANCES); nm = sum(brut[(d, 'MIDDLE')][0] for d in DISTANCES)
    pu = _wilson(ku, nu); pm = _wilson(km, nm); pd = _wilson(kd, nd)
    print('  toutes distances : debout %.1f%% [%.1f-%.1f] | accroupi %.1f%% | couche %.1f%% [%.1f-%.1f]'
          % (100*pu[0], 100*pu[1], 100*pu[2], 100*pm[0], 100*pd[0], 100*pd[1], 100*pd[2]), flush=True)
    if pu[0] > 0:
        print('  profil de posture mesure : [1.00, %.2f, %.2f]   (le sandbox pose [1.00, 0.50, 0.20])'
              % (pm[0] / pu[0], pd[0] / pu[0]), flush=True)
    if flou:
        print('  posture INDISCERNABLE a : ' + ', '.join(flou) + ' — pas assez de balles pour trancher', flush=True)
    print('  NB : banc sur terrain NU. Se coucher sert surtout a profiter du micro-relief,', flush=True)
    print('       supprime ici pour isoler le tir : ce profil vaut pour le DECOUVERT.', flush=True)

    print('', flush=True)
    if al:
        print('[!] LA COURBE VIOLE LE BON SENS — c est le BANC qui est en cause :', flush=True)
        for x in al: print('    - ' + x, flush=True)
        print('>>> NE PAS injecter dans le sandbox.', flush=True)
    else:
        print('[ok] courbe coherente : decroit avec la distance, la posture basse protege', flush=True)
        print('>>> utilisable pour calibrer le sandbox', flush=True)
    json.dump({'skill': a.skill, 'duree': a.duree, 'reps': a.reps, 'zone': a.zone,
               'distances': DISTANCES, 'postures': POSTURES,
               'pct_au_but': {str(d): lignes[d] for d in DISTANCES},
               'balles': {str(d): tirs[d] for d in DISTANCES}, 'alertes': al},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('-> ' + LEV + '/' + a.out, flush=True)
    print('CALIB_DONE', flush=True)
