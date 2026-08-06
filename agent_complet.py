#!/usr/bin/env python3
"""agent_complet.py — L'AGENT À RÉPERTOIRE OUVERT.

Il reçoit tout ce qu'on a capturé. Il dispose de ce qu'un soldat peut faire. Personne ne lui
dit à quoi sert quoi. Les seuils sont figés dans CRITERES_AGENT.md, écrits avant ce run.

CE QUI A MENÉ ICI — quatre versions, chacune arrêtée par un critère écrit d'avance :
  v1 distance pénalisée à chaque pas -> fonce, s'expose PLUS qu'une ligne droite
  v2 pénalité retirée -> fuit, n'arrive jamais
  v3 arrivée obligatoire -> le gradient à travers 50 pas ne converge pas
  v4 choix d'un seul axe -> converge, 93 % de mieux que l'axe moyen. Mais Younes : « je
     t'avais demandé un réseau qui découvre l'ensemble de ce qu'il peut faire ». Non.
     J'avais réduit le problème à un paramètre pour le rendre facile.

CE QUI EST MESURÉ ET QUI SERT DE CALIBRATION (jamais inventé)
  être dans le champ ennemi ...... x1,75 sur le risque  <- sonde 3, 563 000 observations
  pente avec la distance ......... +45 % à 80 m, +84 % à 300 m  <- sonde 3
  se coucher ..................... risque / 1,4  <- courbe n°1, Arma, juillet
  détection ...................... INSENSIBLE au mouvement  <- mesuré
  se coucher ..................... vitesse / 3  <- CHOIX DE CONCEPTION, non mesuré, déclaré

AVEU PORTÉ AU RAPPORT : rien dans nos mesures ne pénalise la course. L'agent choisira donc
probablement de courir en permanence. Ce sera un RÉSULTAT — « dans ce monde l'allure n'a pas
d'arbitrage » — et non un échec. Inventer un malus pour rendre le choix intéressant
reviendrait à fabriquer la conclusion.

LE PIÈGE, ÉCRIT D'AVANCE : ce simulateur est le nôtre. L'agent optimisera NOS règles.
⟨juillet : 96 % en sandbox, 0/38 dans Arma⟩ AUCUN VERDICT NE SORT DE CE RUN. Arma tranchera.
"""
import numpy as np, math, json, time, sys
import torch, torch.nn as nn

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda'; torch.cuda.set_device(0)
torch.backends.cuda.matmul.allow_tf32 = True

# ============ 1. CONFIGURATIONS DÉFENSIVES RÉELLES ============
print("extraction des configurations défensives réelles", flush=True)
X = np.load(f'{D}/noeuds.npy', mmap_mode='r'); P = np.load(f'{D}/presence.npy', mmap_mode='r')
T, N, _ = X.shape
configs = []
rng = np.random.default_rng(5)
for ti in rng.choice(T, 60000, replace=False):
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    for camp in (0, 1):
        s = pt & (xt[:,4] > 0.5) & (xt[:,5] == camp)
        if s.sum() < 4: continue
        pos = xt[s][:,1:3]; azi = xt[s][:,7]; sup = xt[s][:,9]; pst = xt[s][:,8]
        c = pos.mean(0); d = np.linalg.norm(pos-c, axis=1); g = d < 120
        if g.sum() < 4 or g.sum() > 12: continue
        configs.append((pos[g]-pos[g].mean(0), azi[g], sup[g], pst[g])); break
    if len(configs) >= 3000: break
NC = len(configs)
DMAX = max(len(c[0]) for c in configs)
print(f"  {NC} configurations, {np.mean([len(c[0]) for c in configs]):.1f} défenseurs, max {DMAX}", flush=True)

POS = np.zeros((NC,DMAX,2), np.float32); AZI = np.zeros((NC,DMAX), np.float32)
SUP = np.zeros((NC,DMAX), np.float32); PST = np.zeros((NC,DMAX), np.float32)
MSK = np.zeros((NC,DMAX), np.float32)
for i,(p,a,s_,q) in enumerate(configs):
    POS[i,:len(p)]=p; AZI[i,:len(a)]=a; SUP[i,:len(s_)]=s_; PST[i,:len(q)]=q; MSK[i,:len(p)]=1
POS=torch.tensor(POS,device=dev); AZI=torch.tensor(AZI,device=dev)
SUP=torch.tensor(SUP,device=dev); PST=torch.tensor(PST,device=dev); MSK=torch.tensor(MSK,device=dev)

# découpe en trois : entraînement / réglage / JAMAIS VU  ⟨Fable : sinon on mesure une mémorisation⟩
n1, n2 = int(NC*0.7), int(NC*0.85)
I_TR = torch.arange(0, n1, device=dev)
I_VA = torch.arange(n1, n2, device=dev)
I_TE = torch.arange(n2, NC, device=dev)
print(f"  entraînement {len(I_TR)}   réglage {len(I_VA)}   JAMAIS VU {len(I_TE)}", flush=True)

