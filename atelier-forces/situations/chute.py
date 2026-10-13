"""Chute verticale dans l'air ou dans un liquide."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, fr, nb, newtons, poids
from moteur.ui import choix, curseur, interrupteur, nombre

NOM = "Chute"
ICONE = ":material/paragliding:"
AIDE = "Un objet tombe ou monte verticalement : parachutiste, goutte, bille, balle lancée."
G_ = 9.81

FROTT = {"aucun": "Aucun", "lin": "Linéaire  −k₁ v", "quad": "Quadratique  −k₂ v²"}
SENS = {"descend": "Il descend", "monte": "Il monte", "immobile": "Lâché sans vitesse"}

EXEMPLES = {
    "Parachutiste": dict(nom="le parachutiste", m=80.0, frott="quad", k1=0.0, k2=0.26, archi=False,
                         rho_f=1000.0, rho_o=7800.0, sens="descend", v=40.0),
    "Parachute ouvert": dict(nom="le parachutiste", m=80.0, frott="quad", k1=0.0, k2=31.4, archi=False,
                             rho_f=1000.0, rho_o=7800.0, sens="descend", v=8.0),
    "Goutte de pluie": dict(nom="la goutte de pluie", m=4.19e-6, frott="quad", k1=0.0, k2=9.42e-7, archi=False,
                            rho_f=1000.0, rho_o=7800.0, sens="descend", v=6.6),
    "Bille dans la glycérine": dict(nom="la bille d'acier", m=3.27e-5, frott="lin", k1=0.0264, k2=0.0, archi=True,
                                    rho_f=1260.0, rho_o=7800.0, sens="descend", v=0.006),
    "Balle lancée vers le haut": dict(nom="la balle", m=0.057, frott="quad", k1=0.0, k2=0.0014, archi=False,
                                      rho_f=1000.0, rho_o=7800.0, sens="monte", v=15.0),
    "Chute dans le vide": dict(nom="la pierre", m=1.0, frott="aucun", k1=0.0, k2=0.0, archi=False,
                               rho_f=1000.0, rho_o=7800.0, sens="descend", v=10.0),
}


def _vl(p):
    m = p["m"]
    poids_app = m * G_ * (1 - (p["rho_f"] / p["rho_o"] if p["archi"] else 0))
    if p["frott"] == "lin" and p["k1"] > 0:
        return poids_app / p["k1"]
    if p["frott"] == "quad" and p["k2"] > 0:
        return math.sqrt(max(poids_app, 0) / p["k2"])
    return float("inf")


def actions(k):
    choix(f"{k}_frott", "Frottement de l'air ou du liquide", FROTT)
    f = st.session_state[f"{k}_frott"] or "aucun"
    if f == "lin":
        nombre(f"{k}_k1", "Coefficient k₁ (kg·s⁻¹)", aide="Sphère dans un liquide : k₁ = 6πηr (loi de Stokes).")
    elif f == "quad":
        nombre(f"{k}_k2", "Coefficient k₂ (kg·m⁻¹)", aide="k₂ = ½ ρ Cx S. Parachutiste à plat ≈ 0,26 ; voile ouverte ≈ 30.")
    interrupteur(f"{k}_archi", "Poussée d'Archimède (le fluide est un liquide)")
    if st.session_state[f"{k}_archi"]:
        c1, c2 = st.columns(2)
        with c1:
            nombre(f"{k}_rho_f", "ρ du fluide (kg/m³)")
        with c2:
            nombre(f"{k}_rho_o", "ρ de l'objet (kg/m³)", mini=1e-6)


def etat(k, p):
    s = choix(f"{k}_sens", "Que fait-il à cet instant ?", SENS)
    if s != "immobile":
        vl = _vl(p)
        vmax = 2 * vl if math.isfinite(vl) and vl > 0 else 80.0
        curseur(f"{k}_v", "Sa vitesse v (m/s)", 0.0, vmax, vmax / 400, "%.3g")
        if math.isfinite(vl):
            st.caption(f"Repère : la vitesse limite vaut {fr(vl)} m/s ({fr(vl * 3.6)} km/h).")


def construire(p):
    m, v, sens = p["m"], (0.0 if p["sens"] == "immobile" else p["v"]), p["sens"]
    P = m * G_
    rapport = p["rho_f"] / p["rho_o"] if p["archi"] else 0.0
    Pi = P * rapport
    k1 = p["k1"] if p["frott"] == "lin" else 0.0
    k2 = p["k2"] if p["frott"] == "quad" else 0.0
    f = k1 * v + k2 * v * v
    vl = _vl(p)

    d = Dessin()
    gx, gy = 330.0, 225.0
    if p["archi"]:
        d.rect(170, 40, 320, 390, COUL["fluide"], "#B9DCE8", 1.5, rx=10)
        d.texte(184, 66, "liquide", 13.5, "#3E7F95", ancre="start")
    d.cercle(gx, gy, 30, COUL["objet"], COUL["objet_trait"], 1.8)
    d.cercle(gx, gy, 3, COUL["texte"])
    d.texte(gx - 12, gy - 8, "G", 13, COUL["doux"], math=True, italique=True)

    sc = Scene(d, m, (gx, gy))
    vers_haut, vers_bas = (0.0, -1.0), (0.0, 1.0)
    sc.forces.append(poids(m, (gx, gy), cote=-1))
    if f > 0:
        sens_f = vers_haut if sens == "descend" else vers_bas
        if k1:
            expr, formule = "k₁ v", r"\vec f = -k_1\,\vec v \qquad f = k_1\,v"
            calcul = rf"f = {nb(k1)} \times {nb(v)} = {newtons(f)}"
            origine = ("Frottement fluide linéaire : pour un petit objet lent dans un fluide visqueux, la résistance est "
                       "proportionnelle à la vitesse. Pour une sphère de rayon r dans un fluide de viscosité η, la loi de "
                       "Stokes donne k₁ = 6πηr.")
        else:
            expr, formule = "k₂ v²", r"\vec f = -k_2\,\|\vec v\|\,\vec v \qquad f = k_2\,v^2"
            calcul = rf"f = {nb(k2)} \times {nb(v)}^2 = {newtons(f)}"
            origine = ("Frottement fluide quadratique : pour un objet rapide dans l'air, la résistance croît comme le carré "
                       "de la vitesse. Le coefficient vaut k₂ = ½ ρ Cx S (masse volumique de l'air, forme, surface frontale).")
        if math.isfinite(vl):
            astuce = (f"À la vitesse limite, le frottement compense le poids{' apparent' if Pi else ''} : "
                      f"c'est en écrivant f = {'P − Π' if Pi else 'P'} qu'on trouve v_l = {fr(vl)} m/s.")
        else:
            astuce = ""
        sc.forces.append(Force(
            "Frottement fluide", "f", None, "f", f, (gx - 9, gy), sens_f, expr,
            "verticale, opposée à la vitesse", cote=-1 if sens == "descend" else 1,
            agent="l'air" if not p["archi"] else "le liquide", contact=True,
            formule=formule, calcul=calcul, origine=origine,
            astuce=astuce + (" Comme il est opposé à la vitesse, il pointe vers le bas quand l'objet monte."
                             if sens == "monte" else "")))
    if Pi > 0:
        sc.forces.append(Force(
            "Poussée d'Archimède", "Π", None, "Pi", Pi, (gx + 12, gy), vers_haut, "ρ_fluide V g",
            "verticale, vers le haut", cote=1,
            agent="le liquide", contact=True,
            formule=r"\Pi = \rho_{\mathrm{fluide}}\,V\,g = \dfrac{\rho_{\mathrm{fluide}}}{\rho_{\mathrm{objet}}}\,m\,g",
            calcul=rf"\Pi = \dfrac{{{nb(p['rho_f'])}}}{{{nb(p['rho_o'])}}} \times {nb(m)} \times 9{{,}}81 = {newtons(Pi)}",
            origine="Théorème d'Archimède : un corps plongé dans un fluide reçoit une poussée verticale, vers le haut, "
                    "égale au poids du fluide qu'il déplace. Le volume de l'objet vient de V = m / ρ_objet.",
            astuce="Dans l'air, on la néglige presque toujours : l'air est des centaines de fois moins dense que l'objet."))

    sc.repere = (90, 100, (0.0, 1.0), (1.0, 0.0), "z", "x")
    if v > 0:
        ref = vl if math.isfinite(vl) else max(v, 1e-9)
        sc.vitesse = (gx + 140, gy - 45 if sens == "descend" else gy + 45, 0.0, 1.0 if sens == "descend" else -1.0,
                      v / (1.4 * ref))
    sc.composantes = []

    etat_txt = {"descend": f"Il descend à {fr(v)} m/s", "monte": f"Il monte à {fr(v)} m/s",
                "immobile": "Lâché sans vitesse"}[sens]
    sc.infos = [(etat_txt, None)]
    if v > 0:
        sc.infos.append((f"soit {fr(v * 3.6)} km/h", "doux"))
    if f > 0:
        sc.infos.append((f"frottement = {fr(f / P, 2)} × P", "f"))
    if Pi > 0:
        sc.infos.append((f"poussée d'Archimède = {fr(Pi / P, 2)} × P", "Pi"))

    # La résultante sur l'axe vertical, orienté vers le bas
    S = P - Pi + (-f if sens == "descend" else f)
    if abs(S) < 0.01 * P:
        sc.mouvement = ("Les forces se compensent : ΣF = 0. Il tombe à vitesse constante, c'est la **vitesse limite**.")
    elif sens == "descend":
        sc.mouvement = (f"La résultante vaut {fr(abs(S))} N, vers le **{'bas' if S > 0 else 'haut'}**. "
                        + ("Elle est dans le sens du mouvement : **il accélère**" if S > 0 else
                           "Elle est opposée au mouvement : **il ralentit**")
                        + f" (a = {fr(abs(S) / m)} m/s²)."
                        + (f" Il tend vers la vitesse limite {fr(vl)} m/s." if math.isfinite(vl) else ""))
    elif sens == "monte":
        sc.mouvement = (f"Le poids et le frottement sont tous les deux vers le bas : la résultante vaut {fr(abs(S))} N, "
                        f"opposée au mouvement. **Il ralentit** (a = {fr(abs(S) / m)} m/s²), puis retombera.")
    else:
        sc.mouvement = (f"Sans vitesse, pas de frottement fluide. La résultante vaut {fr(S)} N vers le bas : "
                        f"**il commence à tomber** avec a = {fr(S / m)} m/s².")
    sc.retenir = ["Le frottement fluide est toujours opposé à la vitesse : il change de sens si l'objet monte.",
                  "Il grandit avec la vitesse jusqu'à compenser le poids : c'est la vitesse limite."]
    if Pi > 0:
        sc.retenir.append("Dans un liquide, la poussée d'Archimède ρ_fluide V g allège l'objet.")
    if rapport >= 1:
        sc.alertes.append("L'objet est moins dense que le fluide : il flotte et remonte.")
    return sc
