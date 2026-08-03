#!/usr/bin/env python3
"""mesurer_suppression.py — CHANTIER 1, COURBE N2 : que fait vraiment la suppression ?

C'est la courbe qui manque pour que le feu-et-mouvement ait une raison d'exister. Le
sandbox traite la suppression en TOUT OU RIEN : un defenseur supprime ne fait plus
aucun degat. Si la realite est "il tire un peu moins bien", appuyer ne vaut pas ce
qu'on croit ; si c'est "il ne tire plus du tout", ca vaut bien plus. Personne ne l'a
verifie.

PROTOCOLE — A/B strict, les deux bras EN MEME TEMPS (meme heure, meme etat serveur,
meme terrain), seule la presence de feu entrant change :
  A. temoin      : le defenseur tire sur sa cible, personne ne le gene
  B. supprime    : le meme, avec deux tireurs qui l'arrosent

On releve TROIS choses, car la suppression peut agir sur l'une sans l'autre :
  - sa CADENCE (tire-t-il moins ?)
  - sa PRECISION (touche-t-il moins bien quand il tire ?)
  - la valeur de suppression d'Arma elle-meme (getSuppression)

Toutes les lecons du banc n1 sont reprises : impacts dedupliques par instant, impacts
filtres par SOURCE, tireurs invulnerables, groupes vides balayes, seances courtes et
repetees, terrain verifie avant, verdict statistique.
"""
import sys, time, json, math, argparse
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


def _fermer(b):
    """Le pont ne parle qu a UN client : sortir sans fermer le rend muet
    pour tout le monde jusqu au redemarrage du serveur."""
    try:
        b.close()
    except Exception:
        pass

Q = chr(34); P = chr(37)
LEV = '/home/younes/arma3-marl/leviathan'

ap = argparse.ArgumentParser()
ap.add_argument('--duree', type=int, default=60)
ap.add_argument('--reps', type=int, default=8)
ap.add_argument('--skill', type=float, default=0.5)
ap.add_argument('--zone', default='23000,17400')
ap.add_argument('--dx', type=int, default=150)
ap.add_argument('--dist', type=int, default=100, help='distance defenseur -> sa cible')
ap.add_argument('--dsup', type=int, default=120, help='distance des tireurs qui suppriment')
ap.add_argument('--paires', type=int, default=2, help='paires par bras')
ap.add_argument('--out', default='courbe_suppression.json')
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
zx, zy = [int(v) for v in a.zone.split(',')]

# cellules : les `paires` premieres sont TEMOIN, les suivantes SUPPRIMEES
N = a.paires * 2


# CORRECTION 27/07 (soir) : les cellules etaient alignees vers l'EST depuis (23000,17400),
# au pas de 150 m. Deux problemes mesures le meme jour :
#   - vers l'est, Altis devient la MER a partir de ~23900 (altitudes -22, -87, -131 m).
#     Un soldat pose dans l'eau se noie : zero balle, et des « impacts » qui sont des noyades.
#   - 150 m d'ecart, avec des tireurs de suppression a 120 m, fait deborder une cellule
#     sur sa voisine. La consigne est : espacement >= 700 m ET filtre par source.
# On lit donc les cellules CERTIFIEES (terre, plates, sans bati, >= 700 m) quand elles existent.
try:
    _CEL = json.load(open(LEV + '/cellules_altis.json'))['serie']
except Exception:
    _CEL = []


def cel(k):
    if _CEL:
        c = _CEL[k % len(_CEL)]
        return c[0], c[1]
    return zx + k * a.dx, zy


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    ph = k / float(n); d = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / d
    dem = z * math.sqrt(ph * (1 - ph) / n + z * z / (4.0 * n * n)) / d
    return (ph, max(0.0, cen - dem), min(1.0, cen + dem))


def sig_taux(k1, n1, k2, n2):
    """Compare deux TAUX (balles par seconde), pas deux proportions.

    `sig()` plafonne a 1 par construction : c'est un test de proportions. Avec 890 balles
    en 360 s il calculait une racine de variance negative et tuait le banc. Ici la variance
    est celle de Poisson, var(k/n) = k/n^2, sans plafond.
    """
    if n1 <= 0 or n2 <= 0 or (k1 + k2) < 10:
        return 0.0
    r1 = k1 / float(n1); r2 = k2 / float(n2)
    se = math.sqrt(k1 / float(n1) ** 2 + k2 / float(n2) ** 2)
    return (r1 - r2) / se if se > 0 else 0.0


