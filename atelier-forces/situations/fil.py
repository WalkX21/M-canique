"""Pendule : un objet au bout d'un fil."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, deg, fr, nb, newtons, poids
from moteur.ui import choix, curseur, interrupteur, nombre

NOM = "Pendule"
ICONE = ":material/swap_horiz:"
AIDE = "Un objet suspendu à un fil qui oscille : pendule de TP, balançoire, parachutiste sous sa voile."
G_ = 9.81
SENS = {"gauche": "Il va vers la gauche", "droite": "Il va vers la droite"}

_BASE = dict(nom="la masse du pendule", m=0.2, l=1.0, theta0=30.0, theta=12.0, sens="gauche", air=False, k1=0.05)
EXEMPLES = {
    "Pendule de TP": dict(_BASE),
    "En bas de la trajectoire": dict(_BASE, theta=0.0),
    "À l'extrémité": dict(_BASE, theta=30.0),
    "Balançoire": dict(_BASE, nom="l'enfant sur la balançoire", m=25.0, l=2.5, theta0=40.0, theta=0.0, sens="droite"),
    "Parachutiste sous sa voile": dict(_BASE, nom="le parachutiste", m=80.0, l=6.0, theta0=15.0, theta=8.0),
}


def actions(k):
    interrupteur(f"{k}_air", "Frottement de l'air  −k₁ v")
    if st.session_state[f"{k}_air"]:
        nombre(f"{k}_k1", "Coefficient k₁ (kg·s⁻¹)")
    st.caption("Le fil est supposé tendu, de masse négligeable.")


def etat(k, p):
    nombre(f"{k}_l", "Longueur du fil ℓ (m)", mini=0.01)
    curseur(f"{k}_theta0", "Amplitude θ₀ : angle de lâcher (°)", 1.0, 170.0, 1.0)
    t0 = st.session_state[f"{k}_theta0"]
    curseur(f"{k}_theta", "Position actuelle θ (°)", -t0, t0, 0.5)
    if abs(abs(st.session_state[f"{k}_theta"]) - t0) > 1e-6:
        choix(f"{k}_sens", "Sens du mouvement", SENS)


def construire(p):
    m, l = p["m"], p["l"]
    P = m * G_
    t0, th = math.radians(p["theta0"]), math.radians(p["theta"])
    v = math.sqrt(max(0.0, 2 * G_ * l * (math.cos(th) - math.cos(t0))))
    T = P * math.cos(th) + m * v * v / l
    f = (p["k1"] * v) if p["air"] else 0.0

    d = Dessin()
    grand = p["theta0"] > 80
    ox, oy = 360.0, (215.0 if grand else 46.0)
    Lp = 165.0 if grand else 262.0
    d.ligne(ox - 80, oy, ox + 80, oy, COUL["sol"], 2.4)
    for i in range(-6, 7):
        d.ligne(ox + 12 * i, oy, ox + 12 * i - 7, oy - 9, COUL["guide"], 1)
    d.ligne(ox, oy, ox, oy + Lp + 34, COUL["guide"], 1, "4 4")
    d.arc(ox, oy, Lp, 90 - p["theta0"], 90 + p["theta0"], COUL["guide"], 1.2, tirets="3 5")
    bx, by = ox + Lp * math.sin(th), oy + Lp * math.cos(th)
    d.ligne(ox, oy, bx, by, COUL["objet_trait"], 2)
    d.cercle(ox, oy, 4, COUL["texte"])
    d.texte(ox - 14, oy - 10, "O", 14, math=True, italique=True)
    if abs(th) > 0.01:
        a_fil = math.degrees(math.atan2(by - oy, bx - ox))
        d.arc(ox, oy, 58, min(90, a_fil), max(90, a_fil), label="θ", label_r=76)
    d.cercle(bx, by, 16, COUL["objet"], COUL["objet_trait"], 2)
    d.cercle(bx, by, 3, COUL["texte"])

    er = (math.sin(th), math.cos(th))                  # de O vers la masse
    et = (math.cos(th), -math.sin(th))                 # sens des θ croissants (vers la droite en bas)
    s = 1 if p["sens"] == "droite" else -1
    sc = Scene(d, m, (bx, by))
    Th, T0 = deg(abs(p["theta"])), deg(p["theta0"])
    sc.forces.append(poids(m, (bx, by), cote=1))
    sc.forces.append(Force(
        "Tension du fil", "T", None, "T", max(T, 0.0), (bx, by), (-er[0], -er[1]),
        "m g cos θ + m v²/ℓ", "le long du fil, vers O", cote=1,
        agent="le fil", contact=True,
        formule=r"T = m\,g\cos\theta + m\,\dfrac{v^2}{\ell} \qquad v^2 = 2\,g\,\ell\,(\cos\theta - \cos\theta_0)",
        calcul=(rf"v^2 = 2 \times 9{{,}}81 \times {nb(l)} \times (\cos {Th} - \cos {T0}) = {nb(v * v)}\ \mathrm{{m^2/s^2}}"
                rf"\\[4pt] T = {nb(m)} \times 9{{,}}81 \times \cos {Th} + {nb(m)} \times \dfrac{{{nb(v * v)}}}{{{nb(l)}}} = {newtons(T)}"),
        origine="On projette la loi de Newton sur le fil, vers O. La masse décrit un cercle de rayon ℓ : son accélération "
                "vers O vaut v²/ℓ. Donc T − m g cos θ = m v²/ℓ. La vitesse vient de la conservation de l'énergie "
                "depuis le point de lâcher θ₀.",
        astuce=f"La tension n'est égale au poids qu'au repos. En bas, elle vaut m g (3 − 2 cos θ₀) = "
               f"{fr(P * (3 - 2 * math.cos(t0)))} N : c'est là que le fil risque de casser."))
    if f > 0:
        sc.forces.append(Force(
            "Frottement de l'air", "f", None, "f", f, (bx, by), (-s * et[0], -s * et[1]), "k₁ v",
            "tangent, opposé à la vitesse", cote=-1,
            agent="l'air", contact=True, formule=r"\vec f = -k_1\,\vec v \qquad f = k_1\,v",
            calcul=rf"f = {nb(p['k1'])} \times {nb(v)} = {newtons(f)}",
            origine="Frottement fluide linéaire, adapté aux petites vitesses : proportionnel à la vitesse, opposé au "
                    "mouvement. C'est lui qui amortit les oscillations.",
            astuce="On a calculé v avec l'énergie sans frottement : avec frottement, c'est une bonne approximation "
                   "seulement sur la première oscillation."))
    sc.repere = (bx + 70 * er[0] - 60 * et[0], by + 70 * er[1] - 60 * et[1], er, et, "e_r", "e_θ")
    sc.composantes = [(er[0], er[1], math.cos(th), "P cos θ"),
                      ((-1 if th > 0 else 1) * et[0], (-1 if th > 0 else 1) * et[1], abs(math.sin(th)), "P sin θ")]
    if v > 1e-9:
        sc.vitesse = (bx + 26 * er[0], by + 26 * er[1], s * et[0], s * et[1], v / max(math.sqrt(2 * G_ * l * (1 - math.cos(t0))), 1e-9))
    sc.infos = [(f"θ = {fr(p['theta'])}°, v = {fr(v)} m/s", None), (f"tension T = {fr(T / P, 2)} × P", "T")]

    if T < 0:
        sc.alertes.append("La tension calculée est négative : un vrai fil se détendrait. Il faudrait une tige rigide.")
    Sr = m * v * v / l
    sc.mouvement = (("En ce point v = 0 : la résultante est **tangente**, elle vaut m g sin θ0 et ramène la masse vers le bas."
                     if v < 1e-9 else
                     f"Vers O, la résultante vaut m v²/ℓ = {fr(Sr)} N : elle n'est **pas nulle, même en bas**, "
                     "car la trajectoire est un cercle. "
                     + (f"Le long de la trajectoire, la composante m g sin θ = {fr(P * abs(math.sin(th)))} N "
                        "ramène la masse vers la verticale." if abs(th) > 0.01 else
                        "En bas, la composante tangente du poids est nulle : la vitesse est maximale.")))
    sc.retenir = ["La tension ne vaut pas le poids : T = m g cos θ + m v²/ℓ. Elle est maximale en bas.",
                  "Aux extrémités, v = 0 ; en bas, la vitesse est maximale.",
                  "Aux petits angles, sin θ ≈ θ : θ̈ + (g/ℓ) θ = 0, période T₀ = 2π√(ℓ/g)."]
    return sc
