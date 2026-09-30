"""PORTE DES VIVRES DES ENFANTS ( HMT-176, avec le crochet HMT-177 ; 30/09 ). Criteres ecrits AVANT le code :
/mnt/data/hmt/classes/vivres/CRITERES_VIVRES_ENFANTS_20260930T0158.md ( sha256 999fbf63... ).

  V1  invariant, en colonnes, sur une journee de manque provoquee ( Altis, graine 5, pays avec population, le soir du
      jour 3 chaque garde-manger ramene a la moitie du besoin ) : dans tout menage ou un mineur manque ( > 1e-9 ), aucun
      adulte present n a mange plus de 1e-9 ; les adultes n ont pas mange plus que le reste apres les mineurs ; la faim
      de chaque membre suit la regle par personne, au bit ; au moins 20 menages mixtes manquent ( vacuite ) ;
  V2  controle positif : un adulte et un enfant, garde-manger a 1,0 : l enfant mange sa ration ( faim - 1 ), l adulte
      manque 1,0 ( faim + 0,6 ) ;
  V3  falsificateur : l ancien partage egal, sur les memes entrees, est vu en VIOLATION ( V2 et >= 20 menages de V1 ) ;
  V4  controle positif du crochet : manger_dehors( enfant, 1 ) : besoin 1,0, personne ne manque, rations_dehors = 1,0,
      repas_dehors remis a zero ; garde-manger vide : l adulte manque 1,0, l enfant est nourri ; bornes ( ValueError ) ;
      deux appels de 0,7 bornes a 1 ;
  V5  falsificateur du crochet : sans l appel, le besoin reste plein ( manque 1,0 avec 1,0 au garde-manger ) ;
  V6a identite unitaire : 20 000 menages sans mineur ou sans adulte, a = 0 : manque et faim au bit de l ancienne formule ;
  V6c repas_python contre repas ( colonnes ) : 4 jours, manque provoque les soirs 2 a 4, a_i FRACTIONNAIRES meles
      ( 0,24, 0,5, 0,48, 0,7 + 0,7 ) chez les mineurs et les adultes, une ration perdue par soir : faim, garde-manger, nourriture
      consommee, rations_dehors, rations_dehors_perdues identiques au bit ; au moins 20 menages-soirs mixtes qui
      manquent avec deux parts non dyadiques ( la ou l ordre des sommes compte ) ; controle : un chemin sans mineurs
      differe des le soir 2 ( ajout du 30/09, 5 h 50, demande du chef de projet ) ;
  V4 bis  audit : servi = rations_dehors + rations_dehors_perdues ( un mort de la journee, et l excedent au-dela de 1 :
      0,7 + 0,7 ) ; falsificateur : une ration a un vivant a table n est pas perdue ;
  V7  conservation : pour chaque menage, somme ( b_i - manque_i ) = mange a 1e-9 ; verifier_conservation du monde.
( V6b, l identite du monde entier sur 40 jours contre le tronc, se joue hors du depot : deux arbres. )
   python -m monde.porte_vivres_enfants"""
import math, sys
import numpy as np
from . import monde as W, population as P, config as C
from .pays import essais as T

GRAINE = 5
R = C.NOURRITURE_PAR_JOUR


def _membres(w):
    """Les membres a table, comme Monde.repas : vivants, presents, inscrits ; et leur menage."""
    t, n = w.table, w.table.n
    mm = P.menages_inscrits(t, n)
    membres = np.nonzero((t.vivant[:n] == 1) & (t.statut[:n] != P.ABSENT) & (mm >= 0))[0]
    return membres, mm[membres]


