"""
Primitives de dessin SVG pour les schémas de forces.

Coordonnées SVG : x vers la droite, y vers le BAS.
Les schémas sont dessinés sur un fond clair fixe, comme une feuille.
"""

import math
import re
from html import escape
from pathlib import Path

_INDICE = re.compile(r"(?<=[A-Za-zρθ])(_[A-Za-z0-9θ]+)")

COUL = {
    "P": "#2E3DA3",      # poids
    "RN": "#1F7A4D",     # réaction normale
    "RT": "#B42318",     # frottement solide
    "f": "#C4500A",      # frottement fluide
    "T": "#7A3FA0",      # tension
    "F": "#A86A00",      # force motrice
    "Pi": "#0E7C9A",     # poussée d'Archimède
    "S": "#1B2140",      # résultante
    "v": "#5B6280",      # vitesse
    "guide": "#A6ADC4",
    "sol": "#4C5473",
    "texte": "#1B2140",
    "doux": "#5B6280",
    "objet": "#E6E9F4",
    "objet_trait": "#3F4766",
    "fluide": "#E3F1F6",
    "dome": "#EEF1F8",
    "alerte": "#B42318",
}

POLICE_MATH = "'STIX Two Text', 'Latin Modern Roman', 'Times New Roman', Georgia, serif"
POLICE_TEXTE = "'Source Sans 3', 'Source Sans Pro', 'Segoe UI', system-ui, sans-serif"
DOSSIER_POLICES = Path(__file__).resolve().parent.parent / "polices"


