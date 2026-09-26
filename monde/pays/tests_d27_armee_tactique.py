"""Les portes du domaine 27 ( armee C : tactiques, regles d engagement, pertes, evacuation, justice militaire,
formation ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests armee_tactique"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, pays as P, d16_medecine as MED, d19_education as ED, d21_justice as JU
from . import d25_armee as A, d26_armee_soutien as S
from . import d27_armee_tactique as M

_CACHE = {}


def _monde(jours=1, echelle=5, graine=11, modes=None):
    """Un monde avec le domaine et ses dependances, apres `jours` jours ; chaque porte en reprend une copie."""
    k = (jours, echelle, graine, tuple(sorted((modes or {}).items())))
    if k not in _CACHE:
        w, p = T.monde([M.DOMAINE], graine, echelle, modes=modes)
        T.jours(w, jours)
        _CACHE[k] = pickle.dumps(w)
    w = pickle.loads(_CACHE[k])
    return w, w.pays


def _jusqu_a(w, heure):
    for _ in range(C.PAS_PAR_JOUR + 1):
        if abs(w.heure - heure) < 1e-6: return
        w.pas_suivant()
    raise RuntimeError(f"heure {heure} jamais atteinte")


def _groupes(p, n_min=6):
    U = A._dom(p).unites
    return [g for g in A.unites(p, "groupe") if int(U["type"][g]) == A.INFANTERIE and len(M._aptes(p, g)) >= n_min]


def _sections(p):
    U = A._dom(p).unites
    return [s for s in A.unites(p, "section") if int(U["type"][s]) == A.INFANTERIE and len(M._aptes(p, s)) >= 12]


def _signe(a, b):
    """Test des signes apparie ( bilateral ) : p de la binomiale sur les paires non egales."""
    d = np.asarray(a, float) - np.asarray(b, float)
    n = int((np.abs(d) > 1e-12).sum()); k = int((d > 1e-12).sum())
    if n == 0: return 1.0
    q = min(k, n - k)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(q + 1)) / 2.0 ** n)


def _wilson(k, n, z=2.576):
    if n == 0: return 0.0, 1.0
    f = k / n; den = 1 + z * z / n; c = f + z * z / (2 * n); r = z * math.sqrt(f * (1 - f) / n + z * z / (4 * n * n))
    return (c - r) / den, (c + r) / den


# ================================================================== les preconditions
def test_preconditions():
    """Une tactique REFUSE de partir quand une precondition manque, et le refus ne laisse rien ( ni mission, ni ordre
    au domaine 26, ni munition sortie ). 2 500 habitants, 10 h. Embuscade : adversaire inconnu -> refus ; connu par la
    RUMEUR ( source population ) -> refus ( non identifie ) ; observe -> accepte. Appui mutuel de nuit -> refus ; radios
    coupees -> refus. Un effectif minimal hors d atteinte -> refus. Une armurerie videe -> refus ( munitions ). Seuil :
    les sept verdicts attendus, zero mission, zero ordre, zero coup apres les refus, et un evenement tactique_refusee par
    refus de `lancer`."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    d = M._dom(p); d26 = S._dom(p)
    s = _sections(p)[0]
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, s)
    S.poser_camp(p, "rouge", None, 30, visible=False)
    ent = S.poser_entite(p, "rouge", x0 + 400.0, y0, ile, "debout", 6, 0.0)
    ordres0, mun0 = d26.ordres.n, A.stocks_munitions(p)
    r_inconnu = M.verifier(p, "embuscade", s, ent)
    S._connaitre(p, d26, 0, ent, x0 + 450.0, y0, ile, S.SIGMA_LIEU_M, 0.0, S.POPULATION, 0.5, -1, 6.0)
    r_rumeur = M.verifier(p, "embuscade", s, ent)
    m1, raisons1 = M.lancer(p, "embuscade", s, (x0, y0), (x0 + 350.0, y0), cible=ent)
    ids = M._aptes(p, s)
    S.observer(p, S.CAMP_NATIONAL, ids[:1], np.array([[x0 + 250.0, y0]]), np.zeros(1), False, cibles=[ent], ile=ile)
    r_vu = M.verifier(p, "embuscade", s, ent)
    grand = M.Tactique("colonne", "essai", 500, 0.0, 0.0, "aucune", "toutes", False, 0.0, 0.0, M.TACTIQUE["bond"].phases,
                       "marche", 0.2, "debout", M.TACTIQUE["bond"].critere, (1, 1, 1))
    r_eff = M.verifier(p, grand, s)
    S.couper_radios(p, s)
    r_radio = M.verifier(p, "appui_mutuel", s, ent)
    S.couper_radios(p, s, coupe=False)
    base = w.carte.par_n[int(A._dom(p).unites["base"][s])].id
    for b in A.NOMS_MUNITIONS:
        q = A.armurerie(p, base).stock[A._dom(p).bids[b]]
        if q > 0: A.tirer(p, base, b, q, "tir_instruction")
    r_mun = M.verifier(p, "appui_mutuel", s, ent)
    m2, raisons2 = M.lancer(p, "appui_mutuel", s, (x0, y0), (x0 + 350.0, y0), cible=ent)
    _jusqu_a(w, 23.0)
    r_nuit = M.verifier(p, "appui_mutuel", s, ent)
    refus_j = [e for e in p.socle.journal.recents if e["type"] == "tactique_refusee"]
    ok = (any("inconnu" in r for r in r_inconnu) and any("non identifie" in r for r in r_rumeur) and r_vu == []
          and any("effectif" in r for r in r_eff) and any("radio" in r for r in r_radio)
          and any("munitions" in r for r in r_mun) and any("nuit" in r for r in r_nuit)
          and m1 is None and m2 is None and not d.actives and d26.ordres.n == ordres0 and d.tirs == {}
          and len(refus_j) == 2)
    return ok, (f"inconnu {r_inconnu} ; rumeur {r_rumeur} ; observe {r_vu} ; effectif {r_eff} ; radio {r_radio} ; "
                f"munitions {r_mun} ; nuit {r_nuit} ; missions {len(d.actives)}, ordres {d26.ordres.n - ordres0}, "
                f"coups {sum(d.tirs.values())}, refus notes {len(refus_j)}")


