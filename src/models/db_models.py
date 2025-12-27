from datetime import datetime, timedelta, date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.config import config


class Language(str, Enum):
    """
    Поддерживаемые языки
    """
    RU = "ru"
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"


class Topic(str, Enum):
    """
    Темы для общения
    """
    GENERAL = "general"
    MUSIC = "music"
    MOVIES = "movies"
    SPORTS = "sports"
    TECHNOLOGY = "technology"
    TRAVEL = "travel"
    GAMES = "games"


class User(BaseModel):
    """
    Модель нового пользователя (для базы данных).
    """
    user_id: int
    username: Optional[str]
    camefrom: str
    first_name: str
    language: str
    fluency: int
    topics: List[str]
    lang_code: str

class Profile(BaseModel):
    """
    Модель профиля пользователя (для базы данных)
    """
    user_id: int = Field(..., description="User ID")
    nickname: str = Field(..., description="Уникальный никнейм пользователя")
    email: str = Field(..., description="Email пользователя")
    gender: str = Field(..., description="Пол пользователя")
    intro: str = Field(..., description="Краткая информация о пользователе")
    birthday: str = Field(..., description="Дата рождения пользователя")
    dating: Optional[bool] = Field(False, description="Согласие на дэйтинг")
    status: Optional[str] = Field('rookie', description="Видимый статус пользователя")


class Payment(BaseModel):
    """
    Модель платежа (для базы данных).
    """

    user_id: int = Field(..., description="User ID")
    amount: Optional[float] = Field(
        199.00, description="Amount of payment in rubles user agreed to pay"
    )
    period: Optional[str] = Field(
        "trial", description="Period of payment", examples=["month", "year"]
    )
    trial: Optional[bool] = Field(True, description="If it is trial period for user")
    is_active: Optional[bool] = Field(True, description='If this subscription is still active')
    until: Optional[datetime] = Field(
        default=datetime.now(tz=config.tz_info) + timedelta(days=3), description="Trial period"
    )

    currency: Optional[str] = Field("RUB", description="Currency of payment")
    payment_id: Optional[str] = Field(None, description="Payment ID")


    @property
    def until_naive(self) -> Optional[datetime]:
        """ Возвращает until как naive datetime для хранения в БД """
        if self.until:
            date_obj = datetime.fromisoformat(self.until) # noqa
            return date_obj.replace(tzinfo=None)
        return None

    @property
    def created_at(self) -> datetime:
        """ Возвращает текущий timestamp для истории транзакций БД """
        return datetime.now(tz=config.tz_info)
