"""PORTE DES METIERS DE CHAQUE ILE ( 27/09, HMT-126 b ; seuils ecrits avant la premiere mesure ).

La generation ( population.effectifs ) donne a chaque ile les metiers de SES sites. La porte, pour les six iles seules
et pour la carte des six iles ouverte par Altis, au mode par defaut et au mode grec, aux echelles 20 et 12,75 :
  1. aucun metier industriel sans postes : un mineur, un petrolier ou un ouvrier travaille sur un site de son metier,
     et une ile sans ce site n a pas ce metier ;
  2. chaque site est pourvu comme ses postes : a chaque site, les travailleurs du metier au prorata de ses postes, a
     l arrondi du tour de role pres ( une personne, ou la repetition du site dans la liste ponderee : a l echelle 20,
     exactement postes x echelle ) ;
  3. la taille du pays ne change pas : autant de travailleurs civils que le melange d E1 a l echelle ;
  4. le surplus remplit les metiers ouverts les plus en dessous de leur part reelle ( ACCUEIL, Egee du Nord ) : ceux
     qui recoivent finissent au meme niveau effectif / part, a une personne pres, les autres sont deja au-dessus ; le
     manque est pris a ceux qui sont le plus au-dessus, de la meme facon ; les
     hoteliers nes du surplus sont ou sont les lits ( POIDS_HOTELLERIE = domaine 28, POIDS_LIEU ), a l arrondi du tour
     de role pres ;
  5. Altis porte deja ses metiers : sur Altis et sur la carte des six iles ouverte par Altis, les effectifs sont ceux
     de config.ROLES, sans surplus - sauf ( HMT-143, 29/09 ) les postes que la raffinerie a l effectif reel libere : les
     ouvriers en perdent exactement ce nombre, les metiers ouverts le recoivent, et c est tout le surplus ( l identite au bit est prouvee par les portes des domaines et des colonnes ) - sauf
     les patrons, au-dela de l echelle 1,5 ( regle 6 ) ;
  6. ( 28/09 ) les patrons : dans le monde construit ( Monde.__init__ donne les entreprises ), chaque patron possede au
     moins une entreprise privee ( un site de production hors ferme ) et chaque entreprise privee a un patron ; il y a
     min( patrons d E1, entreprises ) patrons, les autres sont marchands ; sur Altis, 8 patrons a l echelle 1 et 12 a
     l echelle 1,5, comme avant.
Controle positif : une mine ajoutee a la carte de Stratis recoit ses 10 x echelle mineurs, pris au surplus ; une
fonderie ajoutee a Stratis recoit son patron ( 1 -> 2 ).
Falsificateur : l ancienne regle posee a la main ( le surplus rendu ouvrier a la fonderie ) est refusee ; l ancienne
regle des patrons ( 160 patrons pour 12 entreprises a l echelle 20, les marchands en trop redevenus patrons ) aussi.

   python -m monde.porte_metiers"""
import copy, sys, time
import numpy as np
from . import carte as K, config as C, population as PO

ECHELLE = 20.0
ILES = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")


def generer(iles, demographie, echelle=ECHELLE, graine=1):
    carte = K.Carte(iles=iles)
    H, M = PO.generer(carte, np.random.default_rng(graine), echelle, demographie=demographie)
    return carte, H._t


def postes_des(carte, r): return PO.postes_des_sites(carte, r)


def e1_patrons(carte, echelle):
    """Les effectifs d E1 a l echelle, apres la regle 6 : min( patrons, entreprises privees ) patrons, les autres
    marchands ( calcule ici sans population.effectifs )."""
    e1 = {r: (max(1, int(round(k * echelle))) if k else 0) for r, (k, _, _) in C.ROLES.items()}
    n = len(carte.de_type(*[t for t in C.RECETTES if t != "ferme"]))
    garde = min(e1["patron"], n)
    e1["marchand"] += e1["patron"] - garde; e1["patron"] = garde
    return e1


