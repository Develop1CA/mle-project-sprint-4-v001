import json
import os
from typing import List, Dict

class UserHistory:
    def __init__(self, history_file: str = "data/online_history.json"):
        self.history_file = history_file
        self.history = self.load_history()
    
    def load_history(self) -> Dict[int, List[int]]:
        """Загрузка истории из файла с конвертацией ключей в int"""
        try:
            with open(self.history_file, 'r') as f:
                raw_data = json.load(f)
                # Конвертируем строковые ключи в int
                return {int(k): v for k, v in raw_data.items()}
        except:
            return {}
    
    def save_history(self):
        """Сохранение истории в файл с конвертацией ключей в str"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            # Конвертируем int ключи в str для JSON
            str_data = {str(k): v for k, v in self.history.items()}
            with open(self.history_file, 'w') as f:
                json.dump(str_data, f)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_interaction(self, user_id: int, track_id: int):
        """Добавить прослушивание трека"""
        if user_id not in self.history:
            self.history[user_id] = []
        
        if track_id in self.history[user_id]:
            self.history[user_id].remove(track_id)
        self.history[user_id].append(track_id)
        self.save_history()
    
    def get_recent_history(self, user_id: int, limit: int = 10) -> List[int]:
        """Получить последние прослушивания"""
        if user_id in self.history:
            return self.history[user_id][-limit:]
        return []
    
    def has_history(self, user_id: int) -> bool:
        """Проверить есть ли история у пользователя"""
        return user_id in self.history and len(self.history[user_id]) > 0