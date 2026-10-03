"""LA DOCTRINE : les rudiments de tactique et de stratégie aériennes que l'état-major ( etat_major.py ) applique, et que
l'agent chef d'état-major lira en clair ( Younes, 02/10 : « mets-toi en mode chef d'état-major : SEAD, strike, DEAD,
tout » ). Chaque règle vient de la doctrine réelle ( campagnes de 1991, 2003, 2022 ) ; chaque chiffre vient de la base
DB3000 de CMO ( portées, ogives, chargements ), jamais d'une estimation.

LES PHASES D'UNE CAMPAGNE AÉRIENNE
  1. SUPÉRIORITÉ AÉRIENNE. Tant que l'adversaire a des défenses sol-air à longue portée intactes, aucune frappe ordinaire
     ne passe ( 02/10 : dix JSOW sur quatorze abattus par un S-300 ). On les SUPPRIME ( SEAD : missiles antiradar qui font
     taire ou détruisent les radars ) puis on les DÉTRUIT ( DEAD : missiles de croisière furtifs tirés hors de portée,
     missiles balistiques, avions furtifs ). En même temps : balayages de chasse et frappes contre ses bases aériennes
     ( OCA : pistes, points d'accès, abris, dépôts ).
  2. INTERDICTION. Une fois le ciel acquis : postes de commandement, logistique, lanceurs de missiles ( chasse aux
     Iskander ), dépôts.
  3. APPUI AU SOL. Quand la guerre terrestre s'engage : appui rapproché et interdiction du champ de bataille.
  EN PERMANENCE : défense aérienne de ses bases et de ses moyens rares ( radars volants, ravitailleurs ).

LES RÈGLES TACTIQUES
  - Défense COURTE portée ( moins de 30 km : Pantsir, Tor, MANPADS ) : on vole au-dessus de son plafond. Défense de MOYENNE
    ou LONGUE portée ( Buk, Patriot, S-300, S-400 ) : c'est un parapluie.
  - On frappe d'abord ce qui MENACE le plus : la base qui aligne le plus d'avions le plus près des siennes ( Kaliningrad,
    bulle au milieu de l'OTAN, avant Baranovitchi ).
  - Un avion sans arme à distance de sécurité ne va pas sous le parapluie : pendant la DEAD, il repasse en chasse ( escorte,
    défense des bases ), et revient à la frappe quand le ciel est ouvert ( « swing-role » ).
  - Cadence : effort intense ( « surge » ) les trois premiers jours, puis effort durable, une sortie par jour et par pilote
    ( 1991, 1999, 2022 ).
  - On ne frappe JAMAIS sous un parapluie sol-air intact avec des armes de courte portée : soit on le détruit d'abord,
    soit on tire de plus loin que sa portée ( arme à distance de sécurité ), soit on pénètre en avion furtif.
  - Un paquet, pas un vol isolé : frappeurs + escorte de chasse + tireurs antiradar ( + brouilleur ).
  - La bonne arme sur la bonne cible : perforante sur abri durci et dépôt enterré, anti-piste sur piste, antiradar sur radar,
    croisière ou balistique sur cible très défendue.
  - Un lanceur n'est affecté qu'aux cibles à sa portée ( ATACMS 162 km, GMLRS 45 km, Iskander 270 km ).
  - On évalue les dégâts réels ( CMO ) et on refrappe ce qui vit encore.
  - On apprend : une mission qui coûte plus qu'elle ne détruit perd ses moyens au profit de celles qui rapportent.
"""
import re
import sqlite3

BASE = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"
NM_KM = 1.852                                             # la DB3000 donne ses portées en MILLES NAUTIQUES ( 03/10 : lues en km,
                                                          # les parapluies étaient 1,85 fois trop courts : S-400 398 km, pas 215 )

PHASES = ("superiorite", "interdiction", "appui")
MISSIONS = {
    "dca": "Défense aérienne d'une base ou d'une zone ( patrouille air-air )",
    "dead": "Destruction des défenses sol-air ( croisière, balistique, furtifs, antiradar )",
    "sead": "Suppression des défenses ( antiradar contre les radars qui émettent )",
    "oca": "Frappe d'une base aérienne ( pistes, accès, abris, dépôts )",
    "interdiction": "Frappe des lanceurs, postes de commandement et de la logistique",
    "escorte": "Chasseurs qui accompagnent un paquet de frappe",
}
# Une défense qui porte à 30 km ou plus menace un avion à moyenne altitude ( Buk, Patriot, S-300, S-400 ) : DEAD d'abord.
# En dessous ( Pantsir, Tor, Strela, MANPADS ), on vole au-dessus de leur plafond, comme la doctrine réelle depuis 1991.
PORTEE_MENACE_KM = 30.0

ARME_DISTANCE = re.compile(r"JASSM|Storm Shadow|SCALP|Taurus|Kh-59|Kh-38|Kh-101|Kh-555|Kalibr|Tomahawk|SPEAR", re.I)
ARME_ANTIRADAR = re.compile(r"HARM|AARGM|ALARM|Kh-31P|Kh-58|Kh-25MP", re.I)
ARME_FURTIVE = re.compile(r"SDB|GBU-39|GBU-53", re.I)


def _c(base=None):
    return sqlite3.connect(f"file:{base or BASE}?mode=ro", uri=True)


