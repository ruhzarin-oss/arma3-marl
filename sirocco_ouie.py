"""sirocco_ouie — LE CANAL BRUIT. Brique ISOLEE, rien n'est branche.

Mesure du 27/07 (sonde_bruit) : Arma n'a AUCUN evenement « j'ai entendu un tir ».
`FiredNear` est un capteur de BALLE QUI PASSE PRES — un tir dans le vide n'alerte personne,
pas meme a 60 m. C'est le canal FROLEMENT, et il est bien nomme : il ne se declenche que si
on te VISE. Excellent signal, mais de contact.

Or la mesure du jour dit que l'agent doit savoir qu'il paie DES 170 m — il contourne a
132 m quand le bon soldat le fait a 184 m, et paie le double. A 170 m, le frolement est
muet. L'alerte lointaine doit donc etre CONSTRUITE.

LA VOIE : un evenement par COUP, cote tireur (mesure : 41 evenements pour 20 tirs), et
c'est ici qu'on decide qui entend quoi. Avantage decisif pour le pont : un evenement par
coup quel que soit le nombre d'ecoutants — a 80 agents, c'est la difference entre un pont
qui tient et un pont qui sature.

CE QU'UN SOLDAT ENTEND, ET RIEN DE PLUS :
  - qu'un coup est parti, s'il est assez pres pour l'entendre
  - une direction APPROXIMATIVE — l'oreille situe mal, surtout en ville
  - un volume qui decroit avec la distance
Ce qu'il n'entend PAS, et qu'on ne donnera donc jamais : qui a tire, ou exactement, ni si
c'etait pour lui. Meme regle dure que le reste de SIROCCO : on ne depose que du percu.

C'est la difference avec `_champ_danger` d'assault_terrain, qui est un ORACLE : il lit les
positions vraies et la LOS vraie. Il a sa valeur — il a fait passer l'agent de 88 % a 94 %
de prise le 27/07 — mais comme ECHAFAUDAGE, pas comme capteur. Il ne peut pas partir en
live. Cette brique-ci le peut.

smoke : python sirocco_ouie.py smoke
"""
import math
import sys

import torch

from sirocco import BRUIT, PERTE


