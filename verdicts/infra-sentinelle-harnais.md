porte: Infrastructure de mesure : sentinelle de pont, harnais de banc, deploiement SQF depuis git
date: 2026-09-04
graines: n/a
chiffre: trois outils en service ; une panne trouvee et non reparee : la couche bronze du lac est un lien mort
verdict: PASSE
depend_de: 
remplace_par: 
source: Plane HMT-17

Trois outils rendent les mesures reprenables : une sentinelle de pont relevee par tache planifiee et qui n'utilise JAMAIS pkill, un harnais de banc a controle positif en bloc zero avec bronze par episode et resynchronisation par marqueur apres la mort du pont, et un deployeur de SQF depuis git avec empreinte et garde contre l'edition manuelle.
Panne trouvee au passage : la couche bronze du lac est un lien symbolique vers un disque qui n'est plus monte. Tout ce qui y ecrit echoue, ou pire ecrirait en silence sur le disque systeme.
Elle n'est pas reparee a dessein : c'est l'architecture de donnees de Younes, a lui de trancher entre remonter le disque et repointer le lien.
Ce que ca n'etablit pas : la qualite des mesures produites, seulement qu'elles sont reprenables et deployees depuis une source unique.
