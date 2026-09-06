#!/usr/bin/env python3
"""BRIQUE 1 — SENTINELLE DE PONT.

Battement sur le port du pont toutes les 30 s. Trois manques consecutifs -> releve du
serveur par la TACHE PLANIFIEE Windows, jamais autrement : un `setsid` lance depuis ssh
MEURT (mesure du projet), seule `HMT_Arma` survit.

⚠️ JAMAIS DE `pkill`. Un `pkill -f arma` tue TOUTES les instances de la ferme — piege deja
paye. La sentinelle ne tue rien du tout : elle ne fait que RELEVER. Si un processus doit
etre arrete, c est par PID, a la main, par Younes.

Elle n interprete rien : elle ecrit un journal que le harnais lit pour inscrire « morts du
pont » dans le depot du matin.
"""
import socket, subprocess, time, json, os, sys, datetime

PORT = int(os.environ.get("HMT_PORT", 5801))
PERIODE = 30
MANQUES = 3
TACHE = "HMT_Arma"
# ⚠️ `schtasks.exe` n est PAS dans le PATH de WSL : l interop est active (`WSLInterop`
# enabled) mais il faut le chemin complet. Un appel par nom simple echoue en `FileNotFound`,
# ce qui aurait fait passer une sentinelle muette pour une sentinelle en service.
SCHTASKS = "/mnt/c/Windows/System32/schtasks.exe"
JOURNAL = "/home/younes/arma3-marl/infra/sentinelle.jsonl"
ATTENTE_RELEVE = 600          # le chargement d Altis + mods prend ~60 s, on laisse large


def vivant(port=PORT, delai=4):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=delai):
            return True
    except OSError:
        return False


def note(evt, **kw):
    ligne = dict(t=datetime.datetime.now().isoformat(timespec="seconds"), evt=evt, **kw)
    os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
    with open(JOURNAL, "a") as f:
        f.write(json.dumps(ligne) + "\n")
    print("  [sentinelle] %s %s" % (evt, kw), flush=True)
    return ligne


def relever():
    """Relève par la tâche planifiée. `schtasks.exe` est appelable depuis WSL (interop)."""
    note("releve_demandee", tache=TACHE)
    try:
        r = subprocess.run([SCHTASKS, "/Run", "/TN", TACHE],
                           capture_output=True, timeout=60)
        ok = (r.returncode == 0)
    except Exception as e:
        note("releve_impossible", erreur=str(e)); return False
    if not ok:
        note("releve_refusee", code=r.returncode); return False
    t0 = time.time()
    while time.time() - t0 < ATTENTE_RELEVE:
        time.sleep(10)
        if vivant():
            note("pont_revenu", secondes=round(time.time() - t0))
            return True
    note("pont_absent_apres_releve", secondes=ATTENTE_RELEVE)
    return False


def main():
    note("demarrage", port=PORT, periode=PERIODE, seuil=MANQUES)
    manques = 0
    while True:
        if vivant():
            if manques:
                note("battement_retrouve", apres_manques=manques)
            manques = 0
        else:
            manques += 1
            note("manque", n=manques)
            if manques >= MANQUES:
                note("pont_mort")
                relever()
                manques = 0
        time.sleep(PERIODE)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("  port %d : %s" % (PORT, "OUVERT" if vivant() else "FERME"))
        print("  tache planifiee joignable :", end=" ")
        try:
            r = subprocess.run([SCHTASKS, "/Query", "/TN", TACHE],
                               capture_output=True, timeout=30)
            print("OUI" if r.returncode == 0 else "NON (code %d)" % r.returncode)
        except Exception as e:
            print("NON (%s)" % e)
        print("  journal :", JOURNAL)
        sys.exit(0)
    main()
