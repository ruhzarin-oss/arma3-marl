src=open("compo_play.py").read().split("\n")
out=[]; i=0
while i < len(src):
    l=src[i]
    if "MOVE._resample_targets = lambda" in l:   # retire le figeage -> resampling natif
        i+=1; continue
    if l.strip().startswith("# COMPO: cible-carotte"):
        out += [
        "            # NATIF: aucune injection (cibles aleatoires du Move env). log pos + hauteur torse.",
        "            if _ci % 12 == 0:",
        "                _r = MOVE._root_xy()[0].tolist()",
        "                _h = float(MOVE.robot.data.body_pos_w[0, MOVE.ref_body_index, 2])",
        "                print(\"[NATIF] t=%3d root=(%.1f,%.1f) h=%.2f\" % (_ci,_r[0],_r[1],_h), flush=True)" ,
        ]
        while i < len(src) and src[i].strip() != "_ci += 1": i+=1
        out.append(src[i]); i+=1; continue
    out.append(l); i+=1
open("native_play.py","w").write("\n".join(out))
print("native_play.py ecrit")
