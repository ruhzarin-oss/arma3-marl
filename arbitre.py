#!/usr/bin/env python3
"""arbitre — LE CONTROLE DYNAMIQUE : un ARBITRE sur des candidats, pas une carte.

LES DEUX PRIORS QUI DESSINENT L ARCHITECTURE
. <champ-spatial-ne-sapprend-pas> : le controle positif d un apprenant spatial rend 50,5 %
  sur 16 797 cas — LE HASARD. On n apprend donc PAS de carte : le monde CALCULE la geometrie
  (terrainIntersectASL puis lineIntersectsSurfaces — les primitives de champ2.py, etendue
  mesuree 13,5 sur 8 directions, 0 % de directions identiques).
. <greffe-le-credit-est-coupable> : +15,3 pts recoltes SANS gradient en SELECTIONNANT parmi
  des candidats evalues par le monde ; ZERO quand la meme information entre dans un apprenant.
  L intelligence est donc dans l ARBITRAGE, pas dans un modele.

CE QUE FAIT CE FICHIER, par homme, toutes les 5-15 s (asynchrone, re-decision anticipee
sur evenement : FiredNear, Hit, contact NOUVEAU au journal) :
  1. K candidats : 8 directions x 2 portees (15 et 30 m) + « continuer » + « rester » ;
  2. le MOTEUR annote chaque candidat contre le JOURNAL de contacts (jamais contre la
     verite-terrain) : etre-vu, voir, possibilite de supprimer depuis la ;
  3. un score en COMPOSITION MONOTONE — chaque coefficient est une MESURE, ou un seuil
     DIMENSIONNE et il le dit en commentaire ;
  4. UN candidat choisi par ECHANTILLONNAGE (jamais argmax fige : <decision-laisser-hesiter>
     — deployer fige un objet optimise stochastique etait une hypothese heritee ;
     <recette-loterie> — 49,6 % ou 3,3 % selon la graine en argmax), emis en doMove 15-30 m.

SANS ETAT DE FORME : chaque re-decision part d ou les hommes SONT (lus au moteur), jamais
d ou ils ont ete envoyes. Aucun terme d erreur vers une disposition : ce terme EST
l hypothese refutee (0/15 formes atteintes sous le feu ; allongement p=0,204).

DEUX REGIMES, BIT EXPLICITE : avant contact la geometrie est bon marche (8/8 formes
assemblees en 10-15 s en monde vide) — l espacement et le tempo se paient LA. Au premier
FiredNear le bit bascule, irreversible pour l episode : il ne reste que le score.

JOURNAL DE CONTACTS A NOUS, horodate, avec decroissance ECRITE PAR NOUS :
<knowsabout-est-de-camp-pas-de-soldat> — knowsAbout est de CAMP et ne decroit JAMAIS ;
on ne s en sert que comme detecteur de premiere decouverte, et la position d un contact
n est rafraichie que s il est VU maintenant ou s il vient de TIRER (evenement).

⚠️ GOTCHAS DEJA PAYES, respectes ici :
  - retour par HMT_EMIT, jamais diag_log ; AUCUN champ vide (sentinelle "0" sur tout blob) ;
  - aucun arithmeticMean sans garde de tableau vide ; jamais getPosATL sur une POSITION ;
  - lineIntersectsSurfaces (pas *Surfs) ; pas de BIS_fnc_checkVisibility ;
  - suivi par IDENTIFIANT (setVariable "hid"), jamais par index de liste ;
  - le MEME doMove n est JAMAIS re-emis (c est la re-emission en boucle du meme ordre qui
    CASSE le calcul de chemin — payee a 12 s puis a 20 s) ; « continuer » = ne rien emettre.
"""
import sys, math, time, random
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))

# ─── LES TARIFS : des MESURES. Aucun poids appris. ───────────────────────────────────────
TARIF_VU         = 2.45   # MESURE — DEPOT_BARREAU 26/08 : rapport de taux de mort « vu »,
                          # 432 transitions, blocs tenus a l ecart. Meme constante que prix_hybride.
TARIF_SUPP_SUBIE = 29.81  # MESURE — meme depot : taux de mort sous suppression x29,81.
                          # C est le tarif du « feu recu recent » : etre vu PENDANT qu on est
                          # arrose coute ce prix-la, pas 2,45.
