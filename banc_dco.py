#!/usr/bin/env python3
"""banc_dco — MON BANC RETROUVE-T-IL, A L AVEUGLE, CE QUE MA LECTURE DE CODE A TROUVE ?

CE QUI EST MESURE ICI N EST PAS DCO. C EST MON BANC.
DCO_AI Reforger (github.com/817r/DCOReforger, 19 200 lignes, 22 000 telechargements, mis a
jour cette semaine) porte trois defauts que j ai trouves EN LISANT SON CODE. La question du
jour n est pas « DCO est-il bon » — je sais deja qu il ne l est pas. La question est :

    mes instruments, en ne voyant que des TRAJECTOIRES, retrouvent-ils ces trois defauts ?

Si oui, le produit-verdict est demontre sur un cas reel et exterieur : je sais juger une IA
tactique sans lire son code. Si non, mon banc est aveugle, et il passe avant tout le reste.

LES TROIS DEFAUTS, RECOPIES A L IDENTIQUE DEPUIS SON CODE
--------------------------------------------------------
D1  LE FLANC EST DEGENERE.  `AICommanderBase.c:423` tire un angle au hasard entre 15 et 315
    degres, construit deux candidats MIROIR gauche/droite autour de l axe base->objectif, et
    les note par `1 - |dot(vers objectif, vers base)|`. Les deux candidats etant symetriques
    par rapport a cet axe, les deux notes sont EGALES PAR CONSTRUCTION : sa fonction
    d evaluation ne peut pas separer ses propres candidats. Aucun terrain, aucun couvert,
    aucune ligne de vue n entre dans la note.
    ⚠️ RECTIFICATIF DU 15/08, apres mesure. J avais ecrit « le `>=` prend donc toujours la
    gauche ». FAUX en pratique : en flottants 32 bits l ordre des operations differe entre
    les deux candidats, l arrondi departage, et la gauche sort 69 % du temps — pas 100 %.
    Le fond est pire que ce que je disais : le cote n est pas un biais fixe qu on pourrait
    corriger, c est du BRUIT D ARRONDI. La consequence observable n est donc pas « il va
    toujours a gauche » mais « le cote choisi est independant du monde ». C est cela qu il
    faut mesurer, et la sonde qui testait 0,95 de gauche testait la mauvaise chose.

D2  LA SUPPRESSION S AUTO-AMPLIFIE.  `DCO_MoraleSystem.c:256` ecrit
        m_fMoraleSuppression += Math.Clamp(m_fMoraleSuppression + plus, 0, 1.5)
    soit x += clamp(x + y) : le stress s ajoute a lui-meme, il DOUBLE a chaque rafale au lieu
    de s incrementer. Son propre changelog du 17/06/2026 dit « Fixing Suppression
    Overreacting » — il a vu le symptome, pas la ligne.

D3  LA CAMARADERIE PESE PLUS QUE LE FEU RECU.  Meme fichier : le stress total retranche 0,08
    par camarade vivant, quand une balle proche ajoute 0,005. Huit camarades valent donc 128
    balles encaissees d avance. C est l INVERSE exact de ce que j ai mesure : la suppression
    subie vaut x10.

LE MONDE
--------
`monde_fidele.monde()` — le gymnase, avec les seules constantes MESUREES sur Arma. Objectif a
l origine, attaquants poses a R_spawn. Rien n est ajoute ni eteint ici : ce banc ne mesure pas
le monde, il mesure mes instruments dans le monde que j ai deja certifie.

LES BRAS. UNE VARIABLE A LA FOIS.
---------------------------------
    DCO        les trois defauts, la politique telle qu elle est ecrite chez lui
    DCO+R1     seul le flanc est repare  (8 candidats, notes par le couvert reellement traverse)
    DCO+R2     seule la suppression est reparee  (x = clamp(x + y))
    DCO+R3     seule la camaraderie est bornee  (le bonus ne peut plus depasser une rafale)
    FRONTAL    CONTROLE POSITIF : aucun contournement, droit sur l objectif
    DCO'       CONTROLE NUL : DCO a l identique, autres graines

LES INSTRUMENTS. ILS NE VOIENT QUE DES TRAJECTOIRES.
---------------------------------------------------
Aucun n a le droit de lire l etat interne de la politique. Tous se calculent depuis les
positions, les expositions et les vies — exactement ce qu un juge exterieur observerait.
    I1  prise            fraction d episodes ou un vivant atteint l objectif
    I2  cout             exposition cumulee par metre gagne vers l objectif   <- LA variable
    I3  part vus         part d hommes passes sous alerte
    I4  accord couvert   accord entre le cote de l EXCURSION DE POINTE (le point ou la
                         trajectoire s ecarte le plus de l axe base->objectif) et le cote le
                         PLUS COUVERT du terrain. 0,5 = le choix ignore le monde. Les episodes
                         sans excursion franche (< 20 m) ou sans cote franchement meilleur
                         (asymetrie < 0,02) SORTENT : ils n ont pas de bonne reponse.
    I5  haltes           part des pas sans progression, sous feu
    I6  pente camarade   pente de (haltes) sur (nombre de vivants), a exposition egale

LES SEUILS SONT PRE-ENREGISTRES ICI, AVANT LA PREMIERE DONNEE
-------------------------------------------------------------
G0  CONTROLE POSITIF. I2 doit separer FRONTAL de DCO d au moins 25 % en valeur relative,
    p < 0,01 (permutation sur les episodes). SI G0 TOMBE, LE BANC EST MUET : tout le reste
    de ce fichier est illisible et on s arrete la. Un banc qui ne voit pas un assaut frontal
    ne verra rien de plus fin.
G0b CONTROLE NUL. DCO contre DCO' : aucune des six metriques ne doit sortir a p < 0,05 apres
    correction de Bonferroni. Si l une sort, mon banc fabrique des differences.
G1  D1. DEUXIEME REECRITURE, LE 15/08, APRES LA PREMIERE TABLE ET AVANT LA SECONDE.
    G1c CONTROLE D INSTRUMENT — ORACLE, qui contourne PERPENDICULAIREMENT du cote le plus
        couvert par construction, doit obtenir I4 >= 0,80. S il ne l obtient pas, I4 est
        aveugle et G1 N EST PAS LISIBLE, quels que soient les chiffres de DCO et de R1.
    G1  DETECTION — I4 dans [0,42 ; 0,58] sur DCO (le cote pris ignore le monde) ET I4 > 0,65
        sur DCO+R1, p < 0,05 (binomial exact contre 0,5).
    Historique des deux revisions, pour qu on puisse me reprocher les deux :
      v1 « cote gauche >= 0,95 » — refutee par le jouet : l arrondi flottant departe, 64-69 %.
      v2 « accord >= 0,65 sur R1 » — TOMBEE a 0,565 sur l integrale laterale, qui compense
         l aller et le retour et que les morts deplacent. L instrument, pas le defaut.
      v3 (ici) excursion de POINTE signee, episodes filtres sur excursion > 20 m ET asymetrie
         de couvert > 0,02, et un ORACLE qui prouve que l instrument sait tirer.
G2  D2 detecte si I5 baisse d au moins 20 % en relatif de DCO a DCO+R2, p < 0,05. INCHANGEE.
G3  D3. REECRITE LE 15/08 : la pente seule est confondue avec la SURVIE — elle valait −0,046
    sur DCO et −0,042 sur DCO+R3, ou la camaraderie est pourtant bornee. Ce qui distingue les
    deux bras n est pas la pente, c est L ECART ENTRE LEURS PENTES.
    v1 pente seule : confondue avec la survie, negative partout. TOMBEE.
    v2 ecart de pentes entre bras : AVEUGLE — la camaraderie x5 ne la bouge pas (p = 0,26).
       Cause : a 4 hommes, le nombre de vivants ne varie que par les MORTS ; « avoir des
       camarades » y est indissociable de « n avoir pas encore ete touche ».
    v3 (ici) LA TAILLE D ESCOUADE VARIE PAR CONCEPTION — 4 hommes contre 8 — et la
       camaraderie se lit dans la DIFFERENCE DE DIFFERENCES :
           [haltes(4 h) - haltes(8 h)] du bras, comparee au meme ecart dans l autre bras.
    G3c CONTROLE D INSTRUMENT — CAM5 (camaraderie x5) doit avoir un ecart 4h-8h
        significativement plus grand que DCO (p < 0,05, permutation). Sinon I6 reste aveugle
        et G3 n est pas lisible.
    G3  DETECTION — l ecart 4h-8h de DCO significativement plus grand que celui de DCO+R3,
        p < 0,05.
    ESCALADE, PRE-ENREGISTREE LE 15/08 A 14h50, AVANT LES DONNEES. A n = 600 par cellule,
    G3c donne p = 0,09145 : la direction est la bonne (CAM5 +0,0123 contre DCO -0,0121) mais
    l echantillon ne tranche pas. UNE SEULE escalade est autorisee, a n = 2400 par cellule
    (x4), evaluee UNE FOIS. Quel que soit son resultat, il est definitif : si p reste >= 0,05,
    I6 est declare AVEUGLE et D3 sans signature comportementale dans ce monde. Pas de
    troisieme tour, pas de troisieme instrument. Ecrit ici pour qu on puisse me l opposer.
VERDICT DU BANC = nombre de defauts sur trois retrouves a l aveugle, G0 et G0b passes.

CE QUI FERAIT ECHOUER CE BANC, ECRIT AVANT DE LE LANCER
------------------------------------------------------
  . les bras rendent des trajectoires identiques -> la substitution ne prend pas, tout est
    nul et rien n est lisible. C EST LE JOUET (--jouet) QUI DOIT L ATTRAPER, pas la table.
  . G0 tombe -> banc muet, verdict = mon banc est aveugle, et c est un resultat qui compte.
  . G0b sort -> banc bavard, il separe deux fois la meme chose ; tout gain est du bruit.
  . I4 vaut 0,5 sur DCO -> le flanc degenere ne se voit PAS dans la trajectoire ; le defaut
    est reel dans le code et invisible au comportement. Resultat NEGATIF, et il compte : il
    dit que lire le code reste necessaire, donc que le produit-verdict ne suffit pas seul.
  . toutes les metriques separent tout -> je mesure la graine, pas la politique.
"""
import sys, os, json, math, argparse, time

sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from monde_fidele import monde

SORTIE = os.environ.get("SORTIE", "/home/younes/arma3-marl/logs_train/banc_dco.jsonl")

# ---------------------------------------------------------------- LES CONSTANTES DE DCO
# Recopiees de DCO_MoraleSystem.c. Aucune n est choisie par moi. Les commentaires portent le
# nom de la constante chez lui, pour qu on puisse verifier ligne a ligne.
MOTIVATED_THRESHOLD = 0.4      # MOTIVATED_THRESHOLD
ANXIOUS_THRESHOLD = 1.5        # ANXIOUS_THRESHOLD
MANIAC_THRESHOLD = 2.0         # MANIAC_THRESHOLD
BREAK_THRESHOLD = 3.7          # BREAK_THRESHOLD
MORALE_CAP = 4.5               # clamp de m_fMoraleTotal
SUPPRESSION_BULLET_INCREMENT = 0.005   # SUPPRESSION_BULLET_INCREMENT
MORALE_DROP_BLEEDING = 0.35            # MORALE_DROP_BLEEDING_FIXED_INCREMENT
ENDANGERED_INCREMENT = 0.02            # ENDANGERED_INCREMENT, par seconde
BOOST_FIXED_FRIENDLY = 0.08            # MORALE_BOOST_FIXED_FRIENDLY_VALUE, par camarade vivant
# ⚠️ SON CODE ECRIT `0.0005 * 0.001` — PAR MILLISECONDE. Je l avais transcrit `0.0005`, mille
# fois trop grand : la decroissance depassait alors la valeur elle-meme (0,0005 x 3280 ms =
# 1,64) et le stress CHANGEAIT DE SIGNE a chaque pas. Le defaut D2 etait eteint dans ma
# recopie, et les bras DCO et DCO+R2 rendaient des trajectoires identiques. Faute de recopie,
# attrapee par la table et non par le jouet — parce que le jouet jugeait l ETAT (le stress
# differe) et non l ACTE (l action differe). Regle 16.
SUPPRESSION_RECOVERY = 0.0005 * 0.001  # MORALE_SUPPRESSION_RECOVERY, par milliseconde
FLANK_ANGLE_MIN, FLANK_ANGLE_MAX = 15.0, 315.0   # m_fFlankAngleMin / Max
FLANK_DIST = 150.0                     # ComputeFlankPosition(base, staging, 150)
WAIT_BASE_S = 3.0                      # ResolveStoppedWaitTime, base

