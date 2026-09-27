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
G13 VILLES OCCUPEES ( 27/09, ecrite avant la mesure ) : la zone de La Trinite ( capitale et siege du gouvernement )
   occupee trois jours dans un petit Malden : les presents au travail a La Trinite, rapportes a ceux d un lieu temoin
   ( la ferme de Dourdan ; AMENDE apres le premier essai : la ville de Larche, prise d abord, n a aucun emploi dans le
   moteur, 0 present, rapport impossible - La Trinite y tombait de 45 492 a 11 574 ), tombent sous 0,4 fois leur rapport d avant ; ils remontent au-dessus de 0,8 fois apres la liberation ;
   une quarantaine posee par le gouvernement lui-meme ( ailleurs ) reste ; le bulletin dit ville occupee et siege
   occupe ; la conservation tient.
G14 USINES OCCUPEES ( 27/09, AMENDEE avant tout verdict : la premiere version mesurait la fonderie de Larche, mais
   les fonderies de Malden ne produisent RIEN, en paix comme a 10 000 habitants - le controle positif a echoue, rien a
   prouver ; la centrale, elle, produit ) : la zone de la centrale ( centrale01 ) occupee trois jours : ses ouvriers
   presents, rapportes a une ferme temoin hors zone ( Dourdan ), tombent sous 0,4 fois leur rapport d avant ; sa
   production tombe sous 0,5 fois ; tout remonte au-dessus de 0,8 fois apres la liberation. ( Deuxieme essai : ouvriers
   0,75 -> 0,19, mais production 1 216 -> 1 169 par jour, -4 % : le domaine 11 fait produire une centrale selon la demande
   du reseau. L occupation met desormais ses groupes EN PANNE, cause occupation - l etat des pannes du domaine 11.
   Troisieme essai : production 1 216 -> 0 -> 1 184, mais ouvriers 0,56 apres contre 0,75 avant : la fenetre d apres
   ( 4 jours ) contenait un dimanche, pas celle d avant. Fenetres portees a SEPT jours chacune : la meme semaine.
   Quatrieme essai : production 1 184 -> 0 -> 1 171, ouvriers 0,76 -> 0,19 -> 0,19. Sonde : la quarantaine est bien
   levee, mais l agenda ( domaine 5 ) planifie la semaine - les ouvriers reviennent 6 sur 21 le mercredi, les 21 le
   mardi suivant. La reprise se juge donc sur la DEUXIEME semaine apres la liberation. )
G15 LES LEVIERS SUIVENT LA TAILLE DU PAYS ( 27/09, ecrite avant la mesure ) : dans un pays de 2 000 habitants
   ( k = 4 ), le gouvernement peut acheter 8 000 unites de nourriture et pas 8 001 ; il peut relever les credits de
   subventions ( la ligne porte sur ses transferts ) puis verser une subvention qu il n aurait pas pu verser avant.
   ( Sur la vraie Stratis du jour 301, « acheter 100 000 » etait refuse a 2 000 et « fixer_budget subventions » borne
   a 3 000. Les regles plafonnent elles-memes a 2 000 : la porte d identite des domaines dit qu elles ne changent pas.
   AMENDEE apres le premier essai : 8 001 y etait refuse faute de CREDITS de la ligne interieur, pas par la borne - le
   test ne prouvait rien ; les credits sont maintenant larges, et le refus doit etre « achat invalide ». )
