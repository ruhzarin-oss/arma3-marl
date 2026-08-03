"""sirocco_cascade — LA REACTION EN CHAINE. Brique ISOLEE, rien n'est branche.

Cinq etages. Chacun a QUATRE choses, et jamais trois :
    un seuil d'entree · une latence · une reaction · un TICKET DE SORTIE.
L'oubli du ticket de sortie est la faute classique — c'est l'inflammation chronique :
l'escouade reste plaquee et la mission n'avance plus.

    etage 0  VEILLE       tient son poste, arc oriente
    etage 1  REFLEXE      individuel, immediat  : se plaque, pivote, rompt la LOS
    etage 2  LOCAL        le binome APPUIE vers la source du camarade sous le feu
    etage 3  RECRUTEMENT  chimiotactisme : au plus `plafond` voisins remontent le gradient
    etage 4  ADAPTATIF    l'officier change de plan (sortie de l'automatisme)
    etage 5  RESOLUTION   retour au dispositif, re-armement des seuils

DEUX REGLES DURES, non negociables :
  1. Un etage ne court-circuite JAMAIS celui d'en dessous. Le reflexe part meme si l'officier
     dit autre chose. Un corps qui attend l'ordre du cerveau pour retirer sa main du feu est
     un corps mort. Concretement : un agent recrute qui prend une balle repasse en REFLEXE.
  2. Le recrutement a un PLAFOND. Sans ce nombre on refabrique le blob deja mesure a 150
     agents. Le plafond est un parametre, pas une opinion : on le balaye.

La cascade NE BOUGE PAS l'agent. Elle rend un etat et un cap de reference. La traduction en
mouvement appartient a l'executeur, qui n'existe pas encore et n'est pas branche ici.

smoke : python sirocco_cascade.py smoke
"""
import sys
import torch

VEILLE, REFLEXE, LOCAL, RECRUT, ADAPT, RESOL = 0, 1, 2, 3, 4, 5
NOMS = ["VEILLE", "REFLEXE", "LOCAL", "RECRUT", "ADAPT", "RESOL"]


