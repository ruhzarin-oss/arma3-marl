#!/usr/bin/env python3
"""catalogue - la base de connaissance CHACAL : UN EPISODE = UNE LIGNE.

Usage : catalogue.py            (regenere depot/catalogue/episodes.csv, episodes.jsonl, LISEZMOI.md)

Chaque episode est lu depuis SON journal (serveur.rpt), jamais depuis le nom de son dossier.
Le 11/09, deux paires de jobs ont partage un dossier de run : le dossier disait V7, l episode
avait joue V8. La ligne CHACAL|FINI porte les leviers joues ; c est elle qui fait foi.

Sources lues :
  runs/*/*/serveur.rpt                 les episodes a leur place
  archive/sauvetage_g8/runs/*/*.rpt    les journaux sauves avant ecrasement (11/09)
Un meme episode vu deux fois (meme graine, memes ticks, meme duree, meme issue) n a qu une ligne.

Aucune dependance. Ecriture atomique : deux appels simultanes ne produisent jamais un fichier a moitie ecrit.
"""
import csv, glob, json, os, re, sys, time

H = "/mnt/data/hmt"
OUT = os.environ.get("CATALOGUE_OUT", f"{H}/depot/catalogue")
LEVIERS = ["depart", "arret", "tenir", "appui_feu", "feu_avant", "mg_assaut", "delai_porteur", "appui_fixe",
           "accessible", "effectif", "oracle"]
ROLES_FS = {"CHEF", "ADJOINT", "DEMO_1", "DEMO_2", "MEDECIN", "TIREUR_1", "TIREUR_2", "AT", "FUSILIER_1", "FUSILIER_2"}
OBJ_COURT = {"Land_Communication_F": "antenne", "Land_TTowerBig_1_F": "tour", "Land_Cargo_HQ_V1_F": "QG"}

COLONNES = [
    "episode", "source", "copies", "banc", "run", "ep", "date", "contamine", "version_job", "version_jouee", "coherent",
    "campagne", "graine", "palier", "jour", "bras", "hors_corpus",
    *LEVIERS,
    "issue", "cause", "charges", "sur", "detruits", "exfiltres", "vivants", "morts_fs", "roles_morts", "pertes_est",
    "renseignement", "alarme", "compromis", "t_compromis", "cause_compromis", "phase_au_compromis",
    "latence_surprise", "abandon", "duree_s",
    "ph1", "ph2", "ph3", "ph4", "ph5", "ph6",
    "charges_detail", "porteur_temps", "tirs_appui_avant", "tirs_appui_total", "appui_position_m", "mg_munitions",
    "porte_lecture", "empreinte", "note_job",
]


def lignes_chacal(path):
    """Les lignes CHACAL jusqu a la premiere FINI incluse (comme lire.py)."""
    out = []
    with open(path, "r", errors="ignore") as f:
        for l in f:
            i = l.find("CHACAL|")
            if i < 0:
                continue
            t = l[i:].rstrip().rstrip('"')
            out.append(t)
            if t.startswith("CHACAL|FINI|"):
                break
    return out


def paires(champs):
    return dict(zip(champs[0::2], champs[1::2]))


