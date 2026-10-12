

import inspect

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from physique import (
    G, Modele, METHODES, etude_convergence, integrer, pas_automatique, pas_euler,
    pas_rk4, solution_exacte, tau_local, temps_95, vitesse_limite_finale,
)

st.set_page_config(page_title="Simulateur de chute", layout="wide")

COULEURS = {"RK4": "#2E3DA3", "Euler": "#C27A12", "exacte": "#B8352B",
            "limite": "#2A7A4C", "tangente": "#B8352B"}

# ---------------------------------------------------------------------------
# Scénarios prêts à l'emploi (repris du carnet et de l'exercice « Le saut »)
# ---------------------------------------------------------------------------

BASE = dict(mode="Chute verticale", m=80.0, archi=False, rho_f=1000.0, rho_o=7800.0,
            F=100.0, use_k1=False, k1=0.0, use_k2=True, k2=0.2594, v0=0.0,
            ouverture=False, k2_fin=31.39, t_ouv=1.0, d_ouv=0.0,
            duree=40.0, methode="RK4", pas_auto=True, dt=0.01)

SCENARIOS = {
    "Parachutiste en chute stabilisée": dict(),
    "Ouverture instantanée du parachute": dict(v0=55.0, ouverture=True, d_ouv=0.0, duree=6.0),
    "Ouverture progressive (3 s)": dict(v0=55.0, ouverture=True, d_ouv=3.0, duree=8.0),
    "Bille dans la glycérine": dict(m=3.267e-5, archi=True, rho_f=1260.0, rho_o=7800.0,
                                    use_k1=True, k1=0.02639, use_k2=False, duree=0.01),
    "Balle lancée vers le haut": dict(m=0.057, k2=0.001398, v0=-20.0, duree=5.0),
    "Cycliste sur le vélodrome": dict(mode="Mouvement horizontal", F=121.0, k2=0.32, duree=25.0),
}


DESCRIPTIONS = {
    "Parachutiste en chute stabilisée": "Exercice « Le saut », partie 2 : k₂ = 0,26 kg/m, vitesse limite 55 m/s.",
    "Ouverture instantanée du parachute": "Partie 3 : à t = 1 s, k₂ passe d'un coup à 31,4 kg/m (vitesse limite 5 m/s).",
    "Ouverture progressive (3 s)": "Même ouverture, mais la voile se gonfle en 3 s : compare l'accélération maximale.",
    "Bille dans la glycérine": "Partie 1 : loi de Stokes et poussée d'Archimède, régime transitoire de quelques ms.",
    "Balle lancée vers le haut": "Frottement quadratique avec changement de sens : pas de solution exacte simple.",
    "Cycliste sur le vélodrome": "Force motrice de 121 N (a₀ = 1,5 m/s² comme dans l'exercice) et vitesse limite de 70 km/h.",
}


def charger_scenario():
    valeurs = {**BASE, **SCENARIOS[st.session_state.scenario]}
    for cle, val in valeurs.items():
        st.session_state[cle] = val


if "m" not in st.session_state:
    st.session_state.scenario = "Parachutiste en chute stabilisée"
    charger_scenario()

