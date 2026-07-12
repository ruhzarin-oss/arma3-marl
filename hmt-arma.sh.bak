#!/bin/bash
# hmt-arma.sh — lance le CLIENT Arma 3 configuré pour l'observation des ops Harmattan.
# -noPause   : le jeu NE SE MET PLUS EN PAUSE quand il perd le focus (alt-tab vers le terminal)
#              -> les ops pilotées par Python survivent pendant que tu lis/écris à côté. INDISPENSABLE.
# -noLauncher -skipIntro : démarrage direct.
# Usage : bash hmt-arma.sh          (vanilla)
#         bash hmt-arma.sh demo     (avec les mods visuels du preset hmt-demo : CBA+JSRS+RLW+Blastcore)
if [ "$1" = "demo" ]; then
  W="/mnt/data/harmattan-sandbox/Steam/steamapps/workshop/content/107410"
  M="/mnt/data/harmattan-sandbox/mods"
  MODS=("$W/450814997" "$W/861133494" "$W/2809399991" "$M/@Blastcore_Edited")
  IFS=';' MODLINE="${MODS[*]}"
  exec steam -applaunch 107410 -noPause -noLauncher -skipIntro "-mod=$MODLINE"
fi
exec steam -applaunch 107410 -noPause -noLauncher -skipIntro
