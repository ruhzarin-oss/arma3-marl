"""LE COTE ARMA DE LA GUERRE : une commande par minute d horloge murale, par le pont fichier du labo.

ArmaGuerre parle a GuerreIles.Malden ( instance 10 ) par la Liaison de labo/arma_labo.py : memes recus, memes pannes
( PontMort, SansRecu, Incomplet ), meme verrou d ecrivain unique. Un tour = GUERRE_fnc_tour : verser la bourse de
chaque camp, puis relire les zones, les forces, les pertes et les cibles. Jamais « aucune zone » a la place de
« pas de reponse » : une zone de la carte que la mission ne rend pas leve Incomplet.

FauxGuerre est le jouet a reponse connue des portes : il tient les proprietaires des zones qu on lui donne et
additionne ce qu on lui verse. Il ne prouve que la plomberie cote Python ; le SQF, seul Arma le prouve."""
import math, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "labo"))
import arma_labo as AL                                   # noqa: E402

INSTANCE = 10
PROFIL = f"/mnt/c/Users/Younes/hmtech{INSTANCE}"
PONT = f"/mnt/c/hmt_bridge/i{INSTANCE}"
VERSION_MISSION = 10                                      # = GUERRE_VERSION, derniere ligne de fonctions.sqf
CAMPS = ("EAST", "WEST", "RESISTANCE")                   # = GUERRE_CAMPS [east, west, independent]
TOLERANCE_M = 5.0
PATIENCE_TOUR_S = 8.0


def lire_tour(lignes, zones):
    """Les lignes R d un tour -> { zones : { n : camp }, camps : { camp : {...} }, temps }. `zones` : la carte de
    guerre ( guerre/zones.py ), secteurs ET bases, dans n importe quel ordre cote Arma."""
    proprio, vus = {}, set()
    for cle, v in lignes:
        if cle != "ZONE": continue
        if len(v) != 3: raise AL.Incomplet(f"ligne ZONE a {len(v)} nombres : {v!r}")
        x, y, c = v
        d, z = min((math.hypot(x - z["x"], y - z["y"]), z) for z in zones)
        if d > TOLERANCE_M: raise AL.Incomplet(f"zone en ({x}, {y}) inconnue de la carte ( la plus proche a {d:.0f} m )")
        if z["n"] in vus: raise AL.Incomplet(f"zone {z['n']} rendue deux fois")
        vus.add(z["n"]); proprio[z["n"]] = CAMPS[int(c)] if 0 <= int(c) < 3 else None
    manquent = sorted(z["n"] for z in zones if z["n"] not in vus)
    if manquent: raise AL.Incomplet(f"zones sans reponse : {manquent} - jamais lues comme « a personne »")
    camps = {}
    for cle, v in lignes:
        if cle == "VERSE" and len(v) == 3:
            camps.setdefault(CAMPS[int(v[0])], {}).update(verse_total=v[1], caisse=v[2])
        elif cle == "FORCES" and len(v) == 6:
            camps.setdefault(CAMPS[int(v[0])], {}).update(vivants=int(v[1]), groupes=int(v[2]), pertes=int(v[3]),
                                                          depense=v[4], achats=int(v[5]))
        elif cle == "CIBLE" and len(v) == 3:
            camps.setdefault(CAMPS[int(v[0])], {})["cible"] = None if v[1] < 0 else (v[1], v[2])
        elif cle == "EM" and len(v) == 8:                # l etat-major du camp ( doctrine.sqf )
            camps.setdefault(CAMPS[int(v[0])], {})["em"] = {"garnison": int(v[1]), "menace": int(v[2]), "defenseurs": int(v[3]),
                                                            "reunis": int(v[4]), "assaut": bool(v[5]),
                                                            "ralliement": None if v[6] < 0 else (v[6], v[7])}
        elif cle == "ANNULE" and len(v) == 2:
            camps.setdefault(CAMPS[int(v[0])], {})["annules"] = v[1]
    for camp in ("EAST", "WEST"):
        c = camps.get(camp, {})
        if not {"caisse", "vivants", "cible"} <= set(c):
            raise AL.Incomplet(f"camp {camp} incomplet dans le tour : {c!r}")
    temps = [v[0] for cle, v in lignes if cle == "TEMPS" and len(v) == 1]
    return {"zones": proprio, "camps": camps, "temps": temps[0] if temps else None}


def _numeros(reserves, camp):
    ns = [int(k) for k in (reserves or {}).get(camp, [])]
    if any(k <= 0 or k >= 1_000_000 for k in ns): raise AL.Refus(f"numeros de front hors [1 ; 999 999] : {ns!r}")
    return "[" + ", ".join(str(k) for k in ns) + "]"


def corps_du_tour(points, reserves=None):
    """Le SQF d un tour : deux nombres ( et, pour suivre les soldats, les numeros de front mobilises ), rien d autre :
    aucun texte du moteur n entre dans Arma."""
    pe, pw = (float(points.get(c, 0.0)) for c in ("EAST", "WEST"))
    for p in (pe, pw):
        if not math.isfinite(p) or p < 0: raise AL.Refus(f"points a verser invalides : {points!r}")
    if reserves is None: return f"[{pe:.3f}, {pw:.3f}] call GUERRE_fnc_tour;"
    return f"[{pe:.3f}, {pw:.3f}, {_numeros(reserves, 'EAST')}, {_numeros(reserves, 'WEST')}] call GUERRE_fnc_tour2;"


