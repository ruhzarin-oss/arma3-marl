# Prefect comme orchestrateur des runs — etat au 09/09/2026

**Rien n'est bascule.** La production reste `HMT_RUN` -> `outils/file3.sh`. Ce qui suit tourne
A COTE et n'a joue qu'un banc factice. Aucun deploiement planifie n'existe : l'ouvrier tourne
mais ne recoit rien.

## Ce qui est monte

| quoi | ou |
|---|---|
| serveur Prefect 3.1.5 | conteneur `harmattan-prefect-1`, API `http://127.0.0.1:4200/api` |
| client Prefect 3.1.5 | `/mnt/data/hmt/prefect/venv` (CPython 3.12) |
| environnement | `/mnt/data/hmt/prefect/env.sh` — a sourcer avant toute commande |
| work pool | `arma`, type `process` |
| limites par instance | `arma-i0` a `arma-i3`, limite 1 chacune ; `arma-i9` pour le factice |
| ouvrier | `prefect/ouvrier.sh`, copie dans `/home/younes/hmt_prefect_ouvrier.sh` |
| tache Windows | `HMT_PREFECT`, au demarrage + 3 min, calque de `HMT_ETAT` |
| flux | `prefect/flux_arma.py` |
| banc de preuve | `bancs/factice/lancer.sh` — dort 20 s, ne mesure rien |

⚠️ **Le systeme est en Python 3.14 ; Prefect 3.1.5 n'y tourne pas.** D'ou le venv en 3.12,
fabrique par `uv`. Et **pydantic doit rester en 2.9.2** : avec pydantic 2.13, Prefect 3.1.5
casse a l'import (`name 'ResultRecordMetadata' is not defined`). `importlib_metadata` est
un ajout manuel, il manque aux dependances de Prefect 3.1.5.

## Ce que l'essai du 09/09 a MESURE

1. **La chaine passe.** Flux -> `run.sh` -> `bancs/factice/lancer.sh` -> deux `resultat.json`
   -> `FIN.json` verdict COMPLET, en 40 s. Run : `runs/2026-09-09_0209_factice`.
2. **La limite mord.** Deux flux lances a 02:13:09 sur l'instance 9 : le premier prend le
   jeton a 02:13:13 et le rend a 02:13:56 ; le second ne l'obtient qu'a 02:13:59. Les deux
   runs ne se recouvrent pas.
3. ⛔ **Une limite ABSENTE ne protege pas — elle se cree toute seule, DESACTIVEE.** Au premier
   essai, `arma-i9` n'existait pas : Prefect a ecrit « Concurrency limits ['arma-i9'] do not
   exist - skipping acquisition », a cree la limite avec `active=False`, et a lance le job
   quand meme. Remede : `strict=True` dans le flux, et verifier `active` — pas seulement
   l'existence :

       . /mnt/data/hmt/prefect/env.sh
       python - <<'PY'
       import asyncio
       from prefect.client.orchestration import get_client
       async def m():
           async with get_client() as c:
               r = await c._client.post("/v2/concurrency_limits/filter", json={"limit": 50})
               for l in r.json():
                   print(l["name"], "limite", l["limit"], "actif", l["active"])
       asyncio.run(m())
       PY

   Une limite `active=False` laisse tout passer en silence. C'est le meme piege qu'un verrou
   `mkdir` qui reussirait toujours.

## S'en servir a la main

    . /mnt/data/hmt/prefect/env.sh
    prefect work-pool ls ; prefect gcl ls ; prefect flow-run ls

Rejouer l'essai factice :

    . /mnt/data/hmt/prefect/env.sh
    python /mnt/data/hmt/depot/prefect/flux_arma.py /mnt/data/hmt/prefect/essai_a 9

## Basculer la production sur Prefect — LE JOUR OU C'EST DECIDE

Ordre obligatoire : **d'abord couper l'ancien preneur**. `flux_arma.py` ne deplace pas les
jobs vers `en_cours/` : si `HMT_RUN` tourne encore, deux preneurs courent sur le meme fichier.

    powershell -NoProfile -Command "Disable-ScheduledTask -TaskName HMT_RUN"

Puis, l'ouvrier tournant deja, creer le deploiement planifie — **il n'existe pas encore, c'est
la piece manquante** :

    . /mnt/data/hmt/prefect/env.sh
    cd /mnt/data/hmt/depot/prefect
    python -c "from flux_arma import avaler_la_file; \
      avaler_la_file.from_source('/mnt/data/hmt/depot/prefect', entrypoint='flux_arma.py:avaler_la_file')\
      .deploy(name='file-arma', work_pool_name='arma', cron='*/10 * * * *')"

## Revenir en arriere

    powershell -NoProfile -Command "Enable-ScheduledTask -TaskName HMT_RUN"
    . /mnt/data/hmt/prefect/env.sh && prefect deployment delete 'avaler-la-file/file-arma'

L'ancienne file est intacte : `file3.sh`, `file2.sh` et `queue/verrous/` n'ont pas ete touches.
Pour retirer completement l'ouvrier :
`powershell -NoProfile -Command "Unregister-ScheduledTask -TaskName HMT_PREFECT -Confirm:$false"`.

## Ce que Prefect ne resout PAS ici

- Il ne remplace pas `run.sh` : reproductibilite, `FIN.json`, copie figee du script, controle
  avant run — tout reste dans `outils/`. Prefect ne fait qu'appeler.
- Il n'apporte rien contre les pieges deja payes (tuyau en travers, edition en vol) : ils sont
  recopies a la main dans `flux_arma.py`.
- Il ne voit pas le code de sortie reel d'un run. `run.sh` se termine sur `wiki.sh`, dont le
  code masque celui du run : depuis le 08/09, `outils/journal.py` plante
  (`TypeError: ... '//': 'NoneType' and 'int'`, ligne 122) et TOUS les runs rendent 1, y
  compris ceux dont le `FIN.json` dit COMPLET. Le flux se fie donc au `FIN.json`, jamais au
  code de sortie. **Ce bug est anterieur a Prefect et n'est pas corrige ici.**
- Il ajoute des pieces a maintenir : un conteneur, un venv 3.12, un pin pydantic, un ouvrier,
  une tache planifiee de plus.
