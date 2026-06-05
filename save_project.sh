#!/bin/bash
DEST="$HOME/Bureau/save01"
PFX="/mnt/data/harmattan-sandbox/Steam/steamapps/compatdata/107410/pfx/drive_c/users/steamuser"
SB="/mnt/data/harmattan-sandbox"
mkdir -p "$DEST/code" "$DEST/arma-missions" "$DEST/arma-server"

# 1. Code complet (modeles .pt, logs, .md, .py, .sqf) SANS le venv
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude='.venv' --exclude='__pycache__' "$HOME/arma3-marl/" "$DEST/code/"
else
  cd "$HOME/arma3-marl" && for f in $(ls -A | grep -vE '^(\.venv|__pycache__)$'); do cp -r "$f" "$DEST/code/" 2>/dev/null; done
fi

# 2. Mission SOLO HarmattanKoth (sans les cmd jetables)
cp -r "$PFX/Documents/Arma 3/missions/HarmattanKoth.Altis" "$DEST/arma-missions/" 2>/dev/null
rm -f "$DEST/arma-missions/HarmattanKoth.Altis/hmt_bridge/"cmd_*.sqf 2>/dev/null

# 3. SQF du pont (depuis la mission bridge dediee)
mkdir -p "$DEST/arma-missions/bridge-sqf"
for f in init.sqf harmattan_actuator.sqf arma_harmattan.sqf mission.sqm; do
  cp "$SB/arma3server/mpmissions/HarmattanBridge0.Altis/$f" "$DEST/arma-missions/bridge-sqf/" 2>/dev/null
done

# 4. Configs serveur + scripts de lancement
cp "$SB/staging/"*.cfg "$DEST/arma-server/" 2>/dev/null
cp "$SB/"*.sh "$DEST/arma-server/" 2>/dev/null
cp "$SB/staging/"*.sh "$DEST/arma-server/" 2>/dev/null

# 5. requirements pour recreer le venv
"$HOME/arma3-marl/.venv/bin/pip" freeze > "$DEST/code/requirements-venv.txt" 2>/dev/null

# 6. resume
{ echo "save01 genere le: $(date)"; echo "taille: $(du -sh "$DEST" | cut -f1)"; echo "fichiers: $(find "$DEST" -type f | wc -l)"; echo "modeles .pt: $(ls "$DEST/code/"*.pt 2>/dev/null | wc -l)"; } > "$DEST/_RESUME_SAVE.txt"
cat "$DEST/_RESUME_SAVE.txt"