# ---------------------------------------------------------------------------
# Barre latérale : paramètres
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Paramètres")
    st.selectbox("Scénario", list(SCENARIOS), key="scenario", on_change=charger_scenario)
    st.caption(DESCRIPTIONS[st.session_state.scenario] + " Tu peux ensuite tout modifier.")

    st.subheader("Force motrice")
    st.radio("Type de mouvement", ["Chute verticale", "Mouvement horizontal"], key="mode",
             horizontal=True)
    st.number_input("Masse m (kg)", min_value=1e-9, format="%g", key="m")
    if st.session_state.mode == "Chute verticale":
        st.checkbox("Poussée d'Archimède", key="archi")
        if st.session_state.archi:
            c1, c2 = st.columns(2)
            c1.number_input("ρ fluide (kg/m³)", min_value=0.0, format="%g", key="rho_f")
            c2.number_input("ρ objet (kg/m³)", min_value=1e-6, format="%g", key="rho_o")
    else:
        st.number_input("Force motrice F (N)", min_value=0.0, format="%g", key="F")

    st.subheader("Frottements")
    st.checkbox("Linéaire : −k₁ v", key="use_k1")
    if st.session_state.use_k1:
        st.number_input("k₁ (kg·s⁻¹)", min_value=0.0, format="%g", key="k1")
    st.checkbox("Quadratique : −k₂ |v| v", key="use_k2")
    if st.session_state.use_k2:
        st.number_input("k₂ (kg·m⁻¹)", min_value=0.0, format="%g", key="k2")
        with st.expander("Ouverture d'un parachute", expanded=st.session_state.ouverture):
            st.checkbox("k₂ change en cours de route", key="ouverture")
            if st.session_state.ouverture:
                st.number_input("k₂ après ouverture (kg·m⁻¹)", min_value=0.0, format="%g", key="k2_fin")
                st.number_input("Début de l'ouverture (s)", min_value=0.0, format="%g", key="t_ouv")
                st.number_input("Durée de l'ouverture (s), 0 = instantanée", min_value=0.0,
                                format="%g", key="d_ouv")

    st.subheader("Conditions initiales")
    st.number_input("Vitesse initiale v₀ (m/s)", format="%g", key="v0")
    if st.session_state.mode == "Chute verticale":
        st.caption("Axe orienté vers le bas : v₀ < 0 signifie lancé vers le haut.")

    st.subheader("Calcul numérique")
    st.number_input("Durée simulée (s)", min_value=1e-6, format="%g", key="duree")
    st.radio("Méthode", ["RK4", "Euler", "Les deux"], key="methode", horizontal=True)
    st.checkbox("Pas automatique", key="pas_auto")
    if not st.session_state.pas_auto:
        st.number_input("Pas dt (s)", min_value=1e-7, format="%g", key="dt")

S = st.session_state

# ---------------------------------------------------------------------------
# Construction du modèle à partir des paramètres
# ---------------------------------------------------------------------------

if S.mode == "Chute verticale":
    rapport = S.rho_f / S.rho_o if S.archi else 0.0
    if rapport >= 1:
        st.error("L'objet est moins dense que le fluide : il remonte. Choisis ρ objet > ρ fluide.")
        st.stop()
    F = S.m * G * (1 - rapport)
else:
    F = S.F

k1 = S.k1 if S.use_k1 else 0.0
k2 = S.k2 if S.use_k2 else 0.0
ouvre = S.use_k2 and S.ouverture
mod = Modele(m=S.m, F=F, k1=k1, k2=k2,
             k2_fin=S.k2_fin if ouvre else None,
             t_ouverture=S.t_ouv, duree_ouverture=S.d_ouv)

v0, duree = S.v0, S.duree
dt = pas_automatique(mod, v0, duree) if S.pas_auto else S.dt
if duree / dt > 300_000:
    st.error("Trop de pas de calcul : augmente dt ou réduis la durée.")
    st.stop()

methodes = ["RK4", "Euler"] if S.methode == "Les deux" else [S.methode]
resultats = {nom: integrer(mod, v0, duree, dt, nom) for nom in methodes}
principal = resultats[methodes[0]]
t = principal[0]
exacte = solution_exacte(mod, v0, t)
vl = vitesse_limite_finale(mod)
a_depart = mod.acceleration(0.0, v0)
tau = vl / mod.a0 if np.isfinite(vl) and mod.a0 > 0 else float("nan")

# Unités d'affichage adaptées à l'échelle (ms, cm/s pour la bille)
ech_t, u_t = (1e3, "ms") if duree < 1 else (1.0, "s")
v_ref = max(abs(v0), vl if np.isfinite(vl) else 0.0, float(np.nanmax(np.abs(principal[2]))))
ech_v, u_v = (100.0, "cm/s") if v_ref < 1 else (1.0, "m/s")


def fmt(x, chiffres=3):
    if x is None or not np.isfinite(x):
        return "—"
    return f"{x:.{chiffres}g}".replace(".", ",")


# ---------------------------------------------------------------------------
# En-tête et indicateurs
# ---------------------------------------------------------------------------

st.title("Simulateur de chute avec frottements")
st.caption("PCSI · mécanique du point · solutions exactes du cours et résolution numérique pas à pas")

frottement = " - ".join(p for p, k in ((r"k_1 v", k1), (r"k_2(t)\,|v|\,v" if ouvre else r"k_2\,|v|\,v", k2)) if k)
st.latex(r"m\,\frac{dv}{dt} = F" + (" - " + frottement if frottement else "")
         + rf"\qquad m = {fmt(S.m)}\ \mathrm{{kg}},\ F = {fmt(F)}\ \mathrm{{N}}")

