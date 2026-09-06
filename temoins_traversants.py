#!/usr/bin/env python3
"""temoins_traversants — CONTROLE N.4 DU HARNAIS, et c'est LE feu vert.

⟨Fable⟩ « Si la doctrine-par-Python perd des points contre la doctrine-SQF, la couture
mange de la performance et aucun verdict d'entrainement n'est lisible. Latence, livraison
d'actions et attribution de recompense sont certifiees par ce seul nombre. »

On rejoue les deux temoins A TRAVERS toute la couture — ticket Python, observation par le
RPT, geste par la DLL — et on compare aux IC GELES, mesures le 30/08 dans Arma sur 51
episodes par temoin, banc B0@30 :
    DOCTRINE  100,0 %  IC95 [93,0 ; 100]
    ALEATOIRE  11,8 %  IC95 [ 5,5 ; 23,4]

⚠️ AUCUN GRADIENT NE TOMBE AVANT QUE CE CONTROLE SOIT VERT.
"""
import sys, time, random, argparse, statistics
sys.path.insert(0, "/home/younes/arma3-marl")
from pont import Pont
from para import instance

PROFIL = "/mnt/c/Users/Younes/hmtech0"
CIBLES = {"DOCTRINE": (93.0, 100.0), "ALEATOIRE": (5.5, 23.4)}

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    ph = k / n; d = 1 + z*z/n
    c = (ph + z*z/(2*n)) / d
    h = z * ((ph*(1-ph)/n + z*z/(4*n*n)) ** 0.5) / d
    return (max(0.0, c-h)*100, min(1.0, c+h)*100)

def choisir(temoin, obs, rng):
    """Les memes deux politiques que le banc SQF, mais ecrites ICI."""
    if temoin == "ALEATOIRE":
        return rng.randrange(13)
    return 8                      # DOCTRINE a B0 : l'ordre le plus bete qui vise le but

