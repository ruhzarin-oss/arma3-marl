"""L AGENT CODEUR ( 26/09, decision de Younes : « les decisions doivent etre du code » ) : un LLM expert en code
( Qwen3.8-27B, Ollama local ) ECRIT le gouvernement d un pays en Python - une fonction gouverner(bulletin, memoire) qui
rend une liste d actions du catalogue - ; le monde la fait tourner, la note, et l agent la reecrit a partir de ce qu il
a vu ( la boucle de Voyager et de FunSearch, avec un pays a la place de Minecraft ).

Garde-fous :
  - le code tourne dans un BAC A SABLE : pas d import, pas de fichier, pas d attribut dunder, des fonctions de base
    reduites, une seconde au plus par appel ; une erreur -> le jour est joue par les regles et compte comme un echec ;
  - chaque action rendue passe par `appliquer` ( les memes bornes que tout gouvernement, humain, LLM ou regles ) ;
  - une version n entre dans la bibliotheque que si elle bat le TEMOIN ( les regles ) sur le meme monde et que la
    conservation de l argent et des biens tient.

   python -m monde.agent_codeur --ile Malden --tours 12 --jours 30 --echelle 20"""
import argparse, ast, builtins, copy, hashlib, json, math, os, re, signal, sys, time, urllib.request
from multiprocessing import get_context
from . import config as C
from .archipel import Archipel
from .pays import d06_etat as ET

MODELE = "qwen3.8:27b"
# 32 768 jetons tiennent sur la RTX 3090 avec le modele ( 17 Go ) ; a 49 152 le modele ne tenait plus ( 26/09 ). La
# consigne ( ~9 000 caracteres ), l historique et la reflexion doivent y tenir ensemble : sinon, reponse vide
CONTEXTE = 32768
HISTORIQUE_K = 3
HOTE = "http://localhost:11434"
DOSSIER = "/mnt/data/hmt/agent_codeur"
SECONDES_PAR_APPEL = 1.0
ACTIONS_MAX = 8
PERMIS = ("abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "int", "isinstance", "len",
          "list", "map", "max", "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip")
BUILTINS = {n: getattr(builtins, n) for n in PERMIS}
REGLES = "regles"                 # le temoin : les regles du domaine 6
RIEN = "def gouverner(b, memoire):\n    return [{'type': 'rien'}]\n"


class CodeRefuse(ValueError):
    pass


class _Delai(Exception):
    pass


def verifier(source):
    """Refuse ce que le bac a sable ne laisse pas passer, avant toute execution."""
    arbre = ast.parse(source)
    for n in ast.walk(arbre):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith)):
            raise CodeRefuse(f"interdit : {type(n).__name__}")
        if isinstance(n, ast.Attribute) and n.attr.startswith("_"): raise CodeRefuse(f"attribut interdit : {n.attr}")
        if isinstance(n, ast.Name) and n.id.startswith("__"): raise CodeRefuse(f"nom interdit : {n.id}")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "gouverner" for n in arbre.body):
        raise CodeRefuse("il faut une fonction gouverner(b, memoire)")
    return arbre


class CerveauCode:
    """Un gouvernement ecrit en code, branche la ou le domaine 6 appelle son cerveau ( w.cerveau(bulletin, memoire) ).
    Picklable : seul le source part dans un instantane."""

    def __init__(self, source, nom="code"):
        verifier(source)
        self.source, self.nom = source, nom
        self.empreinte = hashlib.sha256(source.encode()).hexdigest()[:12]
        self.modele = f"code:{self.empreinte}"
        self.memoire = {}
        self.echecs = 0
        self._f = None

    def __getstate__(self):
        return {"source": self.source, "nom": self.nom, "memoire": self.memoire, "echecs": self.echecs}

    def __setstate__(self, d):
        self.__init__(d["source"], d["nom"]); self.memoire, self.echecs = d["memoire"], d["echecs"]

    def _compiler(self):
        ns = {"__builtins__": BUILTINS, "math": math}
        exec(compile(verifier(self.source), f"<gouvernement {self.empreinte}>", "exec"), ns)
        self._f = ns["gouverner"]

    def __call__(self, bulletin, _memoire_llm=""):
        if self._f is None: self._compiler()
        def delai(*_): raise _Delai(f"plus de {SECONDES_PAR_APPEL} s")
        ancien = signal.signal(signal.SIGALRM, delai)
        signal.setitimer(signal.ITIMER_REAL, SECONDES_PAR_APPEL)
        try:
            actions = self._f(copy.deepcopy(bulletin), self.memoire)
        except BaseException as ex:                # une erreur du code : le domaine 6 jouera les regles ce jour-la
            self.echecs += 1
            raise RuntimeError(f"code {self.empreinte} : {type(ex).__name__}: {ex}") from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, ancien)
        if isinstance(actions, dict): actions = [actions]
        if not isinstance(actions, list): raise RuntimeError(f"code {self.empreinte} : rend {type(actions).__name__}")
        json.dumps(self.memoire)                   # la memoire reste du JSON ( pas d objet du monde )
        return actions[:ACTIONS_MAX], f"code {self.empreinte}"


