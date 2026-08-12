#!/usr/bin/env python3
"""sonde_actuation — L ACTUATION OU LA POLITIQUE ? Le discriminant.

Au banc live, huit hommes sont morts en sept pas SANS GAGNER DEUX METRES. Deux causes
possibles, et on ne peut pas trancher en regardant : soit la politique choisit mal, soit
l ordre de deplacement ne les deplace pas.

On retire donc la politique du tableau. Aucun defenseur, aucune decision : on impose le MEME
cap a tous, et on mesure le deplacement.

DEUX BRAS, et le second est le controle positif :
  A — `setVelocity` UNE FOIS par pas, exactement comme la couture le fait aujourd hui.
  B — `setVelocity` REAPPLIQUE A CHAQUE IMAGE, via un `EachFrame` — la technique de
      `move_combat.py`, qui a ete ecrit precisement pour cette question.

⚠️ CE QUI EST ATTENDU, ECRIT AVANT DE LANCER :
  · si A ne bouge pas et B bouge -> L ACTUATION est en cause, la politique est innocentee,
    et le remede est connu : soutenir la vitesse a chaque image.
  · si A et B bougent tous les deux -> l actuation marche, et c est LA POLITIQUE qui a
    conduit huit hommes a mourir sur place.
  · si NI A NI B ne bouge -> ce n est aucun des deux : c est la pose des hommes (PATH coupe,
    ou une contrainte du moteur), et il faut chercher ailleurs. Ce troisieme cas est ecrit
    ici pour ne pas etre invente apres coup.
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

EXT = 5830
CAP = 6.0          # m/s, comme la couture
DUREE = 8          # secondes de poussee

POSE = '''
HMT_OBJ = [1734, 5391, 0];
private _g = createGroup west; HMT_T = [];
for "_i" from 1 to 4 do {
    private _p = [(HMT_OBJ select 0) + (_i * 8), (HMT_OBJ select 1) + 200, 0];
    private _u = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u allowDamage false;
    _u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE";
    HMT_T pushBack _u;
};
HMT_P0 = []; { HMT_P0 pushBack (getPosATL _x) } forEach HMT_T;
diag_log format ["SONDE_POSE n=%1", count HMT_T];
'''

MESURE = '''
private _d = 0;
{ private _a = HMT_P0 select _forEachIndex; private _b = getPosATL _x;
  _d = _d + sqrt (((_b select 0)-(_a select 0))^2 + ((_b select 1)-(_a select 1))^2);
} forEach HMT_T;
diag_log format ["SONDE_DEPL %1", round (_d / (count HMT_T))];
'''

A_UNE_FOIS = 'HMT_V=[0,%f,0]; { _x setVelocity HMT_V } forEach HMT_T; diag_log "SONDE_A push";' % CAP
B_CHAQUE_IMAGE = ('HMT_V=[0,%f,0]; HMT_EH = addMissionEventHandler ["EachFrame", '
                  '{ { _x setVelocity HMT_V } forEach HMT_T }]; diag_log "SONDE_B on";' % CAP)
B_STOP = 'removeMissionEventHandler ["EachFrame", HMT_EH]; diag_log "SONDE_B off";'


def lire(b, motif, delai=3.0):
    t0 = time.time()
    while time.time() - t0 < delai:
        for L in reversed(b._log_lines(400)):
            m = re.search(motif, L)
            if m: return m.group(1)
        time.sleep(0.2)
    return None


b = SocketBridge(EXT)
print(f"  pont ouvert (n={b.n})\n", flush=True)

for nom, pousser in (("A  une fois par pas ", A_UNE_FOIS), ("B  a chaque image   ", B_CHAQUE_IMAGE)):
    b.send(POSE); time.sleep(2)
    if lire(b, r"SONDE_POSE n=(\d+)") is None:
        print(f"  {nom} : la pose a echoue"); continue
    t0 = time.time()
    while time.time() - t0 < DUREE:
        b.send(pousser, wait=False)          # A : on repousse a chaque pas, comme la couture
        time.sleep(3.28 if nom.startswith("A") else DUREE)
    if nom.startswith("B"):
        b.send(B_STOP, wait=False); time.sleep(0.5)
    b.send(MESURE, wait=False)
    d = lire(b, r"SONDE_DEPL (\d+)")
    attendu = CAP * DUREE
    print(f"  {nom} : deplacement moyen {d} m   (une poussee continue en donnerait ~{attendu:.0f})",
          flush=True)
b.sock.close()
