#!/usr/bin/env python3
"""audit — L'ETIQUETTE DIT-ELLE LA VERITE SUR L'IMAGE ?

⚠️ LA FAUTE QU'ON INSTRUIT ICI, nommee par Fable : « etiquette connue par construction »
est un silence pris pour un etat. La fabrique sait ou elle a POSE le soldat ; elle ne sait
pas s'il est VISIBLE dans l'image capturee. LOD non charge, herbe, repli de terrain,
capture prise trop tot : autant de facons pour qu'une image etiquetee « present » soit
vide. Si c'est le cas ne serait-ce que sur une fraction du jeu, les 70 % contre 74 % de
la sonde ne mesuraient pas un encodeur — ils mesuraient un jeu menteur.

Ce script ne mesure rien. Il fabrique des planches-contact que JE regarde, une par classe,
avec la distance ecrite sur chaque vignette. C'est un audit a l'oeil, et c'est le bon
outil : la question est « y a-t-il un homme sur cette image », et l'oeil y repond.

On audite le jeu CENTRE (lat=0), celui de la derniere sonde : le soldat y est au milieu,
donc un recadrage central suffit a le montrer s'il existe.
"""
import os, sys, json, random, argparse
from PIL import Image, ImageDraw

JEU = "/mnt/c/hmt_bridge/jeu"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="/home/younes/arma3-marl/oeil_centre.jsonl")
    ap.add_argument("--par-classe", type=int, default=30)
    ap.add_argument("--crop", type=int, default=180)
    ap.add_argument("--vignette", type=int, default=180)
    ap.add_argument("--sortie", default="/mnt/c/hmt_bridge/audit")
    a = ap.parse_args()

    os.makedirs(a.sortie, exist_ok=True)
    recs = [json.loads(l) for l in open(a.index)]
    recs = [r for r in recs if os.path.exists(f"{JEU}/{r['nom']}.png")]
    rng = random.Random(5)

    for classe in ["EST", "OUEST", "AUCUN"]:
        lot = [r for r in recs if r["camp"] == classe]
        # on prend un echantillon COUVRANT les distances, pas les 30 plus proches :
        # un audit qui ne regarde que le facile ne peut pas trouver le probleme.
        lot.sort(key=lambda r: r["d"])
        pas = max(1, len(lot) // a.par_classe)
        ech = lot[::pas][:a.par_classe]
        rng.shuffle(ech)

        cols = 6
        lignes = (len(ech) + cols - 1) // cols
        V = a.vignette
        planche = Image.new("RGB", (cols * V, lignes * (V + 16)), (20, 20, 20))
        d = ImageDraw.Draw(planche)
        for k, r in enumerate(ech):
            im = Image.open(f"{JEU}/{r['nom']}.png").convert("RGB")
            w, h = im.size
            g, t = (w - a.crop)//2, (h - a.crop)//2
            im = im.crop((g, t, g + a.crop, t + a.crop)).resize((V, V), Image.LANCZOS)
            x, y = (k % cols) * V, (k // cols) * (V + 16)
            planche.paste(im, (x, y))
            d.text((x + 3, y + V + 2), f"{r['nom']}  {r['d']} m", fill=(230, 230, 230))
        p = f"{a.sortie}/planche_{classe}.png"
        planche.save(p)
        print(f"{classe:6s} : {len(ech)} vignettes, distances "
              f"{min(r['d'] for r in ech)}-{max(r['d'] for r in ech)} m  -> {p}")

if __name__ == "__main__":
    sys.exit(main())