def sig(k1, n1, k2, n2):
    if n1 < 5 or n2 < 5:
        return 0.0
    p1 = k1 / float(n1); p2 = k2 / float(n2)
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return (p1 - p2) / se if se > 0 else 0.0


def terrain_ok(b):
    pts = []
    for k in range(N):
        x, y = cel(k)
        pts += [(x, y), (x, y + a.dist), (x, y - a.dsup)]
    liste = '[' + ','.join('[' + str(x) + ',' + str(y) + ']' for x, y in pts) + ']'
    q = ('private _bad = 0; private _hmin = 9999; private _hmax = -9999; '
         '{ private _c = _x; if (surfaceIsWater _c) then { _bad = _bad + 1 }; '
         '  if (count (nearestTerrainObjects [[_c select 0, _c select 1, 0], '
         '[' + Q + 'HOUSE' + Q + ',' + Q + 'BUILDING' + Q + ',' + Q + 'TREE' + Q + ',' + Q + 'ROCK' + Q + '], 50]) > 2) '
         'then { _bad = _bad + 1 }; '
         '  private _h = getTerrainHeightASL _c; if (_h < _hmin) then {_hmin=_h}; if (_h > _hmax) then {_hmax=_h}; '
         '} forEach ' + liste + '; '
         '(format [' + Q + 'Z ' + P + '1 ' + P + '2 ' + P + '3' + Q + ', _bad, count ' + liste + ', round(_hmax-_hmin)]) call HMT_EMIT;')
    r = b.query(q, r'Z (\d+) (\d+) (-?\d+)', want=1, timeout=40)
    return (int(r[-1].group(1)), int(r[-1].group(2)), int(r[-1].group(3))) if r else None



def marqueurs(b, paires):
    """Points de couleur sur la carte, au banc (23000/17400) :
         BLEU   defenseur temoin        ROUGE  defenseur arrose
         ORANGE tireur de suppression   BLANC  la cible qu'il vise
         VERT   le joueur
    Ecrit en concatenation simple : la version precedente melangeait les guillemets et
    envoyait du charabia qu'Arma ignorait en silence."""
    g = chr(34)
    lignes = [
        '{ deleteMarker _x } forEach (allMapMarkers select { (_x find ' + g + 'hmtsup' + g + ') == 0 });',
        '{',
        '  private _i = _forEachIndex;',
        '  private _m = createMarker [format [' + g + 'hmtsup_d%1' + g + ', _i], getPos _x];',
        '  _m setMarkerType ' + g + 'mil_dot' + g + ';',
        '  _m setMarkerSize [1.2, 1.2];',
        '  if (_i < ' + str(paires) + ') then {',
        '    _m setMarkerColor ' + g + 'ColorBlue' + g + '; _m setMarkerText ' + g + 'temoin' + g + ';',
        '  } else {',
        '    _m setMarkerColor ' + g + 'ColorRed' + g + '; _m setMarkerText ' + g + 'ARROSE' + g + ';',
        '  };',
        '} forEach HMT_DEF;',
        '{',
        '  private _m = createMarker [format [' + g + 'hmtsup_c%1' + g + ', _forEachIndex], getPos _x];',
        '  _m setMarkerType ' + g + 'mil_dot' + g + '; _m setMarkerColor ' + g + 'ColorWhite' + g + ';',
        '  _m setMarkerText ' + g + 'cible' + g + ';',
        '} forEach HMT_CIB;',
        '{',
        '  private _m = createMarker [format [' + g + 'hmtsup_s%1' + g + ', _forEachIndex], getPos _x];',
        '  _m setMarkerType ' + g + 'mil_dot' + g + '; _m setMarkerColor ' + g + 'ColorOrange' + g + ';',
        '  _m setMarkerText ' + g + 'arroseur' + g + ';',
        '} forEach HMT_NSUP;',
        '{ if (isPlayer _x) then {',
        '  private _mj = createMarker [' + g + 'hmtsup_joueur' + g + ', getPos _x];',
        '  _mj setMarkerType ' + g + 'mil_dot' + g + '; _mj setMarkerColor ' + g + 'ColorGreen' + g + ';',
        '  _mj setMarkerSize [1.4, 1.4]; _mj setMarkerText ' + g + 'TOI' + g + ';',
        '} } forEach allUnits;',
    ]
    q = ' '.join(lignes)
    # ENVOI SANS ACCUSE DE RECEPTION. Le mecanisme est prouve (sonde_marqueurs.py : 3/3).
    # Attendre une confirmation ajoutait un point de rupture : quand la reponse arrivait
    # en retard, elle etait prise pour celle de la requete SUIVANTE et tout le dialogue
    # se decalait — la seance restait bloquee.
    b.send(q, wait=False)
    print('      carte : points poses au banc, zone ' + a.zone, flush=True)
    return 0