def episode(pont, uid, temoin, rng, D=30, barreau="B0", sites=None, capdef=False):
    # tout l'alea du monde est tire ICI et voyage dans le ticket
    dx  = rng.uniform(-D/25, D/25)
    dy  = rng.uniform(-D/25, D/25)
    daz = rng.uniform(-6, 6)
    if sites is None:
        pont.envoyer(f"HMT_TICKET = [{uid}, \"{barreau}\", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}];")
    else:
        st = rng.choice(sites)
        # ⚠️ LE CAP DU DEFENSEUR EST TIRE ICI, comme tout l'alea du monde, et il voyage
        # dans le ticket. 0 = il vous fait face, 180 = il vous tourne le dos. Le laisser
        # a 0 mesurerait le pire cas et rendrait « frontiere du monde », pas « barreau ».
        cd = rng.uniform(-180, 180) if capdef else 0
        pont.envoyer(f"HMT_TICKET = [{uid}, \"{barreau}\", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}, "
                     f"{st['x']:.2f}, {st['y']:.2f}, {st['az']}, {cd:.1f}];")

    cycles = 0
    t0 = time.time()
    while time.time() - t0 < 90:
        l = pont.attendre("[ECHP] ", 90 - (time.time() - t0))
        if l is None:
            return None, "silence"
        if "] OBS " in l:
            p = l.split("] OBS ")[1].replace('"', "").split()
            if int(p[0]) != uid:            # appariement par uid, JAMAIS par ordre d'arrivee
                continue
            cycle = int(p[1]); obs = [float(x) for x in p[2:11]]
            g = choisir(temoin, obs, rng)
            pont.envoyer(f"HMT_ACT = [{uid}, {cycle}, {g}];")
            cycles += 1
        elif "] RESULT " in l:
            p = l.split("] RESULT ")[1].replace('"', "").split()
            if int(p[0]) != uid:
                continue
            prise, duree, dfin, viv, coups, voids, refus = \
                int(p[1]), float(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6]), int(p[7])
            if voids:
                return None, "void"
            return dict(prise=prise, duree=duree, dfin=dfin, viv=viv,
                        coups=coups, refus=refus, cycles=cycles), None
    return None, "timeout"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=51)
    ap.add_argument("--temoins", default="DOCTRINE,ALEATOIRE")
    ap.add_argument("--graine", type=int, default=4242)
    ap.add_argument("--D", type=float, default=30.0)
    ap.add_argument("--instance", type=int, default=0)
    # ⚠️ A UNE AUTRE DISTANCE, LES BANDES DE B0@30 NE VEULENT RIEN DIRE. --dimensionner
    # les fait taire : on MESURE au lieu de comparer a une cible qui n'existe pas.
    ap.add_argument("--dimensionner", action="store_true")
    ap.add_argument("--sites", default="")
    ap.add_argument("--barreau", default="B0")
    ap.add_argument("--capdef", action="store_true")
    a = ap.parse_args()

    inst = instance(a.instance)
    if a.dimensionner:
        globals()['CIBLES'] = {}
        print(f"MODE DIMENSIONNEMENT a D={a.D:.0f} m : aucune cible, on mesure.\n", flush=True)
    lots = None
    if a.sites:
        from sites import charger
        lots = charger(a.sites)
        print(f"sites : lot '{a.sites}', {len(lots)} sites, tires a chaque episode\n", flush=True)
    pont = Pont(inst['profil'], pont_dir=inst['pont'])
    print(f"pont : rpt={pont.rpt.split('/')[-1]}  n={pont.n}", flush=True)
    if pont.attendre("ETAT PRET", 60) is None:
        print("la mission ne dit jamais PRET"); return 2

    uid = 1000
    verdicts = {}
    for temoin in a.temoins.split(","):
        # ⚠️ `hash()` SUR UNE CHAINE EST RANDOMISE PAR PROCESSUS en Python (PEP 456).
        # La graine n'etait donc PAS reproductible d'une execution a l'autre : deux
        # mesures du meme temoin, meme --graine, tiraient des sites differents. C'est
        # ce qui a rendu 49/51 et 153/153 incomparables le 02/09. On prend un decalage
        # STABLE et declare.
        DECALAGE = {"DOCTRINE": 0, "ALEATOIRE": 500}
        rng = random.Random(a.graine + DECALAGE.get(temoin, 900))
        pris = 0; joues = 0; rejets = {}
        t0 = time.time()
        for i in range(a.n):
            uid += 1
            r, cause = episode(pont, uid, temoin, rng, a.D, a.barreau, sites=lots, capdef=a.capdef)
            if r is None:
                rejets[cause] = rejets.get(cause, 0) + 1
                if sum(rejets.values()) > a.n * 0.2:
                    print(f"  !! plus de 20 % de rejets ({rejets}) — lot suspect, on arrete")
                    break
                continue
            joues += 1; pris += r["prise"]
            if (i + 1) % 10 == 0:
                print(f"  {temoin} {i+1}/{a.n}  joues={joues} pris={pris} rejets={rejets}", flush=True)
        lo, hi = wilson(pris, joues) if joues else (0, 0)
        taux = 100.0 * pris / joues if joues else float('nan')
        if temoin in CIBLES:
            alo, ahi = CIBLES[temoin]
            ok = joues > 0 and alo <= taux <= ahi
            verdicts[temoin] = ok
            print(f"\n{temoin} : {pris}/{joues} = {taux:.1f} %  IC95 [{lo:.1f} ; {hi:.1f}]"
                  f"   cible Arma [{alo:.1f} ; {ahi:.1f}]  -> {'DANS' if ok else 'HORS'}"
                  f"   rejets={rejets}  ({time.time()-t0:.0f} s)\n", flush=True)
        else:
            # dimensionnement : on ne juge pas, on rend le nombre et sa bande.
            print(f"\n{temoin} : {pris}/{joues} = {taux:.1f} %  IC95 [{lo:.1f} ; {hi:.1f}]"
                  f"   (D={a.D:.0f} m, aucune cible — on dimensionne)"
                  f"   rejets={rejets}  ({time.time()-t0:.0f} s)\n", flush=True)

    if a.dimensionner:
        print("DIMENSIONNEMENT TERMINE — ces nombres deviennent la cible du barreau,")
        print("apres avoir ete ecrits dans une pre-inscription. Ils ne jugent rien aujourd'hui.")
        return 0
    tous = all(verdicts.values()) and len(verdicts) == len(a.temoins.split(","))
    print("VERDICT CONTROLE 4 :",
          "VERT — la couture ne mange rien, l'entrainement peut commencer" if tous
          else "ROUGE — la couture est en cause, aucun verdict d'entrainement ne serait lisible")
    return 0 if tous else 1

if __name__ == "__main__":
    sys.exit(main())