def verifier(carte, t, echelle, demographie):
    """Rend la liste des fautes ( vide : la generation tient les cinq regles )."""
    fautes = []
    n = t.n; ro = t.role[:n]; tr = t.travail[:n]
    eff = PO.effectifs(carte, echelle)
    for r, par_site in PO.POSTES_PAR_SITE.items():
        ids = np.nonzero(ro == PO.CODE_ROLE[r])[0]
        sites = carte.de_type(*par_site)
        if not sites and ids.size: fautes.append(f"{r} : {ids.size} sans aucun site")
        types = np.array([carte.par_n[int(x)].type if x >= 0 else "" for x in tr[ids]])
        hors = int((~np.isin(types, list(par_site))).sum()) if ids.size else 0
        if hors: fautes.append(f"{r} : {hors} hors de leurs sites")
        rep = {}
        for l in PO._lieux_ponderes(carte, r): rep[l.n] = rep.get(l.n, 0) + 1
        for s in sites:
            k = int((tr[ids] == s.n).sum())
            vise = eff[r] * par_site[s.type] / max(1, postes_des(carte, r))
            if abs(k - vise) > max(1, rep.get(s.n, 0)) + 1e-9: fautes.append(f"{r} a {s.id} : {k} pour {vise:.0f} postes")
    # 3. la taille : les civils d E1 a l echelle
    civils_e1 = sum(max(1, int(round(k * echelle))) for r, (k, _, _) in C.ROLES.items()
                    if k and r not in ("enfant", "retraite") + PO.MILITAIRES)
    civils = sum(v for r, v in eff.items() if r not in ("enfant", "retraite") + PO.MILITAIRES)
    if civils != civils_e1: fautes.append(f"civils {civils} contre {civils_e1} au melange d E1")
    if demographie is None and n != sum(eff.values()): fautes.append(f"{n} habitants pour {sum(eff.values())} effectifs")
    # la table porte les effectifs annonces ( les metiers civils ; au mode par defaut, tous )
    sans_base = not PO.metier_possible(carte, "soldat")          # les soldats d une ile sans base sont policiers
    for r, v in eff.items():
        if demographie is not None and (r in ("enfant", "retraite") + PO.MILITAIRES or v == 0): continue
        if sans_base and r in PO.MILITAIRES + ("policier",): continue
        k = int((ro == PO.CODE_ROLE[r]).sum())
        if k != v: fautes.append(f"{r} : {k} dans la table pour {v} annonces")
    # 4. le surplus, au prorata d ACCUEIL
    surplus = sum(max(1, int(round(C.ROLES[r][0] * echelle))) for r in PO.POSTES_PAR_SITE) - \
        sum(eff[r] for r in PO.POSTES_PAR_SITE)
    ouverts = [r for r in PO.ACCUEIL if PO.metier_possible(carte, r)]
    if surplus and ouverts:
        # remplissage vers la structure reelle, verifie par sa propriete ( sans refaire le calcul ) : ceux qui recoivent
        # ( ou cedent ) finissent tous au meme niveau effectif / part reelle, a une personne pres, et ceux qui ne
        # recoivent pas ( ne cedent pas ) sont deja au-dessus ( au-dessous ) de ce niveau ; personne ne va contre le sens
        base = e1_patrons(carte, echelle)
        e1 = {r: base[r] for r in ouverts}
        sens = 1 if surplus > 0 else -1
        bouge = [r for r in ouverts if eff[r] != e1[r]]
        contre = [r for r in bouge if (eff[r] - e1[r]) * sens < 0]
        if contre: fautes.append(f"surplus : {contre} vont contre le sens")
        if sum(eff[r] - e1[r] for r in ouverts) != surplus: fautes.append("surplus : la somme ne tombe pas juste")
        if bouge:
            niv = sum(eff[r] for r in bouge) / sum(PO.ACCUEIL[r] for r in bouge)
            for r in bouge:
                if abs(eff[r] - niv * PO.ACCUEIL[r]) > 1.0 + 1e-9: fautes.append(f"surplus : {r} {eff[r]} pour "
                                                                                    f"{niv * PO.ACCUEIL[r]:.1f} au niveau commun")
            for r in ouverts:
                if r not in bouge and (e1[r] - niv * PO.ACCUEIL[r]) * sens < -1.0 - 1e-9:
                    fautes.append(f"surplus : {r} ( {e1[r]} ) devait bouger ( niveau {niv * PO.ACCUEIL[r]:.1f} )")
    # les hoteliers nes au travail sont ou sont les lits
    k = PO.CODE_ROLE["hotellerie"]
    hot = tr[(ro == k) & (tr >= 0)]
    if hot.size >= 50:
        lieux = PO._lieux_ponderes(carte, "hotellerie")
        attendu = {}
        for l in lieux: attendu[l.n] = attendu.get(l.n, 0) + 1
        tot = sum(attendu.values())
        for x, a in attendu.items():
            vu = int((hot == x).sum())
            if abs(vu - hot.size * a / tot) > a + 1e-9: fautes.append(f"hotellerie a {carte.par_n[x].id} : {vu} pour "
                                                                        f"{hot.size * a / tot:.1f}")
    return fautes, eff, surplus


