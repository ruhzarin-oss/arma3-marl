#!/usr/bin/env python3
"""sentinelle.py — le pont meurt-il tout seul ?

Il a lache trois fois en une heure alors qu'il tenait trois heures ce matin. J'ai
d'abord accuse mon banc de suppression (24 unites en combat perpetuel), puis constate
qu'il meurt AUSSI sans rien qui tourne. Plutot que d'accumuler les theories, on mesure :
un ping toutes les 60 s, rien d'autre sur le serveur, et on note l'heure exacte de la
mort ainsi que la charge processeur juste avant.

Ce que ca tranche :
  - il meurt a vide      -> la cause est le serveur (fuite interne, ALiVE, mods)
  - il tient a vide      -> la cause est bien la charge des bancs
"""
import sys, time, subprocess, datetime
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import theatre

Q = chr(34); P = chr(37)
LOG = '/tmp/sentinelle.log'
PORT = theatre.use('altis').PORT


def cpu_mem():
    try:
        o = subprocess.check_output(
            "ps -eo pcpu,rss,cmd | grep '[a]rma3server_x64' | head -1", shell=True, text=True).split()
        return float(o[0]), int(o[1]) / 1024.0
    except Exception:
        return -1.0, -1.0


def ping():
    """une requete minimale, connexion ouverte PUIS FERMEE (le pont ne parle qu a un client)"""
    from native_bridge import NativeBridge
    b = None
    try:
        b = NativeBridge(port=PORT)
        r = b.query('(format [' + Q + 'P ' + P + '1' + Q + ', round diag_tickTime]) call HMT_EMIT;',
                    r'P (\d+)', want=1, timeout=12)
        return bool(r)
    except Exception:
        return False
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass


with open(LOG, 'w') as f:
    f.write('sentinelle du pont — un ping par minute, rien d autre\n')
t0 = time.time()
mort = None
for k in range(240):                       # jusqu a 4 h
    ok = ping()
    c, m = cpu_mem()
    age = int(time.time() - t0)
    ligne = ('%s  +%4d s  pont=%s  cpu=%5.1f%%  memoire=%6.0f Mo'
             % (datetime.datetime.now().strftime('%H:%M:%S'), age, 'OK ' if ok else 'MUET', c, m))
    with open(LOG, 'a') as f:
        f.write(ligne + '\n')
    if not ok and mort is None:
        mort = age
        with open(LOG, 'a') as f:
            f.write('>>> PREMIERE ABSENCE DE REPONSE apres %d s (%.1f min) de service, '
                    'SANS AUCUNE MESURE EN COURS\n' % (age, age / 60.0))
    if mort is not None and age - mort > 240:
        break                              # confirme pendant 4 min : inutile d insister
    time.sleep(60)
with open(LOG, 'a') as f:
    f.write('fin de la sentinelle\n')
