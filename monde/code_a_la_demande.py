"""LE CODE A LA DEMANDE ( 27/09, etape 1 de plans/plan-code-a-la-demande.md ; Younes : « Qwen doit repondre a toutes
les demandes du moteur pour coder n importe quelle situation a la demande » ).

Un point de decision du socle DEMANDE une fonction au service : son contrat dit ce que l agent voit ( les traits et
leur source ), ce qu il peut faire ( les actions ), ce que fait la regle d aujourd hui ( son code ) et ce que mesure la
note. Qwen ( qwen3.8:27b, local, toujours charge ) ecrit `decider(t)`. Le service la verifie ( bac a sable : pas
d import, pas d attribut prive, 50 ms au plus par appel ; sur 200 entrees tirees, elle rend toujours une action du
catalogue ) et la range dans la BIBLIOTHEQUE, en epreuve. Le monde ne l adopte jamais sur parole : elle decide pour
PART_EPREUVE des cles ( les autres gardent la regle ), chaque note murie est rendue a son bras, et apres JOURS_EPREUVE
jours le verdict compare le candidat a la regle, jour par jour, par permutation. Adoptee : elle decide pour tous ( la
regle reste le repli d une erreur ). Retiree : la raison chiffree retourne a Qwen, qui ecrit la version suivante.
Le monde n attend JAMAIS Qwen : sans version en epreuve, la regle decide ; une erreur du code est un repli sur la regle,
compte contre le candidat.

La bibliotheque ( sur disque, versionnee ) : <BIBLIOTHEQUE>/<point>/v001/ code.py, demande.json, essai.json, etat.json
( en_epreuve | adopte | retire | refuse, et le verdict ). La file : <FILE>/<point>-<horodatage>.json ; traitees dans
<FILE>/fait/. Le journal du pays note chaque branchement ( point, version ) et chaque verdict : une nuit se relit.

   python -m monde.code_a_la_demande --demander importer      ( pose une demande )
   python -m monde.code_a_la_demande --veille                  ( le service : traite la file, sans fin )"""
import argparse, ast, builtins, glob, hashlib, importlib, inspect, json, math, os, pkgutil, re, signal, sys, time
import urllib.request
import numpy as np

BIBLIOTHEQUE = os.environ.get("HMT_BIBLIOTHEQUE_CODE", "/mnt/data/hmt/qwen/bibliotheque")
FILE = os.environ.get("HMT_FILE_CODE", "/mnt/data/hmt/qwen/file")
MODELE = "qwen3.8:27b"
HOTE = os.environ.get("HMT_OLLAMA", "http://localhost:11434")
CONTEXTE = 32768
PART_EPREUVE = 0.10          # la part des cles que le candidat decide pendant l epreuve ( plan : 10 % des agents )
JOURS_EPREUVE = 20           # jours du monde avant le verdict
NOTES_MIN = 40               # notes murees au moins, par bras, pour un verdict ; sinon l epreuve continue
P_VERDICT = 0.05             # adopte si meilleur avec p < 0,05 ; retire si pire avec p < 0,05 ou jamais meilleur
ECHECS_MAX = 0.01            # plus de 1 % de replis ( erreurs du code ) : retire
SECONDES_PAR_APPEL = 0.05
ESSAIS_HORS_LIGNE = 200
TENTATIVES = 3               # un code refuse au service est redemande avec l erreur, 3 fois au plus
PERMIS = ("abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "int", "isinstance", "len",
          "list", "map", "max", "min", "pow", "range", "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip")
BUILTINS = {n: getattr(builtins, n) for n in PERMIS}
DOMAINE_JOURNAL = "code"


class CodeRefuse(ValueError):
    pass


class _Delai(Exception):
    pass


