"""
Скрипт для создания маппингов ID ↔ индексы
Запускать после обучения моделей
"""
import json
import pandas as pd
import pickle
from typing import Dict

def create_mappings():
    """Создание маппингов из обучающих данных"""
    
    try:
        # Загрузка данных
        interactions_df = pd.read_parquet('interactions.parquet')
        items_df = pd.read_parquet('items.parquet')
        
        # Детекция колонок
        user_col = None
        for col in ['user_id', 'userid', 'user']:
            if col in interactions_df.columns:
                user_col = col
                break
        
        track_col = None  
        for col in ['track_id', 'item_id', 'trackid', 'itemid']:
            if col in items_df.columns:
                track_col = col
                break
        
        if not user_col:
            raise ValueError("User column not found in interactions")
        if not track_col:
            raise ValueError("Track column not found in items")
        
        # Маппинг пользователей
        unique_users = sorted(interactions_df[user_col].unique())
        user_id_to_idx = {int(user_id): idx for idx, user_id in enumerate(unique_users)}
        
        # Маппинг треков  
        unique_tracks = sorted(items_df[track_col].unique())
        track_id_to_idx = {int(track_id): idx for idx, track_id in enumerate(unique_tracks)}
        
        # Сохранение маппингов
        with open('user_id_to_idx.json', 'w') as f:
            json.dump(user_id_to_idx, f, indent=2)
        
        with open('track_id_to_idx.json', 'w') as f:
            json.dump(track_id_to_idx, f, indent=2)
        
        print(f"✅ Created mappings:")
        print(f"   - Users: {len(user_id_to_idx)}")
        print(f"   - Tracks: {len(track_id_to_idx)}")
        print(f"   - Files saved: user_id_to_idx.json, track_id_to_idx.json")
        
    except Exception as e:
        print(f"❌ Error creating mappings: {e}")
        raise

if __name__ == "__main__":
    create_mappings()