# TranspoBot — Soutenance Projet GLSi L3
Ce document contient la trame de votre présentation PowerPoint. Copiez/collez ces éléments dans vos slides PowerPoint ou Keynote.

---

### Slide 1 : Page de Garde
**Titre :** TranspoBot : L'Intelligence Artificielle au Service de la Mobilité Urbaine
**Sous-titre :** Projet d'Intégration d'IA dans les SI - Licence 3 GLSi
**Noms des membres :** [Nom du binôme/trinôme]
**Enseignant :** Pr. Ahmath Bamba MBACKE
**Date :** [Date de soutenance]

---

### Slide 2 : Plan de la Présentation
1. Le contexte et la problématique
2. TranspoBot : Notre solution
3. Modélisation Conceptuelle et Logique
4. Architecture Technique 
5. L'intégration IA : Prompt Engineering & Sécurité
6. Démonstration Finale
7. Conclusion et Perspectives

---

### Slide 3 : Contexte et Problématique
- **Le Secteur :** Les sociétés de transport urbain accumulent de vastes quantités de données (trajets, incidents, pannes, retards).
- **Le Problème :** Analyser ces données requiert généralement de solides compétences en SQL (Tableaux de bords figés).
- **Le Besoin :** Permettre au décisionnel ("C-level" ou gestionnaire d'exploitation) d'interroger la donnée avec ses propres mots, intuitivement.

---

### Slide 4 : TranspoBot : Notre Solution
- **Une interface métier Premium :** Un tableau de bord moderne, accessible depuis un navigateur, respectant les normes ergonomiques.
- **Un chatbot propulsé par l'IA :** Le système "Text-to-SQL" interprète les langues naturelles (Français/Anglais) et fouille nos bases invisibles à la volée.
- **Les Entités gérées :** Véhicules, Chauffeurs, Lignes, Tarifs, Trajets et Incidents.

---

### Slide 5 : Modélisation des Données
*(Insérer ici une capture d'écran de votre MCD généré par Mermaid depuis le rapport Markdown)*
**Points Clés :**
- Architecture relationnelle solide (MySQL InnoDb).
- Un "**Trajet**" est l'entité centrale qui fait le lien entre une ligne physique, une ressource matérielle (véhicule) et humaine (chauffeur).

---

### Slide 6 : Architecture Technique
*(Créer un petit schéma visuel sur PowerPoint)*
- **Frontend** : HTML5 / CSS3 (CSS Variables, Glassmorphism design), JavaScript Vanilla (API Fetch).
- **Backend API** : Python (Framework **FastAPI**), `mysql-connector`.
- **Base de données** : MySQL 8.
- **Fournisseur IA (LLM)** : OpenAI API (Modèle GPT-4o-mini).

---

### Slide 7 : Le Cœur du Réacteur : Prompt Engineering
- L'IA n'est pas "laissée libre", elle est encadrée via le "Prompt Système".
- Ce que nous passons secrètement au LLM avant chaque réponse :
  1. Le rôle (`Tu es TranspoBot, l'assistant...`)
  2. Le Modèle Logique de la BDD pour qu'il connaisse les colonnes.
  3. L'heure et la date d'**AUJOURD'HUI** `(Ex: 01 Avril)` pour le repérage temporel.
  4. L'instruction stricte : Produire uniquement du format JSON `{ "sql": "...", "explication": "..." }`.

---

### Slide 8 : Sécurité (Zero Trust)
*Comment empêcher l'IA ou l'utilisateur de détruire notre base de données via le chat ?*
- **La Consigne LLM** : "Génère UNIQUEMENT des requêtes SELECT."
- **La Validation Python (Backend)** : 
  - Analyse Regex avant exécution dans l'API.
  - Tout `DELETE`, `DROP`, `UPDATE` ou `INSERT` génère un rejet total et immédiat du backend. Seul du `SELECT` est autorisé.
  - Limit 50 forcée.

---

### Slide 9 : Démonstration
*C'est le moment de la démo en live !*
- Montrer l'interface web (Onglets Véhicules / Chauffeurs).
- Poser une question simple : *"Combien de trajets avons-nous terminés ?"*
- Poser une question temporelle : *"Quel est le chiffre d'affaires (recette) du mois ?"*
- Poser un cas complexe (Jointure) : *"Qui sont les chauffeurs associés aux récents incidents graves ?"*

---

### Slide 10 : Déploiement
- **Infrastructure as Code** : Utilisation d'un fichier métier `render.yaml` pour assurer le CI/CD.
- Injection des secrets (Mots de passes bases de données et Clé API OpenAI) dans les variables d'environnements (Fichier `.env`).
- Serveur asynchrone (Uvicorn).

---

### Slide 11 : Conclusion & Perspectives
- **Synthèse :** Intégrer un "Cerveau LLM" remanié au cœur d'une architecture SGBD modifie drastiquement le métier de l'analyste de données.
- **Perspectives :** 
  - Passer sur des modèles locaux hébergés (Ollama / Llama 3) pour respecter la confidentialité des données de l'entreprise.
  - Permettre des graphes (Data Visualization) générés par LLM via Python.

---
**Slide 12 : MERCI POUR VOTRE ATTENTION.** Questions ?