class Cascade:
    def __init__(self, N, A, device, sec_par_pas=None,
                 s1=0.25,            # seuil de reflexe, sur l'alarme locale (0..1)
                 s3=2.0,             # seuil de charge inflammatoire de zone (etage 3)
                 lat_local=2.0,      # s : sous le feu depuis ce temps -> le binome appuie
                 lat_recrut=5.0,     # s : zone chargee depuis ce temps -> on recrute
                 lat_adapt=20.0,     # s : recrutement sans progression -> l'officier reprend
                 sortie=3.0,         # s sous le seuil -> on redescend
                 resolution=10.0,    # s de retour au dispositif
                 plafond=2,          # LE nombre anti-blob
                 portee_binome=45.0):
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError(
                "sec_par_pas manquant. Les latences sont en SECONDES (elles decrivent un corps, "
                "pas un sandbox) ; la duree d'un pas se MESURE sur Arma. Pas de valeur par defaut.")
        self.N, self.A, self.dev = int(N), int(A), device
        self.spp = float(sec_par_pas)
        self.s1, self.s3, self.plafond = float(s1), float(s3), int(plafond)
        self.portee_binome = float(portee_binome)

        def en_pas(sec): return max(1, int(round(sec / self.spp)))
        self.p_local = en_pas(lat_local); self.p_recrut = en_pas(lat_recrut)
        self.p_adapt = en_pas(lat_adapt); self.p_sortie = en_pas(sortie)
        self.p_resol = en_pas(resolution)
        z = lambda *s: torch.zeros(*s, device=device)                          # noqa: E731
        self.etat = z(N, A).long()
        self.t_etat = z(N, A).long()          # pas passes dans l'etat courant
        self.t_sous = z(N, A).long()          # pas consecutifs sous le seuil
        self.t_feu = z(N, A).long()           # pas consecutifs en REFLEXE (pour l'etage 2)
        self.recrute = torch.zeros(N, A, dtype=torch.bool, device=device)
        self.etat_grp = z(N).long()
        self.t_grp = z(N).long()
        self.t_charge = z(N).long()           # pas consecutifs au-dessus de s3
        self.meilleure_dist = torch.full((N,), float("inf"), device=device)
        self.t_sans_gain = z(N).long()

    @torch.no_grad()
    def reset(self, idx=None):
        for t in (self.etat, self.t_etat, self.t_sous, self.t_feu, self.etat_grp,
                  self.t_grp, self.t_charge, self.t_sans_gain):
            if idx is None: t.zero_()
            else: t[idx] = 0
        if idx is None:
            self.recrute.zero_(); self.meilleure_dist.fill_(float("inf"))
        else:
            self.recrute[idx] = False; self.meilleure_dist[idx] = float("inf")

    @torch.no_grad()
    def pas(self, danger, px, py, menace_dir, charge=None, grad=None,
            vivant=None, dist_obj=None, seuil=None, grad_soi=None):
        """Un pas de cascade.

        danger      (N,A)    l'alarme locale (AlarmeLocale.danger())
        px, py      (N,A)    positions monde
        menace_dir  (N,A,2)  d'ou vient la menace, unitaire (AlarmeLocale.menace()[...,:2])
        charge      (N,)     charge inflammatoire de la zone (ChampSirocco.somme_zone)
        grad        (N,A,2)  gradient du champ a suivre pour le recrutement
        vivant      (N,A)    bool
        dist_obj    (N,)     distance a l'objectif -> sert a detecter l'absence de progression
        seuil       (N,A)    seuil de reflexe LOCAL (memoire immunitaire). Defaut : s1 partout.

        Rend : etat (N,A), recrute (N,A) bool, etat_grp (N,), cap (N,A,2).
        """
        N, A, dev = self.N, self.A, self.dev
        vivant = torch.ones(N, A, dtype=torch.bool, device=dev) if vivant is None else vivant.bool()
        s = torch.full((N, A), self.s1, device=dev) if seuil is None else seuil
        chaud = (danger >= s) & vivant
        self.t_sous = torch.where(chaud, torch.zeros_like(self.t_sous), self.t_sous + 1)
        self.t_etat = self.t_etat + 1

        # ---- REGLE DURE 1 : le reflexe prime. Il n'attend rien et rien ne l'annule. ----
        entre_reflexe = chaud & (self.etat != REFLEXE)
        self.etat = torch.where(entre_reflexe, torch.full_like(self.etat, REFLEXE), self.etat)
        self.t_etat = torch.where(entre_reflexe, torch.zeros_like(self.t_etat), self.t_etat)
        self.t_feu = torch.where(self.etat == REFLEXE, self.t_feu + 1, torch.zeros_like(self.t_feu))

        # ---- etage 2 : mon binome est sous le feu depuis assez longtemps -> j'appuie ----
        sous_feu = (self.etat == REFLEXE) & (self.t_feu >= self.p_local) & vivant   # (N,A)
        dx = px.unsqueeze(1) - px.unsqueeze(2); dy = py.unsqueeze(1) - py.unsqueeze(2)  # j vu de i
        d2 = dx * dx + dy * dy
        eye = torch.eye(A, dtype=torch.bool, device=dev).unsqueeze(0)
        BIG = torch.tensor(1e18, device=dev)
        d2m = torch.where(eye | ~sous_feu.unsqueeze(1), BIG, d2)
        jm = d2m.argmin(2)                                                          # (N,A)
        proche = d2m.min(2).values <= self.portee_binome ** 2
        devient_local = proche & ~chaud & vivant & (self.etat != REFLEXE)
        entre_local = devient_local & (self.etat != LOCAL)
        self.etat = torch.where(entre_local, torch.full_like(self.etat, LOCAL), self.etat)
        self.t_etat = torch.where(entre_local, torch.zeros_like(self.t_etat), self.t_etat)

        # ---- tickets de sortie : REFLEXE et LOCAL redescendent en RESOLUTION ----
        fini = (self.t_sous >= self.p_sortie) & ((self.etat == REFLEXE) | (self.etat == LOCAL))
        fini = fini & ~devient_local
        self.etat = torch.where(fini, torch.full_like(self.etat, RESOL), self.etat)
        self.t_etat = torch.where(fini, torch.zeros_like(self.t_etat), self.t_etat)
        rearme = (self.etat == RESOL) & (self.t_etat >= self.p_resol)
        self.etat = torch.where(rearme, torch.zeros_like(self.etat), self.etat)
        self.t_etat = torch.where(rearme, torch.zeros_like(self.t_etat), self.t_etat)
        self.etat = torch.where(~vivant, torch.zeros_like(self.etat), self.etat)

        # ---- etage 3 : recrutement, sous PLAFOND ----
        charge = torch.zeros(N, device=dev) if charge is None else charge
        self.t_charge = torch.where(charge >= self.s3, self.t_charge + 1, torch.zeros_like(self.t_charge))
        recrutement_ouvert = self.t_charge >= self.p_recrut                          # (N,)
        eligible = (self.etat == VEILLE) & vivant                                    # ni reflexe ni appui
        # les plus proches du foyer : le foyer est le barycentre des agents sous le feu
        w = sous_feu.float()
        wsum = w.sum(1, keepdim=True).clamp(min=1e-6)
        fx = (px * w).sum(1, keepdim=True) / wsum; fy = (py * w).sum(1, keepdim=True) / wsum
        il_y_a_foyer = sous_feu.any(1, keepdim=True)
        dfoyer = torch.where(eligible & il_y_a_foyer,
                             (px - fx) ** 2 + (py - fy) ** 2, BIG.expand(N, A))
        k = min(self.plafond, A)
        pris = torch.zeros(N, A, dtype=torch.bool, device=dev)
        if k > 0:
            idx = dfoyer.topk(k, dim=1, largest=False).indices
            pris.scatter_(1, idx, True)
            pris &= dfoyer < 1e17                     # on ne "recrute" pas un slot vide
        self.recrute = pris & recrutement_ouvert.unsqueeze(1)
        # REGLE DURE 1 encore : un recrute qui prend une balle n'est plus un recrute.
        self.recrute &= (self.etat == VEILLE)
        assert int(self.recrute.sum(1).max()) <= self.plafond, "PLAFOND VIOLE"

        # ---- etage 4 : recrutement qui dure sans progresser -> l'officier reprend ----
        if dist_obj is not None:
            gagne = dist_obj < self.meilleure_dist - 1.0
            self.meilleure_dist = torch.minimum(self.meilleure_dist, dist_obj)
            self.t_sans_gain = torch.where(gagne, torch.zeros_like(self.t_sans_gain),
                                           self.t_sans_gain + 1)
        actif = recrutement_ouvert
        bloque = actif & (self.t_sans_gain >= self.p_adapt)
        self.etat_grp = torch.where(bloque, torch.full_like(self.etat_grp, ADAPT),
                                    torch.where(actif, torch.full_like(self.etat_grp, RECRUT),
                                                torch.zeros_like(self.etat_grp)))

        # ---- le cap de reference (la cascade ne bouge personne, elle oriente) ----
        cap = torch.zeros(N, A, 2, device=dev)
        # etage 0, MISSING SELF : en veille, on regarde la ou AUCUN ami ne couvre.
        # Les cellules NK ne tuent pas ce qu'elles reconnaissent, elles tuent ce qui MANQUE
        # du marqueur du soi — elles reagissent a une absence. Ici pareil : le canal SOI
        # servait d'IFF et d'anti-blob, il devient un declencheur. Sans ca l'etage VEILLE
        # n'est rien : l'escouade avance en regardant toute dans la meme direction.
        if grad_soi is not None:
            cap = torch.where((self.etat == VEILLE).unsqueeze(-1), -grad_soi, cap)
        est_ref = self.etat == REFLEXE
        cap = torch.where(est_ref.unsqueeze(-1), menace_dir, cap)                    # vers la source
        md_j = torch.gather(menace_dir, 1, jm.unsqueeze(-1).expand(N, A, 2))         # menace du binome
        est_loc = self.etat == LOCAL
        cap = torch.where(est_loc.unsqueeze(-1), md_j, cap)
        if grad is not None:
            cap = torch.where(self.recrute.unsqueeze(-1), grad, cap)
        return {"etat": self.etat, "recrute": self.recrute, "etat_grp": self.etat_grp,
                "cap": cap, "sous_feu": sous_feu}

    def resume(self):
        c = [int((self.etat == e).sum()) for e in range(6)]
        return " ".join("%s=%d" % (NOMS[e], c[e]) for e in range(6) if c[e])


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut          # import local : la cascade ne depend pas du champ
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco_cascade : smoke isole (device %s) ===" % dev, flush=True)
    SPP = 0.7   # VALEUR DE TEST, PAS UNE MESURE.
    N, A = 2, 6

    try:
        Cascade(N, A, dev); dire("sec_par_pas obligatoire", False)
    except ValueError:
        dire("sec_par_pas obligatoire (refus explicite)", True)

    def neuf(**kw):
        c = Cascade(N, A, dev, sec_par_pas=SPP, **kw)
        px = torch.linspace(0, 100, A, device=dev).view(1, A).expand(N, A).contiguous()
        py = torch.zeros(N, A, device=dev)
        md = torch.zeros(N, A, 2, device=dev); md[..., 0] = -1.0     # menace a l'ouest
        return c, px, py, md

    # 1. le reflexe part au premier pas ou le seuil est franchi
    c, px, py, md = neuf()
    d = torch.zeros(N, A, device=dev); d[:, 0] = 0.9
    r = c.pas(d, px, py, md)
    dire("reflexe immediat (pas de latence)", int(r["etat"][0, 0]) == REFLEXE)
    dire("les autres restent en veille", int((r["etat"][0] == VEILLE).sum()) == A - 1)

    # 2. le binome passe en appui apres la latence, pas avant
    etats = []
    for t in range(12):
        r = c.pas(d, px, py, md); etats.append(int(r["etat"][0, 1]))
    dire("l'appui attend la latence (%d pas)" % c.p_local,
         etats[0] == VEILLE and LOCAL in etats,
         "premier appui au pas %d" % (etats.index(LOCAL) + 1 if LOCAL in etats else -1))

    # 3. le ticket de sortie ramene en veille
    d0 = torch.zeros(N, A, device=dev)
    for _ in range(c.p_sortie + c.p_resol + 2): r = c.pas(d0, px, py, md)
    dire("ticket de sortie : retour en VEILLE", int((r["etat"] == VEILLE).all()) == 1,
         c.resume() or "tout en veille")

    # 4. LE test anti-blob : le plafond n'est jamais depasse
    for plaf in (1, 2, 3):
        c, px, py, md = neuf(plafond=plaf)
        d = torch.zeros(N, A, device=dev); d[:, 0] = 0.9
        ch = torch.full((N,), 99.0, device=dev)          # zone tres chargee, en permanence
        mx = 0
        for _ in range(40):
            r = c.pas(d, px, py, md, charge=ch, grad=torch.zeros(N, A, 2, device=dev))
            mx = max(mx, int(r["recrute"].sum(1).max()))
        dire("plafond=%d jamais depasse (40 pas satures)" % plaf, mx <= plaf, "max recrutes %d" % mx)

    # 5. REGLE DURE : un recrute qui prend une balle repasse en reflexe
    c, px, py, md = neuf(plafond=3)
    d = torch.zeros(N, A, device=dev); d[:, 0] = 0.9
    ch = torch.full((N,), 99.0, device=dev)
    for _ in range(12): r = c.pas(d, px, py, md, charge=ch)
    cible = int(r["recrute"][0].nonzero()[0]) if int(r["recrute"][0].sum()) else -1
    dire("il y a bien des recrutes avant le test", cible >= 0, "agent %d" % cible)
    if cible >= 0:
        d[:, cible] = 0.9
        r = c.pas(d, px, py, md, charge=ch)
        dire("le reflexe prime sur le recrutement",
             int(r["etat"][0, cible]) == REFLEXE and not bool(r["recrute"][0, cible]))

    # 6. inflammation chronique -> l'officier reprend la main (etage 4)
    c, px, py, md = neuf()
    d = torch.zeros(N, A, device=dev); d[:, 0] = 0.9
    ch = torch.full((N,), 99.0, device=dev)
    dobj = torch.full((N,), 150.0, device=dev)           # on n'avance JAMAIS
    vus = set()
    for _ in range(c.p_adapt + c.p_recrut + 5):
        r = c.pas(d, px, py, md, charge=ch, dist_obj=dobj); vus.add(int(r["etat_grp"][0]))
    dire("bloque longtemps -> etage ADAPTATIF", ADAPT in vus, "etats groupe vus %s" % sorted(vus))

    # 7. si on progresse, on NE passe PAS en adaptatif (pas de faux positif)
    c, px, py, md = neuf()
    dobj = torch.full((N,), 150.0, device=dev); vus = set()
    for _ in range(c.p_adapt + c.p_recrut + 5):
        dobj = dobj - 2.0
        r = c.pas(d, px, py, md, charge=ch, dist_obj=dobj); vus.add(int(r["etat_grp"][0]))
    dire("on progresse -> jamais ADAPTATIF", ADAPT not in vus, "etats groupe vus %s" % sorted(vus))

    # 8. le cap : le reflexe oriente vers la source
    c, px, py, md = neuf()
    r = c.pas(d, px, py, md)
    dire("cap du reflexe = vers la source", float(r["cap"][0, 0, 0]) < -0.9,
         "capx %.2f" % float(r["cap"][0, 0, 0]))

    # 9. MISSING SELF : en veille, on regarde la ou personne ne couvre
    c, px, py, md = neuf()
    gs = torch.zeros(N, A, 2, device=dev); gs[..., 0] = 1.0      # les amis sont a l'EST
    r = c.pas(torch.zeros(N, A, device=dev), px, py, md, grad_soi=gs)
    dire("veille : cap vers le TROU de couverture (ouest)", float(r["cap"][0, 2, 0]) < -0.9,
         "capx %.2f" % float(r["cap"][0, 2, 0]))
    d2 = torch.zeros(N, A, device=dev); d2[:, 2] = 0.9
    r = c.pas(d2, px, py, md, grad_soi=gs)
    dire("...mais le reflexe reprend le cap des qu'il part",
         int(r["etat"][0, 2]) == REFLEXE and float(r["cap"][0, 2, 0]) < -0.9
         and float(r["cap"][0, 2, 1]) == float(md[0, 2, 1]))

    print("=== sirocco_cascade : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
