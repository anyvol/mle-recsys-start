import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import pandas as pd

logger = logging.getLogger("uvicorn.error")

# Класс для работы с рекомендациями
class Recommendations:
    def __init__(self):
        self._recs = {"personal": None, "default": None}
        self._stats = {
            "request_personal_count": 0,
            "request_default_count": 0,
        }

    def load(self, type, path, **kwargs):
        """Загружает рекомендации из файла"""
        logger.info(f"Loading {type} recommendations from {path}")
        self._recs[type] = pd.read_parquet(path, **kwargs)
        if type == "personal":
            self._recs[type] = self._recs[type].set_index("user_id")
        logger.info(f"{type.capitalize()} recommendations loaded")

    def get(self, user_id: int, k: int = 100):
        """Возвращает рекомендации для пользователя"""
        try:
            recs = self._recs["personal"].loc[user_id]
            recs = recs["item_id"].to_list()[:k]
            self._stats["request_personal_count"] += 1
        except KeyError:
            recs = self._recs["default"]["item_id"].to_list()[:k]
            self._stats["request_default_count"] += 1
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            recs = []
        return recs

    def stats(self):
        """Логирует статистику использования"""
        logger.info("Recommendation service statistics:")
        for name, value in self._stats.items():
            logger.info(f"{name}: {value}")

# Инициализация хранилища
rec_store = Recommendations()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загрузка данных при старте
    rec_store.load(
        "personal",
        "final_recommendations_feat.parquet",
        columns=["user_id", "item_id", "rank"]
    )
    rec_store.load(
        "default",
        "top_recs.parquet",
        columns=["item_id", "rank"]
    )
    yield
    # Логирование статистики при остановке
    rec_store.stats()

app = FastAPI(title="Book Recommendations API", lifespan=lifespan)

@app.post("/recommendations")
async def recommendations(user_id: int, k: int = 100):
    """
    Возвращает список рекомендаций длиной k для пользователя user_id
    """
    recs = rec_store.get(user_id, k)
    return {"recs": recs}