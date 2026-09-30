"""PORTE DES METIERS DE CHAQUE ILE ( 27/09, HMT-126 b ; seuils ecrits avant la premiere mesure ).

La generation ( population.effectifs ) donne a chaque ile les metiers de SES sites. La porte, pour les six iles seules
et pour la carte des six iles ouverte par Altis, au mode par defaut et au mode grec, aux echelles 20 et 12,75 :
  1. aucun metier industriel sans postes : un mineur, un petrolier ou un ouvrier travaille sur un site de son metier,
     et une ile sans ce site n a pas ce metier ;
  2. chaque site est pourvu comme ses postes : a chaque site, les travailleurs du metier au prorata de ses postes, a
     l arrondi du tour de role pres ( une personne, ou la repetition du site dans la liste ponderee : a l echelle 20,
     exactement postes x echelle ; des postes non entiers : une personne, la suite de Sainte-Lague ) ;
  3. la taille du pays ne change pas : autant de travailleurs civils que le melange d E1 a l echelle ;
  4. le surplus remplit les metiers ouverts les plus en dessous de leur part reelle ( ACCUEIL, emploi de la Grece, LFS 2024 ) : ceux
     qui recoivent finissent au meme niveau effectif / part, a une personne pres, les autres sont deja au-dessus ; le
     manque est pris a ceux qui sont le plus au-dessus, de la meme facon ; les
     hoteliers nes du surplus sont ou sont les lits ( POIDS_HOTELLERIE = domaine 28, POIDS_LIEU ), a l arrondi du tour
     de role pres ;
  5. sur Altis et sur la carte des six iles ouverte par Altis, les metiers hors industrie ( regle 9 ) et hors metiers
     ouverts ( regle 4 ) sont ceux de config.ROLES - sauf les patrons, au-dela de l echelle 1,5 ( regle 6 ) ; ( 29/09 :
     jusque-la, Altis portait deja ses metiers, sans surplus ; l industrie au reel lui en donne un ) ;
  6. ( 28/09 ) les patrons : dans le monde construit ( Monde.__init__ donne les entreprises ), chaque patron possede au
     moins une entreprise privee ( un site de production hors ferme ) et chaque entreprise privee a un patron ; il y a
     min( patrons d E1, entreprises ) patrons, les autres sont marchands ; sur Altis, 8 patrons a l echelle 1 et 12 a
     l echelle 1,5, comme avant.
  7. ( 29/09, HMT-140 ) les convoyeurs : quand le domaine 15 porte le fret ( fret="d15" ), max( 4,4 pour 1 000
     habitants EN EMPLOI a l arrondi - au mode par defaut, les nes divises par la survie au recensement, 363 / 500 -,
     une capitale un convoyeur ), au plus ceux d avant l etape, a chaque ile, chaque echelle et
     chaque mode ; le surplus arrive aux AUTRES metiers ouverts ( le total ne change pas ) par le remplissage vers la
     structure reelle ( niveau commun, a une personne pres ). Avec les convois du moteur ( fret="e1", le defaut de
     population.generer ), les convoyeurs d E1, inchanges.
  8. ( 29/09, HMT-140 ) aucun hotelier ne nait des postes liberes : l hotellerie est le tourisme saisonnier du domaine
     28, qui embauche a la saison ; a chaque monde, les hoteliers a la naissance sont ceux d E1 ( 0 ).
  9. ( 29/09, HMT-140 ) l industrie au reel : les postes par unite d echelle d une mine, d une carriere, d une fonderie
     sont le plus grand du reel ( part de son secteur dans l emploi grec de 2024, Eurostat lfsa_egan22d, portee aux
     civils d une unite d echelle et partagee entre les sites du type sur Altis ) et du travail fourni ( heures payees
     du site du type qui travaille le plus, mesure du moteur, en pleins temps de 1 880 heures par an, rapportees aux
     nes ), recalcules ici a part ; chaque site de ces types a postes x echelle travailleurs, a 1,5 personne pres
     ( arrondi du metier et suite de Sainte-Lague ) ; les autres postes ( centrale, pharmacie, puits ) sont ceux d E1.
  10. ( 30/09, HMT-179 ) la cible ACCUEIL est l emploi de la GRECE ( Eurostat lfsa_egan2, 2024, ecrit ici a part :
     A 467,8 ; G 712,9 milliers ), dans population.ACCUEIL et dans l etape des convoyeurs ; falsificateur : les poids de
     l Egee du Nord ( A 15,3 ; G 11,55 ) sont refuses, et ils font monter l emploi agricole de Stratis a la naissance.
Controle positif : une mine ajoutee a la carte de Stratis recoit ses postes x echelle mineurs, pris au surplus ; une
fonderie ajoutee a Stratis recoit son patron ( 1 -> 2 ) ; les convoyeurs d avant l etape sont bien verses aux autres
metiers ouverts ( total egal, a chaque monde de la regle 7 ) ; Altis a l echelle 20 a 99 mineurs a sa mine, 16 ou 17 a
chaque carriere, 46 a chaque fonderie ( regle 9 ).
Falsificateur : l ancienne regle posee a la main ( le surplus rendu ouvrier a la fonderie ) est refusee ; l ancienne
regle des patrons ( 160 patrons pour 12 entreprises a l echelle 20, les marchands en trop redevenus patrons ) aussi ;
l ancienne regle des convoyeurs ( 25 pour 500 habitants ) aussi ; l ancienne cible ( les personnes occupees des unites
locales, l hotellerie a 11,48 ) fait naitre des hoteliers et est refusee ; les anciens postes de d10 ( 10 par mine et
par carriere, 6 par fonderie ) sont refuses, et les postes au seul niveau reel aussi ( la mine qui travaille affamee ).

   python -m monde.porte_metiers"""
