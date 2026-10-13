"""
L'atelier des forces — décrire une situation, obtenir le schéma des forces.
Simulateur en cours de développement par Mohammed Bennani.

Lancer en local :   streamlit run app.py
"""

import re
from html import escape

import streamlit as st

from moteur.cliquable import cliquable
from moteur.dessin import COUL, Dessin, en_png
from moteur.scene import fr, rendre
from situations import chute, dome, fil, pente, sol, virage

# Adresse du dépôt GitHub : à remplir une fois le dépôt créé (ex. "https://github.com/pseudo/atelier-forces")
DEPOT_GITHUB = ""
VERSION = "0.3"

st.set_page_config(page_title="L'atelier des forces", page_icon=":material/architecture:", layout="wide")

SITUATIONS = {"pente": pente, "chute": chute, "sol": sol, "virage": virage, "dome": dome, "fil": fil}
OPTIONS = {"valeurs": "Valeurs", "vitesse": "Vitesse", "resultante": "Résultante ΣF",
           "composantes": "Composantes du poids", "repere": "Repère", "loupe": "Loupe ×5"}

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=STIX+Two+Text:ital,wght@0,400;0,600;1,400;1,600&family=Source+Sans+3:wght@400;600;700&display=swap');
.block-container { max-width: 1340px; padding-top: 1.4rem; padding-bottom: 2rem; }
header[data-testid="stHeader"] { background: transparent; }

