"""PORTES DE LA GUERRE DES ILES, v0 ( ecrites avant la mesure, 26/09 ). Sans Arma : le cote Arma est un jouet.

G1 ZONES : la mission officielle de Malden rend 21 zones dont 2 bases, 405 points par minute sur ses 19 secteurs ;
   la capitale La Trinite est dans un secteur de valeur 30 ; la centrale est rattachee a une zone ( rayon
   d influence ). Controle positif : sans rayon d influence, la centrale est hors de toute zone.
G2 BOURSE : l exemple chiffre ( 10 000 unites de recettes, defense 40 %, 1,15 euro l unite, 50 militaires -> 46
   points ; 1 000 militaires -> 4,6 ) ; une recette negative ne verse rien ; une part de defense hors [0 ; 1] est
   refusee.
G3 RELEVE : la premiere releve rend 0 ; deux jours plus tard, les recettes = la somme de tresor.serie de ces deux jours
   ( au milliardieme ) et jours_clos = 2. Controle : une releve aussitot apres rend 0 et 0 jour.
G4 OCCUPATION ( AMENDEE le 26/09 APRES un echec : la v0 occupait par la quarantaine et mesurait la presence sur le
   lieu ; elle a ECHOUE - presence 1,0 sous occupation - parce qu un paysan qui vit sur sa ferme n a pas a sortir
   pour y travailler. Mecanisme et mesure changes ensemble, voir guerre/moteur.py. Puis fenetre portee a TROIS jours :
   le premier essai du sequestre tombait sur un dimanche et le lundi de Pentecote orthodoxe ( 18/06/2035 ), ou le
   temoin non plus ne livre rien ; on compare donc les fermes LES JOURS OU LE TEMOIN LIVRE ) : sur trois jours
   d occupation, la ferme occupee ne livre AUCUNE ration ( Exploitation.livre_j ), la ferme temoin en livre ; la ferme
   occupee en livrait avant ( controle positif ) et en relivre apres la liberation ( sept jours ) ; l occupation la
   compte parmi ses fermes sous sequestre. La conservation de Malden tient.
G5 HORLOGE ( jouet cote Arma, horloge simulee ) : la zone de Houdan passe a l envahisseur au tour 2 et revient au
   tour 4 -> le moteur la voit occupee apres le tour 2, liberee apres le tour 4 ; les points verses = la formule
   recalculee sur les releves ; une zone ennemie sans lieu n occupe rien.
G6 PONT : lire_tour rend zones et camps d un tour bien forme ; une zone manquante ou inconnue leve Incomplet, jamais
   « a personne » ; un versement negatif ou non fini est refuse avant d etre ecrit.
G7 MISSION : parentheses, crochets, accolades equilibres dans le SQF ; GUERRE_VERSION = arma.VERSION_MISSION ;
   GUERRE_PLAFOND = bourse.PLAFOND_ARMA ; 8 hommes par escouade dans chaque camp.
G8 PASSAGE D ANNEE ( ajoutee le 26/09 avec la correction de d06_etat._cloture ) : une ile seule passe le 1er janvier
   2036 ( jour 200 ) sans planter, et son exercice 2036 s ouvre a la cloture du 31 decembre, pas avant. Elle a su
   echouer : sans la correction, l ile mourait le 31 decembre a 18 h ( ValueError « jour 0 hors de l exercice » ).
G9 SOLDATS SUIVIS ( option 1 de Younes, ecrite avant la mesure ) : apres deux tours ( jouet cote Arma ), chaque ile a
   mobilise 32 soldats, tous vus au front, tous ABSENTS ( poste voyage, dans w.absents ) ; trois soldats de Malden tues
   dans Arma meurent dans le moteur, cause « combat », ne sont plus absents, et Malden compte trois militaires de
   moins ; les 29 autres restent vivants et absents ( controle : les trois etaient vivants juste avant ) ; un releve
   deplace leurs positions ; la conservation de Malden tient le lendemain. Le pont lit U et MORT, refuse un numero
   de front hors [1 ; 999 999].
G10 LA GUERRE COUTE AU TRESOR ( ecrite avant la mesure ) : la premiere releve fixe la base et ne paie rien ; 1 150
   points de plus depenses dans Arma = 115 000 euros d armement importe ( FOB ) plus le fret : la caisse de l Etat
   baisse exactement de ce qui est paye ; le soir, la ligne defense ( achats ) du budget monte d au moins le FOB ; la
   meme depense rendue deux fois ne paie qu une fois ( controle ) ; la conservation de Malden tient.
G11 LE GOUVERNEMENT VOIT LA GUERRE ( ecrite avant la mesure ) : Malden gouvernee par un code sonde, Stratis par les
   regles, deux jours : le code de Malden a recu chaque matin un bulletin avec la section guerre ( soldats au front,
   morts au combat, cout ) et c est lui qui a decide ( evenement decision_gouvernement : cerveau code:... ) ; Stratis
   a decide par les regles, sans une seule bascule « cerveau indisponible ».
G12 LE CONSEIL DE GUERRE ( sans Qwen ; ecrite avant la mesure ) : le scenario lu dans le journal de l essai 9 a des taux
   positifs ; un petit Malden en guerre ( 3 jours ) gouverne par le code de Qwen voit des soldats au front, paie des
   armes, a sa ferme occupee sous sequestre, tient sa conservation et rend une note ; dans un archipel, la releve d un
   gouvernement par le conseil change qui decide des le lendemain ; un code interdit ( import ) est refuse.

   python -m guerre.porte_guerre"""