def lire_episode(path):
    L = lignes_chacal(path)
    fini = [l for l in L if l.startswith("CHACAL|FINI|")]
    if not fini:
        return None
    p = fini[-1].split("|")
    e = {"issue": p[2], "cause": p[3]}
    d = paires(p[4:])
    for k in ("graine", "bras", "palier", "charges", "sur", "exfiltres", "vivants", "pertes_est", "renseignement",
              "alarme", "compromis", "latence_surprise", "abandon", "duree", *LEVIERS):
        e[k] = d.get(k, "")
    e["detruits"] = d.get("detruits_scriptes", "")
    e["duree_s"] = e.pop("duree")
    e["_ticks"] = d.get("ticks", "")
    roles, phases, charges, porteur = {}, {}, [], []
    e.update({"jour": "", "hors_corpus": "0", "t_compromis": "", "cause_compromis": "", "phase_au_compromis": "",
              "tirs_appui_avant": "", "tirs_appui_total": "", "appui_position_m": "", "mg_munitions": ""})
    morts = []
    phase_courante = ""
    for l in L:
        q = l.split("|")
        k = q[1] if len(q) > 1 else ""
        if k == "OK" and len(q) > 2 and q[2] == "socle":
            s = paires(q[4:]); e["jour"] = s.get("jour", "")
            for lv in ("depart", "tenir", "arret"):
                if not e.get(lv): e[lv] = s.get(lv, "")
        elif k == "OK" and len(q) > 4 and q[2] == "appui_feu" and q[3] == "position":
            s = paires(q[5:]); e["appui_position_m"] = s.get("dist_ouverture", "")
        elif k == "AVERT" and len(q) > 2 and q[2] == "hors_corpus":
            e["hors_corpus"] = "1"
        elif k == "PH" and len(q) > 6:
            if q[4] == "debut":
                phase_courante = q[2]
            elif q[4] == "fin":
                phases[q[2]] = f"{q[6]}@{q[5]}"
        elif k == "E" and len(q) > 3:
            ev = q[2]
            if ev == "spawn" and len(q) > 7:
                roles[q[4]] = q[7]
            elif ev == "compromis" and not e["t_compromis"]:
                e["t_compromis"] = q[3]; e["cause_compromis"] = q[5] if len(q) > 5 else ""
                e["phase_au_compromis"] = phase_courante
            elif ev == "charge_posee" and len(q) > 4:
                charges.append(f"{OBJ_COURT.get(q[4], q[4])}:POSEE")
            elif ev == "charge_manquee" and len(q) > 4:
                charges.append(f"{OBJ_COURT.get(q[4], q[4])}:{q[6] if len(q) > 6 else '?'}")
            elif ev == "porteur" and len(q) > 7:
                porteur.append(f"{OBJ_COURT.get(q[4], q[4])}:{q[7]}s")
            elif ev == "premier_pas_assaut" and len(q) > 5:
                e["tirs_appui_avant"] = q[5]
            elif ev == "feu_appui_total" and len(q) > 5:
                e["tirs_appui_total"] = q[5]
            elif ev == "mg_assaut":
                s = paires(q[4:]); e["mg_munitions"] = s.get("munitions_chargees", "")
            elif ev == "mort" and len(q) > 7:
                r = q[7] or roles.get(q[4], "")
                if r in ROLES_FS:
                    morts.append(r)
    for n in "123456":
        e[f"ph{n}"] = phases.get(n, "")
    e["charges_detail"] = " ".join(charges)
    e["porteur_temps"] = " ".join(porteur)
    e["morts_fs"] = str(len(morts))
    e["roles_morts"] = " ".join(morts)
    return e


def charger_jobs():
    """Toutes les definitions de jobs connues, pour retrouver la version reellement jouee."""
    defs = []
    for f in glob.glob(f"{H}/queue/*.json") + glob.glob(f"{H}/queue/*/*.json"):
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if j.get("version"):
            defs.append(j)
    return defs


def version_de(job):
    if not job:
        return ""
    if job.get("version"):
        return job["version"]
    n = job.get("note", "")
    return n.split(" - ")[0][:12] if " - " in n[:16] else ""


def chercher_version(e, defs):
    """La version dont les leviers correspondent a ceux que l episode a JOUES."""
    cand = set()
    for j in defs:
        if e["graine"] and str(e["graine"]) not in [str(g) for g in j.get("graines", [])]:
            continue
        ok = True
        for lv in ("depart", "arret", "tenir", "appui_feu", "feu_avant", "mg_assaut", "delai_porteur", "appui_fixe"):
            if e.get(lv, "") == "":
                continue
            attendu = {"delai_porteur": 45}.get(lv, 0)
            if str(j.get(lv, attendu)) != str(e[lv]):
                ok = False; break
        if ok and e.get("jour", "") != "" and str(j.get("jour", 0)) != str(e["jour"]):
            ok = False
        if ok:
            cand.add(j["version"])
    return cand.pop() if len(cand) == 1 else ("?" if not cand else "/".join(sorted(cand)))


