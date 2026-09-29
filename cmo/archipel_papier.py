"""ArchipelDePapier : ce que l'horloge de guerre ( guerre/horloge.py ) demande à l'archipel, rien de plus. Des recettes
fixes par île, des soldats numérotés, des paiements, des occupations et des morts NOTÉS. Il ne prouve que le côté CMO
de la guerre ( CmoGuerre ) sous la vraie horloge ; le moteur a ses propres portes.

Sert à la porte ( porte_guerre_cmo.py, g10 ) et à l'endurance de guerre ( endurance_guerre.py )."""
import time


class ArchipelDePapier:
    def __init__(self, recettes, part_defense=0.05, militaires=50, pas_s=0.0):
        """recettes : un nombre ( toutes les îles ) ou { île : recettes par relève }. pas_s : la durée d'un « pas du
        moteur » ( l'horloge appelle un_pas() entre deux tours ; 0 en porte, 0,2 s en endurance pour ne pas tourner à
        vide )."""
        self.recettes, self.part, self.militaires, self.pas_s = recettes, part_defense, militaires, pas_s
        self.numero, self.payes, self.occupe, self.suivis, self.morts = {}, {}, [], {}, {}

    def _recettes(self, ile):
        return self.recettes[ile] if isinstance(self.recettes, dict) else self.recettes

    def commande(self, ile, ordre, *a):
        if ordre == "guerre_voir":
            return "regles"
        if ordre == "guerre_releve":
            return {"recettes": self._recettes(ile), "part_defense": self.part, "euros_par_unite": 1.0,
                    "militaires": self.militaires, "occupees": [], "front": {"reserve": 0, "front": 0, "mort": 0},
                    "jour": 1, "jours_clos": 1}
        if ordre == "guerre_mobiliser":
            k0 = self.numero.get(ile, 1)
            self.numero[ile] = k0 + a[0]
            return list(range(k0, k0 + a[0]))
        if ordre == "guerre_payer":
            self.payes.setdefault(ile, []).append(a[0])
            return {"paye": a[0], "dette_points": 0.0}
        if ordre == "occuper":
            self.occupe.append((ile, a[0], a[2]))
            return None
        if ordre == "guerre_suivre":
            self.suivis[ile] = len(a[0])
            return len(a[0])
        if ordre == "guerre_morts":
            self.morts[ile] = self.morts.get(ile, 0) + len(a[0])
            return len(a[0])
        if ordre == "guerre_gouverner":
            return "conseil"
        raise KeyError(ordre)                            # tourisme_risque : l'horloge le tolère

    def un_pas(self):
        if self.pas_s:
            time.sleep(self.pas_s)
