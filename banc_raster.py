#!/usr/bin/env python3
"""banc_raster — LE RASTER CONTRE LES DOUZE NOMBRES.

Critères déposés AVANT la première donnée : PREINSCRIPTION_RASTER.md (le banc imprime son
hachage). Quatre bras, mêmes graines, même monde, même budget :

    A  vecteur seul                  MLP        la référence du dépôt
    B  vecteur + raster              CNN        la revendication
    C  vecteur + raster BROUILLÉ     CNN        contrôle GÉOMÉTRIE  (se lit AVANT B)
    D  vecteur + raster APLATI       MLP        contrôle CAPACITÉ

⚠️ CE FICHIER NE RÉÉCRIT PAS LA RÉCOMPENSE. Il appelle `boucle.jouer` tel quel — le
façonnage par potentiel, le γ, le terme signé, tout vient du dépôt. La seule chose ajoutée
est CE QUE L'AGENT VOIT. Un banc qui réécrit son monde pour tester une observation ne
mesure plus l'observation.
"""
import os, sys, math, json, time, hashlib
import torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from raster import raster, brouilleur, CANAUX_DEFAUT, K_DEFAUT, SPAN_DEFAUT

DEV = "cuda:0"
K, SPAN, C = K_DEFAUT, SPAN_DEFAUT, len(CANAUX_DEFAUT)
NH = 128


class PolVecteur(nn.Module):
    """BRAS A — exactement la Politique du dépôt."""
    def __init__(self, nobs):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(nobs, NH), nn.Tanh(), nn.Linear(NH, NH), nn.Tanh())
        self.pi = nn.Linear(NH, B.NA); self.v = nn.Linear(NH, 1)
    def forward(self, o, r=None):
        h = self.f(o); return self.pi(h), self.v(h).squeeze(-1)


class PolCNN(nn.Module):
    """BRAS B et C — le raster lu PAR CONVOLUTION, concaténé au vecteur."""
    def __init__(self, nobs, nlat=128):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(C, 32, 3, stride=2, padding=1), nn.ReLU(),    # 24 -> 12
            nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.ReLU(),   # 12 -> 6
            nn.Conv2d(64, 64, 3, stride=2, padding=1), nn.ReLU(),   # 6  -> 3
            nn.Flatten(), nn.Linear(64 * 3 * 3, nlat), nn.ReLU())
        self.f = nn.Sequential(nn.Linear(nobs + nlat, NH), nn.Tanh(), nn.Linear(NH, NH), nn.Tanh())
        self.pi = nn.Linear(NH, B.NA); self.v = nn.Linear(NH, 1)
    def forward(self, o, r):
        N, A = o.shape[0], o.shape[1]
        z = self.enc(r.reshape(N * A, C, K, K)).reshape(N, A, -1)
        h = self.f(torch.cat([o, z], dim=-1))
        return self.pi(h), self.v(h).squeeze(-1)


class PolAplati(nn.Module):
    """BRAS D — le MÊME contenu, APLATI, lu sans convolution. Le contrôle de capacité :
    il a PLUS de paramètres à l'interface que le CNN (442 k contre 60 k)."""
    def __init__(self, nobs, nlat=128):
        super().__init__()
        self.enc = nn.Sequential(nn.Flatten(start_dim=-3), nn.Linear(C * K * K, nlat), nn.ReLU())
        self.f = nn.Sequential(nn.Linear(nobs + nlat, NH), nn.Tanh(), nn.Linear(NH, NH), nn.Tanh())
        self.pi = nn.Linear(NH, B.NA); self.v = nn.Linear(NH, 1)
    def forward(self, o, r):
        z = self.enc(r)
        h = self.f(torch.cat([o, z], dim=-1))
        return self.pi(h), self.v(h).squeeze(-1)


BRAS = {"A": (PolVecteur, False, False), "B": (PolCNN, True, False),
        "C": (PolCNN, True, True),       "D": (PolAplati, True, False)}


def faire_raster(e, brouille, br):
    r = raster(e, K=K, span=SPAN)
    return br(r) if brouille else r