def _armes_installation(c, fid):
    """[ ( nom, portée air km, portée sol km ) ] des armes d'une unité au sol ( affûts et magasins )."""
    out = []
    comp = [m for (m,) in c.execute("select ComponentID from DataFacilityMounts where ID = ?", (fid,))]
    for (mid,) in [(m,) for m in comp]:
        for (wr,) in c.execute("select ComponentID from DataMountWeapons where ID = ?", (mid,)):
            r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
            if r:
                w = c.execute("select Name, coalesce(AirRangeMax,0), coalesce(LandRangeMax,0) from DataWeapon where ID = ?",
                              (r[0],)).fetchone()
                if w:
                    out.append(w)
    for (mg,) in c.execute("select ComponentID from DataFacilityMagazines where ID = ?", (fid,)):
        for (wr,) in c.execute("select ComponentID from DataMagazineWeapons where ID = ?", (mg,)):
            r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
            if r:
                w = c.execute("select Name, coalesce(AirRangeMax,0), coalesce(LandRangeMax,0) from DataWeapon where ID = ?",
                              (r[0],)).fetchone()
                if w:
                    out.append(w)
    return out


def portee_sol_air(dbid, base=None):
    """Portée air maximale ( km ) d'une unité au sol ou d'un élément d'installation : 0 si elle ne tire pas en l'air."""
    return NM_KM * max((a for _, a, _ in _armes_installation(_c(base), dbid)), default=0.0)


def portee_sol_sol(dbid, base=None):
    """Portée sol maximale ( km ) d'un lanceur : ATACMS 162, Iskander 270… ; 0 s'il ne frappe pas au sol."""
    return NM_KM * max((s for _, _, s in _armes_installation(_c(base), dbid)), default=0.0)


def chargement(dbid, mission, base=None):
    """Le chargement réel d'un avion pour une mission, ou None : « dead » une arme de croisière ( sinon antiradar, sinon
    furtive ), « sead » une arme antiradar. Parmi les candidats, le chargement à portée la plus longue."""
    c = _c(base)
    lignes = c.execute("""select l.ID, l.Name from DataAircraftLoadouts al join DataLoadout l on l.ID = al.ComponentID
        where al.ID = ? and coalesce(l.Hypothetical,0)=0 and l.Name not like '%Short Range%'""", (dbid,)).fetchall()
    ordre = {"dead": (ARME_DISTANCE, ARME_ANTIRADAR, ARME_FURTIVE), "sead": (ARME_ANTIRADAR,)}[mission]
    for motif in ordre:
        cand = [(i, n) for i, n in lignes if motif.search(n)]
        if cand:
            return max(cand, key=lambda x: ("Long" in x[1] or "ER" in x[1], -x[0]))[0]
    return None


def portee_navire_mer(dbid, base=None):
    """Portée antinavire maximale ( km ) des armes d'un navire ( SurfaceRangeMax ) : affûts et magasins de DataShip."""
    return _portee_navire(dbid, "SurfaceRangeMax", base)


def _portee_navire(dbid, colonne, base=None):
    c = _c(base)
    out = []
    try:
        ids = [m for (m,) in c.execute("select ComponentID from DataShipMounts where ID = ?", (dbid,))]
        recs = [wr for mid in ids for (wr,) in c.execute("select ComponentID from DataMountWeapons where ID = ?", (mid,))]
        mags = [m for (m,) in c.execute("select ComponentID from DataShipMagazines where ID = ?", (dbid,))]
        recs += [wr for mg in mags for (wr,) in c.execute("select ComponentID from DataMagazineWeapons where ID = ?", (mg,))]
        for wr in recs:
            r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
            if r:
                w = c.execute(f"select coalesce({colonne},0) from DataWeapon where ID = ?", (r[0],)).fetchone()
                if w:
                    out.append(w[0])
    except sqlite3.OperationalError:
        return 0.0
    return NM_KM * max(out, default=0.0)


def portee_navire_sol(dbid, base=None):
    """Portée sol maximale ( km ) des armes d'un navire ( Kalibr, Tomahawk… ) : affûts et magasins de DataShip."""
    c = _c(base)
    out = []
    for t_aff, t_mag in (("DataShipMounts", "DataShipMagazines"),):
        try:
            for (mid,) in c.execute(f"select ComponentID from {t_aff} where ID = ?", (dbid,)):
                for (wr,) in c.execute("select ComponentID from DataMountWeapons where ID = ?", (mid,)):
                    r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
                    if r:
                        w = c.execute("select coalesce(LandRangeMax,0) from DataWeapon where ID = ?", (r[0],)).fetchone()
                        if w:
                            out.append(w[0])
            for (mg,) in c.execute(f"select ComponentID from {t_mag} where ID = ?", (dbid,)):
                for (wr,) in c.execute("select ComponentID from DataMagazineWeapons where ID = ?", (mg,)):
                    r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
                    if r:
                        w = c.execute("select coalesce(LandRangeMax,0) from DataWeapon where ID = ?", (r[0],)).fetchone()
                        if w:
                            out.append(w[0])
        except sqlite3.OperationalError:
            continue
    return NM_KM * max(out, default=0.0)


def portee_site_mer(dbid, base=None):
    """Portée antinavire maximale ( km ) d'une batterie côtière ( installation ) : SurfaceRangeMax de ses armes."""
    c = _c(base)
    out = []
    comp = [m for (m,) in c.execute("select ComponentID from DataFacilityMounts where ID = ?", (dbid,))]
    recs = [wr for mid in comp for (wr,) in c.execute("select ComponentID from DataMountWeapons where ID = ?", (mid,))]
    mags = [m for (m,) in c.execute("select ComponentID from DataFacilityMagazines where ID = ?", (dbid,))]
    recs += [wr for mg in mags for (wr,) in c.execute("select ComponentID from DataMagazineWeapons where ID = ?", (mg,))]
    for wr in recs:
        r = c.execute("select ComponentID from DataWeaponRecord where ID = ?", (wr,)).fetchone()
        if r:
            w = c.execute("select coalesce(SurfaceRangeMax,0) from DataWeapon where ID = ?", (r[0],)).fetchone()
            if w:
                out.append(w[0])
    return NM_KM * max(out, default=0.0)
