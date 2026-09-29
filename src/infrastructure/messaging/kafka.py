import json
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from src.application.ports.messaging import MessagePublisher, PublishFailed


class KafkaPublisher(MessagePublisher):
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            enable_idempotence=True,
            key_serializer=str.encode,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def publish(self, key: str, payload: dict[str, Any]) -> None:
        if self._producer is None:
            raise RuntimeError("Kafka Producer is not started")
        try:
            await self._producer.send_and_wait(self._topic, key=key, value=payload)
        except KafkaError as e:
            raise PublishFailed(str(e)) from e
