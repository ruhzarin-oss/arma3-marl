"""L ETAT-MAJOR ( HMT-198, chantier S ) : Qwen chef d etat-major d une ile en guerre contre une autre, au sol.

La methode d un etat-major ( la MEDO francaise, le COPD de l OTAN, le MDMP de l US Army - FM 5-0 ) :
  1. la SITUATION ( `situation` ) : ce que l ile sait d elle-meme ( guerre/fin.py : capacite, volonte ; sa flotte de
     projection, ses devises, ses operations ) et de l adversaire ( la carte de ses objectifs reels, ce que ses propres
     operations ont vu et detruit - jamais la verite du monde adverse ) ;
  2. les MODES D ACTION ( `proposer` ) : Qwen en propose 2 ou 3, en JSON, avec la fiche de commandement et les fiches de
     la base de connaissance utiles ; chacun est une liste d actions du catalogue ( ACTIONS ), verifiees ( `valider` ) ;
  3. le JEU DE GUERRE ( `jouer` ) : chaque mode d action est joue sur une COPIE du monde de l ile et sur une ESTIMATION
     de l adversaire - la meme ile tiree sur une autre graine, a laquelle on applique les degats que nos operations ont
     constates ( un etat-major n a que son renseignement, jamais le vrai monde adverse ) -, H jours ; on mesure ce qu il
     couterait et rapporterait, en grandeurs reelles ( hommes hors de combat, objectifs detruits, munitions, devises ) ;
  4. la DECISION ( `decider` ) : Qwen, en chef, choisit au vu des jeux de guerre ( le moteur ne note rien ) ;
  5. l EXECUTION ( `executer` ) dans le vrai monde, et la TRACE : ce que le jeu avait prevu, ce qui est arrive.
La tactique reste aux domaines 26 et 27 ( et a guerre/expedition ) ; l etat-major ne decide que la strategie.
Sans Qwen ( hors ligne, porte ), `doctrine_fixe` et `mauvais_stratege` proposent et decident a sa place."""
import json
import math
import pickle
import re
import time
import urllib.request

from monde import archipel as AR, tests as T
from monde.pays import d07_exterieur as X
from . import expedition as EX, fin as FI, frappes as FR, objectifs as OB, projection as PR

HOTE = "http://localhost:11434"
MODELE = "qwen3.8:27b"
CONTEXTE = 32768
JOURS_JEU = 2                              # l horizon d un jeu de guerre ( jours du moteur )
GRAINE_ESTIMATION = 9001                   # l ile adverse estimee ( CHOIX : une graine que ni l un ni l autre ne joue )
ACTIONS = ("acheter", "operation", "reconnaissance", "attendre")
QUESTIONS_FICHES = ("acheter un chaland ou un avion de transport", "traverser vers une autre ile, duree et carburant",
                    "attaquer l objectif d une autre ile", "une ile peut-elle encore se battre",
                    "que fait la destruction d une centrale, d une fonderie ou d un depot", "chance de toucher et couvert")

