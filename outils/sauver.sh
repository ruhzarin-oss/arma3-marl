#!/bin/bash
# HMT_SAUVE, chaque nuit a 05:00 : commit, bundle sur C:, push si un remote existe. Garde 7 bundles.
H=/mnt/data/hmt; [ -f $H/.temoin ] || exit 3
exec >> $H/etat/sauver.log 2>&1
echo "=== $(date -Is)"
cd $H/depot || exit 1
# ⭐ 11/09 : le catalogue des episodes fait partie de la sauvegarde ; il part donc sur GitHub avec le code.
timeout 900 python3 $H/depot/outils/catalogue.py || echo "!! catalogue en echec"
git add -A && git commit -qm "sauvegarde nocturne $(date +%F)" 2>/dev/null || echo "rien a commettre"
D=/mnt/c/Users/Younes/hmt_bundles; mkdir -p $D
git bundle create $D/arma3-marl_$(date +%F).bundle --all && echo "bundle ecrit"
ls -t $D/arma3-marl_*.bundle | tail -n +8 | xargs -r rm -v
git remote get-url origin >/dev/null 2>&1 && { git push -q origin --all && echo "push fait" || echo "!! push rate (remote absent ou injoignable)"; }
[ -f $H/depot/ETAT.md ] && cp $H/depot/ETAT.md $D/ETAT.md
# ⛔ CONSTAT DU 11/09 : les episodes n existaient qu en UN exemplaire, sur /mnt/data ; seul le code
# partait sur GitHub. Miroir sur E: (autre disque physique). JAMAIS de --delete : une sauvegarde
# n efface rien, meme ce qui a disparu de la source.
if [ -d /mnt/e/hmt-sauvegardes ]; then
  M=/mnt/e/hmt-sauvegardes/miroir; mkdir -p $M
  for d in runs archive queue; do
    rsync -rt --no-perms --no-owner --no-group $H/$d/ $M/$d/ && echo "miroir $d a jour ($(du -sh $M/$d | cut -f1))" || echo "!! miroir $d rate"
  done
else
  echo "!! E: absent, miroir des episodes NON fait"
fi
