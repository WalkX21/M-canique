

from dataclasses import dataclass
from math import atanh, sqrt, log

import numpy as np

G = 9.81  # intensité de la pesanteur (m/s²)


# ---------------------------------------------------------------------------
# 1. Le modèle physique
# ---------------------------------------------------------------------------

@dataclass
class Modele:
    m: float                     # masse (kg)
    F: float                     # force motrice constante (N)
    k1: float = 0.0              # frottement linéaire (kg/s)
    k2: float = 0.0              # frottement quadratique (kg/m) au départ
    k2_fin: float | None = None  # k2 après ouverture (None : pas d'ouverture)
    t_ouverture: float = 0.0     # instant où l'ouverture commence (s)
    duree_ouverture: float = 0.0 # durée de l'ouverture (0 : instantanée)

    def k2_t(self, t: float) -> float:
        """Coefficient quadratique à l'instant t (rampe linéaire pendant l'ouverture)."""
        if self.k2_fin is None or t < self.t_ouverture:
            return self.k2
        if self.duree_ouverture <= 0 or t >= self.t_ouverture + self.duree_ouverture:
            return self.k2_fin
        fraction = (t - self.t_ouverture) / self.duree_ouverture
        return self.k2 + fraction * (self.k2_fin - self.k2)

    def acceleration(self, t: float, v: float) -> float:
        """Seconde loi de Newton : dv/dt = (F - k1 v - k2 |v| v) / m."""
        return (self.F - self.k1 * v - self.k2_t(t) * abs(v) * v) / self.m

    @property
    def a0(self) -> float:
        """Accélération due à la seule force motrice (g en chute libre)."""
        return self.F / self.m

    @property
    def a_une_solution_exacte(self) -> bool:
        return self.k2_fin is None or self.k2_fin == self.k2


def vitesse_limite(F: float, k1: float, k2: float) -> float:
    """
    Vitesse pour laquelle dv/dt = 0, c'est-à-dire F = k1 v + k2 v².
    On résout le trinôme k2 v² + k1 v - F = 0 et on garde la racine positive.
    """
    if k2 > 0:
        return (-k1 + sqrt(k1 ** 2 + 4 * k2 * F)) / (2 * k2)
    if k1 > 0:
        return F / k1
    return float("inf")  # aucun frottement : pas de vitesse limite


def vitesse_limite_finale(mod: Modele) -> float:
    """Vitesse limite une fois l'éventuelle ouverture terminée."""
    k2 = mod.k2 if mod.k2_fin is None else mod.k2_fin
    return vitesse_limite(mod.F, mod.k1, k2)


# ---------------------------------------------------------------------------
# 2. Résolution numérique : on avance pas à pas
# ---------------------------------------------------------------------------
#
# L'état du système à l'instant t est le couple (z, v). On connaît ses
# dérivées : dz/dt = v et dv/dt = a(t, v). Connaissant l'état à t, on
# estime l'état à t + dt, et on recommence.

def _derivees(mod: Modele, t: float, z: float, v: float) -> tuple[float, float]:
    return v, mod.acceleration(t, v)


def pas_euler(mod: Modele, t: float, z: float, v: float, dt: float) -> tuple[float, float]:
    """
    Méthode d'Euler : on suppose la pente constante pendant dt.
    C'est la définition de la dérivée lue à l'envers : dv ≈ (dv/dt) × dt.
    Erreur globale proportionnelle à dt (méthode d'ordre 1).
    """
    dz, dv = _derivees(mod, t, z, v)
    return z + dt * dz, v + dt * dv


def pas_rk4(mod: Modele, t: float, z: float, v: float, dt: float) -> tuple[float, float]:
    """
    Méthode de Runge-Kutta d'ordre 4 : on mesure la pente en quatre points
    du pas (début, deux fois au milieu, fin) et on en fait une moyenne pondérée.
    Erreur globale proportionnelle à dt⁴ : diviser dt par 2 divise l'erreur par 16.
    """
    z1, v1 = _derivees(mod, t, z, v)
    z2, v2 = _derivees(mod, t + dt / 2, z + dt / 2 * z1, v + dt / 2 * v1)
    z3, v3 = _derivees(mod, t + dt / 2, z + dt / 2 * z2, v + dt / 2 * v2)
    z4, v4 = _derivees(mod, t + dt, z + dt * z3, v + dt * v3)
    z_suiv = z + dt / 6 * (z1 + 2 * z2 + 2 * z3 + z4)
    v_suiv = v + dt / 6 * (v1 + 2 * v2 + 2 * v3 + v4)
    return z_suiv, v_suiv


METHODES = {"Euler": pas_euler, "RK4": pas_rk4}