RATIO_VU_VOIR    = 2.0    # MESURE — etre VU tue 2x plus fort que VOIR ne protege :
                          # +75 % sur 563 000 observations. Le credit de « voir » vaut donc
                          # TARIF_VU / 2.
COTE_SUPP        = 27.9   # MESURE — rapport de cotes de la suppression (contre x1,19-2,45
                          # pour « vu ») : la suppression DOMINE le score. Supprimer un
                          # contact rachete (1 - 1/27,9) = 96 % de l exposition a ce contact.

# ─── LES SEUILS : DIMENSIONNES, pas mesures — et chacun le dit. « Un seuil se dimensionne »
#     (<champ-spatial>). Aucun ne sera ajuste APRES lecture des donnees du banc. ─────────
PORTEES          = (15.0, 30.0)     # SPECIFICATION — segment borne 15-30 m ; jamais une forme.
LAMBDA_METRE     = TARIF_VU / 30.0  # DIMENSIONNE : taux de change « exposition par metre
                                    # GAGNE » — un segment plein (30 m) vaut UN etre-vu (2,45).
                                    # Definition operatoire de <cout-exposition-par-metre>
                                    # (« les gagnants ENTRENT »). A recalibrer sur mesure dediee.
PENTE_IMMOBILITE = TARIF_VU / 30.0  # DIMENSIONNE : 30 s immobile = un etre-vu. La MONOTONIE
                                    # SANS PLATEAU est la specification ; le chiffre a battre
                                    # est le tarif de la tenue deja chiffre : 31,4 % -> 19,9 %,
                                    # ~11,5 pts. Seul acheteur legitime : la suppression
                                    # (credit COTE_SUPP ci-dessus, rien d autre ne paie).
SEG_ANTICIPE     = 10.0             # s — l immobilite du segment A VENIR est facturee d avance
                                    # (milieu de la cadence 5-15 s).
TAU_JOURNAL      = 40.0             # s — DIMENSIONNE : la decroissance du journal, ECRITE PAR
                                    # NOUS. ~ le temps qu un contact qui marche rende sa
                                    # derniere position perimee (100 m a 2,5 m/s).
TAU_FEU          = 12.0             # s — DIMENSIONNE : fenetre du « feu recu recent ».
TAU_CHOIX        = TARIF_VU / 2.0   # temperature d echantillonnage : les quasi-ex-aequo a un
                                    # demi « vu » pres RESTENT en jeu. <decision-laisser-hesiter>.
SEG_MIN, SEG_MAX = 5.0, 15.0        # SPECIFICATION — cadence segment, asynchrone par homme ;
                                    # ni 50 Hz, ni 15-30 s.
REDECISION_MIN   = 3.0              # s — plancher de la re-decision anticipee sur evenement.
EMISSION_MIN     = 5.0              # s — gotcha paye : re-emettre un doMove trop souvent CASSE
                                    # le calcul de chemin. Le defaut paye etait la re-emission
                                    # du MEME ordre en boucle ; ici chaque emission est une
                                    # destination NOUVELLE, et ce plancher protege en plus.
PROGRES_AVANT_CONTACT = 2.0         # DIMENSIONNE — regime AVANT contact : la geometrie est bon
                                    # marche (8/8 en 10-15 s en monde vide) ; le +8,8 du
                                    # catalogue se touche en ENTRANT bien dispose, jamais en
                                    # reparant sous le feu.
ESPACEMENT_MIN   = 8.0              # m — DIMENSIONNE : anti-tas, paye AVANT contact SEULEMENT
                                    # (apres le premier FiredNear il ne reste que le score).
PORTEE_SUPP      = 300.0            # m — DIMENSIONNE : portee utile pour supprimer (5,56 en jeu).

# ─── LE SQF. Quatre requetes, toutes gardees par sentinelle "0" (jamais de champ vide). ──
SQF_ARMER = (
    'if (isNil "HMT_OBJ") then { HMT_OBJ = HMT_POS vectorAdd [0, 450, 0] };'
    'HMT_EVT = [];'
    '{ _x setVariable ["eid", _forEachIndex] } forEach units HMT_GO;'
    '{ private _v = _x;'
    '  _v addEventHandler ["FiredNear", { params ["_h","_t"];'
    '    if (!isNull _t && {side _t == east}) then { private _p = getPosATL _t;'
    '      HMT_EVT pushBack [1, round time, _h getVariable ["hid",-1], _t getVariable ["eid",-1],'
    '        round (_p select 0), round (_p select 1)] } }];'
    '  _v addEventHandler ["Hit", { params ["_h","_s"];'
    '    private _e = -1; private _px = 0; private _py = 0;'
    '    if (!isNull _s && {side _s == east}) then { _e = _s getVariable ["eid",-1];'
    '      private _p = getPosATL _s; _px = round (_p select 0); _py = round (_p select 1) };'
    '    HMT_EVT pushBack [2, round time, _h getVariable ["hid",-1], _e, _px, _py] }];'
    '} forEach units HMT_GB;'
)

