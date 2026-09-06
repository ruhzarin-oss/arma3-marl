#!/usr/bin/env python3
"""oeil_sonde — LES TRAITS DE DINOv2 SEPARENT-ILS QUELQUE CHOSE ?

Deux questions, dans cet ordre, et la seconde est plus dure que la premiere :
  Q1  PRESENT contre ABSENT   — y a-t-il un homme dans l'image ?
  Q2  EST contre OUEST        — de quel camp ? (uniquement sur les images ou il y en a un)

METHODE. On GELE l'encodeur : aucun gradient ne le touche. On lui demande ses 384 traits,
et on entraine dessus une simple regression logistique. Si une droite suffit a separer,
c'est que l'information EST DEJA dans les traits — donc le pre-entrainement sur images
reelles porte, et l'agent n'aura pas a l'apprendre en heures d'Arma.

⚠️ DEUX CONTROLES, sans lesquels un score ne vaut rien :
  · ETIQUETTES MELANGEES — la meme sonde sur des etiquettes battues doit tomber au hasard.
    Si elle ne tombe pas, elle apprend le bruit et tous les autres chiffres sont faux.
  · LE CAMP SUR LES IMAGES VIDES — un classifieur de camp evalue sur des images SANS
    personne doit etre au hasard. S'il ne l'est pas, il lit le decor, pas l'uniforme.
  · Et la lecture PAR DISTANCE : un score de camp qui tient a 400 m, ou l'uniforme fait
    13 pixels, est un score qui triche.

Ce que la sonde NE fait PAS : la permutation des uniformes entre camps. Elle exige de
regenerer un jeu, et c'est le controle suivant — celui qui tuera definitivement l'hypothese
« il a appris la geographie des spawns ».
"""
import os, sys, json, time, argparse
import numpy as np
import torch
from PIL import Image

JEU = "/mnt/c/hmt_bridge/jeu"

def preparer(im, MOY, ECT, crop=0):
    """⚠️ AUCUN REDIMENSIONNEMENT. La premiere version ramenait le cote court a 256 puis
    recadrait 224 au centre : sur une vignette de 448 px elle divisait ENCORE la resolution
    par 1,75 et pouvait recadrer le soldat HORS de l'image, puisqu'il est decale
    lateralement de +/-8 m. Je detruisais la chose que je cherchais avant de la regarder.
    DINOv2 est en patchs de 14 : 448 = 32x32 patchs, il l'avale tel quel."""
    if crop > 0:
        w, h = im.size
        g, t2 = (w - crop)//2, (h - crop)//2
        im = im.crop((g, t2, g+crop, t2+crop))
    x = torch.from_numpy(np.asarray(im, dtype=np.float32)/255.0).permute(2,0,1)
    return (x - MOY) / ECT

def _ajuster(X, y, itr, lam, epoques=1500, lr=0.02):
    d = X.shape[1]; k = int(y.max().item()) + 1
    W = torch.zeros(d, k, device=X.device, requires_grad=True)
    b = torch.zeros(k, device=X.device, requires_grad=True)
    opt = torch.optim.Adam([W, b], lr=lr)
    Xtr, ytr = X[itr], y[itr]
    for _ in range(epoques):
        opt.zero_grad()
        p = torch.nn.functional.cross_entropy(Xtr @ W + b, ytr) + lam * (W * W).sum()
        p.backward(); opt.step()
    return W.detach(), b.detach()