# ================================================================== le resolveur retrouve ses ordres de grandeur
def _duel(p, u, dist, tir=0.5, posture="debout", couvert=0, prot=-1, n_cible=1000, sous_pas=24, seed=1, portee=400.0,
          connu=False):
    """Un stand de tir DANS le resolveur : les hommes de u ( exercice, tir simule, competence forcee ) tirent sur une
    foule adverse immobile qui ne tire pas, a `dist` metres, de jour. Rend ( balles, impacts, arretes )."""
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, u)
    camp = M._camp(p, "adverse")
    ent = S.poser_entite(p, camp, x0 + dist, y0, ile, posture if posture != "couche" else "accroupi", n_cible, 0.0)
    cond = M.Conduite("fixe", posture=posture, regard="objectif", feu="aucun")
    m = M.nouvelle_mission(p, "defense", u, (x0, y0), (x0, y0), adverses=[(ent, n_cible, cond, [], math.pi)],
                           mode="exercice", seed=(seed,), couvert_poste="nu")
    m.tactique = M.Tactique("stand", "essai", 1, 0.0, 0.0, "aucune", "toutes", False, 0.0, 0.0,
                            (M.Phase("tir", None, 10, 600, "duree", "manoeuvre",
                                     {"manoeuvre": M.Conduite("fixe", posture="couche", regard="objectif", feu="libre")}),),
                            "patrouille", 0.0, "accroupi", M.Critere("tenu", "engages", 0.0, 600.0), (1, 1, 1))
    h = m.h; rouges = h["side"] == 1; bleus = h["side"] == 0
    h["tir"][bleus] = tir; h["prot"][rouges] = prot; h["casque"][rouges] = -1
    h["dx"] *= 0.1; h["dy"] *= 0.1
    h["portee"][bleus] = portee               # le fusil et sa hausse : la portee utile de la courbe
    if connu:
        S._connaitre(p, S._dom(p), 0, ent, x0 + dist, y0, ile, 5.0, 0.0, S.OBSERVATION, 0.95, int(h["hid"][0]), n_cible)
    m.elts[-1].couvert = couvert
    M._ouvrir_phase(p, m)
    for _ in range(sous_pas):
        M._sous_pas(p, m, M.DT_S, False); m.t_s += M.DT_S
    balles = float(h["tires"][h["side"] == 0].sum())
    touches, arretes = m.n_impacts[1] - m.n_arretes[1], m.n_arretes[1]
    M._clore(p, m, "fin"); S.retirer_entite(p, ent)
    return balles, touches, arretes


