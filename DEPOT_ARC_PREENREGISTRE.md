# L'ARC — dépôt pré-enregistré. Écrit AVANT de toucher au code.

*12 août 2026, monde neuf. ⟨Fable⟩ « La tentative unique est un dépôt pré-enregistré avant de
toucher au code : schéma d'observation avec empreinte, budget de graines et de pas, bras de
référence à graines égales, grandeur, seuil, lecture, contrôles, et la clause d'échec nommant
ce qui se redépose. Toute retouche après première lecture consomme la tentative. »*

## POURQUOI L'ARC, ET RIEN D'AUTRE

L'agent perd contre une doctrine de flanc écrite à la main. Le flanc ne paie que pour une raison
mesurée : le défenseur a un **arc de tir**, et le contourner achète un **sursis de 4 secondes** —
le cône ne pivote pas, il s'ouvre. Certifié : **18 repérages sur 18 dans le cône contre 0 sur 26
hors.** Aucune des douze entrées ne porte cette information : l'agent ne peut pas *représenter*
la raison pour laquelle le flanc marche.

⚠️ **Ce n'est pas un réglage de récompense. C'est une perception certifiée qu'on lui rend.**

## LE SCHÉMA D'OBSERVATION — figé ici

**14 colonnes**, dans cet ordre exact :

```
0..8    base 9    apx/S, apy/S, dgx, dgy, alive, slope, dcover, los, nd
9..10   ARC 2     sin et cos de l'angle entre la FACE du défenseur le plus proche
                  et la direction sous laquelle il me voit
                  (0 = il me regarde en face · ±π = je suis dans son dos)
11..13  posture 3 one-hot debout / accroupi / couché
```

**Empreinte du schéma** : `base9+arc2+posture3` — à journaliser au démarrage, et à vérifier au
chargement de la politique. Une politique dont le schéma ne correspond pas **refuse de se
charger** ; c'est une panne bruyante, pas une incohérence silencieuse ⟨la leçon du 13/12/12⟩.

**Côté Arma** : la couture produit ces deux colonnes en fin de vecteur (positions 18-19 de ses
20), donc **aucun indice existant ne bouge**. Le portage les remet en position 9-10.

## LE BUDGET — figé ici

- **800 itérations de 256 épisodes**, identiques au bras de référence.
- **Graines d'entraînement** : 11 à 18. **Graines de lecture** : 101 à 106, jamais vues.
- **Une seule graine de réseau** : `torch.manual_seed(0)`.
- **Aucune reprise, aucun redémarrage** : le run va au bout ou il ne compte pas.

## LE BRAS DE RÉFÉRENCE — à graines égales

Le **même monde neuf, arc éteint**, mêmes graines, même budget, entraîné **dans le même run**.
⚠️ **Le 53,3 % de l'ancien monde ne sert PAS de référence** : il est d'un autre monde, il est
partiel. La référence se remesure ici.

## LA GRANDEUR, LE SEUIL, LA LECTURE

- **Grandeur** : le taux de **prise**, sur graines jamais vues.
- **Seuil** : l'arc doit rendre **≥ 5 points** de prise au-dessus du bras sans arc.
  **Dérivé** : c'est la porte du geste ⟨cahier du répertoire, Fable 07/08⟩ — *« le tiers du plus
  petit effet certifié ; en dessous, même vrai, l'effet ne changerait le rang d'aucun levier »*.
  Deux colonnes qui ne déplacent aucun levier ne valent pas d'être portées jusqu'à Arma.
- **Lecture** : **sur la BORNE inférieure** de l'intervalle à 95 % de l'écart apparié par graine.
  Cher et asymétrique ⟨règle 14⟩ : garder deux entrées inutiles alourdit tout ce qui suit, et
  les rendre transportables coûte une couture de plus.

## LES CONTRÔLES — lus avant la grandeur

1. **Les deux colonnes VIVENT** — écart-type non nul sur une traversée entière, des deux côtés,
   gymnase **et** Arma ⟨`releve_traversee.py`⟩. Une colonne morte ne se juge pas.
2. **CONTRÔLE NUL** : deux colonnes de **bruit**, mêmes graines, ne doivent PAS passer le seuil.
   Si elles passent, c'est le banc qui donne la victoire, pas l'arc.
3. **Aiguille dans la bande 20-80 %** sur la prise, pour les deux bras.
4. **Anti-planque** : l'agent avec arc doit gagner **autant de mètres** que celui sans.

## LA CLAUSE D'ÉCHEC — ce qui se redépose

- **Le seuil de 5 points n'est pas atteint** → l'arc n'était pas la pièce manquante. **On
  n'ajoute pas une treizième idée à la perception.** C'est **l'algorithme** qui se redépose —
  la politique par gradient sur retours à rebours, remplacée par ce que Fable jugera.
- **Le contrôle nul passe** → le banc est trop facile, aucune lecture ce jour-là.
- **Une colonne d'arc est morte sur Arma** → c'est la couture qui se répare, et **la tentative
  n'est pas consommée** : on n'a rien mesuré.

⚠️ **Toute retouche après la première lecture consomme la tentative.** Une seule.
