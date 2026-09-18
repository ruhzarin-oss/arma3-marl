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

---

## Amendement 1 — 18/09/2026, après lecture des causes (écrit avant tout nouveau calcul)

**La campagne `PRIX-DU-TEMPS-18-09` (v1) est déclarée NULLE.** Elle n'a pas mesuré le prix du temps, elle a mesuré une
dérive de l'instrument. Deux fautes, l'une de montage, l'autre de critère.

### a. La faute de montage

Faire attendre un détachement sans lui donner d'ordre ne le laisse pas immobile : l'IA reprend son mouvement
précédent. Mesuré homme par homme sur les épisodes de la v1 :

| attente | déplacement pendant l'attente | assaut à sa place au début de la phase 5 | issue |
|---|---|---|---|
| 0 s | — | 16 / 16 | 62 % de 3 charges |
| 600 s | 6 à 7 hommes marchent **818 m** | 0 / 16, à **327–672 m** de leur place | **6 %** de 3 charges, 14 abandons `ARTICULATION_ROMPUE` |
| 1200 s | les mêmes hommes sont **revenus** (0–30 m) | 9 / 16 | 62 % de 3 charges |

Pendant ces attentes : `alarme 0`, `compromis 0`, **10 vivants sur 10** dans 14 cas sur 16. L'ennemi n'y est pour rien.
Le creux à 600 s n'est pas un coût du temps, c'est la photographie du détachement au bout de sa promenade.

**Correctif (`menace/patch_prix_temps_v2.py`)** : pendant l'attente, chaque homme est figé (`doStop` + `PATH` coupé),
puis rendu à lui-même (`PATH` + `doFollow`). L'appui déjà fixé par `CHACAL_APPUI_FIXE` n'est pas touché. La **dérive
maximale** est écrite dans la ligne `attente_test|…|fin|…|derive|N`.

### b. La faute de critère

L'issue primaire de la v1, `exfil_reussie` (au moins 6 exfiltrés), **récompense les épisodes où l'assaut n'a jamais eu
lieu** : à 600 s elle monte à 88 % précisément parce que le détachement a renoncé et est rentré. Un critère de succès
doit pouvoir être manqué en renonçant.

**Nouvelle issue primaire : `mission_reussie` = 3 charges posées ET au moins 6 exfiltrés.** Les deux moitiés restent
lues séparément, à titre descriptif.

### c. Contrôles d'instrument, écrits avant les épisodes

La lecture est **nulle** si l'un de ces trois contrôles échoue — la mesure doit savoir échouer :

1. **Dérive** : `derive` ≤ 30 m dans au moins 95 % des épisodes qui attendent.
2. **Dispositif** : l'assaut est à sa place au début de la phase 5 dans au moins 80 % des épisodes, **dans chaque bras**.
3. **Renoncement** : moins de 20 % d'abandons `ARTICULATION_ROMPUE`, **dans chaque bras**.

Le contrôle 2 est le contrôle positif du test : si le bras à 0 s et le bras à 1200 s ne partent pas du même dispositif,
l'écart mesuré ne porte pas sur le temps.

### d. Ce qui ne change pas

La question, le levier, les 8 mondes, les 48 épisodes, la règle de décision (± 10 points, IC 95 % par
rééchantillonnage des mondes, graine 20260918), le falsificateur, et ce qu'on en fait. Nouvelle campagne :
`PRIX-DU-TEMPS-V2-18-09`.
