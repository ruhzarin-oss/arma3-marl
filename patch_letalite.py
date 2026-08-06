#!/usr/bin/env python3
"""patch_letalite.py — ON PEUT ENFIN MOURIR DANS LA SANDBOX.

Diagnostic du 06/08 : `dehors` ne changeait qu a l ARRIVEE. Rien ne tuait l agent, le risque
n etait qu un terme de recompense, et 80 pas a 16 m donnaient 1 280 m pour 210 m a parcourir.
Tout le monde arrivait, toujours, y compris l agent GELE debout en pleine ligne de mire.

TOUTE constante ci-dessous trace vers une mesure Arma datee. Aucune n est choisie.

  COURBE N1 (26/07, 2 414 balles, 18 conditions) — coups au but pour 100 tires, terrain nu :
      dist      25    50    75   100   150   200
      debout    75    57    41    30    24    26
      accroupi  50    59    45    34    26    23
      couche    44    54    43    36    18    16

  CONVERSIONS MESUREES (leviathan/conversion.json, 26/07) — Arma compte en SECONDES et en
  BALLES, la sandbox en PAS. Les trois sont mesurees, aucune choisie :
      tir_par_pas       1,15    = 0,35 balle/s x 3,28 s
      degat_par_impact  0,233   = seuil 0,7 / 3,00 impacts pour neutraliser (31 neutralisations)
      seuil de mort     0,70

  DETECTION (banc angle mort, 03-04/08) — binaire par orientation : 18/18 detectes dans le
  cone, 0/26 hors. Demi-cone 35 degres (CHAMP, deja dans ce fichier). Et couche : invisible
  au-dela de 120 m.

  AU-DELA DE 200 m — la courbe n est pas mesuree. CHOIX DE CONCEPTION ASSUME, trace : la
  table d injection du 26/07 donne 0,070 de degat/pas a 200 m et 0,052 a 300 m, soit un
  facteur 0,743 par tranche de 100 m. On prolonge avec cette decroissance. On ne met PAS de
  falaise : « au-dela de 110 m l ancien sandbox etait un SANCTUAIRE » — c est la cause
  presumee de trois non-transferts.

CE QUI N EST PAS MODELISE, et qui est ecrit ici pour ne pas etre oublie : la suppression
(mesuree a 8 % de capacite residuelle) n a pas d effet, l agent de cette sandbox ne tire pas.
"""
import pathlib

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