def seance(b):
    _CIBLE_ARROSEUR = []      # arroseur i -> indice du defenseur qu'il arrose
    c = ['if (!isNil ' + Q + 'HMT_S' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S }; '
         'HMT_S = []; HMT_DEF = []; HMT_CIB = []; HMT_SHOTS = []; HMT_HITS = []; HMT_TQ = []; '
         'HMT_SUP = []; HMT_NSUP = []; ']
    for k in range(N):
        K = str(k); x, y = cel(k)
        D = '[' + str(x) + ',' + str(y) + ',0]'
        C = '[' + str(x) + ',' + str(y + a.dist) + ',0]'
        c.append(
            'HMT_SHOTS pushBack 0; HMT_HITS pushBack 0; HMT_TQ pushBack -9; '
            # COLLISION DE NOMS — LA CAUSE, mesuree le 28/07. HMT_NSUP servait a la fois
            # de compteur (un zero par defenseur) et de LISTE DES TIREURS. La liste valait
            # donc [0,0,0,0,unite,unite,unite,unite] : l'ordre faisait `0 reveal [...]`,
            # une erreur de type toutes les 4 s dans un envoi sans accuse — inaudible.
            # Le journal le disait : Arma comptait 8 tireurs, Python en appariait 4.
            # Le role de compteur n'etait relu nulle part : on le supprime.
            'HMT_SUP pushBack 0; '
            # --- LE DEFENSEUR : c'est LUI qu'on mesure ---
            'private _g' + K + ' = createGroup east; '
            'private _d' + K + ' = _g' + K + ' createUnit [' + Q + 'O_Soldier_F' + Q + ', ' + D + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_d' + K + ' setPosATL ' + D + '; _d' + K + ' setSkill ' + ('%.2f' % a.skill) + '; '
            '_d' + K + ' setUnitPos ' + Q + 'UP' + Q + '; _d' + K + ' setBehaviour ' + Q + 'COMBAT' + Q + '; '
            '_d' + K + ' setCombatMode ' + Q + 'RED' + Q + '; '
            '_d' + K + ' disableAI ' + Q + 'PATH' + Q + '; _d' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_d' + K + ' allowDamage false; _d' + K + ' setVehicleAmmo 1; '
            '_d' + K + ' addEventHandler [' + Q + 'Fired' + Q + ', { HMT_SHOTS set [' + K + ', (HMT_SHOTS select ' + K + ') + 1] }]; '
            # --- SA CIBLE : invulnerable, compte les impacts venant de LUI seul ---
            'private _h' + K + ' = createGroup west; '
            'private _c' + K + ' = _h' + K + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + C + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            # DUEL SYMETRIQUE : la cible RIPOSTE, dans les deux bras. Avant, elle etait
            # CARELESS avec la visee coupee — un mannequin —, et le temoin se
            # desinteressait d'elle au bout de quelques coups. On comparait alors un
            # combat a un stand de tir.
            '_c' + K + ' setPosATL ' + C + '; _c' + K + ' setUnitPos ' + Q + 'UP' + Q + '; '
            '_c' + K + ' setSkill ' + ('%.2f' % a.skill) + '; '
            '_c' + K + ' disableAI ' + Q + 'PATH' + Q + '; _c' + K + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
            '_c' + K + ' setBehaviour ' + Q + 'COMBAT' + Q + '; _c' + K + ' setCombatMode ' + Q + 'RED' + Q + '; '
            # INVULNERABLE : une cible morte rend son bras muet (1 seance sur 3 perdue
            # le 28/07). HitPart compte quand meme, lui — c'est tout l'interet.
            '_c' + K + ' allowDamage false; _c' + K + ' setVehicleAmmo 1; '
            # HITPART, PAS HANDLEDAMAGE. Mesure du 28/07 : HandleDamage comptait 12 %
            # la ou HitPart compte 48 % — et 48 % est ce que dit la courbe n1 a 100 m.
            # HitPart se declenche sur l'impact du projectile, donc il traverse
            # `allowDamage false`. `_this select 0 select 1` est le TIREUR.
            '_c' + K + ' addEventHandler [' + Q + 'HitPart' + Q + ', { '
            '  if (diag_tickTime - (HMT_TQ select ' + K + ') > 0.05) then { '
            '    HMT_TQ set [' + K + ', diag_tickTime]; '
            '    if (((_this select 0) select 1) == (HMT_DEF select ' + K + ')) then '
            '      { HMT_HITS set [' + K + ', (HMT_HITS select ' + K + ') + 1] } '
            '  }; }]; '
            'HMT_S pushBack _d' + K + '; HMT_S pushBack _c' + K + '; '
            'HMT_DEF pushBack _d' + K + '; HMT_CIB pushBack _c' + K + '; ')
        if k >= a.paires:      # bras SUPPRIME : deux tireurs l'arrosent
            for j in (0, 1):
                _CIBLE_ARROSEUR.append(k)     # cet arroseur vise le defenseur k
                J = K + '_' + str(j)
                sx = x + (j * 2 - 1) * 25
                S = '[' + str(sx) + ',' + str(y - a.dsup) + ',0]'
                c.append(
                    'private _sg' + J + ' = createGroup west; '
                    'private _s' + J + ' = _sg' + J + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + S + ', [], 0, ' + Q + 'NONE' + Q + ']; '
                    '_s' + J + ' setPosATL ' + S + '; _s' + J + ' setSkill ' + ('%.2f' % a.skill) + '; '
                    '_s' + J + ' setUnitPos ' + Q + 'UP' + Q + '; _s' + J + ' setBehaviour ' + Q + 'COMBAT' + Q + '; '
                    '_s' + J + ' setCombatMode ' + Q + 'RED' + Q + '; '
                    '_s' + J + ' disableAI ' + Q + 'PATH' + Q + '; _s' + J + ' disableAI ' + Q + 'AUTOTARGET' + Q + '; '
                    '_s' + J + ' allowDamage false; _s' + J + ' setVehicleAmmo 1; '
                    'HMT_S pushBack _s' + J + '; HMT_NSUP pushBack _s' + J + '; ')
    c.append('(format [' + Q + 'PRET ' + P + '1 ' + P + '2' + Q + ', count HMT_DEF, count HMT_NSUP]) call HMT_EMIT;')
    r = b.query(''.join(c), r'PRET (\d+) (\d+)', want=1, timeout=120)
    if not r:
        return None
    print('    %s defenseurs (%s temoins / %s supprimes) + %s tireurs de suppression'
          % (r[-1].group(1), a.paires, a.paires, r[-1].group(2)), flush=True)
    time.sleep(3)
    marqueurs(b, a.paires)
    # ORDRE EXPLICITE. Plus aucun calcul d'indice cote SQF : la correspondance est etablie
    # en Python, ou l'on connait les longueurs. Un `select` hors limites est une erreur
    # SQF silencieuse quand l'envoi n'attend pas d'accuse — c'est ce qui tuait le pont
    # toutes les 4 secondes (mesure du 28/07).
    _paires = ['[' + str(i) + ',' + str(k) + ']' for i, k in enumerate(_CIBLE_ARROSEUR)]
    # LES CIBLES RESTENT VIVANTES. 13e defaut silencieux du 28/07 : `HandleDamage` qui
    # renvoie 0 ne protege pas (trois cibles mortes a 100 % de degats). On ne peut pas
    # mettre `allowDamage false` sans perdre le comptage, qui passe par ce meme handler.
    # On efface donc les degats a chaque ordre : l'impact est compte, la cible tient.
    ordre = (             '{ private _c = HMT_CIB select _forEachIndex; _x reveal [_c, 4]; _x doTarget _c; '
             '_x doFire _c; } forEach HMT_DEF; '
             '{ private _d = HMT_DEF select _forEachIndex; _x reveal [_d, 4]; _x doTarget _d; '
             '_x doFire _d; } forEach HMT_CIB; '
             '{ private _i = _x select 0; private _k = _x select 1; '
             '  if (_i < count HMT_NSUP && _k < count HMT_DEF) then { '
             '    private _a = HMT_NSUP select _i; private _v = HMT_DEF select _k; '
             '    _a reveal [_v, 4]; _a doTarget _v; _a doFire _v; }; '
             '} forEach [' + ','.join(_paires) + '];')
    print('      [ordre] %d arroseurs apparies explicitement a %d defenseurs'
          % (len(_CIBLE_ARROSEUR), a.paires * 2), flush=True)
    releve = ('{ HMT_SUP set [_forEachIndex, (HMT_SUP select _forEachIndex) + (getSuppression _x)]; '
              '} forEach HMT_DEF; '
              '{ HMT_SUP set [_forEachIndex, HMT_SUP select _forEachIndex] } forEach HMT_DEF;')
    print('      [phase] tir pendant %d s' % a.duree, flush=True)
    n = 0
    _dernier_ok = -1          # dernier instant ou le pont a repondu PENDANT le tir
    _premier_mort = -1        # premier instant ou il n a pas repondu
    while n < a.duree:
        b.send(ordre, wait=False)
        time.sleep(4); n += 4
        # LECTURE PENDANT LE TIR : savoir QUAND le pont meurt, pas seulement QU IL meurt.
        # Trois cas, trois causes : il tient jusqu au bout puis meurt -> la TRANSITION ;
        # il meurt au milieu -> le TIR lui-meme ; il ne repond jamais -> la MISE EN PLACE.
        # Volontairement minimale (un compteur deja calcule) pour ne pas etre la cause.
        # Elle n arrete JAMAIS le banc : elle note.
        if n % 12 == 0:
            _r = b.query('(format [' + Q + 'VIF ' + P + '1' + Q + ', HMT_SHOTS select 0]) call HMT_EMIT;',
                         r'VIF (\d+)', want=1, timeout=15)
            if _r:
                _dernier_ok = n
                print('        +%2d s : pont VIF (%s balles sur le 1er defenseur)'
                      % (n, _r[-1].group(1)), flush=True)
            else:
                if _premier_mort < 0:
                    _premier_mort = n
                print('        +%2d s : pont MUET' % n, flush=True)
    print('      [pont] dernier signe de vie a +%d s | premiere absence a +%d s'
          % (_dernier_ok, _premier_mort), flush=True)
    # --- DECROISSANCE : les tireurs cessent le feu, on suit la suppression qui retombe.
    # C'est LA grandeur qui decide si le feu-et-mouvement a un sens : si la suppression
    # s'evapore des l'arret du tir (ce que fait le sandbox), il faudrait tirer et courir
    # en meme temps. Si elle dure quelques secondes, le bond devient possible.
    b.send('{ _x doWatch objNull; _x doTarget objNull; _x setCombatMode ' + Q + 'BLUE' + Q + ' } forEach HMT_NSUP;')
    # ---- APRES LE CESSEZ-LE-FEU : la cadence du defenseur remonte-t-elle, et en
    # combien de temps ? C'est LA grandeur qui decide si le feu-et-mouvement a un sens :
    # le sandbox remet la suppression a zero a chaque pas (3,3 s), donc l'adversaire y
    # releve la tete instantanement. Si dans Arma il lui faut plusieurs secondes, cette
    # fenetre EST la manoeuvre.
    print('      [phase] cessez-le-feu, on suit la cadence du defenseur', flush=True)
    b.send('{ _x doWatch objNull; _x doTarget objNull; _x setCombatMode ' + Q + 'BLUE' + Q + '; '
           '  _x disableAI ' + Q + 'AUTOTARGET' + Q + ' } forEach HMT_NSUP;', wait=False)
    decr = []
    _prec = None
    for _k in range(10):
        # on relance l'ordre de tir aux DEFENSEURS : ils sont libres d'y repondre ou non,
        # et c'est precisement ce delai de reponse qu'on mesure
        b.send(ordre, wait=False)
        time.sleep(2)
        rd = b.query('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1,' + Q + ', _x] } forEach HMT_SHOTS; '
                     '(format [' + Q + 'CAD ' + P + '1' + Q + ', _o]) call HMT_EMIT;',
                     r'CAD ([\d,]+)', want=1, timeout=45)
        if not rd:
            decr.append(None)
            print('        +%2d s : pas de reponse' % (2 * _k), flush=True)
            continue
        cur = [int(x) for x in rd[-1].group(1).rstrip(',').split(',') if x.strip().isdigit()]
        if _prec is None:
            delta = [0] * len(cur)
        else:
            delta = [max(0, c - p) for c, p in zip(cur, _prec)]
        _prec = cur
        # moyenne des temoins vs moyenne des arroses, en balles par seconde
        nt = a.paires
        tem = sum(delta[:nt]) / (2.0 * max(nt, 1))
        sup = sum(delta[nt:]) / (2.0 * max(len(delta) - nt, 1))
        decr.append([round(tem, 3), round(sup, 3)])
        print('        +%2d s : temoin %.2f b/s   arrose %.2f b/s' % (2 * _k, tem, sup), flush=True)

    q = ('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1/' + P + '2/' + P + '3;' + Q +
         ', _x, HMT_HITS select _forEachIndex, 0] } forEach HMT_SHOTS; '
         '(format [' + Q + 'RES ' + P + '1' + Q + ', _o]) call HMT_EMIT;')
    # ETAT DES CIBLES — le temoin s'arrete-t-il parce que sa cible est morte ?
    # Sans ce releve, « cadence x3,85 » est ininterpretable.
    _et = b.query('private _o = ' + Q + Q + '; '
                  '{ _o = _o + format [' + Q + P + '1:' + P + '2/' + P + '3;' + Q + ', _forEachIndex, '
                  '  (if (alive _x) then {1} else {0}), round (100 * damage _x)] } forEach HMT_CIB; '
                  '(format [' + Q + 'CIB ' + P + '1' + Q + ', _o]) call HMT_EMIT;',
                  r'CIB (.*)', want=1, timeout=30)
    if _et:
        _txt = _et[-1].group(1).strip().rstrip(';')
        _morts = _txt.count(':0/')
        print('      [cibles] %s   -> %d morte(s) sur %d'
              % (_txt, _morts, N), flush=True)
        if _morts:
            print('      !! une cible morte prive son tireur de travail : la cadence du', flush=True)
            print('         bras concerne ne mesure plus rien.', flush=True)
    else:
        print('      [cibles] pas de reponse — etat inconnu, on ne conclut pas', flush=True)
    print('      [phase] releve final', flush=True)
    rr = b.query(q, r'RES (.*)', want=1, timeout=40)
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_S; HMT_S = []; HMT_NECH = 0; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; '
           '{ deleteMarker _x } forEach (allMapMarkers select { _x find ' + Q + 'hmtsup' + Q + ' == 0 });')
    if not rr:
        return None
    out = []
    _brut = rr[-1].group(1)
    for t in _brut.strip().rstrip(';').split(';'):
        p3 = t.split('/')
        if len(p3) == 3 and all(x.strip().lstrip('-').isdigit() for x in p3):
            try:
                out.append((int(p3[0]), int(p3[1]), int(p3[2]) / 1000.0))
            except ValueError:
                out.append((int(p3[0]), int(p3[1]), 0.0))
    if len(out) != N:
        print('      [releve illisible] %d valeurs sur %d attendues' % (len(out), N), flush=True)
        print('      brut : %s' % _brut[:300], flush=True)
    return out, decr


