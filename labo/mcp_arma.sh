#!/bin/bash
# Serveur MCP du LABO Arma, lancé SUR LA WORKSTATION. Claude lui parle par ssh en stdio, comme à
# Plane (outils/mcp_plane.sh). Rien ne vit sur le Mac.
# ⚠️ Tout ce qui va sur la sortie standard EST le protocole : aucun echo ici, les diagnostics
#   partent sur la sortie d'erreur, versée dans etat/mcp_arma.log.
# ⚠️ Ce script ne lance PAS Arma. Il parle au serveur du labo s'il tourne (labo/lancer_labo.sh) ;
#   sinon chaque outil répond PONT MORT.
# ⚠️ Il vit dans labo/ et pas dans outils/ : controle_avant_run.sh refuse TOUS les jobs dès
#   qu'un fichier de outils/ n'est pas commité.
exec 2>>/mnt/data/hmt/etat/mcp_arma.log
echo "=== $(date -Is) demarrage pid $$" >&2
[ -f /mnt/data/hmt/.temoin ] || { echo "témoin absent : /mnt/data n'est pas le bon disque" >&2; exit 1; }
exec python3 /mnt/data/hmt/depot/labo/mcp_arma.py
