from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from app.service import RecommendationService

app = FastAPI(
    title="Music Recommendation Service",
    description="Микросервис для рекомендаций треков",
    version="1.0.0"
)

# Инициализация сервиса
service = RecommendationService()

class RecommendationRequest(BaseModel):
    user_id: int
    limit: Optional[int] = 10

class InteractionRequest(BaseModel):
    user_id: int
    track_id: int

class RecommendationResponse(BaseModel):
    recommendations: List[int]
    recommendation_type: str
    online_history_used: bool

@app.get("/")
async def root():
    return {"message": "Music Recommendation Service is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Получить рекомендации для пользователя"""
    try:
        recommendations, rec_type, online_used = service.get_recommendations(
            request.user_id, request.limit
        )
        return RecommendationResponse(
            recommendations=recommendations,
            recommendation_type=rec_type,
            online_history_used=online_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interaction")
async def add_interaction(request: InteractionRequest):
    """Добавить взаимодействие пользователя с треком"""
    try:
        service.add_interaction(request.user_id, request.track_id)
        return {"status": "interaction added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/history")
async def get_user_history(user_id: int):
    """Получить историю пользователя"""
    try:
        history = service.get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)