# ============ 2. LE MONDE ============
# LE DEMI-CÔNE EST MESURÉ, PLUS SUPPOSÉ. ⟨banc du 03/08, 26 essais⟩
#   0° · 10° · 20° · 30° -> 4,00, PLATEAU PARFAITEMENT PLAT (8 essais, aucune exception)
#   40° · 44° · 47° · 50° · 53° · 75° · 90° · 180° -> 0,00
# La bascule est donc entre 30 et 40 degrés. J'avais codé 60 sans le vérifier : la zone
# dangereuse était surestimée de près du double, et un agent entraîné là-dedans aurait
# contourné bien plus large qu'Arma ne l'exige. Incertitude assumée : ±5°.
CHAMP=35.0; NPAS=80; DEPART=250.0; ARRIVE=40.0
DEPART_COURANT = 250.0   # modifié par le curriculum de rayon
# 80 pas : debout-course 1 280 m, couché-marche 264 m. Les deux permettent d'arriver, donc
# l'agent ARBITRE au lieu de subir. ⟨à 50 pas, ramper donnait 264 m pour 250 m à parcourir :
# aucune marge, et l'agent devait choisir entre être invisible et arriver⟩
# VITESSES MESURÉES ⟨banc du 03/08, 14 essais, zéro écarté, contrôle passé à 4,91 m/s⟩
#   debout   : lent 1,77 · normal 5,77 · course 5,31 m/s
#   accroupi : normal 2,76 · course 2,83   -> 0,53 de la course debout  (je codais 0,60)
#   couché   : lent 0,67 · normal 1,38 · course 1,24  -> 0,23           (je codais 0,33)
# C'était le DERNIER paramètre inventé du simulateur. Ramper est encore plus lent que je ne
# l'avais supposé : moins d'un quart de la vitesse, pas un tiers. Conséquence directe — ramper
# tout le long devient géométriquement impossible, et l'agent doit choisir OÙ ramper.
# Un pas = 0,2 s de simulation, donc mètres par pas = vitesse x 0,2 x 5 (le tick fait 1 s de jeu).
ALLURES = torch.tensor([0.0, 5.8, 16.0], device=dev)     # arrêt · normal 5,77 m/s · course 5,31->16 m/pas
POSTURES_V = torch.tensor([1.0, 0.53, 0.23], device=dev) # MESURÉ, plus supposé
# LA POSTURE EST UNE MARCHE, PAS UN FACTEUR PLAT.  ⟨banc Arma du 03/08, 52 essais⟩
#   terrain nu, couché :  60 m -> vu (4,00)   100 m -> vu (4,00)   150 m -> INVISIBLE (0,00)
#   terrain nu, accroupi : 4,00 partout — AUCUN effet
# Le premier jet mettait « risque ÷ 1,4 partout », tiré d'une courbe de juillet. C'était plat,
# donc faux : l'agent se couchait EN PERMANENCE et n'en tirait rien, ce qui m'a fait conclure
# à tort que le répertoire était décoratif. Il ne l'était pas — c'est mon monde qui l'aplatissait.
SEUIL_COUCHE = 120.0     # centre de la marche, mesuré entre 100 et 150 m
PENTE_COUCHE = 12.0
def facteur_posture(post_poids, d):
    """part du risque conservée selon la posture ET la distance à l'observateur"""
    couche = 1.0 - torch.sigmoid((d - SEUIL_COUCHE) / PENTE_COUCHE)   # 1 de près, ~0 de loin
    un = torch.ones_like(couche)
    # debout et accroupi : aucun effet en terrain nu, mesuré
    f = torch.stack([un, un, couche], -1)                              # (B, DMAX, 3)
    return (f * post_poids.unsqueeze(1)).sum(-1)                       # (B, DMAX)

def expo(p, post, idx, post_poids=None):
    """exposition instantanée. Deux effets, tous deux MESURÉS et dépendants de la distance :
    l'orientation (sonde 3 : +45 % à 80 m, +84 % à 300 m) et la posture (banc Arma : le
    couché ne paie qu'au-delà de 120 m). Le facteur de posture est appliqué PAR OBSERVATEUR,
    car il dépend de la distance à chacun."""
    v = p.unsqueeze(1) - POS[idx]
    d = v.norm(dim=-1).clamp(min=1.0)
    gis = torch.rad2deg(torch.atan2(v[...,0], v[...,1])) % 360
    ec = ((gis - AZI[idx] + 180) % 360 - 180).abs()
    # PLATEAU PLAT PUIS CHUTE FRANCHE, comme mesuré — et non une décroissance douce.
    # À l'intérieur du cône, s'écarter de l'axe ne rapporte RIEN : c'est tout ou rien.
    dans = torch.sigmoid((CHAMP - ec) * 1.2)
    base = 0.45 * (1.0 - (d/400).clamp(0,1))          # part vue quelle que soit l'orientation
    e = (base + (1.0-base) * dans) * (1.0 - (d/450).clamp(0,1))
    if post_poids is None:
        post_poids = torch.nn.functional.one_hot(post, 3).float()
    e = e * facteur_posture(post_poids, d)
    # AGRÉGATION PAR LE MAXIMUM, PAS PAR LA MOYENNE.
    # ⟨banc de certification du 03/08 : le chemin de l'agent ne transférait pas — écart de
    #  12 % seulement contre 25 % exigés, détecté 15 fois sur 17 comme la ligne droite.⟩
    # La cause : je calculais l'exposition comme une MOYENNE sur les défenseurs. Arma prend le
    # MAXIMUM — il suffit d'UN SEUL homme qui vous voit pour que le camp entier sache où vous
    # êtes. C'est ce qu'on a mesuré le matin même (knowsAbout est de CAMP : un camarade qui
    # voit suffit à faire monter tout le monde à 4,00), et que je n'avais pas répercuté ici.
    # L'agent optimisait donc la mauvaise quantité : il évitait d'être vu EN MOYENNE, alors
    # qu'il faut n'être vu PAR PERSONNE.
    e = e.masked_fill(MSK[idx] < 0.5, 0.0)
    return e.max(dim=1).values

