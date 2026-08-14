#!/bin/bash
# session_suivante.sh — enchaine la session suivante de l etage 1.
# ⚠️ LE JOURNAL PORTE LE NUMERO DE LA SESSION. Premiere version : le nom `c3_session2.out`
# etait ecrit en dur, donc la session 3 s est journalisee dans le fichier de la 2. Le journal
# ne portait pas le nom de ce qu il contient — et un corpus qui ment sur son nom est un corpus
# qu on lira de travers. Trouve pendant la garde du 14/08.
cd /home/younes/arma3-marl
L=/mnt/data/harmattan-sandbox/logs
I=/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancAppui.Stratis/init.sqf
N=$(grep -o 'HMT_SESSION = [0-9]*' $I | grep -o '[0-9]*')
S=$((N+1))
sed -i "s/HMT_SESSION = $N;/HMT_SESSION = $S;/" $I
echo "  etage 1 : campagne 3, session $S"
bash relancer.sh 6012 /mnt/data/harmattan-sandbox/staging/serverAP.cfg \
     /mnt/data/harmattan-sandbox/profilesAP $L/c3_session$S.out 2>&1 | tail -1
