"""sirocco — CHAMP D'ALARME IMMUNITAIRE (le signal). Brique ISOLEE, rien n'est branche.

Deux structures, deux roles — c'est la separation qui porte tout le systeme :

  ChampSirocco   la grille G*G x 6 canaux = le LYMPHE. Partage, il VIEILLIT et DIFFUSE.
                 Personne ne le "recoit" : on baigne dedans. Sert au RECRUTEMENT (etage 3)
                 et a la memoire. Lecture par patch local + gradient, jamais en entier.

  AlarmeLocale   par agent : intensite + direction ACCUMULEES par canal. C'est le DAMP
                 individuel, ce que lit le REFLEXE (etage 1). Decroit vite. C'est LUI qui
                 porte les nombres de la brique B1.

REGLE DURE : on ne depose QUE ce qu'un agent a detecte. Aucune lecture de verite terrain.
C'est la difference avec `_champ_danger` (assault_terrain), qui est un ORACLE : il lit les
positions reelles, la LOS reelle, l'arc reel. Ici personne ne sait tout.

Convention monde<->grille IDENTIQUE a terrain_gpu (_w2g) : px,py dans [-R,R].
Toutes les durees sont en SECONDES et converties par `sec_par_pas` — jamais devinees.

smoke : python sirocco.py smoke
"""
import math
import sys
import torch
import torch.nn.functional as F

try:                                        # on partage la convention de grille si elle est la
    import terrain_gpu as TG
    _HAS_TG = True
except Exception:                           # sinon fallback IDENTIQUE (le smoke verifie l'egalite)
    TG = None
    _HAS_TG = False


def _w2g(px, py, R, G):
    """Monde -> coordonnees grille. Copie EXACTE de terrain_gpu._w2g (verifiee au smoke)."""
    return (((px + R) / (2 * R) * (G - 1)).clamp(0, G - 1),
            ((py + R) / (2 * R) * (G - 1)).clamp(0, G - 1))


# ---- les six canaux ---------------------------------------------------------------------
# Chaque canal a sa DEMI-VIE et sa DIFFUSION. La regle : le signal qui vient de loin est
# vague et dure (BRUIT), le signal local est precis et s'eteint vite (IMPACT). C'est ce
# contraste qui donne au champ sa structure : un coeur net qui pulse, un halo flou qui traine.
CONTACT, IMPACT, FROLEMENT, BRUIT, PERTE, SOI = 0, 1, 2, 3, 4, 5
NOMS = ["CONTACT", "IMPACT", "FROLEMENT", "BRUIT", "PERTE", "SOI"]

#                    demi-vie (s)   diffusion (part/pas)
DEFAUTS = {
    CONTACT:   (6.0,  0.20),   # j'ai vu un ennemi
    IMPACT:    (2.0,  0.05),   # je prends des degats
    FROLEMENT: (2.0,  0.05),   # une balle passe pres -> ON ME VISE
    BRUIT:     (4.0,  0.40),   # un tir entendu : direction vague, porte loin
    PERTE:     (8.0,  0.15),   # un camarade tombe : ici on meurt
    SOI:       (1.0,  0.05),   # mes camarades vivants : canal NEGATIF (IFF + anti-blob)
}
C_MAX = 6


