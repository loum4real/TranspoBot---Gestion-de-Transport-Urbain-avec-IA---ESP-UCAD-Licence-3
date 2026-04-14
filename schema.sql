-- ============================================================
--  TranspoBot — Base de données MySQL
--  Projet GLSi L3 — ESP/UCAD
-- ============================================================
-- Ce script contient le Modèle Logique de Données (MLD) ainsi 
-- qu'un jeu de données de test enrichi pour la démonstration.
-- 
-- Modélisation:
-- 1. VEHICULES <-(1,1)---[Conduit/Assigné]---(0,1)-> CHAUFFEURS
--    Un chauffeur peut être assigné à un véhicule.
-- 2. LIGNES <-(1,n)---[Propose]---(1,1)-> TARIFS
-- 3. TRAJETS(n,1)-> LIGNES | (n,1)-> CHAUFFEURS | (n,1)-> VEHICULES
--    Le trajet est au coeur du système.
-- 4. INCIDENTS(n,1)-> TRAJETS
-- ============================================================

CREATE DATABASE IF NOT EXISTS transpobot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE transpobot;

-- ============================================================
-- DEFINITION DES TABLES (DDL)
-- ============================================================

-- Table : véhicules (Flotte physique)
CREATE TABLE IF NOT EXISTS vehicules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,
    type ENUM('bus','minibus','taxi') NOT NULL,
    capacite INT NOT NULL,
    statut ENUM('actif','maintenance','hors_service') DEFAULT 'actif',
    kilometrage INT DEFAULT 0,
    date_acquisition DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table : utilisateurs (Gestion des accès)
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_utilisateur VARCHAR(50) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    nom_complet VARCHAR(100),
    role ENUM('admin', 'gestionnaire') DEFAULT 'gestionnaire',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertion du compte administrateur principal du système
-- Le mot de passe est sécurisé via la fonction de hachage unidirectionnelle (SHA-256)
INSERT IGNORE INTO utilisateurs (nom_utilisateur, mot_de_passe, nom_complet, role) 
VALUES ('admin', '$pbkdf2-sha256$29000$2ds7x1irdW4txXjv3Ttn7A$aBBtx1OiU5WLJH95ddkdC0FJTSjNSkSRGYe6MxQeb7c', 'Admin TranspoBot', 'admin');


-- Table : chauffeurs (Ressources humaines)
CREATE TABLE IF NOT EXISTS chauffeurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    numero_permis VARCHAR(30) UNIQUE NOT NULL,
    categorie_permis VARCHAR(5),
    disponibilite BOOLEAN DEFAULT TRUE,
    vehicule_id INT, -- Un chauffeur a généralement un véhicule principal
    date_embauche DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id) ON DELETE SET NULL
);

-- Table : lignes (Itinéraires planifiés)
CREATE TABLE IF NOT EXISTS lignes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    nom VARCHAR(100),
    origine VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km DECIMAL(6,2),
    duree_minutes INT
);

-- Table : tarifs (Grille tarifaire par ligne)
CREATE TABLE IF NOT EXISTS tarifs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ligne_id INT NOT NULL,
    type_client ENUM('normal','etudiant','senior') DEFAULT 'normal',
    prix DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (ligne_id) REFERENCES lignes(id) ON DELETE CASCADE
);

-- Table : trajets (Instanciation d'un voyage)
CREATE TABLE IF NOT EXISTS trajets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ligne_id INT NOT NULL,
    chauffeur_id INT NOT NULL,
    vehicule_id INT NOT NULL,
    date_heure_depart DATETIME NOT NULL,
    date_heure_arrivee DATETIME,
    statut ENUM('planifie','en_cours','termine','annule') DEFAULT 'planifie',
    nb_passagers INT DEFAULT 0,
    recette DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ligne_id) REFERENCES lignes(id),
    FOREIGN KEY (chauffeur_id) REFERENCES chauffeurs(id),
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
);

-- Table : incidents (Suivi des pannes, accidents, etc.)
CREATE TABLE IF NOT EXISTS incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trajet_id INT NOT NULL,
    type ENUM('panne','accident','retard','autre') NOT NULL,
    description TEXT,
    gravite ENUM('faible','moyen','grave') DEFAULT 'faible',
    date_incident DATETIME NOT NULL,
    resolu BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trajet_id) REFERENCES trajets(id) ON DELETE CASCADE
);

-- ============================================================
-- INSERTIONS DE DONNEES (DML) - POUR DEMONSTRATION JURY
-- ============================================================

