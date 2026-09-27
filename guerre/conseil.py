"""LE CONSEIL DE GUERRE : Qwen reecrit le gouvernement d une ile PENDANT la guerre, sans que personne n intervienne
( Younes, 26/09 : « le moins d intervention sur le moteur, qu il se gere lui-meme » ; plans/plan-code-a-la-demande.md :
du code a la demande, jamais adopte sur parole, jamais bloquant ).

1. LE SCENARIO : ce que la vraie guerre fait subir a l ile, lu dans le journal de l horloge ( guerre/horloge.py ), a
   l echelle d un habitant : la part de l armee au front, les morts au combat par militaire et par jour du moteur, ce
   que la guerre coute au Tresor par jour ( en part des recettes ), les lieux des zones occupees.
2. L ENTRAINEMENT : de petits pays neufs de l ile ( echelle 20, 10 000 habitants, graines d entrainement de l agent
   codeur ) subissent CHAQUE JOUR le scenario : mobiliser jusqu a la part au front, tuer au combat au taux reel, payer
   les armes ( d07.declarer_import, import_armement ), fermes des zones occupees sous sequestre. Le gouvernement voit
   la guerre dans son bulletin ( CerveauDeGuerre ). La note est celle de l agent codeur ( la faim d abord ).
3. LA BOUCLE : Qwen ecrit une version ( consigne de l agent codeur + la guerre + l historique ) ; elle est notee sur
   les memes mondes que le gouvernement en place ; si elle le bat, EXAMEN sur des mondes jamais vus ( graines
   d examen ) ; si elle le bat encore, elle est ADOPTEE : ecrite dans GOUVERNEMENTS/<Ile>.py, que l horloge de guerre
   relit a chaque tour et pose dans l ile vivante. Sinon, la raison chiffree retourne a Qwen.
4. JAMAIS BLOQUANT : un Qwen indisponible, un code refuse, un examen rate : la guerre continue avec le gouvernement
   en place.

   python -m guerre.conseil --guerre /mnt/data/hmt/guerre/essai10 [ --ile Malden ] [ --versions 6 ]"""
import argparse, json, math, os, re, sys, time
from collections import Counter
import numpy as np
from monde import agent_codeur as AC, config as C
from monde.archipel import Archipel, charger
from monde.pays import d07_exterieur as EXT, d06_etat as ET
from . import moteur as GM, zones as Z

ICI = os.path.dirname(os.path.abspath(__file__))
DEPOT = os.path.dirname(ICI)
GOUVERNEMENTS = "/mnt/data/hmt/guerre/gouvernements"       # le gouvernement adopte de chaque ile, relu par l horloge
SIX_ILES = os.path.join(DEPOT, "monde", "resultats", "agent_codeur", "six_iles")
GRAINES_ENTRAINEMENT = AC.GRAINES_ENTRAINEMENT[:3]          # 2001-2003
GRAINES_EXAMEN = (1001, 1002, 1003)                         # jamais vues pendant l entrainement
ECHELLE, JOURS = 20.0, 20


# ------------------------------------------------------------------ 1. le scenario
def scenario(dossier_guerre, ile, tours=15):
    """Les taux de la vraie guerre pour `ile`, sur les `tours` derniers tours de l horloge."""
    L = [json.loads(x) for x in open(os.path.join(dossier_guerre, "journal.jsonl"))][-tours:]
    if len(L) < 2: raise RuntimeError(f"pas assez de tours dans {dossier_guerre} pour lire la guerre")
    a, b = L[0]["iles"][ile], L[-1]["iles"][ile]
    jours = max(1, b["jour"] - a["jour"])
    mil = max(1, b["militaires"])
    morts = max(0, b["front"]["mort"] - a["front"]["mort"])
    paye = math.fsum(l["iles"][ile].get("paiement", {}).get("paye", 0.0) for l in L[1:])
    recettes = math.fsum(l["iles"][ile]["recettes"] for l in L[1:])
    carte = json.load(open(os.path.join(dossier_guerre, "carte.json")))
    lieux = {z["n"]: z["lieux"] for z in carte["zones"]}
    occupees = sorted(set(L[-1]["occupations"]["tenues"])) if carte["ile"] == ile else []
    return {"ile": ile, "jours_lus": jours, "part_au_front": (b["front"]["front"] + b["front"]["reserve"]) / mil,
            "morts_par_militaire_jour": morts / mil / jours, "part_recettes_armes": paye / recettes if recettes > 0 else 0.0,
            "lieux_occupes": sorted(l for n in occupees for l in lieux.get(n, [])), "zones_occupees": occupees,
            "faim_reelle": None}


