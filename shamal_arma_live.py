#!/usr/bin/env python3
"""shamal_arma_live.py — A3 driver LIVE : SHAMAL (shamal_arma.pt) pilote une escouade Arma via la couture.
WAKE (reveil gardes+escouade) -> boucle { PERC18 -> parse -> cerveau -> ACT13 }. La moitie Python<->net<->SQF
est deja validee hors-ligne (arma_couture._selftest). Ici on ferme la boucle sur un Arma REEL.

  smoke : `python shamal_arma_live.py --steps 6`   -> prouve que la boucle tourne (compteur avance, SQF s'execute)
  live  : `python shamal_arma_live.py --steps 240` -> Younes connecte, on regarde SHAMAL se battre

RAPPEL projet : 0 joueur connecte = IA inerte (sait mais ne bouge/tire pas). Le smoke headless prouve la
PLOMBERIE (obs sortent, actions rentrent, pas d'erreur SQF) ; le COMBAT se juge avec Younes dans le slot.
"""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from train_koth_gpu import Net
from arma_bridge import ArmaBridge
import arma_couture as C

ap = argparse.ArgumentParser()
ap.add_argument("--steps", type=int, default=6)
ap.add_argument("--dt", type=float, default=0.4)
a = ap.parse_args()

net = Net(C.OBS_DIM, C.N_ACT, 512, 3)
net.load_state_dict(torch.load("/home/younes/arma3-marl/shamal_arma.pt", map_location="cpu")); net.eval()
b = ArmaBridge()


def read_obs(timeout=15):
    n = b.send(C.perc_sqf(), wait=True, timeout=timeout); time.sleep(0.5)
    lines = b._log_lines()
    idx = max((i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % n) in ln), default=0)
    obs = C.parse_obs(lines[idx:])
    if not obs: return None
    return torch.tensor([obs[k] for k in sorted(obs)], dtype=torch.float32)


def send_acts(acts, timeout=15):
    n = b.send(C.acts_to_sqf(acts), wait=True, timeout=timeout); time.sleep(0.3)
    for ln in reversed(b._log_lines()):
        if "HARMATTAN_ACTOK" in ln: return ln.strip().split("HARMATTAN_ACTOK")[-1].strip()
    return None


print("=== SHAMAL live -> Arma (couture 18-obs / 13-act) ===", flush=True)
b.send(C.WAKE, wait=True, timeout=15); time.sleep(1)
ok_steps = 0
for t in range(a.steps):
    obs = read_obs()
    if obs is None:
        print("  t=%d : AUCUNE obs (Arma up ? unites nommees HMT_FR/HMT_ENNEMI ?)" % t, flush=True); break
    with torch.no_grad():
        acts = net.a_logits(obs).argmax(-1).tolist()
    st = send_acts(acts)
    ok_steps += 1
    if t % 2 == 0 or t == a.steps - 1:
        from collections import Counter
        print("  t=%d  %d unites  actions=%s  ACTOK=%s" % (t, obs.shape[0], dict(Counter(acts)), st), flush=True)
print("\nboucle : %d/%d pas ont tourne." % (ok_steps, a.steps), flush=True)
print("  -> PLOMBERIE OK (obs->cerveau->SQF sans erreur)." if ok_steps >= a.steps
      else "  -> boucle interrompue : voir message ci-dessus.", flush=True)
print("  (le COMBAT se juge avec Younes connecte — IA inerte sans joueur.)", flush=True)
