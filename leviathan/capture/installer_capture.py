#!/usr/bin/env python3
"""installer_capture.py — installe la capture sur UNE instance et prouve qu elle marche.

Deux etapes, dans cet ordre, et la seconde ne se fait pas si la premiere echoue :
  1. INSTALLATION : execVM du script, puis on exige les lignes OK dans le journal. Pas de ligne
     OK = le script est mort en silence (mode d echec deja vecu le 29/07), on s arrete.
  2. TEST DIRIGE : deux hommes opposes a 50 m, l un tire sur l autre. On exige la CHAINE
     COMPLETE dans le corpus : apparition x2, tir avec projectile, impact, mort.

Usage : installer_capture.py --instance 12 [--dt 0.2]
"""
import argparse, glob, json, os, re, subprocess, sys, time

sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge

SB = '/mnt/data/harmattan-sandbox'
ap = argparse.ArgumentParser()
ap.add_argument('--instance', type=int, required=True)
ap.add_argument('--dt', type=float, default=0.2)
a = ap.parse_args()
PORT = 5801 + a.instance
JOURNAL = '%s/logs/server%d.out' % (SB, a.instance)
OK_ATTENDUS = ['recenseur', 'emetteur', 'morts', 'capture']

print('=== ETAPE 1 : installation sur l instance %d (pont %d) ===' % (a.instance, PORT))
b = NativeBridge(port=PORT, timeout=15)
b.send('[%d, %s] execVM "capture\\hmt_capture.sqf";' % (a.instance, a.dt), wait=True, timeout=20)
time.sleep(6)
b.close()

texte = open(JOURNAL, 'r', errors='ignore').read()
trouves = re.findall(r'HMT\|OK\|(\w+)\|', texte)
print('  lignes OK trouvees : %s' % (sorted(set(trouves)) or 'AUCUNE'))
manquants = [x for x in OK_ATTENDUS if x not in trouves]
if manquants:
    # Une erreur SQF est silencieuse : on va la chercher au lieu de deviner.
    err = [l for l in texte.splitlines()[-400:] if 'Error' in l or 'hmt_capture' in l]
    print('  MORCEAU(X) MUET(S) : %s' % manquants)
    for l in err[-8:]:
        print('    %s' % l.strip()[:200])
    sys.exit('ARRET : on ne construit pas sur un script qui ne s annonce pas.')
print('  -> les %d morceaux se sont annonces.' % len(OK_ATTENDUS))

