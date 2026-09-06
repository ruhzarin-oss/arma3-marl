"""assault_terrain — banc d'essai PERCEPTION (G-perc-0). Un groupe ATTAQUANT manœuvre vers un objectif
DÉFENDU à travers le terrain. Le défilé (approche couverte) réduit l'exposition au feu -> lire le terrain
et choisir l'approche est un LEVIER récompensé. Remplace le KOTH (terrain non exploitable là-bas).
100% GPU vectorisé, réutilise terrain_gpu. obs inclut les variables de perception (G-perc-0)."""
import math
import torch
import terrain_gpu as TG
import numpy as np


class AssaultTerrain:
    def __init__(self, num_envs=2048, A=4, D=4, R_spawn=170.0, terr_R=200.0, terr_G=64, relief=35.0,
                 move=14.0, fire_range=110.0, hit=0.06, secure_r=25.0, max_steps=60, dmg_dead=0.7,
                 grid_obs=False, gridK=8, gridspan=80.0, team_obs=False, role_obs=False,
                 shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2,
                 replica=False, replica_path="replica.npz", device="cuda:0", seed=0, postures=False, flat_los=False,
                 couvert_directionnel=False,   # ⚠️ CHIRURGIE 16/08 : retire le multiplicateur scalaire
                                               # `1 - 0,7*incover`. La protection ne vient alors que de `los`,
                                               # directionnel par construction. Eteint par defaut : le monde
                                               # existant ne bouge pas tant qu on ne l allume pas.
                 overwatch=False, ow_expo=0.05, hull=False, ow_dmg=0.3, ow_tofail=0.5, expose_lut=None,
                 emergent_expo=False, death_pen=0.4, suffer_pen=1.1, win_bonus=1.0, kill_w=1.5, arma_obs=False, obs_dcover_arma=None, obs_sans_slope=None,
                 secure_task=False, approach_w=0.2, secure_only=False, supp_kill=1.0,
                 def_arc=math.pi, def_line=False, def_spread=1.0, def_rline=35.0, def_rand=False, nav_around=False, flank_kill=0.0,
                 arrivee_segment=False, los_tous=False, frein_feu=0.0, alerte=False, courbe=None, tir_par_pas=None, sec_par_pas=None, degat_par_impact=None, arc_obs=False, champ_risque=False, champ_R=35.0, stress=False, mission="assaut", arc_latence_s=None, supp_residuel=None, supp_persist=0.0, cible_unique=True, feu_sur_connu=0.0, feu_de_zone=0.0, relief_stratis=False, canal_cwr=None):
        # ---- COURBE N2 : LA SUPPRESSION MESUREE SUR ARMA (28/07) ----
        # `supp_residuel` = ce qu'il RESTE de capacite de nuire sous suppression pleine.
        # Mesure : 0.08 (cadence x0,57 x precision x0,14). None = ancien tout-ou-rien.
        # `supp_persist` = part de la suppression reportee au pas suivant. Arma : la cadence
        # revient a ~89 % en 2 s pour un pas de 3,28 s, donc le report est FAIBLE.
        # UN DEFENSEUR TIRE SUR UN HOMME. Sans ca, un flanqueur isole encaisse le feu de
        # trois defenseurs dans le meme pas de 3,28 s : pire pas 0,471 pour un seuil de
        # mort a 0,70. Mesure du 28/07. Defaut False = ancien monde.
        self.cible_unique = bool(cible_unique)
        # --- R1 : L ARRIVEE SE TESTE SUR LE SEGMENT, PAS SUR LE POINT ---------------
        # Mesure du 30/08 : au palier 30 m la doctrine du gymnase rend 81,3 % la ou Arma
        # rend 100 %. Bras d attribution : meme monde, rayon porte de 6 a 15 m -> 100,0 %.
        # La cause n est pas la physique, c est que l arrivee n etait constatee qu aux DEUX
        # BOUTS d un pas de 14 m : un objectif de 6 m situe AU MILIEU du pas etait traverse
        # sans etre vu. C est le tunneling classique des moteurs de collision.
        # Ici on teste l intersection du SEGMENT parcouru avec le disque d objectif.
        # ETEINT PAR DEFAUT : aucune mesure passee n est reecrite.
        self.arrivee_segment = bool(arrivee_segment)
        # --- LE FEU SUIT LA POSITION CONNUE -------------------------------------------
        # C EST LE DERNIER GRAND ECART AVEC ARMA. Ici, rompre la ligne de vue coupait le feu
        # AU PAS MEME : se glisser derriere une crete rendait invulnerable instantanement.
        # Dans Arma le camp a une MEMOIRE — `knowsAbout` ne decroit pas (mesure : aucune
        # decroissance en 300 s) — et les defenseurs continuent de battre la derniere
        # position connue. C est pour cela qu ETRE VU TUE 2x PLUS FORT QUE VOIR NE PROTEGE :
        # +75 % de mortalite sur 563 000 observations, effet CROISSANT avec la distance.
        # `feu_sur_connu` = part du feu qui porte encore sur un homme DEJA VU mais
        # momentanement hors de vue. 0 = ancien monde, ou le couvert est un interrupteur.
        # Il se CALIBRE sur le verdict des +75 %, jamais au jugement.
        # --- LE FEU DE ZONE ------------------------------------------------------------
        # MESURE, ET ELLE EST BRUTALE : dans ce monde, un homme qui n est PAS vu
        # geometriquement au pas courant a une mortalite EXACTEMENT NULLE. Pas faible : nulle.
        # Le couvert n est pas « trop protecteur », c est un INTERRUPTEUR ABSOLU.
        # Arma ne connait pas ca : etre vu y multiplie la mortalite par 1,75 seulement
        # (563 000 observations) — les jamais-vus y meurent donc, a 4/7 du taux des vus.
        #
        # ⚠️ ET C EST `cible_unique` QUI TIENT L INTERRUPTEUR. La selection de cible exige
        # `los > 0.5` : un homme jamais vu n est JAMAIS designe, donc `tir` vaut zero pour
        # lui, donc aucun terme multiplie par `tir` ne peut l atteindre. Un premier essai qui
        # planchonnait `los` DANS les termes de tir est reste parfaitement inerte — memes
        # comptes a la dizaine pres sur neuf valeurs du bouton. Le feu de zone n est pas du
        # tir vise attenue : c est un terme SEPARE, qui ne passe pas par la designation.
        #
        # Il ne touche PAS `exposed` : le prix de la manoeuvre reste ce que l agent voit
        # vraiment, sinon on lui apprendrait que se cacher ne sert a rien.
        # Il se CALIBRE sur le verdict des +75 %, jamais au jugement.
        self.feu_de_zone = float(feu_de_zone)
        if not (0.0 <= self.feu_de_zone <= 1.0):
            raise ValueError("feu_de_zone est une fraction du feu vise, versee sans designation")
        self.feu_sur_connu = float(feu_sur_connu)
        if not (0.0 <= self.feu_sur_connu <= 1.0):
            raise ValueError("feu_sur_connu est une fraction du feu qui suit un homme connu")
        self.supp_residuel = supp_residuel
        self.supp_persist = float(supp_persist)
        if supp_residuel is not None and not (0.0 <= supp_residuel <= 1.0):
            raise ValueError("supp_residuel est une fraction de capacite de nuire : 0.08 mesure sur Arma")
        if not (0.0 <= self.supp_persist < 1.0):
            raise ValueError("supp_persist est une fraction reportee : 0 = aucune persistance")

        # ---- COURBE DE TOUCHER MESUREE SUR ARMA (chantier 1) ----
        # Avant : hit=0.06 partout, plus rien au-dela de fire_range. Une falaise la ou Arma
        # a une pente — donc un monde ou se rapprocher ne coute rien, ou manoeuvrer ne peut
        # PAS avoir de sens. C'est ce parametre qui a refuse de transferer trois fois.
        #
        # LA CONVERSION N'EST PAS UN DETAIL : Arma compte en SECONDES et en BALLES, le
        # sandbox en PAS. Passer de l'un a l'autre demande deux grandeurs qu'on ne doit
        # surtout pas choisir :
        #   sec_par_pas = duree reelle d'un pas de sandbox (move / vitesse mesuree sur Arma)
        #   tir_par_pas = balles tirees par un defenseur pendant un pas (mesure sur Arma)
        # Elles sont exposees ici, VIDES par defaut, en attente de leur mesure. Fournir une
        # courbe sans elles leve une erreur : mieux vaut un arret qu'un chiffre invente.
        self.courbe = None
        self.tir_par_pas = tir_par_pas
        self.sec_par_pas = sec_par_pas
        self.degat_par_impact = degat_par_impact
        # ARC PERCU : l'agent voit-il OU REGARDE le defenseur le plus proche ?
        # Sans ca, son observation est identique dans l'angle mort et dans la ligne
        # de mire — seuls les degats different. Il ne peut pas contourner ce qu'il
        # ne percoit pas. Defaut False = comportement historique inchange.
        self.arc_obs = arc_obs
        # CHAMP DE RISQUE : le PRIX du terrain dans les 8 directions, a champ_R metres.
        # Mesure : l agent contourne a 132 m quand le crochet le fait a 184 m — il
        # manoeuvre au tarif fort faute de savoir, de loin, ou est le couloir bon marche.
        self.champ_risque = champ_risque; self.champ_R = champ_R
        # AXE DU STRESS : l audace divise le prix percu du terrain. Le seul mecanisme
        # de SIROCCO qui fasse ENTRER — sans lui le systeme ne sait que se proteger.
        self.stress = stress; self.etat = None
        # ARC DYNAMIQUE : le defenseur se REORIENTE vers la menace apres une latence
        # mesuree sur Arma (~3 s, soit un pas). Sans ca le cone est un mur permanent,
        # et le flanc gagne pour une raison que le vrai jeu n a pas.
        self.arc_latence_s = arc_latence_s
        self.arc_latence_pas = None
        if arc_latence_s is not None:
            if sec_par_pas is None:
                raise ValueError("arc_latence_s sans sec_par_pas : la latence est en "
                                 "SECONDES, un pas n a de duree que si on la mesure.")
            self.arc_latence_pas = max(1, int(round(float(arc_latence_s) / float(sec_par_pas))))
        if stress:
            if not champ_risque:
                raise ValueError("stress sans champ_risque : l audace n a rien a ponderer. "
                                 "Elle multiplie l exposition qu on accepte de payer ; sans "
                                 "champ, ce prix n existe pas dans l observation.")
            if sec_par_pas is None:
                raise ValueError("stress sans sec_par_pas : les demi-vies hormonales sont "
                                 "en SECONDES. Meme regle que le reste.")
            from sirocco_etat import EtatGlobal
            self.etat = EtatGlobal(num_envs, device, mission=mission, sec_par_pas=sec_par_pas)
        if courbe is not None:
            import json as _json
            _c = courbe if isinstance(courbe, dict) else _json.load(open(courbe))
            if _c.get('alertes'):
                raise ValueError('courbe REFUSEE par son propre verificateur : %s' % _c['alertes'])
            if tir_par_pas is None or degat_par_impact is None:
                raise ValueError('courbe fournie sans tir_par_pas / degat_par_impact : '
                                 'ces conversions doivent etre MESUREES sur Arma, pas devinees')
            _d = [float(x) for x in _c['distances']]
            _t = [[_c['pct_au_but'][str(int(dd))][pi] / 100.0 for dd in _d]
                  for pi in range(len(_c['postures']))]
            self._c_dist = torch.tensor(_d, device=device)
            self._c_p = torch.tensor(_t, device=device)   # [posture, distance] : proba PAR BALLE
            self.courbe = _c
        self.def_arc = def_arc   # ARC DE TIR défenseur (rad, demi-angle). π = 360° (défaut, rien ne change). Petit = front dirigé -> flanc aveugle (banc FIBUA)
        self.def_line = def_line; self.def_spread = def_spread; self.def_rline = def_rline   # LIGNE défensive : défenseurs étalés en arc devant l'objectif (flanquable par le bout)
        # GARDE-FOU (2026-07-28) : def_rand TIRE arc/spread/rline au hasard et IGNORE les
        # valeurs passees. Trois bancs ont tourne des semaines en croyant piloter un arc fixe.
        # On refuse desormais le silence : soit on randomise, soit on regle, jamais les deux.
        if def_rand:
            _forces = []
            if abs(float(def_arc) - math.pi) > 1e-9:  _forces.append("def_arc")
            if abs(float(def_spread) - 1.0) > 1e-9:   _forces.append("def_spread")
            if abs(float(def_rline) - 35.0) > 1e-9:   _forces.append("def_rline")
            if _forces:
                import warnings
                warnings.warn(
                    "def_rand=True IGNORE " + ", ".join(_forces) + " : la geometrie defensive "
                    "est tiree au hasard par episode. Passer def_rand=False pour que ces "
                    "valeurs soient reellement appliquees.", RuntimeWarning, stacklevel=2)
        self.def_rand = def_rand   # RANDOMISE la géométrie défensive par épisode (arc/spread/rline/décentrage) -> pas de mémorisation « toujours à gauche » (condition Fable #1)
        self.nav_around = nav_around   # NAV CONSCIENTE DES MURS : cap tapant un mur -> longe (angle libre le plus proche du but), au lieu de s'arrêter net (= doMove Arma). Dissout la tension couvert<->traversée
        self.flank_kill = flank_kill   # FEU DE FLANC : dégâts/pas infligés à un défenseur depuis SON angle mort (il ne riposte pas) ; 0 = désactivé (mur balistique partout)
        # ─── LE RELIEF SUIT LA CARTE, il n est plus une constante ───────────────────
        # Depot du 12/08 : `gen_terrain` normalisait CHAQUE carte a la meme amplitude, donc
        # toutes etaient egalement accidentees. On tire desormais `relief` par environnement
        # dans la distribution MESUREE de Stratis (394 points, formule du gymnase des deux
        # cotes). La pente etant lineaire en `relief`, reproduire les reliefs reproduit les
        # pentes — par construction, pas par reglage. Le facteur d echelle vient du rapport
        # des medianes, il n est pas choisi.
        self.relief_stratis = bool(relief_stratis)
        self._pentes_stratis = None
        if self.relief_stratis:
            import numpy as _np
            _p = _np.load("/home/younes/arma3-marl/pentes_stratis.npy")
            self._pentes_stratis = torch.tensor(_p, device=device, dtype=torch.float32)
        self.N = num_envs; self.A = A; self.D = D; self.R_spawn = R_spawn
        self.terr_R = terr_R; self.terr_G = terr_G; self.relief = relief
        # FREIN SOUS LE FEU (2026-07-30). Defaut 0 = comportement historique, non regressif.
        # Constat : chez le juge externe, les hommes MEURENT EN CHEMIN, partout entre 60 et
        # 130 m, ecart-type de la distance d arret 15 m. Ici la vitesse ne dependait que de
        # l action — jamais du feu recu. Le gymnase etait donc structurellement incapable
        # de representer une halte sous le feu, et annoncait 94,6 % la ou le juge donne 0 %.
        # Ce coefficient se calibre SUR L ISSUE, pas au jugement.
        # MODELE D ALERTE MESURE SUR ARMA (2026-07-30, CRITERES_ALERTE_GYM 417252605cfd14d1).
        # Le gymnase modelisait la visibilite par un CONE DE CAMERA : vu a l infini dans l arc,
        # invisible en dehors. Contourner rendait donc litteralement invisible, d ou 96 % de
        # reussite au debordement quand le juge externe en donne 0 %.
        # Arma dit l inverse : on voit a 60 m DANS TOUTES LES DIRECTIONS, rien au-dela de 100 m.
        #   detection passive : 4,00 a 30 m | 1,72 a 60 m | 0,00 a partir de 100 m
        #   trois tirs depuis l invisibilite : +1,50 sur TOUT LE GROUPE en 3 s
        #   aucune decroissance en 300 s -> l alerte se depense, elle ne se recupere jamais
        self.alerte = bool(alerte)
        self.ALERTE_MAX = 4.0
        self.ALERTE_PAR_TIR = 0.5      # 1,50 mesure pour trois tirs
        self.R_VUE_PLEINE = 30.0       # 4,00 mesure
        self.R_VUE_NULLE = 100.0       # 0,00 mesure
        self.COUCHE_INVISIBLE_M = 120.0   # banc de l angle mort : couche invisible au-dela
        self.los_tous = los_tous       # exposition a TOUS les defenseurs vivants
        self.frein_feu = float(frein_feu)
        self._frein_pret = False   # last_exposed n existe qu apres le premier pas
        self.move = move; self.fire_range = fire_range; self.hit = hit; self.secure_r = secure_r
        self.max_steps = max_steps; self.dmg_dead = dmg_dead; self.dev = device; self.scale = terr_R
        self.replica = replica
        if replica:
            _R = np.load(replica_path)
            self._solid = torch.tensor(_R["solid"].astype("float32"), device=device)
            self._elevR = torch.tensor(_R["elev"].astype("float32"), device=device)
            self._solidhR = torch.tensor(_R["solidh"].astype("float32"), device=device) if "solidh" in _R.files else torch.zeros_like(self._solid)
            self._lowhR = torch.tensor(_R["lowh"].astype("float32"), device=device) if "lowh" in _R.files else torch.zeros_like(self._solid)
            try:   # POINT 5 : DISTANCE-AU-BÂTI (transformée de distance de _solid) = un vrai signal de couvert QUI VARIE (avant : dcover=0)
                from scipy import ndimage
                self._dcoverR = torch.tensor(ndimage.distance_transform_edt(_R["solid"].astype("float32") < 0.5).astype("float32"), device=device)
            except Exception:
                self._dcoverR = None
            self.terr_G = int(_R["GS"]); self.terr_R = float(_R["W"]); self.scale = self.terr_R
            self.R_spawn = min(R_spawn, self.terr_R - 25.0)

        self.g = torch.Generator(device=device).manual_seed(seed)
        self.postures = postures
        self.flat_los = flat_los
        self.couvert_directionnel = couvert_directionnel
        self.overwatch = overwatch; self.ow_expo = ow_expo
        self.hull = hull; self.ow_dmg = ow_dmg; self.ow_tofail = ow_tofail; self.emergent_expo = emergent_expo
        self.death_pen = death_pen; self.suffer_pen = suffer_pen; self.win_bonus = win_bonus; self.kill_w = kill_w   # knobs récompense (défauts = comportement historique)
        self.secure_task = secure_task; self.approach_w = approach_w   # TÂCHE SÉCURISER : victoire = atteindre le FOB (comme Arma), pas juste tuer par le feu ; clôture = moteur
        self.secure_only = secure_only   # CALIBRATION Arma : la SEULE victoire = atteindre le FOB (on ne gagne PLUS en nettoyant au feu)
        self.supp_kill = supp_kill       # efficacité du feu attaquant vs défenseurs (Arma : ~0 contre des retranchés -> forcer à CLORE)
        self.arma_obs = arma_obs
        # ─── ABLATION (12/08). `arma_obs` changeait DEUX choses d un coup : il normalise
        # `dcover` comme le pont (÷30 cape) ET il retire `slope`. La chute de 57,7 % a 29,9 %
        # n avait donc aucune cause identifiee — on ne pouvait pas dire lequel des deux la
        # portait. ⟨Fable : « ton experience est confondue ; ablation, chaque changement seul »⟩
        # Les deux effets sont desormais pilotables separement ; `arma_obs` reste leur
        # conjonction, donc aucun appel existant ne change de comportement.
        self.obs_dcover_arma = self.arma_obs if obs_dcover_arma is None else bool(obs_dcover_arma)
        self.obs_sans_slope = self.arma_obs if obs_sans_slope is None else bool(obs_sans_slope)   # obs ALLÉGÉE cheap-depuis-Arma (sans pente, sans coque) pour le pont SHAMAL->Arma
        self._expose_lut = torch.tensor(expose_lut if expose_lut is not None else [1.0, 0.5, 0.2], device=device)   # HULL-DOWN : profil de corps (debout/accroupi/couche) = fraction touchable
        self.n_actions = (13 if postures else 10)  # 0-7 caps, 8 HOLD, 9 SUPPRESS ; 10-12 postures (debout/accroupi/couche)
        if postures: self._eye_lut = torch.tensor([1.7, 1.0, 0.3], device=device)   # hauteur d'oeil par posture
        self.grid_obs = grid_obs; self.gridK = gridK; self.gridspan = gridspan; self.team_obs = team_obs; self.role_obs = role_obs
        self.shell_obs = shell_obs; self.shellK = shellK; self.shell_R = shell_R
        self.suffer = suffer; self.D_min = D_min
        self.obs_dim = (8 if arma_obs else 9) + (2 * gridK * gridK if grid_obs else 0) + (4 if team_obs else 0) + (2 if role_obs else 0) + ((shellK + 1) if shell_obs else 0) + (2 if suffer else 0) + (3 if postures else 0)   # +grille +coequipiers +ROLE +COQUE +SUFFER +POSTURE
        # ─── EQUATION 1 : LE CANAL DE DETECTION DE `Target.cpp` (CWR/Poseidon, RV1) ───
        # Ce que ca change, et RIEN D AUTRE : la designation de cible passe de
        # `los > 0.5` (interrupteur binaire) a `sideAccuracy >= 1.5` (canal continu).
        # Pourquoi : dans la source, le couvert MULTIPLIE la vue, l ouie le traverse a
        # 90 %, et l ouie seule plafonne a 1,4 contre un seuil de camp a 1,5 — elle dit
        # « quelque chose est la », jamais « c est un ennemi ». Le gymnase, lui, rendait
        # la mortalite des jamais-vus EXACTEMENT NULLE ; Arma 3 mesure +75 %, pas l infini.
        # ⚠️ RV1 N EST PAS RV3 : c est une HYPOTHESE, une nuit Arma 3 la confirme ou la tue.
        # ETEINT PAR DEFAUT. `MONDE_ARMA` ne bouge pas : la batterie gelee n est pas touchee.
        self.canal = None
        if canal_cwr is not None:
            import canal_cwr as _CANAL
            self._CANAL = _CANAL
            # `provisoire()` porte deja la cle `mesure` : on ne le revalide pas, il a crie.
            self.canal = dict(canal_cwr) if "mesure" in canal_cwr else _CANAL.constantes(**canal_cwr)
            # Le canal a besoin d une FRACTION de corps visible — l analogue de
            # `Visibility(brain, ai)`. Sans replique, le gymnase ne sait produire qu un
            # `los` BINAIRE (terrain_gpu.los_clear rend 0 ou 1) et l equation perd son
            # objet : c est le mur 2,5D, pas un reglage. Donc on refuse.
            if not (self.replica and self.emergent_expo):
                raise ValueError(
                    "canal_cwr exige replica=True ET emergent_expo=True : l equation 1 porte sur "
                    "une FRACTION de corps visible, et sans replique le gymnase n a qu un los BINAIRE")
            if not self.cible_unique:
                raise ValueError("canal_cwr remplace la porte de designation de `cible_unique` : "
                                 "l activer sans cible_unique ne changerait rien (module inerte)")
            # ─── L AUTRE MOITIE : LES DEUX HORLOGES DE LA LOI DE TIR ───
            # Arma compte en SECONDES, le gymnase en PAS : aucune duree ne se recopie.
            self.canal_mem_pas = _CANAL.en_pas(_CANAL.MEM_TIR_S, sec_par_pas)       # 10 s
            self.canal_verrou_pas = _CANAL.en_pas(_CANAL.FIRE_VALID_S, sec_par_pas)  # 15 s
            # `feu_sur_connu` etait une FRACTION libre a calibrer. La source dit que ce
            # n en est pas une : c est une FENETRE de 10 s. Deux mecanismes pour une seule
            # grandeur, c est le mode d echec de la calibration marginale.
            if self.feu_sur_connu > 0.0:
                raise ValueError(
                    "canal_cwr REMPLACE `feu_sur_connu` : la source en fait une fenetre de "
                    "%.0f s (%d pas), pas une fraction. Mettre feu_sur_connu=0.0."
                    % (_CANAL.MEM_TIR_S, self.canal_mem_pas))
            if self.feu_de_zone > 0.0:
                # `posError > 2*indirectHitRange` ecarte l arme : pour un FUSIL (rayon ~0)
                # une position connue a l oreille est INTIRABLE. Le feu de zone n existe
                # donc que pour une arme a rayon d effet — que le gymnase ne modelise pas.
                raise ValueError(
                    "canal_cwr : `feu_de_zone` n est licite que pour une arme A RAYON D EFFET "
                    "(la source ecarte l arme si posError > 2*indirectHitRange). Le gymnase "
                    "n en modelise aucune : mettre feu_de_zone=0.0")
        self._reset(torch.arange(num_envs, device=device))

    def _reset(self, idx):
        n = idx.numel(); d = self.dev
        if not hasattr(self, "apx"):
            N, A, D = self.N, self.A, self.D
            self.apx = torch.zeros(N, A, device=d); self.apy = torch.zeros(N, A, device=d); self.admg = torch.zeros(N, A, device=d)
            self.dpx = torch.zeros(N, D, device=d); self.dpy = torch.zeros(N, D, device=d); self.ddmg = torch.zeros(N, D, device=d)
            self.d_attente = torch.zeros(N, D, device=d)   # pas ecoules depuis qu une menace hors cone est perceptible
            self.d_ouvert = torch.zeros(N, D, dtype=torch.bool, device=d)   # sursis ecoule -> le cone ne restreint plus
            self.dface = torch.zeros(N, D, device=d)   # azimut de la FACE de chaque défenseur (arc de tir centré dessus)
            self._dfarc = torch.full((N, 1), math.pi, device=d)   # arc de tir PAR ENV (demi-angle, rad) -> randomisable
            self.dsupp = torch.zeros(N, D, device=d); self.t = torch.zeros(N, dtype=torch.long, device=d)
            self.last_dmg_in = torch.zeros(N, self.A, device=d)
            # UN SEUL compteur par groupe defenseur : la propagation mesuree est
            # instantanee et totale, les quatre defenseurs alertes en trois secondes.
            self.alerte_niv = torch.zeros(N, device=d)
            self.posture = torch.zeros(N, A, dtype=torch.long, device=d)
            # cliquet PAR ATTAQUANT : a-t-il deja ete vu ? monotone, comme l alerte de camp.
            self.a_connu = torch.zeros(N, A, device=d)
            # ─── LOI DE TIR : `lastSeen` (par ATTAQUANT, partage par le groupe defenseur,
            # comme le `Target` de RV1 qui est porte par l AIGroup) et le verrou de cible
            # (par DEFENSEUR). -1e9 = jamais vu, et ce n est pas 0 : au pas 0 un homme
            # jamais vu serait « vu a l instant ».
            self.a_dernier_vu = torch.full((N, A), -1e9, device=d)
            self.d_cible = torch.full((N, D), -1, dtype=torch.long, device=d)
            self.d_verrou = torch.zeros(N, D, dtype=torch.long, device=d)
            self.prev_d = torch.zeros(N, device=d)
            # REVUE 17/08 : distance GELEE a la mort. Sans elle, `cur` etait une moyenne
            # sur les SURVIVANTS : perdre l homme de queue faisait baisser la moyenne et
            # etait paye comme une progression, et une escouade ANEANTIE (denominateur
            # ramene a 1 par clamp) etait comptee A L OBJECTIF.
            self._dlast = torch.zeros(N, A, device=d)
            for nm in ("hm", "slope", "cover", "dcover"):
                setattr(self, nm, torch.zeros(N, self.terr_G, self.terr_G, device=d))
        if self.replica:
            self.hm[idx] = self._elevR; self.cover[idx] = self._solid
            self.slope[idx] = 0.0
            self.dcover[idx] = self._dcoverR if getattr(self, "_dcoverR", None) is not None else 0.0   # POINT 5 : vrai couvert variable
        else:
            # ATTENTION : PAS DE TIRAGE DU RELIEF PAR CARTE. Premiere version : je tirais
            # `relief` dans la distribution des pentes de Stratis — et j appliquais donc la
            # variation DEUX FOIS, puisque chaque carte a deja son propre etalement interne.
            # Mesure : le gymnase s etale de x0,26 a x2,68 autour de sa mediane, Stratis de
            # x0,00 a x2,59. La variete etait DEJA la. Resultat : p99 a plus 46 pour cent.
            # Ce qu il fallait : un FACTEUR D ECHELLE (mediane de Stratis sur mediane du
            # gymnase = 0,408/0,563 = 0,725) et de VRAIES PLAINES, que le bruit lisse ne sait
            # pas produire. Les deux sont MESURES, aucun n est choisi.
            _rel, _plat = self.relief, 0.0
            if self.relief_stratis:
                _rel = self.relief * 0.725
                _plat = 0.071
            T = TG.gen_terrain(n, self.terr_G, d, self.g, relief=_rel, part_plate=_plat)
            for nm in ("hm", "slope", "cover", "dcover"):
                getattr(self, nm)[idx] = T[nm]
        if getattr(self, "fixed_th", None) is not None:                        # AXE FIXE (carte-village dessinée : le décor est aligné sur une approche donnée)
            th = torch.full((n,), float(self.fixed_th), device=d)
        else:
            th = torch.rand(n, generator=self.g, device=d) * 2 * math.pi       # AXE DE MENACE : azimut d'où vient l'escouade (calculé tôt pour orienter la défense)
        if self.def_line:
            # LIGNE défensive : D défenseurs étalés sur un arc ±spread AUTOUR de l'axe de menace, à rline mètres DEVANT l'objectif.
            # L'objectif (origine) est DERRIÈRE la ligne. Chaque défenseur fait face vers l'extérieur -> contourner le BOUT = angle mort.
            if self.def_rand:   # RANDOMISE la géométrie par env (Fable #1) : le cerveau lit le dispositif, ne mémorise pas un côté
                arc = (40 + torch.rand(n, 1, generator=self.g, device=d) * 30) * math.pi / 180.0     # U(40°,70°)
                spread = (10 + torch.rand(n, 1, generator=self.g, device=d) * 20) * math.pi / 180.0   # U(10°,30°)
                rline = 30 + torch.rand(n, 1, generator=self.g, device=d) * 15                        # U(30,45) m
                coff = (torch.rand(n, 1, generator=self.g, device=d) * 2 - 1) * (25 * math.pi / 180)  # DÉCENTRAGE U(-25°,25°) : l'escouade n'arrive pas toujours pile au centre
            else:
                arc = torch.full((n, 1), float(self.def_arc), device=d)
                spread = torch.full((n, 1), float(self.def_spread), device=d)
                rline = torch.full((n, 1), float(self.def_rline), device=d); coff = torch.zeros(n, 1, device=d)
            center = th[:, None] + coff                                                        # (n,1) azimut du centre de la ligne
            frac = (torch.arange(self.D, device=d).float() / max(self.D - 1, 1) - 0.5) * 2.0   # (D,) -1..1
            daz = center + frac[None, :] * spread                                              # (n,D) azimuts étalés
            self.dpx[idx] = rline * torch.sin(daz); self.dpy[idx] = rline * torch.cos(daz)
            if hasattr(self, "dface"): self.dface[idx] = daz; self._dfarc[idx] = arc            # face extérieure + arc PAR ENV
        else:
            dang = torch.arange(self.D, device=d).float() / self.D * 2 * math.pi   # defenseurs en anneau autour de (0,0)
            self.dpx[idx] = 12.0 * torch.cos(dang)[None]; self.dpy[idx] = 12.0 * torch.sin(dang)[None]
            if hasattr(self, "dface"): self.dface[idx] = th[:, None]               # anneau : tous face à l'axe de menace
        if self.replica:
            for _ in range(20):
                _dw = self._sample_solid(self.dpx[idx], self.dpy[idx]) > 0.5
                if not bool(_dw.any()): break
                _jx = (torch.rand_like(self.dpx[idx]) * 2 - 1) * 10.0
                _jy = (torch.rand_like(self.dpy[idx]) * 2 - 1) * 10.0
                self.dpx[idx] = torch.where(_dw, (self.dpx[idx] + _jx).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpx[idx])
                self.dpy[idx] = torch.where(_dw, (self.dpy[idx] + _jy).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpy[idx])
        self.ddmg[idx] = 0.0; self.dsupp[idx] = 0.0
        if hasattr(self, "d_attente"): self.d_attente[idx] = 0.0
        if hasattr(self, "d_ouvert"): self.d_ouvert[idx] = False
        if getattr(self, "etat", None) is not None: self.etat.reset(idx)
        if self.suffer:
            nact = torch.randint(self.D_min, self.D + 1, (n,), device=d)         # nb defenseurs ACTIFS par env
            deact = (torch.arange(self.D, device=d)[None] >= nact[:, None])       # True = desactive
            self.ddmg[idx] = deact.float()                                        # desactives = deja neutralises
        sx = self.R_spawn * torch.sin(th); sy = self.R_spawn * torch.cos(th); ar = torch.arange(self.A, device=d).float()   # attaquants au bord, sur l'axe de menace th
        self.apx[idx] = sx[:, None] + (ar % 2) * 6 - 3; self.apy[idx] = sy[:, None] + (ar - 1) * 6; self.admg[idx] = 0.0
        self.posture[idx] = 0
        if hasattr(self, 'alerte_niv'):
            self.alerte_niv[idx] = 0.0
        if hasattr(self, 'a_connu'):
            self.a_connu[idx] = 0.0
        if hasattr(self, 'a_dernier_vu'):
            self.a_dernier_vu[idx] = -1e9
            self.d_cible[idx] = -1
            self.d_verrou[idx] = 0
        if self.replica:
            for _ in range(10):
                _w = self._sample_solid(self.apx[idx], self.apy[idx]) > 0.5
                if not bool(_w.any()): break
                self.apx[idx] = torch.where(_w, self.apx[idx] * 0.92, self.apx[idx])
                self.apy[idx] = torch.where(_w, self.apy[idx] * 0.92, self.apy[idx])
        self.t[idx] = 0
        self.prev_d[idx] = torch.sqrt(self.apx[idx] ** 2 + self.apy[idx] ** 2).mean(1) / self.scale
        self._dlast[idx] = torch.sqrt(self.apx[idx] ** 2 + self.apy[idx] ** 2) / self.scale
        if not hasattr(self, "_prev_dk"):
            self._prev_dk = torch.zeros(self.N, device=d); self.last_supp = torch.zeros(self.N, self.A, device=d)
            ar = torch.arange(self.A, device=d)
            self.role = (ar >= self.A // 2).long()[None].expand(self.N, self.A).contiguous()   # OFFICIER : 1ere moitie=APPUI(0), 2e=ASSAUT(1)
        self._prev_dk[idx] = (self.ddmg[idx] >= self.dmg_dead).float().sum(1) / self.D; self.last_supp[idx] = 0.0

    def reset(self): return self._obs()
    def _p_balle(self, dist, posture=None):
        """Probabilite de toucher PAR BALLE a une distance quelconque, interpolee dans la
        courbe Arma. Au-dela de la derniere distance mesuree on prolonge la derniere pente
        jusqu'a zero : on n'invente pas de palier, et on ne remet pas de falaise."""
        d = self._c_dist
        plat = dist.reshape(-1)
        i = torch.clamp(torch.searchsorted(d, plat.contiguous()), 1, len(d) - 1)
        d0 = d[i - 1]; d1 = d[i]
        f = ((plat - d0) / (d1 - d0)).clamp(0.0, 1.0)
        if posture is None:
            p0 = self._c_p[0][i - 1]; p1 = self._c_p[0][i]
        else:
            rows = self._c_p.index_select(0, posture.reshape(-1).long())
            p0 = rows.gather(1, (i - 1).unsqueeze(1)).squeeze(1)
            p1 = rows.gather(1, i.unsqueeze(1)).squeeze(1)
        out = p0 + (p1 - p0) * f
        au_dela = plat > d[-1]
        if bool(au_dela.any()):
            pente = ((self._c_p[..., -2] - self._c_p[..., -1]).clamp(min=0.0).max()
                     / (d[-1] - d[-2]))
            out = torch.where(au_dela, (out - pente * (plat - d[-1])).clamp(min=0.0), out)
        return out.reshape(dist.shape)

    def _champ_danger(self, K=8):
        """Pour chacune des K directions : le danger qu on subirait a champ_R metres de la.
        On somme, sur les defenseurs VIVANTS, la probabilite de toucher a cette distance,
        filtree par la ligne de vue et par l arc de tir. C est le PRIX du terrain — pas
        une consigne : le moins cher est toujours de fuir, l arbitrage reste a l agent."""
        N, A, D = self.N, self.A, self.D; S = self.scale
        th = torch.arange(K, device=self.dev).float() * (2.0 * math.pi / K)
        cx = (self.apx.unsqueeze(-1) + torch.sin(th) * self.champ_R).reshape(N, A * K)
        cy = (self.apy.unsqueeze(-1) + torch.cos(th) * self.champ_R).reshape(N, A * K)
        danger = torch.zeros(N, A * K, device=self.dev)
        eye = self._eye()
        eye_c = eye.unsqueeze(-1).expand(N, A, K).reshape(N, A * K) if torch.is_tensor(eye) else eye
        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, A * K); by = self.dpy[:, di:di + 1].expand(N, A * K)
            vivant = self._dalive()[:, di:di + 1].float()
            los = self._losc(self.hm, cx, cy, bx, by, S, eye_a=eye_c, eye_b=1.7)
            dist = torch.sqrt((cx - bx) ** 2 + (cy - by) ** 2)
            act = vivant.expand(N, A * K).clone()
            if self.def_line and hasattr(self, "dface"):        # hors du cone = ne peut pas tirer
                _ang = torch.atan2(cx - bx, cy - by)
                _adf = torch.atan2(torch.sin(_ang - self.dface[:, di:di + 1]),
                                   torch.cos(_ang - self.dface[:, di:di + 1]))
                act = act * (_adf.abs() <= self._dfarc).float()
            if self.courbe is not None:
                p = self._p_balle(dist) * self.tir_par_pas * self.degat_par_impact
            else:
                p = self.hit * (dist < self.fire_range).float()
            danger = danger + p * los * act
        return danger.reshape(N, A, K)

    def _p_norm(self, dist):
        """Prix d'etre vu a cette distance, ramene a [0,1] par le maximum de la courbe.
        C'est ce qui remplace le drapeau « a portee ou non » : etre vu a 200 m coute
        vraiment moins qu'a 25 m, mais ce n'est pas GRATUIT. Le rapport vient de la
        mesure Arma (0,26 au but a 200 m contre 0,75 a 25 m), pas d'un seuil choisi."""
        if not hasattr(self, "_p_ref"):
            self._p_ref = float(self._c_p.max())
        return (self._p_balle(dist) / max(self._p_ref, 1e-6)).clamp(0.0, 1.0)

    def _ouvrir_arcs(self):
        """Le cone ne tourne pas : il s'OUVRE apres la latence mesuree.

        Mesure Arma : le defenseur riposte a 100 % a tous les angles, mais 4 s plus tard
        quand la menace vient du flanc ou du dos — ET SANS PIVOTER (il n'est jamais venu a
        moins de 25 deg de son attaquant). L'angle mort n'est donc ni une protection ni une
        rotation : c'est un SURSIS.

        Tant qu'une menace hors cone est percue, on compte les pas. La latence ecoulee, le
        defenseur tire normalement — l'arc cesse de restreindre. Il se referme quand plus
        aucune menace n'est percue.
        """
        if self.arc_latence_pas is None or not hasattr(self, "dface"):
            return
        N, A, D = self.N, self.A, self.D; S = self.scale
        ex = self.apx.unsqueeze(2) - self.dpx.unsqueeze(1)      # (N,A,D)
        ey = self.apy.unsqueeze(2) - self.dpy.unsqueeze(1)
        d2 = ex * ex + ey * ey
        BIG = torch.tensor(1e18, device=self.dev)
        d2 = torch.where(self._aalive().unsqueeze(2), d2, BIG)
        ka = d2.argmin(1)                                        # (N,D) l'attaquant le plus proche
        ax = torch.gather(self.apx, 1, ka); ay = torch.gather(self.apy, 1, ka)
        los = self._losc(self.hm, self.dpx, self.dpy, ax, ay, S, eye_a=1.7, eye_b=1.7)
        proche = (d2.min(1).values.clamp(max=1e17).sqrt() < self.fire_range)
        percue = (los > 0.5) & proche & self._dalive()
        az = torch.atan2(ax - self.dpx, ay - self.dpy)
        ecart = torch.atan2(torch.sin(az - self.dface), torch.cos(az - self.dface)).abs()
        dehors = percue & (ecart > self._dfarc)
        # le compteur monte tant que la menace hors cone est la, retombe sinon
        self.d_attente = torch.where(dehors, self.d_attente + 1.0, torch.zeros_like(self.d_attente))
        # ─── LE CLIQUET DEPENSE LE SURSIS ────────────────────────────────────────────────
        # ⚠️ `alerte_niv` etait CALCULE PUIS JETE : il montait a chaque pas, monotone, et
        # aucune ligne du fichier ne le lisait. Le cliquet mesure sur Arma — « l alerte se
        # depense, elle ne se recupere jamais », aucune decroissance en 300 s — n avait donc
        # aucun effet sur le monde.
        # Ce qu il commande, et c est mesure aux deux bouts : le sursis de 4 s de l arc de tir
        # est le temps qu il faut a un defenseur pour prendre a partie une menace QU IL NE
        # CONNAISSAIT PAS. Un camp deja alerte n a plus ce temps a perdre. On interpole donc
        # entre les deux ancres mesurees :
        #     alerte 0,00  ->  sursis plein (4 s, mesure)
        #     alerte 4,00  ->  sursis nul   (la menace est deja connue)
        # C est ce qui fait qu en Arma se montrer une seule fois se paie sur TOUTE la
        # traversee, alors que le gymnase ne facturait que le pas ou l on s est montre.
        if self.alerte and hasattr(self, "alerte_niv"):
            _deja = (self.alerte_niv / self.ALERTE_MAX).clamp(0.0, 1.0).unsqueeze(1)
            self.d_attente = torch.maximum(self.d_attente, _deja * float(self.arc_latence_pas))
        # l'arc est OUVERT quand le sursis est ecoule, et se referme sans menace percue
        self.d_ouvert = (self.d_attente >= self.arc_latence_pas) & percue

    def _aalive(self): return self.admg < self.dmg_dead
    def _dalive(self): return self.ddmg < self.dmg_dead
    def _eye(self):
        return self._eye_lut[self.posture] if self.postures else torch.full_like(self.apx, 1.7)

    def _sample_solid(self, px, py):
        G = self.terr_G
        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        return self._solid[gy, gx]

    def _sample_field(self, field, px, py):
        G = self.terr_G
        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        return field[gy, gx]

    def _losc(self, hm, ax, ay, bx, by, R, eye_a=1.7, eye_b=1.7):
        base = TG.los_clear(hm, ax, ay, bx, by, R)
        if not getattr(self, "replica", False):
            return base
        K = 24
        t = torch.linspace(0.0, 1.0, K, device=self.dev)
        pxr = ax.unsqueeze(-1) * (1 - t) + bx.unsqueeze(-1) * t
        pyr = ay.unsqueeze(-1) * (1 - t) + by.unsqueeze(-1) * t
        if getattr(self, "flat_los", False):                       # BASELINE PLAT : LOS binaire (tout batiment bloque, ignore solidh/eye)
            return base * (~(self._sample_solid(pxr, pyr) > 0.5).any(-1)).float()
        # LOS 2.5D : hauteur de l'oeil (sol + eye) aux 2 bouts, interpolee le long du rayon
        za = self._sample_field(self._elevR, ax, ay) + eye_a
        zb = self._sample_field(self._elevR, bx, by) + eye_b
        z_ray = za.unsqueeze(-1) * (1 - t) + zb.unsqueeze(-1) * t
        # sommet a chaque echantillon = sol + hauteur du bati (solidh) ; bloque si un batiment depasse le rayon
        top = self._sample_field(self._elevR, pxr, pyr) + self._sample_field(self._solidhR, pxr, pyr) + self._sample_field(self._lowhR, pxr, pyr)
        blocked = (top > z_ray).any(-1)
        return base * (~blocked).float()

    def _body_exposure(self, ax, ay, eye_a, bx, by, M=5, K=20):
        """Exposition EMERGENTE : fraction du CORPS de A (sol..eye_a) touchable depuis B (oeil 1.7).
        Capteur de A = un point (oeil), mais sa CIBLE = une colonne (M segments pieds->tete).
        Un rayon par segment ; bloque si un obstacle depasse. La fraction visible EMERGE de
        (position x posture x hauteur du couvert) — pas un multiplicateur choisi. Asymetrie possible :
        debout je vois par-dessus mais mon torse depasse ; couche rien ne depasse mais je suis aveugle."""
        d = self.dev
        t = torch.linspace(0.0, 1.0, K, device=d)                         # (K,) le long du rayon B->A
        pxr = bx.unsqueeze(-1) * (1 - t) + ax.unsqueeze(-1) * t            # (N,A,K)
        pyr = by.unsqueeze(-1) * (1 - t) + ay.unsqueeze(-1) * t
        top = (self._sample_field(self._elevR, pxr, pyr)
               + self._sample_field(self._solidhR, pxr, pyr)
               + self._sample_field(self._lowhR, pxr, pyr))               # (N,A,K) sommet obstacle
        gb = self._sample_field(self._elevR, bx, by) + 1.7                # oeil du defenseur (N,A)
        ga = self._sample_field(self._elevR, ax, ay)                      # sol sous A (N,A)
        fr = torch.linspace(0.15, 1.0, M, device=d)                      # segments du corps (fraction de eye_a)
        zA = ga.unsqueeze(-1) + fr.view(1, 1, M) * eye_a.unsqueeze(-1)    # (N,A,M) hauteurs cibles sur le corps
        z_ray = gb[..., None, None] * (1 - t).view(1, 1, 1, K) + zA.unsqueeze(-1) * t.view(1, 1, 1, K)  # (N,A,M,K)
        blocked = (top.unsqueeze(2) > z_ray).any(-1)                      # (N,A,M) segment m bloque ?
        return (~blocked).float().mean(-1)                               # (N,A) fraction du corps visible

    def _obs(self):
        S = self.scale; al = self._aalive()
        dgx = -self.apx / S; dgy = -self.apy / S
        sl = TG.sample(self.slope, self.apx, self.apy, S) / 5.0
        _dcr = TG.sample(self.dcover, self.apx, self.apy, S)   # distance au bâti (cellules = m sur replica)
        dc = (_dcr / 30.0).clamp(max=1.0) if self.obs_dcover_arma else (_dcr / self.terr_G)   # arma_obs : normalisé COMME le pont Arma (÷30 m capé)
        ex = self.dpx.unsqueeze(1) - self.apx.unsqueeze(2); ey = self.dpy.unsqueeze(1) - self.apy.unsqueeze(2)  # (N,A,D)
        BIG = torch.tensor(1e18, device=self.dev)
        ed2 = torch.where(self._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
        bx = torch.gather(self.dpx, 1, km); by = torch.gather(self.dpy, 1, km)
        # ⚠️ 25/08 — `los` DECRIVAIT L EXPOSITION A UN SEUL HOMME, ET QUATRE TIRAIENT.
        # Calcule contre le defenseur LE PLUS PROCHE (km = ed2.argmin) pendant que les degats
        # sommaient sur TOUS les defenseurs vivants (boucle par `di`, plus bas).
        # Mesure du 25/08, A DISTANCE EGALE : etre cache du plus proche fait prendre SIX FOIS
        # PLUS de degats a 0-40 m, et TROIS FOIS MOINS au-dela de 130 m. Le signe de la
        # colonne S INVERSE avec la distance — moyennee elle ne porte aucun signal, et c est
        # pourquoi la brouiller ne coutait que 0,9 point : IGNORER `los` ETAIT RATIONNEL.
        # Reparation minimale : le MAXIMUM sur les defenseurs VIVANTS — « suis-je offert a
        # quelqu un ? ». Defaut False : aucun monde existant ne change.
        if getattr(self, "los_tous", False):
            _lv = []
            for _di in range(self.D):
                _bx = self.dpx[:, _di:_di + 1].expand_as(self.apx)
                _by = self.dpy[:, _di:_di + 1].expand_as(self.apy)
                # ⚠️ LE SENS DU RAYON EST LE DEFAUT ⟨mesure du 25/08⟩. `_losc` rend LA
                # FRACTION DU CORPS DE LA CIBLE visible depuis l oeil de la source. Calcule
                # attaquant -> defenseur, il repond « quelle part de L ENNEMI je vois ».
                # Ce qui TUE est « quelle part de MOI il voit » — l autre question.
                # Mesure : a 0-40 m, 58,9 % des etats ou l agent se croit cache le montrent
                # EN PLEIN a un defenseur ; 53,9 % a 40-60 m, puis 38, 25, 15, 12 %.
                # C est le profil exact de l inversion de signe des degats.
                # On calcule donc DEFENSEUR -> ATTAQUANT, comme la ligne des degats.
                _v = self._losc(self.hm, _bx, _by, self.apx, self.apy, S,
                                eye_a=1.7, eye_b=self._eye())
                _lv.append(_v * self._dalive()[:, _di:_di + 1].float())
            los = torch.stack(_lv, -1).max(-1).values
        else:
            los = self._losc(self.hm, self.apx, self.apy, bx, by, S, eye_a=self._eye(), eye_b=1.7)
        nd = ed2.min(2).values.clamp(max=1e17).sqrt() / S
        if self.obs_sans_slope:      # obs Arma-cheap : sans la pente (slope), on garde dcover (~bâti proche) + LOS (checkVisibility)
            base = torch.stack([self.apx / S, self.apy / S, dgx, dgy, al.float(), dc, los, nd], dim=2)
        else:
            base = torch.stack([self.apx / S, self.apy / S, dgx, dgy, al.float(), sl, dc, los, nd], dim=2)
        parts = [base]
        if self.champ_risque:
            _cd = self._champ_danger()
            if self.etat is not None:
                # audace > 1 : le meme terrain parait moins cher, donc on entre.
                _cd = _cd / self.etat.audace().view(-1, 1, 1).clamp(min=1e-3)
            parts.append(_cd)
        if self.arc_obs and hasattr(self, "dface"):
            # angle entre la FACE du defenseur le plus proche et la direction sous
            # laquelle il me voit. 0 = il me regarde en face ; +-pi = je suis dans son dos.
            _df = torch.gather(self.dface, 1, km)
            _az = torch.atan2(self.apx - bx, self.apy - by)      # azimut defenseur -> moi
            _rel = torch.atan2(torch.sin(_az - _df), torch.cos(_az - _df))
            parts.append(torch.stack([torch.sin(_rel), torch.cos(_rel)], dim=2))
        if self.shell_obs: parts.append(self._cover_shell())
        if self.suffer: parts.append(self._suffer_feats())
        if self.grid_obs: parts.append(self._local_grid())
        if self.team_obs: parts.append(self._team_feats())
        if self.role_obs:                                   # ROLE assigne par l'officier (one-hot appui/assaut)
            parts.append(torch.stack([(self.role == 0).float(), (self.role == 1).float()], dim=2))
        if self.postures:                                   # SELF-PERCEPTION : sa propre posture (one-hot)
            parts.append(torch.stack([(self.posture == 0).float(), (self.posture == 1).float(), (self.posture == 2).float()], dim=2))
        return torch.cat(parts, dim=2) if len(parts) > 1 else base

    def _team_feats(self):
        """Conscience des coequipiers (coordination) : binome le plus proche (dx,dy) + suppresse-t-il ?
        + niveau de feu de l'equipe. Permet le feu+mouvement EXPLICITE (j'avance car mon binome cloue)."""
        S = self.scale; px, py = self.apx, self.apy; al = self._aalive()
        dx = px.unsqueeze(1) - px.unsqueeze(2); dy = py.unsqueeze(1) - py.unsqueeze(2)   # (N,A,A) : ally j vu de i
        BIG = torch.tensor(1e18, device=self.dev)
        eye = torch.eye(self.A, dtype=torch.bool, device=self.dev)[None]
        d2 = torch.where(eye | ~al.unsqueeze(1), BIG, dx * dx + dy * dy); jm = d2.argmin(2)
        adx = torch.gather(dx, 2, jm.unsqueeze(2)).squeeze(2) / S; ady = torch.gather(dy, 2, jm.unsqueeze(2)).squeeze(2) / S
        nm = d2.min(2).values >= 1e18; adx = adx.masked_fill(nm, 0.0); ady = ady.masked_fill(nm, 0.0)
        ally_supp = torch.gather(self.last_supp, 1, jm)                                  # le binome cloue-t-il ?
        frac = ((self.last_supp * al.float()).sum(1, keepdim=True) / al.float().sum(1, keepdim=True).clamp(min=1)).expand(self.N, self.A)
        return torch.stack([adx, ady, ally_supp, frac], dim=2)

    def _suffer_feats(self):
        """Signal de DEBORDEMENT : degats recus au dernier pas + fraction de defenseurs qui PEUVENT me toucher
        (vivant + portee + LOS). C'est ce qui permet de JUGER tenir(gagnable) vs decrocher(submerge)."""
        N, A, D, d, S = self.N, self.A, self.D, self.dev, self.scale
        nt = torch.zeros(N, A, device=d)
        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
            los = self._losc(self.hm, self.apx, self.apy, bx, by, S, eye_a=self._eye(), eye_b=1.7)
            dist = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2 + (self.apy - self.dpy[:, di:di + 1]) ** 2)
            nt += self._dalive()[:, di:di + 1].float() * los * (dist < self.fire_range).float()
        return torch.stack([(self.last_dmg_in * 5.0).clamp(max=1.0), nt / self.D], dim=2)   # (N,A,2)

    def _cover_shell(self):
        """COQUE DE COUVERT : K rayons ray-marches dans le champ de couvert, centres sur la MENACE
        (rayon 0 = vers l'ennemi le + proche, sens horaire). Distance au 1er couvert / portee. = l'obs de l'avatar Arma."""
        N, A, K, d, S = self.N, self.A, self.shellK, self.dev, self.scale
        R, steps = self.shell_R, 20
        ex = self.dpx.unsqueeze(1) - self.apx.unsqueeze(2); ey = self.dpy.unsqueeze(1) - self.apy.unsqueeze(2)
        BIG = torch.tensor(1e18, device=d)
        ed2 = torch.where(self._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
        bx = torch.gather(self.dpx, 1, km); by = torch.gather(self.dpy, 1, km)
        th0 = torch.atan2(by - self.apy, bx - self.apx)                       # cap vers la menace (N,A)
        offs = torch.arange(K, device=d).float() * (2 * math.pi / K)
        ang = th0.unsqueeze(-1) + offs                                        # (N,A,K)
        cs = ang.cos(); sn = ang.sin()
        stp = (torch.arange(1, steps + 1, device=d).float() / steps) * R      # (steps,)
        sx = (self.apx[..., None, None] + cs[..., None] * stp).reshape(N, A * K * steps)
        sy = (self.apy[..., None, None] + sn[..., None] * stp).reshape(N, A * K * steps)
        cov = TG.sample(self.cover, sx, sy, S).reshape(N, A, K, steps)
        hit = cov > 0.5; anyh = hit.any(-1)
        first = hit.float().argmax(-1).float()                               # 1er pas touche (0 si aucun)
        dist = torch.where(anyh, (first + 1) / steps * R, torch.full_like(first, R)) / R
        return torch.cat([dist, self.admg.unsqueeze(-1)], dim=2)             # (N,A,K+1) : coque + degats

    def _local_grid(self):
        """Grille locale (G-perc-1) : fenetre KxK de [couvert, pente] autour de l'agent = CONTEXTE spatial
        (vs les valeurs au point). Aplatie -> 2*K*K features. World-aligned (rotation egocentrique = etape +)."""
        K, span, d, N, A = self.gridK, self.gridspan, self.dev, self.N, self.A
        off = (torch.arange(K, device=d).float() / (K - 1) - 0.5) * span
        gx = (self.apx[..., None, None] + off[None, None, :, None]).expand(N, A, K, K).reshape(N, A * K * K)
        gy = (self.apy[..., None, None] + off[None, None, None, :]).expand(N, A, K, K).reshape(N, A * K * K)
        cov = TG.sample(self.cover, gx, gy, self.scale).reshape(N, A, K * K)
        slp = (TG.sample(self.slope, gx, gy, self.scale) / 5.0).reshape(N, A, K * K)
        return torch.cat([cov, slp], dim=2)

    def step(self, acts, auto_reset=True):
        d = self.dev; N, A, D = self.N, self.A, self.D; al = self._aalive().float()
        self._seg0x = self.apx.clone(); self._seg0y = self.apy.clone()   # R1 : debut du segment
        th = acts.float() * (math.pi / 4.0)                    # STEERING : actions 0-7 = caps (45 deg)
        moving = (acts < 8).float() * al                       # 8 = HOLD, 9 = SUPPRESS, 10-12 postures -> pas de mouvement
        if self.replica and self.nav_around:
            # NAV : essaie le cap, puis des déviations croissantes ; prend le 1er chemin LIBRE (destination + milieu) -> longe les murs, ne se coince pas
            offs = torch.tensor([0., math.pi / 8, -math.pi / 8, math.pi / 4, -math.pi / 4, 3 * math.pi / 8,
                                 -3 * math.pi / 8, math.pi / 2, -math.pi / 2, 5 * math.pi / 8, -5 * math.pi / 8], device=d)
            cth = th.unsqueeze(-1) + offs                       # (N,A,K) caps candidats
            cx = self.apx.unsqueeze(-1) + torch.sin(cth) * self.move; cy = self.apy.unsqueeze(-1) + torch.cos(cth) * self.move
            mx = self.apx.unsqueeze(-1) + torch.sin(cth) * self.move * 0.5; my = self.apy.unsqueeze(-1) + torch.cos(cth) * self.move * 0.5
            K = offs.numel()
            free = (self._sample_solid(cx.reshape(N, -1), cy.reshape(N, -1)).reshape(N, A, K) < 0.5) & \
                   (self._sample_solid(mx.reshape(N, -1), my.reshape(N, -1)).reshape(N, A, K) < 0.5)   # destination ET milieu libres
            pri = offs.abs().view(1, 1, K) + (~free).float() * 1e3    # préfère la déviation MINIMALE, parmi les libres
            sel = torch.gather(cth, -1, pri.argmin(-1, keepdim=True)).squeeze(-1)
            go = moving * free.any(-1).float()                        # aucun chemin libre -> reste sur place
            self.apx = (self.apx + torch.sin(sel) * self.move * go).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
            self.apy = (self.apy + torch.cos(sel) * self.move * go).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
        else:
            _oax = self.apx.clone(); _oay = self.apy.clone()
            if self.frein_feu > 0.0 and hasattr(self, 'last_exposed'):
                # l exposition subie au pas precedent ralentit : un homme sous le feu avance
                # moins vite. Au premier pas elle n existe pas encore : aucun frein.
                _fr = (1.0 - self.frein_feu * self.last_exposed.clamp(0.0, 1.0)).clamp(0.05, 1.0)
                moving = moving * _fr
            self.apx = (self.apx + torch.sin(th) * self.move * moving).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
            self.apy = (self.apy + torch.cos(th) * self.move * moving).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
            if self.replica:
                _wall = self._sample_solid(self.apx, self.apy) > 0.5
                self.apx = torch.where(_wall, _oax, self.apx); self.apy = torch.where(_wall, _oay, self.apy)
        if self.postures:                                          # actions 10/11/12 = poser une posture (sticky)
            for pa, pv in ((10, 0), (11, 1), (12, 2)):
                self.posture = torch.where(acts == pa, torch.full_like(self.posture, pv), self.posture)
        incover = TG.sample(self.cover, self.apx, self.apy, self.scale).clamp(max=1.0)   # couvert = terrain (atteint par steering)
        # --- ALERTE : mise a jour AVANT le feu, car c est elle qui autorise le feu ---
        if self.alerte:
            _al = self._aalive().float()
            _dv = self._dalive().float()
            # (a) DETECTION PASSIVE PAR LA DISTANCE, pas par l arc.
            _dmin = torch.full((N,), 1e4, device=d)
            for _di in range(D):
                _dd = torch.sqrt((self.apx - self.dpx[:, _di:_di + 1]) ** 2
                                 + (self.apy - self.dpy[:, _di:_di + 1]) ** 2)
                _dd = torch.where(_al > 0, _dd, torch.full_like(_dd, 1e4))
                _dd = torch.where(_dv[:, _di:_di + 1] > 0, _dd, torch.full_like(_dd, 1e4))
                # ⚠️ UN HOMME COUCHE AU-DELA DE 120 m NE SE FAIT PAS DETECTER. Mesure Arma
                # certifiee (banc de l angle mort) : 18/18 reperages dans le cone contre 0/26
                # hors, et le COUCHE devient invisible passe 120 m. Sans cette ligne, la
                # posture ne servait qu a reduire la surface touchable — jamais a echapper au
                # REGARD, qui est pourtant l essentiel de ce que la posture achete.
                # ⚠️ Et ce n est PAS en contradiction avec la courbe de toucher, qui donne
                # encore 16-18 % a 150-200 m couche : la courbe mesure le TOUCHER d une cible
                # DEJA connue, cette ligne mesure la DETECTION d une cible qui ne l est pas.
                # Deux grandeurs, deux mesures, et c est le cliquet d alerte qui les separe.
                if self.postures and self.COUCHE_INVISIBLE_M is not None:
                    _couche = (self.posture == 2)
                    _loin = _dd > self.COUCHE_INVISIBLE_M
                    _dd = torch.where(_couche & _loin, torch.full_like(_dd, 1e4), _dd)
                _dmin = torch.minimum(_dmin, _dd.min(dim=1).values)
            _vu = ((self.R_VUE_NULLE - _dmin) / (self.R_VUE_NULLE - self.R_VUE_PLEINE)).clamp(0.0, 1.0)
            # (b) LE FEU DE L ATTAQUANT COUTE, sur TOUT LE GROUPE, quelle que soit la distance.
            _tirs = ((acts == 9) & self._aalive()).float().sum(1)
            # (c) MONOTONE : aucune decroissance mesuree en 300 s.
            self.alerte_niv = torch.maximum(self.alerte_niv, _vu * self.ALERTE_MAX)
            self.alerte_niv = (self.alerte_niv + self.ALERTE_PAR_TIR * _tirs).clamp(max=self.ALERTE_MAX)

        # --- feu des DEFENSEURS sur les attaquants (LOS du relief + portee + couvert) ---
        dmg_a = torch.zeros(N, A, device=d); exposed = torch.zeros(N, A, device=d)
        self._vu_geo = torch.zeros(N, A, device=d)   # vu GEOMETRIQUEMENT a ce pas, avant tout bouton
        for di in range(D):
            _dans_f = None      # porte de tir du defenseur, relevee pour le canal CWR
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
            los = self._losc(self.hm, self.apx, self.apy, bx, by, self.scale, eye_a=self._eye(), eye_b=1.7)
            dist = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2 + (self.apy - self.dpy[:, di:di + 1]) ** 2)
            # SUPPRESSION GRADUEE, pas un interrupteur. Arma (28/07) : sous le feu il reste
            # 8 % de la capacite de nuire — un coup au but toutes les 12 s au lieu d'un par
            # seconde. L'ancien seuil rendait l'attaquant INVULNERABLE des qu'on arrosait,
            # ce qui payait bien trop le feu de couverture.
            _viv = self._dalive()[:, di:di + 1].float()
            if self.supp_residuel is None:
                active = _viv * (self.dsupp[:, di:di + 1] < 0.5).float()
            else:
                _s = self.dsupp[:, di:di + 1].clamp(0.0, 1.0)
                active = _viv * (1.0 - (1.0 - self.supp_residuel) * _s)

            if self.def_line and hasattr(self, "dface"):                 # ARC DE TIR : le défenseur ne tire que dans son cône (±_dfarc autour de sa face)
                _ang = torch.atan2(self.apx - self.dpx[:, di:di + 1], self.apy - self.dpy[:, di:di + 1])   # azimut défenseur->attaquant
                _adf = torch.atan2(torch.sin(_ang - self.dface[:, di:di + 1]), torch.cos(_ang - self.dface[:, di:di + 1]))   # écart à la face, wrap [-π,π]
                _dans = (_adf.abs() <= self._dfarc)
                if self.alerte:
                    # LA DETECTION PAR DISTANCE REMPLACE LE CONE (mesure Arma du 2026-07-30 :
                    # on voit a 60 m DANS TOUTES LES DIRECTIONS). C etait le vrai defaut :
                    # l arc rendait le contournement litteralement invisible, d ou 96 % de
                    # reussite au debordement quand le juge externe en donne 0 %.
                    # Un defenseur tire donc aussi hors de son arc sur ce qu il DETECTE.
                    _dv2 = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2
                                      + (self.apy - self.dpy[:, di:di + 1]) ** 2)
                    _detecte = _dv2 < self.R_VUE_NULLE
                    _dans = _dans | _detecte
                if getattr(self, "d_ouvert", None) is not None:
                    # SURSIS ECOULE : il tire hors de son cone, sans avoir pivote.
                    # Mesure Arma : riposte a 100 %% a tous les angles apres ~4 s,
                    # et sans attenuation d ampleur (impacts 180/0 = 1,17).
                    _dans = _dans | self.d_ouvert[:, di:di + 1]
                _dans_f = _dans.float()
                active = active * _dans_f     # hors cône ET sursis non ecoule = ne peut pas tirer
            # --- LE CLIQUET PAR ATTAQUANT. `los` devient « ce que le defenseur peut
            # battre » : ce qu il VOIT, ou ce qu il A VU et bat encore a taux reduit.
            # le cliquet se tient a jour MEME a bouton nul : sans ca on ne saurait pas
            # mesurer le contraste « deja vu / jamais vu » dans le monde de reference.
            self.a_connu = torch.maximum(self.a_connu, (los > 0.5).float() * _viv)
            # ⚠️ LA VISIBILITE GEOMETRIQUE, RELEVEE AVANT LE BOUTON. Sans elle, l etiquette
            # « vu / pas vu » derive du meme `los` que `feu_sur_connu` modifie : le traitement
            # deplace l etiquette en meme temps que l effet, et le contraste MONTE avec le
            # bouton (856 % puis 4086 % au premier balayage). Une mesure dont l etiquette
            # depend du traitement ne mesure rien.
            self._vu_geo = torch.maximum(self._vu_geo, (los > 0.5).float() * _viv)
            if self.canal is not None:
                # `lastSeen` de RV1 : porte par le groupe, donc par ATTAQUANT et non par
                # couple (defenseur, attaquant). Mis a jour sur la vue geometrique du pas.
                _vu_ici = ((los > 0.5) & (_viv > 0))
                self.a_dernier_vu = torch.where(_vu_ici, self.t.unsqueeze(1).float(),
                                                self.a_dernier_vu)
            if self.feu_sur_connu > 0.0:
                los = torch.maximum(los, self.feu_sur_connu * self.a_connu)
            inr = (dist < self.fire_range).float()
            # SELECTION DE CIBLE. `tir` remplace `active` dans les DEGATS uniquement :
            # « etre vu » n'est pas « etre pris pour cible », et `exposed` doit rester la
            # premiere notion (c'est elle qui porte le cout de la manoeuvre).
            tir = active
            _efrac = None
            if self.canal is not None:
                # LA DESIGNATION PASSE PAR LE CANAL. `_dans_f` est la porte de tir DEJA en
                # service (arc + detection) : on ne superpose pas les cosinus 15/45 de RV1,
                # ca compterait deux fois le meme effet.
                _efrac = self._body_exposure(self.apx, self.apy, self._eye(), bx, by)
                self._canal_out = self._CANAL.canal(_efrac, dist, self.canal, porte_cone=_dans_f)
            if self.cible_unique:
                _porte = (self._canal_out["designe"] if self.canal is not None else (los > 0.5))
                _elig = (active > 0) & _porte & self._aalive()
                if self.canal is not None:
                    # ─── LA FENETRE DE 10 s. `lastSeen` se met a jour sur la VUE
                    # GEOMETRIQUE du pas ; ensuite l homme reste tirable 10 s, puis plus.
                    # Ce n est pas le cliquet eternel de `a_connu` : la source coupe.
                    # ⛔ CORRECTION. J avais lu la fenetre de 10 s comme une PERMISSION
                    # (« le defenseur bat la derniere position connue »). LA SOURCE EN FAIT
                    # UNE RESTRICTION : `WhatFireResult` recalcule la visibilite COURANTE et
                    # refuse sous `MinVisibleFire` (TargetFire.cpp:1203), et la fenetre de
                    # 10 s S AJOUTE a ce refus (l.1241). Les trois conditions sont ET, pas OU.
                    # Consequence dure : il n existe AUCUN tir VISE sur un homme actuellement
                    # cache — ce que la porte `posError > 2*indirectHitRange` disait deja
                    # pour un fusil. Donc le +75 % d Arma 3 ne peut PAS venir de la, et
                    # c est une question de MESURE, pas de modele. Falsificateur au depot.
                    _frais = (((self.t.unsqueeze(1).float() - self.a_dernier_vu)
                               <= float(self.canal_mem_pas)) & (self.a_dernier_vu > -1e8))
                    _voit_assez = (_efrac >= self._CANAL.MIN_VISIBLE_FIRE)
                    _elig = ((active > 0) & self._canal_out["designe"]
                             & _voit_assez & _frais & self._aalive())
                if self.courbe is None:                    # sans courbe, la portee est un mur
                    _elig = _elig & (dist < self.fire_range)
                _INF = torch.full_like(dist, float("inf"))
                _k = torch.where(_elig, dist, _INF).argmin(1, keepdim=True)
                if self.canal is not None:
                    # ─── LE VERROU DE 15 s (`FireValidTime`). Le defenseur RESTE sur sa
                    # cible tant qu elle vit et reste eligible ; il ne re-choisit pas le
                    # plus proche a chaque pas. C est ce verrou qui fait qu un flanqueur
                    # isole encaisse tout, au lieu d etre relache au pas suivant.
                    _anc = self.d_cible[:, di:di + 1]                      # (N,1)
                    _a_valide = (_anc >= 0)
                    _ok_anc = torch.zeros_like(_a_valide)
                    if bool(_a_valide.any()):
                        _idx = _anc.clamp(min=0)
                        _ok_anc = _a_valide & (self.d_verrou[:, di:di + 1] > 0) \
                                  & torch.gather(_elig, 1, _idx)
                    _k = torch.where(_ok_anc, _anc, _k)
                    _neuf = _elig.any(1, keepdim=True) & ~_ok_anc
                    self.d_cible[:, di:di + 1] = torch.where(
                        _neuf, _k, torch.where(_ok_anc, _anc, torch.full_like(_anc, -1)))
                    self.d_verrou[:, di:di + 1] = torch.where(
                        _neuf, torch.full_like(_anc, self.canal_verrou_pas),
                        (self.d_verrou[:, di:di + 1] - 1).clamp(min=0))
                _sel = torch.zeros_like(active).scatter_(1, _k, 1.0) * _elig.float()
                tir = active * _sel
            if self.emergent_expo and self.replica:                # EXPOSITION EMERGENTE : fraction du corps touchable = geometrie (couvert deja capture par les rayons)
                efrac = _efrac if _efrac is not None else self._body_exposure(self.apx, self.apy, self._eye(), bx, by)
                if self.courbe is not None:
                    # posture=None VOLONTAIREMENT : efrac porte deja le profil du corps
                    # (calcule par rayons). Appliquer en plus la colonne posture de la
                    # courbe compterait le meme effet deux fois.
                    if self.canal is not None:
                        # ⭐ LA LOI DE TIR. Avant : `_p * efrac` — le couvert LINEAIRE, et
                        # aucun plancher. La source : `hitProbab *= Square(visible)`, puis
                        # rien si `visible < 0.63`, puis rien si `hitProbab < 0.05`.
                        _pb = self._CANAL.tir(self._p_balle(dist), efrac)
                        _p = _pb * self.tir_par_pas * self.degat_par_impact
                        dmg_a += _p * tir
                    else:
                        _p = self._p_balle(dist) * self.tir_par_pas * self.degat_par_impact
                        dmg_a += _p * efrac * tir
                    if self.feu_de_zone > 0.0:      # le defenseur bat une ZONE : pas de designation, pas de vue
                        dmg_a += _p * self.feu_de_zone * inr * active
                else:
                    dmg_a += self.hit * efrac * inr * tir
                if self.courbe is not None:
                    # plus de falaise : l'exposition suit la COURBE, comme les dégâts.
                    # Sans ça la métrique est aveugle au-delà de 110 m — or le crochet
                    # y fait 74 % de son détour (mesuré 27/07).
                    exposed = torch.maximum(exposed, efrac * active * self._p_norm(dist))
                else:
                    exposed = torch.maximum(exposed, efrac * inr * active)   # exposé = vu par un défenseur qui PEUT tirer (arc inclus)
            else:
                if self.courbe is not None:
                    # plus de (dist < fire_range) : la courbe s'eteint d'elle-meme.
                    # C'etait la falaise a 110 m — celle qui rendait le rapprochement
                    # gratuit, et donc la manoeuvre depourvue de sens.
                    _po = self.posture if self.postures else None
                    _p = self._p_balle(dist, _po) * self.tir_par_pas * self.degat_par_impact
                    dmg_a += _p * los * tir * (1.0 if self.couvert_directionnel else (1.0 - 0.7 * incover))
                    if self.feu_de_zone > 0.0:      # idem : le couvert attenue, il n annule plus
                        dmg_a += _p * self.feu_de_zone * inr * active * (1.0 if self.couvert_directionnel else (1.0 - 0.7 * incover))
                else:
                    _exp = self._expose_lut[self.posture] if (self.postures and self.hull) else 1.0   # HULL-DOWN knob (posture basse = petite cible)
                    dmg_a += self.hit * los * inr * tir * (1.0 if self.couvert_directionnel else (1.0 - 0.7 * incover)) * _exp
                if self.courbe is not None:
                    exposed = torch.maximum(exposed, los * active * self._p_norm(dist))
                else:
                    exposed = torch.maximum(exposed, los * inr * active)   # exposé = vu par un défenseur qui PEUT tirer (arc inclus)
        self.last_dmg_in = (dmg_a * al).detach()
        self.last_exposed = (exposed * al).detach()   # exposition = vu par un defenseur vivant a portee
        self.admg = (self.admg + dmg_a * al).clamp(max=0.95)
        # --- attaquants SUPPRESS (3) les defenseurs en LOS+portee ---
        self._ouvrir_arcs()
        # PERSISTANCE. Le sandbox remettait la suppression a zero a chaque pas : l'adversaire
        # relevait la tete instantanement. Arma donne 2 s de repit pour un pas de 3,28 s —
        # court, mais pas nul. On reporte une fraction avant d'effacer.
        _reste = self.dsupp * self.supp_persist if self.supp_persist > 0 else None
        self.dsupp.zero_(); dmg_d = torch.zeros(N, D, device=d); supp_act = (acts == 9) & self._aalive()
        self.last_supp = supp_act.float()                          # memo pour la conscience d'equipe (coordination)
        for ai in range(A):
            bx = self.apx[:, ai:ai + 1].expand(N, D); by = self.apy[:, ai:ai + 1].expand(N, D)
            los = self._losc(self.hm, self.dpx, self.dpy, bx, by, self.scale, eye_a=1.7, eye_b=self._eye()[:, ai:ai + 1])
            dist = torch.sqrt((self.dpx - self.apx[:, ai:ai + 1]) ** 2 + (self.dpy - self.apy[:, ai:ai + 1]) ** 2)
            eff = los * (dist < self.fire_range).float() * supp_act[:, ai:ai + 1].float()
            self.dsupp = torch.maximum(self.dsupp, eff)
            if self.flank_kill > 0 and self.def_line and hasattr(self, "dface"):
                # FEU DE FLANC LÉTAL : depuis l'angle mort du défenseur (hors de SON arc), l'attaquant l'abat (il ne peut pas riposter) ; frontalement = mur balistique (faible)
                _af = torch.atan2(self.apx[:, ai:ai + 1] - self.dpx, self.apy[:, ai:ai + 1] - self.dpy)   # azimut défenseur->attaquant ai (N,D)
                _adff = torch.atan2(torch.sin(_af - self.dface), torch.cos(_af - self.dface))
                blind = (_adff.abs() > self._dfarc).float()                                                # attaquant dans l'angle mort du défenseur
                dmg_d += (self.flank_kill * blind + self.supp_kill * 0.10 * (1 - blind)) * eff
            else:
                dmg_d += self.supp_kill * 0.10 * eff                       # feu attaquant vs def (calibré vs Arma retranché)
        if _reste is not None:                       # le repit mesure sur Arma, reporte d'un pas
            self.dsupp = torch.maximum(self.dsupp, _reste)
        self.ddmg = (self.ddmg + dmg_d).clamp(max=0.95)
        self.t = self.t + 1
        al2 = self._aalive()
        ndist = torch.sqrt(self.apx ** 2 + self.apy ** 2)
        neutralized = ~self._dalive().any(1)                       # défenseurs neutralisés PAR LE FEU
        if self.arrivee_segment:
            # distance MINIMALE de l objectif (l origine) au segment parcouru pendant le pas
            _vx = self.apx - self._seg0x; _vy = self.apy - self._seg0y
            _vv = _vx * _vx + _vy * _vy
            _t = torch.where(_vv > 1e-9,
                             (-(self._seg0x * _vx + self._seg0y * _vy) / _vv.clamp(min=1e-9)).clamp(0.0, 1.0),
                             torch.zeros_like(_vv))
            _cx = self._seg0x + _t * _vx; _cy = self._seg0y + _t * _vy
            _dtest = torch.sqrt(_cx * _cx + _cy * _cy)
        else:
            _dtest = ndist
        took = ((_dtest < self.secure_r) & al2).any(1)              # un attaquant VIVANT a atteint/sécurisé l'objectif (comme Arma)
        win = took if self.secure_only else ((neutralized | took) if self.secure_task else neutralized)   # secure_only (calib Arma) : SEUL atteindre le FOB gagne
        wiped = ~al2.any(1)
        timeout = self.t >= self.max_steps
        done = win | wiped | timeout
        # REVUE 17/08 : la distance de chaque homme est GELEE a sa mort, donc une mort ne
        # deplace plus la moyenne. Un aneantissement laisse `cur` inchange -> le terme de
        # progression vaut 0 au lieu de +approach_w*prev_d (soit +0,17 au depart).
        self._dlast = torch.where(al2, ndist / self.scale, self._dlast)
        cur = self._dlast.mean(1)                                  # dist a l'objectif (pour entrer en portee)
        losses = 1.0 - al2.float().sum(1) / self.A
        dk = (self.D - self._dalive().float().sum(1)) / self.D     # fraction defenseurs neutralises
        if self.overwatch:                                         # OVERWATCH/DEFILEMENT v2 : engager DEPUIS le couvert (pas rompre le LOS)
            dmg_frac = self.last_dmg_in.sum(1) / al.sum(1).clamp(min=1)    # degats RECUS -> chercher le couvert EN gardant le LOS sur l'ennemi
            rew = (self.kill_w * (dk - self._prev_dk)                       # neutraliser l'ennemi = moteur d'engagement
                   - self.ow_dmg * dmg_frac                         # encaisser COUTE (couvert/hull-down recompense)
                   - 0.005 + win.float() * self.win_bonus              # bonus victoire
                   - self.death_pen * (wiped & ~win).float()           # penalite aneantissement
                   - self.ow_tofail * (timeout & ~win).float())   # se planquer jusqu'au timeout = ECHEC (force a tuer)
        else:
            rew = (self.approach_w * (self.prev_d - cur)              # shaping CLÔTURE : se rapprocher (moteur en tâche sécuriser)
                   + self.kill_w * (dk - self._prev_dk)                        # neutraliser les defenseurs au feu (réduit le feu reçu)
                   - 0.005 + win.float() * self.win_bonus                 # bonus victoire (sécuriser OU nettoyer)
                   - self.death_pen * (wiped & ~win).float())             # penalite aneantissement (CMDP : pertes)
        if self.suffer:
            rew = rew - self.suffer_pen * (wiped & ~win).float()   # la mort COUTE (knob suffer_pen ; total defaut -1.5)
        self.prev_d = cur; self._prev_dk = dk
        if self.role_obs:                                          # OFFICIER : recompense la STRUCTURE feu+mouvement
            appui = ((self.role == 0) & al2).float(); assaut = ((self.role == 1) & al2).float()
            sup = (acts == 9).float(); mov = (acts < 8).float()
            a_sup = (sup * appui).sum(1) / appui.sum(1).clamp(min=1)     # appui qui CLOUE
            a_mov = (mov * assaut).sum(1) / assaut.sum(1).clamp(min=1)   # PENDANT que l'assaut AVANCE
            rew = rew + 0.05 * a_sup * a_mov
        if self.etat is not None:
            _ndist = torch.sqrt(self.apx ** 2 + self.apy ** 2)
            _al = self._aalive().float()
            self.etat.pas(danger=self.last_exposed,
                          pertes=1.0 - _al.mean(1),
                          temps_restant=1.0 - self.t.float() / float(self.max_steps),
                          dist_obj=(_ndist * _al).sum(1) / _al.sum(1).clamp(min=1),
                          dist_obj0=torch.full_like(self.prev_d, self.R_spawn))
        info = {"neutralized": neutralized, "took": took, "win": win, "wiped": wiped, "losses": losses, "dkilled": dk, "exposed": self.last_exposed.sum(1) / al.sum(1).clamp(min=1)}
        if auto_reset:
            self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info

    def scripted_advance(self):
        return [torch.ones(self.N, self.A, dtype=torch.long, device=self.dev)]  # placeholder API