# Actions de l env : 0-7 = caps par 45 deg, 8 = HOLD, 9 = SUPPRESS, 10-12 = postures.
HOLD = 8


def cote_couvert(e, idx):
    """De quel cote de l axe base->objectif le couvert est-il le plus abondant, ET DE COMBIEN.

    Rend l ECART SIGNE (gauche moins droite), pas seulement son signe : un episode ou les deux
    cotes se valent n a pas de bonne reponse, et le compter dilue le contraste. C est le
    monde qui parle ici, jamais la politique — utilise par l instrument comme par le
    controle positif ORACLE.
    """
    import terrain_gpu as TG
    d = e.dev
    bx, by = e.apx[idx].mean(1), e.apy[idx].mean(1)
    a = torch.stack([-bx, -by], 1)
    a = a / a.norm(dim=1, keepdim=True).clamp(min=1e-6)
    px, py = -a[:, 1], a[:, 0]                       # perpendiculaire gauche
    t = torch.linspace(0.2, 0.8, 5, device=d).view(1, 5, 1)
    s = torch.linspace(25.0, 120.0, 4, device=d).view(1, 1, 4)
    ox = bx.view(-1, 1, 1) * (1 - t); oy = by.view(-1, 1, 1) * (1 - t)
    m = idx.numel()
    gx = (ox + px.view(-1, 1, 1) * s).reshape(m, -1)
    gy = (oy + py.view(-1, 1, 1) * s).reshape(m, -1)
    dx_ = (ox - px.view(-1, 1, 1) * s).reshape(m, -1)
    dy_ = (oy - py.view(-1, 1, 1) * s).reshape(m, -1)
    cg = TG.sample(e.cover, gx, gy, e.scale).clamp(max=1.0).mean(1)
    cd = TG.sample(e.cover, dx_, dy_, e.scale).clamp(max=1.0).mean(1)
    return cg - cd, px, py


def _cap_vers(dx, dy):
    """Cap discret (0-7) le plus proche du vecteur demande. 0 = +y, sens horaire."""
    ang = torch.atan2(dx, dy)                       # comme l env : sin sur x, cos sur y
    return (torch.round(ang / (math.pi / 4.0)) % 8).long()