G16 L AIDE ALIMENTAIRE ( 27/09, ecrite avant la mesure ) : la vraie Stratis de l essai 15 ( jour 349, 98 % de menages
   sans nourriture, marches vides, reserve vide ) en trois copies ; dans chacune le gouvernement porte ses credits
   interieur ( achats ) a trois fois le vote ; puis il importe 200 000 unites de nourriture destination « reserve »
   dans la premiere, « population » dans la deuxieme, rien dans la troisieme ( le temoin ). Deux jours. Controle
   positif : le temoin a faim ( au moins 50 % chaque jour ). La reserve ne nourrit personne : a 2 points du temoin
   chaque jour. La population, si : au moins 30 points sous le temoin chaque jour. Les deux imports sont acceptes,
   l unite arrive dans le stock vise ; la conservation tient dans la copie aidee. Une autre destination, ou « population »
   pour un autre bien que la nourriture, est refusee.
   ( AMENDEE apres le premier essai : les deux imports etaient « acceptes » et RIEN n arrivait - les reserves de change
   de Stratis sont a -55 millions d euros, le controle des changes ne laisse rien passer, et le moteur ne le disait pas.
   Le refus est maintenant rendu. La porte teste donc le canal avec des devises - les reserves des trois copies sont
   PORTEES a 50 millions d euros, comme un pret d urgence ( le deuxieme essai les AUGMENTAIT de 50 millions : -5,5
   millions, toujours rien ) - et, AVANT, dans la copie aidee, l etat reel : l import est refuse, avec sa raison, et
   rien n entre. AMENDEE apres le troisieme essai : les DEVISES SEULES nourrissent Stratis - le temoin, avec ses 50
   millions et sans aide, passe de 98 % a 46 % puis 0,8 % de faim, parce que les negociants reimportent aussitot ; le
   controle « le temoin a faim chaque jour » ne pouvait plus tenir. Le temoin doit avoir faim AU DEPART, et l aide se
   juge le PREMIER jour : la population au moins 30 points sous le temoin ( 1,6 % contre 46 % ), la reserve a 2 points
   du temoin chaque jour. La famine de Stratis est une crise de devises. )
G17 UN FOURNISSEUR IMPAYE NE LIVRE PLUS ( 27/09, ecrite avant la mesure ) : un petit archipel, Arma en jouet ; Malden
   ( WEST ) achete pour 1 150 points, et paie ; puis sa banque centrale n a plus de devises et Malden achete 1 150 points
   de plus : le paiement echoue ( 1 150 points impayes ) ; au tour suivant Malden ne recoit AUCUN point, Stratis en
   recoit ( controle ) ; les devises reviennent : l arriere est paye, et au tour d apres Malden recoit de nouveau des
   points. La conservation de Malden tient.
G18 LES CONVOIS A L ECHELLE DE L ILE ( 27/09, ecrite avant la mesure ) : la vraie Stratis de l essai 15 ( 98 % de
   menages sans nourriture, 368 000 rations faites qui attendent un camion dans ses fermes ) en deux copies : le temoin
   garde les convois du moteur ( 60 unites, un par ferme et par heure ) et reste au-dessus de 90 % de faim ; la copie aux
   convois a l echelle de l ile ( 200 ) tombe sous 5 % le premier jour - le stock bloque part ; sa conservation tient ;
   une ile reprise d un instantane d avant le 27/09 recoit l echelle de l archipel.
   ( AMENDEE apres le premier essai : il demandait aussi 5 % le DEUXIEME jour - 11,4 % mesure, puis 100 % au cinquieme :
   les fermes de cette Stratis ne produisent plus, leurs paysans ont une dette de faim de 52 rations, au-dela du seuil
   ou l on ne va plus travailler ( config.ABSENCE_FAIM 1,5 ) et qui ne baisse que d une ration par jour nourri - un autre
   piege, du moteur, rapporte a Younes. Le convoi se juge donc aussi sur une ile NEUVE : une petite Stratis ( echelle
   20, besoin de 10 000 rations par jour, convois du moteur plafonnes a 5 fermes x 24 x 60 = 7 200 ), 30 jours : aux
   convois a l echelle, les rations en attente dans les fermes au jour 30 sont au moins 10 fois moindres que chez le
   temoin, les reserves de change plus hautes, la faim moyenne des jours 21 a 30 pas plus haute d un point.
   AMENDEE apres le deuxieme essai : attente 1 359 contre 21 493, faim 0,99 % contre 1,12 %, mais reserves 32,20 contre
   32,39 millions d euros. La prediction etait fausse, pour une raison reelle, mesuree motif par motif : les fermes du
   temoin, qui ne peuvent pas envoyer leurs rations, vendent plus de grain et d huile a l etranger ( vente_negoce
   +127 000 ), et l ile mieux nourrie importe plus ( import_biens +149 000 ). Les reserves ne mesuraient pas le convoi ;
   le critere est retire. )

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


