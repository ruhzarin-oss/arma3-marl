"""HMT-176 ( 30/09, session Classes ; a relire par le moteur ) : les vivres du menage, les enfants d abord, et le crochet des
repas pris dehors ( HMT-177, Bibliotheque ). Un seul fichier touche : monde/monde.py ( Monde.repas, Monde.repas_python,
une fonction pure du partage, Monde.manger_dehors ). Ancres COURTES, propres au repas ; idempotent.
   python patch_vivres_enfants.py <arbre>          ( <arbre>/monde/monde.py )
Sans manque, sans mineur ou sans adulte, et sans repas pris dehors, le monde est identique au bit a l ancien partage egal."""
import os, sys

ARBRE = sys.argv[1]
F = os.path.join(ARBRE, "monde", "monde.py")
s = open(F).read()
if "def partager_le_manque(" in s: print("deja :", F); sys.exit(0)


def remplacer(ancien, nouveau):
    global s
    assert s.count(ancien) == 1, ("ancre introuvable ou multiple", ancien[:70], s.count(ancien))
    s = s.replace(ancien, nouveau, 1)


# 1. la fonction pure du partage, avant la premiere classe du module
remplacer('''
class ParMenage:''', '''
# HMT-176 ( 30/09 ) : les vivres du menage, LES ENFANTS D ABORD. Quand le garde-manger ne couvre pas tout le monde, les
# adultes se privent d abord ( le « tampon parental » ) : USDA ERS, Household Food Security in the United States in 2023
# ( ERR-337, Rabbitt et al. 2024 ) - menages avec enfants de 0 a 17 ans : insecurite des adultes seuls 9,0 %, des enfants
# 8,9 % ; insecurite TRES grave du menage 5,4 % contre 1,0 % chez les enfants ( « Children are usually shielded from the
# disrupted eating patterns and reduced food intake that characterize very low food security » ) ; McIntyre et al. 2003
# ( CMAJ 168 : 686 ) : les meres seules pauvres ont des apports insuffisants, leurs enfants des apports adequats.
# CHOIX ( non sources, a trancher par Younes ) : tous les mineurs a egalite ( pas les plus jeunes d abord ) ; les adultes
# a egalite entre eux ; tampon TOTAL ( un adulte cede sa ration entiere avant qu un mineur manque ).
AGE_MINEUR = 18.0           # moins de 18 ans ( USDA : enfants de 0 a 17 ans ; convention des droits de l enfant, art. 1 )
TOLERANCE_MANQUE = 1e-6     # la tolerance du repas, en rations par menage : un manque plus petit n est pas un manque


def partager_le_manque(manque, part, mineur, k, M):
    """HMT-176 : le manque de CHAQUE membre, en colonnes. La SEULE ecriture du partage : Monde.repas ( colonnes ) et
    Monde.repas_python ( boucle ) l appellent. Fonction pure : aucun tirage, aucun etat, cout lineaire.
      manque  ( M, ) le manque de chaque menage, en rations ( besoin - mange ) ;
      part    ( m, ) 1 - a_i de chaque membre a table ( a_i : rations deja mangees dehors, bornees a [0 ; 1] ) ;
      mineur  ( m, ) moins de AGE_MINEUR ans ;
      k       ( m, ) le menage de chaque membre ( < M ), les membres d un menage dans l ordre de leurs numeros ( l ordre
              des sommes de bincount : la boucle trie ses membres de la meme facon ).
    Les adultes absorbent le manque d abord, jusqu a leur besoin entier ( NOURRITURE_PAR_JOUR x somme de leurs parts ) ;
    ce qui depasse, au-dela de la tolerance, va aux mineurs. Dans chaque groupe, au prorata de la part. Rend manque_i
    ( m, ), qui ne depasse pas le besoin b_i du membre ( aux arrondis et a la tolerance pres ). Sans mineur, ou sans
    adulte, et a = 0 : manque_i = manque / v AU BIT, l ancien partage egal."""
    part = np.asarray(part, np.float64)
    p_min = np.bincount(k, weights=np.where(mineur, part, 0.0), minlength=M)
    p_adu = np.bincount(k, weights=np.where(mineur, 0.0, part), minlength=M)
    reste = manque - C.NOURRITURE_PAR_JOUR * p_adu                 # ce que le besoin des adultes ne couvre pas
    m_min = np.where((p_min > 0.0) & (reste > TOLERANCE_MANQUE), reste, 0.0)
    m_adu = manque - m_min
    num = np.where(mineur, m_min[k], m_adu[k]) * part
    den = np.where(mineur, p_min[k], p_adu[k])
    return np.divide(num, den, out=np.zeros(len(part)), where=den > 0.0)


class ParMenage:''')

