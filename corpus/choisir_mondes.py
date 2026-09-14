#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
choisir_mondes.py - choisit les mondes de CHACAL par leur SITE, pas par leur numero de graine.

POURQUOI CE SCRIPT EXISTE
    Le generateur de la mission, CHACAL_fnc_rnd, est un Lehmer 75*x+74 mod 65537 :
    un cycle unique de 65 536 etats. Un tirage de monde en consomme plus de deux mille.
    Deux graines dont les marches se rejoignent rendent LE MEME monde, a la virgule pres.
    Mesure : 3754 et 108 partagent [12113.6, 19333.8] ; 5701 et 106 partagent
    [7991.6, 19546.9] ; 109 et 115 partagent [12678.7, 15760.4].
    Cinq des huit "graines juges" gelees le 14/09/2026 au matin etaient donc brulees.

    L'IDENTITE D'UN MONDE EST SON SITE, PAS SON NUMERO.

CE QU'IL FAIT
    a. lit toutes les lignes CHACAL|GEO|... et CHACAL|OK|monde|... des RPT de /mnt/data/hmt/runs ;
       construit la table graine -> site ;
    b. dedoublonne PAR SITE : deux graines a moins de SEUIL_MEME_MONDE metres sont le meme
       monde ; la plus petite graine est la representante, les autres sont des alias ;
    c. marque BRULE tout monde deja joue et tout monde a moins de SEUIL_DISTINCT metres
       d'un site deja joue ;
    d. choisit, par un glouton deterministe (graines croissantes), des mondes mutuellement
       distants d'au moins SEUIL_DISTINCT metres et distants d'autant de tout site brule :
       les N_JUGES premiers acceptes sont les JUGES, les N_CORPUS suivants le CORPUS ;
    e. ecrit mondes.json et imprime trois controles qui doivent etre VERTS.

    Ce script ne lance rien et ne modifie aucune mission. Il lit des RPT deja ecrits.