INSTANTANE_AIDE = "/mnt/data/hmt/guerre/essai15/instantane"


def _aide(args):
    """G16 : une copie de la vraie Stratis, l import d aide ( ou rien ), deux jours."""
    dest, q, jours = args
    import pickle
    from monde.archipel import Ile
    from monde import tests as T
    from monde.pays import d06_etat as ET
    w = pickle.load(open(os.path.join(INSTANTANE_AIDE, "Stratis.pkl"), "rb")); p = w.pays; ile = Ile("Stratis", w)
    from monde.pays import d07_exterieur as X
    bu = ET._etat(p).budget
    r = {"credits": ET.appliquer(p, {"type": "fixer_budget", "ligne": "interieur", "montant": 3.0 * bu.votes[("interieur", "achats")]}),
         "faim0": round(GM.faim(w), 4)}
    if dest == "population":
        s0 = w.publics["population"]["nourriture"]
        r["sans_devises"] = ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": q, "destination": dest})
        r["sans_devises_arrive"] = round(w.publics["population"]["nourriture"] - s0)
    X.reserves_de_change(p); X._ext(p).reserves_euros = 5e7
    if dest is not None:
        s0 = (w.publics["reserve"]["nourriture"], w.publics["population"]["nourriture"])
        r["import"] = ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": q, "destination": dest})
        r["arrive"] = (round(w.publics["reserve"]["nourriture"] - s0[0]), round(w.publics["population"]["nourriture"] - s0[1]))
    if dest == "population":
        r["refus"] = [ET.appliquer(p, {"type": "importer", "bien": "nourriture", "quantite": 10, "destination": "armee"}),
                      ET.appliquer(p, {"type": "importer", "bien": "remedes", "quantite": 10, "destination": "population"})]
    r["faim"] = []
    for _ in range(jours):
        T.jours(w, 1); r["faim"].append(round(ile.commande("etat")["faim"], 4))
    r["conservation"] = bool(p.socle.conservation.tenue()[0])
    return r


def _convois(echelle):
    """G18 : une copie de la vraie Stratis, convois a l echelle donnee, deux jours."""
    import pickle
    from monde.archipel import Ile, _convois as poser
    from monde import tests as T
    w = pickle.load(open(os.path.join(INSTANTANE_AIDE, "Stratis.pkl"), "rb"))
    avant = "echelle_convois" in vars(w)
    if echelle is not None: poser(w, echelle)
    ile = Ile("Stratis", w); f = []
    for _ in range(2):
        T.jours(w, 1); f.append(round(ile.commande("etat")["faim"], 4))
    return {"faim": f, "echelle": w.echelle_convois, "deja": avant, "conservation": bool(w.pays.socle.conservation.tenue()[0])}


