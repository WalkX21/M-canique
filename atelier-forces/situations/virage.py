"""Virage à vitesse constante : route plate ou piste relevée."""

import math

import streamlit as st

from moteur.dessin import COUL, Dessin
from moteur.scene import Force, Scene, deg, fr, nb, newtons, poids
from moteur.ui import choix, curseur, nombre

NOM = "Virage"
ICONE = ":material/roundabout_right:"
AIDE = "Un véhicule qui tourne à vitesse constante : route plate, piste relevée de vélodrome."
G_ = 9.81
VEHICULES = {"deux_roues": "Deux-roues (il se penche)", "voiture": "Voiture"}
ROUTES = {"plate": "Route plate", "relevee": "Piste relevée"}

_BASE = dict(nom="le cycliste et son vélo", m=85.0, vehicule="deux_roues", R=20.0, v=10.0, route="plate",
             beta=42.0, mu=0.8)
EXEMPLES = {
    "Cycliste sur route": dict(_BASE),
    "Cycliste au vélodrome": dict(_BASE, route="relevee", v=13.3),
    "Voiture dans un rond-point": dict(_BASE, nom="la voiture", m=1200.0, vehicule="voiture", R=15.0, v=8.0, mu=0.7),
    "Trop vite sur route mouillée": dict(_BASE, nom="la voiture", m=1200.0, vehicule="voiture", R=15.0, v=12.0, mu=0.4),
}


def actions(k):
    choix(f"{k}_vehicule", "Quel véhicule ?", VEHICULES)
    choix(f"{k}_route", "Quelle route ?", ROUTES)
    if st.session_state[f"{k}_route"] == "relevee":
        curseur(f"{k}_beta", "Inclinaison de la piste β (°)", 0.0, 50.0, 0.5,
                aide="Les virages des vélodromes sont relevés d'environ 42°.")
    nombre(f"{k}_mu", "Adhérence des pneus μ", aide="Route sèche ≈ 0,8 ; route mouillée ≈ 0,4 ; verglas ≈ 0,1.")


def etat(k, p):
    curseur(f"{k}_R", "Rayon du virage R (m)", 2.0, 200.0, 0.5)
    curseur(f"{k}_v", "Sa vitesse v (m/s)", 0.5, 50.0, 0.1)
    st.caption(f"Soit {fr(st.session_state[f'{k}_v'] * 3.6)} km/h, constante pendant le virage.")


