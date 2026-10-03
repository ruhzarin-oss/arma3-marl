#!/usr/bin/env python3
"""LES FICHES DB3000 : une fiche courte en français par plateforme ( avion, navire, sous-marin, installation, unité
terrestre ) en service en 2026 dans les pays retenus ( lexique.PAYS_RETENUS ), par chargement d'avion, par arme et par
capteur que ces plateformes emportent. Base lue en LECTURE SEULE ( copie SQLite de CMO ).

« En service en 2026 » : YearCommissioned <= 2026 et ( YearDecommissioned = 0 ou >= 2026 ), Hypothetical = 0,
Deprecated = 0 ( même règle que cmo/inventaire.py ). Une arme ou un capteur est « en service » s'il est emporté par une
de ces plateformes ( la base ne date pas les armes ).

Unités de la base : portées en milles nautiques ( nm ), vitesses en nœuds, altitudes en mètres, masses en kg. Les
fiches donnent nm ET km ( 1 nm = 1,852 km ).

    .venv312/bin/python savoir/fiches_db.py   ->   /mnt/data/hmt/etat/cmo_savoir/fiches/db_*.jsonl
"""
import collections
import json
import os
import re
import sqlite3
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import lexique as L                                       # noqa: E402

BASE = "/mnt/data/hmt/etat/cmo_db/DB3K_519.db3"
SORTIE = "/mnt/data/hmt/etat/cmo_savoir/fiches"
ANNEE = 2026
MOTS_MAX = 260


def km(nm):
    return round(nm * L.NM_KM)


def f1(x):
    """Un nombre lisible : entier si rond, sinon une décimale."""
    if x is None:
        return "?"
    x = float(x)
    return str(int(round(x))) if abs(x - round(x)) < 0.05 or abs(x) >= 100 else f"{x:.1f}".replace(".", ",")


def couper(texte, mots=MOTS_MAX):
    m = texte.split()
    return texte if len(m) <= mots else " ".join(m[:mots]) + " […]"


def liste(xs, n):
    xs = list(xs)
    return ", ".join(xs[:n]) + (f" et {len(xs) - n} autres" if len(xs) > n else "")


