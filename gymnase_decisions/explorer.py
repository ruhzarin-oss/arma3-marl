import collections, pyarrow.parquet as pq
T = pq.read_table("/mnt/data/hmt/gymnase_decisions/donnees/phases.parquet").to_pylist()
def c(title, it):
    print("==", title); [print(f"  {v:5d}  {k}") for k, v in sorted(collections.Counter(it).items(), key=lambda kv: -kv[1])[:40]]
ok = [r for r in T if r["verdict"] == "ACCEPTE" and r["erreurs_sqf"] == 0]
print("acceptes sans erreur", len(ok), "sur", len(T))
c("palier socle lambs effectif oracle ablation banc_appui placeur", [(r["lev_palier"], r["lev_socle"], r["lev_lambs"], r["lev_effectif"], r["lev_oracle"], r["lev_ablation"], r["lev_banc_appui"], r["lev_placeur"]) for r in ok])
base = [r for r in ok if r["lev_palier"] == 4 and r["lev_socle"] == 1 and r["lev_effectif"] == 10 and r["lev_oracle"] in (0, None)
        and r["lev_ablation"] in (0, None) and r["lev_banc_appui"] in (0, None) and r["lev_placeur"] in (0, None) and r["lev_immortel"] in (0, None) and r["lev_jour"] in (0, None)]
print("base comparable", len(base))
c("tactique appui_feu feu_avant mg_assaut appui_fixe accessible", [(r["lev_tactique"], r["lev_appui_feu"], r["lev_feu_avant"], r["lev_mg_assaut"], r["lev_appui_fixe"], r["lev_accessible"]) for r in base])
c("depart arret delai tenir exfil obs", [(r["lev_depart"], r["lev_arret"], r["lev_delai_porteur"], r["lev_tenir"], r["lev_exfil"], r["lev_obs"]) for r in base])
c("partage qrf_n qrf_delai qrf_dist situation acc", [(r["lev_partage"], r["lev_qrf_n"], r["lev_qrf_delai"], r["lev_qrf_dist"], r["lev_situation"], r["lev_acc"]) for r in base])
c("campagnes de la base", [r["campagne"] for r in base])
c("sites de la base (top)", [r.get("site") for r in base])
print("sites distincts", len({r.get("site") for r in base}))
c("etat debut p5 (vivants, compromis, alarme)", [(r.get("p5_debut_vivants"), r.get("p5_debut_compromis"), r.get("p5_debut_alarme")) for r in base if r.get("p5_debut_t") is not None])
c("fin p5 (issue, charges, vivants, compromis, alarme)", [(r.get("p5_fin_issue"), r.get("p5_fin_charges"), r.get("p5_fin_vivants"), r.get("p5_fin_compromis"), r.get("p5_fin_alarme")) for r in base if r.get("p5_fin_t") is not None])
c("debut p6 (vivants, compromis, alarme) vs p5_fin_charges", [(r.get("p6_debut_vivants"), r.get("p5_fin_charges")) for r in base if r.get("p6_debut_t") is not None])
c("fin p6 issue / FINI", [(r.get("p6_fin_issue"), r["fini_issue"], r["fini_cause"]) for r in base if r.get("p6_debut_t") is not None])
c("porte_indice x delai (p5 joue)", [(r.get("porte_indice"), r["lev_delai_porteur"]) for r in base if r.get("p5_debut_t") is not None])
c("controle: p5_fin_charges vs fini_charges quand arret=5", [(r.get("p5_fin_charges"), r["fini_charges"]) for r in base if r["lev_arret"] == 5][:2000])
