"""02/10 ( HMT-191, etape 0c d Arma a fond ) : l arsenal de depart paye par le budget de l ile.
Avec l option `arsenal_budget` ( posee par archipel.creer_ile sur les seules iles qui la demandent ), le domaine 25
n equipe plus toute l armee « gratuitement » a l installation : le materiel DURABLE de depart vaut au plus ce que les
credits d equipement de la defense achetent pendant la duree de service du materiel. Sans l option, rien ne change
( le monde E1 et les references restent identiques ). Le meme texte pour le depot et l arbre des references ( sans
domaine 25 : absent ). Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_arsenal_budget.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue
        if s.count(a) != 1: raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


NOUVEAU = '''# ( 02/10, HMT-191 0c ) L ARSENAL DE DEPART PAYE PAR LE BUDGET DE L ILE ( option `arsenal_budget` du monde ). Le
# materiel DURABLE qu une armee detient vaut, a neuf, ce que ses credits d equipement achetent pendant sa duree de
# service. Part de l equipement dans la defense : 30,85 %, mediane OTAN 2024 ( Defence Expenditure of NATO Countries
# 2014-2024, « major equipment » et sa R&D ). Duree de service : CHOIX 24 ans, entre les 22 ans de l OMFV et les 26 du
# Paladin ( CBO, Projected Acquisition Costs for the Army s Ground Combat Vehicles, 2021, publication 57103 ). Les
# munitions et les pieces sont des stocks consommables ( SEC 2010 : « military inventories » ), hors enveloppe : leur
# stock de depart suit la regle du domaine, pour le materiel achete. Ordre d achat ( CHOIX ) : le lot individuel de
# chaque militaire dans l ordre des lignes, puis les vehicules et mortiers par categorie ( ORDRE_VEHICULES ), puis la
# reserve de 10 % ; une categorie n est entamee que si la precedente est entiere ; ce qui n est pas paye n existe pas.
PART_EQUIPEMENT_DEFENSE = 0.3085
DUREE_SERVICE_ANS = 24.0
ORDRE_VEHICULES = ("steyr_12m18", "m1114", "m113a1", "mortier_81", "leopard_2a6hel")


def enveloppe_equipement(p, d):
    """L enveloppe du materiel durable de depart ( drachmes ) ; infinie sans loi de programmation."""
    loi = _loi_de_programmation(p, d)
    if loi is None: return math.inf
    return PART_EQUIPEMENT_DEFENSE * loi["defense_an"] * DUREE_SERVICE_ANS


def prix_dr(nom):
    """Le prix neuf d un modele du domaine, en drachmes."""
    for t in (ARME, OPTIQUE, PROTECTION, RADIO, VEHICULE):
        if nom in t: return _dr(t[nom].prix_eur)
    raise KeyError(nom)


def lot_dr(sp):
    """Le lot individuel d une specialite : armes, optique, protection, casque, radio ( drachmes )."""
    a, o, a2 = DOTATION[sp]
    t = sum(prix_dr(x) for x in (a, o, a2) if x is not None)
    t += prix_dr(PROTECTION_DE.get(sp, "plaque_iii")) + prix_dr("casque")
    r = RADIO_DE.get(sp)
    return t + (prix_dr(r) if r else 0.0)


def besoins_vehicules(d):
    """La doctrine de _equipement_initial : [ ( modele, unite, base ) ] des vehicules et des mortiers, par unite."""
    U = d.unites; out = []
    for u in range(U.n):
        niv, ty, b = int(U["niveau"][u]), int(U["type"][u]), int(U["base"][u])
        if b < 0: continue
        dot = []
        if niv == GROUPE and ty == INFANTERIE: dot = ["m113a1"]
        elif niv == GROUPE and ty == CHARS: dot = ["leopard_2a6hel"]
        elif niv == SECTION and ty == INFANTERIE: dot = ["m1114"]
        elif niv == SECTION and ty == APPUI: dot = ["steyr_12m18"]
        elif niv == COMPAGNIE and ty in (INFANTERIE, INSTRUCTION): dot = ["steyr_12m18"] * (2 if ty == INFANTERIE else 1)
        out += [(nom, u, b) for nom in dot]
        if niv == SECTION and ty == APPUI: out += [("mortier_81", u, b)] * MORTIERS_PAR_SECTION_APPUI
    return out


def _equiper_selon_budget(p, d):
    """L installation du materiel sous l enveloppe, a la place de _doter puis _equipement_initial. Le bilan est pose
    sur le monde ( w.arsenal_budget_bilan )."""
    E = d.eff; parc = p.socle.parc; V = d.veh; K = d.coll
    reste = enveloppe = enveloppe_equipement(p, d)
    rows = _lignes(d)
    payes = []
    for r in rows.tolist():
        c = lot_dr(int(E["spec"][r]))
        if c > reste: break
        reste -= c; payes.append(r)
    _doter(p, d, np.array(payes, dtype=np.int64))
    complet = len(payes) == len(rows)
    achetes = {}
    if complet:
        besoins = besoins_vehicules(d)
        for nom in ORDRE_VEHICULES:
            lst = [(u, b) for n, u, b in besoins if n == nom]
            prix = prix_dr(nom); k = 0
            for u, b in lst:
                if prix > reste: break
                reste -= prix; k += 1
                if nom == "mortier_81":
                    arm = d.armureries[d.par_base[b]]
                    o = parc.creer(d.mids["mortier_81"], arm, arm.lieu, "initial", p.pas)
                    j = K.ajouter()
                    K["oid"][j], K["modele"][j], K["base"][j], K["unite"][j] = o.id, IDX_ARME["mortier_81"], b, u
                else:
                    _ajouter_vehicule(p, d, nom, b, u, "initial", usure_km=0.0)
            achetes[nom] = [k, len(lst)]
            if k < len(lst):
                complet = False; break
    reserve = 0
    if complet:
        rows2 = _lignes(d)
        for b in d.bases:
            arm = d.armureries[d.par_base[b]]
            rb = rows2[E["base"][rows2] == b]
            demandes = [(nom, int(math.ceil(x * RESERVE_EQUIPEMENT))) for (bb, nom), x in sorted(d.dotes.items()) if bb == b]
            armes = {}
            for champ in ("arme_m", "arme2_m"):
                for k in E[champ][rb].tolist():
                    if k >= 0: armes[ARMES[k].nom] = armes.get(ARMES[k].nom, 0) + 1
            demandes += [(nom, int(math.ceil(armes[nom] * RESERVE_EQUIPEMENT))) for nom in sorted(armes)]
            for nom, n in demandes:
                n = n if math.isinf(reste) else min(n, int(reste // prix_dr(nom)))
                if n > 0:
                    parc.creer_cohorte(d.mids[nom], arm, arm.lieu, n, "initial", 0.2)
                    reste -= n * prix_dr(nom); reserve += n
    # usure de depart des vehicules, munitions et pieces : la regle de _equipement_initial
    rng = p.hasard("armee_parc")
    nv = V.n
    if nv:
        mod = V["modele"][:nv]
        inter = np.array([VEHICULES[m].intervalle_km for m in mod.tolist()])
        V["km_entretien"][:nv] = inter * rng.random(nv)
        V["km"][:nv] = np.array([VEHICULES[m].vie_km for m in mod.tolist()]) * 0.3 * rng.random(nv)
        for k in range(nv):
            o = parc.objets[int(V["oid"][k])]
            parc.user(o, float(V["km"][k]) / VITESSE_USAGE_KMH)
    for b in d.bases:
        arm = d.armureries[d.par_base[b]]
        for bien, q in sorted(_cible_munitions(p, d, b, JOURS_TIR_CIBLE).items()):
            if q > 0: _entrer(p, d, arm, bien, q, "dotation_initiale_armee", importe=True)
        q = _besoin_pieces(p, d, b)
        if q > 0: _entrer(p, d, arm, "pieces", q, "dotation_initiale_armee", importe=True)
    for bien in NOMS_MUNITIONS + ("pieces",):
        d.stock0[bien] = math.fsum(a.stock[d.bids[bien]] for a in d.armureries)
    d.entrees = {}; d.sorties = {}
    p.w.arsenal_budget_bilan = {"enveloppe_dr": enveloppe, "reste_dr": reste, "militaires": int(len(rows)),
                                "equipes": int(len(payes)), "vehicules": achetes, "reserve": reserve,
                                "complet": bool(complet)}


def _ajouter_vehicule(p, d, nom, base, unite, source, usure_km=0.0):'''

remplacer("monde/pays/d25_armee.py", [
    ('''def _ajouter_vehicule(p, d, nom, base, unite, source, usure_km=0.0):''', NOUVEAU),
    ('''    _organiser(p, d)
    _doter(p, d, _lignes(d))
    _equipement_initial(p, d)
''', '''    _organiser(p, d)
    if getattr(w, "arsenal_budget", False): _equiper_selon_budget(p, d)     # ( 02/10, HMT-191 0c ) l ile qui le demande
    else:
        _doter(p, d, _lignes(d))
        _equipement_initial(p, d)
'''),
])
