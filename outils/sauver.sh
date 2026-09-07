#!/bin/bash
# HMT_SAUVE, chaque nuit a 05:00 : commit, bundle sur C:, push si un remote existe. Garde 7 bundles.
H=/mnt/data/hmt; [ -f $H/.temoin ] || exit 3
exec >> $H/etat/sauver.log 2>&1
echo "=== $(date -Is)"
cd $H/depot || exit 1
git add -A && git commit -qm "sauvegarde nocturne $(date +%F)" 2>/dev/null || echo "rien a commettre"
D=/mnt/c/Users/Younes/hmt_bundles; mkdir -p $D
git bundle create $D/arma3-marl_$(date +%F).bundle --all && echo "bundle ecrit"
ls -t $D/arma3-marl_*.bundle | tail -n +8 | xargs -r rm -v
git remote get-url origin >/dev/null 2>&1 && { git push -q origin --all && echo "push fait" || echo "!! push rate (remote absent ou injoignable)"; }
[ -f $H/depot/ETAT.md ] && cp $H/depot/ETAT.md $D/ETAT.md
