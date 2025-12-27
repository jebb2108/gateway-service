import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


@dataclass
class PayHandlerConfig:
    prefix: str = os.getenv('PAYMENT_HANDLER_PREFIX')

@dataclass
class PayWebhookConfig:
    prefix: str = os.getenv('PAYMENT_WEBHOOK_PREFIX')

@dataclass
class PaymentsConfig:
    host: str = os.getenv('PAYMENT_HOST')
    port: int = int(os.getenv('PAYMENT_PORT'))
    handler: PayHandlerConfig = None
    webhook: PayWebhookConfig = None

    def __post_init__(self):
        if not self.handler: self.handler = PayHandlerConfig()
        if not self.webhook:  self.webhook = PayWebhookConfig()

@dataclass
class DatabaseConfig:
    host: str = os.getenv('DATABASE_HOST')
    port: int = int(os.getenv('DATABASE_PORT'))
    prefix: str = os.getenv('DATABASE_PREFIX')

@dataclass
class Config:

    host: str = os.getenv('THIS_HOST')
    port: int = int(os.getenv('THIS_PORT'))

    payments: PaymentsConfig = None
    database: DatabaseConfig = None
    tz_info: datetime = timezone(timedelta(hours=3.0))

    words_ttl = timedelta(minutes=30)

    def __post_init__(self):
        if not self.payments: self.payments = PaymentsConfig()
        if not self.database: self.database = DatabaseConfig()

config = Config()