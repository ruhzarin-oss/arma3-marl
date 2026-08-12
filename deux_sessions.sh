#!/bin/bash
# deux_sessions.sh — LES SESSIONS 2 ET 3 DE L ETAGE 1, EN TACHE DE FOND.
#
# ⟨Fable, 09/08⟩ « S arreter a une session parce que le resultat est beau, c est l ARRET
# OPTIONNEL — l amendement qui elargit, celui que la regle 13 interdit nommement. Question
# miroir : si la session avait rendu 1,02, aurais-tu demande a t arreter la ? »
#
// et la raison de fond, pas seulement de forme : l eventail va de 0,24 a 0,90, et UNE session
# ne distingue pas un terrain qui REPOND FAIBLEMENT d un terrain qui a TIRE UNE SESSION
# BRUYANTE. L eleve s entrainera sur ces terrains : savoir lesquels portent l effet est une
# donnee d entrainement, pas une formalite de procedure.
#
# Chaque session est un SERVEUR NEUF — c est la seule facon de mesurer entre sessions, et
# l ennemi de ce banc est de session.
set -u
D=/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancAppui.Stratis
L=/mnt/data/harmattan-sandbox/logs
cd /home/younes/arma3-marl || exit 1

for s in 2 3; do
  sed -i "s/HMT_SESSION = [0-9]*;/HMT_SESSION = $s;/" $D/init.sqf
  echo "═══ session $s ═══"
  ./relancer.sh 6012 /mnt/data/harmattan-sandbox/staging/serverAP.cfg \
                /mnt/data/harmattan-sandbox/profilesAP $L/serverAP.out || exit 1
  # on attend la fin de la session, pas une horloge
  for i in $(seq 1 90); do
    grep -q "HMT|AP|TERMINE|session|$s" $L/serverAP.out 2>/dev/null && break
    grep -q "HMT|AP|ECHEC" $L/serverAP.out 2>/dev/null && { echo "ECHEC en session $s"; break; }
    sleep 30
  done
  echo "session $s finie a $(date +%H:%M)"
  cp $L/serverAP.out $L/session${s}.out
done
echo "SESSIONS 2 ET 3 TERMINEES"
