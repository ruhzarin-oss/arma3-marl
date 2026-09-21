#!/bin/bash
# Chaine complete de l equation P2 : jeu A en validation croisee, formule finale, puis jeu B. Aucune lecture ici.
cd /mnt/data/hmt/depot
L=/mnt/data/hmt/equation/p2/chaine.log
echo "DEBUT $(date '+%F %T')" > $L
/mnt/data/hmt/evogp/env/bin/python oracle/ajuster_equation_p2.py --jeu A 2>&1 | grep -v -E "Generation limit|OptimizeWarning|opt_res" >> $L
echo "A_FINI $(date '+%F %T')" >> $L
/mnt/data/hmt/evogp/env/bin/python oracle/formule_finale_p2.py 2>&1 | grep -v -E "Generation limit|OptimizeWarning|opt_res" >> $L
echo "FINALE_FINIE $(date '+%F %T')" >> $L
/mnt/data/hmt/evogp/env/bin/python oracle/ajuster_equation_p2.py --jeu B 2>&1 | grep -v -E "Generation limit|OptimizeWarning|opt_res" >> $L
echo "B_FINI $(date '+%F %T')" >> $L
echo "TOUT_FINI" >> $L