def verifier(manque, part, mineur, k, M, mi, tol=1e-9):
    """L invariant, en colonnes, sur les entrees et la sortie d un partage. Rend ( violations, mixtes qui manquent,
    ecart de conservation le plus grand )."""
    mange_i = R * part - mi
    mineur_affame = np.bincount(k, weights=(mineur & (mi > tol)).astype(float), minlength=M) > 0
    adulte_a_mange = np.bincount(k, weights=(~mineur & (mange_i > tol)).astype(float), minlength=M) > 0
    b_min = R * np.bincount(k, weights=np.where(mineur, part, 0.0), minlength=M)
    mange_adu = np.bincount(k, weights=np.where(mineur, 0.0, mange_i), minlength=M)
    besoin = R * np.bincount(k, weights=part, minlength=M)
    mange = besoin - manque
    viol = (mineur_affame & adulte_a_mange) | (mange_adu > np.maximum(0.0, mange - b_min) + tol)
    a_min = np.bincount(k, weights=mineur.astype(float), minlength=M) > 0
    a_adu = np.bincount(k, weights=(~mineur).astype(float), minlength=M) > 0
    mixtes = int((a_min & a_adu & (manque > 1e-6)).sum())
    presents = np.bincount(k, minlength=M) > 0
    ecart = float(np.abs(np.bincount(k, weights=mange_i, minlength=M) - mange)[presents].max()) if presents.any() else 0.0
    return int(viol.sum()), mixtes, ecart


class Espion:
    """Releve les entrees et la sortie reelles de partager_le_manque ( la fonction du module, appelee par repas )."""
    __slots__ = ("vrai", "vu")

    def __init__(self): self.vrai = W.partager_le_manque; self.vu = []

    def __call__(self, manque, part, mineur, k, M):
        mi = self.vrai(manque, part, mineur, k, M)
        self.vu.append((np.array(manque, float), np.array(part, float), np.array(mineur, bool), np.array(k), int(M), mi.copy()))
        return mi


def _un_plus_un(w):
    """Un menage d un adulte et d un enfant de 5 a 14 ans, seuls a table."""
    t = w.table
    membres, k = _membres(w)
    M = w.table.menages.n
    v = np.bincount(k, minlength=M)
    enf = np.bincount(k[(t.age[membres] >= 5) & (t.age[membres] < 15)], minlength=M)
    mi = np.bincount(k[t.age[membres] < 18], minlength=M)
    for mg in np.nonzero((v == 2) & (enf == 1) & (mi == 1))[0].tolist():
        ids = membres[k == mg]
        enfant = int(ids[t.age[ids] < 18][0]); adulte = int(ids[t.age[ids] >= 18][0])
        return mg, adulte, enfant
    raise SystemExit("aucun menage d un adulte et d un enfant")


def _soir(w, mg, adulte, enfant, gm, dehors=()):
    """Un repas du soir sur ce menage : faim a 5 pour les deux, garde-manger a `gm`, les autres menages pleins."""
    t, mt = w.table, w.table.menages
    mt.garde_manger[:mt.n] = 50.0
    mt.garde_manger[mg] = gm
    t.faim[adulte] = t.faim[enfant] = 5.0
    for i, q in dehors: w.manger_dehors([i], q)
    esp = Espion(); W.partager_le_manque = esp
    try: w.repas()
    finally: W.partager_le_manque = esp.vrai
    return float(t.faim[adulte]), float(t.faim[enfant]), float(mt.garde_manger[mg]), esp.vu[-1]