for nom, (_, _, v, _) in resultats.items():
    if not np.all(np.isfinite(v)):
        st.error(f"Le calcul par {nom} a divergé : le pas dt est trop grand devant le temps de "
                 f"réponse du système ({fmt(tau_local(mod, v_ref))} s). Réduis dt ou passe en pas automatique.")
if not S.pas_auto and "Euler" in methodes and dt > 0.2 * tau_local(mod, v_ref):
    st.warning("Pas grand devant le temps de réponse : Euler devient imprécis, voire instable.")

t95 = temps_95(t, principal[2], vl)
a_max = float(np.nanmax(np.abs(principal[3])))
col = st.columns(5)
col[0].metric("Vitesse limite", f"{fmt(vl * ech_v)} {u_v}" if np.isfinite(vl) else "aucune",
              f"{fmt(vl * 3.6)} km/h" if np.isfinite(vl) and vl >= 1 else None, delta_color="off")
col[1].metric("τ = v_l / a₀", f"{fmt(tau * ech_t)} {u_t}")
col[2].metric("95 % de l'écart rattrapé", f"{fmt(t95 * ech_t)} {u_t}")
col[3].metric("Accélération max", f"{fmt(a_max / G)} g")
col[4].metric("Position finale z", f"{fmt(principal[1][-1])} m")

# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------

def figure(axe_y, titre_y):
    fig = go.Figure()
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10),
                      xaxis_title=f"t ({u_t})", yaxis_title=titre_y,
                      legend=dict(orientation="h", y=1.08, x=0))
    return fig


def tracer(fig, colonne, echelle):
    for nom, res in resultats.items():
        fig.add_trace(go.Scatter(x=res[0] * ech_t, y=res[colonne] * echelle, name=f"Numérique · {nom}",
                                 line=dict(color=COULEURS[nom], width=3 if nom == "RK4" else 2,
                                           dash="solid" if nom == "RK4" else "dash")))


onglets = st.tabs(["Vitesse", "Position", "Accélération", "Comment ça marche", "Données"])

with onglets[0]:
    fig = figure("v", f"v ({u_v})")
    tracer(fig, 2, ech_v)
    if exacte is not None:
        fig.add_trace(go.Scatter(x=t * ech_t, y=exacte[1] * ech_v, name=f"Exacte · {exacte[2]}",
                                 line=dict(color=COULEURS["exacte"], width=2, dash="dot")))
    if np.isfinite(vl):
        fig.add_hline(y=vl * ech_v, line=dict(color=COULEURS["limite"], dash="dash", width=1.5),
                      annotation_text="v_l", annotation_position="top right")
    if exacte is not None and np.isfinite(vl) and a_depart != 0:
        t_croise = (vl - v0) / a_depart          # la tangente à l'origine atteint v_l ici
        if 0 < t_croise <= duree:
            tt = np.array([0, min(1.5 * t_croise, duree)])
            fig.add_trace(go.Scatter(x=tt * ech_t, y=(v0 + a_depart * tt) * ech_v,
                                     name="Tangente à l'origine",
                                     line=dict(color=COULEURS["tangente"], width=1.5, dash="dash")))
            fig.add_vline(x=t_croise * ech_t, line=dict(color=COULEURS["tangente"], dash="dot", width=1),
                          annotation_text=f"t = {fmt(t_croise * ech_t)} {u_t}",
                          annotation_position="bottom right")
    st.plotly_chart(fig)
    st.caption("La tangente à l'origine coupe la vitesse limite en τ dans les cas linéaire et quadratique "
               "depuis le repos. Avec « Les deux » méthodes et un pas manuel, compare Euler et RK4.")

with onglets[1]:
    fig = figure("z", "z (m)")
    tracer(fig, 1, 1.0)
    if exacte is not None:
        fig.add_trace(go.Scatter(x=t * ech_t, y=exacte[0], name="Exacte",
                                 line=dict(color=COULEURS["exacte"], width=2, dash="dot")))
    st.plotly_chart(fig)
    st.caption("z compté à partir du point de départ, dans le sens de l'axe."
               + (" Pour la balle lancée vers le haut, z < 0 signifie au-dessus du point de départ."
                  if v0 < 0 else ""))

with onglets[2]:
    fig = figure("a", "a / g")
    tracer(fig, 3, 1 / G)
    st.plotly_chart(fig)
    st.caption("Compare l'ouverture instantanée (environ −120 g) et l'ouverture progressive : "
               "c'est la question Q3.2 de l'exercice « Le saut ».")