# 2. le crochet des repas pris dehors ( HMT-177 ), juste avant le repas
remplacer('''
    def repas(self):
''', '''
    def manger_dehors(self, ids, rations=1.0):
        """HMT-177 ( Bibliotheque ) : des habitants ont mange DEHORS ( ecole, caserne, hopital, cantine ). L API, pas un
        acces brut : `w.repas_dehors[i]` = les rations ( d une JOURNEE, NOURRITURE_PAR_JOUR ) mangees dehors DEPUIS le
        dernier repas du soir. Monde.repas tourne UNE fois par jour, a 20 h 00 ( pas_suivant ), apres les achats de
        19 h 00 : il lit a_i = min(1, max(0, repas_dehors[i])) pour chaque membre a table, baisse d autant le besoin a la
        maison, puis remet le tableau a zero. Un repas pris dehors avant 20 h compte le soir meme ( d19 appelle a 15 h,
        les jours de classe ) ; apres 20 h, le lendemain soir. Rien ne touche un stock ici : celui qui sert le repas le
        consomme lui-meme au grand livre ( d19 au marche ).
          ids      numeros d habitants ( 0 <= id < table.n ) ;
          rations  un flottant dans ]0 ; 1], ou un tableau aligne sur ids ; deux appels s ajoutent ( borne a 1 au repas ).
        Le tableau ( float64, indexe par numero ) nait au premier appel et grandit avec la table ( naissances ) ; avant,
        il est absent ou None : le monde est identique au bit a l ancien ( un instantane ancien se relit par getattr )."""
        ids = np.asarray(ids, np.int64).ravel()
        q = np.broadcast_to(np.asarray(rations, np.float64), ids.shape)
        if ids.size == 0: return
        n = self.table.n
        if ids.min() < 0 or ids.max() >= n: raise ValueError("manger_dehors : numero d habitant hors de la table")
        if not np.all(np.isfinite(q)) or np.any(q <= 0.0) or np.any(q > 1.0):
            raise ValueError("manger_dehors : rations hors de ]0 ; 1]")
        rd = getattr(self, "repas_dehors", None)
        if rd is None or len(rd) < n:
            neuf = np.zeros(max(n, int(getattr(self.table, "capacite", n))))
            if rd is not None: neuf[:len(rd)] = rd
            self.repas_dehors = rd = neuf
        np.add.at(rd, ids, q)

    def _rations_dehors(self, ids):
        """HMT-177 : a_i des habitants `ids`, borne a [0 ; 1] ; None sans crochet ( absent ou None )."""
        rd = getattr(self, "repas_dehors", None)
        if rd is None: return None
        ids = np.asarray(ids, np.int64)
        a = np.zeros(len(ids)); dans = ids < len(rd)
        a[dans] = np.minimum(1.0, np.maximum(0.0, rd[ids[dans]]))
        return a

    def _vider_repas_dehors(self, a):
        """HMT-177 : apres le repas, le compteur du jour ( somme EXACTE des a_i appliques ) et la remise a zero."""
        rd = getattr(self, "repas_dehors", None)
        if rd is None: return
        self.stats_jour["rations_dehors"] = math.fsum(np.asarray(a, np.float64).tolist()) if a is not None else 0.0
        rd[:] = 0.0

    def repas(self):
''')
remplacer('''        Les menages formes ( doctrine ) gardent la version Python : leur note se lit menage par menage."""
''', '''        Les menages formes ( doctrine ) gardent la version Python : leur note se lit menage par menage.
        HMT-176 / HMT-177 ( 30/09 ) : il tourne UNE fois par jour, a 20 h 00. Le besoin de chaque membre est
        NOURRITURE_PAR_JOUR x ( 1 - a_i ), a_i = les rations mangees dehors depuis le repas precedent ( manger_dehors ) ;
        le manque se partage par partager_le_manque ( les mineurs d abord ) et la faim se juge PAR PERSONNE : un membre
        sans manque est nourri ( faim - 1 ), meme si son menage a manque."""
''')

