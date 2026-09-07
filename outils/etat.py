#!/usr/bin/env python3
# Ecrit ETAT.md (dans le depot) et etat/etat.html a partir des verdicts et des runs. Aucune dependance.
import json, glob, os, time, subprocess, html
H = "/mnt/data/hmt"; V = f"{H}/depot/verdicts"; now = time.strftime("%Y-%m-%d %H:%M")

def entete(p):
    d = {"_fichier": os.path.basename(p)[:-3]}
    for l in open(p, encoding="utf-8"):
        l = l.rstrip("\n")
        if not l.strip(): break
        if ":" in l:
            k, v = l.split(":", 1); d[k.strip()] = v.strip()
    return d

verdicts = [entete(p) for p in sorted(glob.glob(f"{V}/*.md")) if not os.path.basename(p).startswith("_")]
vivants = [v for v in verdicts if not v.get("remplace_par") and v.get("verdict") != "OUVERT"]
ouverts = [v for v in verdicts if v.get("verdict") == "OUVERT" and not v.get("remplace_par")]
remplaces = [v for v in verdicts if v.get("remplace_par")]

runs = []
for r in sorted(glob.glob(f"{H}/runs/*/"), reverse=True):
    j = json.load(open(r + "job.json")) if os.path.exists(r + "job.json") else {}
    f = json.load(open(r + "FIN.json")) if os.path.exists(r + "FIN.json") else None
    age_s = time.time() - os.path.getmtime(r)
    plafond = j.get("plafond_s", 16000) * max(1, len(j.get("graines", [1]))) + 600
    etat = f["verdict"] if f else ("EN COURS" if age_s < plafond else "SANS FIN.json")
    bancv = " ".join(f"{g}:{x.get('verdict','?')}" for g, x in (f or {}).get("resultats", {}).items())
    runs.append({"nom": os.path.basename(r[:-1]), "banc": j.get("banc", "?"), "etat": etat, "duree": f["duree_s"] if f else None, "bancv": bancv})
mois = time.strftime("%Y-%m")
aboutis = sum(1 for r in runs if r["nom"].startswith(mois) and r["etat"] == "COMPLET")
total = sum(1 for r in runs if r["nom"].startswith(mois))
queue = sorted(os.path.basename(p) for p in glob.glob(f"{H}/queue/*.json"))
encours = sorted(os.path.basename(p) for p in glob.glob(f"{H}/queue/en_cours/*.json"))
boot = json.load(open(f"{H}/etat/boot.json")) if os.path.exists(f"{H}/etat/boot.json") else {}

def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e: return f"? {e}"
gpu = sh("/mnt/c/Windows/System32/nvidia-smi.exe --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader")
disque = sh("df -h /mnt/data | tail -n 1 | awk '{print $4\" libres sur \"$2}'")
residus = sh("/mnt/c/Windows/System32/tasklist.exe 2>/dev/null | grep -Ei 'UnrealEditor|vmware-vmx|arma3_x64.exe' | awk '{print $1}' | sort | uniq -c | tr '\\n' ' '")
serveurs = sh("/mnt/c/Windows/System32/tasklist.exe 2>/dev/null | grep -c arma3server_x64")
question = open(f"{V}/_question.md", encoding="utf-8").read().strip() if os.path.exists(f"{V}/_question.md") else "(ecrire verdicts/_question.md)"

L = [f"# ETAT — {now}", "", question, "", "## Machine", "",
     f"- dernier boot : {boot.get('date','?')} ok={boot.get('ok','?')} {boot.get('message','')}",
     f"- GPU : {gpu}", f"- /mnt/data : {disque}", f"- serveurs Arma : {serveurs} · residus : {residus or 'aucun'}", "",
     "## File", "", f"- en cours : {', '.join(encours) or 'rien'}", f"- en attente : {', '.join(queue) or 'rien'}", "",
     f"## Debit du mois {mois}", "", f"- runs aboutis : {aboutis} / {total}", "", "## Portes ouvertes", ""]
