#!/usr/bin/env python3
# CONSTRUCTEUR — tourne dans WSL, la ou vit le registre. Ecrit un colis JSON pour le publieur.
# ! Le conteneur Plane ne voit PAS /mnt/data : premiere version publiait des pages vides (08/09).
# Trois pages : l'ETAT (remplacee), le DETAIL des verdicts (remplacee), le JOURNAL (ajout seulement).
import json, glob, os, time, html, subprocess

H = "/mnt/data/hmt"; V = f"{H}/depot/verdicts"
COLIS = f"{H}/etat/journal_colis.json"
VUS = f"{H}/etat/journal_vus.txt"



def _min(v):
    """Minutes lisibles a partir d'une duree qui peut etre absente ou nulle.
    ! Un FIN.json RECONSTRUIT ou INTERROMPU porte duree_s = null : le calcul direct
    levait un TypeError, wiki.sh sortait en erreur, run.sh rendait le code 1, et le
    wiki n'etait plus regenere depuis le 08/09 22:49 sans que rien ne le dise."""
    try:
        return "%d min" % (int(v) // 60)
    except (TypeError, ValueError):
        return "duree inconnue"

def e(s):
    return html.escape(str(s))


def lire_verdict(p):
    d = {"_fichier": os.path.basename(p)[:-3], "_texte": ""}
    lignes = open(p, encoding="utf-8").read().split("\n")
    i = 0
    while i < len(lignes) and lignes[i].strip():
        if ":" in lignes[i]:
            k, v = lignes[i].split(":", 1); d[k.strip()] = v.strip()
        i += 1
    d["_texte"] = "\n".join(lignes[i + 1:]).strip()
    return d


def sh(c):
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as ex:
        return f"? {ex}"


verdicts = [lire_verdict(p) for p in sorted(glob.glob(f"{V}/*.md"))
            if not os.path.basename(p).startswith("_")]
runs = []
for r in sorted(glob.glob(f"{H}/runs/*/"), reverse=True):
    j = json.load(open(r + "job.json")) if os.path.exists(r + "job.json") else {}
    f = json.load(open(r + "FIN.json")) if os.path.exists(r + "FIN.json") else None
    age = time.time() - os.path.getmtime(r)
    plaf = j.get("plafond_s", 16000) * max(1, len(j.get("graines", [1]))) + 600
    runs.append({"nom": os.path.basename(r[:-1]), "job": j, "fin": f,
                 "etat": f["verdict"] if f else ("EN COURS" if age < plaf else "SANS FIN.json")})

vivants = [v for v in verdicts if not v.get("remplace_par") and v.get("verdict") != "OUVERT"]
ouverts = [v for v in verdicts if v.get("verdict") == "OUVERT" and not v.get("remplace_par")]
remplaces = [v for v in verdicts if v.get("remplace_par")]
mois = time.strftime("%Y-%m")
ab = sum(1 for r in runs if r["nom"].startswith(mois) and r["etat"] == "COMPLET")
tot = sum(1 for r in runs if r["nom"].startswith(mois))
q = sorted(os.path.basename(p) for p in glob.glob(f"{H}/queue/*.json"))
enc = sorted(os.path.basename(p) for p in glob.glob(f"{H}/queue/en_cours/*.json"))
boot = json.load(open(f"{H}/etat/boot.json")) if os.path.exists(f"{H}/etat/boot.json") else {}
question = open(f"{V}/_question.md", encoding="utf-8").read().strip() if os.path.exists(f"{V}/_question.md") else ""
gpu = sh("/mnt/c/Windows/System32/nvidia-smi.exe --query-gpu=memory.used,utilization.gpu --format=csv,noheader")
disque = sh("df -h /mnt/data | tail -n 1 | awk '{print $4\" libres sur \"$2}'")
charge = sh("/mnt/c/Windows/System32/tasklist.exe 2>/dev/null | grep -Eio 'UnrealEditor[A-Za-z-]*|vmware-vmx|arma3server_x64.exe|arma3_x64.exe' | sort | uniq -c | tr '\\n' ' '")
maj = time.strftime("%d/%m/%Y a %H:%M")

# ---------- page 1 : l'etat
h = [f"<p><em>Page generee le {maj} depuis le registre du depot. Ne pas l'editer a la main : "
     "la prochaine generation ecrase. Source de verite : <code>depot/verdicts/</code> et <code>hmt/runs/</code>.</em></p>",
     f"<blockquote><p>{e(question)}</p></blockquote>",
     "<h2>La machine</h2><ul>",
     f"<li>Dernier demarrage : {e(boot.get('date','?'))} — ok={e(boot.get('ok','?'))} {e(boot.get('message',''))}</li>",
     f"<li>Carte graphique : {e(gpu)}</li><li>Disque de travail : {e(disque)}</li>",
     f"<li>Charge en cours : {e(charge) or 'machine libre'}</li></ul>",
     "<h2>La file</h2><ul>",
     f"<li>En cours : {e(', '.join(enc)) or 'rien'}</li>",
     f"<li>En attente : {e(', '.join(q)) or 'rien'}</li>",
     f"<li>Debit du mois {mois} : <strong>{ab} runs aboutis sur {tot}</strong></li></ul>",
     f"<h2>Les portes ouvertes ({len(ouverts)})</h2><ul>"]
h.append("".join(f"<li><strong>{e(v.get('porte','?'))}</strong> — <code>{e(v['_fichier'])}.md</code></li>"
                 for v in ouverts) or "<li>aucune</li>")
h.append("</ul><h2>Les derniers runs</h2><table><tbody>"
         "<tr><th>run</th><th>banc</th><th>etat</th><th>verdicts du banc</th><th>duree</th></tr>")
for r in runs[:12]:
    f = r["fin"] or {}
    bv = " · ".join(f"{g} : {x.get('verdict','?')}" for g, x in f.get("resultats", {}).items())
    d = _min(f.get("duree_s")) if f.get("duree_s") is not None else ""
    h.append(f"<tr><td><code>{e(r['nom'])}</code></td><td>{e(r['job'].get('banc','?'))}</td>"
             f"<td><strong>{e(r['etat'])}</strong></td><td>{e(bv)}</td><td>{e(d)}</td></tr>")
h.append("</tbody></table>")
h.append(f"<h2>Les verdicts vivants ({len(vivants)})</h2><table><tbody>"
         "<tr><th>porte</th><th>date</th><th>chiffre</th><th>verdict</th></tr>")
for v in sorted(vivants, key=lambda x: x.get("date", ""), reverse=True):
    h.append(f"<tr><td>{e(v.get('porte','?'))}</td><td>{e(v.get('date','?'))}</td>"
             f"<td>{e(v.get('chiffre','?'))}</td><td><strong>{e(v.get('verdict','?'))}</strong></td></tr>")
h.append("</tbody></table>")
h.append(f"<h2>Les verdicts remplaces ({len(remplaces)})</h2><ul>" +
         ("".join(f"<li>{e(v.get('porte','?'))} → remplace par <code>{e(v['remplace_par'])}</code></li>"
                  for v in remplaces) or "<li>aucun</li>") + "</ul>")
etat_html = "".join(h)

# ---------- page 2 : le detail des verdicts
h = [f"<p><em>Page generee le {maj} : le texte entier de chaque verdict du registre, "
     f"{len(verdicts)} fichiers. Source unique : <code>depot/verdicts/</code>. Ne pas editer ici.</em></p>"]
ordre = {"PASSE": 0, "OUVERT": 1, "ECHEC": 2, "REFUSE": 3, "VIDE": 4}
for v in sorted(verdicts, key=lambda x: (ordre.get(x.get("verdict", ""), 9), x.get("date", ""))):
    rem = f" — <strong>remplace par {e(v['remplace_par'])}</strong>" if v.get("remplace_par") else ""
    h.append(f"<h2>{e(v.get('porte', v['_fichier']))}</h2>")
    h.append(f"<p><code>{e(v['_fichier'])}.md</code> · {e(v.get('date','?'))} · graines {e(v.get('graines','?'))} · "
             f"<strong>{e(v.get('verdict','?'))}</strong>{rem}</p>")
    h.append(f"<p><strong>Chiffre :</strong> {e(v.get('chiffre',''))}</p>")
    if v.get("depend_de"):
        h.append(f"<p><strong>Depend de :</strong> {e(v['depend_de'])}</p>")
    for para in v["_texte"].split("\n"):
        if para.strip():
            h.append(f"<p>{e(para.strip())}</p>")
verdicts_html = "".join(h)

# ---------- page 3 : le journal, ajout seulement
vus = set(open(VUS).read().split()) if os.path.exists(VUS) else set()
entrees = []
for r in sorted(runs, key=lambda x: x["nom"]):
    if r["nom"] in vus or not r["fin"]:
        continue
    f = r["fin"]; j = r["job"]
    L = [f"<h2>{e(r['nom'])} — {e(f.get('verdict','?'))}</h2>",
         f"<p>Banc <strong>{e(j.get('banc','?'))}</strong>, graines {e(j.get('graines',''))}, "
         f"palier {e(j.get('palier',''))}, depart {e(j.get('depart',''))}. Duree {_min(f.get('duree_s'))}. "
         f"Charge au lancement : {e(f.get('charge_au_lancement','') or 'machine libre')}.</p>"]
    if j.get("note"):
        L.append(f"<p><em>{e(j['note'])}</em></p>")
    for g, x in f.get("resultats", {}).items():
        ent = x.get("entete", {}) if isinstance(x, dict) else {}
        rouges = [k for k, val in (x.get("portes", {}) or {}).items() if val is False]
        L.append(f"<p><strong>{e(g)}</strong> : {e(x.get('verdict','?'))}"
                 + (f" — issue {e(ent.get('issue',''))} / {e(ent.get('cause',''))}, "
                    f"{e(ent.get('vivants','?'))} vivants, {e(ent.get('charges','?'))} charges sur {e(ent.get('sur','?'))}, "
                    f"{e(ent.get('ticks','?'))} pas" if ent else "")
                 + (f". <strong>Portes rouges : {e(', '.join(rouges))}</strong>" if rouges
                    else ". Toutes les portes vertes.") + "</p>")
    entrees.append({"nom": r["nom"], "html": "".join(L)})

os.makedirs(os.path.dirname(COLIS), exist_ok=True)
json.dump({"etat": etat_html, "verdicts": verdicts_html, "entrees": entrees},
          open(COLIS, "w", encoding="utf-8"), ensure_ascii=False)
print(f"colis ecrit : etat {len(etat_html)} car., verdicts {len(verdicts_html)} car. "
      f"({len(verdicts)} fichiers), journal {len(entrees)} entree(s) neuve(s)")
