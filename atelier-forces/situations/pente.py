"""Objet sur un plan incliné : skieur, luge, caisse, téléski."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, deg, fr, nb, newtons, poids
from moteur.ui import choix, curseur, interrupteur, nombre

NOM = "Pente"
ICONE = ":material/downhill_skiing:"
AIDE = "Un objet sur un plan incliné : skieur, luge, caisse, skieur tiré par un téléski."
G_ = 9.81
SENS = {"descend": "Il descend", "monte": "Il monte", "immobile": "Il est immobile"}

_BASE = dict(nom="le skieur", m=75.0, alpha=20.0, sol=True, mu=0.05, air=True, k2=0.30, cable=False,
             gamma=20.0, T=300.0, T_auto=True, sens="descend", v=15.0)
EXEMPLES = {
    "Skieur qui descend": dict(_BASE),
    "Luge": dict(_BASE, nom="la luge et l'enfant", m=45.0, alpha=15.0, mu=0.08, k2=0.15, v=8.0),
    "Caisse immobile": dict(_BASE, nom="la caisse", m=10.0, alpha=15.0, mu=0.4, air=False, sens="immobile", v=0.0),
    "Caisse qui glisse": dict(_BASE, nom="la caisse", m=10.0, alpha=30.0, mu=0.3, air=False, v=2.0),
    "Skieur au téléski": dict(_BASE, alpha=15.0, air=False, cable=True, gamma=25.0, T_auto=True, sens="monte", v=3.0),
    "Sans aucun frottement": dict(_BASE, sol=False, air=False),
}


def actions(k):
    interrupteur(f"{k}_sol", "Frottement du support (neige, sol)")
    if st.session_state[f"{k}_sol"]:
        nombre(f"{k}_mu", "Coefficient de frottement μ",
               aide="Loi de Coulomb : quand ça glisse, R_T = μ R_N. Ski fartés ≈ 0,05 ; bois sur bois ≈ 0,3.")
    interrupteur(f"{k}_air", "Frottement de l'air  −k₂ v²")
    if st.session_state[f"{k}_air"]:
        nombre(f"{k}_k2", "Coefficient k₂ (kg·m⁻¹)", aide="Skieur debout ≈ 0,30 ; en position de l'œuf ≈ 0,12.")
    interrupteur(f"{k}_cable", "Un câble le tire (téléski, corde)")
    if st.session_state[f"{k}_cable"]:
        curseur(f"{k}_gamma", "Angle du câble avec la pente (°)", 0.0, 80.0, 1.0)
        interrupteur(f"{k}_T_auto", "Tension réglée pour une vitesse constante")
        if not st.session_state[f"{k}_T_auto"]:
            nombre(f"{k}_T", "Tension du câble T (N)")


def etat(k, p):
    curseur(f"{k}_alpha", "Inclinaison de la pente α (°)", 0.0, 60.0, 0.5)
    s = choix(f"{k}_sens", "Que fait-il à cet instant ?", SENS)
    if s != "immobile":
        curseur(f"{k}_v", "Sa vitesse v (m/s)", 0.0, 50.0, 0.1)


def construire(p):
    m, a = p["m"], math.radians(p["alpha"])
    P = m * G_
    sens = p["sens"]
    v = 0.0 if sens == "immobile" else p["v"]
    mu = p["mu"] if p["sol"] else 0.0
    k2 = p["k2"] if p["air"] else 0.0
    gam = math.radians(p["gamma"]) if p["cable"] else 0.0
    ca, sa = math.cos(a), math.sin(a)
    alertes = []

    # Tension du câble
    T = 0.0
    if p["cable"]:
        if p["T_auto"]:
            if sens == "immobile":
                T = P * sa / math.cos(gam)
            else:
                s = -1 if sens == "descend" else 1        # signe du frottement le long de la descente
                T = (P * sa + s * (mu * P * ca + k2 * v * v)) / (math.cos(gam) + s * mu * math.sin(gam))
            if T < 0:
                alertes.append("Les frottements suffisent déjà à le freiner : le câble n'a rien à tirer (T = 0).")
                T = 0.0
        else:
            T = p["T"]
    RN = P * ca - T * math.sin(gam)
    if RN < 0:
        alertes.append("Le câble tire si fort qu'il le soulève : il n'est plus en contact avec la pente.")
        RN = 0.0

    # Frottement du support
    descente = P * sa - T * math.cos(gam)        # ce qui le pousse vers le bas de la pente
    if sens == "immobile":
        RT = abs(descente)
        dir_RT = -1 if descente > 0 else 1         # -1 : vers le haut de la pente
        if RT > mu * RN + 1e-9:
            alertes.append(f"Il ne peut pas rester immobile : il faudrait un frottement de {fr(RT)} N, "
                           f"mais le support ne peut en fournir que μ R_N = {fr(mu * RN)} N. Il glisse.")
    else:
        RT = mu * RN
        dir_RT = -1 if sens == "descend" else 1
    f = k2 * v * v
    dir_mvt = 1 if sens == "descend" else -1

    # --- dessin -------------------------------------------------------------
    d = Dessin()
    dx, dy = ca, sa                     # vers le bas de la pente
    nx, ny = sa, -ca                    # normale sortante
    cx, cy = 330.0, 262.0
    haut = min(300.0, (cy - 24) / max(sa, 1e-6), (cx - 24) / ca)
    bas = min(340.0, (460 - 24 - cy) / max(sa, 1e-6), (720 - 24 - cx) / ca)
    d.sol(cx - haut * dx, cy - haut * dy, cx + bas * dx, cy + bas * dy, cote=1)
    if p["alpha"] >= 1:
        axp, ayp = cx + 0.82 * bas * dx, cy + 0.82 * bas * dy
        d.ligne(axp - 150, ayp, axp, ayp, COUL["guide"], 1.2, "4 4")
        d.arc(axp, ayp, 54, 180, 180 + p["alpha"], label="α", label_r=70)

    gx, gy = cx + 50 * nx, cy + 50 * ny
    coins = [(gx + sx * 30 * dx + sy * 50 * nx, gy + sx * 30 * dy + sy * 50 * ny)
             for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    d.polygone(coins, COUL["objet"], COUL["objet_trait"], 1.8)
    d.cercle(gx, gy, 3, COUL["texte"])
    d.texte(gx - 10 * dx + 14 * nx, gy - 10 * dy + 14 * ny + 4, "G", 13, COUL["doux"], math=True, italique=True)

    sc = Scene(d, m, (gx, gy), alertes=alertes)
    A = deg(p["alpha"])
    sc.forces.append(poids(m, (gx, gy), cote=-1))

    # Réaction normale
    if T:
        f_RN, c_RN = (r"R_N = m\,g\cos\alpha - T\sin\gamma",
                      rf"R_N = {nb(m)} \times 9{{,}}81 \times \cos {A} - {nb(T)} \times \sin {deg(p['gamma'])} = {newtons(RN)}")
    else:
        f_RN, c_RN = (r"R_N = m\,g\cos\alpha", rf"R_N = {nb(m)} \times 9{{,}}81 \times \cos {A} = {newtons(RN)}")
    sc.forces.append(Force(
        "Réaction normale", "R", "N", "RN", RN, (cx, cy), (nx, ny),
        "m g cos α" + (" − T sin γ" if T else ""), "perpendiculaire à la pente", cote=-1,
        agent="la pente", contact=True, formule=f_RN, calcul=c_RN,
        origine="Il n'y a pas de mouvement perpendiculaire à la pente. La loi de Newton projetée sur (Oy) donne donc "
                "0 = R_N − m g cos α" + (" + T sin γ, car le câble tire un peu vers le haut" if T else "") + ". "
                "La réaction ne compense que la partie du poids qui appuie sur la pente.",
        astuce="Sur une pente, R_N n'est pas égale au poids : elle vaut m g cos α, plus petite que m g."))

    # Frottement du support
    if RT > 1e-9:
        pt = (cx - 32 * dx, cy - 32 * dy) if dir_RT < 0 else (cx + 32 * dx, cy + 32 * dy)
        if sens == "immobile":
            if T:
                f_RT = r"R_T = \left|\,m\,g\sin\alpha - T\cos\gamma\,\right| \;\le\; \mu R_N"
                c_RT = (rf"R_T = \left|{nb(m)} \times 9{{,}}81 \times \sin {A} - {nb(T)} \times \cos {deg(p['gamma'])}\right|"
                        rf" = {newtons(RT)}")
            else:
                f_RT = r"R_T = m\,g\sin\alpha \;\le\; \mu R_N"
                c_RT = rf"R_T = {nb(m)} \times 9{{,}}81 \times \sin {A} = {newtons(RT)}"
            c_RT += rf"\qquad \mu R_N = {nb(mu)} \times {nb(RN)} = {newtons(mu * RN)}"
            ori_RT = ("Tant qu'il ne glisse pas, c'est un frottement d'adhérence : il prend exactement la valeur qui "
                      "empêche le glissement (loi de Newton projetée sur (Ox) avec a = 0). Il ne peut pas dépasser "
                      "μ R_N : au-delà, l'objet se met à glisser.")
        else:
            f_RT, c_RT = r"R_T = \mu\,R_N", rf"R_T = {nb(mu)} \times {nb(RN)} = {newtons(RT)}"
            ori_RT = ("Loi de Coulomb du frottement solide : pendant le glissement, le frottement vaut μ fois la réaction "
                      "normale et s'oppose au glissement. Il ne dépend pas de la vitesse.")
        sc.forces.append(Force(
            "Frottement du support", "R", "T", "RT", RT, pt, (dir_RT * dx, dir_RT * dy),
            "μ R_N" if sens != "immobile" else "adhérence",
            "le long de la pente, vers le " + ("haut" if dir_RT < 0 else "bas"), cote=1 if dir_RT < 0 else -1,
            agent="la pente (neige, sol)", contact=True, formule=f_RT, calcul=c_RT, origine=ori_RT,
            astuce="R_N et R_T sont les deux composantes d'une seule force : la réaction de la pente. "
                   "On les sépare pour projeter plus facilement."))

    # Frottement de l'air
    if f > 0:
        sc.forces.append(Force(
            "Frottement de l'air", "f", None, "f", f,
            (gx + 46 * nx - dir_mvt * 30 * dx, gy + 46 * ny - dir_mvt * 30 * dy),
            (-dir_mvt * dx, -dir_mvt * dy), "k₂ v²", "opposé à la vitesse", cote=-1,
            agent="l'air", contact=True, formule=r"\vec f = -k_2\,\|\vec v\|\,\vec v \qquad f = k_2\,v^2",
            calcul=rf"f = {nb(k2)} \times {nb(v)}^2 = {newtons(f)}",
            origine="Frottement fluide quadratique : pour un objet de la taille d'un humain qui va vite dans l'air, la "
                    "résistance croît comme le carré de la vitesse. Le coefficient k₂ = ½ ρ Cx S dépend de la posture "
                    "(surface S et forme Cx).",
            astuce="Il est opposé à la vitesse, pas forcément vers le haut de la pente : si l'objet monte, il pointe vers le bas."))

    # Tension du câble
    if T > 0:
        ux, uy = -dx * math.cos(gam) + nx * math.sin(gam), -dy * math.cos(gam) + ny * math.sin(gam)
        ax_, ay_ = gx - 30 * dx + 12 * nx, gy - 30 * dy + 12 * ny
        d.ligne(ax_, ay_, ax_ + ux * 400, ay_ + uy * 400, COUL["guide"], 1.6)
        if p["T_auto"] and sens != "immobile":
            sg = "+" if sens == "monte" else "-"
            f_T = (rf"T = \dfrac{{m\,g\sin\alpha {sg} \left(\mu\,m\,g\cos\alpha + k_2 v^2\right)}}"
                   rf"{{\cos\gamma {sg} \mu\sin\gamma}}")
            c_T = rf"T = {newtons(T)}"
            ori_T = ("La tension est réglée pour une vitesse constante : la loi de Newton projetée sur (Ox) avec a = 0 "
                     "donne T cos γ = m g sin α " + ("+" if sens == "monte" else "−") + " (R_T + f), "
                     "avec R_T = μ (m g cos α − T sin γ). On isole T.")
        elif p["T_auto"]:
            f_T = r"T = \dfrac{m\,g\sin\alpha}{\cos\gamma}"
            c_T = rf"T = \dfrac{{{nb(m)} \times 9{{,}}81 \times \sin {A}}}{{\cos {deg(p['gamma'])}}} = {newtons(T)}"
            ori_T = "Le câble retient le système immobile : sa composante le long de la pente compense m g sin α."
        else:
            f_T, c_T = r"T \text{ (donnée)}", rf"T = {newtons(T)}"
            ori_T = "C'est une donnée de l'énoncé : la valeur choisie dans les réglages."
        sc.forces.append(Force(
            "Tension du câble", "T", None, "T", T, (ax_, ay_), (ux, uy), "T",
            f"le long du câble, à {fr(p['gamma'])}° de la pente", cote=-1,
            agent="le câble", contact=True, formule=f_T, calcul=c_T, origine=ori_T,
            astuce="Un câble ne peut que tirer, jamais pousser : sa tension est toujours dirigée le long du câble, "
                   "vers le point d'attache."))

    sc.repere = (64, 64, (dx, dy), (nx, ny), "x", "y")
    sc.composantes = [(dx, dy, sa, "P sin α"), (-nx, -ny, ca, "P cos α")]
    if v > 0:
        sc.vitesse = (gx + 140 * nx - dir_mvt * 40 * dx, gy + 140 * ny - dir_mvt * 40 * dy,
                      dir_mvt * dx, dir_mvt * dy, v / 30)

    sc.infos = [({"descend": f"Il descend à {fr(v)} m/s", "monte": f"Il monte à {fr(v)} m/s",
                  "immobile": "Il est immobile"}[sens], None),
                (f"pente α = {fr(p['alpha'])}°", "doux"),
                (f"R_N = {fr(RN / P, 2)} × P", "RN")]

    # --- la résultante, le long de la pente (vers le bas positif) -------------
    S = P * sa - T * math.cos(gam) + dir_RT * RT - dir_mvt * f if not (sens == "immobile") else 0.0
    if sens == "immobile":
        sc.mouvement = ("Tant qu'il ne glisse pas, le frottement compense exactement ce qui le tire vers le bas : "
                        "**ΣF = 0**, il reste immobile." if not alertes else
                        "Le frottement maximal ne suffit pas : **il se met à glisser** vers le bas de la pente.")
    elif abs(S) < 0.01 * P:
        sc.mouvement = "Les forces se compensent : **ΣF = 0**, il avance à vitesse constante."
    else:
        dans_le_sens = (S > 0) == (sens == "descend")
        sc.mouvement = (f"La résultante vaut {fr(abs(S))} N, le long de la pente vers le **{'bas' if S > 0 else 'haut'}**. "
                        + ("Dans le sens du mouvement : **il accélère**" if dans_le_sens else
                           "Opposée au mouvement : **il ralentit**") + f" (a = {fr(abs(S) / m)} m/s²).")
    sc.retenir = ["Sur une pente, R_N = m g cos α : la réaction ne vaut pas le poids.",
                  "On projette le poids : P sin α le long de la pente, P cos α perpendiculairement.",
                  f"Il démarre seul si tan α > μ (ici tan α = {fr(math.tan(a), 2)}"
                  + (f", μ = {fr(mu, 2)})." if p["sol"] else ", sans frottement).")]
    return sc