class DB:
    def __init__(self, base=BASE):
        self.c = sqlite3.connect(f"file:{base}?mode=ro", uri=True)
        c = self.c
        e = lambda t: {i: d for i, d, *_ in c.execute(f"select * from {t}")}      # noqa: E731
        self.pays = e("EnumOperatorCountry")
        self.service = e("EnumOperatorService")
        self.e = {t: e(t) for t in (
            "EnumAircraftType", "EnumAircraftCategory", "EnumShipType", "EnumShipCategory", "EnumSubmarineType",
            "EnumSubmarineCategory", "EnumFacilityCategory", "EnumFacilityType", "EnumGroundUnitCategory", "EnumArmorType",
            "EnumWeaponType", "EnumWeaponTarget", "EnumWeaponCode", "EnumWeaponGeneration", "EnumSensorType", "EnumSensorRole",
            "EnumSensorCapability", "EnumSensorCode", "EnumSensorGeneration", "EnumSensorFrequency", "EnumLoadoutRole",
            "EnumLoadoutTimeOfDay", "EnumLoadoutWeather", "EnumRunwayLength", "EnumAircraftPhysicalSize", "EnumAircraftCode",
            "EnumShipCode", "EnumSubmarineCode", "EnumGroundUnitCode", "EnumAircraftFacilityType", "EnumPropulsionType",
            "EnumWarheadType", "EnumCommType", "EnumFuelType", "EnumDockingFacilityType", "EnumShipPhysicalSize")}
        self.role_comment = {i: com for i, d, com in c.execute("select ID, Description, Comment from EnumSensorRole")}
        self.pays_ids = {i for i, d in self.pays.items() if d in L.PAYS_FR}
        # les composants
        self.arme = {r[0]: r for r in c.execute("select * from DataWeapon")}
        self.arme_cols = [x[1] for x in c.execute("pragma table_info(DataWeapon)")]
        self.wrec = {i: (w, d, m) for i, w, d, m, *_ in c.execute(
            "select ID, ComponentID, DefaultLoad, MaxLoad, Deprecated from DataWeaponRecord")}
        self.monture = {i: (n, cap) for i, n, cap in c.execute("select ID, Name, Capacity from DataMount")}
        self.monture_armes = self._multi("DataMountWeapons")
        self.monture_capteurs = self._multi("DataMountSensors")
        self.magasin = {i: (n, cap) for i, n, cap in c.execute("select ID, Name, Capacity from DataMagazine")}
        self.magasin_armes = self._multi("DataMagazineWeapons")
        self.capteur = {r[0]: r for r in c.execute("select * from DataSensor")}
        self.capteur_cols = [x[1] for x in c.execute("pragma table_info(DataSensor)")]
        self.capteur_cap = self._codes("DataSensorCapabilities")
        self.capteur_codes = self._codes("DataSensorCodes")
        self.capteur_freq = collections.defaultdict(list)
        for i, f in c.execute("select ID, Frequency from DataSensorFrequencySearchAndTrack"):
            self.capteur_freq[i].append(f)
        self.perf = collections.defaultdict(list)
        for row in c.execute("select ID, AltitudeBand, Throttle, Speed, AltitudeMin, AltitudeMax, Consumption from DataPropulsionPerformance"):
            self.perf[row[0]].append(row[1:])
        self.propulsion = {i: (n, t) for i, n, t in c.execute("select ID, Name, Type from DataPropulsion")}
        self.chargement = {r[0]: r for r in c.execute("select * from DataLoadout")}
        self.chargement_cols = [x[1] for x in c.execute("pragma table_info(DataLoadout)")]
        self.chargement_armes = collections.defaultdict(list)
        for i, n, comp, opt, inte in c.execute("select ID, ComponentNumber, ComponentID, Optional, Internal from DataLoadoutWeapons order by ID, ComponentNumber"):
            self.chargement_armes[i].append(comp)
        self.ogive = {r[0]: r for r in c.execute("select ID, Name, Type, DamagePoints, ExplosivesWeight, NumberOfWarheads from DataWarhead")}
        self.arme_ogives = self._multi("DataWeaponWarheads")
        self.arme_capteurs = self._multi("DataWeaponSensors")
        self.arme_prop = self._multi("DataWeaponPropulsion")
        self.arme_cibles = self._codes("DataWeaponTargets")
        self.arme_codes = self._codes("DataWeaponCodes")
        self.comm = {i: (n, t, r) for i, n, t, r in c.execute("select ID, Name, Type, Range from DataComm")}
        self.inst_aviation = {i: (t, ps, cap, rl) for i, t, ps, cap, rl in c.execute("select ID, Type, PhysicalSize, Capacity, RunwayLength from DataAircraftFacility")}
        self.carburant = {i: (t, cap) for i, t, cap in c.execute("select ID, Type, Capacity from DataFuel")}
        self.quai = {i: (t, ps, cap) for i, t, ps, cap in c.execute("select ID, Type, PhysicalSize, Capacity from DataDockingFacility")}
        # qui emporte quoi ( rempli par les plateformes )
        self.porteurs_arme = collections.defaultdict(set)      # arme -> { ( nom, pays_fr, genre, relation ) }
        self.porteurs_capteur = collections.defaultdict(set)

    def _multi(self, table):
        d = collections.defaultdict(list)
        for i, comp in self.c.execute(f"select ID, ComponentID from {table} order by ID, ComponentNumber"):
            d[i].append(comp)
        return d

    def _codes(self, table):
        d = collections.defaultdict(list)
        for i, code in self.c.execute(f"select ID, CodeID from {table}"):
            d[i].append(code)
        return d

    def lignes(self, table):
        cols = [x[1] for x in self.c.execute(f"pragma table_info({table})")]
        q = (f"select * from {table} where coalesce(Hypothetical,0)=0 and coalesce(Deprecated,0)=0 and YearCommissioned <= ? "
             f"and (YearDecommissioned = 0 or YearDecommissioned >= ?) order by ID")
        for r in self.c.execute(q, (ANNEE, ANNEE)):
            d = dict(zip(cols, r))
            if d["OperatorCountry"] in self.pays_ids:
                yield d

    def composants(self, table, i):
        if not hasattr(self, "_ordre"):
            self._ordre = {}
        if table not in self._ordre:
            cols = [x[1] for x in self.c.execute(f"pragma table_info({table})")]
            self._ordre[table] = "ComponentNumber" if "ComponentNumber" in cols else "rowid"
        return [x[0] for x in self.c.execute(f"select ComponentID from {table} where ID = ? order by {self._ordre[table]}", (i,))]

    def codes(self, table, i, enum):
        return [self.e[enum].get(x[0], str(x[0])) for x in self.c.execute(f"select CodeID from {table} where ID = ?", (i,))]

    # ---- vitesses ( nœuds ) d'une ou plusieurs propulsions : ( max, croisière, altitude max m, types )
    def vitesses(self, props):
        vmax = vcr = 0
        altmax = 0.0
        types = []
        for p in props:
            if p in self.propulsion:
                types.append(L.tr(L.PROPULSION_FR, self.e["EnumPropulsionType"].get(self.propulsion[p][1], "")))
            for band, thr, v, amin, amax, cons in self.perf.get(p, []):
                vmax = max(vmax, v or 0)
                if thr == 2:
                    vcr = max(vcr, v or 0)
                altmax = max(altmax, amax or 0)
        return vmax, vcr, altmax, [t for t in dict.fromkeys(types) if t]

    AUTODEFENSE = {2005, 2006, 2007, 2008, 2013, 3002, 3003, 3004}

    def rang_arme(self, w):
        """Ordre d'affichage : missiles, torpilles, mines et bombes d'abord ( les plus longues portées en tête ), puis les
        canons par calibre, puis l'autodéfense ( leurres, paillettes, armes légères, réservoirs )."""
        r = self.arme.get(w)
        if not r:
            return (9, 0)
        d = dict(zip(self.arme_cols, r))
        t = d["Type"]
        nom = d["Name"]
        if t in self.AUTODEFENSE or re.search(r"Chaff|Flare|Decoy|Smoke|Salvo|MG Burst|Drop Tank", nom):
            return (3, 0)
        if t == 2004:
            cal = re.match(r"\s*(\d+)", nom)
            return (2, -(int(cal.group(1)) if cal else 0))
        p = self.portee_principale(w)
        return (1, -(p[1] if p else 0))

    def tri(self, compteur):
        return sorted(compteur.items(), key=lambda x: (self.rang_arme(x[0]), -x[1]))

    def nom_arme(self, w):
        r = self.arme.get(w)
        return r[1] if r else f"arme {w}"

    def portee_principale(self, w):
        """( domaine, portée max nm ) la plus longue de l'arme."""
        r = self.arme.get(w)
        if not r:
            return None
        d = dict(zip(self.arme_cols, r))
        best = max((("air", d["AirRangeMax"] or 0), ("surface", d["SurfaceRangeMax"] or 0), ("sol", d["LandRangeMax"] or 0),
                    ("sous-marin", d["SubsurfaceRangeMax"] or 0)), key=lambda x: x[1])
        return best if best[1] > 0 else None

    def libelle_arme(self, w, n=None):
        p = self.portee_principale(w)
        s = (f"{n} x " if n else "") + self.nom_arme(w)
        if p:
            s += f" ({p[0]} {f1(p[1])} nm)"
        return s

    def armes_montures(self, montures, pays_fr, porteur, genre="?"):
        """{ arme : nombre par défaut } des affûts, et { arme } optionnelles ( charge par défaut nulle )."""
        defaut, options = collections.Counter(), set()
        for m in montures:
            for rec in self.monture_armes.get(m, []):
                if rec not in self.wrec:
                    continue
                w, d, mx = self.wrec[rec]
                if w not in self.arme:
                    continue
                self.porteurs_arme[w].add((porteur, pays_fr, genre, "affût"))
                if d and d > 0:
                    defaut[w] += d
                else:
                    options.add(w)
            for s in self.monture_capteurs.get(m, []):
                self.porteurs_capteur[s].add((porteur, pays_fr))
        return defaut, options - set(defaut)

    def armes_magasins(self, magasins, pays_fr, porteur, genre="?"):
        stock = collections.Counter()
        for g in magasins:
            for rec in self.magasin_armes.get(g, []):
                if rec not in self.wrec:
                    continue
                w, d, mx = self.wrec[rec]
                if w not in self.arme:
                    continue
                self.porteurs_arme[w].add((porteur, pays_fr, genre, "soute"))
                stock[w] += d or 0
        return stock

    def capteurs(self, ids, pays_fr, porteur):
        out = []
        for s in ids:
            if s not in self.capteur:
                continue
            self.porteurs_capteur[s].add((porteur, pays_fr))
            out.append(s)
        return list(dict.fromkeys(out))

    def libelle_capteur(self, s):
        d = dict(zip(self.capteur_cols, self.capteur[s]))
        t = L.tr(L.CAPTEUR_TYPE_FR, self.e["EnumSensorType"].get(d["Type"], ""))
        r = f", {f1(d['RangeMax'])} nm" if (d["RangeMax"] or 0) > 0 else ""
        return f"{d['Name']} ({t}{r})"

    def comms(self, ids):
        out = []
        for i in ids:
            if i in self.comm:
                n, t, r = self.comm[i]
                out.append(n)
        return list(dict.fromkeys(out))


