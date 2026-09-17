"""Calibrage du generateur seul : puissance de declaration de la REGLE VRAIE ( pas d'algorithme ). Pour choisir des effets detectables."""
import numpy as np
sig = lambda z: 1 / (1 + np.exp(-z))
def tirer(rng, n):
    d = rng.uniform(0.1, 0.9, n); t = rng.uniform(0, 1, n); al = rng.binomial(1, 0.5, n); vv = rng.binomial(1, 0.4, n)
    de = np.clip(rng.poisson(3, n), 0, 8); return d, t, al, vv, de
VERSIONS = {
 "actuel": dict(niv=lambda d,t,al,vv,de: 0.3 - 0.4*(de-3) - 0.8*al + 0.5*(d-0.5),
     F1=lambda d,t,al,vv: 3*(0.5-d) + 2*(vv-0.5), F2=lambda d,t,al,vv: 8*(d-0.5)*(t-0.5), F3=lambda d,t,al,vv: np.where((al==1)&(d<0.5), 2., -1.)),
 "fort2": dict(niv=lambda d,t,al,vv,de: -0.15*(de-3) - 0.2*al + 0.2*(d-0.5),
     F1=lambda d,t,al,vv: np.clip(10*(0.5-d) + 3*(vv-0.4), -3, 3), F2=lambda d,t,al,vv: np.where((d-0.5)*(t-0.5) > 0, 3., -3.),
     F3=lambda d,t,al,vv: np.where((al==1)&(d<0.7), 3., -3.)),
 "fort": dict(niv=lambda d,t,al,vv,de: -0.2*(de-3) - 0.3*al + 0.3*(d-0.5),
     F1=lambda d,t,al,vv: 7.5*(0.5-d) + 3*(vv-0.4), F2=lambda d,t,al,vv: np.clip(24*(d-0.5)*(t-0.5), -3, 3),
     F3=lambda d,t,al,vv: np.where((al==1)&(d<0.7), 3., -3.)),
}
rng = np.random.default_rng(1)
for nom, V in [("fort2", VERSIONS["fort2"])]:
    for f in ["F1", "F2", "F3"]:
        big = tirer(rng, 200000); g = V[f](*big[:4]); e0 = V["niv"](*big)
        q = np.mean(g > 0); gi = np.mean(sig(e0 + (g > 0) * g)) - max(np.mean(sig(e0)), np.mean(sig(e0 + g)))
        c = int(np.mean(sig(e0 + g)) > np.mean(sig(e0)))
        pw = {}
        for n in (200, 500, 1000):
            ok = 0
            for s in range(1000):
                d_, t_, al_, vv_, de_ = tirer(rng, n); gg = V[f](d_, t_, al_, vv_); a = rng.binomial(1, .5, n)
                Y = rng.binomial(1, sig(V["niv"](d_, t_, al_, vv_, de_) + a * gg)); r = (gg > 0).astype(int)
                dd = 2 * Y * ((a == r).astype(float) - (a == c).astype(float)); se = dd.std(ddof=1) / np.sqrt(n)
                ok += (dd.mean() - 2.326 * se > 0)
            pw[n] = ok / 1000
        print(f"{nom:6s} {f}  part option1 {q:.2f}  gain ideal {gi:+.3f}  puissance regle vraie {pw}")
