"""alize_encodeur — LE RESEAU D'ALIZE. Brique ISOLEE, rien n'est branche.

Le reseau n'emet PAS d'actions. Il emet les PARAMETRES d'une cascade ecrite a la main —
seuils, latences, plafond, audace. La cascade fait le reste, de facon deterministe.
Voir ALIZE.md pour le pourquoi ; ici, le comment.

LA GEOMETRIE EST LE SUJET. Ton monde est toujours egocentre et angulaire : tu l'as deja
ecrit trois fois sans le nommer (coque de couvert 12 rayons, champ de risque 8 directions,
arc de tir). Alors le reseau est bati la-dessus :

  entree      des ANNEAUX : (B, C, K, R) — K secteurs angulaires, R rayons, C canaux
  encodeur    convolution CIRCULAIRE sur l'angle : le secteur K-1 touche le secteur 0
  tete inv.   moyenne sur l'angle  -> INVARIANTE  : seuils, latences, plafond, audace
  tete equi.  pas de moyenne       -> EQUIVARIANTE : un score par secteur (ou aller)

CE QUE CA GARANTIT : la meme situation tournee de 90 degres donne la meme decision, tournee
de 90 degres. Exactement, par construction — pas approximativement apres avoir vu assez
d'exemples. Un CNN ordinaire doit APPRENDRE cette symetrie ; il reapprend huit fois la meme
chose et n'y arrive jamais tout a fait.

Et ca se VERIFIE numeriquement : on tourne l'entree, on regarde si la sortie tourne. C'est le
premier test de ce fichier, et il passe ou il ne passe pas.

smoke : python alize_encodeur.py smoke
"""
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

# Plages PHYSIQUES des parametres de cascade. Ce ne sont pas des bornes de commodite :
# c'est ce qui rend un parametre appris TRANSPORTABLE. Un seuil a un sens (une intensite de
# signal), une latence a un sens (des secondes). Un poids de reseau n'en a aucun — c'est
# exactement pourquoi le manager RL a fait 83 % en sandbox et 0 % sur Arma.
PLAGES = {
    "s1":        (0.05, 0.60),    # seuil de reflexe, sur l'alarme locale
    "s3":        (0.50, 6.00),    # seuil de charge inflammatoire de zone
    "lat_local": (0.50, 6.00),    # s : avant que le binome appuie
    "sortie":    (1.00, 8.00),    # s : sous le seuil avant de redescendre
    "plafond":   (0.00, 4.00),    # nb max de recrutes (arrondi a l'usage)
    "audace":    (0.60, 2.00),    # exposition qu'on accepte de payer
}
NOMS = list(PLAGES)


class ConvPolaire(nn.Module):
    """Convolution 2D circulaire sur l'ANGLE, repliquee sur le RAYON.

    Circulaire sur l'angle parce que l'angle est cyclique — un obstacle a 355 degres est
    voisin d'un obstacle a 5 degres, et un padding a zero le nierait. Repliquee sur le rayon
    parce que le rayon ne l'est pas : au-dela du dernier anneau, on prolonge plutot que
    d'inventer un vide."""

    def __init__(self, c_in, c_out, ka=3, kr=3):
        super().__init__()
        self.conv = nn.Conv2d(c_in, c_out, (ka, kr), padding=0)
        self.pa, self.pr = ka // 2, kr // 2

    def forward(self, x):                                   # (B,C,K,R)
        if self.pa: x = F.pad(x, (0, 0, self.pa, self.pa), mode="circular")
        if self.pr: x = F.pad(x, (self.pr, self.pr, 0, 0), mode="replicate")
        return self.conv(x)


class EncodeurPolaire(nn.Module):
    """(B,C,K,R) -> (B,W,K). Une representation PAR SECTEUR, equivariante a la rotation.

    GroupNorm et pas BatchNorm : ses statistiques sont prises sur (canaux, K, R), donc elles
    ne changent pas quand on tourne l'entree. L'equivariance survit. Une normalisation qui
    depend de la position angulaire la detruirait en silence."""

    def __init__(self, c_in, largeur=48, n_couches=3, ka=3, kr=3, groupes=8):
        super().__init__()
        couches = []
        c = c_in
        for i in range(n_couches):
            couches += [ConvPolaire(c, largeur, ka, kr),
                        nn.GroupNorm(min(groupes, largeur), largeur),
                        nn.SiLU()]
            c = largeur
        self.corps = nn.Sequential(*couches)
        self.largeur = largeur

    def forward(self, x):
        h = self.corps(x)                                   # (B,W,K,R)
        return h.mean(-1)                                   # pool sur le RAYON -> (B,W,K)


