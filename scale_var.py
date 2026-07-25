import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from scale_block import train   # reutilise la boucle du harnais

# Quantifie le BRUIT : meme config (coque seule, bande de forcage) repetee 5x.
# (le net + l'exploration ne sont pas seedes -> chaque run = cerveau different)
A, D, hit = 1, 2, 0.16
scores = []
for r in range(5):
    s = train(A, D, hit, iters=150, seed=r, shell_obs=True)
    scores.append(100 * s)
    print(">>> run %d : %.0f%%" % (r, 100 * s), flush=True)
import statistics as st
print(">>> coque seule : moy %.0f%%  min %.0f  max %.0f  ecart-type %.0f"
      % (st.mean(scores), min(scores), max(scores), st.pstdev(scores)), flush=True)
print("VAR FINI", flush=True)
