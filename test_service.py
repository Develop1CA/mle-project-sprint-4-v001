import requests
import time
import logging
import pandas as pd
import json
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ServiceTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_users = self.load_test_users()
    
    def load_test_users(self):
        """Загрузка тестовых пользователей с fallback'ами"""
        try:
            # Пытаемся загрузить из interactions
            interactions_df = pd.read_parquet('interactions.parquet')
            
            # Детекция колонки user_id
            user_col = None
            for col in ['user_id', 'userid', 'user']:
                if col in interactions_df.columns:
                    user_col = col
                    break
                    
            if user_col:
                users = interactions_df[user_col].unique().tolist()
                offline_user = users[0] if users else 1
                online_user = users[5] if len(users) > 5 else offline_user
            else:
                offline_user = 1
                online_user = 2
                
        except Exception as e:
            logger.warning(f"Could not load from interactions: {e}")
            # Fallback: пробуем взять из online_history.json
            try:
                with open('data/online_history.json') as f:
                    oh = json.load(f)
                    keys = [int(k) for k in oh.keys()]
                    if keys:
                        offline_user = keys[0]
                        online_user = keys[0] if len(keys) == 1 else keys[1]
                    else:
                        offline_user = 1
                        online_user = 2
            except Exception as e2:
                logger.warning(f"Could not load from online_history: {e2}")
                offline_user = 1
                online_user = 2
        
        return {
            'no_history': 999999,
            'offline_only': int(offline_user), 
            'with_history': int(online_user)
        }
    
    def test_health(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Health check passed")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def test_offline_recommendations(self) -> bool:
        """Тест офлайн рекомендаций (пользователь без онлайн истории)"""
        try:
            user_id = self.test_users['offline_only']
            response = requests.post(
                f"{self.base_url}/api/recommendations",
                json={"user_id": user_id, "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Offline recommendations test passed: {len(data['recommendations'])} recommendations")
                return (len(data['recommendations']) > 0)
            else:
                logger.error(f"❌ Offline recommendations test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Offline recommendations test error: {e}")
            return False
    
    def test_blended_recommendations(self) -> bool:
        """Тест смешанных рекомендаций (пользователь с онлайн историей)"""
        try:
            user_id = self.test_users['with_history']
            
            # Сначала добавляем онлайн взаимодействие
            track_id = 123  # Тестовый трек
            response = requests.post(
                f"{self.base_url}/api/interaction",
                json={"user_id": user_id, "track_id": track_id},
                timeout=10
            )
            
            time.sleep(1)  # Даем время на обработку
            
            # Затем получаем рекомендации
            response = requests.post(
                f"{self.base_url}/api/recommendations", 
                json={"user_id": user_id, "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Blended recommendations test passed: {len(data['recommendations'])} recommendations")
                return (len(data['recommendations']) > 0)
            else:
                logger.error(f"❌ Blended recommendations test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Blended recommendations test error: {e}")
            return False
    
    def test_new_user(self) -> bool:
        """Тест нового пользователя (без данных в матрице)"""
        try:
            user_id = self.test_users['no_history']
            response = requests.post(
                f"{self.base_url}/api/recommendations",
                json={"user_id": user_id, "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ New user test passed: {len(data['recommendations'])} recommendations")
                # Новый пользователь должен получить рекомендации (хотя бы популярные)
                return len(data['recommendations']) > 0
            else:
                logger.error(f"❌ New user test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ New user test error: {e}")
            return False
    
    def test_user_history(self) -> bool:
        """Тест получения истории пользователя"""
        try:
            user_id = self.test_users['with_history']
            response = requests.get(
                f"{self.base_url}/api/user/{user_id}/history",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ User history test passed: {len(data)} items")
                return True
            else:
                logger.error(f"❌ User history test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ User history test error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Запуск всех тестов"""
        logger.info("🚀 Starting comprehensive music recommendation service tests...")
        logger.info(f"📊 Test users: {self.test_users}")
        
        # Даем сервису время на запуск
        time.sleep(10)
        
        tests = {
            "service_health": self.test_health(),
            "offline_recommendations": self.test_offline_recommendations(),
            "blended_recommendations": self.test_blended_recommendations(),
            "new_user_recommendations": self.test_new_user(),
            "user_history": self.test_user_history()
        }
        
        passed = sum(tests.values())
        total = len(tests)
        
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        for test_name, result in tests.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"  {test_name}: {status}")
        
        return tests

if __name__ == "__main__":
    tester = ServiceTester()
    results = tester.run_all_tests()
    
    # Сохраняем детальные результаты
    with open('test_service.log', 'w') as f:
        f.write("MUSIC RECOMMENDATION SERVICE - PART 2 TEST RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Test execution time: {time.ctime()}\n")
        f.write("=" * 60 + "\n")
        
        for test_name, result in results.items():
            status = "PASSED" if result else "FAILED"
            f.write(f"{test_name:30} {status}\n")
        
        f.write("=" * 60 + "\n")
        passed = sum(results.values())
        total = len(results)
        f.write(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)\n")