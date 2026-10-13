# L'atelier des forces

Un faiseur de schémas de forces pour la mécanique du point (PCSI), en une seule page.
Simulateur en cours de développement par **Mohammed Bennani**, ouvert aux modifications :
forke le projet et propose les tiennes.

## Ce que fait l'application

On décrit la situation en quatre questions, et le schéma se construit en direct,
avec des vecteurs dessinés à l'échelle du poids.

1. **Quelle situation ?** Pente, chute, sol plat, virage, bosse ou dôme, pendule.
2. **Qui est le système ?** Un nom, une masse, ou un exemple tout prêt.
3. **Quelles actions s'exercent sur lui ?** Frottements, câble, corde, force motrice, poussée d'Archimède…
4. **Et à cet instant ?** Vitesse, angle, sens du mouvement.

On clique sur une flèche du schéma, ou sur une ligne du bilan, pour ouvrir la **fiche de la force** :
qui l'exerce, sa direction, sa formule, d'où elle vient (quelle loi, quelle projection),
et le calcul avec les valeurs choisies.

Le schéma s'exporte en PNG ou en SVG, et le bilan se copie en texte.

## Organisation des fichiers

```
app.py                 la page : les quatre questions, le schéma, le bilan, la fiche
situations/            une situation par fichier : dessin, forces et fiches
moteur/scene.py        forces, échelle des vecteurs, résultante, fiches
moteur/dessin.py       primitives de dessin SVG et export PNG
moteur/cliquable.py    composant qui rend les flèches et les lignes cliquables
moteur/ui.py           petits composants d'interface
polices/               polices libres pour l'export PNG (licences incluses)
.streamlit/config.toml couleurs de l'interface
requirements.txt       bibliothèques à installer
```

Pour ajouter une situation : copier un fichier de `situations/`, l'adapter, puis l'ajouter au
dictionnaire `SITUATIONS` en haut de `app.py`.

## Lancer sur son ordinateur

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Contribuer

1. Clique sur **Fork** en haut de la page du dépôt GitHub : tu obtiens ta propre copie.
2. Fais tes modifications dans ta copie.
3. Ouvre une **pull request** pour proposer de les intégrer au projet.

## Mettre en ligne avec Streamlit Community Cloud (gratuit)

1. Crée un dépôt GitHub (par exemple `atelier-forces`) et dépose-y **tout le contenu** du dossier,
   y compris les dossiers `situations`, `moteur`, `polices` et `.streamlit`.
2. Va sur [share.streamlit.io](https://share.streamlit.io) et connecte-toi avec ton compte GitHub.
3. « Create app », choisis le dépôt, la branche `main` et le fichier `app.py`.
   Dans les réglages avancés, choisis Python 3.12 ou 3.13.
4. « Deploy ». L'application obtient une adresse en `.streamlit.app`.
5. Colle l'adresse du dépôt dans `DEPOT_GITHUB`, en haut de `app.py` : le mot « GitHub » de la page
   devient un lien.
