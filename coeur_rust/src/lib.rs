//! Le coeur du monde en Rust. Les routines qui parcourent toute la population a chaque pas vivent ici, sur des
//! COLONNES ( un tableau par attribut ) que tous les coeurs lisent ensemble.
//!
//! Premiere routine portee : `deplacer`, 58 % d une journee a un million d habitants ( profil du 23/09 : 106,5 s sur
//! 182 ). Elle reproduit `Monde.deplacer` a l identique ; la porte compare les deux, habitant par habitant.

use numpy::{PyReadonlyArray1, PyReadwriteArray1};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Les horaires du monde, dans l ordre des codes : jour, bureau, nuit, ecole, marche ( 5 = garde, -1 = aucun ).
const HORAIRES: [(f64, f64); 5] = [(7.0, 15.0), (8.0, 17.0), (22.0, 6.0), (8.0, 15.0), (8.0, 19.0)];
const GARDE: i8 = 5;

/// `Habitant.au_travail`, mot pour mot. Attention au modulo : Python rend un reste du signe du diviseur,
/// Rust du signe du dividende - d ou `rem_euclid`, sans quoi une garde de nuit se trompait d equipe avant minuit.
#[inline]
fn au_travail(heure: f64, decalage: f64, horaire: i8, equipe: i32, vivant: bool, etat_i: bool, gravite: f64) -> bool {
    let h = heure - decalage / 60.0;
    if horaire < 0 || !vivant || (etat_i && gravite > 0.5) {
        return false;
    }
    if horaire == GARDE {
        let debut = [6.0, 14.0, 22.0][equipe.rem_euclid(3) as usize];
        return (h - debut).rem_euclid(24.0) < 8.0;
    }
    let (a, b) = HORAIRES[horaire as usize];
    if a < b { a <= h && h < b } else { h >= a || h < b }
}

/// Postes : 0 maison, 1 travail, 2 hopital. Un habitant « saute » ( mort, en mer, en sejour ) garde tout en l etat.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn deplacer<'py>(
    py: Python<'py>,
    heure: f64,
    absence_faim: f64,
    heures_par_pas: f64,
    sauter: PyReadonlyArray1<'py, u8>,
    vivant: PyReadonlyArray1<'py, u8>,
    etat_i: PyReadonlyArray1<'py, u8>,
    gravite: PyReadonlyArray1<'py, f64>,
    horaire: PyReadonlyArray1<'py, i8>,
    equipe: PyReadonlyArray1<'py, i32>,
    decalage: PyReadonlyArray1<'py, f64>,
    enferme: PyReadonlyArray1<'py, u8>,
    faim: PyReadonlyArray1<'py, f64>,
    public: PyReadonlyArray1<'py, u8>,
    travail: PyReadonlyArray1<'py, i32>,
    domicile: PyReadonlyArray1<'py, i32>,
    hopital: PyReadonlyArray1<'py, i32>,
    mut lieu: PyReadwriteArray1<'py, i32>,
    mut poste: PyReadwriteArray1<'py, u8>,
    mut heures: PyReadwriteArray1<'py, f64>,
) -> PyResult<()> {
    let (sauter, vivant, etat_i, gravite) = (sauter.as_slice()?, vivant.as_slice()?, etat_i.as_slice()?, gravite.as_slice()?);
    let (horaire, equipe, decalage, enferme) = (horaire.as_slice()?, equipe.as_slice()?, decalage.as_slice()?, enferme.as_slice()?);
    let (faim, public, travail, domicile, hopital) =
        (faim.as_slice()?, public.as_slice()?, travail.as_slice()?, domicile.as_slice()?, hopital.as_slice()?);
    let lieu = lieu.as_slice_mut()?;
    let poste = poste.as_slice_mut()?;
    let heures = heures.as_slice_mut()?;
    // le verrou de Python est rendu pendant le calcul : les douze coeurs travaillent, Python attend
    py.allow_threads(|| {
        lieu.par_iter_mut()
            .zip(poste.par_iter_mut())
            .zip(heures.par_iter_mut())
            .enumerate()
            .for_each(|(i, ((l, p), hj))| {
                if sauter[i] != 0 || vivant[i] == 0 {
                    return;
                }
                if etat_i[i] != 0 && gravite[i] > 0.3 {
                    *l = hopital[i];
                    *p = 2;
                    return;
                }
                let veut = enferme[i] == 0 && !(faim[i] > absence_faim);
                if travail[i] >= 0
                    && veut
                    && au_travail(heure, decalage[i], horaire[i], equipe[i], true, etat_i[i] != 0, gravite[i])
                {
                    *l = travail[i];
                    *p = 1;
                    if public[i] != 0 {
                        *hj += heures_par_pas;
                    }
                } else {
                    *l = domicile[i];
                    *p = 0;
                }
            });
    });
    Ok(())
}

#[pymodule]
fn coeur(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(deplacer, m)?)?;
    Ok(())
}