# ------------------------------------------------------------------ l evaluation
def evaluer(source, ile="Malden", echelle=20.0, jours=30, graine=C.GRAINE):
    """Le pays seul, `jours` jours, gouverne par `source` ( ou par les regles si REGLES ). Rend les mesures du jour
    le jour et le resume ; la faim est celle des menages habites."""
    arc = Archipel(iles=(ile,), echelle=echelle, ouvert=False, parallele=False, graine=graine)
    w = arc.iles[ile].w
    cerveau = None if source == REGLES else CerveauCode(source)
    w.cerveau = cerveau
    v0 = int(w.table.vivant[:w.table.n].sum())
    serie, refus, raisons, replis = [], 0, {}, 0
    n0 = len(w.evenements)
    for j in range(jours):
        arc.jours(1)
        e = arc.commande(ile, "etat")
        serie.append(round(e["faim"], 4))
    for ev in w.evenements[n0:]:
        if ev.get("type") != "decision_gouvernement": continue
        if str(ev.get("motifs", "")).startswith("cerveau indisponible"): replis += 1
        for a in ev.get("actions", []):
            if not a.get("acceptee"):
                refus += 1; r = str(a.get("raison"))[:60]; raisons[r] = raisons.get(r, 0) + 1
    s = ET.sitrep(w.pays)
    tenue, _ = w.pays.socle.conservation.tenue()
    m = {"jours_de_faim": round(sum(serie), 3), "faim_par_jour": serie, "morts_nets": v0 - int(w.table.vivant[:w.table.n].sum()),
         "dette": s["finances"].get("dette"), "caisse_etat": round(w.gouv.caisse), "refus": refus,
         "raisons_refus": dict(sorted(raisons.items(), key=lambda kv: -kv[1])[:6]), "jours_joues_par_les_regles": replis,
         "conservation": bool(tenue)}
    m["score"] = score(m)
    return m


GRAINES_ENTRAINEMENT = tuple(range(2001, 2051))     # jamais celles de l examen ( 1001-1050 ) ni C.GRAINE


def _evaluer_un(args):
    source, ile, echelle, jours, graine = args
    try: return evaluer(source, ile, echelle, jours, graine)
    except (CodeRefuse, SyntaxError) as ex: return {"erreur": f"{type(ex).__name__}: {ex}"}


def evaluer_plusieurs(source, mondes, echelle, jours, travailleurs=4):
    """La moyenne sur plusieurs mondes ( ile, graine ) : un code ne peut plus apprendre UN monde par coeur ( 26/09 ).
    Rend les mesures moyennes, la faim moyenne jour par jour, et le detail de chaque monde."""
    taches = [(source, i, echelle, jours, g) for i, g in mondes]
    with get_context("fork").Pool(min(travailleurs, len(taches))) as pool: res = pool.map(_evaluer_un, taches)
    err = [r["erreur"] for r in res if "erreur" in r]
    if err: raise CodeRefuse(err[0])
    moy = lambda k: round(sum(r[k] for r in res) / len(res), 3)
    m = {"jours_de_faim": moy("jours_de_faim"), "morts_nets": moy("morts_nets"), "dette": moy("dette"),
         "caisse_etat": moy("caisse_etat"), "refus": sum(r["refus"] for r in res), "jours_joues_par_les_regles":
         sum(r["jours_joues_par_les_regles"] for r in res), "conservation": all(r["conservation"] for r in res),
         "faim_par_jour": [round(sum(r["faim_par_jour"][j] for r in res) / len(res), 4) for j in range(jours)],
         "raisons_refus": {k: v for r in res for k, v in r["raisons_refus"].items()},
         "par_monde": {f"{i}/{g}": r["jours_de_faim"] for (i, g), r in zip(mondes, res)}}
    m["score"] = score(m)
    return m


def score(m):
    """Plus haut = mieux. La faim d abord ( un jour ou tous les menages habites ont faim vaut 100 points ), puis les
    morts, puis les jours ou le code a plante ( joues par les regles ), puis les actions refusees."""
    return round(-100.0 * m["jours_de_faim"] - 1.0 * max(0, m["morts_nets"]) - 5.0 * m["jours_joues_par_les_regles"]
                 - 0.5 * m["refus"], 2)


