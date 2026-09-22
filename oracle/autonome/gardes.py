"""LES GARDE-FOUS. Chacun a ete ecrit contre une faute reellement commise les 19, 20 et 21/09 ; la faute est citee.
Un garde-fou qui echoue avant le vol EMPECHE de poser ; apres le vol, il met l iteration en QUARANTAINE ( on n en
apprend rien ) ou ARRETE la boucle ( il faut un humain )."""
import glob, hashlib, json, os, re, subprocess, time
from . import config as C


# ---------------- avant le vol ----------------
def stop_demande():
    return os.path.exists(f"{C.ETAT_DIR}/STOP")


def disque_monte():
    # 20/09 18 h 40 : apres l ecran bleu, /mnt/data n etait plus monte ; les scripts auraient ecrit dans le vide
    return os.path.exists(f"{C.H}/.temoin") and os.path.isdir(C.QUEUE)


def file_vide():
    # ne jamais melanger deux campagnes, ni poser par-dessus une iteration en vol
    return not glob.glob(f"{C.QUEUE}/*.json") and not glob.glob(f"{C.EN_COURS}/*.json")


def empreinte_mission():
    # 20/09 16 h 17 : mission modifiee pendant que douze serveurs jouaient -> 16 episodes sur 32 tues
    h = hashlib.sha256()
    for f in sorted(glob.glob(f"{C.MISSION}/mission.Altis/**/*", recursive=True)) + [f"{C.MISSION}/lancer.sh"]:
        # chemins RELATIFS : l empreinte decrit le contenu, pas l endroit ( trouve par le test de sensibilite du 21/09 :
        # avec le chemin absolu, une copie identique de la mission donnait une autre empreinte )
        if os.path.isfile(f): h.update(os.path.relpath(f, C.MISSION).encode()); h.update(open(f, "rb").read())
    return h.hexdigest()[:16]


def depot_propre():
    r = subprocess.run(["git", "-C", C.DEPOT, "status", "--porcelain", "bancs/chacaloracle", "outils", "oracle/autonome"],
                       capture_output=True, text=True)
    return r.returncode == 0 and not r.stdout.strip()


def armes_permises(p):
    s, g = p["situation"], p["graines"]
    fautes = [f"{k}={s.get(k)}" for k in C.ARMES if s.get(k) not in C.ARMES[k]]
    if len(set(g)) != 2 or any(x not in C.GRAINES for x in g): fautes.append(f"graines={g}")
    return fautes


def budget(etat, n_episodes):
    maintenant = time.time()
    recentes = [h for h in etat["historique"] if maintenant - h.get("debut_ts", 0) < 86400]
    fautes = []
    if n_episodes > C.EPISODES_MAX_ITERATION: fautes.append(f"{n_episodes} episodes > {C.EPISODES_MAX_ITERATION}")
    if len(recentes) >= C.ITERATIONS_MAX_24H: fautes.append(f"{len(recentes)} iterations en 24 h")
    if etat["iteration"] >= C.ITERATIONS_MAX_TOTAL: fautes.append(f"iteration {etat['iteration']} >= {C.ITERATIONS_MAX_TOTAL}")
    return fautes


def controle_job(chemin):
    r = subprocess.run(["bash", C.CONTROLE, chemin], capture_output=True, text=True)
    return "CONTROLE OK" in r.stdout, [l for l in r.stdout.splitlines() if "REFUS" in l]


# ---------------- apres le vol ----------------
def runs_de(campagne):
    out = []
    for jf in glob.glob(f"{C.RUNS}/2026-*/job.json"):
        try:
            j = json.load(open(jf))
            # un job multiple n est pas un run d episodes : ses cellules reviennent en runs virtuels ( amendement 6 )
            if j.get("campagne") == campagne and j.get("banc") != "chacalmulti": out.append(os.path.dirname(jf))
        except Exception: pass
    return out


def deploiement_prouve(campagne):
    # 20/09 16 h 17 : « DEPLOIEMENT NON PROUVE : la mission jouee differe du depot »
    fautifs = [r for r in runs_de(campagne) if "DEPLOIEMENT NON PROUVE" in open(f"{r}/run.log", errors="ignore").read()]
    return not fautifs, fautifs


