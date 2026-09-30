"""LA RESSEMBLANCE : a quel point le pays simule ressemble a la Grece reelle. Un instrument de mesure, en lecture seule.

Pourquoi un instrument a part plutot que les portes des domaines ? Chaque domaine prouve qu il tient ses propres
comptes ; aucun ne dit si le PAYS, pris en entier, a la forme d un pays reel. Trois defauts connus du monde par defaut
( 12 % de militaires, 1,6 personne par menage, aucun enfant de moins de 6 ans ) n etaient vus par aucune porte.

Trois morceaux :
  - les REFERENCES ( references/grece.json ) : pour chaque indicateur, sa definition exacte, la valeur reelle, l annee,
    la source ( code du jeu de donnees ), l adresse, la bande de tolerance et sa justification. Tout est ecrit AVANT
    de mesurer le monde. Une valeur que personne n a pu lire dans sa source porte « a_verifier » : elle est mesuree et
    affichee, mais ne compte pas dans le score ;
  - les MESURES : une fonction par indicateur, qui lit le monde sans l ecrire ( colonnes du moteur et des domaines,
    comptes du grand livre, series des domaines ) et rend une valeur, ou dit pourquoi elle ne le peut pas
    ( NonMesurable : domaine absent, grandeur non tenue ) ;
  - le JUGEMENT : dans la bande, hors bande, non mesurable ; l ecart en demi-bandes ( 0 = la valeur reelle, 1 = le bord
    de la bande ) ; la surete ( un flux de quelques evenements a un intervalle plus large que sa bande : « fragile » ).

On prefere les RAPPORTS et les PARTS aux montants : le niveau des prix du monde est arbitraire. Un montant ne se
compare qu apres conversion par pays.EUROS_PAR_DRACHME, et la ligne le dit.

Les FLUX ( naissances, deces, admissions, paiements ) sont annualises sur la fenetre de mesure, apres la chauffe :
  - les naissances et les deces se relisent dans les colonnes datees de l etat civil ( naissance_j, deces_j ) ;
  - les paiements et les biens se lisent dans les comptes du jour du grand livre ( p.comptes_hier ), que le livre ne
    garde qu un jour : le `Suivi` les additionne chaque soir, en lecture seule. Sans Suivi, la fenetre des comptes
    est la veille seulement, et la ligne le dit ;
  - les compteurs cumules des domaines se lisent en difference entre le releve du debut ( pris par le Suivi ) et la
    fin ; sans Suivi, depuis l installation.
Les references sont ANNUELLES ; le monde nait le 15 juin ( config.DATE_DEPART ) : une fenetre de 30 jours en ete
surestime ce qui a une saison ( recettes du tourisme, emploi d ete, electricite de la climatisation ). L entete du
tableau donne les dates de la fenetre ; un flux de quelques evenements est marque « fragile » ( intervalle de Poisson
a 95 % ) et le resume donne aussi le score sans les verdicts fragiles.

LECTURE SEULE. Mesurer n ecrit rien dans le monde : aucune affectation dans w ou p, aucun tirage ( p.hasard et
p.du_jour creeraient ou avanceraient un flux ), aucune lecture de `Menage.membres` ( elle reconstruit l index des
menages ). Portes : monde/tests_ressemblance.py ( controle positif synthetique et sur le vrai monde, falsificateur,
determinisme, lecture seule, cout ).

   python -m monde.ressemblance --habitants 10000 --jours 30 --chauffe 5 [--domaines tous] [--etiquette defaut]"""
import argparse, json, math, os, sys, time
import numpy as np
from . import config as C, population as PO

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES = os.path.join(RACINE, "references", "grece.json")
RESULTATS = os.path.join(RACINE, "monde", "resultats")
JOURS_AN = 365.0
DANS, HORS, NON_MESURABLE = "dans la bande", "hors bande", "non mesurable"
Z95 = 1.96


class NonMesurable(Exception):
    """Le monde ne permet pas cette mesure : le domaine n est pas installe, ou il ne tient pas la grandeur."""


# ================================================================== les references
def charger(chemin=None):
    """Les references ( references/grece.json ) : { id : indicateur }, dans l ordre du fichier. Verifie la forme : une
    bande qui ne contient pas sa valeur, ou un indicateur sans source, est refuse ( ValueError )."""
    with open(chemin or REFERENCES, encoding="utf-8") as f: doc = json.load(f)
    refs = {}
    for r in doc["indicateurs"]:
        i = r["id"]
        if i in refs: raise ValueError(f"indicateur en double : {i}")
        for c in ("nom", "theme", "definition", "unite", "valeur", "annee", "source", "adresse", "bande", "justification"):
            if c not in r: raise ValueError(f"{i} : champ {c!r} manquant")
        bas, haut = r["bande"]
        if not bas <= r["valeur"] <= haut: raise ValueError(f"{i} : la bande [{bas} ; {haut}] ne contient pas {r['valeur']}")
        if not bas < haut: raise ValueError(f"{i} : bande vide")
        refs[i] = r
    return refs


# ================================================================== le jugement
def intervalle_poisson(n):
    """Intervalle de score a 95 % d un compte de Poisson de n evenements : n + z2/2 -+ z racine( n + z2/4 )."""
    c = n + Z95 * Z95 / 2.0
    r = Z95 * math.sqrt(n + Z95 * Z95 / 4.0)
    return max(0.0, c - r), c + r


def ecart_en_bandes(v, reel, bas, haut):
    """L ecart signe en demi-bandes : 0 a la valeur reelle, +-1 au bord de la bande ; au-dela de 1, hors bande."""
    if v >= reel: return (v - reel) / (haut - reel) if haut > reel else (0.0 if v == reel else math.inf)
    return -(reel - v) / (reel - bas) if reel > bas else -math.inf


def verdict(v, bas, haut):
    return DANS if bas <= v <= haut else HORS


def juger(refs, valeurs):
    """Confronte des valeurs mesurees aux references. `valeurs` : { id : Mesure ou NonMesurable }. Rend une ligne par
    reference, dans l ordre des references. Une reference sans mesure est non mesurable ( « pas de mesure » )."""
    lignes = []
    for i, r in refs.items():
        bas, haut = r["bande"]
        m = valeurs.get(i)
        l = {"id": i, "nom": r["nom"], "theme": r["theme"], "unite": r["unite"], "reel": r["valeur"],
             "annee": r["annee"], "bande": (bas, haut), "a_verifier": bool(r.get("a_verifier", False)),
             "source": r["source"], "simule": None, "verdict": NON_MESURABLE, "ecart": None, "surete": "",
             "detail": "", "domaine": "", "evenements": None}
        if isinstance(m, NonMesurable) or m is None:
            l["detail"] = str(m) if m is not None else "pas de mesure"
        else:
            l["simule"], l["domaine"], l["detail"], l["evenements"] = m.valeur, m.domaine, m.detail, m.evenements
            if m.valeur is None or not math.isfinite(m.valeur):
                l["verdict"], l["detail"] = NON_MESURABLE, (m.detail + " ; valeur non finie").strip(" ;")
            else:
                l["verdict"] = verdict(m.valeur, bas, haut)
                l["ecart"] = ecart_en_bandes(m.valeur, r["valeur"], bas, haut)
                if m.intervalle is not None:
                    a, b = m.intervalle
                    l["surete"] = "fragile" if verdict(a, bas, haut) != verdict(b, bas, haut) or \
                        (a < bas and b > haut) else "sur"
                    if m.evenements is not None: l["surete"] += f" ( {m.evenements} evenements )"
                if getattr(m, "fragile", None): l["surete"] = f"fragile ( {m.fragile} )"
        lignes.append(l)
    return lignes