def sonde(X, y, idx_tr, idx_te, idx_sel=None):
    """Regression logistique sur traits GELES, avec REGULARISATION CHOISIE.

    ⚠️ REPARATION DU 31/08. Sans regularisation, 768 traits pour 240 exemples memorisent
    TOUT : entrainement 100 %, test 50 %, et le controle a etiquettes melangees atteignait
    lui aussi 100 % a l'entrainement. La sonde n'apprenait pas, elle apprenait par coeur.
    On balaie donc la force de la penalite, et on la CHOISIT sur un jeu de SELECTION
    disjoint du test — sinon la porte jugerait sur ce qui a servi a choisir.
    """
    LAMS = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    if idx_sel is None or len(idx_sel) == 0:
        idx_sel = idx_te
    best, bl = None, -1
    for lam in LAMS:
        W, b = _ajuster(X, y, idx_tr, lam)
        a = ((X[idx_sel] @ W + b).argmax(1) == y[idx_sel]).float().mean().item()
        if a > bl: bl, best, blam = a, (W, b), lam
    W, b = best
    acc_tr = ((X[idx_tr] @ W + b).argmax(1) == y[idx_tr]).float().mean().item()
    pred = (X[idx_te] @ W + b).argmax(1)
    return (pred == y[idx_te]).float().mean().item(), pred, acc_tr, blam

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="/home/younes/arma3-marl/oeil_jeu.jsonl")
    ap.add_argument("--modele", default="facebook/dinov2-small")
    ap.add_argument("--crop", type=int, default=0)      # 0 = image entiere
    a = ap.parse_args()

    recs = [json.loads(l) for l in open(a.index)]
    recs = [r for r in recs if os.path.exists(f"{JEU}/{r['nom']}.png")]
    print(f"{len(recs)} images")

    from transformers import AutoModel
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    mod = AutoModel.from_pretrained(a.modele).to(dev).eval()
    MOY = torch.tensor([0.485,0.456,0.406]).view(3,1,1)
    ECT = torch.tensor([0.229,0.224,0.225]).view(3,1,1)

    t0 = time.time(); F = []
    with torch.no_grad():
        for i in range(0, len(recs), 32):
            lot = recs[i:i+32]
            xs = torch.stack([preparer(Image.open(f"{JEU}/{r['nom']}.png").convert("RGB"), MOY, ECT, a.crop) for r in lot]).to(dev)
            h = mod(pixel_values=xs).last_hidden_state
            # ⚠️ LE JETON CLS SEUL EST LE MAUVAIS LECTEUR. C'est un resume GLOBAL de
            # l'image ; un homme de 17 px dans une vignette de 448 px occupe un millieme
            # de la surface, il est noye. On lit aussi la GRILLE DE PATCHS, en gardant le
            # maximum sur chaque trait : un seul patch qui contient un soldat suffit alors
            # a faire monter le trait. C'est la difference entre « de quoi a l'air cette
            # image » et « y a-t-il quelque part la-dedans un homme ».
            F.append(torch.cat([h[:, 0], h[:, 1:].max(1).values], dim=1))
    X = torch.cat(F); X = (X - X.mean(0)) / (X.std(0) + 1e-6)
    print(f"traits : {tuple(X.shape)}  recadrage={a.crop or 'aucun'}  encodes en {time.time()-t0:.0f} s\n")

    D  = np.array([r["d"] for r in recs])
    pres = torch.tensor([r["present"] for r in recs], device=dev)
    camp = torch.tensor([1 if r["camp"] == "EST" else 0 for r in recs], device=dev)

    # ⚠️ DECOUPAGE ALEATOIRE, ET C'EST UNE REPARATION. La premiere version prenait une
    # image sur trois par `i % 3 == 0` — or la CLASSE est elle aussi assignee par `i % 3`
    # dans le generateur (EST, OUEST, AUCUN en rotation). Le test ne contenait donc QUE des
    # ennemis et l'entrainement QUE des amis : confondu par construction, et le « hasard »
    # calcule valait 100 %. Un decoupage doit etre INDEPENDANT de l'etiquette.
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(recs))
    n1 = len(recs) // 4; n2 = len(recs) // 4
    te  = np.sort(perm[:n1]); sel = np.sort(perm[n1:n1+n2]); tr = np.sort(perm[n1+n2:])
    ITE = torch.tensor(te, device=dev); ITR = torch.tensor(tr, device=dev)
    ISE = torch.tensor(sel, device=dev)
    print(f"decoupage : {len(tr)} apprendre / {len(sel)} choisir / {len(te)} juger "
          f"— trois jeux DISJOINTS, la regle du depot")
    print(f"  test : presents={int(sum(recs[i]['present'] for i in te))}/{len(te)}")

    print("=" * 66)
    acc, pred, atr, lam = sonde(X, pres, ITR, ITE, ISE)
    base = max(pres[ITE].float().mean().item(), 1 - pres[ITE].float().mean().item())
    print(f"Q1  PRESENT contre ABSENT : {acc*100:5.1f} %   (hasard {base*100:.1f} %)   entrainement {atr*100:5.1f} %  lambda {lam:g}")
    for lo, hi in [(0,60),(60,140),(140,260),(260,999)]:
        m = (D[te] >= lo) & (D[te] < hi)
        if m.sum() > 4:
            print(f"      {lo:3d}-{hi:3d} m : {(pred[torch.tensor(m,device=dev)] == pres[ITE][torch.tensor(m,device=dev)]).float().mean().item()*100:5.1f} %  (n={int(m.sum())})")

    # controle : etiquettes melangees
    g = torch.Generator(device='cpu').manual_seed(0)
    melange = pres[torch.randperm(len(recs), generator=g).to(dev)]
    accm, _, atrm, _lm = sonde(X, melange, ITR, ITE, ISE)
    print(f"      CONTROLE etiquettes melangees : {accm*100:5.1f} %  (entrainement {atrm*100:.1f} %)")

    print("=" * 66)
    ip = np.where([r["present"] == 1 for r in recs])[0]
    tep = np.array([i for i in ip if i in set(te.tolist())])
    trp = np.array([i for i in ip if i in set(tr.tolist())])
    sep = np.array([i for i in ip if i in set(sel.tolist())])
    ITEP = torch.tensor(tep, device=dev); ITRP = torch.tensor(trp, device=dev)
    ISEP = torch.tensor(sep, device=dev)
    acc2, pred2, atr2, lam2 = sonde(X, camp, ITRP, ITEP, ISEP)
    print(f"Q2  EST contre OUEST      : {acc2*100:5.1f} %   (hasard 50,0 %, n={len(tep)}, "
          f"dont EST {int(camp[ITEP].float().sum())})   entrainement {atr2*100:5.1f} %  lambda {lam2:g}")
    for lo, hi in [(0,60),(60,140),(140,260),(260,999)]:
        m = (D[tep] >= lo) & (D[tep] < hi)
        if m.sum() > 4:
            mm = torch.tensor(m, device=dev)
            print(f"      {lo:3d}-{hi:3d} m : {(pred2[mm] == camp[ITEP][mm]).float().mean().item()*100:5.1f} %  (n={int(m.sum())})")
    melange2 = camp[torch.randperm(len(recs), generator=g).to(dev)]
    accm2, _, atrm2, _lm2 = sonde(X, melange2, ITRP, ITEP, ISEP)
    print(f"      CONTROLE etiquettes melangees : {accm2*100:5.1f} %  (entrainement {atrm2*100:.1f} %)")
    print("=" * 66)

if __name__ == "__main__":
    sys.exit(main())
