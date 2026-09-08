# PUBLIEUR — tourne DANS le conteneur api de Plane, qui a Django et la base mais PAS /mnt/data.
# Il ne fait que consommer le colis produit par journal.py. Imprime « POUSSE <nom> » par entree de
# journal reellement ajoutee : le shell s'en sert pour marquer les runs deja journalises.
import json
from plane.db.models import Page, ProjectPage, Project, Workspace, User

colis = json.load(open("/tmp/journal_colis.json", encoding="utf-8"))
w = Workspace.objects.get(slug="travaux")
u = User.objects.get(email="younesbhn@gmail.com")
p = Project.objects.get(identifier="HMT")


def poser(nom, corps, ajouter=False):
    pg = Page.objects.filter(workspace=w, name=nom).first()
    if pg is None:
        pg = Page.objects.create(workspace=w, name=nom, owned_by=u, access=0, created_by=u,
                                 updated_by=u, description_html=corps, description_stripped=corps)
        ProjectPage.objects.get_or_create(page=pg, project=p, workspace=w, defaults=dict(created_by=u))
        return "creee"
    pg.description_html = ((pg.description_html or "") + corps) if ajouter else corps
    pg.description_stripped = pg.description_html
    pg.updated_by = u
    pg.save(update_fields=["description_html", "description_stripped", "updated_by", "updated_at"])
    ProjectPage.objects.get_or_create(page=pg, project=p, workspace=w, defaults=dict(created_by=u))
    return "mise a jour"


print("ETAT :", poser("ETAT — lire ceci en premier", colis["etat"]))
print("Verdicts :", poser("Verdicts — le detail", colis["verdicts"]))
if colis["entrees"]:
    print("Journal :", poser("Journal des runs", "".join(x["html"] for x in colis["entrees"]), ajouter=True))
    for x in colis["entrees"]:
        print("POUSSE", x["nom"])
else:
    if not Page.objects.filter(workspace=w, name="Journal des runs").exists():
        poser("Journal des runs", "<p><em>Aucun run termine pour l'instant.</em></p>")
    print("Journal : rien de neuf")
for pg in Page.objects.filter(workspace=w).order_by("created_at"):
    print("  page:", pg.name, "|", len(pg.description_html or ""), "caracteres")
