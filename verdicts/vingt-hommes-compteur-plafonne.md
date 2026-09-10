porte: A 20 hommes contre 5, l'issue n'est pas jugeable : le compteur d'exfiltration s'arrete a 6
date: 2026-09-10
graines: 7, 8
chiffre: 2 episodes acceptes, 3 charges sur 3 et 17 vivants dans LES DEUX ; tous deux juges EXFIL_MANQUEE avec exfiltres = 6 exactement, pour un seuil de 12 (0,6 x 20)
verdict: OUVERT
depend_de: plan-de-positions-sans-plan-de-feu
remplace_par: 
source: run 2026-09-09_1615_chacal, instance 3 ; code 60_phases.sqf, phase 6

Cause lue dans le code. La phase 6 attend « au moins 6 vivants a moins de 90 m du point d'exfiltration », avec 6 ecrit en dur. Des que le sixieme arrive, la phase se ferme et le compteur est fige. Le verdict, lui, exige 0,6 x effectif, soit 12 a vingt hommes. Un episode a vingt ne peut donc JAMAIS etre un succes.
A dix hommes, 6 = 0,6 x 10 et rien ne change. MAIS la colonne « exfiltres » de TOUS les runs CHACAL est un seuil atteint, pas un compte : elle vaut 6 meme quand 10 hommes rentrent.
Ce que les deux episodes montrent quand meme : les trois charges posees les deux fois, 17 hommes vivants sur 20, 2 et 4 defenseurs tues. A dix hommes, les trois charges ne sont posees que 4 fois sur 8.
Correction preparee : depot/correctifs/2026-09-10_exfil_suit_effectif.py, le seuil suit l'effectif (identique a dix hommes). Rejeu V20b programme derriere, qui sert aussi d'episode de controle pour la journalisation de TENIR et ARRET.
Rappel de Fable : a vingt hommes on gagne par attrition. Ce run reste un CONTROLE, pas un geste a retenir dans le corpus.
