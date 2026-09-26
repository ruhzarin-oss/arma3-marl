"""La carte : les lieux nommes d Altis ( CfgWorlds >> Altis >> Names, extraits de la configuration du jeu par la recolte
a3recolte ), et le role de chacun dans le pays. Les positions sont celles du jeu, en metres."""
import json, math, os

ICI = os.path.dirname(os.path.abspath(__file__))

# role economique des lieux industriels et militaires d Altis ( choix de la v1, a verifier dans Arma a l etape E2 )
AFFECTATION = {
    "Mine01": "mine", "quarry01": "carriere", "quarry02": "carriere", "quarry03": "carriere",
    "terminal01": "puits", "storage01": "depot",
    "factory01": "raffinerie", "factory02": "fonderie", "factory03": "pharmacie", "factory04": "fonderie",
    "PowerPlant01": "centrale", "PowerPlant02": "centrale", "PowerPlant03": "centrale",
    "military01": "base", "military02": "base", "military03": "base", "military04": "base", "military05": "base",
    "airbase01": "base", "KavalaPier": "port",
}
CAPITALE_GOUVERNEMENT = "Kavala"

# point 13 : les iles du pays. Chaque ile a sa geographie ; un habitant passe de l une a l autre par la mer.
ILES = {"Altis": "altis_lieux.json", "Malden": "malden_lieux.json", "Stratis": "stratis_lieux.json",
        "Tanoa": "tanoa_lieux.json", "Enoch": "enoch_lieux.json", "Sara": "sara_lieux.json"}
from . import config as _C
assert tuple(ILES) == _C.ILES_ARCHIPEL, "l ordre des iles fixe les codes des numeros d archipel"
CODES_ILES = {ile: k for k, ile in enumerate(_C.ILES_ARCHIPEL)}
PORTS = {"Altis": "KavalaPier"}     # les autres iles trouvent leur port toutes seules : la ville la plus proche de la mer
VITESSE_MER_KMH = 25.0                                          # un cargo cotier
PAYS = os.path.join(ICI, "donnees", "pays")     # archipel ( 24/09 ) : la carte de chaque pays, ecrite par monde/pays_carte.py


def carte_du_pays(ile):
    """La carte du pays qu est cette ile ( lieux du moteur, gouvernement, port, aeroports ), si elle a ete ecrite."""
    chemin = os.path.join(PAYS, f"{ile.lower()}.json")
    if not os.path.exists(chemin): return None
    with open(chemin) as f: return json.load(f)


class Lieu:
    def __init__(self, id, type, pos, rayon=(0, 0), ile="Altis"):
        self.id, self.type, self.pos, self.rayon, self.ile = id, type, tuple(pos), tuple(rayon), ile
        self.n = -1                 # son numero dans Carte.par_n : c est ce numero que lisent les colonnes des habitants
        self.marche = None          # la capitale dont le marche sert ce lieu
        self.stocks = {}            # biens presents sur place ( sites de production, depots, marches )

    def distance(self, autre):
        return math.dist(self.pos, autre.pos)

    def __repr__(self):
        return f"{self.id}({self.type})"