import math, os, re, sys, time
from . import bourse as B, zones as Z, arma as A, moteur as GM
from .horloge import HorlogeDeGuerre

MISSION = os.path.join(Z.ICI, "mission", "GuerreIles.Malden")
OCCUPEE, TEMOIN = "Malden_V_Houdan", "Malden_V_Dourdan"


def livraisons(arc, ile, lieux, jours):
    """Jour par jour du moteur : pour chaque ferme, le plus grand livre_j du jour ( rations livrees ce jour-la )."""
    from monde.pays import d09_agriculture as AG
    p = arc.iles[ile].w.pays
    out = []
    for _ in range(jours):
        best = {l: 0.0 for l in lieux}
        for _ in range(144):
            arc.un_pas()
            for l in lieux: best[l] = max(best[l], AG.exploitation_de(p, l).livre_j)
        out.append(best)
    return out


def couverture(w, zones):
    """Pour chaque zone : ses fermes ( sequestre ), ses sites du moteur ( choc ), ses sites non couverts."""
    p = w.pays; out = {"fermes": 0, "moteur": 0, "non_couverts": []}
    for z in zones:
        for l in z["lieux"]:
            e = w.entreprises.get(l)
            if e is None: continue
            dom = p.repris.get(e.id)
            if dom == "agriculture": out["fermes"] += 1
            elif dom is None: out["moteur"] += 1
            else: out["non_couverts"].append(f"{l}:{dom}")
    return out


def sqf_equilibre(texte):
    """Parentheses, crochets et accolades equilibres, chaines et commentaires // retires."""
    s = re.sub(r'"(?:[^"]|"")*"', '""', texte)
    s = re.sub(r"//[^\n]*", "", s)
    pile, paires = [], {")": "(", "]": "[", "}": "{"}
    for c in s:
        if c in "([{": pile.append(c)
        elif c in ")]}":
            if not pile or pile.pop() != paires[c]: return False
    return not pile


class Scenario(A.FauxGuerre):
    """Le jouet, avec des changements de proprietaire au debut de certains tours."""
    def __init__(self, zones, script):
        super().__init__(zones); self.script = script

    def tour(self, points, reserves=None):
        for n, camp in self.script.get(self.tours + 1, {}).items(): self.proprio[n] = camp
        return super().tour(points, reserves)


