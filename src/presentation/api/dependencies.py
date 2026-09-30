from typing import Annotated

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.ports.repositories import OutboxDestination
from src.application.ports.usecases import (
    CreateOrderPort,
    GetOrderPort,
    HandlePaymentCallbackPort,
)
from src.application.usecases.create_order import CreateOrder
from src.application.usecases.get_order import GetOrder
from src.application.usecases.handle_payment_callback import HandlePaymentCallback
from src.application.usecases.handle_shipment_event import HandleShipmentEvent
from src.application.usecases.publish_outbox_messages import PublishOutboxMessages
from src.infrastructure.http.catalog import HttpCatalogClient
from src.infrastructure.http.notifications import HttpNotificationsPublisher
from src.infrastructure.http.payments import HttpPaymentsClient
from src.infrastructure.messaging.kafka import KafkaPublisher
from src.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from src.presentation.workers.shipment_events import ShipmentEventConsumer
from src.settings import Settings


class Container(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)

    engine = providers.Singleton(
        create_async_engine,
        settings.provided.async_database_url,
    )
    session_factory = providers.Singleton(async_sessionmaker, engine)

    uow = providers.Factory(SQLAlchemyUnitOfWork, session_factory=session_factory)

    catalog = providers.Singleton(
        HttpCatalogClient,
        base_url=settings.provided.CAPASHINO_URL,
        api_token=settings.provided.CAPASHINO_API_TOKEN,
    )

    payments = providers.Singleton(
        HttpPaymentsClient,
        base_url=settings.provided.CAPASHINO_URL,
        api_token=settings.provided.CAPASHINO_API_TOKEN,
        callback_url=settings.provided.PAYMENTS_CALLBACK_URL,
    )

    create_order = providers.Factory(
        CreateOrder, uow=uow, catalog=catalog, payments=payments
    )
    get_order = providers.Factory(GetOrder, uow=uow)

    handle_payment_callback = providers.Factory(HandlePaymentCallback, uow=uow)

    publisher = providers.Singleton(
        KafkaPublisher,
        bootstrap_servers=settings.provided.KAFKA_BOOTSTRAP_SERVERS,
        topic=settings.provided.KAFKA_ORDER_EVENTS_TOPIC,
    )

    publish_order_events = providers.Factory(
        PublishOutboxMessages,
        uow=uow,
        publisher=publisher,
        destination=OutboxDestination.ORDER_EVENTS,
    )

    notifications_publisher = providers.Singleton(
        HttpNotificationsPublisher,
        base_url=settings.provided.CAPASHINO_URL,
        api_token=settings.provided.CAPASHINO_API_TOKEN,
    )
    publish_notifications = providers.Factory(
        PublishOutboxMessages,
        uow=uow,
        publisher=notifications_publisher,
        destination=OutboxDestination.NOTIFICATIONS,
    )

    shipment_event_consumer = providers.Singleton(
        ShipmentEventConsumer,
        bootstrap_servers=settings.provided.KAFKA_BOOTSTRAP_SERVERS,
        topic=settings.provided.KAFKA_SHIPMENT_EVENTS_TOPIC,
        group_id=settings.provided.KAFKA_CONSUMER_GROUP,
        handle_event=providers.Factory(HandleShipmentEvent, uow=uow),
    )


CreateOrderDep = Annotated[CreateOrderPort, Depends(Provide[Container.create_order])]
GetOrderDep = Annotated[GetOrderPort, Depends(Provide[Container.get_order])]
HandlePaymentCallbackDep = Annotated[
    HandlePaymentCallbackPort, Depends(Provide[Container.handle_payment_callback])
]
