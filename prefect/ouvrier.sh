#!/bin/bash
# Ouvrier Prefect du pool `arma`. Lance par la tache planifiee Windows HMT_PREFECT au demarrage,
# sur le modele exact de HMT_ETAT (wsl.exe -u younes -- bash <script dans le home>).
#
# ⚠️ /mnt/data N'EST PAS MONTE AU DEMARRAGE : `wsl --mount` n'est pas persistant. On attend
# donc le temoin avant de partir, sinon l'ouvrier meurt trois secondes apres le boot.
#
# Meme garde anti-modification-en-vol que run.sh et file3.sh : on s'execute depuis une copie.
if [ "${HMT_FIGE:-0}" != "1" ]; then
  C=$(mktemp /tmp/ouvrier_fige.XXXX.sh); cp "$0" "$C"
  HMT_FIGE=1 exec bash "$C" "$@"
fi
set -u
for _ in $(seq 1 120); do [ -f /mnt/data/hmt/.temoin ] && break; sleep 30; done
[ -f /mnt/data/hmt/.temoin ] || exit 3
. /mnt/data/hmt/prefect/env.sh
mkdir -p /mnt/data/hmt/etat
exec >> /mnt/data/hmt/etat/prefect_ouvrier.log 2>&1
echo "=== $(date -Is) demarrage de l ouvrier arma (pid $$)"
# exec : bash disparait, plus rien a lire dans le script, plus rien a corrompre.
exec prefect worker start --pool arma --name ouvrier-wsl
