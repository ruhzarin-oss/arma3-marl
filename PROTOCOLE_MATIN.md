# PROTOCOLE DE LECTURE DU MATIN — écrit AVANT le lancement de la nuit
31/08/2026, avant le premier épisode. Rien de ce qui suit ne se décide au réveil.

## L'ordre est contraignant : LES TÉMOINS D'ABORD

Au réveil, **avant de regarder la courbe de la politique**, rejouer les deux témoins
à travers le harnais, n = 51 chacun :

```
./.venv/bin/python -u temoins_traversants.py --n 51
```

| témoin | bande exigée | origine |
|---|---|---|
| DOCTRINE | dans [93,0 ; 100] | IC Wilson de la doctrine mesurée sur le banc SQF, n=51 |
| ALÉATOIRE | dans [5,5 ; 23,4] | idem |

**Si un seul témoin sort de sa bande : la nuit est NULLE.** On ne lit pas la courbe, on
ne cite aucun chiffre d'entraînement. Le monde a bougé pendant la nuit — dérive du
serveur, mur de FPS, pont dégradé — et comparer l'agent du matin à un témoin de la veille
serait exactement la faute que le registre du 16/08 a coûté quatre verdicts à réparer.

**Si les deux tiennent : le monde n'a pas bougé, la courbe est lisible.**

## Ce qu'on lit ensuite, et dans quel ordre

1. **Le taux de rejets par lot.** Plus de 10 % sur un lot → ce lot est suspect, on ne
   l'additionne pas. Un pont mort ne doit jamais compter comme un échec.
2. **L'entropie.** Elle part de 2,549 pour un maximum de 2,565. Si elle s'effondre vers 0,
   c'est la condensation — celle qui a coûté le 3,3 % de la graine perdante. C'est le
   sismographe, il se lit avant le score.
3. **La prise par lot de 24.** Et seulement là.

## Les trois issues, écrites d'avance

- **≥ 93,0 % en série 4/5 sur graines neuves, en mode échantillonné** → porte B0@30 passée.
  Palier 60 : contrôle d'alimentation de l'agent chaud (≥ 2 réussites sur 50), puis témoin
  doctrine local, puis entraînement.
- **La courbe monte sans passer la porte** → plus d'épisodes ou un réglage. L'entropie dit
  lequel. Une reprise, **un seul changement nommé à la fois**.
- **La courbe ne bouge pas** → le monde et le banc sont HORS de cause, ils sont certifiés
  par les témoins traversants. La boucle d'apprentissage est l'unique suspect. C'est
  exactement ce que B0 avait pour mission de trancher.

## Ce qui est INTERDIT ce soir

Toucher au runner. Le contrôle 4 certifie `harnais.py` **dans l'état où il a été contrôlé**.
Toute retouche, même bonne, rend l'instrument non contrôlé au moment où il court sans
surveillance. Les améliorations connues — témoin entrelacé toutes les N décisions, époques
de commandes pour refuser les ordres périmés — se posent DEMAIN, de jour, suivies d'un
nouveau contrôle 4.

## Ce que la nuit ne saura PAS faire, et je le nomme

Le stop-loss compte des épisodes, pas la santé du monde. Si le serveur dégrade à 3 h,
l'attribution de récompense dérive et **rien ne le dira avant le matin**. C'est pour ça que
le protocole commence par les témoins : ils sont le seul détecteur a posteriori de cette
panne-là.

## Paramètres du lancement

Barreau B0, palier 30 m, rayon 6 m, budget 20 s, cycle 4 s. Récompense terminale pure.
Décodeur ÉCHANTILLONNÉ. β entropie 0,01. Mise à jour toutes les 24 épisodes. lr 3e-4.
Point de sauvegarde atomique après chaque mise à jour, portant le SHA de la mission.
Stop-loss : 5 000 épisodes sans quitter la bande de l'aléatoire.
Une seule instance Arma vivante, propriétaire unique de la machine.