# ---------------------------------------------------------------- LE RISQUE APPRIS
# expo, la fonction analytique batie a partir de mesures ponctuelles, vaut AUC 0,5005 sur
# 563 383 observations reelles : LE HASARD. Un predicteur appris sur la GEOMETRIE SEULE —
# distance, angle sous lequel je suis dans son champ, angle sous lequel il est dans le mien —
# atteint 0,6549, et l'ablation montre que l'ecart avec la variante enrichie (0,7178) vient
# a 92 % de la SUPPRESSION SUBIE : une quasi-tautologie que la sandbox n'a pas et ne doit
# pas avoir. La variante transferable n'est donc pas degradee, c'est la seule honnete.
# ⟨les quatre bancs Arma qui ont produit expo restent VRAIS : ils mesuraient la detection du
#  moteur, avec controles. C'est l'AGREGATION qui est morte, pas les faits.⟩
import torch.nn as _nn
class _Risque(_nn.Module):
    def __init__(s, ce, cs, h=96):
        super().__init__()
        s.enc = _nn.Sequential(_nn.Linear(ce, h), _nn.ReLU(), _nn.Linear(h, h))
        s.q = _nn.Linear(cs, h)
        s.out = _nn.Sequential(_nn.Linear(cs+h, h), _nn.ReLU(), _nn.Linear(h, 1))
    def forward(s, soi, enn, msk):
        z = s.enc(enn)
        a = (z * s.q(soi).unsqueeze(1)).sum(-1) / math.sqrt(z.shape[-1])
        a = torch.softmax(a.masked_fill(msk < 0.5, -1e9), -1).unsqueeze(-1)
        return s.out(torch.cat([soi, (z*a).sum(1)], -1)).squeeze(-1)

_ck = torch.load('/mnt/data/corpus/risque_geo.pt', map_location=dev)
RISQUE = _Risque(_ck['ce'], _ck['cs']).to(dev)
RISQUE.load_state_dict(_ck['etat'])
for _p in RISQUE.parameters(): _p.requires_grad_(False)   # gele : on apprend l'agent, pas lui
RISQUE.eval()
print(f"risque appris charge — AUC {_ck['auc']:.4f} sur le corpus "
      f"(expo valait 0,5005, le hasard)", flush=True)

def risque(p, post, idx, post_poids=None):
    """le cout, APPRIS sur Arma. Meme signature et meme echelle [0,1] que expo."""
    v = p.unsqueeze(1) - POS[idx]
    d = v.norm(dim=-1).clamp(min=1.0)
    gis = torch.rad2deg(torch.atan2(v[...,0], v[...,1])) % 360
    a_lui = ((gis - AZI[idx] + 180) % 360 - 180).abs()          # je suis dans SON champ
    # mon cap : je regarde vers l'objectif, qui est a l'origine
    cap = torch.rad2deg(torch.atan2(-p[...,0], -p[...,1])) % 360
    a_moi = (((gis + 180) % 360 - cap.unsqueeze(1) + 180) % 360 - 180).abs()
    ent = torch.stack([(d/400).clamp(max=1.0), a_lui/180, a_moi/180], -1)
    if post_poids is None:
        pc = post.float()/3
    else:
        pc = (post_poids * torch.tensor([0.,1.,2.], device=dev)).sum(-1)/3
    r = RISQUE(pc.unsqueeze(-1), ent, MSK[idx])
    return torch.sigmoid(r)          # ramene sur [0,1], comme expo

# ============ LE CHAMP DE RISQUE — ETAGE 1 ============
# Criteres deposes avant lancement : CRITERES_ETAGE1_PERCEPTION.md (+ addendum sur la taille
# de la porte : 5 graines, succes a 4 sur 5).
CHAMP_ACTIF = '--champ' in sys.argv
CHAMP_PLACEBO = '--placebo' in sys.argv
PORTEE_CHAMP = 100.0   # REQUALIFIE le 06/08 sur la table de dispersion : le champ est un REGARD,
                       # pas un pas. A 35 m (herite du 27/07, calibre sur l expo morte) il ne
                       # parlait qu en deca de 90 m — une fois la manoeuvre deja jouee.
_a8 = torch.arange(8, device=dev, dtype=torch.float32) * (math.pi / 4)
DIRS8 = torch.stack([torch.sin(_a8), torch.cos(_a8)], -1)     # (8,2), huit caps

def champ_risque(p, post, idx):
    """le prix d un pas de 35 m dans chacune des huit directions. (B,8)

    Le PLACEBO tire huit nombres de bruit de meme echelle : meme capacite offerte au reseau,
    zero information. C est le controle qui sait echouer."""
    B = p.shape[0]
    if CHAMP_PLACEBO:
        return torch.rand(B, 8, device=dev)
    pp = (p.unsqueeze(1) + DIRS8.unsqueeze(0) * PORTEE_CHAMP).reshape(B * 8, 2)
    return risque(pp, post.repeat_interleave(8), idx.repeat_interleave(8)).reshape(B, 8)

