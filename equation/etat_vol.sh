#!/bin/bash
echo "ETAT $(ls /mnt/data/hmt/queue/en_cours/ 2>/dev/null | wc -l) $(ls /mnt/data/hmt/queue/*.json 2>/dev/null | wc -l) $(ls /mnt/data/hmt/equation/boucle/STOP /mnt/data/hmt/equation/boucle/FIN 2>/dev/null | wc -l)"