class ChampSirocco:
    def __init__(self, N, R, device, G=28, sec_par_pas=None, demivies=None, diffusions=None,
                 canaux=C_MAX, solide=None):
        """N envs, demi-terrain R (monde dans [-R,R]), grille G*G.

        `sec_par_pas` est OBLIGATOIRE : les demi-vies sont physiques (secondes), le sandbox
        compte en pas. Convertir demande la duree reelle d'un pas, qui se MESURE sur Arma.
        Mieux vaut un arret qu'un chiffre invente.
        """
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError(
                "sec_par_pas manquant. Les demi-vies sont en SECONDES ; un pas de sandbox "
                "n'a de duree que si on la mesure (move / vitesse mesuree sur Arma). "
                "Passer sec_par_pas=<mesure> explicitement.")
        self.N = int(N); self.R = float(R); self.G = int(G); self.dev = device
        self.C = int(canaux); self.sec_par_pas = float(sec_par_pas)
        dv = dict(DEFAUTS); dv.update(demivies or {})
        df = {k: v[1] for k, v in DEFAUTS.items()}; df.update(diffusions or {})
        # facteur de decroissance par PAS : la moitie du signal disparait en une demi-vie
        aT = [0.5 ** (self.sec_par_pas / max(dv[c][0] if isinstance(dv[c], tuple) else dv[c], 1e-6))
              for c in range(self.C)]
        self.aT = torch.tensor(aT, device=device).view(1, self.C, 1, 1)
        self.dif = torch.tensor([float(df[c]) for c in range(self.C)], device=device).view(1, self.C, 1, 1)
        self.champ = torch.zeros(self.N, self.C, G, G, device=device)
        lin = (torch.arange(G, device=device).float() / (G - 1)) * 2 * self.R - self.R
        py, px = torch.meshgrid(lin, lin, indexing="ij")
        self.cellpx = px.reshape(-1); self.cellpy = py.reshape(-1)
        self.libre = None; self.den = None
        if solide is not None: self.set_solide(solide)

    @torch.no_grad()
    def set_solide(self, solide):
        """DRAINAGE DIRECTIONNEL. `solide` (G,G) ou (N,G,G), 1 = obstacle.

        Sans ca, le champ diffuse en rond et fait remonter une alarme A TRAVERS UN MUR :
        l'agent de l'autre cote s'alarme d'un danger qui ne peut pas l'atteindre. Un signal
        qui traverse les murs ment, et en FIBUA il ment tout le temps.

        La lymphe ne diffuse pas dans toutes les directions non plus : elle est collectee par
        des vaisseaux et convoyee. La topologie fait partie du mecanisme. Ici le signal
        remonte la rue et contourne le batiment."""
        s = solide.float()
        if s.dim() == 2: s = s.unsqueeze(0)
        self.libre = (1.0 - s.clamp(0, 1)).unsqueeze(1)            # (n,1,G,G), n = 1 ou N
        self.den = F.avg_pool2d(self.libre, 3, 1, 1).clamp(min=1e-6)

    # ---- ecriture -----------------------------------------------------------------------
    @torch.no_grad()
    def reset(self, idx=None):
        if idx is None: self.champ.zero_()
        else: self.champ[idx] = 0.0

    @torch.no_grad()
    def deposer(self, canal, px, py, inten=1.0, actif=None):
        """Depose sur le canal aux positions monde (N,M). `inten` scalaire ou (N,M).

        Fusion par MAX (comme carte.py) : deux sources au meme endroit ne s'additionnent pas
        en une alarme deux fois plus grosse — une cellule n'a qu'une concentration.

        DEPOT SATURANT : la source remplit les QUATRE cellules qui l'entourent, a valeur
        pleine. C'est indispensable, pas cosmetique : la lecture est bilineaire, donc un
        depot dans une seule cellule serait relu entre 25 % et 100 % de sa valeur selon
        l'endroit ou l'agent se tient DANS sa cellule. Un seuil qui depend de ca est un
        seuil qui ment. Prix a payer : le signal nait large d'une cellule (2R/(G-1) metres) —
        c'est de toute facon la resolution du champ."""
        N, G = self.N, self.G
        gx, gy = _w2g(px, py, self.R, G)
        x0 = gx.floor().long(); y0 = gy.floor().long()
        x1 = (x0 + 1).clamp(max=G - 1); y1 = (y0 + 1).clamp(max=G - 1)
        cells = torch.cat([y0 * G + x0, y0 * G + x1, y1 * G + x0, y1 * G + x1], dim=1)
        val = torch.as_tensor(inten, device=self.dev, dtype=torch.float32).expand_as(px).clone() \
            if not torch.is_tensor(inten) or inten.dim() == 0 else inten.float()
        if actif is not None: val = val * actif.float()
        obs = torch.zeros(N, G * G, device=self.dev)
        obs.scatter_reduce_(1, cells, val.repeat(1, 4), reduce="amax", include_self=True)
        self.champ[:, canal] = torch.maximum(self.champ[:, canal], obs.view(N, G, G))

    @torch.no_grad()
    def pas(self):
        """Un pas de lymphe : VIEILLIR puis DIFFUSER. Rien d'autre. Le champ ne "decide" pas,
        il s'evapore. C'est ce qui rend l'information honnete : elle perime toute seule."""
        N, C, G = self.N, self.C, self.G
        c = self.champ * self.aT                                     # vieillir
        if self.libre is None:
            blur = F.avg_pool2d(c.reshape(N * C, 1, G, G), 3, 1, 1).reshape(N, C, G, G)
        else:
            c = c * self.libre                                       # rien ne stagne dans un mur
            num = F.avg_pool2d(c.reshape(N * C, 1, G, G), 3, 1, 1).reshape(N, C, G, G)
            blur = (num / self.den) * self.libre                     # moyenne sur le LIBRE seul
        self.champ = (1 - self.dif) * c + self.dif * blur            # diffuser
        return self.champ

    # ---- lecture ------------------------------------------------------------------------
    @torch.no_grad()
    def _sample(self, px, py):
        """Bilineaire multi-canal : positions (N,M) -> (N,M,C). Meme math que TG.sample."""
        N, C, G = self.N, self.C, self.G
        gx, gy = _w2g(px, py, self.R, G)
        x0 = gx.floor().long(); y0 = gy.floor().long()
        x1 = (x0 + 1).clamp(max=G - 1); y1 = (y0 + 1).clamp(max=G - 1)
        wx = (gx - x0.float()).unsqueeze(-1); wy = (gy - y0.float()).unsqueeze(-1)
        f = self.champ.reshape(N, C, G * G)
        M = px.shape[1]

        def gat(yy, xx):
            idx = (yy * G + xx).unsqueeze(1).expand(N, C, M)
            return f.gather(2, idx).permute(0, 2, 1)                 # (N,M,C)

        return (gat(y0, x0) * (1 - wx) * (1 - wy) + gat(y0, x1) * wx * (1 - wy)
                + gat(y1, x0) * (1 - wx) * wy + gat(y1, x1) * wx * wy)

    @torch.no_grad()
    def niveau(self, px, py):
        """Concentration de chaque canal sous l'agent. (N,A) -> (N,A,C)."""
        return self._sample(px, py)

    @torch.no_grad()
    def gradient(self, px, py, eps=None):
        """Direction de MONTEE de chaque canal (chimiotactisme). (N,A) -> (N,A,C,2), normalise.
        C'est ce que remonte un effecteur recrute : il ne recoit pas d'adresse, il suit une pente."""
        eps = eps if eps is not None else (2.0 * self.R / (self.G - 1)) * 0.75
        dxp = self._sample(px + eps, py); dxm = self._sample(px - eps, py)
        dyp = self._sample(px, py + eps); dym = self._sample(px, py - eps)
        gx = (dxp - dxm) / (2 * eps); gy = (dyp - dym) / (2 * eps)   # (N,A,C)
        g = torch.stack([gx, gy], dim=-1)                            # (N,A,C,2)
        n = g.norm(dim=-1, keepdim=True).clamp(min=1e-9)
        return g / n * (n > 1e-7).float()                            # nul si le champ est plat

    @torch.no_grad()
    def patch(self, px, py, K=5, span=None):
        """Fenetre K*K du champ autour de l'agent : le CONTEXTE, pas la valeur au point.
        (N,A) -> (N,A,C*K*K). C'est la lecture de la sentinelle : local, jamais global."""
        N, A = px.shape; C = self.C
        span = span if span is not None else (2.0 * self.R / (self.G - 1)) * (K - 1)
        off = (torch.arange(K, device=self.dev).float() / max(K - 1, 1) - 0.5) * span
        qx = (px[..., None, None] + off[None, None, :, None]).expand(N, A, K, K).reshape(N, A * K * K)
        qy = (py[..., None, None] + off[None, None, None, :]).expand(N, A, K, K).reshape(N, A * K * K)
        s = self._sample(qx, qy).reshape(N, A, K * K, C)
        return s.permute(0, 1, 3, 2).reshape(N, A, C * K * K)

    @torch.no_grad()
    def masse(self, canal=None):
        """Signal TOTAL restant sur un canal (somme de la grille). (N,) ou (N,C).

        A ne pas confondre avec `niveau` : la diffusion fait CHUTER la concentration au point
        de depot tout en gardant la masse. Un canal tres diffusif (BRUIT) est donc faible
        partout et present partout — c'est le halo. La demi-vie se lit sur la masse, la
        portee se lit sur le niveau a distance."""
        f = self.champ.reshape(self.N, self.C, -1).sum(-1)
        return f if canal is None else f[:, canal]

    @torch.no_grad()
    def somme_zone(self, cx, cy, rayon, canaux=None):
        """Charge inflammatoire d'une zone : somme ponderee des cellules a moins de `rayon`
        du centre (N,K). -> (N,K). C'est l'entree de l'etage 3 (recrutement)."""
        N = self.N; C = self.C
        canaux = canaux if canaux is not None else [CONTACT, IMPACT, FROLEMENT, PERTE]
        cxx = cx.unsqueeze(-1); cyy = cy.unsqueeze(-1)               # (N,K,1)
        d2 = (self.cellpx.view(1, 1, -1) - cxx) ** 2 + (self.cellpy.view(1, 1, -1) - cyy) ** 2
        m = (d2 <= rayon * rayon).float()                            # (N,K,G*G)
        f = self.champ.reshape(N, C, -1)
        tot = torch.zeros(cx.shape, device=self.dev)
        for c in canaux:
            tot = tot + (f[:, c].unsqueeze(1) * m).sum(-1)
        return tot