def pays_de(db, d):
    p = db.pays.get(d["OperatorCountry"], "?")
    return p, L.PAYS_FR.get(p, p)


def periode(d):
    a, b = d["YearCommissioned"], d["YearDecommissioned"]
    return f"en service depuis {a}" + (f", retrait prévu en {b}" if b else "")


def fiche(fid, typ, titre, texte, source, tags, chiffres):
    return {"id": fid, "type": typ, "titre": titre, "texte": couper(texte), "source": source, "tags": tags, "chiffres": chiffres}


# ============================================================================================ AVIONS
def avions(db):
    out, chargs = [], []
    for d in db.lignes("DataAircraft"):
        i = d["ID"]
        p_en, p = pays_de(db, d)
        nom = d["Name"].strip()
        typ = L.tr(L.AVION_TYPE_FR, db.e["EnumAircraftType"].get(d["Type"], ""))
        cat = L.tr(L.AVION_CAT_FR, db.e["EnumAircraftCategory"].get(d["Category"], ""))
        serv = L.tr(L.SERVICE_FR, db.service.get(d["OperatorService"], ""))
        vmax, vcr, altmax, ptypes = db.vitesses(db.composants("DataAircraftPropulsion", i))
        fuel = sum(db.carburant[f][1] for f in db.composants("DataAircraftFuel", i) if f in db.carburant)
        caps = db.capteurs(db.composants("DataAircraftSensors", i), p, nom)
        defaut, options = db.armes_montures(db.composants("DataAircraftMounts", i), p, nom, "avion")
        codes = [L.CODE_AVION_FR[c] for c in db.codes("DataAircraftCodes", i, "EnumAircraftCode") if c in L.CODE_AVION_FR]
        comms = db.comms(db.composants("DataAircraftComms", i))
        los = [db.chargement[x] for x in db.composants("DataAircraftLoadouts", i) if x in db.chargement]
        los = [lo for lo in los if not dict(zip(db.chargement_cols, lo)).get("Hypothetical")]
        roles = collections.OrderedDict()
        for lo in los:
            dl = dict(zip(db.chargement_cols, lo))
            r = L.tr(L.ROLE_CHARGEMENT_FR, db.e["EnumLoadoutRole"].get(dl["LoadoutRole"], ""))
            roles.setdefault(r, []).append(dl)
            for rec in db.chargement_armes.get(dl["ID"], []):
                if rec in db.wrec and db.wrec[rec][0] in db.arme:
                    db.porteurs_arme[db.wrec[rec][0]].add((nom, p, "avion", "chargement"))
        piste = db.e["EnumRunwayLength"].get(d["RunwayLengthCode"], "")
        taille = L.tr(L.TAILLE_AVION_FR, db.e["EnumAircraftPhysicalSize"].get(d["PhysicalSizeCode"], ""))
        t = [f"{nom} : {typ}" + (f" ({cat})" if cat else "") + f" de {p} ({p_en}" + (f", {serv}" if serv else "") +
             f"), {periode(d)} dans la base DB3000 de CMO."]
        if d.get("Comments") and d["Comments"].strip() not in ("-", ""):
            t.append(f"Note de la base : {d['Comments'].strip()}.")
        t.append(f"Masse à vide {d['WeightEmpty']} kg, maximale {d['WeightMax']} kg, charge utile {d['WeightPayload']} kg ; équipage {d['Crew']}.")
        if vmax:
            t.append(f"Vitesse maximale {vmax} nœuds ({km(vmax)} km/h), croisière {vcr} nœuds ({km(vcr)} km/h)" +
                     (f", plafond des performances {int(altmax)} m" if altmax else "") + ".")
        if fuel:
            t.append(f"Carburant interne {int(fuel)} kg.")
        t.append(f"Agilité {f1(d['Agility'])}, taux de montée {f1(d['ClimbRate'])}, points de dégâts {f1(d['DamagePoints'])}" +
                 (f", taille {taille}" if taille else "") + (f", piste requise {piste}" if piste and piste != "None" else "") + ".")
        if caps:
            t.append("Capteurs : " + liste((db.libelle_capteur(s) for s in caps), 6) + ".")
        princ = [(w, n) for w, n in db.tri(defaut) if db.rang_arme(w)[0] < 3]
        leurres = sum(n for w, n in defaut.items() if db.rang_arme(w)[0] == 3)
        if princ:
            t.append("Armement fixe : " + liste((db.libelle_arme(w, n) for w, n in princ), 4) + ".")
        if leurres:
            t.append(f"Autoprotection : {leurres} salves de leurres / paillettes.")
        if codes:
            t.append("Capacités : " + ", ".join(dict.fromkeys(codes)) + ".")
        if comms:
            t.append("Liaisons : " + liste(comms, 5) + ".")
        roles_utiles = [r for r in roles if r not in ("réserve (sans armement)", "indisponible (maintenance)", "convoyage")]
        if roles_utiles:
            t.append(f"{len(los)} chargements dans la base ; rôles : " + ", ".join(roles_utiles) + f". Détail : fiche chargements-avion-{i}.")
        out.append(fiche(f"avion-{i}", "plateforme", f"{nom} ({p}) — {typ} [avion DB {i}]", " ".join(t),
                         f"DB3000 (DB3K_519.db3), table DataAircraft, ID {i}",
                         ["avion", p, p_en, typ, cat, serv] + roles_utiles[:6],
                         {"dbid": i, "genre": "avion", "pays": p, "vitesse_max_kt": vmax, "croisiere_kt": vcr,
                          "masse_max_kg": d["WeightMax"], "carburant_kg": fuel, "points_degats": d["DamagePoints"],
                          "capteurs": [db.capteur[s][1] for s in caps], "roles": roles_utiles, "n_chargements": len(los),
                          "annees": [d["YearCommissioned"], d["YearDecommissioned"]]}))
        if roles_utiles:
            chargs.append(fiche_chargements(db, d, nom, p, p_en, roles, len(los)))
    return out, chargs


