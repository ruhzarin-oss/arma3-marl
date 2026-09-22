"""LE RESEAU ROUTIER D ALTIS, MESURE - point 7 des douze manques.

Le monde estimait ses distances a vol d oiseau multiplie par 1,3. Ici un vrai camion part, roule par les routes
d Altis avec un chauffeur, et rapporte ce qu il a REELLEMENT parcouru et en combien de temps. Le monde apprend sa
propre carte au lieu de la supposer.

   python -m monde.routes --port 2350            ( le cerveau du monde doit etre arrete : il tient le port )
Porte ecrite d avance ( plans/plan-12-manques.md, point 7 ) : ecart entre distance calculee et trajet reel < 15 %."""
import argparse, json, os, time
from . import carte as K, config as C, pont as PT

SORTIE = "/mnt/data/hmt/depot/monde/donnees/routes_altis.json"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    p.add_argument("--attente", type=float, default=2400.0, help="secondes reelles avant d abandonner")
    p.add_argument("--sortie", default=SORTIE)
    a = p.parse_args()
    carte = K.Carte()
    villes = [l for l in carte.lieux.values() if l.type == "capitale"]
    paires = [(x, y) for i, x in enumerate(villes) for y in villes[i + 1:]]
    pont = PT.Pont(a.port)
    print("en attente d Arma", flush=True)
    if not pont.attendre(300): print("Arma ne s est pas connecte"); return 2

    envois, attendus = [], {}
    for k, (x, y) in enumerate(paires):
        for sens, (d, f) in enumerate(((x, y), (y, x))):
            cid = 8000 + 2 * k + sens
            attendus[cid] = (d.id, f.id, carte.km_route(d, f))
            envois.append(["camion", cid, [round(d.pos[0]), round(d.pos[1])], [round(f.pos[0]), round(f.pos[1])]])
    pont.envoyer(envois)
    print(f"{len(envois)} camions partis : {[f'{d}->{f}' for d, f, _ in attendus.values()]}", flush=True)

    mesures, t0 = {}, time.time()
    while attendus and time.time() - t0 < a.attente:
        for m in pont.messages(1.0):
            if not m or m[0] != "camion": continue
            cid, etat, km, minutes = m[1], m[2], float(m[3]), float(m[4])
            if cid not in attendus: continue
            d, f, estime = attendus.pop(cid)
            mesures.setdefault(f"{d}-{f}", {}).update({"etat": etat, "km_reels": km, "minutes": minutes, "km_estimes": estime})
            print(f"{d} -> {f} : {etat}, {km:.1f} km reels contre {estime:.1f} estimes, {minutes:.1f} min", flush=True)
    for cid, (d, f, estime) in attendus.items():
        mesures.setdefault(f"{d}-{f}", {}).update({"etat": "sans_reponse", "km_estimes": estime})
        print(f"{d} -> {f} : AUCUNE reponse", flush=True)

    arrives = [v for v in mesures.values() if v.get("etat") == "arrive"]
    if arrives:
        ecarts = [abs(v["km_reels"] - v["km_estimes"]) / max(1e-6, v["km_reels"]) for v in arrives]
        print(f"ecart median entre calcul et route reelle : {sorted(ecarts)[len(ecarts) // 2]:.1%} "
              f"( {len(arrives)} trajets arrives sur {len(mesures)} )", flush=True)
    os.makedirs(os.path.dirname(a.sortie), exist_ok=True)
    with open(a.sortie, "w") as f: json.dump(mesures, f, indent=1)
    print("ecrit :", a.sortie, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
