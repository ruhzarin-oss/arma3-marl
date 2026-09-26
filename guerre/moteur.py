"""LE COTE MOTEUR DE LA GUERRE : deux gestes, executes DANS le processus de l ile ( monde/archipel.py, commandes
« guerre_releve » et « occuper » ). Rien ici ne paie ni ne cree un bien : la conservation du socle n est pas touchee.

1. RELEVE : ce que l Etat de l ile a percu pendant les jours du moteur clos depuis la releve precedente, la part de la
   defense dans ses credits votes, son etalon-or, ses militaires vivants. La premiere releve ouvre la guerre : elle
   rend zero recette, la guerre ne paie pas le passe.
2. OCCUPER : une zone tenue par l envahisseur dans Arma. Ce que ses sites produisaient est perdu pour l ile, par
   les mecanismes que le moteur a deja, chacun chez celui qui fait vivre le site :
   - une ferme reprise par l agriculture ( domaine 9 ) passe SOUS SEQUESTRE ( Exploitation.sequestre, l etat de la
     saisie, deja eprouve par tests_d09 ) : ni recolte, ni soins, ni rations livrees, ni vente ; son grenier perit ;
   - un site reste au moteur recoit un choc de rendement nul ( Monde.chocs, celui des secheresses ) ;
   - un site repris par l industrie ( 10 ) ou l energie ( 11 ) n a pas encore d etat de saisie : il est COMPTE
     « non couvert » a chaque occupation, jamais ignore en silence.
   ( 26/09 : la quarantaine, essayee d abord, ne retient pas un paysan qui travaille chez lui - la porte G4 l a vu. )
   La liberation leve le sequestre et ferme le choc au jour de la releve.

   ( 27/09, Younes : « au plus proche du reel » ) Tous les lieux de la zone, VILLES comprises, passent en plus sous les
   RESTRICTIONS DE CIRCULATION de l occupant ( la quarantaine du moteur, respectee par l agenda ) : habitants et
   travailleurs du lieu restent chez eux, sauf les 20 % indociles. Une capitale occupee perd le personnel de son
   marche, de son hopital et de ses ministeres qui vit ailleurs ; le bulletin du gouvernement le dit ( villes occupees,
   siege du gouvernement occupe ).

CE QUE L OCCUPATION NE FAIT PAS ENCORE : l envahisseur ne recoit pas ce que la zone produisait ( la voie :
d09.requisitionner ) ; les fonderies et la centrale ne s arretent pas ; les gens du dehors peuvent encore venir faire
leurs courses au marche d une ville occupee ( l agenda ne bloque que domicile et travail ) ; le gouvernement ne
demenage pas son siege."""
import math
from monde import population as PO

ROLES_MILITAIRES = tuple(r for r in ("soldat", "officier") if r in PO.CODE_ROLE)


def _etat(w):
    p = getattr(w, "pays", None)
    if p is None or not p.a("etat"): raise RuntimeError("la guerre a besoin du domaine 6 ( etat ) : pays sans Etat")
    return p.domaine("etat")


def part_defense(budget):
    tot = math.fsum(budget.credits.values())
    if tot <= 0: return 0.0
    return math.fsum(v for (ligne, _), v in budget.credits.items() if ligne == "defense") / tot


def militaires(w):
    t, n = w.table, w.table.n
    viv = t.vivant[:n] == 1
    return int(sum(int((viv & (t.role[:n] == PO.CODE_ROLE[r])).sum()) for r in ROLES_MILITAIRES))


def releve_de_guerre(w):
    _quarantaine_occupant(w)
    e = _etat(w)
    serie = list(e.tresor.serie)
    dernier = getattr(w, "guerre_dernier_jour", None)
    if dernier is None:                          # la guerre commence : elle ne paie pas le passe
        nouveaux = []
        w.guerre_dernier_jour = serie[-1][0] if serie else -1
    else:
        nouveaux = [s for s in serie if s[0] > dernier]
        if nouveaux: w.guerre_dernier_jour = nouveaux[-1][0]
    o = getattr(w, "etalon_or", None)
    if not o or not o.get("dernier_taux"): raise RuntimeError("la guerre a besoin de l etalon-or ( monde/or_reel.py )")
    return {"jour": int(w.jour), "pas": int(w.pas), "jours_clos": len(nouveaux),
            "recettes": math.fsum(s[1] for s in nouveaux), "part_defense": part_defense(e.budget),
            "euros_par_unite": float(o["dernier_taux"]), "monnaie": o.get("monnaie"), "militaires": militaires(w),
            "occupees": sorted(getattr(w, "occupations", {})), "front": bilan_front(w), "faim": round(faim(w), 4),
            "gouvernement": getattr(w.cerveau, "modele", "regles") if w.cerveau is not None else "regles"}


