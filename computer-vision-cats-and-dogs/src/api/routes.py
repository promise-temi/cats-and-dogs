from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
from pathlib import Path
import time
import sqlite3
from datetime import datetime




# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .auth import verify_token
from src.models.predictor import CatDogPredictor
from src.monitoring.metrics import time_inference, log_inference_time

# Configuration des templates
TEMPLATES_DIR = ROOT_DIR / "src" / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# Initialisation du prédicteur
predictor = CatDogPredictor()

@router.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    """Page d'accueil avec interface web"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "model_loaded": predictor.is_loaded()
    })

@router.get("/info", response_class=HTMLResponse)
async def info_page(request: Request):
    """Page d'informations"""
    model_info = {
        "name": "Cats vs Dogs Classifier",
        "version": "1.0.0",
        "description": "Modèle CNN pour classification chats/chiens",
        "parameters": predictor.model.count_params() if predictor.is_loaded() else 0,
        "classes": ["Cat", "Dog"],
        "input_size": f"{predictor.image_size[0]}x{predictor.image_size[1]}",
        "model_loaded": predictor.is_loaded()
    }
    return templates.TemplateResponse("info.html", {
        "request": request, 
        "model_info": model_info
    })

@router.get("/inference", response_class=HTMLResponse)
async def inference_page(request: Request):
    """Page d'inférence"""
    return templates.TemplateResponse("inference.html", {
        "request": request,
        "model_loaded": predictor.is_loaded()
    })