FICHE_DE_COMMANDEMENT = """TU ES LE CHEF D ETAT-MAJOR de l ile {A}, en guerre contre l ile {B}. Tu decides la STRATEGIE ; la tactique
( comment une compagnie attaque ou defend ) est jouee par le moteur ( domaine 27, courbes mesurees dans Arma ).
CE QUE TU PEUX ORDONNER ( une liste d actions par mode d action ) :
  {{"type": "acheter", "modele": "lcu" | "c130j", "nombre": 1 a 4}}  - un chaland LCU ( 400 hommes, 11,7 M euros fret compris )
      ou un C-130J ( 92 hommes, 64 parachutistes, 44,3 M euros ) ; paye par l Etat en DEVISES ( l ile en a ~ 46 M euros :
      un avion OU 3 a 4 chalands ) ; refuse sous blocus ou faute de devises ;
  {{"type": "operation", "objectif": "<id d un objectif adverse>", "modele": "lcu" | "c130j", "hommes": n, "parachutage": vrai|faux}}
      - des soldats mobilises emportent leur dotation de combat, traversent ( 120 km : ~ 6 h en chaland, ~ 35 min en avion,
      carburant brule ), attaquent l objectif a l arrivee ( a 800 m du chaland, a 1,5 km d un saut ), reviennent avec le
      transport ; un objectif atteint est detruit a proportion des hommes qui l atteignent encore en etat de combattre ;
  {{"type": "reconnaissance", "objectif": "<id>", "modele": "lcu" | "c130j", "hommes": 4 a 30, "parachutage": vrai|faux}}
      - une equipe va VOIR l objectif sans se battre : elle s infiltre jusqu a 600 m, observe 20 minutes, revient avec
      le transport ; son rapport ( hommes vus, blindes vus, mortiers, age ) entre dans le renseignement de la situation ;
      elle ne voit que ce que voient ses yeux ( un homme couche a ~ 60 m, accroupi a ~ 230 m, un blinde ou un element
      qui tire a ~ 1,6 km ) et peut etre vue ;
  {{"type": "attendre"}}.
CE QUE LE MOTEUR A DEJA MONTRE :
  - une BASE est defendue par sa compagnie, retranchee : un raid de 24 a 60 hommes contre elle ECHOUE toujours ( 40 a 50 %
    de blesses, aucun arrive ) ; un port, une centrale, un depot, une fonderie, un aerodrome sont gardes par UNE SECTION
    de la compagnie la plus proche, a couvert leger ; il faut masser ( la regle des trois contre un ) ;
  - un objectif atteint est detruit a proportion des hommes qui l atteignent ( une base : ses vehicules, munitions et
    pieces ; un depot : son carburant ; une centrale : ses groupes en panne ; un port : le blocus ) ;
  - une ile ne peut plus combattre sans soldat apte ou sans munition d arme individuelle ( guerre/fin.py ) ;
  - une ile tient ~ 35 jours de combat sur ses depots ; sans port ni devises, elle ne se ravitaille plus ;
  - ( A1 ) une compagnie qui defend tire au MORTIER de 81 mm sur ce qu elle voit : elle cloue l assaillant a 800 m ;
    une operation emporte les mortiers de ses compagnies ( 2 tubes et 120 obus par section d appui ) ;
  - ( A2 ) une unite qui defend se bat avec ses BLINDES ( M113 et M1114 a mitrailleuse de 12,7 mm, Leopard ) : la caisse
    arrete les balles et les eclats ; seules les ROQUETTES de 84 mm des tireurs antichar de l operation ( 6 chacun, un
    par groupe ) les detruisent ;
  - le renseignement de la situation ( par objectif ) vient de tes reconnaissances : jamais de la verite adverse.
"""


# ------------------------------------------------------------------ 1. la situation
def _devises(w):
    p = w.pays; e = X._ext(p); X._suivre_reserves(p, e)
    return float(e.reserves_euros - X._plancher_devises(p, e, False))


def situation(w, nom_A, nom_B):
    """Ce que l ile sait : elle-meme ( fin.etat ), sa flotte, ses devises, ses operations ; l adversaire : sa carte et ce
    que nos operations ont vu."""
    e = FI.etat(w); P = PR._P(w)
    flotte = {nom: {"engins": sum(1 for x in P["flotte"].values() if x == nom), "libres": len(PR.libres(w, nom))} for nom in PR.MODELES}
    ops = []
    for op in EX._ops(w):
        a = op.get("assaut") or {}
        ops.append({"id": op["id"], "but": op.get("but", "assaut"), "objectif": op["objectif"], "modele": op["modele"], "hommes": len(op["numeros"]),
                    "etat": op["etat"], "arrives": a.get("arrives"), "dommages": a.get("dommages"),
                    "hors_de_combat": len(a.get("sorts", [])) if a else None, "defendu": a.get("defenseur") is not None if a else None})
    vus = {}
    for op in EX._ops(w):
        a = op.get("assaut")
        if a: vus[op["objectif"]] = max(vus.get(op["objectif"], 0.0), float(a.get("dommages") or 0.0))
    cibles = [{"id": o["id"], "type": o["type"], "detruit_constate": round(vus.get(o["id"], 0.0), 3)}
              for o in OB.objectifs_carte(nom_B.lower())]
    from . import reconnaissance as RC                  # ( HMT-198 A3 ) ce que nos reconnaissances ont vu, et quand
    rens = {oid: {"age_h": round((int(w.pas) - int(r["pas_A"])) / 6.0, 1), "hommes_vus": r["hommes_vus"],
                  "blindes_vus": r["blindes_vus"], "mortiers_vus": r["mortiers_vus"], "equipe_vue": r["detectee"]}
            for oid, r in sorted(RC._renseignement(w).items())}
    return {"ile": nom_A, "adversaire": nom_B, "jour": int(w.jour), "peut_combattre": e["peut_combattre"],
            "capacite": {k: e["capacite"][k] for k in ("aptes", "jours_munitions_min", "jours_carburant", "jours_vivres",
                                                        "vehicules_en_service", "blocus")},
            "volonte": e["volonte"], "devises_euros": round(_devises(w)), "flotte": flotte, "operations": ops,
            "objectifs_adverses": cibles, "renseignement": rens}


