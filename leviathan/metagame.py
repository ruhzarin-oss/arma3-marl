#!/usr/bin/env python3
"""metagame — la MATRICE DU MÉTA-JEU (reco n°1 de Fable). Tournoi des manœuvres attaquant × défenseur
(corps scripté déterministe) -> winrate attaquant par case. Tranche entre 3 mondes :
  A. envelop domine toute réponse def -> jeu pauvre, à enrichir.
  B. une réponse def bat envelop mais la co-évo ne l'a jamais trouvée -> problème de signal.
  C. ça cycle déjà (pas de ligne dominante) -> problème d'obs/league.
+ test : une FORME défensive 360° (cercle/carré) contre-t-elle l'enveloppement ? (test de la géométrie)"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
MAN = ["assaut", "defend", "hunt", "bound", "envelop"]


@torch.no_grad()
def duel(am, dm, aform="coin", dform="demi_cercle", seeds=3):
    tot = 0.0; ne = 0
    for sd in range(seeds):
        e = DuelTerrain(num_envs=256, A=12, B=8, a_form=aform, b_form=dform, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)
        obsA, obsB = e.reset()
        e.a_maneuver = torch.full((e.N,), am, dtype=torch.long, device=DEV)
        e.b_maneuver = torch.full((e.N,), dm, dtype=torch.long, device=DEV)
        w = 0.0; nep = 0; done_once = torch.zeros(e.N, dtype=torch.bool, device=DEV)
        for t in range(60):
            aA = repertoire_action(e, 0); aB = repertoire_action(e, 1)
            (obsA, obsB), _, done, info = e.step(aA, aB, auto_reset=False); d2 = done.bool() & ~done_once
            if d2.any(): w += info["att_wins"][d2].float().sum().item(); nep += int(d2.sum())
            done_once |= done.bool()
        tot += w; ne += nep
    return tot / max(ne, 1)


print("=== MATRICE MÉTA-JEU : winrate ATTAQUANT (ligne = manœuvre ATT, colonne = manœuvre DEF) ===")
print("            " + "".join("%-9s" % m for m in MAN))
mat = []
for am in range(5):
    row = [duel(am, dm) for dm in range(5)]
    mat.append(row)
    print("%-11s " % MAN[am] + "".join("%-9.2f" % r for r in row))
# ligne dominante ? (une manœuvre att qui gagne le plus contre TOUTES les réponses def)
best_worst = [min(row) for row in mat]   # pire cas de chaque manœuvre att
dom = best_worst.index(max(best_worst))
print("\n  meilleure manœuvre att au PIRE cas = %s (%.2f). Si envelop domine partout -> monde A." % (MAN[dom], best_worst[dom]))

print("\n=== TEST GÉOMÉTRIE : envelop ATT vs FORME défensive (def en 'defend') — le 360° contre-t-il ? ===")
for dform in ["ligne", "demi_cercle", "cercle", "carre", "colonne"]:
    print("  def %-12s : att-gagne %.2f" % (dform, duel(4, 1, dform=dform)))
print("METAGAME_DONE")
