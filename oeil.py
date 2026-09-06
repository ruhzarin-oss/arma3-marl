#!/usr/bin/env python3
"""oeil — l'encodeur visuel, et sa premiere image d'Arma.

⭐ POURQUOI CE MODELE. Younes veut que l'agent arrive en SACHANT ce qu'il voit, pour ne pas
payer cet apprentissage en heures d'Arma (153 episodes/heure, contre des dizaines de milliers
d'images par heure sur dataset). DINOv2 est deja entraine sur 142 MILLIONS d'images REELLES,
sans etiquettes, par apprentissage auto-supervise. C'est le pre-entrainement sur donnees
reelles, deja fait, gratuit.

CE QUE CE SCRIPT MESURE, ET RIEN DE PLUS :
  1. l'encodeur charge-t-il et tourne-t-il sur la 3090 ;
  2. combien de millisecondes coute une image — a comparer aux 149 ms de la capture ;
  3. la dimension de l'embedding, qui se concatenera aux neuf nombres.

Il ne dit RIEN de la question qui compte — « ces traits separent-ils un soldat du decor
sur une image d'Arma ». Ca, c'est la sonde suivante, et elle exige un jeu etiquete
qu'Arma peut fabriquer gratuitement puisqu'il connait la verite terrain.
"""
import sys, time, argparse
import torch
from PIL import Image

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="/mnt/c/hmt_bridge/cap/ecran.png")
    ap.add_argument("--modele", default="facebook/dinov2-small")
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()

    from transformers import AutoModel
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"appareil : {dev}  {torch.cuda.get_device_name(0) if dev!='cpu' else ''}")

    # ⚠️ PAS d'AutoImageProcessor : il exige torchvision, absent du venv du projet. On
    # n'installe pas une dependance lourde dans l'environnement dont depend tout le depot
    # pour economiser dix lignes. Le pre-traitement de DINOv2 est public et tient ici :
    # cote court a 256, recadrage central 224, normalisation ImageNet.
    import numpy as np
    MOY = torch.tensor([0.485, 0.456, 0.406]).view(3,1,1)
    ECT = torch.tensor([0.229, 0.224, 0.225]).view(3,1,1)
    def preparer(im, court=256, crop=224):
        w, h = im.size
        s = court / min(w, h)
        im = im.resize((max(1,round(w*s)), max(1,round(h*s))), Image.BICUBIC)
        w, h = im.size
        g, t = (w - crop) // 2, (h - crop) // 2
        im = im.crop((g, t, g + crop, t + crop))
        x = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0).permute(2,0,1)
        return ((x - MOY) / ECT).unsqueeze(0)

    t0 = time.time()
    mod = AutoModel.from_pretrained(a.modele).to(dev).eval()
    print(f"modele   : {a.modele}  charge en {time.time()-t0:.1f} s  "
          f"({sum(p.numel() for p in mod.parameters())/1e6:.1f} M parametres)")

    img = Image.open(a.image).convert("RGB")
    print(f"image    : {a.image}  {img.size[0]}x{img.size[1]}")

    with torch.no_grad():
        x = preparer(img).to(dev)
        # chauffe : la premiere passe paie l'allocation CUDA, elle ne compte pas
        for _ in range(3):
            _ = mod(pixel_values=x)
        torch.cuda.synchronize() if dev != "cpu" else None
        ts = []
        for _ in range(a.n):
            t = time.time()
            o = mod(pixel_values=x)
            torch.cuda.synchronize() if dev != "cpu" else None
            ts.append((time.time() - t) * 1000)

    cls = o.last_hidden_state[:, 0]          # le jeton de synthese
    patchs = o.last_hidden_state[:, 1:]      # la grille de patchs
    ts.sort()
    print(f"\nembedding : {tuple(cls.shape)}  (jeton CLS)")
    print(f"patchs    : {tuple(patchs.shape)}  = grille de {int(patchs.shape[1]**0.5)}x{int(patchs.shape[1]**0.5)}")
    print(f"temps/img : mediane {ts[len(ts)//2]:.1f} ms   min {ts[0]:.1f}   max {ts[-1]:.1f}")
    print(f"\nA COMPARER : la capture d'ecran coute 149 ms mesurees, le cycle de decision 4000 ms.")
    print(f"norme du CLS : {cls.norm().item():.2f}   traits non constants : "
          f"{int((cls.std(0) if cls.shape[0]>1 else cls.abs()).gt(1e-6).sum())}/{cls.shape[1]}")

if __name__ == "__main__":
    sys.exit(main())
