#!/usr/bin/env python3
"""canari_setdamage.py — CONTROLE 4 de l audit, cote serveur : la coupe neuve sait-elle mordre ?

Criteres v2 (b7a64e476c3ea211). La coupe seuillee est « morts sans tueur tracable et recense ».
Sur le corpus reel elle a donne 0 sur 51 — un resultat qu on n a PAS le droit de croire tant qu on
n a pas montre qu une mort illegitime la fait compter. Une coupe qui ne sait pas echouer n a pas le
droit de passer.

On tue donc une unite isolee par script, SANS agresseur (degats poses directement). La coupe doit
compter exactement 1 sur 1.

Usage : canari_setdamage.py --instance 12
"""
import argparse, json, os, re, subprocess, sys, time

sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge

SB = '/mnt/data/harmattan-sandbox'
CAP = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--instance', type=int, default=12)
ap.add_argument('--dt', type=float, default=0.2)
a = ap.parse_args()
PORT = 5801 + a.instance
JOURNAL = '%s/logs/server%d.out' % (SB, a.instance)
SESSION = 'canari_sd'
D = '/mnt/data2/lab/replay/openworld/inst%d/%s' % (a.instance, SESSION)

print('=== CANARI setDamage — la coupe « morts sans tueur » sait-elle mordre ? ===')
# le lecteur AVANT l installation, sinon la premiere passe du recenseur est perdue
proc = subprocess.Popen(['/home/younes/env_isaaclab/bin/python3', os.path.join(CAP, 'capture_tail.py'),
                         '--journal', JOURNAL, '--instance', str(a.instance),
                         '--dt', str(a.dt), '--horodatage', SESSION],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(5)
if proc.poll() is not None:
    print(proc.stdout.read()[-600:]); sys.exit('ARRET : lecteur refuse.')

b = NativeBridge(port=PORT, timeout=15)
b.send('[%d, %s] execVM "capture\\hmt_capture.sqf";' % (a.instance, a.dt), wait=True, timeout=25)
time.sleep(10)
txt = open(JOURNAL, errors='ignore').read()
if len(set(re.findall(r'HMT\|OK\|(\w+)\|', txt))) < 4:
    proc.terminate(); sys.exit('ARRET : la capture ne s est pas annoncee.')

# UNE unite isolee, loin de tout, qui ne se battra avec personne : la seule mort du corpus.
r = b.query('if (!isNil "HMT_SD") then { if (!isNull HMT_SD) then {deleteVehicle HMT_SD} }; '
            'HMT_SD = (createGroup east) createUnit ["O_Soldier_F", [16781, 13600, 0], [], 0, "NONE"]; '
            'HMT_SD setPosATL [16781, 13600, 0]; HMT_SD disableAI "PATH"; HMT_SD setBehaviour "CARELESS"; '
            '(format ["POSE %1", alive HMT_SD]) call HMT_EMIT;', r'POSE (\w+)', want=1, timeout=40)
print('  unite isolee posee : %s' % (r[-1].group(1) if r else 'ECHEC'))
if not r:
    proc.terminate(); b.close(); sys.exit('ARRET : la pose a echoue.')
time.sleep(8)
r2 = b.query('(format ["ID %1", HMT_SD getVariable ["hmt_id", -1]]) call HMT_EMIT;',
             r'ID (-?\d+)', want=1, timeout=20)
cid = int(r2[-1].group(1)) if r2 else -1
print('  identifiant : %d (le recenseur l a vue)' % cid)
time.sleep(4)

# LA MORT ILLEGITIME : degats poses directement, aucun agresseur.
print('  -> setDamage 1, sans aucun agresseur')
b.send('HMT_SD setDamage 1;', wait=True, timeout=20)
time.sleep(10)
b.send('if (!isNull HMT_SD) then {deleteVehicle HMT_SD};', wait=False)
b.close()
time.sleep(5)
proc.terminate()
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()

evts = [json.loads(l) for l in open(os.path.join(D, 'events.jsonl'))]
morts = [e for e in evts if e['evt'] == 'killed']
print()
print('  morts dans le corpus : %d' % len(morts))
for m in morts:
    print('    victime %s | tueur %s' % (m['victim'], m['killer']))
print()
print('=== VERDICT DE L AUDIT v2 SUR CE CORPUS ===')
subprocess.run(['/home/younes/env_isaaclab/bin/python3', os.path.join(CAP, 'audit_contamination.py'),
                '--session', D])
sans = 0
sp = {e['id'] for e in evts if e['evt'] == 'spawn'}
for m in morts:
    k = m.get('killer', -1)
    if k < 0 or k == m['victim'] or k not in sp:
        sans += 1
print()
ok = (len(morts) == 1 and sans == 1)
print('  attendu : 1 mort, 1 sans tueur tracable')
print('  obtenu  : %d mort(s), %d sans tueur tracable' % (len(morts), sans))
print('CANARI_SETDAMAGE_%s' % ('OK' if ok else 'RATE'))
if not ok:
    print('  -> la coupe neuve ne sait pas mordre : elle est infalsifiable, on ne lance rien.')
