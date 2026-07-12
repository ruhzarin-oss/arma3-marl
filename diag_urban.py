"""diag_urban — CARACTERISE LE MUR URBAIN. Un assaut RL (8 h, cerveau gele, posture assault) face a 20 defenseurs
retranches dans le bati dense du centre de Paros. On mesure a chaque pas :
  - dist mini assaut->defenseur (se rapproche-t-il en CQB, ou cale-t-il en surplomb ?)
  - defenseurs colles au bati / assaillants entres dans le bati
  - defenseurs tues (l'assaut nettoie-t-il, ou pas ?)
Sortie -> /tmp/diag_urban.out (on la lit ensuite)."""
import time, re
import numpy as np
import torch
from op_arma import OpArma, STANCES
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
CX, CY = M.COMPLEXE
brain = Net(10, 4, 512, 3).to(DEV); brain.load_state_dict(torch.load("koth_finetuned.pt", map_location=DEV)); brain.eval()
env = OpArma(squads=(("ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge2.Altis",
             log=SB + "/logs/server2.out", move=30, acc=1.0, seed=5)
print("spawn : assaut(8) a 70m sud + 20 defenseurs dans le bati de Paros", flush=True)
env.spawn({"ASSAUT": (CX, CY - 70)}, [(CX, CY, 20, 12)])
env._query('{ private _g=_x; while {count waypoints _g > 0} do {deleteWaypoint [_g,0]}; { _x setBehaviour "COMBAT"; doStop _x } forEach units _g; } forEach (allGroups select {side _x == east}); diag_log "HARMATTAN_OK";', settle=1.0)
env.read()
env.goals[0] = np.array([CX, CY], dtype=float); env.stances[0] = "assault"


def act():
    o = env.obs(0)
    with torch.no_grad():
        lg = brain.a_logits(torch.as_tensor(o, dtype=torch.float32, device=DEV)) + torch.as_tensor(STANCES["assault"], device=DEV)
    return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()


print("pas | dist_mini | def_vivants | def_au_bati | assaut_au_bati | assaut_vivants", flush=True)
for step in range(1, 31):
    env.step([act()])
    env.b.send('{ if (alive _x) then {doStop _x} } forEach HMT_EN;', wait=True)         # defenseurs statiques (ils tiennent + tirent)
    al = env.alive(0); eal = env.en_alive()
    if al.any() and eal.any():
        d = np.sqrt((env.px[0][al][:, None] - env.epx[eal][None, :]) ** 2 + (env.py[0][al][:, None] - env.epy[eal][None, :]) ** 2)
        mind = int(d.min())
    else:
        mind = -1
    ls = env._query('private _hb = { (alive _x) && {(count (_x nearObjects ["House",10])) > 0} } count HMT_EN;'
                    'private _ha = { (alive _x) && {(count (_x nearObjects ["House",10])) > 0} } count ASSAUT;'
                    'diag_log format ["HARMATTAN_BLD defbati=%1 assbati=%2", _hb, _ha];', settle=0.7)
    defb = assb = -1
    for l in ls:
        m = re.search(r"HARMATTAN_BLD defbati=(\d+) assbati=(\d+)", l)
        if m:
            defb, assb = int(m.group(1)), int(m.group(2))
    if step % 2 == 0 or step <= 4:
        print("%3d | %8d | %10d | %10d | %12d | %d" % (step, mind, int(eal.sum()), defb, assb, int(al.sum())), flush=True)
print("FINI", flush=True)
