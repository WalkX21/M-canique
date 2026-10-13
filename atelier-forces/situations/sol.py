"""Objet sur un sol horizontal : cycliste, voiture, caisse tirée, palet."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, deg, fr, nb, newtons, poids
from moteur.ui import choix, curseur, interrupteur, nombre

NOM = "Sol plat"
ICONE = ":material/directions_bike:"
AIDE = "Un objet sur un sol horizontal : cycliste, voiture, caisse tirée par une corde, palet."
G_ = 9.81
FORMES = {"velo": "Vélo", "voiture": "Voiture", "caisse": "Caisse", "palet": "Palet"}
MVT = {"avance": "Il avance", "immobile": "Il est immobile"}

_BASE = dict(nom="le cycliste et son vélo", m=85.0, forme="velo", moteur=True, F=60.0, F_auto=True, corde=False,
             T=80.0, beta=30.0, sol=True, mu=0.004, air=True, k2=0.15, mvt="avance", v=15.0)
EXEMPLES = {
    "Cycliste lancé": dict(_BASE),
    "Voiture sur autoroute": dict(_BASE, nom="la voiture", m=1200.0, forme="voiture", mu=0.012, k2=0.4, v=36.0),
    "Voiture qui freine": dict(_BASE, nom="la voiture", m=1200.0, forme="voiture", moteur=False, mu=0.8, k2=0.4, v=25.0),
    "Caisse tirée par une corde": dict(_BASE, nom="la caisse", m=20.0, forme="caisse", moteur=False, corde=True,
                                       T=80.0, beta=30.0, mu=0.35, air=False, v=1.0),
    "Caisse qui résiste": dict(_BASE, nom="la caisse", m=20.0, forme="caisse", moteur=False, corde=True, T=40.0,
                               beta=30.0, mu=0.35, air=False, mvt="immobile", v=0.0),
    "Palet de hockey lancé": dict(_BASE, nom="le palet", m=0.17, forme="palet", moteur=False, mu=0.05, air=False, v=10.0),
}


def actions(k):
    choix(f"{k}_forme", "Dessin de l'objet", FORMES)
    interrupteur(f"{k}_moteur", "Force motrice (le sol pousse la roue motrice)")
    if st.session_state[f"{k}_moteur"]:
        interrupteur(f"{k}_F_auto", "Force réglée pour une vitesse constante")
        if not st.session_state[f"{k}_F_auto"]:
            nombre(f"{k}_F", "Force motrice F (N)")
    interrupteur(f"{k}_corde", "Une corde le tire")
    if st.session_state[f"{k}_corde"]:
        c1, c2 = st.columns(2)
        with c1:
            nombre(f"{k}_T", "Tension T (N)")
        with c2:
            curseur(f"{k}_beta", "Angle avec le sol (°)", 0.0, 80.0, 1.0)
    interrupteur(f"{k}_sol", "Frottement du sol")
    if st.session_state[f"{k}_sol"]:
        nombre(f"{k}_mu", "Coefficient μ",
               aide="Caisse qui glisse ≈ 0,3 ; roues bloquées sur route ≈ 0,8 ; roue qui roule ≈ 0,004 à 0,012.")
    interrupteur(f"{k}_air", "Frottement de l'air  −k₂ v²")
    if st.session_state[f"{k}_air"]:
        nombre(f"{k}_k2", "Coefficient k₂ (kg·m⁻¹)", aide="Cycliste ≈ 0,15 à 0,30 ; voiture ≈ 0,4.")


def etat(k, p):
    s = choix(f"{k}_mvt", "Que fait-il à cet instant ?", MVT)
    if s != "immobile":
        curseur(f"{k}_v", "Sa vitesse v (m/s)", 0.0, 60.0, 0.1)
        st.caption(f"Soit {fr(st.session_state[f'{k}_v'] * 3.6)} km/h.")


def _decor(d, forme, ys):
    """Dessine l'objet ; renvoie G, contact arrière, contact avant, point d'attache avant, haut avant."""
    if forme == "velo":
        r, xa, xv = 40, 250, 450
        for xr in (xa, xv):
            d.cercle(xr, ys - r, r, "none", COUL["objet_trait"], 2.2)
        A, V = (xa, ys - r), (xv, ys - r)
        B, S, H = (345, ys - r + 4), (318, ys - 128), (425, ys - 132)
        for p1, p2 in ((A, S), (S, B), (B, A), (S, H), (H, V), (B, H)):
            d.ligne(*p1, *p2, COUL["objet_trait"], 2.6)
        Sh = (402, ys - 175)
        d.ligne(*S, *Sh, COUL["objet_trait"], 4.5)
        d.ligne(*Sh, *H, COUL["objet_trait"], 2.6)
        d.cercle(424, ys - 190, 14, COUL["objet"], COUL["objet_trait"], 2)
        return (352, ys - 140), (xa, ys), (xv, ys), (xv + 20, ys - 90), Sh
    if forme == "voiture":
        corps = [(190, ys - 34), (190, ys - 82), (262, ys - 90), (318, ys - 140), (452, ys - 140),
                 (500, ys - 92), (548, ys - 84), (548, ys - 34)]
        d.polygone(corps, COUL["objet"], COUL["objet_trait"], 2)
        d.polygone([(330, ys - 130), (440, ys - 130), (478, ys - 94), (300, ys - 94)], "#FFFFFF", COUL["objet_trait"], 1.2)
        for xr in (262, 476):
            d.cercle(xr, ys - 30, 30, "#FFFFFF", COUL["objet_trait"], 2.2)
            d.cercle(xr, ys - 30, 10, COUL["objet"], COUL["objet_trait"], 1.5)
        return (370, ys - 78), (262, ys), (476, ys), (548, ys - 60), (520, ys - 110)
    if forme == "caisse":
        d.rect(280, ys - 120, 170, 120, COUL["objet"], COUL["objet_trait"], 2, rx=3)
        d.ligne(280, ys - 120, 450, ys, COUL["guide"], 1)
        d.ligne(450, ys - 120, 280, ys, COUL["guide"], 1)
        return (365, ys - 60), (300, ys), (430, ys), (450, ys - 60), (450, ys - 100)
    d.rect(300, ys - 26, 130, 26, COUL["objet_trait"], None, rx=6)
    d.rect(300, ys - 26, 130, 9, "#6B7392", None, rx=6)
    return (365, ys - 13), (320, ys), (410, ys), (430, ys - 13), (430, ys - 20)


def construire(p):
    m = p["m"]
    P = m * G_
    v = 0.0 if p["mvt"] == "immobile" else p["v"]
    mu = p["mu"] if p["sol"] else 0.0
    k2 = p["k2"] if p["air"] else 0.0
    T = p["T"] if p["corde"] else 0.0
    b = math.radians(p["beta"]) if p["corde"] else 0.0
    alertes = []
    RN = P - T * math.sin(b)
    if RN < 0:
        alertes.append("La corde le soulève : il n'appuie plus sur le sol.")
        RN = 0.0
    f = k2 * v * v
    traction = T * math.cos(b)
    if p["mvt"] == "immobile":
        F = p["F"] if (p["moteur"] and not p["F_auto"]) else 0.0
        RT = F + traction
        if RT > mu * RN + 1e-9:
            alertes.append(f"Il ne peut pas rester immobile : il faudrait un frottement de {fr(RT)} N, "
                           f"le sol n'en fournit que μ R_N = {fr(mu * RN)} N. Il démarre.")
    else:
        RT = mu * RN
        if p["moteur"]:
            F = (RT + f - traction) if p["F_auto"] else p["F"]
            if F < 0:
                alertes.append("La corde suffit à compenser les frottements : pas besoin de moteur.")
                F = 0.0
        else:
            F = 0.0

    d = Dessin()
    ys = {"velo": 345.0, "voiture": 335.0, "caisse": 320.0, "palet": 300.0}[p["forme"]]
    d.sol(24, ys, 696, ys, cote=1)
    G, arr, av, attache, haut = _decor(d, p["forme"], ys)
    gx, gy = G
    d.cercle(gx, gy, 4, COUL["texte"])
    d.texte(gx - 14, gy - 9, "G", 13, COUL["doux"], math=True, italique=True)

    sc = Scene(d, m, G, alertes=alertes)
    B = deg(p["beta"])
    roule = p["forme"] in ("velo", "voiture")
    sc.forces.append(poids(m, (gx, gy), cote=1))

    if T:
        f_RN = r"R_N = m\,g - T\sin\beta"
        c_RN = rf"R_N = {nb(m)} \times 9{{,}}81 - {nb(T)} \times \sin {B} = {newtons(RN)}"
    else:
        f_RN, c_RN = r"R_N = m\,g", rf"R_N = {nb(m)} \times 9{{,}}81 = {newtons(RN)}"
    sc.forces.append(Force(
        "Réaction normale du sol", "R", "N", "RN", RN, (gx + 16, ys), (0.0, -1.0),
        "m g" + (" − T sin β" if T else ""), "verticale, vers le haut", cote=1,
        agent="le sol", contact=True, formule=f_RN, calcul=c_RN,
        origine="Il n'y a pas de mouvement vertical : la loi de Newton projetée sur la verticale donne "
                "0 = R_N − m g" + (" + T sin β : la corde, en tirant un peu vers le haut, soulage le sol." if T else "."),
        astuce="Sur un vélo ou une voiture, elle se répartit entre les roues ; le schéma montre leur somme."))

    if F > 0:
        if p["F_auto"] and p["mvt"] != "immobile":
            f_F = r"F = R_T + f" + (r" - T\cos\beta" if T else "")
            c_F = rf"F = {nb(RT)} + {nb(f)}" + (rf" - {nb(traction)}" if T else "") + rf" = {newtons(F)}"
            ori_F = ("Elle est réglée pour une vitesse constante : la loi de Newton projetée sur l'horizontale avec a = 0 "
                     "donne F = R_T + f" + (" − T cos β" if T else "") + ". Elle compense exactement les frottements.")
        else:
            f_F, c_F = r"F \text{ (donnée)}", rf"F = {newtons(F)}"
            ori_F = "C'est une donnée de l'énoncé : la valeur choisie dans les réglages."
        sc.forces.append(Force(
            "Force motrice", "F", None, "F", F, arr, (1.0, 0.0), "action du sol sur la roue",
            "horizontale, vers l'avant", cote=1,
            agent="le sol, sur la roue motrice", contact=True, formule=f_F, calcul=c_F, origine=ori_F,
            astuce="Ce n'est pas le moteur ni les jambes qui poussent le véhicule : ce sont des forces intérieures. "
                   "La roue pousse le sol vers l'arrière, et le sol pousse la roue vers l'avant."))

    if T > 0:
        sc.forces.append(Force(
            "Tension de la corde", "T", None, "T", T, attache, (math.cos(b), -math.sin(b)), "T",
            f"le long de la corde, à {fr(p['beta'])}° du sol", cote=-1,
            agent="la corde", contact=True,
            formule=r"T_x = T\cos\beta \qquad T_y = T\sin\beta",
            calcul=rf"T_x = {nb(T)} \times \cos {B} = {newtons(T * math.cos(b))} \qquad "
                   rf"T_y = {nb(T)} \times \sin {B} = {newtons(T * math.sin(b))}",
            origine="La tension est une donnée de l'énoncé. Elle est dirigée le long de la corde : on la projette sur "
                    "l'horizontale (ce qui fait avancer) et sur la verticale (ce qui soulage le sol).",
            astuce="Tirer avec une corde inclinée fait avancer moins efficacement, mais diminue R_N, donc le frottement."))
        d.ligne(*attache, attache[0] + 400 * math.cos(b), attache[1] - 400 * math.sin(b), COUL["guide"], 1.6)

    if RT > 1e-9:
        if p["mvt"] == "immobile":
            f_RT = r"R_T = F + T\cos\beta \;\le\; \mu R_N" if T else r"R_T = F \;\le\; \mu R_N"
            c_RT = (rf"R_T = {newtons(RT)} \qquad \mu R_N = {nb(mu)} \times {nb(RN)} = {newtons(mu * RN)}")
            ori_RT = ("Tant qu'il ne bouge pas, c'est un frottement d'adhérence : il compense exactement ce qui tire vers "
                      "l'avant, sans dépasser μ R_N.")
        else:
            f_RT, c_RT = r"R_T = \mu\,R_N", rf"R_T = {nb(mu)} \times {nb(RN)} = {newtons(RT)}"
            ori_RT = ("Loi de Coulomb : pendant le glissement, le frottement vaut μ fois la réaction normale et s'oppose "
                      "au mouvement." + (" Pour une roue qui roule sans glisser, μ représente la résistance au roulement, "
                                         "beaucoup plus faible (0,004 à 0,012)." if roule else ""))
        sc.forces.append(Force(
            "Frottement du sol", "R", "T", "RT", RT, av, (-1.0, 0.0),
            "μ R_N" if p["mvt"] != "immobile" else "adhérence", "horizontale, vers l'arrière", cote=-1,
            agent="le sol", contact=True, formule=f_RT, calcul=c_RT, origine=ori_RT,
            astuce=("Une voiture qui freine roues bloquées glisse : μ ≈ 0,8 sur route sèche, mais 0,4 seulement sous la pluie."
                    if roule else
                    "Le frottement solide ne dépend pas de l'aire de contact : poser la caisse sur une autre face "
                    "ne change pas R_T. Seules comptent R_N et la nature des surfaces (μ).")))

    if f > 0:
        sc.forces.append(Force(
            "Frottement de l'air", "f", None, "f", f, haut, (-1.0, 0.0), "k₂ v²", "horizontale, vers l'arrière", cote=1,
            agent="l'air", contact=True, formule=r"\vec f = -k_2\,\|\vec v\|\,\vec v \qquad f = k_2\,v^2",
            calcul=rf"f = {nb(k2)} \times {nb(v)}^2 = {newtons(f)}",
            origine="Frottement fluide quadratique : il croît comme le carré de la vitesse, avec k₂ = ½ ρ Cx S. "
                    "Doubler la vitesse multiplie ce frottement par quatre.",
            astuce="C'est lui qui limite la vitesse d'un cycliste : c'est ce qui manquait au modèle du vélodrome."))

    sc.repere = (64, 70, (1.0, 0.0), (0.0, -1.0), "x", "y")
    if v > 0:
        sc.vitesse = (560, 150, 1.0, 0.0, v / 40)
    sc.infos = [(f"Il avance à {fr(v)} m/s" if v > 0 else "Il est immobile", None)]
    if v > 0:
        sc.infos.append((f"soit {fr(v * 3.6)} km/h", "doux"))

    Sx = F + traction - (RT if p["mvt"] != "immobile" else 0.0) - f
    if p["mvt"] == "immobile":
        sc.mouvement = ("Le frottement d'adhérence compense ce qui le tire vers l'avant : **ΣF = 0**, il reste immobile."
                        if not alertes else "Le frottement ne suffit pas : **il se met en mouvement**.")
    elif abs(Sx) < 0.01 * P:
        sc.mouvement = ("Verticalement, R_N compense le poids. Horizontalement, la force motrice compense les frottements : "
                        "**ΣF = 0**, il roule à vitesse constante." if F > 0 else
                        "Les forces se compensent : **ΣF = 0**, il avance à vitesse constante.")
    else:
        sc.mouvement = (f"La résultante est horizontale et vaut {fr(abs(Sx))} N vers l'**{'avant' if Sx > 0 else 'arrière'}** : "
                        + ("**il accélère**" if Sx > 0 else "**il ralentit**") + f" (a = {fr(abs(Sx) / m)} m/s²).")
    sc.retenir = ["Sur un sol plat, R_N = m g, sauf si une force tire vers le haut (corde inclinée : R_N = m g − T sin β).",
                  "Ce qui fait avancer un vélo ou une voiture, c'est le sol : il pousse la roue motrice vers l'avant."]
    return sc
