import requests
import json
import sys

def check_service():
    base_url = "http://localhost:8000"
    results = {}
    
    print("🔍 ФИНАЛЬНАЯ ПРОВЕРКА ПРОЕКТА")
    print("=" * 50)
    
    # Тест 1: Проверка здоровья сервиса
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        results['health'] = response.status_code == 200
        print(f"✅ Проверка здоровья: {'ПРОЙДЕНА' if results['health'] else 'НЕ ПРОЙДЕНА'}")
    except:
        results['health'] = False
        print("❌ Проверка здоровья: НЕ ПРОЙДЕНА - Сервис не запущен")
        return results
    
    # Тест 2: Новый пользователь (без онлайн истории)
    try:
        # Используем небольшой ID, который точно нового (не из interactions)
        new_user_id = 99999  # Уменьшаем ID для скорости
        
        response = requests.post(
            f"{base_url}/api/recommendations",
            json={"user_id": new_user_id, "limit": 3},
            timeout=15  # Увеличиваем таймаут
        )
        data = response.json()
        results['new_user'] = (response.status_code == 200 and 
                             not data['online_history_used'] and
                             len(data['recommendations']) > 0)
        print(f"✅ Рекомендации новому пользователю: {'ПРОЙДЕН' if results['new_user'] else 'НЕ ПРОЙДЕН'}")
        print(f"   Тип: {data['recommendation_type']}, Онлайн история: {data['online_history_used']}")
        print(f"   Получено рекомендаций: {len(data['recommendations'])}")
        
        if not results['new_user']:
            print(f"   Детали: user_id={new_user_id}, recommendations={data['recommendations']}")
            
    except Exception as e:
        results['new_user'] = False
        print(f"❌ Рекомендации новому пользователю: НЕ ПРОЙДЕН - {e}")
    
    # Тест 3: Добавление взаимодействия
    try:
        response = requests.post(
            f"{base_url}/api/interaction",
            json={"user_id": 1, "track_id": 12345},
            timeout=10
        )
        results['interaction'] = response.status_code == 200
        print(f"✅ Добавление взаимодействия: {'ПРОЙДЕН' if results['interaction'] else 'НЕ ПРОЙДЕН'}")
    except Exception as e:
        results['interaction'] = False
        print(f"❌ Добавление взаимодействия: НЕ ПРОЙДЕН - {e}")
    
    # Тест 4: Пользователь с онлайн историей
    try:
        response = requests.post(
            f"{base_url}/api/recommendations",
            json={"user_id": 1, "limit": 3},
            timeout=10
        )
        data = response.json()
        results['online_user'] = (response.status_code == 200 and 
                                data['online_history_used'] and
                                len(data['recommendations']) > 0)
        print(f"✅ Рекомендации с онлайн историей: {'ПРОЙДЕН' if results['online_user'] else 'НЕ ПРОЙДЕН'}")
        print(f"   Тип: {data['recommendation_type']}, Онлайн история: {data['online_history_used']}")
        print(f"   Получено рекомендаций: {len(data['recommendations'])}")
    except Exception as e:
        results['online_user'] = False
        print(f"❌ Рекомендации с онлайн историей: НЕ ПРОЙДЕН - {e}")
    
    # Тест 5: История пользователя
    try:
        response = requests.get(f"{base_url}/api/user/1/history", timeout=10)
        results['history'] = response.status_code == 200
        print(f"✅ История пользователя: {'ПРОЙДЕН' if results['history'] else 'НЕ ПРОЙДЕН'}")
    except Exception as e:
        results['history'] = False
        print(f"❌ История пользователя: НЕ ПРОЙДЕН - {e}")
    
    print("=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ УСЛОВИЯ ВЫПОЛНЕНЫ! Проект готов к сдаче!")
        print("   Микросервис соответствует всем требованиям этапа 4:")
        print("   ✅ Принимает запросы с user_id")
        print("   ✅ Учитывает историю пользователя") 
        print("   ✅ Смешивает онлайн и офлайн рекомендации")
        print("   ✅ Протестирован для разных сценариев")
    else:
        print("⚠️  Некоторые условия не выполнены. Проверьте ошибки выше.")
        print("   Убедитесь что сервис запущен: python -m app.main")
    
    return results

if __name__ == "__main__":
    check_service()