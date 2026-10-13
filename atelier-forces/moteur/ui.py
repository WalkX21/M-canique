"""Petits composants d'interface partagés par les situations."""

import streamlit as st


def choix(cle, libelle, options, aide=None):
    """Choix unique en boutons segmentés. options : {valeur: libellé}."""
    if st.session_state.get(cle) not in options:
        st.session_state[cle] = next(iter(options))
    val = st.segmented_control(libelle, list(options), format_func=options.get, key=cle, help=aide,
                               selection_mode="single", required=True)
    return val if val is not None else next(iter(options))


def curseur(cle, libelle, mini, maxi, pas, fmt="%g", aide=None):
    """Curseur dont la plage peut changer : on recale la valeur si besoin."""
    v = st.session_state.get(cle, mini)
    st.session_state[cle] = float(min(max(v, mini), maxi))
    return st.slider(libelle, float(mini), float(maxi), step=float(pas), key=cle, format=fmt, help=aide)


def nombre(cle, libelle, mini=0.0, aide=None, fmt="%g"):
    return st.number_input(libelle, min_value=mini, format=fmt, key=cle, help=aide)


def interrupteur(cle, libelle, aide=None):
    return st.toggle(libelle, key=cle, help=aide)
