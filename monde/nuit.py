"""LA NUIT DE L ARCHIPEL ( smoke test, 25/09 ) : six pays, pont ouvert, gouvernements joues par Qwen, jusqu a STOP.

Chaque jour du monde : une ligne par pays ( vivants, faim, conservation, monnaie et or, visiteurs, decision du
gouvernement ) et la memoire de chaque processus, dans journal.jsonl et nuit.txt. Un instantane de tout l archipel
tous les INSTANTANE_J jours ; un plantage -> reprise depuis le dernier instantane ( au plus REPRISES_MAX fois ).
On l arrete en posant le fichier STOP dans le dossier de la nuit.

   python -m monde.nuit --echelle 2000 --llm --dossier /mnt/data/hmt/archipel/nuit [ --enregistrer /mnt/data/hmt/archipel/matrice ]"""
import argparse, json, os, shutil, sys, time, traceback
from . import config as C
from .archipel import Archipel

INSTANTANE_J = 5
REPRISES_MAX = 5
# la garde memoire ( 25/09 : WSL plein a 47 Go a fige la station ) : pas d instantane au-dessus de SANS_INSTANTANE_GO,
# arret propre au-dessus de ARRET_GO - la station ne doit jamais se figer
SANS_INSTANTANE_GO = 38.0
ARRET_GO = 42.0
# et la marge de toute la machine WSL ( 47 Go ) : les sondes du jour tournent a cote de la nuit ( 26/09 )
MARGE_MIN_GO = 3.0          # moins que ca de memoire disponible : arret propre
MARGE_INSTANTANE_GO = 8.0   # moins que ca : pas d instantane


def disponible_go():
    try:
        for l in open("/proc/meminfo"):
            if l.startswith("MemAvailable:"): return int(l.split()[1]) / 1e6
    except Exception: pass
    return None


def rss_go(pid):
    try:
        for l in open(f"/proc/{pid}/status"):
            if l.startswith("VmRSS:"): return int(l.split()[1]) / 1e6
    except Exception: pass
    return None


def ecrire(d, ligne, texte):
    with open(os.path.join(d, "journal.jsonl"), "a") as f: f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    with open(os.path.join(d, "nuit.txt"), "a") as f: f.write(texte + "\n")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--echelle", type=float, default=2000)
    a.add_argument("--llm", action="store_true")
    a.add_argument("--dossier", default="/mnt/data/hmt/archipel/nuit")
    a.add_argument("--enregistrer", default=None, help="dossier ou chaque ile ecrit tout ce qui s y passe ( Parquet )")
    x = a.parse_args()
    d = x.dossier; os.makedirs(d, exist_ok=True)
    stop, inst = os.path.join(d, "STOP"), os.path.join(d, "instantane")
    reprises = 0
    while True:
        try:
            t0 = time.time()
            reprise = inst if os.path.exists(os.path.join(inst, "pont.pkl")) else None
            arc = Archipel(echelle=x.echelle, ouvert=True, llm=x.llm, reprise=reprise, enregistrer=x.enregistrer)
            ecrire(d, {"evenement": "depart", "reprise": bool(reprise), "pas": arc.pas, "secondes": round(time.time() - t0)},
                   f"== archipel {'repris au pas ' + str(arc.pas) if reprise else 'cree'} en {time.time() - t0:.0f} s "
                   f"( {x.echelle * 500:,.0f} habitants par pays, gouvernements {'Qwen' if x.llm else 'regles'} )")
            while not os.path.exists(stop):
                t0 = time.time(); arc.jours(1); dt = time.time() - t0
                etats = arc._envoyer_a_tous(lambda n: ("etat",))
                mem = {n: rss_go(p.pid) for n, p in arc.proc.items()}
                jour = next(iter(etats.values()))["jour"]
                ecrire(d, {"jour": jour, "secondes": round(dt, 1), "pas": arc.pas, "en_mer": len(arc.mer), "etats": etats, "memoire_go": mem},
                       f"jour {jour:4d} ( {dt:5.0f} s, {len(arc.mer)} en mer, {sum(v or 0 for v in mem.values()):.1f} Go ) | "
                       + " | ".join(f"{n[:6]} {e['vivants']:,} v faim {e['faim']:.0%} {e['monnaie']} {e['euros_par_unite'] or 0:.2f}€ "
                                    f"{'ok' if e['conservation'] else 'ROMPUE'} {e['etrangers']}e"
                                    + (f" gouv {e['gouvernement']['acceptees']}/{e['gouvernement']['actions']}" if e['gouvernement'] else "")
                                    for n, e in etats.items()))
                total = sum(v or 0 for v in mem.values())
                dispo = disponible_go()
                if dispo is not None and dispo < MARGE_MIN_GO:
                    ecrire(d, {"evenement": "arret_marge", "jour": jour, "disponible_go": dispo},
                           f"== ARRET : {dispo:.1f} Go disponibles dans WSL ( marge {MARGE_MIN_GO} Go ), arret propre")
                    arc.fermer(); return 2
                if total > ARRET_GO:
                    ecrire(d, {"evenement": "arret_memoire", "jour": jour, "memoire_go": total},
                           f"== ARRET : {total:.1f} Go de memoire ( garde a {ARRET_GO} Go ), arret propre avant de figer la station")
                    arc.fermer(); return 2
                if jour % INSTANTANE_J == 0 and (total > SANS_INSTANTANE_GO or (dispo is not None and dispo < MARGE_INSTANTANE_GO)):
                    ecrire(d, {"evenement": "instantane_saute", "jour": jour}, f"   instantane saute ( {total:.1f} Go )")
                elif jour % INSTANTANE_J == 0:
                    tmp = inst + ".tmp"; shutil.rmtree(tmp, ignore_errors=True)
                    arc.instantane(tmp); shutil.rmtree(inst, ignore_errors=True); os.replace(tmp, inst)
                    ecrire(d, {"evenement": "instantane", "jour": jour}, f"   instantane du jour {jour}")
            arc.fermer()
            ecrire(d, {"evenement": "stop"}, "== STOP pose : arret propre")
            return 0
        except Exception as e:
            reprises += 1
            ecrire(d, {"evenement": "plantage", "erreur": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-3000:]},
                   f"!! PLANTAGE {type(e).__name__}: {str(e)[:200]} ( reprise {reprises}/{REPRISES_MAX} )")
            try: arc.fermer()
            except Exception: pass
            if reprises >= REPRISES_MAX: return 1
            time.sleep(30)


if __name__ == "__main__":
    sys.exit(main())