# 3. le repas en colonnes : le besoin ( a_i ), puis la faim par personne
remplacer('''        v = np.bincount(mm[membres], minlength=M)
        besoin = C.NOURRITURE_PAR_JOUR * v
''', '''        v = np.bincount(mm[membres], minlength=M)
        dehors = self._rations_dehors(membres)                      # HMT-177 : a_i ( None sans crochet )
        part = np.ones(len(membres)) if dehors is None else 1.0 - dehors
        besoin = C.NOURRITURE_PAR_JOUR * np.bincount(mm[membres], weights=part, minlength=M)   # a = 0 : R x v, au bit
''')
remplacer('''        t.faim[membres] = np.where(affame[k], faim + np.maximum(0.0, manque[k] / np.maximum(v[k], 1) - C.FAIM_ADAPTATION), np.maximum(0.0, faim - 1))
''', '''        mi = partager_le_manque(manque, part, t.age[membres] < AGE_MINEUR, k, M)   # HMT-176 : les mineurs d abord
        t.faim[membres] = np.where(affame[k] & (mi > 0.0), faim + np.maximum(0.0, mi - C.FAIM_ADAPTATION), np.maximum(0.0, faim - 1))
        self._vider_repas_dehors(dehors)
''')

# 4. le repas en boucle : la meme regle, par la meme fonction ; les membres dans l ordre de leurs numeros
remplacer('''            besoin = C.NOURRITURE_PAR_JOUR * len(vivants)
''', '''            vivants.sort(key=_numero)                                # l ordre des sommes de la version en colonnes
            dehors = self._rations_dehors([p.id for p in vivants])  # HMT-177
            part = np.ones(len(vivants)) if dehors is None else 1.0 - dehors
            besoin = C.NOURRITURE_PAR_JOUR * sum(part.tolist())     # a = 0 : R x len(vivants), au bit
''')
remplacer('''            for p in vivants: p.faim = p.faim + max(0.0, manque / len(vivants) - C.FAIM_ADAPTATION) if manque > 1e-6 else max(0.0, p.faim - 1)
''', '''            if vivants:                                               # HMT-176 : les mineurs d abord, la faim par personne
                mi = partager_le_manque(np.array([manque], np.float64), part, np.array([p.age < AGE_MINEUR for p in vivants]),
                                        np.zeros(len(vivants), np.int64), 1).tolist()
                for p, m_i in zip(vivants, mi):
                    p.faim = p.faim + max(0.0, m_i - C.FAIM_ADAPTATION) if manque > 1e-6 and m_i > 0.0 else max(0.0, p.faim - 1)
                if dehors is not None: vus_dehors.extend(dehors.tolist())
''')
remplacer('''        self.stats_jour["menages_sans_nourriture"] = sans
''', '''        self.stats_jour["menages_sans_nourriture"] = sans
        self._vider_repas_dehors(vus_dehors)                          # HMT-177
''')
remplacer('''    def repas_python(self):
        sans = 0
''', '''    def repas_python(self):
        sans = 0
        vus_dehors = []                                               # HMT-177 : les a_i appliques, pour le compteur
''')
# la cle de tri : une fonction de module ( picklable, pas de lambda )
remplacer('''
class ParMenage:''', '''
def _numero(h):
    return h.id


class ParMenage:''')
open(F, "w").write(s)
print("corrige :", F)