L += [f"- **{v.get('porte','?')}** — {v['_fichier']}.md" for v in ouverts] or ["- aucune"]
L += ["", "## Verdicts vivants", "", "| porte | date | graines | chiffre | verdict | depend de | fichier |", "|---|---|---|---|---|---|---|"]
L += [f"| {v.get('porte','?')} | {v.get('date','?')} | {v.get('graines','?')} | {v.get('chiffre','?')} | {v.get('verdict','?')} | {v.get('depend_de','')} | {v['_fichier']}.md |" for v in vivants]
L += ["", "## Remplaces", ""] + ([f"- {v.get('porte','?')} ({v['_fichier']}.md) → remplace par {v['remplace_par']}" for v in remplaces] or ["- aucun"])
L += ["", "## Derniers runs", "", "| run | banc | etat du run | verdicts du banc | duree s |", "|---|---|---|---|---|"] + ([f"| {r['nom']} | {r['banc']} | {r['etat']} | {r['bancv']} | {r['duree'] if r['duree'] is not None else ''} |" for r in runs[:15]] or ["| aucun | | | | |"])
open(f"{H}/depot/ETAT.md", "w", encoding="utf-8").write("\n".join(L) + "\n")

def esc(s): return html.escape(str(s))
couleur = {"COMPLET": "#2C7A4B", "ECHEC": "#B3261E", "SANS FIN.json": "#B3261E", "EN COURS": "#9A6A12"}
rows = "".join(f"<tr><td>{esc(r['nom'])}</td><td>{esc(r['banc'])}</td><td style='color:{couleur.get(r['etat'],'#333')};font-weight:600'>{esc(r['etat'])}</td><td>{esc(r['bancv'])}</td><td>{r['duree'] if r['duree'] is not None else ''}</td></tr>" for r in runs[:30])
vrows = "".join(f"<tr><td>{esc(v.get('porte','?'))}</td><td>{esc(v.get('date','?'))}</td><td>{esc(v.get('graines','?'))}</td><td>{esc(v.get('chiffre','?'))}</td><td>{esc(v.get('verdict','?'))}</td><td>{esc(v.get('depend_de',''))}</td></tr>" for v in vivants)
orows = "".join(f"<li><b>{esc(v.get('porte','?'))}</b> — {esc(v['_fichier'])}.md</li>" for v in ouverts)
rrows = "".join(f"<li>{esc(v.get('porte','?'))} → {esc(v['remplace_par'])}</li>" for v in remplaces)
page = f"""<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=300><title>ETAT HARMATTAN</title>
<style>body{{font:16px/1.5 system-ui;margin:2rem auto;max-width:70rem;padding:0 1rem;color:#16202A;background:#EDF0F3}}table{{border-collapse:collapse;width:100%;background:#fff}}td,th{{padding:.35rem .6rem;border-bottom:1px solid #CBD3DA;text-align:left;font-variant-numeric:tabular-nums;vertical-align:top}}.k{{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:.8rem}}.k div{{background:#fff;padding:.8rem 1rem;border-left:4px solid #B8471B}}.k b{{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:#7C8A96}}h1{{font-size:1.6rem}}h2{{font-size:1.15rem;margin-top:2rem}}</style>
<h1>ETAT — {now}</h1><p>{esc(question)}</p>
<div class=k><div><b>boot</b>{esc(boot.get('date','?'))} ok={esc(boot.get('ok','?'))} {esc(boot.get('message',''))}</div><div><b>GPU</b>{esc(gpu)}</div><div><b>/mnt/data</b>{esc(disque)}</div>
<div><b>serveurs Arma / residus</b>{esc(serveurs)} / {esc(residus) or 'aucun'}</div><div><b>file</b>en cours : {esc(', '.join(encours) or 'rien')}<br>en attente : {esc(', '.join(queue) or 'rien')}</div><div><b>debit {mois}</b>{aboutis} aboutis / {total}</div></div>
<h2>Derniers runs</h2><table><tr><th>run</th><th>banc</th><th>etat du run</th><th>verdicts du banc</th><th>duree s</th></tr>{rows}</table>
<h2>Portes ouvertes</h2><ul>{orows or '<li>aucune</li>'}</ul>
<h2>Verdicts vivants</h2><table><tr><th>porte</th><th>date</th><th>graines</th><th>chiffre</th><th>verdict</th><th>depend de</th></tr>{vrows}</table>
<h2>Remplaces</h2><ul>{rrows or '<li>aucun</li>'}</ul>"""
os.makedirs(f"{H}/etat", exist_ok=True)
open(f"{H}/etat/etat.html", "w", encoding="utf-8").write(page)
print(f"ETAT ecrit : {len(vivants)} verdicts vivants, {len(ouverts)} ouverts, {len(remplaces)} remplaces, {len(runs)} runs, {aboutis}/{total} aboutis en {mois}")
