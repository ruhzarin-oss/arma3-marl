#!/usr/bin/env python3
"""theatre.py — CONFIGURATION DE THÉÂTRE : un seul endroit pour les coordonnées, ports et missions.

Avant : « 3253,2984 » était écrit en dur dans 18 fichiers. Changer de carte = 18 modifications.
Après  : un script demande `from theatre import T` et lit `T.FOB`, `T.PORT`, `T.MISSION`...

DÉFAUT = STRATIS -> tous les scripts existants gardent EXACTEMENT le même comportement.
Bascule Altis, au choix :
    export HMT_THEATRE=altis          (variable d'environnement, avant de lancer)
    python mon_script.py --theatre altis   (si le script utilise add_theatre_arg)
    from theatre import use; use("altis")  (dans le code)

Usage typique dans un script :
    from theatre import T
    ap.add_argument("--fob", default=T.fob_str)     # au lieu de "3253,2984"
    b = NativeBridge(port=T.PORT)                   # au lieu de 5816
"""
import os, math


class Theatre:
    def __init__(self, name, world, fob, port, game_port, mission, launch, approach_az=0, dist=140.0, notes=""):
        self.NAME = name              # identifiant court (stratis / altis)
        self.WORLD = world            # worldName Arma (Stratis / Altis)
        self.FOB = fob                # objectif du banc : (x, y)
        self.APPROACH_AZ = approach_az  # AZIMUT d'approche (d'où viennent les attaquants) : 0=nord, 90=est, 180=sud, 270=ouest
        self.DIST = dist              # distance de départ (m)
        self.PORT = port              # pont natif TCP (NativeBridge)
        self.GAME_PORT = game_port    # port jeu (pour rejoindre)
        self.MISSION = mission        # dossier de mission
        self.LAUNCH = launch          # script de lancement du serveur
        self.NOTES = notes

    def spawn_for(self, fob=None, dist=None):
        """Départ des attaquants pour un objectif donné, selon l'AXE D'APPROCHE du théâtre.
        Stratis (az=0) -> (fx, fy+140), soit exactement l'ancien comportement codé en dur."""
        fx, fy = fob if fob else self.FOB
        d = dist if dist else self.DIST
        rad = math.radians(self.APPROACH_AZ)
        return (fx + math.sin(rad) * d, fy + math.cos(rad) * d)

    @property
    def SPAWN(self):
        return self.spawn_for()

    @property
    def fob_str(self):                # format attendu par les argparse existants : "x,y"
        return "%d,%d" % self.FOB

    @property
    def spawn_str(self):
        return "%d,%d" % tuple(int(round(v)) for v in self.SPAWN)

    def __repr__(self):
        return "<Theatre %s world=%s fob=%s port=%d>" % (self.NAME, self.WORLD, self.fob_str, self.PORT)


SB = "/mnt/data/harmattan-sandbox"

THEATRES = {
    # --- STRATIS : le monde historique (leviathan001). NE PAS CASSER : c'est le point de comparaison. ---
    "stratis": Theatre(
        name="stratis", world="Stratis",
        fob=(3253, 2984),            # FOB Maxwell — l'objectif de tous les bancs A/B
        approach_az=0,               # attaquants au NORD (= l'ancien « fy + 140 » codé en dur)
        port=5816, game_port=3902,
        mission="HarmattanFOB.Stratis",
        launch=SB + "/launch_fob.sh",
        notes="Monde milsim complet : 25 FOB, garnisons, rôles, logistique. Baselines : timide 20% pris, téméraire 0%. "
              "Couvert UNIFORME autour du FOB -> le flanc ne s'y distingue pas (finding 23/07).",
    ),
    # --- ALTIS : le nouveau théâtre (meltemi001) + ALiVE. ---
    "altis": Theatre(
        name="altis", world="Altis",
        fob=(16781, 12604),          # PYRGOS — banc mesuré : meilleure ASYMÉTRIE de couvert des 48 villes d'Altis
        approach_az=270,             # attaquants à l'OUEST : couloir frontal DÉCOUVERT, flancs nord/sud COUVERTS
        port=5826, game_port=3912,
        mission="HarmattanBridge.Altis",
        launch=SB + "/launch_altis.sh",
        notes="ALiVE chargé (monde vivant virtualisé). Banc Pyrgos mesuré 25/07 : couvert frontal 13 vs flancs 46 (score 33, "
              "1er sur 48 villes). Vérifié : objectif et départ sur terre, objectif dans le bâti (15 bât./40 m), "
              "couloir d'approche dégagé (2 bât.). C'est l'asymétrie qui manquait à Stratis.",
    ),
}

# théâtre actif — DÉFAUT STRATIS (compatibilité totale avec l'existant)
T = THEATRES[os.environ.get("HMT_THEATRE", "stratis").strip().lower()]


def use(name):
    """Bascule le théâtre actif. Renvoie le théâtre choisi."""
    global T
    key = name.strip().lower()
    if key not in THEATRES:
        raise ValueError("théâtre inconnu : %s (connus : %s)" % (name, ", ".join(THEATRES)))
    T = THEATRES[key]
    return T


def add_theatre_arg(ap):
    """Ajoute --theatre à un argparse existant. À appeler AVANT parse_args()."""
    ap.add_argument("--theatre", choices=sorted(THEATRES), default=None,
                    help="théâtre : stratis (défaut) ou altis")
    return ap


def apply_theatre_arg(args):
    """À appeler APRÈS parse_args() : applique --theatre s'il est fourni. Renvoie le théâtre actif."""
    if getattr(args, "theatre", None):
        return use(args.theatre)
    return T


if __name__ == "__main__":
    print("=== THÉÂTRES DISPONIBLES ===")
    for k, th in THEATRES.items():
        actif = "  <-- ACTIF" if th.NAME == T.NAME else ""
        print("  %-8s monde=%-8s fob=%-14s spawn=%-14s pont=%d jeu=%d%s" % (
            k, th.WORLD, th.fob_str, th.spawn_str, th.PORT, th.GAME_PORT, actif))
        print("           mission=%s" % th.MISSION)
        print("           %s" % th.NOTES)
    print("\nbascule : export HMT_THEATRE=altis   (défaut = stratis)")