def resume(lignes):
    """Le score : les indicateurs confirmes ( sans « a_verifier » ) dans la bande, hors bande, non mesurables."""
    compte = [l for l in lignes if not l["a_verifier"]]
    r = {"dans": sum(1 for l in compte if l["verdict"] == DANS), "hors": sum(1 for l in compte if l["verdict"] == HORS),
         "non_mesurables": sum(1 for l in compte if l["verdict"] == NON_MESURABLE),
         "a_verifier": sum(1 for l in lignes if l["a_verifier"]), "total": len(lignes)}
    r["mesures"] = r["dans"] + r["hors"]
    r["score"] = r["dans"] / r["mesures"] if r["mesures"] else None
    # un verdict « fragile » ( l intervalle a 95 % d un flux compte chevauche un bord ) ne tranche pas : le score sur
    # ne garde que les verdicts surs
    surs = [l for l in compte if l["verdict"] != NON_MESURABLE and not l["surete"].startswith("fragile")]
    r["fragiles"] = r["mesures"] - len(surs)
    r["dans_surs"] = sum(1 for l in surs if l["verdict"] == DANS)
    r["score_sur"] = r["dans_surs"] / len(surs) if surs else None
    return r


# ================================================================== une mesure
class Mesure:
    """Ce que rend la mesure d un indicateur : la valeur ( dans l unite de la reference ), le domaine du monde ou elle
    se lit, une phrase qui dit comment, et pour un flux compte, l intervalle a 95 % et le nombre d evenements.
    `fragile` ( 27/09 ) : la raison pour laquelle la mesure ne tranche pas, quel que soit son intervalle ( une inflation
    annualisee sur moins de 90 jours )."""
    __slots__ = ("valeur", "domaine", "detail", "intervalle", "evenements", "fragile")

    def __init__(self, valeur, domaine, detail="", intervalle=None, evenements=None, fragile=None):
        self.valeur = None if valeur is None else float(valeur)
        self.domaine, self.detail, self.intervalle, self.evenements = domaine, detail, intervalle, evenements
        self.fragile = fragile


# ================================================================== la fenetre, le releve, le suivi
def pas_du_jour(jour):
    """Le monde nait a l aube du jour 0 ( config.DATE_DEPART : 6 h ) et `essais.jours` compte des journees d aube a
    aube : la fenetre qui commence au jour j commence au pas 144 j."""
    return int(jour) * C.PAS_PAR_JOUR


def _a(p, nom): return p is not None and p.a(nom)


def releve(w, p):
    """Les compteurs CUMULES du monde a cet instant ( lecture seule ) : leur difference entre deux releves est un flux.
    Les compteurs des domaines partent de zero a l installation."""
    r = {"pas": int(w.pas), "jour": int(w.jour)}
    if _a(p, "energie"):
        r["servi_kwh"] = math.fsum(float(R.cumul["servi"]) for R in p.domaine("energie").reseaux)
    if _a(p, "transport"):
        r["tues_route"] = float(p.domaine("transport").stats["tues_sur_le_coup"])
    if _a(p, "medecine"):
        r["morts_lesion_route"] = float(p.domaine("medecine").compteurs.get(("deces", "lesion_route"), 0))
    if _a(p, "justice"):
        from .pays import d21_justice as JU
        r["homicides"] = float(p.domaine("justice").vrais[JU.IDX["homicide"]])
    return r


class Suivi:
    """Ce que le grand livre ne garde qu un jour ( p.comptes_hier ) : le Suivi l additionne chaque soir, en LECTURE
    SEULE, et garde le releve du debut de la fenetre. `apres_jour( w, p )` s appelle apres chaque journee
    ( `essais.jours( w, 1 )` ) ; appele deux fois sur la meme cloture, il ne compte qu une fois ; une cloture manquee
    est comptee dans `trous`, et les lignes qui en dependent le disent.
      argent  ( motif, classe du payeur, classe du receveur ) -> drachmes, sur la fenetre
      biens   ( nature, motif, bien ) -> quantite, sur la fenetre
      depart  le releve des compteurs cumules au debut de la fenetre"""
    __slots__ = ("jour_debut", "pas_debut", "clotures", "derniere", "trous", "argent", "biens", "depart")

    def __init__(self, w, p):
        self.jour_debut, self.pas_debut = int(w.jour), int(w.pas)
        self.clotures, self.derniere, self.trous = 0, None, 0
        self.argent, self.biens = {}, {}
        self.depart = releve(w, p)

    def apres_jour(self, w, p):
        c = p.comptes_hier if p is not None else None
        if c is None: return
        jour = int(w.jour)
        if self.derniere is not None and self.derniere[1] is c: return          # meme cloture, deja comptee
        if self.derniere is not None and jour - self.derniere[0] > 1: self.trous += jour - self.derniere[0] - 1
        self.derniere = (jour, c)
        self.clotures += 1
        for m, pa, re, s, _ in c["argent"]:
            k = (m, pa, re); self.argent[k] = self.argent.get(k, 0.0) + float(s)
        for nat, m, b, q in c["biens"]:
            k = (nat, m, b); self.biens[k] = self.biens.get(k, 0.0) + float(q)

    def __getstate__(self):
        return {"jour_debut": self.jour_debut, "pas_debut": self.pas_debut, "clotures": self.clotures,
                "derniere": None if self.derniere is None else (self.derniere[0], None), "trous": self.trous,
                "argent": self.argent, "biens": self.biens, "depart": self.depart}

    def __setstate__(self, d):
        for k, v in d.items(): setattr(self, k, v)