def test_resolveur():
    """Le resolveur retrouve les ordres de grandeur declares, mesures DANS le combat ( detection du domaine 26, ROE,
    tir, impacts ) et non dans la formule. 2 500 habitants, 10 h, une section qui tire sur une foule debout a decouvert
    ( competence 0,5 : le skill 0,5 de la courbe ; portee utile 400 m, celle du fusil et de sa hausse ), qui ne peut
    tomber qu en partie. Seuils : a 25, 50, 100 et 150 m, la
    part des balles au but est a moins de 15 % ( relatif ) de la courbe 1 d Arma ( 75, 57, 30, 24 % ) et l intervalle de
    Wilson a 99 % la contient ; elle decroit de 25 a 150 m ; au-dela de 1,5 fois la portee utile ( 450 m pour un G3 au
    fer, 300 m ), sur une cible identifiee, des balles partent et aucune ne porte. COUVERT : une cible couchee en couvert leger est touchee ~ 0,72 x 0,20 fois
    moins ( a 25 % relatif pres ). PROTECTION : des plaques NIJ III arretent la balle de fusil sur le thorax et l abdomen,
    soit 39 % des impacts sur un homme debout ( modele de zones ) : la part arretee mesuree est dans son Wilson a 99 %.
    RISQUES : pour chacune des neuf tactiques, quatre exercices de jour : l exposition mesuree ( part du temps de marche
    debout d un homme de manoeuvre ) est a 0,05 de l exposition declaree, et la signature vue par l adversaire est la
    declaree."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    s = _sections(p)[0]
    lignes, ok = [], True
    parts = []
    for dist, attendu in ((25.0, 0.75), (50.0, 0.57), (100.0, 0.30), (150.0, 0.24)):
        b, t, a_ = _duel(p, s, dist, sous_pas=3 if dist < 60 else 8)
        t += a_
        f = t / max(1.0, b); lo, hi = _wilson(t, int(b))
        ok &= abs(f / attendu - 1.0) <= 0.15 and lo <= attendu <= hi
        parts.append(f); lignes.append(f"{dist:.0f} m {t}/{b:.0f} = {f:.3f} ( courbe {attendu:.2f} )")
    ok &= all(a > b for a, b in zip(parts, parts[1:]))
    b_loin, t_loin, _ = _duel(p, s, 460.0, sous_pas=4, portee=300.0, connu=True)
    ok &= t_loin == 0 and b_loin > 0
    b0, t0, _ = _duel(p, s, 100.0, sous_pas=8, seed=2)
    bc, tc, _ = _duel(p, s, 100.0, posture="couche", couvert=1, sous_pas=24, seed=3)
    rapport = (tc / max(1.0, bc)) / max(1e-9, t0 / max(1.0, b0))
    ok &= abs(rapport / (0.72 * 0.20) - 1.0) <= 0.25
    bp, tp, ap = _duel(p, s, 50.0, prot=A.IDX_PROTECTION["plaque_iii"], sous_pas=3, seed=4)
    lo, hi = _wilson(ap, ap + tp)
    part_arret = ap / max(1, ap + tp)
    ok &= lo <= 0.39 <= hi
    # le risque DECLARE de chaque tactique ( exposition, signature ) est celui que le resolveur execute
    ecarts = []
    gs = _groupes(p)
    for t in M.TACTIQUES:
        ex, sg = [], []
        for k in range(4):
            m = M.exercice(p, t.nom, gs[k % len(gs)], p.socle.hasard.sous_flux("tests_armee_tactique", 2, M.IDX_TACTIQUE[t.nom], k))
            if m.resultat["exposition"] is not None: ex.append(m.resultat["exposition"]); sg.append(m.resultat["signature"])
        if not ex or abs(float(np.mean(ex)) - t.exposition) > 0.05 or any(x != t.signature for x in sg):
            ecarts.append((t.nom, t.exposition, round(float(np.mean(ex)), 3) if ex else None, t.signature, sg))
    ok &= not ecarts
    return ok, (" ; ".join(lignes) + f" ; 460 m ( au-dela de 1,5 x 300 ) : {t_loin} au but sur {b_loin:.0f} ; couvert "
                f"leger et couche : x{rapport:.3f} ( attendu {0.72 * 0.2:.3f} ) ; plaques III : {part_arret:.2f} des "
                f"impacts arretes ( attendu 0,39, Wilson [{lo:.2f} ; {hi:.2f}] ) ; risques declares contre executes, "
                f"ecarts {ecarts}")


# ================================================================== les controles positifs
def _paires(p, tac_a, tac_b, n, qual_a=None, qual_b=None, taille=4):
    gs = _groupes(p)
    pa, pb, ra, rb = [], [], [], []
    for k in range(n):
        g = gs[k % len(gs)]
        for tac, q, pert, arr in ((tac_a, qual_a, pa, ra), (tac_b, qual_b, pb, rb)):
            rng = p.socle.hasard.sous_flux("tests_armee_tactique", 1, k)
            m = M.exercice(p, tac, g, rng, qual=q, taille=taille, reperer=True)
            pert.append(m.resultat["pertes"]); arr.append(m.resultat["part"])
    return np.array(pa), np.array(pb), np.array(ra), np.array(rb)


def test_controles_positifs():
    """Deux effets poses expres, que l instrument doit voir. 2 500 habitants, 10 h, 40 exercices apparies ( memes
    situations, memes graines ) contre un poste adverse de 4 hommes, repere par un guetteur, a moins de 100 m de
    l itineraire, aux 35 a 65 % d un trajet de 500 a 900 m.
    APPUI MUTUEL contre BOND : l appui neutralise le poste pendant que la manoeuvre bondit ; seuil : pertes moyennes de
    l appui au plus 70 % de celles du bond, et le test des signes apparie p < 0,05. QUALIFIE contre NON QUALIFIE ( le
    meme bond, livret plein ou vide ) : seuil : pertes moyennes plus faibles, part arrivee plus forte, signes p < 0,05
    sur les pertes."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    pa, pb, _, _ = _paires(p, "appui_mutuel", "bond", 40)
    ok1 = pa.mean() <= 0.7 * pb.mean() and pa.mean() < pb.mean() and _signe(pb, pa) < 0.05
    qa, qb, ra, rb = _paires(p, "bond", "bond", 40, qual_a=1.0, qual_b=0.0)
    ok2 = qa.mean() < qb.mean() and ra.mean() > rb.mean() and _signe(qb, qa) < 0.05
    return ok1 and ok2, (f"pertes appui {pa.mean():.3f} contre bond {pb.mean():.3f} ( signes p {_signe(pb, pa):.4f} ) ; "
                         f"qualifie : pertes {qa.mean():.3f} contre {qb.mean():.3f}, arrives {ra.mean():.2f} contre "
                         f"{rb.mean():.2f} ( signes p {_signe(qb, qa):.4f} )")


