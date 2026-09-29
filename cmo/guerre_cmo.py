"""LE CÔTÉ CMO DE LA GUERRE DES ÎLES : la langue d'ArmaGuerre ( guerre/arma.py ), parlée à Command: Modern Operations
par le pont cmo_labo. L'horloge de guerre ( guerre/horloge.py ) prend l'un ou l'autre sans rien changer :
ouvrir / fermer / tour( points, reserves ) / positions().

UNE GUERRE AÉRIENNE. Chaque île achète des avions avec les points que son économie verse ( guerre/bourse.py ) ; chaque
avion a pour pilote un habitant de son île ( un numéro de front que le moteur a mobilisé ) ; un avion abattu est un
pilote mort au combat. Les zones du champ de bataille ( guerre/zones.py, en mètres sur la carte Arma de l'île ) sont
posées sur une île réelle de la mer Égée par Geo ; une zone est TENUE par le camp qui a le ciel au-dessus d'elle.

Un tour = 4 envois au plus ( relevé, achats, ordres, canari ) : tous les ordres d'un tour partent ensemble.

CHOIX PRIS EN COPIANT LE RÉEL, À TRANCHER PAR YOUNES ( rapport du 29/09 ) — chacun est une constante ci-dessous :
- ILES_REELLES : Stratis sur Ágios Efstrátios ( l'île réelle que Bohemia a copiée pour Stratis ), Malden sur Skyros
  ( île réelle du même ordre de taille, avec une vraie base aérienne ), à ~75 km l'une de l'autre ;
- CATALOGUE : un seul avion, le F-15C ( dbid 3500, loadout 16934 : le seul prouvé dans CMO ), 50 M€ pièce ( ordre de
  grandeur réel d'un chasseur lourd ), soit 500 000 points à 100 € le point ;
- RAYON_CIEL_M = 5 km : un camp tient une zone quand il a au moins un avion à moins de 5 km de son centre et que l'autre
  n'en a aucun ; sinon la zone garde son dernier maître. Dans le réel, une aviation interdit, elle n'occupe pas : à
  remplacer par un blocus quand le moteur saura le dire ;
- PLAFOND_AVIONS = 12 en vol par camp ; pas d'avion sans pilote ( pas d'achat sans numéro de front ) ;
- DOCTRINE v1 ( les MISSIONS de CMO ) : chaque camp a UNE patrouille de défense aérienne ( Patrol AAW ) sur un carré de
  DEMI_ZONE_KM autour de sa zone cible ; ses avions y sont affectés à l'achat, et c'est l'IA de CMO qui vole, engage et
  rentre. L'envahisseur vise la zone qu'il ne tient pas la plus proche de son aéroport ; le défenseur patrouille sur
  cette zone tant que l'envahisseur a des avions en vol, sinon sur la zone perdue la plus proche de son aéroport. Quand
  la cible change, ce sont les points de la zone qui bougent, pas les affectations ;
- les avions naissent en vol au-dessus de l'aéroport de leur île ( aucune base aérienne posée dans CMO : un avion à sec
  tombe, et c'est un pilote mort ).

FauxCMO ( faux_cmo.py ) sert à la porte ( porte_guerre_cmo.py ) : le vrai Lua, un faux Command. Une guerre dans le vrai
CMO attend le feu vert de Younes.
"""
import json
import math
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402

PAYS = os.path.join(os.path.dirname(ICI), "monde", "donnees", "pays")
CAMPS_ARMA = ("EAST", "WEST", "RESISTANCE")             # l'ordre des camps d'Arma ( guerre/arma.py )
CAMPS_HORLOGE = {"WEST": "Malden", "EAST": "Stratis"}   # = CAMPS de guerre/horloge.py
CHAMP = "Malden"
DECALAGE = 10_000_000                                    # numéro CMO = ( index du camp + 1 ) x DECALAGE + numéro de front

ILES_REELLES = {                                         # île : ( côté de la carte Arma en m, lat et lon réelles du centre )
    "Stratis": (8192.0, 39.525, 24.995),                 # Ágios Efstrátios
    "Malden": (12800.0, 38.870, 24.550),                 # Skyros
}
CATALOGUE = {"nom": "F-15C", "dbid": 3500, "loadout": 16934, "alt_m": 6000.0, "prix_points": 500_000.0}
RAYON_CIEL_M = 5000.0
DEMI_ZONE_KM = 3.5                                       # la diagonale du carré ( 4,9 km ) reste sous RAYON_CIEL_M
PLAFOND_AVIONS = 12
M_PAR_DEG = 111_320.0