def percevoir(p, post, idx):
    """TOUT ce qu'on a, sans résumé : une ligne par entité, l'attention triera."""
    v = p.unsqueeze(1) - POS[idx]
    d = v.norm(dim=-1).clamp(min=1.0)
    gis = torch.rad2deg(torch.atan2(v[...,0], v[...,1])) % 360
    ec_lui = ((gis - AZI[idx] + 180) % 360 - 180).abs()      # je suis dans SON champ
    ent = torch.stack([
        v[...,0]/300, v[...,1]/300, (d/400).clamp(0,2),
        ec_lui/180, torch.sigmoid((CHAMP-ec_lui)*1.2),
        SUP[idx], PST[idx]/3, MSK[idx],
        (1.0-(d/450).clamp(0,1)),
    ], -1) * MSK[idx].unsqueeze(-1)
    moi = torch.cat([p/300, p.norm(dim=-1,keepdim=True)/300,
                     torch.nn.functional.one_hot(post,3).float(),
                     MSK[idx].sum(1,keepdim=True)/DMAX,
                     risque(p, post, idx).unsqueeze(-1)]
                    + ([champ_risque(p, post, idx)] if CHAMP_ACTIF else []), -1)
    return moi, ent

CE, CM = 9, (8 + 8 if CHAMP_ACTIF else 8)   # +8 = le champ de risque (etage 1)
print(f"observation : {CE} par entite, {CM} pour soi"
      f"{' — CHAMP DE RISQUE ACTIF' if CHAMP_ACTIF else ''}"
      f"{' (PLACEBO : bruit)' if CHAMP_PLACEBO else ''}", flush=True)
H = 128

if '--smoke' in sys.argv:
    # LE SEUIL NE BOUGE PAS : 0,010 de dispersion entre les huit directions. Ce qui change,
    # c est l exigence — il doit etre franchi A CHAQUE DISTANCE du trajet, pas en moyenne.
    # Un champ qui ne parle qu au but est un champ qui parle trop tard.
    _SEUIL = 0.010
    _B = 512
    _idx = torch.randint(0, NC, (_B,), device=dev)
    _po = torch.zeros(_B, dtype=torch.long, device=dev)
    print(f"\n  SMOKE — champ de risque, portee {PORTEE_CHAMP:.0f} m"
          f"{' (PLACEBO : bruit)' if CHAMP_PLACEBO else ''}")
    print("  " + "-" * 68)
    _tout = True
    for _d in (40, 60, 90, 120, 160, 200, 250):
        _a = torch.rand(_B, device=dev) * 2 * math.pi
        _p = torch.stack([torch.sin(_a), torch.cos(_a)], -1) * _d
        _c = champ_risque(_p, _po, _idx)
        _disp = _c.std(dim=1).mean().item()
        _ok = _disp > _SEUIL
        _tout &= _ok
        print(f"    a {_d:3d} m de l objectif   dispersion {_disp:.4f}   "
              f"{'OK' if _ok else 'MORD — le champ est plat ici'}")
    _moi, _ent = percevoir(_p, _po, _idx)
    _larg = (_moi.shape[-1] == CM and _ent.shape[-1] == CE)
    print("  " + "-" * 68)
    print(f"    largeur de l observation : soi={_moi.shape[-1]} (attendu {CM})"
          f" · entite={_ent.shape[-1]} (attendu {CE})   {'OK' if _larg else 'ECHEC'}")
    print(f"\n  SMOKE {'PASSE — lancement autorise' if (_tout and _larg) else 'MORD — on ne lance rien'}\n")
    sys.exit(0 if (_tout and _larg) else 1)