# ================================================================== les regles d engagement et le tribunal militaire
def test_regles_engagement():
    """Une violation va au tribunal militaire ; le respect ne tire pas. Au combat ( balles reelles ), 2 500 habitants,
    23 h ( nuit : on ne voit qu a 36 m ). Un contact connu par la RUMEUR seulement ( source population ) a 150 m d une section en defense, feu libre,
    discipline forcee a 1 : aucune balle, aucune violation. Meme scene, le chef ORDONNE le feu sur le contact : des
    balles, une violation sans_identification du chef, une affaire militaire a son nom, un dossier au tribunal
    militaire ( le lendemain ). De jour, un adversaire OBSERVE ( identifie ) dans une ZONE INTERDITE : discipline 1, aucune balle ; ordre
    du chef : violation zone_interdite. Seuil : les six constats, et `anomalies` sans violation_sans_affaire."""
    w, p = _monde(1)
    _jusqu_a(w, 23.0)
    d = M._dom(p); d26 = S._dom(p)
    s = _sections(p)[0]
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, s)
    chef = int(A._dom(p).unites["chef"][s])

    def scene(feu_chef, roe=M.ROE_DEFAUT, source=S.POPULATION, conf=0.5, sigma=S.SIGMA_LIEU_M, seed=1):
        camp = M._camp(p, "adverse")
        ent = S.poser_entite(p, camp, x0 + 150.0, y0, ile, "accroupi", 4, 0.0)
        S._connaitre(p, d26, 0, ent, x0 + 160.0, y0, ile, sigma, 0.0, source, conf,
                     int(M._aptes(p, s)[0]) if source == S.OBSERVATION else -1, 4.0)
        cond = M.Conduite("fixe", posture="couche", regard="objectif", feu="aucun")
        m = M.nouvelle_mission(p, "defense", s, (x0, y0), (x0, y0), adverses=[(ent, 4, cond, [], math.pi)],
                               mode="combat", voix=True, seed=(seed,), feu_sur_contact=feu_chef, roe=roe, axe=0.0)
        m.h["disc"][m.h["side"] == 0] = 1.0
        m.t_max_s = 1200.0
        M.executer(p, m)
        S.retirer_entite(p, ent)
        return m, float(m.h["tires"][m.h["side"] == 0].sum())

    m1, b1 = scene(False)
    m2, b2 = scene(True, seed=2)
    _jusqu_a(w, 10.0)
    af = JU.affaires(p, type_="militaire")
    af_chef = [a for a in af if a["suspect"] == chef]
    zone = M.RegleEngagement(zones=((x0 + 150.0, y0, ile, 200.0),))
    m3, b3 = scene(False, roe=zone, source=S.OBSERVATION, conf=0.95, sigma=10.0, seed=3)
    m4, b4 = scene(True, roe=zone, source=S.OBSERVATION, conf=0.95, sigma=10.0, seed=4)
    viol = [(v[3], v[2]) for v in d.violations]
    anom = [a for a in M.anomalies(p) if a[0] == "violation_sans_affaire"]
    ok = (b1 == 0 and not m1.violations and b2 > 0 and ("sans_identification", chef) in viol and len(af_chef) >= 1
          and af_chef[0]["dossier"] is not None and b3 == 0 and not m3.violations and ("zone_interdite", chef) in viol
          and b4 > 0 and not anom)
    return ok, (f"rumeur, discipline : {b1:.0f} balles, {len(m1.violations)} violation ; ordre du chef : {b2:.0f} balles, "
                f"violations {viol} ; affaires militaires du chef {len(af_chef)} ( dossier "
                f"{af_chef[0]['dossier'] if af_chef else None}, etat {af_chef[0]['etat'] if af_chef else None} ) ; zone "
                f"interdite : {b3:.0f} balles sans ordre, {b4:.0f} sur ordre ; anomalies {anom}")


