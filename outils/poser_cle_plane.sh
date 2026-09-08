#!/bin/bash
# Pose la cle d'API Plane SUR LA WORKSTATION. A lancer par Younes, depuis un terminal :
#   ssh -t ws "wsl -u younes -- bash /mnt/data/hmt/depot/outils/poser_cle_plane.sh"
# La cle n'est pas affichee, n'est pas passee en argument, et ne quitte jamais la workstation.
set -u
F=/mnt/data/hmt/etat/plane_api.key
H=http://localhost:8080
E=travaux
printf "Colle la cle d'API Plane (rien ne s'affiche), puis Entree : "
read -rs CLE; echo
[ -n "$CLE" ] || { echo "!! cle vide, rien n'a ete ecrit"; exit 1; }
CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $CLE" "$H/api/v1/workspaces/$E/projects/")
if [ "$CODE" != "200" ]; then
  echo "!! Plane refuse cette cle (code $CODE). Rien n'a ete ecrit."
  echo "   Verifie que le jeton appartient bien a l'espace « $E »."
  exit 1
fi
umask 077
printf '%s' "$CLE" > "$F"
chmod 600 "$F"
unset CLE
echo "cle acceptee (code 200) et posee dans $F, en 600."
echo "Relance Claude Code : le serveur MCP « plane » sera disponible."
