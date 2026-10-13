"""
Une scène = le décor dessiné + la liste des forces à l'instant choisi.
La fonction rendre() ajoute les vecteurs, à l'échelle du poids.
Chaque force porte aussi sa « fiche » : qui l'exerce, sa formule, d'où elle vient, le calcul.
"""

import math
from dataclasses import dataclass, field

from moteur.dessin import COUL, Dessin

G_ = 9.81
L_P = 118.0          # longueur du poids, en pixels : c'est l'échelle de référence
L_MAX = 230.0
L_MIN = 20.0
SEUIL_FAIBLE = 0.2   # avec la loupe, les forces < 0,2 P sont dessinées 5 fois plus grandes

EXPOSANTS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


# --- nombres --------------------------------------------------------------

def fr(x, n=3):
    """Nombre au format français, n chiffres significatifs (3,14 ; 2,6·10⁻²)."""
    x = float(x)
    if not math.isfinite(x):
        return "—"
    if x == 0:
        return "0"
    s = f"{x:.{n}g}"
    if "e" in s:
        mant, exp = s.split("e")
        s = f"{mant}·10{str(int(exp)).translate(EXPOSANTS)}"
    return s.replace(".", ",")


def nb(x, n=3):
    """Nombre pour LaTeX : virgule décimale et puissance de dix."""
    x = float(x)
    if x == 0:
        return "0"
    s = f"{x:.{n}g}"
    if "e" in s:
        mant, exp = s.split("e")
        return f"{mant.replace('.', '{,}')} \\times 10^{{{int(exp)}}}"
    return s.replace(".", "{,}")


def newtons(x):
    return nb(x) + r"\ \mathrm{N}"


def deg(a):
    return nb(a) + r"^\circ"


# --- forces ---------------------------------------------------------------

@dataclass
class Force:
    nom: str                    # « Poids »
    lettre: str                 # « P »
    indice: str | None          # « N » pour R_N
    cle: str                    # clé de couleur dans COUL
    valeur: float               # en newtons
    point: tuple                # point d'application (pixels)
    direction: tuple            # vecteur unitaire (repère SVG)
    expression: str = ""        # « m g », « μ R_N »… (version courte, pour le bilan)
    sens: str = ""              # « verticale, vers le bas »
    cote: int = 1               # côté de l'étiquette
    # La fiche
    agent: str = ""             # qui exerce la force : « la Terre »
    contact: bool = True        # action de contact ou à distance
    formule: str = ""           # LaTeX
    origine: str = ""           # d'où vient la formule (Markdown)
    calcul: str = ""            # LaTeX, avec les valeurs
    astuce: str = ""            # piège ou remarque (Markdown)

    @property
    def symbole_tex(self):
        return rf"\vec {self.lettre}" if not self.indice else rf"\vec {self.lettre}_{{\mathrm{{{self.indice}}}}}"


def poids(m, point, cote=1):
    P = m * G_
    return Force("Poids", "P", None, "P", P, point, (0.0, 1.0), "m g", "verticale, vers le bas", cote,
                 agent="la Terre", contact=False,
                 formule=r"\vec P = m\,\vec g \qquad P = m\,g",
                 origine="C'est l'attraction de la Terre sur le système. Elle s'applique au centre de gravité G, "
                         "elle est toujours verticale vers le bas, et elle ne dépend ni de la vitesse ni du support. "
                         "Près du sol, on prend g = 9,81 m·s⁻².",
                 calcul=rf"P = {nb(m)} \times 9{{,}}81 = {newtons(P)}",
                 astuce="Le poids ne disparaît jamais, même quand l'objet est posé : c'est la réaction du support "
                        "qui le compense.")


@dataclass
class Scene:
    dessin: Dessin
    m: float
    G: tuple
    forces: list = field(default_factory=list)
    repere: tuple | None = None         # (x, y, (ux, uy), (vx, vy), nom1, nom2)
    vitesse: tuple | None = None        # (x, y, ux, uy, fraction entre 0 et 1)
    composantes: list = field(default_factory=list)   # (ux, uy, fraction, texte)
    infos: list = field(default_factory=list)         # lignes affichées en haut à droite
    mouvement: str = ""                 # ce que dit la résultante
    alertes: list = field(default_factory=list)
    retenir: list = field(default_factory=list)

    @property
    def P(self):
        return self.m * G_

    @property
    def visibles(self):
        """Les forces non nulles, avec leur numéro (celui utilisé pour les clics)."""
        return [(i, f) for i, f in enumerate(self.forces) if f.valeur > 0]


def longueur(F, P, loupe):
    if F <= 0:
        return 0.0, False, False
    agrandie = loupe and F < SEUIL_FAIBLE * P
    L = L_P * F / P * (5 if agrandie else 1)
    if L > L_MAX:
        return L_MAX, True, agrandie
    return max(L, L_MIN), False, agrandie


def resultante(scene):
    sx = sum(f.valeur * f.direction[0] for f in scene.forces)
    sy = sum(f.valeur * f.direction[1] for f in scene.forces)
    return sx, sy


