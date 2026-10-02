"""LA GUERRE DES BLOCS dans CMO : OTAN contre Russie-Chine sur un théâtre ( theatres/<nom>.py ), en capture de drapeaux
comme les secteurs Warlords d'Arma ( demande de Younes, 29/09 ). Chaque pays achète sur son vrai catalogue ( catalogue.py )
avec son vrai budget ( budgets.py ) ; ses avions sont posés sur ses bases réelles ( ou chez un hôte ), décollent en mission
de CMO, et c'est l'IA de CMO qui vole et combat. Un tour = 4 envois : relevé, achats, missions, canari.

LES RÈGLES ( chacune est une constante, à valider par Younes ) :
- un drapeau change de main quand un camp est SEUL dans le ciel à moins de RAYON_KM pendant TENUE_TOURS tours de suite
  ( guerre du 29/09 : un seul avion de passage faisait basculer une zone, 116 bascules en 6 h ) ; SEULS LES AVIONS EN VOL
  ( plus de EN_VOL_M ) comptent : un avion garé ne tient pas le ciel ( guerre du 29/09 au 30/09 : 21 avions russes cloués
  au sol à Tchkalovsk ont bloqué ce drapeau 160 tours sous 18 avions de l'OTAN ) ;
- prendre le QG adverse gagne la guerre ; sinon le score cumule la valeur des drapeaux tenus à chaque tour ;
- chaque pays reçoit par tour son budget d'équipement du théâtre, plus un crédit de départ de CREDIT_INITIAL_MIN minutes ;
  il achète la famille la plus chère qu'il peut payer, et la pose sur celle de ses bases qui a le moins d'avions ;
- MASSE : l'offensive d'un camp ne part qu'avec MASSE avions d'un coup ( 29/09 : l'envahisseur arrivait un par un et
  perdait 32 avions sur 32 ) ; un tiers de la flotte tient la patrouille défensive ( règle du tiers de CMO ), l'offensive
  part en entier ;
- PLAFOND_TOTAL avions vivants pour tout le théâtre ( CMO doit tenir la cadence ), partagés entre les camps AU PRORATA DE
  LEUR BUDGET : un plafond égal donnait à l'OTAN, 3,3 fois plus riche, autant d'avions que la Russie ( essai du 29/09 ).

Numéros ( que des nombres vers CMO ) : avion = DEC_AVION + ( index du pays + 1 ) x 100 000 + rang d'achat ; installation
= DEC_BASE + n du drapeau + 1 ; patrouille = index du camp x 10 + 1 ( offensive ) ou + 2 ( défense )."""
import importlib
import math
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import budgets as BU                                      # noqa: E402

DEC_AVION, DEC_BASE = 10_000_000, 90_000_000
RAYON_KM = 25.0
TENUE_TOURS = 3
MASSE = 6
PART_DEFENSE = 1 / 3
CREDIT_INITIAL_MIN = 30.0
PLAFOND_TOTAL = 96
DEMI_ZONE_KM = 15.0
EN_VOL_M = 500.0                                         # altitude de CMO ; les bases du théâtre sont sous 250 m
CAPACITE_BASE = 120                                      # 80 hangars et 40 places ( Single-Unit Airfield )


