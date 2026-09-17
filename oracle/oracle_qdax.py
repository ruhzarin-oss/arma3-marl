"""
Oracle QDax : MAP-Elites ( qualite-diversite ) en ask / tell, sur les MEMES episodes simules que les autres oracles.
Genotype = theta ( 3 dimensions ) ; descripteur = ( distance, moment ) sur une grille 10 x 10 ; fitness = z moyen.
Reglages ( ecrits avant, oracle/CRITERES_BANC_ORACLE.md ) : MixingEmitter, variation isoline ( iso_sigma 0,05,
line_sigma 0,10 ), 100 % de variation. Variantes : « me4 » 24 situations x 4 episodes par tour ; « me8 » 12 x 8
( fitness moins bruitee, meme budget ). Candidats = elites au meilleur fitness, separees.
  XLA_PYTHON_CLIENT_PREALLOCATE=false python oracle_qdax.py sortie.jsonl MONDE [ reps ] [ debut ] [ me4 | me8 ]
"""
import functools, json, os, sys, time
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
import numpy as np, jax, jax.numpy as jnp
from qdax.core.map_elites import MAPElites
from qdax.core.containers.mapelites_repertoire import compute_euclidean_centroids
from qdax.core.emitters.mutation_operators import isoline_variation
from qdax.core.emitters.standard_emitters import MixingEmitter
from qdax.utils.metrics import default_qd_metrics
from mondes import MONDES, PAR_TOUR, TOURS, episodes, separer, evaluer


def lancer(monde, rep, variante="me4"):
    ep = 4 if variante == "me4" else 8
    lot = PAR_TOUR // ep
    rng = np.random.default_rng(11_000_000 + rep)
    rng_ep = np.random.default_rng(12_000_000 + 1000 * list(MONDES).index(monde) + rep)
    key = jax.random.key(13_000 + rep)
    centroides = compute_euclidean_centroids(grid_shape=(10, 10), minval=0.0, maxval=1.0)
    variation = functools.partial(isoline_variation, iso_sigma=0.05, line_sigma=0.10, minval=0.0, maxval=1.0)
    emetteur = MixingEmitter(mutation_fn=None, variation_fn=variation, variation_percentage=1.0, batch_size=lot)
    me = MAPElites(scoring_function=None, emitter=emetteur, metrics_function=functools.partial(default_qd_metrics, qd_offset=2.0))
    T = rng.random((lot, 3))
    fit = episodes(monde, T, ep, rng_ep)[0]
    explores = T.tolist()
    key, sous = jax.random.split(key)
    rep_me, etat, _ = me.init_ask_tell(genotypes=jnp.array(T), fitnesses=jnp.array(fit), descriptors=jnp.array(T[:, :2]),
                                       centroids=centroides, key=sous, extra_scores={})
    for tour in range(1, TOURS):
        key, sous = jax.random.split(key)
        G, info = me.ask(rep_me, etat, sous)
        T = np.clip(np.array(G), 0, 1)
        fit = episodes(monde, T, ep, rng_ep)[0]
        explores += T.tolist()
        rep_me, etat, _ = me.tell(genotypes=jnp.array(T), fitnesses=jnp.array(fit), descriptors=jnp.array(T[:, :2]),
                                  repertoire=rep_me, emitter_state=etat, extra_scores={}, extra_info=info)
    F = np.array(rep_me.fitnesses).reshape(-1)
    E = np.array(rep_me.genotypes).reshape(len(F), -1)
    ok = np.isfinite(F)
    return explores, separer(E[ok], F[ok]) if ok.any() else []


if __name__ == "__main__":
    sortie, monde = sys.argv[1], sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    debut = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    variante = sys.argv[5] if len(sys.argv) > 5 else "me4"
    for rep in range(debut, debut + reps):
        t0 = time.time()
        X, cand = lancer(monde, rep, variante)
        res = evaluer(monde, rep, f"qdax_{variante}", X, cand); res["duree_s"] = round(time.time() - t0, 1)
        with open(sortie, "a") as f: f.write(json.dumps(res) + "\n")
        print(monde, rep, res["regions_trouvees"], "/", res["K"], "fausses", res["fausses"], "en faille", round(res["part_budget_en_faille"], 3), res["duree_s"], "s", flush=True)