# ================================================================== pertes, evacuation, grand livre
def _combat(w, p, n_sections=4, rouges=8, pas=36):
    if not any(c.nom == "rouge" for c in S._dom(p).camps): S.poser_camp(p, "rouge", None, 30, visible=False)
    ms = []
    for s in _sections(p)[:n_sections]:
        x0, y0, ile = S.position(p, S.CAMP_NATIONAL, s)
        ent = S.poser_entite(p, "rouge", x0 + 250.0, y0 + 40.0, ile, "accroupi", rouges, 0.0)
        m, r = M.lancer(p, "bond", s, (x0 - 300.0, y0), (x0 + 400.0, y0 + 40.0), voix=True,
                        adverses=[(ent, rouges, M.Conduite("fixe", regard="objectif", feu="libre"), [], math.pi)])
        if m is not None: ms.append(m)
    for _ in range(pas):
        w.pas_suivant()
        if all(m.fini for m in ms): break
    return ms


def test_pertes_evacuation():
    """Au combat ( balles reelles ), 2 500 habitants, 10 h : quatre sections progressent par bonds vers un poste de 8
    hommes a 250 m, qui les voit venir. Seuils : au moins 5 blesses ; CHAQUE blesse ( hors contusion ) est evacue par le
    domaine 26 ( admis au domaine 17 : son evacuation est enregistree au domaine 26 ) ; CHAQUE mort est passe par d01.deceder, cause combat, et
    `morts_hors_deceder` est vide 12 h plus tard ; les coups demandes par le combat sont exactement ceux sortis de
    l armurerie ( tir_combat du domaine 25 ), le domaine 25 n a pas de munition hors consommation, le socle tient sa
    conservation. MATERIEL : une mission qui ROMPT abandonne l arme de ses hommes hors de combat ( P 0,8 ) : chaque arme
    perdue sort du Parc, chaque munition portee perdue sort par perte_au_combat."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    d = M._dom(p); a = A._dom(p)
    sort0 = {k: v for k, v in a.sorties.items()}
    ms = _combat(w, p)
    for _ in range(72): w.pas_suivant()
    bl = [b for b in d.blesses]
    evac = [b for b in bl if b[5] is not None]
    ev26 = {e[1] for e in S._dom(p).evacuations}
    admis = [b for b in bl if b[2] in ev26]
    morts = [h for h in sorted(d.engages) if not w.table.vivant[h]]
    dj = p.col("habitant", "deces_j"); cause = p.col("habitant", "cause_deces")
    morts_ok = all(dj[h] >= 0 and cause[h] == M._cause_combat() for h in morts)
    tirs = {k: v for k, v in d.tirs.items() if not k[1].endswith(":perte")}
    delta = {}
    for (b, mo), v in a.sorties.items():
        if mo == "tir_combat": delta[b] = delta.get(b, 0.0) + v - sort0.get((b, mo), 0.0)
    par_bien = {}
    for (lid, b), v in tirs.items(): par_bien[b] = par_bien.get(b, 0.0) + v
    livre_ok = all(abs(par_bien.get(b, 0.0) - delta.get(b, 0.0)) < 1e-6 for b in set(par_bien) | set(delta))
    mun = [x for x in A.anomalies(p) if x[0] == "munition_hors_consommation"]
    tenue, msg = p.socle.conservation.tenue()
    # le materiel perdu quand l unite rompt
    m = max(ms, key=lambda x: (int(((x.h["side"] == 0) & (x.h["actif"] == 0)).sum()), -x.id))
    m.rupture = True
    nb_objets0 = len(p.socle.parc.objets); perdues0 = len(d.armes_perdues)
    perte0 = sum(v for (b, mo), v in a.sorties.items() if mo == "perte_au_combat")
    hors = int(((m.h["side"] == 0) & (m.h["actif"] == 0)).sum())
    M._perdre_materiel(p, m)
    perdues = len(d.armes_perdues) - perdues0
    perte = sum(v for (b, mo), v in a.sorties.items() if mo == "perte_au_combat") - perte0
    mat_ok = perdues >= 1 and len(p.socle.parc.objets) == nb_objets0 - perdues and perte > 0
    anom = M.anomalies(p)
    ok = (len(bl) >= 5 and len(evac) == len(bl) and len(admis) == len(bl) and morts_ok and not MED.morts_hors_deceder(p)
          and livre_ok and not mun and tenue and mat_ok and not anom and p.socle.conservation.tenue()[0])
    moyens = {}
    for b in evac: moyens[b[5]] = moyens.get(b[5], 0) + 1
    return ok, (f"{len(ms)} missions ( {[m_.issue for m_ in ms]} ) ; {len(bl)} blesses, evacues {len(evac)} {moyens}, admis "
                f"au domaine 26 {len(admis)} ; {len(d.contusions)} contusions ; morts {len(morts)} ( deceder, cause combat : "
                f"{morts_ok} ) ; coups {sum(par_bien.values()):.0f} demandes = {sum(delta.values()):.0f} sortis "
                f"( tir_combat ) : {livre_ok} ; rupture forcee : {hors} hors de combat, {perdues} armes perdues, "
                f"{perte:.0f} coups perdus ; conservation {msg} ; anomalies {anom}")


# ================================================================== le monde par defaut ne combat pas
def test_monde_sans_combat():
    """Le monde par defaut ( 2 500 habitants, 10 jours, aucun camp adverse ) ne connait aucun combat : aucune mission
    au combat, aucun coup de combat du domaine, aucun blesse ni mort de cause combat dans tout le pays, aucune violation.
    La vie du domaine continue : le plan d instruction forme des compagnies ( exercices au tir SIMULE ) ."""
    w, p = _monde(10)
    d = M._dom(p)
    tb = w.table; n = tb.n
    dj = p.col("habitant", "deces_j")[:n]; cause = p.col("habitant", "cause_deces")[:n]
    morts_combat = int(((dj >= 0) & (cause == M._cause_combat())).sum())
    combats = [b for b in d.bilans if b[3] == "combat"]
    blessures = [e for e in p.socle.journal.recents if e["type"] == "blessure" and e.get("cause") == "combat"]
    camps = [c.nom for c in S._dom(p).camps]
    ok = (not combats and not d.tirs and not d.blesses and not d.morts and morts_combat == 0 and not blessures
          and not d.violations and set(camps) <= {S.CAMP_NATIONAL, "plastron"})
    return ok, (f"missions de combat {len(combats)}, coups {sum(d.tirs.values()):.0f}, blesses {len(d.blesses)}, morts de "
                f"cause combat {morts_combat}, violations {len(d.violations)} ; camps {camps} ; formations en cours "
                f"{len(d.formations)}, exercices {d.exercices}, notes d exercice {d.notes_formation}")


# ================================================================== le falsificateur
def test_falsificateur():
    """Les erreurs posees a la main sont vues ; le monde intact n en a aucune. Apres un combat ( 2 sections ) :
    `anomalies` vide. Puis, chacune seule et retiree ensuite : un tir compte sans munition sortie ( tir_sans_munition ),
    un militaire engage tue a la main sans d01.deceder ( mort_sans_deceder ), un blesse sans evacuation
    ( blesse_sans_evacuation ), une marche Arma sans destination ( marche_sans_destination ). Et un homme SANS munition
    ne tire pas : une section aux cartouchieres vides, au contact, ne tire aucune balle."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    d = M._dom(p)
    _combat(w, p, 2)
    intact = M.anomalies(p)
    vus = {}
    k = next(iter(d.tirs)); d.tirs[k] += 10.0
    vus["tir_sans_munition"] = any(a[0] == "tir_sans_munition" for a in M.anomalies(p)); d.tirs[k] -= 10.0
    h = next(x for x in sorted(d.engages) if w.table.vivant[x])
    w.table.vivant[h] = 0
    vus["mort_sans_deceder"] = any(a[0] == "mort_sans_deceder" for a in M.anomalies(p)); w.table.vivant[h] = 1
    d.blesses.append((w.pas, -1, h, "membre", 9, None))
    vus["blesse_sans_evacuation"] = any(a[0] == "blesse_sans_evacuation" for a in M.anomalies(p)); d.blesses.pop()
    d.ordres_arma.append((w.pas, -1, "manoeuvre", [("moveTo", 0, (0.0, 0.0))]))
    vus["marche_sans_destination"] = any(a[0] == "marche_sans_destination" for a in M.anomalies(p)); d.ordres_arma.pop()
    apres = M.anomalies(p)
    # sans munition
    s = _sections(p)[-1]
    x0, y0, ile = S.position(p, S.CAMP_NATIONAL, s)
    ent = S.poser_entite(p, "rouge", x0 + 120.0, y0, ile, "debout", 3, 0.0)
    m = M.nouvelle_mission(p, "defense", s, (x0, y0), (x0, y0), mode="combat", voix=True, seed=(9,), axe=0.0,
                           adverses=[(ent, 3, M.Conduite("fixe", posture="debout", regard="objectif", feu="aucun"), [], math.pi)])
    m.h["coups"][m.h["side"] == 0] = 0.0
    m.t_max_s = 600.0
    M.executer(p, m)
    vides = float(m.h["tires"][m.h["side"] == 0].sum())
    connu = S.connaissance(p, S.CAMP_NATIONAL, ent) is not None
    ok = not intact and all(vus.values()) and not apres and vides == 0 and connu
    return ok, f"intact {intact} ; vus {vus} ; apres retrait {apres} ; sans munition, adversaire connu {connu} : {vides:.0f} balle"


