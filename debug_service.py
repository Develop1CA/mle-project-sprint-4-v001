import requests
import json

def debug_service():
    base_url = "http://localhost:8000"
    
    print("🐛 ДИАГНОСТИКА СЕРВИСА")
    print("=" * 50)
    
    # 1. Проверим здоровье
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return
    
    # 2. Проверим конкретного пользователя
    test_users = [1, 999999, 5]  # разные сценарии
    
    for user_id in test_users:
        print(f"\n--- Тестируем user_id={user_id} ---")
        
        # Сначала добавим взаимодействие
        try:
            response = requests.post(
                f"{base_url}/api/interaction",
                json={"user_id": user_id, "track_id": 100},
                timeout=5
            )
            print(f"✅ Interaction added: {response.status_code}")
        except Exception as e:
            print(f"❌ Interaction failed: {e}")
        
        # Проверим историю
        try:
            response = requests.get(f"{base_url}/api/user/{user_id}/history", timeout=5)
            history = response.json()
            print(f"📋 History: {len(history)} items - {history}")
        except Exception as e:
            print(f"❌ History failed: {e}")
        
        # Получим рекомендации
        try:
            response = requests.post(
                f"{base_url}/api/recommendations",
                json={"user_id": user_id, "limit": 5},
                timeout=5
            )
            data = response.json()
            print(f"🎵 Recommendations: {len(data['recommendations'])} items")
            print(f"   Type: {data['recommendation_type']}")
            print(f"   Online used: {data['online_history_used']}")
            print(f"   Items: {data['recommendations']}")
        except Exception as e:
            print(f"❌ Recommendations failed: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    debug_service()