def v2_a_v5(dire):
    w, p = T.monde(["population"], graine=GRAINE)
    T.jours(w, 1)
    mg, adulte, enfant = _un_plus_un(w)
    # V2
    fa, fe, g, (manque, part, mineur, k, M, mi) = _soir(w, mg, adulte, enfant, 1.0)
    dire(fe == 4.0 and fa == 5.0 + (1.0 - C.FAIM_ADAPTATION) and g == 0.0,
         f"V2 un adulte et un enfant, garde-manger 1,0 : enfant faim 5 -> {fe:g} ( nourri ), adulte 5 -> {fa:g} ( manque 1,0 ), "
         f"garde-manger {g:g}")
    viol, _, ecart = verifier(manque, part, mineur, k, M, mi)
    sel = k == mg
    # V3 : l ancien partage egal sur les memes entrees
    v = np.bincount(k, minlength=M)
    ancien = manque[k] / np.maximum(v[k], 1)
    viol_anc = verifier(manque, part, mineur, k, M, ancien)[0]
    dire(viol == 0 and viol_anc >= 1 and np.allclose(ancien[sel], 0.5),
         f"V3 falsificateur : l ancien partage egal donne {ancien[sel].tolist()} au menage et le verificateur voit "
         f"{viol_anc} violation(s) ( la regle : {viol} )")
    # V5 : sans crochet, le besoin reste plein
    dire(abs(manque[mg] - 1.0) < 1e-12 and "rations_dehors" not in w.stats_jour and getattr(w, "repas_dehors", None) is None,
         f"V5 sans manger_dehors : manque du menage {manque[mg]:g} ( besoin plein 2,0 ), pas de compteur, pas de tableau")
    # V4 : le crochet
    fa, fe, g, (manque, part, mineur, k, M, mi) = _soir(w, mg, adulte, enfant, 1.0, dehors=((enfant, 1.0),))
    rd = w.repas_dehors
    r4a = w.stats_jour.get("rations_dehors")
    ok4a = manque[mg] == 0.0 and fa == 4.0 and fe == 4.0 and g == 0.0 and r4a == 1.0 \
        and not rd.any() and len(rd) >= w.table.n
    fa2, fe2, g2, (manque2, *_r) = _soir(w, mg, adulte, enfant, 0.0, dehors=((enfant, 1.0),))
    ok4b = manque2[mg] == 1.0 and fa2 == 5.0 + (1.0 - C.FAIM_ADAPTATION) and fe2 == 4.0
    fa3, fe3, g3, (manque3, *_r) = _soir(w, mg, adulte, enfant, 1.0, dehors=((enfant, 0.7), (enfant, 0.7)))
    ok4c = manque3[mg] == 0.0 and w.stats_jour.get("rations_dehors") == 1.0
    erreurs = 0
    for ids, q in (([enfant], 0.0), ([enfant], 1.5), ([enfant], float("nan")), ([w.table.n], 1.0), ([-1], 0.5), ([enfant, adulte], [0.5, 0.5, 0.5])):
        try: w.manger_dehors(ids, q)
        except ValueError: erreurs += 1
    w.repas_dehors[:] = 0.0
    from .pays import d01_population as PO
    membres, k = _membres(w)
    v = np.bincount(k, minlength=w.table.menages.n)
    seul = [int(i) for i in membres if v[w.table.menage[i]] == 1 and w.table.age[i] >= 18 and i not in (adulte, enfant)]
    z1, z2 = seul[0], seul[1]
    z3 = seul[2]
    w.manger_dehors([z1], 0.3); w.manger_dehors([z2], 0.25); PO.deceder(p, w.habitants[z1], "naturelle")
    w.manger_dehors([z3], 0.7); w.manger_dehors([z3], 0.7)          # deux appels de 0,7 : 0,4 au-dela de 1
    w.repas()
    perdues, dehors_ok = w.stats_jour.get("rations_dehors_perdues"), w.stats_jour.get("rations_dehors")
    servi = 0.3 + 0.25 + 0.7 + 0.7
    w.manger_dehors([z2], 0.25); w.repas()
    perdues2, dehors2 = w.stats_jour.get("rations_dehors_perdues"), w.stats_jour.get("rations_dehors")
    dire(abs(perdues - 0.7) <= 1e-12 and dehors_ok == 1.25 and abs(servi - (dehors_ok + perdues)) <= 1e-9
         and perdues2 == 0.0 and dehors2 == 0.25,
         f"V4 bis audit : 0,3 puis mort avant le repas, 0,25 a table, 0,7 + 0,7 a table -> appliquees {dehors_ok!r}, perdues "
         f"{perdues!r} ( attendu 0,3 + 0,4 ) ; servi {servi!r} = appliquees + perdues a {abs(servi - dehors_ok - perdues):.1e} "
         f"pres ; falsificateur, 0,25 a un vivant a table -> perdues {perdues2!r}")
    dire(ok4a and ok4b and ok4c and erreurs == 6,
         f"V4 crochet : enfant a l ecole ( a = 1 ) -> manque {manque[mg]:g}, adulte 5 -> {fa:g}, enfant 5 -> {fe:g}, "
         f"rations_dehors {r4a}, tableau remis a zero {not rd.any()} ; garde-manger vide : "
         f"manque {manque2[mg]:g}, adulte -> {fa2:g}, enfant -> {fe2:g} ; 0,7 + 0,7 -> manque {manque3[mg]:g} ; "
         f"ValueError {erreurs} / 6")
    return w, p


