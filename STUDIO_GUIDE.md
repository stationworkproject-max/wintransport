# 🚆 WinTransport Studio — Guide d'Utilisation

**WinTransport Studio** est une application web interactive d'édition cartographique SIG conçue pour modifier, tracer, corriger et lisser les voies ferroviaires, les lignes de bus et les arrêts de transport en Tunisie, sans modifier manuellement les fichiers de code.

---

## 🚀 1. Lancement Rapide

Pour lancer le Studio localement :

```bash
npm run studio
```
*(ou directement : `python scripts/studio_server.py`)*

Ouvrez ensuite votre navigateur à l'adresse :
👉 **[http://127.0.0.1:5055/studio.html](http://127.0.0.1:5055/studio.html)**

---

## 🗺️ 2. Fonctionnalités Principales

### 1. Sélection de Ligne & Filtres Réseaux
- **Filtres par réseau :** Tous, Métro Léger (1 à 6), TGM, RFR (Lignes E & D), Trains SNCFT (Grandes Lignes & Banlieue Sud), Bus Transtu (toutes les lignes urbaines).
- **Recherche Instantanée :** Tapez le numéro ou nom de ligne (ex: `TGM`, `Métro 4`, `38B`, `RFR E`, `SNCFT 21`...).

### 2. Gestion Indépendante Aller (0) & Retour (1)
- **Choix de la voie à éditer :**
  - 🔵 **Aller (0)** : Voie active en Cyan avec poignées de manipulation.
  - 🟠 **Retour (1)** : Voie active en Ambre avec poignées de manipulation.
- **Affichage simultané ou individuel :** Deux cases à cocher permettent d'afficher l'Aller seul, le Retour seul, ou **les deux voies en même temps** pour aligner les deux voies parallèles avec précision sur l'imagerie satellite.

### 3. Édition des Nœuds & Tracés
- **Déplacer un nœud :** Cliquez et glissez n'importe quel point rond sur la carte satellite. Le tracé s'adapte en temps réel à 60 FPS sans clignotement.
- **Insérer un nœud :** **Double-cliquez directement sur la ligne** à l'endroit souhaité pour insérer un nouveau point.
- **Supprimer un nœud :** **Clic droit** sur un nœud rond pour le supprimer.
- **Mode Ajouter au Clic :** Permet de prolonger le tracé point par point en cliquant sur la carte (option *Ajouter à la Fin* ou *Ajouter au Début*).

### 4. 🪄 Outil d'Arrondi & Lissage de Virage (Anti-Angles)
Pour transformer des virages bruts ou angulaires en **courbes circulaires parfaites** :
1. Dans l'onglet **« Outils & Virages »**, activez le mode **« 🪄 Arrondir Virage »**.
2. Cliquez sur le **Nœud A** (début du virage) 👉 il devient vert.
3. Cliquez sur le **Nœud B** (fin du virage) 👉 il devient rouge.
4. Choisissez la méthode :
   - **Chaikin (Recommandé)** : découpe et adoucit les virages de façon naturelle comme les vraies voies de tramway et chemin de fer.
   - **Spline Catmull-Rom** : génère une courbure spline ultra-fluide.
5. Réglez l'intensité (*Léger*, *Moyen*, *Fort*).
6. Cliquez sur **« 🪄 Arrondir le Virage Sélectionné »**.
7. *(Optionnel)* Cliquez sur **« Lisser Tous les Angles de la Ligne »** pour adoucir toute la ligne d'un seul coup.

### 5. Déplacement des Stations & Arrêts
- Activez le mode **« Déplacer Arrêts »** pour glisser directement les pastilles d'arrêts numérotées sur les quais ou les trottoirs.
- Bouton **« Ajouter un arrêt »** pour créer un nouvel arrêt au centre de la vue.

### 6. Opérations Automatiques
- **Inverser depuis la voie opposée :** Clone le tracé opposé en l'inversant.
- **Générer voie opposée parallèle (+3.5m) :** Crée automatiquement une voie parallèle décalée de 3.5 mètres.
- **Annuler / Rétablir :** Raccourcis clavier `Ctrl+Z` et `Ctrl+Y`.

---

## 💾 3. Enregistrement & Compilation

- **Bouton « 💾 Enregistrer » :** Sauvegarde instantanément les modifications directement dans :
  - `src/data/transitShapes.json` (géométries précises Aller et Retour).
  - `src/data/staticTransit.js` (coordonnées et liste des arrêts).
- **Bouton « 🚀 Compiler & Sync » :** Déclenche la compilation de production (`npm run build`) et la synchronisation avec le projet Android (`npx cap sync android`).

---

## 📁 4. Architecture des Fichiers Studio

- `public/studio.html` : Interface web de l'éditeur cartographique (Leaflet + Tailwind).
- `scripts/studio_server.py` : Serveur Python local gérant les requêtes de sauvegarde et de compilation sur le port `5055`.
- `public/studio_data.js` : Export statique des données des lignes et des tracés.
