#!/usr/bin/env python3
"""mesurer_impacts_mort.py — combien d'impacts pour mettre un homme hors de combat ?

Premiere tentative ratee : lire la valeur de degat passee au gestionnaire d'Arma. Elle
sort a 0,006 par impact — invraisemblable — parce que le gestionnaire est appele une
fois par PARTIE DU CORPS et que je relevais la premiere venue, pas la blessure entiere.

On ne rafistole pas l'instrument, on en change. Ce dont le sandbox a besoin n'est pas
une valeur de degat mais un COMPTE : combien de balles au but avant que l'homme tombe.
Ca se compte sans interpretation — la cible est vulnerable, on compte ses impacts, on
s'arrete quand elle meurt, et on recommence.

Le sandbox tue a dmg_dead=0.7 : degat_par_impact = 0.7 / (impacts pour tuer).
"""
import sys, time, json
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
TH = theatre.use('altis')
zx, zy = 23000, 17400
DIST = 100
N_DUELS = 8        # 8 duels en parallele = 8 morts par vague
VAGUES = 5
DUREE = 75

b = _enregistrer_pont(NativeBridge(port=TH.PORT))
b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
time.sleep(2)


def vague():
    c = ['if (!isNil ' + Q + 'HMT_M' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_M }; '
         'HMT_M = []; HMT_TIR = []; HMT_CIB = []; HMT_NB = []; HMT_MORT = []; HMT_TQ = []; ']
    for k in range(N_DUELS):
        K = str(k)
        tx = zx + k * 150
        T = '[' + str(tx) + ',' + str(zy) + ',0]'
        C = '[' + str(tx) + ',' + str(zy + DIST) + ',0]'
        c.append(
            'HMT_NB pushBack 0; HMT_MORT pushBack -1; HMT_TQ pushBack -9; '
            'private _g' + K + ' = createGroup east; '
            'private _t' + K + ' = _g' + K + ' createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + T + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_t' + K + ' setPosATL ' + T + '; _t' + K + ' setSkill 0.5; _t' + K + ' setUnitPos ' + Q + 'UP' + Q + '; '
            '_t' + K + ' setBehaviour ' + Q + 'COMBAT' + Q + '; _t' + K + ' setCombatMode ' + Q + 'RED' + Q + '; '
            '_t' + K + ' disableAI ' + Q + 'PATH' + Q + '; _t' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_t' + K + ' allowDamage false; _t' + K + ' setVehicleAmmo 1; '
            # CIBLE VULNERABLE : on la laisse mourir, c'est tout l'objet de la mesure
            'private _h' + K + ' = createGroup west; '
            'private _c' + K + ' = _h' + K + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_c' + K + ' setPosATL ' + C + '; _c' + K + ' setUnitPos ' + Q + 'UP' + Q + '; '
            '_c' + K + ' disableAI ' + Q + 'PATH' + Q + '; _c' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_c' + K + ' disableAI ' + Q + 'TARGET' + Q + '; _c' + K + ' setBehaviour ' + Q + 'CARELESS' + Q + '; '
            '_c' + K + ' addEventHandler [' + Q + 'HandleDamage' + Q + ', { '
            '  if (diag_tickTime - (HMT_TQ select ' + K + ') > 0.05) then { '
            '    HMT_TQ set [' + K + ', diag_tickTime]; '
            '    if ((_this select 3) == (HMT_TIR select ' + K + ')) then { '
            '      HMT_NB set [' + K + ', (HMT_NB select ' + K + ') + 1] } }; '
            '  _this select 2 }]; '
            '_c' + K + ' addEventHandler [' + Q + 'Killed' + Q + ', { '
            '  if ((HMT_MORT select ' + K + ') < 0) then { HMT_MORT set [' + K + ', HMT_NB select ' + K + '] } }]; '
            'HMT_M pushBack _t' + K + '; HMT_M pushBack _c' + K + '; '
            'HMT_TIR pushBack _t' + K + '; HMT_CIB pushBack _c' + K + '; ')
    c.append('(format [' + Q + 'PRET ' + P + '1' + Q + ', count HMT_CIB]) call HMT_EMIT;')
    r = b.query(''.join(c), r'PRET (\d+)', want=1, timeout=90)
    if not r:
        return []
    time.sleep(3)
    n = 0
    while n < DUREE:
        b.send('{ private _c = HMT_CIB select _forEachIndex; if (alive _c) then { '
               '_x reveal [_c, 4]; _x doTarget _c; _x doFire _c } } forEach HMT_TIR;')
        time.sleep(2); n += 2
    q = ('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1;' + Q + ', _x] } forEach HMT_MORT; '
         '(format [' + Q + 'M ' + P + '1' + Q + ', _o]) call HMT_EMIT;')
    rr = b.query(q, r'M (.*)', want=1, timeout=30)
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_M; HMT_M = []; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
    if not rr:
        return []
    return [int(t) for t in rr[-1].group(1).strip().rstrip(';').split(';')
            if t.strip().lstrip('-').isdigit()]


print('=== IMPACTS NECESSAIRES POUR METTRE UN HOMME HORS DE COMBAT ===', flush=True)
print('    %d duels x %d vagues, a %d m, debout' % (N_DUELS, VAGUES, DIST), flush=True)
tous = []
for v in range(1, VAGUES + 1):
    res = vague()
    morts = [x for x in res if x > 0]
    tous += morts
    print('  vague %d/%d : %d morts sur %d  %s' % (v, VAGUES, len(morts), N_DUELS,
          sorted(morts)), flush=True)
b.close()

print('', flush=True)
al = []
if len(tous) < 10:
    al.append('moins de 10 morts observees (%d) : trop peu pour conclure' % len(tous))
if tous:
    tous_tri = sorted(tous)
    moy = sum(tous) / float(len(tous))
    med = tous_tri[len(tous_tri) // 2]
    print('=== RESULTAT ===', flush=True)
    print('  %d neutralisations observees' % len(tous), flush=True)
    print('  impacts pour tuer : moyenne %.2f | mediane %d | min %d | max %d'
          % (moy, med, tous_tri[0], tous_tri[-1]), flush=True)
    if not al:
        print('', flush=True)
        print('  >>> degat_par_impact = 0.7 / %.2f = %.3f' % (moy, 0.7 / moy), flush=True)
        print('      (0.7 = seuil de mort du sandbox)', flush=True)
else:
    al.append('aucune neutralisation')
if al:
    print('[!] MESURE INSUFFISANTE :', flush=True)
    for x in al: print('    - ' + x, flush=True)
json.dump({'dist': DIST, 'impacts_pour_tuer': tous, 'alertes': al},
          open(LEV + '/courbe_impacts_mort.json', 'w'), indent=1)
print('-> ' + LEV + '/courbe_impacts_mort.json', flush=True)
print('MORT_DONE', flush=True)
