"""LA MONTEE EN CHARGE - point 11 des douze manques : jusqu ou un serveur tient-il des corps ?

On incarne par paquets de 50 dans les trois capitales, et on lit ce qu Arma rapporte : nombre de corps et images par
seconde. La legende dit « environ 300 unites par serveur » ; ici on mesure, au lieu de la croire.

   python -m monde.charge --max 600        ( le cerveau du monde doit etre arrete : il tient le port )"""
import argparse, json, os, time
from . import carte as K, pont as PT

CIVILS = ["C_man_1", "C_man_polo_1_F", "C_man_polo_4_F", "C_man_w_worker_F", "C_scientist_F"]


def vus_recents(pont):
    """Les corps signales en mouvement dans les derniers rapports ( vitesse > 0 )."""
    return []


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    p.add_argument("--max", type=int, default=600)
    p.add_argument("--paquet", type=int, default=50)
    p.add_argument("--repos", type=float, default=25.0, help="secondes d observation par palier")
    p.add_argument("--marche", action="store_true", help="tous les corps marchent : c est le mouvement qui coute")
    p.add_argument("--sortie", default="/mnt/data/hmt/monde/charge")
    a = p.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    carte = K.Carte()
    villes = [carte.lieux[x] for x in ("Kavala", "Athira", "Pyrgos")]
    pont = PT.Pont(a.port)
    print("en attente d Arma", flush=True)
    if not pont.attendre(300): print("Arma ne s est pas connecte"); return 2
    paliers, n = [], 0
    journal = open(os.path.join(a.sortie, "charge.jsonl"), "a")
    while n < a.max:
        ordres = []
        for k in range(a.paquet):
            i = 20000 + n + k
            v = villes[(n + k) % 3]
            ordres.append(["incarner", i, CIVILS[i % len(CIVILS)], "civ", [round(v.pos[0]), round(v.pos[1])], 350, (i * 7) % 997])
        pont.envoyer(ordres); n += a.paquet
        if a.marche:      # tout le monde repart vers un autre batiment : l ordonnanceur et le calcul de chemin travaillent
            pont.envoyer([["aller", 20000 + i, [round(villes[i % 3].pos[0]), round(villes[i % 3].pos[1])], 350,
                           (i * 13 + int(time.time())) % 997] for i in range(n)])
        fps, corps, t0 = [], None, time.time()
        while time.time() - t0 < a.repos:
            for m in pont.messages(0.5):
                if m and m[0] == "etat": fps.append(m[4]); corps = m[5]
        if fps:
            moy = sum(fps) / len(fps)
            marcheurs = sum(1 for i in vus_recents(pont) if i)      # place tenue : le compte des corps en marche
            palier = {"demandes": n, "corps": corps, "images_par_seconde": round(moy, 1), "pire": min(fps),
                      "en_marche": marcheurs}
            paliers.append(palier); journal.write(json.dumps(palier) + "\n"); journal.flush()
            print(palier, flush=True)
            if moy < 15:
                print("plafond atteint : moins de 15 images par seconde", flush=True); break
    pont.envoyer([["desincarner", 20000 + i] for i in range(n)])
    time.sleep(5)
    with open(os.path.join(a.sortie, "paliers.json"), "w") as f: json.dump(paliers, f, indent=1)
    print("paliers ecrits", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
