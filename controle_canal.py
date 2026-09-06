#!/usr/bin/env python3
"""controle_canal — LES CHAMPS « ENNEMI » S'ALLUMENT-ILS DEVANT QUELQU'UN ?

⚠️ CE QU'ON CONTROLE, ET POURQUOI AVANT TOUT GRADIENT. L'observation porte deja quatre
champs sur l'ennemi (indices 3,4,5,6) et un sur le feu recu (8). Ils n'ont JAMAIS servi :
tout le barreau B0 se joue sans adversaire, ils y valent leur valeur par defaut. Avant de
batir un barreau adverse dessus, il faut savoir s'ils sont cables ou s'ils sont morts.

⟨Fable⟩ « Le B1 qui existe dans la mission n'est pas un adversaire, c'est un decor. Un
defenseur IA coupee, immobile, CARELESS, ne peut faire echouer ni la doctrine ni
l'aleatoire. Ne le joue pas comme barreau. Joue-le une demi-heure comme controle
d'instrument : les champs s'allument-ils quand il y a quelqu'un ? »

LE CONTROLE SAIT ECHOUER, et bruyamment :
  · champs identiques entre B0 et B1 -> LE CANAL EST MORT, la nuit s'arrete ici.
  · champ 3 qui descend sous 2.0, champ 6 a 0.125, champs 4/5 non nuls -> il est cable.
Meme graine des deux cotes : memes sites, meme jitter. Seule la presence change.
"""
import sys, time, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
import random
from pont import Pont
from para import instance
from sites import charger

NOMS = ["d_obj", "ux", "uy", "d_enn", "ex", "ey", "n_enn", "posture", "suppression"]
INTERET = [3, 4, 5, 6, 8]

def episodes(pont, barreau, n, sites, uid0):
    """Doctrine (geste 8) ; on ne veut pas une politique, on veut des observations."""
    rng = random.Random(4242)
    obs = []
    uid = uid0
    for i in range(n):
        uid += 1
        D = 30.0
        dx, dy = rng.uniform(-D/25, D/25), rng.uniform(-D/25, D/25)
        daz = rng.uniform(-6, 6)
        st_ = rng.choice(sites)
        pont.envoyer(f'HMT_TICKET = [{uid}, "{barreau}", {D}, {dx:.3f}, {dy:.3f}, {daz:.3f}, '
                     f'{st_["x"]:.2f}, {st_["y"]:.2f}, {st_["az"]}];')
        t0 = time.time()
        while time.time() - t0 < 60:
            l = pont.attendre("[ECHP] ", 60 - (time.time() - t0))
            if l is None: break
            if "] OBS " in l:
                p = l.split("] OBS ")[1].replace('"', "").split()
                if int(p[0]) != uid: continue
                obs.append([float(x) for x in p[2:11]])
                pont.envoyer(f"HMT_ACT = [{uid}, {int(p[1])}, 8];")
            elif "] RESULT " in l:
                if int(l.split("] RESULT ")[1].split()[0]) == uid: break
    return obs

def main():
    inst = instance(1)
    pont = Pont(inst["profil"], pont_dir=inst["pont"], patience_sync=60)
    if pont.attendre("ETAT PRET", 90) is None:
        print("la mission ne dit jamais PRET"); return 2
    sites = charger("jugement")
    print(f"controle sur l'instance 1, {len(sites)} sites, meme graine des deux cotes\n", flush=True)

    res = {}
    for b, uid0 in [("B0", 700000), ("B1", 710000)]:
        o = episodes(pont, b, 20, sites, uid0)
        res[b] = o
        print(f"barreau {b} : {len(o)} observations", flush=True)

    print(f"\n{'champ':14s} {'B0 (sans personne)':>28s}   {'B1 (avec le decor)':>28s}")
    verdict = []
    for k in INTERET:
        a = [v[k] for v in res["B0"]]; c = [v[k] for v in res["B1"]]
        if not a or not c: continue
        fa = f"min={min(a):6.3f} med={st.median(a):6.3f} max={max(a):6.3f}"
        fc = f"min={min(c):6.3f} med={st.median(c):6.3f} max={max(c):6.3f}"
        bouge = (min(c) != min(a)) or (max(c) != max(a)) or (st.median(c) != st.median(a))
        verdict.append((NOMS[k], bouge))
        print(f"{NOMS[k]:14s} {fa:>28s}   {fc:>28s}   {'ALLUME' if bouge else 'inerte'}")

    vivants = [n for n, b in verdict if b]
    print(f"\nchamps qui reagissent a la presence : {vivants if vivants else 'AUCUN'}")
    if not vivants:
        print("\n⛔ LE CANAL EST MORT. Aucun champ ne distingue un monde avec defenseur")
        print("   d'un monde vide. Batir un barreau adverse dessus serait batir sur rien.")
        return 1
    print("\n✅ LE CANAL EST CABLE. Il dit OU est l'ennemi.")
    print("   Il ne dit toujours pas S'IL VOUS VOIT — cone, visibilite, knowsAbout")
    print("   restent a ajouter. C'est l'objet de l'etape suivante.")
    return 0

sys.exit(main())
