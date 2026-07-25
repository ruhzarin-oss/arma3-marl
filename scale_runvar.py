import sys
sys.path.insert(0, "/home/younes/arma3-marl")
from train_soldier import run

# Chemin EPROUVE (train_soldier.run), coque seule, bande D=2 h0.16, 5 repetitions.
# But : variance du chemin de reference vs mon harnais (qui donne 0%).
print("=== run() eprouve : coque D=2 h0.16 x5 ===", flush=True)
sc = []
for s in range(5):
    r, l = run(True, 150, 8192, 1, 2, 40.0, 0.16, s, tag="rv")
    sc.append(100 * r)
    print(">>> seed %d : %.0f%%" % (s, 100 * r), flush=True)
print(">>> moy %.0f  min %.0f  max %.0f" % (sum(sc)/len(sc), min(sc), max(sc)), flush=True)
print("RUNVAR FINI", flush=True)