"""

import os
import re
import sys
import json
import math
import datetime
import collections

# ----------------------------------------------------------------------------- reglages
RACINE_RUNS = "/mnt/data/hmt/runs"
SORTIE = "/mnt/data/hmt/depot/corpus/mondes.json"

SEUIL_MEME_MONDE = 5.0      # metres : en deca, deux graines rendent le meme monde
SEUIL_DISTINCT = 1000.0     # metres : deux mondes retenus doivent etre au moins si loin
N_JUGES = 8
N_CORPUS = 36

# Graines deja JOUEES : elles ont servi a mesurer et a regler, leurs mondes sont brules.
GRAINES_JOUEES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12]

# Collisions mesurees a la main le 14/09/2026 : le controle (iii) exige de les retrouver.
COLLISIONS_CONNUES = [(3754, 108), (5701, 106), (109, 115)]

RE_GEO = re.compile(
    r"CHACAL\|GEO\|[^|]*\|graine\|(\d+)\|site\|\[\s*([-0-9.eE]+)\s*,\s*([-0-9.eE]+)")
RE_OK = re.compile(
    r"CHACAL\|OK\|monde\|essais\|\d+\|site\|\[\s*([-0-9.eE]+)\s*,\s*([-0-9.eE]+)")
RE_DOSSIER_GRAINE = re.compile(r"/g(\d+)(?:_r\d+)?/")


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ----------------------------------------------------------------------------- a. lecture
def lire_les_rpt(racine=RACINE_RUNS):
    """Parcourt tous les *.rpt sous racine. Rend (table, journal).

    table : graine -> {"site": (x, y), "source": "GEO" | "OK|monde"}
    La ligne GEO fait foi quand elle existe ; la ligne OK|monde sert aux graines
    jouees, qui n'ont pas de recolte de geometrie.
    """
    geo = collections.defaultdict(set)     # graine (lue dans la ligne) -> {sites}
    okm = collections.defaultdict(set)     # graine (lue dans le dossier g<n>) -> {sites}
    n_fichiers = 0
    n_geo = 0
    n_ok = 0

    chemins = []
    for dossier, _sous, fichiers in os.walk(racine):
        for nom in fichiers:
            if nom.endswith(".rpt"):
                chemins.append(os.path.join(dossier, nom))
    chemins.sort()                          # lecture deterministe

    for chemin in chemins:
        n_fichiers += 1
        m = RE_DOSSIER_GRAINE.search(chemin + "/")
        graine_dossier = int(m.group(1)) if m else None
        try:
            texte = open(chemin, errors="replace").read()
        except OSError:
            continue
        for mm in RE_GEO.finditer(texte):
            n_geo += 1
            g = int(mm.group(1))
            geo[g].add((round(float(mm.group(2)), 1), round(float(mm.group(3)), 1)))
        if graine_dossier is not None:
            for mm in RE_OK.finditer(texte):
                n_ok += 1
                okm[graine_dossier].add(
                    (round(float(mm.group(1)), 1), round(float(mm.group(2)), 1)))

    incoherentes = sorted([g for g, s in geo.items() if len(s) > 1] +
                          [g for g, s in okm.items() if len(s) > 1 and g not in geo])

    table = {}
    for g in sorted(geo):
        table[g] = {"site": sorted(geo[g])[0], "source": "GEO"}
    for g in sorted(okm):
        if g not in table and len(okm[g]) == 1:
            table[g] = {"site": sorted(okm[g])[0], "source": "OK|monde"}

    journal = {
        "racine": racine,
        "fichiers_rpt_lus": n_fichiers,
        "lignes_GEO_lues": n_geo,
        "lignes_OK_monde_lues": n_ok,
        "graines_avec_ligne_GEO": len(geo),
        "graines_avec_site": len(table),
        "graines_a_site_incoherent": incoherentes,
    }
    return table, journal


# ------------------------------------------------------------------- b. dedoublonnage
def dedoublonner(table):
    """Regroupe les graines qui rendent le meme site. Rend (representantes, alias)."""
    representantes = []
    alias = collections.defaultdict(list)
    for g in sorted(table):
        site = table[g]["site"]
        trouvee = None
        for r in representantes:
            if distance(table[r]["site"], site) < SEUIL_MEME_MONDE:
                trouvee = r
                break
        if trouvee is None:
            representantes.append(g)
        else:
            alias[trouvee].append(g)
    return representantes, alias


# ------------------------------------------------------------------------ c. brulures
def bruler(table, representantes, alias):
    """Rend (brules, sites_joues, joues_introuvables).

    brules : graine representante -> raison (str)
    """
    jouees = set(GRAINES_JOUEES)
    sites_joues = {g: table[g]["site"] for g in GRAINES_JOUEES if g in table}
    joues_introuvables = [g for g in GRAINES_JOUEES if g not in table]

    brules = {}
    for r in representantes:
        famille = set([r] + alias[r])
        deja = sorted(jouees & famille)
        if deja:
            brules[r] = "monde deja joue (graines %s)" % (", ".join(str(x) for x in deja))
            continue
        for gj in sorted(sites_joues):
            d = distance(table[r]["site"], sites_joues[gj])
            if d < SEUIL_DISTINCT:
                brules[r] = "a %.1f m du site de la graine jouee %d" % (d, gj)
                break
    return brules, sites_joues, joues_introuvables


# --------------------------------------------------------------------------- d. glouton
def choisir(table, representantes, brules, sites_joues):
    """Glouton deterministe : graines croissantes, accepte si loin de tout accepte
    ET de tout site brule (sites joues compris)."""
    sites_brules = [table[r]["site"] for r in sorted(brules)]
    for g in sorted(sites_joues):
        s = sites_joues[g]
        if s not in sites_brules:
            sites_brules.append(s)

    candidates = [r for r in sorted(representantes) if r not in brules]
    acceptes = []
    refus = {}
    for g in candidates:
        site = table[g]["site"]
        trop_pres_accepte = [a for a in acceptes
                             if distance(site, table[a]["site"]) < SEUIL_DISTINCT]
        if trop_pres_accepte:
            a = trop_pres_accepte[0]
            refus[g] = "a %.1f m du monde retenu %d" % (
                distance(site, table[a]["site"]), a)
            continue
        trop_pres_brule = [s for s in sites_brules if distance(site, s) < SEUIL_DISTINCT]
        if trop_pres_brule:
            refus[g] = "a %.1f m d'un site brule" % distance(site, trop_pres_brule[0])
            continue
        acceptes.append(g)
    return acceptes, refus, candidates


# ------------------------------------------------------------------------- controles
def controler(table, retenus, roles, sites_joues, alias, representante_de):
    controles = []

    # (i) aucune paire de mondes retenus a moins de SEUIL_DISTINCT
    pire = None
    for i, a in enumerate(retenus):
        for b in retenus[i + 1:]:
            d = distance(table[a]["site"], table[b]["site"])
            if pire is None or d < pire[0]:
                pire = (d, a, b)
    if pire is None:
        controles.append(("i", False, "aucun monde retenu : rien a verifier"))
    else:
        ok = pire[0] >= SEUIL_DISTINCT
        controles.append(("i", ok,
                          "distance minimale entre mondes retenus = %.1f m (%d vs %d), seuil %.0f m"
                          % (pire[0], pire[1], pire[2], SEUIL_DISTINCT)))

    # (ii) aucun juge a moins de SEUIL_DISTINCT d'un site joue
    juges = [g for g in retenus if roles[g] == "JUGE"]
    pire2 = None
    for g in juges:
        for gj, sj in sites_joues.items():
            d = distance(table[g]["site"], sj)
            if pire2 is None or d < pire2[0]:
                pire2 = (d, g, gj)
    if pire2 is None:
        controles.append(("ii", False, "aucun juge ou aucun site joue connu"))
    else:
        ok = pire2[0] >= SEUIL_DISTINCT
        controles.append(("ii", ok,
                          "distance minimale juge <-> site joue = %.1f m (juge %d vs graine jouee %d)"
                          % (pire2[0], pire2[1], pire2[2])))

    # (iii) les trois collisions connues sont bien vues comme alias
    details = []
    tout_ok = True
    for a, b in COLLISIONS_CONNUES:
        ra = representante_de.get(a)
        rb = representante_de.get(b)
        vu = (ra is not None and ra == rb)
        tout_ok = tout_ok and vu
        if a in table and b in table:
            d = distance(table[a]["site"], table[b]["site"])
            details.append("%d/%d : %s (representante %s, d = %.2f m)"
                           % (a, b, "ALIAS" if vu else "NON DETECTE", ra, d))
        else:
            details.append("%d/%d : site absent de la table" % (a, b))
    controles.append(("iii", tout_ok, " ; ".join(details)))
    return controles


# ------------------------------------------------------------------------------- main
def main():
    sortie = sys.argv[1] if len(sys.argv) > 1 else SORTIE

    table, journal = lire_les_rpt()
    representantes, alias = dedoublonner(table)
    brules, sites_joues, joues_introuvables = bruler(table, representantes, alias)
    acceptes, refus, candidates = choisir(table, representantes, brules, sites_joues)

    roles = {}
    for i, g in enumerate(acceptes):
        roles[g] = "JUGE" if i < N_JUGES else "CORPUS"
    retenus = acceptes[:N_JUGES + N_CORPUS]
    roles = {g: roles[g] for g in retenus}

    representante_de = {}
    for r in representantes:
        representante_de[r] = r
        for a in alias[r]:
            representante_de[a] = r

    # distance au monde retenu le plus proche
    plus_proche = {}
    for g in retenus:
        autres = [(distance(table[g]["site"], table[h]["site"]), h)
                  for h in retenus if h != g]
        plus_proche[g] = min(autres) if autres else (None, None)

    mondes = []
    for g in retenus:
        d, voisin = plus_proche[g]
        mondes.append({
            "graine": g,
            "site": [table[g]["site"][0], table[g]["site"][1]],
            "role": roles[g],
            "alias": sorted(alias[g]),
            "source": table[g]["source"],
            "distance_au_plus_proche_m": (round(d, 1) if d is not None else None),
            "monde_le_plus_proche": voisin,
        })

    liste_brules = []
    for r in sorted(brules):
        liste_brules.append({
            "graine": r,
            "site": [table[r]["site"][0], table[r]["site"][1]],
            "alias": sorted(alias[r]),
            "pourquoi": brules[r],
        })
    for g in sorted(refus):
        liste_brules.append({
            "graine": g,
            "site": [table[g]["site"][0], table[g]["site"][1]],
            "alias": sorted(alias[g]),
            "pourquoi": "ecarte par le glouton : " + refus[g],
        })

    controles = controler(table, retenus, roles, sites_joues, alias, representante_de)
    tout_vert = all(ok for _, ok, _ in controles)

    doc = {
        "genere_le": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "genere_par": "corpus/choisir_mondes.py",
        "regle": {
            "identite": "L'IDENTITE D'UN MONDE EST SON SITE, PAS SON NUMERO DE GRAINE. "
                        "CHACAL_fnc_rnd est un Lehmer 75x+74 mod 65537 : un cycle unique de "
                        "65 536 etats, et un tirage de monde en consomme plus de deux mille. "
                        "Deux graines dont les marches se rejoignent rendent le meme monde.",
            "juges": "Les mondes JUGE ne servent JAMAIS a entrainer, a regler un seuil, ni a "
                     "choisir un modele. Ils ne servent qu a JUGER, une fois, a la fin. Toute "
                     "campagne qui les utilise hors certification finale invalide la "
                     "certification.",
            "corpus": "Les mondes CORPUS servent a entrainer et a regler. Ils sont distincts "
                      "des juges par construction : au moins %.0f m entre deux sites retenus."
                      % SEUIL_DISTINCT,
            "brules": "Un monde est brule s il a deja ete joue, ou s il est a moins de %.0f m "
                      "d un site deja joue : jouer un site le rend impropre au jugement."
                      % SEUIL_DISTINCT,
            "usage": "Ne jamais designer un monde par sa graine seule sans verifier son site. "
                     "Les alias listes ci-dessous sont des graines qui rendent LE MEME monde.",
        },
        "parametres": {
            "seuil_meme_monde_m": SEUIL_MEME_MONDE,
            "seuil_distinct_m": SEUIL_DISTINCT,
            "n_juges_vises": N_JUGES,
            "n_corpus_vises": N_CORPUS,
            "graines_jouees": GRAINES_JOUEES,
        },
        "lecture": journal,
        "bilan": {
            "mondes_distincts": len(representantes),
            "mondes_brules": len(brules),
            "candidats": len(candidates),
            "acceptes_par_le_glouton": len(acceptes),
            "juges_retenus": sum(1 for g in retenus if roles[g] == "JUGE"),
            "corpus_retenus": sum(1 for g in retenus if roles[g] == "CORPUS"),
            "manque": max(0, (N_JUGES + N_CORPUS) - len(retenus)),
        },
        "sites_joues": {str(g): [s[0], s[1]] for g, s in sorted(sites_joues.items())},
        "sites_joues_introuvables": joues_introuvables,
        "juges": [g for g in retenus if roles[g] == "JUGE"],
        "corpus": [g for g in retenus if roles[g] == "CORPUS"],
        "mondes": mondes,
        "brules": liste_brules,
        "controles": [{"controle": c, "vert": ok, "detail": d} for c, ok, d in controles],
        "controles_tous_verts": tout_vert,
    }

    with open(sortie, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=True)
        f.write("\n")

    # ------------------------------------------------------------------ impression
    print("LECTURE")
    print("  fichiers .rpt lus            : %d" % journal["fichiers_rpt_lus"])
    print("  lignes CHACAL|GEO            : %d" % journal["lignes_GEO_lues"])
    print("  lignes CHACAL|OK|monde       : %d" % journal["lignes_OK_monde_lues"])
    print("  graines avec un site         : %d" % journal["graines_avec_site"])
    if journal["graines_a_site_incoherent"]:
        print("  ATTENTION graines a site incoherent : %s"
              % journal["graines_a_site_incoherent"])
    print("")
    print("MONDES")
    print("  mondes distincts (site)      : %d" % len(representantes))
    print("  dont brules                  : %d" % len(brules))
    print("  candidats                    : %d" % len(candidates))
    print("  acceptes par le glouton      : %d" % len(acceptes))
    if joues_introuvables:
        print("  graines jouees sans site connu : %s (elles ne brulent rien)"
              % joues_introuvables)
    print("")
    print("JUGES")
    for g in retenus:
        if roles[g] == "JUGE":
            d, v = plus_proche[g]
            print("  g%-6d site [%9.1f, %9.1f]  alias %-18s  plus proche %.0f m (g%s)"
                  % (g, table[g]["site"][0], table[g]["site"][1],
                     sorted(alias[g]) if alias[g] else "-", d, v))
    print("")
    corpus = [g for g in retenus if roles[g] == "CORPUS"]
    print("CORPUS (%d) : %s" % (len(corpus), corpus))
    if len(retenus) < N_JUGES + N_CORPUS:
        print("")
        print("  INSUFFISANT : %d mondes disponibles, %d demandes (%d juges + %d corpus)."
              % (len(retenus), N_JUGES + N_CORPUS, N_JUGES, N_CORPUS))
        print("  Il manque %d mondes. Pour en avoir plus il faut recolter de la GEOMETRIE"
              % ((N_JUGES + N_CORPUS) - len(retenus)))
        print("  sur de nouvelles graines : la reserve actuelle est epuisee.")
    print("")
    print("CONTROLES")
    for c, ok, d in controles:
        print("  (%s) %-5s %s" % (c, "VERT" if ok else "ROUGE", d))
    print("")
    print("ecrit : %s" % sortie)
    print("VERDICT : %s" % ("TOUS LES CONTROLES SONT VERTS"
                            if tout_vert else "UN CONTROLE EST ROUGE - NE PAS COMMITER"))
    return 0 if tout_vert else 1


if __name__ == "__main__":
    sys.exit(main())
