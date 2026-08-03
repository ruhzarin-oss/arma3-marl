"""sirocco_memoire — LA MEMOIRE IMMUNITAIRE. Brique ISOLEE, rien n'est branche.

L'anticipation immunitaire n'est PAS une prediction. C'est un SEUIL ABAISSE.

Le corps ne devine pas la deuxieme agression : il est devenu chatouilleux la ou la premiere
a eu lieu. Meme antigene, deuxieme fois : la reponse part pour beaucoup moins de signal.
C'est la seule facon d'obtenir une reaction AVANT le premier impact — puisque le frolement,
lui, arrive avant l'impact mais est plus faible que lui.

Deux memoires, deux horloges :

  SENSIBILISATION  duree = le run. Une cellule ou l'alarme a franchi le seuil garde une
                   marque qui decroit lentement. Y revenir declenche pour moins.
  PRIMING          duree = la carte. Certains lieux mordent toujours : la fenetre en
                   enfilade, l'angle de rue, la crete. On y entre deja sensibilise.
                   Ce n'est pas de la voyance : c'est un a priori sur la geometrie.

GARDE-FOU : le seuil ne descend jamais sous `plancher` fois sa valeur nominale. Sans ce
plancher, la memoire fabrique la pathologie inverse de l'anergie — un agent qui sursaute a
tout, partout, tout le temps.

smoke : python sirocco_memoire.py smoke
"""
import os
import sys
import numpy as np
import torch
import torch.nn.functional as F

from sirocco import _w2g


