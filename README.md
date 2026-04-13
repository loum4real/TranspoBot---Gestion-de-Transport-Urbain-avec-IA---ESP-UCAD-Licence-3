# TranspoBot 🚌

**TranspoBot** est une plateforme moderne de gestion de transport conçue pour optimiser la gestion des flottes, des chauffeurs et de la planification des trajets.

## ✨ Fonctionnalités
- 📊 **Tableau de bord interactif** avec KPIs en temps réel.
- 🚛 **Gestion de flotte** : CRUD complet sur les véhicules.
- 👤 **Registre des chauffeurs** : Suivi des disponibilités.
- 📅 **Planification des trajets** : Assignation dynamique ligne/bus/chauffeur.
- 🔐 **Sécurité** : Authentification JWT et rôles (Admin, Gestionnaire).
- 🤖 **Assistant Intelligent** : Interface de chat intégrée.

## 🛠️ Stack Technique
- **Backend** : FastAPI (Python 3.10+)
- **Base de données** : MySQL
- **Frontend** : HTML5, Vanilla JS, CSS3, Highcharts
- **Sécurité** : JWT (JSON Web Tokens), PBKDF2 hashing

## 🚀 Installation

1. **Cloner le projet**
   ```bash
   git clone https://github.com/votre-user/transpobot.git
   cd transpobot
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer la base de données**
   - Créez une base de données MySQL nommée `transpobot`.
   - Importez le fichier `schema.sql`.

4. **Variables d'environnement**
   - Créez un fichier `.env` à la racine :
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASS=votre_mot_de_passe
   DB_NAME=transpobot
   SECRET_KEY=votre_cle_aleatoire
   ```

5. **Lancer l'application**
   ```bash
   python app.py
   ```

## 📝 Auteur
- Développé dans le cadre du projet GLSI.