class TeteInvariante(nn.Module):
    """(B,W,K) -> (B,n). Moyenne sur l'angle : la sortie ne bouge pas quand la scene tourne.
    C'est ce qu'on veut pour un SEUIL — « a quel point suis-je chatouilleux » n'a pas de
    direction."""

    def __init__(self, largeur, n_sorties, cache=64):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(largeur, cache), nn.SiLU(), nn.Linear(cache, n_sorties))

    def forward(self, h):
        return self.f(h.mean(-1))                           # (B,W) -> (B,n)


class TeteEquivariante(nn.Module):
    """(B,W,K) -> (B,K). Pas de moyenne sur l'angle : la sortie TOURNE avec la scene.
    C'est ce qu'on veut pour « ou aller » — un cap a une direction, par definition."""

    def __init__(self, largeur, ka=3):
        super().__init__()
        self.c1 = ConvPolaire(largeur, largeur // 2, ka, 1)
        self.c2 = ConvPolaire(largeur // 2, 1, ka, 1)

    def forward(self, h):
        x = h.unsqueeze(-1)                                 # (B,W,K,1)
        x = F.silu(self.c1(x))
        return self.c2(x).squeeze(-1).squeeze(1)            # (B,K)


class PolitiqueParametres(nn.Module):
    """LE COEUR D'ALIZE : contexte -> distribution sur les parametres de cascade.

    Le reseau sort une moyenne et un ecart-type par parametre. On echantillonne, on joue la
    cascade, on mesure le retour, on remonte le gradient jusqu'au reseau — JAMAIS a travers
    la cascade, qui n'est pas derivable et n'a pas a l'etre. C'est la voie (a) d'ALIZE.md :
    un gradient de politique sur un espace continu de dimension 6.

    A comparer a une politique end-to-end sur 13 actions pendant 60 pas. C'est la meme tache,
    dans un espace des centaines de fois plus petit — et ton goulot mesure etait l'exploration.
    """

    def __init__(self, c_in, K, largeur=48, n_couches=3, noms=None, log_sigma0=-1.0):
        super().__init__()
        self.noms = list(noms) if noms else NOMS
        self.enc = EncodeurPolaire(c_in, largeur, n_couches)
        self.tete = TeteInvariante(largeur, len(self.noms))
        self.cap = TeteEquivariante(largeur)
        self.log_sigma = nn.Parameter(torch.full((len(self.noms),), float(log_sigma0)))
        self.K = int(K)

    def forward(self, x):
        h = self.enc(x)
        return self.tete(h), self.cap(h)                    # (B,n) logits bruts, (B,K)

    @staticmethod
    def _borner(z, noms):
        """logit -> valeur physique, par sigmoide sur la plage. Bornes DURES : le reseau ne
        peut pas demander un plafond de 40 hommes ni un seuil negatif, meme mal entraine."""
        lo = torch.tensor([PLAGES[n][0] for n in noms], device=z.device)
        hi = torch.tensor([PLAGES[n][1] for n in noms], device=z.device)
        return lo + (hi - lo) * torch.sigmoid(z)

    def parametres(self, x):
        """Les parametres MOYENS, sans bruit. C'est ce qu'on deploie une fois entraine."""
        z, cap = self.forward(x)
        v = self._borner(z, self.noms)
        return {n: v[:, i] for i, n in enumerate(self.noms)}, cap

    def echantillonner(self, x):
        """Tire des parametres et rend leur log-vraisemblance (pour le gradient de politique).
        Le bruit est mis sur le LOGIT, pas sur la valeur : ainsi l'echantillon reste toujours
        dans la plage physique, sans rejet ni troncature."""
        z, cap = self.forward(x)
        sigma = self.log_sigma.exp().clamp(1e-3, 3.0)
        # L'ECHANTILLON EST DETACHE, et la log-vraisemblance est evaluee EN CE POINT comme
        # fonction de (z, sigma). Ecrire logp a partir du bruit tire — -0.5*eps**2 — donne
        # une expression qui ne depend plus de z du tout : le gradient sur la moyenne est
        # alors nul et l'entrainement ne bouge pas d'un pouce, sans qu'aucune erreur ne
        # soit levee. C'est la faute silencieuse classique de REINFORCE.
        zt = (z + sigma * torch.randn_like(z)).detach()
        logp = (-0.5 * ((zt - z) / sigma) ** 2 - self.log_sigma - 0.9189385).sum(-1)
        v = self._borner(zt, self.noms)
        return {n: v[:, i] for i, n in enumerate(self.noms)}, logp, cap


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut
    dev = device_defaut()
    torch.manual_seed(0)
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== alize_encodeur : smoke isole (device %s) ===" % dev, flush=True)
    B, C, K, R = 4, 5, 12, 6
    x = torch.randn(B, C, K, R, device=dev)
    net = PolitiqueParametres(C, K).to(dev).eval()

    # 1. LE test : on tourne la scene, la decision tourne avec elle. Exactement.
    pires_inv, pires_equi = 0.0, 0.0
    for k in (1, 3, 6, 11):
        with torch.no_grad():
            z0, cap0 = net(x)
            zk, capk = net(torch.roll(x, k, dims=2))        # rotation de k secteurs
        pires_inv = max(pires_inv, float((zk - z0).abs().max()))
        pires_equi = max(pires_equi, float((capk - torch.roll(cap0, k, dims=1)).abs().max()))
    dire("tete INVARIANTE : seuils inchanges par rotation", pires_inv < 1e-4,
         "ecart max %.2e" % pires_inv)
    dire("tete EQUIVARIANTE : le cap tourne avec la scene", pires_equi < 1e-4,
         "ecart max %.2e" % pires_equi)

    # 2. le contraste : un MLP sur le meme vecteur aplati n'a AUCUNE de ces deux proprietes.
    #    C'est le bras d'ablation A- du protocole, et voila ce qu'il perd.
    mlp = nn.Sequential(nn.Flatten(), nn.Linear(C * K * R, 64), nn.SiLU(),
                        nn.Linear(64, len(NOMS))).to(dev).eval()
    with torch.no_grad():
        e_mlp = float((mlp(torch.roll(x, 3, dims=2)) - mlp(x)).abs().max())
    dire("le MLP temoin, lui, change de reponse", e_mlp > 1e-2, "ecart %.3f" % e_mlp)

    # 3. les parametres sortent BORNES, quoi qu'on lui donne
    with torch.no_grad():
        p, _ = net.parametres(torch.randn(B, C, K, R, device=dev) * 50.0)   # entree absurde
    dedans = all(PLAGES[n][0] - 1e-5 <= float(p[n].min()) and
                 float(p[n].max()) <= PLAGES[n][1] + 1e-5 for n in NOMS)
    dire("bornes physiques tenues (entree absurde x50)", dedans,
         "s1 in [%.2f, %.2f]" % (float(p["s1"].min()), float(p["s1"].max())))

    # 4. l'echantillonnage rend une log-vraisemblance derivable — ET par rapport a la MOYENNE.
    #    Ce second point est le seul qui compte : sans lui, l'entrainement tourne a vide.
    p, logp, cap = net.echantillonner(x)
    g_sig = torch.autograd.grad(logp.sum(), net.log_sigma, retain_graph=True)[0]
    g_moy = torch.autograd.grad(logp.sum(), net.tete.f[-1].weight, retain_graph=True)[0]
    dire("log-vraisemblance derivable / ecart-type", float(g_sig.abs().sum()) > 0)
    dire("log-vraisemblance derivable / MOYENNE", float(g_moy.abs().sum()) > 0,
         "grad %.2e" % float(g_moy.abs().sum()))
    dire("le cap a bien un score par secteur", tuple(cap.shape) == (B, K))

    # 5. LA boucle bout en bout, sur un probleme jouet dont on connait la reponse.
    #    Cible : s1 = 0.30. Le retour ne dit RIEN d'autre que « c'etait mieux ou moins bien »
    #    — exactement comme une mesure de prise-a-pertes. Si le reseau y arrive ici, la
    #    plomberie d'apprentissage est bonne ; le reste est une affaire d'environnement.
    torch.manual_seed(1)
    net2 = PolitiqueParametres(C, K).to(dev)
    opt = torch.optim.Adam(net2.parameters(), 3e-3)     # 3e-2 sature la borne et s'y bloque
    xb = torch.randn(64, C, K, R, device=dev)
    CIBLE = 0.52                      # loin du depart (~0.33) : la convergence doit se VOIR
    with torch.no_grad(): depart = float(net2.parametres(xb)[0]["s1"].mean())
    base = None
    for it in range(400):
        p, logp, _ = net2.echantillonner(xb)
        r = (-(p["s1"] - CIBLE).abs()).detach()            # scalaire opaque, non derivable
        base = r.mean() if base is None else 0.9 * base + 0.1 * r.mean()
        avantage = (r - base) / (r - base).std().clamp(min=1e-6)   # REINFORCE, base mobile
        perte = -(logp * avantage).mean()
        opt.zero_grad(); perte.backward(); opt.step()
    with torch.no_grad(): arrivee = float(net2.parametres(xb)[0]["s1"].mean())
    dire("REINFORCE converge vers le seuil cible (jouet)",
         abs(arrivee - CIBLE) < abs(depart - CIBLE) * 0.25,
         "%.3f -> %.3f (cible %.2f)" % (depart, arrivee, CIBLE))

    # 6. le reseau reste petit : c'est un argument, pas un detail (3090 partagee avec Arma)
    n_par = sum(q.numel() for q in net.parameters())
    dire("reseau compact", n_par < 200_000, "%d parametres" % n_par)

    print("=== alize_encodeur : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