# ------------------------------------------------------------------ l agent
def consigne(ile, bulletin_exemple):
    return f"""Tu gouvernes le pays insulaire {ile} ( monnaie : le {C.MONNAIES[ile]} ) en ECRIVANT DU CODE PYTHON.
Chaque matin a 6 h, le moteur appelle ta fonction :

    def gouverner(b, memoire):
        ...
        return [ action, ... ]        # au plus {ACTIONS_MAX} actions du catalogue

- `b` est le bulletin du matin ( un dict, voir l exemple plus bas ) : de la statistique publique, avec ses retards.
- `memoire` est un dict que tu peux lire et ecrire : il est garde d un jour a l autre ( JSON seulement ).
- Pas d import ( `math` est deja la ), pas de fichier, pas de `__`, une seconde au plus. Si ton code plante, les regles
  jouent ce jour-la et ton score est penalise.
- Toute action hors du catalogue ou hors de ses bornes est refusee ( et penalisee ).

Ton but : que chaque habitant mange ( la faim d abord ), soit soigne, et que les finances publiques tiennent.
Le score d une version = -100 x jours de faim ( somme de la part des menages habites qui n ont pas mange ) - morts
- 5 x jours ou ton code a plante - 0,5 x actions refusees. Le temoin a battre : les regles actuelles du pays.
Leviers utiles contre la faim : acheter de la nourriture pour la reserve "population" ( distribuee aux menages qui
n ont plus rien ), subventionner les menages pauvres, importer, et PREVOIR : les marches ferment le dimanche et les
jours feries, et les livraisons s arretent le week-end.

{ET.CATALOGUE_ETAT}

Exemple de bulletin ( JSON ) :
{json.dumps(bulletin_exemple, ensure_ascii=False)[:6000]}

Reponds par UN SEUL bloc ```python contenant la fonction gouverner ( et ses aides si tu veux ), rien d autre."""


def demander(prompt, penser=True, jetons=16000):
    """Une reponse de l agent. S il a reflechi jusqu a epuiser sa sortie sans ecrire de code ( 26/09 : versions 5 et 6,
    40 000 caracteres de reflexion et rien d autre ), on lui redemande le code, sans reflexion cette fois."""
    def appel(texte, pense, n):
        corps = {"model": MODELE, "stream": False, "think": pense, "prompt": texte,
                 "options": {"temperature": 0.4, "num_predict": n, "num_ctx": CONTEXTE}}
        req = urllib.request.Request(HOTE + "/api/generate", data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=3600).read())
    r = appel(prompt, penser, jetons)
    texte, pensee = r.get("response", ""), r.get("thinking", "")
    if "def gouverner" not in texte:
        r = appel(prompt + "\n\nEcris MAINTENANT le code, sans rien expliquer : un seul bloc ```python.", False, 8000)
        texte = r.get("response", "")
    return texte, pensee


def extraire_code(texte):
    m = re.findall(r"```(?:python)?\n(.*?)```", texte, re.S)
    return (max(m, key=len) if m else texte).strip() + "\n"


def historique(versions, k=HISTORIQUE_K):
    """Ce que l agent a deja essaye : les k meilleures versions et la derniere, avec leurs mesures."""
    choix = sorted(versions, key=lambda v: -v["mesures"]["score"])[:k]
    if versions and versions[-1] not in choix: choix.append(versions[-1])
    out = []
    for v in choix:
        m = v["mesures"]
        out.append(f"### version {v['n']} - score {m['score']} ( jours de faim {m['jours_de_faim']}, morts {m['morts_nets']}, "
                   f"plantages {m['jours_joues_par_les_regles']}, refus {m['refus']} {m['raisons_refus']}, dette {m['dette']} )\n"
                   f"faim par jour ( moyenne des mondes ) : {m['faim_par_jour']}\n"
                   + (f"jours de faim par monde : {m['par_monde']}\n" if m.get("par_monde") else "")
                   + f"```python\n{v['source']}```")
    return "\n\n".join(out)


