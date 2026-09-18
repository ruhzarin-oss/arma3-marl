# Critères pré-enregistrés — le prix du temps

*18/09/2026, 12 h. Test indépendant demandé par Younes après la saisine de Fable (`SAISINE_FORME_DE_LA_REGLE.md`,
3262dba). Écrit et commité avant le premier épisode. Une seule lecture, à la fin.*

## La question

La forme proposée par Fable, `Δ = α − β·ln(τ) + γ·s`, repose sur **τ = surcoût en temps / temps restant**. Elle n'a de
sens que si **le temps a un prix** dans notre monde. Or la lecture du code ne montre **aucune échéance de mission** :
le succès est « 3 charges posées et au moins 60 % d'exfiltrés », sans terme de temps. Les seuls coûts possibles du
temps sont indirects : patrouilles qui tournent, alarme, renfort.

**Question : une attente imposée, prise en dehors de tout plafond de phase, fait-elle baisser la réussite ?**

## Le dispositif

- Vignette `d4a6` (assaut puis exfiltration), sans menace de phase, exactement le gabarit de CHOIX-P6-17-09.
- Levier `CHACAL_ATTENTE_TEST` : le détachement attend **0, 600 ou 1200 secondes avant le début de la phase 5**.
  L'attente est prise **avant** `debutPhase`, donc elle ne mange aucun plafond : le seul coût possible est celui du
  monde qui tourne.
- 3 attentes × 8 mondes (paires 4-5, 6-7, 8-9, 11-12) × 2 répétitions = **48 épisodes**, 12 jobs.
- Issue primaire : **`exfil_reussie`** (au moins 6 exfiltrés). Secondaires, descriptives : charges posées, vivants en
  fin de phase 5, alarme au début de la phase 5, compromission, durée totale.

## Les critères

- **Le temps a un prix** si la réussite baisse de plus de 10 points entre 0 s et 1200 s, avec un IC 95 % (par
  rééchantillonnage des mondes, graine 20260918) qui exclut zéro.
- **Le temps est gratuit** si l'écart entre 0 s et 1200 s a un IC contenu dans ±10 points.
- **Indécis** sinon, et il faudra doubler les répétitions.

## Ce qu'on en fait, écrit d'avance

- **S'il est gratuit** : le rapport τ de la forme de Fable n'est pas identifiable dans ce monde. Deux issues possibles,
  à trancher par Younes : introduire une vraie échéance (aube, renfort au bout de N minutes, fenêtre d'extraction), ou
  abandonner l'axe du temps et chercher l'inversion ailleurs (portée de perception, effectif).
- **S'il a un prix** : on mesure la pente entre 0, 600 et 1200 s, et cette pente donne l'ordre de grandeur de β avant
  de lancer les 480 épisodes de la campagne d'inversion.

## Falsificateur

« Si une attente de 20 minutes ne fait pas baisser la réussite de plus de 10 points, alors le temps n'a pas de prix
mesurable dans ce monde, et aucune règle ne peut y apprendre à l'économiser. »