# etat + decouvertes + drainage des evenements, en UNE requete par tic.
SQF_ETAT = (
    'HMT_RB = ""; HMT_RO = ""; HMT_RE = "";'
    'private _amis = (units HMT_GB select {alive _x});'
    'HMT_NBB = count _amis;'
    '{ private _p = getPosATL _x;'
    '  HMT_RB = HMT_RB + format ["%1;%2;%3;%4|", _x getVariable ["hid",-1],'
    '    round (_p select 0), round (_p select 1), round (1000 * getSuppression _x)];'
    '} forEach _amis;'
    # decouverte : knowsAbout de CAMP comme DETECTEUR ; le bit _vu dit si le contact est vu
    # MAINTENANT par au moins un ami (seule condition de rafraichissement de sa position).
    '{ private _e = _x;'
    '  if ((west knowsAbout _e) > 1.5) then {'
    '    private _pe = getPosATL _e; private _vu = 0;'
    '    { if (_vu == 0) then {'
    '        private _a = eyePos _x; private _c = getPosASL _e; _c set [2, (_c select 2) + 1.0];'
    '        if !(terrainIntersectASL [_a, _c]) then {'
    '          if (count (lineIntersectsSurfaces [_a, _c, _x, _e]) == 0) then { _vu = 1 } } } } forEach _amis;'
    '    HMT_RO = HMT_RO + format ["%1;%2;%3;%4|", _e getVariable ["eid",-1],'
    '      round (_pe select 0), round (_pe select 1), _vu];'
    '  };'
    '} forEach (units HMT_GO select {alive _x});'
    '{ _x params ["_k","_t","_h","_ei","_ex","_ey"];'
    '  HMT_RE = HMT_RE + format ["%1;%2;%3;%4;%5;%6|", _k, _t, _h, _ei, _ex, _ey];'
    '} forEach HMT_EVT;'
    'HMT_EVT = [];'
    'if (HMT_RB == "") then { HMT_RB = "0" };'
    'if (HMT_RO == "") then { HMT_RO = "0" };'
    'if (HMT_RE == "") then { HMT_RE = "0" };'
)

# annotation des candidats — les primitives EXACTES de champ2/prix_hybride : relief d abord
# (bon marche), surfaces ensuite. Contacts et candidats INJECTES en positions (__CTC__,
# __DEM__) : l annotation se fait contre le JOURNAL, jamais contre la verite-terrain.
SQF_ANNOTER = (
    'HMT_RA = "";'
    'private _ctc = __CTC__;'
    '{ _x params ["_h","_cl"];'
    '  private _u = objNull;'
    '  { if ((_x getVariable ["hid",-1]) == _h) exitWith { _u = _x } } forEach (units HMT_GB select {alive _x});'
    '  if (!isNull _u) then {'
    '    HMT_RA = HMT_RA + format ["%1", _h];'
    '    { _x params ["_cx","_cy"];'
    '      private _zt = getTerrainHeightASL [_cx,_cy];'
    '      private _oeil = [_cx,_cy,_zt+1.5]; private _torse = [_cx,_cy,_zt+1.0];'
    '      private _vw = 0; private _rw = 0; private _ns = 0;'
    '      { _x params ["_ex","_ey","_w"];'
    '        private _ze = getTerrainHeightASL [_ex,_ey];'
    '        private _eo = [_ex,_ey,_ze+1.6]; private _et = [_ex,_ey,_ze+1.0];'
    # etre-vu : de l oeil du contact vers le torse du candidat
    '        if !(terrainIntersectASL [_eo,_torse]) then {'
    '          if (count (lineIntersectsSurfaces [_eo,_torse,_u,objNull]) == 0) then { _vw = _vw + _w } };'
    # voir : de l oeil du candidat vers le torse du contact ; supprimer = voir a portee utile
    '        if !(terrainIntersectASL [_oeil,_et]) then {'
    '          if (count (lineIntersectsSurfaces [_oeil,_et,_u,objNull]) == 0) then {'
    '            _rw = _rw + _w;'
    '            if (([_cx,_cy,0] distance2D [_ex,_ey,0]) < 300) then { _ns = _ns + 1 } } };'
    '      } forEach _ctc;'
    '      HMT_RA = HMT_RA + format [";%1;%2;%3", _vw, _rw, _ns];'
    '    } forEach _cl;'
    '    HMT_RA = HMT_RA + "|";'
    '  };'
    '} forEach __DEM__;'
    'if (HMT_RA == "") then { HMT_RA = "0" };'
)

