"""
Un petit composant qui affiche du HTML et signale à Python l'élément cliqué.

Tout élément portant l'attribut data-force="3" devient cliquable : un clic renvoie « 3 »
dans le résultat du composant (result.clic), le temps d'une exécution du script.
On l'utilise pour le schéma (on clique sur une flèche) et pour le bilan (on clique sur une ligne).
"""

import streamlit as st

_JS = """
export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let racine = parentElement.querySelector('.racine');
  if (!racine) {
    racine = document.createElement('div');
    racine.className = 'racine';
    parentElement.appendChild(racine);
  }
  if (racine._html === data.html) return;      // rien n'a changé : on ne redessine pas
  racine._html = data.html;
  racine.innerHTML = data.html;
  racine.querySelectorAll('[data-force]').forEach((el) => {
    if (el.tagName.toLowerCase() === 'g') {     // flèches du schéma : accessibles au clavier aussi
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setTriggerValue('clic', el.dataset.force); }
      });
    }
    el.addEventListener('click', () => setTriggerValue('clic', el.dataset.force));
  });
}
"""

_CSS = """
.racine { font-family: 'Source Sans 3', 'Source Sans Pro', 'Segoe UI', system-ui, sans-serif; color: #1B2140; }
.racine svg { width: 100%; height: auto; display: block; border-radius: 14px; border: 1px solid #E3E6EF; }
.racine .force { cursor: pointer; transition: opacity .15s ease; outline: none; }
.racine svg:has(.force:hover) .force:not(:hover),
.racine svg:has(.force:focus-visible) .force:not(:focus-visible) { opacity: .28; }
.racine .force:focus-visible { filter: drop-shadow(0 0 4px rgba(46, 61, 163, .55)); }

.liste { display: grid; }
.ligne { all: unset; box-sizing: border-box; width: 100%; cursor: pointer; display: grid;
         grid-template-columns: 11px minmax(0, 1fr) auto 16px; gap: 12px; align-items: center;
         padding: 10px 10px; border-radius: 10px; border-bottom: 1px solid #EEF0F5; transition: background .12s; }
.ligne:last-child { border-bottom: 0; }
.ligne:hover { background: #F1F3F9; }
.ligne:focus-visible { outline: 2px solid #2E3DA3; outline-offset: 1px; }
.pt { width: 11px; height: 11px; border-radius: 50%; }
.nom { font-weight: 600; font-size: 15.5px; }
.sym { font-family: 'STIX Two Text', 'Latin Modern Roman', Georgia, serif; font-style: italic; font-size: 17.5px;
       margin-left: 5px; }
.sym sub { font-style: normal; font-size: 12px; }
.det { display: block; color: #5B6280; font-size: 13.5px; margin-top: 2px; line-height: 1.35; }
.val { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; font-size: 15px; }
.val small { display: block; font-weight: 400; color: #5B6280; font-size: 12.5px; }
.chev { color: #A6ADC4; font-size: 20px; line-height: 1; transition: transform .12s, color .12s; }
.ligne:hover .chev { color: #2E3DA3; transform: translateX(2px); }
"""

def cliquable(html, key):
    """Affiche le HTML ; renvoie le numéro de la force cliquée (int) pendant l'exécution qui suit le clic."""
    # On (ré)enregistre le composant à chaque exécution : c'est sans effet s'il existe déjà à l'identique,
    # et ça le rend disponible même après un rechargement du code sur le serveur.
    composant = st.components.v2.component("atelier_cliquable", js=_JS, css=_CSS)
    res = composant(data={"html": html}, key=key, on_clic_change=lambda: None)
    valeur = getattr(res, "clic", None) if res is not None else None
    return int(valeur) if valeur not in (None, "") else None