def lire_positions(lignes):
    """U camp numero x y degats -> { camp : [ ( numero, x, y, degats ) ] } ; MORT camp numero -> { camp : [ numero ] }."""
    vivants, morts = {"EAST": [], "WEST": []}, {"EAST": [], "WEST": []}
    for cle, v in lignes:
        if cle == "U":
            if len(v) != 5: raise AL.Incomplet(f"ligne U a {len(v)} nombres : {v!r}")
            vivants[CAMPS[int(v[0])]].append((int(v[1]), v[2], v[3], v[4]))
        elif cle == "MORT":
            if len(v) != 2: raise AL.Incomplet(f"ligne MORT a {len(v)} nombres : {v!r}")
            morts[CAMPS[int(v[0])]].append(int(v[1]))
    return vivants, morts


class ArmaGuerre:
    def __init__(self, zones, instance=INSTANCE, profil=PROFIL, pont=PONT):
        self.zones = zones
        self.liaison = AL.Liaison(profil, pont, instance=instance)
        self.verrou = AL.VerrouEcrivain(os.path.join(AL.ETAT, f"guerre_i{instance}.ecrivain"))
        self.ouvert = False

    def ouvrir(self):
        self.verrou.prendre()
        try:
            self.liaison.ouvrir()
            self.canari()
        except Exception:
            self.verrou.rendre(); raise
        self.ouvert = True
        return self

    def fermer(self):
        self.liaison.fermer(); self.verrou.rendre(); self.ouvert = False

    def canari(self):
        r = self.liaison.executer('["CANARI", [HMT_n, (if (isNil "GUERRE_VERSION") then {0} else {GUERRE_VERSION})]] call LABO_R;')
        n, version = AL._une(r["lignes"], "CANARI", 2)
        if version != VERSION_MISSION:
            raise AL.Incomplet(f"la mission jouee est en version {version}, le module attend {VERSION_MISSION} : "
                               "ce n est pas GuerreIles.Malden du depot ( relancer guerre/lancer_guerre.sh )")
        return {"actuateur_n": n, "version": version, "recu": r["recu"]}

    def tour(self, points, reserves=None):
        r = self.liaison.executer(corps_du_tour(points, reserves), patience=PATIENCE_TOUR_S)
        t = lire_tour(r["lignes"], self.zones)
        t["recu"] = r["recu"]
        return t

    def positions(self):
        r = self.liaison.executer("[] call GUERRE_fnc_positions;", patience=PATIENCE_TOUR_S)
        return lire_positions(r["lignes"])

    def identifier(self, reserves):
        """Donne un numero de front aux soldats deja poses sans numero ( branchement en cours de bataille )."""
        r = self.liaison.executer(f"[{_numeros(reserves, 'EAST')}, {_numeros(reserves, 'WEST')}] call GUERRE_fnc_identifier;")
        return {CAMPS[int(v[0])]: {"identifies": int(v[1]), "sans_numero": int(v[2])} for c, v in r["lignes"] if c == "IDENTIFIE"}


class FauxGuerre:
    """Le jouet : proprietaires fixes par le test ( `proprio` ), versements additionnes. Aucun combat. Les numeros de
    front recus deviennent des soldats vivants au releve suivant ; `tuer( camp, numero )` en fait un mort."""

    def __init__(self, zones, proprio=None):
        self.zones = zones
        self.proprio = dict(proprio or {z["n"]: ("WEST" if z.get("camp_base") != 1 else "EAST") for z in zones})
        self.verse = {"EAST": 0.0, "WEST": 0.0}
        self.tours = 0
        self.soldats = {"EAST": {}, "WEST": {}}      # numero -> ( x, y ) des vivants
        self.morts = {"EAST": [], "WEST": []}         # morts pas encore rapportes

    def ouvrir(self): return self
    def fermer(self): pass

    def tuer(self, camp, k):
        if self.soldats[camp].pop(k, None) is not None: self.morts[camp].append(k)

    def positions(self):
        v = {c: [(k, x, y, 0.0) for k, (x, y) in sorted(s.items())] for c, s in self.soldats.items()}
        m, self.morts = self.morts, {"EAST": [], "WEST": []}
        return v, m

    def tour(self, points, reserves=None):
        corps_du_tour(points, reserves)                  # le meme controle que le vrai
        for c, ks in (reserves or {}).items():
            for k in ks: self.soldats[c][int(k)] = (5000.0 + k, 5000.0)
        for c in self.verse: self.verse[c] += float(points.get(c, 0.0))
        self.tours += 1
        return {"zones": dict(self.proprio),
                "camps": {c: {"verse_total": v, "caisse": v, "vivants": len(self.soldats[c]), "groupes": 0, "pertes": 0,
                              "depense": 0.0, "achats": 0, "cible": None} for c, v in self.verse.items()},
                "temps": self.tours * 60, "recu": {"rtt_ms": 0}}
