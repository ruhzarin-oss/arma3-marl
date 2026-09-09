#!/usr/bin/env python3
"""Orchestration des runs Arma par Prefect — EN PARALLELE de la file historique.

Ce fichier n'a AUCUN pouvoir tant que personne ne l'appelle : il n'installe pas de
deploiement planifie. La file historique (HMT_RUN -> outils/file3.sh) reste seule en
production. Ici on se contente d'appeler le MEME lanceur, outils/run.sh, avec les
memes jobs JSON.

Ce que Prefect apporte par rapport a file3.sh :
  - la concurrence par instance devient une limite nommee cote serveur (arma-i<N>),
    au lieu d'un mkdir de verrou dans queue/verrous/ ;
  - un run mort ne laisse pas un verrou orphelin : le jeton est rendu par le serveur ;
  - l'historique des executions est interrogeable (prefect flow-run ls).

⛔ DEUX PIEGES DEJA PAYES, REPORTES ICI TELS QUELS :
  1. AUCUN TUYAU en travers de run.sh. Un tuyau ne se ferme que quand TOUS ses ecrivains
     ont ferme, or le serveur Arma lance par le petit-fils herite du descripteur. Le 08/09
     un `| tee` a tenu un verrou trois heures apres la fin du run. On redirige donc la
     sortie vers un FICHIER.
  2. UN RUN QUI A RENDU UN VERDICT NE SE REJOUE PAS. Meme un FIN.json en ECHEC est un
     resultat : le rejouer fabriquerait un doublon dans runs/ et fausserait le debit.
     La reprise n'existe donc que pour un run mort SANS FIN.json.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.concurrency.sync import concurrency

H = Path("/mnt/data/hmt")
RUN_SH = H / "depot" / "outils" / "run.sh"
QUEUE = H / "queue"
INSTANCES = (0, 1, 2, 3)


def instance_du_job(chemin_job: str) -> int:
    """Numero d'instance Arma declare par le job. C'est lui qui choisit la limite."""
    return int(json.loads(Path(chemin_job).read_text(encoding="utf-8"))["instance"])


def runs_du_job(chemin_job: str, depuis: float) -> list[Path]:
    """Dossiers de runs/ nes apres `depuis` et portant EXACTEMENT ce job.

    On compare le CONTENU du job.json recopie par run.sh, pas son nom : deux jobs
    peuvent porter le meme nom de fichier a des jours d'intervalle.
    """
    voulu = Path(chemin_job).read_text(encoding="utf-8")
    trouves = []
    for j in glob.glob(str(H / "runs" / "*" / "job.json")):
        p = Path(j)
        if p.stat().st_mtime < depuis - 5:
            continue
        try:
            if p.read_text(encoding="utf-8") == voulu:
                trouves.append(p.parent)
        except OSError:
            continue
    return sorted(trouves)


def verdict_deja_rendu(chemin_job: str, depuis: float) -> tuple[Path, dict] | None:
    """Renvoie (dossier, FIN.json) si ce job a DEJA rendu un verdict depuis `depuis`."""
    for r in runs_du_job(chemin_job, depuis):
        f = r / "FIN.json"
        if f.exists():
            return r, json.loads(f.read_text(encoding="utf-8"))
    return None


@task(name="jouer-job", retries=1, retry_delay_seconds=60, log_prints=True)
def jouer_job(chemin_job: str, depuis: float | None = None) -> dict:
    """Joue UN job par le lanceur historique run.sh, sous la limite de son instance.

    `depuis` est l'horodatage du debut du flux. Il sert a reconnaitre le run que CETTE
    execution a cree — et donc a ne pas le rejouer a la reprise s'il a rendu un FIN.json.
    """
    log = get_run_logger()
    depuis = time.time() if depuis is None else depuis
    inst = instance_du_job(chemin_job)
    nom = Path(chemin_job).name

    # --- LA GARDE DE REPRISE. A la 2e tentative, si le 1er essai a rendu un verdict,
    # on ne rejoue pas : on rend ce verdict. `retries=1` ne sert donc qu'aux runs MORTS.
    deja = verdict_deja_rendu(chemin_job, depuis)
    if deja is not None:
        r, fin = deja
        log.info("%s a deja rendu %s dans %s — pas de rejeu", nom, fin.get("verdict"), r.name)
        return {"job": nom, "instance": inst, "run": str(r), "verdict": fin.get("verdict"),
                "code": fin.get("code"), "rejoue": False}

    # ⛔ `strict=True` N EST PAS UN DETAIL. Mesure du 09/09 : sans lui, une limite
    # ABSENTE (`arma-i9`) est ignoree avec un simple WARNING et le job part quand meme.
    # Une protection qui se desactive toute seule quand on se trompe de nom ne protege
    # rien. Avec `strict`, l instance sans limite declaree fait ECHOUER le job.
    with concurrency(f"arma-i{inst}", strict=True):
        log.info("jeton arma-i%s pris — %s", inst, nom)
        fd, trace = tempfile.mkstemp(prefix="prefect_run_", suffix=".log", dir="/tmp")
        os.close(fd)
        t0 = time.time()
        # ⛔ Pas de PIPE ici (voir l'entete). Sortie vers un fichier, stdin ferme.
        with open(trace, "wb") as sortie:
            code = subprocess.run(
                ["bash", str(RUN_SH), chemin_job],
                stdout=sortie, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            ).returncode
        log.info("run.sh a rendu le code %s en %ds — trace %s", code, int(time.time() - t0), trace)

    fin = verdict_deja_rendu(chemin_job, depuis)
    if fin is None:
        # Aucun FIN.json : le run est mort sans rendre de verdict. C'est le SEUL cas
        # ou une reprise a un sens.
        raise RuntimeError(
            f"{nom} : run.sh code {code} et AUCUN FIN.json — voir {trace}"
        )
    r, contenu = fin
    log.info("%s -> %s verdict %s", nom, r.name, contenu.get("verdict"))
    return {"job": nom, "instance": inst, "run": str(r), "verdict": contenu.get("verdict"),
            "code": contenu.get("code"), "rejoue": False}


@flow(name="avaler-la-file", log_prints=True)
def avaler_la_file(racine: str = str(QUEUE), instances: list[int] | None = None) -> list[dict]:
    """Joue tous les jobs d'un repertoire, un par instance a la fois.

    `racine` : le repertoire des jobs. Par defaut la vraie file.
    `instances` : si donne, on ne prend que les jobs de ces instances. C'est le
                  garde-fou pour essayer le flux sans toucher aux jobs Arma reels.

    ⚠️ Ce flux ne DEPLACE pas les jobs (pas de en_cours/, pas de faits/). Tant que
    HMT_RUN tourne, faire pointer ce flux sur la vraie file ferait courir DEUX preneurs
    sur le meme fichier. Voir prefect/LISEZMOI.md pour l'ordre de bascule.
    """
    log = get_run_logger()
    t_flux = time.time()
    jobs = sorted(glob.glob(os.path.join(racine, "*.json")), key=os.path.getmtime)
    retenus = []
    for j in jobs:
        try:
            i = instance_du_job(j)
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            log.warning("IGNORE %s : instance illisible (%s)", Path(j).name, e)
            continue
        if instances is not None and i not in instances:
            continue
        retenus.append((j, i))
    log.info("%d job(s) retenu(s) sur %d dans %s", len(retenus), len(jobs), racine)

    futurs = [jouer_job.submit(j, t_flux) for j, _ in retenus]
    resultats = []
    for f, (j, i) in zip(futurs, retenus):
        try:
            resultats.append(f.result())
        except Exception as e:  # un job casse n'emporte pas les autres
            log.error("%s (instance %s) a echoue : %s", Path(j).name, i, e)
            resultats.append({"job": Path(j).name, "instance": i, "verdict": "ECHEC", "erreur": str(e)})
    return resultats


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(avaler_la_file(racine=sys.argv[1],
                                        instances=[int(x) for x in sys.argv[2:]] or None),
                         indent=1, ensure_ascii=False))
    else:
        print(json.dumps(avaler_la_file(), indent=1, ensure_ascii=False))