def libelle_chargement(db, dl, detail=True, court=False):
    armes = collections.Counter()
    for rec in db.chargement_armes.get(dl["ID"], []):
        if rec in db.wrec:
            w, n, mx = db.wrec[rec]
            armes[w] += n or 0
    s = f"« {dl['Name'].strip()} »"
    bits = []
    if detail and armes:
        bits.append(", ".join(db.libelle_arme(w, n) for w, n in armes.items() if n))
    if dl["DefaultCombatRadius"]:
        bits.append(f"rayon {dl['DefaultCombatRadius']} nm ({km(dl['DefaultCombatRadius'])} km)")
    if court:
        return s + (" : " + " ; ".join(bits) if bits else "")
    if dl["DefaultTimeOnStation"]:
        bits.append(f"{dl['DefaultTimeOnStation']} min sur zone")
    if dl["ReadyTime"]:
        bits.append(f"préparation {dl['ReadyTime']} min")
    if dl["QuickTurnaround"]:
        bits.append(f"rotation rapide {dl['QuickTurnaround_ReadyTime']} min, {dl['QuickTurnaround_MaxSorties']} sorties")
    j = L.tr(L.JOUR_FR, db.e["EnumLoadoutTimeOfDay"].get(dl["TimeofDay"], ""))
    m = L.tr(L.METEO_FR, db.e["EnumLoadoutWeather"].get(dl["Weather"], ""))
    if (j or m) and (j, m) != ("jour et nuit", "tout temps"):
        bits.append(" / ".join(x for x in (j, m) if x))
    return s + (" : " + " ; ".join(bits) if bits else "")


def fiche_chargements(db, d, nom, p, p_en, roles, n):
    i = d["ID"]
    t = [f"Chargements DB3000 du {nom} ({p}) : {n} au total ( rayon d'action, temps sur zone et préparation au sol par chargement )."]
    chiffres = {"dbid": i, "pays": p, "roles": {}}
    for r, dls in roles.items():
        if r in ("réserve (sans armement)", "indisponible (maintenance)"):
            continue
        t.append(f"{r[0].upper() + r[1:]} ({len(dls)}) : " + " | ".join(libelle_chargement(db, dl, k == 0, k > 0) for k, dl in enumerate(dls[:2])) +
                 (" …" if len(dls) > 2 else "") + ".")
        chiffres["roles"][r] = [{"id": dl["ID"], "nom": dl["Name"].strip(), "rayon_nm": dl["DefaultCombatRadius"],
                                 "pret_min": dl["ReadyTime"]} for dl in dls[:6]]
    return fiche(f"chargements-avion-{i}", "chargement", f"Chargements du {nom} ({p}) [avion DB {i}]", " ".join(t),
                 f"DB3000, tables DataAircraftLoadouts / DataLoadout / DataLoadoutWeapons / DataWeaponRecord, avion ID {i}",
                 ["chargement", "armement", nom, p, p_en] + list(chiffres["roles"])[:6], chiffres)


# ============================================================================================ NAVIRES ET SOUS-MARINS
def armement_texte(db, defaut, options, stock):
    """( phrases d'armement, phrases secondaires ) : armes principales d'abord ; l'autodéfense résumée."""
    t, fin = [], []
    princ = [(w, n) for w, n in db.tri(defaut) if db.rang_arme(w)[0] < 3]
    auto = [(w, n) for w, n in db.tri(defaut) if db.rang_arme(w)[0] == 3]
    if princ:
        t.append("Armement ( affûts, charge par défaut ) : " + liste((db.libelle_arme(w, n) for w, n in princ), 8) + ".")
    if auto:
        t.append("Autodéfense et leurres : " + liste((db.nom_arme(w) for w, n in auto), 3) + ".")
    sp = [(w, n) for w, n in db.tri(stock) if n and db.rang_arme(w)[0] < 3]
    if sp:
        fin.append("Réserves en soute ( rechargements ) : " + liste((f"{n} x {db.nom_arme(w)}" for w, n in sp), 6) + ".")
    opt = [w for w in options if db.rang_arme(w)[0] < 3]
    if opt:
        fin.append("Munitions possibles en option : " + liste((db.nom_arme(w) for w in sorted(opt, key=db.rang_arme)), 4) + ".")
    return t, fin