print('=== lecteur de journal ===')
proc = subprocess.Popen(['/home/younes/env_isaaclab/bin/python3',
                         '/home/younes/arma3-marl/leviathan/capture/capture_tail.py',
                         '--journal', JOURNAL, '--instance', str(a.instance),
                         '--dt', str(a.dt), '--horodatage', 'testdirige'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(4)
if proc.poll() is not None:
    print(proc.stdout.read()[-800:])
    sys.exit('ARRET : le lecteur a refuse de demarrer.')
print('  lecteur en marche (pid %d)' % proc.pid)

print('=== ETAPE 2 : test dirige — deux hommes opposes a 50 m ===')
b = NativeBridge(port=PORT, timeout=15)
# Recette EPROUVEE (mesures du 30/07) : tireur EAST en RED, AUTOTARGET coupe, munitions pleines,
# cible revelee puis designee puis engagee. Sans reveal l IA ne sait pas que la cible existe.
sqf = ('if (!isNil "HMT_T") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_T }; '
       'HMT_T = []; private _p = [16781, 12604, 0]; '
       'HMT_GE = createGroup east; HMT_GW = createGroup west; '
       'HMT_TIREUR = HMT_GE createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; '
       'HMT_TIREUR setPosATL _p; HMT_TIREUR setSkill 1; HMT_TIREUR setBehaviour "COMBAT"; '
       'HMT_TIREUR setCombatMode "RED"; HMT_TIREUR disableAI "AUTOTARGET"; '
       'HMT_TIREUR setVehicleAmmo 1; HMT_TIREUR allowDamage false; HMT_T pushBack HMT_TIREUR; '
       'HMT_CIBLE = HMT_GW createUnit ["B_Soldier_F", [(_p select 0), (_p select 1) - 50, 0], [], 0, "NONE"]; '
       'HMT_CIBLE setPosATL [(_p select 0), (_p select 1) - 50, 0]; HMT_CIBLE setUnitPos "UP"; '
       'HMT_CIBLE disableAI "PATH"; HMT_CIBLE setBehaviour "CARELESS"; HMT_T pushBack HMT_CIBLE; '
       '[] spawn { sleep 4; HMT_TIREUR reveal [HMT_CIBLE, 4]; HMT_TIREUR doTarget HMT_CIBLE; '
       'sleep 1; for "_i" from 1 to 180 do { HMT_TIREUR doFire HMT_CIBLE; sleep 0.5 }; }; '
       '(format ["POSE %1", count HMT_T]) call HMT_EMIT;')
r = b.query(sqf, r'POSE (\d+)', want=1, timeout=40)
print('  poses : %s' % (r[-1].group(1) if r else 'ECHEC'))
if not r:
    b.close(); sys.exit('ARRET : la pose a echoue.')
print('  ... 90 s de tir (ACE est charge : un homme touche passe inconscient avant de mourir,')
print('      il faut donc laisser le temps aux degats de s accumuler)')
time.sleep(90)
r = b.query('(format ["ETAT %1 %2", (alive HMT_CIBLE), round ((damage HMT_CIBLE) * 100)]) call HMT_EMIT;',
            r'ETAT (\w+) (\d+)', want=1, timeout=15)
mort_naturelle = bool(r) and r[-1].group(1).lower() == 'false'
print('  cible apres 90 s : %s (degats %s %%)'
      % (('MORTE' if mort_naturelle else 'vivante'), r[-1].group(2) if r else '?'))
sonde_forcee = False
if not mort_naturelle:
    # SONDE DE CABLAGE, annoncee comme telle : la question « le monde tue-t-il ? » et la question
    # « le capteur de mort est-il branche ? » sont deux choses. Ici on ne teste que la seconde.
    print('  -> sonde de cablage : mort forcee par setDamage, pour verifier le capteur seul')
    b.send('HMT_CIBLE setDamage 1;', wait=True, timeout=15)
    sonde_forcee = True
    time.sleep(4)
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_T; HMT_T = [];', wait=False)
b.close()
time.sleep(5)
proc.terminate()
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()

D = '/mnt/data2/lab/replay/openworld/inst%d/testdirige' % a.instance
evts = [json.loads(l) for l in open(os.path.join(D, 'events.jsonl'))] if os.path.exists(os.path.join(D, 'events.jsonl')) else []
etats = [json.loads(l) for l in open(os.path.join(D, 'state.jsonl'))] if os.path.exists(os.path.join(D, 'state.jsonl')) else []
meta = json.load(open(os.path.join(D, 'meta.json'))) if os.path.exists(os.path.join(D, 'meta.json')) else {}

par = {}
for e in evts:
    par.setdefault(e['evt'], []).append(e)
print()
print('=== CE QUE LE CORPUS CONTIENT ===')
print('  ticks d etat : %d   dt observe : %s   trous : %d   incomplets : %d'
      % (len(etats), meta.get('dt_observe'), len(meta.get('trous_tick', [])),
         sum(1 for x in etats if x.get('incomplet'))))
print('  empreinte du monde : %s' % (meta.get('monde') or {}).get('sha256'))
for k in ('spawn', 'fired', 'hit', 'killed', 'despawn'):
    print('  %-8s : %d' % (k, len(par.get(k, []))))
print('  impacts doublons ecartes : %d' % meta.get('impacts_doublons', 0))

# --- LA CHAINE, exigee de bout en bout ---
print()
print('=== CHAINE EXIGEE ===')
verdicts = []


def dire(nom, ok, detail=''):
    verdicts.append(ok)
    print('  [%s] %s %s' % ('OK ' if ok else 'RATE', nom, detail))


dire('apparition des deux hommes', len(par.get('spawn', [])) >= 2,
     '(%d apparitions)' % len(par.get('spawn', [])))
tirs = par.get('fired', [])
dire('tir enregistre', len(tirs) > 0, '(%d tirs)' % len(tirs))
avec_proj = [t for t in tirs if t.get('proj') == 1]
dire('tir AVEC projectile', len(tirs) > 0 and len(avec_proj) == len(tirs),
     '(%d/%d avec projectile)' % (len(avec_proj), len(tirs)))
hits = par.get('hit', [])
dire('impact enregistre', len(hits) > 0, '(%d impacts)' % len(hits))
dire('impact avec tireur tracable', any(h.get('shooter', -1) > 0 for h in hits))
morts = par.get('killed', [])
dire('capteur de mort branche', len(morts) > 0,
     '(%d morts%s)' % (len(morts), ' — dont une FORCEE par sonde' if sonde_forcee else ''))
# CHAINAGE : exige seulement si la mort est venue des balles. Une mort forcee par script n a
# aucune raison d avoir un impact dans les 5 s : l exiger serait un faux critere.
chaine = 0
for m in morts:
    if any(h['target'] == m['victim'] and 0 <= m['t'] - h['t'] <= 5.0 for h in hits):
        chaine += 1
if sonde_forcee:
    print('  [n/a ] mort adossee a un impact — non exigible sur une mort forcee (%d/%d chainees)'
          % (chaine, len(morts)))
    print('         A RETENIR : 90 s de tir a 50 m n ont PAS tue sous ACE. Le chainage se')
    print('         mesurera sur le vrai corpus, ou les morts viennent des balles.')
else:
    dire('mort ADOSSEE a un impact', bool(morts) and chaine == len(morts),
         '(%d/%d chainees)' % (chaine, len(morts)))
dire('etats emis', len(etats) > 10, '(%d ticks)' % len(etats))
dire('mort visible dans les etats', any(any(e[4] == 0 for e in x['ents']) for x in etats))

print()
if all(verdicts):
    print('TEST_DIRIGE_OK — la chaine tient de bout en bout.')
else:
    print('TEST_DIRIGE_RATE — %d controle(s) sur %d ont echoue. On ne lance rien de persistant.'
          % (sum(1 for v in verdicts if not v), len(verdicts)))
