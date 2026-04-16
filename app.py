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

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="transpopool",
    pool_size=5,
    host=DB_HOST,
    port=DB_PORT,
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
    res = executer_requete("SELECT COUNT(*) as n FROM utilisateurs")
    if res[0]['n'] == 0:
        h_pass = pwd_context.hash("admin123")
        executer_requete("INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, nom_complet, role) VALUES (%s, %s, %s, 'admin')", ("admin", h_pass, "Administrateur"))

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

class QuestionIA(BaseModel):
    question: str

@app.post("/api/auth/inscription")
def inscription(u: ModèleInscription):
    h_pass = pwd_context.hash(u.mot_de_passe)
    executer_requete("INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe, nom_complet, role) VALUES (%s, %s, %s, 'gestionnaire')", (u.nom_utilisateur, h_pass, u.nom_complet))
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

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

@app.post("/api/chat")
async def chat_ia(q: QuestionIA):
    if not GROQ_API_KEY:
        return {"answer": "⚠️ Clé API Groq manquante. L'IA est désactivée."}

    # 1. Définition du Schéma pour le Text-to-SQL (On retire la table utilisateurs pour la sécurité)
    schema = """
    Table vehicules (id, immatriculation, type, capacite, statut)
    Table chauffeurs (id, nom, prenom, telephone, numero_permis, categorie_permis, vehicule_id, disponibilite)
    Table lignes (id, code, nom, origine, destination, distance_km, duree_minutes)
    Table tarifs (id, ligne_id, type_client, prix)
    Table trajets (id, ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette)
    Table incidents (id, trajet_id, type, description, gravite, date_incident, resolu)
    """

    prompt = f"""Tu es un expert Text-to-SQL MySQL.
    Schéma de la base de données :
    {schema}
    
    Tâche: Traduis la demande utilisateur en requête SQL MySQL SELECT.
    Demande: "{q.question}"
    
    Règles STRICTES:
    - Si l'utilisateur demande des infos sur les comptes ou mots de passe, refuse poliment.
    - "flotte", "bus", "véhicules" ou "voitures" désignent la table 'vehicules'.
    - Les statuts possibles pour un véhicule sont : 'actif', 'maintenance', 'hors_service'.
    - Si l'utilisateur demande "hors service" ou "en panne", cherche statut = 'hors_service'.
    - Si l'utilisateur fait une faute de frappe, utilise LIKE '%terme%' pour plus de flexibilité.
    - Fais des JOIN pour récupérer les noms réels quand nécessaire (ex: lignes.nom, vehicules.immatriculation).
    - NE CRÉE PAS DE COLONNES IMAGINAIRES. Utilise uniquement les colonnes listées dans le Schéma.
    - Qu'un "trajet fréquent" veut dire la "ligne" la plus utilisée (GROUP BY trajets.ligne_id).
    - Renvoie UNIQUEMENT la requête SQL. Aucun texte avant ou après, pas de balises. Commence par SELECT.
    """

    try:
        # ÉTAPE 1 : Appel à l'IA pour générer UNIQUEMENT la requête SQL
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 150
            },
            timeout=15
        )
        response.raise_for_status()
        sql_query = response.json()["choices"][0]["message"]["content"].strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # SÉCURITÉ : Si l'IA refuse ou génère autre chose qu'un SELECT
        if not sql_query.upper().startswith("SELECT"):
            return {"answer": "🔒 <strong>CONFIDENTIALITÉ :</strong> Je n'ai pas l'autorisation d'accéder aux comptes utilisateurs ou aux données de sécurité du système."}
        
        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "UTILISATEURS"]
        if any(kw in sql_query.upper() for kw in forbidden_keywords):
            return {"answer": "🔒 <strong>CONFIDENTIALITÉ :</strong> Ces données sont protégées. Je ne peux consulter que les informations liées à la flotte et aux trajets."}

        # ÉTAPE 2 : Exécution de la requête SQL
        result = executer_requete(sql_query)
        
        # Formatage de la réponse vide
        if not result:
            return {"answer": "Aucun résultat trouvé pour votre demande."}

        # ÉTAPE 3 : Synthèse en langage naturel
        prompt_synthese = f"""Tu es l'assistant de gestion TranspoBot.
Question de l'utilisateur : "{q.question}"
Résultats : {result[:10]}
Rédige une réponse courte en Français."""
        
        response_fr = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt_synthese}],
                "temperature": 0.3,
                "max_tokens": 150
            },
            timeout=10
        )
        response_fr.raise_for_status()
        phrase_fr = response_fr.json()["choices"][0]["message"]["content"].strip()

        # On renvoie uniquement la phrase naturelle (sans aucun tableau ni code SQL)
        return {"answer": f"<div style='font-weight:500;'>{phrase_fr}</div>"}

    except requests.exceptions.RequestException as e:
        print(f"Erreur API: {e}")
        raise HTTPException(status_code=503, detail="L'API Groq est injoignable.")
    except Exception as e:
        print(f"Erreur SQL généré : {e}")
        return {"answer": f"❌ L'IA a rencontré une erreur technique : <br><code>{str(e)}</code><br><small>Re-posez la question différemment.</small>"}

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

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Détection automatique du port pour Railway/Render
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
