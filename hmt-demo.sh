#!/bin/bash
# Preset DEMO — visuel/audio uniquement, AUCUN impact sur les dynamics.
# Compatible avec les cerveaux actuels (koth_finetuned.pt) sans re-fine-tune.
W="/mnt/data/harmattan-sandbox/Steam/steamapps/workshop/content/107410"
M="/mnt/data/harmattan-sandbox/mods"

MODS=(
  "$W/450814997"            # CBA_A3
  "$W/861133494"            # JSRS Soundmod
  "$W/2809399991"           # Real Lighting and Weather
  "$M/@Blastcore_Edited"    # Blastcore
)

IFS=';' MODLINE="${MODS[*]}"
exec steam -applaunch 107410 -noLauncher -skipIntro "-mod=$MODLINE"