def entrainer(bras, graine, iters=140, n=256, lr=3e-4, eval_tous=0, film=None):
    """Copie FIDÈLE de `boucle.entrainer` — même perte, même γ, même écrêtage.
    Seule différence : la politique reçoit aussi le raster."""
    Cls, avec_r, brouille = BRAS[bras]
    torch.manual_seed(graine)
    e0 = B.monde(8, B.GRAINES_TRAIN[0]); e0.reset()
    nobs = e0._obs().shape[-1]
    pol = Cls(nobs).to(DEV)
    br = brouilleur(K, C, DEV) if brouille else None
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    npar = sum(p.numel() for p in pol.parameters())
    print("    bras %s graine %d — %d entrees vectorielles, %s, %d parametres"
          % (bras, graine, nobs, ("raster %dx%dx%d" % (C, K, K)) if avec_r else "sans raster", npar), flush=True)
    for it in range(iters):
        e = B.monde(n, B.GRAINES_TRAIN[it % len(B.GRAINES_TRAIN)])
        def choisir(o, t, _e=e):
            r = faire_raster(_e, brouille, br) if avec_r else None
            lo, v = pol(o, r)
            di = torch.distributions.Categorical(logits=lo)
            a = di.sample()
            return a, di.log_prob(a), v
        st, lps, vals, rs, masques = B.jouer(e, choisir, garder=True)
        R = torch.zeros_like(rs[0]); rets = []
        for r_ in reversed(rs):
            R = r_ + 0.99 * R; rets.append(R)
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
        if it % 100 == 0 or it == iters - 1:
            print("      it %4d  prise %5.1f %%  tenus %6.1f m" % (it, st["prise"], st["metres_tenus"]), flush=True)
        # ─── LE FILM, PAS LA DERNIERE IMAGE ⟨amendement 1⟩. On lit sur GRAINES_SELECT :
        # ni apprises, ni jugees. GRAINES_TEST reste INTOUCHE jusqu au verdict final, et
        # aucun point de sauvegarde n est selectionne sur cette courbe — elle est publiee,
        # elle ne choisit rien.
        if eval_tous and film is not None and (it % eval_tous == 0 or it == iters - 1):
            p_, t_ = evaluer(pol, bras, B.GRAINES_SELECT, n=n)
            film.append({"it": it, "prise_select": p_, "tenus_select": t_})
            print("      FILM it %4d  select : prise %5.1f %%  tenus %6.1f m" % (it, p_, t_), flush=True)
    return pol


def evaluer(pol, bras, graines, n=256):
    """Lecture sur graines JAMAIS vues. Décodeur = ÉCHANTILLONNAGE (décision du 24/08)."""
    _, avec_r, brouille = BRAS[bras]
    br = brouilleur(K, C, DEV) if brouille else None
    prises, tenus = [], []
    for g in graines:
        e = B.monde(n, g)
        def gele(o, t, _e=e):
            r = faire_raster(_e, brouille, br) if avec_r else None
            with torch.no_grad():
                lo, v = pol(o, r)
            return torch.distributions.Categorical(logits=lo).sample(), None, None
        st, *_ = B.jouer(e, gele)
        prises.append(st["prise"]); tenus.append(st["metres_tenus"])
    return sum(prises) / len(prises), sum(tenus) / len(tenus)