with onglets[3]:
    st.markdown("""
#### 1. Découper le temps
On ne cherche pas de formule. On découpe le temps en petits pas $dt$ et on avance pas à pas.
L'état du système à l'instant $t$ est le couple $(z, v)$, et la loi de Newton donne ses dérivées :
$\\dot z = v$ et $\\dot v = a(t, v) = \\dfrac{F - k_1 v - k_2 |v| v}{m}$.

#### 2. Méthode d'Euler : la pente est supposée constante pendant un pas
C'est la définition de la dérivée, lue à l'envers : $\\dfrac{\\Delta v}{\\Delta t} \\approx \\dot v$.
""")
    st.latex(r"v_{n+1} = v_n + a(t_n, v_n)\,dt \qquad z_{n+1} = z_n + v_n\,dt")
    st.markdown("""
L'erreur est proportionnelle à $dt$ : diviser le pas par 2 divise l'erreur par 2 (méthode d'ordre 1).

#### 3. Méthode de Runge-Kutta 4 : quatre mesures de pente par pas
On mesure la pente au début du pas, deux fois au milieu, puis à la fin, et on fait une moyenne pondérée.
""")
    st.latex(r"p_1 = a(t_n, v_n),\quad p_2 = a\!\left(t_n + \tfrac{dt}{2},\, v_n + \tfrac{dt}{2}p_1\right),\quad "
             r"p_3 = a\!\left(t_n + \tfrac{dt}{2},\, v_n + \tfrac{dt}{2}p_2\right),\quad p_4 = a(t_n + dt,\, v_n + dt\,p_3)")
    st.latex(r"v_{n+1} = v_n + \frac{dt}{6}\,(p_1 + 2p_2 + 2p_3 + p_4)")
    st.markdown("L'erreur est proportionnelle à $dt^4$ : diviser le pas par 2 divise l'erreur par 16.")

    st.markdown("#### 4. Vérifier le calcul contre la solution exacte")
    lignes = etude_convergence(mod, v0, duree) if exacte is not None else None
    if lignes:
        df = pd.DataFrame(lignes)
        df = df[np.isfinite(df.erreur) & (df.erreur > 0)]
        fig = go.Figure()
        pentes = {}
        for nom in METHODES:
            d = df[df.methode == nom]
            fig.add_trace(go.Scatter(x=d.dt, y=d.erreur, mode="lines+markers", name=nom,
                                     line=dict(color=COULEURS[nom])))
            fiables = d[d.erreur > 1e-10]          # au-delà, on touche la précision de la machine
            if len(fiables) >= 2:
                pentes[nom] = np.polyfit(np.log(fiables.dt), np.log(fiables.erreur), 1)[0]
        fig.update_xaxes(type="log", title=f"pas dt ({'s'})")
        fig.update_yaxes(type="log", title="erreur max sur v (m/s)")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig)
        st.markdown("En échelle log-log, la pente de chaque droite donne l'ordre de la méthode. Pentes mesurées : "
                    + " ; ".join(f"**{nom} ≈ {fmt(p, 2)}**" for nom, p in pentes.items())
                    + ". On attend 1 pour Euler et 4 pour RK4.")
    else:
        st.info("Ce cas n'a pas de solution exacte simple (frottement mixte, ouverture, ou changement de sens "
                "avec un frottement quadratique). C'est justement là que la résolution numérique est "
                "indispensable. Pour la contrôler, on vérifie que le résultat ne change plus quand on divise dt par deux.")

    st.markdown("#### 5. Le code")
    st.code(inspect.getsource(pas_euler), language="python")
    st.code(inspect.getsource(pas_rk4), language="python")
    st.code(inspect.getsource(Modele.acceleration), language="python")

with onglets[4]:
    t_, z_, v_, a_ = principal
    donnees = pd.DataFrame({"t (s)": t_, "z (m)": z_, "v (m/s)": v_, "a (m/s²)": a_})
    if exacte is not None:
        donnees["v exacte (m/s)"] = exacte[1]
    st.caption(f"{len(donnees)} points calculés avec {methodes[0]}, pas dt = {fmt(dt)} s.")
    pas_affichage = max(1, len(donnees) // 500)
    st.dataframe(donnees.iloc[::pas_affichage], height=360)
    st.download_button("Télécharger les données (CSV)", donnees.to_csv(index=False).encode("utf-8"),
                       file_name="simulation.csv", mime="text/csv")
