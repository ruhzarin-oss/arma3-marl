#!/bin/bash
# Applique le patch « menace visible » quand rien ne tourne, commite, pose les 19 jobs de controle.
set -e
H=/mnt/data/hmt; D=$H/depot
N=$(ls $H/queue/en_cours/ 2>/dev/null | wc -l); Q=$(ls $H/queue/*.json 2>/dev/null | wc -l)
[ "$N" -eq 0 ] && [ "$Q" -eq 0 ] || { echo "ARRET : $N en vol, $Q en file"; exit 1; }
cd $D
[ -z "$(git status --short bancs/chacal outils)" ] || { echo "ARRET : bancs/chacal ou outils modifies"; exit 1; }
python3 menace/patch_mission_menace.py $D || { git checkout bancs/chacal outils; exit 1; }
bash -n bancs/chacal/lancer.sh || { git checkout bancs/chacal outils; exit 1; }
git add bancs/chacal outils && git -c user.name="Younes Bouhassoun" -c user.email="younesbhn@gmail.com" commit -q -m "mission : menace visible ( perceptions de la menace en fin de ligne de decision, fenetre d observation, controle de perception )

Version 3 du marqueur de decision. CHACAL_OBSERVATION ( 0 = origine, 90 s fixe par Younes ) avant les choix P1, P2, P4 ;
CHACAL_CONTROLE_PERCEPTION ( groupe inerte a 150 m devant ou 1500 m derriere ). Deux canaux : CHACAL_fnc_voit et
targetKnowledge du groupe ; verite a part. Plan : plans/plan-menace-visible.md ; controles : menace/CONTROLES_MENACE_VISIBLE.md.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
echo "mission $(git rev-parse --short HEAD)"
python3 $D/menace/jobs_controles.py --poser