# ================================================================== le contexte d une mesure
class Contexte:
    """Ce que toutes les mesures lisent, calcule une fois : la population vivante, les ages, la fenetre. Rien n est
    ecrit dans le monde ; les tableaux sont des tranches [:n] relues a chaque mesure."""
    __slots__ = ("w", "p", "suivi", "depuis_jour", "pas_debut", "jours", "n", "vivants", "_age", "_flux", "_lignes",
                 "_sect")

    def __init__(self, w, p, depuis_jour=None, suivi=None):
        self.w, self.p, self.suivi = w, p, suivi
        if suivi is not None: self.depuis_jour, self.pas_debut = suivi.jour_debut, suivi.pas_debut
        else:
            self.depuis_jour = int(depuis_jour) if depuis_jour is not None else 0
            self.pas_debut = pas_du_jour(self.depuis_jour)
        self.jours = (int(w.pas) - self.pas_debut) / C.PAS_PAR_JOUR
        tb = w.table
        self.n = n = tb.n
        self.vivants = tb.vivant[:n] == 1
        self._age = self._flux = self._lignes = self._sect = None

    # ---------------------------------------------------------------- outils
    def exiger(self, *domaines):
        for d in domaines:
            if not _a(self.p, d): raise NonMesurable(f"domaine {d} non installe")

    def col(self, entite, nom, n=None):
        """Une colonne d un domaine, tranchee ; NonMesurable si le domaine ne l a pas declaree."""
        cols = self.p.colonnes[entite] if self.p is not None else None
        if cols is None or nom not in cols: raise NonMesurable(f"colonne {entite}.{nom} absente")
        a = cols[nom]
        n = self.n if n is None else n
        if len(a) < n: raise NonMesurable(f"colonne {entite}.{nom} plus courte que la table ( {len(a)} < {n} )")
        return a[:n]

    def population(self): return int(self.vivants.sum())

    def age(self):
        """Age en annees : la date de naissance de l etat civil ( domaine 1 ) quand il est installe, sinon l age du
        moteur ( ce que `population.generer` a pose )."""
        if self._age is None:
            if _a(self.p, "population"):
                self._age = (self.w.jour - self.col("habitant", "naissance_j").astype(np.int64)) / JOURS_AN
            else: self._age = self.w.table.age[:self.n].astype(np.float64)
        return self._age

    def fenetre_ok(self):
        if self.jours <= 0: raise NonMesurable("fenetre de mesure vide ( aucun jour apres la chauffe )")

    def flux_demographiques(self):
        """( naissances, deces ) dates dans la fenetre, et la population moyenne sur la fenetre. Les naissances : des
        habitants nes du domaine 1 ( numero >= la population du recensement ) dont la date de naissance est dans la
        fenetre ; les deces : la date de deces de l etat civil, sans les emigres. La population du debut se reconstruit par
        fin - naissances + deces ( + emigres - immigres du domaine 7 ) : la moyenne est celle des deux bouts."""
        if self._flux is None:
            self.exiger("population")
            d0 = self.depuis_jour
            nj = self.col("habitant", "naissance_j"); dj = self.col("habitant", "deces_j")
            ids = np.arange(self.n)
            n0 = int(self.p.domaine("population").vivants_depart)
            nes = int(((nj >= d0) & (ids >= n0)).sum())
            mig = 0
            if _a(self.p, "exterieur"):
                em = self.col("habitant", "ext_emigre_j"); im = self.col("habitant", "ext_immigre_j")
                mig = int((em >= d0).sum()) - int((im >= d0).sum())
                # un emigre n est pas mort : le domaine 7 lui pose deces_j au jour de sa SORTIE ( pour que le domaine 1
                # ne le reprenne pas ) ; le compter doublait la mortalite ( 27/09 : 16 emigres sur 27 « deces » )
                morts = int(((dj >= d0) & (em < 0)).sum())
            else:
                morts = int((dj >= d0).sum())
            fin = self.population()
            debut = fin - nes + morts + mig
            self._flux = (nes, morts, 0.5 * (debut + fin))
        return self._flux

    def personnes_annees(self):
        self.fenetre_ok()
        return self.flux_demographiques()[2] * self.jours / JOURS_AN

    def pop_moyenne(self):
        """La population moyenne de la fenetre si l etat civil la donne, sinon celle d aujourd hui."""
        if _a(self.p, "population"): return self.flux_demographiques()[2]
        return float(self.population())

    def compteur(self, cle):
        """La difference d un compteur cumule sur la fenetre ( releve du Suivi ), ou depuis l installation sans
        Suivi. Rend ( valeur, jours de la fenetre, phrase )."""
        fin = releve(self.w, self.p)
        if cle not in fin: raise NonMesurable(f"compteur {cle} absent")
        if self.suivi is not None and cle in self.suivi.depart:
            return fin[cle] - self.suivi.depart[cle], self.jours, "sur la fenetre"
        return fin[cle], self.w.pas / C.PAS_PAR_JOUR, "depuis l installation ( pas de Suivi )"

    def lignes(self):
        """Les lignes d argent de la fenetre : celles du Suivi, sinon la veille seulement ( p.comptes_hier ). Rend
        ( { ( motif, payeur, receveur ) : drachmes }, nombre de clotures, phrase )."""
        if self._lignes is None:
            if self.suivi is not None:
                if self.suivi.clotures == 0: raise NonMesurable("Suivi sans aucune cloture")
                self._lignes = (self.suivi.argent, self.suivi.clotures,
                                f"{self.suivi.clotures} clotures du grand livre"
                                + (f", {self.suivi.trous} manquees" if self.suivi.trous else ""))
            else:
                c = self.p.comptes_hier if self.p is not None else None
                if c is None: raise NonMesurable("aucune cloture du grand livre ( ni Suivi ni comptes de la veille )")
                a = {}
                for m, pa, re, s, _ in c["argent"]: a[(m, pa, re)] = a.get((m, pa, re), 0.0) + float(s)
                self._lignes = (a, 1, "la veille seulement ( pas de Suivi )")
        return self._lignes

    def secteurs(self):
        if self._sect is None:
            s = {f.classe: f.secteur for f in self.p.socle.registre.familles.values() if f.classe}
            s["Exterieur"], s["Emission"] = "exterieur", "emission"
            self._sect = s
        return self._sect

    def nature(self, motif):
        m = self.p.socle.livre.motifs.get(motif)
        return m.nature if m is not None else "non_declare"


def _taux_poisson(k, expo, par, dom, quoi):
    """Un flux de k evenements sur `expo` personnes-annees, pour `par` habitants, avec son intervalle a 95 %."""
    if expo <= 0: raise NonMesurable("exposition nulle")
    a, b = intervalle_poisson(k)
    return Mesure(k / expo * par, dom, f"{k} {quoi} sur {expo:.1f} personnes-annees",
                  (a / expo * par, b / expo * par), k)


def _part(num, den):
    if den <= 0: raise NonMesurable("denominateur nul")
    return 100.0 * num / den


# ================================================================== les mesures, une par indicateur
MESURES = {}      # id -> fonction( contexte ) -> Mesure ( ou NonMesurable levee )


def mesure(ident):
    def poser(f):
        if ident in MESURES: raise ValueError(f"mesure en double : {ident}")
        MESURES[ident] = f
        return f
    return poser


def _role(nom): return PO.CODE_ROLE[nom]


def _en_poste(x, *roles):
    """Les vivants qui exercent l un de ces metiers du moteur ( un lieu de travail : un licencie ou un detenu garde
    son role mais perd son lieu )."""
    tb = x.w.table
    r = tb.role[:x.n]
    m = np.zeros(x.n, bool)
    for nom in roles: m |= r == _role(nom)
    return x.vivants & m & (tb.travail[:x.n] >= 0)


# ---------------------------------------------------------------- demographie
def _part_age(x, bas, haut):
    age = x.age()
    v = x.vivants
    src = "etat civil ( naissance_j )" if _a(x.p, "population") else "age du moteur"
    return Mesure(_part(int((v & (age >= bas) & (age < haut)).sum()), int(v.sum())),
                  "population" if _a(x.p, "population") else "moteur", f"vivants ; {src}")


@mesure("part_0_14")
def _mesure_part_0_14(x): return _part_age(x, 0.0, 15.0)


@mesure("part_15_64")
def _mesure_part_15_64(x): return _part_age(x, 15.0, 65.0)


@mesure("part_65_plus")
def _mesure_part_65_plus(x): return _part_age(x, 65.0, math.inf)


@mesure("part_moins_5")
def _mesure_part_moins_5(x): return _part_age(x, 0.0, 5.0)


@mesure("age_median")
def _mesure_age_median(x):
    a = x.age()[x.vivants]
    if not a.size: raise NonMesurable("aucun vivant")
    return Mesure(float(np.median(a)), "population" if _a(x.p, "population") else "moteur", "mediane des ages des vivants")


@mesure("rapport_masculinite")
def _mesure_rapport_masculinite(x):
    x.exiger("population")
    s = x.col("habitant", "sexe")[x.vivants]
    h, f = int((s == 1).sum()), int((s == 0).sum())
    if f == 0: raise NonMesurable("aucune femme")
    return Mesure(100.0 * h / f, "population", f"{h} hommes, {f} femmes vivants")


@mesure("taille_menages")
def _mesure_taille_menages(x):
    m = PO.menages_inscrits(x.w.table, x.n)[x.vivants]
    m = m[m >= 0]
    if not m.size: raise NonMesurable("aucun menage habite")
    habites = int((np.bincount(m) > 0).sum())
    return Mesure(m.size / habites, "moteur", f"{m.size} vivants dans {habites} menages habites ( au moins un vivant )")


