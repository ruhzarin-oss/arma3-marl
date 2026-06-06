#!/bin/bash
# Preset DYNAMICS — le "vrai jeu" hardcore : ACE + RHS + factions.
# ⚠️ Change les mécaniques (médical, balistique, fatigue) :
#    nécessite le cycle re-fine-tune avant toute éval sérieuse.
# Compats ACE<->RHS : intégrées à ACE >= 3.16, rien à charger.
W="/mnt/data/harmattan-sandbox/Steam/steamapps/workshop/content/107410"
M="/mnt/data/harmattan-sandbox/mods"

MODS=(
  "$W/450814997"            # CBA_A3
  "$W/463939057"            # ACE3
  "$W/843425103"            # RHS AFRF
  "$W/843577117"            # RHS USAF
  "$W/843593391"            # RHS GREF
  "$W/843632231"            # RHS SAF
  "$W/1673456286"           # 3CB Factions
  "$W/943682362"            # R3F unités
  "$W/583496184"            # CUP Terrains Core
  "$W/583544987"            # CUP Terrains Maps (Takistan etc.)
  "$W/861133494"            # JSRS Soundmod
  "$W/2809399991"           # Real Lighting and Weather
  "$M/@Blastcore_Edited"    # Blastcore
)

# Outillage scénarios : lancer avec "ZEUS=1 ./hmt-dynamics.sh"
[ -n "$ZEUS" ] && MODS+=("$M/@Zeus_Enhanced")

IFS=';' MODLINE="${MODS[*]}"
exec steam -applaunch 107410 -noLauncher -skipIntro "-mod=$MODLINE"
