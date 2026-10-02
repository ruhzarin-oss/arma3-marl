#!/usr/bin/env python3
"""Le guide des symboles de CMO ( 1.10 ) en français : les images du jeu ( dossier Symbols ) rangées par domaine, chaque type
avec ses variantes d'identification, puis les cercles et lignes de la carte, les arcs, la barre du temps et les boutons.
HTML imprimé en PDF par Chrome sans tête."""
import base64
import html
import io
import os
import re
import subprocess

from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE_HTML = os.path.join(ICI, "symboles_cmo.html")
SORTIE_PDF = os.path.join(ICI, "Symboles CMO.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

POSTURES = {"friendly": "ami", "friednly": "ami", "unfriendly": "non-ami", "neutral": "neutre", "hostile": "hostile",
            "unknown": "inconnu", "blank": "sans identification"}
ORDRE_POSTURE = ["friendly", "unfriendly", "neutral", "hostile", "unknown", "blank"]
FORMES = {"rectangle": "cadre rectangle", "diamond": "cadre losange", "flower": "cadre trèfle", "blank": "vide"}

TYPES = {  # code CMO -> nom français
    "air_fw": "Avion ( voilure fixe )", "air_rw": "Hélicoptère ( voilure tournante )", "UAS": "Drone",
    "air_decoy": "Leurre aérien", "AirGroup": "Groupe aérien ( plusieurs avions )", "aerostat": "Aérostat ( ballon captif )",
    "satellite": "Satellite", "missile": "Missile en vol", "guidedprojectile": "Obus guidé en vol",
    "RV": "Corps de rentrée ( ogive balistique )", "MaRV": "Corps de rentrée manœuvrant", "paradrop": "Parachutage",
    "seasurface": "Navire de surface", "carrier": "Porte-avions", "SurfaceGroup": "Groupe naval de surface",
    "sub": "Sous-marin", "SubGroup": "Groupe de sous-marins", "torp": "Torpille", "sonobuoy_active": "Bouée acoustique active",
    "sonobuoy_passive": "Bouée acoustique passive", "underwaterdecoy": "Leurre sous-marin",
    "AirBase": "Base aérienne", "Installation": "Installation fixe", "fixed": "Installation fixe ( autre symbole )",
    "radar": "Radar", "SAM": "Défense sol-air ( missiles )", "AAA": "Artillerie antiaérienne ( canons )",
    "airdef_mis": "Défense aérienne, missiles", "airdef_arty": "Défense aérienne, canons", "HQ": "Poste de commandement",
    "headquarters": "Quartier général", "supply": "Ravitaillement", "CSS": "Soutien logistique",
    "H_S": "Compagnie de commandement et de services ( H&S )", "surveillance": "Surveillance",
    "mobile": "Unité terrestre mobile", "mobilegroup": "Groupe terrestre mobile",
    "armor": "Blindés ( chars )", "armor_recon": "Reconnaissance blindée", "ACV": "Véhicule de combat blindé",
    "LAR": "Reconnaissance blindée légère", "AAV": "Véhicule d'assaut amphibie", "infantry": "Infanterie",
    "infantry_old": "Infanterie ( ancien symbole )", "mechinfantry": "Infanterie mécanisée",
    "mechInfantry": "Infanterie mécanisée ( variante )", "mechinf": "Infanterie mécanisée ( variante courte )",
    "motorized_infantry": "Infanterie motorisée", "mechwheeled": "Infanterie mécanisée sur roues",
    "amp_mechwheeled": "Infanterie mécanisée amphibie sur roues", "amph_mechwheeled": "Infanterie mécanisée amphibie ( variante )",
    "marines": "Infanterie de marine", "mechmarines": "Infanterie de marine mécanisée", "airborne": "Troupes aéroportées",
    "mechairborne": "Aéroporté mécanisé", "air_assault": "Assaut aérien ( héliporté )", "mountain": "Troupes de montagne",
    "special_forces": "Forces spéciales", "special_forces_": "Forces spéciales ( variante )", "recon": "Reconnaissance",
    "amphibious_recon": "Reconnaissance amphibie", "anti_tank": "Antichar", "anti_tank_W": "Antichar sur roues",
    "engineer": "Génie", "combined_arms": "Interarmes", "artillery_gun": "Artillerie à canon",
    "artillery_SP": "Artillerie automotrice", "artillery_towed": "Artillerie tractée", "artillery_mortar": "Mortiers",
    "artillery_rocket_tracked": "Lance-roquettes multiple chenillé", "artillery_rocket_wheeled": "Lance-roquettes multiple sur roues",
    "artillery_SSM": "Missiles sol-sol", "arty_gun": "Pièce d'artillerie", "arty_mis": "Missile d'artillerie",
    "unknown": "Type non identifié",
}
DOMAINES = [
    ("Dans les airs", ["air_fw", "air_rw", "UAS", "air_decoy", "AirGroup", "aerostat", "satellite", "missile",
                       "guidedprojectile", "RV", "MaRV", "paradrop"]),
    ("En mer", ["seasurface", "carrier", "SurfaceGroup"]),
    ("Sous la mer", ["sub", "SubGroup", "torp", "sonobuoy_active", "sonobuoy_passive", "underwaterdecoy"]),
    ("Installations et défense aérienne", ["AirBase", "Installation", "fixed", "radar", "SAM", "AAA", "airdef_mis",
                                           "airdef_arty", "HQ", "headquarters", "supply", "CSS", "H_S", "surveillance",
                                           "mobile", "mobilegroup"]),
    ("Forces terrestres", ["armor", "armor_recon", "ACV", "LAR", "AAV", "infantry", "infantry_old", "mechinfantry",
                           "mechInfantry", "mechinf", "motorized_infantry", "mechwheeled", "amp_mechwheeled",
                           "amph_mechwheeled", "marines", "mechmarines", "airborne", "mechairborne", "air_assault",
                           "mountain", "special_forces", "special_forces_", "recon", "amphibious_recon", "anti_tank",
                           "anti_tank_W", "engineer", "combined_arms"]),
    ("Artillerie et missiles sol-sol", ["artillery_gun", "artillery_SP", "artillery_towed", "artillery_mortar",
                                        "artillery_rocket_tracked", "artillery_rocket_wheeled", "artillery_SSM", "arty_gun",
                                        "arty_mis"]),
    ("Non identifié", ["unknown"]),
]
OBJETS = {"Bomb": "Bombe", "Rocket": "Roquette", "DC": "Grenade anti-sous-marine", "mine_bottom": "Mine de fond",
          "mine_float": "Mine dérivante", "mine_limpet": "Mine ventouse ( posée sur coque )", "mine_mobile": "Mine mobile",
          "mine_moored": "Mine à orin", "mine_rising": "Mine remontante", "LockedRP": "Point de référence verrouillé",
          "LockedRP_selected": "Point de référence verrouillé, sélectionné", "hosted_units": "Unités hébergées ( à bord, au sol )",
          "rescue": "Sauvetage", "unknown": "Contact non identifié", "unknown_flower_": "Contact non identifié ( cadre trèfle )",
          "artillery_SSM": "Missiles sol-sol ( sans posture )", "artillery_SSM_rectangle_": "Missiles sol-sol ( cadre rectangle )"}

ARCS = {"360": "Tout autour ( 360° )", "base": "Arc de base", "pb": "Bâbord avant", "pmf": "Bâbord milieu, vers l'avant",
        "pma": "Bâbord milieu, vers l'arrière", "ps": "Bâbord arrière", "sb": "Tribord avant",
        "smf": "Tribord milieu, vers l'avant", "sma": "Tribord milieu, vers l'arrière", "ss": "Tribord arrière"}
BARRE = {"Pause": "Pause", "Play": "Lecture", "Play_1x": "Lecture, temps réel", "Time_1x": "Temps réel ( x1 )",
         "Time_2x": "x2", "Time_5x": "x5", "Time_15x": "x15",
         "Time_DoubleFlame": "« Double flamme » : grands pas de temps, simulation moins fine",
         "Time_Turbo": "Turbo : le plus vite possible", "Record": "Enregistrer la partie", "RecordStop": "Arrêter l'enregistrement",
         "Layers": "Couches de la carte", "Special": "Actions spéciales", "OptionsIcon": "Options", "Arrow": "Flèche"}
BOUTONS = {"Btn_Aircraft_Operations": "Opérations aériennes ( avions d'une base ou d'un navire )",
           "Btn_Auto_Engage_Target": "Engager une cible, automatique", "Btn_Manually_Engage_Target": "Engager une cible, manuel",
           "Btn_Boat_Operations": "Opérations des embarcations", "Btn_Formation_Editor": "Formation d'un groupe",
           "Btn_Magazines": "Magasins ( munitions )", "Btn_Mission_Editor": "Missions", "Btn_Mount_Weapons": "Affûts et armes",
           "Btn_Plot_Course": "Tracer une route", "Btn_Sensors": "Capteurs", "Btn_Systems_Damage": "Systèmes et dégâts",
           "Btn_Throttle_Altitude": "Vitesse et altitude", "Btn_Unit-Group_Doctrine": "Doctrine de l'unité ou du groupe"}
METEO = {"Noon": "Jour", "DawnDusk": "Aube ou crépuscule", "Night": "Nuit", "NoCloud": "Ciel dégagé", "Cloudy": "Nuageux",
         "LightRain": "Pluie faible", "HeavyRain": "Pluie forte", "Impact": "Impact", "Impact_Electronic": "Impact électronique",
         "Lock": "Verrouillé", "Positive": "Positif", "Negative": "Négatif"}


def img(chemin, cote=56):
    try:
        im = Image.open(chemin).convert("RGBA")
    except Exception:
        return ""
    im.thumbnail((cote, cote), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return f'<img src="data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}" alt="">'


def analyser(nom):
    """( code du type, posture, forme ) d'un fichier du jeu, ou ( None, None, None )."""
    base = re.sub(r"(\.png)+$|\.gif$", "", nom, flags=re.I)
    t = base.split("_")
    for i, x in enumerate(t):
        if x.lower() in POSTURES:
            code = "_".join(t[:i])
            if code == "special_forces" and i + 1 < len(t) and t[i - 1] == "":
                code = "special_forces_"
            reste = [y for y in t[i + 1:] if y]
            return code, x.lower().replace("friednly", "friendly"), " ".join(FORMES.get(y.lower(), y) for y in reste)
    return None, None, None


def catalogue(jeu):
    d = os.path.join(ICI, jeu)
    par_type, objets = {}, []
    for n in sorted(os.listdir(d)):
        if not re.search(r"\.(png|gif)$", n, re.I) or n.lower().endswith(".gif") and os.path.exists(os.path.join(d, n[:-4] + ".png")):
            continue
        code, posture, forme = analyser(n)
        code = {"special_forces_": "special_forces_"}.get(code, code)
        if code is None or code == "":
            objets.append(n)
            continue
        par_type.setdefault(code, []).append((posture, forme, n))
    out = [f'<h1 class="saut">Jeu « {html.escape(jeu)} »</h1>']
    vus = set()
    for titre, codes in DOMAINES:
        lignes = []
        for c in codes + ([] if titre != "Non identifié" else [c for c in par_type if c not in vus and c not in sum((x[1] for x in DOMAINES), [])]):
            if c not in par_type or c in vus:
                continue
            vus.add(c)
            v = sorted(par_type[c], key=lambda x: (ORDRE_POSTURE.index(x[0]) if x[0] in ORDRE_POSTURE else 9, x[1]))
            cases = "".join(f'<div class="case">{img(os.path.join(d, n))}<div class="leg">{POSTURES[p]}'
                            f'{"<br>" + html.escape(f) if f else ""}</div></div>' for p, f, n in v)
            lignes.append(f'<div class="type"><div class="nom">{html.escape(TYPES.get(c, c))}<div class="code">{html.escape(c)}</div></div>'
                          f'<div class="cases">{cases}</div></div>')
        if lignes:
            out.append(f"<h2>{titre}</h2>" + "".join(lignes))
    if objets:
        cases = []
        for n in objets:
            cle = re.sub(r"(\.png)+$|\.gif$", "", n, flags=re.I)
            cases.append(f'<div class="case large">{img(os.path.join(d, n))}<div class="leg">{html.escape(OBJETS.get(cle, cle))}</div></div>')
        out.append('<h2>Armes, mines, repères et objets</h2><div class="cases">' + "".join(cases) + "</div>")
    return "".join(out)


def grille(dossier, table, cote=72, cle=lambda n: n):
    cases = []
    for n in sorted(os.listdir(os.path.join(ICI, dossier))):
        if not n.lower().endswith(".png"):
            continue
        k = cle(n[:-4])
        if k in table:
            cases.append(f'<div class="case large">{img(os.path.join(ICI, dossier, n), cote)}<div class="leg">{html.escape(table[k])}</div></div>')
    return '<div class="cases">' + "".join(cases) + "</div>"


def anneau(couleur, texte, tirets=False):
    style = f"border: 3px {'dashed' if tirets else 'solid'} {couleur};"
    return f'<div class="anneau"><span class="fond"><span class="rond" style="{style}"></span></span>{html.escape(texte)}</div>'


def ligne(couleur, texte):
    return f'<div class="anneau"><span class="fond"><span class="trait" style="border-top: 3px dashed {couleur};"></span></span>{html.escape(texte)}</div>'


def page():
    exemple = os.path.join(ICI, "NTDS")
    ex = "".join(f'<div class="case large">{img(os.path.join(exemple, f"air_fw_{p}.png"), 72)}<div class="leg">{POSTURES[p]}</div></div>'
                 for p in ORDRE_POSTURE if os.path.exists(os.path.join(exemple, f"air_fw_{p}.png")))
    arcs = grille("arcs", ARCS, 80, cle=lambda n: re.sub(r"^arc_|\d$", "", n))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Symboles de CMO</title><style>
@page {{ size: A4; margin: 14mm 12mm; }}
body {{ font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1d1d1f; font-size: 10.5pt; }}
h1 {{ font-size: 20pt; margin: 0 0 6mm; }} h2 {{ font-size: 13pt; margin: 6mm 0 2mm; border-bottom: 1px solid #ccc; padding-bottom: 1mm; }}
.saut {{ page-break-before: always; }}
.couv {{ height: 250mm; display: flex; flex-direction: column; justify-content: center; }}
.couv h1 {{ font-size: 30pt; }} .couv p {{ font-size: 12pt; color: #555; max-width: 150mm; }}
.type {{ display: flex; align-items: center; border-bottom: 1px solid #eee; padding: 1.2mm 0; page-break-inside: avoid; }}
.nom {{ width: 52mm; font-weight: 600; font-size: 9.5pt; }} .code {{ font-weight: 400; color: #888; font-size: 7.5pt; }}
.cases {{ display: flex; flex-wrap: wrap; gap: 1.5mm; }}
.case {{ width: 19mm; text-align: center; }} .case.large {{ width: 34mm; }}
.case img {{ display: block; margin: 0 auto; background: #2b3a4a; border-radius: 2px; padding: 1px; }}
.leg {{ font-size: 7pt; color: #444; line-height: 1.15; margin-top: 0.6mm; }}
.anneau {{ display: flex; align-items: center; gap: 4mm; margin: 1.6mm 0; }}
.fond {{ display: inline-flex; align-items: center; justify-content: center; width: 20mm; height: 13mm; background: #2b3a4a; border-radius: 2px; }}
.rond {{ display: inline-block; width: 9mm; height: 9mm; border-radius: 50%; }}
.trait {{ display: inline-block; width: 16mm; height: 0; }}
.boite {{ background: #f4f4f6; border-radius: 3px; padding: 3mm 4mm; margin: 3mm 0; }}
li {{ margin: 0.8mm 0; }}
</style></head><body>
<div class="couv"><h1>Lire la carte de CMO</h1>
<p>Tous les symboles de Command: Modern Operations 1.10, tirés des images du jeu ( dossier <i>Symbols</i> ), avec leur sens en
français : les quatre jeux de symboles ( NTDS, APP-6, Directional, Stylized ), les armes et repères, les cercles et lignes de
la carte, les arcs de tir, la barre du temps et les boutons d'unité.</p>
<p>Les symboles sont montrés sur fond sombre, comme sur la carte du jeu.</p></div>

<h1 class="saut">Comment lire un symbole</h1>
<div class="boite"><b>La couleur dit la posture</b>, c'est-à-dire ce que votre camp pense de cette unité. <b>La forme dit le
domaine</b> ( air, surface, sous-marin, sol ) ; <b>le dessin au centre dit le type</b> ( chasseur, hélicoptère, char, radar… ).</div>
<div class="cases">{ex}</div>
<ul>
<li><b>Ami</b> ( bleu clair ) : votre camp, ou un camp allié. Une petite lettre <b>F</b> marque un contact ami ; une lettre <b>A</b>, en bas à
gauche, un allié ( postures amies dans les deux sens ).</li>
<li><b>Non-ami</b> ( orange ) : un camp qui ne vous aime pas, sans être en guerre ; on ne tire pas dessus sans ordre.</li>
<li><b>Neutre</b> ( vert ) : ni ami ni ennemi ( trafic civil, pays non engagé ).</li>
<li><b>Hostile</b> ( rouge ) : ennemi ; vos unités peuvent l'engager selon leurs règles de tir.</li>
<li><b>Inconnu</b> ( jaune ) : contact détecté mais pas encore identifié ; sa posture n'est pas connue.</li>
<li><b>Sans identification</b> ( blanc ) : symbole vierge, avant toute classification.</li>
</ul>
<div class="boite"><b>Petits chiffres blancs</b> à côté d'une unité : ses points de visée ( par exemple les quatre chars d'un
peloton ), pour savoir combien d'armes lui allouer.<br><b>Bloc de données</b> ( texte blanc à droite ) : nom, cap et vitesse.<br>
<b>Vue groupe ou vue unité</b> : touche 9 du pavé numérique ; en vue groupe, un symbole de groupe remplace ses membres.<br>
<b>Points de référence</b> : repères de zones et de routes ; non sélectionné, sélectionné ( son nom s'affiche ), ou verrouillé
( on ne peut pas le déplacer ).</div>
<div class="boite"><b>Changer de jeu de symboles</b> : dans les options du jeu, rubrique de l'affichage de la carte. NTDS ( norme
navale américaine ) est le jeu par défaut ; APP-6 est la norme de l'OTAN ; Directional oriente le symbole selon le cap ; Stylized
dessine des silhouettes.</div>

<h1 class="saut">Cercles et lignes de la carte</h1>
<h2>Portée des capteurs</h2>
{anneau("#ffffff", "Capteurs aériens ( radars air ) : blanc")}
{anneau("#f5d90a", "Capteurs de surface : jaune")}
{anneau("#39ff14", "Capteurs sous-marins actifs ( sonars ) : vert vif")}
<h2>Portée des armes</h2>
{anneau("#ff8fc8", "Armes contre avions : rose")}
{anneau("#8b0000", "Armes contre navires : rouge foncé")}
{anneau("#8b5a2b", "Armes contre la terre : brun")}
{anneau("#3d7a3d", "Armes sous-marines : vert terne")}
{anneau("#3b82f6", "Rayon d'action d'un avion ( distance franchissable, pas rayon de combat ) : bleu")}
{anneau("#ff8fc8", "Portée théorique d'un contact ennemi identifié : même couleur, en tirets", True)}
<h2>Lignes</h2>
{ligne("#e00000", "Illumination : tirets rouges, du radar de conduite de tir vers sa cible")}
{ligne("#00b050", "Ciblage : tirets verts, du tireur vers sa cible, avec l'heure prévue du tir")}
<ul>
<li><b>Liaisons de données</b> : lignes entre unités qui se transmettent des informations.</li>
<li><b>Émissions des contacts</b> : rayonnements radar repérés chez l'adversaire ( tous, sélectionné, ou seulement les
radars de conduite de tir ).</li>
<li><b>Routes tracées</b> et <b>zones de mission</b> : la route d'une unité ; la zone d'une mission, encadrée, avec son nom.</li>
<li><b>Ligne de vue</b> ( LOS ) : zone colorée de ce qu'une unité peut voir, relief compris.</li>
</ul>

<h2 class="saut">Arcs de tir et de détection d'un navire</h2>
<p>Chaque affût ou capteur couvre un secteur autour du navire. Bâbord est le côté gauche, tribord le côté droit.</p>
{arcs}

<h2>Barre du temps</h2>
{grille("Bar", BARRE, 90)}
<h2>Boutons d'une unité</h2>
{grille("Menu", BOUTONS, 64)}
<h2>Météo, jour et nuit, indicateurs</h2>
{grille(".", METEO, 48)}

{catalogue("NTDS")}
{catalogue("APP6")}
{catalogue("Directional")}
{catalogue("Stylized")}
</body></html>"""


if __name__ == "__main__":
    with open(SORTIE_HTML, "w", encoding="utf-8") as f:
        f.write(page())
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={SORTIE_PDF}",
                    "file://" + SORTIE_HTML], check=True, capture_output=True, timeout=600)
    print(SORTIE_PDF, round(os.path.getsize(SORTIE_PDF) / 1e6, 1), "Mo")