@mesure("natalite")
def _mesure_natalite(x):
    nes, _, _ = x.flux_demographiques()
    return _taux_poisson(nes, x.personnes_annees(), 1000.0, "population", "naissances")


@mesure("mortalite")
def _mesure_mortalite(x):
    _, morts, _ = x.flux_demographiques()
    return _taux_poisson(morts, x.personnes_annees(), 1000.0, "population", "deces ( toutes causes )")


@mesure("deces_faim")
def _mesure_deces_faim(x):
    """27/09 ( HMT-129 ) : les morts de faim ( cause « faim » de l etat civil, domaine 1 ) dates dans la fenetre, pour
    100 000 habitants par an. Un emigre n est pas mort ( le domaine 7 lui pose deces_j sans cause ) ; une mort naturelle
    n est pas une mort de faim. L indicateur de la faim du moteur ne compte que les VIVANTS : deux iles de la guerre ont
    perdu presque toute leur population par la faim pendant qu il baissait."""
    x.exiger("population")
    from .pays import d01_population as D1
    dj = x.col("habitant", "deces_j"); cd = x.col("habitant", "cause_deces")
    m = (dj >= x.depuis_jour) & (cd == D1.CAUSES.index("faim"))
    if _a(x.p, "exterieur"): m &= x.col("habitant", "ext_emigre_j") < 0
    return _taux_poisson(int(m.sum()), x.personnes_annees(), 1e5, "population", "morts de faim ( cause faim, domaine 1 )")


@mesure("population_rapport")
def _mesure_population_rapport(x):
    """27/09 ( HMT-129 ) : les vivants sur les vivants de la naissance du monde ( domaine 1, vivants_depart ), sur toute
    la vie du monde ( chauffe comprise ) : ramene a un an quand le monde a plus d un an, brut sinon ( la bande d une
    annee contient a fortiori le rapport reel sur moins d un an : elle contient 1 ). Une ile qui meurt de faim ou se
    vide le montre, meme quand ses vivants n ont plus faim."""
    x.exiger("population")
    v0 = int(x.p.domaine("population").vivants_depart)
    if v0 <= 0: raise NonMesurable("aucun vivant a la naissance du monde")
    j = x.w.pas / C.PAS_PAR_JOUR
    r = x.population() / v0
    v = r ** (JOURS_AN / j) if j > JOURS_AN else r
    return Mesure(v, "population", f"{x.population()} vivants pour {v0} a la naissance du monde, en {j:.0f} jours "
                  f"( rapport brut {r:.4f}{'' if j <= JOURS_AN else ', ramene a un an'} ) ; emigres et morts comptent")


def _migrants(x, colonne, quoi):
    x.exiger("population", "exterieur")
    k = int((x.col("habitant", colonne) >= x.depuis_jour).sum())
    return _taux_poisson(k, x.personnes_annees(), 100.0, "exterieur", quoi)


@mesure("taux_emigration")
def _mesure_taux_emigration(x):
    return _migrants(x, "ext_emigre_j", "emigres ( domaine 7, ext_emigre_j ), mineurs compris")


@mesure("taux_immigration")
def _mesure_taux_immigration(x):
    return _migrants(x, "ext_immigre_j", "immigres ( domaine 7, ext_immigre_j ), mineurs compris")


# ---------------------------------------------------------------- travail
def _statuts(x):
    x.exiger("travail")
    from .pays import d04_travail as TR
    return TR, x.col("habitant", "tr_statut")


@mesure("taux_emploi_20_64")
def _mesure_taux_emploi_20_64(x):
    TR, st = _statuts(x)
    age = x.age()
    m = x.vivants & (age >= 20) & (age < 65)
    e = int((m & np.isin(st, TR.EN_EMPLOI)).sum())
    return Mesure(_part(e, int(m.sum())), "travail", f"{e} en emploi ( salarie, fonctionnaire, independant ) sur "
                  f"{int(m.sum())} vivants de 20-64 ans ; les militaires comptent en emploi")


@mesure("chomage_15_74")
def _mesure_chomage_15_74(x):
    TR, st = _statuts(x)
    age = x.age()
    m = x.vivants & (age >= 15) & (age < 75)
    e = int((m & np.isin(st, TR.EN_EMPLOI)).sum()); c = int((m & (st == TR.CHOMEUR)).sum())
    return Mesure(_part(c, e + c), "travail", f"{c} chomeurs ( statut CHOMEUR ) sur {e + c} actifs de 15-74 ans")


def _emploi(x):
    TR, st = _statuts(x)
    return x.vivants & np.isin(st, TR.EN_EMPLOI)


@mesure("part_emploi_public")
def _mesure_part_emploi_public(x):
    e = _emploi(x)
    pub = int((e & (x.w.table.public[:x.n] == 1)).sum())
    return Mesure(_part(pub, int(e.sum())), "travail", f"{pub} en emploi dans un metier public du moteur "
                  f"( config.ROLES ) sur {int(e.sum())} en emploi")


@mesure("part_emploi_agricole")
def _mesure_part_emploi_agricole(x):
    e = _emploi(x)
    a = int((e & (x.w.table.role[:x.n] == _role("paysan"))).sum())
    return Mesure(_part(a, int(e.sum())), "travail", f"{a} paysans en emploi sur {int(e.sum())}")


@mesure("part_emploi_hebergement")
def _mesure_part_emploi_hebergement(x):
    x.exiger("tourisme")
    e = _emploi(x)
    a = int((e & (x.w.table.role[:x.n] == _role("hotellerie"))).sum())
    return Mesure(_part(a, int(e.sum())), "tourisme", f"{a} en emploi dans l hotellerie sur {int(e.sum())}")


@mesure("part_militaires")
def _mesure_part_militaires(x):
    if _a(x.p, "armee"):
        k = int((x.vivants & (x.col("habitant", "ar_rang") >= 0)).sum())
        return Mesure(_part(k, x.population()), "armee", f"{k} vivants aux effectifs de l armee ( ar_rang ) sur "
                      f"{x.population()}")
    tb = x.w.table
    k = int((x.vivants & np.isin(tb.role[:x.n], (_role("soldat"), _role("officier")))).sum())
    return Mesure(_part(k, x.population()), "moteur", f"{k} soldats et officiers du moteur sur {x.population()}")


@mesure("kaitz")
def _mesure_kaitz(x):
    TR, st = _statuts(x)
    tb = x.w.table
    sal = x.vivants & np.isin(st, TR.PAYES_A_L_HEURE)
    if not sal.any(): raise NonMesurable("aucun salarie")
    f = np.where(tb.public[:x.n][sal] == 1, float(x.w.gouv.facteur_salaire_public), 1.0)
    taux = x.col("habitant", "tr_taux")[sal] * f
    med = float(np.median(taux))
    if med <= 0: raise NonMesurable("salaire median nul")
    return Mesure(100.0 * TR.SMIC_HORAIRE / med, "travail", f"SMIC horaire brut {TR.SMIC_HORAIRE:.2f} dr sur le taux "
                  f"horaire brut median de {int(sal.sum())} salaries et fonctionnaires ( {med:.2f} dr )")


@mesure("part_retraites")
def _mesure_part_retraites(x):
    x.exiger("travail")
    v = x.w.table.vivant
    k = sum(1 for h, pn in x.p.domaine("travail").pensions.items()
            if pn.nature in ("vieillesse", "non_assure") and h < x.n and v[h] == 1)
    return Mesure(_part(k, x.population()), "travail", f"{k} vivants titulaires d une pension de vieillesse "
                  f"( ou de l allocation des non-assures ) sur {x.population()}")


