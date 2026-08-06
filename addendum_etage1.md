
---

## Addendum — LA TAILLE DE LA PORTE, exigée par Fable et absente de la première version

*6 août, avant tout lancement. Ce fichier avait un critère de mort ; il n'avait pas sa
sensibilité. Une porte sans ce chiffre n'est pas une porte.*

Le plan initial disait : « succès = +1 palier au moins sur **2 graines sur 3** ». J'ai calculé
ce que ce dispositif sait voir, et **il ne sait pas voir grand-chose**.

Le palier est une échelle à barreaux (60, 80, 95, 110, 125, 140 m). D'une graine à l'autre,
sans aucun effet réel, il arrive qu'une graine gagne un barreau par simple chance de tirage —
disons une fois sur trois, ce qui est l'ordre de grandeur observé sur les runs précédents.

> Alors « 2 graines sur 3 » se produit **par hasard une fois sur cinq environ**.
> Une porte qui s'ouvre toute seule 20 % du temps ne prouve rien.

**Le dispositif est donc corrigé AVANT le lancement, et sur ce seul motif :**

- **5 graines**, pas 3 ;
- **succès = +1 palier au moins sur 4 graines sur 5.**

Avec la même chance de gain fortuit, ce seuil ne s'atteint tout seul qu'environ **3 fois sur
100**. C'est une porte.

⟨coût : cinq curriculums au lieu de trois. Ils tiennent dans la journée et la nuit sur une
3090 libre, et le goulot de cette machine est le CPU, pas le GPU.⟩

### Ce que la porte ne saura pas voir, et qu'on ne prétendra pas

Un gain **inférieur à un barreau** — un agent qui arrive un peu mieux au même palier — est
**invisible** à ce dispositif. Si le champ de risque améliore la marge sans franchir le
barreau suivant, on lira « pas d'effet », et ce sera faux. C'est le prix d'une métrique en
escalier, et il est accepté ici parce que la question posée est un franchissement, pas un
raffinement.

> En conséquence : un ÉCHEC de l'étage 1 se rapportera comme **« pas de franchissement »**,
> jamais comme « le champ n'apporte rien ».

### Le placebo garde le même barème

Le contrôle C1 (huit nombres de bruit) est jugé **au même seuil, sur les mêmes 5 graines**. Si
le placebo passe aussi, c'est la taille du réseau qui paie, et le résultat tombe — quel que
soit le score du vrai champ.