/* En-tête */
.entete { padding: .4rem 0 1.2rem; display: grid; gap: .35rem; }
.entete .marque { font-size: .76rem; letter-spacing: .14em; text-transform: uppercase; color: #2E3DA3; font-weight: 700; }
.entete h1 { font-family: 'STIX Two Text', Georgia, serif; font-weight: 600; font-size: 2.7rem; line-height: 1.05;
             margin: 0; padding: 0; letter-spacing: -.01em; color: #1B2140; }
.entete p { color: #5B6280; font-size: 1.08rem; margin: 0; max-width: 62ch; }
.entete .credit { font-size: .93rem; color: #4C5473; margin-top: .3rem; max-width: 92ch; line-height: 1.55; }
.entete .credit .badge { display: inline-block; font-size: .68rem; font-weight: 700; letter-spacing: .08em;
                         text-transform: uppercase; color: #2E3DA3; background: #E7EAF8; border-radius: 999px;
                         padding: .1rem .55rem; margin-right: .5rem; transform: translateY(-1px); }
.entete .credit a { color: #2E3DA3; font-weight: 600; text-decoration: underline; text-underline-offset: 2px; }

/* Cartes et étapes */
[class*="st-key-carte"] { background: #FFFFFF; box-shadow: 0 1px 2px rgba(27,33,64,.05), 0 10px 28px rgba(27,33,64,.05); }
.etape { display: flex; gap: .7rem; align-items: flex-start; }
.etape .num { width: 1.8rem; height: 1.8rem; border-radius: 50%; background: #2E3DA3; color: #fff; flex: none;
              display: grid; place-items: center; font-weight: 700; font-size: .92rem; margin-top: .05rem; }
.etape .titre { font-family: 'STIX Two Text', Georgia, serif; font-size: 1.28rem; font-weight: 600; line-height: 1.25; color: #1B2140; }
.etape .aide { color: #5B6280; font-size: .9rem; line-height: 1.35; margin-top: .1rem; }
.st-key-situation button { font-size: 1rem; padding: .5rem .95rem; }

/* Colonne du schéma : reste visible pendant qu'on répond aux questions */
@media (min-width: 640px) {
  div[data-testid="stColumn"]:has(.st-key-droite) { position: sticky; top: 3.2rem; align-self: flex-start; }
}
@media (max-width: 639px) {   /* sur téléphone : le schéma d'abord, les questions ensuite */
  div[data-testid="stHorizontalBlock"]:has(.st-key-droite) { flex-direction: column-reverse; }
}
.schema-titre { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin: 0 0 .5rem; }
.schema-titre .t { font-family: 'STIX Two Text', Georgia, serif; font-size: 1.3rem; font-weight: 600; color: #1B2140; }
.schema-titre .s { color: #5B6280; font-size: .9rem; text-align: right; }
.astuce-clic { display: flex; gap: .45rem; align-items: center; color: #5B6280; font-size: .88rem; margin: .1rem 0 .2rem; }
.astuce-clic .main { font-size: 1rem; }

/* Bas de page */
.titre-bloc { font-family: 'STIX Two Text', Georgia, serif; font-size: 1.12rem; font-weight: 600; color: #1B2140; margin: .1rem 0 .3rem; }
.sous-titre { color: #5B6280; font-size: .86rem; margin: 0 0 .4rem; }
.st-key-retenir li { margin: .3rem 0; color: #3B4262; }
.pied { margin-top: 1.6rem; padding-top: 1rem; border-top: 1px solid #DCE0EA; color: #5B6280; font-size: .86rem;
        display: flex; gap: .4rem 1.2rem; flex-wrap: wrap; justify-content: space-between; }
.pied a { color: #2E3DA3; }

/* Fiche d'une force */
.fiche-id { display: flex; gap: .9rem; align-items: center; margin: .2rem 0 .8rem; }
.fiche-id .nom { font-family: 'STIX Two Text', Georgia, serif; font-size: 1.45rem; font-weight: 600; color: #1B2140; line-height: 1.15; }
.fiche-id .val { font-variant-numeric: tabular-nums; color: #4C5473; font-size: 1rem; margin-top: .15rem; }
.fiche-id .val b { color: #1B2140; font-size: 1.15rem; }
.fiche-faits { display: grid; grid-template-columns: auto 1fr; gap: .45rem 1rem; margin: 0; font-size: .95rem; }
.fiche-faits dt { color: #5B6280; }
.fiche-faits dd { margin: 0; color: #1B2140; font-weight: 600; }
.fiche-section { font-size: .74rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; color: #5B6280;
                 margin: .9rem 0 .1rem; }
.st-key-fiche_astuce { background: #FFF6E5; border-radius: 10px; padding: .75rem .95rem; margin-top: .6rem; }
.st-key-fiche_astuce p { color: #5C3D00; }
.st-key-fiche_astuce strong { color: #8A5A00; }
div[data-testid="stDialog"] .katex-display { overflow-x: auto; overflow-y: hidden; padding: .2rem 0; }
[data-testid="stMarkdownContainer"] p .katex, [data-testid="stMarkdownContainer"] li .katex { font-size: 1.04em; }
</style>
""")


# ---------------------------------------------------------------------------
# Petites fonctions d'affichage
# ---------------------------------------------------------------------------

def etape(numero, titre, aide=None):
    st.html(f'<div class="etape"><div class="num">{numero}</div><div><div class="titre">{titre}</div>'
            + (f'<div class="aide">{aide}</div>' if aide else "") + "</div></div>")


def symbole(f, taille=30):
    """Le vecteur écrit comme sur une copie (lettre italique, indice, flèche), en petit SVG."""
    d = Dessin(64, 46)
    d.label_vecteur(30, 36, f.lettre, f.indice, COUL[f.cle], taille)
    return (f'<svg viewBox="0 0 64 46" width="64" height="46" xmlns="http://www.w3.org/2000/svg">'
            f'{"".join(d.el)}</svg>')


_INDICE = re.compile(r"(?<![\\$\w])([A-Za-z])_([A-Za-zθ]{1,6})(?![\w])")
_RHO = re.compile(r"ρ_(\w+)")


def joli(texte):
    """Pour le Markdown : « R_N » devient $R_N$ (rendu comme en maths)."""
    texte = _RHO.sub(lambda m: rf"$\rho_{{\text{{{m.group(1)}}}}}$", texte)
    def remplace(m):
        indice = r"\theta" if m.group(2) == "θ" else rf"\text{{{m.group(2)}}}"
        return rf"${m.group(1)}_{{{indice}}}$"
    return _INDICE.sub(remplace, texte)


def indices_html(texte):
    """Pour le HTML : « R_N » devient R<sub>N</sub>."""
    return re.sub(r"(?<=[A-Za-zρ])_([A-Za-z0-9]+)", r"<sub>\1</sub>", escape(texte))


def point_application(f):
    a = f.agent
    if not f.contact:
        return "au centre de gravité G"
    if "air" in a or "liquide" in a:
        return "répartie sur la surface en contact avec le fluide"
    if any(m in a for m in ("câble", "corde", "fil")):
        return "au point d'attache"
    return "au point de contact"


def bilan_html(scene):
    lignes = []
    for i, f in scene.visibles:
        sym = f"{escape(f.lettre)}<sub>{escape(f.indice)}</sub>" if f.indice else escape(f.lettre)
        lignes.append(
            f'<button class="ligne" data-force="{i}" title="Voir la fiche de cette force">'
            f'<span class="pt" style="background:{COUL[f.cle]}"></span>'
            f'<span><span class="nom">{escape(f.nom)}</span><span class="sym" style="color:{COUL[f.cle]}">{sym}</span>'
            f'<span class="det">{indices_html(f.expression)} · {escape(f.sens)}</span></span>'
            f'<span class="val">{fr(f.valeur)} N<small>{fr(f.valeur / scene.P, 2)} × P</small></span>'
            f'<span class="chev">›</span></button>')
    return '<div class="liste">' + "".join(lignes) + "</div>"


def ouvrir_fiche(scene, options, i):
    """Fenêtre qui détaille une force : qui l'exerce, sa formule, d'où elle vient, le calcul avec les valeurs."""
    st.session_state["fiche_choix"] = i

    @st.dialog("Fiche de la force", width="large", icon=":material/insights:")
    def _fiche():
        numeros = [j for j, _ in scene.visibles]
        if len(numeros) > 1:
            st.pills("Changer de force", numeros, key="fiche_choix", required=True, label_visibility="collapsed",
                     format_func=lambda j: scene.forces[j].nom)
        j = st.session_state.get("fiche_choix", i)
        j = j if j in numeros else numeros[0]
        f = scene.forces[j]

        c1, c2 = st.columns([1.15, 1], gap="medium")
        with c1:
            svg_aff, _ = rendre(scene, options | {"valeurs"}, choisie=j)
            st.markdown(f'<div style="border:1px solid #E3E6EF;border-radius:14px;overflow:hidden">{svg_aff}</div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="fiche-id">{symbole(f)}<div><div class="nom">{escape(f.nom)}</div>'
                        f'<div class="val"><b>{fr(f.valeur)} N</b> · {fr(f.valeur / scene.P, 2)} × P</div></div></div>'
                        f'<dl class="fiche-faits">'
                        f'<dt>Exercée par</dt><dd>{escape(f.agent)}</dd>'
                        f'<dt>Type</dt><dd>{"action de contact" if f.contact else "action à distance"}</dd>'
                        f'<dt>Direction</dt><dd>{escape(f.sens)}</dd>'
                        f'<dt>Appliquée</dt><dd>{point_application(f)}</dd></dl>', unsafe_allow_html=True)
            st.html('<div class="fiche-section">La formule</div>')
            st.latex(f.formule)

        st.html('<div class="fiche-section">D\'où elle vient</div>')
        st.markdown(joli(f.origine))
        st.html('<div class="fiche-section">Avec tes valeurs</div>')
        calcul = f.calcul if "\\\\" not in f.calcul else r"\begin{gathered}" + f.calcul + r"\end{gathered}"
        st.latex(calcul)
        if f.astuce:
            with st.container(key="fiche_astuce"):
                st.markdown("**À ne pas confondre.** " + joli(f.astuce))

    _fiche()


def charger(k, module):
    choix = st.session_state.get(f"{k}_exemple")
    if choix:
        for nom, val in module.EXEMPLES[choix].items():
            st.session_state[f"{k}_{nom}"] = val


# ---------------------------------------------------------------------------
# État de départ, et conservation des réglages quand on passe d'une situation à l'autre
# ---------------------------------------------------------------------------

for k, module in SITUATIONS.items():
    if f"{k}_init" not in st.session_state:
        st.session_state[f"{k}_init"] = True
        st.session_state[f"{k}_exemple"] = next(iter(module.EXEMPLES))
        charger(k, module)
for cle in list(st.session_state.keys()):
    if cle.split("_")[0] in SITUATIONS:
        st.session_state[cle] = st.session_state[cle]
if st.session_state.get("situation") not in SITUATIONS:
    st.session_state["situation"] = st.session_state.get("situation_memo", "pente")
st.session_state["situation_memo"] = st.session_state["situation"]
if "options" not in st.session_state:
    st.session_state["options"] = ["valeurs", "vitesse", "loupe"]

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------

github = (f'<a href="{escape(DEPOT_GITHUB)}" target="_blank" rel="noopener">GitHub</a>' if DEPOT_GITHUB else "GitHub")
st.html(f"""<div class="entete"><div class="marque">PCSI · mécanique du point</div>
<h1>L'atelier des forces</h1>
<p>Décris la situation en quatre questions : le schéma des forces se construit sous tes yeux,
avec des vecteurs à l'échelle.</p>
<p class="credit"><span class="badge">bêta {VERSION}</span>
<span>Un simulateur en cours de développement par <b>Mohammed Bennani</b>, ouvert aux modifications :
forke le projet sur {github} et propose les tiennes :))</span></p></div>""")

gauche, droite = st.columns([0.9, 1.3], gap="large")

# ---------------------------------------------------------------------------
# Les quatre questions
# ---------------------------------------------------------------------------

with gauche:
    with st.container(border=True, key="carte_1"):
        etape(1, "Quelle situation ?")
        st.pills("Situation", list(SITUATIONS), key="situation", label_visibility="collapsed", required=True,
                 format_func=lambda c: f"{SITUATIONS[c].ICONE} {SITUATIONS[c].NOM}")
    k = st.session_state["situation"] or st.session_state["situation_memo"]
    mod = SITUATIONS[k]
    with gauche.container(border=True, key="carte_2"):
        etape(2, "Qui est le système ?", mod.AIDE)
        st.pills("Partir d'un exemple", list(mod.EXEMPLES), key=f"{k}_exemple", on_change=charger, args=(k, mod))
        c1, c2 = st.columns([1.6, 1])
        c1.text_input("Nom du système", key=f"{k}_nom")
        c2.number_input("Masse m (kg)", min_value=1e-9, format="%g", key=f"{k}_m")
        st.caption("Référentiel terrestre, supposé galiléen.")
    with gauche.container(border=True, key="carte_3"):
        etape(3, "Quelles actions s'exercent sur lui ?", "Le poids est toujours là. Ajoute les contacts et les frottements.")
        mod.actions(k)

    defaut = next(iter(mod.EXEMPLES.values()))

    def parametres():
        p = {}
        for nom, val in defaut.items():
            x = st.session_state.get(f"{k}_{nom}")
            p[nom] = val if x is None else x
        return p

    with gauche.container(border=True, key="carte_4"):
        etape(4, "Et à cet instant ?", "Ce qui se passe au moment où on regarde.")
        mod.etat(k, parametres())

p = parametres()
scene = mod.construire(p)
nom = (p["nom"] or "le système").strip()
a_ouvrir = None

# ---------------------------------------------------------------------------
# Le schéma
# ---------------------------------------------------------------------------

with droite:
    with st.container(key="droite"):
        with st.container(border=True, key="carte_schema"):
            st.html(f'<div class="schema-titre"><span class="t">Schéma des forces</span>'
                    f'<span class="s">{escape(nom)} · {fr(p["m"])} kg</span></div>')
            options = st.pills("Afficher", list(OPTIONS), format_func=OPTIONS.get, selection_mode="multi",
                               key="options", label_visibility="collapsed")
            options = set(options or [])
            svg_aff, svg_exp = rendre(scene, options)
            clic = cliquable(svg_aff, key=f"schema_{k}")
            a_ouvrir = clic if clic is not None else a_ouvrir
            st.caption(":material/touch_app: Clique sur une flèche pour voir la formule de la force "
                       "et d'où vient sa valeur.")
            for a in scene.alertes:
                st.warning(a, icon=":material/warning:")
            e1, e2, e3 = st.columns([1, 1, 1.5])
            fichier = re.sub(r"[^a-z0-9]+", "-", nom.lower()).strip("-") or "schema"
            try:
                e1.download_button("PNG", en_png(svg_exp), file_name=f"schema-{fichier}.png", mime="image/png",
                                   icon=":material/download:", width="stretch")
            except Exception:
                e1.caption("Export PNG indisponible ici.")
            e2.download_button("SVG", svg_exp.encode("utf-8"), file_name=f"schema-{fichier}.svg",
                               mime="image/svg+xml", icon=":material/download:", width="stretch")
            with e3.popover("Bilan à copier", icon=":material/content_copy:", width="stretch"):
                texte = [f"Système : {nom}, de masse m = {fr(p['m'])} kg.",
                         "Référentiel : terrestre, supposé galiléen.", "Bilan des forces :"]
                texte += [f"- {f.nom} {f.lettre}{('_' + f.indice) if f.indice else ''} = {f.expression} = "
                          f"{fr(f.valeur)} N, {f.sens}" for _, f in scene.visibles]
                texte.append("Résultante : " + scene.mouvement.replace("**", ""))
                st.code("\n".join(texte), language=None, wrap_lines=True)

# ---------------------------------------------------------------------------
# Bilan, résultante, à retenir
# ---------------------------------------------------------------------------

with st.container(border=True, key="carte_bilan"):
    b1, b2, b3 = st.columns([1.3, 1, 1], gap="large")
    with b1:
        st.html('<div class="titre-bloc">Bilan des forces</div>'
                '<div class="sous-titre">Clique sur une force pour ouvrir sa fiche.</div>')
        clic = cliquable(bilan_html(scene), key=f"bilan_{k}")
        a_ouvrir = clic if clic is not None else a_ouvrir
    with b2:
        st.html('<div class="titre-bloc">Ce que dit la résultante</div>')
        st.markdown(joli(scene.mouvement))
    with b3:
        st.html('<div class="titre-bloc">À retenir</div>')
        with st.container(key="retenir"):
            st.markdown("\n".join(f"- {joli(r)}" for r in scene.retenir))

st.html(f'<div class="pied"><span>L\'atelier des forces · bêta {VERSION} · par Mohammed Bennani</span>'
        f'<span>Code ouvert sur {github} : les forks et les propositions de modification sont bienvenus.</span></div>')

if a_ouvrir is not None and 0 <= a_ouvrir < len(scene.forces):
    ouvrir_fiche(scene, options, a_ouvrir)