class Politique(nn.Module):
    def __init__(s):
        super().__init__()
        s.enc = nn.Sequential(nn.Linear(CE,H), nn.ReLU(), nn.Linear(H,H))
        s.q   = nn.Linear(CM,H)
        s.tronc = nn.Sequential(nn.Linear(CM+H,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU())
        s.dir = nn.Linear(H,2); s.allure = nn.Linear(H,3); s.posture = nn.Linear(H,3)
        s.dir_sigma = nn.Parameter(torch.zeros(1) - 0.7)   # écart-type appris de la direction
        s.valeur = nn.Linear(H,1)                       # ligne de base, pour réduire le bruit
    def forward(s, moi, ent, msk):
        h = s.enc(ent)
        a = (h * s.q(moi).unsqueeze(1)).sum(-1) / math.sqrt(H)
        a = torch.softmax(a.masked_fill(msk<0.5, -1e9), -1).unsqueeze(-1)
        z = s.tronc(torch.cat([moi, (h*a).sum(1)], -1))
        return s.dir(z), s.allure(z), s.posture(z), s.valeur(z).squeeze(-1)

# ============ 3. DÉROULEMENT ============
# CHANGEMENT DE MÉTHODE, et pourquoi.
# REINFORCE ne prend pas ici : il compare des épisodes partis de positions différentes, et la
# chance du tirage de départ noie le signal des actions. Mesuré : l'agent choisit « arrêt » et
# « couché » à 100 % alors que rester immobile rapporte -25,1 et courir droit +19,3.
# Ce qui a MARCHÉ, c'est v4 : le gradient direct à travers la fonction d'exposition, qui est
# dérivable — il convergeait proprement (93 % de mieux que l'axe moyen). Son seul obstacle
# était les choix discrets, que le gradient ne traverse pas.
# On lève cet obstacle : les choix d'allure et de posture passent par une relaxation continue
# (Gumbel-softmax). Le tirage reste discret en avant, mais le gradient passe en arrière.
# Tout redevient dérivable, et on retrouve la convergence de v4 avec le répertoire complet.
def derouler(pol, idx, tarif, echantillonne=True, gel=None, azi_faux=False, force_dir=None):
    """gel : (allure, posture) imposées -> sert au test d'ablation"""
    global AZI
    if azi_faux:
        sauv = AZI.clone(); AZI = torch.rand_like(AZI)*360
    B = len(idx)
    ang = torch.rand(B, device=dev)*2*math.pi
    p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * DEPART_COURANT
    post = torch.zeros(B, dtype=torch.long, device=dev)
    lp_tot = torch.zeros(B, device=dev); ent_tot = torch.zeros(B, device=dev)
    val_l, rec_l = [], []
    arrive = torch.zeros(B, device=dev); dehors = torch.ones(B, device=dev)
    expo_cum = torch.zeros(B, device=dev); chemin = torch.zeros(B, device=dev)
    expo_pic = torch.zeros(B, device=dev)     # le PIC d'exposition : ce qui est irréversible
    temps = torch.zeros(B, device=dev); trop = torch.zeros(B, device=dev)
    n_post = torch.zeros(B, 3, device=dev); n_all = torch.zeros(B, 3, device=dev)
    expo_quand_couche = torch.zeros(B, device=dev); n_couche = torch.zeros(B, device=dev)
    expo_quand_debout = torch.zeros(B, device=dev); n_debout = torch.zeros(B, device=dev)

    for t in range(NPAS):
        d_prec = p.norm(dim=-1)
        moi, ent = percevoir(p, post, idx)
        dr, al, po, val = pol(moi, ent, MSK[idx])
        # LA DIRECTION EST UN CAP, PAS UNE VITESSE. Sans cette normalisation — perdue dans un
        # patch — le réseau apprend à produire des vecteurs de norme énorme et l'agent se
        # TÉLÉPORTE : arrivée 98,9 %, exposition divisée par quatorze, en DEUX pas pour
        # 250 mètres. C'est le critère « temps de mission » qui l'a attrapé.
        dr = dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)
        if force_dir is not None:
            # RÉFÉRENCE HONNÊTE : droit au but, debout, en courant. Le premier jet forçait
            # la direction mais héritait des postures de l'agent — je comparais l'agent à
            # lui-même rampant, et sa « référence » n'arrivait qu'à 25,9 %.
            wa = torch.zeros(B,3,device=dev); wa[:,2] = 1
            wp = torch.zeros(B,3,device=dev); wp[:,0] = 1
        elif gel is not None:
            wa = torch.zeros(B,3,device=dev); wa[:,gel[0]] = 1
            wp = torch.zeros(B,3,device=dev); wp[:,gel[1]] = 1
        elif echantillonne:
            # relaxation continue : discret en avant, dérivable en arrière
            wa = torch.nn.functional.gumbel_softmax(al, tau=1.0, hard=True)
            wp = torch.nn.functional.gumbel_softmax(po, tau=1.0, hard=True)
        else:
            wa = torch.nn.functional.one_hot(al.argmax(-1),3).float()
            wp = torch.nn.functional.one_hot(po.argmax(-1),3).float()
        ia = wa.argmax(-1); ip = wp.argmax(-1)
        lp = torch.zeros(B, device=dev)
        if force_dir is not None: dr = force_dir(p)
        post = ip
        # la vitesse et le risque passent par les POIDS, pas par l'indice : c'est là que
        # le gradient traverse le choix discret
        vit = (wa*ALLURES).sum(-1) * (wp*POSTURES_V).sum(-1)
        pas_reel = dr * vit.unsqueeze(-1) * dehors.unsqueeze(-1)
        p = p + pas_reel
        chemin = chemin + pas_reel.norm(dim=-1); temps = temps + dehors
        # SURVEILLANCE DE L'EXPLOITATION : on mesure le déplacement RÉELLEMENT effectué, pas
        # celui qu'on croit avoir ordonné. Tout écart trahit une fuite du simulateur.
        trop = trop + (pas_reel.norm(dim=-1) > ALLURES.max()*1.01).float()
        e = risque(p, post, idx, wp)      # LE COUT EST APPRIS, plus invente
        expo_cum = expo_cum + e*dehors
        # LE CLIQUET. Ce qui se paie, c est l AUGMENTATION du pic, pas l exposition de
        # chaque pas. La somme des increments du pic EST le pic final : l agent paie une
        # fois d avoir ete vu, et ne peut plus le racheter en etant discret ensuite.
        # ⟨table du 04/08 : sous la regle SOMME, le chemin optimal-max score PIRE que celui
        #  de l agent dans 19 configurations sur 20. La sandbox recompensait le rachat.
        #  Arma ne rachete rien : la memoire du camp ne decroit pas, 5 minutes mesurees.⟩
        d_pic = (e*dehors - expo_pic).clamp(min=0)
        expo_pic = expo_pic + d_pic
        n_post.scatter_add_(1, ip.unsqueeze(1), dehors.unsqueeze(1))
        n_all.scatter_add_(1, ia.unsqueeze(1), dehors.unsqueeze(1))
        m_c = (ip==2).float()*dehors; m_d = (ip==0).float()*dehors
        expo_quand_couche += e*m_c; n_couche += m_c
        expo_quand_debout += e*m_d; n_debout += m_d
        d = p.norm(dim=-1)
        vient = (d < ARRIVE).float()*dehors
        arrive = arrive + vient; dehors = dehors*(1-vient)
        lp_tot = lp_tot + lp*dehors
        # GUIDAGE PAR POTENTIEL. Sans lui, l'agent s'enferme : ne trouvant jamais l'arrivée
        # par hasard, le seul levier qu'il voit est de baisser son exposition — il se couche,
        # sa vitesse est divisée par trois, et l'arrivée devient impossible. Récompenser les
        # MÈTRES GAGNÉS (une différence, pas une distance absolue) éclaire le chemin sans
        # déplacer la solution optimale. ⟨v1 pénalisait la distance absolue : l'agent fonçait⟩
        gagne = (d_prec - p.norm(dim=-1)) * dehors
        val_l.append(val); rec_l.append(-tarif*d_pic + 0.05*gagne)
    reste = (p.norm(dim=-1)-ARRIVE).clamp(min=0)/DEPART_COURANT
    # arriver doit payer FRANCHEMENT. Avec l'ancienne prime de 3, ne jamais arriver coûtait
    # -16,5 et arriver -2,6 : rentable en principe, mais l'écart ne guidait pas l'exploration.
    R = torch.stack(rec_l).sum(0) + arrive*15.0 - 15.0*reste
    if azi_faux: AZI = sauv
    return dict(R=R, lp=lp_tot, ent=ent_tot, val=torch.stack(val_l).mean(0), trop=trop,
                arrive=arrive, expo=expo_cum, chemin=chemin, temps=temps,
                n_post=n_post, n_all=n_all,
                e_couche=expo_quand_couche/n_couche.clamp(min=1), n_couche=n_couche,
                e_debout=expo_quand_debout/n_debout.clamp(min=1), n_debout=n_debout)