def appliquer_scenario(w, sc, rng):
    """Un jour de guerre dans un petit pays : mobiliser, tuer, payer, occuper ( une fois )."""
    if not getattr(w, "guerre_scenario_pose", False):
        if sc["lieux_occupes"]: GM.occuper(w, 0, sc["lieux_occupes"], True)
        w.guerre_scenario_pose = True
    mil = GM.militaires(w)
    front = GM.bilan_front(w)
    manque = int(round(sc["part_au_front"] * mil)) - front["front"] - front["reserve"]
    if manque > 0:
        ks = GM.mobiliser(w, manque)
        GM.suivre(w, [(k, 0.0, 0.0, 0.0) for k in ks])                # au front aussitot
    vivants = [k for k, s in GM._front(w).items() if s["etat"] == "front"]
    n_morts = min(len(vivants), int(rng.poisson(sc["morts_par_militaire_jour"] * mil)))
    if n_morts: GM.morts_au_combat(w, list(rng.choice(vivants, n_morts, replace=False)))
    serie = list(GM._etat(w).tresor.serie)
    if serie and sc["part_recettes_armes"] > 0:
        valeur = sc["part_recettes_armes"] * max(0.0, serie[-1][1]) / 1.05       # FOB : le fret en plus
        paye = EXT.declarer_import(w.pays, w.gouv, valeur, GM.FAMILLE_ARMEMENT, motif="import_armement") if valeur > 0 else 0.0
        if paye > 0:                                   # compte comme dans la vraie guerre ( moteur.payer_la_guerre )
            w.guerre_paye = getattr(w, "guerre_paye", 0.0) + paye
            if not hasattr(w, "guerre_paiements"): w.guerre_paiements = []
            w.guerre_paiements.append((int(w.jour), paye)); del w.guerre_paiements[:-500]


# ------------------------------------------------------------------ 2. l entrainement
def evaluer_en_guerre(source, ile, sc, echelle=ECHELLE, jours=JOURS, graine=C.GRAINE):
    arc = Archipel(iles=(ile,), echelle=echelle, ouvert=False, parallele=False, graine=graine)
    w = arc.iles[ile].w
    w.cerveau = None if source == AC.REGLES else AC.CerveauCode(source)
    GM.voir_la_guerre(w)
    rng = np.random.default_rng([graine, 7])
    v0 = int(w.table.vivant[:w.table.n].sum())
    serie, refus, replis, actions, raisons = [], 0, 0, 0, Counter()
    n0 = len(w.evenements)
    for _ in range(jours):
        appliquer_scenario(w, sc, rng)
        arc.jours(1)
        serie.append(round(arc.commande(ile, "etat")["faim"], 4))
    patr = sum(1 for ev in w.evenements[n0:] if ev.get("type") == "patrouille_annulee")
    for ev in w.evenements[n0:]:
        if ev.get("type") != "decision_gouvernement": continue
        if str(ev.get("motifs", "")).startswith("cerveau indisponible"): replis += 1
        for a in ev.get("actions", []):
            actions += 1
            if not a.get("acceptee"): refus += 1; raisons[motif_du_refus(a)] += 1
    tenue, _ = w.pays.socle.conservation.tenue()
    m = {"jours_de_faim": round(sum(serie), 3), "faim_par_jour": serie, "morts_nets": v0 - int(w.table.vivant[:w.table.n].sum()),
         "dette": ET.sitrep(w.pays)["finances"].get("dette"), "refus": refus, "actions": actions, "patrouilles_annulees": patr,
         "raisons_refus": dict(raisons.most_common(6)), "jours_joues_par_les_regles": replis, "conservation": bool(tenue), "guerre": GM.bulletin_guerre(w)}
    m["score"] = AC.score(m)
    arc.fermer()
    return m


