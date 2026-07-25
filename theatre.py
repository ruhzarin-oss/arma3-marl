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
import os


class Theatre:
    def __init__(self, name, world, fob, spawn, port, game_port, mission, launch, notes=""):
        self.NAME = name              # identifiant court (stratis / altis)
        self.WORLD = world            # worldName Arma (Stratis / Altis)
        self.FOB = fob                # objectif du banc : (x, y)
        self.SPAWN = spawn            # départ des attaquants : (x, y)
        self.PORT = port              # pont natif TCP (NativeBridge)
        self.GAME_PORT = game_port    # port jeu (pour rejoindre)
        self.MISSION = mission        # dossier de mission
        self.LAUNCH = launch          # script de lancement du serveur
        self.NOTES = notes

    @property
    def fob_str(self):                # format attendu par les argparse existants : "x,y"
        return "%d,%d" % self.FOB

    @property
    def spawn_str(self):
        return "%d,%d" % self.SPAWN

    def __repr__(self):
        return "<Theatre %s world=%s fob=%s port=%d>" % (self.NAME, self.WORLD, self.fob_str, self.PORT)


SB = "/mnt/data/harmattan-sandbox"

THEATRES = {
    # --- STRATIS : le monde historique (leviathan001). NE PAS CASSER : c'est le point de comparaison. ---
    "stratis": Theatre(
        name="stratis", world="Stratis",
        fob=(3253, 2984),            # FOB Maxwell — l'objectif de tous les bancs A/B
        spawn=(3253, 3124),          # départ attaquants, 140 m au nord du FOB
        port=5816, game_port=3902,
        mission="HarmattanFOB.Stratis",
        launch=SB + "/launch_fob.sh",
        notes="Monde milsim complet : 25 FOB, garnisons, rôles, logistique. Baselines mesurées : timide 20% pris, téméraire 0%.",
    ),
    # --- ALTIS : le nouveau théâtre (meltemi001) + ALiVE. ---
    "altis": Theatre(
        name="altis", world="Altis",
        fob=(16797, 12783),          # PROVISOIRE : Pyrgos (terre ferme vérifiée). À REMPLACER par un vrai village de banc.
        spawn=(16797, 12923),        # 140 m au nord, même géométrie que Stratis
        port=5826, game_port=3912,
        mission="HarmattanBridge.Altis",
        launch=SB + "/launch_altis.sh",
        notes="ALiVE chargé (monde vivant virtualisé). FOB provisoire = Pyrgos centre-ville, à recaler sur un village avec asymétrie de couvert.",
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