# ---------------------------------------------------------------- economie
def _pib(x):
    """Le PIB de la fenetre ( comptes nationaux du domaine 6, par la depense ) : la somme des comptes du jour dont la
    cloture tombe dans la fenetre ( la cloture du jour J porte l etiquette J+1 ). Rend ( somme des comptes, nombre de
    jours ) ; avec un Suivi, la meme fenetre que ses lignes."""
    x.exiger("etat")
    st = x.p.domaine("etat").stat
    c = [cn for j, cn in st.comptes if x.depuis_jour < j <= x.w.jour]
    if not c:
        if not st.comptes: raise NonMesurable("aucun compte national publie")
        c = [st.comptes[-1][1]]
    tot = {}
    for cn in c:
        for k, v in cn.items(): tot[k] = tot.get(k, 0.0) + float(v)
    if tot.get("pib", 0.0) <= 0: raise NonMesurable("PIB nul ou negatif sur la fenetre")
    return tot, len(c)


def _ratio_pib(x, num, k_num, quoi):
    """Un flux de la fenetre ( k_num clotures ) rapporte au PIB de la fenetre ( k_pib jours ), en % du PIB."""
    tot, k_pib = _pib(x)
    pib = tot["pib"] * k_num / k_pib
    return 100.0 * num / pib, f"{quoi} / PIB ( {k_pib} jours de comptes nationaux )"


@mesure("importations_pib")
def _mesure_importations_pib(x):
    tot, k = _pib(x)
    return Mesure(100.0 * tot["importations"] / tot["pib"], "exterieur",
                  f"importations des comptes nationaux ( domaine 6 ) / PIB, {k} jours")


@mesure("exportations_pib")
def _mesure_exportations_pib(x):
    tot, k = _pib(x)
    return Mesure(100.0 * tot["exportations"] / tot["pib"], "exterieur",
                  f"exportations des comptes nationaux ( domaine 6 ) / PIB, {k} jours")


@mesure("pib_par_habitant")
def _mesure_pib_par_habitant(x):
    from .pays.pays import EUROS_PAR_DRACHME
    tot, k = _pib(x)
    pib_an = tot["pib"] * JOURS_AN / k
    return Mesure(pib_an / x.pop_moyenne() * EUROS_PAR_DRACHME, "etat",
                  f"PIB annualise ( {k} jours ) par habitant, converti a {EUROS_PAR_DRACHME} euro la drachme "
                  f"( pays.EUROS_PAR_DRACHME ) : un MONTANT, le niveau des prix du monde est un choix de calibrage")


@mesure("dette_publique_pib")
def _mesure_dette_publique_pib(x):
    x.exiger("etat", "banques")
    from .pays import d06_etat as ET
    tot, k = _pib(x)
    return Mesure(100.0 * ET.dette_nominale(x.p) / (tot["pib"] * JOURS_AN / k), "etat",
                  f"dette nominale ( Maastricht, domaine 6 ) / PIB annualise sur {k} jours")


ADMIN = "administrations"


def _finances_publiques(x):
    """Recettes fiscales et depense publique des administrations CONSOLIDEES, sur les lignes du grand livre :
      - recettes = impots sur la production, impots sur le revenu et cotisations recus par une administration d un
        autre secteur, moins les impots sur le revenu rendus ; plus les cotisations qu une administration verse a une
        autre pour ses propres agents ( la part salariale et patronale d un fonctionnaire : dans le SEC, elles
        passent par le salaire brut ) ;
      - depense = tout ce qu une administration paie a un autre secteur, hors financier et illegal ; plus ces memes
        cotisations ( elles sont une part de la remuneration des agents ). Les transferts entre administrations se
        consolident."""
    x.exiger("etat")
    a, k, phrase = x.lignes()
    sect = x.secteurs()
    rec = dep = 0.0
    for (m, pa, re), s in a.items():
        if pa == re: continue
        nat = x.nature(m)
        spa, sre = sect.get(pa, "inconnu"), sect.get(re, "inconnu")
        if nat in ("financier", "illegal"): continue
        if spa == ADMIN and sre == ADMIN:
            if nat == "cotisation": rec += s; dep += s
            continue
        if sre == ADMIN and nat in ("impot_production", "impot_revenu", "cotisation"): rec += s
        if spa == ADMIN:
            dep += s
            if nat == "impot_revenu": rec -= s
    return rec, dep, k, phrase


@mesure("recettes_fiscales_pib")
def _mesure_recettes_fiscales_pib(x):
    rec, _, k, phrase = _finances_publiques(x)
    v, d = _ratio_pib(x, rec, k, "impots et cotisations recus par les administrations")
    return Mesure(v, "etat", f"{d} ; {phrase}")


@mesure("depense_publique_pib")
def _mesure_depense_publique_pib(x):
    _, dep, k, phrase = _finances_publiques(x)
    v, d = _ratio_pib(x, dep, k, "depense consolidee des administrations ( hors financier )")
    return Mesure(v, "etat", f"{d} ; {phrase}")


@mesure("recettes_tourisme_pib")
def _mesure_recettes_tourisme_pib(x):
    x.exiger("tourisme")
    a, k, phrase = x.lignes()
    r = math.fsum(s for (m, pa, re), s in a.items() if m == "recette_touristique" and pa == "Exterieur")
    v, d = _ratio_pib(x, r, k, "recettes touristiques venues de l exterieur ( motif recette_touristique )")
    return Mesure(v, "tourisme", f"{d} ; {phrase}")


# Les postes du budget des menages : motifs d achat payes par un menage. Hors consommation : l achat d un logement,
# d un terrain, les travaux ( formation de capital ), et ce qui n est pas un achat ( impots, primes, cotisations ).
HORS_CONSOMMATION = ("vente_logement", "frais_transaction", "vente_terrain", "travaux", "second_oeuvre", "achat_abri",
                     "import_materiaux", "investissement", "cession_liquidation", "droits_mutation")
POSTES = {"alimentation": ("nourriture",),
          "logement": ("loyer", "facture_electricite", "facture_eau"),
          "transport": ("carburant", "carburant_station", "entretien_vehicule", "reparation_vehicule", "vente_vehicule",
                        "reprise_vehicule", "lecons_conduite")}
BIENS_DES_MARCHES = ("nourriture", "carburant", "remedes", "outils")


def _budget(x):
    """Les depenses de consommation des menages sur la fenetre, par poste : les achats d un menage a un autre
    secteur, plus les loyers d un menage a un autre ( un loyer est une consommation, meme entre menages ). La TVA des
    menages tombe sous un seul motif ; elle est repartie au prorata de leurs achats aux marches, seuls a la porter
    a part ( les autres prix sont TTC )."""
    x.exiger("economie")
    a, k, phrase = x.lignes()
    conso, par_motif, tva = 0.0, {}, 0.0
    for (m, pa, re), s in a.items():
        if pa != "Menage": continue
        if m == "tva": tva += s; continue
        if x.nature(m) != "achat" or m in HORS_CONSOMMATION: continue
        if re == "Menage" and m != "loyer": continue
        par_motif[m] = par_motif.get(m, 0.0) + s
        conso += s
    marches = math.fsum(s for (m, pa, re), s in a.items() if pa == "Menage" and re == "Marche" and m in BIENS_DES_MARCHES)
    for m in BIENS_DES_MARCHES:
        if marches > 0:
            q = math.fsum(s for (mo, pa, re), s in a.items() if mo == m and pa == "Menage" and re == "Marche")
            par_motif[m] = par_motif.get(m, 0.0) + tva * q / marches
    conso += tva
    if conso <= 0: raise NonMesurable("aucune depense de consommation des menages")
    return par_motif, conso, phrase