class MemoireImmunitaire:
    def __init__(self, N, R, device, G=28, sec_par_pas=None,
                 demivie_sensib=45.0,   # s : la marque du run s'efface en ~une minute
                 k_sensib=1.5,          # force de l'abaissement de seuil
                 k_priming=1.0,         # force du souvenir de carte
                 plancher=0.35,         # le seuil ne descend jamais plus bas que ca
                 halo=0.85):            # part du danger que reprend la cellule voisine
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError("sec_par_pas manquant (voir sirocco.ChampSirocco).")
        self.N, self.R, self.G, self.dev = int(N), float(R), int(G), device
        self.aT = 0.5 ** (float(sec_par_pas) / max(demivie_sensib, 1e-6))
        self.k_s, self.k_p, self.plancher, self.halo = k_sensib, k_priming, plancher, halo
        self.sensib = torch.zeros(self.N, G, G, device=device)     # par env, par run
        self.priming = torch.zeros(G, G, device=device)            # par carte, persistant
        self.n_runs = 0

    @torch.no_grad()
    def reset(self, idx=None):
        """Fin de run : la sensibilisation s'efface. Le priming, LUI, reste."""
        if idx is None: self.sensib.zero_()
        else: self.sensib[idx] = 0.0

    @torch.no_grad()
    def marquer(self, px, py, force=1.0, actif=None):
        """"Ici, ca a mordu." Positions monde (N,M). A appeler quand l'alarme franchit le seuil.

        Depot SATURANT sur les 4 cellules voisines, pour la meme raison que
        ChampSirocco.deposer : la lecture est bilineaire, un depot dans une seule cellule
        serait relu affaibli d'un facteur qui depend de la position sub-cellulaire. Ici la
        consequence serait pire qu'ailleurs — une memoire qui n'abaisse le seuil qu'a moitie
        ne declenche jamais avant l'impact, et l'anticipation ne marche pas sans qu'on voie
        pourquoi."""
        N, G = self.N, self.G
        gx, gy = _w2g(px, py, self.R, G)
        x0 = gx.floor().long(); y0 = gy.floor().long()
        x1 = (x0 + 1).clamp(max=G - 1); y1 = (y0 + 1).clamp(max=G - 1)
        cells = torch.cat([y0 * G + x0, y0 * G + x1, y1 * G + x0, y1 * G + x1], dim=1)
        v = torch.as_tensor(force, device=self.dev, dtype=torch.float32).expand_as(px).clone() \
            if not torch.is_tensor(force) or force.dim() == 0 else force.float()
        if actif is not None: v = v * actif.float()
        obs = torch.zeros(N, G * G, device=self.dev)
        obs.scatter_reduce_(1, cells, v.repeat(1, 4), reduce="amax", include_self=True)
        self.sensib = torch.maximum(self.sensib, obs.view(N, G, G)).clamp(max=1.0)

    @torch.no_grad()
    def pas(self):
        """La marque vieillit, et s'ETEND aux abords du mauvais endroit.

        Etendre, pas diffuser. C'est une DILATATION (max_pool), pas un floutage (avg_pool) —
        et la difference decide si l'anticipation marche. Un souvenir ne se dilue pas : la
        zone dangereuse gagne ses abords sans que son centre s'affadisse. Avec un floutage,
        une marque posee a un endroit valait 0.15 quarante pas plus tard et n'abaissait plus
        le seuil que de 3 % — le mecanisme etait la, l'effet avait disparu.

        `halo` fixe la decroissance du souvenir avec la distance : la cellule voisine reprend
        `halo` fois la valeur, donc a k cellules il reste halo^k. Le halo s'arrete tout seul."""
        s = self.sensib * self.aT
        dilat = F.max_pool2d(s.unsqueeze(1), 3, 1, 1).squeeze(1) * self.halo
        self.sensib = torch.maximum(s, dilat)
        return self.sensib

    @torch.no_grad()
    def _lire(self, champ, px, py):
        """Bilineaire simple sur une grille (N,G,G) ou (G,G). (N,A) -> (N,A)."""
        N, A = px.shape; G = self.G
        f = champ if champ.dim() == 3 else champ.unsqueeze(0).expand(N, G, G)
        gx, gy = _w2g(px, py, self.R, G)
        x0 = gx.floor().long(); y0 = gy.floor().long()
        x1 = (x0 + 1).clamp(max=G - 1); y1 = (y0 + 1).clamp(max=G - 1)
        wx = gx - x0.float(); wy = gy - y0.float(); ff = f.reshape(N, -1)

        def gat(yy, xx): return ff.gather(1, yy * G + xx)

        return (gat(y0, x0) * (1 - wx) * (1 - wy) + gat(y0, x1) * wx * (1 - wy)
                + gat(y1, x0) * (1 - wx) * wy + gat(y1, x1) * wx * wy)

    @torch.no_grad()
    def seuil(self, px, py, s1):
        """LE point du module. Rend le seuil de reflexe LOCAL, abaisse par la memoire. (N,A).

        Nulle part ailleurs on ne touche au seuil : la cascade le recoit tel quel. C'est ce qui
        rend l'anticipation mesurable en isolation — on peut comparer le meme scenario avec et
        sans memoire, sans rien changer d'autre."""
        m = self.k_s * self._lire(self.sensib, px, py) + self.k_p * self._lire(self.priming, px, py)
        facteur = (1.0 / (1.0 + m)).clamp(min=self.plancher)
        return float(s1) * facteur

    @torch.no_grad()
    def cloturer_run(self, poids=1.0, reset=True, normaliser=True):
        """Fin de run : ce que la sensibilisation a appris passe dans le priming (moyenne mobile),
        PUIS la sensibilisation s'efface. Le priming est un a priori de CARTE : il moyenne les
        envs et les runs, il ne garde pas l'accident d'une partie.

        Le reset est fait ICI, et par defaut, pour une raison vecue : appeler reset() avant
        cloturer_run() moyenne une grille deja vide, le priming reste nul, et l'anticipation
        ne marche pas sans qu'aucun test n'echoue. Un ordre d'appel qu'on peut inverser en
        silence est un piege — autant le supprimer.

        `normaliser` remet le pic a 1 avant d'integrer. Sans ca, l'echelle du priming depend
        du NOMBRE d'envs : moyenner 2048 envs qui ont mordu a des endroits differents ecrase
        tout vers zero, et `k_priming` ne voudrait plus rien dire d'un run a l'autre. Ce qui
        compte dans un a priori de carte, c'est la FORME — ou c'est dangereux — pas l'amplitude."""
        moy = self.sensib.mean(0)
        if normaliser:
            pic = float(moy.max())
            if pic > 1e-6: moy = moy / pic
        self.n_runs += 1
        a = poids / self.n_runs
        self.priming = (1 - a) * self.priming + a * moy
        if reset: self.sensib.zero_()
        return self.priming

    def sauver(self, chemin):
        np.savez(chemin, priming=self.priming.cpu().numpy(), n_runs=self.n_runs,
                 R=self.R, G=self.G)
        return chemin

    def charger(self, chemin, strict=True):
        """Recharge un priming de carte. `strict` refuse un fichier d'une AUTRE geometrie —
        un souvenir de la mauvaise carte est pire que pas de souvenir."""
        if not os.path.exists(chemin):
            if strict: raise FileNotFoundError(chemin)
            return False
        d = np.load(chemin)
        if int(d["G"]) != self.G or abs(float(d["R"]) - self.R) > 1e-6:
            raise ValueError("priming d'une autre carte : G=%s R=%s attendu G=%d R=%.1f"
                             % (d["G"], d["R"], self.G, self.R))
        self.priming = torch.tensor(d["priming"], device=self.dev).float()
        self.n_runs = int(d["n_runs"])
        return True


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco_memoire : smoke isole (device %s) ===" % dev, flush=True)
    SPP = 0.7   # VALEUR DE TEST, PAS UNE MESURE.
    S1 = 0.25
    mem = MemoireImmunitaire(N=2, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    ici = torch.zeros(2, 1, device=dev)
    loin = torch.full((2, 1), 150.0, device=dev)

    dire("seuil nominal sans memoire", abs(float(mem.seuil(ici, ici, S1)[0, 0]) - S1) < 1e-6)

    mem.marquer(ici, ici, 1.0)
    s_ici = float(mem.seuil(ici, ici, S1)[0, 0]); s_loin = float(mem.seuil(loin, loin, S1)[0, 0])
    attendu = S1 / (1.0 + mem.k_s)          # marque PLEINE : c'est la valeur exacte a atteindre
    dire("le seuil baisse la ou ca a mordu", abs(s_ici - attendu) < 1e-4,
         "%.3f (exact : %.3f)" % (s_ici, attendu))
    dire("il ne baisse PAS ailleurs", abs(s_loin - S1) < 1e-6, "%.3f" % s_loin)

    # la marque doit valoir PLEIN ou qu'on se tienne dans la cellule (cf. depot saturant)
    pire = 0.0
    for f in (0.0, 0.25, 0.5, 0.75):
        m = MemoireImmunitaire(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
        p = torch.full((1, 1), f * (2 * 200.0 / 27), device=dev)
        m.marquer(p, p, 1.0)
        pire = max(pire, float(m.seuil(p, p, S1)[0, 0]))
    dire("marque pleine a tout offset sub-cellulaire", abs(pire - attendu) < 1e-4,
         "pire seuil %.3f" % pire)

    # plancher : meme sature, le seuil ne s'effondre pas (pathologie inverse de l'anergie)
    m2 = MemoireImmunitaire(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP, k_sensib=50.0)
    o = torch.zeros(1, 1, device=dev)
    for _ in range(20): m2.marquer(o, o, 1.0)
    dire("plancher tenu (pas d'hyperreactivite)",
         float(m2.seuil(o, o, S1)[0, 0]) >= S1 * m2.plancher - 1e-6,
         "%.3f >= %.3f" % (float(m2.seuil(o, o, S1)[0, 0]), S1 * m2.plancher))

    # LE HALO : la zone dangereuse gagne ses abords SANS que son centre s'affadisse.
    # C'est ce qui separe une memoire utile d'une flaque tiede (cf. MemoireImmunitaire.pas).
    mh = MemoireImmunitaire(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP, demivie_sensib=1e9)
    o = torch.zeros(1, 1, device=dev)
    mh.marquer(o, o, 1.0)
    for _ in range(10): mh.pas()
    pas_cell = 2 * 200.0 / 27
    centre = float(mh.sensib[0].max())
    loin3 = float(mh._lire(mh.sensib, torch.full((1, 1), 3 * pas_cell, device=dev), o)[0, 0])
    dire("halo : le centre ne s'affadit pas", centre > 0.99, "centre %.3f" % centre)
    dire("halo : les abords s'allument, en decroissant",
         0.3 < loin3 < 0.95, "a 3 cellules : %.2f (halo^3 = %.2f)" % (loin3, mh.halo ** 3))

    # la marque s'efface avec le temps
    avant = float(mem.seuil(ici, ici, S1)[0, 0])
    for _ in range(int(90 / SPP)): mem.pas()
    apres = float(mem.seuil(ici, ici, S1)[0, 0])
    dire("la marque s'efface (90 s)", apres > avant, "%.3f -> %.3f (nominal %.2f)" % (avant, apres, S1))

    # LE test d'anticipation : deux passages identiques, le second reagit PLUS TOT
    from sirocco import AlarmeLocale, FROLEMENT, IMPACT
    from sirocco_cascade import Cascade, REFLEXE

    def passage(memoire):
        """Un agent approche : d'abord des frolements faibles, puis un impact franc.
        Rend le pas ou le reflexe part (-1 si jamais)."""
        al = AlarmeLocale(N=1, A=1, device=dev, sec_par_pas=SPP)
        cas = Cascade(N=1, A=1, device=dev, sec_par_pas=SPP, s1=S1)
        p = torch.zeros(1, 1, device=dev); src = torch.full((1, 1), -50.0, device=dev)
        for t in range(14):
            al.pas()
            if t < 8: al.signaler(FROLEMENT, p, p, src, p, 0.045)   # on me vise, faiblement
            else: al.signaler(IMPACT, p, p, src, p, 0.5)            # on me touche
            m = al.menace()
            s = memoire.seuil(p, p, S1) if memoire is not None else None
            r = cas.pas(al.danger(), p, p, m[..., :2], seuil=s)
            if int(r["etat"][0, 0]) == REFLEXE:
                if memoire is not None: memoire.marquer(p, p, 1.0)
                return t
        return -1

    m3 = MemoireImmunitaire(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    t1 = passage(m3)                       # premier contact : on marque en partant
    t2 = passage(m3)                       # second contact au meme endroit
    t0 = passage(None)                     # temoin : sans memoire du tout
    dire("1er contact : la reaction suit l'impact", t1 >= 8, "pas %d (impact au pas 8)" % t1)
    dire("2e contact : la reaction PRECEDE l'impact", 0 <= t2 < 8, "pas %d" % t2)
    dire("la memoire est bien la cause (temoin sans memoire)", t0 == t1, "temoin pas %d" % t0)

    # priming : cloture, sauvegarde, rechargement, refus d'une autre carte
    m3.cloturer_run()
    chemin = "/tmp/sirocco_priming_smoke.npz"
    m3.sauver(chemin)
    m4 = MemoireImmunitaire(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    m4.charger(chemin)
    dire("priming recharge non nul", float(m4.priming.max()) > 0.0,
         "max %.3f" % float(m4.priming.max()))
    dire("priming : seuil deja abaisse a l'entree", float(m4.seuil(o, o, S1)[0, 0]) < S1)
    m5 = MemoireImmunitaire(N=1, R=100.0, device=dev, G=28, sec_par_pas=SPP)   # autre carte
    try:
        m5.charger(chemin); dire("refus d'un priming d'une autre carte", False)
    except ValueError:
        dire("refus d'un priming d'une autre carte", True)
    os.remove(chemin)

    print("=== sirocco_memoire : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
