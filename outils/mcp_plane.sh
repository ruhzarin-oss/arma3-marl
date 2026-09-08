#!/bin/bash
# Serveur MCP de Plane, lance SUR LA WORKSTATION. Claude ne fait que lui parler par ssh (stdio).
# Rien du projet ne vit sur le Mac : ni le serveur, ni la cle d'API.
#
# La cle est lue dans un fichier local en 600, jamais passee en argument (les arguments d'un
# processus sont visibles de toute la machine par `ps`).
# ! Tout ce qui va sur la sortie standard EST le protocole : aucun echo ici, les diagnostics
#   partent sur la sortie d'erreur.
CLE_F=/mnt/data/hmt/etat/plane_api.key
exec 2>>/mnt/data/hmt/etat/mcp_plane.log
echo "=== $(date -Is) demarrage" >&2
[ -r "$CLE_F" ] || { echo "cle absente : $CLE_F (lancer poser_cle_plane.sh)" >&2; exit 1; }
export PLANE_API_KEY="$(tr -d '\r\n' < "$CLE_F")"
export PLANE_API_HOST_URL=http://localhost:8080
export PLANE_WORKSPACE_SLUG=travaux
exec node /home/younes/.local/lib/node_modules/@makeplane/plane-mcp-server/build/index.js