INSERT IGNORE INTO vehicules (immatriculation, type, capacite, statut, kilometrage, date_acquisition) VALUES
('DK-1234-AB', 'bus', 60, 'actif', 45000, '2021-03-15'),
('DK-5678-CD', 'minibus', 25, 'actif', 32000, '2022-06-01'),
('DK-9012-EF', 'bus', 60, 'maintenance', 78000, '2019-11-20'),
('DK-3456-GH', 'taxi', 4, 'actif', 120000, '2020-01-10'),
('DK-7890-IJ', 'minibus', 25, 'actif', 15000, '2023-09-05'),
('DK-1111-AA', 'bus', 65, 'hors_service', 150000, '2016-05-12'),
('DK-2222-BB', 'minibus', 30, 'actif', 20000, '2024-01-10');

INSERT IGNORE INTO chauffeurs (nom, prenom, telephone, numero_permis, categorie_permis, vehicule_id, date_embauche) VALUES
('DIOP', 'Mamadou', '+221771234567', 'P-2019-001', 'D', 1, '2019-04-01'),
('FALL', 'Ibrahima', '+221772345678', 'P-2020-002', 'D', 2, '2020-07-15'),
('NDIAYE', 'Fatou', '+221773456789', 'P-2021-003', 'B', 4, '2021-02-01'),
('SECK', 'Ousmane', '+221774567890', 'P-2022-004', 'D', 5, '2022-10-20'),
('BA', 'Aminata', '+221775678901', 'P-2023-005', 'D', NULL, '2023-01-10'),
('GAYE', 'Modou', '+221776666666', 'P-2018-009', 'D', 7, '2018-11-01');

INSERT IGNORE INTO lignes (code, nom, origine, destination, distance_km, duree_minutes) VALUES
('L1', 'Ligne Dakar-Thiès', 'Dakar', 'Thiès', 70.5, 90),
('L2', 'Ligne Dakar-Mbour', 'Dakar', 'Mbour', 82.0, 120),
('L3', 'Ligne Centre-Banlieue', 'Plateau', 'Pikine', 15.0, 45),
('L4', 'Ligne Aéroport', 'Centre-ville', 'AIBD', 45.0, 60);

INSERT IGNORE INTO tarifs (ligne_id, type_client, prix) VALUES
(1, 'normal', 2500), (1, 'etudiant', 1500), (1, 'senior', 1800),
(2, 'normal', 3000), (2, 'etudiant', 1800),
(3, 'normal', 500),  (3, 'etudiant', 300),
(4, 'normal', 5000), (4, 'etudiant', 3000);

-- Insertion de trajets historiques (récents) et d'aujourd'hui
INSERT IGNORE INTO trajets (ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_ADD(DATE_SUB(NOW(), INTERVAL 5 DAY), INTERVAL 90 MINUTE), 'termine', 55, 137500),
(1, 2, 2, DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_ADD(DATE_SUB(NOW(), INTERVAL 4 DAY), INTERVAL 90 MINUTE), 'termine', 20, 50000),
(2, 3, 4, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_ADD(DATE_SUB(NOW(), INTERVAL 3 DAY), INTERVAL 120 MINUTE), 'termine', 4, 12000),
(3, 4, 5, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_ADD(DATE_SUB(NOW(), INTERVAL 2 DAY), INTERVAL 45 MINUTE), 'termine', 22, 11000),
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(DATE_SUB(NOW(), INTERVAL 1 DAY), INTERVAL 90 MINUTE), 'termine', 58, 145000),
(4, 2, 2, DATE_SUB(NOW(), INTERVAL 10 HOUR), DATE_ADD(DATE_SUB(NOW(), INTERVAL 10 HOUR), INTERVAL 60 MINUTE), 'termine', 18, 90000),
(3, 6, 7, DATE_SUB(NOW(), INTERVAL 1 HOUR), NULL, 'en_cours', 30, 15000),
(1, 5, 1, DATE_ADD(NOW(), INTERVAL 2 HOUR), NULL, 'planifie', 0, 0);

-- Insertion d'incidents
-- Afin de matcher les IDs avec IGNORE potentiellement, on lie statiquement ou en considérant les auto increments (1 à 8)
INSERT IGNORE INTO incidents (trajet_id, type, description, gravite, date_incident, resolu) VALUES
(2, 'retard', 'Embouteillage monstre à la sortie de Dakar', 'faible', DATE_SUB(NOW(), INTERVAL 4 DAY), TRUE),
(3, 'panne', 'Crevaison du pneu avant droit', 'moyen', DATE_SUB(NOW(), INTERVAL 3 DAY), TRUE),
(6, 'accident', 'Accrochage léger au rond-point, pare-choc endommagé', 'grave', DATE_SUB(NOW(), INTERVAL 10 HOUR), FALSE);
