#!/bin/bash
# ═══ LA NUIT — NATIF x2, DOS A DOS ═══════════════════════════════════════════════════
# Predicat d acceptation : DEPOT_NATIF.md, ecrit AVANT le premier episode.
# Deux passes a l identique. Concordance exigee a moins de 10 points, sinon aucun des
# deux n est cite ⟨Fable : deux chiffres qui divergent sont un avertissement recu avant
# de batir dessus⟩.
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/natif
for PASSE in 1 2; do
  echo "═══ PASSE $PASSE — $(date +%H:%M) ═══"
  for i in $(seq 1 67); do
    # ⚠️ LA NUIT EST REPRENABLE ⟨21/08⟩. WSL a redemarre en pleine nuit et a tue 31
    # episodes deja joues sur socle sain — les rejouer aurait coute deux heures pour
    # rien. Un episode DEJA TERMINE est saute : il porte sa marque de fin.
    # ⚠️ « Termine » se lit sur la MARQUE, pas sur l existence du fichier : un episode
    # coupe en plein vol laisse un .txt partiel qui doit etre REJOUE.
    F=/mnt/data/natif/p${PASSE}_e${i}.txt
    if [ -f "$F" ] && grep -aq "BANC DE MONTAGE TERMINE" "$F"; then
      echo "  p${PASSE} e${i}/67  DEJA JOUE — saute"
      continue
    fi
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3
    rm -f /tmp/releve_live.npz
    # ⚠️ MINUTEUR DERIVE DU COUT MESURE DU MECANISME, ET JAMAIS CONTRAIGNANT ⟨20/08⟩.
    # `timeout 330` etait un chiffre ROND, et il ne laissait meme pas la place au prevol
    # certifie. Termes, chacun lu dans le code ou mesure :
    #   echauffement du serveur ............  45 s  (banc_live.py:198)
    #   pont + socle + scene ...............  25 s  (mesure : placeur atteint a ~10 s)
    #   prevol, BORNE EXTERIEURE ...........  180 s (prevol.py, sa duree max legitime)
    #   episode : PAS_MAX 60 x PERIODE 3,28  197 s  (banc_live.py:52)
    #   cloture, releve, npz ...............  10 s
    #                                        ------
    #                                         457 s
    #   marge = UN prevol complet de plus ..  180 s  (absorbe un serveur lent)
    #                                        ------
    #                                         637 s -> 640 s
    # ⚠️ CE MINUTEUR NE DOIT JAMAIS MORDRE : ce sont les gardes nommees qui coupent et
    # qui DISENT pourquoi. Un minuteur qui coupe est une panne muette — c est lui qui a
    # tronque les cinq lots du 19/08 a 5-7 tirages sur 12, sans que rien ne le signale.
    # ⚠️ CHAQUE EPISODE A SON JOURNAL ⟨21/08⟩ : sans `HMT_SESSION`, tous ecrivaient dans
    # `serverLV.out`, un accumulateur multi-jours de 27,8 Mo qu aucune ligne de juge ne
    # pouvait lire. Meme idiome que `porte_lots.sh` depuis toujours.
    HMT_SESSION="_p${PASSE}e${i}" timeout 640 ./.venv/bin/python banc_live.py natif > /mnt/data/natif/p${PASSE}_e${i}.txt 2>&1
    rc=$?; [ "$rc" = "124" ] && echo "  ⛔ LE MINUTEUR A MORDU — episode $i tronque, il ne compte pas" | tee -a /mnt/data/natif/JOURNAL.txt
    if [ -f /tmp/releve_live.npz ]; then cp /tmp/releve_live.npz /mnt/data/natif/p${PASSE}_e${i}.npz; fi
    V=$(grep -ac "prevol VERT" /mnt/data/natif/p${PASSE}_e${i}.txt 2>/dev/null)
    # ⚠️ COMPTE A PART LES EPISODES QUI N ONT PAS EU LIEU ⟨21/08⟩ : l escouade morte
    # pendant le prevol. Les melanger aux echecs deprime le taux — c est ce qui s est
    # passe sur les 147 episodes archives, 9 d entre eux.
    M=$(grep -ac "ESCOUADE MORTE AVANT LE DEPART" /mnt/data/natif/p${PASSE}_e${i}.txt 2>/dev/null)
    echo "  p${PASSE} e${i}/67  $(date +%H:%M)  prevol_vert=${V}  sans_escouade=${M}  npz=$([ -f /mnt/data/natif/p${PASSE}_e${i}.npz ] && echo oui || echo NON)"
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ NUIT TERMINEE — $(date +%H:%M) ═══"