@router.post("/api/predict")
@time_inference  # Décorateur de monitoring
async def predict_api(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    """API de prédiction avec monitoring"""
    if not predictor.is_loaded():
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Format d'image invalide")
    
    try:
        image_data = await file.read()
        result = predictor.predict(image_data)
        
        response_data = {
            "filename": file.filename,
            "prediction": result["prediction"],
            "confidence": f"{result['confidence']:.2%}",
            "probabilities": {
                "cat": f"{result['probabilities']['cat']:.2%}",
                "dog": f"{result['probabilities']['dog']:.2%}"
            }
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction: {str(e)}")

        # Logger les métriques
        log_inference_time(
            inference_time_ms=inference_time_ms,
            filename=file.filename,
            prediction=result["prediction"],
            confidence=f"{result['confidence']:.2%}",
            success=True
        )
        
        return response_data
        
    except Exception as e:
        # En cas d'erreur, logger quand même le temps
        end_time = time.perf_counter()
        inference_time_ms = (end_time - start_time) * 1000
        
        log_inference_time(
            inference_time_ms=inference_time_ms,
            filename=file.filename if file else "unknown",
            success=False
        )
        
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction: {str(e)}")

@router.get("/api/info")
async def api_info():
    """Informations API JSON"""
    return {
        "model_loaded": predictor.is_loaded(),
        "model_path": str(predictor.model_path),
        "version": "1.0.0",
        "parameters": predictor.model.count_params() if predictor.is_loaded() else 0
    }

@router.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "model_loaded": predictor.is_loaded()
    }




@router.get("/performance")
async def performance():
    conn = sqlite3.connect("src/api/database.db")
    cur = conn.cursor()

    # Nombre total de feedback
    cur.execute("SELECT COUNT(*) FROM Feedback")
    total_feedback = cur.fetchone()[0]

    # Nombre de feedback positifs (status = 'oui')
    cur.execute("SELECT COUNT(*) FROM Feedback WHERE status = 'OUI'")
    total_positifs = cur.fetchone()[0]

    # Nombre de feedback négatifs (status = 'non')
    cur.execute("SELECT COUNT(*) FROM Feedback WHERE status = 'NON'")
    total_negatifs = cur.fetchone()[0]

    # Nombre de prédictions chien (détail oui/non)
    cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Dog' AND status = 'OUI'")
    chien_positifs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Dog' AND status = 'NON'")
    chien_negatifs = cur.fetchone()[0]

    # Nombre de prédictions chat (détail oui/non)
    cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Cat' AND status = 'OUI'")
    chat_positifs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Feedback WHERE predicted_class = 'Cat' AND status = 'NON'")
    chat_negatifs = cur.fetchone()[0]

    conn.close()

    bad_feedback_pourcentage = (total_negatifs / total_feedback * 100) if total_feedback > 0 else 0

    feedback_message = "Ce modèle est plutôt bon"
    if bad_feedback_pourcentage >= 30:
        feedback_message = "Ce modèle est plutôt bon, mais laisse à désirer."
    if bad_feedback_pourcentage >= 50:
        feedback_message = "Ce modèle n'est pas performant, un nouvel entraînement est nécessaire."

    result_final =  {
        "total_feedback": total_feedback,
        "positifs": total_positifs,
        "negatifs": total_negatifs,
        "chien": {
            "positifs": chien_positifs,
            "negatifs": chien_negatifs
        },
        "chat": {
            "positifs": chat_positifs,
            "negatifs": chat_negatifs
        },
        "bad_feedback_pourcentage": bad_feedback_pourcentage,
        "message": feedback_message
    }

    html_content = f"""
    <html>
        <head>
            <title>Rapport Feedback</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                table {{
                    border-collapse: collapse;
                    width: 50%;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #aaa;
                    padding: 8px 12px;
                    text-align: center;
                }}
                th {{ background-color: #f0f0f0; }}
                .msg {{ margin-top: 20px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Rapport de performance</h1>
            <p>Total feedback : {total_feedback}</p>
            </br>
            <p>Rien à signaler : {total_feedback - (total_negatifs + total_positifs)}</p>
            <p>Positifs : {total_positifs} | Négatifs : {total_negatifs}</p>
            <p>Taux de feedback négatif : {bad_feedback_pourcentage:.2f}%</p>

            <h2>Détail par classe</h2>
            <table>
                <tr>
                    <th>Classe</th>
                    <th>Positifs</th>
                    <th>Négatifs</th>
                </tr>
                <tr>
                    <td>Chien (Dog)</td>
                    <td>{chien_positifs}</td>
                    <td>{chien_negatifs}</td>
                </tr>
                <tr>
                    <td>Chat (Cat)</td>
                    <td>{chat_positifs}</td>
                    <td>{chat_negatifs}</td>
                </tr>
            </table>

            <p class="msg">{feedback_message}</p>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content)







@router.post("/api/feedback")
async def feedback_api(request: Request, token: str = Depends(verify_token)):
    # Récupérer le JSON brut envoyé par le front
    data = await request.json()
    
    
    feedback = data.get("feedback")
    prediction = data.get("prediction")
    updated_id = data.get("updated_id")
    ts = datetime.now().isoformat(" ")

    # Connexion à la base existante
    conn = sqlite3.connect("src/api/database.db")
    cur = conn.cursor()
    
    # Cas 1 : Sauvegarde automatique du feedback utilisateur
    #   Création d’un nouveau feedback
    #   Cela signifie que l’utilisateur vient de lancer une nouvelle prédiction et que l’on sauvegarde automatiquement un feedback par défaut
    #   ("RAS" = rien à signaler).
    

    if updated_id == False:
        cur.execute("""
            INSERT INTO Feedback (timestamp, predicted_class, status)
            VALUES (?, ?, ?)
        """, (ts, prediction, feedback))

        conn.commit()
        new_id = cur.lastrowid  # Récupérer l’ID généré

        conn.close()
        # Réponse simple
        return {
            "status": "ok",
            "updated_id": new_id,
        }



    # Cas 2 : Mise à jour du feedback si donnée par le user 
    #   Le front utilise l’ID déjà reçu lors de la création pour mettre à jour ce feedback.
    #   Si l’utilisateur relance une prédiction ou recharge la page, updated_id repasse à False et on recrée.


    else : 
        cur.execute("""
            UPDATE Feedback
            SET predicted_class = ?, status = ?, timestamp = ?
            WHERE id = ?
        """, (prediction, feedback, ts, updated_id))

        conn.commit()
        conn.close()
        return {
            "status": "ok",
            "updated_id": updated_id,
        }
        

    