class PolitiqueDCO:
    """DCO recopie : l accumulateur de stress, ses seuils, sa regle de direction, son flanc.

    `reparations` est un ensemble parmi {"R1", "R2", "R3"}. Vide = DCO tel qu il est ecrit.
    `frontal=True` = le controle positif : aucun point de contournement, droit sur l objectif.
    """

    def __init__(self, env, reparations=(), frontal=False, seed=0):
        self.e = env
        self.rep = set(reparations)
        self.frontal = bool(frontal)
        self.g = torch.Generator(device="cpu").manual_seed(seed)
        d = env.dev
        N, A = env.N, env.A
        self.stress = torch.zeros(N, A, device=d)
        self.supp = torch.zeros(N, A, device=d)          # m_fMoraleSuppression
        self.supp_plus = torch.zeros(N, A, device=d)     # m_fMoraleSuppressionPlus
        self.endangered = torch.zeros(N, A, device=d)
        self.attente = torch.zeros(N, A, device=d)       # pas d immobilite restants
        self.dmg_prec = torch.zeros(N, A, device=d)
        self.wp = torch.zeros(N, 2, device=d)            # point de passage courant, par env
        self.cote = torch.zeros(N, device=d)             # +1 gauche, -1 droite (trace interne)
        self.nouveau(torch.arange(N, device=d))

    # ---------------------------------------------------------------- LE FLANC DE DCO
    def nouveau(self, idx):
        """Recalcule le point de contournement pour les env qui viennent de repartir."""
        if idx.numel() == 0:
            return
        e = self.e
        d = e.dev
        base_x = e.apx[idx].mean(1)
        base_y = e.apy[idx].mean(1)
        # objectif = origine (l env gagne par `sqrt(apx^2+apy^2) < secure_r`)
        ax, ay = -base_x, -base_y
        n = torch.sqrt(ax * ax + ay * ay).clamp(min=1e-6)
        ax, ay = ax / n, ay / n
        if self.frontal:
            self.wp[idx, 0] = 0.0
            self.wp[idx, 1] = 0.0
            self.cote[idx] = 0.0
            return
        if "ORACLE" in self.rep:
            # CONTROLE POSITIF DE L INSTRUMENT I4, pas un bras de mesure. Point de passage
            # pose PERPENDICULAIREMENT a l axe, du cote ou le couvert est le plus abondant :
            # un contournement franc, du bon cote, par construction. Si l instrument ne le
            # note pas haut, c est l instrument qui est aveugle, pas la politique.
            ec, px, py = cote_couvert(e, idx)
            sg = torch.sign(ec)
            tot = torch.sqrt(base_x ** 2 + base_y ** 2)
            mx = base_x + ax * (tot * 0.5)
            my = base_y + ay * (tot * 0.5)
            self.wp[idx, 0] = (mx + px * sg * FLANK_DIST).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
            self.wp[idx, 1] = (my + py * sg * FLANK_DIST).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
            self.cote[idx] = sg
            return
        m = idx.numel()
        ang = (torch.rand(m, generator=self.g).to(d)
               * (FLANK_ANGLE_MAX - FLANK_ANGLE_MIN) + FLANK_ANGLE_MIN) * math.pi / 180.0
        ratio = torch.rand(m, generator=self.g).to(d) * 0.25 + 0.45      # RandomFloat(0.45, 0.70)
        tot = torch.sqrt(base_x ** 2 + base_y ** 2)
        mx = base_x + ax * (tot * ratio)
        my = base_y + ay * (tot * ratio)
        c, s = torch.cos(ang), torch.sin(ang)
        if "R1" in self.rep:
            # REPARATION : on n oppose plus deux candidats miroirs notes par un angle, on en
            # pose huit et on les note par ce que le monde repond — le couvert reellement
            # traverse entre le candidat et l objectif, moins l exposition au poser.
            K = 8
            angs = torch.linspace(0.0, 2.0 * math.pi, K + 1, device=d)[:K].view(1, K)
            dx = torch.sin(angs) * FLANK_DIST
            dy = torch.cos(angs) * FLANK_DIST
            cx = (mx.view(-1, 1) + dx).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
            cy = (my.view(-1, 1) + dy).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
            note = self._note_couvert(cx, cy)
            j = note.argmax(1, keepdim=True)
            self.wp[idx, 0] = torch.gather(cx, 1, j).squeeze(1)
            self.wp[idx, 1] = torch.gather(cy, 1, j).squeeze(1)
            # cote reel du point retenu, pour la trace interne seulement
            sel_x = self.wp[idx, 0] - mx
            sel_y = self.wp[idx, 1] - my
            self.cote[idx] = torch.sign(ax * sel_y - ay * sel_x)
            return
        # DCO tel quel : deux candidats miroirs, note = 1 - |dot|, et `>=` prend la gauche.
        lx = ax * c - ay * s
        ly = ax * s + ay * c
        rx = ax * c + ay * s
        ry = -ax * s + ay * c
        cand_lx, cand_ly = mx + lx * FLANK_DIST, my + ly * FLANK_DIST
        cand_rx, cand_ry = mx + rx * FLANK_DIST, my + ry * FLANK_DIST
        note_l = self._note_dot(cand_lx, cand_ly, base_x, base_y)
        note_r = self._note_dot(cand_rx, cand_ry, base_x, base_y)
        gauche = note_l >= note_r                                    # le `>=` de son code
        self.wp[idx, 0] = torch.where(gauche, cand_lx, cand_rx).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
        self.wp[idx, 1] = torch.where(gauche, cand_ly, cand_ry).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
        self.cote[idx] = torch.where(gauche, torch.ones_like(note_l), -torch.ones_like(note_l))

    def _note_dot(self, cx, cy, bx, by):
        """`EvaluateFlankCandidate` : 1 - |dot(vers objectif, vers base)|, a plat."""
        ox, oy = -cx, -cy                       # objectif = origine
        n1 = torch.sqrt(ox * ox + oy * oy).clamp(min=1e-6)
        ox, oy = ox / n1, oy / n1
        tx, ty = bx - cx, by - cy
        n2 = torch.sqrt(tx * tx + ty * ty).clamp(min=1e-6)
        tx, ty = tx / n2, ty / n2
        return 1.0 - (ox * tx + oy * ty).abs()

    def _note_couvert(self, cx, cy):
        """R1 : ce que le monde repond. Couvert moyen sur le segment candidat->objectif."""
        e = self.e
        import terrain_gpu as TG
        P = 6
        t = torch.linspace(0.15, 0.9, P, device=e.dev).view(1, 1, P)
        sx = cx.unsqueeze(-1) * (1 - t)
        sy = cy.unsqueeze(-1) * (1 - t)
        M, K = cx.shape
        cov = TG.sample(e.cover, sx.reshape(M, -1), sy.reshape(M, -1), e.scale).reshape(M, K, P)
        return cov.clamp(max=1.0).mean(-1)

    # ---------------------------------------------------------------- DIAGNOSTICS DU JOUET
    def _geometrie(self):
        e = self.e
        bx, by = e.apx.mean(1), e.apy.mean(1)
        ax, ay = -bx, -by
        n = torch.sqrt(ax * ax + ay * ay).clamp(min=1e-6)
        ax, ay = ax / n, ay / n
        ang = (torch.rand(e.N, generator=self.g).to(e.dev)
               * (FLANK_ANGLE_MAX - FLANK_ANGLE_MIN) + FLANK_ANGLE_MIN) * math.pi / 180.0
        ratio = torch.rand(e.N, generator=self.g).to(e.dev) * 0.25 + 0.45
        tot = torch.sqrt(bx ** 2 + by ** 2)
        return bx, by, ax, ay, ang, bx + ax * (tot * ratio), by + ay * (tot * ratio)

    def diagnostic_note(self):
        """L ecart entre les deux notes de DCO. Doit etre nul : elles ne separent rien."""
        bx, by, ax, ay, ang, mx, my = self._geometrie()
        c, s = torch.cos(ang), torch.sin(ang)
        lx, ly = ax * c - ay * s, ax * s + ay * c
        rx, ry = ax * c + ay * s, -ax * s + ay * c
        nl = self._note_dot(mx + lx * FLANK_DIST, my + ly * FLANK_DIST, bx, by)
        nr = self._note_dot(mx + rx * FLANK_DIST, my + ry * FLANK_DIST, bx, by)
        return float((nl - nr).abs().median()), float((nl >= nr).float().mean())

    def diagnostic_etendue(self):
        """L etendue des notes de R1. Doit etre franche : le monde repond quelque chose."""
        e = self.e
        _, _, _, _, _, mx, my = self._geometrie()
        K = 8
        angs = torch.linspace(0.0, 2.0 * math.pi, K + 1, device=e.dev)[:K].view(1, K)
        cx = (mx.view(-1, 1) + torch.sin(angs) * FLANK_DIST).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
        cy = (my.view(-1, 1) + torch.cos(angs) * FLANK_DIST).clamp(-e.terr_R * 0.99, e.terr_R * 0.99)
        note = self._note_couvert(cx, cy)
        return float((note.max(1).values - note.min(1).values).mean())

    # ---------------------------------------------------------------- LE STRESS DE DCO
    def _maj_stress(self, exposed, vivants, nviv):
        e = self.e
        dt_ms = e.sec_par_pas * 1000.0 if getattr(e, "sec_par_pas", None) else 3280.0
        # recuperation, comme chez lui (falloff proportionnel)
        self.supp = self.supp - self.supp * SUPPRESSION_RECOVERY * dt_ms
        self.supp_plus = self.supp_plus - self.supp_plus * SUPPRESSION_RECOVERY * dt_ms
        # entree : les balles proches. Le monde rend une exposition ; on la convertit en
        # nombre de balles avec les constantes DEJA mesurees du gymnase, pas des miennes.
        balles = exposed * getattr(e, "tir_par_pas", 1.15) * e.D
        self.supp_plus = (self.supp_plus + balles * SUPPRESSION_BULLET_INCREMENT).clamp(0.0, 3.2)
        if "R2" in self.rep:
            self.supp = (self.supp + self.supp_plus).clamp(0.0, MORALE_CAP)      # repare
        else:
            self.supp = self.supp + (self.supp + self.supp_plus).clamp(0.0, MORALE_CAP)  # sa ligne
        # blessure : le passage d un seuil de degats vaut l hemorragie
        saigne = (e.admg > self.dmg_prec + 0.05).float()
        self.dmg_prec = e.admg.clone()
        # avoir une cible sous les yeux
        self.endangered = torch.where(
            exposed > 0.0,
            (self.endangered + ENDANGERED_INCREMENT * e.sec_par_pas).clamp(max=1.2),
            self.endangered * 0.98)
        boost = nviv.unsqueeze(1) * BOOST_FIXED_FRIENDLY
        if "CAM5" in self.rep:
            # CONTROLE POSITIF DE L INSTRUMENT I6, pas un bras de mesure. La camaraderie est
            # multipliee par cinq : le defaut D3 est rendu ENORME. Si la pente ne le voit pas,
            # l instrument est aveugle a la camaraderie et G3 n est pas lisible.
            boost = boost * 5.0
        if "R3" in self.rep:
            # REPARATION : la camaraderie ne peut plus valoir plus qu une rafale encaissee.
            boost = boost.clamp(max=20.0 * SUPPRESSION_BULLET_INCREMENT)
        self.stress = (self.supp + saigne * MORALE_DROP_BLEEDING + self.endangered
                       - boost).clamp(0.0, MORALE_CAP) * vivants

    # ---------------------------------------------------------------- L ACTION
    def acte(self):
        e = self.e
        d = e.dev
        vivants = e._aalive().float()
        nviv = vivants.sum(1)
        exposed = getattr(e, "last_exposed", torch.zeros_like(e.apx))
        self._maj_stress(exposed, vivants, nviv)

        # halte : ResolveStoppedWaitTime, converti en pas
        attente_s = WAIT_BASE_S + (self.stress / MORALE_CAP) * 1.5 + 1.0
        pas_attente = torch.ceil(attente_s / e.sec_par_pas)
        doit_stopper = (self.stress > ANXIOUS_THRESHOLD) & (self.attente <= 0)
        self.attente = torch.where(doit_stopper, pas_attente, (self.attente - 1).clamp(min=0))

        # point de passage : le contournement tant qu on ne l a pas atteint, puis l objectif
        wx = self.wp[:, 0].unsqueeze(1).expand_as(e.apx)
        wy = self.wp[:, 1].unsqueeze(1).expand_as(e.apy)
        dwp = torch.sqrt((e.apx - wx) ** 2 + (e.apy - wy) ** 2)
        atteint = dwp < 30.0
        cx = torch.where(atteint, torch.zeros_like(wx), wx)
        cy = torch.where(atteint, torch.zeros_like(wy), wy)
        dx, dy = cx - e.apx, cy - e.apy

        # la regle de direction de DCO, MoraleAndThreatPushMove
        sous_feu = exposed > 0.05
        recule = (self.stress > MANIAC_THRESHOLD) & sous_feu
        lateral = (self.stress > ANXIOUS_THRESHOLD) & (self.stress <= MANIAC_THRESHOLD)
        rx, ry = -dx, -dy                                          # BACKWARD
        sx, sy = -dy, dx                                           # LEFT
        tire = (torch.rand(e.N, e.A, generator=self.g).to(d) < 0.5)
        sx = torch.where(tire, sx, -sx)
        sy = torch.where(tire, sy, -sy)
        fx = torch.where(recule, rx, torch.where(lateral, sx, dx))
        fy = torch.where(recule, ry, torch.where(lateral, sy, dy))

        acts = _cap_vers(fx, fy)
        acts = torch.where(self.attente > 0, torch.full_like(acts, HOLD), acts)
        return acts