def integrer(mod: Modele, v0: float, duree: float, dt: float, methode: str = "RK4"):
    """Renvoie les tableaux t, z, v, a de t = 0 à t = duree."""
    pas = METHODES[methode]
    n = max(1, int(np.ceil(duree / dt)))
    t = np.linspace(0.0, n * dt, n + 1)
    z = np.empty(n + 1)
    v = np.empty(n + 1)
    z[0], v[0] = 0.0, v0
    with np.errstate(all="ignore"):            # un schéma instable peut déborder
        for i in range(n):
            z[i + 1], v[i + 1] = pas(mod, t[i], float(z[i]), float(v[i]), dt)
            if not (np.isfinite(v[i + 1]) and abs(v[i + 1]) < 1e12):   # instable : on s'arrête
                z[i + 1:], v[i + 1:] = np.nan, np.nan
                break
    a = np.array([mod.acceleration(ti, vi) if np.isfinite(vi) else np.nan
                  for ti, vi in zip(t, v)])
    return t, z, v, a


# ---------------------------------------------------------------------------
# 3. Solutions exactes (celles du cours)
# ---------------------------------------------------------------------------

def _ln_cosh(x):
    return np.logaddexp(x, -x) - log(2)          # ln ch x sans dépassement


def _ln_sinh(x):
    return x + np.log1p(-np.exp(-2 * x)) - log(2)  # ln sh x, pour x > 0


def solution_exacte(mod: Modele, v0: float, t: np.ndarray):
    """
    Renvoie (z, v, nom_du_cas) quand une solution exacte existe, sinon None.
      - vide            : v = v0 + a0 t
      - linéaire seul   : v = vl + (v0 - vl) exp(-t/τ),  τ = m/k1
      - quadratique seul: v = vl th(t/τ + C) ou vl coth(t/τ + C),  τ = vl/a0
    """
    if not mod.a_une_solution_exacte:
        return None
    m, F, k1, k2, a0 = mod.m, mod.F, mod.k1, mod.k2, mod.a0

    if k1 == 0 and k2 == 0:
        return v0 * t + a0 * t ** 2 / 2, v0 + a0 * t, "vide"

    if k2 == 0:
        vl, tau = F / k1, m / k1
        e = np.exp(-t / tau)
        return vl * t + (v0 - vl) * tau * (1 - e), vl + (v0 - vl) * e, "linéaire"

    if k1 == 0 and v0 >= 0 and F > 0:
        vl = sqrt(F / k2)
        tau = vl / a0
        u0 = v0 / vl
        if abs(u0 - 1) < 1e-12:
            return vl * t, np.full_like(t, vl), "quadratique"
        if u0 < 1:
            c = atanh(u0)
            x = t / tau + c
            return vl * tau * (_ln_cosh(x) - _ln_cosh(c)), vl * np.tanh(x), "quadratique (th)"
        c = atanh(1 / u0)                           # argcoth(u0)
        x = t / tau + c
        return vl * tau * (_ln_sinh(x) - _ln_sinh(c)), vl / np.tanh(x), "quadratique (coth)"

    return None  # frottement mixte, ou quadratique avec changement de sens


# ---------------------------------------------------------------------------
# 4. Outils d'analyse
# ---------------------------------------------------------------------------

def temps_95(t: np.ndarray, v: np.ndarray, v_inf: float) -> float:
    """Premier instant où 95 % de l'écart initial à la vitesse limite est rattrapé."""
    ecart0 = abs(v[0] - v_inf)
    if not np.isfinite(v_inf) or ecart0 == 0:
        return float("nan")
    atteint = np.nonzero(np.abs(v - v_inf) <= 0.05 * ecart0)[0]
    return float(t[atteint[0]]) if atteint.size else float("nan")


def tau_local(mod: Modele, v: float) -> float:
    """
    Temps de réponse local m / (k1 + 2 k2 |v|) : l'échelle de temps sur laquelle
    la vitesse réagit au voisinage de v. Le pas de calcul doit rester petit devant.
    """
    k2 = max(mod.k2, mod.k2_fin or 0.0)
    d = mod.k1 + 2 * k2 * abs(v)
    return mod.m / d if d > 0 else float("inf")


def pas_automatique(mod: Modele, v0: float, duree: float) -> float:
    """Pas de calcul : 1/200 du plus petit temps caractéristique, sans dépasser 100 000 pas."""
    vl = vitesse_limite_finale(mod)
    v_max = max(abs(v0), vl if np.isfinite(vl) else abs(v0) + mod.a0 * duree)
    echelle = min(tau_local(mod, v_max), duree)
    return max(echelle / 200, duree / 100_000)


def etude_convergence(mod: Modele, v0: float, duree: float, fractions=(2, 5, 10, 20, 50, 100, 200)):
    """
    Erreur maximale |v_num - v_exacte| pour plusieurs pas dt = T / fraction,
    avec T le temps caractéristique. Renvoie None s'il n'y a pas de solution exacte.
    """
    vl = vitesse_limite_finale(mod)
    T = min(tau_local(mod, max(abs(v0), vl if np.isfinite(vl) else 1.0)), duree)
    lignes = []
    for f in fractions:
        dt = T / f
        for nom in METHODES:
            t, _, v, _ = integrer(mod, v0, duree, dt, nom)
            exacte = solution_exacte(mod, v0, t)
            if exacte is None:
                return None
            err = float(np.nanmax(np.abs(v - exacte[1]))) if np.all(np.isfinite(v)) else float("inf")
            lignes.append({"dt": dt, "methode": nom, "erreur": err})
    return lignes
