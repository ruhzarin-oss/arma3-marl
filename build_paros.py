"""build_paros — cree paros.py = maneuvers.py avec la geographie portee sur PAROS (ville de colline).
Copie tout le repertoire (M1-M12) et ne remplace QUE le bloc de coordonnees, ancre sur la reconnaissance."""
import re

PAROS_GEO = '''# --- geographie PAROS (ville de colline, ancree sur recon_paros : terre + LOS verifies) ---
COMPLEXE  = (20885, 16959)        # objectif : garnison, centre-ville Paros (50 m, bati dense)
CRETE     = (20708, 17136)        # base de feu : hauteur NORD-OUEST 62 m, LOS sur l'objectif (domine la ville)
ATTENTE   = (20960, 16800)        # attente assaut ouest (approche SE, bas)
ATTENTE_E = (21070, 16860)        # attente assaut est (approche E, bas)
LIGNE_O   = (20930, 16850)        # ligne de depart ouest
LIGNE_E   = (21020, 16895)        # ligne de depart est
FLANC_O   = (20737, 16811)        # flanc OUEST reel (SO 47 m, LOS oui)
FLANC_E   = (21033, 17107)        # flanc EST reel (NE 38 m, LOS oui)
INF_O     = (20850, 16760)        # axe d'infiltration sud-ouest (bas)
INF_E     = (20990, 16790)        # axe d'infiltration sud-est (bas)
POSTE_RES = (20900, 16700)        # poste d'attente reserve (sud, bas)
QRF_PT    = (20885, 17220)        # contre-attaque : surgit du NORD, derriere la ville
LZ        = (20885, 16700)        # exfiltration : sud, bas, terre

SPAWN_APPUI = (20600, 17120); SPAWN_ASSAUT = (20990, 16600)   # appui spawn NW haut -> monte sur CRETE ; assaut O spawn SE bas
SPAWN_A_EST = (21130, 16800); SPAWN_RESERVE = (20900, 16630)  # assaut E spawn E bas ; reserve sud bas
SPAWNS = {"SQ_APPUI": SPAWN_APPUI, "SQ_A_OUEST": SPAWN_ASSAUT, "SQ_A_EST": SPAWN_A_EST, "SQ_RESERVE": SPAWN_RESERVE}
GARRISON = [(COMPLEXE[0], COMPLEXE[1], 12, 60), (20960, 17050, 4, 90), (20790, 16880, 4, 90)]  # noyau ville + 2 patrouilles
SQUADS = (("SQ_APPUI", 7), ("SQ_A_OUEST", 7), ("SQ_A_EST", 7), ("SQ_RESERVE", 7))

'''

if __name__ == "__main__":
    src = open("maneuvers.py").read()
    # remplacer le bloc geographie : de "# --- géographie" jusqu'a (exclus) "# succès commun"
    start = src.index("# --- g")          # debut bloc geo (accent-insensible via 'g')
    end = src.index("# succ")             # debut du SUCCESS (a garder)
    out = src[:start] + PAROS_GEO + src[end:]
    out = out.replace('"""maneuvers', '"""paros (theatre Paros) — derive de maneuvers', 1)
    with open("paros.py", "w") as f:
        f.write(out)
    print("paros.py cree (%d lignes). Geographie portee sur Paros, repertoire M1-M12 intact." % len(out.splitlines()))
    # sanity : importable + memes manoeuvres
    import importlib.util
    spec = importlib.util.spec_from_file_location("paros", "paros.py"); pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
    print("manoeuvres disponibles :", list(pm.MANEUVERS.keys()))
    print("COMPLEXE =", pm.COMPLEXE, "| CRETE =", pm.CRETE, "| SPAWNS =", pm.SPAWNS)
