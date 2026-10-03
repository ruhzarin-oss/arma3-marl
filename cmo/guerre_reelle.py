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
import etat_major as EM                                   # noqa: E402
import inventaires as INV                                 # noqa: E402

DEC_AVION, DEC_SOL, DEC_INST = 10_000_000, 20_000_000, 90_000_000
DEC_NAV = 30_000_000                                      # navires et sous-marins ( dans les mobiles relevés à chaque tour )
MOBILES = (DEC_AVION, DEC_INST - 1)
SEUIL_PISTE = 50.0                                        # % de dégâts au-delà duquel une piste ne sert plus
PACKS_INITIAUX = 4                                        # chargements complets en dépôt par avion avant la guerre
SEUIL_PACKS, CIBLE_PACKS = 2, 4                           # par avion : on rachète sous SEUIL, jusqu'à CIBLE
N_STOCKS, N_BILAN = 5, 10                                 # tours entre deux relevés des dépôts, des bilans de CMO
DEMI_ZONE_KM = 30.0
PORTEE_FRAPPE_KM = 900.0
SURGE_H = 72.0                                            # cadence « surge » les 3 premiers jours, puis soutenue ( le réel )
TEMPO_SURGE, TEMPO_SOUTENU = 0, 1                         # air_operations_tempo de CMO ( 0 : défaut des camps, le surge )
GARDE_CIBLE = 0.8                                         # on garde la cible tant qu'elle menace au moins 80 % de la pire
BDA_AGE_S = 1800.0                                        # un contact vu depuis moins de 30 min montre l'état réel de la cible
BDA_BASES = 3                                             # bases adverses suivies par la reconnaissance : la cible et les 2 d'avant
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
    soutien_seul = {d for _, _, d, _, p in flottes if isinstance(p, str)} - {d for _, _, d, _, p in flottes if not isinstance(p, str)}
    for _, pays, dbid, n, part in flottes:                 # les flottes de soutien : le chargement de leur rôle, et lui seul
        if isinstance(part, str):
            out[dbid][part] = chargement_role(c, dbid, part)
            if dbid in soutien_seul:
                out[dbid]["aa"] = out[dbid]["frappe"] = None
    return out


MOTIFS_ROLE = {"reco": (r"^Recon", r"Battlefield Surveillance"), "elint": (r"ELINT",),
               "guet": (r"Airborne Early Warning",), "ravitailleur": (r"^Tanker",), "brouilleur": (r"Offensive ECM",),
               "sead": (r"AARGM", r"HARM", r"ALARM", r"Kh-31P|Kh-58"),
               "bombardier": (r"Kh-101", r"JASSM-ER", r"Kh-32", r"Kh-555", r"Kh-22MA INS", r"JASSM"),
               "helico": (r"JAGM", r"Hellfire", r"LMUR", r"Vikhr|Scallion", r"Ataka|Spiral")}
JAMAIS = r"Nuclear|kT\b|Kh-102|Inert"                    # jamais d'arme nucléaire ni de munition inerte


def chargement_role(c, dbid, role):
    """Le chargement réel d'un avion de soutien pour son rôle ( guet radar, ravitaillement, brouillage, antiradar ), le
    premier motif qui trouve l'emporte, jamais un chargement « Short-Range » ni hypothétique."""
    import re as _re
    lignes = c.execute("""select l.ID, l.Name from DataAircraftLoadouts al join DataLoadout l on l.ID = al.ComponentID
        where al.ID = ? and coalesce(l.Hypothetical,0)=0 and l.Name not like '%Short-Range%'""", (dbid,)).fetchall()
    for motif in MOTIFS_ROLE[role]:
        cand = [i for i, n in lignes if _re.search(motif, n) and not _re.search(JAMAIS, n)]
        if cand:
            return min(cand)
    return None


def role_origine(a):
    """Le rôle d'un avion dans sa flotte : un frappeur réarmé en DEAD ou basculé en chasse reste un frappeur."""
    return a.get("bascule") or ("frappe" if a["role"] == "dead" else a["role"])


