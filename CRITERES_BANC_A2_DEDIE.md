# Banc A2 dédié — le contrôle positif doit pouvoir REFUSER

*6 août 2026, 02h30. Critères déposés AVANT de lancer. Aucun score n a été lu.*

## Pourquoi ce banc existe

Deux corpus indépendants donnent le même écart sur la TENUE : **+17,3 pts (p = 0,012)** puis
**+15,0 pts (p = 0,024)**, avec **zéro écart sur l élimination** les deux fois. Le fait est
reproduit.

Mais la porte A2 — le contrôle positif — n a jamais pu se fermer :

| | effectif | écart | p |
|---|---|---|---|
| corpus n°1 | 18 configs | +16,7 % | 0,278 |
| réplication | 31 configs | **−8,3 %** | 0,609 |

Elle a pointé dans un sens, puis dans l autre, jamais significativement. **Une porte qui ne
peut pas se fermer n est pas une porte.** À 20 % du tirage, A2 était une décoration.

Sur le corpus n°1 j avais argumenté qu elle était sous-dimensionnée *mais pointait dans le
bon sens*. Cet argument est mort à la réplication. On ne le rejoue pas : **on dimensionne la
porte pour de bon**, et on la laisse refuser si elle veut refuser.

## Ce que le banc mesure

**100 % de configurations figées**, deux bras à 50/50. Rien d autre ne change : même monde,
même charge (6 accrochages simultanés), même rapport de force (1,5-3,0), mêmes journaux.

En mode figé, les défenseurs gardent le cap `_az1` — l axe frontal — pendant tout
l accrochage. Leur compétence, leur armement et leur garnison sont **intacts** : seul le cap
est tenu, et il est journalisé (`HMT|G|FIGE`) pour qu on puisse le vérifier après coup.

Un second axe arrive alors **hors de leur cône tenu**. Or l angle mort d Arma est binaire par
orientation : 18/18 détectés dans le cône, 0/26 hors. **Si le deux-axes n écrase pas ICI, ce
banc ne peut rien juger du tout.**

## La métrique et le seuil

**PRIMAIRE — la TENUE**, exactement la même grandeur que l A/B, sans retouche.

> **Le banc passe si l écart est >= +10 points avec p < 0,05.**

L effectif est dimensionné pour ça : à ~1 accrochage clos par minute, on juge **une seule
fois**, au premier de ces termes :

- **>= 120 accrochages clos par bras** (240 au total, ~4 h) ;
- **ou 09h00** le 6 août.

Si à ce terme la TENUE compte moins de 30 événements au total, la primaire est illisible et
on le dit tel quel.

## Contrôle de PRÉSENCE — la manipulation a-t-elle vraiment eu lieu ?

Le journal `HMT|G|FIGE` doit apparaître pour **>= 95 %** des accrochages, avec un cap
non nul et un effectif de défenseurs cohérent.

> Sous ce seuil, on n a pas mesuré un contrôle positif : on a mesuré un `setDir` qui ne
> prenait pas. Aucune conclusion, ni dans un sens ni dans l autre.

## Témoin de mécanisme — choisi DANS les données

**La part d hommes vus par axe** (journal `SU`, `knowsAbout` > 0). C est la grandeur qui a
déjà ordonné correctement la détection en cascade — 31/60 contre 51/60.

> En figé, l axe `_az2` doit être **vu moins** que l axe `_az1`.

Si l écart de tenue apparaît **sans** cet écart de détection, on garde le chiffre et on écrit
« ça marche, on ne sait pas pourquoi ». On ne raconte pas d histoire.

⟨la faute du 27/07 : un témoin choisi dans l intuition — « temps passé dans l angle mort » —
montait pendant que l exposition chutait de 28 %. Je savais QUE, pas COMMENT.⟩

## Ce qui la ferait échouer — écrit maintenant

- **Écart < +10 points, ou signe inversé.** Alors le banc ne sépare pas deux axes d un seul
  même quand les défenseurs sont structurellement aveuglés. **Ce n est pas l agent qui est en
  cause : c est l instrument.** Et les +17,3 et +15,0 deviennent illisibles sur ce banc —
  observations d un dispositif qui ne discrimine pas, pas verdicts.
- **La présence cède (< 95 %).** Rien n est conclu ; on répare le `setDir` et on recommence.
- **La primaire passe mais le témoin ne suit pas.** On garde le gain, sans récit.

C est le résultat le plus utile que cette nuit puisse rendre, y compris — et surtout — s il
démolit les deux corpus précédents. Un banc qui ne peut pas refuser n a jamais rien prouvé.

---

## Aveu : j ai vu 24 accrochages avant l heure

*05h05.* Pour valider le dépouilleur `juger_a2.py` je l ai fait tourner sur le journal vif —
24 accrochages, soit un dixième de la cible. **C était de la plomberie, pas une lecture.**
Je le consigne parce que taire un coup d oeil est pire que l avoir donné.

Ce que ça ne change pas : la règle d arrêt et les seuils, qui restent ceux déposés plus haut.
Le jugement reste **unique**, à 09h00 ou à 120 accrochages par bras.

Ce que ça a montré, et qui est une PISTE, pas un résultat : le témoin de mécanisme pointe
**à l envers**. L axe hors du cône tenu est vu *davantage* (61 %) que l axe fixé (49 %).

Si ça se confirme sur l effectif complet, l explication est déjà dans le dossier :
**`knowsAbout` est une grandeur de CAMP, pas de soldat.** Figer le cap de chaque défenseur
ne peut alors pas les aveugler — le camp continue de savoir. Ce qui voudrait dire que le
« contrôle positif » n a jamais contrôlé quoi que ce soit, et que sa faillite depuis deux
corpus n est pas du bruit mais une **impossibilité de construction**.

À trancher à 09h00, pas maintenant.