# ================================================================== le bac a sable
def verifier(source):
    """Refuse ce que le bac a sable ne laisse pas passer, avant toute execution ; exige `decider(t)`."""
    arbre = ast.parse(source)
    for n in ast.walk(arbre):
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith, ast.Lambda,
                          ast.Yield, ast.YieldFrom, ast.Await)):
            raise CodeRefuse(f"interdit : {type(n).__name__}")
        if isinstance(n, ast.Attribute) and n.attr.startswith("_"): raise CodeRefuse(f"attribut interdit : {n.attr}")
        if isinstance(n, ast.Name) and n.id.startswith("__"): raise CodeRefuse(f"nom interdit : {n.id}")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "decider" and len(n.args.args) == 1 for n in arbre.body):
        raise CodeRefuse("il faut une fonction decider(t)")
    return arbre


def compiler(source, nom="candidat"):
    ns = {"__builtins__": BUILTINS, "math": math}
    exec(compile(verifier(source), f"<{nom}>", "exec"), ns)
    return ns["decider"]


def appeler(f, t, actions):
    """Un appel dans le bac a sable : rend l indice de l action, ou leve ( delai, erreur, action hors catalogue )."""
    def delai(*_): raise _Delai(f"plus de {SECONDES_PAR_APPEL} s")
    ancien = signal.signal(signal.SIGALRM, delai)
    signal.setitimer(signal.ITIMER_REAL, SECONDES_PAR_APPEL)
    try: r = f(dict(t))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, ancien)
    if isinstance(r, str) and r in actions: return actions.index(r)
    if isinstance(r, (int, np.integer)) and not isinstance(r, bool) and 0 <= r < len(actions): return int(r)
    raise CodeRefuse(f"rend {r!r}, pas une action de {list(actions)}")