if __name__ == '__main__':
    b = _enregistrer_pont(NativeBridge(port=TH.PORT))
    b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange; HMT_NECH = 0; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
    time.sleep(2)
    rj = b.query('(format [' + Q + 'J ' + P + '1' + Q + ', count allPlayers]) call HMT_EMIT;', r'J (\d+)', want=1, timeout=25)
    nj = int(rj[-1].group(1)) if rj else 0
    print('=== COURBE N2 : EFFET REEL DE LA SUPPRESSION ===', flush=True)
    print('    %d temoins vs %d supprimes, EN MEME TEMPS | %d seances de %d s | duel a %d m'
          % (a.paires, a.paires, a.reps, a.duree, a.dist), flush=True)
    print('    joueurs connectes : %d %s' % (nj, '' if nj else '<-- ATTENTION : sans joueur l IA reste inerte'), flush=True)
    if nj == 0:
        # MESURE du 27/07 : l'IA combat SANS joueur (2 repetitions, canari passe,
        # 65 et 52 tirs en configuration normale). L'ancien garde-fou « 0 joueur =
        # ARRET » etait FAUX : il venait d'une note du projet jamais testee, il a fait
        # echouer trois lancements de cette courbe et oblige Younes a se reconnecter
        # une demi-douzaine de fois pour rien. On avertit, on n'arrete plus.
        print('    (aucun joueur : sans importance, l IA combat quand meme — mesure 27/07)', flush=True)
    t = terrain_ok(b)
    if t is None:
        print('  !! controle de terrain sans reponse. ARRET.', flush=True); _fermer(b); sys.exit(2)
    mauvais, tot, rel = t
    print('    terrain : %d/%d points douteux | relief %d m' % (mauvais, tot, rel), flush=True)
    if mauvais > tot // 4 or rel > 25:
        print('  !! terrain inadapte. ARRET.', flush=True); _fermer(b); sys.exit(2)

    brut = [[0, 0, 0.0, 0] for _ in range(N)]; DECR = []
    for rep in range(1, a.reps + 1):
        _r = seance(b)
        v, dec = (_r if _r else (None, None))
        if dec: DECR.append(dec)
        if not v or len(v) != N:
            print('  seance %d : incomplete, ignoree' % rep, flush=True); continue
        for i, (s, h, sup) in enumerate(v):
            brut[i][0] += s; brut[i][1] += h; brut[i][2] += sup; brut[i][3] += 1
        st = sum(brut[i][0] for i in range(a.paires)); ss = sum(brut[i][0] for i in range(a.paires, N))
        print('  seance %d/%d : cumul %d balles temoin / %d balles supprime' % (rep, a.reps, st, ss), flush=True)
        time.sleep(2)
    b.close()

    ST = sum(brut[i][0] for i in range(a.paires)); HT = sum(brut[i][1] for i in range(a.paires))
    SS = sum(brut[i][0] for i in range(a.paires, N)); HS = sum(brut[i][1] for i in range(a.paires, N))
    supT = sum(brut[i][2] for i in range(a.paires)) / max(1, sum(brut[i][3] for i in range(a.paires)))
    supS = sum(brut[i][2] for i in range(a.paires, N)) / max(1, sum(brut[i][3] for i in range(a.paires, N)))
    secs = a.reps * a.duree * a.paires

    # LA MESURE D'ABORD, L'AFFICHAGE ENSUITE. Le 28/07 un NaN dans le tableau de
    # decroissance a tue le banc APRES la mesure et AVANT l'ecriture : trois seances
    # perdues pour une barre de caracteres. Plus jamais.
    json.dump({'temoin': {'balles': ST, 'au_but': HT, 'suppression': supT},
               'supprime': {'balles': SS, 'au_but': HS, 'suppression': supS},
               'secondes_par_bras': secs, 'dist': a.dist, 'skill': a.skill,
               'decroissance': DECR, 'alertes': []},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('-> mesure ecrite d abord : ' + LEV + '/' + a.out, flush=True)

    print('', flush=True)
    print('=== RESULTAT ===', flush=True)
    pt = wilson(HT, ST); ps = wilson(HS, SS)
    print('  %-12s %12s %12s' % ('', 'TEMOIN', 'SUPPRIME'), flush=True)
    print('  %-12s %12d %12d' % ('balles tirees', ST, SS), flush=True)
    print('  %-12s %12.2f %12.2f' % ('balles/s', ST / float(secs), SS / float(secs)), flush=True)
    print('  %-12s %12s %12s' % ('au but', '%.1f%%' % (100 * pt[0]), '%.1f%%' % (100 * ps[0])), flush=True)
    print('  %-12s %12s %12s' % ('  (95%)', '[%.0f-%.0f]' % (100*pt[1], 100*pt[2]), '[%.0f-%.0f]' % (100*ps[1], 100*ps[2])), flush=True)
    print('  %-12s %12.3f %12.3f' % ('suppression', supT, supS), flush=True)

    zc = sig_taux(ST, secs, SS, secs)     # cadence : un TAUX, pas une proportion
    zp = sig(HT, ST, HS, SS)              # precision
    print('', flush=True)
    print('=== CE QUE LA SUPPRESSION FAIT REELLEMENT ===', flush=True)
    if SS > 0 and ST > 0:
        print('  cadence   : x%.2f  %s' % (SS / float(ST), 'NETTE' if abs(zc) > 1.96 else 'indiscernable'), flush=True)
    if pt[0] > 0:
        print('  precision : x%.2f  %s (z=%+.2f)' % (ps[0] / pt[0], 'NETTE' if abs(zp) > 1.96 else 'indiscernable', zp), flush=True)
        eff = (SS * ps[0]) / max(1e-9, ST * pt[0])
        print('  ---> DANGER TOTAL (balles x precision) : x%.2f' % eff, flush=True)
        print('', flush=True)
        print('  le sandbox traite la suppression en TOUT OU RIEN (degats mis a zero).', flush=True)
        print('  la mesure dit : le feu entrant laisse %.0f%% de la capacite de nuire.' % (100 * eff), flush=True)
    if DECR:
        print('', flush=True)
        print('=== APRES L ARRET DU FEU : la suppression retombe-t-elle vite ? ===', flush=True)
        # CORRECTION : chaque releve est une PAIRE [temoin, arrose]. L ancienne moyenne
        # faisait sum() sur des listes -> exception, et la phase entiere disparaissait.
        # Ce qu on veut n est pas une « decroissance de la suppression » (getSuppression
        # ne repond pas) mais le TEMPS DE RETOUR A LA CADENCE : combien de secondes
        # l arrose met-il a retrouver le rythme du temoin apres le cessez-le-feu.
        nmax = max(len(d) for d in DECR)
        moyT, moyS = [], []
        for i in range(nmax):
            vt = [d[i][0] for d in DECR if i < len(d) and d[i] is not None]
            vs = [d[i][1] for d in DECR if i < len(d) and d[i] is not None]
            moyT.append(sum(vt) / len(vt) if vt else None)
            moyS.append(sum(vs) / len(vs) if vs else None)
        print('   t(s)   temoin b/s   arrose b/s   rapport', flush=True)
        for i in range(nmax):
            if moyT[i] is None:
                continue
            rap = (moyS[i] / moyT[i]) if moyT[i] > 1e-9 else float('nan')
            print('  +%2d      %8.2f     %8.2f     %6.2f  %s'
                  % (2 * i, moyT[i], moyS[i], rap, ('' if rap != rap else '#' * int(round(min(max(rap, 0.0), 2.0) * 20)))), flush=True)
        # temps de retour : premier instant ou l arrose atteint 80 % de la cadence du temoin
        retour = None
        for i in range(nmax):
            if moyT[i] and moyT[i] > 1e-9 and moyS[i] is not None and moyS[i] >= 0.8 * moyT[i]:
                retour = 2 * i
                break
        print('', flush=True)
        print('  TEMPS DE RETOUR A LA CADENCE (80 %% du temoin) : %s'
              % (('%d s' % retour) if retour is not None else 'plus de %d s' % (2 * (nmax - 1))), flush=True)
        print('  le sandbox remet la suppression a ZERO a chaque pas (3,28 s) :', flush=True)
        print('  si ce temps depasse 3,3 s, le sandbox sous-estime la fenetre du bond.', flush=True)

    al = []
    if ST < 100 or SS < 100:
        al.append('moins de 100 balles dans un bras : trop peu pour conclure')
    # `getSuppression` NE REPOND PAS sur ce serveur (mesure du 27/07) : supT et supS
    # valent 0 par construction. En faire une alerte declenchait un faux « a reprendre »
    # a chaque run. Le juge est la CADENCE, pas cette valeur.
    if supS <= supT and (supT > 0 or supS > 0):
        al.append('les supprimes ne sont PAS plus supprimes que les temoins (%.3f vs %.3f) : le feu de suppression ne porte pas' % (supS, supT))
    if al:
        print('', flush=True)
        print('[!] MESURE A REPRENDRE :', flush=True)
        for x in al: print('    - ' + x, flush=True)
    json.dump({'temoin': {'balles': ST, 'au_but': HT, 'suppression': supT},
               'supprime': {'balles': SS, 'au_but': HS, 'suppression': supS},
               'secondes_par_bras': secs, 'dist': a.dist, 'skill': a.skill, 'alertes': al},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('-> ' + LEV + '/' + a.out, flush=True)
    print('SUPP_DONE', flush=True)
