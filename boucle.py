#!/usr/bin/env python3
"""boucle — ETAPE 4 DE LA FEUILLE DE ROUTE : quelque chose apprend enfin.

Criteres deposes AVANT le premier pas : CRITERES_BOUCLE.md
  recompense : 1,0 x prise + 0,01 x metre gagne. AUCUN terme d exposition — la sandbox
               la sur-tarife (+856 % contre +75 % sur Arma), on ne met pas dans la
               recompense une quantite dont on sait que le monde la facture faux.
  porte      : G1 battre les DEUX doctrines scriptees sur graines HELD-OUT, sur la BORNE
               G2 controle nul — une politique aleatoire ne doit PAS passer G1
               G3 le gain ne vient pas de se terrer : metres gagnes >= la meilleure doctrine
"""
import math, sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

DEV = "cuda:0"
PAS = 60
GRAINES_TRAIN = [11, 12, 13, 14, 15, 16, 17, 18]
GRAINES_TEST = [101, 102, 103, 104, 105, 106]     # JAMAIS vues a l entrainement
NA = 10                                            # 8 caps + tenir + feu


# ⚠️ LE MONDE EST UNE VARIABLE DE MODULE. Par defaut le monde de reference — rien ne
# bouge pour qui ne la touche pas. Un entrainement sur le monde OPERE fait `B.CFG = MONDE_OPERE`.
CFG = MONDE_ARMA

def monde(n, seed):
    return AssaultTerrain(num_envs=n, seed=seed, device=DEV, max_steps=PAS, **CFG)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def frontal(e, t):
    return cap(-e.apx, -e.apy)


def flanc(e, t, n_fixe=2, pas_crochet=14):
    act = cap(-e.apx, -e.apy)
    d = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    act = torch.where(fixe & (d < e.fire_range * 0.9), torch.full_like(act, 9), act)
    if t < pas_crochet:
        act = torch.where(~fixe, cap(-e.apy, e.apx), act)
    return act


class Politique(nn.Module):
    """Petit reseau par homme. Il voit ce que le monde lui donne, rien de plus."""
    def __init__(self, nobs, nh=128):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(nobs, nh), nn.Tanh(), nn.Linear(nh, nh), nn.Tanh())
        self.pi = nn.Linear(nh, NA)
        self.v = nn.Linear(nh, 1)

    def forward(self, o):
        h = self.f(o)
        return self.pi(h), self.v(h).squeeze(-1)