def main():
    ok = {}
    if not os.path.exists(os.path.join(MISSION, "mission.sqm")):
        from . import fabriquer_mission as FM
        print(f"   mission.sqm de Bohemia lu dans le jeu ( empreinte {FM.fabriquer()} )", flush=True)
    sqm = open(os.path.join(MISSION, "mission.sqm"), encoding="latin-1").read()
    carte = Z.carte_de_guerre(sqm, "Malden")
    zs = carte["zones"]
    sect = [z for z in zs if z["genre"] == "secteur"]
    zone_de = {l: z["n"] for z in zs for l in z["lieux"]}
    # G1
    lt = next(z for z in zs if "Malden_C_LaTrinite" in z["lieux"])
    lieux = __import__("json").load(open(os.path.join(Z.PAYS, "malden.json")))["lieux"]
    _, hors0 = Z.rattacher(zs, lieux, rayon=0.0)
    ok["G1 21 zones, 2 bases, 405 points par minute"] = (len(zs) == 21 and len(sect) == 19 and sum(z["valeur"] for z in sect) == 405)
    ok["G1 La Trinite dans un secteur de valeur 30"] = lt["genre"] == "secteur" and lt["valeur"] == 30
    ok["G1 la centrale rattachee ; controle : hors zone sans rayon"] = ("centrale01" in zone_de) and ("centrale01" in hors0)
    # G2
    p50, f50, _ = B.points_de_la_minute(10000, 0.4, 1.15, 50)
    p1000, f1000, _ = B.points_de_la_minute(10000, 0.4, 1.15, 1000)
    pneg, _, _ = B.points_de_la_minute(-5000, 0.4, 1.15, 50)
    try: B.points_de_la_minute(1, 1.5, 1.15, 1); refuse = False
    except ValueError: refuse = True
    ok["G2 bourse : 46 et 4,6 points, rien sur recette negative, part hors bornes refusee"] = (
        abs(p50 - 46.0) < 1e-9 and abs(p1000 - 4.6) < 1e-9 and f1000 == 0.1 and pneg == 0.0 and refuse)
    # G3, G4, G5 : un petit archipel Malden + Stratis, sequentiel ( on lit les iles de l interieur )
    from monde.archipel import Archipel
    t0 = time.time()
    arc = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w = arc.iles["Malden"].w
    r0 = arc.commande("Malden", "guerre_releve")
    arc.jours(2)
    r2 = arc.commande("Malden", "guerre_releve")
    serie = [s for s in GM._etat(w).tresor.serie]
    attendu = math.fsum(s[1] for s in serie[-2:])
    r2b = arc.commande("Malden", "guerre_releve")
    ok["G3 releve : 0 au depart, puis la somme des deux jours ; controle aussitot apres = 0"] = (
        r0["recettes"] == 0 and r0["jours_clos"] == 0 and r2["jours_clos"] == 2 and abs(r2["recettes"] - attendu) <= 1e-9 * max(1, abs(attendu))
        and r2b["recettes"] == 0 and r2b["jours_clos"] == 0)
    print(f"   releve : {r2['recettes']:.0f} {r2['monnaie']} en 2 jours, defense {r2['part_defense']:.3f}, {r2['militaires']} militaires", flush=True)
    # G4
    print(f"   couverture des zones de Malden : {couverture(w, zs)}", flush=True)
    zo = zone_de[OCCUPEE]
    lz = next(z["lieux"] for z in zs if z["n"] == zo)
    avant = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 3)
    occ = arc.commande("Malden", "occuper", zo, lz, True)
    pendant = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 3)
    arc.commande("Malden", "occuper", zo, lz, False)
    apres = livraisons(arc, "Malden", (OCCUPEE, TEMOIN), 7)
    tenue = arc.commande("Malden", "tenue")
    r = lambda js: [(round(j[OCCUPEE]), round(j[TEMOIN])) for j in js]
    print(f"   rations livrees par jour ( occupee, temoin ) : avant {r(avant)}, occupee {r(pendant)}, liberee {r(apres)}", flush=True)
    jours_temoin = lambda js: [j for j in js if j[TEMOIN] > 0]
    ok["G4 controle positif : les jours ou le temoin livre, la ferme livrait avant l occupation"] = (
        bool(jours_temoin(avant)) and all(j[OCCUPEE] > 0 for j in jours_temoin(avant)))
    ok["G4 occupee : la ferme sous sequestre ne livre rien, le temoin livre"] = (
        all(j[OCCUPEE] == 0 for j in pendant) and bool(jours_temoin(pendant)) and occ["fermes"] == [OCCUPEE])
    ok["G4 liberee : les jours ou le temoin livre, la ferme relivre"] = (
        bool(jours_temoin(apres)) and all(j[OCCUPEE] > 0 for j in jours_temoin(apres)))
    ok["G4 conservation de Malden"] = bool(tenue[0])
    # G5
    vide = next(z["n"] for z in sect if not z["lieux"])
    horloge = iter(x / 432.0 for x in range(10 ** 8))          # 432 pas du moteur ( 3 jours ) par periode d une seconde simulee
    arma = Scenario(zs, {2: {zo: "EAST", vide: "EAST"}, 4: {zo: "WEST"}})
    h = HorlogeDeGuerre(arc, arma, carte, periode_s=1.0, horloge=lambda: next(horloge)).ouvrir()
    vus, tours = [], []
    for _ in range(4):
        h.boucle(tours=h.tours + 1)
        vus.append(sorted(getattr(arc.iles["Malden"].w, "occupations", {})))      # lu sans releve : une releve de plus volerait des recettes
        tours.append(h.derniere)
    ok["G5 occupee apres le tour 2, liberee apres le tour 4, zone vide jamais occupee"] = (
        vus[0] == [] and vus[1] == [zo] and vus[2] == [zo] and vus[3] == [])
    formule = all(abs(B.points_de_la_minute(r["recettes"], r["part_defense"], r["euros_par_unite"], r["militaires"])[0]
                      - l["points"][r["camp"]]) < 1e-9 for l in tours for r in l["iles"].values())
    somme = all(abs(arma.verse[c] - math.fsum(l["points"][c] for l in tours)) < 1e-6 for c in ("EAST", "WEST"))
    ok["G5 les points verses suivent la formule, et Arma a recu leur somme"] = formule and somme
    print(f"   horloge : {h.tours} tours ; points par tour {[{c: round(v, 1) for c, v in l['points'].items()} for l in tours]} ; "
          f"jours du moteur par tour {[l['iles']['Malden']['jours_clos'] for l in tours]}", flush=True)
    arc.fermer()
    # G6
    bonnes = [("VERSE", [0, 10.0, 10.0]), ("VERSE", [1, 20.0, 20.0])] + \
             [("ZONE", [round(z["x"]), round(z["y"]), 1 if z["n"] != zo else 0]) for z in zs] + \
             [("FORCES", [0, 8, 1, 0, 1150, 1]), ("FORCES", [1, 16, 2, 3, 2300, 2]), ("CIBLE", [0, 7102, 6096]),
              ("CIBLE", [1, -1, -1]), ("TEMPS", [120])]
    t = A.lire_tour(bonnes, zs)
    manque = [l for l in bonnes if not (l[0] == "ZONE" and l[1][0] == round(zs[3]["x"]))]
    inconnue = bonnes + [("ZONE", [100, 100, 0])]
    def leve(lignes):
        try: A.lire_tour(lignes, zs); return False
        except A.AL.Incomplet: return True
    def refuse_versement(p):
        try: A.corps_du_tour(p); return False
        except A.AL.Refus: return True
    ok["G6 tour bien forme lu ; zone manquante ou inconnue -> Incomplet ; versement invalide refuse"] = (
        t["zones"][zo] == "EAST" and t["camps"]["WEST"]["vivants"] == 16 and t["camps"]["WEST"]["cible"] is None
        and leve(manque) and leve(inconnue) and refuse_versement({"EAST": -1}) and refuse_versement({"WEST": float("nan")})
        and "//" not in A.corps_du_tour({"EAST": 1.5, "WEST": 2}))
    v, m = A.lire_positions([("U", [1, 7, 3000, 7000, 0.25]), ("U", [0, 9, 5000, 11000, 0.0]), ("MORT", [1, 4])])
    def refuse_numero(k):
        try: A.corps_du_tour({"EAST": 1}, {"EAST": [k]}); return False
        except A.AL.Refus: return True
    ok["G9 pont : U et MORT lus, numero de front hors bornes refuse"] = (
        v["WEST"] == [(7, 3000, 7000, 0.25)] and v["EAST"] == [(9, 5000, 11000, 0.0)] and m == {"EAST": [], "WEST": [4]}
        and refuse_numero(0) and refuse_numero(1_000_000)
        and A.corps_du_tour({"EAST": 1, "WEST": 2}, {"EAST": [1, 2], "WEST": []}) == "[1.000, 2.000, [1, 2], []] call GUERRE_fnc_tour2;")
    # G7
    fn = open(os.path.join(MISSION, "fonctions.sqf")).read()
    ini = open(os.path.join(MISSION, "initServer.sqf")).read()
    sv = open(os.path.join(MISSION, "suivi.sqf")).read()
    dc = open(os.path.join(MISSION, "doctrine.sqf")).read()
    version = int(re.search(r"GUERRE_VERSION = (\d+);", fn).group(1))
    plafond = int(re.search(r"GUERRE_PLAFOND = (\d+);", fn).group(1))
    escouades = re.search(r"GUERRE_ESCOUADE = \[(.*?)\];", fn, re.S).group(1)
    tailles = [len(re.findall(r'"[^"]+"', b)) for b in re.findall(r"\[([^\[\]]*)\]", escouades)]
    ok["G7 SQF equilibre, version, plafond, escouades de 8"] = (
        sqf_equilibre(fn) and sqf_equilibre(ini) and sqf_equilibre(sv) and "//" not in sv and sqf_equilibre(dc) and "//" not in dc and version == A.VERSION_MISSION and plafond == B.PLAFOND_ARMA
        and tailles == [8, 8])
    # G8
    from monde.archipel import creer_ile
    from monde import tests as T
    w8 = creer_ile("Malden", 1, 4.0); e8 = w8.pays.domaine("etat"); vus = []
    w8.pays.cloture("porte_guerre", lambda p, c: vus.append((p.jour, e8.fisc.debut)))
    try:
        T.jours(w8, 205); plante = None
    except Exception as ex: plante = f"{type(ex).__name__} au jour {w8.jour} : {ex}"
    ouvert = next((j for j, d in vus if d == 200), None)
    print(f"   passage d annee : {plante or 'aucun plantage jusqu au jour ' + str(w8.jour)} ; exercice 2036 ouvert a la cloture vue au jour {ouvert}", flush=True)
    ok["G8 le 1er janvier passe, l exercice s ouvre a la cloture du 31 decembre"] = plante is None and ouvert == 200
    # G9
    from monde.pays import d01_population as POP1
    from monde import population as PO
    arc9 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    faux = A.FauxGuerre(zs)
    h9_t = iter(x / 432.0 for x in range(10 ** 8))
    h9 = HorlogeDeGuerre(arc9, faux, carte, periode_s=1.0, periode_suivi_s=1 / 6.0, horloge=lambda: next(h9_t)).ouvrir()
    h9.boucle(tours=2); h9.suivre_soldats()
    w9 = arc9.iles["Malden"].w; t9 = w9.table
    f9 = w9.guerre_front
    b9 = {ile: arc9.commande(ile, "guerre_releve")["front"] for ile in ("Malden", "Stratis")}
    absents = all(t9.statut[s["i"]] == PO.ABSENT and t9.poste[s["i"]] == PO.CODE_POSTE["voyage"] and s["i"] in w9.absents for s in f9.values())
    mil0 = GM.militaires(w9)
    tues = sorted(faux.soldats["WEST"])[:3]
    vivants_avant = all(t9.vivant[f9[k]["i"]] == 1 for k in tues)
    pos_avant = {k: (f9[k]["x"], f9[k]["y"]) for k in f9}
    for k in tues: faux.tuer("WEST", k)
    for k in list(faux.soldats["WEST"])[:5]: faux.soldats["WEST"][k] = (1234.0, 4321.0)
    h9.suivre_soldats()
    cause = w9.pays.colonnes["habitant"]["cause_deces"]
    morts_ok = all(t9.vivant[f9[k]["i"]] == 0 and cause[f9[k]["i"]] == POP1.CAUSES.index("combat") and f9[k]["i"] not in w9.absents
                   and f9[k]["etat"] == "mort" for k in tues)
    restent = [s for k, s in f9.items() if k not in tues]
    restent_ok = len(restent) == 29 and all(t9.vivant[s["i"]] == 1 and t9.statut[s["i"]] == PO.ABSENT for s in restent)
    bouges = sum(1 for k, s in f9.items() if k not in tues and (s["x"], s["y"]) != pos_avant[k])
    mil1 = GM.militaires(w9)
    arc9.jours(1); tenue9 = arc9.commande("Malden", "tenue")
    print(f"   soldats suivis : front {b9} ; militaires de Malden {mil0} -> {mil1} ; {bouges} positions deplacees", flush=True)
    ok["G9 32 soldats par ile mobilises, vus au front, absents"] = (
        b9["Malden"] == {"reserve": 0, "front": 32, "mort": 0} and b9["Stratis"] == {"reserve": 0, "front": 32, "mort": 0} and absents)
    ok["G9 trois tues dans Arma meurent au combat dans le moteur ( controle : vivants juste avant )"] = (
        vivants_avant and morts_ok and mil1 == mil0 - 3)
    ok["G9 les 29 autres vivants et absents, positions suivies, conservation"] = restent_ok and bouges == 5 and bool(tenue9[0])
    # G10
    w10 = arc9.iles["Malden"].w
    e10 = GM._etat(w10)
    # une ile qui n a jamais paye ( l horloge de G9 a deja fixe la base de Malden a 0 point : premier essai de G10
    # ECHOUE pour cette raison, 466 266 francs payes pour une « base » de 5 000 points )
    for att in ("guerre_points_payes", "guerre_paye"): w10.__dict__.pop(att, None)
    base = arc9.commande("Malden", "guerre_payer", 5000.0, B.EUROS_PAR_POINT)
    c0 = w10.gouv.caisse; d0 = e10.budget.depenses.get(("defense", "achats"), 0.0)
    r10 = arc9.commande("Malden", "guerre_payer", 6150.0, B.EUROS_PAR_POINT)
    c1 = w10.gouv.caisse
    bis = arc9.commande("Malden", "guerre_payer", 6150.0, B.EUROS_PAR_POINT)
    fob = 1150 * B.EUROS_PAR_POINT / w10.etalon_or["dernier_taux"]
    arc9.jours(1)
    d1 = GM._etat(w10).budget.depenses.get(("defense", "achats"), 0.0)
    tenue10 = arc9.commande("Malden", "tenue")
    print(f"   la guerre paie : base {base} ; paye {r10['paye']:.2f} ( FOB {fob:.2f} ) ; caisse {c0:.2f} -> {c1:.2f} ; "
          f"defense achats {d0:.2f} -> {d1:.2f} ; deuxieme fois {bis['paye']}", flush=True)
    ok["G10 la base ne paie rien ; l achat sort de la caisse, FOB + fret ; une seule fois"] = (
        base["paye"] == 0.0 and r10["paye"] > fob and abs((c0 - c1) - r10["paye"]) <= 1e-6 * max(1.0, r10["paye"])
        and bis["paye"] == 0.0)
    ok["G10 le soir, la ligne defense monte d au moins le FOB ; conservation"] = (d1 - d0) >= fob * (1 - 1e-9) and bool(tenue10[0])
    arc9.fermer()
    # G11
    sonde = "def gouverner(b, memoire):\n    memoire['vus'] = memoire.get('vus', 0) + 1\n    memoire['guerre'] = b.get('guerre')\n    return [{'type': 'rien'}]\n"
    arc11 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False, gouvernement={"Malden": sonde})
    modeles = {ile: arc11.commande(ile, "guerre_voir") for ile in ("Malden", "Stratis")}
    arc11.commande("Malden", "guerre_mobiliser", 5)
    arc11.jours(2)
    wm, ws = arc11.iles["Malden"].w, arc11.iles["Stratis"].w
    mem = wm.cerveau.interieur.memoire
    dec = lambda w: [e for e in w.evenements if e.get("type") == "decision_gouvernement"]
    g11 = mem.get("guerre") or {}
    print(f"   gouvernements : {modeles} ; le code a vu {mem.get('vus')} bulletins, guerre = {g11}", flush=True)
    ok["G11 le code recoit la section guerre chaque matin et decide"] = (
        mem.get("vus", 0) >= 2 and g11.get("soldats_en_reserve") == 5 and "morts_au_combat" in g11 and "cout_guerre_total" in g11
        and all(str(e.get("cerveau", "")).startswith("code:") for e in dec(wm)) and len(dec(wm)) >= 2)
    # G12
    from . import conseil as CO
    sc_reel = CO.scenario("/mnt/data/hmt/guerre/essai9", "Malden")
    sc = dict(sc_reel, part_recettes_armes=max(0.05, sc_reel["part_recettes_armes"]), morts_par_militaire_jour=max(0.005, sc_reel["morts_par_militaire_jour"]),
              lieux_occupes=[OCCUPEE])
    m12 = CO.evaluer_en_guerre(open(os.path.join(CO.SIX_ILES, "Malden.py")).read(), "Malden", sc, echelle=4.0, jours=3, graine=2001)
    g12 = m12["guerre"]
    lu = {k: v for k, v in sc_reel.items() if k != "lieux_occupes"}
    print(f"   conseil : scenario reel {lu} ; petit Malden en guerre : score {m12['score']} guerre {g12}", flush=True)
    ok["G12 scenario lu ; un petit pays en guerre : front, morts, armes payees, ferme occupee, conservation"] = (
        sc_reel["part_au_front"] > 0 and g12["soldats_au_front"] > 0 and g12["morts_au_combat"] >= 1 and g12["cout_guerre_total"] > 0
        and g12["fermes_sous_sequestre"] == 1 and m12["conservation"] and isinstance(m12["score"], float))
    arc12 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    avant = arc12.commande("Malden", "guerre_voir")
    apres = arc12.commande("Malden", "guerre_gouverner", sonde, "conseil:Malden")
    arc12.jours(1)
    d12 = [e for e in arc12.iles["Malden"].w.evenements if e.get("type") == "decision_gouvernement"]
    try: arc12.commande("Malden", "guerre_gouverner", "import os\ndef gouverner(b, memoire):\n    return []\n"); refuse12 = False
    except Exception: refuse12 = True
    ok["G12 la releve change qui decide ; un code interdit est refuse"] = (
        avant == "regles" and apres.startswith("code:") and d12 and str(d12[-1].get("cerveau", "")).startswith("code:") and refuse12)
    arc12.fermer()
    ok["G11 l ile sans code decide par les regles, sans bascule"] = (
        len(dec(ws)) >= 2 and all(e.get("cerveau") == "regles" and not str(e.get("motifs", "")).startswith("cerveau indisponible") for e in dec(ws)))
    arc11.fermer()
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    passe = all(ok.values())
    print(f"PORTES DE LA GUERRE : {'FRANCHIES' if passe else 'ECHOUEES'} ( {time.time() - t0:.0f} s )")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