# ================================================================== la decision
def test_decision():
    """Porte de decision : le scenario d exercices ( 2 500 habitants, 5 jours, 4 exfiltrations par jour et par groupe
    d infanterie contre une force adverse posee - poste ou patrouille -, tir simule ), mode hasard. Part du choix >= 0,01
    et p de permutation < 0,05, avec au moins 5 notes par action et par jour sur 4 jours au moins. La regle et le temoin
    ( toujours le bond ) sont mesures sur les memes situations : notes moyennes rapportees."""
    w, p = M.scenario_exercices(jours=5, mode="hasard")
    dec = M._dom(p).decideur
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (nb, s_, q) in dec.stats.items(): par_jour.setdefault(j, []).append(nb)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == len(M.ACTIONS) and min(v) >= 5)

    def moy(dc):
        na = dc.notes_par_action()
        return sum(k * v for k, v in na.values()) / max(1, sum(k for k, _ in na.values()))
    regle = M._dom(M.scenario_exercices(jours=5, mode="regle")[1]).decideur
    temoin = M._dom(M.scenario_exercices(jours=5, mode="temoin")[1]).decideur
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 4 and dec.n_decisions >= 200
    na = {k: (nb, round(v, 3)) for k, (nb, v) in dec.notes_par_action().items()}
    return ok, (f"hasard : {dec.n_decisions} decisions, part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes par "
                f"action ; notes {na} ; moyennes regle {moy(regle):.3f}, temoin {moy(temoin):.3f}, hasard {moy(dec):.3f} ; "
                f"regle {regle.notes_par_action()}")


