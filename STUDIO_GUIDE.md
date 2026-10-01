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

### 2. Gestion Ciblée Aller (0), Retour (1) & Les Deux (Simultané)
- **Cible de Correction & Tracé :**
  - 🔵 **Aller (0)** : Voie active en Cyan.
  - 🟠 **Retour (1)** : Voie active en Ambre.
  - 🟣 **Les Deux (Simultané)** : Permet de tracer et corriger les voies Aller ET Retour en parallèle en un seul clic !
- **Affichage sur la carte :** Deux cases à cocher permettent d'afficher l'Aller seul, le Retour seul, ou les deux voies superposées sur le plan Google Maps.

### 3. Fonds de Carte Haute Précision
- 🗺️ **Plan Google (Par défaut)** : Affiche le véritable fond de carte routier de Google Maps avec le réseau des rues, numéros de routes nationales (RN, RR, R33...), ponts, giratoires et terre-pleins centraux.
- 🛰️ **Satellite Google** : Imagerie aérienne détaillée pour positionner les voies sur les chaussées et quais physiques.
- 🚦 **Trafic Google** : Visualisation en direct du trafic et des axes principaux.
- 🌙 **Plan Sombre** : Mode haute visibilité nocturne.

### 4. 🧭 Tracé d'Itinéraire Tronçon (Nœud A ➔ Nœud B) style Google Maps
Pour corriger un tronçon problématique (par exemple un virage coupé, un terre-plein franchi illégalement ou un demi-tour manqué) :
1. Activez le mode **« Arrondir / Tronçon »**.
2. **Cliquez sur le Nœud A** (Point de départ / point d'origine) 👉 un badge vert fluo **`A (Départ)`** s'affiche sur la carte.
3. **Cliquez sur le Nœud B** (Point d'arrivée / prochain point à atteindre) 👉 un badge rouge **`B (Arrivée)`** s'affiche sur la carte.
4. **Tracé Automatique :** Si l'option *« Tracer auto dès sélection du Nœud B »* est cochée, le tronçon est instantanément recalculé et plaqué sur la route selon l'itinéraire Google Maps !
5. **Respect strict du code de la route :**
   - L'itinéraire prend obligatoirement les ronds-points (« hip ») pour faire demi-tour.
   - Il emprunte les bretelles et ponts légaux sans jamais couper à travers les terre-pleins ou rails.
6. **Bouton « Inverser A ⇄ B » :** Inverse immédiatement le sens de parcours en cas de besoin.
7. **Bouton « Tracer l'Itinéraire Google Maps (A ➔ B) » :** Déclenche le calcul manuel à la demande.

### 5. 🪄 Tracé Global de la Ligne & Anti-Boucles
- Cliquez sur **« Tracer la Voie »** pour recalculer l'ensemble de l'itinéraire le long de tous les arrêts.
- Si le mode **« Les Deux »** est sélectionné, l'Aller et le Retour sont tous les deux calculés et synchronisés en parallèle.
- Le bouton **« Supprimer les Boucles & Demi-Tours »** élimine les petits décrochés ou fausses manœuvres.

### 6. 🪄 Outil d'Arrondi & Lissage de Virage (Anti-Angles)
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

### 7. 📍 Gestion Complète des Stations & Synchronisation Base de Données
- **Déplacement fluide sur la carte :** Glissez directement n'importe quelle pastille numérotée d'arrêt sur les quais ou les trottoirs.
- **Mise à jour en cascade dans la base de données :** Lorsque vous déplacez un arrêt et cliquez sur **« Enregistrer Base »**, les nouvelles coordonnées (`lat`, `lon`) sont instantanément sauvegardées dans `src/data/staticTransit.js`. Si cet arrêt est partagé avec d'autres lignes (ex: Place de Barcelone, Passage, Bab Saadoun...), toutes les lignes du réseau sont automatiquement synchronisées !
- **➕ Ajouter une Nouvelle Station :**
  - Via le bouton **« + Nouvel Arrêt »** : ouvre un formulaire pour renseigner le nom en Français, le nom en Arabe, les coordonnées et la position dans la ligne (début/fin).
  - Via le bouton **« 🖱️ Au Clic »** : cliquez directement sur l'imagerie satellite pour pré-remplir les coordonnées exactes du nouvel arrêt.
- **✏️ Modifier ou Supprimer un Arrêt :** Cliquez sur une pastille d'arrêt ou sur l'icône crayon dans la liste des arrêts pour éditer ses noms bilingues ou le supprimer.

### 8. Opérations Automatiques
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