def motif_du_refus(a):
    """« type : raison », les nombres effaces : les refus d un meme motif se comptent ensemble."""
    return f"{(a.get('action') or {}).get('type')} : " + re.sub(r"[0-9][0-9.e+-]*", "N", str(a.get("raison", "")))[:70]


def _un(args):
    source, ile, sc, graine = args
    try: return evaluer_en_guerre(source, ile, sc, graine=graine)
    except (AC.CodeRefuse, SyntaxError) as ex: return {"erreur": f"{type(ex).__name__}: {ex}"}


def evaluer(source, ile, sc, graines, travailleurs=3):
    from multiprocessing import get_context
    with get_context("spawn").Pool(min(travailleurs, len(graines))) as pool:      # pas fork : voir deux()
        res = pool.map(_un, [(source, ile, sc, g) for g in graines])
    err = [r["erreur"] for r in res if "erreur" in r]
    if err: raise AC.CodeRefuse(err[0])
    moy = lambda k: round(sum(r[k] for r in res) / len(res), 3)
    m = {"jours_de_faim": moy("jours_de_faim"), "morts_nets": moy("morts_nets"), "dette": moy("dette"),
         "refus": sum(r["refus"] for r in res), "jours_joues_par_les_regles": sum(r["jours_joues_par_les_regles"] for r in res),
         "conservation": all(r["conservation"] for r in res), "actions": sum(r.get("actions", 0) for r in res),
         "patrouilles_annulees": sum(r.get("patrouilles_annulees", 0) for r in res),
         "raisons_refus": dict(sum((Counter(r.get("raisons_refus", {})) for r in res), Counter()).most_common(6)),
         "faim_par_jour": [round(sum(r["faim_par_jour"][j] for r in res) / len(res), 4) for j in range(len(res[0]["faim_par_jour"]))],
         "par_monde": {str(g): r["jours_de_faim"] for g, r in zip(graines, res)}}
    m["score"] = AC.score(m)
    return m


# ------------------------------------------------------------------ 3. la boucle
def contexte_de_guerre(sc, actuel):
    return f"""

TON PAYS EST EN GUERRE. Tu ne decides pas de la bataille ( elle se joue ailleurs ) : tu gouvernes le pays PENDANT
qu elle dure. Chaque jour, la guerre lui prend ( mesure dans la vraie guerre, a l echelle d un habitant ) :
- {sc['part_au_front']:.2%} de l armee est partie au front : absents, ils ne travaillent plus et ne mangent plus ici ;
- des soldats tues au combat ( {sc['morts_par_militaire_jour']:.5f} par militaire et par jour ) ;
- les armes achetees a l etranger, payees par le Tresor sur la ligne defense ( {sc['part_recettes_armes']:.1%} des
  recettes du jour ) ;
- les fermes des zones occupees par l ennemi, sous sequestre : elles ne livrent plus ( {len(sc['lieux_occupes'])} lieux ).
Le bulletin a une section « guerre » ( soldats au front, morts, cout ). La note est la meme : la faim d abord.
Tu peux changer les credits de la defense ( fixer_budget, ligne defense ) : c est l argent verse au front.

Le gouvernement en place ( a battre ) :
```python
{actuel}```"""


def actuel(ile):
    for d in (GOUVERNEMENTS, SIX_ILES):
        f = os.path.join(d, f"{ile}.py")
        if os.path.exists(f): return open(f).read()
    return AC.REGLES