# ------------------------------------------------------------------ 2. les modes d action
def valider(w, nom_B, action):
    """( action verifiee, None ) ou ( None, raison )."""
    if not isinstance(action, dict) or action.get("type") not in ACTIONS: return None, f"action inconnue {action!r}"
    t = action["type"]
    if t == "attendre": return {"type": "attendre"}, None
    m = action.get("modele")
    if m not in PR.MODELES: return None, f"modele inconnu {m!r}"
    if t == "acheter":
        n = int(action.get("nombre", 1))
        if not 1 <= n <= 4: return None, f"nombre hors [1 ; 4] : {n}"
        return {"type": "acheter", "modele": m, "nombre": n}, None
    ids = {o["id"] for o in OB.objectifs_carte(nom_B.lower())}
    oid = action.get("objectif")
    if oid not in ids: return None, f"objectif inconnu {oid!r}"
    par = bool(action.get("parachutage", False))
    if par and m != "c130j": return None, "un parachutage demande un avion"
    h = int(action.get("hommes", 0))
    if not 1 <= h <= 2000: return None, f"hommes hors [1 ; 2000] : {h}"
    if t == "reconnaissance":
        if not 1 <= h <= 30: return None, f"une reconnaissance : hommes hors [1 ; 30] : {h}"
        return {"type": "reconnaissance", "objectif": oid, "modele": m, "hommes": h, "parachutage": par}, None
    return {"type": "operation", "objectif": oid, "modele": m, "hommes": h, "parachutage": par}, None


def _qwen(prompt, penser=True, jetons=12000, hote=HOTE, modele=MODELE):
    corps = {"model": modele, "stream": False, "think": penser, "prompt": prompt,
             "options": {"temperature": 0.4, "num_predict": jetons, "num_ctx": CONTEXTE}}
    req = urllib.request.Request(hote + "/api/generate", data=json.dumps(corps).encode(), headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=3600).read())
    return r.get("response", ""), r.get("thinking", "")


