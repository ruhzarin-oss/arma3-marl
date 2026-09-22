"""Le gouvernement : un chef et six ministres, une caisse, des impots, des salaires publics, des lois. Il decide chaque
matin du monde, par un CATALOGUE d actions typees et bornees - jamais par du code libre. Deux cerveaux possibles :
les regles ( deterministe, pour les tests ) et le LLM ( Qwen, par Ollama, en local ). Chaque decision est journalisee
avec ses entrees, sa consigne ( empreinte ) et sa sortie."""
import hashlib, json, urllib.request
from . import config as C

LOIS_DEFAUT = {"couvre_feu": None, "rationnement_nourriture": None, "quarantaine": [], "ecole_obligatoire": True,
               "prix_plafond": {}}
BORNES = {"impot_revenu": (0.0, 0.40), "tva": (0.0, 0.25), "facteur_salaire_public": (0.5, 2.0)}


class Gouvernement:
    def __init__(self):
        self.caisse = 200000.0
        self.impot_revenu = 0.15
        self.tva = 0.08
        self.facteur_salaire_public = 1.0
        self.lois = json.loads(json.dumps(LOIS_DEFAUT))
        self.commandes = []            # achats en cours ( bien, quantite, destination )
        self.decisions = []            # journal des decisions
        self.membres = []              # habitants : chef et ministres

    def appliquer(self, action, monde):
        """Applique UNE action du catalogue. Rend ( acceptee, raison ). Toute action hors catalogue ou hors bornes est
        refusee et journalisee : le gouvernement ne peut pas casser le monde."""
        t = action.get("type")
        try:
            if t == "fixer_impot":
                n, v = action["nom"], float(action["valeur"])
                if n not in ("impot_revenu", "tva"): return False, f"impot inconnu {n}"
                lo, hi = BORNES[n]
                if not lo <= v <= hi: return False, f"{n}={v} hors [{lo} ; {hi}]"
                setattr(self, n, v); return True, ""
            if t == "fixer_salaires_publics":
                v = float(action["facteur"]); lo, hi = BORNES["facteur_salaire_public"]
                if not lo <= v <= hi: return False, f"facteur {v} hors [{lo} ; {hi}]"
                self.facteur_salaire_public = v; return True, ""
            if t == "acheter":
                b, q = action["bien"], float(action["quantite"])
                if b not in C.BIENS or q <= 0 or q > 2000: return False, f"achat invalide {b} {q}"
                dest = action.get("destination", "hopitaux" if b == "remedes" else "armee" if b == "carburant" else "reserve")
                if dest not in ("hopitaux", "armee", "reserve", "population"): return False, f"destination inconnue {dest}"
                cout = q * monde.prix_moyen(b) * 1.1
                if cout > self.caisse: return False, f"caisse insuffisante ( {cout:.0f} > {self.caisse:.0f} )"
                self.commandes.append({"bien": b, "quantite": q, "destination": dest}); return True, ""
            if t == "importer":
                b, q = action["bien"], float(action["quantite"])
                if b not in C.BIENS or b == "or" or q <= 0 or q > 2000: return False, f"import invalide {b} {q}"
                cout = q * C.PRIX_MONDE[b] * 1.2
                if cout > self.caisse: return False, "caisse insuffisante"
                monde.importer(b, q, cout); return True, ""
            if t == "exporter_or":
                q = float(action["quantite"])
                return monde.exporter_or(q)
            if t == "couvre_feu":
                d, f = action.get("debut"), action.get("fin")
                if d is None: self.lois["couvre_feu"] = None; return True, ""
                if not (0 <= int(d) < 24 and 0 <= int(f) < 24): return False, "heures invalides"
                self.lois["couvre_feu"] = [int(d), int(f)]; return True, ""
            if t == "quarantaine":
                lieu = action["lieu"]
                if lieu not in monde.carte.lieux: return False, f"lieu inconnu {lieu}"
                if action.get("levee"): self.lois["quarantaine"] = [x for x in self.lois["quarantaine"] if x != lieu]
                elif lieu not in self.lois["quarantaine"]: self.lois["quarantaine"].append(lieu)
                return True, ""
            if t == "rationnement":
                v = action.get("par_jour")
                self.lois["rationnement_nourriture"] = None if v is None else max(0.5, min(3.0, float(v))); return True, ""
            if t == "subvention":
                qui, montant = action["cible"], float(action["montant"])
                if montant <= 0 or montant > self.caisse * 0.2: return False, "montant invalide"
                return monde.subventionner(qui, montant)
            if t == "rien":
                return True, ""
        except (KeyError, TypeError, ValueError) as e:
            return False, f"action mal formee : {e}"
        return False, f"action hors catalogue : {t}"