def conseil(ile, dossier_guerre, versions=6, dossier=None, penser=True):
    d = dossier or os.path.join("/mnt/data/hmt/guerre/conseil", ile); os.makedirs(d, exist_ok=True)
    os.makedirs(GOUVERNEMENTS, exist_ok=True)
    journal = open(os.path.join(d, "journal.jsonl"), "a")
    def noter(x): journal.write(json.dumps(x, ensure_ascii=False) + "\n"); journal.flush()
    sc = scenario(dossier_guerre, ile)
    src0 = actuel(ile)
    t0 = time.time()
    en_place = evaluer(src0, ile, sc, GRAINES_ENTRAINEMENT)
    print(f"{ile} : scenario {json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in sc.items() if k != 'lieux_occupes'})}", flush=True)
    print(f"{ile} : gouvernement en place, en guerre : score {en_place['score']} faim {en_place['jours_de_faim']} ( {time.time() - t0:.0f} s )", flush=True)
    noter({"scenario": sc, "en_place": en_place, "source_en_place": src0})
    arc = Archipel(iles=(ile,), echelle=ECHELLE, ouvert=False, parallele=False)
    w = arc.iles[ile].w; GM.voir_la_guerre(w)
    appliquer_scenario(w, sc, np.random.default_rng(1)); arc.jours(1)
    exemple = dict(ET.sitrep(w.pays), guerre=GM.bulletin_guerre(w)); arc.fermer()
    base = AC.consigne(ile, exemple) + contexte_de_guerre(sc, src0 if src0 != AC.REGLES else "( les regles )\n")
    faites = []
    for n in range(1, versions + 1):
        t1 = time.time()
        prompt = base + (("\n\nTes versions precedentes et ce qu elles ont donne ( le gouvernement en place fait "
                          f"score {en_place['score']}, jours de faim {en_place['jours_de_faim']} ) :\n\n" + AC.historique(faites)) if faites else "")
        try:
            texte, pensee = AC.demander(prompt, penser=penser)
        except Exception as ex:                                     # jamais bloquant : Qwen indisponible, on attend
            print(f"{ile} v{n} : Qwen indisponible ( {ex} ), nouvel essai dans 60 s", flush=True); time.sleep(60); continue
        source = AC.extraire_code(texte)
        try: mes = evaluer(source, ile, sc, GRAINES_ENTRAINEMENT)
        except (AC.CodeRefuse, SyntaxError) as ex:
            mes = {"score": -1e9, "jours_de_faim": None, "faim_par_jour": [], "morts_nets": 0, "dette": None, "refus": 0,
                   "raisons_refus": {}, "jours_joues_par_les_regles": JOURS, "conservation": None, "erreur": f"{type(ex).__name__}: {ex}"}
        v = {"n": n, "source": source, "mesures": mes, "secondes": round(time.time() - t1), "pensee": len(pensee)}
        faites.append(v); noter(v)
        with open(os.path.join(d, f"v{n:03d}.py"), "w") as f: f.write(source)
        bat = bool(mes.get("conservation")) and mes["score"] > en_place["score"]
        print(f"{ile} v{n} : score {mes['score']} faim {mes['jours_de_faim']} {'BAT LE GOUVERNEMENT EN PLACE' if bat else ''} "
              f"{mes.get('erreur', '')[:100]} ( {v['secondes']} s )", flush=True)
        if not bat: continue
        ex_code = evaluer(source, ile, sc, GRAINES_EXAMEN); ex_place = evaluer(src0, ile, sc, GRAINES_EXAMEN)
        passe = ex_code["conservation"] and ex_code["score"] > ex_place["score"]
        noter({"examen": n, "code": ex_code, "en_place": ex_place, "passe": passe})
        print(f"{ile} v{n} : EXAMEN {'PASSE' if passe else 'RATE'} ( code {ex_code['score']} faim {ex_code['jours_de_faim']}, "
              f"en place {ex_place['score']} faim {ex_place['jours_de_faim']} )", flush=True)
        if passe:
            tmp = os.path.join(GOUVERNEMENTS, f".{ile}.py"); open(tmp, "w").write(source)
            os.replace(tmp, os.path.join(GOUVERNEMENTS, f"{ile}.py"))
            json.dump({"version": n, "adopte": time.strftime("%Y-%m-%d %H:%M:%S"), "entrainement": mes["score"],
                       "examen": ex_code["score"], "en_place_examen": ex_place["score"], "scenario": sc},
                      open(os.path.join(GOUVERNEMENTS, f"{ile}.json"), "w"), ensure_ascii=False)
            print(f"{ile} : version {n} ADOPTEE, l horloge la pose dans l ile au prochain tour", flush=True)
            return v
    return None


