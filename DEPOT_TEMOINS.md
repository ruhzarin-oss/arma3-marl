# FAMILLE DE TÉMOINS — déposée AVANT tout calcul, 26/08/2026

⚠️ **Aucun de ces témoins n'a été calculé au moment où ce fichier est écrit.** C'est tout
l'objet : on choisit la FAMILLE avant de rien mesurer, et le maximum choisit tout seul.
⟨Fable : « tu ne choisis pas le témoin : tu choisis la famille avant de rien calculer »⟩

## POURQUOI
J'ai publié le 26/08 un barreau à **AUC 0,7196** (la suppression prédit la mort), puis je l'ai
**retiré** : il portait sur de fausses transitions, produites par un fenêtrage par PLACE. Un
témoin choisi après coup n'est pas un témoin, c'est un décor.

## LA CIBLE, UNE SEULE
**La TRANSITION** : l'entité est vivante au pas k et morte au pas k+1, en la suivant par son
**IDENTIFIANT** à travers les places. Jamais l'état (« est morte »), qui est trivial —
99,98 % des morts en k+1 l'étaient déjà en k, et le témoin « était mort » y fait 0,9998.

## LA FAMILLE FERMÉE — cinq prédicteurs à UN SEUL TRAIT
| # | trait au pas k | colonne |
|---|---|---|
| T1 | **suppression subie** | 9 |
| T2 | **est-vu** (dérivé des arêtes, `aretes[:,4]=vue`, `[:,5]=mesurée`) | arêtes |
| T3 | **distance au plus proche ennemi** | 1,2 (x,y) + 5 (camp) |
| T4 | **sous le feu récemment** (tir dirigé sur lui dans les N derniers pas) | arêtes / 6 |
| T5 | **immobile contre en mouvement** (norme du déplacement k−1→k) | 1,2 |

Plus deux témoins de plancher, obligatoires : **le hasard** et **« était mort en k »**.

## LE BARREAU
**Le barreau est le MAXIMUM de la famille**, publié avec son **n de positifs**. Tout modèle se
publie contre ce maximum, **jamais contre le témoin qui l'arrange**.

## LES TROIS PORTES, ÉTAGÉES ⟨Fable⟩
**BASSE** — battre le barreau sur la transition, sur journaux tenus à l'écart, avec le n.

**MOYENNE — la vraie porte, et je ne l'avais pas vue.** Le modèle doit **RETROUVER, sans
qu'on les lui montre, les tarifs qu'Arma a déjà avoués indépendamment** : risque ordonné
**vu > non-vu**, **supprimé > non-supprimé**, et l'écart **×2** d'être vu (mesuré sur 563 000
observations). Mesuré en **strates**, sur journaux tenus à l'écart.
> *Un modèle qui prédit la transition mais ordonne mal ces facteurs n'a rien compris
> d'actionnable.*

**D'ADOPTION — plus tard, elle attend son monde.** Le classement de comportements en déroulé
interne. Un corpus **passif** ne permet pas de dérouler des doctrines : il faut un banc
**interventionnel** Arma. Deux portes avant d'adopter — la troisième attendra.

## CE QUI EST INTERDIT À PARTIR DE MAINTENANT
1. **Entraîner quoi que ce soit avant que ce fichier soit haché.** La séduction de la perte
   qui descend est ce qui m'a fait publier le 0,7196.
2. **Ajouter un témoin après avoir vu les chiffres.** La famille est fermée. Si un sixième
   trait paraît évident plus tard, il fera l'objet d'un amendement daté, et le barreau
   d'origine restera publié à côté.
3. **Citer une AUC sans son n de positifs.** À 0,0113 % de taux de base côté places, la
   question du n n'est pas une coquetterie.