class Ouie:
    """Transforme des COUPS TIRES en perceptions auditives, par agent.

    `portee_m` est OBLIGATOIRE et sans defaut. C'est LE parametre qui decide si l'ouie
    repond au probleme du jour : si elle ne porte pas au-dela de 170 m, elle n'apprendra
    pas a l'agent qu'il paie deja en arrivant. Le deviner reviendrait a refaire l'erreur
    de `hit=0.06` — un chiffre raisonnable, choisi par quelqu'un de sense, qui a coute
    trois experiences.

    A MESURER SUR ARMA (sonde a ecrire) : a quelle distance l'IA d'Arma detecte-t-elle un
    tireur au SON seul, tireur hors de vue ? `knowsAbout` monte-t-il, et a partir d'ou ?
    En attendant, on passe la valeur explicitement et on la note comme non mesuree.
    """

    def __init__(self, N, A, device, portee_m=None, sec_par_pas=None,
                 erreur_dir_deg=25.0, exposant=1.5, seuil_audible=0.05,
                 attenuation_relief=0.0):
        if portee_m is None or portee_m <= 0:
            raise ValueError(
                "portee_m manquante. C'est LE nombre qui decide si l'ouie couvre les 170 m "
                "ou le probleme se joue. Le passer explicitement, et le mesurer sur Arma.")
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError(
                "sec_par_pas manquant. Les durees sont physiques ; un pas de sandbox n'a de "
                "duree que si on la mesure. Meme regle que le reste de SIROCCO.")
        self.N, self.A, self.dev = int(N), int(A), device
        self.portee = float(portee_m)
        self.spp = float(sec_par_pas)
        # L'oreille situe mal. 25 deg d'ecart-type est un ordre de grandeur, PAS une mesure :
        # c'est ce qui empeche l'ouie de devenir un radar. La baisser a 0 rendrait le canal
        # malhonnete — l'agent saurait exactement d'ou vient le coup sans avoir rien vu.
        self.err = math.radians(float(erreur_dir_deg))
        self.exposant = float(exposant)          # decroissance du volume avec la distance
        self.seuil = float(seuil_audible)        # en dessous : inaudible, on ne depose rien
        self.att_relief = float(attenuation_relief)   # 0 = pas de masquage par le terrain

    # ------------------------------------------------------------------
    @torch.no_grad()
    def percevoir(self, ax, ay, tx, ty, actif=None, generateur=None):
        """Que chaque agent entend-il des coups partis ce pas ?

        ax, ay : positions des agents            (N, A)
        tx, ty : positions des coups tires       (N, M)   M = coups de ce pas
        actif  : (N, M) 1 si le coup a eu lieu   (permet un M fixe avec des trous)

        Rend (N, A, 3) : volume percu, et la direction UNITAIRE bruitee d'ou ca vient.
        Le volume est la somme des coups audibles — plusieurs tireurs font plus de bruit
        qu'un seul, et c'est exactement l'information qui manque a 170 m.
        """
        N, A = self.N, self.A
        M = tx.shape[1]
        dx = tx.unsqueeze(1) - ax.unsqueeze(2)               # (N,A,M) vecteur AGENT -> SOURCE
        dy = ty.unsqueeze(1) - ay.unsqueeze(2)
        d = torch.sqrt(dx * dx + dy * dy).clamp(min=1.0)

        # volume : 1 au depart, 0 a la portee. Decroissance en (1 - d/portee)^exposant.
        v = (1.0 - d / self.portee).clamp(min=0.0) ** self.exposant
        if actif is not None:
            v = v * actif.unsqueeze(1).float()
        v = torch.where(v >= self.seuil, v, torch.zeros_like(v))

        # direction bruitee : l'oreille se trompe, et elle se trompe DAVANTAGE de loin.
        ang = torch.atan2(dx, dy)                             # azimut agent -> source
        if self.err > 0:
            g = torch.Generator(device=ax.device) if generateur is None else generateur
            bruit_ang = torch.randn(N, A, M, device=ax.device) * self.err * (0.5 + 0.5 * d / self.portee)
            ang = ang + bruit_ang
        # somme vectorielle ponderee par le volume : deux tirs opposes s'annulent en
        # direction mais pas en volume — c'est ce que vit un homme pris entre deux feux.
        sx = (torch.sin(ang) * v).sum(-1)
        sy = (torch.cos(ang) * v).sum(-1)
        vol = v.sum(-1)
        n = torch.sqrt(sx * sx + sy * sy).clamp(min=1e-6)
        return torch.stack([vol, sx / n, sy / n], dim=-1)      # (N,A,3)

    # ------------------------------------------------------------------
    @torch.no_grad()
    def alimenter(self, champ, alarme, ax, ay, tx, ty, actif=None):
        """Branche l'ouie sur les deux structures de SIROCCO.

        Dans le CHAMP : on depose au point ENTENDU, pas au point vrai. L'agent croit que
        ca vient de la ; il se trompe un peu, et le champ porte cette erreur. C'est voulu :
        un champ construit sur du percu doit contenir les erreurs du percu.

        Dans l'ALARME LOCALE : le volume et la direction, pour le reflexe.
        """
        p = self.percevoir(ax, ay, tx, ty, actif)             # (N,A,3)
        vol = p[..., 0]
        # position ENTENDUE : a une distance plausible dans la direction percue.
        # On ne connait pas la distance a l'oreille — on la prend a la moitie de la portee,
        # ponderee par le volume (fort = proche). C'est grossier, et c'est honnete.
        dist_crue = (self.portee * (1.0 - vol.clamp(max=1.0)) * 0.5 + 20.0)
        hx = ax + p[..., 1] * dist_crue
        hy = ay + p[..., 2] * dist_crue
        audible = (vol > 0).float()
        champ.deposer(BRUIT, hx, hy, inten=vol.clamp(max=1.0), actif=audible)
        alarme.signaler(BRUIT, ax, ay, hx, hy, vol.clamp(max=1.0), actif=audible)
        return p