def ile_en_difficulte(dossier_guerre):
    """L ile dont la faim reelle est la plus haute au dernier tour ( a defaut : la plus touchee par la guerre )."""
    l = [json.loads(x) for x in open(os.path.join(dossier_guerre, "journal.jsonl"))][-1]
    return max(l["iles"], key=lambda i: (l["iles"][i].get("faim") or 0.0, l["iles"][i]["front"]["mort"]))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--guerre", required=True, help="le dossier de l horloge de guerre en cours")
    a.add_argument("--ile", default=None, help="sans : l ile la plus en difficulte")
    a.add_argument("--versions", type=int, default=6)
    a.add_argument("--sans-reflexion", action="store_true")
    a.add_argument("--reel", default=None, help="un instantane de la guerre : Qwen s entraine sur l etat reel de l ile")
    x = a.parse_args()
    ile = x.ile or ile_en_difficulte(x.guerre)
    if x.reel: conseil_reel(ile, x.reel, x.versions, penser=not x.sans_reflexion)
    else: conseil(ile, x.guerre, x.versions, penser=not x.sans_reflexion)
    return 0



# ------------------------------------------------------------------ 5. le conseil sur l etat reel ( 27/09 )
# Le premier conseil s entrainait sur de petits pays NEUFS : 20 jours ou la faim reste vers 2 %, alors que la vraie
# Malden du jour 250 a 38 % de faim ( et Stratis 98 % au jour 268 ). Qwen apprenait a gerer un pays qui va bien. Avec le
# marche immobilier accelere ( x15 ), une copie de l ile reelle ( l instantane de la guerre ) se joue en ~15 s par jour :
# chaque version est notee sur la VRAIE crise, contre le gouvernement en place, sur la meme copie ; examen = la meme
# copie sur un horizon double.
JOURS_REEL, JOURS_EXAMEN_REEL = 4, 8


def evaluer_reel(source, instantane, ile, jours=JOURS_REEL):
    import pickle
    from monde.archipel import Ile
    from monde import tests as T
    w = charger(os.path.join(instantane, f"{ile}.pkl"))
    w.cerveau = GM.CerveauDeGuerre(None if source == AC.REGLES else AC.CerveauCode(source), w)
    v0 = int(w.table.vivant[:w.table.n].sum())
    serie, refus, replis, actions, raisons = [], 0, 0, 0, Counter()
    n0 = len(w.evenements)
    ile_ = Ile(ile, w)
    for _ in range(jours):
        T.jours(w, 1)
        serie.append(round(ile_.commande("etat")["faim"], 4))
    patr = sum(1 for ev in w.evenements[n0:] if ev.get("type") == "patrouille_annulee")
    for ev in w.evenements[n0:]:
        if ev.get("type") != "decision_gouvernement": continue
        if str(ev.get("motifs", "")).startswith("cerveau indisponible"): replis += 1
        for a in ev.get("actions", []):
            actions += 1
            if not a.get("acceptee"): refus += 1; raisons[motif_du_refus(a)] += 1
    tenue, _ = w.pays.socle.conservation.tenue()
    m = {"jours_de_faim": round(sum(serie), 3), "faim_par_jour": serie, "morts_nets": v0 - int(w.table.vivant[:w.table.n].sum()),
         "dette": ET.sitrep(w.pays)["finances"].get("dette"), "refus": refus, "actions": actions, "patrouilles_annulees": patr,
         "raisons_refus": dict(raisons.most_common(6)), "jours_joues_par_les_regles": replis, "conservation": bool(tenue)}
    m["score"] = AC.score(m)
    return m


def _reel(args):
    source, instantane, ile, jours = args
    try: return evaluer_reel(source, instantane, ile, jours)
    except (AC.CodeRefuse, SyntaxError) as ex: return {"erreur": f"{type(ex).__name__}: {ex}", "score": -1e9}