def _poste(x, nom):
    par_motif, conso, phrase = _budget(x)
    v = math.fsum(par_motif.get(m, 0.0) for m in POSTES[nom])
    return Mesure(100.0 * v / conso, "economie", f"motifs {', '.join(POSTES[nom])} / consommation des menages "
                  f"( TVA comprise ) ; {phrase}")


@mesure("part_alimentation")
def _mesure_part_alimentation(x): return _poste(x, "alimentation")


@mesure("part_logement")
def _mesure_part_logement(x): return _poste(x, "logement")


@mesure("part_transport")
def _mesure_part_transport(x): return _poste(x, "transport")


@mesure("taux_epargne")
def _mesure_taux_epargne(x):
    """Revenu disponible brut des menages = remunerations, revenus de la propriete, prestations et transferts courants
    recus d un autre secteur, plus les loyers recus d autres menages ; moins les impots sur le revenu et le patrimoine,
    les cotisations, les transferts courants et les interets verses. Consommation : comme les postes du budget.
    Epargne = revenu disponible - consommation ; taux = epargne / revenu disponible."""
    x.exiger("economie")
    a, k, phrase = x.lignes()
    rdb = 0.0
    for (m, pa, re), s in a.items():
        nat = x.nature(m)
        if re == "Menage" and pa != "Menage" and nat in ("remuneration", "revenu_propriete", "prestation",
                                                         "transfert_courant", "impot_revenu"):
            rdb += s                           # impot_revenu recu : un remboursement
        elif pa == "Menage" and re != "Menage" and nat in ("impot_revenu", "cotisation", "transfert_courant",
                                                           "revenu_propriete"):
            rdb -= s
        elif pa == "Menage" and re == "Menage" and m == "loyer":
            rdb += s
    _, conso, _ = _budget(x)
    if rdb <= 0: raise NonMesurable(f"revenu disponible des menages non positif ( {rdb:.0f} dr )")
    return Mesure(100.0 * (rdb - conso) / rdb, "economie", f"( revenu disponible - consommation ) / revenu disponible ;"
                  f" {phrase}")


# 27/09 ( HMT-128 ) : l indice du monde bouge de ~0,5 % par jour ( ecart-type des variations journalieres du log, pays
# grec et Stratis, jours 40 a 240 ) ; annualisee sur 30 jours, l inflation de fenetres voisines va de -60 a +125 % par an.
# Elle se mesure sur 90 jours au moins ; entre 30 et 90 jours, elle est rendue mais dite fragile ; sous 30 jours, non
# mesurable. L intervalle a 95 % : l indice est une marche au hasard avec derive, lue par semaines entieres ( les
# variations d une semaine absorbent le cycle du marche ferme le dimanche et la correlation d un jour a l autre ).
INFLATION_FENETRE_J = 90
INFLATION_MIN_J = 30


def inflation_annuelle(v, k):
    """( taux annualise en % par an, intervalle a 95 %, ecart-type d une semaine ) de l indice `v` sur ses k derniers
    jours ( k + 1 valeurs ). Le point : ( dernier / premier ) ^ ( 365 / k ) - 1. L intervalle : les variations du log
    sur des semaines entieres, sans chevauchement, comptees depuis la fin ; la derive d une semaine a l ecart-type
    s / racine( semaines ) ; annualisee, exp( 365 / 7 x ( m +- 1,96 s / racine semaines ) ) - 1, centree sur le point."""
    x = np.log(np.asarray(list(v)[len(v) - 1 - k:], np.float64))     # l indice du domaine 2 est une deque
    taux = 100.0 * math.expm1((x[-1] - x[0]) * JOURS_AN / k)
    sem = x[::-1][::7][::-1]                        # une valeur par semaine, la derniere comprise
    d = np.diff(sem)
    if d.size < 2: return taux, None, None
    s = float(d.std(ddof=1))
    m = (x[-1] - x[0]) / k * 7.0
    e = Z95 * s / math.sqrt(d.size)
    return taux, (100.0 * math.expm1((m - e) * JOURS_AN / 7.0), 100.0 * math.expm1((m + e) * JOURS_AN / 7.0)), s


@mesure("inflation")
def _mesure_inflation(x):
    """L indice des prix de la banque centrale ( domaine 2 : prix affiches des marches, TVA comprise ; une valeur
    chaque matin a 6 h 10 ), entre le dernier matin avant la fenetre et le dernier matin de la fenetre, annualise ;
    l intervalle et la fenetre minimale : voir INFLATION_FENETRE_J."""
    x.exiger("banques")
    v = x.p.domaine("banques").bc.indice.valeurs
    k = int(round(x.jours))
    if k < INFLATION_MIN_J:
        raise NonMesurable(f"fenetre de {k} jours : sous {INFLATION_MIN_J} jours, annualiser multiplie le bruit de l indice "
                           f"( ~0,5 % par jour ) par plus de 12 ; mesurer sur {INFLATION_FENETRE_J} jours au moins")
    if len(v) <= k: raise NonMesurable(f"indice trop court ( {len(v)} valeurs pour {k} jours )")
    taux, ic, s = inflation_annuelle(v, k)
    a, b = v[-1 - k], v[-1]
    fr = None if k >= INFLATION_FENETRE_J else (f"fenetre de {k} jours, sous {INFLATION_FENETRE_J} : l annualisation "
                                                 f"amplifie le bruit de l indice")
    d = (f"indice {a:.2f} -> {b:.2f} en {k} jours, annualise ( panier de 4 biens des marches )"
         + ("" if ic is None else f" ; intervalle a 95 % [{ic[0]:.1f} ; {ic[1]:.1f}] ( marche au hasard, semaines entieres )"))
    return Mesure(taux, "banques", d, ic, fragile=fr)


# ---------------------------------------------------------------- sante
@mesure("lits_hopital")
def _mesure_lits_hopital(x):
    x.exiger("hopitaux")
    E = [e for e in x.p.domaine("hopitaux").etabs if e.ouvert]
    lits = sum(len(e.lits_occ) + len(e.rea_occ) for e in E)
    rea = sum(len(e.rea_occ) for e in E)
    mil = [e for e in E if e.type == "militaire"]
    lm = sum(len(e.lits_occ) + len(e.rea_occ) for e in mil)
    return Mesure(1000.0 * lits / x.population(), "hopitaux",
                  f"{lits} lits de {len(E)} etablissements ouverts, dont {rea} de reanimation et {lm} dans "
                  f"{len(mil)} hopitaux militaires ( sans eux : {1000.0 * (lits - lm) / x.population():.2f} )")


@mesure("medecins")
def _mesure_medecins(x):
    k = int(_en_poste(x, "medecin").sum())
    return Mesure(1000.0 * k / x.population(), "hopitaux" if _a(x.p, "hopitaux") else "moteur",
                  f"{k} medecins en poste ( role du moteur )")


@mesure("infirmiers")
def _mesure_infirmiers(x):
    k = int(_en_poste(x, "infirmier").sum())
    return Mesure(1000.0 * k / x.population(), "hopitaux" if _a(x.p, "hopitaux") else "moteur",
                  f"{k} infirmiers en poste ( role du moteur )")