# ---------------------------------------------------------------- 1. la loi
ANC = "def facteur_posture(post_poids, d):"
LOI = '''# ============ LA LOI DE MORT, MESUREE SUR ARMA ============
# Voir l en-tete de patch_letalite.py pour la provenance de chaque nombre.
COURBE_D = torch.tensor([25., 50., 75., 100., 150., 200.], device=dev)
COURBE_P = torch.tensor([[0.75, 0.57, 0.41, 0.30, 0.24, 0.26],    # debout
                         [0.50, 0.59, 0.45, 0.34, 0.26, 0.23],    # accroupi
                         [0.44, 0.54, 0.43, 0.36, 0.18, 0.16]],   # couche
                        device=dev)
TIR_PAR_PAS = 1.15          # MESURE : 0,35 balle/s x 3,28 s
DEGAT_PAR_IMPACT = 0.233    # MESURE : seuil 0,7 / 3,00 impacts pour neutraliser
SEUIL_MORT = 0.70           # MESURE
DECROISSANCE_LOIN = 0.743   # par 100 m au-dela de 200 m — choix assume, trace (table 26/07)
COUCHE_INVISIBLE = 120.0    # MESURE : couche invisible au-dela de 120 m

def p_toucher(d, post_poids):
    """probabilite qu une balle porte, par distance et par posture. (B,N)

    Interpolation lineaire entre les six distances mesurees, prolongee au-dela de 200 m par
    la decroissance de la table d injection. PAS DE FALAISE : le sanctuaire au-dela de 110 m
    est precisement le defaut qu on repare."""
    dd = d.clamp(min=25.0)
    i = torch.searchsorted(COURBE_D, dd.clamp(max=200.0).contiguous())
    i = i.clamp(1, len(COURBE_D) - 1)
    d0, d1 = COURBE_D[i - 1], COURBE_D[i]
    w = ((dd.clamp(max=200.0) - d0) / (d1 - d0)).clamp(0, 1)
    # melange des postures par leurs POIDS : le gradient traverse le choix discret
    p = 0.0
    for k in range(3):
        pk = COURBE_P[k][i - 1] * (1 - w) + COURBE_P[k][i] * w
        p = p + pk * post_poids[..., k].unsqueeze(-1)
    loin = torch.where(dd > 200.0, DECROISSANCE_LOIN ** ((dd - 200.0) / 100.0),
                       torch.ones_like(dd))
    return p * loin

def degats_du_pas(p_xy, post_poids, idx):
    """degats subis pendant UN PAS, tous defenseurs confondus. (B,)

    Un defenseur ne tire que s il VOIT : detection binaire par orientation, 18/18 dans le
    cone contre 0/26 hors. Et un homme couche est invisible au-dela de 120 m."""
    v = p_xy.unsqueeze(1) - POS[idx]
    d = v.norm(dim=-1).clamp(min=1.0)
    gis = torch.rad2deg(torch.atan2(v[..., 0], v[..., 1])) % 360
    ec = ((gis - AZI[idx] + 180) % 360 - 180).abs()
    vu = torch.sigmoid((CHAMP - ec) * 1.2)                       # le cone, adouci pour le gradient
    pas_vu_couche = 1.0 - post_poids[..., 2].unsqueeze(-1) * (d > COUCHE_INVISIBLE).float()
    impacts = TIR_PAR_PAS * p_toucher(d, post_poids) * vu * pas_vu_couche * MSK[idx]
    return (impacts * DEGAT_PAR_IMPACT).sum(-1)

def facteur_posture(post_poids, d):'''
assert t.count(ANC) == 1, "ancre facteur_posture"
t = t.replace(ANC, LOI, 1)

# ---------------------------------------------------------------- 2. mourir dans la boucle
A2 = """        d = p.norm(dim=-1)
        vient = (d < ARRIVE).float()*dehors
        arrive = arrive + vient; dehors = dehors*(1-vient)"""
N2 = """        # ---- ON PEUT MOURIR. C est la reparation du 06/08. ----
        # Les degats s accumulent au tarif MESURE sur Arma ; au seuil de 0,70 (trois impacts)
        # l homme est neutralise : il cesse d avancer et il n arrivera pas.
        deg = deg + degats_du_pas(p, wp, idx) * dehors
        vivant = (deg < SEUIL_MORT).float()
        mort_ici = dehors * (1.0 - vivant)
        tues = tues + mort_ici
        dehors = dehors * vivant
        d = p.norm(dim=-1)
        vient = (d < ARRIVE).float()*dehors
        arrive = arrive + vient; dehors = dehors*(1-vient)"""
assert t.count(A2) == 1, "ancre de l arrivee"
t = t.replace(A2, N2, 1)

# ---------------------------------------------------------------- 3. les compteurs
A3 = "    expo_pic = torch.zeros(B, device=dev)     # le PIC d'exposition : ce qui est irréversible"
N3 = (A3 + "\n    deg = torch.zeros(B, device=dev)          # degats cumules, seuil de mort a 0,70\n"
      "    tues = torch.zeros(B, device=dev)         # combien sont tombes, et quand")
assert t.count(A3) == 1, "ancre des compteurs"
t = t.replace(A3, N3, 1)

A4 = "                arrive=arrive, expo=expo_cum, pic=expo_pic, chemin=chemin, temps=temps,"
N4 = ("                arrive=arrive, expo=expo_cum, pic=expo_pic, chemin=chemin, temps=temps,\n"
      "                tues=tues, degats=deg,")
assert t.count(A4) == 1, "ancre du retour"
t = t.replace(A4, N4, 1)

P.write_text(t, encoding='utf-8')
print("loi de mort mesuree installee — provenance de chaque nombre dans l en-tete")
