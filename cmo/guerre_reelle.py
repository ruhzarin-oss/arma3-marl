"""LA GUERRE RÉELLE dans CMO ( 02/10, Younes : « que du réel, on ne joue plus », « la totale, troupes au sol » ). Plus de
drapeaux ni de score : la guerre avance par ce qui est DÉTRUIT, et c'est CMO qui le calcule.

LE THÉÂTRE ( theatres/<nom>.py ) : de vraies installations livrées avec CMO ( ImportExport ), importées et numérotées ; des
flottes réelles posées PAR PAIRES sur leurs bases ; des forces au sol réelles ( défense sol-air, missiles, blindés,
artillerie ) sur leurs sites. Construit UNE fois dans un scénario propre ( banc du 02/10 : 2 023 éléments tiennent x1,0,
mais une table rase en masse ralentit CMO à x0,25 jusqu'au rechargement ).

UN TOUR ( periode_min de jeu ) :
  1. relevé des unités mobiles ( avions, forces au sol ) : vivants, morts une fois chacune ;
  2. journal des messages de CMO : les éléments d'installations détruits ( piste, dépôt, abri… ) ;
  3. dégâts des éléments clés de chaque base ( pistes, accès, dépôts ) : une base est OPÉRATIONNELLE si une piste au
     moins a moins de SEUIL_PISTE % de dégâts, un accès vit ( s'il en a ) et un dépôt vit ;
  4. l'argent : chaque pays reçoit son budget d'équipement du théâtre ; il remplace ses avions perdus PAR PAIRES sur une de
     ses bases opérationnelles, et rachète des munitions quand ses dépôts baissent ( prix réels, munitions.py ) ;
  5. les ordres : une patrouille de défense aérienne sur chaque base, ses chasseurs affectés ; une FRAPPE par camp contre
     la base aérienne adverse opérationnelle la plus proche ( ses pistes, accès et dépôts ), les avions de frappe et les
     lanceurs de missiles du camp affectés ; quand la base cible tombe, la frappe suivante vise la suivante ;
  6. tous les N_BILAN tours, les pertes et munitions tirées comptées par CMO ( VP_GetSide().losses / .expenditures ).

CHOIX À VALIDER PAR YOUNES ( copier le réel ) : SEUIL_PISTE, PACKS_INITIAUX ( stocks d'avant-guerre ), SEUIL_PACKS et
CIBLE_PACKS ( rachat de munitions ), la cible des frappes ( la base adverse la plus proche, vue sans brouillard de guerre
en v1 : le brouillard viendra avec l'agent ).

Numéros ( que des nombres vers CMO ) : avion DEC_AVION + ( pays + 1 ) x 100 000 + rang ; force au sol DEC_SOL + … ;
élément de l'installation i DEC_INST + i x 1 000 + j ; patrouille de la base i : 100 + i ; frappe : 1 000 + camp x 100 + k.
"""
import importlib
import math
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
import budgets as BU                                      # noqa: E402

DEC_AVION, DEC_SOL, DEC_INST = 10_000_000, 20_000_000, 90_000_000
MOBILES = (DEC_AVION, DEC_INST - 1)
SEUIL_PISTE = 50.0                                        # % de dégâts au-delà duquel une piste ne sert plus
PACKS_INITIAUX = 4                                        # chargements complets en dépôt par avion avant la guerre
SEUIL_PACKS, CIBLE_PACKS = 2, 4                           # par avion : on rachète sous SEUIL, jusqu'à CIBLE
N_STOCKS, N_BILAN = 5, 10                                 # tours entre deux relevés des dépôts, des bilans de CMO
DEMI_ZONE_KM = 30.0
PORTEE_FRAPPE_KM = 900.0
_DETRUIT = re.compile(r"\] HMT-(\d+) \([^)]*\) has been destroyed!")


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


