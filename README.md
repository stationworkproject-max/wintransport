# 🚆 WinTransport TN (وين الترنسبور)
### Suivi en temps réel & crowd-sourcé du transport public en Tunisie

Application web et mobile temps réel basée sur le réseau **Tunismapper** (Métro léger de Tunis, TGM, RFR, Trains SNCFT, Bus Transtu) et synchronisée avec **Supabase** (`rqwpafatgsyncvretjym`).

---

## 🌟 Fonctionnalités Principales

1. **Carte Interactive en Direct** :
   - Affichage de toutes les lignes et stations du Grand Tunis et liaisons régionales (Métro 1 à 6, TGM, RFR A/D/E, Trains, Bus).
   - Trace des lignes officielles avec codes couleurs fidèles à Tunismapper.
   - Balises des véhicules en direct avec anneau radar animé (vitesse, direction, nombre de voyageurs à bord).

2. **Mode Passager « Je suis à bord »** :
   - Un clic pour activer la diffusion GPS haute précision (`watchPosition`).
   - Détection automatique de la ligne la plus proche.
   - Partage anonyme et sécurisé de la position du véhicule à destination des voyageurs en attente aux stations.

3. **Panneau des Départs & Arrivées aux Stations** :
   - Cliquez sur n'importe quel arrêt pour connaître les prochains passages.
   - Distingue les passages théoriques et les arrivées vérifiées par GPS en direct (`🟢 LIVE GPS`).

4. **Signalements Communautaires Waze-Like** :
   - Signalez en 1 clic : Forte affluence / Rame bondée, Retard important, Panne, Trafic fluide.
   - Diffusion instantanée via Supabase Realtime WebSocket sans recharger la page.

5. **Mode Démo & Simulation Embarqué** :
   - Bouton « Mode Démo » permettant de simuler des rames et bus circulant sur les lignes avec mise à jour continue dans la base de données.

---

## 🛠️ Stack Technique

- **Frontend** : React 18, Vite, Tailwind CSS, Leaflet, Lucide Icons.
- **Backend & Base de données** : Supabase PostgreSQL (`rqwpafatgsyncvretjym`).
- **Temps Réel** : Supabase Realtime Channels (WebSockets).

---

## 🚀 Démarrage

```bash
# Lancer le serveur de développement
npm run dev

# Accéder à l'application
http://localhost:3000
```