JAMAIS = 10 ** 9            # la duree d un choc d occupation tant qu il n est pas leve


def _ferme(p, lieu):
    from monde.pays import d09_agriculture as AG
    return AG.exploitation_de(p, lieu) if p.a("agriculture") else None


def _quarantaine_occupant(w):
    """L occupant tient ses lieux : RESTRICTIONS DE CIRCULATION ( la quarantaine du moteur, que l agenda respecte ) -
    ceux qui y habitent et ceux qui y travaillent restent chez eux, sauf la part indocile ( config.QUARANTAINE_VIOLEE ).
    Remise a chaque releve si le gouvernement la leve ; une quarantaine du gouvernement n est jamais retiree ici."""
    q = w.gouv.lois.setdefault("quarantaine", [])
    for o in getattr(w, "occupations", {}).values():
        for l in o.get("quarantaine", ()):
            if l not in q: q.append(l)


def occuper(w, zone, lieux, actif):
    """Pose ( actif ) ou leve l occupation d une zone. Rend les zones occupees et ce que chacune tient."""
    p = w.pays
    occ = w.__dict__.setdefault("occupations", {})
    zone = int(zone)
    if actif and zone in occ and "quarantaine" not in occ[zone]:          # une occupation d avant le 27/09 : les villes aussi
        q = w.gouv.lois.setdefault("quarantaine", [])
        occ[zone]["quarantaine"] = [l for l in lieux if l in w.carte.lieux and l not in q]
        occ[zone]["lieux"] = list(lieux)
        _quarantaine_occupant(w)
    if actif and zone not in occ:
        fermes, moteur, hors = [], [], []
        for l in lieux:
            e = w.entreprises.get(l)
            if e is None: continue                                   # une ville, un port, une base : rien a perdre ici
            dom = p.repris.get(e.id)
            ex = _ferme(p, l) if dom == "agriculture" else None
            if ex is not None:
                if not ex.sequestre: ex.sequestre = True; fermes.append(l)
            elif dom is None: moteur.append(l)
            else: hors.append(f"{l}:{dom}")
        c = {"debut": int(w.jour), "jours": JAMAIS, "lieux": tuple(moteur), "facteur": 0.0, "occupation": zone} if moteur else None
        if c is not None: w.chocs.append(c)
        q = w.gouv.lois.setdefault("quarantaine", [])
        occ[zone] = {"fermes": fermes, "moteur": moteur, "non_couverts": hors, "choc": c, "lieux": list(lieux),
                     "quarantaine": [l for l in lieux if l in w.carte.lieux and l not in q]}
        _quarantaine_occupant(w)
        w.noter("occupation", zone=zone, fermes=len(fermes), sites_moteur=len(moteur), non_couverts=len(hors))
    elif not actif and zone in occ:
        o = occ.pop(zone)
        for l in o["fermes"]: _ferme(p, l).sequestre = False
        levees = set(o.get("quarantaine", ())) - {l for x in occ.values() for l in x.get("quarantaine", ())}
        w.gouv.lois["quarantaine"] = [l for l in w.gouv.lois.get("quarantaine", []) if l not in levees]
        if o["choc"] is not None: o["choc"]["jours"] = max(0, int(w.jour) - o["choc"]["debut"])
        w.noter("liberation", zone=zone)
    return {"occupees": sorted(occ), "fermes": sorted(l for o in occ.values() for l in o["fermes"]),
            "lieux_sous_occupation": sorted(l for o in occ.values() for l in o.get("quarantaine", ())),
            "sites_moteur": sorted(l for o in occ.values() for l in o["moteur"]),
            "non_couverts": sorted(l for o in occ.values() for l in o["non_couverts"])}


# ================================================================== les soldats au front ( option 1 de Younes, 26/09 )
# Chaque soldat pose dans Arma est un habitant du moteur, designe par son ile. Il porte dans Arma un NUMERO DE FRONT
# ( petit entier : Arma compte en flottants 32 bits, le numero d archipel n y tiendrait pas ). Etats :
#   reserve  mobilise, parti de sa base, pas encore vu dans Arma ( la reserve que le commandant d Arma depense ) ;
#   front    vu vivant dans Arma : sa position et ses blessures suivies toutes les 10 s ;
#   mort     tue dans Arma : il meurt dans le moteur, cause « combat » ( d01_population.deceder, le chemin de toute mort ).
# Au front, il est ABSENT, comme un voyageur : il ne mange pas chez lui, ne travaille pas, n est pas planifie
# ( population.ABSENT, poste « voyage », w.absents ) ; l agenda, la medecine et l economie le savent deja.