class AlarmeLocale:
    """Le DAMP individuel. Ce que la cellule blessee relache : une intensite ET une direction.

    Cette structure est la BRIQUE B1 a elle seule. Elle ne demande ni grille, ni voisinage,
    ni officier — juste des evenements (on me touche / une balle me frole) et une horloge.
    """

    def __init__(self, N, A, device, sec_par_pas=None, demivies=None, canaux=C_MAX):
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError("sec_par_pas manquant (voir ChampSirocco).")
        self.N = int(N); self.A = int(A); self.C = int(canaux); self.dev = device
        dv = {c: DEFAUTS[c][0] for c in range(self.C)}
        dv.update(demivies or {})
        # l'alarme individuelle decroit PLUS VITE que le champ : le corps oublie sa douleur
        # avant que le tissu oublie l'agression. Facteur 0.6 sur la demi-vie.
        aT = [0.5 ** (sec_par_pas / max(0.6 * dv[c], 1e-6)) for c in range(self.C)]
        self.aT = torch.tensor(aT, device=device).view(1, 1, self.C)
        self.inten = torch.zeros(N, A, self.C, device=device)
        self.dirx = torch.zeros(N, A, self.C, device=device)
        self.diry = torch.zeros(N, A, self.C, device=device)

    @torch.no_grad()
    def reset(self, idx=None):
        for t in (self.inten, self.dirx, self.diry):
            if idx is None: t.zero_()
            else: t[idx] = 0.0

    @torch.no_grad()
    def signaler(self, canal, px, py, srcx, srcy, inten, actif=None):
        """Un evenement percu par l'agent. (px,py)=moi, (srcx,srcy)=d'ou ca vient, tous (N,A).
        La direction est accumulee PONDEREE par l'intensite : deux tirs opposes se neutralisent,
        exactement comme un corps qui ne sait plus d'ou vient le coup. Ce n'est pas un bug."""
        v = torch.as_tensor(inten, device=self.dev, dtype=torch.float32).expand(self.N, self.A).clone() \
            if not torch.is_tensor(inten) or inten.dim() == 0 else inten.float()
        if actif is not None: v = v * actif.float()
        dx = srcx - px; dy = srcy - py
        n = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-6)
        self.inten[:, :, canal] = (self.inten[:, :, canal] + v).clamp(max=1.0)
        self.dirx[:, :, canal] = self.dirx[:, :, canal] + (dx / n) * v
        self.diry[:, :, canal] = self.diry[:, :, canal] + (dy / n) * v

    @torch.no_grad()
    def pas(self):
        self.inten *= self.aT; self.dirx *= self.aT; self.diry *= self.aT
        return self.inten

    @torch.no_grad()
    def menace(self):
        """Direction agregee de la menace + son intensite. (N,A,3) : dirx, diry, force.
        Le corps ne distingue pas finement la source d'un frolement de celle d'un impact —
        il sait "ca vient de la". Les canaux IMPACT/FROLEMENT/BRUIT sont fusionnes."""
        cs = [IMPACT, FROLEMENT, BRUIT]
        dx = sum(self.dirx[:, :, c] for c in cs); dy = sum(self.diry[:, :, c] for c in cs)
        n = torch.sqrt(dx * dx + dy * dy)
        ux = torch.where(n > 1e-6, dx / n.clamp(min=1e-6), torch.zeros_like(dx))
        uy = torch.where(n > 1e-6, dy / n.clamp(min=1e-6), torch.zeros_like(dy))
        force = torch.stack([self.inten[:, :, c] for c in cs], -1).max(-1).values
        return torch.stack([ux, uy, force], dim=-1)

    @torch.no_grad()
    def lire_b1(self):
        """LES QUATRE NOMBRES DE LA BRIQUE B1. (N,A,4) :
             0,1  direction unitaire d'ou vient la menace
             2    intensite IMPACT     (on me touche)
             3    intensite FROLEMENT  (on me vise, et je n'ai encore rien paye)
        Reference : deux nombres d'arc de tir ont deja donne -28% d'exposition."""
        m = self.menace()
        return torch.stack([m[..., 0], m[..., 1],
                            self.inten[:, :, IMPACT], self.inten[:, :, FROLEMENT]], dim=-1)

    @torch.no_grad()
    def lire_complet(self):
        """(N,A,C*3) : intensite + direction de CHAQUE canal. Pour les ablations."""
        return torch.cat([self.inten, self.dirx, self.diry], dim=-1)

    @torch.no_grad()
    def danger(self):
        """Le scalaire que lit la cascade : le plus fort des signaux de dommage. (N,A)."""
        return torch.maximum(self.inten[:, :, IMPACT], self.inten[:, :, FROLEMENT])


