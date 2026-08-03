#!/usr/bin/env python3
"""debit_et_canari.py — point de controle de DEBIT + CANARI de l audit, sur l instance de dev.

Criteres de debit (specification de l architecte) :
  - zero trou de numerotation de tick
  - cout p95 de l emetteur < 5 ms a densite reelle
  - FPS serveur a moins de 20 % sous son niveau AVANT capture
Le niveau de reference est pris AVANT d installer la capture, a la MEME densite : sinon on compare
deux mondes. Et sous les mods du juge, jamais en vanilla — le monde mode remplit le journal
beaucoup plus, donc un debit mesure nu ne transfere pas.

CANARI (controle 2 de l audit) : une entite isolee, un bond delibere de +500 m, puis suppression.
L audit doit compter pour CETTE entite exactement une teleportation et une disparition.

Usage : debit_et_canari.py --instance 12 [--unites 240] [--minutes 5]
"""
import argparse, json, os, statistics, subprocess, sys, time

sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge

SB = '/mnt/data/harmattan-sandbox'
CAP = '/home/younes/arma3-marl/leviathan/capture'
ap = argparse.ArgumentParser()
ap.add_argument('--instance', type=int, default=12)
ap.add_argument('--unites', type=int, default=240)
ap.add_argument('--minutes', type=float, default=5.0)
ap.add_argument('--dt', type=float, default=0.2)
a = ap.parse_args()
PORT = 5801 + a.instance
JOURNAL = '%s/logs/server%d.out' % (SB, a.instance)
SESSION = 'debit'


def fps(b, n=8):
    v = []
    for _ in range(n):
        r = b.query('(format ["FPS %1 %2", round (diag_fps * 100), count (allUnits + allDeadMen)]) call HMT_EMIT;',
                    r'FPS (\d+) (\d+)', want=1, timeout=15)
        if r:
            v.append((int(r[-1].group(1)) / 100.0, int(r[-1].group(2))))
        time.sleep(2)
    return v