import copy, sys, time
import numpy as np
from . import carte as K, config as C, population as PO

ECHELLE = 20.0
ILES = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")


def generer(iles, demographie, echelle=ECHELLE, graine=1, fret="d15"):
    carte = K.Carte(iles=iles)
    H, M = PO.generer(carte, np.random.default_rng(graine), echelle, demographie=demographie, fret=fret)
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


CONVOYEURS_POUR_MILLE = 1000.0 * 45591 / 10375764      # Eurostat H49.4 2024 sur demo_pjan 2024 ( ecrit ici a part )
SURVIE = 363 / 500      # ( 30/09 ) convoyeurs au travail apres le recensement de d04 sur les nes ( graine 71, e8f1ee8 )


def fautes_convoyeurs(carte, avant, eff, habitants, survie=SURVIE):
    """Les fautes de la regle 7 : le compte des convoyeurs ( 4,4 pour 1 000 EN EMPLOI : les nes divises par la survie au
    recensement, 1 pour une population copiee sur le reel ), et le surplus verse aux autres metiers ouverts ( total egal,
    niveau commun du remplissage ), d apres les effectifs d avant l etape et ceux d apres."""
    fautes = []
    vise = max(max(1, int(round(CONVOYEURS_POUR_MILLE * habitants / 1000.0 / survie))), len(carte.capitales))
    attendu = min(avant["convoyeur"], vise)
    if eff["convoyeur"] != attendu:
        fautes.append(f"convoyeurs {eff['convoyeur']} pour {attendu} ( {habitants} habitants, {len(carte.capitales)} capitales )")
    autres = [r for r in PO.ACCUEIL if r != "convoyeur" and PO.metier_possible(carte, r)]
    surplus = avant["convoyeur"] - eff["convoyeur"]
    recu = sum(eff[r] - avant[r] for r in autres)
    if recu != surplus: fautes.append(f"surplus des convoyeurs {surplus}, recus par les autres metiers ouverts {recu}")
    if sum(eff.values()) != sum(avant.values()): fautes.append("la taille du pays a change")
    hors = [r for r in eff if r not in autres + ["convoyeur"] and eff[r] != avant[r]]
    if hors: fautes.append(f"des metiers hors de l etape ont bouge {hors}")
    bouge = [r for r in autres if eff[r] != avant[r]]
    if any(eff[r] < avant[r] for r in bouge): fautes.append("un metier ouvert a perdu des bras")
    if bouge:
        niv = sum(eff[r] for r in bouge) / sum(PO.ACCUEIL[r] for r in bouge)
        for r in bouge:
            if abs(eff[r] - niv * PO.ACCUEIL[r]) > 1.0 + 1e-9: fautes.append(f"convoyeurs verses : {r} {eff[r]} pour {niv * PO.ACCUEIL[r]:.1f}")
        for r in autres:
            if r not in bouge and avant[r] < niv * PO.ACCUEIL[r] - 1.0 - 1e-9: fautes.append(f"convoyeurs verses : {r} devait recevoir")
    return fautes


