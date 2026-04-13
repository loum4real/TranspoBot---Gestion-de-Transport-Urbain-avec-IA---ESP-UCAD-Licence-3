import os
import mysql.connector
from mysql.connector import Error, pooling
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TranspoBot - Gestion de Transport")

# Configuration via variables d'environnement
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "Seydina20042018")
DB_NAME = os.getenv("DB_NAME", "transpobot")
SECRET_KEY = os.getenv("SECRET_KEY", "cle_secrete_transpobot_2024")
ALGORITHM = "HS256"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pool de connexion pour plus de performance
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="transpopool",
    pool_size=5,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    charset='utf8mb4',
    use_unicode=True
)

def executer_requete(requete, params=None):
    try:
        conn = db_pool.get_connection()
        curseur = conn.cursor(dictionary=True)
        curseur.execute("SET NAMES utf8mb4")
        curseur.execute(requete, params or ())
        resultat = curseur.fetchall()
        conn.commit()
        return resultat
    except Error as e:
        if 'conn' in locals(): conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'curseur' in locals(): curseur.close()
        if 'conn' in locals(): conn.close()

# ── Sécurité & Auth ──────────────────────────────────────────
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def obtenir_u_connecte(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        u_name = payload.get("sub")
        u = executer_requete("SELECT * FROM utilisateurs WHERE nom_utilisateur=%s", (u_name,))
        if not u: raise HTTPException(status_code=401)
        return u[0]
    except: raise HTTPException(status_code=401)

@app.on_event("startup")
async def initialiser():
    # Création admin par défaut si vide
    res = executer_requete("SELECT COUNT(*) as n FROM utilisateurs")
    if res[0]['n'] == 0:
        h_pass = pwd_context.hash("admin123")
        executer_requete("INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, nom_complet, role) VALUES (%s, %s, %s, 'admin')",
                        ("admin", h_pass, "Administrateur"))

# ── Modèles Pydantic ──────────────────────────────────────────
class ModèleInscription(BaseModel):
    nom_utilisateur: str
    mot_de_passe: str
    nom_complet: str

class ModèleVéhicule(BaseModel):
    immatriculation: str
    type: str
    capacite: int
    statut: str

class ModèleChauffeur(BaseModel):
    nom: str
    prenom: str
    telephone: str
    numero_permis: str
    categorie_permis: str
    vehicule_id: Optional[int] = None

class ModèleTrajet(BaseModel):
    ligne_id: int
    chauffeur_id: int
    vehicule_id: int
    date_heure_depart: str
    recette: float = 0.0

# ── Routes API ────────────────────────────────────────────────
@app.post("/api/auth/inscription")
def inscription(u: ModèleInscription):
    h_pass = pwd_context.hash(u.mot_de_passe)
    executer_requete("INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, nom_complet, role) VALUES (%s, %s, %s, 'gestionnaire')",
                    (u.nom_utilisateur, h_pass, u.nom_complet))
    return {"ok": True}

@app.post("/api/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    u = executer_requete("SELECT * FROM utilisateurs WHERE nom_utilisateur=%s", (form.username,))
    if not u or not pwd_context.verify(form.password, u[0]['mot_de_passe']):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token = jwt.encode({"sub": u[0]['nom_utilisateur'], "exp": datetime.utcnow() + timedelta(days=1)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": {"nom_complet": u[0]['nom_complet'], "role": u[0]['role']}}

@app.get("/api/stats")
def stats():
    t = executer_requete("SELECT COUNT(*) as n FROM trajets")[0]['n']
    v = executer_requete("SELECT COUNT(*) as n FROM vehicules WHERE statut='actif'")[0]['n']
    r = executer_requete("SELECT SUM(recette) as n FROM trajets")[0]['n'] or 0
    c = executer_requete("SELECT COUNT(*) as n FROM chauffeurs WHERE disponibilite=1")[0]['n']
    return {"total_trajets": t, "vehicules_actifs": v, "recette_totale": float(r), "chauffeurs_libres": c}

@app.get("/api/vehicules")
def list_v(): return executer_requete("SELECT * FROM vehicules")

@app.post("/api/vehicules")
def add_v(v: ModèleVéhicule, u: dict = Depends(obtenir_u_connecte)):
    if u['role'] not in ['admin', 'gestionnaire']: raise HTTPException(status_code=403)
    executer_requete("INSERT INTO vehicules (immatriculation, type, capacite, statut) VALUES (%s,%s,%s,%s)", (v.immatriculation, v.type, v.capacite, v.statut))
    return {"ok": True}

@app.get("/api/chauffeurs")
def list_c(): return executer_requete("SELECT c.*, v.immatriculation FROM chauffeurs c LEFT JOIN vehicules v ON c.vehicule_id = v.id")

@app.post("/api/chauffeurs")
def add_c(c: ModèleChauffeur, u: dict = Depends(obtenir_u_connecte)):
    if u['role'] not in ['admin', 'gestionnaire']: raise HTTPException(status_code=403)
    executer_requete("INSERT INTO chauffeurs (nom, prenom, telephone, numero_permis, categorie_permis, vehicule_id) VALUES (%s,%s,%s,%s,%s,%s)", (c.nom, c.prenom, c.telephone, c.numero_permis, c.categorie_permis, c.vehicule_id))
    return {"ok": True}

@app.get("/api/trajets")
def list_t(): return executer_requete("SELECT t.*, l.nom as ligne, CONCAT(ch.prenom, ' ', ch.nom) as chauffeur_nom, v.immatriculation FROM trajets t JOIN lignes l ON t.ligne_id = l.id JOIN chauffeurs ch ON t.chauffeur_id = ch.id JOIN vehicules v ON t.vehicule_id = v.id ORDER BY t.date_heure_depart DESC")

@app.post("/api/trajets")
def add_t(t: ModèleTrajet, u: dict = Depends(obtenir_u_connecte)):
    if u['role'] not in ['admin', 'gestionnaire']: raise HTTPException(status_code=403)
    executer_requete("INSERT INTO trajets (ligne_id, chauffeur_id, vehicule_id, date_heure_depart, recette) VALUES (%s,%s,%s,%s,%s)", (t.ligne_id, t.chauffeur_id, t.vehicule_id, t.date_heure_depart, t.recette))
    return {"ok": True}

@app.get("/api/lignes")
def list_l(): return executer_requete("SELECT * FROM lignes")

@app.get("/api/utilisateurs")
def list_u(u: dict = Depends(obtenir_u_connecte)):
    if u['role'] != 'admin': raise HTTPException(status_code=403)
    return executer_requete("SELECT id, nom_utilisateur, nom_complet, role FROM utilisateurs")

# Montage statique
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