# ============ 4. ENTRAÎNEMENT — REINFORCE avec ligne de base ============
def entrainer(graine, tarif, B=2048, iters=250 if ('court' in sys.argv) else 600):
    """CURRICULUM INVERSÉ SUR LE POINT DE DÉPART.

    ⟨Fable, 03/08 : « Le chiffre qui compte n'est pas l'écart de récompense. C'est que l'agent
    libre n'est JAMAIS arrivé une seule fois. La récompense d'arrivée n'a donc jamais existé
    dans un seul gradient. »⟩

    Douze versions ont demandé à l'optimiseur de traverser une vallée : se lever coûte tout de
    suite, arriver ne paie qu'à la fin, et toute politique intermédiaire — se lever à mi-chemin —
    est pire que les deux extrêmes. Aucun gradient ne traverse ça. L'imitation n'y changeait
    rien : elle façonne les ACTIONS, pas ce que l'agent VIT.

    Ici on ne touche ni aux constantes mesurées ni à la récompense. On change SEULEMENT le
    point de naissance. À 20 m, l'agent arrive presque par accident, debout. L'arrivée devient
    l'événement fréquent, et le rampement n'a jamais le temps de devenir l'optimum local.
    On recule d'un cran dès que le palier est tenu.

    CRITÈRE D'ÉCHEC ÉCRIT AVANT : si à un rayon donné l'arrivée s'effondre et ne remonte pas
    en deux fois le budget d'itérations, la mesure a ÉCHOUÉ — et elle dira à quelle distance
    la vallée commence. C'est une mesure qui sait échouer.
    """
    global DEPART_COURANT
    torch.manual_seed(graine); np.random.seed(graine)
    pol = Politique().to(dev)
    opt = torch.optim.Adam(pol.parameters(), lr=1e-3)

    # PALIERS AFFINÉS JUSTE AU-DESSUS DU RAYON D'ARRIVÉE (40 m).
    # Le tour précédent : 20 m et 35 m tenus à 100 %, 55 m effondré à 0 %. Mais à 20 et 35 m
    # l'agent naît DANS la zone d'objectif ou à cinq mètres — il arrivait sans rien faire, ces
    # paliers ne mesuraient rien. Le premier palier qui demande un vrai déplacement (55 m, soit
    # 15 m à parcourir) échoue d'emblée. La vallée ne commence donc pas à mi-parcours : elle
    # commence dès les premiers mètres. On la découpe au pas de 3 m pour voir si la chute est
    # franche ou graduelle.
    # ---- PHASE 0 : DONNER UN CAP. Sans elle, la direction produite par le réseau est
    # aléatoire à l'initialisation — accélérer au hasard n'approche pas de l'objectif, ça ne
    # fait qu'exposer. Le gradient pousse donc à NE PAS BOUGER, et il a raison.
    # ⟨mesuré : à 42 m de départ pour 40 m de rayon d'arrivée, soit DEUX mètres à parcourir,
    #  l'agent échouait encore. Le problème n'était ni la distance ni la vallée : il ne se
    #  déplaçait pas du tout.⟩
    # Les deux curriculums ne sont pas concurrents : l'imitation donne le CAP, le rayon donne
    # l'EXPÉRIENCE DE L'ARRIVÉE. Il faut les deux, dans cet ordre.
    DEPART_COURANT = 120.0
    for it in range(120):
        idx = I_TR[torch.randint(0, len(I_TR), (B,), device=dev)]
        ang = torch.rand(B, device=dev)*2*math.pi
        p = torch.stack([torch.sin(ang), torch.cos(ang)], -1) * DEPART_COURANT
        post = torch.zeros(B, dtype=torch.long, device=dev)
        perte = 0.0
        for t in range(0, NPAS, 5):
            moi, ent = percevoir(p, post, idx)
            dr, al, po, _ = pol(moi, ent, MSK[idx])
            cible = -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)
            dr = dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)
            perte = perte + ((dr - cible)**2).sum(-1).mean()
            perte = perte + nn.functional.cross_entropy(al, torch.full((B,), 2, device=dev))
            perte = perte + nn.functional.cross_entropy(po, torch.zeros(B, dtype=torch.long, device=dev))
            p = p + cible * 16.0
        opt.zero_grad(); perte.backward()
        torch.nn.utils.clip_grad_norm_(pol.parameters(), 1.0); opt.step()
    DEPART_COURANT = 120.0
    with torch.no_grad():
        v = derouler(pol, I_VA[:256], tarif, echantillonne=False)
    print(f"    graine {graine} apres CAP : arrive {float(v['arrive'].mean()):.1%}"
          f"  chemin {float(v['chemin'].mean()):.0f} m", flush=True)

    # PALIERS RESSERRÉS. Le tour précédent : 60 et 85 m tenus à 100 %, 110 m à 12,5 % — donc
    # PROCHE du seuil, pas de l'autre côté d'un mur. Et chaque palier était tenu en exactement
    # 40 itérations, c'est-à-dire dès le premier test : il tenait sans marge. On resserre le pas
    # et on laisse plus de temps par palier.
    PALIERS = [60, 80, 95, 110, 125, 145, 170, 195, 220, 250]
    SEUIL = 0.90                 # taux d'arrivée à tenir avant de reculer
    par_palier = max(iters // 2, 150)      # deux fois plus de budget qu'au tour précédent
    journal = []
    bloque_a = None
    import copy
    # LE MEILLEUR ÉTAT EST CONSERVÉ. Le tour précédent : l'agent tenait 125 m, puis trois
    # cents itérations d'acharnement sur un palier hors de portée ont fait DIVERGER les poids
    # — verdict final rempli de « nan », politique perdue. Un palier tenu est un point de
    # reprise, pas une étape qu'on peut sacrifier.
    meilleur_etat = copy.deepcopy(pol.state_dict())
    meilleur_rayon = 0

    for rayon in PALIERS:
        DEPART_COURANT = float(rayon)
        tenu = False
        for it in range(par_palier * 2):        # deux fois le budget avant de déclarer l'échec
            idx = I_TR[torch.randint(0, len(I_TR), (B,), device=dev)]
            r = derouler(pol, idx, tarif)
            perte = -r['R'].mean()
            opt.zero_grad(); perte.backward()
            torch.nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
            opt.step()
            if it % 15 == 14:
                with torch.no_grad():
                    v = derouler(pol, I_VA[:256], tarif, echantillonne=False)
                a = float(v['arrive'].mean())
                if a >= SEUIL and it >= 30:
                    tenu = True
                    journal.append((rayon, it+1, a, float(v['expo'].mean())))
                    meilleur_etat = copy.deepcopy(pol.state_dict()); meilleur_rayon = rayon
                    print(f"    graine {graine} rayon {rayon:3d} m tenu en {it+1:4d} it"
                          f"   arrive {a:.1%}  expo {float(v['expo'].mean()):.2f}", flush=True)
                    break
                # garde-fou numérique : une perte non finie signe une divergence, on arrête
                if not math.isfinite(float(perte)):
                    print(f"    graine {graine} rayon {rayon:3d} m DIVERGENCE — retour au dernier etat sain", flush=True)
                    break
        if not tenu:
            with torch.no_grad():
                v = derouler(pol, I_VA[:256], tarif, echantillonne=False)
            a = float(v['arrive'].mean())
            journal.append((rayon, par_palier*2, a, float(v['expo'].mean())))
            print(f"    graine {graine} rayon {rayon:3d} m NON TENU   arrive {a:.1%}"
                  f"  <- LA VALLEE COMMENCE ICI", flush=True)
            bloque_a = rayon
            break

    # ON REVIENT AU DERNIER ÉTAT QUI TENAIT, et on évalue à CETTE distance-là.
    # Évaluer à 250 m une politique qui n'a jamais vu au-delà de 125 m ne mesure rien.
    pol.load_state_dict(meilleur_etat)
    DEPART_COURANT = float(max(meilleur_rayon, 60))
    print(f"    graine {graine} -> politique retenue : celle du palier {meilleur_rayon} m"
          f" (evaluation a cette distance)", flush=True)
    return pol, journal, bloque_a

class Directe:
    """référence : on va droit au but, allure et posture libres"""
    def __call__(self, p): return -p/p.norm(dim=-1,keepdim=True).clamp(min=1e-6)

print("\n" + "="*78, flush=True)
COURT = len(sys.argv) > 1 and sys.argv[1] == "court"
# MISE A L ECHELLE DU TARIF. Le risque appris est 2,7 fois moins disperse qu expo
# (ecart-type 0,088 contre 0,235, plages [0,474-0,742] contre [0,182-0,846]). Garder 1,75
# reviendrait a comparer « agent a cout fort » et « agent a cout faible » : on mesurerait
# l effet du TARIF, pas celui de la FONCTION. On multiplie donc par 0,235/0,088 = 2,67.
# C est un changement d unite, pas de structure, et il est fait AVANT de voir le resultat.
TARIFS = [4.7]
# CINQ graines, pas trois. « 2 sur 3 » s ouvrait tout seul une fois sur cinq : ce n etait
# pas une porte. A 4 sur 5, le hasard ne passe que 3 fois sur 100.
GRAINES = (1,) if COURT else (1, 2, 3, 4, 5)
resultats = {}
for tarif in TARIFS:
    for graine in GRAINES:
        t0 = time.time()
        pol, journal, bloque = entrainer(graine, tarif)
        if bloque is not None:
            print(f"    -> curriculum interrompu a {bloque} m", flush=True)
        with torch.no_grad():
            ev   = derouler(pol, I_TE, tarif, echantillonne=False)
            gel  = derouler(pol, I_TE, tarif, echantillonne=False, gel=(2,0))   # course + debout
            faux = derouler(pol, I_TE, tarif, echantillonne=False, azi_faux=True)
            dr   = derouler(pol, I_TE, tarif, echantillonne=False, force_dir=Directe())
        f = lambda x: float(x.float().mean())
        resultats[(tarif,graine)] = dict(
            arrive=f(ev['arrive']), expo=f(ev['expo']), temps=f(ev['temps']), chemin=f(ev['chemin']),
            expo_gele=f(gel['expo']), arrive_gele=f(gel['arrive']),
            expo_faux=f(faux['expo']), expo_directe=f(dr['expo']), arrive_directe=f(dr['arrive']),
            trop=f(ev['trop']),
            post=(ev['n_post'].sum(0)/ev['n_post'].sum()).tolist(),
            allure=(ev['n_all'].sum(0)/ev['n_all'].sum()).tolist(),
            e_couche=f(ev['e_couche']), e_debout=f(ev['e_debout']),
            n_couche=f(ev['n_couche']), secondes=time.time()-t0)
        r = resultats[(tarif,graine)]
        print(f"  tarif {tarif} graine {graine} : arrivé {r['arrive']:.1%} expo {r['expo']:.2f}"
              f" (gelé {r['expo_gele']:.2f}, directe {r['expo_directe']:.2f})"
              f"  postures {['%.2f'%x for x in r['post']]}  {r['secondes']:.0f}s", flush=True)

json.dump({f"{k[0]}_{k[1]}": v for k,v in resultats.items()},
          open('/mnt/data/corpus/agent_complet.json','w'), indent=2)

# ============ 5. LECTURE CONTRE LES SEUILS FIGÉS ============
print("\n" + "="*78)
print("RÉSULTATS — contre CRITERES_AGENT.md, figé avant le run\n")
for tarif in TARIFS:
    rs = [resultats[(tarif,g)] for g in GRAINES]
    m = lambda k: np.mean([r[k] for r in rs]); s = lambda k: np.std([r[k] for r in rs])
    gain_dir = (m('expo_directe')-m('expo'))/max(m('expo_directe'),1e-9)
    cout_gel = (m('expo_gele')-m('expo'))/max(m('expo'),1e-9)
    perte_faux = (m('expo_faux')-m('expo'))/max(m('expo_directe')-m('expo'),1e-9)
    print(f"TARIF {tarif}   (moyenne de 3 graines, ± écart-type)")
    print(f"  arrivée .................. {m('arrive'):.1%} ± {s('arrive'):.1%}   (directe {m('arrive_directe'):.1%})")
    print(f"  exposition ............... {m('expo'):.2f} ± {s('expo'):.2f}   (directe {m('expo_directe'):.2f}) -> {gain_dir:+.0%}")
    print(f"  ABLATION du répertoire ... {m('expo_gele'):.2f}  (arrivée {m('arrive_gele'):.1%})"
          f"  -> le geler coûte {cout_gel:+.1%}")
    print(f"  regards au hasard ........ {m('expo_faux'):.2f}  -> perd {perte_faux:.0%} de son avantage")
    print(f"  postures (debout/accr/couché) {['%.2f'%x for x in np.mean([r['post'] for r in rs],0)]}")
    print(f"  allures  (arrêt/marche/course) {['%.2f'%x for x in np.mean([r['allure'] for r in rs],0)]}")
    print(f"  exposition quand COUCHÉ {m('e_couche'):.4f}   quand DEBOUT {m('e_debout'):.4f}"
          f"   -> {'corrélé au danger' if m('e_couche')>m('e_debout')*1.15 else 'PAS corrélé'}")
    print(f"  exposition par mètre gagné {m('expo')/max(m('chemin'),1)*100:.3f}"
          f"   temps {m('temps'):.0f} pas   chemin {m('chemin'):.0f} m")
    print(f"  pas trop longs (fuite du simulateur) : {m('trop'):.2f} par épisode"
          f"  -> {'PROPRE' if m('trop') < 0.01 else 'FUITE DÉTECTÉE'}")
    print()

print("="*78)
print("VERDICT (tarif 1,75)\n")
if not rs: sys.exit(0)
rs = [resultats[(1.75,g)] for g in GRAINES] if 1.75 in TARIFS else []
m = lambda k: np.mean([r[k] for r in rs])
c1 = m('arrive') >= m('arrive_directe') - 0.02
c2 = m('expo') < m('expo_directe')
c4 = (m('expo_gele')-m('expo'))/max(m('expo'),1e-9) >= 0.02
c5 = m('e_couche') > m('e_debout')*1.15
c3 = (m('expo_faux')-m('expo'))/max(m('expo_directe')-m('expo'),1e-9) >= 0.5
for n,(lib,ok) in enumerate([("1. arrive autant que l'approche directe",c1),
                             ("2. s'expose moins que l'approche directe",c2),
                             ("3. perd la moitié de son avantage sur regards faux",c3),
                             ("4. ABLATION : geler le répertoire coûte >= 2 %",c4),
                             ("5. « couché » corrélé à une exposition élevée",c5)],1):
    print(f"  {'PASSE ' if ok else 'ÉCHOUE'}  {lib}")
print()
if c4 and c5:
    print("  L'AGENT A DÉCOUVERT SON RÉPERTOIRE : le geler coûte, et il s'en sert quand il faut.")
else:
    print("  LE RÉPERTOIRE EST DÉCORATIF sur ce monde — l'agent n'a pas trouvé quoi en faire.")
print("\n  RAPPEL : ce simulateur est le nôtre. Aucun verdict avant un banc Arma.")