# ---------------------------------------------------------------- LES INSTRUMENTS
class Instruments:
    """Ne voit que des trajectoires : positions, exposition, vies. Jamais l etat interne."""

    def __init__(self, env):
        self.e = env
        N = env.N
        d = env.dev
        z = lambda: torch.zeros(N, device=d)
        self.expo = z(); self.gagne = z(); self.vus = z(); self.pas = z()
        self.halte = z(); self.pas_feu = z(); self.viv = z()
        # I4 REPARE : on ne cumule plus l ecart lateral (l aller et le retour se compensent,
        # les morts deplacent le barycentre, et l integrale finit par ne mesurer que du
        # bruit). On garde l EXCURSION DE POINTE, signee : le point ou la trajectoire
        # s ecarte le plus de l axe base->objectif. C est la definition naturelle de
        # « de quel cote sont-ils passes », et elle reste purement trajectorielle.
        self.lat_pic = z(); self.lat_abs = z()
        self.d0 = torch.sqrt(env.apx ** 2 + env.apy ** 2).mean(1)
        self.dprec = self.d0.clone()
        self.axe = torch.stack([-env.apx.mean(1), -env.apy.mean(1)], 1)
        n = self.axe.norm(dim=1, keepdim=True).clamp(min=1e-6)
        self.axe = self.axe / n
        self.cg = cote_couvert(env, torch.arange(N, device=d))[0]
        self.ep = []

    def observe(self, info):
        e = self.e
        al = e._aalive().float()
        nviv = al.sum(1)
        expo = getattr(e, "last_exposed", torch.zeros_like(e.apx))
        dist = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        dmoy = (dist * al).sum(1) / nviv.clamp(min=1)
        # ⚠️ L AVANCE SE CALCULE AVANT D ECRASER LA DISTANCE PRECEDENTE. La premiere version
        # faisait `self.dprec = dmoy` puis testait `(self.dprec - dmoy)` : identiquement nul,
        # donc « halte » valait « sous le feu » et ne pouvait pas echouer. Faute de mesure
        # attrapee au premier coup d oeil sur la table, pas par le jouet.
        avance = self.dprec - dmoy                      # > 0 = on se rapproche de l objectif
        self.expo += (expo * al).sum(1) / nviv.clamp(min=1)
        self.gagne += avance.clamp(min=0.0)
        self.vus += (getattr(e, "alerte_niv", torch.zeros(e.N, device=e.dev)) > 0).float()
        sous_feu = ((expo * al).sum(1) / nviv.clamp(min=1)) > 0.05
        self.halte += (sous_feu & (avance.abs() < 1.0)).float()
        self.pas_feu += sous_feu.float()
        self.dprec = dmoy
        cx = (e.apx * al).sum(1) / nviv.clamp(min=1)
        cy = (e.apy * al).sum(1) / nviv.clamp(min=1)
        lat = self.axe[:, 0] * cy - self.axe[:, 1] * cx            # ecart signe a l axe, en m
        plus_loin = lat.abs() > self.lat_abs
        self.lat_pic = torch.where(plus_loin, lat, self.lat_pic)
        self.lat_abs = torch.where(plus_loin, lat.abs(), self.lat_abs)
        self.viv += nviv
        self.pas += 1

    def recolte(self, idx, info):
        """Range les episodes finis et remet les compteurs a zero. AVANT le reset du monde."""
        if idx.numel() == 0:
            return
        pris = info["took"][idx].float()
        expo = self.expo[idx]
        gagne = self.gagne[idx].clamp(min=1.0)
        for k in range(idx.numel()):
            self.ep.append(dict(
                prise=float(pris[k]),
                cout=float(expo[k] / gagne[k]),
                vus=float(self.vus[idx][k] / self.pas[idx][k].clamp(min=1)),
                accord=float(torch.sign(self.lat_pic[idx][k]) == torch.sign(self.cg[idx][k])),
                excursion=float(self.lat_abs[idx][k]),   # m : sous 20 m, « le cote » n a pas
                                                         # de sens, l episode sort de I4
                asym=float(self.cg[idx][k].abs()),       # asymetrie de couvert du monde :
                                                         # a zero, il n y a pas de bon cote
                haltes=float(self.halte[idx][k] / self.pas_feu[idx][k].clamp(min=1)),
                feu=float(self.pas_feu[idx][k]),   # 0 = episode sans feu : `haltes` est VIDE,
                                                   # a exclure de I5 au lieu de le compter 0
                viv=float(self.viv[idx][k] / self.pas[idx][k].clamp(min=1)),
            ))
        for a in (self.expo, self.gagne, self.vus, self.pas, self.halte,
                  self.pas_feu, self.lat_pic, self.lat_abs, self.viv):
            a[idx] = 0.0

    def reamorce(self, idx):
        """Reprend l axe, le cote couvert et la distance. APRES le reset du monde."""
        if idx.numel() == 0:
            return
        self.dprec[idx] = torch.sqrt(self.e.apx[idx] ** 2 + self.e.apy[idx] ** 2).mean(1)
        ax = torch.stack([-self.e.apx[idx].mean(1), -self.e.apy[idx].mean(1)], 1)
        self.axe[idx] = ax / ax.norm(dim=1, keepdim=True).clamp(min=1e-6)
        self.cg[idx] = cote_couvert(self.e, idx)[0]


