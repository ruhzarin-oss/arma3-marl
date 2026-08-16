> ⚠️ **SURSITAIRE le 16/08/2026** — mesure prise sur des hommes désarmés (`combatMode "BLUE"`).
> La grandeur n'en dépend pas directement, mais la trajectoire d'un homme qui ne riposte pas
> n'est pas celle d'un homme qui combat. **Non citable** avant refonte sous socle 1.2.0.
> Voir `REGISTRE_BLUE.md`.

# VERDICT — l'exposition est CHOISIE, pas subie. L'hypothèse de Fable est réfutée.

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_SUBIE.md` (`405f92c`).
**Première application de la règle 18** : les quatre cas fabriqués sont passés avant de
toucher aux données — chaque bande s'est montrée atteignable ET rejetable.

## Le résultat

| | P(exposé \| couvert À PORTÉE) | part forcée | exposition totale |
|---|---|---|---|
| **GYMNASE** | **0,232** | 51,8 % | 21,6 % |
| **ARMA** (corps réparé) | **0,727** | 85,0 % | 55,3 % |

**Rapport = 3,13** — au-delà du seuil de 1,4 déposé. **Lecture : CHOISIE.**

Les deux contrôles positifs passent (≥ 100 pas dans chaque situation ; `los` sépare
des deux côtés).

## Ce que ça réfute

Fable proposait que l'exposition d'Arma soit **subie** — du transit entre couverts rares —
en s'appuyant sur un paradoxe réel : le gymnase surfacture l'exposition ×2, donc la
politique transférée devrait y être **trop prudente**, et elle s'expose 2,5 fois plus.

**C'est faux.** Quand le couvert est à une cellule — donc atteignable en un pas — l'agent
s'expose **73 % du temps sur Arma contre 23 % au gymnase**. Il ne manque pas d'abri à ce
moment-là : il ne s'en sert pas.

Les deux faits coexistent : le couvert **manque** (85 % de l'exposition d'Arma est sans
alternative contre 52 %) **et** celui qui est là **n'est pas employé**. Le critère déposé
tranche sur le second.

## ⚠️ CE QUE CE VERDICT N'ÉTABLIT PAS — et la limite est dans le critère lui-même

**La comparaison n'est pas contrôlée.** Conditionner sur `dcover ≤ 0,033` ne fige pas les
onze autres colonnes. Les pas « couvert à portée » d'Arma diffèrent de ceux du gymnase sur
la distance à l'ennemi, la position, la pente — et la politique répond au **vecteur entier**,
pas à `dcover` seul.

Donc « l'agent se conduit autrement quand il a le choix » **confond le comportement et la
situation**. Le verdict est celui du critère déposé ; il ne prouve pas que la politique
elle-même décide différemment.

Cette limite était **dans ma bande dès l'écriture** : je ne la découvre pas après coup, je
constate que je ne l'avais pas fermée. La règle 18 vérifie qu'une porte peut passer et
échouer — **elle ne vérifie pas qu'elle mesure une chose non confondue.**

## Une piste que ce résultat ouvre, non mesurée

Le `cover` du gymnase est un masque de pente qui **réduit les dégâts de 70 %**. Rien ne dit
qu'il **masque la vue**. Sur Arma, se tenir sur une cellule pentue ne cache pas davantage.
Si le couvert du gymnase protège sans cacher, un agent qui l'occupe reste « exposé » au sens
de `los` dans les deux mondes — et la question redevient : que fait exactement le couvert,
de chaque côté.

**Non déposée, non mesurée.** Elle s'écrira avant d'être lue.

## Ce qui reste vrai

L'hypothèse **A (disponibilité)** n'est toujours pas établie proprement — Fable l'a dit :
« temps passé près du couvert » mélange la carte et la politique. Sa mesure géométrique,
sur la carte seule, reste à faire.
