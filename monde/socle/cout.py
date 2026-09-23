"""LE COUT DU SOCLE, mesure ( format de livraison, point 8 ).   python -m monde.socle.cout

Des couts unitaires mesures sur la station, puis ce qu ils coutent a un monde reel : un Monde E1 a 50 000 habitants,
deux jours sans socle, deux jours avec. L extrapolation a 1 et 50 millions suit le nombre de paiements par habitant
et par jour, mesure ici, pas suppose."""
import math, time, tracemalloc
import numpy as np
from .. import monde as W, config as C
from . import biens as B, objets as O, comptes as K, registre as R, echeancier as E, journal as J, hasard as H
from . import brancher as BR


class Foyer:
    __slots__ = ("caisse",)
    def __init__(self, c): self.caisse = c


def _foyers(w): return w


def ns_par_appel(f, n):
    t0 = time.perf_counter(); f(n); return (time.perf_counter() - t0) / n * 1e9


def octets_par(fabrique, n):
    tracemalloc.start(); avant = tracemalloc.get_traced_memory()[0]
    garde = fabrique(n)
    apres = tracemalloc.get_traced_memory()[0]; tracemalloc.stop()
    del garde
    return (apres - avant) / n


def main():
    cat = B.catalogue_du_moteur()
    livre = K.GrandLivre(cat); livre.declarer_motif("salaire", "remuneration", "cout")
    a, b = Foyer(1e12), Foyer(0.0)

    def e1(n):
        for _ in range(n): W.Monde.transferer(None, a, b, 1.0, "salaire")

    def socle(n):
        for _ in range(n): livre.transferer(a, b, 1.0, "salaire")

    t_e1, t_socle = ns_par_appel(e1, 1_000_000), ns_par_appel(socle, 1_000_000)
    print(f"transferer : moteur E1 {t_e1:.0f} ns, grand livre {t_socle:.0f} ns ( + {t_socle - t_e1:.0f} ns par paiement )")

    def stocks(k):
        def f(n):
            out = []
            for _ in range(n):
                s = B.Stock()
                for b_ in range(k): s._ajouter(b_, 1.0)
                out.append(s)
            return out
        return f
    s1, s9 = octets_par(stocks(1), 100_000), octets_par(stocks(9), 100_000)
    d9 = octets_par(lambda n: [{b_: 1.0 for b_ in C.BIENS} for _ in range(n)], 100_000)
    print(f"stock : {s1:.0f} octets avec 1 bien, {s9:.0f} avec 9 ; dictionnaire E1 des 9 biens {d9:.0f}")

    parc = O.Parc(H.Hasard(1)); parc.declarer_modele("berline", "vehicule", 1.5e4, 1300.0, 1.5e5)
    oct_obj = octets_par(lambda n: [parc.creer(0, None, "L", "initial", 0) for _ in range(n)], 100_000)
    oct_coh = octets_par(lambda n: [parc.creer_cohorte(0, k, "L", 10, "initial") for k in range(n)], 100_000)
    coh = parc.creer_cohorte(0, "flotte", "L", 10 ** 6, "initial", 0.3)
    t_mat = ns_par_appel(lambda n: [parc.materialiser(coh, 0) for _ in range(n)], 10_000)
    print(f"objet : {oct_obj:.0f} octets par individu, {oct_coh:.0f} par cohorte ( quel que soit son nombre ) ; "
          f"materialiser {t_mat / 1000:.1f} us")

    ech = E.Echeancier(); ech.declarer("t")
    oct_ech = octets_par(lambda n: [ech.poser(k % 52560, "t", k) for k in range(n)], 1_000_000)
    t0 = time.perf_counter(); ech.servir(52559); t_serv = (time.perf_counter() - t0) / 1e6 * 1e9
    print(f"echeancier : {oct_ech:.0f} octets par echeance en attente, service {t_serv:.0f} ns par echeance")

    h = H.Hasard(1); g = h.flux("cout")
    t_sous = ns_par_appel(lambda n: [h.sous_flux("cout", 2, k) for k in range(n)], 10_000)
    t_scal = ns_par_appel(lambda n: [g.random() for _ in range(n)], 1_000_000)
    t0 = time.perf_counter(); g.random(10_000_000); t_vec = (time.perf_counter() - t0) / 1e7 * 1e9
    print(f"hasard : sous-flux {t_sous / 1000:.1f} us a creer ; tirage {t_scal:.0f} ns a l unite, {t_vec:.1f} ns en vecteur")

    jl = J.Journal(); jl.declarer("achat", "cout", "compte")
    print(f"journal : compter {ns_par_appel(lambda n: [jl.compter('achat') for _ in range(n)], 1_000_000):.0f} ns")

    rng = np.random.default_rng(4)
    foyers = [Foyer(float(x)) for x in rng.lognormal(6.5, 1.0, 300_000)]
    reg = R.Registre(foyers, cat); reg.inscrire("foyers", "menages", _foyers, "caisse", None, "Foyer")
    t0 = time.perf_counter(); avant = reg.argent(); t_reg = time.perf_counter() - t0
    naif0 = sum(f.caisse for f in foyers)
    i, j = rng.integers(0, 300_000, 10_000_000), rng.integers(0, 300_000, 10_000_000)
    m = rng.uniform(0, 50, 10_000_000)
    t0 = time.perf_counter()
    for x, y, v in zip(i.tolist(), j.tolist(), m.tolist()):
        fx = foyers[x]
        if fx.caisse >= v: fx.caisse -= v; foyers[y].caisse += v
    t_drift = time.perf_counter() - t0
    apres = reg.argent(); naif1 = sum(f.caisse for f in foyers)
    print(f"registre : {t_reg * 1000:.0f} ms pour sommer 300 000 caisses ; derive flottante apres 10 millions de "
          f"paiements ( {t_drift:.0f} s ) : {apres - avant:+.2e} drachmes exacte ( fsum ), {naif1 - naif0:+.2e} en somme naive, "
          f"sur {avant:,.0f}")

    for socle_ in (False, True):
        w = W.Monde(echelle=100)
        s = BR.brancher(w) if socle_ else None
        t0 = time.perf_counter()
        for _ in range(2 * C.PAS_PAR_JOUR): w.pas_suivant()
        t = (time.perf_counter() - t0) / 2
        if socle_:
            n_hab = len(w.habitants); par_hab = s.livre.n_transferts / 2 / n_hab
            t_cons = time.perf_counter(); ok, msg = s.conservation.tenue(); t_cons = time.perf_counter() - t_cons
            print(f"monde a {n_hab:,} habitants AVEC socle : {t:.2f} s par jour ; {s.livre.n_transferts / 2:,.0f} paiements "
                  f"par jour ( {par_hab:.2f} par habitant ) ; conservation {'tenue' if ok else 'ROMPUE'} en {t_cons:.2f} s")
            for pop in (1e6, 5e7):
                print(f"  a {pop:,.0f} habitants : {pop * par_hab * (t_socle - t_e1) * 1e-9:,.1f} s de plus par jour pour le "
                      f"grand livre ; conservation ~ {t_cons * pop / n_hab:,.0f} s une fois par jour")
        else:
            print(f"monde a {len(w.habitants):,} habitants SANS socle : {t:.2f} s par jour")


if __name__ == "__main__":
    main()