SEL_HOMME = ('private _u = objNull;'
             '{ if ((_x getVariable ["hid",-1]) == %d) exitWith { _u = _x } }'
             ' forEach (units HMT_GB select {alive _x});')

# mesure de fin d episode — garde du tableau vide (arithmeticMean sur [] a tue deux runs).
SQF_MESURE = (
    'private _v = (units HMT_GB select {alive _x});'
    'HMT_MD = if (count _v > 0) then {'
    '  round ((_v apply { _x distance2D HMT_OBJ }) call BIS_fnc_arithmeticMean) } else { -1 };'
) + E("HMTAM v=%1 d=%2 a=%3",
      "count (units HMT_GB select {alive _x})",
      "{ (west knowsAbout _x) > 1.5 } count (units HMT_GO)",
      "HMT_MD")


class Homme:
    def __init__(self, hid):
        self.hid = hid
        self.pos = (0.0, 0.0)
        self.sup = 0.0
        self.t_immobile = 0.0     # mesuree sur la POSITION lue, jamais sur l ordre emis
        self.t_feu = 0.0
        self.t_prochaine = 0.0    # prochaine decision reguliere (tirage 5-15 s, par homme)
        self.t_decision = 0.0
        self.t_emission = 0.0
        self.dest = None          # derniere destination EMISE (pour « continuer » et pour ne
                                  # jamais re-emettre le meme doMove)
        self.stoppe = False
        self.evenement = False    # re-decision anticipee demandee