def navires(db):
    out = []
    for d in db.lignes("DataShip"):
        i = d["ID"]
        p_en, p = pays_de(db, d)
        nom = d["Name"].strip()
        typ = L.sigle_navire(db.e["EnumShipType"].get(d["Type"], ""))
        cat = L.tr(L.NAVIRE_CAT_FR, db.e["EnumShipCategory"].get(d["Category"], ""))
        vmax, vcr, _, ptypes = db.vitesses(db.composants("DataShipPropulsion", i))
        defaut, options = db.armes_montures(db.composants("DataShipMounts", i), p, nom, "navire")
        stock = db.armes_magasins(db.composants("DataShipMagazines", i), p, nom, "navire")
        caps = db.capteurs(db.composants("DataShipSensors", i), p, nom)
        aviation = collections.Counter()
        for f in db.composants("DataShipAircraftFacilities", i):
            if f in db.inst_aviation:
                ty, ps, cap, rl = db.inst_aviation[f]
                aviation[L.tr(L.INSTALL_AVIATION_FR, db.e["EnumAircraftFacilityType"].get(ty, ""))] += cap or 1
        codes = db.codes("DataShipCodes", i, "EnumShipCode")
        logist = sorted({fr for c in codes for pre, fr in L.CODE_NAVIRE_PREFIXES if c.startswith(pre)})
        comms = db.comms(db.composants("DataShipComms", i))
        t = [f"{nom} : {typ}" + (f", {cat}" if cat else "") + f", de {p} ({p_en}), {periode(d)} dans la base DB3000 de CMO."]
        if d.get("Comments") and d["Comments"].strip() not in ("-", ""):
            t.append(f"Note de la base : {d['Comments'].strip()}.")
        t.append(f"Déplacement {d['DisplacementFull']} t à pleine charge, longueur {f1(d['Length'])} m, équipage {d['Crew']}" +
                 (f", vitesse maximale {vmax} nœuds ({km(vmax)} km/h)" if vmax else "") + (f", propulsion {', '.join(ptypes)}" if ptypes else "") + ".")
        t.append(f"Points de dégâts {f1(d['DamagePoints'])}, valeur de défense antimissile {d['MissileDefense']}" +
                 (f", troupes {d['TroopCapacity']}" if d.get("TroopCapacity") else "") + ".")
        arm, fin = armement_texte(db, defaut, options, stock)
        t += arm
        if caps:
            t.append("Capteurs : " + liste((db.libelle_capteur(s) for s in caps), 6) + ".")
        if aviation:
            t.append("Installations aéronautiques : " + ", ".join(f"{k} ({v})" for k, v in aviation.items()) + ".")
        if logist:
            t.append("Ravitaillement à la mer : " + ", ".join(logist) + ".")
        t += fin
        if comms:
            t.append("Liaisons : " + liste(comms, 4) + ".")
        out.append(fiche(f"navire-{i}", "plateforme", f"{nom} ({p}) — {typ} [navire DB {i}]", " ".join(t),
                         f"DB3000 (DB3K_519.db3), table DataShip, ID {i}", ["navire", p, p_en, typ, cat],
                         {"dbid": i, "genre": "navire", "pays": p, "deplacement_t": d["DisplacementFull"], "vitesse_max_kt": vmax,
                          "points_degats": d["DamagePoints"], "defense_antimissile": d["MissileDefense"],
                          "armes": {db.nom_arme(w): n for w, n in db.tri(defaut)[:12]},
                          "capteurs": [db.capteur[s][1] for s in caps][:12], "annees": [d["YearCommissioned"], d["YearDecommissioned"]]}))
    return out


def sous_marins(db):
    out = []
    for d in db.lignes("DataSubmarine"):
        i = d["ID"]
        p_en, p = pays_de(db, d)
        nom = d["Name"].strip()
        typ = L.tr(L.SOUSMARIN_TYPE_FR, db.e["EnumSubmarineType"].get(d["Type"], ""))
        vmax, vcr, _, ptypes = db.vitesses(db.composants("DataSubmarinePropulsion", i))
        defaut, options = db.armes_montures(db.composants("DataSubmarineMounts", i), p, nom, "sous-marin")
        stock = db.armes_magasins(db.composants("DataSubmarineMagazines", i), p, nom, "sous-marin")
        caps = db.capteurs(db.composants("DataSubmarineSensors", i), p, nom)
        t = [f"{nom} : {typ} de {p} ({p_en}), {periode(d)} dans la base DB3000 de CMO."]
        if d.get("Comments") and d["Comments"].strip() not in ("-", ""):
            t.append(f"Note de la base : {d['Comments'].strip()}.")
        t.append(f"Déplacement {d['DisplacementFull']} t en plongée/pleine charge, longueur {f1(d['Length'])} m, équipage {d['Crew']}, "
                 f"immersion maximale {abs(d['MaxDepth'] or 0)} m" + (f", vitesse maximale {vmax} nœuds" if vmax else "") +
                 (f", propulsion {', '.join(ptypes)}" if ptypes else "") + f". Points de dégâts {f1(d['DamagePoints'])}.")
        arm, fin = armement_texte(db, defaut, options, stock)
        t += arm
        if caps:
            t.append("Capteurs : " + liste((db.libelle_capteur(s) for s in caps), 6) + ".")
        t += fin
        out.append(fiche(f"sousmarin-{i}", "plateforme", f"{nom} ({p}) — {typ} [sous-marin DB {i}]", " ".join(t),
                         f"DB3000 (DB3K_519.db3), table DataSubmarine, ID {i}", ["sous-marin", p, p_en, typ],
                         {"dbid": i, "genre": "sous-marin", "pays": p, "immersion_max_m": abs(d["MaxDepth"] or 0), "vitesse_max_kt": vmax,
                          "points_degats": d["DamagePoints"], "armes": {db.nom_arme(w): n for w, n in db.tri(defaut)[:12]},
                          "reserves": {db.nom_arme(w): n for w, n in stock.most_common(12)},
                          "capteurs": [db.capteur[s][1] for s in caps][:12], "annees": [d["YearCommissioned"], d["YearDecommissioned"]]}))
    return out


