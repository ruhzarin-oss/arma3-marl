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
/// En dessous, le calcul reste sur un coeur ; au-dessus, il est reparti par paquets de PAQUET habitants.
const SEUIL_PARALLELE: usize = 20_000;
const PAQUET: usize = 8_192;

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

/// Postes : 0 maison, 1 travail, 2 hopital. Un habitant « saute » ( en mer, en sejour ) garde son lieu et son poste.
/// `travaille` recoit, pour chaque vivant, le resultat de « est-ce son heure de travail » - independamment de son
/// choix : un paysan qui vit dans son village de travail compte parmi les presents meme reste chez lui.
/// Etats de sante : 0 sain, 1 expose, 2 malade ( I ), 3 gueri.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn deplacer<'py>(
    py: Python<'py>,
    heure: f64,
    absence_faim: f64,
    heures_par_pas: f64,
    sauter: PyReadonlyArray1<'py, u8>,
    vivant: PyReadonlyArray1<'py, u8>,
    etat: PyReadonlyArray1<'py, u8>,
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
    mut travaille: PyReadwriteArray1<'py, u8>,
) -> PyResult<()> {
    let (sauter, vivant, etat, gravite) = (sauter.as_slice()?, vivant.as_slice()?, etat.as_slice()?, gravite.as_slice()?);
    let (horaire, equipe, decalage, enferme) = (horaire.as_slice()?, equipe.as_slice()?, decalage.as_slice()?, enferme.as_slice()?);
    let (faim, public, travail, domicile, hopital) =
        (faim.as_slice()?, public.as_slice()?, travail.as_slice()?, domicile.as_slice()?, hopital.as_slice()?);
    let lieu = lieu.as_slice_mut()?;
    let poste = poste.as_slice_mut()?;
    let heures = heures.as_slice_mut()?;
    let travaille = travaille.as_slice_mut()?;
    // un habitant : ou il va a ce pas. Le meme corps sert au calcul seul et au calcul parallele.
    let un = |i: usize, l: &mut i32, p: &mut u8, hj: &mut f64, tr: &mut u8| {
        if vivant[i] == 0 {
            *tr = 0;
            return;
        }
        let malade = etat[i] == 2;
        let a_son_heure = au_travail(heure, decalage[i], horaire[i], equipe[i], true, malade, gravite[i]);
        *tr = a_son_heure as u8;
        if sauter[i] != 0 {
            return;
        }
        if malade && gravite[i] > 0.3 {
            *l = hopital[i];
            *p = 2;
            return;
        }
        let veut = enferme[i] == 0 && !(faim[i] > absence_faim);
        if travail[i] >= 0 && veut && a_son_heure {
            *l = travail[i];
            *p = 1;
            if public[i] != 0 {
                *hj += heures_par_pas;
            }
        } else {
            *l = domicile[i];
            *p = 0;
        }
    };
    if lieu.len() < SEUIL_PARALLELE {
        // un petit monde : reveiller vingt fils coutait 470 microsecondes pour 500 habitants ( mesure du 23/09 ),
        // cent fois le calcul lui-meme. Un seul coeur suffit.
        for (i, (((l, p), hj), tr)) in lieu.iter_mut().zip(poste.iter_mut()).zip(heures.iter_mut()).zip(travaille.iter_mut()).enumerate() {
            un(i, l, p, hj, tr);
        }
    } else {
        // le verrou de Python est rendu pendant le calcul : tous les coeurs travaillent, par paquets assez gros
        py.allow_threads(|| {
            lieu.par_iter_mut()
                .zip(poste.par_iter_mut())
                .zip(heures.par_iter_mut())
                .zip(travaille.par_iter_mut())
                .enumerate()
                .with_min_len(PAQUET)
                .for_each(|(i, (((l, p), hj), tr))| un(i, l, p, hj, tr));
        });
    }
    Ok(())
}

#[pymodule]
fn coeur(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(deplacer, m)?)?;
    Ok(())
}
