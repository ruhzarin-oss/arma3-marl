#!/bin/bash
# build_ext.sh — compile la DLL hmt_ext_x64.dll (extension Arma, pour le client Proton SOLO)
# et la pose dans la racine du client Arma. Crée aussi le dossier-pont /tmp/hmt_bridge.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ARMA_CLIENT="/mnt/data/harmattan-sandbox/Steam/steamapps/common/Arma 3"

echo "== 1. Vérif du compilateur mingw =="
if ! command -v x86_64-w64-mingw32-gcc >/dev/null 2>&1; then
  echo "ABSENT. Lance d'abord :  sudo apt install -y gcc-mingw-w64-x86-64"
  exit 1
fi

echo "== 2. Compilation hmt_ext_x64.dll =="
x86_64-w64-mingw32-gcc -O2 -shared -static-libgcc \
  -o "$HERE/hmt_ext_x64.dll" "$HERE/hmt_ext_x64.c"
echo "OK -> $HERE/hmt_ext_x64.dll"
echo "   exports :"; x86_64-w64-mingw32-objdump -p "$HERE/hmt_ext_x64.dll" 2>/dev/null | grep -iE "RVExtension" || true

echo "== 3. Pose la DLL dans la racine du client Arma =="
cp -v "$HERE/hmt_ext_x64.dll" "$ARMA_CLIENT/hmt_ext_x64.dll"

# REVUE 17/08 : ce script préparait /tmp/hmt_bridge (= Z:\tmp\hmt_bridge) alors que la DLL
# lit C:\hmt_bridge (DEFAULT_BRIDGE dans hmt_ext_x64.c). fopen échouait donc, et son échec
# renvoie "" — exactement le code de retour de « pas encore écrit ». Absence de fichier et
# mauvais chemin étaient LE MÊME SIGNAL, et l'actuateur repollait indéfiniment.
echo "== 4. Dossier-pont — ATTENTION AU CHEMIN =="
echo "   la DLL ouvre  : C:\\hmt_bridge\\cmd_<N>.sqf   (DEFAULT_BRIDGE, hmt_ext_x64.c)"
echo "   surchargeable : variable d'environnement HMT_BRIDGE_WIN"
echo "   Ce script ne crée plus /tmp/hmt_bridge : ce chemin (Z:\\tmp\\hmt_bridge) n'est PAS"
echo "   celui que la DLL lit. Crée le dossier dans le préfixe Proton (drive_c/hmt_bridge),"
echo "   ou pose HMT_BRIDGE_WIN — et vérifie que Python écrit bien au même endroit."

echo
echo "PRÊT. Suite = test en jeu (voir README-SOCKET.md) :"
echo "  - charger harmattan_actuator_ext.sqf depuis l'init de la mission cliente"
echo "  - lancer  python live_arena_sp_socket.py  puis mettre la mission en jeu"