# ============================================================================================ INSTALLATIONS ET UNITÉS TERRESTRES
def installations(db):
    out = []
    for d in db.lignes("DataFacility"):
        i = d["ID"]
        p_en, p = pays_de(db, d)
        nom = d["Name"].strip()
        cat = L.tr(L.INSTALLATION_CAT_FR, db.e["EnumFacilityCategory"].get(d["Category"], ""))
        typ = L.tr(L.INSTALLATION_TYPE_FR, db.e["EnumFacilityType"].get(d["Type"], ""))
        defaut, options = db.armes_montures(db.composants("DataFacilityMounts", i), p, nom, "installation")
        stock = db.armes_magasins(db.composants("DataFacilityMagazines", i), p, nom, "installation")
        caps = db.capteurs(db.composants("DataFacilitySensors", i), p, nom)
        aviation = collections.Counter()
        for f in db.composants("DataFacilityAircraftFacilities", i):
            if f in db.inst_aviation:
                ty, ps, cap, rl = db.inst_aviation[f]
                aviation[L.tr(L.INSTALL_AVIATION_FR, db.e["EnumAircraftFacilityType"].get(ty, ""))] += cap or 1
        mobile = d["Category"] in (5001, 5002, 5003, 5004, 5005)
        blind = L.tr(L.BLINDAGE_FR, db.e["EnumArmorType"].get(d["ArmorGeneral"], ""))
        genre = "unité mobile au sol ( installation mobile de CMO )" if mobile else "installation fixe"
        t = [f"{nom} : {genre}" + (f", {typ}" if typ else "") + (f", {cat}" if cat else "") + f", de {p} ({p_en}), {periode(d)} dans la base DB3000."]
        if mobile:
            t.append("Dans CMO, les formations terrestres ( bataillons sol-air, batteries, régiments ) sont des installations mobiles "
                     "( catégorie 5001 ) qui peuvent rouler ; un véhicule isolé est une unité terrestre.")
        t.append(f"Points de dégâts {f1(d['DamagePoints'])}, blindage {blind}, équipage {d['Crew']}" +
                 (f", défense antimissile {d['MissileDefense']}" if d.get("MissileDefense") else "") + ".")
        arm, fin = armement_texte(db, defaut, options, stock)
        t += arm
        if caps:
            t.append("Capteurs : " + liste((db.libelle_capteur(s) for s in caps), 6) + ".")
        t += fin
        if aviation:
            t.append("Installations aéronautiques : " + ", ".join(f"{k} ({v})" for k, v in aviation.items()) + ".")
        portee_air = max((db.portee_principale(w)[1] for w in defaut if db.portee_principale(w) and db.portee_principale(w)[0] == "air"), default=0)
        out.append(fiche(f"installation-{i}", "plateforme", f"{nom} ({p}) — installation {typ or cat} [installation DB {i}]", " ".join(t),
                         f"DB3000 (DB3K_519.db3), table DataFacility, ID {i}", ["installation", p, p_en, typ, cat] + (["mobile"] if mobile else []),
                         {"dbid": i, "genre": "installation", "mobile": mobile, "pays": p, "points_degats": d["DamagePoints"],
                          "armes": {db.nom_arme(w): n for w, n in db.tri(defaut)[:12]},
                          "capteurs": [db.capteur[s][1] for s in caps][:12], "portee_air_max_nm": portee_air,
                          "annees": [d["YearCommissioned"], d["YearDecommissioned"]]}))
    return out


def terrestres(db):
    out = []
    for d in db.lignes("DataGroundUnit"):
        i = d["ID"]
        p_en, p = pays_de(db, d)
        nom = d["Name"].strip()
        cat = L.tr(L.TERRESTRE_CAT_FR, db.e["EnumGroundUnitCategory"].get(d["Category"], ""))
        vmax, vcr, _, ptypes = db.vitesses(db.composants("DataGroundUnitPropulsion", i))
        defaut, options = db.armes_montures(db.composants("DataGroundUnitMounts", i), p, nom, "unité terrestre")
        stock = db.armes_magasins(db.composants("DataGroundUnitMagazines", i), p, nom, "unité terrestre")
        caps = db.capteurs(db.composants("DataGroundUnitSensors", i), p, nom)
        blind = L.tr(L.BLINDAGE_FR, db.e["EnumArmorType"].get(d["ArmorGeneral"], ""))
        t = [f"{nom} : unité terrestre ( véhicule ), {cat}, de {p} ({p_en}), {periode(d)} dans la base DB3000. Dans CMO c'est une unité "
             "de type « Vehicle » ( table DataGroundUnit ), distincte des formations sol qui sont des installations mobiles."]
        t.append(f"Masse {f1(d['Mass'])} kg, équipage {d['Crew']}, troupes transportées {d['TroopCapacity']}, blindage {blind}, "
                 f"points de dégâts {f1(d['DamagePoints'])}" + (f", vitesse maximale {vmax} nœuds ({km(vmax)} km/h)" if vmax else "") + ".")
        arm, fin = armement_texte(db, defaut, options, stock)
        t += arm
        if caps:
            t.append("Capteurs : " + liste((db.libelle_capteur(s) for s in caps), 6) + ".")
        t += fin
        out.append(fiche(f"terrestre-{i}", "plateforme", f"{nom} ({p}) — unité terrestre {cat} [véhicule DB {i}]", " ".join(t),
                         f"DB3000 (DB3K_519.db3), table DataGroundUnit, ID {i}", ["unité terrestre", "véhicule", p, p_en, cat],
                         {"dbid": i, "genre": "unité terrestre", "pays": p, "masse_kg": d["Mass"], "vitesse_max_kt": vmax,
                          "blindage": blind, "points_degats": d["DamagePoints"], "armes": {db.nom_arme(w): n for w, n in db.tri(defaut)[:12]},
                          "annees": [d["YearCommissioned"], d["YearDecommissioned"]]}))
    return out