def repartition(n, part, c):
    """[ ( rôle, nombre ) ] d'une flotte : une part en frappe, le reste air-air ( par paires ) ; ou, flotte de soutien
    ( la part est un rôle ), toute la flotte dans ce rôle."""
    if isinstance(part, str):
        return [(part, n)] if c.get(part) else []
    if not c.get("aa"):
        return []
    n_fr = 2 * round(n * part / 2) if c.get("frappe") else 0
    return [("frappe", n_fr), ("aa", 2 * ((n - n_fr) // 2))]


def prix_pack_db():
    import munitions as M
    cache = {}

    def prix(loadout):
        if loadout not in cache:
            cache[loadout] = (M.cout(M.armes(loadout)), [(a["arme"], a["n"]) for a in M.armes(loadout) if a["prix_m"]])
        return cache[loadout]
    return prix


def readytime_db():
    """Minutes de préparation réelles d'un chargement ( DataLoadout.ReadyTime ), 60 à défaut."""
    import sqlite3
    c = sqlite3.connect(f"file:{CL_DB}?mode=ro", uri=True)

    def rt(loadout):
        r = c.execute("select ReadyTime from DataLoadout where ID = ?", (loadout,)).fetchone()
        return int(r[0]) if r and r[0] else 60
    return rt


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
                 flottes=None, sol=None, classer=None, chargements=None, prix_pack=None, prix_arme=None, em_kw=None,
                 readytime=None, brouillard=True, reserve=None, generation=True, chef=None, dossier=None,
                 navires=None, zones_navales=None, roles_terre=None, objectifs_terre=None):
        self.T = importlib.import_module(f"theatres.{theatre}")
        self.camps, self.pays = tuple(self.T.CAMPS), list(self.T.PAYS)
        self.installations = list(installations if installations is not None else self.T.INSTALLATIONS)
        self.flottes = list(flottes if flottes is not None else self.T.FLOTTES)
        self.sol_ob = list(sol if sol is not None else self.T.SOL)
        # LA COMPOSANTE NAVALE ( 03/10 ) : ( pays, dbid, nom, nombre, lat, lon de la rade, rôle, genre navire / sous_marin )
        self.flotte_navale = list(navires if navires is not None else getattr(self.T, "NAVIRES", []))
        self.zones_navales = dict(zones_navales if zones_navales is not None else getattr(self.T, "ZONES_NAVALES", {}))
        self.navires = {}                                # numéro -> { pays, camp, dbid, nom, rôle, genre, pos }
        # LA COMPOSANTE TERRESTRE ( 03/10 ) : rôle des unités au sol par dbid, objectifs de chaque camp
        self.roles_terre = dict(roles_terre if roles_terre is not None else getattr(self.T, "ROLES_TERRE", {}))
        self.objectifs_terre = dict(objectifs_terre if objectifs_terre is not None else getattr(self.T, "OBJECTIFS_TERRE", {}))
        for d in getattr(self.T, "LANCEURS", set()):
            self.roles_terre.setdefault(d, "lanceur")
        self.classer = classer or classer_db()
        self.charg = chargements if chargements is not None else chargements_db(self.flottes)
        self.prix_pack = prix_pack or prix_pack_db()
        self.prix_arme = prix_arme or prix_arme_db()
        self.labo, self.labo_kw, self.possede = labo, labo_kw or {}, labo is None
        self.fichier_cmo = getattr(self.T, "fichier_cmo", lambda f: f)
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
        self.debut, self.tempo = None, TEMPO_SURGE        # temps du scénario au premier tour ; cadence en cours
        # LA RÉSERVE NATIONALE ( inventaires.py ) : « pays|dbid » -> avions disponibles hors du théâtre ; les renforts en
        # route vers le théâtre, posés à leur arrivée ( délai de convoyage )
        self.reserve_injectee = reserve
        self.generation = generation                     # l'état-major engage-t-il lui-même ses forces ?
        self.reserve, self.renforts = {}, []
        self.pertes = {p: 0 for p in self.pays}
        self.achats = {p: 0 for p in self.pays}
        self.packs_achetes = {p: 0 for p in self.pays}
        self.refus_construction = []                     # ce que CMO a refusé de poser, et pourquoi ( code REFUS_LUA )
        self.altitudes, self.affecte_avant = {}, {}
        self.brouillard = brouillard                     # l'état-major ne voit que ce que CMO montre à son camp
        self.vus = {c: {} for c in self.camps}           # camp -> { numéro adverse : ( classification, âge, lat, lon, n ) }
        self.bda = {c: {} for c in self.camps}           # camp -> { élément adverse : [ dégâts PERÇUS %, tour de l'observation ] }
        self.bda_bases = {c: [] for c in self.camps}     # camp -> bases adverses suivies ( dernières cibles )
        self.readytime = readytime or readytime_db()
        self.em = EM.EtatMajor(self, **(em_kw or {}))    # l'état-major : doctrine, DEAD avant OCA, escortes, apprentissage
        self.chef = None                                 # le chef d'état-major Qwen ( chef_qwen.py ), au-dessus de l'état-major
        if chef is not None:
            import chef_qwen as CQ
            savoir = None
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(ICI), "savoir"))
                import savoir as SV                      # la base de connaissance de CMO ( si elle est là )
                savoir = SV.rechercher
            except Exception:
                savoir = None
            self.chef = chef if not isinstance(chef, str) else CQ.ChefQwen(self, savoir=savoir, dossier=dossier)
            try:
                self.chef.commandement = SV.commandement() if savoir else None      # la fiche de commandement, fixe
            except Exception:
                self.chef.commandement = None

    # ---- numéros
    def _numero(self, dec, pays):
        self.rang[pays] += 1
        return dec + (self.pays.index(pays) + 1) * 100_000 + self.rang[pays]

    def camp_de_pays(self, pays):
        return self.T.PAYS[pays][0]

    # ---- 0. construire le théâtre ( une fois, dans un scénario propre )
    def ouvrir(self, journal_id=None):
        if self.labo is None:
            fichiers = tuple(self.fichier_cmo(f) for f, *_ in self.installations)
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

    def construire(self, attente_import=1.5, sommeil=None, restes_max=300):
        """Le théâtre dans le scénario ouvert. Refuse si le scénario en contient déjà un ( plus de restes_max unités HMT ) :
        l'effacer en masse ralentirait CMO jusqu'au rechargement ( banc du 02/10 ) ; recharger, ou reprendre ( charger ).
        Les restes d'une construction interrompue, eux, sont peu nombreux : table rase."""
        import time
        sommeil = sommeil or time.sleep
        n = sum(c["hmt_vivants"] for c in self.labo.etat_camps()["camps"].values())
        if n > restes_max:
            raise CL.Refus(f"le scénario contient déjà {n} unités HMT : recharger un scénario propre, ou reprendre la guerre "
                           "( endurance_reelle.py --reprendre <dossier> )")
        self.labo.nettoyer()
        if hasattr(self.T, "rafraichir_copies"):
            self.T.rafraichir_copies()                   # identifiants neufs : voir theatres/baltique_reel.COPIES
        for i, (f, camp, pays, role) in enumerate(self.installations):
            self.labo.importer(camp, self.fichier_cmo(f))
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
        self._poser_navires(self.flotte_navale)
        for camp in self.camps:
            self.labo.doctrine(camp, "air_operations_tempo", TEMPO_SURGE)   # l'ouverture de la campagne : surge
        return self

    # ---- 0 bis. compléter un théâtre en cours ( corriger au fur et à mesure, Younes 02/10 ) : sans le reconstruire
    ROLES_AIR = ("chasse", "transport", "aéronavale", "police du ciel balte", "hélicoptères", "aérodrome", "attaque", "soutien")

    def completer(self, attente_import=1.5, sommeil=None):
        """Ajoute à la guerre en cours ce que la construction n'a pas posé : une base aérienne importée à moins de 5
        éléments ( réimportée d'une copie aux identifiants neufs, numérotée après ses restes ), les avions jamais posés
        ou refusés par CMO ( sur leur base, sinon DISPERSÉS sur la base la plus proche de leur camp qui les accepte ), les
        forces au sol refusées ( aux coordonnées actuelles du théâtre ). Rend ce qui a été ajouté."""
        import time
        sommeil = sommeil or time.sleep
        if hasattr(self.T, "rafraichir_copies"):
            self.T.rafraichir_copies()
        ajoute = {"bases": [], "avions": 0, "sol": 0, "refus": []}
        for i, (f, camp, pays, role) in enumerate(self.installations):
            mes = [k for k, e in self.elements.items() if e["inst"] == i]
            if role not in self.ROLES_AIR or len(mes) >= 5:
                continue
            self.labo.importer(camp, self.fichier_cmo(f))
            sommeil(attente_import)
            debut = max(mes) + 1 if mes else DEC_INST + i * 1000 + 1
            el = self.labo.adopter(camp, debut)["elements"]
            self._enregistrer(i, f, camp, pays, role, el)
            if i in self.bases:
                ajoute["bases"].append(f)
        # les avions : la flotte voulue moins ce qui vole, attend son remplacement ou est déjà perdu
        voulus = {}
        for f, pays, dbid, n, part in self.flottes:
            c = self.charg.get(dbid, {})
            for role, m in repartition(n, part, c):
                voulus[(f, pays, dbid, role)] = voulus.get((f, pays, dbid, role), 0) + m
        # tenus : vivants + perdus en attente de remplacement ( un perdu remplacé est un vivant ) ; par base d'ORIGINE
        tenus = {}
        for a in self.avions.values():
            cle = (a.get("origine") or self.bases[a["base"]]["fichier"], a["pays"], a["dbid"], role_origine(a))
            tenus[cle] = tenus.get(cle, 0) + 1
        for r in self.renforts:                          # en route vers le théâtre : déjà tenus
            cle = (self.bases[r["origine"]]["fichier"] if r["origine"] in self.bases else None, r["pays"], r["dbid"], r["role"])
            tenus[cle] = tenus.get(cle, 0) + r["n"]
        for pays, dbid, role, base in self.a_remplacer:
            cle = (self.bases[base]["fichier"] if base in self.bases else None, pays, dbid, "frappe" if role == "dead" else role)
            tenus[cle] = tenus.get(cle, 0) + 1
        for (f, pays, dbid, role), n in voulus.items():
            manque = n - tenus.get((f, pays, dbid, role), 0)
            manque -= manque % 2
            if manque <= 0:
                continue
            lo = self.charg[dbid][role]
            camp = self.camp_de_pays(pays)
            i0 = self.base_de_fichier(f)
            ordre = [i0] if i0 is not None else []
            depart = self.bases[i0]["pos"] if i0 is not None else None
            autres = sorted((i for i, b in self.bases.items() if b["camp"] == camp and i != i0),
                            key=lambda i: km(self.bases[i]["pos"], depart) if depart else 0)
            for i in ordre + autres:
                if manque <= 0:
                    break
                ks = [self._numero(DEC_AVION, pays) for _ in range(manque)]
                r = self.labo.poser_base_lots([(camp, dbid, lo, self.bases[i]["groupe"], ks)])
                for k in r["poses"]:
                    self.avions[k] = {"pays": pays, "camp": camp, "dbid": dbid, "base": i, "role": role, "loadout": lo,
                                      "origine": f}
                depots = [k for k in self.bases[i]["depots"] if self.elements[k]["vivant"]]
                if r["poses"] and depots:                # leurs munitions d'avant-guerre, comme à la construction
                    packs = len(r["poses"]) * PACKS_INITIAUX
                    self.labo.armer([(depots[0], lo, packs)])
                    self.stock_initial_m[pays] += self.prix_pack(lo)[0] * packs
                ajoute["avions"] += len(r["poses"])
                manque -= len(r["poses"])
            if manque > 0:
                ajoute["refus"].append({"genre": "avion", "fichier": f, "pays": pays, "dbid": dbid, "role": role, "manque": manque})
        # les forces au sol refusées, aux coordonnées actuelles du théâtre
        par_nom = {nom: (pays, dbid, la, lo) for pays, dbid, nom, la, lo in self.sol_ob}
        restes = []
        for x in self.refus_construction:
            if x.get("genre") != "sol" or x.get("nom") not in par_nom:
                restes.append(x)
                continue
            pays, dbid, la, lo = par_nom[x["nom"]]
            k = self._numero(DEC_SOL, pays)
            r = self.labo.poser_lots([(self.camp_de_pays(pays), "site", dbid, [(k, la, lo)], 0.0, 0)])
            if k in r["poses"]:
                self.sol[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "nom": x["nom"], "pos": (la, lo)}
                ajoute["sol"] += 1
            else:
                restes.append(dict(x, code=r["refus"].get(k)))
        self.refus_construction = [x for x in restes if x.get("genre") != "avion"] + ajoute["refus"]
        ajoute["navires"] = len(self.completer_navires())
        return ajoute

    def _enregistrer(self, i, f, camp, pays, role, el):
        b = self.bases.get(i) or {"groupe": None, "pistes": [], "acces": [], "depots": [], "camp": camp, "pays": pays,
                                  "role": role, "pos": None, "op": False, "fichier": f}
        for k, dbid, la, lo, groupe in el:
            cl = "groupe" if groupe else self.classer(dbid)
            self.elements[k] = {"inst": i, "dbid": dbid, "classe": cl, "pos": (la, lo), "camp": camp, "vivant": True,
                                "degats": 0.0}
            if groupe:
                b["groupe"], b["pos"] = k, (la, lo)
            elif cl in ("piste", "acces", "depot"):
                b[{"piste": "pistes", "acces": "acces", "depot": "depots"}[cl]].append(k)
        if b["pos"] is None and el:
            b["pos"] = (sum(e[2] for e in el) / len(el), sum(e[3] for e in el) / len(el))
        if b["pistes"] and b["groupe"]:
            b["op"] = True
            self.bases[i] = b
            if b["depots"]:
                self.labo.armer([(b["depots"][j % len(b["depots"])], lo, n * PACKS_INITIAUX)
                                 for j, (lo, n) in enumerate(sorted(self._besoins(i).items()))] or [])
        return b

    def base_de_fichier(self, f):
        return next((i for i, b in self.bases.items() if b["fichier"] == f), None)

    def _poser_flottes(self):
        lots, demandes = {}, []
        for f, pays, dbid, n, part_frappe in self.flottes:
            i = self.base_de_fichier(f)
            c = self.charg.get(dbid, {})
            if i is None:
                continue
            for role, m in repartition(n, part_frappe, c):
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
                cout, armes = self.prix_pack(lo)
                if not armes:                            # guet radar, ravitailleur : rien à stocker
                    continue
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

    def _poser_navires(self, liste):
        """Les navires et sous-marins réels, posés en mer devant leur port ( la rade du théâtre ), en ligne à 2 km d'écart ;
        un refus de CMO ( à terre, par exemple ) est gardé pour le rapport."""
        lots = {}
        for pays, dbid, nom, nombre, la, lo, role, genre in liste:
            if pays not in self.pays:
                continue
            for j in range(int(nombre)):
                k = self._numero(DEC_NAV, pays)
                p = (la + 0.018 * (j % 4), lo + 0.03 * (j // 4))
                self.navires[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "nom": nom, "role": role,
                                   "genre": genre, "pos": p}
                lots.setdefault((self.camp_de_pays(pays), genre, dbid), []).append((k, *p))
        if not lots:
            return []
        r = self.labo.poser_lots([(camp, genre, dbid, poses, 0.0, 0) for (camp, genre, dbid), poses in lots.items()])
        for k, code in r["refus"].items():
            n = self.navires.pop(k, None)
            self.refus_construction.append({"genre": "navire", "numero": k, "code": code, **(n or {})})
        return sorted(r["poses"])

    def completer_navires(self):
        """Corriger au fur et à mesure : les navires de la flotte qui n'ont jamais été posés ( ni vivants ni perdus ) le sont."""
        tenus = {}
        for n in self.navires.values():
            tenus[(n["pays"], n["dbid"], n["nom"])] = tenus.get((n["pays"], n["dbid"], n["nom"]), 0) + 1
        for m in self.morts:
            if m["genre"] == "navire" and m.get("cle"):
                c = tuple(m["cle"][:3])
                tenus[c] = tenus.get(c, 0) + 1
        manque = [(p, d, nom, n - tenus.get((p, d, nom), 0), la, lo, r, ge) for p, d, nom, n, la, lo, r, ge in self.flotte_navale
                  if n - tenus.get((p, d, nom), 0) > 0]
        return self._poser_navires(manque)

    # ---- l'état du théâtre, pour reprendre une guerre sans le reconstruire ( le scénario garde les unités HMT )
    CHAMPS_ETAT = ("elements", "bases", "avions", "sol", "rang", "caisse", "verse", "depense", "stock_initial_m",
                   "a_remplacer", "pertes", "achats", "packs_achetes", "frappe", "k_frappe", "affecte", "patrouilles",
                   "refus_construction", "journal", "journal_pos", "tours", "bilans", "morts", "detruits", "altitudes",
                   "debut", "tempo", "bda", "bda_bases", "reserve", "renforts", "navires")

    def etat(self):
        e = {k: (sorted(v) if isinstance(v, set) else v) for k, v in ((k, getattr(self, k)) for k in self.CHAMPS_ETAT)}
        e["em"] = self.em.etat()
        e["vus"] = self.vus                              # le renseignement du dernier tour ( affichage ; refait à chaque tour )
        if self.chef is not None:
            e["chef"] = self.chef.etat()
        return e

    def charger(self, e):
        """L'inverse de etat() après un aller-retour JSON ( les clés numériques y deviennent du texte )."""
        num = lambda d: {int(k): v for k, v in d.items()}          # noqa: E731
        for k in self.CHAMPS_ETAT:
            if k in e:
                setattr(self, k, e[k])
        self.altitudes = {int(k): v for k, v in (e.get("altitudes") or {}).items()}
        self.bda = {c: {int(k): v for k, v in (e.get("bda") or {}).get(c, {}).items()} for c in self.camps}
        # les navires : numéros entiers et positions en tuple ( 03/10 : relus en texte à la reprise, ils manquaient au
        # relevé et chaque tour était refusé )
        self.navires = {int(k): dict(v, pos=tuple(v["pos"])) for k, v in (e.get("navires") or {}).items()}
        self.bda_bases = {c: [int(i) for i in (e.get("bda_bases") or {}).get(c, [])] for c in self.camps}
        if e.get("em"):
            self.em.charger(e["em"])
        if self.chef is not None and e.get("chef"):
            self.chef.charger(e["chef"])
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
            for k, la, lo, alt in us:
                vus.add(k)
                self.altitudes[k] = alt
                if k in self.navires:
                    self.navires[k]["pos"] = (la, lo)
                elif k in self.sol:
                    self.sol[k]["pos"] = (la, lo)          # les forces terrestres manœuvrent ( 03/10 )
        for camp, ks in p["morts"].items():
            for k in ks:
                if k in self.avions:
                    a = self.avions.pop(k)
                    self.pertes[a["pays"]] += 1
                    self.a_remplacer.append((a["pays"], a["dbid"], role_origine(a), a["base"]))
                    self.affecte.pop(k, None)
                    origine = a.get("origine") or (self.bases[a["base"]]["fichier"] if a["base"] in self.bases else None)
                    self.morts.append({"numero": k, "genre": "avion", "pays": a["pays"], "tour": self.tours,
                                       "cle": [origine, a["pays"], a["dbid"], a["role"]]})
                    nouveaux.append(k)
                elif k in self.sol:
                    s = self.sol.pop(k)
                    self.affecte.pop(k, None)
                    self.morts.append({"numero": k, "genre": "sol", "pays": s["pays"], "tour": self.tours})
                    nouveaux.append(k)
                elif k in self.navires:
                    n = self.navires.pop(k)
                    self.affecte.pop(k, None)
                    self.morts.append({"numero": k, "genre": "navire", "pays": n["pays"], "tour": self.tours,
                                       "cle": [n["pays"], n["dbid"], n["nom"], n["role"]]})
                    nouveaux.append(k)
        # les batteries côtières sont des installations FIXES, hors du relevé des mobiles : leur mort est constatée auprès de
        # CMO tous les N_STOCKS tours ( 03/10 : 5 batteries vues « vivantes mais absentes du relevé », tours refusés )
        fixes = {k for k, n in self.navires.items() if n.get("genre") == "site"}
        if fixes and self.tours % N_STOCKS == 0:
            for k in self.labo.etats(sorted(fixes))["absents"]:
                n = self.navires.pop(k)
                self.morts.append({"numero": k, "genre": "navire", "pays": n["pays"], "tour": self.tours, "constatee": True,
                                   "cle": [n["pays"], n["dbid"], n["nom"], n["role"]]})
                nouveaux.append(k)
        perdus = (set(self.avions) | set(self.sol) | (set(self.navires) - fixes)) - vus - set(nouveaux)
        if perdus:
            # 03/10 : des navires vivants manquaient au relevé ( registre périmé ) ; on refait d'abord le registre depuis les
            # noms du scénario et on relève à nouveau, avant de conclure à une mort ou à une incohérence
            self.labo.recenser()
            p2 = self.labo.positions(*MOBILES)
            for camp, us in p2["vivants"].items():
                for k, la, lo, alt in us:
                    if k in perdus:
                        vus.add(k)
                        self.altitudes[k] = alt
                        if k in self.navires:
                            self.navires[k]["pos"] = (la, lo)
            perdus -= vus
        if perdus:
            # Ni dans les vivants ni dans les morts : morte pendant une bascule ( sa mort a été relevée par le processus
            # d'avant, puis le registre refait depuis les noms l'a oubliée : 02/10, avion 10100024 ). On demande à CMO :
            # absente, c'est une mort constatée, comptée une fois ; présente, c'est une vraie incohérence.
            r = self.labo.etats(sorted(perdus))
            if r["etats"]:
                raise CL.Incomplet(f"unités {sorted(r['etats'])[:5]} vivantes dans CMO mais absentes du relevé")
            for k in r["absents"]:
                if k in self.avions:
                    a = self.avions.pop(k)
                    self.pertes[a["pays"]] += 1
                    self.a_remplacer.append((a["pays"], a["dbid"], role_origine(a), a["base"]))
                    genre, pays = "avion", a["pays"]
                elif k in self.navires:
                    n = self.navires.pop(k)
                    genre, pays = "navire", n["pays"]
                else:
                    genre, pays = "sol", self.sol.pop(k)["pays"]
                self.affecte.pop(k, None)
                m = {"numero": k, "genre": genre, "pays": pays, "tour": self.tours, "constatee": True}
                if genre == "navire":                    # son identité, pour qu'un complément ne le ressuscite pas ( 03/10 )
                    m["cle"] = [n["pays"], n["dbid"], n["nom"], n["role"]]
                self.morts.append(m)
                nouveaux.append(k)
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
            # un point d'accès « n'est jamais détruit » dans CMO ( manuel ), mais à 99,9 % il ne sert plus ( 02/10, Šiauliai )
            acces = [k for k in vit(b["acces"]) if self.elements[k]["degats"] < SEUIL_PISTE]
            b["op"] = bool(pistes) and (not b["acces"] or bool(acces)) and bool(vit(b["depots"]))

    # ---- 4. l'argent : budget, avions remplacés par paires, munitions rachetées
    def _verser(self):
        for p in self.pays:
            self.caisse[p] += self.debit[p] * self.periode_min
            self.verse[p] += self.debit[p] * self.periode_min

    def _ouvrir_reserve(self):
        """La réserve nationale au premier tour ( construction ou reprise d'une guerre d'avant l'inventaire ) : les avions
        disponibles de chaque pays moins ceux déjà au théâtre."""
        if self.reserve:
            return
        if self.reserve_injectee is not None:
            base = {tuple(k.split("|")) if isinstance(k, str) else k: v for k, v in self.reserve_injectee.items()}
            base = {(p, int(d)): v for (p, d), v in base.items()}
        else:
            noms = {d: c.get("nom") for d, c in self.charg.items()}
            base = INV.engageables(noms)
        au_theatre = {}
        for a in self.avions.values():
            au_theatre[(a["pays"], a["dbid"])] = au_theatre.get((a["pays"], a["dbid"]), 0) + 1
        self.reserve = {f"{p}|{d}": float(max(0, n - au_theatre.get((p, d), 0))) for (p, d), n in base.items() if p in self.pays}

    def _produire(self):
        for (p, d), par_mois in INV.PRODUCTION_MOIS.items():
            cle = f"{p}|{d}"
            if cle in self.reserve:
                self.reserve[cle] += par_mois * self.periode_min / (30 * 24 * 60)

    def _engager(self):
        """La génération de force : ce que l'état-major de chaque camp décide d'engager part de la réserve et arrive au
        théâtre après le délai de convoyage."""
        for camp in self.camps:
            self.em.apprendre_forces(camp)
            for pays, dbid, role, n, base in self.em.engager(camp):
                self.reserve[f"{pays}|{dbid}"] -= n
                self.renforts.append({"pays": pays, "dbid": dbid, "role": role, "n": n, "origine": base,
                                      "arrivee": (self.temps or 0) + INV.delai_s(pays), "engage": True})

    def _remplacer(self):
        """Une perte se comble par la RÉSERVE nationale, par paires ( une patrouille ne part que par vols de deux ), jamais
        par un achat ; le renfort part de sa base d'attache et n'arrive au théâtre qu'après le délai de convoyage. Réserve
        vide : la perte attend la production."""
        paires = {}
        for pays, dbid, role, base in self.a_remplacer:
            role = "frappe" if role == "dead" else role          # le remplaçant arrive en frappeur : l'état-major le réarme
            paires.setdefault((pays, dbid, role, base), 0)
            paires[(pays, dbid, role, base)] += 1
        reste = []
        for (pays, dbid, role, base), n in paires.items():
            cle = f"{pays}|{dbid}"
            while n >= 2 and self.reserve.get(cle, 0.0) >= 2:
                self.reserve[cle] -= 2
                self.renforts.append({"pays": pays, "dbid": dbid, "role": role, "n": 2, "origine": base,
                                      "arrivee": (self.temps or 0) + INV.delai_s(pays)})
                n -= 2
            reste += [(pays, dbid, role, base)] * n
        self.a_remplacer = reste
        return self._arrivees()

    def _arrivees(self):
        """Les renforts arrivés au théâtre sont posés sur leur base d'origine si elle tient, sinon sur la plus proche de leur
        camp ; une pose refusée retourne à la réserve."""
        prets = [r for r in self.renforts if (self.temps or 0) >= r["arrivee"]]
        if not prets:
            return []
        self.renforts = [r for r in self.renforts if r not in prets]
        lots, demandes = {}, []
        for r in prets:
            pays, dbid, role, base = r["pays"], r["dbid"], r["role"], r["origine"]
            ops = [i for i, b in self.bases.items() if b["op"] and self.camp_de_pays(b["pays"]) == self.camp_de_pays(pays)]
            ref = self.bases[base]["pos"] if base in self.bases else None
            dest = base if base in ops else (min(ops, key=lambda i: km(self.bases[i]["pos"], ref) if ref else 0) if ops else None)
            lo = self.charg.get(dbid, {}).get(role)
            if dest is None or not lo:
                self.reserve[f"{pays}|{dbid}"] = self.reserve.get(f"{pays}|{dbid}", 0.0) + r["n"]
                continue
            ks = [self._numero(DEC_AVION, pays) for _ in range(r["n"])]
            lots.setdefault((self.camp_de_pays(pays), dbid, lo, self.bases[dest]["groupe"]), []).extend(ks)
            demandes += [(k, pays, dbid, dest, role, lo, base) for k in ks]
        if not lots:
            return []
        res = self.labo.poser_base_lots([(camp, d, lo, g, ks) for (camp, d, lo, g), ks in lots.items()])
        poses = set(res["poses"])
        for k, pays, dbid, dest, role, lo, origine in demandes:
            if k in poses:
                self.avions[k] = {"pays": pays, "camp": self.camp_de_pays(pays), "dbid": dbid, "base": dest, "role": role,
                                  "loadout": lo, "origine": self.bases[origine]["fichier"] if origine in self.bases else None}
                self.achats[pays] += 1                   # « achats » : les renforts posés ( le nom reste pour les rapports )
            else:
                self.reserve[f"{pays}|{dbid}"] = self.reserve.get(f"{pays}|{dbid}", 0.0) + 1
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
                if not armes:
                    continue
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
        frappes, aff_f, escortes, rearmes = [], [], [], []
        for ci, camp in enumerate(self.camps):
            f, a, e, rr = self.em.planifier(ci, camp)
            frappes += f
            aff_f += a
            escortes += e
            rearmes += rr
        if self.em.a_clore:
            r = self.labo.clore(self.em.a_clore)
            self.em.journal.append({"tour": self.tours, "clos": r["clos"]})
            self.em.a_clore = []
        if frappes or aff_f:
            r = self.labo.frappes(frappes, aff_f)
            for fid, ks in aff_f:
                for k in ks:
                    if k in r["affectes"]:
                        self.affecte[k] = fid
                    elif k in self.sol:
                        self.affecte[k] = -1                              # refusé par CMO : on ne redemande pas
        if escortes:
            r = self.labo.escortes(escortes)
            for fid, ks in escortes:
                for k in ks:
                    if k in r["escortes"]:
                        self.affecte[k] = -fid                            # négatif : escorteur de la frappe fid
        # la composante air : guet radar, ravitailleurs, brouilleurs, SEAD, barrière de chasse ( après la décision de frappe,
        # dont dépendent la SEAD et le brouillage ; la barrière reprend des chasseurs aux patrouilles des bases )
        zones, aff_z = [], []
        for ci, camp in enumerate(self.camps):
            z, a = self.em.soutiens(ci, camp)
            zones += z
            aff_z += a
        an_f, an_a = [], []
        for ci, camp in enumerate(self.camps):            # la composante navale
            z, a = self.em.marine(ci, camp)
            zones += z
            aff_z += a
            f2, a2 = self.em.antinavire(ci, camp)
            an_f += f2
            an_a += a2
        ordres_terre = []
        for ci, camp in enumerate(self.camps):            # la composante terrestre : manœuvre et appui feu
            if self.tours % EM.TERRE_TOURS == 1:
                ordres_terre += self.em.terre(camp)
            f3, a3 = self.em.appui(ci, camp)
            an_f_terre = f3
            if f3:
                self.labo.frappes(f3, ())
            an_a += a3
        if ordres_terre:
            self.labo.aller_tous(ordres_terre)
        if self.em.a_clore:
            r = self.labo.clore(self.em.a_clore)
            self.em.journal.append({"tour": self.tours, "clos": r["clos"]})
            self.em.a_clore = []
        if an_f:
            self.labo.frappes_navales(an_f)
        if an_a:
            r = self.labo.frappes((), an_a)
            for fid, ks in an_a:
                for k in ks:
                    if k in r["affectes"]:
                        self.affecte[k] = fid
        if zones or aff_z:
            r = self.labo.zones(zones, aff_z)
            for zid, ks in aff_z:
                for k in ks:
                    if k in r["affectes"]:
                        self.affecte[k] = zid
        if rearmes:
            self._rearmer(rearmes)

    def _rearmer(self, lots):
        """Avions de frappe posés réarmés pour la DEAD. Le dépôt de leur base doit contenir les armes ( sinon CMO laisse
        l'avion SANS armement, sonde du 02/10 ) : s'il ne peut armer l'avion, PACKS_INITIAUX chargements sont achetés au prix
        réel par le pays ( la réserve suit au relevé des stocks ), puis ScenEdit_SetLoadout, relu. Refusé ( en vol, au roulage ), l'avion garde son chargement ; laissé vide,
        il reprend aussitôt l'ancien."""
        par_base, charge, roles = {}, [], {}
        for k, lo, role in lots:
            roles[k] = role
            a = self.avions.get(k)
            b = self.bases.get(a["base"]) if a else None
            depots = [d for d in (b["depots"] if b else []) if self.elements[d]["vivant"]]
            if depots:
                par_base.setdefault(a["base"], (depots, []))[1].append((k, lo))
        achats = []
        for i, (depots, ks) in par_base.items():
            total = {}
            for s in self.labo.stocks(depots)["stocks"].values():
                for w, (c, _) in s.items():
                    total[w] = total.get(w, 0) + c
            for k, lo in ks:
                a = self.avions[k]
                cout, armes = self.prix_pack(lo)
                dispo = min((total.get(w, 0) // q for w, q in armes), default=0)
                manque = PACKS_INITIAUX if dispo < 1 else 0  # de quoi armer cet avion : un lot ; la réserve, au relevé
                if manque and self.caisse[a["pays"]] < manque * cout:
                    continue
                if manque:
                    self.caisse[a["pays"]] -= manque * cout
                    self.depense[a["pays"]] += manque * cout
                    self.packs_achetes[a["pays"]] += manque
                    achats.append((depots[0], lo, manque))
                for w, q in armes:                          # le stock relu sert aussi aux suivants de la même base
                    total[w] = total.get(w, 0) + manque * q - q
                charge.append((k, lo, self.readytime(lo)))
        if achats:
            self.labo.armer(achats)
        if not charge:
            return
        r = self.labo.charger(charge)
        rendre = []
        for k, lo, _ in charge:
            lu, ancien = r["charges"].get(k), self.avions[k]["loadout"]
            if lu == lo:
                a, role = self.avions[k], roles[k]
                if role in ("aa", "sead") and a["role"] == "frappe":
                    a["bascule"] = "frappe"                       # swing-role : il reste un frappeur de sa flotte
                elif role not in ("aa", "sead"):
                    a.pop("bascule", None)
                a.update(role=role, loadout=lo)
                self.affecte.pop(k, None)
            elif lu is not None and lu != ancien:
                rendre.append((k, ancien, 0))
            self.em.journal.append({"tour": self.tours, "rearme": k, "role": roles[k], "chargement": lo, "ok": lu == lo, "lu": lu})
        if rendre:
            r2 = self.labo.charger(rendre)
            self.em.journal.append({"tour": self.tours, "rendu": {k: r2["charges"].get(k) for k, _, _ in rendre}})

    def _choisir_cible(self, camp):
        """La base aérienne adverse opérationnelle qui MENACE le plus le camp : ses avions basés, rapportés à sa distance à
        la plus proche des bases du camp ( le réel : Kaliningrad, bulle au milieu de l'OTAN, avant Baranovitchi ). On garde
        la cible en cours tant qu'elle menace au moins GARDE_CIBLE de la pire : pas de valse des missions."""
        miennes = [b["pos"] for b in self.bases.values() if b["camp"] == camp and b["op"]] or \
                  [b["pos"] for b in self.bases.values() if b["camp"] == camp]
        if not miennes:
            return None
        n = {}
        for a in self.avions.values():
            n[a["base"]] = n.get(a["base"], 0) + 1
        menace = {}
        for i, b in self.bases.items():
            if b["camp"] == camp or not self.op_percu(camp, i):     # ce que le camp CROIT de la base
                continue
            d = min(km(b["pos"], p) for p in miennes)
            if d <= PORTEE_FRAPPE_KM:
                menace[i] = (n.get(i, 0) + 1) / max(d, 50.0)
        if not menace:
            return None
        pire = max(menace, key=lambda i: (menace[i], -i))
        impose = self.em.cible_imposee.get(camp)         # le chef d'état-major a désigné la cible prioritaire
        if impose is not None:
            impose = int(impose)
            if impose in menace:
                return impose
        cours = (self.frappe.get(camp) or {}).get("base")
        if cours in menace and menace[cours] >= GARDE_CIBLE * menace[pire]:
            return cours
        return pire

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
        self.affecte_avant = dict(self.affecte)
        morts = self._relever()
        self.em.suivre(morts)
        detruits = self._lire_journal()
        self._etat_bases()
        self._verser()
        self._ouvrir_reserve()
        self._produire()
        if self.chef is not None:
            self.chef.tour()                             # décisions stratégiques arrivées, bilans, nouvelles demandes
        if self.generation and self.tours % EM.ENGAGER_TOURS == 1:
            self._engager()
        achats = self._remplacer()
        munitions = self._racheter_munitions() if self.tours % N_STOCKS == 1 else []
        self._renseigner()
        self._ordonner()
        if self.tours % N_BILAN == 1:
            self._bilans()
        c = self.labo.canari()
        self.temps = c["temps"]
        self._cadence()
        return {"tour": self.tours, "temps": self.temps, "rtt_ms": c["recu"]["rtt_ms"], "morts": morts,
                "detruits": detruits, "achats": achats, "munitions": len(munitions),
                "decisions": [d for d in self.em.journal if d.get("tour") == self.tours],
                "camps": {cp: self.resume(cp) for cp in self.camps}}

    def _renseigner(self):
        """Le renseignement du tour : pour chaque camp, les unités au sol adverses ( mobiles ) que ses capteurs voient dans
        CMO. Les installations fixes ( bases, sites sol-air enterrés ) sont connues d'avance, comme dans le réel."""
        if not self.brouillard:
            return
        for camp in self.camps:
            adverses = sorted([k for k, s in self.sol.items() if s["camp"] != camp] +
                              [k for k, n in self.navires.items() if n["camp"] != camp])
            self.vus[camp] = self.labo.vus(camp, adverses)["vus"] if adverses else {}
        self.em.renseigner()                             # la carte des menaces ( garnisons d'avant-guerre au premier tour )
        self._evaluer_degats()

    def _evaluer_degats(self):
        """L'ÉVALUATION DES DÉGÂTS ( BDA ) : un camp ne connaît l'état d'une base adverse que par ce qu'il en VOIT. Pour
        les bases suivies ( la cible et les deux d'avant ), un élément dont le contact a moins de BDA_AGE_S montre ses
        dégâts réels ; la base observée, ses éléments détruits sont vus détruits. Sinon le camp garde ce qu'il croyait.
        La reconnaissance ( drones, avions d'écoute ) et les avions qui frappent rafraîchissent les contacts."""
        for camp in self.camps:
            fr = self.frappe.get(camp)
            suivies = self.bda_bases[camp]
            if fr and fr.get("base") in self.bases and fr["base"] not in suivies:
                suivies.append(fr["base"])
            suivies[:] = [i for i in suivies if i in self.bases][-BDA_BASES:]
            for i in suivies:
                b = self.bases[i]
                ks = b["pistes"] + b["acces"] + b["depots"]
                vivants = [k for k in ks if self.elements[k]["vivant"]]
                vus = self.labo.vus(camp, vivants)["vus"] if vivants else {}
                frais = [k for k, v in vus.items() if v[1] <= BDA_AGE_S]
                for k in frais:
                    self.bda[camp][k] = [self.elements[k]["degats"], self.tours]
                if frais:
                    for k in ks:
                        if not self.elements[k]["vivant"]:
                            self.bda[camp][k] = [100.0, self.tours]

    def percu(self, camp, k):
        """Les dégâts d'un élément adverse tels que le camp les CROIT ( 0 : jamais vu endommagé )."""
        if not self.brouillard:
            e = self.elements[k]
            return 100.0 if not e["vivant"] else e["degats"]
        return self.bda[camp].get(k, [0.0])[0]

    def op_percu(self, camp, i):
        """La base adverse i est-elle opérationnelle aux yeux du camp ( même règle que _etat_bases, sur les dégâts perçus ) ?"""
        if not self.brouillard:
            return self.bases[i]["op"]
        b = self.bases[i]
        pistes = [k for k in b["pistes"] if self.percu(camp, k) < SEUIL_PISTE]
        acces = [k for k in b["acces"] if self.percu(camp, k) < SEUIL_PISTE]
        return bool(pistes) and (not b["acces"] or bool(acces)) and any(self.percu(camp, k) < 100.0 for k in b["depots"])

    def _cadence(self):
        """Surge les SURGE_H premières heures de la guerre ( temps du scénario ), puis cadence soutenue : une sortie par jour
        et par pilote, comme les campagnes réelles ( 1991, 1999, 2022 )."""
        if self.temps is None:
            return
        if self.debut is None:
            self.debut = self.temps
        if self.tempo == TEMPO_SURGE and self.temps - self.debut >= SURGE_H * 3600:
            for camp in self.camps:
                self.labo.doctrine(camp, "air_operations_tempo", TEMPO_SOUTENU)
            self.tempo = TEMPO_SOUTENU
            self.em.journal.append({"tour": self.tours, "cadence": "soutenue", "apres_h": round((self.temps - self.debut) / 3600, 1)})

    def resume(self, camp):
        bases = [b for b in self.bases.values() if b["camp"] == camp]
        return {"avions": sum(1 for a in self.avions.values() if a["camp"] == camp),
                "sol": sum(1 for s in self.sol.values() if s["camp"] == camp),
                "bases_op": sum(1 for b in bases if b["op"]), "bases": len(bases),
                "elements_perdus": sum(1 for d in self.detruits if d["camp"] == camp),
                "frappe": self.frappe[camp] and self.bases.get(self.frappe[camp]["base"], {}).get("fichier"),
                "bilan": self.bilans.get(camp)}