# ---- ce que la base DB3000 dit d'un élément, d'un avion, d'un chargement ( lu sur la WS ; injecté dans la porte ) -------
def classer_db(base=None):
    import sqlite3
    c = sqlite3.connect(f"file:{base or CL_DB}?mode=ro", uri=True)
    cache = {}

    def classer(dbid):
        if dbid == 0:
            return "groupe"
        if dbid not in cache:
            r = c.execute("select Name, Category from DataFacility where ID = ?", (dbid,)).fetchone()
            nom, cat = (r or ("", 0))
            avions = c.execute("select count(*) from DataFacilityAircraftFacilities where ID = ?", (dbid,)).fetchone()[0]
            radars = c.execute("select count(*) from DataFacilitySensors where ID = ?", (dbid,)).fetchone()[0]
            if cat in (2001, 2002):
                k = "piste"
            elif cat == 2003:
                k = "acces"
            elif "Ammo" in nom:
                k = "depot"
            elif "AvGas" in nom or "Fuel" in nom:
                k = "carburant"
            elif "SAM" in nom:
                k = "sol-air"
            elif avions:
                k = "abri"
            elif radars:
                k = "radar"
            else:
                k = "autre"
            cache[dbid] = k
        return cache[dbid]
    return classer


CL_DB = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"


def chargements_db(flottes):
    """{ dbid : { aa, frappe, prix_m } } pour les avions des flottes : air-air et prix du catalogue, frappe guidée."""
    import sqlite3
    import catalogue as CAT
    c = sqlite3.connect(f"file:{CL_DB}?mode=ro", uri=True)
    out = {}
    for _, pays, dbid, *_ in flottes:
        if dbid in out:
            continue
        cat = {x["dbid"]: x for x in CAT.catalogue(pays)}
        nom = c.execute("select Name from DataAircraft where ID = ?", (dbid,)).fetchone()[0]
        fam, prix = CAT.famille(nom)
        aa = cat[dbid]["loadout"] if dbid in cat else None
        fr = CAT.chargement_frappe(dbid)
        out[dbid] = {"aa": aa, "frappe": fr[0] if fr else None, "prix_m": prix or 50, "nom": nom}
    return out


def prix_pack_db():
    import munitions as M
    cache = {}

    def prix(loadout):
        if loadout not in cache:
            cache[loadout] = (M.cout(M.armes(loadout)), [(a["arme"], a["n"]) for a in M.armes(loadout) if a["prix_m"]])
        return cache[loadout]
    return prix


def prix_arme_db():
    import sqlite3
    import munitions as M
    c = sqlite3.connect(f"file:{CL_DB}?mode=ro", uri=True)
    cache = {}

    def prix(dbid):
        if dbid not in cache:
            r = c.execute("select Name from DataWeapon where ID = ?", (dbid,)).fetchone()
            cache[dbid] = M.prix(r[0]) if r else None
        return cache[dbid]
    return prix


