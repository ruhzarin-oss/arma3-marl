import sys
sys.path.insert(0, "/home/younes/arma3-marl")
from train_soldier import run

# SCENARIO DUR : couvert existe (relief 40) MAIS defenseurs nombreux+letaux
# -> survivre a decouvert devient impossible -> le couvert (la coque) devient essentiel.
ITERS, ENVS = 250, 8192
A, D, relief, hit = 1, 4, 40.0, 0.20
print("=== SCENARIO DUR : A=%d vs D=%d relief=%.0f hit=%.2f ===" % (A, D, relief, hit), flush=True)
rs, ls = run(True,  ITERS, ENVS, A, D, relief, hit, 0, tag="hard_shell")
rb, lb = run(False, ITERS, ENVS, A, D, relief, hit, 0, tag="hard_noshell")
print(">>> DUR neutralises: COQUE %.0f%% (pertes %.0f%%) | SANS %.0f%% (pertes %.0f%%) | ecart %+.0f pts"
      % (100*rs, 100*ls, 100*rb, 100*lb, 100*(rs-rb)), flush=True)
print("HARD FINI", flush=True)