def _front(w):
    if not hasattr(w, "guerre_front"): w.guerre_front, w.guerre_prochain_numero = {}, 1
    return w.guerre_front


def mobiliser(w, n):
    """Designe n soldats presents ( soldat ou officier, vivants, residents, pas deja au front ), les fait partir au
    front, et rend leurs numeros de front. Moins de n si l armee n en a plus : le pays ne se fabrique pas de soldats."""
    f = _front(w)
    t, nn = w.table, w.table.n
    deja = {x["i"] for x in f.values()}
    codes = [PO.CODE_ROLE[r] for r in ROLES_MILITAIRES]
    ok = (t.vivant[:nn] == 1) & (t.statut[:nn] == PO.RESIDENT) & sum((t.role[:nn] == c) for c in codes).astype(bool)
    cands = [int(i) for i in ok.nonzero()[0] if int(i) not in deja][:max(0, int(n))]
    out = []
    for i in cands:
        k = w.guerre_prochain_numero; w.guerre_prochain_numero += 1
        t.statut[i] = PO.ABSENT; t.lieu[i] = -1; t.poste[i] = PO.CODE_POSTE["voyage"]
        w.absents[i] = {"destination": "front", "depart_pas": int(w.pas)}
        f[k] = {"i": i, "nia": int(t.nia[i]), "etat": "reserve", "x": None, "y": None, "degats": 0.0, "depuis_pas": int(w.pas)}
        out.append(k)
    if out: w.noter("mobilisation", soldats=len(out))
    return out


def suivre(w, releves):
    """releves : [ ( numero, x, y, degats ) ] des soldats vus vivants dans Arma. Rend le nombre de soldats suivis."""
    f = _front(w); vus = 0
    for k, x, y, d in releves:
        s = f.get(int(k))
        if s is None or s["etat"] == "mort": continue
        s.update(etat="front", x=float(x), y=float(y), degats=float(d), vu_pas=int(w.pas)); vus += 1
    return vus


def morts_au_combat(w, numeros):
    """Les soldats tues dans Arma meurent dans le moteur. Rend le nombre de morts nouvelles."""
    from monde.pays import d01_population as POP
    f = _front(w); p = getattr(w, "pays", None); n = 0
    for k in numeros:
        s = f.get(int(k))
        if s is None or s["etat"] == "mort": continue
        i = s["i"]; t = w.table
        w.absents.pop(i, None); t.statut[i] = PO.RESIDENT
        h = w.habitants[i]
        if p is not None and p.a("population"): POP.deceder(p, h, "combat")
        else: h.vivant = False; h.lieu = None
        s.update(etat="mort", mort_pas=int(w.pas)); n += 1
    if n: w.noter("morts_au_combat", soldats=n)
    return n


def bilan_front(w):
    f = _front(w)
    return {e: sum(1 for s in f.values() if s["etat"] == e) for e in ("reserve", "front", "mort")}


# ================================================================== la guerre coute au Tresor ( demande de Younes, 26/09 )
# Les points de Warlords sont un CREDIT : l argent ne quitte le Tresor de l ile qu a l ACHAT. A chaque tour, Arma rend
# ce que son camp a depense en tout ( points ) ; l ile paie la difference avec ce qu elle a deja paye, comme un import
# d armement ( d07.declarer_import, motif import_armement : devises, prix FOB, fret aux armateurs etrangers,
# declaration en douane ; l Etat ne se paie pas de droit ). Le soir, d06 le range sur la ligne DEFENSE, nature achats.
# Ce que la caisse ne paie pas n est pas perdu : c est une dette de guerre, repayee au tour suivant ( le Tresor
# emprunte chaque matin pour tenir son coussin ). La premiere releve fixe la base : les achats d avant ne sont pas payes.
FAMILLE_ARMEMENT = "produit_fini"


def payer_la_guerre(w, depense_points, euros_par_point):
    from monde.pays import d07_exterieur as EXT
    p = w.pays
    depense_points = float(depense_points)
    if not hasattr(w, "guerre_points_payes"):
        w.guerre_points_payes, w.guerre_paye = depense_points, 0.0
        return {"base": depense_points, "points": 0.0, "paye": 0.0, "dette_points": 0.0}
    a_payer = max(0.0, depense_points - w.guerre_points_payes)
    paye = 0.0
    if a_payer > 0:
        valeur = a_payer * float(euros_par_point) / float(w.etalon_or["dernier_taux"])     # FOB, en monnaie de l ile
        paye = EXT.declarer_import(p, w.gouv, valeur, FAMILLE_ARMEMENT, motif="import_armement")
        if paye > 0:
            w.guerre_points_payes += a_payer; w.guerre_paye += paye
            if not hasattr(w, "guerre_paiements"): w.guerre_paiements = []
            w.guerre_paiements.append((int(w.jour), paye)); del w.guerre_paiements[:-500]
            w.noter("achat_armement", points=round(a_payer, 1), paye=round(paye, 2))
    return {"points": a_payer if paye > 0 else 0.0, "paye": paye,
            "dette_points": max(0.0, depense_points - w.guerre_points_payes), "paye_total": w.guerre_paye}