def v1_journee_de_manque(dire):
    w, p = T.monde(["population"], graine=GRAINE)
    T.jours(w, 2)
    vrai_repas = w.repas
    esp = Espion(); releve = {}

    def repas_provoque():
        t, mt = w.table, w.table.menages
        membres, k = _membres(w)
        besoin = R * np.bincount(k, minlength=mt.n)
        mt.garde_manger[:mt.n] = 0.5 * besoin                  # la journee de manque : la moitie du besoin
        releve["avant"] = t.faim.copy(); releve["membres"] = membres
        releve["c0"] = w.verifier_conservation()[1]["nourriture"]
        W.partager_le_manque = esp
        try: vrai_repas()
        finally: W.partager_le_manque = esp.vrai
        releve["apres"] = t.faim.copy()
        releve["c1"] = w.verifier_conservation()[1]["nourriture"]
    w.repas = repas_provoque
    T.jours(w, 1)
    w.repas = vrai_repas
    manque, part, mineur, k, M, mi = esp.vu[-1]
    viol, mixtes, ecart = verifier(manque, part, mineur, k, M, mi)
    m = releve["membres"]; f0 = releve["avant"][m]; f1 = releve["apres"][m]
    attendu = np.where((manque[k] > 1e-6) & (mi > 0.0), f0 + np.maximum(0.0, mi - C.FAIM_ADAPTATION), np.maximum(0.0, f0 - 1))
    au_bit = bool(np.array_equal(f1, attendu))
    v = np.bincount(k, minlength=M)
    viol_anc = verifier(manque, part, mineur, k, M, manque[k] / np.maximum(v[k], 1))[0]
    enfants_nourris = int((mineur & (mi == 0.0)).sum()); enfants = int(mineur.sum())
    dire(viol == 0 and mixtes >= 20 and au_bit,
         f"V1 journee de manque ( graine {GRAINE}, jour 3 ) : {mixtes} menages mixtes manquent, violations {viol}, faim par "
         f"personne au bit {au_bit} ; {enfants_nourris} mineurs sur {enfants} mangent leur ration")
    dire(viol_anc >= 20, f"V3 falsificateur ( journee provoquee ) : l ancien partage egal viole l invariant dans {viol_anc} menages")
    dc = abs(releve["c1"] - releve["c0"])
    dire(ecart <= 1e-9 and dc <= 1e-6, f"V7 conservation par menage : somme des rations mangees - mange, pire ecart {ecart:.2e} ; "
                        f"nourriture du monde ( verifier_conservation ) avant et apres le repas : ecart {dc:.2e}")


