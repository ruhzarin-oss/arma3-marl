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


class Lieu:
    def __init__(self, id, type, pos, rayon=(0, 0)):
        self.id, self.type, self.pos, self.rayon = id, type, tuple(pos), tuple(rayon)
        self.marche = None          # la capitale dont le marche sert ce lieu
        self.stocks = {}            # biens presents sur place ( sites de production, depots, marches )

    def distance(self, autre):
        return math.dist(self.pos, autre.pos)

    def __repr__(self):
        return f"{self.id}({self.type})"


class Carte:
    def __init__(self, fichier=os.path.join(ICI, "donnees", "altis_lieux.json")):
        brut = json.load(open(fichier))
        self.routes = self._routes_mesurees()
        self.lieux = {}
        for l in brut:
            t = {"NameCityCapital": "capitale", "NameCity": "ville", "NameVillage": "village"}.get(l["type"])
            if t is None: t = AFFECTATION.get(l["id"])
            if t is None: continue                       # caps, iles, collines : pas de role dans la v1
            self.lieux[l["id"]] = Lieu(l["id"], t, l["pos"], l.get("rayon", (0, 0)))
        # chaque village est aussi une ferme : l agriculture vit dans les villages
        self.capitales = [l for l in self.lieux.values() if l.type == "capitale"]
        for l in self.lieux.values():
            l.marche = min(self.capitales, key=lambda c: l.distance(c))
        self.gouvernement = self.lieux[CAPITALE_GOUVERNEMENT]

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

    def km_route(self, a, b):
        """La longueur de route entre deux lieux. Quand un camion a REELLEMENT fait le trajet dans Arma ( point 7,
        `monde/routes.py` ), c est sa mesure qui fait foi ; sinon le vol d oiseau multiplie par 1,3, qui s est revele
        bon a 5-13 % pres sur les trois capitales."""
        mesure = self.routes.get(f"{a.id}-{b.id}") or self.routes.get(f"{b.id}-{a.id}")
        if mesure and mesure.get("etat") == "arrive": return float(mesure["km_reels"])
        return 1.3 * a.distance(b) / 1000.0
