#!/usr/bin/env python3
"""chacal_lire - extrait un episode CHACAL d'un RPT Arma et le CERTIFIE.

Le RPT est le seul exemplaire du corpus tant que ce script n'a pas tourne.
Il ne se contente donc pas de convertir : il REFUSE un episode dont les
instruments ne se sont pas prouves. Les deux portes sont le canari (mort ET
tir) et la continuite des pas. Un corpus qui passe sans porte est un corpus
qu'on n'osera plus interroger dans six mois.
"""
import re, sys, json, csv, os

CH = "CHACAL|"

def lire(path):
    """Lit les lignes CHACAL et S'ARRETE A LA PREMIERE LIGNE `FINI`.

    Correction 2 (Fable, 03/09) : le premier episode accepte contenait 6 193
    lignes APRES son verdict, soit 16 % du fichier, dont trois morts de FS
    posterieures a l'episode. Elles n'appartiennent a rien. On les compte -
    c'est une porte - et on ne les ingere pas.
    """
    lignes, apres = [], 0
    fini = False
    with open(path, "r", errors="ignore") as f:
        for l in f:
            i = l.find(CH)
            if i < 0:
                continue
            t = l[i:].rstrip().rstrip('"')
            if fini:
                # L'epilogue de la mission (arret de la capture, serveur au repos)
                # suit le verdict par construction et n'est pas de la donnee.
                if t.split("|")[1:2] not in (["OK"], ["AVERT"]):
                    apres += 1
                continue
            lignes.append(t)
            if t.split("|")[1:2] == ["FINI"]:
                fini = True
    return lignes, apres

def parse_liste(s):
    """[[1,2.3,...],[...]] -> liste de listes de flottants."""
    out = []
    for m in re.finditer(r"\[([^\[\]]+)\]", s):
        champs = []
        for c in m.group(1).split(","):
            c = c.strip().strip('"')
            try: champs.append(float(c))
            except ValueError: champs.append(c)
        out.append(champs)
    return out

