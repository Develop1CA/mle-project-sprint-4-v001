import pandas as pd
import pickle
import numpy as np
from typing import List, Tuple, Dict
import os
from scipy.sparse import load_npz, csr_matrix
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        except Exception as e:
            logger.warning(f"Could not load history: {e}")
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
            logger.error(f"Error saving history: {e}")
    
    def add_interaction(self, user_id: int, track_id: int):
        """Добавить прослушивание трека"""
        if user_id not in self.history:
            self.history[user_id] = []
        
        if track_id in self.history[user_id]:
            self.history[user_id].remove(track_id)
        self.history[user_id].append(track_id)
        self.save_history()
        logger.info(f"Added interaction: user={user_id}, track={track_id}")
    
    def get_recent_history(self, user_id: int, limit: int = 10) -> List[int]:
        """Получить последние прослушивания"""
        if user_id in self.history:
            return self.history[user_id][-limit:]
        return []
    
    def has_history(self, user_id: int) -> bool:
        """Проверить есть ли история у пользователя"""
        return user_id in self.history and len(self.history[user_id]) > 0

class RecommendationService:
    def __init__(self):
        self.als_model = None
        self.user_item_matrix = None
        self.items_df = None
        self.interactions_df = None
        self.user_history = UserHistory()
        
        # Маппинги между внешними ID и внутренними индексами
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.track_id_to_idx = {}
        self.idx_to_track_id = {}
        
        self.load_models_and_data()
        logger.info("✅ RecommendationService initialized")
    
    def _build_mappings(self):
        """Построение маппингов между ID и индексами матрицы (fallback)"""
        try:
            # Маппинг для пользователей из interactions
            if self.interactions_df is not None:
                user_col = None
                for col in ['user_id', 'userid', 'user']:
                    if col in self.interactions_df.columns:
                        user_col = col
                        break
                
                if user_col:
                    unique_users = sorted(self.interactions_df[user_col].unique())
                    self.user_id_to_idx = {user_id: idx for idx, user_id in enumerate(unique_users)}
                    self.idx_to_user_id = {idx: user_id for idx, user_id in enumerate(unique_users)}
                    logger.info(f"✅ User mappings built: {len(self.user_id_to_idx)} users")
            
            # Маппинг для треков из items
            if self.items_df is not None:
                track_col = None
                for col in ['track_id', 'item_id', 'trackid', 'itemid']:
                    if col in self.items_df.columns:
                        track_col = col
                        break
                
                if track_col:
                    unique_tracks = sorted(self.items_df[track_col].unique())
                    self.track_id_to_idx = {track_id: idx for idx, track_id in enumerate(unique_tracks)}
                    self.idx_to_track_id = {idx: track_id for idx, track_id in enumerate(unique_tracks)}
                    logger.info(f"✅ Track mappings built: {len(self.track_id_to_idx)} tracks")
            
        except Exception as e:
            logger.error(f"❌ Error building mappings: {e}")
    
    def load_models_and_data(self):
        """Загрузка моделей и данных из файлов проекта"""
        try:
            # Загрузка ALS модели - используем улучшенную версию
            if os.path.exists('als_model_improved.pkl'):
                with open('als_model_improved.pkl', 'rb') as f:
                    self.als_model = pickle.load(f)
                logger.info("✅ ALS model loaded from als_model_improved.pkl")
            elif os.path.exists('als_model.pkl'):
                with open('als_model.pkl', 'rb') as f:
                    self.als_model = pickle.load(f)
                logger.info("✅ ALS model loaded from als_model.pkl")
            else:
                logger.error("❌ No ALS model found")
            
            # Загрузка матрицы взаимодействий - используем улучшенную версию
            if os.path.exists('user_item_matrix_improved.npz'):
                self.user_item_matrix = load_npz('user_item_matrix_improved.npz')
                logger.info(f"✅ User-item matrix loaded: {self.user_item_matrix.shape}")
            elif os.path.exists('user_item_matrix.npz'):
                self.user_item_matrix = load_npz('user_item_matrix.npz')
                logger.info(f"✅ User-item matrix loaded: {self.user_item_matrix.shape}")
            else:
                logger.error("❌ No user-item matrix found")
            
            # Загрузка информации о треках
            if os.path.exists('items.parquet'):
                self.items_df = pd.read_parquet('items.parquet')
                logger.info(f"✅ Items data loaded: {self.items_df.shape}")
            else:
                logger.error("❌ No items data found")
            
            # Загрузка взаимодействий
            if os.path.exists('interactions.parquet'):
                self.interactions_df = pd.read_parquet('interactions.parquet')
                logger.info(f"✅ Interactions data loaded: {self.interactions_df.shape}")
            else:
                logger.error("❌ No interactions data found")
            
            # ЗАГРУЗКА МАППИНГОВ - КРИТИЧЕСКИ ВАЖНЫЙ БЛОК
            if os.path.exists('user_id_to_idx.json'):
                with open('user_id_to_idx.json', 'r') as f:
                    self.user_id_to_idx = {int(k): v for k, v in json.load(f).items()}
                self.idx_to_user_id = {v: k for k, v in self.user_id_to_idx.items()}
                logger.info(f"✅ User mappings loaded from file: {len(self.user_id_to_idx)} users")
            
            if os.path.exists('track_id_to_idx.json'):  
                with open('track_id_to_idx.json', 'r') as f:
                    self.track_id_to_idx = {int(k): v for k, v in json.load(f).items()}
                self.idx_to_track_id = {v: k for k, v in self.track_id_to_idx.items()}
                logger.info(f"✅ Track mappings loaded from file: {len(self.track_id_to_idx)} tracks")
            
            # Если маппинги не загружены из файлов, строим из данных (fallback)
            if not self.user_id_to_idx:
                logger.info("🔄 Building mappings from data (fallback)")
                self._build_mappings()
            
        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")
    
    def get_offline_recommendations(self, user_id: int, limit: int = 10) -> List[int]:
        """Получение офлайн рекомендаций с использованием ALS модели"""
        logger.info(f"🔍 Getting offline recs for user {user_id}")
        
        if self.als_model is None or self.user_item_matrix is None:
            logger.error("❌ No model or matrix available")
            return self.get_popular_tracks(limit)
        
        if user_id not in self.user_id_to_idx:
            logger.warning(f"❌ User {user_id} not in mappings")
            return self.get_popular_tracks(limit)
        
        try:
            # Конвертируем user_id во внутренний индекс
            user_idx = self.user_id_to_idx[user_id]
            user_items = self.user_item_matrix[user_idx]
            
            # Получаем рекомендации от ALS модели
            recommendations_data = self.als_model.recommend(
                user_idx, 
                user_items, 
                N=limit * 2,
                filter_already_liked_items=True
            )
            
            # Конвертируем обратно в track_id
            recommendations = []
            for item_idx, score in zip(recommendations_data[0], recommendations_data[1]):
                if item_idx in self.idx_to_track_id:
                    track_id = int(self.idx_to_track_id[item_idx])
                    recommendations.append(track_id)
            
            logger.info(f"✅ ALS returned {len(recommendations)} recommendations")
            
            if not recommendations:
                logger.warning("⚠️ ALS returned empty list")
                return self.get_popular_tracks(limit)
                
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting ALS recommendations: {e}")
            return self.get_popular_tracks(limit)
    
    def get_online_recommendations(self, user_id: int, limit: int = 10) -> List[int]:
        """Получение онлайн рекомендаций на основе недавней истории"""
        recent_history = self.user_history.get_recent_history(user_id, limit=10)
        logger.info(f"🔍 Online recs for user {user_id}, history: {len(recent_history)} items")
        
        if not recent_history:
            return []
        
        # На основе прослушанных треков находим похожие
        similar_tracks = []
        for track_id in recent_history[-3:]:  # Берем только 3 последних
            similar = self.get_similar_tracks(track_id, 2)
            similar_tracks.extend(similar)
        
        # Убираем дубликаты и уже прослушанные
        recommendations = []
        for track_id in similar_tracks:
            if track_id not in recent_history and track_id not in recommendations:
                recommendations.append(track_id)
        
        logger.info(f"✅ Online recommendations: {len(recommendations)} items")
        return recommendations[:limit]
    
    def get_similar_tracks(self, track_id: int, count: int = 3) -> List[int]:
        """Получение похожих треков на основе коллаборативной фильтрации"""
        if track_id not in self.track_id_to_idx:
            logger.warning(f"❌ Track {track_id} not in mappings")
            return []
        
        try:
            # Конвертируем track_id во внутренний индекс
            track_idx = self.track_id_to_idx[track_id]
            
            # Используем похожесть из ALS модели
            similar_items = self.als_model.similar_items(track_idx, N=count)
            similar_tracks = []
            
            for similar_idx, score in zip(similar_items[0], similar_items[1]):
                if similar_idx in self.idx_to_track_id:
                    similar_tracks.append(int(self.idx_to_track_id[similar_idx]))
            
            return similar_tracks
            
        except Exception as e:
            logger.error(f"❌ Error getting similar tracks: {e}")
            return []
    
    def get_popular_tracks(self, limit: int = 10) -> List[int]:
        """Получение популярных треков с детекцией колонки"""
        try:
            if self.interactions_df is not None:
                # Пробуем разные возможные названия колонки
                for col_name in ['track_id', 'item_id', 'trackid', 'itemid']:
                    if col_name in self.interactions_df.columns:
                        popular_tracks = self.interactions_df[col_name].value_counts().head(limit)
                        result = [int(x) for x in popular_tracks.index.tolist()]
                        logger.info(f"✅ Popular tracks from '{col_name}': {len(result)} items")
                        return result
            
            # Fallback: если не нашли колонку, используем первые N треков из маппинга
            if self.idx_to_track_id:
                result = [self.idx_to_track_id[i] for i in range(min(limit, len(self.idx_to_track_id)))]
                logger.info(f"✅ Popular tracks fallback: {len(result)} items")
                return result
                
            logger.error("❌ No data available for popular tracks")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error in get_popular_tracks: {e}")
            return []
    
    def blend_recommendations(self, offline_recs: List[int], 
                            online_recs: List[int], 
                            limit: int = 10) -> List[int]:
        """Смешивание онлайн и офлайн рекомендаций"""
        logger.info(f"🔄 Blending: {len(offline_recs)} offline, {len(online_recs)} online")
        
        # Если нет онлайн рекомендаций, возвращаем офлайн
        if not online_recs:
            return offline_recs[:limit]
        
        # Стратегия смешивания: 60% онлайн, 30% офлайн, 10% популярные
        online_count = min(len(online_recs), int(limit * 0.6))
        offline_count = min(len(offline_recs), int(limit * 0.3))
        popular_count = limit - online_count - offline_count
        
        blended = []
        
        # Добавляем онлайн рекомендации
        blended.extend(online_recs[:online_count])
        
        # Добавляем офлайн рекомендации (исключая дубликаты)
        for track_id in offline_recs:
            if track_id not in blended and len(blended) < online_count + offline_count:
                blended.append(track_id)
        
        # Добавляем популярные треки если нужно
        if popular_count > 0:
            popular_tracks = self.get_popular_tracks(popular_count * 2)
            for track_id in popular_tracks:
                if track_id not in blended and len(blended) < limit:
                    blended.append(track_id)
        
        logger.info(f"✅ Blended recommendations: {len(blended)} items")
        return blended[:limit]
    
    def get_recommendations(self, user_id: int, limit: int = 10) -> Tuple[List[int], str, bool]:
        """Основной метод получения рекомендаций"""
        logger.info(f"🎯 Getting recommendations for user {user_id}")
        
        # Проверяем является ли пользователь новым (нет в офлайн данных)
        is_new_user = user_id not in self.user_id_to_idx
        logger.info(f"👤 User type: {'NEW' if is_new_user else 'EXISTING'}")
        
        # Проверяем есть ли онлайн история
        has_online_history = self.user_history.has_history(user_id)
        logger.info(f"📱 Online history: {has_online_history}")
        
        # Для нового пользователя без истории используем только популярные треки
        if is_new_user and not has_online_history:
            logger.info("🎯 Using popular tracks for new user")
            popular_tracks = self.get_popular_tracks(limit)
            return popular_tracks, "popular", False
        
        # Получаем офлайн рекомендации
        offline_recommendations = self.get_offline_recommendations(user_id, limit)
        logger.info(f"📊 Offline: {len(offline_recommendations)} items")
        
        if has_online_history:
            # Получаем онлайн рекомендации
            online_recommendations = self.get_online_recommendations(user_id, limit)
            logger.info(f"📊 Online: {len(online_recommendations)} items")
            
            if online_recommendations:
                # Смешиваем рекомендации
                blended_recommendations = self.blend_recommendations(
                    offline_recommendations, online_recommendations, limit
                )
                logger.info(f"🎉 Final blended: {len(blended_recommendations)} items")
                return blended_recommendations, "blended", True
            else:
                # Есть история, но не получилось сгенерировать онлайн рекомендации
                logger.info("🎯 Using offline fallback (has history)")
                return offline_recommendations, "offline_fallback", True
        else:
            # Нет онлайн истории - используем только офлайн
            logger.info("🎯 Using offline only (no history)")
            return offline_recommendations, "offline", False
    
    def get_user_history(self, user_id: int) -> List[int]:
        """Получить историю прослушиваний пользователя"""
        return self.user_history.get_recent_history(user_id, limit=20)
    
    def add_interaction(self, user_id: int, track_id: int):
        """Добавить прослушивание трека"""
        self.user_history.add_interaction(user_id, track_id)