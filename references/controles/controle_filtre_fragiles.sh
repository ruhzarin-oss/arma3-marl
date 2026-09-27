#!/bin/bash
# Controle du filtre des tests fragiles de portes.sh : meme code, fichiers fabriques.
cd $(mktemp -d); mkdir references; cp $1 references/tests_fragiles_pays.txt; FR=references/tests_fragiles_pays.txt
filtre() { awk -v F="$FR" 'BEGIN { while ((getline l < F) > 0) if (l !~ /^#/ && split(l, a, " ") >= 3) fr[a[2] " " a[3]] = 1 }
                              !(($2 " " $3) in fr)'; }
printf 'ECHOUE  economie          test_credit\nECHOUE  travail           test_inactifs_changent\n' > references/echecs_attendus_pays.txt
juge() { if diff -q <(sort references/echecs_attendus_pays.txt | filtre) <(sort $1 | filtre) >/dev/null; then echo PASSE; else echo ECHOUE; fi; }
printf 'ECHOUE  economie          test_credit\nECHOUE  travail           test_inactifs_changent\n' > a.txt
printf 'ECHOUE  economie          test_credit\nECHOUE  travail           test_inactifs_changent\nECHOUE  justice           test_elucidation_et_effort\n' > b.txt
printf 'ECHOUE  economie          test_credit\nECHOUE  travail           test_inactifs_changent\nECHOUE  justice           test_autre\n' > c.txt
printf 'ECHOUE  economie          test_credit\n' > d.txt
echo "1 memes echecs                       : $(juge a.txt)   ( attendu PASSE )"
echo "2 + un test fragile qui echoue        : $(juge b.txt)   ( attendu PASSE )"
echo "3 + un test NON fragile qui echoue    : $(juge c.txt)  ( attendu ECHOUE : controle positif )"
echo "4 un echec attendu qui ne vient plus  : $(juge d.txt)  ( attendu ECHOUE )"
