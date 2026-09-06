#!/usr/bin/env python3
"""porte_b0 — L'EVALUATION DE PORTE. Elle juge, elle n'entraine pas.

⚠️ POURQUOI ELLE NE PEUT PAS ETRE LA COURBE D'ENTRAINEMENT. La nuit a fini a 99,0 % sur
les cent derniers episodes — mais ces cent-la ont servi a APPRENDRE. Les lire comme un
verdict, c'est juger sur ce qui a servi a choisir. La porte se joue ailleurs :

  · GRAINES DE MISSION NEUVES — un autre tirage que celui de l'entrainement (90210+graine).
    Ici 777000+serie. Le jitter, l'azimut et l'ordre des episodes sont donc inedits.
  · MODE ECHANTILLONNE, jamais argmax. Deux graines sur trois du depot ne se condensent
    pas ; on juge la politique telle qu'elle sera DEPLOYEE.
  · SERIE 4 SUR 5. Une porte binaire a un essai se laisse franchir par un coup de des.
  · AUCUN GRADIENT. Le reseau est charge, mis en eval, et n'apprend rien ici.

PORTE PRE-INSCRITE : B0@30 >= 93,0 % — borne basse de l'IC Wilson de la doctrine mesuree
sur ce banc, n=51. Non-inferiorite : la doctrine y fait 100 %, on ne demande pas de la
battre, on demande de la rejoindre.
"""
import os, sys, time, random, argparse
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from pont import Pont
from harnais import Politique, episode, PROFIL, sha_mission
from para import instance

PORTE = 93.0
SERIES = 5
N = 51

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    ph = k/n; d = 1 + z*z/n
    c = (ph + z*z/(2*n)) / d
    h = z * ((ph*(1-ph)/n + z*z/(4*n*n)) ** 0.5) / d
    return (max(0.0, c-h)*100, min(1.0, c+h)*100)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--point", required=True)
    ap.add_argument("--D", type=float, default=30.0)
    ap.add_argument("--barreau", default="B0")
    ap.add_argument("--series", type=int, default=SERIES)
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--instance", type=int, default=0)
    ap.add_argument("--sites", default="")
    # ⚠️ JUGER DANS UN AUTRE MONDE QUE CELUI DE L'ENTRAINEMENT SE DIT, IL NE SE TAIT PAS.
    # Le refus sur SHA discordant est la pour empecher un jugement muet dans un monde
    # change par accident. Ici le monde est change EXPRES : on ne desactive pas le garde-
    # fou, on exige un aveu qui nomme les deux SHA dans la sortie.
    ap.add_argument("--transfert", action="store_true")
    a = ap.parse_args()

    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    c = torch.load(a.point, map_location=dev, weights_only=False)
    sha = sha_mission()
    if c["sha_mission"] != sha:
        if not a.transfert:
            print(f"REFUS DE JUGER : le point porte le SHA {c['sha_mission']}, la mission "
                  f"deployee vaut {sha}. Ce ne serait pas le meme monde.")
            return 2
        print(f"⚠️ JUGEMENT EN TRANSFERT, MONDE DIFFERENT ASSUME.")
        print(f"   politique entrainee dans le monde {c['sha_mission']}")
        print(f"   jugee            dans le monde {sha}")
        print(f"   Toute citation de ce chiffre doit porter cette phrase.\n")
    pol = Politique().to(dev); pol.load_state_dict(c["pol"]); pol.eval()
    print(f"point   : {os.path.basename(a.point)}  ({c['fait']} episodes d'entrainement, "
          f"graine torch {c['graine']})")
    print(f"monde   : SHA {sha} concordant")
    print(f"porte   : >= {PORTE} %  ·  {a.series} series de {a.n}  ·  "
          f"ECHANTILLONNE  ·  graines de mission NEUVES\n", flush=True)

    inst = instance(a.instance)
    pont = Pont(inst['profil'], pont_dir=inst['pont'])
    lots = None
    if a.sites:
        from sites import charger
        lots = charger(a.sites)
        print(f"sites   : lot '{a.sites}', {len(lots)} sites tires a chaque episode\n", flush=True)
    if pont.attendre("ETAT PRET", 60) is None:
        print("la mission ne dit jamais PRET"); return 2

    uid = 900000
    passees, rejets_tot = 0, {}
    for s in range(a.series):
        rng = random.Random(777000 + s)          # DISJOINT du 90210+graine de l'entrainement
        pris, joues, rejets = 0, 0, {}
        t0 = time.time()
        for i in range(a.n):
            uid += 1
            traj, r = episode(pont, pol, uid, rng, a.D, a.barreau, sites=lots)
            if traj is None:
                rejets[r] = rejets.get(r, 0) + 1
                rejets_tot[r] = rejets_tot.get(r, 0) + 1
                continue
            joues += 1; pris += int(r)
        taux = 100.0*pris/joues if joues else float('nan')
        lo, hi = wilson(pris, joues)
        ok = joues > 0 and taux >= PORTE
        passees += int(ok)
        print(f"  serie {s+1}/{a.series} : {pris}/{joues} = {taux:5.1f} %  "
              f"IC95 [{lo:5.1f} ; {hi:5.1f}]  rejets={rejets}  "
              f"{'PASSE' if ok else 'ECHOUE'}   ({time.time()-t0:.0f} s)", flush=True)

    print(f"\n{passees}/{a.series} series au-dessus de {PORTE} %   rejets totaux={rejets_tot}")
    verdict = passees >= 4
    print(f"VERDICT PORTE {a.barreau}@{a.D:.0f} :",
          "PASSEE (4/5 exige)" if verdict
          else "NON PASSEE — la politique ne tient pas la porte sur graines neuves")
    print("\n⚠️ Ce verdict ne vaut que pour UNE graine torch. La regle pre-inscrite exige")
    print("   deux graines : si elles divergent, on ne cite NI l'une NI l'autre.")
    return 0 if verdict else 1

if __name__ == "__main__":
    sys.exit(main())