def main():
    defs = charger_jobs()
    sources = sorted(glob.glob(f"{H}/runs/*/*/serveur.rpt")) + sorted(glob.glob(f"{H}/archive/sauvetage_g8/runs/*/*.rpt"))
    vus, ignores = {}, 0
    for path in sources:
        e = lire_episode(path)
        if e is None:
            ignores += 1; continue
        sauve = "/archive/sauvetage_g8/" in path
        run = path.split("/")[-3] if not sauve else path.split("/")[-2]
        ep = path.split("/")[-2] if not sauve else os.path.basename(path)[:-4]
        rdir = f"{H}/runs/{run}"
        job = {}
        try:
            job = json.load(open(f"{rdir}/job.json"))
        except Exception:
            pass
        contamine = os.path.exists(f"{rdir}/CONTAMINE.txt")
        e.update({"source": path, "run": run, "ep": ep, "date": run[:10], "contamine": "1" if contamine else "0",
                  "campagne": job.get("campagne", ""), "note_job": job.get("note", "")[:120].replace("\n", " ")})
        e["version_job"] = "" if contamine else version_de(job)
        # la version se deduit des leviers SEULEMENT quand le dossier est contamine ; sinon deux
        # bancs aux memes leviers (V2 et AL1) se confondraient.
        e["version_jouee"] = chercher_version(e, [j for j in defs if j.get("campagne") == "G8-FABLE-11-09"]) if contamine else e["version_job"]
        e["banc"] = job.get("banc", "")
        if contamine and not e["campagne"]:
            e["campagne"] = "G8-FABLE-11-09"
        # ! Fable 11/09 : coherent MESURE, il ne declare pas. 1 si chaque levier ecrit dans la ligne FINI
        # vaut celui du job (defauts d origine sinon), 0 sinon, vide sans job.
        if job:
            defauts = {"delai_porteur": 45, "effectif": 10, "arret": 6, "depart": 1}
            ok = True
            for lv in LEVIERS:
                if e.get(lv, "") == "": continue
                att = job.get(lv, defauts.get(lv, 0))
                try: same = float(e[lv]) == float(att)
                except (TypeError, ValueError): same = str(e[lv]) == str(att)
                if not same: ok = False; break
            e["coherent"] = "1" if ok else "0"
        else:
            e["coherent"] = ""
        porte = ""
        if not contamine and not sauve:
            try:
                porte = json.load(open(os.path.join(os.path.dirname(path), "resultat.json"))).get("verdict", "")
            except Exception:
                pass
        e["porte_lecture"] = porte
        try:
            e["empreinte"] = open(f"{rdir}/empreinte_mission.txt").read().strip()
        except Exception:
            e["empreinte"] = ""
        sig = (e["graine"], e["_ticks"], e["duree_s"], e["issue"], e["cause"])
        if sig in vus:
            vus[sig]["copies"] = str(int(vus[sig]["copies"]) + 1)
            # on garde la copie a sa place d origine quand elle est saine
            if vus[sig]["contamine"] == "1" and not contamine and not sauve:
                e["copies"] = vus[sig]["copies"]; vus[sig] = e
            continue
        e["copies"] = "1"
        vus[sig] = e
    lignes = sorted(vus.values(), key=lambda x: (x["run"], x["ep"]))
    for x in lignes:
        x["episode"] = f"{x['run']}/{x['ep']}"
    os.makedirs(OUT, exist_ok=True)
    tmp = f"{OUT}/.episodes.csv.{os.getpid()}"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES, extrasaction="ignore")
        w.writeheader(); w.writerows(lignes)
    os.replace(tmp, f"{OUT}/episodes.csv")
    tmp = f"{OUT}/.episodes.jsonl.{os.getpid()}"
    with open(tmp, "w") as f:
        for x in lignes:
            f.write(json.dumps({k: x.get(k, "") for k in COLONNES}, ensure_ascii=False) + "\n")
    os.replace(tmp, f"{OUT}/episodes.jsonl")
    par_v = {}
    for x in lignes:
        if x["campagne"]:
            k = (x["campagne"], x["version_jouee"])
            n, s = par_v.get(k, (0, 0))
            par_v[k] = (n + 1, s + (1 if x["charges"] and x["charges"] == x["sur"] else 0))
    resume = "\n".join(f"| {c} | {v} | {n} | {s} |" for (c, v), (n, s) in sorted(par_v.items()))
    lisez = f"""# Catalogue des episodes CHACAL

Genere par `outils/catalogue.py` le {time.strftime('%Y-%m-%d %H:%M')}. **Ne pas editer a la main** : il est
regenere apres chaque run (file3.sh) et chaque nuit (sauver.sh).

- **{len(lignes)} episodes**, lus depuis {len(sources)} journaux ({ignores} sans ligne FINI ignores).
- Un episode = une ligne ; `episodes.csv` pour un tableur, `episodes.jsonl` pour un programme.
- Le journal complet de chaque episode est dans la colonne `source` ; ses tables (etat de chaque homme
  toutes les ~2 s, perception, evenements, phases) sont a cote, dans `extrait/`.

## Ce qui fait foi
`version_jouee` est deduite des leviers ecrits dans la ligne `CHACAL|FINI` de l episode, pas du nom
du dossier. `coherent = 0` signale un episode dont le job et le jeu different ; `contamine = 1`, un
dossier partage (incident du 11/09). `copies` compte les exemplaires identiques retrouves.

## Colonnes utiles
- `issue`, `cause` : le verdict de la mission ; `charges`/`sur` : charges posees sur objectifs.
- `ph1`..`ph6` : issue et instant de fin de chaque phase (`ATTEINT@4778.87`).
- `t_compromis`, `phase_au_compromis`, `cause_compromis` : quand, dans quelle phase, et pourquoi le detachement est repere.
- `charges_detail` : objectif par objectif, POSEE ou la cause du manque ; `porteur_temps` : secondes du porteur.
- `morts_fs`, `roles_morts` : nos pertes et leurs roles ; `pertes_est` : defenseurs tues.
- `tirs_appui_avant` / `tirs_appui_total` : coups de l appui avant le premier pas de l assaut / sur toute la phase.
- `porte_lecture` : ACCEPTE si les instruments de l episode se sont prouves (canari, pas continus...).

## Campagnes (episodes, dont charges completes)
| campagne | version jouee | episodes | charges completes |
|---|---|---|---|
{resume}
"""
    open(f"{OUT}/LISEZMOI.md", "w").write(lisez)
    print(f"catalogue : {len(lignes)} episodes, {ignores} journaux sans FINI ignores -> {OUT}/episodes.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
