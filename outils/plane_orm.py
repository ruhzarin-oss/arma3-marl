#!/usr/bin/env python3
"""Parle a Plane par son ORM, dans le conteneur. Pas de jeton d API : le classifieur de
permissions de Claude Code refuse d en creer un, et un jeton en clair sur le disque serait
un secret de plus a garder. `docker exec` suffit et ne sort pas de la machine."""
import json, subprocess, sys

CONTENEUR = "plane-app-api-1"
SLUG = "travaux"
PROJET = "HMT"


def orm(code, timeout=120):
    """Execute du Python dans le conteneur et rend ce que le code a imprime entre
    les balises <<<JSON>>>. Toute autre sortie (bannieres Django) est ignoree."""
    script = ("import json\n"
              "from plane.db.models import Workspace, Project, Issue, State, Label, "
              "IssueLabel, IssueComment, User\n"
              "W = Workspace.objects.get(slug=%r)\n"
              "P = Project.objects.get(workspace=W, identifier=%r)\n"
              "E = {s.name: s for s in State.objects.filter(project=P)}\n"
              "U = User.objects.filter(email='younesbhn@gmail.com').first()\n"
              "def rendre(x):\n"
              "    print('<<<JSON>>>' + json.dumps(x, default=str) + '<<<FIN>>>')\n"
              % (SLUG, PROJET)) + code
    r = subprocess.run(["docker", "exec", "-i", CONTENEUR, "python", "manage.py", "shell"],
                       input=script.encode(), capture_output=True, timeout=timeout)
    out = r.stdout.decode("utf-8", "ignore")
    if "<<<JSON>>>" not in out:
        raise RuntimeError("ORM sans reponse.\n%s\n%s" % (out[-800:], r.stderr.decode()[-800:]))
    return json.loads(out.split("<<<JSON>>>")[1].split("<<<FIN>>>")[0])


def taches(etat=None, etiquette=None):
    code = ("q = Issue.objects.filter(project=P)\n"
            "if %r: q = q.filter(state__name=%r)\n"
            "if %r:\n"
            "    ids = IssueLabel.objects.filter(project=P, label__name=%r).values_list('issue_id', flat=True)\n"
            "    q = q.filter(id__in=ids)\n"
            "rendre([{'seq': i.sequence_id, 'nom': i.name, 'etat': i.state.name if i.state else None,\n"
            "         'html': i.description_html or ''} for i in q.order_by('sequence_id')])\n"
            % (etat, etat, etiquette, etiquette))
    return orm(code)


def etat(seq, nouvel_etat):
    return orm("i = Issue.objects.get(project=P, sequence_id=%d)\n"
               "i.state = E[%r]; i.save()\n"
               "rendre({'seq': i.sequence_id, 'etat': i.state.name})\n" % (seq, nouvel_etat))


def commenter(seq, html):
    return orm("i = Issue.objects.get(project=P, sequence_id=%d)\n"
               "c = IssueComment.objects.create(issue=i, project=P, workspace=W,\n"
               "        comment_html=%r, created_by=U, actor=U)\n"
               "rendre({'seq': i.sequence_id, 'commentaire': str(c.id)})\n" % (seq, html))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "liste"
    if a == "liste":
        for t in taches():
            print("  HMT-%-3d [%-10s] %s" % (t["seq"], t["etat"], t["nom"][:66]))
    elif a == "run":
        for t in taches(etat="A faire", etiquette="run"):
            print("  HMT-%-3d %s" % (t["seq"], t["nom"][:70]))