def doctrines(graines, n=256):
    """Les deux doctrines scriptées du dépôt, sur les MÊMES graines. Le contrôle positif :
    si personne ne les bat, ce n'est pas l'observation qui est en cause."""
    out = {}
    for nom, doc in (("frontal", B.frontal), ("flanc", B.flanc)):
        p, t = [], []
        for g in graines:
            e = B.monde(n, g)
            st, *_ = B.jouer(e, lambda o, tt, _d=doc, _e=e: (_d(_e, tt), None, None))
            p.append(st["prise"]); t.append(st["metres_tenus"])
        out[nom] = (sum(p) / len(p), sum(t) / len(t))
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=140)
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--graines", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--bras", nargs="+", default=["A", "B", "C", "D"])
    ap.add_argument("--chrono", action="store_true", help="mesure le cout de 2 iterations et sort")
    ap.add_argument("--eval_tous", type=int, default=200, help="film sur GRAINES_SELECT")
    ap.add_argument("--sortie", default="/mnt/data/raster_resultats.json")
    a = ap.parse_args()

    h = hashlib.sha256(open("/home/younes/arma3-marl/PREINSCRIPTION_RASTER.md", "rb").read()).hexdigest()[:16]
    ha = hashlib.sha256(open("/home/younes/arma3-marl/AMENDEMENT_BUDGET_RASTER.md", "rb").read()).hexdigest()[:16]
    print("=" * 78)
    print(" BANC RASTER — pre-inscription %s + amendement budget %s" % (h, ha))
    print("=" * 78)

    if a.chrono:
        for b in a.bras:
            t0 = time.time(); entrainer(b, 0, iters=2, n=a.n); dt = (time.time() - t0) / 2
            print("    -> bras %s : %.1f s / iteration  ->  %.1f min pour %d iterations\n"
                  % (b, dt, dt * a.iters / 60.0, a.iters), flush=True)
        sys.exit(0)

    # ─── REPRENABLE ⟨compagnon n1 d un run long⟩. On saute une unite de travail sur sa
    # MARQUE DE FIN (le couple (bras, graine) present dans `faits`), jamais sur la seule
    # existence du fichier : un run coupe en plein entrainement laisse un JSON valide dont
    # la derniere unite est incomplete, et elle doit etre REJOUEE.
    res = {"hachage_preinscription": h, "iters": a.iters, "n": a.n,
           "graines_entrainement": a.graines, "graines_jugement": B.GRAINES_TEST,
           "K": K, "span": SPAN, "canaux": list(CANAUX_DEFAUT), "bras": {}, "faits": []}
    if os.path.exists(a.sortie):
        try:
            _v = json.load(open(a.sortie))
            if _v.get("hachage_preinscription") == h and _v.get("iters") == a.iters:
                res = _v; res.setdefault("faits", [])
                print("  REPRISE — %d unites deja faites : %s"
                      % (len(res["faits"]), ", ".join(res["faits"])), flush=True)
            else:
                print("  fichier existant IGNORE (autre pre-inscription ou autre budget)", flush=True)
        except Exception as _e:
            print("  fichier existant illisible (%s) — on repart de zero" % _e, flush=True)

    if "doctrines" not in res:
        print("\n  doctrines scriptees du depot, memes graines de jugement :", flush=True)
        res["doctrines"] = doctrines(B.GRAINES_TEST, n=a.n)
        json.dump(res, open(a.sortie, "w"), indent=1)
    for k, (p, t) in res["doctrines"].items():
        print("    %-8s prise %5.1f %%   tenus %6.1f m" % (k, p, t), flush=True)

    for b in a.bras:
        res["bras"].setdefault(b, {"prise": [], "tenus": [], "film": {}})
        for g in a.graines:
            marque = "%s:%d" % (b, g)
            if marque in res["faits"]:
                print("    -- %s deja fait, saute" % marque, flush=True); continue
            t0 = time.time()
            film = []
            pol = entrainer(b, g, iters=a.iters, n=a.n, eval_tous=a.eval_tous, film=film)
            p, t = evaluer(pol, b, B.GRAINES_TEST, n=a.n)
            res["bras"][b]["prise"].append(p); res["bras"][b]["tenus"].append(t)
            res["bras"][b].setdefault("film", {})[str(g)] = film
            res["faits"].append(marque)          # LA MARQUE DE FIN, ecrite APRES le jugement
            print("    == bras %s graine %d : PRISE %5.1f %%   TENUS %6.1f m   (%.1f min)"
                  % (b, g, p, t, (time.time() - t0) / 60.0), flush=True)
            json.dump(res, open(a.sortie, "w"), indent=1)
        v = sorted(res["bras"][b]["prise"])
        if v:
            print("    ==== BRAS %s : mediane %5.1f %%  etendue [%.1f ; %.1f]\n"
                  % (b, v[len(v) // 2], v[0], v[-1]), flush=True)
    json.dump(res, open(a.sortie, "w"), indent=1)
    print("  ecrit dans %s" % a.sortie)
