#!/usr/bin/env python3
"""nuit0.py — collecte NUIT 0 sur la ferme : ou le succes apparait-il, et dans quel ordre ?

Criteres : CRITERES_NUIT0.md (4745631a705e79c0). Refuse de demarrer si le fichier a bouge.

Un ordonnanceur simple : une file de taches (mode, A, rep), quatorze ouvriers, chacun colle a
son instance de ferme. Chaque ouvrier joue un episode complet (poser la defense, armer, jouer,
desarmer) et depose l episode ENTIER en JSON. On ne juge rien ici : on collecte. La lecture est
faite par un autre programme, sur les criteres figes.
"""
import argparse, hashlib, json, os, queue, shutil, subprocess, sys, threading, time

LEV = '/home/younes/arma3-marl/leviathan'
SORTIE = '/mnt/data2/lab/replay/nuit0'
CRIT = os.path.join(LEV, 'CRITERES_NUIT0.md')
EMPREINTE_ATTENDUE = '4745631a705e79c0'
MODES = ['frontal', 'supfront', 'envelop', 'reckless']

ap = argparse.ArgumentParser()
ap.add_argument('--n', type=int, default=20, help='episodes par case (mode, A)')
ap.add_argument('--ags', default='4,8,12')
ap.add_argument('--instances', type=int, default=14)
a = ap.parse_args()

emp = hashlib.sha256(open(CRIT, 'rb').read()).hexdigest()[:16]
if emp != EMPREINTE_ATTENDUE:
    sys.exit('REFUS : criteres modifies (%s au lieu de %s). Rien ne demarre.' % (emp, EMPREINTE_ATTENDUE))
os.makedirs(SORTIE, exist_ok=True)

# VERROU. Le 30/07 un second exemplaire de ce run s est lance pendant le premier : les deux se
# sont battus pour les memes instances, 228 echecs en 6 minutes, et la case decisive n a jamais
# ete collectee. Un run de ferme est exclusif.
VERROU = '/tmp/nuit0.lock'
_fd = os.open(VERROU, os.O_CREAT | os.O_RDWR)
try:
    import fcntl
    fcntl.flock(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    sys.exit('REFUS : un autre exemplaire de nuit0 tourne deja (verrou %s).' % VERROU)

verrou = threading.Lock()
AGS = [int(x) for x in a.ags.split(',')]
taches = queue.Queue()
for A in AGS:
    for m in MODES:
        for r in range(1, a.n + 1):
            # REPRISE : un episode deja sur le disque ne se rejoue pas. La collecte est
            # idempotente, donc interruptible sans perte.
            if os.path.exists(os.path.join(SORTIE, 'n0_%s_A%d_r%02d.json' % (m, A, r))):
                continue
            taches.put((m, A, r))
TOTAL = taches.qsize()
print('=== NUIT 0 : %d episodes (%d modes x %d rapports x %d rep) sur %d instances ==='
      % (TOTAL, len(MODES), len(AGS), a.n, a.instances), flush=True)

etat = {'faits': 0, 'echecs': 0, 'debut': time.time()}
par_instance = {i: 0 for i in range(a.instances)}


ERREURS = os.path.join(SORTIE, 'erreurs.txt')
_n_err = [0]


def lancer(cmd, secondes, env):
    # On GARDE la sortie d erreur des 20 premiers echecs. Le 30/07 les 240 episodes ont echoue en
    # une minute, sortie jetee dans /dev/null : une heure perdue a re-jouer un episode a la main
    # pour lire un message qu on avait deja produit 240 fois.
    try:
        r = subprocess.run(cmd, cwd=LEV, env=env, timeout=secondes,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if r.returncode != 0 and _n_err[0] < 20:
            _n_err[0] += 1
            with verrou:
                with open(ERREURS, 'a') as f:
                    f.write('--- %s (code %d)\n%s\n' % (' '.join(cmd), r.returncode,
                                                          r.stderr.decode('utf-8', 'ignore')[-1500:]))
        return r.returncode
    except subprocess.TimeoutExpired:
        return -9


def ouvrier(idx):
    th = 'ferme%d' % idx
    env = dict(os.environ, HMT_THEATRE=th)
    while True:
        try:
            mode, A, rep = taches.get_nowait()
        except queue.Empty:
            return
        nom = 'n0_%s_A%d_r%02d' % (mode, A, rep)
        tmp = os.path.join(LEV, nom + '.json')
        lancer(['python3', 'poser_fob.py', '8'], 180, env)
        lancer(['python3', 'envelop_arma.py', 'setup', '--theatre', th, '--nag', str(A)], 180, env)
        c = lancer(['python3', 'envelop_arma.py', 'run', '--theatre', th, '--mode', mode,
                    '--nag', str(A), '--steps', '120', '--offset', '45', '--standoff', '70',
                    '--flank', '0.45', '--assault_tick', '24', '--out', nom + '.json'], 600, env)
        lancer(['python3', 'envelop_arma.py', 'disarm', '--theatre', th], 150, env)
        ok = False
        if c == 0 and os.path.exists(tmp):
            try:
                d = json.load(open(tmp))
                d['_meta'] = {'mode': mode, 'A': A, 'rep': rep, 'instance': idx, 'ts': int(time.time())}
                json.dump(d, open(os.path.join(SORTIE, nom + '.json'), 'w'))
                os.remove(tmp)
                ok = True
            except Exception:
                pass
        with verrou:
            etat['faits'] += 1
            if not ok:
                etat['echecs'] += 1
            par_instance[idx] += 1
            n, ec = etat['faits'], etat['echecs']
            ecoule = time.time() - etat['debut']
        if n % 10 == 0 or n == TOTAL:
            print('  %3d/%d faits (%d rates) — %.0f min ecoulees, %.0f ep/h'
                  % (n, TOTAL, ec, ecoule / 60.0, n * 3600.0 / max(ecoule, 1)), flush=True)


fils = [threading.Thread(target=ouvrier, args=(i,), daemon=True) for i in range(a.instances)]
for f in fils:
    f.start()
for f in fils:
    f.join()

print('=== fin : %d episodes, %d rates, %.0f min ==='
      % (etat['faits'], etat['echecs'], (time.time() - etat['debut']) / 60.0))
print('  debit par instance : %s' % ' '.join('%d:%d' % (k, v) for k, v in sorted(par_instance.items())))
print('NUIT0_DONE')