def rendre(scene, options, choisie=None):
    """
    Dessine les forces sur une copie du décor (la scène n'est pas modifiée).
    options : ensemble parmi {'valeurs', 'vitesse', 'repere', 'composantes', 'resultante', 'loupe'}.
    choisie : numéro d'une force à mettre en avant (les autres sont estompées).
    Renvoie (svg pour la page, svg pour l'export).
    """
    base = scene.dessin
    d = Dessin(base.W, base.H)
    d.fond, d.el = list(base.fond), list(base.el)
    P = scene.P
    loupe = "loupe" in options
    gx, gy = scene.G
    infos = list(scene.infos)
    estompe = 0.18 if choisie is not None else 1.0

    def groupe_debut(opac=1.0, attributs=""):
        d.el.append(f'<g opacity="{opac}"{attributs}>')

    def groupe_fin():
        d.el.append("</g>")

    if "composantes" in options:
        groupe_debut(estompe if choisie is not None and scene.forces[choisie].lettre != "P" else 1.0)
        for ux, uy, frac, txt in scene.composantes:
            L = L_P * frac
            if L < 4:
                continue
            d.ligne(gx, gy, gx + ux * L, gy + uy * L, COUL["P"], 1.6, "4 4", 0.75)
            d.cercle(gx + ux * L, gy + uy * L, 2.5, COUL["P"], opac=0.75)
            d.texte(gx + ux * (L + 16), gy + uy * (L + 16) + 4, txt, 12.5, COUL["P"], italique=True, math=True)
        groupe_fin()

    if "repere" in options and scene.repere:
        x, y, (ux, uy), (vx, vy), n1, n2 = scene.repere
        for (a, b), n in (((ux, uy), n1), ((vx, vy), n2)):
            d.fleche(x, y, a * 38, b * 38, COUL["doux"], 1.5)
            d.texte(x + a * 52, y + b * 52 + 5, n, 14, COUL["doux"], math=True, italique=True)
        d.cercle(x, y, 2.5, COUL["doux"])

    # Les forces : chacune dans un groupe cliquable, avec une zone de clic plus large que la flèche
    for i, f in enumerate(scene.forces):
        L, ecr, agr = longueur(f.valeur, P, loupe)
        if L == 0:
            continue
        ux, uy = f.direction
        x, y = f.point
        coul = COUL[f.cle]
        opac = 1.0 if choisie in (None, i) else estompe
        groupe_debut(opac, f' class="force" data-force="{i}"')
        if choisie == i:   # halo sous la force choisie
            d.ligne(x, y, x + ux * L, y + uy * L, coul, 16, opac=0.16)
        d.el.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + ux * L:.1f}" y2="{y + uy * L:.1f}" '
                    f'stroke="#000" stroke-opacity="0" stroke-width="24" stroke-linecap="round"/>')
        d.fleche(x, y, ux * L, uy * L, coul, ep=4.2 if choisie == i else 3.2, ecretee=ecr)
        px, py = -uy, ux
        lx = x + ux * (L + 16) + px * 20 * f.cote
        ly = y + uy * (L + 16) + py * 20 * f.cote + 7
        fin = d.label_vecteur(lx, ly, f.lettre, f.indice, coul, suffixe="×5" if agr else None)
        if "valeurs" in options or choisie == i:
            d.texte(fin + 6, ly, f"{fr(f.valeur)} N", 13, coul, ancre="start")
        groupe_fin()

    if "vitesse" in options and scene.vitesse:
        x, y, ux, uy, frac = scene.vitesse
        if frac > 0:
            groupe_debut(estompe)
            L = max(22.0, 95 * min(frac, 1.0))
            d.fleche(x, y, ux * L, uy * L, COUL["v"], 2.2, tirets="6 4")
            d.label_vecteur(x + ux * (L + 14) - uy * 14, y + uy * (L + 14) + ux * 14 + 6, "v", None, COUL["v"], 15)
            groupe_fin()

    if "resultante" in options:
        sx, sy = resultante(scene)
        S = math.hypot(sx, sy)
        if S < 0.01 * P:
            infos.append(("ΣF = 0 : les forces se compensent", "S"))
        else:
            groupe_debut(estompe)
            L, ecr, agr = longueur(S, P, loupe)
            ux, uy = sx / S, sy / S
            ox, oy = gx - uy * 24, gy + ux * 24          # décalée sur le côté pour ne pas masquer les forces
            d.fleche(ox, oy, ux * L, uy * L, COUL["S"], 2.6, tirets="8 5", ecretee=ecr)
            d.label_vecteur(ox + ux * (L + 16) - uy * 18, oy + uy * (L + 16) + ux * 18 + 6, "ΣF", None,
                            COUL["S"], 16, suffixe="×5" if agr else None)
            groupe_fin()

    for k, (txt, cle) in enumerate(infos):
        d.texte(d.W - 22, 36 + 25 * k, txt, 17 if k == 0 else 15, COUL.get(cle, COUL["texte"]) if cle else None,
                ancre="end", gras=(k == 0))
    if loupe and any(longueur(f.valeur, P, True)[2] for f in scene.forces):
        d.texte(22, d.H - 16, "×5 : force faible agrandie cinq fois pour être lisible", 13, COUL["doux"], ancre="start")
    return d.svg(), d.svg(pour_export=True)