# ============================================================================================ ARMES
def armes(db):
    out = []
    for w, porteurs in sorted(db.porteurs_arme.items()):
        d = dict(zip(db.arme_cols, db.arme[w]))
        if d.get("Hypothetical"):
            continue
        nom = d["Name"].strip()
        typ = L.tr(L.ARME_TYPE_FR, db.e["EnumWeaponType"].get(d["Type"], ""))
        gen = db.e["EnumWeaponGeneration"].get(d["Generation"], "")
        t = [f"{nom} : {typ}" + (f", génération {gen}" if gen and gen not in ("None", "Not Applicable (N/A)") else "") + "."]
        if d.get("Comments") and d["Comments"].strip() not in ("-", ""):
            t.append(f"Note de la base : {d['Comments'].strip()}.")
        if d["Weight"]:
            t.append(f"Masse {f1(d['Weight'])} kg" + (f", longueur {f1(d['Length'])} m" if d["Length"] else "") + ".")
        portees, chiffres = [], {"dbid": w, "type": typ}
        for dom, cle, pok in (("aéronefs", "Air", "AirPoK"), ("navires de surface", "Surface", "SurfacePoK"),
                              ("cibles terrestres", "Land", "LandPoK"), ("sous-marins", "Subsurface", "SubsurfacePoK")):
            mx, mn = d[f"{cle}RangeMax"] or 0, d[f"{cle}RangeMin"] or 0
            if mx > 0:
                portees.append(f"contre {dom} {f1(mn)} à {f1(mx)} nm ({km(mn)}-{km(mx)} km)" + (f", PoK de base {f1(d[pok])} %" if d[pok] else ""))
                chiffres[f"portee_{cle.lower()}_nm"] = mx
                chiffres[f"pok_{cle.lower()}"] = d[pok]
        if portees:
            t.append("Portées : " + " ; ".join(portees) + ".")
        vit = max((v for p in db.arme_prop.get(w, []) for _, thr, v, *_ in db.perf.get(p, [])), default=0)
        if vit:
            mach = str(round(vit / 661.5, 1)).replace(".", ",")
            t.append(f"Vitesse {vit} nœuds ({km(vit)} km/h, ≈ Mach {mach}).")
            chiffres["vitesse_kt"] = vit
        if d["TorpedoSpeedFull"]:
            t.append(f"Torpille : {d['TorpedoSpeedFull']} nœuds sur {f1(d['TorpedoRangeFull'])} nm, ou {d['TorpedoSpeedCruise']} nœuds sur {f1(d['TorpedoRangeCruise'])} nm.")
        if d["CEP"]:
            t.append(f"Précision (CEP) {d['CEP']} m.")
        if d["CruiseAltitude"]:
            t.append(f"Altitude de croisière {f1(d['CruiseAltitude'])} m.")
        if d["MaxFlightTime"]:
            t.append(f"Temps de vol maximal {d['MaxFlightTime']} s.")
        cibles = [L.tr(L.CIBLE_FR, db.e["EnumWeaponTarget"].get(c, "")) for c in db.arme_cibles.get(w, [])]
        if cibles:
            t.append("Cibles possibles : " + ", ".join(cibles) + ".")
            chiffres["cibles"] = cibles
        seek = [db.capteur[s][1] for s in db.arme_capteurs.get(w, []) if s in db.capteur]
        if seek:
            t.append("Autodirecteur / guidage : " + ", ".join(dict.fromkeys(seek)) + ".")
        codes = [L.CODE_ARME_FR.get(db.e["EnumWeaponCode"].get(c, ""), db.e["EnumWeaponCode"].get(c, "")) for c in db.arme_codes.get(w, [])]
        codes = [c for c in codes if c and "DELETED" not in c]
        if codes:
            t.append("Particularités : " + ", ".join(dict.fromkeys(codes)) + ".")
        for o in db.arme_ogives.get(w, []):
            if o in db.ogive:
                _, onom, oty, dp, kg, nb = db.ogive[o]
                t.append(f"Ogive {L.tr(L.OGIVE_FR, db.e['EnumWarheadType'].get(oty, ''))} : {f1(dp)} points de dégâts" +
                         (f", {f1(kg)} kg d'explosif" if kg else "") + (f", {nb} têtes" if nb and nb > 1 else "") + ".")
                chiffres.setdefault("ogive_points_degats", dp)
                break
        pays = sorted({p for _, p, _, _ in porteurs})
        noms = sorted({n for n, *_ in porteurs})
        tireurs = sorted({n for n, _, g, rel in porteurs if rel != "soute"})
        soutes = sorted({n for n, _, g, rel in porteurs if rel == "soute"} - set(tireurs))
        if tireurs:
            t.append(f"Mise en œuvre en 2026 par {len(tireurs)} types de plateformes ( " + liste(tireurs, 8) + " ).")
        if soutes:
            t.append(f"En soute ( rechargement ) sur {len(soutes)} types ( " + liste(soutes, 4) + " ).")
        t.append("Pays : " + ", ".join(pays) + ".")
        chiffres["pays"] = pays
        chiffres["porteurs"] = (tireurs + soutes)[:20]
        out.append(fiche(f"arme-{w}", "arme", f"{nom} — {typ} [arme DB {w}]", " ".join(t), f"DB3000 (DB3K_519.db3), table DataWeapon, ID {w}",
                         ["arme", typ] + cibles[:4] + pays[:6], chiffres))
    return out