# ================================================================== le gouvernement voit la guerre ( 26/09, Younes : « qu il se gere lui-meme » )
# Chaque matin, le domaine 6 appelle w.cerveau( bulletin, memoire ). CerveauDeGuerre ajoute au bulletin une section
# « guerre » ( ce que l Etat sait de SON armee au front et de ce que la guerre lui coute ) puis passe la main au
# gouvernement de l ile : le code ecrit par Qwen ( agent codeur ), ou les regles s il n y en a pas. Le levier est deja
# dans le catalogue : fixer_budget sur la ligne defense change la part de la defense, donc les points verses au front.

def bulletin_guerre(w):
    f = _front(w)
    semaine = int(w.pas) - 7 * 144
    pay = list(getattr(w, "guerre_paiements", []))
    occ = getattr(w, "occupations", {})
    return {"soldats_au_front": sum(1 for s in f.values() if s["etat"] == "front"),
            "soldats_en_reserve": sum(1 for s in f.values() if s["etat"] == "reserve"),
            "morts_au_combat": sum(1 for s in f.values() if s["etat"] == "mort"),
            "morts_au_combat_7j": sum(1 for s in f.values() if s["etat"] == "mort" and s.get("mort_pas", -1) >= semaine),
            "cout_guerre_total": round(getattr(w, "guerre_paye", 0.0)),
            "cout_guerre_30j": round(math.fsum(x for j, x in pay if j >= int(w.jour) - 30)),
            "zones_occupees": len(occ), "fermes_sous_sequestre": sum(len(o.get("fermes", ())) for o in occ.values()),
            "lieux_sous_occupation": sorted(l for o in occ.values() for l in o.get("quarantaine", ())),
            "villes_occupees": sorted(l for o in occ.values() for l in o.get("quarantaine", ())
                                      if w.carte.lieux[l].type in ("capitale", "ville")),
            "siege_du_gouvernement_occupe": any(w.carte.gouvernement.id in o.get("quarantaine", ()) for o in occ.values()),
            "source": "etat-major et Tresor, le jour meme"}


class CerveauDeGuerre:
    def __init__(self, interieur, w):
        self.interieur, self.w = interieur, w

    @property
    def modele(self): return getattr(self.interieur, "modele", "regles")

    @property
    def empreinte(self): return getattr(self.interieur, "empreinte", None)

    def __call__(self, bulletin, memoire=""):
        bulletin = dict(bulletin, guerre=bulletin_guerre(self.w))
        if self.interieur is None:
            from monde.pays import d06_etat as ET
            return ET.decider_regles_etat(bulletin), "regles"
        return self.interieur(bulletin, memoire)


def voir_la_guerre(w):
    """Pose ( une fois ) la section guerre dans le bulletin du gouvernement de l ile. Rend le modele qui gouverne."""
    if not isinstance(w.cerveau, CerveauDeGuerre): w.cerveau = CerveauDeGuerre(w.cerveau, w)
    return w.cerveau.modele


def gouverner_par(w, source, nom="conseil"):
    """Le conseil de guerre a adopte un nouveau gouvernement : il remplace l ancien dans l ile vivante ( bac a sable de
    l agent codeur, verifie avant ; memoire neuve ), et voit la guerre comme lui. Rend son modele."""
    from monde import agent_codeur as AC
    w.cerveau = CerveauDeGuerre(AC.CerveauCode(source, nom=nom), w)
    w.noter("gouvernement_adopte", modele=w.cerveau.modele, par="conseil de guerre")
    return w.cerveau.modele


def faim(w):
    """La part des menages habites qui n ont pas mange hier ( comme Ile.commande( « etat » ) )."""
    t, n = w.table, w.table.n
    ins = PO.menages_inscrits(t, n)
    import numpy as np
    habites = int((np.bincount(ins[(t.vivant[:n] == 1) & (ins >= 0)], minlength=len(w.menages)) > 0).sum())
    return w.stats_jour.get("menages_sans_nourriture", 0) / max(1, habites)