class Carte:
    def __init__(self, fichier=None, iles=("Altis",)):
        """Une carte peut couvrir plusieurs iles. Chaque lieu sait sur laquelle il se trouve, et son identifiant porte
        le nom de l ile quand ce n est pas l ile de depart ( deux villages peuvent avoir le meme nom )."""
        self.routes = self._routes_mesurees()
        self.lieux = {}
        self.iles = list(iles)
        marines = {}                      # les lieux marins de chaque ile : ils designent la cote
        # archipel ( 24/09 ) : une ile autre qu Altis qui ouvre le monde est un PAYS - elle prend sa carte de pays
        # ( bases, usines, centrales, port, depot, gouvernement tires de l inventaire de la carte par Arma ). Altis garde
        # la sienne, choisie a la main et tenue par toutes les portes.
        premiere = self.iles[0]
        self.pays = carte_du_pays(premiere) if (premiere != "Altis" and not fichier) else None
        for ile in self.iles:
            if self.pays is not None and ile == premiere:
                for l in self.pays["lieux"]:
                    self.lieux[l["id"]] = Lieu(l["id"], l["type"], l["pos"], l.get("rayon", (0, 0)), ile=ile)
                continue
            chemin = fichier if (fichier and ile == self.iles[0]) else os.path.join(ICI, "donnees", ILES[ile])
            for l in json.load(open(chemin)):
                if l["type"] == "NameMarine": marines.setdefault(ile, []).append(tuple(l["pos"]))
                t = {"NameCityCapital": "capitale", "NameCity": "ville", "NameVillage": "village"}.get(l["type"])
                if t is None: t = AFFECTATION.get(l["id"])
                if t is None: continue                   # caps, iles, collines : pas de role dans la v1
                cle = l["id"] if ile == self.iles[0] else f"{ile}:{l['id']}"
                self.lieux[cle] = Lieu(cle, t, l["pos"], l.get("rayon", (0, 0)), ile=ile)
        # chaque village est aussi une ferme : l agriculture vit dans les villages
        self.par_n = list(self.lieux.values())      # les lieux par numero, dans l ordre de la carte
        for k, l in enumerate(self.par_n): l.n = k
        self.capitales = [l for l in self.lieux.values() if l.type == "capitale"]
        for l in self.lieux.values():       # un lieu depend d un marche de SON ile
            candidats = [c for c in self.capitales if c.ile == l.ile] or self.capitales
            l.marche = min(candidats, key=lambda c: l.distance(c))
        self.gouvernement = self.lieux[self.pays["gouvernement"] if self.pays else CAPITALE_GOUVERNEMENT]
        # le port de chaque ile : c est par la qu on embarque. Un port peut aussi etre un village ( Malden ).
        self.ports = {}
        for ile in self.iles:
            if self.pays is not None and ile == premiere:          # le port du pays, ou aucun ( Livonia : par air )
                if self.pays.get("port"): self.ports[ile] = self.lieux[self.pays["port"]]
                continue
            nom = PORTS.get(ile)
            cle = nom if ile == self.iles[0] else f"{ile}:{nom}"
            if cle in self.lieux:
                self.ports[ile] = self.lieux[cle]; continue
            # pas de port nomme : on prend la ville habitee la plus proche de la mer, d apres les lieux marins de l ile
            cotes = marines.get(ile, [])
            villes = [l for l in self.lieux.values() if l.ile == ile and l.type in ("capitale", "ville", "village")]
            if cotes and villes:
                self.ports[ile] = min(villes, key=lambda v: min(math.dist(v.pos, c) for c in cotes))
            elif villes:
                self.ports[ile] = villes[0]

    def de_type(self, *types):
        return [l for l in self.lieux.values() if l.type in types]

    @staticmethod
    def _routes_mesurees():
        """Les trajets que des camions ont vraiment faits dans Arma, s ils ont ete mesures."""
        chemin = os.path.join(ICI, "donnees", "routes_altis.json")
        try:
            with open(chemin) as f: return json.load(f)
        except Exception: return {}

    def habitables(self):
        return self.de_type("capitale", "ville", "village")

    def plus_proche(self, lieu, types):
        return min(self.de_type(*types), key=lambda x: lieu.distance(x))

    def port(self, ile):
        return self.ports.get(ile)

    def km_mer(self, a, b):
        """Deux iles ne se touchent pas : on va au port, on traverse, on repart du port d en face. Les positions des
        deux cartes ne sont pas dans le meme repere : la traversee est une distance FIXE, a calibrer en bateau."""
        pa, pb = self.port(a.ile), self.port(b.ile)
        km = 120.0                                        # traversee Altis - Malden, valeur d attente
        if pa is not None: km += self.km_route(a, pa)
        if pb is not None: km += self.km_route(pb, b)
        return km

    def km_route(self, a, b):
        """La longueur de route entre deux lieux. Quand un camion a REELLEMENT fait le trajet dans Arma ( point 7,
        `monde/routes.py` ), c est sa mesure qui fait foi ; sinon le vol d oiseau multiplie par 1,3, qui s est revele
        bon a 5-13 % pres sur les trois capitales."""
        if a.ile != b.ile: return self.km_mer(a, b)
        mesure = self.routes.get(f"{a.id}-{b.id}") or self.routes.get(f"{b.id}-{a.id}")
        if mesure and mesure.get("etat") == "arrive": return float(mesure["km_reels"])
        return 1.3 * a.distance(b) / 1000.0
