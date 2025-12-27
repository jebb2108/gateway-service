from typing import Union, Optional

from pydantic import BaseModel, Field


class Word(BaseModel):
    user_id: int = Field(..., description="Уникальный идентификатор пользователя")
    word: Union[str, None] = Field(None, description="Слово, которое нужно добавить в словарь")
    part_of_speech: Union[str, None] = Field(None, description="Часть речи слова")
    translation: Union[str, None] = Field(None, description="Перевод слова")
    is_public: bool = Field(False, description="Видно ли слово остальным пользователям")
    context: Optional[str] = Field(None, description="Контекст к слову")
    audio: Optional[bytes] = Field(None, description="bytes of audio recording")

    source: Optional[str] = Field(
        default="api", description="Источник запроса (api, tg-bot-service, etc)"
    )