def km(a, b):
    """Distance de grand cercle en km entre deux ( lat, lon )."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


class GuerreBlocs:
    def __init__(self, theatre="baltique", *, labo=None, labo_kw=None, catalogue=None, periode_min=1.0,
                 rayon_km=RAYON_KM, tenue=TENUE_TOURS, masse=MASSE, plafond=PLAFOND_TOTAL, credit_initial_min=CREDIT_INITIAL_MIN):
        self.T = importlib.import_module(f"theatres.{theatre}")
        self.camps, self.pays = tuple(self.T.CAMPS), list(self.T.PAYS)
        if catalogue is None:
            import catalogue as CAT
            catalogue = {p: CAT.catalogue(p) for p in self.pays}
        self.cat = {p: sorted(catalogue.get(p, []), key=lambda x: -x["prix_m"]) for p in self.pays}
        self.labo, self.labo_kw, self.possede = labo, labo_kw or {}, labo is None
        self.periode_min, self.rayon, self.tenue, self.masse, self.plafond = periode_min, rayon_km, tenue, masse, plafond
        self.drapeaux = [dict(n=i, nom=d[0], hote=d[1], pos=(d[2], d[3]), genre=d[4], valeur=d[5], camp0=d[6], dbid=d[7],
                              qg=d[8]) for i, d in enumerate(self.T.DRAPEAUX)]
        par_nom = {d["nom"]: d for d in self.drapeaux}
        self.bases_de = {p: [par_nom[b]["n"] for b in self.T.BASES_DE.get(p, [])] for p in self.pays}
        for p, ns in self.bases_de.items():
            for n in ns:
                if self.drapeaux[n]["camp0"] != self.T.PAYS[p][0] or self.drapeaux[n]["dbid"] is None:
                    raise ValueError(f"{p} ne peut pas décoller de {self.drapeaux[n]['nom']}")
        self.proprio = {d["n"]: d["camp0"] for d in self.drapeaux}
        self.seul = {d["n"]: (None, 0) for d in self.drapeaux}
        self.debit = {p: BU.millions_par_minute(p, self.T.PAYS[p][1]) for p in self.pays}
        par_camp = {c: sum(self.debit[p] for p in self.pays if self.T.PAYS[p][0] == c) for c in self.camps}
        total = sum(par_camp.values()) or 1.0
        self.plafond_camp = {c: max(1, round(plafond * par_camp[c] / total)) for c in self.camps}
        self.caisse = {p: self.debit[p] * credit_initial_min for p in self.pays}
        self.verse = dict(self.caisse)
        self.depense = {p: 0.0 for p in self.pays}
        self.achats, self.pertes, self.rang = ({p: 0 for p in self.pays} for _ in range(3))
        self.avions = {}                                 # numéro -> { pays, camp, famille, base }
        self.positions = {}                              # numéro -> ( lat, lon ) au dernier relevé
        self.altitudes = {}                              # numéro -> altitude ( m ) au dernier relevé
        self.score = {c: 0 for c in self.camps}
        self.offensive, self.defense = {c: None for c in self.camps}, {c: None for c in self.camps}
        self.zone_mission, self.affecte = {}, {}         # id -> n posé ; numéro -> id
        self.morts, self.flips = [], []
        self.tours, self.victoire, self.temps, self.ouvert = 0, None, None, False
        self.journal = None

    # ---- numéros
    def numero_avion(self, pays):
        self.rang[pays] += 1
        return DEC_AVION + (self.pays.index(pays) + 1) * 100_000 + self.rang[pays]

    def pays_de(self, k):
        i = (k - DEC_AVION) // 100_000 - 1
        return self.pays[i] if DEC_AVION <= k < DEC_BASE and 0 <= i < len(self.pays) else None

    # ---- ouverture : les camps hostiles, le journal des messages, table rase, les installations des drapeaux
    def ouvrir(self, journal_id=None):
        if self.labo is None:
            self.labo = CL.Labo(camps=self.camps, **self.labo_kw).ouvrir()
        try:
            self.labo.hostiles(*self.camps[:2])
            if journal_id:
                self.journal = self.labo.journal_messages(journal_id)
            self.labo.nettoyer()
            lots = {}
            for d in self.drapeaux:
                if d["dbid"]:
                    lots.setdefault((d["camp0"], d["dbid"]), []).append((DEC_BASE + d["n"] + 1, *d["pos"]))
            r = self.labo.poser_lots([(camp, "site", dbid, poses, 0.0, 0) for (camp, dbid), poses in lots.items()])
            if r["refus"]:
                raise CL.Refus(f"CMO refuse des installations de drapeaux : {r['refus']}")
        except BaseException:
            self.fermer()
            raise
        self.ouvert = True
        return self

    def fermer(self):
        if self.labo is not None and self.possede:
            self.labo.fermer()
            self.labo = None
        self.ouvert = False

    # ---- 1. le relevé : vivants, morts ( une fois chacune ), positions
    def _relever(self):
        p = self.labo.positions()
        vus = set()
        for camp, us in p["vivants"].items():
            for k, la, lo, alt in us:
                if self.pays_de(k):
                    vus.add(k)
                    self.positions[k] = (la, lo)
                    self.altitudes[k] = alt
        nouveaux = []
        for camp, ks in p["morts"].items():
            for k in ks:
                pays = self.pays_de(k)
                if pays and k in self.avions:
                    self.pertes[pays] += 1
                    self.morts.append({"numero": k, "pays": pays, "camp": camp, "tour": self.tours})
                    nouveaux.append(k)
                    del self.avions[k]
                    self.positions.pop(k, None)
                    self.altitudes.pop(k, None)
                    self.affecte.pop(k, None)
        perdus = set(self.avions) - vus
        if perdus:
            raise CL.Incomplet(f"avions {sorted(perdus)[:5]} ni vivants ni morts dans CMO")
        return nouveaux

    # ---- 2. les drapeaux : seul dans le ciel TENUE tours de suite
    def en_vol(self, k):
        return self.altitudes.get(k, 0.0) > EN_VOL_M

    def _drapeaux(self):
        flips = []
        for d in self.drapeaux:
            presents = {self.avions[k]["camp"] for k, pos in self.positions.items()
                        if k in self.avions and self.en_vol(k) and km(pos, d["pos"]) <= self.rayon}
            if len(presents) != 1:
                self.seul[d["n"]] = (None, 0)
                continue
            camp = presents.pop()
            c0, t = self.seul[d["n"]]
            self.seul[d["n"]] = (camp, t + 1 if c0 == camp else 1)
            if self.seul[d["n"]][1] >= self.tenue and self.proprio[d["n"]] != camp:
                flips.append((d["n"], self.proprio[d["n"]], camp))
                self.proprio[d["n"]] = camp
                if d["qg"] and self.victoire is None:
                    self.victoire = camp
        for c in self.camps:
            self.score[c] += sum(d["valeur"] for d in self.drapeaux if self.proprio[d["n"]] == c)
        self.flips += [{"tour": self.tours, "n": n, "nom": self.drapeaux[n]["nom"], "de": a, "a": b} for n, a, b in flips]
        return flips

    # ---- 3. les achats : le budget du tour, la famille la plus chère qu'on paie, la base la moins pleine
    def _acheter(self):
        for p in self.pays:
            self.caisse[p] += self.debit[p] * self.periode_min
            self.verse[p] += self.debit[p] * self.periode_min
        par_camp = {c: sum(1 for a in self.avions.values() if a["camp"] == c) for c in self.camps}
        par_base = {}
        for a in self.avions.values():
            par_base[a["base"]] = par_base.get(a["base"], 0) + 1
        lots, demandes = {}, []
        for p in self.pays:
            camp = self.T.PAYS[p][0]
            while self.bases_de[p] and par_camp[camp] < self.plafond_camp[camp]:
                choix = next((x for x in self.cat[p] if x["prix_m"] <= self.caisse[p]), None)
                base = min(self.bases_de[p], key=lambda n: par_base.get(n, 0))
                if choix is None or par_base.get(base, 0) >= CAPACITE_BASE:
                    break
                k = self.numero_avion(p)
                self.caisse[p] -= choix["prix_m"]
                par_camp[camp] += 1
                par_base[base] = par_base.get(base, 0) + 1
                lots.setdefault((camp, choix["dbid"], choix["loadout"], base), []).append(k)
                demandes.append((k, p, camp, choix, base))
        if not lots:
            return []
        r = self.labo.poser_base_lots([(c, d, l, DEC_BASE + b + 1, ks) for (c, d, l, b), ks in lots.items()])
        poses = set(r["poses"])
        for k, p, camp, choix, base in demandes:
            if k in poses:
                self.avions[k] = {"pays": p, "camp": camp, "famille": choix["famille"], "base": base}
                self.positions[k] = self.drapeaux[base]["pos"]
                self.altitudes[k] = 0.0
                self.depense[p] += choix["prix_m"]
                self.achats[p] += 1
            else:                                        # refusé par CMO : rien de payé
                self.caisse[p] += choix["prix_m"]
        return sorted(poses)

    # ---- 4. les missions : une défense et une offensive par camp, massées ; tout en un envoi
    def _centre(self, camp):
        ps = [self.drapeaux[n]["pos"] for p in self.pays if self.T.PAYS[p][0] == camp for n in self.bases_de[p]]
        return (sum(x for x, _ in ps) / len(ps), sum(y for _, y in ps) / len(ps)) if ps else None

    def _ordonner(self):
        patrouilles, affectations = [], []
        for ci, camp in enumerate(self.camps):
            autre = next(c for c in self.camps if c != camp)
            moi, lui = self._centre(camp), self._centre(autre)
            if moi is None or lui is None:
                continue
            ennemis = [d for d in self.drapeaux if self.proprio[d["n"]] != camp]
            miens = [d for d in self.drapeaux if self.proprio[d["n"]] == camp]
            self.offensive[camp] = min(ennemis, key=lambda d: km(d["pos"], moi))["n"] if ennemis else None
            self.defense[camp] = min(miens, key=lambda d: km(d["pos"], lui))["n"] if miens else None
            flotte = sorted(k for k, a in self.avions.items() if a["camp"] == camp)
            for rang_m, n, tiers in ((2, self.defense[camp], 1), (1, self.offensive[camp], 0)):
                i = ci * 10 + rang_m
                if n is not None and self.zone_mission.get(i) != n:
                    patrouilles.append((i, camp, *self.drapeaux[n]["pos"], DEMI_ZONE_KM, tiers))
                    self.zone_mission[i] = n
            libres = [k for k in flotte if k not in self.affecte]
            en_defense = sum(1 for k in flotte if self.affecte.get(k) == ci * 10 + 2)
            besoin = max(0, math.ceil(PART_DEFENSE * len(flotte)) - en_defense)
            if self.defense[camp] is not None and besoin:
                affectations.append((ci * 10 + 2, libres[:besoin]))
                libres = libres[besoin:]
            if self.offensive[camp] is not None and len(libres) >= self.masse:   # le paquet part en entier, ou pas
                affectations.append((ci * 10 + 1, libres))
        if not patrouilles and not any(ks for _, ks in affectations):
            return
        r = self.labo.missions(patrouilles, [(i, ks) for i, ks in affectations if ks])
        faits = set(r["affectes"])
        for i, ks in affectations:
            for k in ks:
                if k in faits:
                    self.affecte[k] = i

    # ---- un tour
    def tour(self):
        self.tours += 1
        morts = self._relever()
        flips = self._drapeaux()
        achats = self._acheter()
        self._ordonner()
        c = self.labo.canari()
        self.temps = c["temps"]
        return {"tour": self.tours, "morts": morts, "achats": achats, "flips": flips, "victoire": self.victoire,
                "temps": self.temps, "rtt_ms": c["recu"]["rtt_ms"],
                "camps": {cp: {"avions": sum(1 for a in self.avions.values() if a["camp"] == cp), "score": self.score[cp],
                               "drapeaux": sum(1 for n in self.proprio if self.proprio[n] == cp),
                               "offensive": self.offensive[cp], "defense": self.defense[cp]} for cp in self.camps}}