# ---- smoke ------------------------------------------------------------------------------
def device_defaut():
    """Premier GPU que ce PyTorch sait REELLEMENT piloter, sinon le CPU.

    La workstation a deux cartes : la 3090 (sm_86, supportee) sert au RL, la 1060 (sm_61)
    sert a Arma. Prendre `cuda:0` en aveugle tombe parfois sur la 1060, que ce build de
    PyTorch ne supporte pas — ca marche en apparence et ca ment plus tard."""
    if not torch.cuda.is_available(): return "cpu"
    try:
        archs = torch.cuda.get_arch_list()
        mini = min(int(a[3:]) for a in archs if a.startswith("sm_"))
    except Exception:
        mini = 0
    for i in range(torch.cuda.device_count()):
        maj, mnr = torch.cuda.get_device_capability(i)
        if maj * 10 + mnr >= mini: return "cuda:%d" % i
    return "cpu"


def _smoke():
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco : smoke isole (device %s) ===" % dev, flush=True)

    # 0. la convention de grille est bien celle de terrain_gpu
    if _HAS_TG:
        a = torch.tensor([[-200.0, 0.0, 200.0]], device=dev)
        g1 = _w2g(a, a, 200.0, 28); g2 = TG._w2g(a, a, 200.0, 28)
        dire("convention _w2g identique a terrain_gpu",
             torch.allclose(g1[0], g2[0]) and torch.allclose(g1[1], g2[1]))
    else:
        print("  (terrain_gpu absent : fallback local, egalite non verifiee)")

    SPP = 0.7   # VALEUR DE TEST, PAS UNE MESURE. La vraie vient d'Arma (move / vitesse).
    ch = ChampSirocco(N=4, R=200.0, device=dev, G=28, sec_par_pas=SPP)

    # 1. sec_par_pas obligatoire
    try:
        ChampSirocco(N=1, R=200.0, device=dev); dire("sec_par_pas obligatoire", False)
    except ValueError:
        dire("sec_par_pas obligatoire (refus explicite)", True)

    # 2. demi-vie : apres une demi-vie, il reste la moitie
    p = torch.zeros(4, 1, device=dev)
    ch.deposer(IMPACT, p, p, 1.0)
    v0 = ch.niveau(p, p)[0, 0, IMPACT].item()
    npas = int(round(DEFAUTS[IMPACT][0] / SPP))
    for _ in range(npas): ch.pas()
    v1 = ch.niveau(p, p)[0, 0, IMPACT].item()
    dire("demi-vie IMPACT respectee (~50%% en %.1f s)" % DEFAUTS[IMPACT][0],
         0.30 < v1 / max(v0, 1e-9) < 0.62, "reste %.0f%%" % (100 * v1 / max(v0, 1e-9)))

    # 2-bis. CE QU'ON DEPOSE EST CE QU'ON RELIT, ou qu'on se tienne dans la cellule.
    #        Le test qui manquait : avec un depot mono-cellule, on relisait entre 25 % et
    #        100 % selon la position sub-cellulaire — un seuil qui bouge avec le pied.
    pas_cell = 2 * 200.0 / 27
    pire = 1.0
    for f in (0.0, 0.25, 0.5, 0.75):
        c = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
        pos = torch.full((1, 1), f * pas_cell, device=dev)
        c.deposer(CONTACT, pos, pos, 1.0)
        pire = min(pire, float(c.niveau(pos, pos)[0, 0, CONTACT]))
    dire("depot == relecture (4 offsets sub-cellulaires)", pire > 0.99,
         "pire relecture %.2f" % pire)

    # 3. BRUIT dure plus longtemps que IMPACT -> se lit sur la MASSE, pas sur le niveau au
    #    point : la diffusion vide le centre sans effacer le signal (cf. ChampSirocco.masse).
    ch2 = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    q = torch.zeros(1, 1, device=dev)
    ch2.deposer(IMPACT, q, q, 1.0); ch2.deposer(BRUIT, q, q, 1.0)
    for _ in range(6): ch2.pas()
    mb = float(ch2.masse(BRUIT)[0]); mi = float(ch2.masse(IMPACT)[0])
    dire("BRUIT survit a IMPACT (masse)", mb > mi, "bruit %.3f > impact %.3f" % (mb, mi))
    nb = float(ch2.niveau(q, q)[0, 0, BRUIT]); ni = float(ch2.niveau(q, q)[0, 0, IMPACT])
    dire("...mais il est plus FAIBLE au centre (halo)", nb < ni,
         "au point : bruit %.3f < impact %.3f" % (nb, ni))

    # 4. la diffusion elargit la tache
    ch3 = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    ch3.deposer(BRUIT, q, q, 1.0)
    loin = torch.full((1, 1), 30.0, device=dev)
    avant = ch3.niveau(loin, loin)[0, 0, BRUIT].item()
    for _ in range(8): ch3.pas()
    apres = ch3.niveau(loin, loin)[0, 0, BRUIT].item()
    dire("la tache s'elargit (signal a 30 m)", apres > avant + 1e-6,
         "%.4f -> %.4f" % (avant, apres))

    # 4-bis. DRAINAGE DIRECTIONNEL : un signal ne traverse pas un mur.
    def _propage(solide, pas_n=14):
        c = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP, solide=solide)
        s = torch.zeros(1, 1, device=dev)
        for _ in range(pas_n):
            c.deposer(BRUIT, s, s, 1.0)      # source entretenue en (0,0) = colonne 13-14
            c.pas()
        cible = torch.full((1, 1), 400.0 * 19 / 27 - 200.0, device=dev)   # colonne 19
        return float(c.niveau(cible, torch.zeros(1, 1, device=dev))[0, 0, BRUIT])

    mur = torch.zeros(28, 28, device=dev); mur[:, 16] = 1.0            # cloison pleine
    porte = mur.clone(); porte[13, 16] = 0.0                            # une ouverture
    libre_v = _propage(None); mur_v = _propage(mur); porte_v = _propage(porte)
    dire("sans obstacle : le signal passe", libre_v > 1e-4, "%.4f" % libre_v)
    dire("mur plein : le signal NE passe PAS", mur_v < 1e-6, "%.6f" % mur_v)
    dire("porte : il passe, attenue", 1e-6 < porte_v < libre_v,
         "%.4f contre %.4f a l'air libre" % (porte_v, libre_v))

    # 5. le gradient pointe VERS la source
    ch4 = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    src = torch.tensor([[60.0]], device=dev); zero = torch.zeros(1, 1, device=dev)
    ch4.deposer(CONTACT, src, zero, 1.0)
    for _ in range(3): ch4.pas()
    g = ch4.gradient(zero, zero)[0, 0, CONTACT]
    dire("le gradient pointe vers la source", g[0].item() > 0.8 and abs(g[1].item()) < 0.4,
         "(%.2f, %.2f)" % (g[0].item(), g[1].item()))

    # 6. formes de lecture
    px = torch.zeros(4, 3, device=dev); py = torch.zeros(4, 3, device=dev)
    dire("patch 5x5 : forme (N,A,C*25)", tuple(ch.patch(px, py, K=5).shape) == (4, 3, 6 * 25))
    dire("niveau : forme (N,A,C)", tuple(ch.niveau(px, py).shape) == (4, 3, 6))
    dire("somme_zone : forme (N,K)", tuple(ch.somme_zone(px, py, 40.0).shape) == (4, 3))

    # 7. alarme locale : direction correcte
    al = AlarmeLocale(N=2, A=3, device=dev, sec_par_pas=SPP)
    moi = torch.zeros(2, 3, device=dev)
    tireur_x = torch.full((2, 3), -50.0, device=dev)     # le tireur est a l'OUEST
    al.signaler(FROLEMENT, moi, moi, tireur_x, moi, 0.8)
    b1 = al.lire_b1()
    dire("B1 : forme (N,A,4)", tuple(b1.shape) == (2, 3, 4))
    dire("B1 : direction = vers le tireur (ouest)", b1[0, 0, 0].item() < -0.9,
         "dirx %.2f" % b1[0, 0, 0].item())
    dire("B1 : FROLEMENT actif AVANT tout degat",
         b1[0, 0, 3].item() > 0.5 and b1[0, 0, 2].item() < 1e-6,
         "frolement %.2f / impact %.2f" % (b1[0, 0, 3].item(), b1[0, 0, 2].item()))

    # 8. deux tirs opposes se neutralisent (le corps ne sait plus d'ou vient le coup)
    al2 = AlarmeLocale(N=1, A=1, device=dev, sec_par_pas=SPP)
    o = torch.zeros(1, 1, device=dev)
    al2.signaler(FROLEMENT, o, o, torch.full((1, 1), -50.0, device=dev), o, 0.5)
    al2.signaler(FROLEMENT, o, o, torch.full((1, 1), 50.0, device=dev), o, 0.5)
    m = al2.menace()
    dire("tirs opposes : direction nulle, force gardee",
         abs(m[0, 0, 0].item()) < 0.1 and m[0, 0, 2].item() > 0.9,
         "dir %.2f force %.2f" % (m[0, 0, 0].item(), m[0, 0, 2].item()))

    # 9. l'alarme s'eteint plus vite que le champ : le corps oublie sa douleur avant que le
    #    tissu oublie l'agression. Se lit sur les TAUX (et sur la masse), jamais sur le niveau
    #    au point — le champ diffuse, l'alarme non : les deux ne sont pas comparables au point.
    al3 = AlarmeLocale(N=1, A=1, device=dev, sec_par_pas=SPP)
    ch5 = ChampSirocco(N=1, R=200.0, device=dev, G=28, sec_par_pas=SPP)
    dire("taux : l'alarme decroit plus vite que le champ",
         float(al3.aT[0, 0, IMPACT]) < float(ch5.aT[0, IMPACT, 0, 0]),
         "%.3f < %.3f par pas" % (float(al3.aT[0, 0, IMPACT]), float(ch5.aT[0, IMPACT, 0, 0])))
    al3.signaler(IMPACT, o, o, torch.full((1, 1), 10.0, device=dev), o, 1.0)
    ch5.deposer(IMPACT, o, o, 1.0)
    m0 = float(ch5.masse(IMPACT)[0])
    for _ in range(4): al3.pas(); ch5.pas()
    ra = float(al3.inten[0, 0, IMPACT]); rc = float(ch5.masse(IMPACT)[0]) / max(m0, 1e-9)
    dire("l'alarme oublie avant le tissu", ra < rc,
         "reste alarme %.0f%% < champ %.0f%%" % (100 * ra, 100 * rc))
    print("=== sirocco : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