def _neuve(echelle_convois):
    """G18 : une petite Stratis neuve ( echelle 20 ), 30 jours, a l echelle de convois donnee."""
    from monde.archipel import creer_ile, Ile
    from monde import tests as T
    from monde.pays import d07_exterieur as X
    w = creer_ile("Stratis", 1, 20.0); w.echelle_convois = float(echelle_convois); ile = Ile("Stratis", w); f = []
    for _ in range(30):
        T.jours(w, 1); f.append(ile.commande("etat")["faim"])
    attente = sum(e.stocks.get("nourriture", 0.0) for e in w.entreprises.values() if e.type == "ferme")
    return {"attente": round(attente), "reserves": round(X.reserves_de_change(w.pays)[0]), "faim_21_30": round(sum(f[20:]) / 10, 4),
            "conservation": bool(w.pays.socle.conservation.tenue()[0])}


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
    # G13
    from monde import population as PO13
    arc13 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w13 = arc13.iles["Malden"].w; t13 = w13.table
    zt = next(z["n"] for z in zs if "Malden_C_LaTrinite" in z["lieux"]); lt = next(z["lieux"] for z in zs if z["n"] == zt)
    kt, kl = w13.carte.lieux["Malden_C_LaTrinite"].n, w13.carte.lieux["Malden_V_Dourdan"].n
    w13.gouv.lois.setdefault("quarantaine", []).append("Malden_V_Goisse")       # la quarantaine du gouvernement, ailleurs
    def au_travail(jours):
        tot = [0, 0]
        for _ in range(jours * 144):
            arc13.un_pas(); n13 = t13.n
            at = (t13.vivant[:n13] == 1) & (t13.poste[:n13] == PO13.CODE_POSTE["travail"])
            tot[0] += int((at & (t13.lieu[:n13] == kt)).sum()); tot[1] += int((at & (t13.lieu[:n13] == kl)).sum())
        return tot
    av = au_travail(3)
    arc13.commande("Malden", "occuper", zt, lt, True)
    b13 = GM.bulletin_guerre(w13)
    pe = au_travail(3)
    arc13.commande("Malden", "occuper", zt, lt, False)
    ap = au_travail(4)
    rap = lambda x: x[0] / max(1, x[1])
    gv = "Malden_V_Goisse" in w13.gouv.lois["quarantaine"] and "Malden_C_LaTrinite" not in w13.gouv.lois["quarantaine"]
    tenue13 = arc13.commande("Malden", "tenue")
    print(f"   villes occupees : presents La Trinite / Dourdan avant {av} ( {rap(av):.2f} ), occupee {pe} ( {rap(pe):.2f} ), "
          f"liberee {ap} ( {rap(ap):.2f} ) ; bulletin {b13['villes_occupees']} siege {b13['siege_du_gouvernement_occupe']}", flush=True)
    ok["G13 controle positif : La Trinite travaillait avant ; occupee, sous 0,4 fois son rapport au temoin"] = (
        av[0] > 0 and av[1] > 0 and pe[1] > 0 and rap(pe) < 0.4 * rap(av))
    ok["G13 liberee, au-dessus de 0,8 fois ; la quarantaine du gouvernement reste ; bulletin ; conservation"] = (
        rap(ap) > 0.8 * rap(av) and gv and "Malden_C_LaTrinite" in b13["villes_occupees"] and b13["siege_du_gouvernement_occupe"]
        and bool(tenue13[0]))
    # G15
    from monde.pays import d06_etat as ET15
    arc15 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    w15 = arc15.iles["Malden"].w; p15 = w15.pays
    w15.gouv.caisse = max(w15.gouv.caisse, 1e8)
    b15 = ET15._etat(p15).budget
    b15.credits[("interieur", "achats")] = b15.credits.get(("interieur", "achats"), 0.0) + 1e7    # la borne seule doit lier
    a_ok = ET15.appliquer(p15, {"type": "acheter", "bien": "nourriture", "quantite": 8000, "destination": "population"})
    a_non = ET15.appliquer(p15, {"type": "acheter", "bien": "nourriture", "quantite": 8001, "destination": "population"})
    dispo0 = b15.credits.get(("subventions", "transferts"), 0.0) - b15.depenses.get(("subventions", "transferts"), 0.0)
    s_avant = ET15.appliquer(p15, {"type": "subvention", "cible": "menages_pauvres", "montant": round(dispo0 + 5000)})
    f15 = ET15.appliquer(p15, {"type": "fixer_budget", "ligne": "subventions", "montant": round(b15.depenses.get(("subventions", "transferts"), 0.0) + dispo0 + 10000)})
    s_apres = ET15.appliquer(p15, {"type": "subvention", "cible": "menages_pauvres", "montant": round(dispo0 + 5000)})
    print(f"   leviers : acheter 8 000 {a_ok} ; 8 001 {a_non} ; subvention avant {s_avant} ; fixer_budget {f15} ; subvention apres {s_apres}", flush=True)
    ok["G15 acheter jusqu a 2 000 x k, pas au-dela ; subventions relevees puis versees"] = (
        a_ok[0] and not a_non[0] and "achat invalide" in a_non[1] and not s_avant[0] and f15[0] and s_apres[0])
    arc15.fermer()
    # G14
    z14 = zone_de["centrale01"]; l14 = next(z["lieux"] for z in zs if z["n"] == z14)
    kc, kw = w13.carte.lieux["centrale01"].n, w13.carte.lieux["Malden_V_Dourdan"].n
    def usine(jours):
        pres, prod = [0, 0], 0.0
        for _ in range(jours):
            a0 = sum(w13.entreprises["centrale01"].produit_du_jour.values())
            for _ in range(144):
                arc13.un_pas(); n14 = t13.n
                at = (t13.vivant[:n14] == 1) & (t13.poste[:n14] == PO13.CODE_POSTE["travail"])
                pres[0] += int((at & (t13.lieu[:n14] == kc)).sum()); pres[1] += int((at & (t13.lieu[:n14] == kw)).sum())
            a1 = sum(w13.entreprises["centrale01"].produit_du_jour.values())
            prod += (a1 - a0) if a1 >= a0 else a1
        return pres, prod / jours
    pa, qa = usine(7)
    arc13.commande("Malden", "occuper", z14, l14, True)
    pp, qp = usine(7)
    arc13.commande("Malden", "occuper", z14, l14, False)
    usine(7)                                        # la semaine du retour ( l agenda planifie la semaine )
    pl, ql = usine(7)
    rp = lambda x: x[0] / max(1, x[1])
    print(f"   usines occupees : ouvriers de la centrale / temoin avant {pa} ( {rp(pa):.2f} ), occupee {pp} ( {rp(pp):.2f} ), liberee {pl} "
          f"( {rp(pl):.2f} ) ; production par jour {qa:.0f} -> {qp:.0f} -> {ql:.0f}", flush=True)
    ok["G14 controle positif : la centrale travaillait ; occupee, ouvriers sous 0,4 fois, production sous 0,5 fois"] = (
        pa[0] > 0 and pa[1] > 0 and pp[1] > 0 and qa > 0 and rp(pp) < 0.4 * rp(pa) and qp < 0.5 * qa)
    ok["G14 liberee, au-dessus de 0,8 fois"] = rp(pl) > 0.8 * rp(pa) and ql > 0.8 * qa
    arc13.fermer()
    # G16
    from multiprocessing import get_context
    Q16 = 200000
    with get_context("fork").Pool(3) as pool:
        re16, po16, te16 = pool.map(_aide, [("reserve", Q16, 2), ("population", Q16, 2), (None, Q16, 2)])
    print(f"   aide alimentaire ( vraie Stratis ) : temoin {te16} ; reserve {re16} ; population {po16}", flush=True)
    ok["G16 controle positif : le temoin a faim au depart ; les deux imports acceptes, arrives dans le stock vise"] = (
        te16["faim0"] >= 0.5 and te16["credits"][0] and re16["import"][0] and po16["import"][0]
        and re16["arrive"] == (Q16, 0) and po16["arrive"] == (0, Q16))
    ok["G16 sans devises ( l etat reel ) : l import est refuse, avec sa raison, et rien n entre"] = (
        not po16["sans_devises"][0] and "refuse" in po16["sans_devises"][1] and po16["sans_devises_arrive"] == 0)
    ok["G16 la reserve ne nourrit personne ; la population, si ; autre destination refusee ; conservation"] = (
        all(abs(a - b) <= 0.02 for a, b in zip(re16["faim"], te16["faim"]))
        and po16["faim"][0] <= te16["faim"][0] - 0.30
        and not any(x[0] for x in po16["refus"]) and po16["conservation"])
    # G17
    from monde.pays import d07_exterieur as X17
    arc17 = Archipel(iles=("Malden", "Stratis"), echelle=4.0, parallele=False)
    faux17 = A.FauxGuerre(zs)
    h17_t = iter(x / 432.0 for x in range(10 ** 8))
    h17 = HorlogeDeGuerre(arc17, faux17, carte, periode_s=1.0, suivre=False, horloge=lambda: next(h17_t)).ouvrir()
    p17 = arc17.iles["Malden"].w.pays
    def devises(v): X17.reserves_de_change(p17); X17._ext(p17).reserves_euros = v
    def un_tour(): h17.boucle(tours=h17.tours + 1); return h17.derniere
    t1 = un_tour()
    faux17.depense["WEST"] = 1150.0; t2 = un_tour()
    devises(-1e9); faux17.depense["WEST"] = 2300.0; t3 = un_tour()
    t4 = un_tour()
    devises(1e9); t5 = un_tour()
    t6 = un_tour()
    tenue17 = arc17.commande("Malden", "tenue")
    arc17.fermer()
    m17 = lambda t: (round(t["iles"]["Malden"]["points"], 1), round(t["iles"]["Malden"]["paiement"]["paye"]), t["iles"]["Malden"]["paiement"]["dette_points"],
                     round(t["iles"]["Stratis"]["points"], 1))
    print(f"   fournisseur impaye ( points Malden, paye, impayes, points Stratis ) : {[m17(t) for t in (t2, t3, t4, t5, t6)]}", flush=True)
    ok["G17 paye puis impaye : 1 150 points d arriere ; au tour suivant Malden ne recoit rien, Stratis si"] = (
        t2["iles"]["Malden"]["paiement"]["paye"] > 0 and t3["iles"]["Malden"]["points"] > 0 and t3["iles"]["Malden"]["paiement"]["paye"] == 0
        and t3["iles"]["Malden"]["paiement"]["dette_points"] == 1150.0 and t4["iles"]["Malden"]["points"] == 0.0
        and t4["iles"]["Stratis"]["points"] > 0)
    ok["G17 les devises reviennent : l arriere est paye, Malden recoit de nouveau ; conservation"] = (
        t5["iles"]["Malden"]["paiement"]["paye"] > 0 and t5["iles"]["Malden"]["paiement"]["dette_points"] == 0.0
        and t6["iles"]["Malden"]["points"] > 0 and bool(tenue17[0]))
    # G18
    with get_context("fork").Pool(2) as pool:
        te18, ec18 = pool.map(_convois, [None, 200.0])
    print(f"   convois : temoin {te18} ; a l echelle de l ile {ec18}", flush=True)
    with get_context("fork").Pool(2) as pool:
        nt18, ne18 = pool.map(_neuve, [1.0, 20.0])
    print(f"   convois, ile neuve 30 jours : temoin {nt18} ; a l echelle {ne18}", flush=True)
    ok["G18 vraie Stratis : temoin au-dessus de 90 %, convois a l echelle sous 5 % le premier jour ; echelle posee a la reprise ; conservation"] = (
        min(te18["faim"]) >= 0.90 and ec18["faim"][0] <= 0.05 and te18["echelle"] == 1.0 and ec18["echelle"] == 200.0
        and not ec18["deja"] and ec18["conservation"])
    ok["G18 ile neuve : attente 10 fois moindre, faim pas plus haute ; conservation"] = (
        ne18["attente"] * 10 <= nt18["attente"] and ne18["faim_21_30"] <= nt18["faim_21_30"] + 0.01 and ne18["conservation"])
    ok["G11 l ile sans code decide par les regles, sans bascule"] = (
        len(dec(ws)) >= 2 and all(e.get("cerveau") == "regles" and not str(e.get("motifs", "")).startswith("cerveau indisponible") for e in dec(ws)))
    arc11.fermer()
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    passe = all(ok.values())
    print(f"PORTES DE LA GUERRE : {'FRANCHIES' if passe else 'ECHOUEES'} ( {time.time() - t0:.0f} s )")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