class Dessin:
    def __init__(self, largeur=720, hauteur=460):
        self.W, self.H = largeur, hauteur
        self.fond, self.el = [], []

    # --- primitives -------------------------------------------------------
    def ligne(self, x1, y1, x2, y2, coul="#000", ep=1.5, tirets=None, opac=1.0):
        d = f' stroke-dasharray="{tirets}"' if tirets else ""
        self.el.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{coul}" '
                       f'stroke-width="{ep}" stroke-linecap="round" opacity="{opac}"{d}/>')

    def cercle(self, cx, cy, r, rempl="none", trait=None, ep=1.5, opac=1.0):
        t = f' stroke="{trait}" stroke-width="{ep}"' if trait else ""
        self.el.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{rempl}"{t} opacity="{opac}"/>')

    def ellipse(self, cx, cy, rx, ry, rempl="none", trait=None, ep=1.5, angle=0.0):
        t = f' stroke="{trait}" stroke-width="{ep}"' if trait else ""
        self.el.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{rempl}"{t} '
                       f'transform="rotate({angle:.1f} {cx:.1f} {cy:.1f})"/>')

    def polygone(self, pts, rempl="#000", trait=None, ep=1.0, opac=1.0):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        t = f' stroke="{trait}" stroke-width="{ep}" stroke-linejoin="round"' if trait else ""
        self.el.append(f'<polygon points="{p}" fill="{rempl}"{t} opacity="{opac}"/>')

    def chemin(self, d, trait="#000", ep=1.5, rempl="none", tirets=None, opac=1.0):
        t = f' stroke-dasharray="{tirets}"' if tirets else ""
        self.el.append(f'<path d="{d}" stroke="{trait}" stroke-width="{ep}" fill="{rempl}" '
                       f'stroke-linecap="round" stroke-linejoin="round" opacity="{opac}"{t}/>')

    def rect(self, x, y, w, h, rempl, trait=None, ep=1.0, rx=0):
        t = f' stroke="{trait}" stroke-width="{ep}"' if trait else ""
        self.el.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{rempl}"{t}/>')

    def texte(self, x, y, s, taille=13, coul=None, ancre="middle", gras=False, italique=False, math=False):
        """Texte ; « R_N » s'écrit avec N en indice."""
        coul = coul or COUL["texte"]
        fam = POLICE_MATH if math else POLICE_TEXTE
        style = (' font-weight="700"' if gras else "") + (' font-style="italic"' if italique else "")
        corps, decale = [], 0.0
        for morceau in _INDICE.split(s):
            if morceau.startswith("_"):
                dy = taille * 0.3
                corps.append(f'<tspan dy="{dy:.1f}" font-size="{taille * 0.7:.1f}">{escape(morceau[1:])}</tspan>'
                             f'<tspan dy="{-dy:.1f}"></tspan>')
            elif morceau:
                corps.append(escape(morceau))
        self.el.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{taille}" fill="{coul}" text-anchor="{ancre}" '
                       f'font-family="{fam}"{style}>{"".join(corps)}</text>')

    def label_vecteur(self, x, y, nom, indice=None, coul=None, taille=19, suffixe=None):
        """Vecteur écrit comme dans une copie : lettre italique, indice, petite flèche au-dessus."""
        coul = coul or COUL["texte"]
        l_nom = taille * 0.6 * len(nom)
        largeur = l_nom + (taille * 0.42 * len(indice) if indice else 0)
        x0 = x - largeur / 2
        sub = (f'<tspan font-size="{taille * 0.66:.1f}" dy="{taille * 0.28:.1f}" font-style="normal">'
               f'{escape(indice)}</tspan>') if indice else ""
        self.el.append(f'<text x="{x0:.1f}" y="{y:.1f}" font-size="{taille}" fill="{coul}" '
                       f'font-family="{POLICE_MATH}" font-style="italic">{escape(nom)}{sub}</text>')
        ya = y - taille * 0.9
        xa2 = x0 + l_nom + 1
        self.ligne(x0, ya, xa2, ya, coul, 1.1)
        self.polygone([(xa2 + 3, ya), (xa2 - 2, ya - 2.6), (xa2 - 2, ya + 2.6)], coul)
        if suffixe:
            self.texte(x0 + largeur + 4, y, suffixe, 12, coul, ancre="start")
        return x0 + largeur + (4 + 7 * len(suffixe) if suffixe else 0)     # abscisse de fin de l'étiquette

    def fleche(self, x, y, dx, dy, coul, ep=3.2, tirets=None, ecretee=False):
        L = math.hypot(dx, dy)
        if L < 1:
            return
        ux, uy = dx / L, dy / L
        tete = min(13.0, 0.45 * L)
        xb, yb = x + dx - ux * tete * 0.8, y + dy - uy * tete * 0.8
        self.ligne(x, y, xb, yb, coul, ep, tirets)
        px, py = -uy, ux
        self.polygone([(x + dx, y + dy),
                       (x + dx - ux * tete + px * tete * 0.46, y + dy - uy * tete + py * tete * 0.46),
                       (x + dx - ux * tete - px * tete * 0.46, y + dy - uy * tete - py * tete * 0.46)], coul)
        if ecretee:  # flèche raccourcie : deux traits obliques sur la tige
            mx, my = x + dx * 0.5, y + dy * 0.5
            for k in (-4, 4):
                cx, cy = mx + ux * k, my + uy * k
                a = (cx - px * 7 - ux * 3, cy - py * 7 - uy * 3, cx + px * 7 + ux * 3, cy + py * 7 + uy * 3)
                self.ligne(*a, "#FBFBFD", 4)
                self.ligne(*a, coul, 1.4)

    def arc(self, cx, cy, r, a1, a2, coul=None, ep=1.3, label=None, label_r=None, tirets=None):
        """Arc entre les angles a1 et a2 (degrés, sens SVG : horaire depuis +x)."""
        coul = coul or COUL["doux"]
        if abs(a2 - a1) < 0.5:
            return
        x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
        x2, y2 = cx + r * math.cos(math.radians(a2)), cy + r * math.sin(math.radians(a2))
        grand = 1 if abs(a2 - a1) > 180 else 0
        sens = 1 if a2 > a1 else 0
        self.chemin(f"M{x1:.1f},{y1:.1f} A{r},{r} 0 {grand} {sens} {x2:.1f},{y2:.1f}", coul, ep, tirets=tirets)
        if label:
            am = math.radians((a1 + a2) / 2)
            rl = label_r or r + 14
            self.texte(cx + rl * math.cos(am), cy + rl * math.sin(am) + 5, label, 16, coul, math=True, italique=True)

    def sol(self, x1, y1, x2, y2, cote=1, pas=14):
        """Trait de sol hachuré du côté 'cote'."""
        self.ligne(x1, y1, x2, y2, COUL["sol"], 2.4)
        L = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy * cote, ux * cote
        for i in range(int(L // pas) + 1):
            bx, by = x1 + ux * i * pas, y1 + uy * i * pas
            self.ligne(bx, by, bx + nx * 9 - ux * 6, by + ny * 9 - uy * 6, COUL["guide"], 1)

    # --- sortie -----------------------------------------------------------
    def svg(self, pour_export=False):
        corps = (f'<rect x="0" y="0" width="{self.W}" height="{self.H}" rx="14" fill="#FBFBFD"/>'
                 + "".join(self.fond) + "".join(self.el))
        if pour_export:
            return (f'<svg viewBox="0 0 {self.W} {self.H}" width="{self.W}" height="{self.H}" '
                    f'xmlns="http://www.w3.org/2000/svg">{corps}</svg>')
        return (f'<svg viewBox="0 0 {self.W} {self.H}" xmlns="http://www.w3.org/2000/svg" role="img" '
                f'style="width:100%;height:auto;display:block;border-radius:14px">{corps}</svg>')


def en_png(svg_export, largeur=1600):
    """Convertit le SVG en PNG avec les polices fournies dans le dossier polices/."""
    import resvg_py
    polices = [str(p) for p in DOSSIER_POLICES.glob("*.otf")]
    donnees = resvg_py.svg_to_bytes(svg_string=svg_export, font_files=polices, width=largeur)
    return bytes(donnees)
