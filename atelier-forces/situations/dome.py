"""Objet qui glisse sur un dôme ou une bosse : pingouin sur l'igloo, skieur sur une bosse."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, deg, fr, nb, newtons, poids
from moteur.ui import choix, curseur, interrupteur, nombre

NOM = "Bosse ou dôme"
ICONE = ":material/landscape:"
AIDE = "Un objet glisse sur une surface bombée : pingouin sur un igloo, skieur sur une bosse, voiture sur un dos-d'âne."
G_ = 9.81
VITESSE = {"energie": "Partie du sommet sans vitesse", "manuel": "Je choisis la vitesse"}

_BASE = dict(nom="le pingouin", m=30.0, R=1.5, theta=30.0, mode_v="energie", v=2.0, sol=False, mu=0.1)
EXEMPLES = {
    "Pingouin sur l'igloo": dict(_BASE),
    "Juste avant le décollage": dict(_BASE, theta=47.0),
    "Skieur sur une bosse": dict(_BASE, nom="le skieur", m=75.0, R=8.0, theta=5.0, mode_v="manuel", v=7.0),
    "Voiture sur un dos-d'âne": dict(_BASE, nom="la voiture", m=1200.0, R=5.0, theta=0.0, mode_v="manuel", v=5.0),
}


def actions(k):
    interrupteur(f"{k}_sol", "Frottement de la surface")
    if st.session_state[f"{k}_sol"]:
        nombre(f"{k}_mu", "Coefficient μ", aide="Glace ≈ 0,03 ; neige ≈ 0,1.")
    st.caption("On néglige l'air : la vitesse reste modeste.")


def etat(k, p):
    nombre(f"{k}_R", "Rayon de courbure R (m)", mini=0.1)
    curseur(f"{k}_theta", "Position θ, mesurée depuis le sommet (°)", 0.0, 89.0, 0.5)
    mode = choix(f"{k}_mode_v", "Sa vitesse", VITESSE)
    if mode == "manuel":
        curseur(f"{k}_v", "Sa vitesse v (m/s)", 0.0, 30.0, 0.1)
    else:
        th = math.radians(st.session_state[f"{k}_theta"])
        v = math.sqrt(2 * G_ * st.session_state[f"{k}_R"] * (1 - math.cos(th)))
        st.caption(f"Par l'énergie (sans frottement) : v = √(2gR(1 − cos θ)) = {fr(v)} m/s.")


def construire(p):
    m, R, th = p["m"], p["R"], math.radians(p["theta"])
    P = m * G_
    v = math.sqrt(2 * G_ * R * (1 - math.cos(th))) if p["mode_v"] == "energie" else p["v"]
    mu = p["mu"] if p["sol"] else 0.0
    RN = P * math.cos(th) - m * v * v / R
    decolle = RN <= 0
    RN = max(RN, 0.0)
    RT = mu * RN if v > 1e-9 else 0.0

    d = Dessin()
    ox, oy, Rp = 300.0, 400.0, 200.0
    d.sol(24, oy, 696, oy, cote=1)
    d.chemin(f"M{ox - Rp},{oy} A{Rp},{Rp} 0 0 1 {ox + Rp},{oy}", COUL["objet_trait"], 2.2, rempl=COUL["dome"])
    d.cercle(ox, oy, 3.5, COUL["texte"])
    d.texte(ox - 4, oy + 24, "O", 14, math=True, italique=True)
    d.ligne(ox, oy, ox, oy - Rp - 30, COUL["guide"], 1, "4 4")
    if p["mode_v"] == "energie":
        tc = math.acos(2 / 3)
        xd, yd = ox + Rp * math.sin(tc), oy - Rp * math.cos(tc)
        d.cercle(xd, yd, 4.5, "#FFFFFF", COUL["alerte"], 2)
        d.texte(xd + 14, yd + 2, "décollage (cos θ = 2/3)", 12, COUL["alerte"], ancre="start")
    ur = (math.sin(th), -math.cos(th))                 # radial, vers l'extérieur
    ut = (math.cos(th), math.sin(th))                  # tangent, sens du mouvement
    ecart = 18 if decolle else 12
    px, py = ox + (Rp + ecart) * ur[0], oy + (Rp + ecart) * ur[1]
    d.ligne(ox, oy, ox + Rp * ur[0], oy + Rp * ur[1], COUL["guide"], 1, "4 4")
    d.arc(ox, oy, 54, -90, -90 + p["theta"], label="θ", label_r=70)
    d.ellipse(px, py, 11, 12, COUL["objet_trait"], angle=math.degrees(th))
    d.ellipse(px + 2 * ut[0] + 2 * ur[0], py + 2 * ut[1] + 2 * ur[1], 6, 8, "#FFFFFF", angle=math.degrees(th))

    sc = Scene(d, m, (px, py))
    Th = deg(p["theta"])
    energie = p["mode_v"] == "energie"
    sc.forces.append(poids(m, (px, py), cote=1))
    if RN > 0:
        sc.forces.append(Force(
            "Réaction normale", "R", "N", "RN", RN, (px, py), ur, "m g cos θ − m v²/R",
            "radiale, vers l'extérieur", cote=-1,
            agent="la surface du dôme", contact=True,
            formule=r"R_N = m\,g\cos\theta - m\,\dfrac{v^2}{R}",
            calcul=rf"R_N = {nb(m)} \times 9{{,}}81 \times \cos {Th} - {nb(m)} \times \dfrac{{{nb(v)}^2}}{{{nb(R)}}} = {newtons(RN)}",
            origine="On projette la loi de Newton sur le rayon, en base polaire. Le mouvement est circulaire : "
                    "l'accélération vers le centre O vaut v²/R. Donc m g cos θ − R_N = m v²/R."
                    + (" La vitesse vient de la conservation de l'énergie depuis le sommet : v² = 2 g R (1 − cos θ)."
                       if energie else ""),
            astuce="Sur une bosse, R_N est plus petite que m g : on se sent plus léger. Quand elle s'annule, il décolle."))
    if RT > 0:
        sc.forces.append(Force(
            "Frottement de la surface", "R", "T", "RT", RT, (px, py), (-ut[0], -ut[1]), "μ R_N",
            "tangent, opposé au mouvement", cote=1,
            agent="la surface du dôme", contact=True, formule=r"R_T = \mu\,R_N",
            calcul=rf"R_T = {nb(mu)} \times {nb(RN)} = {newtons(RT)}",
            origine="Loi de Coulomb : pendant le glissement, le frottement vaut μ fois la réaction normale et s'oppose "
                    "au mouvement, le long de la surface.",
            astuce="Comme R_N diminue en descendant, le frottement diminue aussi."
                   + (" Avec du frottement, la formule de l'énergie sans frottement surestime la vitesse." if energie else "")))
    sc.repere = (px + 74 * ur[0] + 40 * ut[0], py + 74 * ur[1] + 40 * ut[1], ur, ut, "uᵣ", "u_θ")
    sc.composantes = [(-ur[0], -ur[1], math.cos(th), "P cos θ"), (ut[0], ut[1], math.sin(th), "P sin θ")]
    if v > 0:
        sc.vitesse = (px + 30 * ur[0], py + 30 * ur[1], ut[0], ut[1], v / max(math.sqrt(G_ * R), 1e-9))
    sc.infos = [(f"θ = {fr(p['theta'])}°, v = {fr(v)} m/s", None),
                (f"R_N = {fr(RN / P, 2)} × P", "RN")]

    if decolle:
        sc.alertes.append("R_N s'annule : il a décollé. Il ne subit plus que son poids et suit une parabole.")
        sc.mouvement = "Plus de contact : la résultante est le **poids seul**. C'est une chute libre."
    else:
        Sr = m * v * v / R
        St = P * math.sin(th) - RT
        sc.mouvement = (f"Vers le centre O, la résultante vaut m v²/R = {fr(Sr)} N : c'est ce qui courbe la trajectoire. "
                        f"Le long de la surface, elle vaut {fr(St)} N : "
                        + ("**il accélère** en glissant." if St > 0.01 * P else
                           "**il ralentit**." if St < -0.01 * P else "la vitesse ne change pas."))
    sc.retenir = ["Sur une bosse, R_N < m g : R_N = m g cos θ − m v²/R.",
                  "Il décolle quand R_N s'annule. Parti du sommet sans vitesse et sans frottement : cos θ = 2/3 (48,2°).",
                  "Base polaire : aᵣ = −v²/R vers le centre, a_θ = dv/dt le long de la surface."]
    return sc
