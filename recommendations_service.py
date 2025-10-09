"""
Music Recommendation Service
FastAPI-сервис для выдачи рекомендаций
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from app.service import RecommendationService

# Создаем FastAPI приложение
app = FastAPI(title="Music Recommendation Service")

# Инициализируем сервис рекомендаций
service = RecommendationService()

# Pydantic-модели для запросов
class RecommendationRequest(BaseModel):
    user_id: int
    limit: int = 10

class InteractionRequest(BaseModel):
    user_id: int
    track_id: int

# Эндпоинт здоровья сервиса
@app.get("/health")
def health():
    return {"status": "healthy"}

# Корневой эндпоинт
@app.get("/")
def root():
    return {"message": "Music Recommendation Service is running!"}

# Получение рекомендаций
@app.post("/api/recommendations")
def recommendations(request: RecommendationRequest):
    try:
        recs, rec_type, online_used = service.get_recommendations(
            user_id=request.user_id,
            limit=request.limit
        )
        # Возвращаем словарь с ключами, как ожидают тесты
        return {
            "recommendations": recs,
            "recommendation_type": rec_type,
            "online_history_used": online_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Добавление взаимодействия пользователя
@app.post("/api/interaction")
def add_interaction(request: InteractionRequest):
    try:
        service.add_interaction(user_id=request.user_id, track_id=request.track_id)
        return {"status": "interaction added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Получение истории пользователя
@app.get("/api/user/{user_id}/history")
def user_history(user_id: int):
    try:
        history = service.get_user_history(user_id=user_id)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
