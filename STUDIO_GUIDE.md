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

### 4. 🧭 Tracé Intelligent Directionnel & Anti-Boucle (Anti-Demi-Tour)
Pour générer ou corriger un itinéraire qui **épouse fidèlement la route dans le bon sens de circulation**, sans faire de demi-tours farfelus ni de boucles inutiles :
1. Rendez-vous dans l'onglet **« Routage & Outils »**.
2. Sélectionnez le **Mode de Routage** :
   - ⚡ **Automatique** : détecte automatiquement s'il s'agit d'une ligne ferroviaire (Métro, TGM, Train, RFR) ou de bus.
   - 🚗 **Routier Intelligent** : force le cap directionnel (`bearings`) et interdit formellement les demi-tours (`continue_straight=true`) pour rester sur la bonne chaussée (Aller vs Retour).
   - 🚌 **Direct & Couloirs Bus** : emprunte les couloirs de bus, voies réservées et zones piétonnes directes (Habib Bourguiba, Passage, Barcelone) sans détours autoroutiers.
   - 🚆 **Réseau Ferré Réel** : suit strictement les rails de chemin de fer et voies de métro léger (`rail.geojson`).
3. Options activées par défaut :
   - ☑️ **Anti-Boucle** : détecte et élimine automatiquement les boucles et épingles à cheveux où le véhicule quitte l'avenue et revient au même endroit.
   - ☑️ **Sens de Circulation Strict** : aligne le tracé sur la chaussée correspondant au sens Aller ou Retour.
4. **Tracer Tout l'Itinéraire :** Cliquez sur **« 🪄 Tracer Tout l'Itinéraire entre les Arrêts »**.
5. **Tracer / Corriger un Tronçon Spécifique :**
   - Sélectionnez le mode **« Arrondir / Tronçon »**.
   - Cliquez sur le **Nœud A** puis sur le **Nœud B** encadrant la zone à corriger.
   - Cliquez sur **« 🧭 Tracer ce Tronçon sur la Route »** pour réaligner uniquement cette portion sans toucher au reste de la ligne !
6. **Bouton « ✂️ Supprimer les Boucles & Demi-Tours du Tracé » :** Nettoie en 1 clic toute boucle ou détour parasite sur le tracé actif.

### 5. 🪄 Outil d'Arrondi & Lissage de Virage (Anti-Angles)
Pour transformer des virages bruts ou angulaires en **courbes circulaires parfaites** :
1. Dans l'onglet **« Routage & Outils »**, activez le mode **« 🪄 Arrondir Virage »**.
2. Cliquez sur le **Nœud A** (début du virage) 👉 il devient vert.
3. Cliquez sur le **Nœud B** (fin du virage) 👉 il devient rouge.
4. Choisissez la méthode :
   - **Chaikin (Recommandé)** : découpe et adoucit les virages de façon naturelle comme les vraies voies de tramway et chemin de fer.
   - **Spline Catmull-Rom** : génère une courbure spline ultra-fluide.
5. Réglez l'intensité (*Léger*, *Moyen*, *Fort*).
6. Cliquez sur **« 🪄 Arrondir ce Virage »**.
7. *(Optionnel)* Cliquez sur **« Lisser Tous les Angles de la Ligne »** pour adoucir toute la ligne d'un seul coup.

### 6. 📍 Gestion Complète des Stations & Synchronisation Base de Données
- **Déplacement fluide sur la carte :** Glissez directement n'importe quelle pastille numérotée d'arrêt sur les quais ou les trottoirs.
- **Mise à jour en cascade dans la base de données :** Lorsque vous déplacez un arrêt et cliquez sur **« Enregistrer Base »**, les nouvelles coordonnées (`lat`, `lon`) sont instantanément sauvegardées dans `src/data/staticTransit.js`. Si cet arrêt est partagé avec d'autres lignes (ex: Place de Barcelone, Passage, Bab Saadoun...), toutes les lignes du réseau sont automatiquement synchronisées !
- **➕ Ajouter une Nouvelle Station :**
  - Via le bouton **« + Nouvel Arrêt »** : ouvre un formulaire pour renseigner le nom en Français, le nom en Arabe, les coordonnées et la position dans la ligne (début/fin).
  - Via le bouton **« 🖱️ Au Clic »** : cliquez directement sur l'imagerie satellite pour pré-remplir les coordonnées exactes du nouvel arrêt.
- **✏️ Modifier ou Supprimer un Arrêt :** Cliquez sur une pastille d'arrêt ou sur l'icône crayon dans la liste des arrêts pour éditer ses noms bilingues ou le supprimer.

### 7. Opérations Automatiques
- **Inverser depuis la voie opposée :** Clone le tracé opposé en l'inversant.
- **Générer voie opposée parallèle (+3.5m) :** Crée automatiquement une voie parallèle décalée de 3.5 mètres.
- **Annuler / Rétablir :** Raccourcis clavier `Ctrl+Z` et `Ctrl+Y`.

---

## 💾 3. Enregistrement & Compilation

- **Bouton « 💾 Enregistrer Base » :** Sauvegarde instantanément les modifications directement dans :
  - `src/data/transitShapes.json` (géométries précises Aller et Retour).
  - `src/data/staticTransit.js` (coordonnées et liste des arrêts pour toutes les lignes connectées).
  - `public/studio_data.js` (synchronisation des caches locaux).
- **Bouton « 🚀 Compiler & Sync » :** Déclenche la compilation de production (`npm run build`) et la synchronisation avec le projet Android (`npx cap sync android`).

---

## 📁 4. Architecture des Fichiers Studio

- `public/studio.html` : Interface web de l'éditeur cartographique (Leaflet + Tailwind + Lucide).
- `scripts/studio_server.py` : Serveur Python local gérant le proxy de routage OSRM (`/api/route`), la persistance en base (`/api/save`), et la compilation (`/api/build`) sur le port `5055`.
- `public/studio_data.js` : Export statique des données des lignes et des tracés.

