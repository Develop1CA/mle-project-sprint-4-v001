import requests

def быстрая_проверка():
    base_url = "http://localhost:8000"
    
    print("🚀 БЫСТРАЯ ПРОВЕРКА МИКРОСЕРВИСА")
    print("=" * 40)
    
    # 1. Проверка здоровья
    try:
        ответ = requests.get(f"{base_url}/health", timeout=3)
        if ответ.status_code == 200:
            print("✅ Сервис запущен и работает")
        else:
            print("❌ Сервис не отвечает")
            return
    except:
        print("❌ Сервис не запущен. Запустите: python -m app.main")
        return
    
    # 2. Проверка рекомендаций
    try:
        ответ = requests.post(
            f"{base_url}/api/recommendations",
            json={"user_id": 1, "limit": 3},
            timeout=5
        )
        данные = ответ.json()
        print(f"✅ Рекомендации работают")
        print(f"   Получено {len(данные['recommendations'])} рекомендаций")
        print(f"   Тип: {данные['recommendation_type']}")
        print(f"   Онлайн история: {данные['online_history_used']}")
    except Exception as e:
        print(f"❌ Ошибка получения рекомендаций: {e}")
    
    # 3. Проверка добавления взаимодействия
    try:
        ответ = requests.post(
            f"{base_url}/api/interaction", 
            json={"user_id": 1, "track_id": 999},
            timeout=5
        )
        if ответ.status_code == 200:
            print("✅ Добавление взаимодействия работает")
        else:
            print("❌ Ошибка добавления взаимодействия")
    except Exception as e:
        print(f"❌ Ошибка добавления взаимодействия: {e}")
    
    print("=" * 40)
    print("🎯 Микросервис готов к тестированию!")
    print("   Запустите полные тесты: python test_service.py")

if __name__ == "__main__":
    быстрая_проверка()