print('=== densite reelle : %d unites autour de l objectif ===' % a.unites)
b = NativeBridge(port=PORT, timeout=15)
# deux camps disperses sur ~600 m, en groupes de 8 : de vrais groupes qui se voient et se battent
sqf = ('if (!isNil "HMT_D") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D }; '
       'HMT_D = []; private _c = [16781, 12604, 0]; '
       'for "_g" from 0 to %d do { '
       '  private _cote = if (_g %% 2 == 0) then {east} else {west}; '
       '  private _gr = createGroup _cote; '
       '  private _ang = _g * 37; private _ray = 120 + (_g %% 5) * 90; '
       '  private _p = [(_c select 0) + _ray * sin _ang, (_c select 1) + _ray * cos _ang, 0]; '
       '  for "_i" from 1 to 8 do { '
       '    private _t = if (_cote == east) then {"O_Soldier_F"} else {"B_Soldier_F"}; '
       '    private _u = _gr createUnit [_t, _p, [], 12, "NONE"]; '
       '    _u setSkill 0.5; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; '
       '    HMT_D pushBack _u; }; }; '
       '(format ["DENSITE %%1", count HMT_D]) call HMT_EMIT;' % max(0, a.unites // 8 - 1))
r = b.query(sqf, r'DENSITE (\d+)', want=1, timeout=180)
print('  unites posees : %s' % (r[-1].group(1) if r else 'ECHEC'))
if not r:
    b.close(); sys.exit('ARRET : la pose a echoue.')
print('  ... 45 s pour que le monde se mette en marche')
time.sleep(45)

print('=== FPS de reference, AVANT capture, a cette densite ===')
avant = fps(b)
f_avant = statistics.median([x[0] for x in avant]) if avant else 0
print('  FPS median %.1f  (unites vues : %s)' % (f_avant, avant[-1][1] if avant else '?'))

# LE LECTEUR D ABORD. Le 31/07, il demarrait apres l installation et manquait la premiere passe
# du recenseur : 1 apparition enregistree sur 240, donc 62 % de fantomes a l audit.
print('=== lecteur de journal (AVANT installation) ===')
proc = subprocess.Popen(['/home/younes/env_isaaclab/bin/python3', os.path.join(CAP, 'capture_tail.py'),
                         '--journal', JOURNAL, '--instance', str(a.instance),
                         '--dt', str(a.dt), '--horodatage', SESSION],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(5)
if proc.poll() is not None:
    print(proc.stdout.read()[-600:]); sys.exit('ARRET : lecteur refuse.')

print('=== installation de la capture ===')
b.send('[%d, %s] execVM "capture\\hmt_capture.sqf";' % (a.instance, a.dt), wait=True, timeout=25)
time.sleep(10)
b.close()
txt = open(JOURNAL, errors='ignore').read()
import re
oks = sorted(set(re.findall(r'HMT\|OK\|(\w+)\|', txt)))
print('  morceaux annonces : %s' % oks)
if len(oks) < 4:
    proc.terminate(); sys.exit('ARRET : la capture ne s est pas annoncee entierement.')

print('=== %.0f min de capture a densite reelle ===' % a.minutes)
b = NativeBridge(port=PORT, timeout=15)
apres = fps(b)
f_apres = statistics.median([x[0] for x in apres]) if apres else 0
print('  FPS median PENDANT capture : %.1f' % f_apres)

print('=== canari : bond delibere de +500 m puis suppression ===')
r = b.query('HMT_CANARI = (createGroup east) createUnit ["O_Soldier_F", [16781,13200,0], [], 0, "NONE"]; '
            'HMT_CANARI setPosATL [16781,13200,0]; HMT_CANARI disableAI "PATH"; '
            '(format ["CANARI %1", 1]) call HMT_EMIT;', r'CANARI (\d+)', want=1, timeout=30)
time.sleep(6)
r2 = b.query('(format ["CANARI_ID %1", HMT_CANARI getVariable ["hmt_id", -1]]) call HMT_EMIT;',
             r'CANARI_ID (-?\d+)', want=1, timeout=20)
cid = int(r2[-1].group(1)) if r2 else -1
print('  identifiant du canari : %d' % cid)
time.sleep(4)
b.send('HMT_CANARI setPosASL [(getPosASL HMT_CANARI select 0) + 500, getPosASL HMT_CANARI select 1, getPosASL HMT_CANARI select 2];', wait=True, timeout=20)
time.sleep(4)
b.send('deleteVehicle HMT_CANARI;', wait=True, timeout=20)
time.sleep(6)

reste = max(0.0, a.minutes * 60 - 60)
print('  ... %.0f s de capture restante' % reste)
b.close()
time.sleep(reste)

b = NativeBridge(port=PORT, timeout=15)
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_D; HMT_D = [];', wait=False)
b.close()
time.sleep(4)
proc.terminate()
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()

D = '/mnt/data2/lab/replay/openworld/inst%d/%s' % (a.instance, SESSION)
meta = json.load(open(os.path.join(D, 'meta.json')))
cout = [float(c.split('|')[1]) for c in meta.get('cout', []) if c.startswith('cout_ms|')]
print()
print('=== POINT DE CONTROLE DE DEBIT ===')
print('  ticks %d | trous %d | incomplets ? voir audit | dt observe %s | bascules journal %d'
      % (meta['ticks'], len(meta['trous_tick']), meta.get('dt_observe'), len(meta.get('bascules_journal', []))))
print('  cout de l emetteur : %s ms (moyennes par tranche de 300 ticks)'
      % (', '.join('%.2f' % c for c in cout) if cout else 'non rapporte'))
p95 = None
if cout:
    p95 = sorted(cout)[min(len(cout) - 1, int(0.95 * len(cout)))]
chute = (100.0 * (f_avant - f_apres) / f_avant) if f_avant else 0
print('  FPS %.1f -> %.1f  (chute %.1f %%)' % (f_avant, f_apres, chute))
v = []
v.append(('zero trou de tick', len(meta['trous_tick']) == 0, '%d trous' % len(meta['trous_tick'])))
v.append(('cout emetteur < 5 ms', (p95 is not None and p95 < 5.0), ('p95 %.2f ms' % p95) if p95 else 'non mesure'))
v.append(('chute de FPS < 20 %%', chute < 20.0, 'chute %.1f %%' % chute))
for nom, ok, det in v:
    print('  [%s] %s (%s)' % ('OK ' if ok else 'RATE', nom, det))

print()
print('=== CANARI (controle 2 de l audit) ===')
evts = [json.loads(l) for l in open(os.path.join(D, 'events.jsonl'))]
etats = [json.loads(l) for l in open(os.path.join(D, 'state.jsonl'))]
disp = [e for e in evts if e['evt'] == 'despawn' and e['id'] == cid]
import math
tel = 0
last = None
for x in sorted(etats, key=lambda z: z['t']):
    for e in x['ents']:
        if e[0] == cid:
            if last:
                dt = x['t'] - last[0]
                if dt > 0 and math.hypot(e[1] - last[1], e[2] - last[2]) / dt > 60.0:
                    tel += 1
            last = (x['t'], e[1], e[2])
print('  teleportations du canari : %d (attendu 1)' % tel)
print('  disparitions du canari   : %d (attendu 1)' % len(disp))
ok_can = (tel == 1 and len(disp) == 1)
print('  [%s] canari compte exactement' % ('OK ' if ok_can else 'RATE'))
print()
print('=== AUDIT DE LA SESSION ===')
subprocess.run(['/home/younes/env_isaaclab/bin/python3', os.path.join(CAP, 'audit_contamination.py'),
                '--session', D])
print()
print('DEBIT_CANARI_%s' % ('OK' if (all(x[1] for x in v) and ok_can) else 'RATE'))