# ============================================================================================ CAPTEURS
def capteurs(db):
    out = []
    for s, porteurs in sorted(db.porteurs_capteur.items()):
        d = dict(zip(db.capteur_cols, db.capteur[s]))
        if d.get("Hypothetical"):
            continue
        nom = d["Name"].strip()
        typ = L.tr(L.CAPTEUR_TYPE_FR, db.e["EnumSensorType"].get(d["Type"], ""))
        role_en = db.e["EnumSensorRole"].get(d["Role"], "")
        role = L.role_capteur(role_en)
        gen = db.e["EnumSensorGeneration"].get(d["Generation"], "")
        t = [f"{nom} : {typ}" + (f", rôle « {role} » ({role_en})" if role_en and role_en != "None" else "") +
             (f", génération {gen}" if gen and gen not in ("None", "Not Applicable (N/A)") else "") + "."]
        if d.get("Comments") and d["Comments"].strip() not in ("-", ""):
            t.append(f"Note de la base : {d['Comments'].strip()}.")
        chiffres = {"dbid": s, "type": typ, "role": role_en}
        if (d["RangeMax"] or 0) > 0:
            t.append(f"Portée {f1(d['RangeMin'] or 0)} à {f1(d['RangeMax'])} nm ({km(d['RangeMax'])} km)" +
                     (f", altitude couverte jusqu'à {f1(d['AltitudeMax'])} m" if d["AltitudeMax"] else "") + ".")
            chiffres["portee_max_nm"] = d["RangeMax"]
        caps = [L.tr(L.CAPACITE_CAPTEUR_FR, db.e["EnumSensorCapability"].get(c, "")) for c in db.capteur_cap.get(s, [])]
        if caps:
            t.append("Capacités : " + ", ".join(caps) + ".")
        codes = [L.tr(L.CODE_CAPTEUR_FR, db.e["EnumSensorCode"].get(c, "")) for c in db.capteur_codes.get(s, [])]
        if codes:
            t.append("Particularités : " + ", ".join(codes) + ".")
        fr = [db.e["EnumSensorFrequency"].get(f, "").split(" [")[0] for f in db.capteur_freq.get(s, [])]
        if fr:
            t.append("Bandes : " + ", ".join(dict.fromkeys(fr)) + ".")
        mx = [(k, d[f"MaxContacts{k}"]) for k in ("Air", "Surface", "Submarine", "Illuminate") if d.get(f"MaxContacts{k}")]
        if mx:
            noms_c = {"Air": "air", "Surface": "surface", "Submarine": "sous-marins", "Illuminate": "illumination"}
            t.append("Contacts simultanés max : " + ", ".join(f"{noms_c[k]} {v}" for k, v in mx) + ".")
        if d["ScanInterval"]:
            t.append(f"Intervalle de balayage {d['ScanInterval']} s.")
        if d["Type"] == 3002 and (d["ECMGain"] or d["ECMNumberOfTargets"]):
            t.append(f"Brouilleur : gain {f1(d['ECMGain'])}, {d['ECMNumberOfTargets']} cibles simultanées, réduction de PoK {f1(d['ECMPoKReduction'])}.")
        if d["Type"] == 3001 and d["ESMNumberOfChannels"]:
            t.append(f"ESM : {d['ESMNumberOfChannels']} canaux" + (", identification précise de l'émetteur" if d["ESMPreciseEmitterID"] else "") + ".")
        if d["SonarTowLength"]:
            t.append(f"Antenne remorquée de {f1(d['SonarTowLength'])} m, immersion {f1(d['SonarMinimumDeploymentDepth'])} à {f1(d['SonarMaximumDeploymentDepth'])} m.")
        if d["MineSweepWidth"]:
            t.append(f"Largeur de dragage {f1(d['MineSweepWidth'])} m, vitesse de dragage max {d['MineSweepMaximumSpeed']} nœuds.")
        pays = sorted({p for _, p in porteurs})
        noms = sorted({n for n, _ in porteurs})
        t.append(f"Monté en 2026 sur {len(noms)} types de plateformes ( " + liste(noms, 8) + " ), pays : " + ", ".join(pays) + ".")
        chiffres["pays"] = pays
        chiffres["porteurs"] = noms[:20]
        out.append(fiche(f"capteur-{s}", "capteur", f"{nom} — {typ} [capteur DB {s}]", " ".join(t), f"DB3000 (DB3K_519.db3), table DataSensor, ID {s}",
                         ["capteur", typ, role] + pays[:6], chiffres))
    return out


def ecrire(nom, fiches):
    os.makedirs(SORTIE, exist_ok=True)
    with open(os.path.join(SORTIE, f"db_{nom}.jsonl"), "w") as f:
        for x in fiches:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"{nom:14s} {len(fiches):6d} fiches")


if __name__ == "__main__":
    db = DB()
    av, ch = avions(db)
    ecrire("avions", av)
    ecrire("chargements", ch)
    ecrire("navires", navires(db))
    ecrire("sous_marins", sous_marins(db))
    ecrire("installations", installations(db))
    ecrire("terrestres", terrestres(db))
    ecrire("armes", armes(db))
    ecrire("capteurs", capteurs(db))
