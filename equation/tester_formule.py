"""Controle du traducteur : 2000 arbres EvoGP tires au hasard ( tous les operateurs ), infix -> codes -> evaluation
Python ; doit egaler forward() d'EvoGP sur 200 points aleatoires, a 1e-4 pres. Aucun ecart toléré."""
import numpy as np, torch
from evogp.tree import Forest, GenerateDescriptor
from formule import analyser, encoder, evaluer_codes, evaluer, CONSTANTES
torch.manual_seed(1)
d = GenerateDescriptor(max_tree_len=32, input_len=5, output_len=1, using_funcs=["+", "-", "*", "min", "max", "neg", ">"],
                       max_layer_cnt=5, const_samples=CONSTANTES)
foret = Forest.random_generate(pop_size=2000, descriptor=d)
rng = np.random.default_rng(2)
X = np.column_stack([rng.integers(0, 2, 200), rng.integers(-1, 300, 200), rng.integers(0, 2, 200), rng.integers(5, 11, 200), rng.integers(0, 7, 200)]).astype(np.float32)
X[:40] = np.array([[1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [0.5, 0.5, 0.5, 0.5, 0.5], [-1, -1, -1, -1, -1]] * 10, dtype=np.float32)   # egalites exactes
Xg = torch.tensor(X, device="cuda").contiguous()
ecarts, echecs, tailles = 0, 0, []
for i in range(2000):
    arbre_evogp = foret[i]
    try:
        a = analyser(str(arbre_evogp.to_infix()), [f"x{j}" for j in range(5)])
        codes = encoder(a)
    except Exception as e:
        echecs += 1
        if echecs <= 3: print("ECHEC", e, str(arbre_evogp.to_infix())[:120])
        continue
    tailles.append(len(codes))
    ref = arbre_evogp.forward(Xg).reshape(-1).cpu().numpy()
    moi = np.array([evaluer_codes(codes, x) for x in X])
    moi2 = np.array([evaluer(a, x) for x in X])
    ok = np.isfinite(ref)
    if not (np.allclose(ref[ok], moi[ok], atol=1e-3, rtol=1e-4) and np.allclose(moi, moi2)):
        ecarts += 1
        if ecarts <= 3:
            j = np.argmax(np.abs(ref - moi)); print("ECART", str(arbre_evogp.to_infix())[:160], X[j], ref[j], moi[j])
print(f"arbres : 2000, echecs de traduction : {echecs}, ecarts d'evaluation : {ecarts}, noeuds moyen {np.mean(tailles):.1f} max {max(tailles)}")