def main(rpt, outdir, graine_attendue=None):
    os.makedirs(outdir, exist_ok=True)
    L, lignes_apres_fini = lire(rpt)
    entete, phases, etats, perc, evts, canari = {}, [], [], [], [], {}
    ticks = set()
    tronquees = 0
    for l in L:
        p = l.split("|")
        if len(p) < 2: continue
        k = p[1]
        if k == "OK":
            entete.setdefault("ok", []).append(p[2:])
        elif k == "FINI":
            entete["issue"], entete["cause"] = p[2], p[3]
            for i in range(4, len(p) - 1, 2):
                entete[p[i]] = p[i + 1]
        elif k == "VOID":
            entete["issue"] = "VOID"; entete["void"] = p[2:]
        elif k == "PH":
            phases.append(dict(zip(
                ["n", "nom", "bord", "t", "issue_ou_vivants"], p[2:7])))
        elif k == "CANARI":
            canari[p[2]] = p[3:]
        elif k == "S":
            tick, morceau, t, n, ph = int(p[2]), int(p[3]), float(p[4]), int(p[5]), int(p[6])
            ticks.add(tick)
            if len(l) >= 890: tronquees += 1
            for u in parse_liste(p[7]):
                if len(u) >= 11:
                    etats.append([tick, t, ph] + u[:11])
        elif k in ("VC", "VH", "VG"):
            perc.append([k, float(p[2]), int(p[3]), p[4], p[5] if len(p) > 5 else ""])
        elif k == "E":
            if p[2] == "opord":
                entete["opord"] = p[3:]
            evts.append(p[2:])

    def ecrire(nom, entetes, lignes):
        with open(os.path.join(outdir, nom), "w", newline="") as f:
            w = csv.writer(f); w.writerow(entetes); w.writerows(lignes)
        return len(lignes)

    n_etat = ecrire("etat.csv",
        ["tick","t","phase","id","x","y","z","cap","vivant","camp","posture","comportement","vitesse","tir"], etats)
    n_perc = ecrire("perception.csv", ["canal","t","phase","etiquette","donnees"], perc)
    n_evt  = ecrire("evenements.csv", ["type","t","a","b","c","d","e","f"],
                    [e + [""] * (8 - len(e)) for e in (x[:8] for x in evts)])
    n_ph   = ecrire("phases.csv", ["n","nom","bord","t","suite"], [list(d.values()) for d in phases])

    # ---------------- LES PORTES ----------------
    portes = {}
    # CANARI|pose|<t>|id|<n>|pos|[...]  ->  p[3:] = [t, "id", n, "pos", ...]
    # Premier jet : je lisais l'index 1, donc la chaine "id". La porte du canari
    # etait donc rouge sur un canari parfaitement enregistre. Une porte fausse
    # coute plus cher qu'une porte absente : elle fait chercher au mauvais endroit.
    id_can = canari["pose"][2] if ("pose" in canari and len(canari["pose"]) > 2) else None
    morts_can = [e for e in evts if e and e[0] == "mort" and len(e) > 5 and e[5] == "CANARI"]
    tirs_can  = [e for e in evts if e and e[0] == "tir"  and id_can and len(e) > 2 and e[2] == id_can]
    portes["canari_pose"] = id_can is not None
    portes["canari_mort_journalisee"] = len(morts_can) > 0
    portes["canari_mort_dans_etat"] = False
    if id_can:
        v = [e[8] for e in etats if str(int(e[3])) == str(id_can)]
        portes["canari_mort_dans_etat"] = (1.0 in v) and (0.0 in v)
    # Le canari annonce TROIS coups. Trois, pas "au moins un" : un canal qui
    # rend 6 quand on en tire 3 est aussi casse qu'un canal muet, il ment juste
    # dans l'autre sens - et c'est arrive le 03/09 (deux voies de tir cumulees).
    portes["canari_tir_journalise"] = len(tirs_can) == 3
    portes["aucun_identifiant_nul"] = not any(e[3] < 0 for e in etats)
    portes["pas_continus"] = (len(ticks) == (max(ticks) - min(ticks) + 1)) if ticks else False
    portes["aucune_ligne_tronquee"] = tronquees == 0
    socle = {}
    for o in entete.get("ok", []):
        if o and o[0] == "socle":
            # o = ["socle", version, "graine", g, "echelle", e, ...] : les cles
            # commencent a l'indice 2, pas 1.
            for i in range(2, len(o) - 1, 2):
                socle[o[i]] = o[i + 1]
    portes["lambs_actif"] = socle.get("lambs") == "1"
    portes["episode_termine"] = "issue" in entete
    # Correction 2 : rien ne doit avoir ete ecrit apres le verdict.
    portes["rien_apres_fini"] = lignes_apres_fini == 0
    # L'echelle raccourcit les plafonds mais PAS le monde : une nuit a 25 % est
    # une autre mission, et la melanger au corpus le rend inexploitable.
    portes["echelle_pleine"] = entete.get("echelle") == "1"
    if graine_attendue is not None:
        portes["graine_conforme"] = str(entete.get("graine")) == str(graine_attendue)
    # Correction 10 : les trois canaux de perception ont leur propre controle
    # positif - un temoin bleu a 40 m du canari, en vue franche.
    id_tem = canari["temoin"][2] if ("temoin" in canari and len(canari["temoin"]) > 2) else None
    vg_ok = vh_ok = vc_ok = False
    if id_tem and id_can:
        for c, t, ph, etiq, don in perc:
            if c == "VG" and ("[%s," % id_tem) in don and (",%s," % id_can) in don:
                vg_ok = True
            if c == "VH" and etiq == "ouest" and ("[%s,%s," % (id_tem, id_can)) in don:
                vh_ok = True
            if c == "VC" and etiq == "est_sur_ouest":
                for e in parse_liste(don):
                    if len(e) >= 2 and str(int(e[0])) == str(id_tem) and e[1] >= 1:
                        vc_ok = True
    portes["temoin_vu_par_VG"] = vg_ok
    portes["temoin_vu_par_VH"] = vh_ok
    portes["temoin_vu_par_VC"] = vc_ok

    verdict = "ACCEPTE" if all(portes.values()) else "REFUSE"
    resume = {"rpt": os.path.basename(rpt), "verdict": verdict, "portes": portes,
              "entete": {k: v for k, v in entete.items() if k != "ok"},
              "opord": entete.get("opord"),
              "mesures": {"coups_canari": len(tirs_can),
                          "lignes_apres_fini": lignes_apres_fini,
                          "id_temoin": id_tem,
                          "id_canari": id_can,
                          "lignes_tir_total": len([e for e in evts if e and e[0] == "tir"])},
              "volumes": {"etat": n_etat, "perception": n_perc, "evenements": n_evt,
                          "phases": n_ph, "pas": len(ticks), "lignes_chacal": len(L)}}
    with open(os.path.join(outdir, "episode.json"), "w") as f:
        json.dump(resume, f, indent=2, ensure_ascii=False)
    print(json.dumps(resume, indent=2, ensure_ascii=False))
    return 0 if verdict == "ACCEPTE" else 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
