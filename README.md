markdown
# Music Recommendation Service

Микросервис для выдачи персонализированных музыкальных рекомендаций с использованием ALS-модели и онлайн-истории пользователей.

## Архитектура решения

Сервис сочетает несколько стратегий рекомендаций:
- **Офлайн-рекомендации** - на основе ALS-модели, обученной на исторических данных
- **Онлайн-рекомендации** - на основе последних прослушиваний пользователя  
- **Популярные треки** - fallback-стратегия для новых пользователей

## Стратегия смешивания рекомендаций

### Алгоритм смешивания:
1. **Для пользователей с онлайн-историей** (60% онлайн + 30% офлайн + 10% популярные):
   - 60%: рекомендации на основе последних прослушанных треков
   - 30%: персональные рекомендации от ALS-модели
   - 10%: популярные треки из системы

2. **Для пользователей без онлайн-истории**:
   - 100% офлайн-рекомендации от ALS-модели

3. **Для новых пользователей** (нет в обучающих данных):
   - 100% популярные треки

### Приоритеты:
- Онлайн-история имеет высший приоритет
- Исключаются дубликаты и уже прослушанные треки
- Гарантируется выдача запрошенного количества рекомендаций

## Подготовка окружения

### Склонируйте репозиторий
```bash
git clone https://github.com/Develop1CA/mle-project-sprint-4-v001.git
или git clone git@github.com:Develop1CA/mle-project-sprint-4-v001.git
cd mle-project-sprint-4-v001
Активируйте виртуальное окружение
Используйте виртуальное окружение, созданное для работы с уроками. Если его не существует, создайте новое:

bash
python3 -m venv env_recsys_start
source env_recsys_start/bin/activate  # для Linux/Mac
Установите зависимости
bash
pip install -r requirements.txt
Подготовка данных

Для начала работы понадобится три файла с данными:
- [tracks.parquet](https://storage.yandexcloud.net/mle-data/ym/tracks.parquet)
- [catalog_names.parquet](https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet)
- [interactions.parquet](https://storage.yandexcloud.net/mle-data/ym/interactions.parquet)
 
Скачайте их в директорию локального репозитория. Для удобства вы можете воспользоваться командой wget:

```
wget https://storage.yandexcloud.net/mle-data/ym/tracks.parquet

wget https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet

wget https://storage.yandexcloud.net/mle-data/ym/interactions.parquet
```

Обученную модель и матрицу взаимодействий можно скачать по ссылке и поместить в корень проекта:
- [Модель и матрица, encoders.pkl](https://disk.yandex.ru/d/huLR2TyGUwmf7w)


Убедитесь, что в директории проекта присутствуют необходимые файлы:

*.pkl - обученные модели (ALS модель)

*.npz - матрицы взаимодействий

*.parquet - данные о треках и взаимодействиях

data/online_history.json - файл для хранения онлайн-истории

Запуск сервиса рекомендаций
Основной запуск
bash
# Запуск сервиса
python -m app.main

# Сервис будет доступен по http://localhost:8000
Альтернативный запуск
bash
# Или используйте прямое выполнение
python app/main.py
Тестирование сервиса
Полное тестирование (обязательно для проверки)
bash
# Запустите полный набор тестов
python test_service.py

# Результаты автоматически сохранятся в test_service.log
Быстрая проверка работоспособности
bash
python quick_check_ru.py
Дополнительные проверки
bash
# Диагностика сервиса
python debug_service.py

# Финальная проверка всех требований
python final_check_ru.py
Проверка API вручную
1. Проверка здоровья сервиса
bash
curl http://localhost:8000/health
2. Получение рекомендаций
bash
curl -X POST "http://localhost:8000/api/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "limit": 5}'
3. Добавление взаимодействия
bash
curl -X POST "http://localhost:8000/api/interaction" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 12345}'
4. Получение истории пользователя
bash
curl http://localhost:8000/api/user/1/history
Документация API
После запуска сервиса документация доступна по адресам:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Структура проекта
text
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── service.py           # Логика рекомендаций
│   └── models.py            # Модели данных
├── data/
│   └── online_history.json  # Онлайн-история пользователей
├── *.pkl, *.npz, *.parquet  # Модели и данные
├── test_service.py          # Основные тесты (обязателен)
├── quick_check_ru.py        # Быстрая проверка
├── debug_service.py         # Диагностика
├── final_check_ru.py        # Финальная проверка
├── create_mappings.py       # Создание маппингов
└── requirements.txt         # Зависимости
Особенности реализации
Отказоустойчивость: Fallback на популярные треки при ошибках

Гибкая стратегия: Адаптивные рекомендации под разные типы пользователей

Логирование: Детальное логирование всех операций

Кэширование: Сохранение онлайн-истории в JSON-файле