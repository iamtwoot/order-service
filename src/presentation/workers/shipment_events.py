import asyncio
import json
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer, ConsumerRecord, TopicPartition

from src.application.ports.usecases import HandleShipmentEventPort, ShipmentEventInput

logger = logging.getLogger(__name__)

EVENT_TYPES = {"order.shipped": True, "order.cancelled": False}


class ShipmentEventConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        handle_event: HandleShipmentEventPort,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._handle_event = handle_event

    async def run(self) -> None:
        while True:
            try:
                await self._consume()
            except Exception:
                logger.exception("Shipment events consumer crashed, restarting")
                await asyncio.sleep(5)

    async def _consume(self) -> None:
        consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await consumer.start()
        try:
            async for record in consumer:
                try:
                    await self._process(record)
                except Exception:
                    logger.exception(
                        "Failed to process %s, retrying", _message_id(record)
                    )
                    consumer.seek(
                        TopicPartition(record.topic, record.partition), record.offset
                    )
                    await asyncio.sleep(1)
                    continue
                await consumer.commit()
        finally:
            await consumer.stop()

    async def _process(self, record: ConsumerRecord) -> None:
        try:
            payload = json.loads(record.value)
            shipped = EVENT_TYPES[payload["event_type"]]
            order_id = UUID(payload["order_id"])
        except (ValueError, KeyError, TypeError):
            logger.warning("Skipping unexpected message %s", _message_id(record))
            return

        await self._handle_event(
            ShipmentEventInput(
                message_id=_message_id(record),
                order_id=order_id,
                shipped=shipped,
                payload=payload,
            )
        )


def _message_id(record: ConsumerRecord) -> str:
    return f"{record.topic}:{record.partition}:{record.offset}"