# ================================================================== le bras de code dans le monde
class BrasCode:
    """Un candidat en epreuve sur un point de decision ( Decideur.bras ). Picklable : le source part dans l instantane,
    la fonction se recompile a la reprise. `prend(cle)` : son etiquette ( la version ) pour PART des cles, tirees par
    une empreinte de la cle ( aucun tirage du hasard du monde ), « regle » pour les autres."""

    def __init__(self, source, version, point, part=PART_EPREUVE, debut_j=0, graine=0):
        compiler(source)
        self.source, self.version, self.point_nom, self.part = source, version, point, float(part)
        self.debut_j, self.graine = int(debut_j), int(graine)
        self.stats = {}             # ( jour, bras ) -> [ n, somme, somme des carres ] ; bras : "candidat" | "regle"
        self.echantillon = []       # ( jour, bras, note )
        self.n = {"candidat": 0, "regle": 0, "repli": 0}
        self.dernier_echec = False
        self.derniere_erreur = None
        self._f = None

    def __getstate__(self):
        d = dict(self.__dict__); d["_f"] = None; return d

    def __setstate__(self, d):
        self.__dict__.update(d); self._f = None

    def prend(self, cle):
        if self.part >= 1.0: e = self.version
        else:
            h = int.from_bytes(hashlib.blake2b(f"{self.graine}:{self.point_nom}:{cle}".encode(), digest_size=4).digest(), "big")
            e = self.version if h < self.part * 2 ** 32 else "regle"
        self.n["regle" if e == "regle" else "candidat"] += 1
        return e

    def decider(self, x, point):
        self.dernier_echec = False
        if self._f is None: self._f = compiler(self.source, f"{self.point_nom} {self.version}")
        t = {nom: float(v) for (nom, _), v in zip(point.traits, x)}
        try: return appeler(self._f, t, point.actions)
        except BaseException as ex:            # une erreur du code : la regle decide, et le repli compte contre lui
            self.dernier_echec = True; self.n["repli"] += 1
            self.derniere_erreur = f"{type(ex).__name__}: {str(ex)[:160]}"
            return None

    def noter(self, jour, etiquette, note):
        b = "regle" if etiquette == "regle" else "candidat"         # un repli compte pour le candidat ( intention )
        s = self.stats.get((jour, b))
        if s is None: self.stats[(jour, b)] = [1, note, note * note]
        else: s[0] += 1; s[1] += note; s[2] += note * note
        self.echantillon.append((jour, b, note))

    def verdict(self, n_perm=400, graine=0):
        """Candidat contre regle : l ecart des notes moyennes, et sa probabilite sous le hasard ( les etiquettes
        permutees A L INTERIEUR de chaque jour ). Rend { notes, moyennes, ecart, p_meilleur, p_pire, replis, decision }."""
        c = np.array([(j, 1 if b == "candidat" else 0, v) for j, b, v in self.echantillon], dtype=float).reshape(-1, 3)
        nc, nr = int((c[:, 1] == 1).sum()), int((c[:, 1] == 0).sum())
        r = {"notes_candidat": nc, "notes_regle": nr, "replis": self.n["repli"], "decisions_candidat": self.n["candidat"],
             "part_replis": self.n["repli"] / max(1, self.n["candidat"])}
        if nc < NOTES_MIN or nr < NOTES_MIN:
            r["decision"] = "en_epreuve"; return r
        def ecart(lab):
            return c[lab == 1, 2].mean() - c[lab == 0, 2].mean()
        lab = c[:, 1].copy(); obs = ecart(lab)
        ordre = np.argsort(c[:, 0], kind="stable"); jours = c[ordre, 0]
        coupes = np.flatnonzero(np.diff(jours)) + 1
        blocs = list(zip(np.concatenate(([0], coupes)), np.concatenate((coupes, [len(jours)]))))
        rng = np.random.default_rng(graine); plus = moins = 0
        for _ in range(n_perm):
            b = lab[ordre].copy()
            for x, y in blocs:
                if y - x > 1: b[x:y] = b[x:y][rng.permutation(y - x)]
            e = c[ordre][b == 1, 2].mean() - c[ordre][b == 0, 2].mean()
            plus += e >= obs - 1e-15; moins += e <= obs + 1e-15
        r.update({"moyenne_candidat": float(c[lab == 1, 2].mean()), "moyenne_regle": float(c[lab == 0, 2].mean()),
                  "ecart": float(obs), "p_meilleur": (1 + plus) / (n_perm + 1), "p_pire": (1 + moins) / (n_perm + 1)})
        if r["part_replis"] > ECHECS_MAX: r["decision"] = "retire"; r["raison"] = f"{r['replis']} replis ( erreurs du code )"
        elif obs > 0 and r["p_meilleur"] < P_VERDICT: r["decision"] = "adopte"
        else:
            r["decision"] = "retire"
            r["raison"] = ("pire que la regle" if obs < 0 and r["p_pire"] < P_VERDICT else "pas meilleur que la regle")
        return r


# ================================================================== la bibliotheque
def _dossier_point(point, biblio=None):
    return os.path.join(biblio or BIBLIOTHEQUE, point)


def versions(point, biblio=None):
    """[ ( version, etat ) ] dans l ordre."""
    d = _dossier_point(point, biblio)
    out = []
    for v in sorted(glob.glob(os.path.join(d, "v[0-9][0-9][0-9]"))):
        try: out.append((os.path.basename(v), json.load(open(os.path.join(v, "etat.json")))))
        except (OSError, ValueError): pass
    return out


def en_service(point, biblio=None):
    """La version qui decide aujourd hui : ( version, source, etat ) - l adoptee la plus recente passe avant une epreuve
    ( elle decide pour tous ) ; sinon la version en epreuve ; sinon None."""
    vs = versions(point, biblio)
    for etat in ("adopte", "en_epreuve"):
        for v, e in reversed(vs):
            if e.get("etat") == etat:
                return v, open(os.path.join(_dossier_point(point, biblio), v, "code.py")).read(), e
    return None