class Geo:
    """Le repère en mètres d'une carte Arma posé sur la Terre, centre sur centre ( équirectangulaire : sur 13 km, l'erreur
    est de l'ordre du mètre ). x vers l'est, y vers le nord, comme dans Arma."""

    def __init__(self, cote, lat0, lon0):
        self.c, self.lat0, self.lon0 = cote / 2.0, lat0, lon0
        self.m_lon = M_PAR_DEG * math.cos(math.radians(lat0))

    def vers_latlon(self, x, y):
        return self.lat0 + (y - self.c) / M_PAR_DEG, self.lon0 + (x - self.c) / self.m_lon

    def vers_xy(self, lat, lon):
        return self.c + (lon - self.lon0) * self.m_lon, self.c + (lat - self.lat0) * M_PAR_DEG


def aeroport(ile, pays=PAYS):
    """Le premier aéroport de l'île dans les données du moteur ( monde/donnees/pays/<ile>.json ), en mètres Arma."""
    with open(os.path.join(pays, f"{ile.lower()}.json")) as f:
        a = json.load(f)["aeroports"][0]
    return float(a["x"]), float(a["y"])


class CmoGuerre:
    def __init__(self, zones, *, camps=CAMPS_HORLOGE, champ=CHAMP, labo=None, labo_kw=None, catalogue=CATALOGUE,
                 plafond=PLAFOND_AVIONS, rayon_ciel_m=RAYON_CIEL_M, iles=ILES_REELLES, pays=PAYS):
        self.zones, self.camps, self.champ = zones, dict(camps), champ
        for camp, ile in self.camps.items():
            if camp not in CAMPS_ARMA[:2] or ile not in CL.CAMPS or ile not in iles:
                raise CL.Refus(f"camp {camp} -> île {ile} : inconnu du pont CMO ( {CL.CAMPS} ) ou sans île réelle")
        self.labo, self.labo_kw, self.possede = labo, labo_kw or {}, labo is None
        self.cat, self.plafond, self.rayon = dict(catalogue), int(plafond), float(rayon_ciel_m)
        self.geo = {ile: Geo(*iles[ile]) for ile in self.camps.values()}
        self.geo_champ = self.geo[champ]
        self.defenseur = next(c for c, ile in self.camps.items() if ile == champ)
        self.envahisseurs = [c for c in self.camps if c != self.defenseur]
        # l'aéroport de chaque camp, dans le repère du champ de bataille
        self.base = {c: self.geo_champ.vers_xy(*self.geo[ile].vers_latlon(*aeroport(ile, pays))) for c, ile in self.camps.items()}
        self.proprio = {}
        for z in zones:
            base = z.get("genre") == "base" and z.get("camp_base") in (0, 1)
            self.proprio[z["n"]] = CAMPS_ARMA[z["camp_base"]] if base else self.defenseur
        self.caisse = {c: 0.0 for c in self.camps}
        self.verse = {c: 0.0 for c in self.camps}
        self.depense = {c: 0.0 for c in self.camps}
        self.achats = {c: 0 for c in self.camps}
        self.pertes = {c: 0 for c in self.camps}
        self.pilotes = {c: [] for c in self.camps}       # numéros de front mobilisés, pas encore en vol
        self.connus = {c: set() for c in self.camps}
        self.en_vol = {c: set() for c in self.camps}
        self.cible = {c: None for c in self.camps}       # n de zone visée
        self.zone_mission = {}                           # camp -> n de zone où sa patrouille est posée dans CMO
        self.affectes = set()                            # ( camp, numéro ) affectés à la patrouille de leur camp
        self.morts_a_rendre = {c: [] for c in self.camps}
        self.ouvert = False

    # ---- numéros : chaque île numérote ses soldats depuis 1, CMO veut des noms uniques
    def _vers_cmo(self, camp, k):
        k = int(k)
        if not 0 < k < DECALAGE:
            raise CL.Refus(f"numéro de front {k} hors de ] 0 ; {DECALAGE} [")
        return (CAMPS_ARMA.index(camp) + 1) * DECALAGE + k

    def _depuis_cmo(self, kc):
        i, k = divmod(int(kc), DECALAGE)
        camp = CAMPS_ARMA[i - 1] if 1 <= i <= 2 else None
        return (camp, k) if camp in self.camps and k > 0 else (None, None)

    # ---- ouverture
    def ouvrir(self):
        if self.labo is None:
            self.labo = CL.Labo(**self.labo_kw).ouvrir()
        try:
            iles = list(self.camps.values())
            self.labo.hostiles(iles[0], iles[1])
            self._relever()                              # une reprise : les avions déjà en vol sont ceux de la guerre
        except BaseException:
            self.fermer()
            raise
        self.ouvert = True
        return self

    def fermer(self):
        if self.labo is not None and self.possede:
            self.labo.fermer()
            self.labo = None                             # une ouverture retentée repart d'un pont neuf
        self.ouvert = False

    # ---- le relevé : vivants dans le repère du champ, morts gardés jusqu'à positions()
    def _relever(self):
        p = self.labo.positions()
        vivants, vus = {c: [] for c in self.camps}, {c: set() for c in self.camps}
        for ile, liste in p["vivants"].items():
            for kc, lat, lon, _alt in liste:
                camp, k = self._depuis_cmo(kc)
                if camp is None:
                    continue                             # une unité HMT d'un autre usage ( labo, endurance )
                if self.camps[camp] != ile:
                    raise CL.Incomplet(f"l'avion {kc} du camp {camp} vole pour {ile} dans CMO")
                x, y = self.geo_champ.vers_xy(lat, lon)
                vivants[camp].append((k, x, y))
                vus[camp].add(k)
                self.en_vol[camp].add(k)
                self.connus[camp].add(k)
        for ile, ks in p["morts"].items():
            for kc in ks:
                camp, k = self._depuis_cmo(kc)
                if camp is None:
                    continue
                self.en_vol[camp].discard(k)
                self.pertes[camp] += 1
                self.morts_a_rendre[camp].append(k)
        for camp in self.camps:
            perdus = self.en_vol[camp] - vus[camp]
            if perdus:
                raise CL.Incomplet(f"avions {sorted(perdus)} du camp {camp} ni vivants ni morts dans CMO")
        return vivants

    # ---- les achats : l'argent et les pilotes, sous le plafond ; les deux camps en un seul envoi
    def _acheter(self):
        lots, demandes = [], {}
        for camp, ile in self.camps.items():
            poses = []
            while (self.caisse[camp] >= self.cat["prix_points"] and self.pilotes[camp]
                   and len(self.en_vol[camp]) + len(poses) < self.plafond):
                k = self.pilotes[camp].pop(0)
                lat, lon = self.geo_champ.vers_latlon(*self.base[camp])
                decal = (len(poses) % 5) * 0.005            # quelques centaines de mètres entre deux avions
                poses.append((self._vers_cmo(camp, k), lat + decal, lon))
                self.caisse[camp] -= self.cat["prix_points"]
            if poses:
                lots.append((ile, "air", self.cat["dbid"], poses, self.cat["alt_m"], self.cat["loadout"]))
                demandes[camp] = poses
        if not lots:
            return
        r = self.labo.poser_lots(lots)
        for camp, poses in demandes.items():
            for kc, _lat, _lon in poses:
                _, k = self._depuis_cmo(kc)
                if kc in r["poses"]:
                    self.en_vol[camp].add(k)
                    self.connus[camp].add(k)
                    self.depense[camp] += self.cat["prix_points"]
                    self.achats[camp] += 1
                else:                                    # refusé par CMO : ni payé, ni pilote perdu
                    self.caisse[camp] += self.cat["prix_points"]
                    self.pilotes[camp].insert(0, k)

    # ---- le ciel : qui tient quelle zone
    def _ciel(self, vivants):
        for z in self.zones:
            if z.get("genre") == "base":
                continue
            presents = [c for c in self.camps
                        if any(math.hypot(x - z["x"], y - z["y"]) <= self.rayon for _, x, y in vivants[c])]
            if len(presents) == 1:
                self.proprio[z["n"]] = presents[0]

    # ---- la doctrine v1 : une patrouille par camp, déplacée quand la cible change ; les neufs y sont affectés
    def _mission(self, camp):
        return CAMPS_ARMA.index(camp) + 1

    def _ordonner(self):
        secteurs = [z for z in self.zones if z.get("genre") != "base"]
        for camp in self.envahisseurs:
            libres = [z for z in secteurs if self.proprio[z["n"]] != camp]
            bx, by = self.base[camp]
            self.cible[camp] = min(libres, key=lambda z: math.hypot(z["x"] - bx, z["y"] - by))["n"] if libres else None
        visees = [self.cible[c] for c in self.envahisseurs if self.cible[c] is not None and self.en_vol[c]]
        perdues = [z for z in secteurs if self.proprio[z["n"]] != self.defenseur]
        bx, by = self.base[self.defenseur]
        if visees:                                       # défendre la zone attaquée
            self.cible[self.defenseur] = visees[0]
        elif perdues:                                    # le ciel est libre : reprendre
            self.cible[self.defenseur] = min(perdues, key=lambda z: math.hypot(z["x"] - bx, z["y"] - by))["n"]
        else:
            self.cible[self.defenseur] = None
        patrouilles, affectations, deplacees = [], [], {}
        for camp, ile in self.camps.items():
            n = self.cible[camp]
            if n is not None and self.zone_mission.get(camp) != n:
                z = next(z for z in self.zones if z["n"] == n)
                patrouilles.append((self._mission(camp), ile, *self.geo_champ.vers_latlon(z["x"], z["y"]), DEMI_ZONE_KM))
                deplacees[camp] = n
            if n is not None or camp in self.zone_mission:   # une patrouille existe ( ou naît ) : y mettre les neufs
                neufs = [k for k in sorted(self.en_vol[camp]) if (camp, k) not in self.affectes]
                if neufs:
                    affectations.append((self._mission(camp), [self._vers_cmo(camp, k) for k in neufs]))
        if not patrouilles and not affectations:
            return
        r = self.labo.missions(patrouilles, affectations)
        self.zone_mission.update(deplacees)
        for kc in r["affectes"]:
            self.affectes.add(self._depuis_cmo(kc))

    # ---- l'interface de l'horloge
    def tour(self, points, reserves=None):
        for camp in self.camps:
            p = float(points.get(camp, 0.0))
            if not math.isfinite(p) or p < 0:
                raise CL.Refus(f"points à verser invalides : {points!r}")
            self.caisse[camp] += p
            self.verse[camp] += p
            for k in (reserves or {}).get(camp, []):
                k = int(k)
                if not 0 < k < DECALAGE:
                    raise CL.Refus(f"numéro de front hors de ] 0 ; {DECALAGE} [ : {k}")
                if k not in self.connus[camp] and k not in self.pilotes[camp]:
                    self.pilotes[camp].append(k)
        vivants = self._relever()                        # pertes d'abord : un avion abattu libère sa place
        self._acheter()
        self._ciel(vivants)
        self._ordonner()
        c = self.labo.canari()                           # le pont vit, le Lua et le build sont les bons
        temps = c["temps"]
        camps = {camp: {"verse_total": self.verse[camp], "caisse": self.caisse[camp], "vivants": len(self.en_vol[camp]),
                        "groupes": 0, "pertes": self.pertes[camp], "depense": self.depense[camp],
                        "achats": self.achats[camp], "pilotes": len(self.pilotes[camp]),
                        "cible": None if self.cible[camp] is None else
                        next((z["x"], z["y"]) for z in self.zones if z["n"] == self.cible[camp])}
                 for camp in self.camps}
        return {"zones": dict(self.proprio), "camps": camps, "temps": temps, "recu": c["recu"]}

    def positions(self):
        """( vivants, morts ) comme ArmaGuerre : vivants { camp : [ ( numéro de front, x, y, dégâts ) ] } dans le repère
        du champ de bataille ; morts { camp : [ numéro de front ] }, chacun rendu UNE fois, même vu pendant un tour.
        Dégâts à 0 : le pont ne les lit pas encore."""
        vivants = self._relever()
        morts, self.morts_a_rendre = self.morts_a_rendre, {c: [] for c in self.camps}
        return {c: [(k, x, y, 0.0) for k, x, y in v] for c, v in vivants.items()}, morts
