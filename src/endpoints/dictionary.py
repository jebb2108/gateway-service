import logging
from json import loads, dumps
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Query
from redis.asyncio import Redis as aioredis

from src.config import config
from src.models import Word

logger = logging.getLogger('gateway')

redis = aioredis.from_url("redis://redis")

router = APIRouter(prefix='/api')


DATABASE_BASE_URL = f"http://{config.database.host}:{config.database.port}"

@router.get('/words')
async def get_words_handler(
        user_id: int = Query(..., description="User ID")
):
    """ Перенаправляет запрос на получение слова пользователя """
    try:
        cached = await redis.hgetall(f'words:{user_id}')
        if cached:
            return { key: loads(val) for key, val in cached.items() }

        async with httpx.AsyncClient() as client:
            url = DATABASE_BASE_URL + config.database.prefix + f'/words?user_id={user_id}'
            resp = await client.get(url=url)
            if resp.status_code == 200:
                words = resp.json()
                if words:
                    key = f'words:{user_id}'
                    mapping = {str(key): dumps(val) for key, val in words.items()}
                    await redis.hset(key, mapping=mapping)
                    await redis.expire(key, config.words_ttl)

                return words

            else:
                raise HTTPException(
                    status_code=resp.status_code, detail=resp.text
                )
    except Exception as e:
        logger.error(f'Error in get_words_handler: {e}')
        raise HTTPException(status_code=500, detail='Internal Server Error')


@router.post('/words')
async def save_word_handler(word_data: Word):
    try:
        async with httpx.AsyncClient() as client:
            url = DATABASE_BASE_URL + config.database.prefix + '/words'
            headers = {'content-type': 'application/json'}
            resp = await client.post(
                url=url,
                headers=headers,
                content=word_data.model_dump_json()
            )
            if resp.status_code == 200:
                user_id=word_data.user_id
                await redis.delete(f'words:{user_id}', f'stats:{user_id}')
                return 200

            else:
                raise HTTPException(
                    status_code=resp.status_code, detail=resp.text
                )
    except Exception as e:
        logger.error(f'Error in save_word_handler: {e}')
        raise HTTPException(status_code=500, detail='Internal Server Error')


@router.delete("/words")
async def api_delete_word_handler(
    user_id: int = Query(..., description="User ID"),
    word_id: int = Query(..., description="Word ID which it goes by in DB"),
):
    try:
        async with httpx.AsyncClient() as client:
            url = DATABASE_BASE_URL + config.database.prefix + f'/words?user_id={user_id}&word_id={word_id}'
            resp = await client.delete(url=url)
            if resp.status_code == 200:
                await redis.delete(f'words:{user_id}', f'stats:{user_id}')
                return 200
            else:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

    except Exception as e:
        logger.error(f"Error in api_delete_word_handler: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/words/search")
async def api_search_word_handler(
        word: str = Query(..., description="Слово для поиска среди пользователей"),
        user_id: int = Query(..., description="User ID пользователя"),
):
    try:
        # Создаем Redis key без user_id если он None
        redis_key = f'search_words:{word}:{user_id if user_id else "all"}'
        cached = await redis.hgetall(redis_key)
        if cached:
            return {str(key): loads(val) for key, val in cached.items()}

        # Ищем слово от пользователя
        async with httpx.AsyncClient() as client:
            # Строим URL в зависимости от наличия user_id
            if user_id:
                url = DATABASE_BASE_URL + config.database.prefix + \
                    f'/words/search?user_id={user_id}&word={word}'
            else:
                url = DATABASE_BASE_URL + config.database.prefix + \
                    f'/words/search?word={word}'
            
            resp = await client.get(url=url)
            if resp.status_code == 200:
                words = resp.json()
                if words:
                    mapping = {key: dumps(val) for key, val in words.items()}
                    await redis.hset(redis_key, mapping=mapping)
                    await redis.expire(redis_key, config.words_ttl)

                return words
            else:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

    except Exception as e:
        logger.error(f"Error in api_search_word_handler: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/words/stats")
async def api_stats_handler(
        user_id: int = Query(..., description="USer ID")
):
    """ Обработчик статистики слов пользователя """
    cached = await redis.hgetall(f'stats:{user_id}')
    if cached:
        return cached

    try:
        async with httpx.AsyncClient() as client:
            url = DATABASE_BASE_URL + config.database.prefix + f'/words/stats?user_id={user_id}'
            resp = await client.get(url=url)
            if resp.status_code == 200:
                stats = resp.json()
                if stats:
                    await redis.hset(f'stats:{user_id}', mapping=stats)
                    await redis.expire(f'stats:{user_id}', config.words_ttl)

                return stats

            else:
                raise HTTPException(
                    status_code=resp.status_code, detail=resp.text
                )

    except Exception as e:
        logger.error(f"Error in api_stats_handler: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