def publier(point, source, demande, essai, etat="en_epreuve", biblio=None):
    d = _dossier_point(point, biblio); os.makedirs(d, exist_ok=True)
    n = 1 + max([int(v[1:]) for v, _ in versions(point, biblio)] or [0])
    v = f"v{n:03d}"; dv = os.path.join(d, v); os.makedirs(dv)
    open(os.path.join(dv, "code.py"), "w").write(source)
    json.dump(demande, open(os.path.join(dv, "demande.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(essai, open(os.path.join(dv, "essai.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"etat": etat, "depuis": time.strftime("%Y-%m-%d %H:%M")}, open(os.path.join(dv, "etat.json"), "w"), ensure_ascii=False)
    return v


def poser_etat(point, version, etat, verdict=None, biblio=None):
    f = os.path.join(_dossier_point(point, biblio), version, "etat.json")
    e = json.load(open(f)); e.update({"etat": etat, "depuis": time.strftime("%Y-%m-%d %H:%M")})
    if verdict is not None: e["verdict"] = verdict
    json.dump(e, open(f, "w"), ensure_ascii=False, indent=1)


# ================================================================== les points de decision et leurs contrats
def trouver_point(nom):
    """Le PointDeDecision declare sous ce nom, dans les modules du pays."""
    from .socle import decision as D
    from . import pays as PK
    for m in pkgutil.iter_modules(PK.__path__):
        if not m.name.startswith("d"): continue
        mod = importlib.import_module(f"monde.pays.{m.name}")
        for v in vars(mod).values():
            if isinstance(v, D.PointDeDecision) and v.nom == nom: return v
    raise KeyError(f"point de decision inconnu : {nom!r}")


def contrat(point):
    try: regle = inspect.getsource(point.regle)
    except (OSError, TypeError): regle = "( source indisponible )"
    return {"cle": f"decision/{point.nom}", "point": point.nom, "domaine": point.domaine,
            "traits": [list(t) for t in point.traits], "actions": list(point.actions), "note": point.note,
            "horizon_j": point.horizon_j, "regle": regle}


def demander(point_nom, raison="premiere version", retour=None, exemples=None, file=None):
    """Pose une demande dans la file du service ( ne bloque jamais : un fichier ). Rend son chemin."""
    d = file or FILE; os.makedirs(d, exist_ok=True)
    c = contrat(trouver_point(point_nom))
    c.update({"raison": raison, "retour": retour, "exemples": exemples or [], "posee": time.strftime("%Y-%m-%d %H:%M:%S")})
    f = os.path.join(d, f"{point_nom}-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}.json")
    json.dump(c, open(f + ".tmp", "w"), ensure_ascii=False, indent=1); os.replace(f + ".tmp", f)
    return f


# ================================================================== le monde : brancher, juger
def brancher(p, biblio=None, part=PART_EPREUVE):
    """A l installation ( ou a la reprise ) : chaque decideur du pays dont la bibliotheque a une version en service
    recoit son bras ( une adoptee decide pour tous, une en epreuve pour `part` des cles ). Une routine du soir juge les
    epreuves. Sans bibliotheque ou sans version, rien ne change ( aucun bras )."""
    J = p.socle.journal
    for t, champs in (("code_branche", ("point", "version", "part")), ("code_verdict", ("point", "version", "decision", "ecart", "p"))):
        try: J.declarer(t, DOMAINE_JOURNAL, "individuel", champs)
        except ValueError: pass
    p.w.code_biblio = biblio or BIBLIOTHEQUE           # sur le monde : Pays a des __slots__
    n = 0
    for nom, dec in getattr(p, "decideurs", {}).items():
        n += _brancher_un(p, dec, part)
    p.routine(23 + 50 / 60, 98, DOMAINE_JOURNAL, _juger)
    return n


def _brancher_un(p, dec, part):
    s = en_service(dec.point.nom, getattr(p.w, "code_biblio", None))
    if s is None: return 0
    v, source, etat = s
    try:
        dec.bras = BrasCode(source, v, dec.point.nom, 1.0 if etat.get("etat") == "adopte" else part, p.jour,
                            graine=int(p.socle.hasard.graine))
    except (CodeRefuse, SyntaxError) as ex:
        poser_etat(dec.point.nom, v, "refuse", {"raison": f"au branchement : {ex}"}, getattr(p.w, "code_biblio", None))
        return 0
    p.noter("code_branche", point=dec.point.nom, version=v, part=dec.bras.part)
    return 1


def _juger(p):
    """23 h 50 : une epreuve arrivee a JOURS_EPREUVE jours rend son verdict ( ecrit dans la bibliotheque, note au
    journal ). Retiree : le bras est ote, la raison chiffree part a Qwen dans une nouvelle demande. Adoptee : elle decide
    pour tous. Un point sans bras reprend la version qu un service aurait publiee entre-temps."""
    biblio = getattr(p.w, "code_biblio", None)
    for nom, dec in getattr(p, "decideurs", {}).items():
        b = getattr(dec, "bras", None)
        if b is None:
            _brancher_un(p, dec, PART_EPREUVE); continue
        if b.part >= 1.0 or p.jour - b.debut_j < JOURS_EPREUVE: continue
        r = b.verdict()
        if r["decision"] == "en_epreuve": continue
        poser_etat(nom, b.version, r["decision"], r, biblio)
        p.noter("code_verdict", point=nom, version=b.version, decision=r["decision"], ecart=round(r.get("ecart", 0.0), 6),
                p=round(r.get("p_meilleur", 1.0), 4))
        if r["decision"] == "adopte":
            b.part = 1.0
        else:
            dec.bras = None
            try: demander(nom, raison=f"{b.version} {r['decision']} : {r.get('raison')}", retour=r)
            except OSError: pass


# ================================================================== le service ( Qwen )
def consigne(d, historique):
    traits = "\n".join(f"  - t[{n!r}] : {src}" for n, src in d["traits"])
    passe = "\n".join(f"  - {h}" for h in historique) or "  ( aucune : c est la premiere version )"
    return f"""Tu ecris le code d une DECISION dans un pays simule ( point « {d['point']} », domaine « {d['domaine']} » ).
A chaque decision, le moteur appelle ta fonction decider(t) avec t, un dict de traits, chacun un nombre dans [0 ; 1] :
{traits}
Elle rend UNE action, par son nom, parmi : {d['actions']}.
Ce que mesure la note de chaque choix ( sur {d['horizon_j']} jours, c est elle qui te juge ) : {d['note']}
La regle d aujourd hui ( ta rivale : tu dois faire MIEUX qu elle, mesure dans le monde, jour par jour, sur des milliers de
decisions ; ce qu elle lit de plus que t n est pas a ta disposition ) :
```python
{d['regle']}
```
Les versions deja essayees et leur verdict :
{passe}
Pourquoi cette demande : {d.get('raison')}
Regles du bac a sable : une seule fonction decider(t) ( des fonctions auxiliaires sont permises ), pas d import, pas de
fichier, pas d attribut commencant par _, pas de global ; fonctions de base seulement ( {', '.join(PERMIS)} ) et le module
math ; 50 ms au plus par appel ; toujours rendre une action du catalogue, meme pour des traits inattendus.
Reponds avec UN bloc ```python contenant le code complet, puis une phrase qui dit ton idee."""


def _appel_qwen(prompt, penser=True, jetons=12000):
    corps = {"model": MODELE, "stream": False, "think": penser, "prompt": prompt, "keep_alive": -1,
             "options": {"temperature": 0.4, "num_predict": jetons, "num_ctx": CONTEXTE}}
    req = urllib.request.Request(HOTE + "/api/generate", data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=3600).read())