# ================================================================== la formation
def test_formation():
    """Le cycle du domaine 19 : une compagnie d infanterie est inscrite au programme du bond ( 3 jours d instruction,
    3 d exercice, 1 de debrief, puis l epreuve ) ; les jours d exercice, un exercice REEL contre une autre compagnie
    ( plastron ) note chaque stagiaire ( `noter_exercice` ). 2 500 habitants, 16 jours. Seuils : au moins autant de
    notes d exercice que de stagiaires ; au moins la moitie des stagiaires qualifies ; les qualifications tactiques du
    domaine sont EXACTEMENT celles que le domaine 19 a delivrees pour ce programme ( journal qualification_formation ) ;
    aucun stagiaire qualifie qui n ait recu au moins une note d un exercice reel."""
    w, p = _monde(1)
    _jusqu_a(w, 8.0)
    d = M._dom(p); U = A._dom(p).unites
    c = next(c for c in A.compagnies(p) if int(U["type"][c]) == A.INFANTERIE and c not in d.formations
             and len(M._aptes(p, c)) >= 12)
    n = M.former(p, c, "bond")
    ins = set(d.formations[c][2])
    notes_recues = set()

    for _ in range(16):
        n0 = d.notes_formation
        sta = ED._dom(p).stagiaires
        avant = {h for h in ins if h in sta and sta[h].phase == ED.EXERCICE}
        T.jours(w, 1)
        if d.notes_formation > n0: notes_recues |= avant
    bit = 1 << M.IDX_TACTIQUE["bond"]
    qual = {h for h in ins if d.qualifs.get(h, 0) & bit}
    journal = {e["habitant"] for e in p.socle.journal.recents if e["type"] == "qualification_formation"
               and e["programme"] == M.PROGRAMME["bond"] and e["habitant"] in ins}
    nc = d.notes_par_compagnie.get(c, 0)
    ok = (n >= 12 and nc >= n and len(qual) >= 0.5 * n and qual == journal and qual <= notes_recues)
    return ok, (f"compagnie {c} : {n} stagiaires ; {nc} notes d exercices reels ( plastron ) ; "
                f"{len(qual)} qualifies au bond ( journal du 19 : {len(journal)} ) ; qualifies sans note d exercice "
                f"{len(qual - notes_recues)} ; exercices {d.exercices}")