class GuerreReelle:
    def __init__(self, theatre="baltique_reel", *, labo=None, labo_kw=None, periode_min=1.0, installations=None,
                 flottes=None, sol=None, classer=None, chargements=None, prix_pack=None, prix_arme=None):
        self.T = importlib.import_module(f"theatres.{theatre}")
        self.camps, self.pays = tuple(self.T.CAMPS), list(self.T.PAYS)
        self.installations = list(installations if installations is not None else self.T.INSTALLATIONS)
        self.flottes = list(flottes if flottes is not None else self.T.FLOTTES)
        self.sol_ob = list(sol if sol is not None else self.T.SOL)
        self.classer = classer or classer_db()
        self.charg = chargements if chargements is not None else chargements_db(self.flottes)
        self.prix_pack = prix_pack or prix_pack_db()
        self.prix_arme = prix_arme or prix_arme_db()
        self.labo, self.labo_kw, self.possede = labo, labo_kw or {}, labo is None
        self.periode_min = periode_min
        self.debit = {p: BU.millions_par_minute(p, self.T.PAYS[p][1]) for p in self.pays}
        self.caisse = {p: 0.0 for p in self.pays}
        self.verse, self.depense = dict(self.caisse), dict(self.caisse)
        self.stock_initial_m = {p: 0.0 for p in self.pays}
        self.rang = {p: 0 for p in self.pays}
        self.elements = {}                               # numéro -> { inst, dbid, classe, pos, camp, groupe, vivant, degats }
        self.bases = {}                                  # index d'installation -> { groupe, pistes, acces, depots, camp, pays, pos, op }
        self.avions = {}                                 # numéro -> { pays, camp, dbid, base, role, loadout }
        self.sol = {}                                    # numéro -> { pays, camp, dbid, nom, pos }
        self.a_remplacer = []                            # ( pays, dbid, role, base d'origine ) par avion perdu
        self.morts, self.detruits, self.journal, self.journal_pos = [], [], None, 0
        self.frappe = {c: None for c in self.camps}      # camp -> { id, base, cibles }
        self.k_frappe = {c: 0 for c in self.camps}
        self.affecte = {}                                # numéro -> id de mission
        self.patrouilles = set()
        self.bilans, self.tours, self.temps, self.ouvert = {}, 0, None, False
        self.pertes = {p: 0 for p in self.pays}
        self.achats = {p: 0 for p in self.pays}
        self.packs_achetes = {p: 0 for p in self.pays}
        self.refus_construction = []                     # ce que CMO a refusé de poser, et pourquoi ( code REFUS_LUA )

    # ---- numéros
    def _numero(self, dec, pays):
        self.rang[pays] += 1
        return dec + (self.pays.index(pays) + 1) * 100_000 + self.rang[pays]

    def camp_de_pays(self, pays):
        return self.T.PAYS[pays][0]

    # ---- 0. construire le théâtre ( une fois, dans un scénario propre )
    def ouvrir(self, journal_id=None):
        if self.labo is None:
            fichiers = tuple(f for f, *_ in self.installations)
            self.labo = CL.Labo(camps=self.camps, installations=fichiers, **self.labo_kw).ouvrir()
        self.labo.hostiles(*self.camps[:2])
        if journal_id:
            self.journal = self.labo.journal_messages(journal_id)
        self.ouvert = True
        return self

    def fermer(self):
        if self.labo is not None and self.possede:
            self.labo.fermer()
            self.labo = None
        self.ouvert = False

    def construire(self, attente_import=1.5, sommeil=None):
        import time
        sommeil = sommeil or time.sleep
        for i, (f, camp, pays, role) in enumerate(self.installations):
            self.labo.importer(camp, f)
            sommeil(attente_import)
            el = self.labo.adopter(camp, DEC_INST + i * 1000 + 1)["elements"]
            b = {"groupe": None, "pistes": [], "acces": [], "depots": [], "camp": camp, "pays": pays, "role": role,
                 "pos": None, "op": False, "fichier": f}
            for k, dbid, la, lo, groupe in el:
                cl = "groupe" if groupe else self.classer(dbid)
                self.elements[k] = {"inst": i, "dbid": dbid, "classe": cl, "pos": (la, lo), "camp": camp, "vivant": True,
                                    "degats": 0.0}
                if groupe:
                    b["groupe"], b["pos"] = k, (la, lo)
                elif cl == "piste":
                    b["pistes"].append(k)
                elif cl == "acces":
                    b["acces"].append(k)
                elif cl == "depot":
                    b["depots"].append(k)
            if b["pos"] is None and el:
                b["pos"] = (sum(e[2] for e in el) / len(el), sum(e[3] for e in el) / len(el))
            if b["pistes"] and b["groupe"]:
                b["op"] = True
                self.bases[i] = b
        self._poser_flottes()
        self._armer_initial()
        self._poser_sol()
        for camp in self.camps:
            self.labo.doctrine(camp, "air_operations_tempo", 0)      # cadence soutenue « Surge » : c'est la guerre
        return self

    def base_de_fichier(self, f):
        return next((i for i, b in self.bases.items() if b["fichier"] == f), None)

    def _poser_flottes(self):
        lots, demandes = {}, []
        for f, pays, dbid, n, part_frappe in self.flottes:
            i = self.base_de_fichier(f)
            c = self.charg.get(dbid, {})
            if i is None or not c.get("aa"):
                continue
            n_fr = 2 * round(n * part_frappe / 2) if c.get("frappe") else 0
            for role, m in (("frappe", n_fr), ("aa", 2 * ((n - n_fr) // 2))):
                for _ in range(m):
                    k = self._numero(DEC_AVION, pays)
                    lots.setdefault((self.camp_de_pays(pays), dbid, c[role], self.bases[i]["groupe"]), []).append(k)
                    demandes.append((k, pays, dbid, i, role, c[role]))
        if not lots:
            return
        r = self.labo.poser_base_lots([(camp, d, lo, g, ks) for (camp, d, lo, g), ks in lots.items()])
        poses = set(r["poses"])
        for k, pays, dbid, i, role, lo in demandes:
            if k in poses:
                self.avions[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "base": i, "role": role,
                                  "loadout": lo}
            else:
                self.refus_construction.append({"genre": "avion", "numero": k, "code": r["refus"].get(k), "pays": pays,
                                                "dbid": dbid, "loadout": lo, "base": self.bases[i]["fichier"]})

    def _besoins(self, i):
        """{ loadout : avions de la base i qui l'emportent }."""
        out = {}
        for a in self.avions.values():
            if a["base"] == i:
                out[a["loadout"]] = out.get(a["loadout"], 0) + 1
        return out

    def _armer_initial(self):
        lots = []
        for i, b in self.bases.items():
            if not b["depots"]:
                continue
            for j, (lo, n) in enumerate(sorted(self._besoins(i).items())):
                packs = n * PACKS_INITIAUX
                cout, _ = self.prix_pack(lo)
                self.stock_initial_m[b["pays"]] += cout * packs
                lots.append((b["depots"][j % len(b["depots"])], lo, packs))
        for k in range(0, len(lots), 40):
            self.labo.armer(lots[k:k + 40])

    def _poser_sol(self):
        lots = {}
        for pays, dbid, nom, la, lo in self.sol_ob:
            k = self._numero(DEC_SOL, pays)
            self.sol[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "nom": nom, "pos": (la, lo)}
            lots.setdefault((self.camp_de_pays(pays), dbid), []).append((k, la, lo))
        if lots:
            r = self.labo.poser_lots([(camp, "site", dbid, poses, 0.0, 0) for (camp, dbid), poses in lots.items()])
            for k, code in r["refus"].items():
                s = self.sol.pop(k, None)
                self.refus_construction.append({"genre": "sol", "numero": k, "code": code, **(s or {})})

    # ---- l'état du théâtre, pour reprendre une guerre sans le reconstruire ( le scénario garde les unités HMT )
    CHAMPS_ETAT = ("elements", "bases", "avions", "sol", "rang", "caisse", "verse", "depense", "stock_initial_m",
                   "a_remplacer", "pertes", "achats", "packs_achetes", "frappe", "k_frappe", "affecte", "patrouilles",
                   "refus_construction", "journal", "journal_pos", "tours", "bilans", "morts", "detruits")

    def etat(self):
        return {k: (sorted(v) if isinstance(v, set) else v) for k, v in ((k, getattr(self, k)) for k in self.CHAMPS_ETAT)}

    def charger(self, e):
        """L'inverse de etat() après un aller-retour JSON ( les clés numériques y deviennent du texte )."""
        num = lambda d: {int(k): v for k, v in d.items()}          # noqa: E731
        for k in self.CHAMPS_ETAT:
            setattr(self, k, e[k])
        self.elements, self.avions, self.sol, self.affecte = num(self.elements), num(self.avions), num(self.sol), num(self.affecte)
        self.bases = num(self.bases)
        for b in self.bases.values():
            b["pos"] = tuple(b["pos"]) if b["pos"] else None
        for x in self.elements.values():
            x["pos"] = tuple(x["pos"])
        for s in self.sol.values():
            s["pos"] = tuple(s["pos"])
        self.patrouilles = set(self.patrouilles)
        self.a_remplacer = [tuple(x) for x in self.a_remplacer]
        return self

    # ---- 1. relevé des unités mobiles
    def _relever(self):
        p = self.labo.positions(*MOBILES)
        vus, nouveaux = set(), []
        for camp, us in p["vivants"].items():
            for k, *_ in us:
                vus.add(k)
        for camp, ks in p["morts"].items():
            for k in ks:
                if k in self.avions:
                    a = self.avions.pop(k)
                    self.pertes[a["pays"]] += 1
                    self.a_remplacer.append((a["pays"], a["dbid"], a["role"], a["base"]))
                    self.affecte.pop(k, None)
                    self.morts.append({"numero": k, "genre": "avion", "pays": a["pays"], "tour": self.tours})
                    nouveaux.append(k)
                elif k in self.sol:
                    s = self.sol.pop(k)
                    self.affecte.pop(k, None)
                    self.morts.append({"numero": k, "genre": "sol", "pays": s["pays"], "tour": self.tours})
                    nouveaux.append(k)
        perdus = (set(self.avions) | set(self.sol)) - vus - set(nouveaux)
        if perdus:
            raise CL.Incomplet(f"unités {sorted(perdus)[:5]} ni vivantes ni mortes dans CMO")
        return nouveaux

    # ---- 2. le journal : éléments d'installations détruits
    def _lire_journal(self):
        if not self.journal or not os.path.exists(self.journal):
            return []
        with open(self.journal, errors="ignore") as g:
            g.seek(self.journal_pos)
            texte = g.read()
            self.journal_pos = g.tell()
        nouveaux = []
        for k in (int(x) for x in _DETRUIT.findall(texte)):
            e = self.elements.get(k)
            if e and e["vivant"]:
                e["vivant"], e["degats"] = False, 100.0
                self.detruits.append({"numero": k, "classe": e["classe"], "camp": e["camp"], "inst": e["inst"],
                                      "tour": self.tours})
                nouveaux.append(k)
        return nouveaux

    # ---- 3. l'état des bases
    def _etat_bases(self):
        cles = [k for b in self.bases.values() for k in b["pistes"] + b["acces"] + b["depots"] if self.elements[k]["vivant"]]
        for j in range(0, len(cles), 300):
            r = self.labo.etats(cles[j:j + 300])
            for k, (pct, _feu, _eau) in r["etats"].items():
                self.elements[k]["degats"] = float(pct)
            for k in r["absents"]:
                self.elements[k]["vivant"], self.elements[k]["degats"] = False, 100.0
        for b in self.bases.values():
            vit = lambda ks: [k for k in ks if self.elements[k]["vivant"]]        # noqa: E731
            pistes = [k for k in vit(b["pistes"]) if self.elements[k]["degats"] < SEUIL_PISTE]
            b["op"] = bool(pistes) and (not b["acces"] or bool(vit(b["acces"]))) and bool(vit(b["depots"]))

    # ---- 4. l'argent : budget, avions remplacés par paires, munitions rachetées
    def _verser(self):
        for p in self.pays:
            self.caisse[p] += self.debit[p] * self.periode_min
            self.verse[p] += self.debit[p] * self.periode_min

    def _remplacer(self):
        paires = {}
        for pays, dbid, role, base in self.a_remplacer:
            paires.setdefault((pays, dbid, role, base), 0)
            paires[(pays, dbid, role, base)] += 1
        reste, lots, demandes = [], {}, []
        for (pays, dbid, role, base), n in paires.items():
            prix = self.charg[dbid]["prix_m"]
            ops = [i for i, b in self.bases.items() if b["op"] and self.camp_de_pays(b["pays"]) == self.camp_de_pays(pays)]
            dest = base if base in ops else (min(ops, key=lambda i: km(self.bases[i]["pos"], self.bases[base]["pos"]))
                                             if ops else None)
            while n >= 2 and dest is not None and self.caisse[pays] >= 2 * prix:
                ks = [self._numero(DEC_AVION, pays) for _ in range(2)]
                lo = self.charg[dbid][role]
                self.caisse[pays] -= 2 * prix
                lots.setdefault((self.camp_de_pays(pays), dbid, lo, self.bases[dest]["groupe"]), []).extend(ks)
                demandes += [(k, pays, dbid, dest, role, lo, prix) for k in ks]
                n -= 2
            reste += [(pays, dbid, role, base)] * n
        self.a_remplacer = reste
        if not lots:
            return []
        r = self.labo.poser_base_lots([(camp, d, lo, g, ks) for (camp, d, lo, g), ks in lots.items()])
        poses = set(r["poses"])
        for k, pays, dbid, dest, role, lo, prix in demandes:
            if k in poses:
                self.avions[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "base": dest, "role": role,
                                  "loadout": lo}
                self.depense[pays] += prix
                self.achats[pays] += 1
            else:
                self.caisse[pays] += prix
                self.a_remplacer.append((pays, dbid, role, dest))
        return sorted(poses)

    def _racheter_munitions(self):
        lots = []
        for i, b in self.bases.items():
            depots = [k for k in b["depots"] if self.elements[k]["vivant"]]
            if not b["op"] or not depots:
                continue
            st = self.labo.stocks(depots)["stocks"]
            total = {}
            for s in st.values():
                for w, (c, _) in s.items():
                    total[w] = total.get(w, 0) + c
            for lo, n in sorted(self._besoins(i).items()):
                cout, armes = self.prix_pack(lo)
                dispo = min((total.get(w, 0) // q for w, q in armes), default=0)
                if dispo >= SEUIL_PACKS * n:
                    continue
                packs = CIBLE_PACKS * n - dispo
                payeur = b["pays"]
                packs = min(packs, int(self.caisse[payeur] // cout)) if cout > 0 else packs
                if packs <= 0:
                    continue
                self.caisse[payeur] -= packs * cout
                self.depense[payeur] += packs * cout
                self.packs_achetes[payeur] += packs
                lots.append((depots[0], lo, packs))
        if lots:
            self.labo.armer(lots)
        return lots

    # ---- 5. les ordres : défense de chaque base, une frappe par camp
    def _ordonner(self):
        patrouilles, aff_p = [], []
        for i, b in self.bases.items():
            pid = 100 + i
            if pid not in self.patrouilles and b["op"]:
                patrouilles.append((pid, b["camp"], *b["pos"], DEMI_ZONE_KM, 1))
                self.patrouilles.add(pid)
            libres = sorted(k for k, a in self.avions.items() if a["base"] == i and a["role"] == "aa" and k not in self.affecte)
            libres = libres[:len(libres) // 2 * 2]                        # par vols de deux
            if libres and (pid in self.patrouilles):
                aff_p.append((pid, libres))
        r = self.labo.missions(patrouilles, aff_p) if (patrouilles or aff_p) else {"affectes": []}
        for pid, ks in aff_p:
            for k in ks:
                if k in r["affectes"]:
                    self.affecte[k] = pid
        frappes, aff_f = [], []
        for ci, camp in enumerate(self.camps):
            f = self.frappe[camp]
            if f is None or not self.bases[f["base"]]["op"]:
                cible = self._choisir_cible(camp)
                if cible is None:
                    self.frappe[camp] = None
                    continue
                self.k_frappe[camp] += 1
                fid = 1000 + ci * 100 + self.k_frappe[camp]
                b = self.bases[cible]
                cibles = [k for k in b["pistes"] + b["acces"] + b["depots"] if self.elements[k]["vivant"]]
                self.frappe[camp] = {"id": fid, "base": cible, "cibles": cibles}
                frappes.append((fid, camp, cibles))
                for k, m in list(self.affecte.items()):
                    if m >= 1000 and (m - 1000) // 100 == ci:
                        del self.affecte[k]                               # réaffectés à la nouvelle frappe
            f = self.frappe[camp]
            libres = sorted(k for k, a in self.avions.items() if a["camp"] == camp and a["role"] == "frappe"
                            and k not in self.affecte)
            libres = libres[:len(libres) // 2 * 2]
            lanceurs = sorted(k for k, s in self.sol.items() if s["camp"] == camp and k not in self.affecte
                              and s["dbid"] in getattr(self.T, "LANCEURS", set()))
            if libres or lanceurs:
                aff_f.append((f["id"], libres + lanceurs))
        if frappes or aff_f:
            r = self.labo.frappes(frappes, aff_f)
            for fid, ks in aff_f:
                for k in ks:
                    if k in r["affectes"]:
                        self.affecte[k] = fid
                    elif k in self.sol:
                        self.affecte[k] = -1                              # refusé par CMO : on ne redemande pas

    def _choisir_cible(self, camp):
        """La base aérienne adverse opérationnelle la plus proche des bases du camp, à portée."""
        miennes = [b["pos"] for b in self.bases.values() if b["camp"] == camp]
        if not miennes:
            return None
        centre = (sum(p[0] for p in miennes) / len(miennes), sum(p[1] for p in miennes) / len(miennes))
        cand = [(km(b["pos"], centre), i) for i, b in self.bases.items() if b["camp"] != camp and b["op"]]
        cand = [x for x in cand if x[0] <= PORTEE_FRAPPE_KM]
        return min(cand)[1] if cand else None

    # ---- 6. les bilans de CMO
    def _bilans(self):
        for camp in self.camps:
            b = self.labo.bilan(camp)
            m = sum(n * (self.prix_arme(d) or 0.0) for (t, d), n in b["depenses"].items() if t == "arme")
            self.bilans[camp] = {"pertes": sum(b["pertes"].values()), "munitions_tirees": sum(
                n for (t, _), n in b["depenses"].items() if t == "arme"), "munitions_m": round(m, 2)}

    # ---- un tour
    def tour(self):
        self.tours += 1
        morts = self._relever()
        detruits = self._lire_journal()
        self._etat_bases()
        self._verser()
        achats = self._remplacer()
        munitions = self._racheter_munitions() if self.tours % N_STOCKS == 1 else []
        self._ordonner()
        if self.tours % N_BILAN == 1:
            self._bilans()
        c = self.labo.canari()
        self.temps = c["temps"]
        return {"tour": self.tours, "temps": self.temps, "rtt_ms": c["recu"]["rtt_ms"], "morts": morts,
                "detruits": detruits, "achats": achats, "munitions": len(munitions),
                "camps": {cp: self.resume(cp) for cp in self.camps}}

    def resume(self, camp):
        bases = [b for b in self.bases.values() if b["camp"] == camp]
        return {"avions": sum(1 for a in self.avions.values() if a["camp"] == camp),
                "sol": sum(1 for s in self.sol.values() if s["camp"] == camp),
                "bases_op": sum(1 for b in bases if b["op"]), "bases": len(bases),
                "elements_perdus": sum(1 for d in self.detruits if d["camp"] == camp),
                "frappe": self.frappe[camp] and self.bases[self.frappe[camp]["base"]]["fichier"],
                "bilan": self.bilans.get(camp)}
