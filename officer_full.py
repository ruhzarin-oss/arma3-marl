"""officer_full — L'OFFICIER INTEGRE, end-to-end : il LIT la carte tactique -> CHOISIT l'axe (LLM qwen)
-> l'EQUIPE EMERGENTE EXECUTE l'assaut -> on rapporte le RESULTAT + sa JUSTIFICATION en clair.
Une seule boucle (lit -> decide -> combat -> explique), pas trois scripts. Schema = concentre (defaut) :
mesure montre que le schema n'est pas lisible sur la carte, donc l'officier capture l'AXE (+10/-9), pas le schema."""
import torch
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
from officer_llm import tactical_map, ask_llm, NAMES
from officer_select import exposure_by_bearing, place_at
from officer_maneuver import outcome
dev = "cuda:0"


def fight_rep(net, env, kb, R=16):
    """Place l'escouade au cap kb (par env) et joue R fois (defenseurs remis a neuf) -> neutralise/pertes de-bruites."""
    accN = torch.zeros(env.N, device=dev); accL = torch.zeros(env.N, device=dev)
    for _ in range(R):
        env.ddmg.zero_(); env.dsupp.zero_(); place_at(env, kb)
        n, l = outcome(net, env); accN += n; accL += l
    return accN / R, accL / R


if __name__ == "__main__":
    N = 12
    env = AssaultTerrain(num_envs=N, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=21)
    net = Net(env.obs_dim, env.n_actions, 256, 3).to(dev)
    net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
    env.reset(); expo = exposure_by_bearing(env)
    print("=" * 76)
    print("OFFICIER INTEGRE : lit la carte -> choisit l'axe -> l'equipe assaut -> explique")
    print("=" * 76)
    kb = torch.zeros(N, dtype=torch.long, device=dev); justs = []
    for e in range(N):
        carte, _, _ = tactical_map(env, e)
        try:
            ans = ask_llm(carte); axe = ans.get("axe", "?"); just = ans.get("justification", "")
        except Exception as ex:
            axe = NAMES[int(expo[e].argmin())]; just = "(repli scripte: %s)" % ex
        ki = NAMES.index(axe) if axe in NAMES else int(expo[e].argmin())
        kb[e] = ki; justs.append((axe, just))
    # combat : officier (axe choisi) vs pas d'officier (axe au hasard), meme terrain, de-bruite
    rnd = torch.randint(0, 8, (N,), device=dev)
    no, lo = fight_rep(net, env, kb); nr, lr = fight_rep(net, env, rnd)
    for e in range(N):
        print("\n  Situation %2d | OFFICIER choisit : %-11s (%2.0f%% expose) -> assaut : neutralise %3.0f%% | pertes %3.0f%%"
              % (e + 1, justs[e][0], 100 * expo[e].min(), 100 * no[e], 100 * lo[e]))
        print("     \"%s\"" % justs[e][1])
    print("\n" + "=" * 76)
    print("BILAN (12 situations, combat de-bruite x16) :")
    print("  OFFICIER (lit+choisit l'axe) : neutralise %3.0f%% | pertes %3.0f%%" % (100 * no.mean(), 100 * lo.mean()))
    print("  PAS D'OFFICIER (axe hasard)  : neutralise %3.0f%% | pertes %3.0f%%" % (100 * nr.mean(), 100 * lr.mean()))
    print("  -> apport de l'officier : %+.0f pts neutralise | %+.0f pts pertes" % (100 * (no.mean() - nr.mean()), 100 * (lo.mean() - lr.mean())))
    print("FULL FINI")
