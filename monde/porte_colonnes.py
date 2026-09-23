"""La porte de la refonte en colonnes : le nouveau moteur ( habitants en colonnes, `deplacer` et `produire` par le
coeur Rust ) doit rendre LE MEME MONDE que l ancien, au centime pres, habitant par habitant, jour apres jour.

L ancien moteur est une copie du depot avant la refonte, rangee sous le nom `monde_ancien` ( /mnt/data/hmt/ref ).
   python -m monde.porte_colonnes"""
import sys, time
sys.path.insert(0, "/mnt/data/hmt/ref")
import monde_ancien.monde as WA
from . import monde as W, config as C, carte as K


def photo(w):
    """Tout ce qui doit etre identique : chaque habitant, l argent, les biens, le resume du jour, le journal."""
    gens = [(h.id, h.vivant, h.lieu.id if h.lieu is not None else None, h.poste, h.faim, h.etat, h.gravite,
             h.heures_jour, h.role, h.age) for h in w.habitants]
    return gens, w.argent_total(), w.biens_totaux(), w.resume_jour(), len(w.evenements)


def comparer(nom, ancien, neuf, jours, quarantaine_jour=None):
    ta = tb = 0.0
    for j in range(jours):
        if quarantaine_jour == j:
            ancien.gouv.lois["quarantaine"] = ["Pyrgos"]; neuf.gouv.lois["quarantaine"] = ["Pyrgos"]
        t = time.perf_counter()
        for _ in range(C.PAS_PAR_JOUR): ancien.pas_suivant()
        ta += time.perf_counter() - t
        t = time.perf_counter()
        for _ in range(C.PAS_PAR_JOUR): neuf.pas_suivant()
        tb += time.perf_counter() - t
        ga, argent_a, biens_a, res_a, ev_a = photo(ancien)
        gb, argent_b, biens_b, res_b, ev_b = photo(neuf)
        ecarts = [(x, y) for x, y in zip(ga, gb) if x != y]
        identique = (not ecarts and len(ga) == len(gb) and argent_a == argent_b and biens_a == biens_b
                     and res_a == res_b and ev_a == ev_b)
        print(f"  {nom} jour {j + 1} : {'IDENTIQUE' if identique else 'DIFFERENT'} | habitants {len(gb):,} "
              f"| ecarts {len(ecarts)} | argent {argent_a - argent_b:+.2e} | evenements {ev_a} / {ev_b}", flush=True)
        if not identique:
            for x, y in ecarts[:3]: print(f"     ancien {x}\n     neuf   {y}", flush=True)
            if biens_a != biens_b: print(f"     biens ancien {biens_a}\n     biens neuf   {biens_b}", flush=True)
            return False, ta, tb
    return True, ta, tb


def main():
    ok = True
    cas = [("Altis 500", lambda: WA.Monde(graine=11), lambda: W.Monde(graine=11), 6, None),
           ("Altis 500 + quarantaine", lambda: WA.Monde(graine=12), lambda: W.Monde(graine=12), 5, 1),
           ("six iles 50 000", lambda: WA.Monde(graine=13, iles=tuple(K.ILES), echelle=100),
            lambda: W.Monde(graine=13, iles=tuple(K.ILES), echelle=100), 4, None)]
    for nom, fa, fb, jours, qj in cas:
        bon, ta, tb = comparer(nom, fa(), fb(), jours, qj)
        ok &= bon
        print(f"{'PASSE ' if bon else 'ECHOUE'} {nom} : ancien {ta:.1f} s, neuf {tb:.1f} s ( x{ta / max(1e-9, tb):.1f} )", flush=True)
    print("PORTE DES COLONNES :", "FRANCHIE" if ok else "NON FRANCHIE", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
