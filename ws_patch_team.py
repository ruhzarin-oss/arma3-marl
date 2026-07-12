#!/usr/bin/env python3
# Ajoute team_obs (conscience d'equipe -> feu+mouvement) a train_soldier.run.
s = open("train_soldier.py").read()
A = 'def run(shell, iters, envs, A, D, relief, hit, seed, rollout=16, tag="soldier", replica=False):'
assert s.count(A) == 1, "ancre run"
s = s.replace(A, 'def run(shell, iters, envs, A, D, relief, hit, seed, rollout=16, tag="soldier", replica=False, team_obs=False):')
B = '    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=relief, hit=hit, shell_obs=shell, max_steps=60,'
assert s.count(B) == 1, "ancre env"
s = s.replace(B, '    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=relief, hit=hit, shell_obs=shell, team_obs=team_obs, max_steps=60,')
open("train_soldier.py", "w").write(s)
print("PATCH team OK")
