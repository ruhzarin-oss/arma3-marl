#!/usr/bin/env python3
# Ajoute l'option replica a train_soldier.run (terrain = la replique du complexe).
s = open("train_soldier.py").read()
A = 'def run(shell, iters, envs, A, D, relief, hit, seed, rollout=16, tag="soldier"):'
assert s.count(A) == 1, "ancre run introuvable"
s = s.replace(A, 'def run(shell, iters, envs, A, D, relief, hit, seed, rollout=16, tag="soldier", replica=False):')
B = '    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=relief, hit=hit, shell_obs=shell, max_steps=60, device=DEV, seed=seed)'
assert s.count(B) == 1, "ancre env introuvable"
s = s.replace(B, '    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=relief, hit=hit, shell_obs=shell, max_steps=60,\n'
                  '                         replica=replica, replica_path="/home/younes/arma3-marl/replica.npz", device=DEV, seed=seed)')
open("train_soldier.py", "w").write(s)
print("PATCH trainrep OK")
