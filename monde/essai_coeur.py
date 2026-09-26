"""La porte du coeur Rust : `coeur.deplacer` doit decider EXACTEMENT comme `Monde.deplacer`, habitant par habitant, a
chaque pas d une journee, et on mesure le gain de temps.

   python -m monde.essai_coeur --echelle 2000        ( un million d habitants, six iles )
Les colonnes sont reconstruites depuis les objets Python a chaque pas : c est le cout de la preuve, pas du moteur.
Il est mesure a part, parce qu il dit pourquoi la refonte en colonnes est necessaire."""
import argparse, time
import numpy as np
import coeur
from . import monde as W, carte as K, config as C

HORAIRE = {None: -1, "jour": 0, "bureau": 1, "nuit": 2, "ecole": 3, "marche": 4, "garde": 5}
POSTE = {"maison": 0, "travail": 1, "hopital": 2, "voyage": 3}


def colonnes(w, idx):
    H = w.habitants
    n = len(H)
    q = set(w.gouv.lois["quarantaine"])
    c = {
        "sauter": np.fromiter(((h.poste == "voyage" or h.id in w.sejours) for h in H), np.uint8, n),
        "vivant": np.fromiter((h.vivant for h in H), np.uint8, n),
        "etat_i": np.fromiter((h.etat == "I" for h in H), np.uint8, n),
        "gravite": np.fromiter((h.gravite for h in H), np.float64, n),
        "horaire": np.fromiter((HORAIRE[h.horaire] for h in H), np.int8, n),
        "equipe": np.fromiter((h.equipe for h in H), np.int32, n),
        "decalage": np.fromiter((h.decalage for h in H), np.float64, n),
        "enferme": np.fromiter(((h.domicile.id in q or (h.travail is not None and h.travail.id in q)) for h in H), np.uint8, n),
        "faim": np.fromiter((h.faim for h in H), np.float64, n),
        "public": np.fromiter((C.ROLES[h.role][2] for h in H), np.uint8, n),
        "travail": np.fromiter((idx[h.travail.id] if h.travail is not None else -1 for h in H), np.int32, n),
        "domicile": np.fromiter((idx[h.domicile.id] for h in H), np.int32, n),
        "hopital": np.fromiter((idx[h.domicile.marche.id] for h in H), np.int32, n),
        "lieu": np.fromiter((idx[h.lieu.id] if h.lieu is not None else -1 for h in H), np.int32, n),
        "poste": np.fromiter((POSTE.get(h.poste, 0) for h in H), np.uint8, n),
        "heures": np.fromiter((h.heures_jour for h in H), np.float64, n),
    }
    return c, bool(q)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--echelle", type=float, default=2000)
    p.add_argument("--pas", type=int, default=C.PAS_PAR_JOUR)
    a = p.parse_args()
    t0 = time.time()
    w = W.Monde(iles=tuple(K.ILES), echelle=a.echelle)
    idx = {lid: i for i, lid in enumerate(w.carte.lieux)}
    print(f"{len(w.habitants)} habitants, monde cree en {time.time() - t0:.0f} s", flush=True)
    stats = {"rust": 0.0, "python": 0.0, "colonnes": 0.0, "compares": 0, "ecarts": 0, "exclus": 0, "pas_quarantaine": 0}
    original = w.deplacer

    def compare(h):
        t = time.perf_counter(); c, quarantaine = colonnes(w, idx); stats["colonnes"] += time.perf_counter() - t
        if quarantaine: stats["pas_quarantaine"] += 1        # le tirage au hasard de la quarantaine n est pas encore porte
        t = time.perf_counter()
        coeur.deplacer(h, C.ABSENCE_FAIM, C.MINUTES_PAR_PAS / 60.0, c["sauter"], c["vivant"], c["etat_i"], c["gravite"],
                       c["horaire"], c["equipe"], c["decalage"], c["enferme"], c["faim"], c["public"], c["travail"],
                       c["domicile"], c["hopital"], c["lieu"], c["poste"], c["heures"])
        stats["rust"] += time.perf_counter() - t
        t = time.perf_counter(); original(h); stats["python"] += time.perf_counter() - t
        # habitant par habitant : meme lieu, meme poste, memes heures payees
        for i, hab in enumerate(w.habitants):
            if c["sauter"][i]: stats["exclus"] += 1; continue
            stats["compares"] += 1
            lieu_py = idx[hab.lieu.id] if hab.lieu is not None else -1
            if (lieu_py != c["lieu"][i] or POSTE.get(hab.poste, 0) != c["poste"][i]
                    or hab.heures_jour != c["heures"][i]):
                stats["ecarts"] += 1
                if stats["ecarts"] <= 5:
                    print(f"  ECART pas {w.pas} habitant {hab.id} : python {hab.poste}/{lieu_py}/{hab.heures_jour} "
                          f"rust {c['poste'][i]}/{c['lieu'][i]}/{c['heures'][i]}", flush=True)

    w.deplacer = compare
    t0 = time.time()
    for k in range(a.pas):
        w.pas_suivant()
        if k % 24 == 23:
            print(f"  pas {k + 1:3d} | compares {stats['compares']:>11,} | ecarts {stats['ecarts']} | "
                  f"rust {stats['rust']:6.2f} s | python {stats['python']:6.1f} s | colonnes {stats['colonnes']:6.1f} s", flush=True)
    print(f"PORTE : {stats['ecarts']} ecart sur {stats['compares']:,} decisions comparees "
          f"( {stats['exclus']:,} exclues : en mer ou en sejour ; {stats['pas_quarantaine']} pas avec quarantaine )", flush=True)
    print(f"TEMPS sur {a.pas} pas : rust {stats['rust']:.2f} s | python {stats['python']:.1f} s | "
          f"gain x{stats['python'] / max(1e-9, stats['rust']):.0f} | construction des colonnes {stats['colonnes']:.1f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
