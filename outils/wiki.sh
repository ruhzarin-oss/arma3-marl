#!/bin/bash
# Regenere le wiki de Plane depuis le registre. Appele par run.sh a la fin d'un run
# et par la boucle de HMT_ETAT. Deux etages : construire dans WSL, publier dans le conteneur.
H=/mnt/data/hmt
[ -f $H/.temoin ] || exit 3
docker ps --format '{{.Names}}' 2>/dev/null | grep -q plane-app-api-1 || { echo "$(date -Is) Plane eteint, wiki non regenere"; exit 0; }
python3 $H/depot/outils/journal.py || exit 1
docker cp $H/etat/journal_colis.json plane-app-api-1:/tmp/journal_colis.json >/dev/null
docker cp $H/depot/outils/pousser_journal.py plane-app-api-1:/tmp/pousser_journal.py >/dev/null
S=$(docker exec plane-app-api-1 sh -c 'python manage.py shell -c "exec(open(\"/tmp/pousser_journal.py\").read())"' 2>&1 | grep -v "objects imported")
echo "$S"
echo "$S" | grep '^POUSSE ' | awk '{print $2}' >> $H/etat/journal_vus.txt
