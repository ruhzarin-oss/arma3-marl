"""L empreinte de missions de defense, d un exercice et d un monde sans combat ( porte A2, critere B5, HMT-198 ). S execute
dans n importe quel arbre du depot ( celui de PYTHONPATH ), avec les blindes coupes pour les missions de combat s ils
existent. Imprime un JSON { cle : empreinte }.
   python empreinte_missions.py graine"""
import hashlib
import json
import pickle
import sys

from monde import archipel as AR, tests as T
from monde.pays import d25_armee as A, d26_armee_soutien as S, d27_armee_tactique as TT
from guerre import porte_tir_indirect as PTI
from guerre.arsenal import porte_etat_des_lieux as PE

CHAMPS = ("side", "elt", "hid", "dx", "dy", "actif", "tir", "portee", "prot", "casque", "coups", "cal", "base", "arme", "disc",
          "stress", "moral", "moitie", "contus", "tires", "arrive_s", "viole")


def _h(x):
    return hashlib.sha256(repr(x).encode()).hexdigest()[:20]


def mission(w, u, dist, mode="combat", seed=1, taille=20):
    """Une defense de la base de u contre `taille` hommes reperes a `dist` m, qui avancent par bonds ( feu libre )."""
    p = w.pays
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, u)
    dep = (x0 + dist, y0)
    ent = S.poser_entite(p, TT._camp(p, "adverse"), dep[0], dep[1], ile, "debout", taille, 0.0)
    cond = TT.Conduite("bond", "objectif", regard="objectif", feu="libre")
    TT._reperer(p, u, ent, dep[0], dep[1], ile)
    return TT.nouvelle_mission(p, "defense", u, (x0, y0), (x0, y0), adverses=[(ent, taille, cond, [(x0, y0)], None)],
                               mode=mode, voix=True, couvert_poste="leger", seed=(seed,), ile=ile,
                               axe=S.azimut(x0, y0, dep[0], dep[1]))


def empreinte_mission(w, m):
    return _h(([m.h[k].tobytes() for k in CHAMPS], sorted(m.morts), sorted(m.blesses), int(m.neutr_adv), m.t_s, m.issue,
               sorted(m.lesions_adverses), sorted(A._dom(w.pays).sorties.items()), sorted(TT._dom(w.pays).reserve.items())))


def main(g):
    w0 = AR.creer_ile("Malden", g, 20); T.jours(w0, 1); oc = pickle.dumps(w0, protocol=4)
    u = PTI.compagnie_a_mortiers(w0.pays)
    out = {}
    TT.BLINDES = False
    for sg in range(5):
        w = pickle.loads(oc); m = mission(w, u, 1500.0, seed=7600 + sg); TT.executer(w.pays, m)
        out[f"combat_{sg}"] = empreinte_mission(w, m)
    TT.BLINDES = True
    w = pickle.loads(oc); m = mission(w, u, 1500.0, mode="exercice", seed=7650); TT.executer(w.pays, m)
    out["exercice"] = empreinte_mission(w, m)
    w = pickle.loads(oc); T.jours(w, 2)
    out["monde_2_jours"] = _h(sorted(PE.empreinte_etendue(w).items()))
    print(json.dumps(out))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2111)
