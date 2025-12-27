import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.config import config
from src.endpoints.dictionary import router as dictionary_endpoints_router
from src.endpoints.payments import router as payment_endpoints_router
from src.endpoints.users import router as user_endpoints_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware, # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_endpoints_router)
app.include_router(payment_endpoints_router)
app.include_router(dictionary_endpoints_router)

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=config.host,
        port=config.port
    )