def deux(sa, sb, instantane, ile, jours):
    """La version et le gouvernement en place, sur deux copies de la meme ile, en parallele. Des processus NEUFS
    ( spawn ) : le 27/09, apres les appels a Qwen, deux copies nees par fork ont attendu 30 minutes un verrou herite
    ( futex ), sans calculer."""
    from multiprocessing import get_context
    with get_context("spawn").Pool(2) as pool:
        return pool.map(_reel, [(sa, instantane, ile, jours), (sb, instantane, ile, jours)])


MOINS_DE_FAIM = 0.005     # somme des parts de menages affames sur l examen : un demi-point de pourcentage de moins au moins


def conseil_reel(ile, instantane, versions=6, dossier=None, penser=True):
    import pickle
    d = dossier or os.path.join("/mnt/data/hmt/guerre/conseil_reel", ile); os.makedirs(d, exist_ok=True)
    os.makedirs(GOUVERNEMENTS, exist_ok=True)
    journal = open(os.path.join(d, "journal.jsonl"), "a")
    def noter(x): journal.write(json.dumps(x, ensure_ascii=False) + "\n"); journal.flush()
    src0 = actuel(ile)
    t0 = time.time()
    en_place = evaluer_reel(src0, instantane, ile)
    w = charger(os.path.join(instantane, f"{ile}.pkl"))
    exemple = dict(ET.sitrep(w.pays), guerre=GM.bulletin_guerre(w), exterieur=GM.bulletin_exterieur(w), refus_hier=GM.refus_hier(w),
                   famine=GM.bulletin_famine(w))
    faim0 = GM.faim(w); jour0 = w.jour; del w
    print(f"{ile} ( etat reel, jour {jour0}, faim {faim0:.1%} ) : gouvernement en place score {en_place['score']} faim {en_place['faim_par_jour']} "
          f"( {time.time() - t0:.0f} s )", flush=True)
    noter({"instantane": instantane, "jour": jour0, "faim": faim0, "en_place": en_place, "source_en_place": src0})
    px = [m["nourriture"]["prix"] for m in exemple.get("marches", {}).values() if "nourriture" in m]
    px = sum(px) / len(px) if px else None
    prix_nourriture = ("Le prix de la nourriture n est affiche sur aucun marche" if px is None else
                       f"Le prix de la nourriture ce matin : {px:.2f}" + ( " ( son plafond : les marches manquent )" if px >= 9.99 else ""))
    base = AC.consigne(ile, exemple) + f"""

TON PAYS EST EN CRISE ET EN GUERRE, AUJOURD HUI ( jour {jour0} ) : {faim0:.0%} des menages n ont pas mange hier. Le
bulletin ci-dessus est le VRAI bulletin de ce matin, section « guerre » comprise. Ta version sera jouee sur une copie
exacte du pays, {JOURS_REEL} jours, contre le gouvernement en place sur la meme copie ; puis {JOURS_EXAMEN_REEL} jours pour
l examen. {prix_nourriture}. Tes leviers : acheter de la
nourriture pour la reserve population ( elle est distribuee a ceux qui n ont plus rien ; mais au marche il n y en a
plus ), importer de la nourriture destination « population » ( l aide alimentaire : au prix mondial + 20 %, elle arrive
au port et elle est distribuee aux menages sans nourriture ; dans les credits interieur, que fixer_budget peut porter a
trois fois le vote : chaque ligne de finances.budget porte son « plancher » et son « plafond », reste entre les deux ), subventionner, fixer les budgets ( la defense comprise ). Tout import passe par les devises de la
banque centrale ( section « exterieur » du bulletin ) : sans reserves de change, il est refuse ; exporter_or en rapporte.
La section « famine » compte tes morts de faim d hier et des 30 derniers jours : la faim du bulletin ne compte que les
menages VIVANTS, elle baisse quand les affames meurent. Sous 3 mois d importations de reserves, la banque centrale ne
sert plus que l essentiel ( nourriture, medicaments, energie, armement ) : le reste de tes achats a l etranger attend.
Ton armee ne patrouille que si son depot a du carburant ( section « armee » du bulletin : carburant_depot,
patrouilles_annulees_hier ) : c est a toi de l acheter ( acheter carburant, destination « armee », dans les credits de
la defense ) - dans la guerre, tes gouvernements ne l achetaient plus, et chaque patrouille etait annulee.
Le bulletin porte aussi « refus_hier » : les actions refusees a ta decision d hier, chacune avec sa raison ( souvent les
bornes permises, par exemple « credits X hors [a ; b] » ). Ne rejoue jamais une action refusee telle quelle : lis sa raison
et corrige-la ( reste dans les bornes ) ou choisis autre chose. Une action refusee ne fait rien et compte contre toi.

Le gouvernement en place ( a battre ) :
```python
{src0 if src0 != AC.REGLES else '( les regles )'}```"""
    faites = []
    for n in range(1, versions + 1):
        t1 = time.time()
        prompt = base + (("\n\nTes versions precedentes, jouees sur la copie ( le gouvernement en place fait score "
                          f"{en_place['score']}, faim par jour {en_place['faim_par_jour']} ) :\n\n" + AC.historique(faites)) if faites else "")
        try: texte, pensee = AC.demander(prompt, penser=penser)
        except Exception as ex:
            print(f"{ile} v{n} : Qwen indisponible ( {ex} ), nouvel essai dans 60 s", flush=True); time.sleep(60); continue
        source = AC.extraire_code(texte)
        mes = _reel((source, instantane, ile, JOURS_REEL))
        if "erreur" in mes:
            mes.update({"jours_de_faim": None, "faim_par_jour": [], "morts_nets": 0, "dette": None, "refus": 0, "raisons_refus": {},
                        "jours_joues_par_les_regles": JOURS_REEL, "conservation": None})
        v = {"n": n, "source": source, "mesures": mes, "secondes": round(time.time() - t1), "pensee": len(pensee)}
        faites.append(v); noter(v)
        with open(os.path.join(d, f"v{n:03d}.py"), "w") as f: f.write(source)
        marge = 1.0                                  # un point de score au moins : un souffle d avance n est pas une preuve
        bat = bool(mes.get("conservation")) and mes["score"] >= en_place["score"] + marge
        print(f"{ile} v{n} : score {mes['score']} faim {mes.get('faim_par_jour')} {'BAT LE GOUVERNEMENT EN PLACE' if bat else ''} "
              f"{mes.get('erreur', '')[:100]} ( {v['secondes']} s )", flush=True)
        if not bat: continue
        ex_code, ex_place = deux(source, src0, instantane, ile, JOURS_EXAMEN_REEL)
        # 27/09 : et la faim doit BAISSER a l examen - Stratis avait adopte une version a faim identique au dix-millieme,
        # gagnante d un point par des refus en moins ; au moins un demi-point de pourcentage de faim en moins sur 8 jours
        moins_de_faim = sum(ex_place.get("faim_par_jour") or [0]) - sum(ex_code.get("faim_par_jour") or [0]) >= MOINS_DE_FAIM
        passe = bool(ex_code.get("conservation")) and ex_code["score"] >= ex_place["score"] + marge and moins_de_faim
        noter({"examen": n, "code": ex_code, "en_place": ex_place, "passe": passe})
        print(f"{ile} v{n} : EXAMEN ( {JOURS_EXAMEN_REEL} jours ) {'PASSE' if passe else 'RATE'} ( code {ex_code['score']} faim {ex_code.get('faim_par_jour')}, "
              f"en place {ex_place['score']} faim {ex_place.get('faim_par_jour')} )", flush=True)
        if passe:
            tmp = os.path.join(GOUVERNEMENTS, f".{ile}.py"); open(tmp, "w").write(source)
            os.replace(tmp, os.path.join(GOUVERNEMENTS, f"{ile}.py"))
            json.dump({"version": n, "adopte": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": "reel", "jour": jour0,
                       "copie": mes["score"], "examen": ex_code["score"], "en_place_examen": ex_place["score"]},
                      open(os.path.join(GOUVERNEMENTS, f"{ile}.json"), "w"), ensure_ascii=False)
            print(f"{ile} : version {n} ADOPTEE, l horloge la pose dans l ile au prochain tour", flush=True)
            return v
    return None


if __name__ == "__main__":
    sys.exit(main())
