import os
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', ''),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER', ''),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', ''),
    charset='utf8mb4'
)

def executer_requete(req):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(req)
    return cursor.fetchall()
    
schema = """
    Table utilisateurs (id, nom_utilisateur, mot_de_passe, nom_complet, role)
    Table vehicules (id, immatriculation, type, capacite, statut)
    Table chauffeurs (id, nom, prenom, telephone, numero_permis, categorie_permis, vehicule_id, disponibilite)
    Table lignes (id, code, nom, origine, destination, distance_km, duree_minutes)
    Table tarifs (id, ligne_id, type_client, prix)
    Table trajets (id, ligne_id, chauffeur_id, vehicule_id, date_heure_depart, date_heure_arrivee, statut, nb_passagers, recette)
    Table incidents (id, trajet_id, type, description, gravite, date_incident, resolu)
"""

prompt = f"""Tu es un expert Text-to-SQL MySQL.
    Schéma:
    {schema}
    
    Tâche: Traduis la demande utilisateur en requête SQL MySQL SELECT.
    Demande: "quel est le trajet le plus frequent?"
    
    Règles STRICTES:
    - Fais TOUJOURS des JOIN pour récupérer les noms (lignes.nom, chauffeurs.nom, vehicules.immatriculation).
    - Utilise des alias (ex: AS Ligne_Nom, AS Chauffeur_Nom).
    - Qu'un "trajet fréquent" veut dire la "ligne" la plus utilisée (GROUP BY ligne_id).
    - Renvoie UNIQUEMENT la SQL. Aucun texte avant ou après.
"""

r = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
    json={'model': 'llama-3.1-8b-instant', 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.0}
)
sql_query = r.json()['choices'][0]['message']['content'].strip()
sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
print('Raw SQL:', sql_query)

try:
    res = executer_requete(sql_query)
    print('DB Result:', res)
except Exception as e:
    print('SQL ERROR:', e)
