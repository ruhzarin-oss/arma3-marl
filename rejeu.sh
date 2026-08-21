#!/bin/bash
# ═══ LE REJEU APPARIE DE LA POLITIQUE ════════════════════════════════════════════════
# ⟨AMENDEMENT_NATIF.md § B⟩ Le 44,8 % a ete joue SANS ce prevol. Une certification plus
# stricte jette plus de mondes defectueux, donc NATIF tire d une distribution plus propre
# et le biais pousse DANS LE SENS DU RETRAIT de l acquis. La comparaison n est licite que
# contre une politique REJOUEE sous le meme prevol. Meme forme que la nuit natif.
# ⚠️ NE PAS LANCER avant que T5 ait son controle positif et que T7 ait certifie le canal
# de feu — la politique, elle, emprunte ce canal.
cd /home/younes/arma3-marl || exit 1
mkdir -p /mnt/data/politique
for PASSE in 1 2; do
  echo "═══ PASSE $PASSE — $(date +%H:%M) ═══"
  for i in $(seq 1 67); do
    for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
    sleep 3
    rm -f /tmp/releve_live.npz
    # ⚠️ MINUTEUR DERIVE, MEME DERIVATION QUE `nuit_natif.sh` ⟨20/08⟩ : echauffement 45
    # + amorcage 25 + borne exterieure du prevol 180 + episode (PAS_MAX 60 x PERIODE
    # 3,28) 197 + cloture 10 = 457 s, plus une marge d UN prevol complet = 637 -> 640.
    # `timeout 330` ne laissait meme pas la place au prevol certifie. Il gouverne la
    # nuit POLITIQUE, qui vient apres le natif : derive AVANT elle, pas pendant.
    # ⚠️ CHAQUE EPISODE A SON JOURNAL ⟨21/08⟩ : sans `HMT_SESSION`, tous ecrivaient dans
    # `serverLV.out`, un accumulateur multi-jours de 27,8 Mo qu aucune ligne de juge ne
    # pouvait lire. Meme idiome que `porte_lots.sh` depuis toujours.
    HMT_SESSION="_p${PASSE}e${i}" timeout 640 ./.venv/bin/python banc_live.py politique > /mnt/data/politique/p${PASSE}_e${i}.txt 2>&1
    rc=$?; [ "$rc" = "124" ] && echo "  ⛔ LE MINUTEUR A MORDU — episode $i tronque, il ne compte pas"
    if [ -f /tmp/releve_live.npz ]; then cp /tmp/releve_live.npz /mnt/data/politique/p${PASSE}_e${i}.npz; fi
    echo "  p${PASSE} e${i}/67  $(date +%H:%M)  npz=$([ -f /mnt/data/politique/p${PASSE}_e${i}.npz ] && echo oui || echo NON)"
  done
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ REJEU TERMINE — $(date +%H:%M) ═══"