def fautes_patrons(w, echelle):
    """Les fautes de la regle 6 dans un monde construit : patrons sans entreprise, entreprise privee sans patron,
    compte des patrons different de min( E1, entreprises )."""
    t = w.table; n = t.n
    patrons = set(np.nonzero(t.role[:n] == PO.CODE_ROLE["patron"])[0].tolist())
    privees = [e for e in w.entreprises.values() if e.type != "ferme"]
    proprietaires = {e.proprietaire.id for e in privees if e.proprietaire is not None}
    fautes = []
    sans = patrons - proprietaires
    if sans: fautes.append(f"{len(sans)} patrons sans entreprise")
    orphelines = [e.id for e in privees if e.proprietaire is None]
    if orphelines: fautes.append(f"entreprises sans patron {orphelines[:3]}")
    vise = min(max(1, int(round(C.ROLES["patron"][0] * echelle))), len(privees))
    if len(patrons) != vise: fautes.append(f"{len(patrons)} patrons pour {vise} attendus")
    return fautes, len(patrons), len(privees)


def main():
    t0 = time.perf_counter()
    ok = True
    from .pays import d28_tourisme as TO
    meme = PO.POIDS_HOTELLERIE == TO.POIDS_LIEU
    print(f"{'PASSE ' if meme else 'ECHOUE'} poids des hotels = ceux du domaine 28 : {PO.POIDS_HOTELLERIE} / {TO.POIDS_LIEU}")
    ok &= meme
    for ech, dem in ((ECHELLE, None), (ECHELLE, "grece"), (12.75, None), (12.75, "grece")):
        for iles in [(i,) for i in ILES] + [tuple(ILES)]:
            carte, t = generer(iles, dem, ech)
            fautes, eff, surplus = verifier(carte, t, ech, dem)
            nom = "+".join(i[:3] for i in iles) + f" x{ech:g}"
            if iles[0] == "Altis":        # 5. Altis porte deja ses metiers, sauf la raffinerie a l effectif reel ( HMT-143 )
                e1 = e1_patrons(carte, ech)
                libres = e1["ouvrier"] - max(1, int(round(PO.postes_des_sites(carte, "ouvrier") * ech)))
                autres = [r for r in eff if r != "ouvrier" and r not in PO.ACCUEIL]
                ok5 = (all(eff[r] == e1[r] for r in autres) and eff["ouvrier"] == e1["ouvrier"] - libres and surplus == libres
                       and sum(eff[r] for r in PO.ACCUEIL) == sum(e1[r] for r in PO.ACCUEIL) + libres)
                if not ok5: fautes.append(f"Altis : effectifs {eff} : E1 {e1} moins {libres} postes liberes par la raffinerie attendus")
            ind = {r: eff[r] for r in PO.POSTES_PAR_SITE}
            acc = {r: eff[r] for r in PO.ACCUEIL}
            print(f"{'PASSE ' if not fautes else 'ECHOUE'} {nom:30s} {dem or 'defaut':6s} {t.n:6d} hab. | industrie {ind} "
                  f"| surplus {surplus:+d} | metiers ouverts {acc}" + (f" | FAUTES {fautes[:4]}" if fautes else ""),
                  flush=True)
            ok &= not fautes
    # 6. les patrons, dans les mondes construits
    from . import monde as W
    for ech, dem in ((ECHELLE, None), (ECHELLE, "grece"), (1.0, None), (1.5, None)):
        for iles in [(i,) for i in ILES] + [tuple(ILES)]:
            if ech < 2 and iles[0] != "Altis": continue
            w = W.Monde(graine=1, iles=iles, echelle=ech, demographie=dem)
            fautes, npat, nent = fautes_patrons(w, ech)
            if iles[0] == "Altis" and ech <= 1.5 and npat != max(1, int(round(C.ROLES["patron"][0] * ech))):
                fautes.append(f"Altis a l echelle {ech} : {npat} patrons, E1 en a {max(1, int(round(C.ROLES['patron'][0] * ech)))}")
            nom = "+".join(i[:3] for i in iles) + f" x{ech:g}"
            print(f"{'PASSE ' if not fautes else 'ECHOUE'} patrons {nom:30s} {dem or 'defaut':6s} {npat} patrons pour {nent} "
                  f"entreprises privees" + (f" | FAUTES {fautes}" if fautes else ""), flush=True)
            ok &= not fautes
    # controle positif : une mine posee sur Stratis recoit ses mineurs
    reel = K.carte_du_pays
    def avec_mine(ile):
        c = reel(ile)
        if c is not None and ile == "Stratis":
            c = copy.deepcopy(c); f = next(l for l in c["lieux"] if l["type"] == "fonderie")
            c["lieux"].append({"id": "mine_controle", "type": "mine", "pos": [f["pos"][0] + 500, f["pos"][1]]})
        return c
    K.carte_du_pays = avec_mine
    try:
        carte, t = generer(("Stratis",), None)
        fautes, eff, surplus = verifier(carte, t, ECHELLE, None)
    finally:
        K.carte_du_pays = reel
    carte0, t0_ = generer(("Stratis",), None)
    _, eff0, surplus0 = verifier(carte0, t0_, ECHELLE, None)
    mine = carte.lieux["mine_controle"]
    vus = int(((t.role[:t.n] == PO.CODE_ROLE["mineur"]) & (t.travail[:t.n] == mine.n)).sum())
    cp = not fautes and vus == int(10 * ECHELLE) and surplus0 - surplus == vus
    print(f"{'PASSE ' if cp else 'ECHOUE'} controle positif : une mine posee sur Stratis recoit {vus} mineurs "
          f"( attendus {int(10 * ECHELLE)} ), surplus {surplus0:+d} -> {surplus:+d}" + (f" FAUTES {fautes[:3]}" if fautes else ""))
    ok &= cp
    # falsificateur : l ancienne regle ( le surplus a la fonderie, comme ouvriers ) posee a la main
    carte, t = generer(("Stratis",), None)
    fonderie = carte.de_type("fonderie")[0]
    ids = np.nonzero(t.role[:t.n] == PO.CODE_ROLE["paysan"])[0][:int(round(89 * ECHELLE))]
    t.role[ids] = PO.CODE_ROLE["ouvrier"]; t.travail[ids] = fonderie.n
    fautes, _, _ = verifier(carte, t, ECHELLE, None)
    fa = bool(fautes)
    print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur : {ids.size} ouvriers de plus a {fonderie.id} ( l ancienne regle ) "
          f"{'refuses' if fa else 'NON VUS'} : {fautes[:2]}")
    ok &= fa
    # controle positif des patrons : une fonderie posee sur Stratis recoit son patron
    def avec_fonderie(ile):
        c = reel(ile)
        if c is not None and ile == "Stratis":
            c = copy.deepcopy(c); f = next(l for l in c["lieux"] if l["type"] == "fonderie")
            c["lieux"].append({"id": "fonderie_controle", "type": "fonderie", "pos": [f["pos"][0], f["pos"][1] + 500]})
        return c
    w0 = W.Monde(graine=1, iles=("Stratis",), echelle=ECHELLE)
    K.carte_du_pays = avec_fonderie
    try: w1 = W.Monde(graine=1, iles=("Stratis",), echelle=ECHELLE)
    finally: K.carte_du_pays = reel
    f0, n0, _ = fautes_patrons(w0, ECHELLE); f1, n1, _ = fautes_patrons(w1, ECHELLE)
    neuve = w1.entreprises["fonderie_controle"].proprietaire
    cp = not f0 and not f1 and (n0, n1) == (1, 2) and neuve is not None and neuve.role == "patron"
    print(f"{'PASSE ' if cp else 'ECHOUE'} controle positif des patrons : une fonderie posee sur Stratis, patrons {n0} -> {n1}, "
          f"la fonderie neuve a pour patron {getattr(neuve, 'id', None)} ( {getattr(neuve, 'role', None)} )")
    ok &= cp
    # falsificateur des patrons : l ancienne regle posee a la main ( 148 marchands redevenus patrons sur Altis x20 )
    w = W.Monde(graine=1, iles=("Altis",), echelle=ECHELLE)
    t = w.table
    ids = np.nonzero(t.role[:t.n] == PO.CODE_ROLE["marchand"])[0][:148]
    t.role[ids] = PO.CODE_ROLE["patron"]
    fautes, npat, nent = fautes_patrons(w, ECHELLE)
    fa = bool(fautes)
    print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur des patrons : {npat} patrons pour {nent} entreprises ( l ancienne regle ) "
          f"{'refuses' if fa else 'NON VUS'} : {fautes[:2]}")
    ok &= fa
    print(f"PORTE DES METIERS DES ILES : {'FRANCHIE' if ok else 'NON FRANCHIE'} ( {time.perf_counter() - t0:.0f} s )")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