def fautes_saisonniers(eff, echelle):
    """Regle 8 : les hoteliers a la naissance sont ceux d E1 ( aucun ne nait des postes liberes )."""
    k = C.ROLES["hotellerie"][0]
    e1 = max(1, int(round(k * echelle))) if k else 0
    return [] if eff.get("hotellerie", 0) == e1 else [f"{eff.get('hotellerie', 0)} hoteliers nes des postes liberes ( E1 : {e1} )"]


# regle 9 ( 29/09, HMT-140 ) : les postes des sites de d10, recalcules ici a part des memes sources
EMPLOI_GRECE_2024 = 4265.9                                            # milliers, Eurostat lfsa_egan22d, 15-74 ans
SECTEURS = {"mine": (2.3,), "carriere": (4.6,), "fonderie": (17.1, 47.3)}   # B07 ; B08 ; C24 et C25
SITES_ALTIS = {"mine": 1, "carriere": 3, "fonderie": 2}
MESURE = {"mine": (345.3, 135.8, 200), "carriere": (58.4, 137.3, 200), "fonderie": (98.0, 81.8, 120)}   # h/j, equipe, nes
METIER_DU_SITE = {"mine": "mineur", "carriere": "mineur", "fonderie": "ouvrier"}


def postes_attendus(t):
    """( postes par unite d echelle, reel, travail fourni ) d un site de d10."""
    civils = sum(k for r, (k, _, _) in C.ROLES.items() if r not in ("enfant", "retraite") + PO.MILITAIRES)
    reel = sum(SECTEURS[t]) / EMPLOI_GRECE_2024 * civils / SITES_ALTIS[t]
    h, e, nes = MESURE[t]
    travail = h * 365.0 / 1880.0 * nes / e / 20.0
    return max(reel, travail), reel, travail


def fautes_industrie(carte, t, echelle):
    """Les fautes de la regle 9 : les postes de POSTES_PAR_SITE, et les travailleurs de chaque site de d10 dans la table."""
    fautes = []
    n = t.n; ro = t.role[:n]; tr = t.travail[:n]
    for typ, r in METIER_DU_SITE.items():
        vise = postes_attendus(typ)[0]
        if abs(PO.POSTES_PAR_SITE[r][typ] - vise) > 1e-9: fautes.append(f"postes d une {typ} : {PO.POSTES_PAR_SITE[r][typ]:.4f} pour {vise:.4f}")
        for s in carte.de_type(typ):
            k = int(((ro == PO.CODE_ROLE[r]) & (tr == s.n)).sum())
            if abs(k - vise * echelle) > 1.5 + 1e-9: fautes.append(f"{s.id} : {k} {r}s pour {vise * echelle:.1f}")
    for typ in ("centrale", "pharmacie"):
        if PO.POSTES_PAR_SITE["ouvrier"][typ] != C.OUVRIERS_PAR_SITE[typ]: fautes.append(f"postes d une {typ} changes")
    if PO.POSTES_PAR_SITE["petrolier"] != {"puits": 15}: fautes.append("postes d un puits changes")
    return fautes


def _grec():
    R = PO._cibles("grece")
    return R.emploi_par_habitant() - R.PART_MILITAIRES