def signature_seconde_graine(campagne):
    # meme incident, vu dans l inventaire : la premiere graine du job a un resultat, la seconde aucun
    n = 0
    for r in runs_de(campagne):
        gs = [x for x in sorted(glob.glob(f"{r}/g*/")) if not os.path.exists(x + "ARRET_MANUEL")]
        if len(gs) >= 2 and os.path.exists(gs[0] + "resultat.json") and not os.path.exists(gs[-1] + "resultat.json"): n += 1
    return n


def verifier_apres_vol(E, campagne):
    """Retourne ( quarantaine: bool, arret: bool, raisons: list )."""
    raisons, quarantaine, arret = [], False, False
    ok, fautifs = deploiement_prouve(campagne)
    if not ok: raisons.append(f"DEPLOIEMENT NON PROUVE dans {len(fautifs)} run(s)"); quarantaine = arret = True
    sig = signature_seconde_graine(campagne)
    if sig >= 2: raisons.append(f"{sig} jobs dont la seconde graine n a aucun resultat ( signature d un deploiement rate )"); quarantaine = arret = True
    acc = [e for e in E if e["verdict"] == "ACCEPTE"]
    # 20/09 : quatre erreurs SQF quand les dix hommes etaient morts ( liste des vivants vide )
    err = sum(e["erreurs"] for e in acc)
    if err: raisons.append(f"{err} erreur(s) SQF dans les episodes acceptes"); quarantaine = True
    # 20/09 : option confondue avec la situation ; ici on verifie que l option jouee est celle imposee
    faux = [e for e in acc if e.get("choix_joue") not in (None, e["option_imposee"])]
    if faux: raisons.append(f"{len(faux)} episode(s) ou l option jouee differe de l option imposee"); quarantaine = True
    taux = len(acc) / max(1, len(E))
    if taux < C.SEUIL_ACCEPTATION: raisons.append(f"acceptation {taux:.2f} < {C.SEUIL_ACCEPTATION}"); quarantaine = True
    return quarantaine, arret, raisons


def cases_vides(E, propositions):
    """( candidat, option ) sans aucun episode utilisable. Se repare par rejeu - une fois. Compte des CASES, pas des
    exemplaires ( 20/09 : une porte qui comptait des exemplaires ne pouvait plus jamais passer apres un plantage )."""
    pleines = {(e["candidat"], e["option_imposee"]) for e in E if e["verdict"] == "ACCEPTE" and e["fin"] and e["erreurs"] == 0}
    return [(k, o) for k in range(len(propositions)) for o in (1, 2) if (k, o) not in pleines]


# ---------------- la sante de l imagination ----------------
def imagination_saine(monde, E):
    """21/09 : l imagination v1 predisait 0,335 partout pour un taux reel de 0,162 - des reseaux figes a mi-chemin
    entre leur sortie de depart ( 0,5 ) et le vrai taux. Trois signatures, verifiees sur ses PROPRES episodes
    d apprentissage avant qu elle ait le droit d imaginer quoi que ce soit :
      1. calibree  : sa prediction moyenne tombe sur le taux reel ;
      2. vivante   : ses predictions varient d une situation a l autre ;
      3. utile     : sur ses propres donnees, elle fait mieux que la constante.
    Un echec veut dire un defaut de code, pas un monde difficile : la boucle s ARRETE, et la signature est ecrite."""
    import numpy as np
    mu, _ = monde.predire([{k: e[k] for k in C.ARMES} for e in E], [e["graine"] for e in E], [e["option"] for e in E])
    Y = np.array([e["compromis"] for e in E], dtype=float)
    m = dict(prediction_moyenne=float(mu.mean()), taux_reel=float(Y.mean()), ecart_type=float(mu.std()),
             brier=float(np.mean((mu - Y) ** 2)), brier_constante=float(np.mean((Y.mean() - Y) ** 2)))
    raisons = []
    if abs(m["prediction_moyenne"] - m["taux_reel"]) > C.TOLERANCE_CALIBRATION:
        raisons.append(f"imagination DECALIBREE : predit {m['prediction_moyenne']:.3f} en moyenne pour un taux reel de {m['taux_reel']:.3f}")
    if m["ecart_type"] < C.ECART_MIN_PREDICTIONS:
        raisons.append(f"imagination FIGEE : ecart-type des predictions {m['ecart_type']:.4f}, elle predit la meme chose partout")
    if m["brier"] >= m["brier_constante"]:
        raisons.append(f"imagination INUTILE : Brier {m['brier']:.4f} sur ses propres donnees, pas mieux que la constante ( {m['brier_constante']:.4f} )")
    return not raisons, raisons, m
