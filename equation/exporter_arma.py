"""
Export des episodes Arma pour le test B ( Windows, venv dbt, base harmattan.duckdb en lecture seule ).
  C:\\hmt\\dbt\\.venv\\Scripts\\python.exe exporter_arma.py C:/hmt/tmp/equation/arma_choix.parquet
Colonnes : campagne, point, graine, bras, a ( 0/1 ), Y ( issue primaire pre-enregistree ), perceptions au moment du choix.
bras et graine servent aux plis et a la lecture, jamais comme perceptions.
"""
import os, sys
import duckdb

SORTIE = sys.argv[1]
# seulement les campagnes deja lues avec leurs criteres : P3 et P6 s'ajoutent apres leur lecture, jamais avant
CAMPAGNES = sys.argv[2].split(",") if len(sys.argv) > 2 else ["CHOIX-P1-17-09", "CHOIX-P2-17-09", "CHOIX-P4-17-09"]
os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
c = duckdb.connect("C:/hmt/dbt/harmattan.duckdb", read_only=True)
CHOIX = ", ".join(f"'{x}'" for x in CAMPAGNES)
sql = f"""
with lignes as (
  select episode_id, regexp_extract(reste, '\\|point\\|([A-Z_0-9]+)', 1) as point,
    try_cast(nullif(regexp_extract(reste, '\\|vehicule_vu\\|(-?[0-9.]+)', 1), '') as double) as vehicule_vu,
    try_cast(nullif(regexp_extract(reste, '\\|reco_vivants\\|(-?[0-9.]+)', 1), '') as double) as reco_vivants,
    try_cast(nullif(regexp_extract(reste, '\\|distance_point\\|(-?[0-9.]+)', 1), '') as double) as distance_point
  from stg_lignes where famille = 'E' and cle = 'decision'
),
choix as (
  select v.campagne, v.point, v.graine, v.bras,
    case v.point when 'OBS_DUREE' then (v.choix = 480) when 'EXFIL_ALLURE' then (v.choix = 1) else (v.choix = 2) end::int as a,
    case v.point when 'INSERTION_ATTENTE' then v.phase_discrete when 'TRAVERSEE' then v.phase_discrete
                 when 'ITINERAIRE' then v.mise_en_place_propre when 'OBS_DUREE' then v.observation_utile
                 when 'EXFIL_ALLURE' then v.exfil_reussie end::int as Y,
    d.alarme, d.depuis_alarme, d.compromis, d.vivants, d.defenseurs_connus, l.vehicule_vu, l.reco_vivants, l.distance_point
  from vignette_choix v
  join stg_decision d on d.episode_id = v.episode_id and d.point = v.point
  join lignes l on l.episode_id = v.episode_id and l.point = v.point
  where v.verdict = 'ACCEPTE' and v.erreurs_sqf = 0 and v.campagne in ({CHOIX})
    and v.point in ('INSERTION_ATTENTE', 'TRAVERSEE', 'ITINERAIRE', 'OBS_DUREE', 'EXFIL_ALLURE')
),
pilote as (
  select campagne, 'DELAI_PORTEUR' as point, graine, bras, (choix = 180)::int as a, assaut_utile::int as Y,
    alarme_au_choix as alarme, depuis_alarme, compromis_au_choix as compromis, vivants_au_choix as vivants, defenseurs_connus,
    null::double as vehicule_vu, null::double as reco_vivants, null::double as distance_point
  from pilote_p5 where verdict = 'ACCEPTE' and erreurs_sqf = 0 and campagne = 'PILOTE-P5-DELAI-SITUATION-16-09'
)
select * from choix union all select * from pilote
"""
c.execute(f"copy ({sql}) to '{SORTIE}' (format parquet)")
for r in c.execute(f"select campagne, point, count(*), sum(a), sum(Y), count(distinct graine) from read_parquet('{SORTIE}') group by 1, 2 order by 1").fetchall():
    print(r)
