import json
import logging
from json import loads

import httpx
from fastapi import HTTPException, APIRouter
from fastapi.params import Query
from redis.asyncio import Redis as aioredis

from src.config import config
from src.models import Payment

logger = logging.getLogger('gateway')

redis = aioredis.from_url("redis://redis")

router = APIRouter(prefix='/api')

PAYMENT_BASE_URL = f"http://{config.payments.host}:{config.payments.port}"


@router.get("/test_connection")
async def test_connection():
    """Тест соединения с database-сервисом"""
    try:
        async with (httpx.AsyncClient() as client):
            url = f"http://{config.database.host}:{config.database.port}" + \
                  f"{config.database.prefix}/health"

            logger.info(f"Testing connection to: {url}")
            response = await client.get(url, timeout=5.0)
            return {
                "status": "success",
                "database_url": url,
                "response": response.text
            }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "status": "error",
            "database_host": config.database.host,
            "database_port": config.database.port,
            "error": str(e)
        }


@router.get("/due_to")
async def get_users_due_to_handler(user_id = Query(..., description="User ID")):
    try:
        cached = await redis.hgetall(f'due_to:{user_id}')
        if cached:
            return { key: loads(val) for key, val in cached.items() }

        async with httpx.AsyncClient() as client:

            url = PAYMENT_BASE_URL + config.payments.handler.prefix + \
                  f'/due_to?user_id={user_id}'

            response = await client.get(url=url, timeout=5.0)
            if response.status_code == 200:
                if data := response.json():
                    mapping = {key: json.dumps(value) for key, value in data.items()}
                    await redis.hset(f'due_to:{user_id}', mapping=mapping)
                    await redis.expire(f'due_to:{user_id}', 900)

                return data # Возвращает либо словарь, либо null

    except Exception as e:
        logger.error(f'Error in get_users_due_to_handler: {e}')
        raise HTTPException(status_code=500, detail=f"Failed to update DB: {e}")


@router.get('/payment_data')
async def get_payment_data_handler(
        user_id: int = Query(..., description="User ID")
) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            url = PAYMENT_BASE_URL + config.payments.handler.prefix + f'/payment_data?user_id={user_id}'
            response = await client.get(url, timeout=5.0)
            return response.json()

    except Exception as e:
        logger.error(f'Error in get_payment_data_handler: {e}')
        raise HTTPException(status_code=500, detail=f"Failed to receive payment data: {e}")


@router.get('/yookassa_link')
async def get_yookassa_link_handler(
        user_id: int = Query(..., description="User ID")
) -> str:
    try:
        async with httpx.AsyncClient() as client:
            url = PAYMENT_BASE_URL + config.payments.handler.prefix + f'/link?user_id={user_id}'
            response = await client.get(url, timeout=5.0)
            return response.json()

    except Exception as e:
        logger.error(f'Error in get_yookassa_link_handler: {e}')
        raise HTTPException(status_code=500, detail=f"Failed to receive link: {e}")


@router.post("/create_payment")
async def create_payment(user_data: Payment):
    try:
        async with httpx.AsyncClient() as client:
            url = PAYMENT_BASE_URL + config.payments.handler.prefix + "/add"
            response = await client.post(
                url=url,
                json=user_data.model_dump(),
                timeout=10.0
            )
            await redis.delete(f'due_to:{user_data.user_id}')
            if response.status_code == 200:
                logger.info(f"Successfully posted: {response.status_code}")
                return {"status": "success"}

            return {"status": "failed", "error": response.status_code, "response": response.text}

    except Exception as e:
        logger.error(f'Error in create_payment_handler: {e}')
        raise HTTPException(status_code=500, detail=f"Failed to update DB: {e}")


@router.post('/toggle_sub')
async def deactivate_subscription_handler(user_data: dict):
    try:
        async with httpx.AsyncClient() as client:
            url = PAYMENT_BASE_URL + config.payments.handler.prefix
            url += '/activate' if user_data.get('activate') else '/deactivate'

            resp = await client.post(
                url=url,
                json=user_data,
                timeout=10.0
            )
            if resp.status_code == 200:
                logger.info(f"Successfully stopped subscription: {resp.status_code}")
                return {"status": "success"}

            return {"status": "failed", "error": resp.status_code, "response": resp.text}

    except Exception as e:
        logger.error(f'Error in deactivate_subscription_handler: {e}')
        raise HTTPException(status_code=500, detail=f"Failed to update DB: {e}")
