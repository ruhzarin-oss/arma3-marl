"""Etape E2 : la bulle. Le cerveau fait vivre le pays ; les habitants presents dans les lieux regardes deviennent des
corps dans Arma, les autres restent des donnees. Le cerveau avance au rythme de l horloge d Arma ( acceleree x4 : une
journee du monde en 6 heures reelles ) : un pas de 10 minutes du monde chaque fois qu Arma les a vecues.
   python -m monde.incarner --regard Kavala --duree 3600 --port 2350 --sortie /mnt/data/hmt/monde/e2
Portes ( ecrites dans plans/plan-monde-complet.md, E2 ) : un habitant n a jamais deux corps ; les corps rapportes par
Arma sont exactement les habitants incarnes par le cerveau ; un habitant desincarne puis reincarne garde son identite."""
import argparse, datetime, json, os, pickle, time, zlib
from . import monde as W, ecole as S, pont as PT, config as C, agents as A

CLASSES = {
    "soldat": ("I_Soldier_F", "ind"), "officier": ("I_officer_F", "ind"), "policier": ("B_GEN_Soldier_F", "ind"),
}
CIVILS = ["C_man_1", "C_man_polo_1_F", "C_man_polo_2_F", "C_man_polo_3_F", "C_man_polo_4_F", "C_man_polo_5_F",
          "C_man_polo_6_F", "C_man_shorts_1_F", "C_man_w_worker_F", "C_scientist_F"]


def classe_de(h):
    if h.role in CLASSES: return CLASSES[h.role]
    return CIVILS[h.id % len(CIVILS)], "civ"


SOIGNANTS = ("medecin", "infirmier")


def cle(h):
    """Le batiment, selon le POSTE et non la ville ( a Kavala, on vit et on travaille dans le meme lieu ) : la maison est
    propre au menage ; le travail est commun a tous ceux du meme role ; l hopital est commun a tous les malades du lieu.
    Point 9 : les soignants travaillent A L HOPITAL - sinon les malades y allaient seuls, sans personne pour les voir."""
    if h.poste == "hopital" or (h.poste == "travail" and h.role in SOIGNANTS):
        return zlib.crc32(f"hopital-{h.lieu.id}".encode()) % 997
    if h.poste == "travail": return zlib.crc32(f"travail-{h.lieu.id}-{h.role}".encode()) % 997
    return zlib.crc32(f"maison-{h.menage.id}".encode()) % 997


def rayon(lieu): return max(150.0, min(450.0, float(lieu.rayon[0] or 300)))


def ile_de(lieu): return getattr(lieu, "ile", "Altis")     # point 13 : chaque lieu appartient a une ile


DEPART = datetime.datetime(*C.DATE_DEPART)


def minutes_arma(date, daytime):
    """Minutes du monde ecoulees depuis le depart, lues sur l horloge d Arma - meme origine que le cerveau.
    Passe les changements de mois : un pays qui vit sept jours peut traverser un 30 ou un 31."""
    jour = datetime.datetime(int(date[0]), int(date[1]), int(date[2]))
    return (jour - DEPART.replace(hour=0, minute=0)).total_seconds() / 60.0 + float(daytime) * 60.0 \
        - (C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4])