def verifier(carte, t, echelle, demographie, fret="d15"):
    """Rend la liste des fautes ( vide : la generation tient les regles 1 a 4, 7, 8 et 9 ) d une population nee avec ce
    fret ( celui de la generation de `t` )."""
    fautes = []
    n = t.n; ro = t.role[:n]; tr = t.travail[:n]
    kw = {} if demographie is None else {"emploi_civil_par_habitant": _grec()}
    eff = PO.effectifs(carte, echelle, fret=fret, **kw)
    avant = PO._effectifs_avant_convoyeurs(carte, echelle)       # les effectifs avant la derniere etape ( regle 7 )
    if fret == "d15": fautes += fautes_convoyeurs(carte, avant, eff, n, SURVIE if demographie is None else 1.0)
    elif eff != avant: fautes.append(f"fret e1 : effectifs changes par l etape des convoyeurs {eff['convoyeur']} / {avant['convoyeur']}")
    fautes += fautes_saisonniers(eff, echelle)
    fautes += fautes_industrie(carte, t, echelle)
    for r, par_site in PO.POSTES_PAR_SITE.items():
        ids = np.nonzero(ro == PO.CODE_ROLE[r])[0]
        sites = carte.de_type(*par_site)
        if not sites and ids.size: fautes.append(f"{r} : {ids.size} sans aucun site")
        types = np.array([carte.par_n[int(x)].type if x >= 0 else "" for x in tr[ids]])
        hors = int((~np.isin(types, list(par_site))).sum()) if ids.size else 0
        if hors: fautes.append(f"{r} : {hors} hors de leurs sites")
        rep = {}
        for l in PO._lieux_ponderes(carte, r): rep[l.n] = rep.get(l.n, 0) + 1
        entiers = all(float(par_site[s.type]).is_integer() for s in sites)
        for s in sites:
            k = int((tr[ids] == s.n).sum())
            vise = eff[r] * par_site[s.type] / max(1, postes_des(carte, r))
            tol = max(1, rep.get(s.n, 0)) if entiers else 1.0          # la suite de Sainte-Lague : une personne
            if abs(k - vise) > tol + 1e-9: fautes.append(f"{r} a {s.id} : {k} pour {vise:.1f} postes")
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
    # 4. le surplus de l industrie, au prorata d ACCUEIL ( avant l etape des convoyeurs, qui a sa regle 7 )
    surplus = sum(max(1, int(round(C.ROLES[r][0] * echelle))) for r in PO.POSTES_PAR_SITE) - \
        sum(avant[r] for r in PO.POSTES_PAR_SITE)
    ouverts = [r for r in PO.ACCUEIL if PO.metier_possible(carte, r)]
    if surplus and ouverts:
        # remplissage vers la structure reelle, verifie par sa propriete ( sans refaire le calcul ) : ceux qui recoivent
        # ( ou cedent ) finissent tous au meme niveau effectif / part reelle, a une personne pres, et ceux qui ne
        # recoivent pas ( ne cedent pas ) sont deja au-dessus ( au-dessous ) de ce niveau ; personne ne va contre le sens
        base = e1_patrons(carte, echelle)
        e1 = {r: base[r] for r in ouverts}
        sens = 1 if surplus > 0 else -1
        bouge = [r for r in ouverts if avant[r] != e1[r]]
        contre = [r for r in bouge if (avant[r] - e1[r]) * sens < 0]
        if contre: fautes.append(f"surplus : {contre} vont contre le sens")
        if sum(avant[r] - e1[r] for r in ouverts) != surplus: fautes.append("surplus : la somme ne tombe pas juste")
        if bouge:
            niv = sum(avant[r] for r in bouge) / sum(PO.ACCUEIL[r] for r in bouge)
            for r in bouge:
                if abs(avant[r] - niv * PO.ACCUEIL[r]) > 1.0 + 1e-9: fautes.append(f"surplus : {r} {avant[r]} pour "
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
    return fautes, eff, surplus, avant


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
    meme = PO.ACCUEIL_CONVOYEURS == PO.ACCUEIL
    print(f"{'PASSE ' if meme else 'ECHOUE'} les parts de l etape des convoyeurs = ACCUEIL : {meme}")
    ok &= meme
    for ech, dem in ((ECHELLE, None), (ECHELLE, "grece"), (12.75, None), (12.75, "grece")):
        for iles in [(i,) for i in ILES] + [tuple(ILES)]:
            carte, t = generer(iles, dem, ech)
            fautes, eff, surplus, avant = verifier(carte, t, ech, dem)
            nom = "+".join(i[:3] for i in iles) + f" x{ech:g}"
            if iles[0] == "Altis":        # 5. hors industrie et metiers ouverts, Altis a les metiers d E1 ( avant la regle 7 )
                e1 = e1_patrons(carte, ech)
                hors = {r: (avant[r], e1[r]) for r in e1 if r not in PO.POSTES_PAR_SITE and r not in PO.ACCUEIL and avant[r] != e1[r]}
                if hors: fautes.append(f"Altis : metiers differents d E1 {hors}")
            ind = {r: eff[r] for r in PO.POSTES_PAR_SITE}
            acc = {r: f"{avant[r]}->{eff[r]}" if avant[r] != eff[r] else eff[r] for r in PO.ACCUEIL}
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
        fautes, eff, surplus, _ = verifier(carte, t, ECHELLE, None)
    finally:
        K.carte_du_pays = reel
    carte0, t0_ = generer(("Stratis",), None)
    _, eff0, surplus0, _ = verifier(carte0, t0_, ECHELLE, None)
    mine = carte.lieux["mine_controle"]
    vus = int(((t.role[:t.n] == PO.CODE_ROLE["mineur"]) & (t.travail[:t.n] == mine.n)).sum())
    vise = int(round(PO.POSTES_PAR_SITE["mineur"]["mine"] * ECHELLE))
    cp = not fautes and vus == vise and surplus0 - surplus == vus
    print(f"{'PASSE ' if cp else 'ECHOUE'} controle positif : une mine posee sur Stratis recoit {vus} mineurs "
          f"( attendus {vise} ), surplus {surplus0:+d} -> {surplus:+d}" + (f" FAUTES {fautes[:3]}" if fautes else ""))
    ok &= cp
    # falsificateur : l ancienne regle ( le surplus a la fonderie, comme ouvriers ) posee a la main
    carte, t = generer(("Stratis",), None)
    fonderie = carte.de_type("fonderie")[0]
    ids = np.nonzero(t.role[:t.n] == PO.CODE_ROLE["paysan"])[0][:int(round(89 * ECHELLE))]
    t.role[ids] = PO.CODE_ROLE["ouvrier"]; t.travail[ids] = fonderie.n
    fautes, _, _, _ = verifier(carte, t, ECHELLE, None)
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
    # falsificateur des convoyeurs : l ancienne regle ( 25 pour 500 habitants ) posee a la main
    carte = K.Carte(iles=("Altis",))
    avant = PO._effectifs_avant_convoyeurs(carte, ECHELLE)
    ancien = dict(avant)
    fautes = fautes_convoyeurs(carte, avant, ancien, sum(avant.values()))
    neuf = PO.effectifs(carte, ECHELLE, fret="d15"); k = avant["convoyeur"] - neuf["convoyeur"]
    fa = bool(fautes)
    print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur des convoyeurs : {ancien['convoyeur']} convoyeurs pour "
          f"{sum(avant.values())} habitants ( l ancienne regle ) {'refuses' if fa else 'NON VUS'} : {fautes[:1]} ; la nouvelle "
          f"regle en verse {k} aux autres metiers ouverts")
    ok &= fa
    # falsificateur de la regle 8 : l ancienne cible ( personnes occupees des unites locales, sbs_r_nuts2021 ) posee a la main
    vieux = {"paysan": 15.3, "marchand": 21.9 * 10156 / 25491, "convoyeur": 21.9 * 1969 / 25491, "hotellerie": 21.9 * 13366 / 25491}
    a, b = PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS
    PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS = vieux, vieux
    try: fs = fautes_saisonniers(PO.effectifs(K.Carte(iles=("Stratis",)), ECHELLE, fret="d15"), ECHELLE)
    finally: PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS = a, b
    fa = bool(fs)
    print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur des saisonniers : l ancienne cible ( hotellerie {vieux['hotellerie']:.2f} ) sur "
          f"Stratis {'refusee' if fa else 'NON VUE'} : {fs[:1]}")
    ok &= fa
    # regle 7, les convois du moteur : le defaut de population.generer est fret="e1", et il garde les convoyeurs d E1
    import inspect
    defaut = inspect.signature(PO.generer).parameters["fret"].default
    for iles in (("Altis",), ("Stratis",)):
        carte, t = generer(iles, None, fret="e1")
        fautes = verifier(carte, t, ECHELLE, None, fret="e1")[0]
        e1 = PO._effectifs_avant_convoyeurs(carte, ECHELLE)["convoyeur"]
        vus = int((t.role[:t.n] == PO.CODE_ROLE["convoyeur"]).sum())
        cp = not fautes and defaut == "e1" and vus == e1
        print(f"{'PASSE ' if cp else 'ECHOUE'} fret e1 ( defaut de la generation : {defaut} ) {iles[0]} x{ECHELLE:g} : {vus} convoyeurs "
              f"pour {e1} d E1" + (f" FAUTES {fautes[:3]}" if fautes else ""))
        ok &= cp
    # regle 10 : la cible ACCUEIL est l emploi national ( LFS 2024 ), et les poids de l Egee du Nord sont refuses
    LFS = {"paysan": 467.8, "marchand": 712.9}
    EL41 = {"paysan": 15.3, "marchand": 21.9 * 712.9 / (712.9 + 240.4 + 398.8)}
    NON_EMPLOI = ("enfant", "retraite", "petit_enfant", "etudiant", "chomeur", "inactif")
    def part_agricole(iles, poids):
        a, b = PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS
        PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS = dict(poids), dict(poids)
        try: eff = PO.effectifs(K.Carte(iles=iles), ECHELLE, fret="d15")
        finally: PO.ACCUEIL, PO.ACCUEIL_CONVOYEURS = a, b
        return eff["paysan"] / sum(v for r, v in eff.items() if r not in NON_EMPLOI)
    juste = PO.ACCUEIL == LFS and PO.ACCUEIL_CONVOYEURS == LFS
    pa = {i: (part_agricole((i,), LFS), part_agricole((i,), EL41)) for i in ("Altis", "Stratis")}
    print(f"{'PASSE ' if juste else 'ECHOUE'} regle 10 : ACCUEIL = emploi de la Grece ( LFS 2024 ) {PO.ACCUEIL} ; part agricole a la "
          f"naissance ( fret d15, x{ECHELLE:g} ) : " + ", ".join(f"{i} {x:.1%} ( Egee du Nord : {y:.1%} )" for i, (x, y) in pa.items()))
    ok &= juste
    fa = EL41 != LFS and pa["Stratis"][1] >= pa["Stratis"][0] + 0.03
    print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur de la regle 10 : les poids de l Egee du Nord sont refuses et font monter "
          f"l emploi agricole de Stratis de {100 * (pa['Stratis'][1] - pa['Stratis'][0]):.1f} points")
    ok &= fa
    # regle 9 : controle positif ( Altis a l echelle 20 ) et deux falsificateurs ( anciens postes, reel seul )
    carte, t = generer(("Altis",), None)
    fautes = fautes_industrie(carte, t, ECHELLE)
    ro, tr = t.role[:t.n], t.travail[:t.n]
    vus = {s.id: int(((ro == PO.CODE_ROLE[METIER_DU_SITE[s.type]]) & (tr == s.n)).sum()) for s in carte.de_type(*METIER_DU_SITE)}
    detail = {k: (round(postes_attendus(k)[1], 3), round(postes_attendus(k)[2], 3)) for k in METIER_DU_SITE}
    cp = not fautes and vus.get("Mine01") == 99 and all(v in (16, 17) for k, v in vus.items() if k.startswith("quarry")) \
        and all(v == 46 for k, v in vus.items() if k.startswith("factory"))
    print(f"{'PASSE ' if cp else 'ECHOUE'} controle positif de l industrie : Altis x{ECHELLE:g}, {vus} ; ( reel, travail ) par unite "
          f"{detail}" + (f" FAUTES {fautes[:3]}" if fautes else ""))
    ok &= cp
    for nom, postes in (("les anciens postes ( 10, 10, 6 )", {"mine": 10, "carriere": 10, "fonderie": 6}),
                        ("les postes au seul niveau reel", {k: postes_attendus(k)[1] for k in METIER_DU_SITE})):
        garde = {r: dict(v) for r, v in PO.POSTES_PAR_SITE.items()}
        for k, v in postes.items(): PO.POSTES_PAR_SITE[METIER_DU_SITE[k]][k] = v
        try:
            carte, t = generer(("Altis",), None)
            fautes = fautes_industrie(carte, t, ECHELLE)
        finally:
            for r, v in garde.items(): PO.POSTES_PAR_SITE[r] = v
        fa = bool(fautes)
        print(f"{'PASSE ' if fa else 'ECHOUE'} falsificateur de l industrie : {nom} {'refuses' if fa else 'NON VUS'} : {fautes[:3]}")
        ok &= fa
    print(f"PORTE DES METIERS DES ILES : {'FRANCHIE' if ok else 'NON FRANCHIE'} ( {time.perf_counter() - t0:.0f} s )")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
