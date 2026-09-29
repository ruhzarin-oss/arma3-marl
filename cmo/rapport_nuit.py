#!/usr/bin/env python3
"""rapport_nuit — attend la fin de l'endurance ( cmo/endurance.py ), puis écrit le bilan de la nuit en clair dans
/mnt/data/hmt/etat/cmo_nuit/rapport.md. Ne touche ni à CMO ni au pont : il lit resume.json et le journal.

    .venv312/bin/python cmo/rapport_nuit.py [--attendre]
"""
import json
import os
import subprocess
import sys
import time

DOSSIER = "/mnt/data/hmt/etat/cmo_nuit"


def en_vol():
    """Un PROCESSUS python d'endurance vit encore. ⚠️ pgrep seul trouve aussi le serveur tmux, qui garde la ligne de
    commande de la session qui l'a lancé ( 29/09 : le rapport attendait sans fin )."""
    r = subprocess.run(["pgrep", "-f", "python cmo/endurance.py"], capture_output=True, text=True)
    for pid in r.stdout.split():
        try:
            if open(f"/proc/{pid}/comm").read().strip().startswith("python"):
                return True
        except OSError:
            pass
    return False


def rapport():
    r = json.load(open(os.path.join(DOSSIER, "resume.json")))
    evs = [json.loads(l) for l in open(r["journal"])]
    points = [e for e in evs if e["quoi"] in ("debut", "point", "fin")]
    mem = [(e["t"], e.get("memoire")) for e in points if e.get("memoire")]
    lua = [(e["t"], e["journaux"].get(k)) for e in points for k in e.get("journaux", {}) if k.startswith("LuaHistory")]
    erreurs = [e for e in evs if e["quoi"] == "erreur"]
    disparus = [e for e in evs if e["quoi"] == "disparu_sans_mort"]
    l = [f"# Nuit du pont CMO — {r['debut']} → {r['maintenant']} ({r['heures']} h, {'terminée' if r['final'] else 'EN COURS'})", ""]
    l.append(f"- Canaris réussis : **{r['canaris_ok']}** ; erreurs : **{sum(r['erreurs'].values())}** {r['erreurs'] or ''}")
    l.append(f"- Aller-retour : médiane {r['rtt_ms']['mediane']} ms, p99 {r['rtt_ms']['p99']} ms, max {r['rtt_ms']['max']} ms")
    l.append(f"- Pannes du pont (jeu en pause, CMO fermé…) : {len(r['pannes_s'])} {r['pannes_s'] or ''}")
    l.append(f"- Morts d'avions rendues : {len(r['morts'])} (doubles : **{r['morts_doubles']}**) ; "
             f"disparus sans mort : **{sum(len(e['numeros']) for e in disparus)}**")
    if mem:
        l.append(f"- Mémoire de CMO : {mem[0][1] / 1e9:.2f} Go → {mem[-1][1] / 1e9:.2f} Go "
                 f"({(mem[-1][1] - mem[0][1]) / 1e6:+.0f} Mo en {(mem[-1][0] - mem[0][0]) / 3600:.1f} h)")
    if len(lua) > 1:
        d = (lua[-1][1] - lua[0][1]) / max(1.0, lua[-1][0] - lua[0][0])
        l.append(f"- LuaHistory : {d:.0f} octets/s, soit {d * 86400 / 1e6:.1f} Mo par jour")
    if erreurs:
        l += ["", "## Erreurs (les 10 premières)"] + [f"- t={e['t']} s {e['appel']} {e['type']} : {e['message'][:160]}"
                                                      for e in erreurs[:10]]
    if r["morts"]:
        l += ["", "## Morts (avions à sec ou autres)"] + [f"- avion {m['numero']} à t={m['t']} s" for m in r["morts"][:20]]
    open(os.path.join(DOSSIER, "rapport.md"), "w").write("\n".join(l) + "\n")
    return "\n".join(l)


if __name__ == "__main__":
    if "--attendre" in sys.argv:
        while en_vol():
            time.sleep(60)
    print(rapport())