CATALOGUE = """Actions permises ( JSON, une liste ) :
- {"type": "fixer_impot", "nom": "impot_revenu" | "tva", "valeur": nombre}            ( impot_revenu 0-0,40 ; tva 0-0,25 )
- {"type": "fixer_salaires_publics", "facteur": nombre}                               ( 0,5-2,0 )
- {"type": "acheter", "bien": bien, "quantite": nombre, "destination": "hopitaux" | "armee" | "reserve" | "population"}
- {"type": "importer", "bien": bien, "quantite": nombre}                              ( au prix mondial + 20 %, par le port de Kavala )
- {"type": "exporter_or", "quantite": nombre}                                         ( vend l or des reserves au prix mondial )
- {"type": "couvre_feu", "debut": heure, "fin": heure}  ou  {"type": "couvre_feu", "debut": null}
- {"type": "quarantaine", "lieu": lieu, "levee": false}
- {"type": "rationnement", "par_jour": nombre | null}
- {"type": "subvention", "cible": "menages_pauvres" | "fermes" | "hopitaux", "montant": nombre}
- {"type": "rien"}"""


def decider_regles(sitrep):
    """Le gouvernement par regles : prudent, previsible. Sert aux tests et de repere pour juger le LLM."""
    a = []
    if sitrep["sante"]["infectes"] > 25 and sitrep["stocks_publics"]["remedes"] < 60:
        a.append({"type": "acheter", "bien": "remedes", "quantite": 60, "destination": "hopitaux"})
    if sitrep["armee"]["carburant_depot"] < 80:
        a.append({"type": "acheter", "bien": "carburant", "quantite": 120, "destination": "armee"})
    if sitrep["finances"]["caisse"] < 150000 and sitrep["stocks_publics"]["or"] > 2:
        a.append({"type": "exporter_or", "quantite": sitrep["stocks_publics"]["or"]})
    if sitrep["population"]["menages_sans_nourriture"] > 20:
        a.append({"type": "subvention", "cible": "menages_pauvres", "montant": 3000})
    f = sitrep["finances"]
    if f["caisse"] < 150000:                  # un budget en deficit : on releve les impots, par pas
        a.append({"type": "fixer_impot", "nom": "tva", "valeur": round(min(0.25, f["tva"] + 0.02), 2)})
        a.append({"type": "fixer_impot", "nom": "impot_revenu", "valeur": round(min(0.40, f["impot_revenu"] + 0.02), 2)})
    elif f["caisse"] > 300000:
        a.append({"type": "fixer_impot", "nom": "tva", "valeur": round(max(0.0, f["tva"] - 0.01), 2)})
    return a or [{"type": "rien"}]


class CerveauLLM:
    """Le gouvernement joue par Qwen ( Ollama local ). Sortie JSON imposee ; toute action est reverifiee par
    Gouvernement.appliquer. La consigne est figee et son empreinte journalisee ( rejouabilite )."""
    def __init__(self, modele="qwen2.5:14b", hote="http://localhost:11434"):
        self.modele, self.hote = modele, hote
        self.consigne = ("Tu es le gouvernement d Altis : un chef et six ministres ( finances, sante, interieur, defense, "
                         "education, industrie ). Ton pays est en paix. Ton but : que chaque habitant mange, soit soigne, "
                         "travaille et vive en securite, et que les finances publiques tiennent. Tu lis le bulletin du "
                         "matin et tu decides. Reponds UNIQUEMENT par un objet JSON {\"motifs\": \"...\", \"actions\": [...]}.\n"
                         + CATALOGUE)
        self.empreinte = hashlib.sha256(self.consigne.encode()).hexdigest()[:12]

    def __call__(self, sitrep, memoire=""):
        corps = {"model": self.modele, "format": "json", "stream": False, "options": {"temperature": 0.2, "seed": 7},
                 "prompt": self.consigne + ("\n\nCe que tu as appris des jours passes :\n" + memoire if memoire else "")
                           + "\n\nBulletin du matin :\n" + json.dumps(sitrep, ensure_ascii=False)}
        req = urllib.request.Request(self.hote + "/api/generate", data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json"})
        brut = json.loads(urllib.request.urlopen(req, timeout=300).read())["response"]
        try: d = json.loads(brut)
        except json.JSONDecodeError: return [{"type": "rien"}], "sortie illisible : " + brut[:200]
        return d.get("actions", [{"type": "rien"}]), d.get("motifs", "")