class Arbitre:
    """mode : 'arbitre' (score normal) | 'uniforme' (score ignore, temoin) |
              'anti' (signes des termes TARIFES inverses) | 'melange' (annotations permutees
              entre candidats avant scorage). Les quatre partagent candidats et execution :
              seul le SCORE varie — c est ce que le controle positif isole."""

    def __init__(self, b, mode="arbitre", graine_ech=0):
        self.b = b
        self.mode = mode
        self.rng = random.Random(graine_ech)
        self.hommes = {}
        self.journal = {}          # eid -> {t, pos, w} : A NOUS, horodate, decroissance ecrite ici
        self.contact = False       # LE BIT DE REGIME — bascule au premier FiredNear, irreversible
        self.obj = None
        self.t_etat = None
        self.hist = []             # (t, vivants, dist moyenne a l objectif) — cote Python
        self.feu_total = 0
        self.feu_inconnu = 0       # tirs recus dont l eid n etait PAS au journal (lecture
                                   # perdante n.1 « contre l inconnu », diagnostiquee ici)

    # ─── armement (APRES la scene) ───────────────────────────────────────────────────────
    def armer(self):
        r = self.b.query(SQF_ARMER + E("HMTAA %1 %2 %3",
                                       "round (HMT_OBJ select 0)", "round (HMT_OBJ select 1)",
                                       "count (units HMT_GB select {alive _x})"),
                         r"HMTAA (-?\d+) (-?\d+) (\d+)", want=1, timeout=30)
        if not r:
            raise RuntimeError("armement sans reponse")
        self.obj = (float(r[0].group(1)), float(r[0].group(2)))
        return int(r[0].group(3))

    def d_obj(self, p):
        return math.hypot(p[0] - self.obj[0], p[1] - self.obj[1])

    def dist_moy(self):
        if not self.hommes:
            return None
        return float(np.mean([self.d_obj(h.pos) for h in self.hommes.values()]))

    # ─── lecture d etat + evenements + journal, un tic ──────────────────────────────────
    def lire_etat(self):
        now = time.time()
        r = self.b.query(SQF_ETAT + E("HMTAE %1 %2 %3 %4", "HMT_NBB", "HMT_RB", "HMT_RO", "HMT_RE"),
                         r"HMTAE (\d+) (\S+) (\S+) (\S+)", want=1, timeout=30)
        if not r:
            return False
        rb, ro, rev = r[0].group(2), r[0].group(3), r[0].group(4)
        dt = (now - self.t_etat) if self.t_etat else 0.0
        vivants = set()
        if rb != "0":
            for seg in rb.split("|"):
                if not seg:
                    continue
                hid, x, y, s = (int(v) for v in seg.split(";"))
                vivants.add(hid)
                h = self.hommes.get(hid)
                if h is None:
                    h = Homme(hid)
                    h.pos = (float(x), float(y))
                    # cadence ASYNCHRONE des le depart : premiers tirages etales sur 0-15 s
                    h.t_prochaine = now + self.rng.uniform(0.0, SEG_MAX)
                    self.hommes[hid] = h
                else:
                    if math.hypot(x - h.pos[0], y - h.pos[1]) < 1.5:
                        h.t_immobile += dt      # immobilite : la POSITION, pas l ordre
                    else:
                        h.t_immobile = 0.0
                    h.pos = (float(x), float(y))
                h.sup = s / 1000.0
        for hid in list(self.hommes):            # suivi par IDENTIFIANT, jamais par index
            if hid not in vivants:
                del self.hommes[hid]
        # evenements draines par la MEME requete (HMT_EVT remis a [] cote serveur)
        if rev != "0":
            for seg in rev.split("|"):
                if not seg:
                    continue
                v = [int(z) for z in seg.split(";")]
                if len(v) != 6:
                    continue
                _k, _t, hid, eid, ex, ey = v
                self.feu_total += 1
                if eid < 0 or eid not in self.journal:
                    self.feu_inconnu += 1
                if not self.contact:
                    self.contact = True          # premier FiredNear : le referent de forme
                                                 # est ABANDONNE, il ne reste que le score
                h = self.hommes.get(hid)
                if h:
                    h.t_feu = now
                    h.evenement = True
                if eid >= 0 and (ex or ey):
                    self.journal[eid] = dict(t=now, pos=(float(ex), float(ey)))
        # decouvertes : premiere entree au journal a la premiere lecture (knowsAbout ne
        # decroit jamais -> la premiere apparition EST le franchissement) ; ensuite la
        # position n est rafraichie que si le contact est VU maintenant.
        if ro != "0":
            for seg in ro.split("|"):
                if not seg:
                    continue
                eid, x, y, vu = (int(v) for v in seg.split(";"))
                if eid not in self.journal:
                    self.journal[eid] = dict(t=now, pos=(float(x), float(y)))
                    for h in self.hommes.values():   # contact NOUVEAU : re-decision anticipee
                        if math.hypot(h.pos[0] - x, h.pos[1] - y) < 300:
                            h.evenement = True
                elif vu:
                    self.journal[eid] = dict(t=now, pos=(float(x), float(y)))
        # LA DECROISSANCE — la notre, exponentielle, TAU_JOURNAL
        for eid in list(self.journal):
            w = math.exp(-(now - self.journal[eid]["t"]) / TAU_JOURNAL)
            if w < 0.05:
                del self.journal[eid]
            else:
                self.journal[eid]["w"] = w
        self.t_etat = now
        d = self.dist_moy()
        if d is not None:
            self.hist.append((now, len(vivants), d))
        return True

    # ─── candidats : 8 directions x 2 portees + continuer + rester ──────────────────────
    def candidats(self, h):
        c = []
        d0 = self.d_obj(h.pos)
        for d in range(8):
            a = math.radians(d * 45)
            for r in PORTEES:
                x = h.pos[0] + r * math.sin(a)
                y = h.pos[1] + r * math.cos(a)
                c.append(dict(label="d%dr%d" % (d, int(r)), x=x, y=y,
                              metres=d0 - self.d_obj((x, y))))
        if h.dest is not None and math.hypot(h.dest[0] - h.pos[0], h.dest[1] - h.pos[1]) > 3.0:
            c.append(dict(label="continuer", x=h.dest[0], y=h.dest[1],
                          metres=d0 - self.d_obj(h.dest)))
        c.append(dict(label="rester", x=h.pos[0], y=h.pos[1], metres=0.0))
        return c

    # ─── annotation par le moteur, tous les hommes decideurs en UNE requete ─────────────
    def annoter(self, demandes):
        ctc = ",".join("[%d,%d,%d]" % (int(e["pos"][0]), int(e["pos"][1]), int(1000 * e["w"]))
                       for e in self.journal.values())
        dem = ",".join("[%d,[%s]]" % (h.hid, ",".join("[%d,%d]" % (int(c["x"]), int(c["y"]))
                                                      for c in cands))
                       for h, cands in demandes)
        sqf = SQF_ANNOTER.replace("__CTC__", "[%s]" % ctc).replace("__DEM__", "[%s]" % dem)
        r = self.b.query(sqf + E("HMTAC %1", "HMT_RA"), r"HMTAC (\S+)", want=1, timeout=30)
        out = {}
        if not r or r[0].group(1) == "0":
            return out
        for seg in r[0].group(1).split("|"):
            if not seg:
                continue
            v = seg.split(";")
            vals = v[1:]
            if len(vals) % 3:
                continue
            out[int(v[0])] = [(int(vals[i]) / 1000.0, int(vals[i + 1]) / 1000.0, int(vals[i + 2]))
                              for i in range(0, len(vals), 3)]
        return out

    # ─── LE SCORE : composition monotone, coefficients mesures ──────────────────────────
    def scorer(self, h, cands, ann):
        if self.mode == "uniforme":
            return np.zeros(len(cands))          # temoin : memes candidats, meme execution,
                                                 # le score seul est retire
        now = time.time()
        feu = math.exp(-(now - h.t_feu) / TAU_FEU) if h.t_feu else 0.0
        wmax = max((e["w"] for e in self.journal.values()), default=0.0)
        # 'anti' : signes des SEULS termes tarifes inverses (maximiser etre-vu, penaliser la
        # suppression). Progres et immobilite gardent leur signe : l anti perd — s il perd —
        # par l EXPOSITION, pas parce qu on l aurait envoye fuir l objectif.
        signe = -1.0 if self.mode == "anti" else 1.0
        s = []
        for c, (vw, rw, ns) in zip(cands, ann):
            # etre vu coute 2,45 ; etre vu SOUS LE FEU RECENT coute jusqu a 29,81
            # (interpolation monotone entre les deux tarifs mesures du DEPOT_BARREAU)
            tarif_vu_eff = TARIF_VU + feu * (TARIF_SUPP_SUBIE - TARIF_VU)
            expo = - tarif_vu_eff * vw
            expo += (TARIF_VU / RATIO_VU_VOIR) * rw          # voir protege 2x moins (+75 %, 563k)
            if ns > 0:
                # pouvoir supprimer rachete jusqu a (1 - 1/27,9) = 96 % de l exposition au
                # contact le plus lourd visible (borne par rw : somme des poids visibles)
                expo += TARIF_VU * (1.0 - 1.0 / COTE_SUPP) * min(wmax, rw)
            v = signe * expo
            prog = LAMBDA_METRE * c["metres"]
            if not self.contact:
                prog *= PROGRES_AVANT_CONTACT                # la geometrie est bon marche AVANT
                dmin = min((math.hypot(c["x"] - a.pos[0], c["y"] - a.pos[1])
                            for a in self.hommes.values() if a.hid != h.hid), default=1e9)
                if dmin < ESPACEMENT_MIN:                    # l espacement se paie avant contact,
                    v -= TARIF_VU / 2.0                      # jamais sous le feu
            v += prog
            if c["label"] == "rester":
                # cout MONOTONE, SANS PLATEAU, du temps immobile consecutif — le segment a
                # venir est facture d avance. Seul acheteur legitime : le credit suppression.
                v -= PENTE_IMMOBILITE * (h.t_immobile + SEG_ANTICIPE)
            s.append(v)
        return np.array(s)

    def echantillonner(self, s):
        z = (s - s.max()) / TAU_CHOIX
        p = np.exp(z)
        p = p / p.sum()
        return int(self.rng.choices(range(len(s)), weights=list(p))[0])

    # ─── decision + emission ────────────────────────────────────────────────────────────
    def decider(self, dus):
        demandes = [(h, self.candidats(h)) for h in dus]
        ann = self.annoter(demandes)
        now = time.time()
        ordres = []
        for h, cands in demandes:
            a = ann.get(h.hid)
            if not a or len(a) != len(cands):
                continue                          # homme mort ou reponse partielle : on passe
            if self.mode == "melange":
                a = list(a)
                self.rng.shuffle(a)               # annotations MELANGEES entre candidats :
                                                  # l arbitre doit retomber sur l uniforme
            s = self.scorer(h, cands, a)
            k = self.echantillonner(s)
            ordres.append((h, cands[k]))
            h.t_decision = now
            h.t_prochaine = now + self.rng.uniform(SEG_MIN, SEG_MAX)
            h.evenement = False
        self.emettre(ordres)

    def contact_le_plus_lourd(self):
        if not self.journal:
            return None
        e = max(self.journal.values(), key=lambda z: z["w"])
        return (int(e["pos"][0]), int(e["pos"][1]))

    def emettre(self, ordres):
        now = time.time()
        cmds = []
        for h, c in ordres:
            if c["label"] == "continuer":
                continue                                          # NE RIEN re-emettre (gotcha)
            if c["label"] == "rester":
                if not h.stoppe:
                    cible = self.contact_le_plus_lourd()
                    watch = (' _u doWatch [%d,%d,0];' % cible) if cible else ''
                    cmds.append(SEL_HOMME % h.hid +
                                'if (!isNull _u) then { doStop _u;%s };' % watch)
                    h.dest = None
                    h.stoppe = True
                    h.t_emission = now
                continue
            if now - h.t_emission < EMISSION_MIN:
                continue                                          # plancher d emission
            if h.dest is not None and math.hypot(c["x"] - h.dest[0], c["y"] - h.dest[1]) < 5.0:
                continue                                          # JAMAIS le meme doMove
            cmds.append(SEL_HOMME % h.hid +
                        'if (!isNull _u) then { _u doMove [%d,%d,0] };'
                        % (int(c["x"]), int(c["y"])))
            h.dest = (c["x"], c["y"])
            h.stoppe = False
            h.t_emission = now
        if cmds:
            self.b.query("".join(cmds) + E("HMTAO %1", "1"), r"HMTAO (\d+)", want=1, timeout=30)

    def mesurer(self):
        r = self.b.query(SQF_MESURE, r"HMTAM v=(\d+) d=(\d+) a=(-?\d+)", want=1, timeout=30)
        return tuple(int(g) for g in r[0].groups()) if r else (None, None, None)

    # ─── la boucle ──────────────────────────────────────────────────────────────────────
    def boucle(self, duree=300, tic=1.0):
        fin = time.time() + duree
        while time.time() < fin:
            t0 = time.time()
            if not self.lire_etat():
                break
            if not self.hommes:
                break                                             # force aneantie
            dus = [h for h in self.hommes.values()
                   if t0 >= h.t_prochaine
                   or (h.evenement and t0 - h.t_decision >= REDECISION_MIN)]
            if dus:
                self.decider(dus)
            reste = tic - (time.time() - t0)
            if reste > 0:
                time.sleep(reste)


