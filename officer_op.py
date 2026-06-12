"""officer_op — OFFICIER OPERATIF (chef d'operation), Jalon 1 du commandement Arma.
Lit un RAPPORT DE CONTACT -> estime la posture defensive ennemie -> CHOISIT une manoeuvre du repertoire
M1-M12 -> ALLOUE les escouades -> JUSTIFIE en clair (pour l'observateur). Doctrine FR/OTAN.
Cerveau = qwen2.5:14b via ollama. Savoir doctrinal ancre sur la MATRICE MESUREE (instrument v2 propre)."""
import json, urllib.request

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"

# repertoire doctrinal (resume pour le prompt)
MANEUVERS = {
    "M1": "appui-feu + assaut frontal",
    "M2": "double enveloppement (deux flancs)",
    "M3": "enveloppement simple (fixer + flanc lourd)",
    "M5": "feinte + debordement (demonstration + effort principal)",
    "M8": "percee (toute la force sur un axe etroit + exploitation)",
    "M9": "mouvement tournant (marche profonde, prise de l'arriere)",
    "M10": "marteau-enclume (bloc au nord + assaut au sud)",
    "M11": "raid (coup de main rapide + exfil avant la contre-attaque)",
    "M12": "reconnaissance en force (sonde, puis bascule selon la reception)",
}

# savoir doctrinal MESURE (matrice propre v2) : signature observable -> meilleure manoeuvre (taux succes %)
DOCTRINE = [
    ("garnison statique avec ecran de patrouilles, pas de manoeuvre", "M3", 81),
    ("les patrouilles se MASSENT sur le flanc que l'on menace (defense anti-flanc reactive)", "M3", 62),
    ("un bloc central avance bouche l'axe frontal (defense anti-centre/profondeur)", "M3", 69),
    ("reserve mobile qui contre-attaque nos concentrations", "M3", 62),
    ("defense ELASTIQUE : l'ennemi recule par bonds sur des lignes successives sous la pression", "M1", 50),
    ("HERISSON : tout l'ennemi masse en perimetre dense DANS l'objectif, aucun ecran dehors", "M8", 62),
    ("APPAT : l'ennemi ABANDONNE l'objectif puis contre-attaque quand on l'occupe", "M12", 81),
    ("SORTIE : l'ennemi attaque nos zones de rassemblement des le premier contact", "M12", 69),
]

SYSTEM = (
    "Tu es un OFFICIER OPERATIF (chef d'operation) d'une armee de terre, doctrine OTAN/francaise. "
    "Tu commandes 4 escouades : APPUI, ASSAUT-OUEST, ASSAUT-EST, RESERVE, pour prendre un objectif defendu.\n\n"
    "REPERTOIRE DE MANOEUVRES :\n" + "\n".join("%s = %s" % (k, v) for k, v in MANEUVERS.items()) + "\n\n"
    "CONNAISSANCE DOCTRINALE MESUREE (meilleure manoeuvre selon la posture defensive observee, taux de succes) :\n"
    + "\n".join("- si %s -> %s (%d%%)" % (sig, m, s) for sig, m, s in DOCTRINE) + "\n\n"
    "On te donne un RAPPORT DE CONTACT du terrain. Comme un vrai PC tactique, tu dois :\n"
    "1) ESTIMER la posture defensive ennemie d'apres les indices observables,\n"
    "2) CHOISIR UNE SEULE manoeuvre du repertoire (le code M..),\n"
    "3) ALLOUER les escouades (qui fait quoi),\n"
    "4) JUSTIFIER en clair, 2-3 phrases, comme un ordre transmis a tes escouades.\n\n"
    "Reponds UNIQUEMENT en JSON : "
    '{"posture": "...", "manoeuvre": "M..", "allocation": "...", "justification": "..."}'
)


def decide(report, model=MODEL, timeout=120):
    """Appelle l'officier (qwen) sur un rapport de contact. Renvoie le dict de decision."""
    body = json.dumps({
        "model": model, "stream": False, "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "RAPPORT DE CONTACT :\n" + report},
        ],
        "options": {"temperature": 0.2},
    }).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return json.loads(r["message"]["content"])


# ----- sérialiseur de rapport de contact (version live : depuis l'état op_arma ; ici un helper générique) -----
def build_report(contacts_par_secteur, pertes_par_escouade, objectif_tenu, note=""):
    """Construit un rapport de contact texte a partir d'observations structurees (utilise en live depuis op_arma)."""
    lignes = ["Objectif : %s." % ("TENU par l'ennemi" if objectif_tenu else "ennemi absent/replie")]
    if contacts_par_secteur:
        lignes.append("Contacts ennemis : " + ", ".join("%s sur %s" % (n, sec) for sec, n in contacts_par_secteur.items()) + ".")
    if pertes_par_escouade:
        lignes.append("Pertes amies : " + ", ".join("%s %s" % (sq, p) for sq, p in pertes_par_escouade.items()) + ".")
    if note:
        lignes.append(note)
    return " ".join(lignes)


if __name__ == "__main__":
    import sys
    print(decide(sys.stdin.read()))