def jouer(e, choisir, garder=False):
    """Un episode complet. `choisir(obs, t) -> (actions, logprob, valeur)`."""
    o = e.reset()
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dprec = d0.clone(); dmin = d0.clone()
    lps, vals, rs, masques = [], [], [], []
    for t in range(PAS):
        viv = (~fini).float()
        a, lp, v = choisir(o, t)
        o, _, done, info = e.step(a, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        # AVEU DU 11/08 (AVEU_RECOMPENSE.md). Le `.clamp(min=0)` rendait la recompense
        # POMPABLE : reculer gratuit, avancer paye, donc on oscille sans progresser. Et il
        # cassait le telescopage. Terme SIGNE = faconnage par potentiel ⟨Ng, Harada & Russell
        # 1999⟩ : sa somme vaut k x (depart - arrivee), bornee, et il est PROUVE qu il ne
        # deplace pas la politique optimale. Il guide sans pouvoir mentir.
        gagne = dprec - d                            # SIGNE : reculer coute ce qu avancer rapporte
        dprec = d; dmin = torch.minimum(dmin, torch.where(fini, dmin, d))
        neuf = info["took"] & ~fini
        # 0,001 et non 0,01 : a 114 metres le guide valait 1,14, PLUS que le but a 1,0.
        # L agent a optimise ce que je lui payais le plus — marcher. Regle deposee : le guide
        # ne vaut jamais plus du CINQUIEME de ce qu il guide (0,001 x 200 = 0,2).
        r = 1.0 * neuf.float() + 0.001 * gagne      # la recompense corrigee, rien d autre
        pris |= neuf
        if garder:
            lps.append(lp); vals.append(v); rs.append(r * viv); masques.append(viv)
        fini |= done.bool()
        if bool(fini.all()):
            break
    stats = dict(prise=100.0 * float(pris.float().mean()),
                 metres=float((d0 - dmin).mean()))
    return stats, lps, vals, rs, masques


def entrainer(iters=140, n=256, lr=3e-4):
    e0 = monde(8, GRAINES_TRAIN[0]); e0.reset()
    nobs = e0._obs().shape[-1]
    pol = Politique(nobs).to(DEV)
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    print(f"\n  entrainement — {nobs} entrees, {NA} actions, {iters} iterations de {n} episodes")
    for it in range(iters):
        e = monde(n, GRAINES_TRAIN[it % len(GRAINES_TRAIN)])

        def choisir(o, t):
            lo, v = pol(o)
            di = torch.distributions.Categorical(logits=lo)
            a = di.sample()
            return a, di.log_prob(a), v

        st, lps, vals, rs, masques = jouer(e, choisir, garder=True)
        # retours a rebours, avantage = retour - valeur (baseline apprise)
        R = torch.zeros_like(rs[0]); rets = []
        for r in reversed(rs):
            R = r + 0.99 * R; rets.append(R)
        rets.reverse()
        pl = vl = 0.0
        for lp, v, ret, m in zip(lps, vals, rets, masques):
            ret_a = ret.unsqueeze(1).expand_as(lp)
            adv = (ret_a - v).detach()
            adv = (adv - adv.mean()) / (adv.std() + 1e-6)
            pl = pl - (lp * adv * m.unsqueeze(1)).mean()
            vl = vl + ((v - ret_a) ** 2 * m.unsqueeze(1)).mean()
        perte = pl + 0.5 * vl
        opt.zero_grad(); perte.backward()
        nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
        opt.step()
        if it % 20 == 0 or it == iters - 1:
            print(f"    iter {it:>4}  prise {st['prise']:>5.1f} %  metres {st['metres']:>6.1f}", flush=True)
    return pol


def evaluer(pol, graines, n=256):
    """Lecture sur graines HELD-OUT, par graine — l appariement vit la ⟨regle 12⟩."""
    def gele(o, t):
        with torch.no_grad():
            lo, v = pol(o)
        return lo.argmax(-1), None, None
    res = {"appris": [], "frontal": [], "flanc": []}
    met = {"appris": [], "frontal": [], "flanc": []}
    for g in graines:
        for nom, f in (("appris", gele),
                       ("frontal", lambda o, t, _e=None: (None, None, None)),
                       ("flanc", None)):
            pass
    for g in graines:
        e = monde(n, g)
        st, *_ = jouer(e, gele)
        res["appris"].append(st["prise"]); met["appris"].append(st["metres"])
        for nom, doc in (("frontal", frontal), ("flanc", flanc)):
            e = monde(n, g)
            st, *_ = jouer(e, lambda o, t, _d=doc, _e=e: (_d(_e, t), None, None))
            res[nom].append(st["prise"]); met[nom].append(st["metres"])
    return res, met


if __name__ == "__main__":
    torch.manual_seed(0)
    pol = entrainer(iters=int(sys.argv[1]) if len(sys.argv) > 1 else 140)

    print("\n  LA PORTE — graines JAMAIS vues a l entrainement")
    print("  " + "=" * 66)
    res, met = evaluer(pol, GRAINES_TEST)
    moy = lambda v: sum(v) / len(v)
    for k in ("appris", "frontal", "flanc"):
        print(f"    {k:<10} prise {moy(res[k]):>5.1f} %   metres gagnes {moy(met[k]):>6.1f}")

    # G1 : sur la BORNE, apparie par graine
    import statistics as stx
    ok1 = True
    for adv in ("frontal", "flanc"):
        d = [a - b for a, b in zip(res["appris"], res[adv])]
        m = moy(d); s = stx.stdev(d) if len(d) > 1 else 0.0
        lo = m - 2.571 * s / math.sqrt(len(d))          # t(5), 95 %
        print(f"    G1 vs {adv:<8} ecart {m:+.1f} pt   borne inferieure {lo:+.1f}")
        ok1 &= lo > 0

    # G2 : controle nul — politique aleatoire
    e0 = monde(8, 1); e0.reset()
    alea = Politique(e0._obs().shape[-1]).to(DEV)
    res_a, _ = evaluer(alea, GRAINES_TEST)
    ok2 = True
    for adv in ("frontal", "flanc"):
        d = [a - b for a, b in zip(res_a["appris"], res_a[adv])]
        m = moy(d); s = stx.stdev(d) if len(d) > 1 else 0.0
        lo = m - 2.571 * s / math.sqrt(len(d))
        if lo > 0: ok2 = False
    print(f"    G2 controle nul (politique aleatoire) : {'PASSE' if ok2 else 'TOMBE'}"
          f"  — prise aleatoire {moy(res_a['appris']):.1f} %")

    meilleure = max(("frontal", "flanc"), key=lambda k: moy(res[k]))
    ok3 = moy(met["appris"]) >= moy(met[meilleure])
    print(f"    G3 metres appris {moy(met['appris']):.1f} contre {moy(met[meilleure]):.1f} "
          f"({meilleure}) : {'PASSE' if ok3 else 'TOMBE'}")

    print("  " + "=" * 66)
    if ok1 and ok2 and ok3:
        print("    LA BOUCLE EST FERMEE. Quelque chose apprend, dans le monde calibre, sur")
        print("    une recompense mesuree, et bat les deux doctrines ecrites a la main.")
        torch.save(pol.state_dict(), "/home/younes/arma3-marl/boucle_pol.pt")
        print("    politique gardee : boucle_pol.pt")
    else:
        print("    LA PORTE NE PASSE PAS. On le dit, on ne rejoue pas les graines.")
    print("\n    ⚠️ AUCUN VERDICT DE MISSION N EN SORT. Le monde est le notre.")
    print("       ⟨juillet : 96 % en sandbox, 0/38 dans Arma⟩ Arma tranchera.")