def boucle(ile, tours, jours, echelle, graine, mondes=None, travailleurs=4, dossier=None, depart=None):
    """`mondes` : la liste des ( ile, graine ) sur lesquels chaque version est notee ( la moyenne ) ; sans, le seul
    monde ( ile, graine ) du premier essai."""
    mondes = mondes or [(ile, graine)]
    evalue = lambda s: evaluer_plusieurs(s, mondes, echelle, jours, travailleurs)
    d = dossier or os.path.join(DOSSIER, ile); os.makedirs(d, exist_ok=True)
    journal = open(os.path.join(d, "journal.jsonl"), "a")
    def noter(x): journal.write(json.dumps(x, ensure_ascii=False) + "\n"); journal.flush()
    t0 = time.time()
    temoin = evalue(REGLES)
    rien = evalue(RIEN)
    print(f"temoin ( regles ) : score {temoin['score']} faim {temoin['jours_de_faim']} | rien : score {rien['score']} "
          f"faim {rien['jours_de_faim']} ( {time.time() - t0:.0f} s )", flush=True)
    noter({"temoin": temoin, "rien": rien})
    arc = Archipel(iles=(ile,), echelle=echelle, ouvert=False, parallele=False, graine=graine)
    arc.jours(1)
    exemple = ET.sitrep(arc.iles[ile].w.pays)
    base = consigne(ile, exemple)
    versions = []
    # reprise : les versions deja ecrites et notees ( sur le meme monde ) restent dans l historique de l agent
    for l in open(os.path.join(d, "journal.jsonl")):
        x = json.loads(l)
        if "n" in x and "erreur" not in x["mesures"] and x["mesures"].get("jours_de_faim") is not None: versions.append(x)
    if depart and not versions:                # un point de depart deja examine ( version 0 )
        src = open(depart).read(); v0 = {"n": 0, "source": src, "mesures": evalue(src), "secondes": 0, "pensee": 0, "depart": depart}
        versions.append(v0); noter(v0)
        print(f"depart ( {depart} ) : score {v0['mesures']['score']} faim {v0['mesures']['jours_de_faim']}", flush=True)
    debut = max([v["n"] for v in versions], default=0) + 1
    if versions: print(f"reprise : {len(versions)} versions notees, meilleure {max(v['mesures']['score'] for v in versions)}", flush=True)
    for n in range(debut, debut + tours):
        t1 = time.time()
        prompt = base
        if versions:
            prompt += ("\n\nTes versions precedentes et ce qu elles ont donne ( ameliore la meilleure ; le temoin fait "
                       f"score {temoin['score']}, jours de faim {temoin['jours_de_faim']}, faim par jour {temoin['faim_par_jour']} ) :\n\n"
                       + historique(versions))
        texte, pensee = demander(prompt)
        source = extraire_code(texte)
        try:
            mes = evalue(source)
        except (CodeRefuse, SyntaxError) as ex:
            mes = {"score": -1e9, "jours_de_faim": None, "faim_par_jour": [], "morts_nets": 0, "dette": None, "caisse_etat": None,
                   "refus": 0, "raisons_refus": {}, "jours_joues_par_les_regles": jours, "conservation": None,
                   "erreur": f"{type(ex).__name__}: {ex}"}
        v = {"n": n, "source": source, "mesures": mes, "secondes": round(time.time() - t1), "pensee": len(pensee)}
        versions.append(v); noter(v)
        with open(os.path.join(d, f"v{n:03d}.py"), "w") as f: f.write(source)
        bat = mes.get("conservation") and mes["score"] > temoin["score"]
        print(f"version {n} : score {mes['score']} faim {mes['jours_de_faim']} plantages {mes['jours_joues_par_les_regles']} "
              f"refus {mes['refus']} {'BAT LE TEMOIN' if bat else ''} {mes.get('erreur', '')[:120]} ( {v['secondes']} s )", flush=True)
    meilleure = max(versions, key=lambda v: v["mesures"]["score"])
    with open(os.path.join(d, "meilleur.py"), "w") as f: f.write(meilleure["source"])
    with open(os.path.join(d, "meilleur.json"), "w") as f:
        json.dump({"version": meilleure["n"], "mesures": meilleure["mesures"], "temoin": temoin["score"], "rien": rien["score"],
                   "mondes": mondes}, f, ensure_ascii=False)
    print(f"\nmeilleure : version {meilleure['n']}, score {meilleure['mesures']['score']} ( temoin {temoin['score']}, rien {rien['score']} )")
    return meilleure, temoin, rien


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--ile", default="Malden"); a.add_argument("--tours", type=int, default=12)
    a.add_argument("--jours", type=int, default=30); a.add_argument("--echelle", type=float, default=20.0)
    a.add_argument("--graine", type=int, default=C.GRAINE)
    a.add_argument("--mondes", type=int, default=0, help="nombre de graines d entrainement ( 0 : le seul monde --graine )")
    a.add_argument("--travailleurs", type=int, default=4)
    a.add_argument("--dossier", default=None)
    a.add_argument("--depart", default=None, help="un code deja examine, note comme version 0")
    x = a.parse_args()
    mondes = [(x.ile, g) for g in GRAINES_ENTRAINEMENT[:x.mondes]] if x.mondes else None
    boucle(x.ile, x.tours, x.jours, x.echelle, x.graine, mondes, x.travailleurs, x.dossier, x.depart)
    return 0


if __name__ == "__main__":
    sys.exit(main())
