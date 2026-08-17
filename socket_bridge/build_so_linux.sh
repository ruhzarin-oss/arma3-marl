#!/bin/bash
# ═══ LA RECETTE DU .so LINUX — celle qui produit le binaire QUE LE SERVEUR CHARGE ═══
#
# ⚠️ `build_ext.sh` NE PRODUIT PAS CE BINAIRE. Il compile avec `x86_64-w64-mingw32-gcc`,
# donc une DLL Windows. Le serveur tourne sous WSL et charge un ELF Linux. La recette du
# .so Linux n'était documentée NULLE PART : retrouvée le 17/08 par reproduction — la source
# de `manager-appris` recompilée avec la ligne ci-dessous rend EXACTEMENT 17600 octets, la
# taille du binaire qui tournait. C'est ce qui a prouvé que `hmt_native.c` en est la source.
#
# Sans ce fichier, la prochaine personne qui veut rebâtir le pont lit `build_ext.sh`,
# produit une DLL Windows, et ne comprend pas pourquoi le serveur ne la charge pas.
set -e
cd "$(dirname "$0")"
SB=/mnt/data/harmattan-sandbox/arma3server

# ⚠️ JAMAIS À CHAUD. Le serveur garde le .so ouvert ; le remplacer sous lui donne des pannes
# qu'aucun journal n'explique.
N=$(pgrep -f arma3server | wc -l)
if [ "$N" -gt 0 ]; then echo "⛔ $N serveur(s) tourne(nt) — on ne remplace pas à chaud."; exit 1; fi

gcc -shared -fPIC -O2 -o hmt_native_x64.so hmt_native.c -lpthread
echo "compilé : $(stat -c%s hmt_native_x64.so) o"

# ⚠️ SAUVEGARDE HORODATÉE AVANT TOUT REMPLACEMENT, avec l'empreinte de ce qu'on écrase.
if [ -f "$SB/hmt_native_x64.so" ]; then
  mkdir -p "$SB/so_sauvegardes"
  cp -p "$SB/hmt_native_x64.so" "$SB/so_sauvegardes/hmt_native_x64.so.$(date +%d%m%Y-%H%M)"
  echo "ancien sauvé — sha256 $(sha256sum "$SB/hmt_native_x64.so" | cut -c1-24)"
fi
cp hmt_native_x64.so "$SB/hmt_native_x64.so"
echo "déployé — sha256 $(sha256sum "$SB/hmt_native_x64.so" | cut -c1-24)"
