#!/bin/bash
# ═══ LES CINQ SABOTAGES SUR UN SEUL HASH ⟨ligne 4 du critere⟩ ═══════════════════════════════
# Ils dataient de TROIS socles differents : munitions et jambes sur 2.8.0, gel sur 2.10.0,
# lenteur sur 2.12.0 — « tous rejoues » etait la faute d hier reconstruite. Ici, un seul hash.
# ⚠️ CHAQUE RUN ECRIT UN TAMPON LISIBLE PAR MACHINE : mode, version LUE DANS LE MONDE, commit,
# verdict, date. La ligne 4 cessera d etre une constante basculee a la main — elle LIRA.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/sabotages6; mkdir -p $D; : > $D/JOURNAL.txt; : > $D/TAMPONS.txt
COMMIT=$(git rev-parse --short HEAD)
VER=$(grep -o 'HMT_SOCLE_VERSION = "[^"]*"' bancs/socle/socle.sqf | sed 's/.*= "//;s/"//')
echo "socle $VER  commit $COMMIT  $(date +%H:%M)" | tee -a $D/JOURNAL.txt
# tir passe par le smoke du placeur (bras A2, arme videe). Le bras A du smoke visait
# la traverse : il ne juge plus rien depuis le 20/08 et son tampon n est plus ecrit.
# ancien commentaire : traverse et tir passent par le smoke du placeur, deja joue sur ce hash — on le rejoue ici
# pour que son tampon porte la meme version que les autres.
for m in smoke sabotage jambes gel lenteur; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
  echo "═══ $m — $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
  if [ "$m" = "smoke" ]; then
    timeout 900 ./.venv/bin/python -u smoke_placeur.py > $D/$m.txt 2>&1; rc=$?
    VM=$(grep -ao 'socle : [0-9.]*-[0-9]*' $D/$m.txt | head -1 | sed 's/socle : //')
    # ⚠️ SEUL LE BRAS A2 COMPTE DEPUIS LE 20/08. Le bras A du smoke sabotait la TRAVERSE
    # du placeur — un acte retire pour premisse fausse : il ne juge plus rien, et exiger
    # son vert ferait echouer un tampon qui doit certifier LE TIR. Un critere qui compte
    # un bras mort dans son quorum certifie du vide.
    OK=$(grep -c "✓ A2" $D/$m.txt)
    [ "$OK" -ge 1 ] && V=PASSE || V=ECHEC
    # ⛔ le tampon `traverse` est retire le 20/08 : son acte n existe plus (selecteur).
    echo "tir|$VM|$COMMIT|$V|$(date +%Y-%m-%dT%H:%M)" >> $D/TAMPONS.txt
  else
    HMT_SESSION="_6$m" timeout 900 ./.venv/bin/python -u prevol.py 3 $m 45 > $D/$m.txt 2>&1; rc=$?
    VM=$(grep -ao 'socle DU MONDE *: *[0-9.]*-[0-9]*' $D/$m.txt | head -1 | sed 's/.*: *//')
    [ "$rc" = "0" ] && V=PASSE || V=ECHEC
    nom=$m; [ "$m" = "sabotage" ] && nom=munitions
    echo "$nom|$VM|$COMMIT|$V|$(date +%Y-%m-%dT%H:%M)" >> $D/TAMPONS.txt
  fi
  echo "  code $rc" | tee -a $D/JOURNAL.txt
  tail -5 $D/$m.txt | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ TAMPONS ═══" | tee -a $D/JOURNAL.txt
cat $D/TAMPONS.txt | tee -a $D/JOURNAL.txt
echo "═══ TERMINE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