# ================================================================== la porte commune et le cout
def test_porte_commune():
    return T.porte_commune(M.DOMAINE)


class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, *a, **k):
        t0 = time.perf_counter(); r = self.f(*a, **k); self.t += time.perf_counter() - t0; return r


def test_cout():
    """Coeur Rust. A 10 000 habitants, les routines du domaine ( et l echeance de ses missions, et leur lancement )
    coutent au plus 25 % d une journee du moteur seul, en moyenne sur trois jours : un jour de paix ( le lundi, plan
    d instruction ), un jour ou deux sections combattent, un jour d exercices de formation ( les stagiaires d une
    compagnie mis en phase d exercice ). Installer le domaine a 100 000 habitants ( ses dependances deja la ) coute au
    plus 15 fois l installation a 10 000."""
    coeur = W.COEUR is not None
    w0 = W.Monde(echelle=20); T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = T.monde([M.DOMAINE], 11, 20)
    T.jours(w, 1)
    chronos = []
    for minute, lst in p.routines.items():
        for i, (o, dom, f) in enumerate(lst):
            if dom == M.DOMAINE:
                c = _Chrono(f); lst[i] = (o, dom, c); chronos.append(c)
    c = _Chrono(p.gestionnaires["armee_tactique_pas"]); p.gestionnaires["armee_tactique_pas"] = c; chronos.append(c)
    T.jours(w, 1)
    _jusqu_a(w, 9.0)
    lancer = _Chrono(M.lancer); M.lancer = lancer
    try: ms = _combat(w, p, 2, pas=0)
    finally: M.lancer = lancer.f
    T.jours(w, 1)
    _jusqu_a(w, 9 + 50 / 60)                    # le lundi : le plan d instruction est passe a 9 h 40
    d = M._dom(p); sta = ED._dom(p).stagiaires
    c = next(iter(sorted(d.formations)), None)
    n_ex = 0
    if c is not None:
        for h in d.formations[c][2]:
            if h in sta: sta[h].phase, sta[h].jours = ED.EXERCICE, 0; n_ex += 1
    ex0 = d.exercices
    T.jours(w, 1)
    propre = (sum(c_.t for c_ in chronos) + lancer.t) / 3
    deps = sorted(set(P.fermeture([M.DOMAINE])) - {M.DOMAINE}, key=P.RANG.get)

    def installation(ech):
        wx = W.Monde(echelle=ech); P.installer(wx, deps)
        t = time.perf_counter(); P.installer(wx, [M.DOMAINE]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {w.table.n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres "
                f"{propre * 1000:.0f} ms par jour, {propre / t_e1:.1%} ( {len(ms)} combats, {d.exercices - ex0} exercices "
                f"de formation pour {n_ex} stagiaires ) ; installation {n10} habitants "
                f"{t10:.3f} s, {n100} habitants {t100:.3f} s ( x{t100 / t10:.1f} )")


TESTS = [test_preconditions, test_resolveur, test_controles_positifs, test_regles_engagement, test_pertes_evacuation,
         test_monde_sans_combat, test_falsificateur, test_decision, test_formation, test_porte_commune, test_cout]
