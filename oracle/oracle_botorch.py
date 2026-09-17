"""
Oracle BoTorch : processus gaussien sur le regret signe r(theta), lot de 24 situations par tour choisi par qUCB.
Reglages ( ecrits avant, oracle/CRITERES_BANC_ORACLE.md ) : SingleTaskGP, bruit fixe 0,5 ( variance de z <= 2, 4 episodes ).
Variante « ts » ( principale ) : echantillonnage de Thompson en lot ( MaxPosteriorSampling sur 4000 situations tirees au hasard ).
Variante « ucb » : qUpperConfidenceBound beta = 4, optimize_acqf sequentiel. Candidats = moyenne a posteriori.
  ( fumee du 17/09 : ucb a coute 322 s par repetition et n a mis que 3,75 % du budget dans les failles de W2 )
  python oracle_botorch.py sortie.jsonl MONDE [ reps ]
"""
import json, sys, time, warnings
import numpy as np, torch
from botorch.models import SingleTaskGP
from botorch.fit import fit_gpytorch_mll
from botorch.acquisition import qUpperConfidenceBound
from botorch.optim import optimize_acqf
from botorch.generation import MaxPosteriorSampling
from gpytorch.mlls import ExactMarginalLogLikelihood
from gpytorch.kernels import ScaleKernel, RBFKernel
from gpytorch.constraints import Interval
from mondes import MONDES, POINTS_PAR_TOUR, TOURS, episodes, separer, evaluer

warnings.filterwarnings("ignore")
torch.set_default_dtype(torch.float64)
DEV = torch.device("cuda")
BORNES = torch.tensor([[0.0] * 3, [1.0] * 3], device=DEV)
EP, BRUIT, BETA = 4, 0.5, 4.0


def ajuster(X, Y, court=False):
    x = torch.tensor(np.array(X), device=DEV); y = torch.tensor(np.array(Y), device=DEV)[:, None]
    if court:   # longueurs de correlation bornees a [0,02 ; 0,30] : une faille fait quelques dixiemes de l espace
        noyau = ScaleKernel(RBFKernel(ard_num_dims=3, lengthscale_constraint=Interval(0.02, 0.30))).to(DEV)
        gp = SingleTaskGP(x, y, train_Yvar=torch.full_like(y, BRUIT), covar_module=noyau)
    else:
        gp = SingleTaskGP(x, y, train_Yvar=torch.full_like(y, BRUIT))
    fit_gpytorch_mll(ExactMarginalLogLikelihood(gp.likelihood, gp))
    return gp


def lancer(monde, rep, variante="ts"):
    rng = np.random.default_rng(6_000_000 + rep)
    rng_ep = np.random.default_rng(7_000_000 + 1000 * list(MONDES).index(monde) + rep)
    torch.manual_seed(8_000_000 + rep)
    X = rng.random((POINTS_PAR_TOUR, 3)).tolist()
    Y = episodes(monde, X, EP, rng_ep)[0].tolist()
    court = variante.endswith("court")
    for tour in range(1, TOURS):
        gp = ajuster(X, Y, court)
        if variante == "ucb":
            cand, _ = optimize_acqf(qUpperConfidenceBound(gp, beta=BETA), bounds=BORNES, q=POINTS_PAR_TOUR,
                                    num_restarts=5, raw_samples=256, sequential=True)
        else:
            pool = torch.tensor(rng.random((4000, 3)), device=DEV)
            with torch.no_grad():
                cand = MaxPosteriorSampling(model=gp, replacement=False)(pool, num_samples=POINTS_PAR_TOUR)
        T = cand.detach().cpu().numpy().reshape(-1, 3).clip(0, 1)
        X += T.tolist(); Y += episodes(monde, T, EP, rng_ep)[0].tolist()
    gp = ajuster(X, Y, court)
    G = rng.random((20000, 3))
    with torch.no_grad():
        mu = gp.posterior(torch.tensor(G, device=DEV)).mean.squeeze(-1).cpu().numpy()
    return X, separer(G, mu)


if __name__ == "__main__":
    sortie, monde = sys.argv[1], sys.argv[2]
    variante = sys.argv[5] if len(sys.argv) > 5 else "ts"
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    debut = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    for rep in range(debut, debut + reps):
        t0 = time.time()
        X, cand = lancer(monde, rep, variante)
        res = evaluer(monde, rep, f"botorch_{variante}", X, cand); res["duree_s"] = round(time.time() - t0, 1)
        with open(sortie, "a") as f: f.write(json.dumps(res) + "\n")
        print(monde, rep, res["regions_trouvees"], "/", res["K"], "fausses", res["fausses"], res["duree_s"], "s", flush=True)