# ---------------------------------------------------------------- LA MANCHE
def tourner(bras, n_env, n_ep, seed, device):
    # DEUXIEME REPARATION DE I6. La pente haltes/vivants est aveugle a la camaraderie meme
    # multipliee par cinq (G3c tombee, p = 0,26) — parce qu a 4 hommes le nombre de vivants
    # ne varie QUE par les morts : « avoir des camarades » y est indissociable de « n avoir
    # pas encore ete touche ». On fait donc varier la taille d escouade PAR CONCEPTION :
    # un suffixe `@8` construit le monde a 8 attaquants au lieu de 4. La camaraderie se lit
    # alors dans l ECART ENTRE TAILLES, a attrition comparable.
    A = 4
    if "@" in bras:
        bras, a_txt = bras.split("@")
        A = int(a_txt)
    rep, frontal = {
        "DCO": ((), False), "DCO+R1": (("R1",), False), "DCO+R2": (("R2",), False),
        "DCO+R3": (("R3",), False), "FRONTAL": ((), True), "DCO'": ((), False),
        "ORACLE": (("ORACLE",), False),      # controle positif de l instrument I4
        "CAM5": (("CAM5",), False),          # controle positif de l instrument I6
    }[bras]
    e = monde(num_envs=n_env, device=device, seed=seed, A=A)
    pol = PolitiqueDCO(e, rep, frontal, seed=seed)
    ins = Instruments(e)
    e.reset()
    t0 = time.time()
    while len(ins.ep) < n_ep:
        acts = pol.acte()
        # auto_reset=False : le reset interne de l env appelle `gen_terrain(0, ...)` quand
        # aucun episode ne se termine, et son `torch.quantile` tombe sur un tenseur vide.
        # On ne touche pas a son monde, on prend la main sur la clotures ici.
        _, _, done, info = e.step(acts, auto_reset=False)
        ins.observe(info)
        idx = done.nonzero(as_tuple=True)[0]
        if idx.numel():
            ins.recolte(idx, info)
            e._reset(idx)
            ins.reamorce(idx)
            pol.nouveau(idx)
            pol.stress[idx] = 0.0; pol.supp[idx] = 0.0; pol.supp_plus[idx] = 0.0
            pol.endangered[idx] = 0.0; pol.attente[idx] = 0.0; pol.dmg_prec[idx] = 0.0
        if time.time() - t0 > 1800:
            print(f"  ! {bras} : temps depasse a {len(ins.ep)} episodes")
            break
    return ins.ep[:n_ep], float(pol.cote.mean())


