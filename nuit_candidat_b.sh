#!/bin/bash
# ═══ LA NUIT DU CANDIDAT B — TROIS MANOEUVRES, ENTRELACEES ═══════════════════════
# Pre-inscription 82101f9 + AMENDEMENT_CANDIDAT_B.md (87e06cf) + ANGLE_MORT (819354e).
#
# ⚠️ ENTRELACEES, PAS L UNE APRES L AUTRE. Jouer 20 frontales puis 20 flancs puis 20 arrets
# confondrait la manoeuvre avec l HEURE : un serveur qui se degrade, un disque qui se
# remplit, une machine qui chauffe — tout ca frapperait le troisieme bras seul. En tour de
# role, chaque bras prend la meme part de chaque moment de la nuit.
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/candb
N=20
for i in $(seq 1 $N); do
  for BRAS in b_frontale b_flanc b_arret; do
    F=/mnt/data/candb/${BRAS}_e${i}.txt
    # ⚠️ REPRENABLE PAR LA MARQUE DE FIN, jamais par l existence du fichier : un episode
    # coupe en plein vol laisse un .txt partiel qui doit etre REJOUE.
    if [ -f "$F" ] && grep -aq "BANC DE MONTAGE TERMINE" "$F"; then
      echo "  ${BRAS} e${i}/${N}  DEJA JOUE — saute"; continue
    fi
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3
    rm -f /tmp/releve_live.npz
    # minuteur : le meme que la nuit natif, derive terme a terme (banc_live.py). Il ne doit
    # JAMAIS mordre — ce sont les gardes nommees qui coupent et qui disent pourquoi.
    HMT_SESSION="_${BRAS}e${i}" timeout 640 ./.venv/bin/python banc_live.py $BRAS > "$F" 2>&1
    rc=$?
    [ "$rc" = "124" ] && echo "  ⛔ LE MINUTEUR A MORDU — ${BRAS} e${i} tronque, il ne compte pas" | tee -a /mnt/data/candb/journal.txt
    [ -f /tmp/releve_live.npz ] && cp /tmp/releve_live.npz /mnt/data/candb/${BRAS}_e${i}.npz
    V=$(grep -ac "prevol VERT" "$F" 2>/dev/null)
    M=$(grep -ac "ESCOUADE MORTE AVANT LE DEPART" "$F" 2>/dev/null)
    echo "  ${BRAS} e${i}/${N}  $(date +%H:%M)  prevol_vert=${V}  sans_escouade=${M}" | tee -a /mnt/data/candb/journal.txt
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ NUIT CANDIDAT B TERMINEE — $(date +%H:%M) ═══" | tee -a /mnt/data/candb/journal.txt