def essayer(source, d, n=ESSAIS_HORS_LIGNE, graine=0):
    """Hors ligne : sur les exemples reels de la demande et n entrees tirees dans [0 ; 1], le candidat rend toujours une
    action du catalogue, a temps. Rend { essais, actions ( repartition ), duree_max_ms } ou leve CodeRefuse."""
    f = compiler(source)
    rng = np.random.default_rng(graine)
    noms = [n_ for n_, _ in d["traits"]]
    entrees = [dict(zip(noms, e)) for e in d.get("exemples") or []]
    entrees += [dict(zip(noms, rng.random(len(noms)).tolist())) for _ in range(n)]
    entrees += [dict.fromkeys(noms, 0.0), dict.fromkeys(noms, 1.0)]
    rep = {}; dmax = 0.0
    for t in entrees:
        t0 = time.perf_counter(); a = appeler(f, t, d["actions"]); dmax = max(dmax, time.perf_counter() - t0)
        rep[d["actions"][a]] = rep.get(d["actions"][a], 0) + 1
    return {"essais": len(entrees), "actions": rep, "duree_max_ms": round(1000 * dmax, 2)}


def extraire_code(texte):
    m = re.findall(r"```(?:python)?\n(.*?)```", texte, re.S)
    return (max(m, key=len) if m else texte).strip() + "\n"


