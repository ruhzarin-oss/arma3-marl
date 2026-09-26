"""LA CARTE SE RACONTE ELLE-MEME - point 13 : une geographie par ile, demandee au jeu.

Le monde ne suppose plus la carte : il la demande au serveur qui la fait tourner. Chaque serveur Arma rend les lieux
nommes de son ile ( CfgWorlds >> monde >> Names ), et le cerveau les ecrit dans donnees/<ile>_lieux.json.
Marche pour une carte officielle comme pour une carte moddee dont la configuration n a jamais ete recoltee.

   python -m monde.geographie --port 2350 --attente 180     ( le cerveau du monde doit etre arrete )"""
import argparse, json, os, time
from . import pont as PT

ICI = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    p.add_argument("--attente", type=float, default=180.0)
    a = p.parse_args()
    pont = PT.Pont(a.port)
    print("en attente des serveurs", flush=True)
    if not pont.attendre(240): print("aucun serveur Arma"); return 2
    time.sleep(45)                      # laisser chaque serveur se nommer ( il se presente toutes les 30 s )
    iles = [i for i in pont.iles() if i != "inconnue"]
    print("iles connectees :", iles, flush=True)
    for ile in iles: pont.envoyer([["lieux"]], ile)

    recolte, attendus, t0 = {}, {}, time.time()
    while time.time() - t0 < a.attente:
        for ile_msg, m in pont.messages_iles(1.0):
            if not m or m[0] != "lieux": continue
            _, monde, total, page = m
            attendus[monde] = int(total)
            recolte.setdefault(monde, [])
            for l in page:
                recolte[monde].append({"id": str(l[0]), "type": str(l[1]), "pos": [float(l[2]), float(l[3])],
                                       "rayon": [float(l[4]), float(l[5])]})
        # toutes les iles connectees doivent avoir repondu, pas seulement la plus rapide
        if set(attendus) >= set(iles) and all(len(recolte.get(k, [])) >= v for k, v in attendus.items()): break

    for monde, lieux in recolte.items():
        vus, propres = set(), []
        for l in lieux:
            if l["id"] in vus: continue
            vus.add(l["id"]); propres.append(l)
        chemin = os.path.join(ICI, "donnees", f"{monde.lower()}_lieux.json")
        with open(chemin, "w") as f: json.dump(propres, f, indent=1)
        types = {}
        for l in propres: types[l["type"]] = types.get(l["type"], 0) + 1
        print(f"{monde} : {len(propres)} lieux ecrits dans {os.path.basename(chemin)} | {types}", flush=True)
    if not recolte: print("aucune geographie recue", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