@mesure("hospitalisations")
def _mesure_hospitalisations(x):
    """Les sejours hospitaliers ( passages admis en lit ) arrives dans la fenetre : clos ( historique ) ou en cours."""
    x.exiger("hopitaux")
    H = x.p.domaine("hopitaux")
    p0 = x.pas_debut
    k = sum(1 for t in H.historique if t[11] and t[7] >= p0)
    k += sum(1 for ps in H.actifs.values() if ps.admis and ps.t_arrivee >= p0)
    return _taux_poisson(k, x.personnes_annees(), 1000.0, "hopitaux", "sejours admis")


# ---------------------------------------------------------------- transport
@mesure("voitures")
def _mesure_voitures(x):
    x.exiger("transport")
    from .pays import d14_transport as TP
    M = x.w.table.menages.n
    mi = PO.menages_inscrits(x.w.table, x.n)
    nv = np.bincount(mi[x.vivants & (mi >= 0)], minlength=M)[:M]
    hab = (nv > 0) & (x.col("menage", "dissous", M) == 0) if "dissous" in x.p.colonnes["menage"] else nv > 0
    k = 0
    for j in range(3):
        m = x.col("menage", f"vh_m{j}", M).astype(np.int64)
        k += int((hab & (m >= 0) & TP.IS_VOITURE[np.maximum(m, 0)]).sum())
    return Mesure(1000.0 * k / x.population(), "transport",
                  f"{k} voitures des menages habites ( les flottes d entreprise ne sont pas comptees )")


@mesure("morts_route")
def _mesure_morts_route(x):
    x.exiger("transport")
    k, j, ou = x.compteur("tues_route")
    k2 = 0.0
    if _a(x.p, "medecine"): k2, _, _ = x.compteur("morts_lesion_route")
    n = int(round(k + k2))
    expo = x.pop_moyenne() * j / JOURS_AN
    m = _taux_poisson(n, expo, 1e6, "transport", "morts de la route ( sur le coup et des suites a l hopital )")
    m.detail += f", {ou}"
    return m


# ---------------------------------------------------------------- energie, education, justice, politique, logement
@mesure("electricite_par_habitant")
def _mesure_electricite_par_habitant(x):
    x.exiger("energie")
    kwh, j, ou = x.compteur("servi_kwh")
    if j <= 0: raise NonMesurable("fenetre vide")
    return Mesure(kwh / x.pop_moyenne() * JOURS_AN / j, "energie",
                  f"{kwh:.0f} kWh servis par les reseaux ( tous usages finals, hors pertes ), annualises, {ou}")


@mesure("eleves_par_enseignant")
def _mesure_eleves_par_enseignant(x):
    x.exiger("education")
    c = x.col("habitant", "ed_cycle")
    el = int((x.vivants & (c >= 1) & (c <= 5)).sum())
    ens = int(_en_poste(x, "enseignant").sum())
    if ens == 0: raise NonMesurable("aucun enseignant en poste")
    return Mesure(el / ens, "education", f"{el} eleves de la maternelle au lycee ( ed_cycle 1-5 ) pour {ens} "
                  f"enseignants en poste")


@mesure("detenus")
def _mesure_detenus(x):
    x.exiger("justice")
    k = int((x.vivants & (x.col("habitant", "ju_detenu") > 0)).sum())
    return Mesure(1e5 * k / x.population(), "justice", f"{k} detenus vivants ( provisoires et condamnes )")


@mesure("policiers")
def _mesure_policiers(x):
    k = int(_en_poste(x, "policier").sum())
    return Mesure(1e5 * k / x.population(), "justice" if _a(x.p, "justice") else "moteur",
                  f"{k} policiers en poste ( role du moteur )")


@mesure("homicides")
def _mesure_homicides(x):
    x.exiger("justice")
    k, j, ou = x.compteur("homicides")
    m = _taux_poisson(int(round(k)), x.pop_moyenne() * j / JOURS_AN, 1e5, "justice", "homicides ( verite du domaine )")
    m.detail += f", {ou}"
    return m


@mesure("participation_electorale")
def _mesure_participation_electorale(x):
    x.exiger("politique")
    d = x.p.domaine("politique")
    if not d.scrutins:
        raise NonMesurable(f"aucun scrutin tenu depuis l installation ( prochain prevu au jour {d.prochaine} )")
    s = d.scrutins[-1]
    ins = int(s.inscrits.sum())
    if ins == 0: raise NonMesurable("scrutin sans inscrits")
    return Mesure(100.0 * int(s.votants.sum()) / ins, "politique", f"dernier scrutin ( jour {s.jour} ) : votants / inscrits")


@mesure("part_proprietaires")
def _mesure_part_proprietaires(x):
    x.exiger("immobilier")
    M = x.w.table.menages.n
    mi = PO.menages_inscrits(x.w.table, x.n)
    nv = np.bincount(mi[x.vivants & (mi >= 0)], minlength=M)[:M]
    hab = (nv > 0) & (x.col("menage", "dissous", M) == 0)
    pr = hab & (x.col("menage", "im_statut", M) == 1)
    return Mesure(_part(int(nv[pr].sum()), int(nv[hab].sum())), "immobilier",
                  "personnes des menages proprietaires de leur logement / personnes des menages habites")


# ================================================================== mesurer, juger, afficher
def valeurs(w, p, depuis_jour=None, suivi=None, ids=None):
    """{ id : Mesure ou NonMesurable } pour chaque mesure connue ( ou celles de `ids` ). Lecture seule."""
    x = Contexte(w, p, depuis_jour, suivi)
    out = {}
    for i, f in MESURES.items():
        if ids is not None and i not in ids: continue
        try: out[i] = f(x)
        except NonMesurable as e: out[i] = e
    return out


def mesurer(w, p, depuis_jour=None, suivi=None, refs=None):
    """Le tableau de la ressemblance : une ligne par indicateur des references ( indicateur, valeur simulee, valeur
    reelle, bande, verdict ). `depuis_jour` : le premier jour de la fenetre des flux ( apres la chauffe ) ; `suivi` :
    le Suivi tenu sur cette fenetre ( il la fixe lui-meme ). Ne change rien au monde."""
    refs = refs if refs is not None else charger()
    return juger(refs, valeurs(w, p, depuis_jour, suivi, ids=set(refs)))


def _fmt(v, unite=""):
    if v is None: return "-"
    a = abs(v)
    s = f"{v:,.0f}" if a >= 1000 else f"{v:.1f}" if a >= 100 else f"{v:.2f}" if a >= 1 else f"{v:.3f}"
    return s.replace(",", " ")


def tableau_de_bord(lignes, titre="Ressemblance du pays a la Grece"):
    """Le tableau lisible au terminal : une ligne par indicateur, groupees par theme, et le resume."""
    r = resume(lignes)
    out = [titre, "=" * len(titre)]
    theme = None
    for l in lignes:
        if l["theme"] != theme:
            theme = l["theme"]; out.append(f"-- {theme}")
        ec = "" if l["ecart"] is None else f"{l['ecart']:+.1f}"
        av = " [a verifier]" if l["a_verifier"] else ""
        out.append(f"  {l['nom'][:44]:44s} {_fmt(l['simule']):>9s} {_fmt(l['reel']):>9s} "
                   f"[{_fmt(l['bande'][0])} ; {_fmt(l['bande'][1])}]".ljust(96)
                   + f" {l['verdict']:14s} {ec:>7s} {l['surete']}{av}")
    out.append("")
    out.append(f"Dans la bande : {r['dans']} / {r['mesures']} mesures ( score "
               f"{'-' if r['score'] is None else f'{100 * r['score']:.0f} %'} ) ; hors bande : {r['hors']} ; "
               f"non mesurables : {r['non_mesurables']} ; a verifier ( hors score ) : {r['a_verifier']}")
    out.append(f"Sans les {r['fragiles']} verdicts fragiles : {r['dans_surs']} / {r['mesures'] - r['fragiles']} "
               f"( {'-' if r['score_sur'] is None else f'{100 * r['score_sur']:.0f} %'} )")
    return "\n".join(out)


