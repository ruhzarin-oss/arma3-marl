# GESTE N°3 — PRISE DE COUVERT SOUS LE FEU. Critères déposés avant toute mesure.

*8 août 2026, 20 h 45. Aucun accrochage n'a encore été joué sur ce geste.*

**Fiches relues ⟨règle 10⟩** : `courbe1-toucher-mesuree`, `etre-vu-tue-deux-fois-plus`,
`posture-couche-est-observation`, `arma-cover-envelope`, `arc-tir-sursis-mesure`,
`mesure-doit-savoir-echouer`, `accord-sur-zero-nest-pas-accord`.

## Le fait certifié qu'il exploite

Le toucher tombe de **75 % à 26 %** de 25 à 200 m, et le couvert **coupe la vue** — l'enveloppe
de couvert d'Arma a été relevée à 12 rayons ⟨`soldier_shell.pt`, +97⟩. Être vu tue **2× plus
fort**, et l'effet **croît** avec la distance.

## Le dispositif

Une traversée de **3-4 cases majoritairement ouvertes** vers un couvert d'arrivée.

⚠️ **L'objectif n'a PAS besoin de bâti dense ici.** Les 81 agrégats de Stratis sont trop rares
pour être dépensés là où ils ne servent pas.

**Le sel est SOUS le pas de la carte.** Les masques utiles sont à **10-20 m du trajet** —
invisibles à 50 m de résolution. D'où **deux étages de filtre** :

1. **étage carte** (fait) : couloir ouvert vers un couvert, avec des cases masquées
   **adjacentes** — la promesse qu'il y a de la matière à côté du chemin ;
2. **étage géomètre, en jeu** (à faire, obligatoire) : mesurer les objets **réels** à moins de
   15 m de la ligne de marche. **Sans ce second étage, on certifierait des lieux où le geste est
   physiquement impossible** — et on lirait « l'agent n'a pas appris » là où il n'y avait rien
   à faire.

**Professeur** : l'équipe avance debout ; **au premier tir proche** — détecté par le projectile,
pas par le dégât ⟨`HitPart`, jamais `HandleDamage`⟩ — chaque homme rejoint le masque le plus
proche sous 30 m et se couche ; reprise **10 s après la dernière balle**.

**Témoin** : continuer debout, droit, sans halte.

## La grandeur, et les deux portes

**Grandeur jugée : LES PERTES** — survie de l'équipe à la traversée. L'arrivée est relevée en
second, et ne décide pas.

| ce qu'on juge | porte | pourquoi cette taille |
|---|---|---|
| **le LIEU** (professeur vs témoin, scriptés) | **≥ 10 points** | un lieu qui sépare à peine ferait un tribunal faible |
| **l'AGENT** (élève vs professeur) | **≥ 5 points** | le tiers du plus petit effet certifié du dossier |

## Le feu à mi-course — la ligne entre l'injection légitime et la triche

Le feu doit partir **à mi-parcours**, sinon la traversée n'a pas de milieu et le geste n'a pas
de sens. On l'obtient par un **lâcher contrôlé** : défenseurs en `holdFire` jusqu'au
franchissement de la mi-ligne, puis libérés.

> **Ce n'est pas fabriquer la réponse, et voici le critère qui les sépare** ⟨Fable, 08/08⟩ : le
> déclencheur est **identique aux deux bras, aveugle au bras, écrit avant, dans l'empreinte** ;
> il fixe **QUAND** le feu commence, **jamais COMMENT** il se comporte ensuite. La triche serait
> un déclencheur qui **lit le comportement** et **diffère** entre bras.

Le tribunal a besoin de reproductible plus que de naturel. Le naturel, Arma le fournit après la
première balle.

## Contrôles obligatoires

- **PORTE 0 du lieu** : les deux doctrines dans la bande **20-80 %** de survie, au point de
  fonctionnement du jugement ⟨l'aiguille au butoir⟩ ;
- **contrôle du déclencheur** : la distance parcourue au premier coup de feu doit être la
  **même distribution** dans les deux bras. Si elle diffère, le lâcher n'est plus aveugle et
  le verdict ne vaut rien ;
- **contrôle négatif** : les mêmes bras sur des traversées quelconques ne doivent **pas** séparer ;
- **bras contemporains**, empreinte du monde, journal de santé, filtre au dépouillement ;
- **écart de 500 m minimum entre lieux retenus**.

## Ce qui la ferait échouer — écrit maintenant

- **Le géomètre ne trouve pas de masques réels à moins de 15 m** sur les couloirs retenus : les
  lieux sont invalides, pas le geste. On rechasse, ou on change d'île.
- **La distance au premier coup diffère entre bras** : le lâcher a fui, on jette le run.
- **Le témoin survit autant** : à cette distance et sous ce feu, s'arrêter ne paie pas — et
  c'est un résultat, pas un échec. On le dit et le geste sort du répertoire.
- **Les deux bras dans le butoir** (tout le monde meurt, ou personne) : le banc ne mesure rien.