def v6a_identite_unitaire(dire):
    rng = np.random.default_rng(176)
    M = 20_000
    v = rng.integers(1, 12, M)
    k = np.repeat(np.arange(M), v)
    seul_min = rng.random(M) < 0.3                            # 30 % de menages de mineurs seuls, 70 % d adultes seuls
    mineur = seul_min[k]
    gm = np.where(rng.random(M) < 0.3, 0.0, rng.random(M) * v * 1.3)
    besoin = R * v
    manque = besoin - np.minimum(besoin, gm)
    part = np.ones(len(k))
    besoin2 = R * np.bincount(k, weights=part, minlength=M)
    mi = W.partager_le_manque(manque, part, mineur, k, M)
    ancien = manque[k] / np.maximum(v[k], 1)
    faim = rng.random(len(k)) * 30
    affame = manque > 1e-6
    f_anc = np.where(affame[k], faim + np.maximum(0.0, manque[k] / np.maximum(v[k], 1) - C.FAIM_ADAPTATION), np.maximum(0.0, faim - 1))
    f_neu = np.where(affame[k] & (mi > 0.0), faim + np.maximum(0.0, mi - C.FAIM_ADAPTATION), np.maximum(0.0, faim - 1))
    ok = np.array_equal(besoin, besoin2) and np.array_equal(mi[affame[k]], ancien[affame[k]]) and np.array_equal(f_anc, f_neu)
    dire(ok, f"V6a identite unitaire : {M:,} menages ( {int(affame.sum()):,} manquent ), besoin, manque et faim au bit de "
             f"l ancien partage egal : {ok}")


def _monde_v6c(python, mineur=None, numero=None):
    """Un monde de 4 jours ; les soirs 2 a 4 : garde-manger a la moitie du besoin, des a_i FRACTIONNAIRES meles ( 0,24,
    0,5, 0,24 + 0,24 ) chez les mineurs ET les adultes, et une ration perdue ( un habitant seul mange dehors a 15 h et
    meurt avant le repas ). `mineur` / `numero` : le controle ( un chemin a qui l on change l age de la majorite ou le
    tri des membres ). Rend les photos du soir et, chemin en colonnes, le nombre de menages mixtes qui manquent avec au
    moins deux parts non dyadiques ( la ou l ordre des sommes compte )."""
    from .pays import d01_population as PO
    w, p = T.monde(["population"], graine=GRAINE)
    if python: w.utiliser_coeur = False
    vrai = w.repas
    etat = {"jour": 0, "sensibles": 0}

    def repas_du_jour():
        etat["jour"] += 1
        t, mt = w.table, w.table.menages
        if etat["jour"] >= 2:
            membres, k = _membres(w)
            mt.garde_manger[:mt.n] = 0.5 * R * np.bincount(k, minlength=mt.n)
            viv = membres[np.argsort(membres)]
            enf, adu = viv[t.age[viv] < 18], viv[t.age[viv] >= 18]
            servi = []
            for ids, q in ((enf[0::3], 0.24), (enf[1::3], 0.5), (adu[0::4], 0.24), (adu[1::4], 0.5), (enf[0::6], 0.24),
                           (adu[2::8], 0.24), (adu[3::8], 0.7), (adu[3::8], 0.7)):
                if ids.size: w.manger_dehors(ids, q); servi += [q] * ids.size
            v = np.bincount(k, minlength=mt.n)
            seul = viv[(v[t.menage[viv]] == 1) & (t.age[viv] >= 18)]
            if seul.size:                                   # une ration perdue : il a mange dehors, il meurt avant 20 h
                z = int(seul[etat["jour"] % seul.size]); w.manger_dehors([z], 0.3); servi.append(0.3)
                PO.deceder(p, w.habitants[z], "naturelle")
            etat["servi"] = math.fsum(servi)
            membres, k = _membres(w)
            a = np.minimum(1.0, w.repas_dehors[membres]); part = 1.0 - a
            besoin = R * np.bincount(k, weights=part, minlength=mt.n)
            mi = np.bincount(k, weights=(t.age[membres] < 18).astype(float), minlength=mt.n)
            v = np.bincount(k, minlength=mt.n)
            dyad = np.isin(a, (0.0, 0.5, 1.0))
            nd = np.bincount(k, weights=(~dyad).astype(float), minlength=mt.n)
            gm = mt.garde_manger[:mt.n]
            etat["sensibles"] += int(((mi > 0) & (mi < v) & (nd >= 2) & (gm > 0) & (gm < besoin - 1e-6)).sum())
        vrai()
        if etat["jour"] >= 2:
            etat["bilan"] = max(etat.get("bilan", 0.0), abs(etat["servi"] - w.stats_jour["rations_dehors"]
                                                            - w.stats_jour["rations_dehors_perdues"]))
    w.repas = repas_du_jour
    ancien = (W.AGE_MINEUR, W._numero)
    if mineur is not None: W.AGE_MINEUR = mineur
    if numero is not None: W._numero = numero
    photos = []
    try:
        for _ in range(4):
            T.jours(w, 1)
            t, mt = w.table, w.table.menages
            photos.append((t.faim[:t.n].copy(), mt.garde_manger[:mt.n].copy(), w.flux["consomme"]["nourriture"],
                           w.stats_jour.get("rations_dehors"), w.stats_jour.get("menages_sans_nourriture"),
                           w.stats_jour.get("rations_dehors_perdues")))
    finally:
        W.AGE_MINEUR, W._numero = ancien
    return photos, etat["sensibles"], etat.get("bilan")