if __name__ == "__main__":
    import argparse
    from marge import scene
    ap = argparse.ArgumentParser(description="un episode de demonstration (mode arbitre)")
    ap.add_argument("--graine", type=int, default=0)
    ap.add_argument("--duree", type=int, default=300)
    a = ap.parse_args()
    print("=" * 92)
    print(" L ARBITRE — episode de demonstration, graine %d, %d s" % (a.graine, a.duree))
    print("=" * 92, flush=True)
    b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        scene(b, a.graine)
        time.sleep(3)
        arb = Arbitre(b, mode="arbitre", graine_ech=a.graine)
        n = arb.armer()
        v0, d0, _ = arb.mesurer()
        print("  %d hommes armes, objectif (%d, %d)" % (n, arb.obj[0], arb.obj[1]), flush=True)
        arb.boucle(a.duree)
        v1, d1, _ = arb.mesurer()
        av = (arb.hist[0][2] - arb.hist[-1][2]) if len(arb.hist) >= 2 else 0.0
        print("  vivants %s -> %s   decouverte %s -> %s   avance %.0f m   feu inconnu %d/%d"
              % (v0, v1, d0, d1, av, arb.feu_inconnu, arb.feu_total))
    finally:
        if b:
            try:
                b.close()
            except Exception:
                pass