# ---------------------------------------------------------------- LE JOUET
def jouet(device):
    """AVANT la table : prouver que les trois substitutions PRENNENT.

    Si un bras rend la meme chose que DCO, la table entiere est illisible, et c est ici
    qu il faut le voir — pas apres trente minutes de calcul.
    """
    print("\n  JOUET — les substitutions prennent-elles ?")
    print("  " + "=" * 70)
    ok = True
    e = monde(num_envs=256, device=device, seed=1)
    e.reset()
    p_dco = PolitiqueDCO(e, (), seed=1)
    p_r1 = PolitiqueDCO(e, ("R1",), seed=1)
    # D1 : le defaut n est PAS un cote, c est une note qui ne separe pas. On mesure donc
    # l ecart entre les deux notes de DCO, et l etendue des notes de R1.
    ecart, gauche = p_dco.diagnostic_note()
    etendue = p_r1.diagnostic_etendue()
    print(f"    D1  |note_g - note_d| median = {ecart:.3e}   (cote gauche {gauche:.3f})")
    print(f"        etendue des notes R1      = {etendue:.3f}")
    if ecart > 1e-4:
        print("        ECHEC : ma recopie separe les candidats, DCO non. Recopie fausse."); ok = False
    if etendue < 0.02:
        print("        ECHEC : R1 note tout pareil, la reparation ne repare rien."); ok = False

    ex = torch.full((e.N, e.A), 0.5, device=e.dev)
    viv = torch.ones(e.N, e.A, device=e.dev); nv = viv.sum(1)
    a = PolitiqueDCO(e, (), seed=2); b = PolitiqueDCO(e, ("R2",), seed=2)
    for _ in range(5):
        a._maj_stress(ex, viv, nv); b._maj_stress(ex, viv, nv)
    print(f"    D2  stress apres 5 pas sous feu : DCO {float(a.stress.mean()):.3f}"
          f"   R2 {float(b.stress.mean()):.3f}")
    if float(a.stress.mean()) <= float(b.stress.mean()) * 1.2:
        print("        ECHEC : l auto-amplification ne se voit pas."); ok = False

    # D3 : avec 8 camarades il faut 0,64 de suppression accumulee avant que le stress quitte
    # zero. Un seul pas ne peut donc RIEN montrer — la premiere version de cette sonde
    # comparait deux zeros et croyait mesurer. On tient le feu jusqu a saturation.
    # D3 se mesure au FRANCHISSEMENT DU SEUIL, pas a saturation. Sous un feu soutenu les deux
    # bras plafonnent a 4,5 et ne peuvent plus differer : la premiere version comparait deux
    # plafonds et croyait mesurer. Ce qui decide, c est QUAND le seuil ANXIOUS est franchi —
    # c est cela que la camaraderie retarde.
    def pas_avant_seuil(pol, nviv, maxi=60):
        n = torch.full((e.N,), float(nviv), device=e.dev)
        for k in range(1, maxi + 1):
            pol._maj_stress(ex, viv, n)
            if float(pol.stress.mean()) > ANXIOUS_THRESHOLD:
                return k
        return maxi
    k2 = pas_avant_seuil(PolitiqueDCO(e, (), seed=3), 2)
    k8 = pas_avant_seuil(PolitiqueDCO(e, (), seed=3), 8)
    j2 = pas_avant_seuil(PolitiqueDCO(e, ("R3",), seed=3), 2)
    j8 = pas_avant_seuil(PolitiqueDCO(e, ("R3",), seed=3), 8)
    print(f"    D3  pas avant de franchir ANXIOUS, 2 vivants -> 8 vivants :"
          f" DCO {k2} -> {k8}   R3 {j2} -> {j8}")
    if k8 <= k2:
        print("        ECHEC : la camaraderie ne retarde pas la panique dans ma recopie."); ok = False
    if j8 != j2:
        print("        ECHEC : R3 ne borne pas la camaraderie."); ok = False

    # ---- L ACTE, PAS L ETAT. Regle 16. Un stress qui differe et qui ne franchit aucun seuil
    # de decision ne change AUCUNE action : les deux bras rendent alors la meme trajectoire
    # et la table entiere est un zero deguise. On compare donc les ACTIONS EMISES, dans le
    # monde, sur les memes graines.
    print("\n    ACTE — les bras emettent-ils des actions differentes ?")
    ref = None
    for nom, rep in (("DCO", ()), ("DCO+R1", ("R1",)), ("DCO+R2", ("R2",)), ("DCO+R3", ("R3",))):
        ee = monde(num_envs=128, device=device, seed=11)
        ee.reset()
        p = PolitiqueDCO(ee, rep, seed=11)
        traces, hold = [], 0.0
        for _ in range(25):
            a = p.acte()
            traces.append(a.clone())
            hold += float((a == HOLD).float().mean())
            ee.step(a, auto_reset=False)
        t = torch.stack(traces)
        if ref is None:
            ref, nom_ref = t, nom
            print(f"      {nom:<7} part de HOLD {hold / 25:.3f}   (reference)")
        else:
            diff = float((t != ref).float().mean())
            print(f"      {nom:<7} part de HOLD {hold / 25:.3f}   actions differentes de "
                  f"{nom_ref} : {diff:.3f}")
            if diff < 0.02:
                print(f"        ECHEC : {nom} agit comme {nom_ref}. La reparation ne prend "
                      f"pas dans l ACTE."); ok = False

    print("\n    " + ("JOUET PASSE — la table est lisible." if ok else
                      "JOUET TOMBE — NE PAS LANCER LA TABLE."))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jouet", action="store_true")
    ap.add_argument("--env", type=int, default=256)
    ap.add_argument("--ep", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--bras", default="DCO,DCO+R1,DCO+R2,DCO+R3,FRONTAL,DCO'")
    a = ap.parse_args()
    if a.jouet:
        sys.exit(0 if jouet(a.device) else 1)
    for i, b in enumerate(a.bras.split(",")):
        graine = a.seed + (1000 if b == "DCO'" else 0)
        ep, cote = tourner(b, a.env, a.ep, graine, a.device)
        ligne = dict(bras=b, n=len(ep), seed=graine, cote_interne=cote,
                     A=(int(b.split("@")[1]) if "@" in b else 4), episodes=ep)
        with open(SORTIE, "a") as f:
            f.write(json.dumps(ligne) + "\n")
        m = lambda k, s=None: (sum(e[k] for e in (s or ep)) / max(len(s or ep), 1))
        sf = [e for e in ep if e["feu"] > 0]          # I5 n a de sens que sous le feu
        lis = [e for e in ep if e["excursion"] > 20.0 and e["asym"] > 0.02]   # I4 lisible
        print(f"  {b:<8} n={len(ep):<4} prise={m('prise'):.3f} cout={m('cout'):.4f} "
              f"vus={m('vus'):.3f} accord={m('accord', lis):.3f} (n_cote={len(lis)}) "
              f"haltes={m('haltes', sf):.3f} (n_feu={len(sf)})")


if __name__ == "__main__":
    main()