def tableau_markdown(lignes, entete=""):
    """Le tableau complet en Markdown : chaque indicateur, sa valeur simulee, la valeur reelle, la bande, le verdict,
    l ecart en demi-bandes, la surete, le domaine et la maniere de mesurer."""
    r = resume(lignes)
    out = [entete, "",
           f"**Dans la bande : {r['dans']} sur {r['mesures']} indicateurs mesures** "
           f"({'-' if r['score'] is None else f'{100 * r['score']:.0f} %'}) ; hors bande : {r['hors']} ; "
           f"non mesurables : {r['non_mesurables']} ; a verifier (hors score) : {r['a_verifier']}. "
           f"Sans les {r['fragiles']} verdicts fragiles : {r['dans_surs']} sur {r['mesures'] - r['fragiles']} "
           f"({'-' if r['score_sur'] is None else f'{100 * r['score_sur']:.0f} %'}).", "",
           "Ecart : en demi-bandes (0 = la valeur reelle, +-1 = le bord de la bande ; au-dela, hors bande). "
           "Surete : « fragile » quand l'intervalle a 95 % d'un flux compte deborde de part et d'autre d'un bord.", "",
           "| Theme | Indicateur | Unite | Simule | Reel (annee) | Bande | Verdict | Ecart | Surete | Domaine | Mesure |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in lignes:
        ec = "" if l["ecart"] is None else f"{l['ecart']:+.1f}"
        av = " (a verifier)" if l["a_verifier"] else ""
        d = l["detail"].replace("|", "/")
        out.append(f"| {l['theme']} | {l['nom']}{av} | {l['unite']} | {_fmt(l['simule'])} | {_fmt(l['reel'])} "
                   f"({l['annee']}) | {_fmt(l['bande'][0])} - {_fmt(l['bande'][1])} | {l['verdict']} | {ec} | "
                   f"{l['surete']} | {l['domaine']} | {d} |")
    hors = sorted((l for l in lignes if l["verdict"] == HORS and not l["a_verifier"]), key=lambda l: -abs(l["ecart"]))
    if hors:
        out += ["", "**Les ecarts les plus graves (en demi-bandes)** :", ""]
        for l in hors[:10]:
            out.append(f"- {l['nom']} : {_fmt(l['simule'])} contre {_fmt(l['reel'])} ({l['ecart']:+.1f}) - domaine "
                       f"{l['domaine']}")
    nm = [l for l in lignes if l["verdict"] == NON_MESURABLE]
    if nm:
        out += ["", "**Non mesurables** :", ""]
        for l in nm: out.append(f"- {l['nom']} : {l['detail']}")
    return "\n".join(out) + "\n"


# ================================================================== la ligne de commande
def _domaines(texte):
    if texte in ("tous", "all", None): return None
    if texte in ("aucun", ""): return []
    return [d.strip() for d in texte.split(",") if d.strip()]


def main(argv=None):
    a = argparse.ArgumentParser(description="Mesure la ressemblance du pays simule a la Grece reelle.")
    a.add_argument("--habitants", type=int, default=10000)
    a.add_argument("--jours", type=int, default=30, help="jours de mesure, apres la chauffe")
    a.add_argument("--chauffe", type=int, default=5, help="jours de chauffe, hors mesure")
    a.add_argument("--domaines", default="tous", help="tous, aucun, ou une liste separee par des virgules")
    a.add_argument("--graine", type=int, default=C.GRAINE)
    a.add_argument("--iles", default="Altis")
    a.add_argument("--demographie", default=None,
                   help="passe tel quel a monde.Monde( demographie=... ) si le moteur le connait ( sinon : erreur )")
    a.add_argument("--etiquette", default="defaut")
    a.add_argument("--references", default=None)
    x = a.parse_args(argv)
    from . import monde as W
    from .pays import essais as E, pays as P
    refs = charger(x.references)
    t0 = time.perf_counter()
    kw = {"graine": x.graine, "echelle": x.habitants / 500.0, "iles": tuple(x.iles.split(","))}
    if x.demographie is not None: kw["demographie"] = x.demographie
    doms = _domaines(x.domaines)
    kw["fret"] = "d15" if "logistique" in P.fermeture(doms if doms is not None else list(P.MODULE)) else "e1"   # 29/09
    w = W.Monde(**kw)
    p = P.installer(w, doms)
    t_inst = time.perf_counter() - t0
    print(f"monde : {w.table.n} habitants, {len(p.domaines)} domaines, coeur Rust "
          f"{'charge' if W.COEUR is not None else 'ABSENT'} ; installation {t_inst:.1f} s", flush=True)
    t1 = time.perf_counter()
    E.jours(w, x.chauffe)
    suivi = Suivi(w, p)
    for k in range(x.jours):
        E.jours(w, 1); suivi.apres_jour(w, p)
        if (k + 1) % 5 == 0: print(f"  jour {w.jour} ( {k + 1}/{x.jours} de mesure )", flush=True)
    t_jours = time.perf_counter() - t1
    t2 = time.perf_counter()
    lignes = mesurer(w, p, suivi=suivi, refs=refs)
    t_mes = time.perf_counter() - t2
    par_jour = t_jours / max(1, x.chauffe + x.jours)
    print(tableau_de_bord(lignes))
    print(f"\n{x.chauffe + x.jours} jours en {t_jours:.0f} s ( {par_jour:.2f} s par jour ) ; mesure {t_mes * 1000:.0f} ms")
    import datetime
    d0 = datetime.date(*C.DATE_DEPART[:3])
    du, au = d0 + datetime.timedelta(days=suivi.jour_debut), d0 + datetime.timedelta(days=w.jour)
    entete = (f"# Ressemblance a la Grece : {x.etiquette}\n\n"
              f"Monde : graine {x.graine}, iles {x.iles}, {w.table.n} habitants crees ( {x.habitants} demandes ), "
              f"domaines {'tous' if x.domaines == 'tous' else x.domaines} ({len(p.domaines)}), "
              f"demographie {x.demographie or 'du moteur'}. Chauffe {x.chauffe} jours, mesure {x.jours} jours "
              f"(jours {suivi.jour_debut} a {w.jour}, du {du:%d/%m/%Y} au {au:%d/%m/%Y}), {suivi.clotures} clotures "
              f"suivies. Les references sont ANNUELLES : une fenetre d ete surestime les flux saisonniers (tourisme, "
              f"emploi d ete, climatisation) et la ligne reste a lire avec sa saison. "
              f"Installation {t_inst:.1f} s ; {par_jour:.2f} s par jour ; mesure {t_mes * 1000:.0f} ms.\n\n"
              f"References : `references/grece.json` (ecrites avant la mesure). Commande : "
              f"`python -m monde.ressemblance {' '.join(argv if argv is not None else sys.argv[1:])}`")
    os.makedirs(RESULTATS, exist_ok=True)
    chemin = os.path.join(RESULTATS, f"ressemblance_{x.etiquette}.md")
    with open(chemin, "w", encoding="utf-8") as f: f.write(tableau_markdown(lignes, entete))
    print(f"ecrit : {chemin}")
    return lignes


if __name__ == "__main__":
    main()