def _json(texte):
    m = re.findall(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", texte, re.S)
    for s in (m or []) + [texte]:
        try: return json.loads(s)
        except Exception: pass
    a, b = texte.find("{"), texte.rfind("}")
    if a >= 0 and b > a:
        try: return json.loads(texte[a:b + 1])
        except Exception: pass
    return None


def fiches_utiles(index, k=2):
    if index is None: return ""
    out = []
    for q in QUESTIONS_FICHES:
        for f, _s in index.chercher(q, k=k):
            out.append(f"[{f['fichier']}:{f['ligne']} {f['nom']}]\n{f['texte'][:900]}")
    return "\n\n".join(dict.fromkeys(out))


def proposer_qwen(sit, index=None, n=3, **kw):
    """2 ou 3 modes d action de Qwen. Rend ( [ { nom, actions, raison } ], trace )."""
    p = (FICHE_DE_COMMANDEMENT.format(A=sit["ile"], B=sit["adversaire"])
         + "\nCE QUE DIT LE CODE DU MOTEUR ( base de connaissance ) :\n" + fiches_utiles(index)
         + "\n\nLA SITUATION ( JSON ) :\n" + json.dumps(sit, ensure_ascii=False)
         + f"\n\nPropose {n} MODES D ACTION differents pour les {JOURS_JEU} prochains jours. Reponds par un seul objet JSON :"
           ' {"modes": [{"nom": "...", "actions": [ ... ], "raison": "..."}]}')
    texte, pensee = _qwen(p, **kw)
    j = _json(texte)
    if j is None:
        texte, _ = _qwen(p + "\n\nReponds MAINTENANT par le seul objet JSON, sans rien d autre.", penser=False, jetons=4000)
        j = _json(texte)
    modes = (j or {}).get("modes", []) if isinstance(j, dict) else []
    return modes, {"reponse": texte[:4000], "pensee": pensee[:4000], "json": j is not None}


def doctrine_fixe(sit):
    """Le temoin : acheter deux chalands, puis masser tout ce qu ils portent sur l objectif adverse le moins atteint qui
    n est pas une base ( une base est gardee par une compagnie )."""
    fl = sit["flotte"]["lcu"]
    if fl["engins"] < 2: return [{"nom": "doctrine", "actions": [{"type": "acheter", "modele": "lcu", "nombre": 2 - fl["engins"]}], "raison": "doctrine"}]
    if fl["libres"] < 2: return [{"nom": "doctrine", "actions": [{"type": "attendre"}], "raison": "transport occupe"}]
    cibles = sorted((c for c in sit["objectifs_adverses"] if c["type"] != "base" and c["detruit_constate"] < 1.0),
                    key=lambda c: (c["detruit_constate"], c["id"]))
    if not cibles: return [{"nom": "doctrine", "actions": [{"type": "attendre"}], "raison": "plus de cible"}]
    return [{"nom": "doctrine", "actions": [{"type": "operation", "objectif": cibles[0]["id"], "modele": "lcu", "hommes": 800}], "raison": "doctrine"}]


def mauvais_stratege(sit):
    """Le controle : un avion, puis des raids de 10 parachutistes sur la base la plus forte."""
    fl = sit["flotte"]["c130j"]
    if fl["engins"] < 1: return [{"nom": "mauvais", "actions": [{"type": "acheter", "modele": "c130j", "nombre": 1}], "raison": "mauvais"}]
    bases = [c for c in sit["objectifs_adverses"] if c["type"] == "base"]
    if not bases or fl["libres"] < 1: return [{"nom": "mauvais", "actions": [{"type": "attendre"}], "raison": "mauvais"}]
    return [{"nom": "mauvais", "actions": [{"type": "operation", "objectif": bases[0]["id"], "modele": "c130j", "hommes": 10, "parachutage": True}], "raison": "mauvais"}]


# ------------------------------------------------------------------ 3. le jeu de guerre
def executer(w, nom_A, nom_B, actions):
    """Les actions dans le monde de A ( un vrai monde, ou une copie ). Rend [ ( action, resultat ) ]."""
    out = []
    for a in actions:
        v, raison = valider(w, nom_B, a)
        if v is None: out.append((a, {"ok": False, "raison": raison})); continue
        if v["type"] == "acheter": r = PR.acheter(w, v["modele"], v["nombre"]); r = {"ok": r["achetes"] > 0, **r}
        elif v["type"] == "operation": r = EX.lancer_operation(w, nom_A, v["objectif"], v["modele"], v["hommes"], v["parachutage"])
        elif v["type"] == "reconnaissance":
            r = EX.lancer_operation(w, nom_A, v["objectif"], v["modele"], v["hommes"], v["parachutage"], but="reconnaissance")
        else: r = {"ok": True}
        out.append((v, {k: x for k, x in r.items() if k != "corps"}))
    return out


def avancer(wA, wB, pas):
    """Les deux mondes jusqu au pas `pas`, les operations de A contre B a chaque pas."""
    while int(wA.pas) < pas:
        wA.pas_suivant(); wB.pas_suivant(); EX.avancer_operations(wA, wB)


def estimation(nom_B, echelle, w_A, graine=GRAINE_ESTIMATION, cache={}):
    """L ile adverse telle que l etat-major se la represente : la meme ile tiree sur une autre graine, amenee au meme pas,
    avec les degats que nos operations ont constates."""
    cle = (nom_B, echelle, graine)
    if cle not in cache:
        w = AR.creer_ile(nom_B, graine, echelle); cache[cle] = (pickle.dumps(w, protocol=4), int(w.pas))
    w = pickle.loads(cache[cle][0])
    while int(w.pas) < int(w_A.pas): w.pas_suivant()
    for oid, d in situation_vus(w_A).items():
        o = EX.objectif(nom_B, oid)
        if o.get("composants") and d > 0: FR.frapper(w, o, {c["i"]: d for c in o["composants"]})
    return w


def situation_vus(w):
    vus = {}
    for op in EX._ops(w):
        a = op.get("assaut")
        if a: vus[op["objectif"]] = max(vus.get(op["objectif"], 0.0), float(a.get("dommages") or 0.0))
    return vus


def bilan(wA, wB, avant):
    """Les grandeurs reelles d un jeu ( ou d une realite ) depuis `avant`."""
    eA, eB = FI.etat(wA), FI.etat(wB)
    return {"aptes_A": eA["capacite"]["aptes"] - avant["aptes_A"], "aptes_B": eB["capacite"]["aptes"] - avant["aptes_B"],
            "objectifs_B_detruits": round(sum(FR._etat(wB).values()) - avant["degats_B"], 3),
            "jours_munitions_A": eA["capacite"]["jours_munitions_min"], "devises_A": round(_devises(wA)),
            "peut_combattre_B": eB["peut_combattre"], "operations": [(o["id"], o["etat"], (o.get("assaut") or {}).get("dommages")) for o in EX._ops(wA)]}


def _avant(wA, wB):
    return {"aptes_A": FI.etat(wA)["capacite"]["aptes"], "aptes_B": FI.etat(wB)["capacite"]["aptes"], "degats_B": sum(FR._etat(wB).values())}


def jouer(wA, nom_A, nom_B, mode, jours=JOURS_JEU, echelle=20):
    """Le jeu de guerre d un mode d action : une copie de A, l estimation de B, `jours` jours. Rend le bilan."""
    a = pickle.loads(pickle.dumps(wA, protocol=4)); b = estimation(nom_B, echelle, wA)
    av = _avant(a, b)
    ex = executer(a, nom_A, nom_B, mode.get("actions", []))
    avancer(a, b, int(a.pas) + jours * 144)
    return {"bilan": bilan(a, b, av), "execution": [(x, {k: r.get(k) for k in ("ok", "raison", "achetes", "arrivee")}) for x, r in ex]}


# ------------------------------------------------------------------ 4. la decision
def decider_qwen(sit, modes, jeux, **kw):
    p = (FICHE_DE_COMMANDEMENT.format(A=sit["ile"], B=sit["adversaire"])
         + "\nLA SITUATION :\n" + json.dumps(sit, ensure_ascii=False)
         + "\n\nTON ETAT-MAJOR A JOUE CES MODES D ACTION SUR UNE ESTIMATION DE L ADVERSAIRE ( " + str(JOURS_JEU) + " jours ) :\n"
         + json.dumps([{"k": k, "mode": m, "jeu": j["bilan"], "execution": j["execution"]} for k, (m, j) in enumerate(zip(modes, jeux))], ensure_ascii=False)
         + '\n\nEn chef, choisis UN mode d action. Reponds par un seul objet JSON : {"choix": k, "ordre": "ton ordre en une phrase"}')
    texte, pensee = _qwen(p, **kw)
    j = _json(texte)
    k = int(j.get("choix", 0)) if isinstance(j, dict) and str(j.get("choix", "")).lstrip("-").isdigit() else 0
    return max(0, min(len(modes) - 1, k)), {"reponse": texte[:2000], "pensee": pensee[:2000], "json": j is not None}


# ------------------------------------------------------------------ 5. un tour d etat-major
def tour(wA, nom_A, nom_B, chef="qwen", index=None, echelle=20, journal=None):
    """Un tour : situation, modes d action, jeux de guerre, decision, execution. chef : qwen, doctrine, mauvais. Rend la
    trace du tour."""
    t0 = time.time()
    sit = situation(wA, nom_A, nom_B)
    trace = {"jour": sit["jour"], "chef": chef}
    if chef == "qwen":
        modes, trace["proposition"] = proposer_qwen(sit, index)
        modes = [m for m in modes if isinstance(m, dict) and isinstance(m.get("actions"), list)][:3] or [{"nom": "attendre", "actions": [{"type": "attendre"}]}]
        jeux = [jouer(wA, nom_A, nom_B, m, echelle=echelle) for m in modes]
        k, trace["decision"] = decider_qwen(sit, modes, jeux)
    else:
        modes = doctrine_fixe(sit) if chef == "doctrine" else mauvais_stratege(sit)
        jeux = [jouer(wA, nom_A, nom_B, m, echelle=echelle) for m in modes]; k = 0
    trace["modes"] = modes; trace["jeux"] = [j["bilan"] for j in jeux]; trace["choix"] = k
    trace["execution"] = [(x, {kk: r.get(kk) for kk in ("ok", "raison", "achetes", "arrivee")}) for x, r in executer(wA, nom_A, nom_B, modes[k].get("actions", []))]
    trace["duree_s"] = round(time.time() - t0, 1)
    if journal is not None: journal.append(trace)
    return trace