def traiter(fichier, biblio=None, appel=None):
    """Une demande : Qwen ecrit, le service verifie et essaie ; bon -> publie en epreuve ; refuse -> redemande avec
    l erreur, TENTATIVES fois au plus, puis publie refuse ( la raison reste ). Rend ( version, etat )."""
    appel = appel or _appel_qwen
    d = json.load(open(fichier))
    hist = []
    for v, e in versions(d["point"], biblio):
        vd = e.get("verdict") or {}
        hist.append(f"{v} : {e.get('etat')} ( note candidat {vd.get('moyenne_candidat')}, regle {vd.get('moyenne_regle')}, "
                    f"p {vd.get('p_meilleur')}, replis {vd.get('replis')} ) {vd.get('raison') or ''}")
    prompt = consigne(d, hist[-6:])
    erreur, source = None, ""
    for k in range(TENTATIVES):
        r = appel(prompt + (f"\n\nTa version precedente a ete REFUSEE par le service : {erreur}. Corrige-la." if erreur else ""))
        source = extraire_code(r.get("response", ""))
        if "def decider" not in source:
            r = appel(prompt + "\n\nEcris MAINTENANT le code, sans rien expliquer : un seul bloc ```python.", penser=False)
            source = extraire_code(r.get("response", ""))
        try:
            essai = essayer(source, d)
            return publier(d["point"], source, d, essai, "en_epreuve", biblio), "en_epreuve"
        except (CodeRefuse, SyntaxError, _Delai, Exception) as ex:
            erreur = f"{type(ex).__name__}: {str(ex)[:200]}"
    return publier(d["point"], source, d, {"erreur": erreur}, "refuse", biblio), "refuse"


def veiller(file=None, biblio=None, pause_s=30, une_fois=False):
    """Le service : traite la file dans l ordre d arrivee, sans fin ( une_fois : une passe ). Une demande pour un point
    qui a deja une version en epreuve attend la fin de l epreuve."""
    d = file or FILE; fait = os.path.join(d, "fait"); os.makedirs(fait, exist_ok=True)
    while True:
        for f in sorted(glob.glob(os.path.join(d, "*.json")), key=os.path.getmtime):
            point = os.path.basename(f).split("-")[0]
            if any(e.get("etat") == "en_epreuve" for _, e in versions(point, biblio)): continue
            try: v, etat = traiter(f, biblio)
            except Exception as ex:                          # Ollama coupe, reseau : la demande reste dans la file
                print(f"{time.strftime('%H:%M')} {os.path.basename(f)} : service indisponible ( {type(ex).__name__}: {ex} )", flush=True)
                continue
            os.replace(f, os.path.join(fait, os.path.basename(f)))
            print(f"{time.strftime('%H:%M')} {point} : {v} {etat}", flush=True)
        if une_fois: return
        time.sleep(pause_s)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--demander"); a.add_argument("--raison", default="premiere version")
    a.add_argument("--veille", action="store_true"); a.add_argument("--une-fois", action="store_true")
    x = a.parse_args()
    if x.demander: print(demander(x.demander, x.raison))
    if x.veille or x.une_fois: veiller(une_fois=x.une_fois)


if __name__ == "__main__":
    main()