def date_du_monde(w):
    """La date d Arma qui correspond a l heure du cerveau - c est elle qu on pose en reprenant un instantane."""
    d = DEPART + datetime.timedelta(minutes=w.minutes - (C.DATE_DEPART[3] * 60 + C.DATE_DEPART[4]))
    return [d.year, d.month, d.day, d.hour, d.minute]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=2350)
    p.add_argument("--regard", default="Kavala")
    p.add_argument("--duree", type=float, default=3600.0, help="secondes reelles")
    p.add_argument("--sortie", default="/mnt/data/hmt/monde/e2")
    p.add_argument("--doctrine", default="", help="doctrine des menages a charger ; ils continuent d apprendre en vivant")
    p.add_argument("--reprendre", action="store_true", help="repartir du dernier instantane du monde ( point 10 )")
    p.add_argument("--iles", default="Altis", help="les iles du monde, separees par des virgules ( point 13 )")
    p.add_argument("--cerveau", default="llm", choices=["llm", "regles"], help="qui gouverne : Qwen ou le catalogue")
    p.add_argument("--eleve", default="llm", choices=["llm", "memoire", "sans_memoire"], help="qui va a l ecole")
    a = p.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    regard = set(a.regard.split(","))
    instantane = os.path.join(a.sortie, "instantane.pkl")
    if a.reprendre and os.path.exists(instantane):
        w = pickle.load(open(instantane, "rb"))
        print(f"monde repris : jour {w.jour}, {w.heure:.2f} h, {sum(1 for h in w.habitants if h.vivant)} vivants", flush=True)
    else:
        eleve = {"llm": S.EleveLLM, "memoire": S.EleveMemoire, "sans_memoire": S.EleveSansMemoire}[a.eleve]()
        w = W.Monde(cerveau=a.cerveau, eleve=eleve, journal=os.path.join(a.sortie, "journal_monde.jsonl"),
                    iles=tuple(a.iles.split(",")))
        print(f"gouvernement : {a.cerveau} | eleve : {eleve.nom}", flush=True)
    if a.doctrine:
        w.doctrine = A.Doctrine.lire(a.doctrine, epsilon=0.05)     # il vit avec ce qu il a appris, et continue d apprendre
        print(f"doctrine chargee : {w.doctrine.n_lecons} lecons", flush=True)
    pont = PT.Pont(a.port)
    trace = open(os.path.join(a.sortie, "trace_e2.jsonl"), "a")
    def noter(**d):
        d["t"] = round(time.time(), 2); trace.write(json.dumps(d, ensure_ascii=False) + "\n"); trace.flush()
    print(f"en attente d Arma sur le port {a.port}", flush=True)
    if not pont.attendre(600): print("Arma ne s est pas connecte"); return 2
    for ile in a.iles.split(","):            # chaque ile doit s etre NOMMEE avant qu on y envoie un corps
        if not pont.attendre(420, ile): print(f"l ile {ile} ne s est pas presentee", flush=True)
    print("iles connectees :", pont.iles(), flush=True)
    t0 = time.time()
    lot_date = pont.envoyer([["date", date_du_monde(w)], ["temps", C.ACCELERATION]])[0]
    incarnes = {}                       # id -> ( lieu, poste ) ou le corps se trouve
    arma = {"minutes": 0.0, "fps": None, "horloge": False, "par_ile": {}}   # l horloge n est crue qu apres l accuse du lot « date »
                                                             # ( sinon un cerveau relance rattraperait l ancienne heure )
    vus = {}                            # ( ile, id ) -> ( instant du dernier rapport, [id, x, y, vivant, vitesse] )
    purges = set()
    sortis = {}                         # id -> instant de desincarnation ( Arma le rapporte encore une seconde ou deux )
    anomalies = {"doublon": 0, "ecart_corps": 0, "orphelins_purges": 0}
    deplacements = [0]

    def synchroniser():
        ordres = []
        voulus = {h.id: h for h in w.habitants if h.vivant and h.lieu is not None and h.lieu.id in regard}
        for i in list(incarnes):
            if i not in voulus:
                ordres.append(["desincarner", i, incarnes[i][2]]); del incarnes[i]; sortis[i] = time.time()
        for i, h in voulus.items():
            ou = (h.lieu.id, h.poste, ile_de(h.lieu))
            if i not in incarnes:
                classe, camp = classe_de(h); purges.discard((ile_de(h.lieu), i))
                ordres.append(["incarner", i, classe, camp, [round(h.lieu.pos[0]), round(h.lieu.pos[1])], rayon(h.lieu), cle(h), ile_de(h.lieu)])
                incarnes[i] = ou
            elif incarnes[i] != ou:
                # dans le regard, un changement de poste du cerveau ( maison -> travail, meme dans une seule ville )
                # devient un deplacement du corps
                if incarnes[i][2] != ile_de(h.lieu):        # il a change d ile : on rend le corps ici, on en cree un la-bas
                    classe, camp = classe_de(h)
                    ordres.append(["desincarner", i, incarnes[i][2]])
                    ordres.append(["incarner", i, classe, camp, [round(h.lieu.pos[0]), round(h.lieu.pos[1])], rayon(h.lieu), cle(h), ile_de(h.lieu)])
                else:
                    ordres.append(["aller", i, [round(h.lieu.pos[0]), round(h.lieu.pos[1])], rayon(h.lieu), cle(h), ile_de(h.lieu)])
                incarnes[i] = ou
                deplacements[0] += 1
        return ordres

    def poster(ordres):
        """Chaque ordre part au serveur de SON ile : un corps ne doit jamais naitre sur deux cartes a la fois.
        Une ile absente n arrete pas le monde : ses habitants restent des donnees, et le cerveau le dit."""
        par_ile = {}
        for o in ordres: par_ile.setdefault(o[-1] if isinstance(o[-1], str) else "Altis", []).append(o[:-1] if isinstance(o[-1], str) else o)
        for ile, lot in par_ile.items():
            if not lot: continue
            try: pont.envoyer(lot, ile)
            except ConnectionError:
                for o in lot:                       # on oublie ce qu on croyait incarne la-bas : il faudra recommencer
                    if o[0] == "incarner" and o[1] in incarnes: del incarnes[o[1]]
                noter(type="ile_absente", ile=ile, ordres=len(lot))

    # le premier lot : tout ce que le regard contient a 6 h
    ordres = synchroniser(); poster(ordres)
    noter(type="depart", incarnes=len(incarnes), ordres=len(ordres))
    dernier_log = 0
    dernier_controle = time.time()
    dernier_jour = w.jour

    def garder():
        """L instantane : le monde entier, doctrine comprise. C est ce qui lui permet de durer au-dela d une soiree."""
        pickle.dump(w, open(instantane + ".tmp", "wb")); os.replace(instantane + ".tmp", instantane)
        if w.doctrine is not None: w.doctrine.ecrire(os.path.join(a.sortie, "doctrine.json"))
        noter(type="instantane", jour=w.jour, heure=round(w.heure, 2), vivants=sum(1 for h in w.habitants if h.vivant))
    while time.time() - t0 < a.duree:
        for ile_msg, m in pont.messages_iles(0.5):
            if not m: continue
            if m[0] == "etat":
                arma["par_ile"][ile_msg] = m[5]        # chaque serveur compte SES corps ; le pays est la somme
                if not arma["horloge"]: continue
                arma["minutes"] = minutes_arma(m[2], m[3]); arma["fps"] = m[4]
                arma["n"] = sum(arma["par_ile"].values())
            elif m[0] == "corps":
                for c in m[1]: vus[(ile_msg, c[0])] = (time.time(), c)
            elif m[0] == "mort":
                noter(type="mort_dans_arma", habitant=m[1])
            elif m[0] == "bonjour":
                arma["par_ile"].pop("inconnue", None)      # il vient de se nommer : son compte anonyme n a plus lieu d etre
                for k in [k for k in vus if k[0] == "inconnue"]: vus.pop(k, None)
                noter(type="bonjour", ile=m[1], detail=m[2:])
            elif m[0] in ("recu", "pret"):
                noter(type=m[0], detail=m[1:])
                if m[0] == "recu" and m[1] >= lot_date: arma["horloge"] = True
                if m[0] == "pret":
                    # « pret » ne sort qu au demarrage d une mission : Arma a redemarre, il n a plus un seul corps.
                    # Le cerveau oublie ce qu il croyait incarne et repeuple, au lieu de parler a des morts.
                    incarnes.clear(); purges.clear(); vus.clear(); arma["horloge"] = False
                    lot_date = pont.envoyer([["date", date_du_monde(w)], ["temps", C.ACCELERATION]])[0]
                    o = synchroniser()
                    if o: poster(o)
                    noter(type="repeuplement", incarnes=len(incarnes), ordres=len(o))
        # la reconciliation : un corps qu Arma rapporte et que le cerveau ne connait pas ( cerveau redemarre, ordre perdu )
        # est desincarne - le cerveau fait foi
        recents = {k for k, (t, _) in vus.items() if time.time() - t < 5}
        # Un corps est orphelin s il est inconnu du cerveau, OU s il se trouve sur une ile ou son habitant n est pas.
        # C est ce second cas qui interdit le doublon : le meme homme avec un corps sur Altis ET sur Malden.
        # un rapport arrive AVANT que le serveur se nomme ne dit pas ou est le corps : on ne purge jamais sur sa foi
        # ( 23/09 : 123 corps supprimes d un coup pour cette raison )
        orphelins = [(ile, i) for ile, i in recents
                     if ile != "inconnue" and (i not in incarnes or incarnes[i][2] != ile)
                     and (ile, i) not in purges and time.time() - sortis.get(i, 0) > 10]
        for ile, i in orphelins:
            try: pont.envoyer([["desincarner", i]], ile)
            except ConnectionError: continue
            purges.add((ile, i))
        if orphelins:
            anomalies["orphelins_purges"] += len(orphelins)
            noter(type="purge", corps=[[ile, i] for ile, i in orphelins][:50], total=len(orphelins))
        # le cerveau rattrape l horloge d Arma, un pas de 10 minutes a la fois
        while arma["minutes"] >= (w.minutes - C.DATE_DEPART[3] * 60 - C.DATE_DEPART[4]) + C.MINUTES_PAR_PAS:
            t_pas = time.time()
            w.pas_suivant()
            if time.time() - t_pas > 2.0:      # un pas long = le LLM a parle ( gouvernement, lecon, exercice )
                noter(type="pas_long", heure=round(w.heure, 2), secondes=round(time.time() - t_pas, 1))
            ordres = synchroniser()
            if ordres: poster(ordres)
        # une ile videe ( serveur redemarre, purge malheureuse ) est REPEUPLEE : le cerveau oublie ce qu il croyait
        # y avoir, et la synchronisation suivante recree les corps
        if time.time() - dernier_controle > 30:
            dernier_controle = time.time()
            for ile, n_ile in arma["par_ile"].items():
                if ile == "inconnue": continue
                crus = [k for k, v in incarnes.items() if v[2] == ile]
                if crus and n_ile == 0:
                    for k in crus: del incarnes[k]
                    noter(type="repeuplement_ile", ile=ile, corps=len(crus))
                    o = synchroniser()
                    if o: poster(o)
        if w.jour != dernier_jour:            # un instantane par jour du monde
            dernier_jour = w.jour; garder()
        if time.time() - dernier_log > 60:
            dernier_log = time.time()
            n_arma = arma.get("n")
            if n_arma is not None and n_arma != len(incarnes): anomalies["ecart_corps"] += 1
            noter(type="bilan", heure_cerveau=round(w.heure, 2), jour=w.jour, minutes_arma=round(arma["minutes"], 1),
                  incarnes=len(incarnes), corps_arma=n_arma, corps_rapportes=len(vus), par_ile=dict(arma["par_ile"]),
                  deplacements=deplacements[0], en_marche=sum(1 for k in recents if vus[k][1][4] > 0), fps=arma["fps"], lots=pont.envoyes, lus=pont.lus,
                  illisibles=pont.illisibles, anomalies=dict(anomalies))
            print(f"{time.strftime('%H:%M:%S')} cerveau jour {w.jour} {w.heure:5.2f} h | Arma {arma['minutes'] / 60 + 6:5.2f} h | "
                  f"incarnes {len(incarnes)} corps {n_arma} | {arma['fps']} images/s | lots {pont.envoyes} | anomalies {anomalies}", flush=True)
    garder()
    noter(type="fin", anomalies=anomalies, incarnes=len(incarnes), jour=w.jour, heure=round(w.heure, 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