def _jours_differents(a, b):
    return [j + 1 for j, (x, y) in enumerate(zip(a, b))
            if not (np.array_equal(x[0], y[0]) and np.array_equal(x[1], y[1]) and x[2:] == y[2:])]


def _sans_tri(h):
    return 0


def v6c_python_colonnes(dire):
    (a, sensibles, bil_a), (b, _s, bil_b) = _monde_v6c(False), _monde_v6c(True)
    ecarts = _jours_differents(a, b)
    dire(bil_a is not None and bil_b is not None and max(bil_a, bil_b) <= 1e-9,
         f"V6c audit, chaque soir de 2 a 4 et sur les deux chemins : servi = rations_dehors + rations_dehors_perdues, pire "
         f"ecart {max(bil_a, bil_b):.1e} ( perdues du dernier soir {a[-1][5]!r} : un mort de la journee et les excedents )")
    dire(not ecarts and sensibles >= 20,
         f"V6c repas_python contre repas en colonnes, AU BIT, sous manque, menages mixtes, a_i fractionnaires meles "
         f"( 0,24 / 0,5 / 0,48, mineurs et adultes ) : {sensibles} menages-soirs mixtes qui manquent avec au moins deux "
         f"parts non dyadiques ; rations_dehors {a[-1][3]!r} / {b[-1][3]!r}, perdues {a[-1][5]!r} / {b[-1][5]!r} ; "
         f"jours differents {ecarts or 'aucun'}")
    c, _s, _b = _monde_v6c(True, mineur=-1.0)
    ec = _jours_differents(a, c)
    dire(len(ec) >= 1, f"V6c controle : le comparateur sait echouer ( chemin Python sans mineurs : jours differents {ec} )")
    d, _s, _b = _monde_v6c(True, numero=_sans_tri)
    print(f"INFO   V6c repas_python SANS le tri des membres : jours differents {_jours_differents(a, d) or 'aucun'} "
          f"( le tri garantit l ordre des sommes ; son absence ne se voit que si l ordre d arrivee differe )", flush=True)


def main():
    ok_tout = True

    def dire(ok, texte):
        nonlocal ok_tout
        ok_tout &= bool(ok); print(f"{'PASSE ' if ok else 'ECHOUE'} {texte}", flush=True)
    v2_a_v5(dire)
    v1_journee_de_manque(dire)
    v6a_identite_unitaire(dire)
    v6c_python_colonnes(dire)
    print(f"PORTE DES VIVRES DES ENFANTS : {'FRANCHIE' if ok_tout else 'REFUSEE'}", flush=True)
    return 0 if ok_tout else 1


if __name__ == "__main__":
    sys.exit(main())