def construire(p):
    m, R, v, mu = p["m"], p["R"], p["v"], p["mu"]
    P = m * G_
    b = math.radians(p["beta"]) if p["route"] == "relevee" else 0.0
    an = v * v / R
    N = m * (G_ * math.cos(b) + an * math.sin(b))
    f = m * (an * math.cos(b) - G_ * math.sin(b))       # > 0 : vers le centre
    derape = abs(f) > mu * N + 1e-9
    phi = math.atan(an / G_) if p["vehicule"] == "deux_roues" else 0.0

    d = Dessin()
    # --- encart : vue de dessus ---------------------------------------------
    d.rect(18, 18, 214, 196, "#FFFFFF", "#DCE0EA", 1, rx=10)
    d.texte(30, 40, "VUE DE DESSUS", 11, COUL["doux"], ancre="start", gras=True)
    cxi, cyi, ri = 112, 128, 62
    d.cercle(cxi, cyi, ri, "none", COUL["guide"], 1.4)
    d.cercle(cxi, cyi, 3, COUL["texte"])
    d.texte(cxi - 11, cyi + 4, "C", 13, math=True, italique=True)
    mx, my = cxi + ri, cyi
    d.cercle(mx, my, 6, COUL["F"])
    d.fleche(mx, my, 0, -48, COUL["v"], 2, tirets="5 4")
    d.texte(mx + 12, my - 44, "v", 14, COUL["v"], math=True, italique=True)
    d.fleche(mx, my, -46, 0, COUL["S"], 2)
    d.texte(mx - 32, my + 18, "aₙ", 14, COUL["S"], math=True, italique=True)

    # --- vue de face ----------------------------------------------------------
    kx, ky = (470.0, 306.0) if b else (400.0, 352.0)
    ux, uy = math.cos(b), -math.sin(b)                 # le long du sol, vers l'extérieur
    nx, ny = -math.sin(b), -math.cos(b)                # normale au sol
    gauche = min(300.0, (460 - 22 - ky) / max(math.sin(b), 1e-6))
    droite = min(300.0, (ky - 160) / max(math.sin(b), 1e-6), (720 - 30 - kx) / max(math.cos(b), 1e-6))
    d.sol(kx - gauche * ux, ky - gauche * uy, kx + droite * ux, ky + droite * uy, cote=1)
    if b:
        x0, y0 = kx - gauche * ux, ky - gauche * uy
        d.ligne(x0, y0, x0 + 260, y0, COUL["guide"], 1.2, "4 4")
        d.arc(x0, y0, 60, -p["beta"], 0, label="β", label_r=76)
    d.fleche(250, 250 if not b else 236, -150, 0, COUL["guide"], 1.6, tirets="6 5")
    d.texte(100, (250 if not b else 236) - 12, "vers le centre C", 12.5, COUL["doux"], ancre="start")

    if p["vehicule"] == "deux_roues":
        wx, wy = -math.sin(phi), -math.cos(phi)        # axe du vélo, penché vers le centre
        d.ellipse(kx + 40 * wx, ky + 40 * wy, 7, 40, "#FFFFFF", COUL["objet_trait"], 2.2, angle=-math.degrees(phi))
        d.ligne(kx + 82 * wx, ky + 82 * wy, kx + 205 * wx, ky + 205 * wy, COUL["objet_trait"], 6)
        d.cercle(kx + 224 * wx, ky + 224 * wy, 15, COUL["objet"], COUL["objet_trait"], 2)
        gx, gy = kx + 172 * wx, ky + 172 * wy
        d.ligne(kx, ky, kx, ky - 240, COUL["guide"], 1, "4 4")
        d.arc(kx, ky, 92, -90 - math.degrees(phi), -90, label="φ", label_r=108)
    else:
        L, H = 80.0, 66.0
        coins = [(kx + sx * L * ux + h * nx, ky + sx * L * uy + h * ny) for sx, h in ((-1, 14), (1, 14), (1, H), (-1, H))]
        d.polygone(coins, COUL["objet"], COUL["objet_trait"], 2)
        for sx in (-1, 1):
            cxr, cyr = kx + sx * 58 * ux + 14 * nx, ky + sx * 58 * uy + 14 * ny
            d.ellipse(cxr, cyr, 13, 14, "#FFFFFF", COUL["objet_trait"], 2, angle=-math.degrees(b))
        gx, gy = kx + 46 * nx, ky + 46 * ny
    d.cercle(gx, gy, 4, COUL["texte"])
    d.texte(gx + 12, gy - 8, "G", 13, COUL["doux"], math=True, italique=True)

    sc = Scene(d, m, (gx, gy))
    Bd = deg(p["beta"])
    sc.forces.append(poids(m, (gx, gy), cote=-1))
    if b:
        f_N = r"R_N = m\left(g\cos\beta + \dfrac{v^2}{R}\sin\beta\right)"
        c_N = (rf"R_N = {nb(m)} \times \left(9{{,}}81 \times \cos {Bd} + \dfrac{{{nb(v)}^2}}{{{nb(R)}}} \times \sin {Bd}\right)"
               rf" = {newtons(N)}")
        o_N = ("La résultante doit valoir m v²/R, horizontale et vers le centre. On projette la loi de Newton "
               "perpendiculairement à la piste : R_N − m g cos β = m (v²/R) sin β. La piste relevée « pousse » donc "
               "plus fort que le poids.")
    else:
        f_N, c_N = r"R_N = m\,g", rf"R_N = {nb(m)} \times 9{{,}}81 = {newtons(N)}"
        o_N = ("Pas de mouvement vertical : la loi de Newton projetée sur la verticale donne 0 = R_N − m g. "
               "Le virage ne change rien à la verticale, il agit à l'horizontale.")
    sc.forces.append(Force(
        "Réaction normale", "R", "N", "RN", N, (kx + 14 * ux, ky + 14 * uy), (nx, ny),
        "m (g cos β + v²/R sin β)" if b else "m g", "perpendiculaire au sol", cote=1 if b else -1,
        agent="la route", contact=True, formule=f_N, calcul=c_N, origine=o_N,
        astuce="Sur une piste relevée, la réaction normale est inclinée vers le centre : elle aide à tourner."))
    if abs(f) > 1e-6:
        s = 1 if f > 0 else -1
        if b:
            f_T = r"R_T = m\left(\dfrac{v^2}{R}\cos\beta - g\sin\beta\right)"
            c_T = (rf"R_T = {nb(m)} \times \left(\dfrac{{{nb(v)}^2}}{{{nb(R)}}} \times \cos {Bd} - 9{{,}}81 \times \sin {Bd}\right)"
                   rf" = {newtons(f)}")
            o_T = ("On projette la loi de Newton le long de la piste : il faut R_T + m g sin β = m (v²/R) cos β. "
                   + ("Ici le résultat est positif : le frottement tire vers le centre, il va plus vite que la vitesse idéale."
                      if f > 0 else "Ici le résultat est négatif : il va moins vite que la vitesse idéale, le frottement "
                                    "doit le retenir vers l'extérieur pour qu'il ne glisse pas vers le bas de la piste."))
        else:
            f_T = r"R_T = m\,\dfrac{v^2}{R}"
            c_T = rf"R_T = {nb(m)} \times \dfrac{{{nb(v)}^2}}{{{nb(R)}}} = {newtons(f)}"
            o_T = ("Sur route plate, c'est la seule force horizontale : elle doit fournir à elle seule la force m v²/R "
                   "qui fait tourner (accélération normale v²/R vers le centre du virage).")
        lim = rf"\qquad \mu R_N = {nb(mu)} \times {nb(N)} = {newtons(mu * N)}"
        sc.forces.append(Force(
            "Frottement latéral" + (" nécessaire" if derape else ""), "R", "T",
            "alerte" if derape else "RT", abs(f), (kx, ky), (-s * ux, -s * uy),
            "m v²/R" if not b else "m (v²/R cos β − g sin β)",
            "le long du sol, " + ("vers le centre" if f > 0 else "vers l'extérieur"), cote=-1 if f > 0 else 1,
            agent="la route, sur les pneus", contact=True, formule=f_T, calcul=c_T + lim, origine=o_T,
            astuce=("Les pneus ne peuvent pas fournir plus que μ R_N : au-delà, ils dérapent. "
                    + (f"Ici il faudrait {fr(abs(f))} N, ils n'en fournissent que {fr(mu * N)} N." if derape
                       else f"Ici il faut {fr(abs(f))} N, ils peuvent en fournir jusqu'à {fr(mu * N)} N : ça passe."))))
    sc.composantes = [(-ux, -uy, math.sin(b), "P sin β"), (-nx, -ny, math.cos(b), "P cos β")] if b else []
    sc.repere = (640, 410, (1.0, 0.0), (0.0, -1.0), "uᵣ", "z")

    sc.infos = [(f"Il roule à {fr(v)} m/s", None), (f"soit {fr(v * 3.6)} km/h", "doux"),
                (f"aₙ = v²/R = {fr(an)} m/s²", "S")]
    if p["vehicule"] == "deux_roues":
        sc.infos.append((f"inclinaison φ = {fr(math.degrees(phi))}°", "doux"))

    if derape:
        sc.alertes.append(f"Il dérape : il faudrait un frottement latéral de {fr(abs(f))} N, "
                          f"mais les pneus ne peuvent fournir que μ R_N = {fr(mu * N)} N.")
    sc.mouvement = (f"La résultante vaut m v²/R = {fr(m * an)} N. Elle est **horizontale et dirigée vers le centre** : "
                    "c'est elle qui le fait tourner. Sa vitesse garde la même valeur mais change de direction.")
    if not b:
        vmax = math.sqrt(mu * G_ * R)
        sc.retenir = ["Même à vitesse constante, il y a une accélération : aₙ = v²/R, vers le centre.",
                      "Sur route plate, c'est le frottement latéral des pneus qui fournit m v²/R.",
                      f"Il passe sans déraper tant que v ≤ √(μ g R) = {fr(vmax)} m/s ({fr(vmax * 3.6)} km/h)."]
    else:
        vi = math.sqrt(R * G_ * math.tan(b))
        sc.retenir = ["Sur une piste relevée, la réaction normale est inclinée vers le centre et aide à tourner.",
                      f"À la vitesse idéale √(R g tan β) = {fr(vi)} m/s ({fr(vi * 3.6)} km/h), aucun frottement n'est nécessaire.",
                      "Plus lent, il faut retenir vers l'extérieur ; plus rapide, il faut tirer vers le centre."]
    if p["vehicule"] == "deux_roues":
        sc.retenir.append("Le cycliste se penche de φ avec tan φ = v²/(R g) pour ne pas basculer.")
    return sc
