# Prefect comme orchestrateur des runs — etat au 09/09/2026

**Rien n'est bascule.** La production reste `HMT_RUN` -> `outils/file3.sh`. Ce qui suit
tourne A COTE et n'a joue qu'un banc factice.

## Ce qui est monte

| quoi | ou |
|---|---|
| serveur Prefect 3.1.5 | conteneur `harmattan-prefect-1`, API `http://127.0.0.1:4200/api` |
| client Prefect 3.1.5 | `/mnt/data/hmt/prefect/venv` (CPython 3.12) |
| environnement | `/mnt/data/hmt/prefect/env.sh` — a sourcer avant toute commande |
| work pool | `arma`, type `process` |
| limites par instance | `arma-i0` a `arma-i3`, limite 1 chacune |
| ouvrier | `prefect/ouvrier.sh`, copie dans `/home/younes/hmt_prefect_ouvrier.sh` |
| tache Windows | `HMT_PREFECT`, au demarrage, sur le modele de `HMT_ETAT` |
| flux | `prefect/flux_arma.py` |

⚠️ **Le systeme est en Python 3.14 ; Prefect 3.1.5 n'y tourne pas.** D'ou le venv en 3.12,
fabrique par `uv`. Et pydantic doit rester en **2.9.2** : avec pydantic 2.13, Prefect 3.1.5
casse a l'import (`name 'ResultRecordMetadata' is not defined`).

## S'en servir a la main

    . /mnt/data/hmt/prefect/env.sh
    prefect work-pool ls
    prefect gcl ls
    prefect flow-run ls

Jouer un repertoire de jobs (ici l'essai factice, instance 9) :

    . /mnt/data/hmt/prefect/env.sh
    python /mnt/data/hmt/depot/prefect/flux_arma.py /mnt/data/hmt/prefect/queue_essai 9

## Basculer la production sur Prefect — LE JOUR OU C'EST DECIDE

Ordre obligatoire : **d'abord couper l'ancien preneur**, sinon deux preneurs courent sur le
meme fichier de job. `flux_arma.py` ne deplace pas les jobs vers `en_cours/`, il ne sait donc
pas se proteger de `file3.sh`.

    powershell -NoProfile -Command "Disable-ScheduledTask -TaskName HMT_RUN; Start-ScheduledTask -TaskName HMT_PREFECT"

puis creer le deploiement planifie (il n'existe pas encore) :

    . /mnt/data/hmt/prefect/env.sh
    cd /mnt/data/hmt/depot/prefect
    prefect deploy --help   # ou : avaler_la_file.serve(...) / prefect.yaml, a ecrire

## Revenir en arriere

    powershell -NoProfile -Command "Enable-ScheduledTask -TaskName HMT_RUN; Stop-ScheduledTask -TaskName HMT_PREFECT"

L'ancienne file est intacte : `file3.sh`, `file2.sh` et les verrous `queue/verrous/` n'ont pas
ete touches.

## Ce que Prefect ne resout PAS ici

- Il ne remplace pas `run.sh` : la reproductibilite, le `FIN.json`, la copie figee du script,
  tout cela reste dans `outils/`. Prefect ne fait qu'appeler.
- Il n'apporte rien contre les pieges deja payes (tuyau, edition en vol) : ils sont recopies
  a la main dans `flux_arma.py`.
- Il ajoute une piece a maintenir : un conteneur, un venv en 3.12, un pin pydantic, un ouvrier.