# ----------------------------------------------------------------------------------------
def _smoke():
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  [%s] %-46s %s" % ("ok" if cond else "!!", nom, detail), flush=True)

    print("=== smoke sirocco_ouie ===", flush=True)

    try:
        Ouie(2, 4, dev, sec_par_pas=3.28)
        dire("portee obligatoire", False, "aucune erreur levee")
    except ValueError:
        dire("portee obligatoire", True, "refuse de demarrer sans portee mesuree")

    o = Ouie(2, 4, dev, portee_m=300.0, sec_par_pas=3.28)

    # un agent a l'origine, un coup a 50 m au nord, un a 280 m au sud
    ax = torch.zeros(2, 4, device=dev); ay = torch.zeros(2, 4, device=dev)
    tx = torch.tensor([[0.0, 0.0]], device=dev).repeat(2, 1)
    ty = torch.tensor([[50.0, -280.0]], device=dev).repeat(2, 1)
    p = o.percevoir(ax, ay, tx, ty)
    vol = p[0, 0, 0].item(); dy = p[0, 0, 2].item()
    dire("un coup proche est plus fort qu'un lointain", vol > 0.5, "volume total %.2f" % vol)
    dire("la direction pointe vers le plus fort", dy > 0.3, "composante nord %.2f" % dy)

    # au-dela de la portee : rien
    ty2 = torch.full((2, 2), 400.0, device=dev)
    p2 = o.percevoir(ax, ay, tx, ty2)
    dire("hors de portee : inaudible", float(p2[..., 0].max()) == 0.0,
         "volume max %.3f" % float(p2[..., 0].max()))

    # l'erreur de direction existe VRAIMENT (sinon c'est un radar, pas une oreille)
    o2 = Ouie(64, 1, dev, portee_m=300.0, sec_par_pas=3.28, erreur_dir_deg=25.0)
    axb = torch.zeros(64, 1, device=dev); ayb = torch.zeros(64, 1, device=dev)
    txb = torch.zeros(64, 1, device=dev); tyb = torch.full((64, 1), 150.0, device=dev)
    pb = o2.percevoir(axb, ayb, txb, tyb)
    ecart = torch.atan2(pb[..., 1], pb[..., 2]).abs().mean().item()
    dire("l'oreille se trompe (ce n'est pas un radar)", 0.05 < ecart < 1.2,
         "ecart moyen %.0f deg" % math.degrees(ecart))

    o3 = Ouie(64, 1, dev, portee_m=300.0, sec_par_pas=3.28, erreur_dir_deg=0.0)
    p3 = o3.percevoir(axb, ayb, txb, tyb)
    e3 = torch.atan2(p3[..., 1], p3[..., 2]).abs().mean().item()
    dire("sans erreur reglee, la direction est exacte", e3 < 0.02,
         "ecart %.1f deg (temoin)" % math.degrees(e3))

    # branchement sur le champ et l'alarme
    try:
        from sirocco import ChampSirocco, AlarmeLocale
        ch = ChampSirocco(2, 200.0, dev, G=28, sec_par_pas=3.28)
        al = AlarmeLocale(2, 4, dev, sec_par_pas=3.28)
        avant = float(ch.champ[:, BRUIT].sum())
        o.alimenter(ch, al, ax, ay, tx, ty)
        apres = float(ch.champ[:, BRUIT].sum())
        dire("le champ BRUIT se remplit", apres > avant, "masse %.2f -> %.2f" % (avant, apres))
        b1 = al.lire_complet() if hasattr(al, "lire_complet") else None
        dire("l'alarme locale recoit le canal", b1 is not None, "")
    except Exception as x:
        dire("branchement champ/alarme", False, str(x)[:60])

    print("\n>>> %s" % ("smoke OK" if ok else "SMOKE EN ECHEC"), flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(_smoke())
    print(__doc__)