if __name__ == "__main__":
    dev = "cuda:0"
    def run(relief, steps=60):
        e = AssaultTerrain(num_envs=2048, relief=relief, device=dev, seed=7)
        e.reset(); neut = wiped = 0.0; losssum = 0.0; nep = 0
        for _ in range(steps):
            th = torch.atan2(-e.apx, -e.apy)
            a = (torch.round(th / (math.pi / 4.0)) % 8).long()
            _, r, done, info = e.step(a)
            di = done.bool()
            if di.any():
                neut += info["neutralized"][di].float().sum().item()
                wiped += info["wiped"][di].float().sum().item()
                losssum += info["losses"][di].sum().item(); nep += int(di.sum())
        return neut / max(nep, 1), wiped / max(nep, 1), losssum / max(nep, 1), nep
    print("ASSAUT direct (foncer) — terrain PLAT vs RELIEF (foncer sans supprimer doit ECHOUER) :")
    for label, rel in [("plat (relief 1m)", 1.0), ("relief 35m", 35.0), ("relief 60m", 60.0)]:
        pr, pw, pl, npe = run(rel)
        print("  %-18s : defenseurs neutralises %3.0f%% | aneanti %3.0f%% | pertes moy %3.0f%% (%d episodes)"
              % (label, 100 * pr, 100 * pw, 100 * pl, npe))
