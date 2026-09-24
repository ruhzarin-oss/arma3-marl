"""Les outils communs des portes des domaines, et la porte que TOUT domaine doit passer."""
import pickle
from .. import monde as W, config as C
from ..socle import registre as R
from . import pays as P

FAMILLES_HORS_LIVRE_E1 = ("gouvernement", "marches")   # importer, exporter_or, ventes au port : monde.py:136, 145, 516, 522


def monde(domaines, graine=C.GRAINE, echelle=1.0, modes=None, iles=("Altis",)):
    """Un Monde E1 avec ses domaines ( et leurs dependances ) installes."""
    w = W.Monde(graine=graine, echelle=echelle, iles=iles)
    return w, P.installer(w, domaines, modes)


def jours(w, n):
    for _ in range(int(n * C.PAS_PAR_JOUR)): w.pas_suivant()
    return w


def menages_habites(w):
    return [m for m in w.menages if any(h.vivant for h in m.membres)]


def faim(w):
    return w.stats_jour.get("menages_sans_nourriture", 0) / max(1, len(menages_habites(w)))


def hors_livre(p, net0, ext0, monnaie0):
    """L argent exterieur qui est entre sans passer par le grand livre : le seul reste admis au rapprochement."""
    L = p.socle.livre
    net = L.net_par_classe()
    d_ext = (L.ext["entree"] - ext0["entree"]) - (L.ext["sortie"] - ext0["sortie"])
    d_emis = (L.monnaie["emise"] - monnaie0["emise"]) - (L.monnaie["detruite"] - monnaie0["detruite"])
    vu = sum(net.get(k, 0.0) - net0.get(k, 0.0) for k in ("Exterieur", "Emission"))
    return d_ext + d_emis + vu


def porte_commune(domaine, n_jours=12, graine=11, modes=None):
    """La porte de tout domaine. Installe avec ses dependances, le pays vit `n_jours` jours :
      - la conservation du socle tient ( argent, biens, objets ) ;
      - seules les familles du moteur E1 qui touchent l exterieur a la main ( gouvernement, marches ) ont de l argent
        hors du grand livre, et ce reste est exactement l argent exterieur entre a la main ;
      - le pays reste vivable : au plus 5 % des menages habites sans nourriture, au moins 97 % des habitants vivants ;
      - un instantane a mi-course reprend a l identique, et deux mondes de meme graine sont identiques."""
    w, p = monde([domaine], graine, modes=modes)
    L = p.socle.livre
    net0, ext0, monnaie0 = L.net_par_classe(), dict(L.ext), dict(L.monnaie)
    rap = R.Rapprochement(p.socle.registre, L)
    vivants0 = sum(1 for h in w.habitants if h.vivant)
    moitie = n_jours // 2
    jours(w, moitie); snap = pickle.dumps(w); jours(w, n_jours - moitie)
    repris = jours(pickle.loads(snap), n_jours - moitie)
    jumeau = jours(monde([domaine], graine, modes=modes)[0], n_jours)
    tenue, msg = p.socle.conservation.tenue()
    restes = rap.restes()
    autres = {k: v for k, v in restes.items() if k not in FAMILLES_HORS_LIVRE_E1 and abs(v) > R.tolerance(v)}
    attendu = hors_livre(p, net0, ext0, monnaie0)
    exterieur = not autres and abs(sum(restes.values()) - attendu) <= R.tolerance(attendu) + 1e-6
    f = faim(w)
    vivants = sum(1 for h in w.habitants if h.vivant)
    vivable = f <= 0.05 and vivants >= 0.97 * vivants0
    identique = (w.resume_jour() == repris.resume_jour() == jumeau.resume_jour()
                 and w.argent_total() == repris.argent_total() == jumeau.argent_total())
    ok = tenue and exterieur and vivable and identique
    return ok, (f"{domaine}, {n_jours} jours : conservation {msg} ; argent hors livre "
                f"{'exterieur seulement' if exterieur else f'NON EXTERIEUR {autres}'} ; faim {f:.1%}, vivants "
                f"{vivants}/{vivants0} ; reprise et jumeau {'identiques' if identique else 'DIFFERENTS'}")
